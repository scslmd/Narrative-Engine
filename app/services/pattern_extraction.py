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
    MythosExtractionRequest,
    NarrativeStructure,
    Relationship,
    SymbolicMotif,
)
from ..schemas.pattern_extraction import (
    NarrativePattern,
    PatternExtractionAnalysis,
    PatternExtractionResponse,
    PatternExtractionSummary,
    StoryEntity,
    ThematicConstraint,
    VoiceProfile,
    WorldRule,
)
from ..settings import settings
from .mythos_extraction import MythosExtractionService, MythosExtractionError
from .projects import ProjectService
from .runtime_prompts import build_narrative_analysis_request

logger = logging.getLogger(__name__)


class PatternExtractionError(ValueError):
    """Error during pattern extraction."""
    pass


class PatternExtractionService:
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
        self._mythos_service = MythosExtractionService(
            project_service=project_service,
            repository=repository,
            inferencer=inferencer,
            root_dir=self._root_dir,
        )

    def extract(
        self,
        text: str,
        source_type: str = "narrative",
        generation_mode: str = "same_world",
        project_id: str | None = None,
        source_corpus: str | None = None,
    ) -> PatternExtractionResponse:
        """Main entry point for pattern extraction.

        Dispatches to mythology or narrative extraction based on source_type.
        """
        if source_type == "mythology":
            return self._extract_mythology(
                text=text,
                generation_mode=generation_mode,
                project_id=project_id,
                source_corpus=source_corpus,
            )

        return self._extract_narrative(
            text=text,
            generation_mode=generation_mode,
            source_corpus=source_corpus,
        )

    def _extract_mythology(
        self,
        text: str,
        generation_mode: str,
        project_id: str | None,
        source_corpus: str | None,
    ) -> PatternExtractionResponse:
        """Delegate mythology extraction to MythosExtractionService."""
        mythos_request = MythosExtractionRequest(
            text=text,
            generation_mode=generation_mode,
            project_id=project_id,
            source_corpus=source_corpus,
        )
        mythos_response = self._mythos_service.extract(mythos_request)

        summary: PatternExtractionSummary | None = None
        if mythos_response.status == "completed" and mythos_response.extraction is not None:
            summary = PatternExtractionSummary(
                source_corpus=mythos_response.extraction.source_corpus,
                archetypal_patterns=mythos_response.extraction.archetypal_patterns,
                narrative_structures=mythos_response.extraction.narrative_structures,
                world_rules=mythos_response.extraction.cosmic_rules,
                symbolic_motifs=mythos_response.extraction.symbolic_motifs,
            )

        return PatternExtractionResponse(
            status=mythos_response.status,
            project_id=mythos_response.project_id,
            extraction=summary,
            error=mythos_response.error,
        )

    def extract_from_project(
        self,
        *,
        project_id: str,
        source_type: str = "narrative",
        generation_mode: str = "same_world",
        source_corpus: str | None = None,
    ) -> PatternExtractionResponse:
        """Extract patterns from manuscript documents of an existing project.

        Retrieves all manuscript documents for the project, concatenates their
        content as source text, and delegates to extract().
        """
        documents = self._repository.list_manuscript_documents(project_id)
        if not documents:
            return PatternExtractionResponse(
                status="failed",
                project_id=project_id,
                error=f"No manuscript documents found for project {project_id}",
            )

        text = "\n\n".join(doc.content for doc in documents)
        return self.extract(
            text=text,
            source_type=source_type,
            generation_mode=generation_mode,
            project_id=project_id,
            source_corpus=source_corpus,
        )

    def _extract_narrative(
        self,
        text: str,
        generation_mode: str,
        source_corpus: str | None,
    ) -> PatternExtractionResponse:
        """Extract patterns from narrative text via LLM."""
        try:
            inference_request = build_narrative_analysis_request(
                story_text=text,
                source_corpus=source_corpus,
                generation_mode=generation_mode,
                default_model=self._inferencer.descriptor.default_model,
            )

            response = self._inferencer.generate_text(inference_request)
            analysis = self._parse_llm_json(response.content)

            if analysis is None:
                return PatternExtractionResponse(
                    status="failed",
                    project_id="",
                    error="Failed to parse LLM response as JSON",
                )

            return PatternExtractionResponse(
                status="completed",
                project_id="",
                extraction=PatternExtractionSummary(
                    source_corpus=analysis.source_corpus,
                    archetypal_patterns=len(analysis.archetypal_patterns),
                    narrative_structures=len(analysis.narrative_structures),
                    world_rules=len(analysis.world_rules),
                    symbolic_motifs=len(analysis.symbolic_motifs),
                ),
            )

        except InferenceBackendError as exc:
            return PatternExtractionResponse(
                status="failed",
                project_id="",
                error=f"LLM service unavailable: {exc.code}",
            )

    def _parse_llm_json(self, content: str) -> PatternExtractionAnalysis | None:
        """Extract JSON from LLM response and build analysis.

        Tries direct parse, then markdown fence extraction.
        Returns None if parsing fails.
        """
        stripped = content.strip()
        if not stripped:
            return None

        data: dict[str, Any] | None = None

        # Try direct JSON parse
        try:
            data = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try extracting from markdown fences
        if data is None:
            fenced = re.sub(
                r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE
            )
            fenced = fenced.strip()
            if fenced:
                try:
                    data = json.loads(fenced)
                except (json.JSONDecodeError, ValueError):
                    pass

        # Try finding balanced JSON object
        if data is None:
            first_brace = stripped.find("{")
            if first_brace != -1:
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
                        data = json.loads(stripped[first_brace : json_end + 1])
                    except (json.JSONDecodeError, ValueError):
                        pass

        if data is None:
            return None

        if not isinstance(data, dict):
            return None

        return self._build_analysis(data)

    def _build_analysis(self, data: dict[str, Any]) -> PatternExtractionAnalysis:
        """Build PatternExtractionAnalysis from parsed JSON data.

        Handles missing fields gracefully by using defaults.
        """

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

        archetypal_patterns = [
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

        narrative_structures = [
            NarrativeStructure(
                name=_to_str(s.get("name")),
                phases=_to_list(s.get("phases")),
                tension_curve=_to_str(s.get("tension_curve")),
                resolution_type=_to_str(s.get("resolution_type")),
            )
            for s in (data.get("narrative_structures") or [])
            if isinstance(s, dict)
        ]

        world_rules = [
            WorldRule(
                rule=_to_str(r.get("rule")),
                enforcement=_to_str(r.get("enforcement")),
                exceptions=_to_list(r.get("exceptions")),
            )
            for r in (data.get("world_rules") or [])
            if isinstance(r, dict)
        ]

        symbolic_motifs = [
            SymbolicMotif(
                symbol=_to_str(m.get("symbol")),
                meaning=_to_str(m.get("meaning")),
                narrative_function=_to_str(m.get("narrative_function")),
            )
            for m in (data.get("symbolic_motifs") or [])
            if isinstance(m, dict)
        ]

        # Narrative-specific fields
        np_data = data.get("narrative_pattern")
        narrative_pattern: NarrativePattern | None = None
        if isinstance(np_data, dict):
            narrative_pattern = NarrativePattern(
                pacing=_to_str(np_data.get("pacing")),
                chapter_structure=_to_str(np_data.get("chapter_structure")),
                conflict_type=_to_str(np_data.get("conflict_type")),
                dialogue_style=_to_str(np_data.get("dialogue_style")),
                scene_transition=_to_str(np_data.get("scene_transition")),
            )

        vp_data = data.get("voice_profile")
        voice_profile: VoiceProfile | None = None
        if isinstance(vp_data, dict):
            voice_profile = VoiceProfile(
                narrative_voice=_to_str(vp_data.get("narrative_voice")),
                sentence_rhythm=_to_str(vp_data.get("sentence_rhythm")),
                descriptive_density=_to_str(vp_data.get("descriptive_density")),
                humor_level=_to_str(vp_data.get("humor_level")),
                emotional_temperature=_to_str(
                    vp_data.get("emotional_temperature")
                ),
            )

        thematic_constraints = [
            ThematicConstraint(
                theme=_to_str(tc.get("theme")),
                moral_stance=_to_str(tc.get("moral_stance")),
                recurring_questions=_to_list(tc.get("recurring_questions")),
                forbidden_elements=_to_list(tc.get("forbidden_elements")),
            )
            for tc in (data.get("thematic_constraints") or [])
            if isinstance(tc, dict)
        ]

        key_entities = [
            StoryEntity(
                name=_to_str(e.get("name")),
                entity_type=_to_str(e.get("entity_type")),
                archetype=_to_str(e.get("archetype")),
                domain_or_power=_to_str(e.get("domain_or_power")),
                canonical_facts=_to_list(e.get("canonical_facts")),
            )
            for e in (data.get("key_entities") or [])
            if isinstance(e, dict)
        ]

        entity_relationships = [
            Relationship(
                source=_to_str(r.get("source")),
                target=_to_str(r.get("target")),
                relationship_type=_to_str(r.get("relationship_type")),
                description=_to_str(r.get("description")),
            )
            for r in (data.get("entity_relationships") or [])
            if isinstance(r, dict)
        ]

        return PatternExtractionAnalysis(
            source_type=_to_str(data.get("source_type"), "narrative"),
            source_corpus=_to_str(data.get("source_corpus")),
            generation_mode=data.get("generation_mode", "same_world")
            or "same_world",
            archetypal_patterns=archetypal_patterns,
            narrative_structures=narrative_structures,
            world_rules=world_rules,
            symbolic_motifs=symbolic_motifs,
            thematic_spine=_to_str(data.get("thematic_spine")),
            emotional_promise=_to_str(data.get("emotional_promise")),
            tone_and_voice_direction=_to_str(data.get("tone_and_voice_direction")),
            narrative_pattern=narrative_pattern,
            voice_profile=voice_profile,
            thematic_constraints=thematic_constraints,
            key_entities=key_entities,
            entity_relationships=entity_relationships,
        )

    def _create_and_persist(
        self,
        project_id: str | None,
        analysis: PatternExtractionAnalysis,
    ) -> str:
        """Create or validate project, persist extracted patterns in a transaction."""
        if project_id:
            try:
                self._project_service.get_project(project_id)
            except sqlite3.Error as exc:
                logger.error("DB error checking project %s: %s", project_id, exc)
                raise PatternExtractionError(
                    f"Database error while verifying project: {exc}"
                ) from exc
            except FileNotFoundError:
                raise PatternExtractionError(f"Project not found: {project_id}")
        else:
            from ..schemas.projects import ProjectCreateRequest

            create_request = ProjectCreateRequest(
                project_name=f"Narrative: {analysis.source_corpus or 'Extracted Patterns'}"
            )
            response = self._project_service.create_project(create_request)
            project_id = response.project_id

        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._repository.db_path, timeout=30)
        try:
            conn.execute("BEGIN")
            self._import_foundation(conn, project_id, analysis, now)
            self._import_world_bible(conn, project_id, analysis, now)
            self._import_entities(conn, project_id, analysis, now)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self._update_manifest(project_id, analysis)
        return project_id

    def _import_foundation(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: PatternExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert foundation_profiles header + foundation_revisions with narrative fields."""
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

        narrative_constraints: dict[str, Any] = {}

        if analysis.narrative_pattern:
            narrative_constraints["narrative_pattern"] = {
                "pacing": analysis.narrative_pattern.pacing,
                "chapter_structure": analysis.narrative_pattern.chapter_structure,
                "conflict_type": analysis.narrative_pattern.conflict_type,
                "dialogue_style": analysis.narrative_pattern.dialogue_style,
                "scene_transition": analysis.narrative_pattern.scene_transition,
            }

        if analysis.voice_profile:
            narrative_constraints["voice_profile"] = {
                "narrative_voice": analysis.voice_profile.narrative_voice,
                "sentence_rhythm": analysis.voice_profile.sentence_rhythm,
                "descriptive_density": analysis.voice_profile.descriptive_density,
                "humor_level": analysis.voice_profile.humor_level,
                "emotional_temperature": analysis.voice_profile.emotional_temperature,
            }

        if analysis.thematic_constraints:
            narrative_constraints["thematic_constraints"] = [
                {
                    "theme": tc.theme,
                    "moral_stance": tc.moral_stance,
                    "recurring_questions": tc.recurring_questions,
                    "forbidden_elements": tc.forbidden_elements,
                }
                for tc in analysis.thematic_constraints
            ]

        narrative_constraints_json = json.dumps(
            narrative_constraints, ensure_ascii=True, sort_keys=True
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
        analysis: PatternExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert world rules and symbolic motifs as world_bible_entries."""
        for rule in analysis.world_rules:
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
                    f"Rule: {rule.rule}",
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
                    "motif",
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

    def _import_entities(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: PatternExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert key entities as character_profiles and relationships as edges."""
        for entity in analysis.key_entities:
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
                    "narrative_entity",
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

    def _update_manifest(self, project_id: str, analysis: PatternExtractionAnalysis) -> None:
        """Update manifest.json with narrative source corpus and generation mode."""
        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Manifest not found for project %s, skipping metadata update", project_id)
            return

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
            return

        if "config" not in manifest_data:
            manifest_data["config"] = {}

        if analysis.source_type:
            manifest_data["config"]["pattern_source_type"] = analysis.source_type
        if analysis.source_corpus:
            manifest_data["config"]["pattern_source_corpus"] = analysis.source_corpus
        if analysis.generation_mode:
            manifest_data["config"]["pattern_generation_mode"] = analysis.generation_mode

        try:
            manifest_path.write_text(
                json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write manifest for project %s: %s", project_id, exc)


def _hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value."""
    raw = f"pattern-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"pattern-{prefix}-{short_hash}"
