from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.sqlite import connect as connect_sqlite
from ..persistence.story_development import StoryDevelopmentRepository
from ..utils.db_inserts import (
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
from ..schemas.inference import InferenceRequest
from ..schemas.story_import import (
    PlotEvent,
    StoryImportAnalysis,
    StoryImportArc,
    StoryImportChapterSummary,
    StoryImportCharacterRequest,
    StoryImportRequest,
    StoryImportResponse,
    StoryImportSequence,
    StoryImportWorldEntry,
)
from ..settings import settings
from .multi_pass_import import MULTI_PASS_THRESHOLD, MultiPassImportService
from .projects import ProjectService
from .runtime_prompts import build_import_analysis_request

logger = logging.getLogger(__name__)

# Normalization map for world_bible entry_type synonyms from LLM output.
_ENTRY_TYPE_SYNONYMS: dict[str, str] = {
    "setting": "location",
    "place": "location",
    "region": "location",
    "city": "location",
    "country": "location",
    "area": "location",
    "town": "location",
    "kingdom": "location",
    "culture": "culture",
    "society": "culture",
    "custom": "culture",
    "magic": "magic_system",
    "power": "magic_system",
    "spell": "magic_system",
    "technology": "technology",
    "device": "technology",
    "tool": "technology",
    "organization": "organization",
    "faction": "organization",
    "group": "organization",
    "institution": "organization",
    "history": "history",
    "event": "history",
    "war": "history",
    "creature": "creature",
    "species": "creature",
    "being": "creature",
    "animal": "creature",
    "concept": "concept",
    "idea": "concept",
    "rule": "concept",
    "law": "concept",
    "principle": "concept",
    "contract": "concept",
    "pact": "concept",
    "agreement": "concept",
    "code": "concept",
    "oath": "concept",
}


class StoryImportError(ValueError):
    """Base error for story import failures."""
    pass


class StoryImportService:
    def __init__(
        self,
        *,
        project_service: ProjectService,
        repository: StoryDevelopmentRepository,
        inferencer: InferenceBackend,
        root_dir: Path | None = None,
    ) -> None:
        self._project_service = project_service
        self._repository = repository
        self._inferencer = inferencer
        self._root_dir = root_dir or settings.root_dir
        self._multi_pass_service = MultiPassImportService(inferencer)

    def import_story(self, request: StoryImportRequest) -> StoryImportResponse:
        """Main entry point. Synchronous processing flow.

        Routes to single-pass or multi-pass analysis based on story size.
        Stories > MULTI_PASS_THRESHOLD chars use multi-pass chunking.

        Steps:
        1. Validate request (text length, project_id if provided)
        2. Create project (if project_id not provided, create new)
        3. Analyze story (single-pass for small, multi-pass for large)
        4. Validate LLM output against StoryImportAnalysis schema
        5. Create all entities (foundation, characters, world bible, arcs)
        6. Update manifest with LLM metadata
        7. Return response
        """
        project_id = ""
        analysis_mode = "single_pass"
        chapters_processed = 0
        total_chapters = 0
        chunks_processed = 0
        total_chunks = 0
        warnings: list[str] = []

        try:
            project_id = self._create_project(request)

            # Route based on story size
            if len(request.story_text) > MULTI_PASS_THRESHOLD:
                analysis_mode = "multi_pass"
                analysis = self._multi_pass_service.analyze_large_story(
                    request.story_text,
                    genre_hint=request.genre,
                    tone_hint=request.tone,
                )
                chapters_processed, total_chapters, chunks_processed, total_chunks = self._analysis_metrics(analysis)
                warnings.extend(self._analysis_warnings(analysis))
            else:
                analysis = self._analyze_story(request.story_text, request.genre, request.tone)
                if analysis.chapter_summaries:
                    chapters_processed, total_chapters, chunks_processed, total_chunks = self._analysis_metrics(analysis)
                    warnings.extend(self._analysis_warnings(analysis))

            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)
            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=warnings,
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )
        except StoryImportError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=str(exc),
                warnings=["Import failed - partial data may exist on retry"],
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )
        except InferenceBackendError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=f"LLM service unavailable: {exc.code}",
                warnings=["Retry the import when the inference service is available"],
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )

    def import_story_with_progress(
        self,
        request: StoryImportRequest,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> StoryImportResponse:
        """Same as import_story but reports progress via callback."""
        project_id = ""
        analysis_mode = "single_pass"
        chapters_processed = 0
        total_chapters = 0
        chunks_processed = 0
        total_chunks = 0
        warnings: list[str] = []

        try:
            project_id = self._create_project(request)

            if on_progress:
                on_progress("initializing", {
                    "chapters_processed": 0,
                    "total_estimated_chapters": 0,
                    "chunks_processed": 0,
                    "total_estimated_chunks": 0,
                })

            if len(request.story_text) > MULTI_PASS_THRESHOLD:
                analysis_mode = "multi_pass"
                analysis = self._multi_pass_service.analyze_large_story(
                    request.story_text,
                    genre_hint=request.genre,
                    tone_hint=request.tone,
                    on_progress=on_progress,  # type: ignore[arg-type]
                )
                chapters_processed, total_chapters, chunks_processed, total_chunks = self._analysis_metrics(analysis)
                warnings.extend(self._analysis_warnings(analysis))
            else:
                if on_progress:
                    on_progress("analysis", {
                        "chapters_processed": 0,
                        "total_estimated_chapters": 0,
                        "chunks_processed": 0,
                        "total_estimated_chunks": 0,
                    })
                analysis = self._analyze_story(request.story_text, request.genre, request.tone)
                if analysis.chapter_summaries:
                    chapters_processed, total_chapters, chunks_processed, total_chunks = self._analysis_metrics(analysis)
                    warnings.extend(self._analysis_warnings(analysis))

            if on_progress:
                on_progress("persisting", {
                    "chapters_processed": chapters_processed,
                    "total_estimated_chapters": total_chapters,
                    "chunks_processed": chunks_processed,
                    "total_estimated_chunks": total_chunks,
                })

            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)

            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=warnings,
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )
        except StoryImportError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=str(exc),
                warnings=["Import failed - partial data may exist on retry"],
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )
        except InferenceBackendError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=f"LLM service unavailable: {exc.code}",
                warnings=["Retry the import when the inference service is available"],
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
                chunks_processed=chunks_processed,
                total_estimated_chunks=total_chunks,
                analysis_mode=analysis_mode,
            )

    def _create_project(self, request: StoryImportRequest) -> str:
        """Create project if needed, return project_id."""
        from ..schemas.projects import ProjectCreateRequest

        if request.project_id:
            try:
                self._project_service.get_project(request.project_id)
            except sqlite3.Error as exc:
                logger.error("DB error checking project %s: %s", request.project_id, exc)
                raise StoryImportError(f"Database error while verifying project: {exc}") from exc
            except FileNotFoundError:
                raise StoryImportError(f"Project not found: {request.project_id}")
            return request.project_id

        create_request = ProjectCreateRequest(project_name=request.project_name)
        response = self._project_service.create_project(create_request)
        return response.project_id

    def _analysis_metrics(
        self,
        analysis: StoryImportAnalysis,
    ) -> tuple[int, int, int, int]:
        chapter_count = len(analysis.chapter_summaries)
        chunk_count = analysis.completed_chunk_count or 0
        total_chunks = analysis.total_estimated_chunks or 0
        if chapter_count and not total_chunks:
            total_chunks = chapter_count
        if chapter_count and not chunk_count:
            chunk_count = chapter_count
        return chapter_count, chapter_count, chunk_count, total_chunks

    def _analysis_warnings(self, analysis: StoryImportAnalysis) -> list[str]:
        warnings: list[str] = []
        failed_titles = [
            chapter.title
            for chapter in analysis.chapter_summaries
            if chapter.analysis_status == "analysis_failed"
        ]
        partial_titles = [
            chapter.title
            for chapter in analysis.chapter_summaries
            if chapter.analysis_status == "partial_import"
        ]
        if failed_titles:
            warnings.append(
                "Some chapters could not be analyzed and were imported without downstream planning artifacts: "
                + ", ".join(failed_titles[:5])
            )
        if partial_titles:
            warnings.append(
                "Some chapters were only partially analyzed; imported planning artifacts may need review: "
                + ", ".join(partial_titles[:5])
            )
        return warnings

    def _update_manifest(self, project_id: str, analysis: StoryImportAnalysis) -> None:
        """Update manifest.json with LLM-extracted metadata (B4/M3)."""
        project_dir = self._project_service.projects_dir / project_id
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Manifest not found for project %s, skipping LLM metadata update", project_id)
            return

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
            return

        # Normalize genre from LLM to title case (e.g., "fantasy" -> "Fantasy")
        genre = analysis.genre.strip().title() if analysis.genre else None
        tone = analysis.tone.strip() if analysis.tone else None

        if "config" not in manifest_data:
            manifest_data["config"] = {}

        if genre:
            manifest_data["config"]["genre"] = genre
        if tone:
            manifest_data["config"]["tone_profile"] = tone

        # Validate and set POV
        try:
            pov_value = analysis.pov.strip() if analysis.pov else None
            if pov_value:
                # Try to match against known PovMode values
                for mode in PovMode:
                    if mode.value == pov_value or mode.name == pov_value:
                        manifest_data["config"]["pov"] = mode.value
                        break
        except Exception:
            logger.warning("Invalid POV value in analysis, skipping")

        # Validate and set story structure
        try:
            structure_value = analysis.story_structure.strip() if analysis.story_structure else None
            if structure_value:
                for structure in StoryStructure:
                    if structure.value == structure_value or structure.name == structure_value:
                        manifest_data["config"]["story_structure"] = structure.value
                        break
        except Exception:
            logger.warning("Invalid story structure value in analysis, skipping")

        # Set premise text
        if analysis.premise:
            manifest_data["premise_text"] = analysis.premise

        # Set constraints from analysis
        if analysis.narrative_constraints:
            manifest_data["constraints"] = [c.strip() for c in analysis.narrative_constraints if c.strip()]

        try:
            manifest_path.write_text(
                json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write manifest for project %s: %s", project_id, exc)

    def _analyze_story(self, story_text: str, genre_hint: str | None, tone_hint: str | None) -> StoryImportAnalysis:
        """Call LLM to analyze story and extract structured data."""
        inference_request = build_import_analysis_request(
            story_text=story_text,
            genre_hint=genre_hint,
            tone_hint=tone_hint,
            default_model=self._inferencer.descriptor.default_model,
        )

        try:
            response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError:
            raise

        parsed = self._parse_llm_json(response.content)
        mapped = _map_llm_fields(parsed)
        try:
            analysis = StoryImportAnalysis.model_validate(mapped)
        except ValidationError as exc:
            raise StoryImportError(f"Invalid LLM response structure: {exc.errors()[0]['msg']}") from exc

        if not analysis.characters or len(analysis.characters) == 0:
            raise StoryImportError("LLM analysis returned no characters")

        return analysis

    def _parse_llm_json(self, content: str) -> dict[str, Any]:
        """Extract JSON from LLM response."""
        data = extract_json(content)
        if data is None or not isinstance(data, dict):
            raise StoryImportError("Failed to parse LLM response as JSON")
        return data

    def _transactional_import(
        self,
        project_id: str,
        analysis: StoryImportAnalysis,
    ) -> None:
        """Execute entire entity creation in a single database transaction.

        Uses raw SQL with a single connection (NOT repo methods) to ensure
        atomicity. All inserts use ON CONFLICT for idempotent retries.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = connect_sqlite(self._repository.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            self._import_foundation(conn, project_id, analysis, now)
            self._import_characters(conn, project_id, analysis, now)
            self._import_world_bible(conn, project_id, analysis, now)
            self._import_arcs(conn, project_id, analysis, now)
            self._import_planning(conn, project_id, analysis, now)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _import_foundation(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Insert foundation revision (3 operations: header + revision + update)."""
        next_rev = next_revision_number(conn, project_id)

        narrative_constraints_json = json_safe(list(analysis.narrative_constraints or []))

        revision_id = insert_foundation_profile(
            conn, project_id, now, next_rev,
            premise=analysis.premise,
            logline=analysis.logline,
            thematic_spine=analysis.thematic_spine or None,
            emotional_promise=analysis.emotional_promise or None,
            tone_direction=analysis.tone or None,
            target_audience=analysis.target_audience or None,
            constraints_json=narrative_constraints_json,
            complexity_level=analysis.complexity_level or None,
            success_definition=analysis.success_definition or None,
        )
        update_foundation_revision_id(conn, project_id, revision_id, now)

    def _import_characters(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Insert all characters with ON CONFLICT for idempotency."""
        for char_data in analysis.characters:
            char_id = hash_id("import-character", f"{project_id}:{char_data.name}")
            insert_character_profile(
                conn, char_id, project_id,
                display_name=char_data.name,
                role_in_story=char_data.role or None,
                archetype=char_data.archetype or None,
                external_goal=_to_none(char_data.external_goal),
                internal_need=_to_none(char_data.internal_need),
                core_fear=_to_none(char_data.core_fear),
                primary_strength=_to_none(char_data.primary_strength),
                fatal_flaw=_to_none(char_data.fatal_flaw),
                contradictions_json=json_safe(char_data.contradictions or []),
                backstory_summary=_to_none(char_data.backstory),
                voice_notes=_to_none(char_data.voice_notes),
                secrets_json=json_safe(char_data.secrets or []),
                values_json=json_safe(char_data.values or []),
                taboos_json=json_safe(char_data.taboos or []),
                change_axis=_to_none(char_data.change_axis),
                continuity_facts_json=json_safe(char_data.continuity_facts or []),
                # Deep analysis fields (multi-pass import)
                aliases_json=json_safe(getattr(char_data, "aliases", []) or []),
                physical_description=_to_none(getattr(char_data, "physical_description", None)),
                personality_traits_json=json_safe(getattr(char_data, "personality_traits", []) or []),
                motives=_to_none(getattr(char_data, "motives", None)),
                relationships_json=json_safe(getattr(char_data, "relationships", []) or []),
                character_arc=_to_none(getattr(char_data, "character_arc", None)),
                symbolic_role=_to_none(getattr(char_data, "symbolic_role", None)),
                dialogue_patterns=_to_none(getattr(char_data, "dialogue_patterns", None)),
                psychological_depth=_to_none(getattr(char_data, "psychological_depth", None)),
                narrative_purpose=_to_none(getattr(char_data, "narrative_purpose", None)),
                thematic_significance=_to_none(getattr(char_data, "thematic_significance", None)),
                impact_on_others=_to_none(getattr(char_data, "impact_on_others", None)),
                first_appearance_chapter=_to_none(getattr(char_data, "first_appearance_chapter", None)),
                chapter_appearances_json=json_safe(getattr(char_data, "chapter_appearances", []) or []),
            )

    def _import_world_bible(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Insert all world bible entries with ON CONFLICT for idempotency."""
        for entry in analysis.world_bible:
            insert_world_bible_entry(
                conn, project_id, entry.entry_type, entry.title,
                summary=entry.summary if entry.summary else None,
                canonical_facts_json=json_safe(entry.canonical_facts or []),
                related_character_ids_json=json_safe(entry.related_character_ids or []),
            )

    def _import_arcs(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Insert all arc candidates with ON CONFLICT for idempotency."""
        for arc_data in analysis.story_arcs:
            arc_id = hash_id("import-arc", f"{project_id}:{arc_data.name}")
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
                    arc_data.name,
                    arc_data.summary if arc_data.summary else None,
                    json_safe(arc_data.stage_map or []),
                    json_safe([]),
                    json_safe(arc_data.tags or []),
                    now,
                    now,
                ),
            )

    def _import_planning(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Persist deterministic sequence/chapter planning artifacts when import analysis provides them."""
        if not analysis.sequences and not analysis.chapter_summaries:
            return

        chapter_summaries = self._validate_planning_chapter_summaries(analysis.chapter_summaries)
        sequences = self._validate_planning_sequences(analysis.sequences, chapter_summaries)
        if not chapter_summaries and not sequences:
            return

        character_ids_by_name = {
            character.name.strip().lower(): hash_id("import-character", f"{project_id}:{character.name}")
            for character in analysis.characters
            if character.name.strip()
        }
        planned_sequences: list[tuple[str, str, str, list[str]]] = []
        if sequences:
            for position, sequence in enumerate(sequences):
                planned_sequences.append((
                    hash_id("import-sequence", f"{project_id}:{sequence.title}:{position}"),
                    sequence.title,
                    sequence.summary,
                    list(sequence.chapters),
                ))
        elif chapter_summaries:
            planned_sequences.append((
                hash_id("import-sequence", f"{project_id}:main-narrative:0"),
                "Main Narrative",
                f"Imported story with {len(chapter_summaries)} chapters",
                [chapter.chapter_id for chapter in chapter_summaries],
            ))

        sequence_id_by_source_chapter: dict[str, str] = {}
        for position, (sequence_id, title, summary, source_chapter_ids) in enumerate(planned_sequences):
            for source_chapter_id in source_chapter_ids:
                sequence_id_by_source_chapter[source_chapter_id] = sequence_id
            source_sequence = sequences[position] if position < len(sequences) else None
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
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    sequence_id,
                    project_id,
                    title,
                    summary,
                    json_safe([]),
                    json_safe([]),
                    "imported" if chapter_summaries else "imported_high_level",
                    position,
                    (
                        source_sequence.provenance_note
                        if source_sequence is not None and source_sequence.provenance_note.strip()
                        else ("planning synthesis from analyzed chapters" if chapter_summaries else "single-pass high-level import")
                    ),
                    (
                        source_sequence.confidence_score
                        if source_sequence is not None and source_sequence.confidence_score > 0
                        else (0.75 if chapter_summaries else 0.45)
                    ),
                    now,
                    now,
                ),
            )

        if not chapter_summaries:
            return

        persisted_chapter_ids: dict[str, str] = {}
        scene_ids_by_source_chapter: dict[str, list[str]] = {}
        beat_ids_by_source_chapter: dict[str, list[str]] = {}
        chapter_reference_ids: dict[str, list[str]] = {}
        previous_chapter_plan_id: str | None = None
        previous_scene_id: str | None = None
        previous_beat_id: str | None = None

        for chapter in chapter_summaries:
            persisted_chapter_ids[chapter.chapter_id] = hash_id("import-chapter", f"{project_id}:{chapter.chapter_id}")

        for chapter_position, chapter in enumerate(chapter_summaries):
            chapter_plan_id = persisted_chapter_ids[chapter.chapter_id]
            sequence_id = sequence_id_by_source_chapter.get(chapter.chapter_id)

            active_character_ids = self._active_character_ids_for_summary(chapter, character_ids_by_name)
            chapter_status = self._planning_status_for_chapter(chapter)

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
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at,
                    target_word_count = excluded.target_word_count
                """,
                (
                    chapter_plan_id,
                    project_id,
                    sequence_id,
                    chapter.title,
                    chapter.summary or chapter.objective,
                    chapter.objective or chapter.summary or f"Advance {chapter.title}.",
                    chapter.conflict or "Conflict to refine from imported narrative.",
                    chapter.stakes or "Carry forward the imported narrative consequences.",
                    json_safe(active_character_ids),
                    json_safe(chapter.continuity_requirements),
                    json_safe(chapter.unresolved_questions),
                    chapter_status,
                    chapter_position,
                    chapter.provenance_note or "planning synthesis from analyzed chapter evidence",
                    chapter.confidence_score,
                    now,
                    now,
                    chapter.estimated_word_count,
                ),
            )

            scene_ids: list[str] = []
            beat_ids: list[str] = []
            prior_scene_id: str | None = None
            prior_beat_id: str | None = None

            if chapter.analysis_status == "analysis_failed":
                scene_ids_by_source_chapter[chapter.chapter_id] = scene_ids
                beat_ids_by_source_chapter[chapter.chapter_id] = beat_ids
                chapter_reference_ids[chapter.chapter_id] = list(dict.fromkeys(active_character_ids))
                if previous_chapter_plan_id is not None:
                    self._insert_planning_dependency(
                        conn,
                        dependency_id=hash_id("import-dependency", f"{project_id}:{previous_chapter_plan_id}:{chapter_plan_id}:precedes"),
                        project_id=project_id,
                        upstream_id=previous_chapter_plan_id,
                        downstream_id=chapter_plan_id,
                        dependency_kind="precedes",
                        reason="Imported chronological chapter order.",
                        now=now,
                    )
                previous_chapter_plan_id = chapter_plan_id
                continue

            plot_events = chapter.plot_events or []
            if not plot_events:
                plot_events = [
                    PlotEvent(
                        summary=chapter.summary or chapter.objective or chapter.title,
                        characters_involved=list(chapter.active_character_names),
                        significance="development",
                        unresolved_threads=list(chapter.unresolved_questions),
                    )
                ]

            for item_position, plot_event in enumerate(plot_events):
                event_active_character_ids = self._character_ids_for_names(
                    plot_event.characters_involved or chapter.active_character_names,
                    character_ids_by_name,
                )
                arc_stage = self._normalize_arc_stage(plot_event.significance)
                beat_id = hash_id("import-beat", f"{project_id}:{chapter.chapter_id}:{item_position}:{plot_event.summary}")
                scene_id = hash_id("import-scene", f"{project_id}:{chapter.chapter_id}:{item_position}:{plot_event.summary}")

                beat_dependency_ids = [dep for dep in (prior_beat_id, previous_beat_id) if dep is not None]
                conn.execute(
                    """
                    INSERT INTO beat_plans (
                        beat_id, project_id, objective, conflict, stakes, dependency_ids_json, arc_stage,
                        active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                        status, position, provenance_note, confidence_score, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(beat_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        objective = excluded.objective,
                        conflict = excluded.conflict,
                        stakes = excluded.stakes,
                        dependency_ids_json = excluded.dependency_ids_json,
                        arc_stage = excluded.arc_stage,
                        active_character_ids_json = excluded.active_character_ids_json,
                        continuity_requirements_json = excluded.continuity_requirements_json,
                        unresolved_questions_json = excluded.unresolved_questions_json,
                        status = excluded.status,
                        position = excluded.position,
                        provenance_note = excluded.provenance_note,
                        confidence_score = excluded.confidence_score,
                        updated_at = excluded.updated_at
                    """,
                    (
                        beat_id,
                        project_id,
                        plot_event.summary,
                        chapter.conflict or f"Resolve {plot_event.significance.replace('_', ' ')} tension.",
                        chapter.stakes or "Carry the narrative consequences forward.",
                        json_safe(beat_dependency_ids),
                        arc_stage,
                        json_safe(event_active_character_ids),
                        json_safe(chapter.continuity_requirements),
                        json_safe(plot_event.unresolved_threads or chapter.unresolved_questions),
                        chapter_status,
                        len(beat_ids),
                        chapter.provenance_note or "derived from imported chapter planning evidence",
                        chapter.confidence_score,
                        now,
                        now,
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO scene_plans (
                        scene_id, project_id, chapter_id, title, summary, objective, conflict, stakes,
                        active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                        status, position, provenance_note, confidence_score, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(scene_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        chapter_id = excluded.chapter_id,
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
                        provenance_note = excluded.provenance_note,
                        confidence_score = excluded.confidence_score,
                        updated_at = excluded.updated_at
                    """,
                    (
                        scene_id,
                        project_id,
                        chapter_plan_id,
                        self._scene_title(chapter, item_position, plot_event),
                        plot_event.summary,
                        plot_event.summary,
                        chapter.conflict or f"Escalate {plot_event.significance.replace('_', ' ')} tension.",
                        chapter.stakes or "Advance the imported narrative trajectory.",
                        json_safe(event_active_character_ids),
                        json_safe(chapter.continuity_requirements),
                        json_safe(plot_event.unresolved_threads or chapter.unresolved_questions),
                        chapter_status,
                        len(scene_ids),
                        chapter.provenance_note or "derived from imported chapter planning evidence",
                        chapter.confidence_score,
                        now,
                        now,
                    ),
                )

                if prior_scene_id is not None:
                    self._insert_planning_dependency(
                        conn,
                        dependency_id=hash_id("import-dependency", f"{project_id}:{prior_scene_id}:{scene_id}:precedes"),
                        project_id=project_id,
                        upstream_id=prior_scene_id,
                        downstream_id=scene_id,
                        dependency_kind="precedes",
                        reason=f"Imported chronological order within {chapter.title}.",
                        now=now,
                    )
                elif previous_scene_id is not None:
                    self._insert_planning_dependency(
                        conn,
                        dependency_id=hash_id("import-dependency", f"{project_id}:{previous_scene_id}:{scene_id}:precedes"),
                        project_id=project_id,
                        upstream_id=previous_scene_id,
                        downstream_id=scene_id,
                        dependency_kind="precedes",
                        reason="Imported chronological order across chapters.",
                        now=now,
                    )

                prior_scene_id = scene_id
                prior_beat_id = beat_id
                previous_scene_id = scene_id
                previous_beat_id = beat_id
                scene_ids.append(scene_id)
                beat_ids.append(beat_id)

            scene_ids_by_source_chapter[chapter.chapter_id] = scene_ids
            beat_ids_by_source_chapter[chapter.chapter_id] = beat_ids
            chapter_reference_ids[chapter.chapter_id] = list(dict.fromkeys(active_character_ids + scene_ids + beat_ids))

            if previous_chapter_plan_id is not None:
                self._insert_planning_dependency(
                    conn,
                    dependency_id=hash_id("import-dependency", f"{project_id}:{previous_chapter_plan_id}:{chapter_plan_id}:precedes"),
                    project_id=project_id,
                    upstream_id=previous_chapter_plan_id,
                    downstream_id=chapter_plan_id,
                    dependency_kind="precedes",
                    reason="Imported chronological chapter order.",
                    now=now,
                )

            previous_chapter_plan_id = chapter_plan_id

            packet_id = hash_id("import-packet", f"{project_id}:{chapter.chapter_id}")
            conn.execute(
                """
                INSERT INTO chapter_packets (
                    packet_id, project_id, chapter_id, included_reference_ids_json, constraints_json,
                    scene_goals_json, status, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    included_reference_ids_json = excluded.included_reference_ids_json,
                    constraints_json = excluded.constraints_json,
                    scene_goals_json = excluded.scene_goals_json,
                    status = excluded.status,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    packet_id,
                    project_id,
                    chapter_plan_id,
                    json_safe(chapter_reference_ids[chapter.chapter_id]),
                    json_safe(list(dict.fromkeys((analysis.narrative_constraints or []) + chapter.continuity_requirements))),
                    json_safe([event.summary for event in plot_events[:8]]),
                    chapter_status,
                    chapter.provenance_note or "derived from imported chapter planning evidence",
                    chapter.confidence_score,
                    now,
                    now,
                ),
            )

        sequence_beat_ids: dict[str, list[str]] = {}
        sequence_chapter_ids: dict[str, list[str]] = {}
        for chapter in chapter_summaries:
            sequence_id = sequence_id_by_source_chapter.get(chapter.chapter_id)
            if sequence_id is None:
                continue
            sequence_chapter_ids.setdefault(sequence_id, []).append(persisted_chapter_ids[chapter.chapter_id])
            sequence_beat_ids.setdefault(sequence_id, []).extend(beat_ids_by_source_chapter.get(chapter.chapter_id, []))

        for position, (sequence_id, title, summary, _) in enumerate(planned_sequences):
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
                    beat_ids_json = excluded.beat_ids_json,
                    chapter_ids_json = excluded.chapter_ids_json,
                    status = excluded.status,
                    position = excluded.position,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    sequence_id,
                    project_id,
                    title,
                    summary,
                    json_safe(sequence_beat_ids.get(sequence_id, [])),
                    json_safe(sequence_chapter_ids.get(sequence_id, [])),
                    "imported",
                    position,
                    sequences[position].provenance_note if position < len(sequences) else "planning synthesis from analyzed chapters",
                    sequences[position].confidence_score if position < len(sequences) else 0.75,
                    now,
                    now,
                ),
            )

    def _validate_planning_chapter_summaries(
        self,
        chapter_summaries: list[StoryImportChapterSummary],
    ) -> list[StoryImportChapterSummary]:
        valid: list[StoryImportChapterSummary] = []
        seen_ids: set[str] = set()
        for chapter in chapter_summaries:
            if not chapter.chapter_id.strip() or chapter.chapter_id in seen_ids:
                continue
            seen_ids.add(chapter.chapter_id)
            valid.append(chapter)
        return valid

    def _validate_planning_sequences(
        self,
        sequences: list[StoryImportSequence],
        chapter_summaries: list[StoryImportChapterSummary],
    ) -> list[StoryImportSequence]:
        known_chapter_ids = {chapter.chapter_id for chapter in chapter_summaries}
        valid: list[StoryImportSequence] = []
        for sequence in sequences:
            chapter_ids = list(dict.fromkeys(
                chapter_id for chapter_id in sequence.chapters if not known_chapter_ids or chapter_id in known_chapter_ids
            ))
            valid.append(
                StoryImportSequence(
                    title=sequence.title,
                    summary=sequence.summary,
                    chapters=chapter_ids,
                    provenance_note=sequence.provenance_note,
                    confidence_score=sequence.confidence_score,
                )
            )
        return valid

    def _active_character_ids_for_summary(
        self,
        chapter: StoryImportChapterSummary,
        character_ids_by_name: dict[str, str],
    ) -> list[str]:
        return self._character_ids_for_names(chapter.active_character_names, character_ids_by_name)

    def _character_ids_for_names(
        self,
        names: list[str],
        character_ids_by_name: dict[str, str],
    ) -> list[str]:
        resolved: list[str] = []
        for name in names:
            normalized = name.strip().lower()
            if normalized and normalized in character_ids_by_name:
                resolved.append(character_ids_by_name[normalized])
        return list(dict.fromkeys(resolved))

    def _scene_title(
        self,
        chapter: StoryImportChapterSummary,
        item_position: int,
        plot_event: PlotEvent,
    ) -> str:
        prefix = chapter.title or chapter.chapter_id
        return f"{prefix} Scene {item_position + 1}"

    def _planning_status_for_chapter(self, chapter: StoryImportChapterSummary) -> str:
        if chapter.analysis_status == "analysis_failed":
            return "analysis_failed"
        if chapter.analysis_status == "partial_import":
            return "partial_import"
        return "imported"

    def _normalize_arc_stage(self, significance: str | None) -> str:
        if not significance:
            return "development"
        normalized = significance.strip().lower()
        valid_stages = {
            "status_quo",
            "inciting_incident",
            "rising_action",
            "crisis",
            "climax",
            "resolution",
            "turning_point",
            "development",
        }
        return normalized if normalized in valid_stages else "development"

    def _insert_planning_dependency(
        self,
        conn: sqlite3.Connection,
        *,
        dependency_id: str,
        project_id: str,
        upstream_id: str,
        downstream_id: str,
        dependency_kind: str,
        reason: str,
        now: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO planning_dependencies (
                dependency_id, project_id, upstream_id, downstream_id, dependency_kind, reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dependency_id) DO UPDATE SET
                project_id = excluded.project_id,
                upstream_id = excluded.upstream_id,
                downstream_id = excluded.downstream_id,
                dependency_kind = excluded.dependency_kind,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (
                dependency_id,
                project_id,
                upstream_id,
                downstream_id,
                dependency_kind,
                reason,
                now,
                now,
            ),
        )


def _to_none(value: str | None) -> str | None:
    """Convert empty strings to None for database compatibility."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _map_llm_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Post-process LLM JSON to translate common wrong field names to expected ones.

    The LLM frequently uses natural-language synonyms instead of the exact schema keys.
    This mapper corrects those before Pydantic validation.

    Known LLM substitutions:
    - world_bible: name->title, description->summary, significance->append to summary
    - story_arcs: description->summary, type->tags (if single value), missing stage_map/tags
    - sequences: name->title, description->summary, missing chapters
    - character arrays: strings instead of lists for contradictions, secrets, values, taboos, continuity_facts
    """
    result = dict(data)

    # Process world_bible entries
    wb = result.get("world_bible", [])
    if isinstance(wb, list):
        mapped_wb = []
        for entry in wb:
            if not isinstance(entry, dict):
                continue
            mapped = {}

            # title: use 'title' if present, otherwise 'name'
            if "title" in entry:
                mapped["title"] = entry["title"]
            elif "name" in entry:
                mapped["title"] = entry["name"]

            # entry_type: try 'entry_type', fall back to deriving from title
            if "entry_type" in entry:
                raw_type = str(entry["entry_type"]).strip().lower()
                mapped["entry_type"] = _ENTRY_TYPE_SYNONYMS.get(raw_type, raw_type)
            else:
                # Try to infer from title context or default to 'other'
                title = str(mapped.get("title", "")).lower()
                if any(w in title for w in ["kingdom", "city", "land", "region", "mountain", "place", "location"]):
                    mapped["entry_type"] = "location"
                elif any(w in title for w in ["track", "contract", "agreement", "pact", "rule"]):
                    mapped["entry_type"] = "concept"
                elif any(w in title for w in ["railway", "train", "transport"]):
                    mapped["entry_type"] = "technology"
                elif any(w in title for w in ["empire", "state"]):
                    mapped["entry_type"] = "culture"
                else:
                    mapped["entry_type"] = "other"

            # summary: use 'summary' if present, otherwise 'description',
            # optionally append 'significance'
            if "summary" in entry:
                summary = str(entry["summary"])
            elif "description" in entry:
                summary = str(entry["description"])
            else:
                summary = ""

            if "significance" in entry and entry["significance"]:
                sig = str(entry["significance"]).strip()
                if sig and not summary.endswith(sig):
                    summary = f"{summary}. {sig}" if summary else sig

            mapped["summary"] = summary
            cf = entry.get("canonical_facts", [])
            if isinstance(cf, str) and cf.strip():
                mapped["canonical_facts"] = [cf.strip()]
            elif isinstance(cf, list):
                mapped["canonical_facts"] = [str(v) for v in cf if v]
            else:
                mapped["canonical_facts"] = []
            rc = entry.get("related_character_ids", [])
            if isinstance(rc, str) and rc.strip():
                mapped["related_character_ids"] = [rc.strip()]
            elif isinstance(rc, list):
                mapped["related_character_ids"] = [str(v) for v in rc if v]
            else:
                mapped["related_character_ids"] = []
            mapped_wb.append(mapped)
        result["world_bible"] = mapped_wb

    # Process story_arcs entries
    arcs = result.get("story_arcs", [])
    if isinstance(arcs, list):
        mapped_arcs = []
        for arc in arcs:
            if not isinstance(arc, dict):
                continue
            mapped = {}

            mapped["name"] = arc.get("name", "")
            if not isinstance(mapped["name"], str):
                mapped["name"] = str(mapped["name"])

            # summary: use 'summary' if present, otherwise 'description'
            if "summary" in arc:
                mapped["summary"] = str(arc["summary"])
            elif "description" in arc:
                mapped["summary"] = str(arc["description"])
            else:
                mapped["summary"] = ""

            # stage_map: default list if missing
            if "stage_map" in arc and arc["stage_map"]:
                mapped["stage_map"] = arc["stage_map"]
                if not isinstance(mapped["stage_map"], list):
                    mapped["stage_map"] = [str(mapped["stage_map"])]
            else:
                mapped["stage_map"] = []

            # tags: use 'tags' if present, otherwise derive from 'type' field
            if "tags" in arc:
                mapped["tags"] = arc["tags"]
                if not isinstance(mapped["tags"], list):
                    mapped["tags"] = [str(mapped["tags"])] if mapped["tags"] else []
            elif "type" in arc and arc["type"]:
                mapped["tags"] = [str(arc["type"])]
            else:
                mapped["tags"] = []

            mapped_arcs.append(mapped)
        result["story_arcs"] = mapped_arcs

    # Process sequences entries
    seqs = result.get("sequences", [])
    if isinstance(seqs, list):
        mapped_seqs = []
        for seq in seqs:
            if not isinstance(seq, dict):
                continue
            mapped = {}

            # title: use 'title' if present, otherwise 'name'
            if "title" in seq:
                mapped["title"] = str(seq["title"])
            elif "name" in seq:
                mapped["title"] = str(seq["name"])
            else:
                mapped["title"] = ""

            # summary: use 'summary' if present, otherwise 'description'
            if "summary" in seq:
                mapped["summary"] = str(seq["summary"])
            elif "description" in seq:
                mapped["summary"] = str(seq["description"])
            else:
                mapped["summary"] = ""

            # chapters: default empty list
            mapped["chapters"] = seq.get("chapters", [])
            if not isinstance(mapped["chapters"], list):
                mapped["chapters"] = []

            mapped_seqs.append(mapped)
        result["sequences"] = mapped_seqs

    # Process character list fields: ensure array fields are actually lists
    chars = result.get("characters", [])
    if isinstance(chars, list):
        array_fields = ["contradictions", "secrets", "values", "taboos", "continuity_facts"]
        mapped_chars = []
        for char in chars:
            if not isinstance(char, dict):
                continue
            mapped = dict(char)
            for field in array_fields:
                val = mapped.get(field)
                if isinstance(val, str) and val.strip():
                    # Convert single string to list
                    mapped[field] = [val.strip()]
                elif isinstance(val, list):
                    # Ensure all items are strings
                    mapped[field] = [str(v) for v in val if v]
                else:
                    mapped[field] = []
            mapped_chars.append(mapped)
        result["characters"] = mapped_chars

    # Ensure narrative_constraints is a list
    nc = result.get("narrative_constraints")
    if isinstance(nc, str):
        result["narrative_constraints"] = [nc.strip()] if nc.strip() else []
    elif not isinstance(nc, list):
        result["narrative_constraints"] = []

    return result
