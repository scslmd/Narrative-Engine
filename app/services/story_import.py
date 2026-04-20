from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.story_development import StoryDevelopmentRepository
from ..schemas.enums import PovMode, StoryStructure
from ..schemas.inference import InferenceRequest
from ..schemas.manifest import Manifest, ManifestConfig
from ..schemas.story_import import (
    StoryImportAnalysis,
    StoryImportArc,
    StoryImportCharacterRequest,
    StoryImportRequest,
    StoryImportResponse,
    StoryImportWorldEntry,
)
from ..settings import settings
from .projects import ProjectService
from .runtime_prompts import build_import_analysis_request

logger = logging.getLogger(__name__)


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

    def import_story(self, request: StoryImportRequest) -> StoryImportResponse:
        """Main entry point. Synchronous processing flow.

        Steps:
        1. Validate request (text length, project_id if provided)
        2. Create project (if project_id not provided, create new)
        3. Call LLM to analyze and extract structured data
        4. Validate LLM output against StoryImportAnalysis schema
        5. Create all entities (foundation, characters, world bible, arcs)
        6. Update manifest with LLM metadata
        7. Return response
        """
        project_id = ""
        try:
            project_id = self._create_project(request)
            analysis = self._analyze_story(request.story_text, request.genre, request.tone)
            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)
            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=[],
            )
        except StoryImportError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=str(exc),
                warnings=["Import failed - partial data may exist on retry"],
            )
        except InferenceBackendError as exc:
            return StoryImportResponse(
                project_id=project_id,
                status="failed",
                message=f"LLM service unavailable: {exc.code}",
                warnings=["Retry the import when the inference service is available"],
            )

    def _create_project(self, request: StoryImportRequest) -> str:
        """Create project if needed, return project_id."""
        import sqlite3

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

    def _update_manifest(self, project_id: str, analysis: StoryImportAnalysis) -> None:
        """Update manifest.json with LLM-extracted metadata (B4/M3)."""
        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
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
        truncated_text = story_text[:24_000]
        inference_request = build_import_analysis_request(
            story_text=truncated_text,
            genre_hint=genre_hint,
            tone_hint=tone_hint,
            default_model=self._inferencer.descriptor.default_model,
        )

        try:
            response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError:
            raise

        parsed = self._parse_llm_json(response.content)
        try:
            analysis = StoryImportAnalysis.model_validate(parsed)
        except ValidationError as exc:
            raise StoryImportError(f"Invalid LLM response structure: {exc.errors()[0]['msg']}") from exc

        if not analysis.characters or len(analysis.characters) == 0:
            raise StoryImportError("LLM analysis returned no characters")

        return analysis

    def _parse_llm_json(self, content: str) -> dict[str, Any]:
        """Extract JSON from LLM response.

        Handles:
        - Raw JSON object
        - JSON inside ```json code fences
        - JSON with trailing text/garbage
        - JSON with leading text/garbage
        """
        stripped = content.strip()

        # Try direct parse first
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strip markdown code fences
        fenced = re.sub(r'^```(?:json)?\s*|\s*```$', '', stripped, flags=re.MULTILINE)
        fenced = fenced.strip()
        if fenced:
            try:
                return json.loads(fenced)
            except (json.JSONDecodeError, ValueError):
                pass

        # Find first { and last } in content
        first_brace = stripped.find('{')
        last_brace = stripped.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = stripped[first_brace : last_brace + 1]
            try:
                return json.loads(candidate)
            except (json.JSONDecodeError, ValueError):
                pass

        raise StoryImportError("Failed to parse LLM response as JSON")

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
        conn = sqlite3.connect(self._repository.db_path, timeout=30)
        try:
            conn.execute("BEGIN")

            self._import_foundation(conn, project_id, analysis, now)
            self._import_characters(conn, project_id, analysis, now)
            self._import_world_bible(conn, project_id, analysis, now)
            self._import_arcs(conn, project_id, analysis, now)

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
        # 1a. Insert foundation_profiles header
        conn.execute(
            """
            INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (project_id, now, now),
        )

        # 1b. Get next revision number
        rev_row = conn.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        next_rev = rev_row[0]

        narrative_constraints_json = json.dumps(
            list(analysis.narrative_constraints or []), ensure_ascii=True, sort_keys=True
        )

        conn.execute(
            """
            INSERT INTO foundation_revisions (
                project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                tone_direction, target_audience, narrative_constraints_json, complexity_level,
                success_definition, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, revision_number) DO UPDATE SET
                premise = excluded.premise,
                logline = excluded.logline,
                thematic_spine = excluded.thematic_spine,
                emotional_promise = excluded.emotional_promise,
                tone_direction = excluded.tone_direction,
                target_audience = excluded.target_audience,
                narrative_constraints_json = excluded.narrative_constraints_json,
                complexity_level = excluded.complexity_level,
                success_definition = excluded.success_definition,
                updated_at = excluded.updated_at
            """,
            (
                project_id,
                next_rev,
                analysis.premise,
                analysis.logline,
                analysis.thematic_spine or None,
                analysis.emotional_promise or None,
                analysis.tone or None,
                analysis.target_audience or None,
                narrative_constraints_json,
                analysis.complexity_level or None,
                analysis.success_definition or None,
                now,
                now,
            ),
        )

        # 1c. Update foundation_profiles.current_revision_id
        revision_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
            (revision_id, now, project_id),
        )

    def _import_characters(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: StoryImportAnalysis,
        now: str,
    ) -> None:
        """Insert all characters with ON CONFLICT for idempotency."""
        for char_data in analysis.characters:
            char_id = _hash_id("character", char_data.name)
            contradictions_json = json.dumps(char_data.contradictions or [], ensure_ascii=True, sort_keys=True)
            secrets_json = json.dumps(char_data.secrets or [], ensure_ascii=True, sort_keys=True)
            values_json = json.dumps(char_data.values or [], ensure_ascii=True, sort_keys=True)
            taboos_json = json.dumps(char_data.taboos or [], ensure_ascii=True, sort_keys=True)
            continuity_facts_json = json.dumps(char_data.continuity_facts or [], ensure_ascii=True, sort_keys=True)

            conn.execute(
                """
                INSERT INTO character_profiles (
                    character_id, project_id, display_name, role_in_story, archetype,
                    external_goal, internal_need, misbelief_or_wound, core_fear,
                    primary_strength, fatal_flaw_or_limitation, contradictions_json,
                    backstory_summary, voice_notes, relationship_map_json, secrets_json,
                    values_json, taboos_json, change_axis, arc_stage_notes,
                    continuity_facts_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(character_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    display_name = excluded.display_name,
                    role_in_story = excluded.role_in_story,
                    archetype = excluded.archetype,
                    external_goal = excluded.external_goal,
                    internal_need = excluded.internal_need,
                    misbelief_or_wound = excluded.misbelief_or_wound,
                    core_fear = excluded.core_fear,
                    primary_strength = excluded.primary_strength,
                    fatal_flaw_or_limitation = excluded.fatal_flaw_or_limitation,
                    contradictions_json = excluded.contradictions_json,
                    backstory_summary = excluded.backstory_summary,
                    voice_notes = excluded.voice_notes,
                    relationship_map_json = excluded.relationship_map_json,
                    secrets_json = excluded.secrets_json,
                    values_json = excluded.values_json,
                    taboos_json = excluded.taboos_json,
                    change_axis = excluded.change_axis,
                    arc_stage_notes = excluded.arc_stage_notes,
                    continuity_facts_json = excluded.continuity_facts_json,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    char_id,
                    project_id,
                    char_data.name,
                    char_data.role or None,
                    char_data.archetype or None,
                    _to_none(char_data.external_goal),
                    _to_none(char_data.internal_need),
                    None,
                    _to_none(char_data.core_fear),
                    _to_none(char_data.primary_strength),
                    _to_none(char_data.fatal_flaw),
                    contradictions_json,
                    _to_none(char_data.backstory),
                    _to_none(char_data.voice_notes),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    secrets_json,
                    values_json,
                    taboos_json,
                    _to_none(char_data.change_axis),
                    None,
                    continuity_facts_json,
                    None,
                    now,
                    now,
                ),
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
            canonical_facts_json = json.dumps(entry.canonical_facts or [], ensure_ascii=True, sort_keys=True)
            related_chars_json = json.dumps(entry.related_character_ids or [], ensure_ascii=True, sort_keys=True)
            source_artifacts_json = json.dumps([], ensure_ascii=True, sort_keys=True)
            continuity_warnings_json = json.dumps([], ensure_ascii=True, sort_keys=True)

            conn.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json,
                    related_character_ids_json, visibility_scope, source_artifacts_json,
                    continuity_warnings_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                    summary = excluded.summary,
                    canonical_facts_json = excluded.canonical_facts_json,
                    related_character_ids_json = excluded.related_character_ids_json,
                    visibility_scope = excluded.visibility_scope,
                    source_artifacts_json = excluded.source_artifacts_json,
                    continuity_warnings_json = excluded.continuity_warnings_json,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    entry.entry_type,
                    entry.title,
                    entry.summary if entry.summary else None,
                    canonical_facts_json,
                    related_chars_json,
                    "project",
                    source_artifacts_json,
                    continuity_warnings_json,
                    None,
                    now,
                    now,
                ),
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
            arc_id = _hash_id("arc", arc_data.name)
            stage_map_json = json.dumps(arc_data.stage_map or [], ensure_ascii=True, sort_keys=True)
            fit_notes_json = json.dumps([], ensure_ascii=True, sort_keys=True)
            tags_json = json.dumps(arc_data.tags or [], ensure_ascii=True, sort_keys=True)

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
                    stage_map_json,
                    fit_notes_json,
                    tags_json,
                    now,
                    now,
                ),
            )


def _hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value.

    Uses SHA-256 to produce a deterministic ID regardless of input ordering.
    Prefix format: import-{prefix}-{hash}
    """
    raw = f"import-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"import-{prefix}-{short_hash}"


def _to_none(value: str | None) -> str | None:
    """Convert empty strings to None for database compatibility."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None
