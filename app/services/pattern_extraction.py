from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.story_development import StoryDevelopmentRepository
from ..utils.db_inserts import (
    hash_id,
    insert_character_profile,
    insert_foundation_profile,
    insert_relationship_edge,
    insert_world_bible_entry,
    json_safe,
    next_revision_number,
    update_foundation_revision_id,
)
from ..utils.json_extract import extract_json
from ..utils.manifest import update_manifest as _update_manifest_util
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
from .mythos_extraction import MythosExtractionService
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

    def extract_with_progress(
        self,
        text: str,
        source_type: str,
        generation_mode: str,
        project_id: str | None,
        source_corpus: str | None,
        on_progress: Callable[[str, dict[str, Any]], None],
    ) -> PatternExtractionResponse:
        """Extract patterns with progress callbacks for async operation."""
        if source_type == "mythology":
            mythos_request = MythosExtractionRequest(
                text=text,
                generation_mode=generation_mode,
                project_id=project_id,
                source_corpus=source_corpus,
            )
            mythos_response = self._mythos_service.extract_with_progress(
                mythos_request, on_progress
            )

            summary: PatternExtractionSummary | None = None
            if (
                mythos_response.status == "completed"
                and mythos_response.extraction is not None
            ):
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

        try:
            on_progress("creating_project", {})
            if project_id:
                try:
                    self._project_service.get_project(project_id)
                except sqlite3.Error as exc:
                    raise PatternExtractionError(
                        f"Database error while verifying project: {exc}"
                    ) from exc
                except FileNotFoundError:
                    raise PatternExtractionError(
                        f"Project not found: {project_id}"
                    )
            else:
                from ..schemas.projects import ProjectCreateRequest

                create_request = ProjectCreateRequest(
                    project_name=f"Narrative: {source_corpus or 'Extracted Patterns'}"
                )
                response = self._project_service.create_project(create_request)
                project_id = response.project_id

            on_progress("analyzing", {})
            inference_request = build_narrative_analysis_request(
                story_text=text,
                source_corpus=source_corpus,
                generation_mode=generation_mode,
                default_model=self._inferencer.descriptor.default_model,
            )
            response = self._inferencer.generate_text(inference_request)
            analysis = self._parse_llm_json(response.content)
            if analysis is None:
                raise PatternExtractionError(
                    "Failed to parse LLM response as JSON"
                )

            on_progress("persisting", {})
            now = datetime.now(timezone.utc).isoformat()
            conn = sqlite3.connect(self._repository.db_path, timeout=30)
            try:
                conn.execute("BEGIN IMMEDIATE")
                self._import_foundation(conn, project_id, analysis, now)
                self._import_world_bible(conn, project_id, analysis, now)
                self._import_entities(conn, project_id, analysis, now)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

            on_progress("updating_manifest", {})
            self._update_manifest(project_id, analysis)

            return PatternExtractionResponse(
                status="completed",
                project_id=project_id,
                extraction=PatternExtractionSummary(
                    source_corpus=analysis.source_corpus,
                    archetypal_patterns=len(analysis.archetypal_patterns),
                    narrative_structures=len(analysis.narrative_structures),
                    world_rules=len(analysis.world_rules),
                    symbolic_motifs=len(analysis.symbolic_motifs),
                ),
            )
        except PatternExtractionError as exc:
            return PatternExtractionResponse(
                status="failed",
                project_id=project_id or "",
                error=str(exc),
            )
        except InferenceBackendError as exc:
            return PatternExtractionResponse(
                status="failed",
                project_id=project_id or "",
                error=f"LLM service unavailable: {exc.code}",
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

        NOTE: The concatenated text is truncated to 24,000 chars for single-pass
        LLM analysis. For projects with many chapters, only the earliest content
        may reach the LLM. Consider using the extraction endpoint per-chapter
        or in batches for large projects.
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
        """Extract JSON from LLM response and build analysis."""
        data = extract_json(content)
        if data is None:
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
            conn.execute("BEGIN IMMEDIATE")
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
        next_rev = next_revision_number(conn, project_id)

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

        narrative_constraints_json = json_safe(narrative_constraints)

        revision_id = insert_foundation_profile(
            conn, project_id, now, next_rev,
            thematic_spine=analysis.thematic_spine or None,
            emotional_promise=analysis.emotional_promise or None,
            tone_direction=analysis.tone_and_voice_direction or None,
            constraints_json=narrative_constraints_json,
        )
        update_foundation_revision_id(conn, project_id, revision_id, now)

    def _import_world_bible(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: PatternExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert world rules and symbolic motifs as world_bible_entries."""
        for rule in analysis.world_rules:
            insert_world_bible_entry(
                conn, project_id, "concept", f"Rule: {rule.rule}",
                summary=rule.enforcement if rule.enforcement else None,
                canonical_facts_json=json_safe(rule.exceptions or []),
            )

        for motif in analysis.symbolic_motifs:
            summary_parts = [motif.meaning]
            if motif.narrative_function:
                summary_parts.append(f"Narrative function: {motif.narrative_function}")
            summary = ". ".join(summary_parts)
            insert_world_bible_entry(
                conn, project_id, "motif", f"Motif: {motif.symbol}",
                summary=summary if summary else None,
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
            char_id = hash_id("pattern-entity", entity.name)
            insert_character_profile(
                conn, char_id, project_id,
                display_name=entity.name, role_in_story="narrative_entity",
                archetype=entity.archetype or None,
                primary_strength=entity.domain_or_power or None,
                continuity_facts_json=json_safe(entity.canonical_facts or []),
            )

        for rel in analysis.entity_relationships:
            edge_id = hash_id("pattern-edge", f"{rel.source}-{rel.target}")
            insert_relationship_edge(
                conn, edge_id, project_id,
                source_character_id=hash_id("pattern-entity", rel.source),
                target_character_id=hash_id("pattern-entity", rel.target),
                relation_kind=rel.relationship_type or "related",
                summary=rel.description or "",
            )

    def _update_manifest(self, project_id: str, analysis: PatternExtractionAnalysis) -> None:
        """Update manifest.json with narrative source corpus and generation mode."""
        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
        config_updates: dict[str, str] = {}
        if analysis.source_type:
            config_updates["pattern_source_type"] = analysis.source_type
        if analysis.source_corpus:
            config_updates["pattern_source_corpus"] = analysis.source_corpus
        if analysis.generation_mode:
            config_updates["pattern_generation_mode"] = analysis.generation_mode
        _update_manifest_util(project_dir, project_id, config_updates)



