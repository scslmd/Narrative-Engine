from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

        parsed = extract_json(response.content)
        if parsed is None:
            raise MythosExtractionError("Failed to parse LLM response as JSON")
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
            conn.execute("BEGIN IMMEDIATE")
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
        next_rev = next_revision_number(conn, project_id)

        narrative_constraints_json = json_safe(
            {
                "archetypal_patterns": [
                    {"name": p.name, "description": p.description, "character_type": p.character_type}
                    for p in analysis.archetypal_patterns
                ],
                "narrative_structures": [
                    {"name": s.name, "phases": s.phases}
                    for s in analysis.narrative_structures
                ],
            }
        )

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
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert cosmic rules and symbolic motifs as world_bible_entries."""
        for rule in analysis.cosmic_rules:
            insert_world_bible_entry(
                conn, project_id, "concept", f"Cosmic Rule: {rule.rule}",
                summary=rule.enforcement if rule.enforcement else None,
                canonical_facts_json=json_safe(rule.exceptions or []),
            )

        for motif in analysis.symbolic_motifs:
            summary_parts = [motif.meaning]
            if motif.narrative_function:
                summary_parts.append(f"Narrative function: {motif.narrative_function}")
            summary = ". ".join(summary_parts)
            insert_world_bible_entry(
                conn, project_id, "concept", f"Motif: {motif.symbol}",
                summary=summary if summary else None,
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
            char_id = hash_id("mythos-archetype", pattern.name)
            insert_character_profile(
                conn, char_id, project_id,
                display_name=pattern.character_type or pattern.name,
                role_in_story="archetype", archetype=pattern.name,
                backstory_summary=pattern.description or None,
                arc_stage_notes=json_safe(pattern.narrative_beats or []),
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
                char_id = hash_id("mythos-entity", entity.name)
                insert_character_profile(
                    conn, char_id, project_id,
                    display_name=entity.name, role_in_story="mythos_entity",
                    archetype=entity.archetype or None,
                    primary_strength=entity.domain_or_power or None,
                    continuity_facts_json=json_safe(entity.canonical_facts or []),
                )
            else:
                insert_world_bible_entry(
                    conn, project_id, entity.entity_type or "concept", entity.name,
                    summary=entity.domain_or_power or None,
                    canonical_facts_json=json_safe(entity.canonical_facts or []),
                )

        for rel in analysis.entity_relationships:
            edge_id = hash_id("mythos-edge", f"{rel.source}-{rel.target}")
            insert_relationship_edge(
                conn, edge_id, project_id,
                source_character_id=hash_id("mythos-entity", rel.source),
                target_character_id=hash_id("mythos-entity", rel.target),
                relation_kind=rel.relationship_type or "related",
                summary=rel.description or "",
            )

    def _update_manifest(self, project_id: str, analysis: MythosExtractionAnalysis) -> None:
        """Update manifest.json with mythos source corpus and generation mode."""
        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
        config_updates: dict[str, str] = {}
        if analysis.source_corpus:
            config_updates["mythos_source_corpus"] = analysis.source_corpus
        if analysis.generation_mode:
            config_updates["mythos_generation_mode"] = analysis.generation_mode
        _update_manifest_util(project_dir, project_id, config_updates)


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
