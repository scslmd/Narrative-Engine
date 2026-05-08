from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..inference.base import InferenceBackend, InferenceBackendError
from ..inference.factory import build_inference_backend
from ..persistence.sqlite import OPERATIONS_SCHEMA, OPERATIONS_INDEXES, connect as connect_sqlite, ensure_operations_db
from ..utils.db_inserts import (
    CharacterInsertData,
    hash_id,
    insert_character_profile,
    insert_foundation_profile,
    insert_world_bible_entry,
    json_safe,
    next_revision_number,
    update_foundation_revision_id,
)
from ..utils.json_extract import extract_json
from ..schemas.enums import PovMode, StoryStructure
from ..schemas.guided_setup import (
    CategoryProgress,
    ExtractedFields,
    GuidedArc,
    GuidedCharacter,
    GuidedChapter,
    GuidedConfig,
    GuidedFoundation,
    GuidedSequence,
    GuidedSetupAnalyzeRequest,
    GuidedSetupAnalyzeResponse,
    GuidedSetupCreateRequest,
    GuidedSetupCreateResponse,
    GuidedWorldEntry,
)
from ..settings import settings
from .projects import ProjectService
from .runtime_prompts import build_guided_setup_request

logger = logging.getLogger(__name__)


class GuidedSetupError(ValueError):
    pass


class GuidedSetupLLMError(GuidedSetupError):
    pass


class GuidedSetupValidationError(GuidedSetupError):
    pass


def _to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


class GuidedSetupService:
    """Service for LLM-guided project setup via conversational Q&A."""

    def __init__(
        self,
        project_service: ProjectService | None = None,
        inferencer: InferenceBackend | None = None,
        operations_db_path: Path | None = None,
    ) -> None:
        self._project_service = project_service or ProjectService()
        self._inferencer = inferencer
        self._operations_db_path = operations_db_path

    def _get_operations_db_path(self) -> Path:
        if self._operations_db_path:
            return self._operations_db_path
        return settings.operations_db_path

    def analyze_turn(
        self,
        request: GuidedSetupAnalyzeRequest,
    ) -> GuidedSetupAnalyzeResponse:
        """Analyze a conversation turn and extract structured fields.

        Calls the LLM with conversation history + current answer,
        returns extracted fields, next question, and progress tracking.
        """
        inferencer = self._inferencer or build_inference_backend(settings)

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        accumulated_dict = request.accumulated_fields.model_dump(mode="python")

        inference_request = build_guided_setup_request(
            conversation_history=conversation_history,
            current_answer=request.current_answer,
            accumulated_fields=accumulated_dict,
            default_model=settings.inference_default_model,
        )

        try:
            response = inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            raise GuidedSetupLLMError(f"LLM service unavailable: {exc}") from exc

        raw_data = extract_json(response.content)
        if not raw_data or not isinstance(raw_data, dict):
            raise GuidedSetupLLMError("Failed to parse LLM response as JSON")

        return self._parse_analyze_response(raw_data, accumulated_dict)

    def create_project_from_fields(
        self,
        request: GuidedSetupCreateRequest,
    ) -> GuidedSetupCreateResponse:
        """Create a project and populate entities from accumulated fields.

        Follows the story import's transactional pattern: single SQLite
        connection with BEGIN IMMEDIATE, raw SQL, ON CONFLICT for idempotency.
        """
        fields = request.accumulated_fields
        config = fields.config

        # Step 1: Create the project
        from ..schemas.projects import ProjectCreateRequest

        story_structure = StoryStructure.THREE_ACT
        try:
            story_structure = StoryStructure(config.story_structure)
        except (ValueError, AttributeError):
            pass

        pov_mode = PovMode.THIRD_LIMITED
        try:
            pov_mode = PovMode(config.pov)
        except (ValueError, AttributeError):
            pass

        from ..schemas.manifest import ManifestConfig

        manifest_config = ManifestConfig(
            genre=config.genre or "Unknown",
            tone_profile=config.tone_profile or "Neutral",
            pov=pov_mode,
            primary_language=config.primary_language or "English",
            secondary_language=config.secondary_language,
            story_structure=story_structure,
        )

        create_request = ProjectCreateRequest(
            project_name=config.project_name,
            config=manifest_config,
            constraints=config.constraints or [],
            premise_text=fields.foundation.premise_text or None,
        )

        project_response = self._project_service.create_project(create_request)
        project_id = project_response.project_id

        # Connect to the operations DB (where entity tables live)
        ops_db_path = ensure_operations_db(self._get_operations_db_path())
        conn = connect_sqlite(ops_db_path)
        # Ensure schema is initialized on this connection
        conn.executescript(OPERATIONS_SCHEMA)
        conn.executescript(OPERATIONS_INDEXES)

        # Step 2: Populate entities transactionally
        characters_created = 0
        world_created = 0
        arcs_created = 0
        foundation_created = False
        sequences_created = 0
        chapters_created = 0

        try:
            conn.execute("BEGIN IMMEDIATE")

            self._insert_foundation(conn, project_id, fields.foundation)
            foundation_created = True

            for char_data in fields.characters:
                self._insert_character(conn, project_id, char_data)
                characters_created += 1

            for world_entry in fields.world_bible:
                self._insert_world_entry(conn, project_id, world_entry)
                world_created += 1

            for arc_data in fields.arcs:
                self._insert_arc(conn, project_id, arc_data, fields.characters)
                arcs_created += 1

            # Build character name -> ID map for chapter resolution
            character_name_to_id: dict[str, str] = {}
            for char_data in fields.characters:
                char_id = hash_id("guided-character", f"{project_id}:{char_data.name}")
                character_name_to_id[char_data.name.strip().lower()] = char_id

            # Insert sequences (first pass — chapter_ids_json is empty placeholder)
            persisted_sequence_ids: list[str | None] = []
            sequence_id_map: dict[str, str] = {}
            for position, seq in enumerate(fields.sequences):
                seq_id = self._insert_sequence(conn, project_id, seq, position)
                persisted_sequence_ids.append(seq_id)
                if seq_id and seq.sequence_id:
                    sequence_id_map[seq.sequence_id] = seq_id

            # Insert chapters
            persisted_chapter_ids: list[str | None] = []
            for chapter in fields.chapters:
                ch_id = self._insert_chapter(conn, project_id, chapter, character_name_to_id, sequence_id_map)
                persisted_chapter_ids.append(ch_id)

            # Second pass: update sequences with actual chapter IDs
            for seq_idx, seq in enumerate(fields.sequences):
                current_seq_id = persisted_sequence_ids[seq_idx]
                if current_seq_id is None:
                    continue
                seq_chapter_ids = [
                    cid for cid, ch in zip(persisted_chapter_ids, fields.chapters)
                    if cid is not None and ch.sequence_id == seq.sequence_id
                ]
                if seq_chapter_ids:
                    conn.execute(
                        "UPDATE sequence_plans SET chapter_ids_json = ?, updated_at = ? WHERE sequence_id = ?",
                        (json_safe(seq_chapter_ids), datetime.now(timezone.utc).isoformat(), current_seq_id),
                    )

            sequences_created = len(fields.sequences)
            chapters_created = len(fields.chapters)

            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Failed to populate entities for project %s", project_id)
            raise
        finally:
            conn.close()

        return GuidedSetupCreateResponse(
            project_id=project_id,
            project_name=config.project_name,
            characters_created=characters_created,
            world_entries_created=world_created,
            arcs_created=arcs_created,
            foundation_created=foundation_created,
            sequences_created=sequences_created,
            chapters_created=chapters_created,
            message=(
                f"Project '{config.project_name}' created with "
                f"{characters_created} characters, {world_created} world entries, "
                f"{arcs_created} arcs, {sequences_created} sequences, {chapters_created} chapters"
            ),
        )

    def _insert_foundation(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        foundation: GuidedFoundation,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        next_rev = next_revision_number(conn, project_id)

        narrative_constraints_json = json_safe(list(foundation.narrative_constraints or []))

        insert_foundation_profile(
            conn, project_id, now, next_rev,
            premise=foundation.premise_text or "",
            logline=foundation.logline or "",
            thematic_spine=_to_none(foundation.thematic_spine),
            emotional_promise=_to_none(foundation.emotional_promise),
            tone_direction=None,
            target_audience=_to_none(foundation.target_audience),
            constraints_json=narrative_constraints_json,
            complexity_level=_to_none(foundation.complexity_level),
            success_definition=_to_none(foundation.success_definition),
        )
        update_foundation_revision_id(conn, project_id, None, now)

    def _parse_analyze_response(
        self,
        raw_data: dict[str, Any],
        previous_fields: dict[str, Any],
    ) -> GuidedSetupAnalyzeResponse:
        """Parse LLM JSON response into structured response, merging with previous state."""
        extracted_raw = raw_data.get("extracted_fields", {})

        # Merge: new values override previous, empty values fall back to previous
        merged_config = self._merge_dict(
            previous_fields.get("config", {}),
            extracted_raw.get("config", {}),
        )
        merged_foundation = self._merge_dict(
            previous_fields.get("foundation", {}),
            extracted_raw.get("foundation", {}),
        )

        # For lists, prefer new if non-empty, otherwise keep previous
        merged_characters = extracted_raw.get("characters") or previous_fields.get("characters", [])
        merged_world = extracted_raw.get("world_bible") or previous_fields.get("world_bible", [])
        merged_arcs = extracted_raw.get("arcs") or previous_fields.get("arcs", [])
        merged_sequences = extracted_raw.get("sequences") or previous_fields.get("sequences", [])
        merged_chapters = extracted_raw.get("chapters") or previous_fields.get("chapters", [])

        try:
            extracted = ExtractedFields(
                config=GuidedConfig(**merged_config),
                foundation=GuidedFoundation(**merged_foundation),
                characters=[GuidedCharacter(**c) for c in merged_characters] if merged_characters else [],
                world_bible=[GuidedWorldEntry(**w) for w in merged_world] if merged_world else [],
                arcs=[GuidedArc(**a) for a in merged_arcs] if merged_arcs else [],
                sequences=[GuidedSequence(**s) for s in merged_sequences] if merged_sequences else [],
                chapters=[GuidedChapter(**c) for c in merged_chapters] if merged_chapters else [],
            )
        except ValidationError as exc:
            raise GuidedSetupValidationError(f"Invalid extracted fields: {exc}") from exc

        category_progress_raw = raw_data.get("category_progress", [])
        try:
            category_progress = [
                CategoryProgress(**cp) for cp in category_progress_raw
            ] if category_progress_raw else []
        except ValidationError:
            category_progress = []

        return GuidedSetupAnalyzeResponse(
            extracted_fields=extracted,
            next_question=raw_data.get("next_question", "Please tell me more about your story idea."),
            confidence=float(raw_data.get("confidence", 0.5)),
            progress=float(raw_data.get("progress", 0)),
            ready_to_create=bool(raw_data.get("ready_to_create", False)),
            category_progress=category_progress,
        )

    @staticmethod
    def _merge_dict(previous: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        """Merge two dicts: new non-empty values override previous."""
        merged = dict(previous)
        for key, value in new.items():
            if value and value not in ("", []):
                merged[key] = value
        return merged

    def _insert_character(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        char_data: GuidedCharacter,
    ) -> None:
        char_id = hash_id("guided-character", f"{project_id}:{char_data.name}")
        insert_character_profile(conn, CharacterInsertData(
            character_id=char_id,
            project_id=project_id,
            display_name=char_data.name,
            role_in_story=char_data.role or None,
            archetype=_to_none(char_data.archetype),
            external_goal=_to_none(char_data.external_goal),
            internal_need=_to_none(char_data.internal_need),
            core_fear=_to_none(char_data.core_fear),
            primary_strength=_to_none(char_data.primary_strength),
            fatal_flaw=_to_none(char_data.fatal_flaw),
            contradictions_json=json_safe(char_data.contradictions or []),
            backstory_summary=_to_none(char_data.backstory_summary),
            voice_notes=_to_none(char_data.voice_notes),
            secrets_json=json_safe(char_data.secrets or []),
            values_json=json_safe(char_data.values or []),
            taboos_json=json_safe(char_data.taboos or []),
            change_axis=_to_none(char_data.change_axis),
            continuity_facts_json=json_safe([]),
        ))

    def _insert_world_entry(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        entry: GuidedWorldEntry,
    ) -> None:
        insert_world_bible_entry(
            conn, project_id, entry.entry_type, entry.title,
            summary=_to_none(entry.summary),
            canonical_facts_json=json_safe(entry.canonical_facts or []),
            related_character_ids_json=json_safe([]),
        )

    def _insert_arc(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        arc_data: GuidedArc,
        characters: list[GuidedCharacter],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        arc_id = hash_id("guided-arc", f"{project_id}:{arc_data.character_name}:{arc_data.arc_type}")

        # Try to find the character reference
        char_ref = arc_data.character_name
        for c in characters:
            if c.name.lower() == arc_data.character_name.lower():
                char_ref = c.name
                break

        conn.execute(
            """
            INSERT INTO arc_candidates (
                arc_id, project_id, name, summary, stage_map_notes_json,
                fit_notes_json, tags_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(arc_id) DO UPDATE SET
                project_id = excluded.project_id,
                name = excluded.name,
                summary = excluded.summary,
                stage_map_notes_json = excluded.stage_map_notes_json,
                fit_notes_json = excluded.fit_notes_json,
                tags_json = excluded.tags_json,
                updated_at = excluded.updated_at
            """,
            (
                arc_id,
                project_id,
                f"{char_ref} - {arc_data.arc_type}",
                _to_none(arc_data.summary),
                json_safe(arc_data.stages or []),
                json_safe([]),
                json_safe(arc_data.tags or []),
                now,
                now,
            ),
        )

    def _insert_sequence(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        sequence: GuidedSequence,
        position: int,
    ) -> str | None:
        now = datetime.now(timezone.utc).isoformat()
        seq_id = hash_id("guided-sequence", f"{project_id}:{sequence.title}")

        conn.execute(
            """
            INSERT INTO sequence_plans (
                sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json,
                status, position, provenance_note, confidence_score, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sequence_id) DO UPDATE SET
                project_id = excluded.project_id,
                title = excluded.title,
                summary = excluded.summary,
                status = excluded.status,
                position = excluded.position,
                confidence_score = excluded.confidence_score,
                updated_at = excluded.updated_at
            """,
            (
                seq_id,
                project_id,
                sequence.title,
                _to_none(sequence.summary),
                json_safe([]),
                json_safe([]),
                sequence.status or "guided",
                position,
                "guided setup wizard",
                0.75,
                now,
                now,
            ),
        )

        return seq_id

    def _insert_chapter(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        chapter: GuidedChapter,
        character_name_to_id: dict[str, str],
        sequence_id_map: dict[str, str],
    ) -> str | None:
        now = datetime.now(timezone.utc).isoformat()
        ch_id = hash_id("guided-chapter", f"{project_id}:{chapter.chapter_id}")

        resolved_characters: list[str] = []
        for name in chapter.active_character_ids:
            stripped = name.strip()
            if not stripped:
                continue
            resolved = character_name_to_id.get(stripped.lower())
            if resolved:
                resolved_characters.append(resolved)

        # Resolve original sequence_id to persisted sequence_id for FK reference
        resolved_sequence_id = None
        if chapter.sequence_id:
            resolved_sequence_id = sequence_id_map.get(chapter.sequence_id)

        conn.execute(
            """
            INSERT INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes,
                active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                status, position, provenance_note, confidence_score, created_at, updated_at, target_word_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chapter_id) DO UPDATE SET
                project_id = excluded.project_id,
                sequence_id = excluded.sequence_id,
                title = excluded.title,
                summary = excluded.summary,
                objective = excluded.objective,
                conflict = excluded.conflict,
                stakes = excluded.stakes,
                active_character_ids_json = excluded.active_character_ids_json,
                continuity_requirements_json = excluded.continuity_requirements_json,
                unresolved_questions_json = excluded.unresolved_questions_json,
                status = excluded.status,
                position = excluded.position,
                confidence_score = excluded.confidence_score,
                updated_at = excluded.updated_at
            """,
            (
                ch_id,
                project_id,
                resolved_sequence_id,
                chapter.title,
                _to_none(chapter.summary),
                _to_none(chapter.objective),
                _to_none(chapter.conflict),
                _to_none(chapter.stakes),
                json_safe(resolved_characters),
                json_safe(chapter.continuity_requirements or []),
                json_safe(chapter.unresolved_questions or []),
                chapter.status or "guided",
                chapter.position,
                "guided setup wizard",
                0.75,
                now,
                now,
                None,
            ),
        )

        return ch_id
