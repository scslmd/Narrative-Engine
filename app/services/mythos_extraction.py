from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.story_development import StoryDevelopmentRepository
from ..schemas.mythos_extraction import (
    ArchetypalPattern,
    CosmicRule,
    ExtractionSummary,
    MythosEntity,
    MythosExtractionAnalysis,
    MythosExtractionRequest,
    MythosExtractionResponse,
    NarrativeStructure,
    Relationship,
    SymbolicMotif,
)
from ..settings import settings
from .projects import ProjectService
from .runtime_prompts import build_mythos_analysis_request

logger = logging.getLogger(__name__)


class MythosExtractionError(ValueError):
    """Base error for mythos extraction failures."""
    pass


class MythosExtractionService:
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

    def extract(self, request: MythosExtractionRequest) -> MythosExtractionResponse:
        """Main entry point. Synchronous processing flow."""
        project_id = ""
        try:
            project_id = self._create_project(request)
            analysis = self._analyze_mythos(
                request.text, request.source_corpus, request.generation_mode
            )
            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)
            return MythosExtractionResponse(
                project_id=project_id,
                status="completed",
                extraction=ExtractionSummary(
                    source_corpus=analysis.source_corpus,
                    archetypal_patterns=len(analysis.archetypal_patterns),
                    narrative_structures=len(analysis.narrative_structures),
                    cosmic_rules=len(analysis.cosmic_rules),
                    symbolic_motifs=len(analysis.symbolic_motifs),
                ),
            )
        except MythosExtractionError as exc:
            return MythosExtractionResponse(
                project_id=project_id,
                status="failed",
                error=str(exc),
            )
        except InferenceBackendError as exc:
            return MythosExtractionResponse(
                project_id=project_id,
                status="failed",
                error=f"LLM service unavailable: {exc.code}",
            )

    def _create_project(self, request: MythosExtractionRequest) -> str:
        """Create project if needed, return project_id."""
        from ..schemas.projects import ProjectCreateRequest

        if request.project_id:
            try:
                self._project_service.get_project(request.project_id)
            except sqlite3.Error as exc:
                logger.error(
                    "DB error checking project %s: %s", request.project_id, exc
                )
                raise MythosExtractionError(
                    f"Database error while verifying project: {exc}"
                ) from exc
            except FileNotFoundError:
                raise MythosExtractionError(
                    f"Project not found: {request.project_id}"
                )
            return request.project_id

        project_name = f"Mythos: {request.source_corpus or 'Unknown Tradition'}"
        create_request = ProjectCreateRequest(project_name=project_name)
        response = self._project_service.create_project(create_request)
        return response.project_id

    def _analyze_mythos(
        self,
        mythos_text: str,
        source_corpus: str | None,
        generation_mode: str,
    ) -> MythosExtractionAnalysis:
        """Call LLM to analyze mythology text and extract patterns."""
        inference_request = build_mythos_analysis_request(
            mythos_text=mythos_text,
            source_corpus=source_corpus,
            generation_mode=generation_mode,
            default_model=self._inferencer.descriptor.default_model,
        )

        try:
            response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError:
            raise

        parsed = _extract_json(response.content)
        analysis = _parse_mythos_analysis(parsed)
        return analysis

    def _transactional_import(
        self,
        project_id: str,
        analysis: MythosExtractionAnalysis,
    ) -> None:
        """Execute entire entity creation in a single database transaction."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._repository.db_path, timeout=30)
        try:
            conn.execute("BEGIN")
            self._import_foundation(conn, project_id, analysis, now)
            self._import_world_bible(conn, project_id, analysis, now)
            self._import_archetypes(conn, project_id, analysis, now)
            self._import_entities(conn, project_id, analysis, now)
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
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert foundation_profiles header + foundation_revisions."""
        conn.execute(
            """
            INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (project_id, now, now),
        )

        rev_row = conn.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        next_rev = rev_row[0]

        narrative_constraints_json = json.dumps(
            {
                "archetypal_patterns": [
                    {"name": p.name, "description": p.description, "character_type": p.character_type}
                    for p in analysis.archetypal_patterns
                ],
                "narrative_structures": [
                    {"name": s.name, "phases": s.phases}
                    for s in analysis.narrative_structures
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
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
                "",
                "",
                analysis.thematic_spine or None,
                analysis.emotional_promise or None,
                analysis.tone_and_voice_direction or None,
                None,
                narrative_constraints_json,
                None,
                None,
                now,
                now,
            ),
        )

        revision_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
            (revision_id, now, project_id),
        )

    def _import_world_bible(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert cosmic rules and symbolic motifs as world_bible_entries."""
        for rule in analysis.cosmic_rules:
            exceptions_json = json.dumps(rule.exceptions or [], ensure_ascii=True, sort_keys=True)
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
                    "concept",
                    f"Cosmic Rule: {rule.rule}",
                    rule.enforcement if rule.enforcement else None,
                    exceptions_json,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    "project",
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    now,
                    now,
                ),
            )

        for motif in analysis.symbolic_motifs:
            summary_parts = [motif.meaning]
            if motif.narrative_function:
                summary_parts.append(f"Narrative function: {motif.narrative_function}")
            summary = ". ".join(summary_parts)

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
                    "concept",
                    f"Motif: {motif.symbol}",
                    summary if summary else None,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    "project",
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    now,
                    now,
                ),
            )

    def _import_archetypes(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert archetypal patterns as character_profiles."""
        for pattern in analysis.archetypal_patterns:
            char_id = _hash_id("archetype", pattern.name)
            narrative_beats_json = json.dumps(pattern.narrative_beats or [], ensure_ascii=True, sort_keys=True)

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
                    pattern.character_type or pattern.name,
                    "archetype",
                    pattern.name,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    pattern.description or None,
                    None,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    narrative_beats_json,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    now,
                    now,
                ),
            )

    def _import_entities(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert key entities: deities/forces as characters, locations/concepts as world bible."""
        for entity in analysis.key_entities:
            if entity.entity_type in ("deity", "force"):
                char_id = _hash_id("entity", entity.name)
                canonical_facts_json = json.dumps(entity.canonical_facts or [], ensure_ascii=True, sort_keys=True)

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
                        entity.name,
                        "mythos_entity",
                        entity.archetype or None,
                        None,
                        None,
                        None,
                        None,
                        entity.domain_or_power or None,
                        None,
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        None,
                        None,
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        None,
                        None,
                        canonical_facts_json,
                        None,
                        now,
                        now,
                    ),
                )
            else:
                canonical_facts_json = json.dumps(entity.canonical_facts or [], ensure_ascii=True, sort_keys=True)
                related_chars_json = json.dumps([], ensure_ascii=True, sort_keys=True)

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
                        entity.entity_type or "concept",
                        entity.name,
                        entity.domain_or_power or None,
                        canonical_facts_json,
                        related_chars_json,
                        "project",
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        None,
                        now,
                        now,
                    ),
                )

        for rel in analysis.entity_relationships:
            edge_id = _hash_id("edge", f"{rel.source}-{rel.target}")
            conn.execute(
                """
                INSERT INTO relationship_edges (
                    edge_id, project_id, source_character_id, target_character_id,
                    relation_kind, summary, tension, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(edge_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_character_id = excluded.source_character_id,
                    target_character_id = excluded.target_character_id,
                    relation_kind = excluded.relation_kind,
                    summary = excluded.summary,
                    tension = excluded.tension,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    edge_id,
                    project_id,
                    _hash_id("entity", rel.source),
                    _hash_id("entity", rel.target),
                    rel.relationship_type or "related",
                    rel.description or "",
                    None,
                    None,
                    now,
                    now,
                ),
            )

    def _update_manifest(self, project_id: str, analysis: MythosExtractionAnalysis) -> None:
        """Update manifest.json with mythos source corpus and generation mode."""
        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Manifest not found for project %s, skipping mythos metadata update", project_id)
            return

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
            return

        if "config" not in manifest_data:
            manifest_data["config"] = {}

        if analysis.source_corpus:
            manifest_data["config"]["mythos_source_corpus"] = analysis.source_corpus
        if analysis.generation_mode:
            manifest_data["config"]["mythos_generation_mode"] = analysis.generation_mode

        try:
            manifest_path.write_text(
                json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write manifest for project %s: %s", project_id, exc)


def _hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value."""
    raw = f"mythos-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"mythos-{prefix}-{short_hash}"


def _extract_json(content: str) -> dict[str, Any]:
    """Extract JSON object from LLM response text."""
    stripped = content.strip()

    # Try direct parse first
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strip markdown code fences
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE)
    fenced = fenced.strip()
    if fenced:
        try:
            return json.loads(fenced)
        except (json.JSONDecodeError, ValueError):
            pass

    # Find first { in content
    first_brace = stripped.find("{")
    if first_brace == -1:
        raise MythosExtractionError("Failed to parse LLM response as JSON")

    # Find balanced brace depth from first {
    depth = 0
    in_string = False
    escape_next = False
    json_end = -1
    for i in range(first_brace, len(stripped)):
        ch = stripped[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                json_end = i
                break

    if json_end != -1:
        try:
            return json.loads(stripped[first_brace : json_end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    raise MythosExtractionError("Failed to parse LLM response as JSON")


def _parse_mythos_analysis(data: dict[str, Any]) -> MythosExtractionAnalysis:
    """Parse and validate LLM JSON into MythosExtractionAnalysis."""

    def _to_str(value: Any, default: str = "") -> str:
        if isinstance(value, str):
            return value.strip() or default
        return str(value) if value else default

    def _to_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    patterns = [
        ArchetypalPattern(
            name=_to_str(p.get("name")),
            description=_to_str(p.get("description")),
            character_type=_to_str(p.get("character_type")),
            narrative_beats=_to_list(p.get("narrative_beats")),
            examples_from_text=_to_list(p.get("examples_from_text")),
        )
        for p in (data.get("archetypal_patterns") or [])
        if isinstance(p, dict)
    ]

    structures = [
        NarrativeStructure(
            name=_to_str(s.get("name")),
            phases=_to_list(s.get("phases")),
            tension_curve=_to_str(s.get("tension_curve")),
            resolution_type=_to_str(s.get("resolution_type")),
        )
        for s in (data.get("narrative_structures") or [])
        if isinstance(s, dict)
    ]

    rules = [
        CosmicRule(
            rule=_to_str(r.get("rule")),
            enforcement=_to_str(r.get("enforcement")),
            exceptions=_to_list(r.get("exceptions")),
        )
        for r in (data.get("cosmic_rules") or [])
        if isinstance(r, dict)
    ]

    motifs = [
        SymbolicMotif(
            symbol=_to_str(m.get("symbol")),
            meaning=_to_str(m.get("meaning")),
            narrative_function=_to_str(m.get("narrative_function")),
        )
        for m in (data.get("symbolic_motifs") or [])
        if isinstance(m, dict)
    ]

    entities = [
        MythosEntity(
            name=_to_str(e.get("name")),
            entity_type=_to_str(e.get("entity_type"), "concept"),
            archetype=_to_str(e.get("archetype")),
            domain_or_power=_to_str(e.get("domain_or_power")),
            canonical_facts=_to_list(e.get("canonical_facts")),
        )
        for e in (data.get("key_entities") or [])
        if isinstance(e, dict)
    ]

    relationships = [
        Relationship(
            source=_to_str(r.get("source")),
            target=_to_str(r.get("target")),
            relationship_type=_to_str(r.get("relationship_type")),
            description=_to_str(r.get("description")),
        )
        for r in (data.get("entity_relationships") or [])
        if isinstance(r, dict)
    ]

    return MythosExtractionAnalysis(
        source_corpus=_to_str(data.get("source_corpus"), "Unknown Tradition"),
        generation_mode=data.get("generation_mode", "same_world") or "same_world",
        archetypal_patterns=patterns,
        narrative_structures=structures,
        cosmic_rules=rules,
        symbolic_motifs=motifs,
        thematic_spine=_to_str(data.get("thematic_spine")),
        emotional_promise=_to_str(data.get("emotional_promise")),
        tone_and_voice_direction=_to_str(data.get("tone_and_voice_direction")),
        key_entities=entities,
        entity_relationships=relationships,
    )
