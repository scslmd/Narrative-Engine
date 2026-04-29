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
                chapters_processed = len(analysis.sequences[0].chapters) if analysis.sequences else 0
                total_chapters = chapters_processed
            else:
                analysis = self._analyze_story(request.story_text, request.genre, request.tone)

            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)
            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=warnings,
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
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
        warnings: list[str] = []

        try:
            project_id = self._create_project(request)

            if on_progress:
                on_progress("initializing", {"chapters_processed": 0})

            if len(request.story_text) > MULTI_PASS_THRESHOLD:
                analysis_mode = "multi_pass"
                analysis = self._multi_pass_service.analyze_large_story(
                    request.story_text,
                    genre_hint=request.genre,
                    tone_hint=request.tone,
                    on_progress=on_progress,  # type: ignore[arg-type]
                )
                chapters_processed = len(analysis.sequences[0].chapters) if analysis.sequences else 0
                total_chapters = chapters_processed
            else:
                if on_progress:
                    on_progress("analysis", {"chapters_processed": 0})
                analysis = self._analyze_story(request.story_text, request.genre, request.tone)

            if on_progress:
                on_progress("persisting", {"chapters_processed": chapters_processed})

            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)

            return StoryImportResponse(
                project_id=project_id,
                status="completed",
                message=f"Successfully imported story into project '{analysis.project_name}'",
                warnings=warnings,
                chapters_processed=chapters_processed,
                total_estimated_chapters=total_chapters,
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
                analysis_mode=analysis_mode,
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
        if data is None:
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
        conn = sqlite3.connect(self._repository.db_path, timeout=30)
        try:
            conn.execute("BEGIN IMMEDIATE")

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
            char_id = hash_id("import-character", char_data.name)
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
            arc_id = hash_id("import-arc", arc_data.name)
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
