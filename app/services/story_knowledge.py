from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from uuid import uuid4

from app.persistence.story_development import RelationshipEdgeRecord, StoryDevelopmentRepository
from app.schemas import (
    ArcCandidate,
    ArcSelection,
    ArcStageMap,
    CharacterProfile,
    RelationshipEdge,
    StoryDecisionChangeType,
    StoryDecisionNodeType,
    StoryObjectType,
    WorldBibleEntry,
)


@dataclass(slots=True)
class ArcCandidateComparison:
    candidate: ArcCandidate
    rank: int
    score: tuple[int, int, int, int]
    notes: tuple[str, ...]


class StoryKnowledgeServiceError(ValueError):
    pass


class StoryKnowledgeNotFoundError(StoryKnowledgeServiceError):
    pass


class StoryKnowledgeValidationError(StoryKnowledgeServiceError):
    pass


class StoryKnowledgeService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def upsert_character_profile(
        self,
        project_id: str,
        *,
        character_id: str,
        display_name: str,
        role_in_story: str,
        archetype: str,
        external_goal: str,
        internal_need: str,
        misbelief_or_wound: str,
        core_fear: str,
        primary_strength: str,
        fatal_flaw_or_limitation: str,
        contradictions: Sequence[str] | None = None,
        backstory_summary: str,
        voice_notes: str,
        secrets: Sequence[str] | None = None,
        values: Sequence[str] | None = None,
        taboos: Sequence[str] | None = None,
        change_axis: str,
        arc_stage_notes: Sequence[str] | None = None,
        continuity_facts: Sequence[str] | None = None,
        writer_notes: str | None = None,
    ) -> CharacterProfile:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_character_id = self._normalize_text(character_id, field_name="character_id")
        normalized_arc_stage_notes = self._normalize_text_list(arc_stage_notes, field_name="arc_stage_notes")
        record = self.repository.upsert_character_profile(
            project_id=normalized_project_id,
            character_id=normalized_character_id,
            display_name=self._normalize_text(display_name, field_name="display_name"),
            role_in_story=self._normalize_text(role_in_story, field_name="role_in_story"),
            archetype=self._lenient_text(archetype, field_name="archetype"),
            external_goal=self._lenient_text(external_goal, field_name="external_goal"),
            internal_need=self._lenient_text(internal_need, field_name="internal_need"),
            misbelief_or_wound=self._lenient_text(misbelief_or_wound, field_name="misbelief_or_wound"),
            core_fear=self._lenient_text(core_fear, field_name="core_fear"),
            primary_strength=self._lenient_text(primary_strength, field_name="primary_strength"),
            fatal_flaw_or_limitation=self._lenient_text(
                fatal_flaw_or_limitation,
                field_name="fatal_flaw_or_limitation",
            ),
            contradictions=self._normalize_text_list(contradictions, field_name="contradictions"),
            backstory_summary=self._lenient_text(backstory_summary, field_name="backstory_summary"),
            voice_notes=self._lenient_text(voice_notes, field_name="voice_notes"),
            relationship_map=[
                edge.edge_id
                for edge in self.repository.list_relationship_edges_for_character(normalized_project_id, normalized_character_id)
            ],
            secrets=self._normalize_text_list(secrets, field_name="secrets"),
            values=self._normalize_text_list(values, field_name="values"),
            taboos=self._normalize_text_list(taboos, field_name="taboos"),
            change_axis=self._lenient_text(change_axis, field_name="change_axis"),
            arc_stage_notes="\n".join(normalized_arc_stage_notes) if normalized_arc_stage_notes else None,
            continuity_facts=self._normalize_text_list(continuity_facts, field_name="continuity_facts"),
            writer_notes=self._normalize_optional_text(writer_notes, field_name="writer_notes"),
        )
        return self._character_profile_from_record(record)

    def upsert_relationship_edge(
        self,
        project_id: str,
        *,
        source_character_id: str,
        target_character_id: str,
        relation_kind: str,
        summary: str,
        tension: str | None = None,
        notes: str | None = None,
        edge_id: str | None = None,
    ) -> RelationshipEdge:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        source_id = self._normalize_text(source_character_id, field_name="source_character_id")
        target_id = self._normalize_text(target_character_id, field_name="target_character_id")
        record = self.repository.upsert_relationship_edge(
            project_id=normalized_project_id,
            source_character_id=source_id,
            target_character_id=target_id,
            relation_kind=self._normalize_text(relation_kind, field_name="relation_kind"),
            summary=self._normalize_text(summary, field_name="summary"),
            tension=self._normalize_optional_text(tension, field_name="tension"),
            notes=self._normalize_optional_text(notes, field_name="notes"),
            edge_id=self._normalize_optional_text(edge_id, field_name="edge_id"),
        )
        return self._relationship_edge_from_record(record)

    def upsert_world_bible_entry(
        self,
        project_id: str,
        *,
        entry_type: str,
        title: str,
        summary: str,
        canonical_facts: Sequence[str] | None = None,
        related_character_ids: Sequence[str] | None = None,
        source_artifacts: Sequence[str] | None = None,
        visibility_scope: str = "project",
        continuity_warnings: Sequence[str] | None = None,
        writer_notes: str | None = None,
    ) -> WorldBibleEntry:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        record = self.repository.upsert_world_bible_entry(
            project_id=normalized_project_id,
            entry_type=self._normalize_text(entry_type, field_name="entry_type"),
            title=self._normalize_text(title, field_name="title"),
            summary=self._normalize_text(summary, field_name="summary"),
            canonical_facts=self._normalize_text_list(canonical_facts, field_name="canonical_facts"),
            related_character_ids=self._normalize_text_list(
                related_character_ids,
                field_name="related_character_ids",
            ),
            source_artifacts=self._normalize_text_list(source_artifacts, field_name="source_artifacts"),
            visibility_scope=self._normalize_text(visibility_scope, field_name="visibility_scope"),
            continuity_warnings=self._normalize_text_list(
                continuity_warnings,
                field_name="continuity_warnings",
            ),
            writer_notes=self._normalize_optional_text(writer_notes, field_name="writer_notes"),
        )
        return self._world_bible_entry_from_record(record)

    def compare_arc_candidates(
        self,
        project_id: str,
        *,
        candidates: Sequence[ArcCandidate | Mapping[str, Any] | str],
    ) -> tuple[ArcCandidateComparison, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        candidate_records = [self._resolve_and_persist_arc_candidate(normalized_project_id, candidate) for candidate in candidates]
        unique_candidates = self._unique_candidates(candidate_records)
        if len(unique_candidates) < 2:
            raise StoryKnowledgeValidationError("At least two arc candidates are required.")

        scored = [
            (
                self._candidate_score(candidate),
                candidate,
                self._candidate_notes(candidate),
            )
            for candidate in unique_candidates
        ]
        scored.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2], item[0][3], item[1].arc_id))
        comparisons = tuple(
            ArcCandidateComparison(
                candidate=candidate,
                rank=index,
                score=score,
                notes=notes,
            )
            for index, (score, candidate, notes) in enumerate(scored, start=1)
        )
        comparison_id = self._comparison_id(normalized_project_id)
        self.repository.upsert_arc_comparison(
            project_id=normalized_project_id,
            comparison_id=comparison_id,
            ranked_candidates=[
                {
                    "candidate": {
                        "arc_id": comparison.candidate.arc_id,
                        "project_id": comparison.candidate.project_id,
                        "name": comparison.candidate.name,
                        "summary": comparison.candidate.summary,
                        "stage_map_notes": list(comparison.candidate.stage_map_notes),
                        "fit_notes": list(comparison.candidate.fit_notes),
                        "tags": list(comparison.candidate.tags),
                    },
                    "rank": comparison.rank,
                    "score": list(comparison.score),
                    "notes": list(comparison.notes),
                }
                for comparison in comparisons
            ],
            review_notes=[f"Arc comparison stored for {normalized_project_id}."],
        )
        return comparisons

    def select_arc_candidate(
        self,
        project_id: str,
        *,
        selected_arc: ArcCandidate | Mapping[str, Any] | str,
        rejected_arc_ids: Sequence[str] | None = None,
        comparison_notes: Sequence[str] | None = None,
        stage_map: ArcStageMap | Mapping[str, Any] | None = None,
    ) -> ArcSelection:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        candidate = self._resolve_and_persist_arc_candidate(normalized_project_id, selected_arc)
        rejected_ids = self._normalize_text_list(rejected_arc_ids, field_name="rejected_arc_ids")
        if candidate.arc_id in rejected_ids:
            raise StoryKnowledgeValidationError("Selected arc cannot be rejected.")

        normalized_stage_map = self._resolve_stage_map(normalized_project_id, candidate.arc_id, stage_map)
        if normalized_stage_map is None:
            try:
                normalized_stage_map = self._arc_stage_map_from_record(
                    self.repository.get_arc_stage_map(normalized_project_id, arc_id=candidate.arc_id)
                )
            except KeyError:
                normalized_stage_map = None

        notes = self._normalize_text_list(comparison_notes, field_name="comparison_notes")
        if not notes:
            notes = list(self._comparison_notes_for_arc(normalized_project_id, candidate.arc_id))
        if not notes:
            notes = list(self._candidate_notes(candidate))

        selection_id = self._selection_id(normalized_project_id)
        selection_record = self.repository.upsert_arc_selection(
            project_id=normalized_project_id,
            selection_id=selection_id,
            selected_arc=candidate,
            rejected_arc_ids=rejected_ids,
            comparison_notes=notes,
            comparison_record_ids=self._comparison_record_ids_for_selection(normalized_project_id),
            stage_map=normalized_stage_map,
        )
        self._record_story_decision_for_selection(
            project_id=normalized_project_id,
            selection_id=selection_id,
            selected_arc=candidate,
            comparison_record_ids=selection_record.comparison_record_ids,
            rejected_arc_ids=rejected_ids,
            prior_selection=self._previous_arc_selection(normalized_project_id, selection_id),
        )
        return self._selection_from_record(selection_record)

    def update_arc_stage_map(
        self,
        project_id: str,
        *,
        arc_id: str,
        stage_kinds: Sequence[str],
        notes: str | None = None,
    ) -> ArcStageMap:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_arc_id = self._normalize_text(arc_id, field_name="arc_id")
        try:
            self.repository.get_arc_candidate(normalized_project_id, arc_id=normalized_arc_id)
        except KeyError as exc:
            raise StoryKnowledgeNotFoundError(normalized_arc_id) from exc

        stage_map_record = self.repository.upsert_arc_stage_map(
            project_id=normalized_project_id,
            arc_id=normalized_arc_id,
            stage_kinds=self._normalize_text_list(stage_kinds, field_name="stage_kinds"),
            notes=self._normalize_optional_text(notes, field_name="notes"),
        )
        stage_map = self._arc_stage_map_from_record(stage_map_record)

        matched_selection = False
        for selection in self.repository.list_arc_selections(normalized_project_id):
            if selection.selected_arc_id != normalized_arc_id:
                continue
            self.repository.upsert_arc_selection(
                project_id=normalized_project_id,
                selection_id=selection.selection_id,
                selected_arc=selection.selected_arc,
                rejected_arc_ids=selection.rejected_arc_ids,
                comparison_notes=selection.comparison_notes,
                comparison_record_ids=selection.comparison_record_ids,
                stage_map=stage_map_record,
            )
            matched_selection = True
        if matched_selection:
            self._record_story_decision_for_stage_map(
                project_id=normalized_project_id,
                selected_arc_id=normalized_arc_id,
                stage_map=stage_map_record,
                parent_node_id=self._latest_decision_node_id(normalized_project_id),
            )
        return stage_map

    def get_character_profile(self, project_id: str, character_id: str) -> CharacterProfile:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_character_id = self._normalize_text(character_id, field_name="character_id")
        try:
            record = self.repository.get_character_profile(normalized_character_id)
        except KeyError as exc:
            raise StoryKnowledgeNotFoundError(normalized_character_id) from exc
        if record.project_id != normalized_project_id:
            raise StoryKnowledgeNotFoundError(normalized_character_id)
        return self._character_profile_from_record(record)

    def list_character_profiles(self, project_id: str) -> tuple[CharacterProfile, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        relationship_edges_by_character = self._group_relationship_edges_by_character(
            self.repository.list_relationship_edges(normalized_project_id)
        )
        profiles = [
            self._character_profile_from_record(
                record,
                relationship_edges=relationship_edges_by_character.get(record.character_id, ()),
            )
            for record in self.repository.list_character_profiles(normalized_project_id)
        ]
        return tuple(sorted(profiles, key=lambda profile: (profile.display_name.casefold(), profile.character_id)))

    def get_world_bible_entry(self, project_id: str, *, entry_type: str, title: str) -> WorldBibleEntry:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        try:
            record = self.repository.get_world_bible_entry(
                normalized_project_id,
                entry_type=self._normalize_text(entry_type, field_name="entry_type"),
                title=self._normalize_text(title, field_name="title"),
            )
        except KeyError as exc:
            raise StoryKnowledgeNotFoundError(self._world_entry_id(normalized_project_id, entry_type, title)) from exc
        return self._world_bible_entry_from_record(record)

    def list_world_bible_entries(self, project_id: str) -> tuple[WorldBibleEntry, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        entries = [
            self._world_bible_entry_from_record(record)
            for record in self.repository.list_world_bible_entries(normalized_project_id)
        ]
        return tuple(sorted(entries, key=lambda entry: (entry.entry_type.casefold(), entry.title.casefold(), entry.entry_id)))

    def list_arc_comparisons(self, project_id: str) -> tuple[tuple[ArcCandidateComparison, ...], ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        comparisons: list[tuple[ArcCandidateComparison, ...]] = []
        for record in self.repository.list_arc_comparisons(normalized_project_id):
            comparisons.append(self._comparison_record_to_comparisons(record))
        return tuple(comparisons)

    def list_arc_selections(self, project_id: str) -> tuple[ArcSelection, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        return tuple(
            self._selection_from_record(record)
            for record in self.repository.list_arc_selections(normalized_project_id)
        )

    def list_relationship_edges_for_character(self, project_id: str, character_id: str) -> tuple[RelationshipEdge, ...]:
        """List all relationship edges for a specific character.
        
        Args:
            project_id: The project identifier.
            character_id: The character identifier.
            
        Returns:
            A tuple of RelationshipEdge objects sorted by edge_id.
            
        Raises:
            StoryKnowledgeValidationError: If project_id or character_id are invalid.
        """
        if not project_id or not project_id.strip():
            raise StoryKnowledgeValidationError("project_id cannot be empty.")
        if not character_id or not character_id.strip():
            raise StoryKnowledgeValidationError("character_id cannot be empty.")
        
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_character_id = self._normalize_text(character_id, field_name="character_id")
        edges = [
            self._relationship_edge_from_record(record)
            for record in self.repository.list_relationship_edges_for_character(normalized_project_id, normalized_character_id)
        ]
        return tuple(sorted(edges, key=lambda edge: edge.edge_id))

    def list_all_relationship_edges(self, project_id: str) -> tuple[RelationshipEdge, ...]:
        """List all relationship edges for a project.
        
        Args:
            project_id: The project identifier.
            
        Returns:
            A tuple of RelationshipEdge objects sorted by edge_id.
        """
        if not project_id or not project_id.strip():
            raise StoryKnowledgeValidationError("project_id cannot be empty.")
        
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        edges = [
            self._relationship_edge_from_record(record)
            for record in self.repository.list_relationship_edges(normalized_project_id)
        ]
        return tuple(sorted(edges, key=lambda edge: edge.edge_id))

    def delete_relationship_edge(self, project_id: str, edge_id: str) -> None:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_edge_id = self._normalize_text(edge_id, field_name="edge_id")
        try:
            self.repository.delete_relationship_edge(normalized_project_id, edge_id=normalized_edge_id)
        except KeyError:
            raise StoryKnowledgeNotFoundError(normalized_edge_id)

    def upsert_arc_candidate(
        self,
        project_id: str,
        *,
        arc_id: str,
        name: str,
        summary: str,
        stage_map_notes: Sequence[str] = (),
        fit_notes: Sequence[str] = (),
        tags: Sequence[str] = (),
    ) -> ArcCandidate:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_arc_id = self._normalize_text(arc_id, field_name="arc_id")
        candidate = ArcCandidate(
            arc_id=normalized_arc_id,
            project_id=normalized_project_id,
            name=name,
            summary=summary,
            stage_map_notes=list(stage_map_notes),
            fit_notes=list(fit_notes),
            tags=list(tags),
        )
        record = self.repository.upsert_arc_candidate(
            project_id=normalized_project_id,
            arc_id=normalized_arc_id,
            name=candidate.name,
            summary=candidate.summary,
            stage_map_notes=list(candidate.stage_map_notes),
            fit_notes=list(candidate.fit_notes),
            tags=list(candidate.tags),
        )
        return self._arc_candidate_from_record(record)

    def list_arc_candidates(self, project_id: str) -> tuple[ArcCandidate, ...]:
        """List all arc candidates for a project.
        
        Args:
            project_id: The project identifier.
            
        Returns:
            A tuple of ArcCandidate objects sorted by name then arc_id.
            
        Raises:
            StoryKnowledgeValidationError: If project_id is invalid.
        """
        if not project_id or not project_id.strip():
            raise StoryKnowledgeValidationError("project_id cannot be empty.")
        
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        candidates = [
            self._arc_candidate_from_record(record)
            for record in self.repository.list_arc_candidates(normalized_project_id)
        ]
        return tuple(sorted(candidates, key=lambda candidate: (candidate.name.casefold(), candidate.arc_id)))

    def list_arc_stage_maps(self, project_id: str) -> tuple[ArcStageMap, ...]:
        """List all arc stage maps for a project.
        
        Args:
            project_id: The project identifier.
            
        Returns:
            A tuple of ArcStageMap objects sorted by arc_id.
            
        Raises:
            StoryKnowledgeValidationError: If project_id is invalid.
        """
        if not project_id or not project_id.strip():
            raise StoryKnowledgeValidationError("project_id cannot be empty.")
        
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        stage_maps = [
            self._arc_stage_map_from_record(record)
            for record in self.repository.list_arc_stage_maps(normalized_project_id)
        ]
        return tuple(sorted(stage_maps, key=lambda sm: sm.arc_id))

    def get_arc_stage_map(self, project_id: str, *, arc_id: str) -> ArcStageMap | None:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_arc_id = self._normalize_text(arc_id, field_name="arc_id")
        try:
            record = self.repository.get_arc_stage_map(normalized_project_id, arc_id=normalized_arc_id)
        except KeyError:
            return None
        return self._arc_stage_map_from_record(record)

    def get_arc_selection(self, project_id: str, selection_id: str) -> ArcSelection | None:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_selection_id = self._normalize_text(selection_id, field_name="selection_id")
        try:
            record = self.repository.get_arc_selection(normalized_project_id, selection_id=normalized_selection_id)
        except KeyError:
            return None
        return self._selection_from_record(record)

    def delete_arc_selection(self, project_id: str, selection_id: str) -> None:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_selection_id = self._normalize_text(selection_id, field_name="selection_id")
        try:
            self.repository.delete_arc_selection(normalized_project_id, selection_id=normalized_selection_id)
        except KeyError:
            raise StoryKnowledgeNotFoundError(normalized_selection_id)

    def _update_selection_notes(self, project_id: str, selection_id: str, comparison_notes: list[str]) -> ArcSelection:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_selection_id = self._normalize_text(selection_id, field_name="selection_id")
        record = self.repository.get_arc_selection(normalized_project_id, selection_id=normalized_selection_id)
        updated = self.repository.update_arc_selection_notes(
            project_id=normalized_project_id,
            selection_id=normalized_selection_id,
            comparison_notes=comparison_notes,
        )
        return self._selection_from_record(updated)

    def _resolve_and_persist_arc_candidate(
        self,
        project_id: str,
        candidate: ArcCandidate | Mapping[str, Any] | str,
    ) -> ArcCandidate:
        if isinstance(candidate, str):
            normalized_arc_id = self._normalize_text(candidate, field_name="arc_id")
            try:
                record = self.repository.get_arc_candidate(project_id, arc_id=normalized_arc_id)
            except KeyError as exc:
                raise StoryKnowledgeNotFoundError(normalized_arc_id) from exc
            if record.project_id != project_id:
                raise StoryKnowledgeNotFoundError(normalized_arc_id)
            return self._arc_candidate_from_record(record)

        normalized = self._arc_candidate_schema(candidate)
        if normalized.project_id != project_id:
            raise StoryKnowledgeValidationError("Arc candidate project_id must match the selected project.")
        record = self.repository.upsert_arc_candidate(
            project_id=project_id,
            arc_id=normalized.arc_id,
            name=normalized.name,
            summary=normalized.summary,
            stage_map_notes=list(normalized.stage_map_notes),
            fit_notes=list(normalized.fit_notes),
            tags=list(normalized.tags),
        )
        return self._arc_candidate_from_record(record)

    def _arc_candidate_schema(self, candidate: ArcCandidate | Mapping[str, Any]) -> ArcCandidate:
        if isinstance(candidate, ArcCandidate):
            return candidate
        payload = {
            key: candidate[key]
            for key in ("arc_id", "project_id", "name", "summary", "stage_map_notes", "fit_notes", "tags")
            if key in candidate
        }
        return ArcCandidate.model_validate(payload)

    def _candidate_score(self, candidate: ArcCandidate) -> tuple[int, int, int, int]:
        return (
            len(candidate.stage_map_notes),
            len(candidate.fit_notes),
            len(candidate.tags),
            -len(candidate.summary.split()),
        )

    def _candidate_notes(self, candidate: ArcCandidate) -> tuple[str, ...]:
        notes = [
            f"{candidate.name}: {len(candidate.fit_notes)} fit note(s), {len(candidate.stage_map_notes)} stage-map note(s), {len(candidate.tags)} tag(s)."
        ]
        if candidate.fit_notes:
            notes.append(f"Fit notes: {', '.join(candidate.fit_notes)}")
        if candidate.stage_map_notes:
            notes.append(f"Stage map notes: {', '.join(candidate.stage_map_notes)}")
        if candidate.tags:
            notes.append(f"Tags: {', '.join(candidate.tags)}")
        return tuple(notes)

    def _comparison_notes_for_arc(self, project_id: str, arc_id: str) -> tuple[str, ...]:
        for record in reversed(self.repository.list_arc_comparisons(project_id)):
            for ranked_candidate in record.ranked_candidates:
                if ranked_candidate.candidate.arc_id == arc_id:
                    return tuple(ranked_candidate.notes)
        try:
            return self._candidate_notes(
                self._arc_candidate_from_record(self.repository.get_arc_candidate(project_id, arc_id=arc_id))
            )
        except KeyError:
            return ()

    def _resolve_stage_map(
        self,
        project_id: str,
        arc_id: str,
        stage_map: ArcStageMap | Mapping[str, Any] | None,
    ) -> ArcStageMap | None:
        if stage_map is None:
            return None
        normalized = stage_map if isinstance(stage_map, ArcStageMap) else self._arc_stage_map_schema(stage_map)
        if normalized.arc_id != arc_id:
            raise StoryKnowledgeValidationError("stage_map.arc_id must match the selected arc.")
        if normalized.project_id != project_id:
            raise StoryKnowledgeValidationError("stage_map.project_id must match the selected project.")
        return normalized

    def _arc_stage_map_schema(self, stage_map: ArcStageMap | Mapping[str, Any]) -> ArcStageMap:
        if isinstance(stage_map, ArcStageMap):
            return stage_map
        payload = {
            key: stage_map[key]
            for key in ("arc_stage_map_id", "project_id", "arc_id", "stage_kinds", "notes")
            if key in stage_map
        }
        return ArcStageMap.model_validate(payload)

    def _selection_id(self, project_id: str) -> str:
        return f"{self._normalize_text(project_id, field_name='project_id')}:selection:{uuid4().hex}"

    def _world_entry_id(self, project_id: str, entry_type: str, title: str) -> str:
        return f"{self._normalize_text(project_id, field_name='project_id')}:{self._normalize_text(entry_type, field_name='entry_type')}:{self._normalize_text(title, field_name='title')}"

    def _relationship_edge_from_record(self, record) -> RelationshipEdge:
        return RelationshipEdge(
            edge_id=record.edge_id,
            source_character_id=record.source_character_id,
            target_character_id=record.target_character_id,
            relation_kind=record.relation_kind,
            summary=record.summary,
            tension=record.tension,
            notes=record.notes,
        )

    def _character_profile_from_record(
        self,
        record,
        *,
        relationship_edges: Sequence[RelationshipEdgeRecord] | None = None,
    ) -> CharacterProfile:
        arc_stage_notes = [line for line in (record.arc_stage_notes or "").splitlines() if line.strip()]
        edge_records = (
            list(relationship_edges)
            if relationship_edges is not None
            else self.repository.list_relationship_edges_for_character(record.project_id, record.character_id)
        )
        return CharacterProfile(
            character_id=record.character_id,
            project_id=record.project_id,
            display_name=record.display_name,
            role_in_story=record.role_in_story or "",
            archetype=record.archetype or "",
            external_goal=record.external_goal or "",
            internal_need=record.internal_need or "",
            misbelief_or_wound=record.misbelief_or_wound or "",
            core_fear=record.core_fear or "",
            primary_strength=record.primary_strength or "",
            fatal_flaw_or_limitation=record.fatal_flaw_or_limitation or "",
            contradictions=list(record.contradictions),
            backstory_summary=record.backstory_summary or "",
            voice_notes=record.voice_notes or "",
            relationship_edges=[
                self._relationship_edge_from_record(edge_record)
                for edge_record in edge_records
            ],
            secrets=list(record.secrets),
            values=list(record.values),
            taboos=list(record.taboos),
            change_axis=record.change_axis or "",
            arc_stage_notes=arc_stage_notes,
            continuity_facts=list(record.continuity_facts),
            writer_notes=record.writer_notes,
        )

    def _world_bible_entry_from_record(self, record) -> WorldBibleEntry:
        return WorldBibleEntry(
            entry_id=self._world_entry_id(record.project_id, record.entry_type, record.title),
            project_id=record.project_id,
            entry_type=record.entry_type,
            title=record.title,
            summary=record.summary or "",
            canonical_facts=list(record.canonical_facts),
            related_character_ids=list(record.related_character_ids),
            source_artifacts=list(record.source_artifacts),
            visibility_scope=record.visibility_scope,
            continuity_warnings=list(record.continuity_warnings),
            writer_notes=record.writer_notes,
        )

    def _arc_candidate_from_record(self, record) -> ArcCandidate:
        return ArcCandidate(
            arc_id=record.arc_id,
            project_id=record.project_id,
            name=record.name,
            summary=record.summary,
            stage_map_notes=list(record.stage_map_notes),
            fit_notes=list(record.fit_notes),
            tags=list(record.tags),
        )

    def _arc_stage_map_from_record(self, record) -> ArcStageMap:
        return ArcStageMap(
            arc_stage_map_id=record.arc_stage_map_id,
            project_id=record.project_id,
            arc_id=record.arc_id,
            stage_kinds=list(record.stage_kinds),
            notes=record.notes,
        )

    def _selection_from_record(self, record) -> ArcSelection:
        return ArcSelection(
            selection_id=record.selection_id,
            project_id=record.project_id,
            selected_arc=self._arc_candidate_from_record(record.selected_arc),
            rejected_arc_ids=list(record.rejected_arc_ids),
            comparison_notes=list(record.comparison_notes),
            comparison_record_ids=list(record.comparison_record_ids),
            stage_map=self._arc_stage_map_from_record(record.stage_map) if record.stage_map is not None else None,
        )

    def _comparison_record_to_comparisons(self, record) -> tuple[ArcCandidateComparison, ...]:
        return tuple(
            ArcCandidateComparison(
                candidate=self._arc_candidate_from_record(ranked.candidate),
                rank=ranked.rank,
                score=ranked.score,
                notes=tuple(ranked.notes),
            )
            for ranked in record.ranked_candidates
        )

    def _comparison_record_ids_for_selection(self, project_id: str) -> list[str]:
        comparisons = self.repository.list_arc_comparisons(project_id)
        return [comparisons[-1].comparison_id] if comparisons else []

    def _previous_arc_selection(self, project_id: str, current_selection_id: str) -> ArcSelection | None:
        selections = self.repository.list_arc_selections(project_id)
        for record in reversed(selections):
            if record.selection_id == current_selection_id:
                continue
            return self._selection_from_record(record)
        return None

    def _latest_decision_node_id(self, project_id: str) -> str | None:
        nodes = self.repository.list_story_decision_nodes(project_id)
        return nodes[-1].node_id if nodes else None

    def _record_story_decision_for_selection(
        self,
        *,
        project_id: str,
        selection_id: str,
        selected_arc: ArcCandidate,
        comparison_record_ids: Sequence[str],
        rejected_arc_ids: Sequence[str],
        prior_selection: ArcSelection | None,
    ) -> None:
        prior_summary = (
            f"{prior_selection.selected_arc.name} was the active arc."
            if prior_selection is not None
            else "No arc had been selected yet."
        )
        self.repository.record_story_decision_node(
            node_id=f"{selection_id}:decision",
            project_id=project_id,
            node_type=StoryDecisionNodeType.DECISION.value,
            change_type=StoryDecisionChangeType.ARC_SELECTION.value,
            subject_type=StoryObjectType.ARC_SELECTION.value,
            subject_id=selection_id,
            parent_node_id=self._latest_decision_node_id(project_id),
            branch_id=None,
            summary=f"Select {selected_arc.name} arc",
            prior_state_ref=prior_selection.selected_arc.arc_id if prior_selection is not None else None,
            prior_state_summary=prior_summary,
            new_state_ref=selected_arc.arc_id,
            new_state_summary=f"{selected_arc.name} becomes the active arc.",
            reason_or_note=f"Selected arc with {len(rejected_arc_ids)} rejected alternative(s).",
            made_by="story-knowledge-service",
            related_object_links=[
                {
                    "object_type": StoryObjectType.ARC_SELECTION.value,
                    "object_id": selection_id,
                    "relation_kind": "primary",
                },
                {
                    "object_type": StoryObjectType.ARC_CANDIDATE.value,
                    "object_id": selected_arc.arc_id,
                    "relation_kind": "selected_arc",
                },
            ],
            informing_object_links=[
                {
                    "object_type": StoryObjectType.ARC_COMPARISON_RECORD.value,
                    "object_id": comparison_id,
                    "relation_kind": "informed_by",
                }
                for comparison_id in comparison_record_ids
            ],
        )

    def _record_story_decision_for_stage_map(
        self,
        *,
        project_id: str,
        selected_arc_id: str,
        stage_map,
        parent_node_id: str | None,
    ) -> None:
        self.repository.record_story_decision_node(
            node_id=f"{project_id}:{selected_arc_id}:stage-map:{len(self.repository.list_story_decision_nodes(project_id)) + 1:03d}",
            project_id=project_id,
            node_type=StoryDecisionNodeType.DECISION.value,
            change_type=StoryDecisionChangeType.PLANNING_PIVOT.value,
            subject_type=StoryObjectType.ARC_STAGE_MAP.value,
            subject_id=stage_map.arc_stage_map_id,
            parent_node_id=parent_node_id,
            branch_id=None,
            summary=f"Update stage map for {selected_arc_id}",
            prior_state_ref=None,
            prior_state_summary=None,
            new_state_ref=stage_map.arc_stage_map_id,
            new_state_summary="Stage map refreshed from the current arc selection.",
            reason_or_note=stage_map.notes,
            made_by="story-knowledge-service",
            related_object_links=[
                {
                    "object_type": StoryObjectType.ARC_STAGE_MAP.value,
                    "object_id": stage_map.arc_stage_map_id,
                    "relation_kind": "primary",
                },
                {
                    "object_type": StoryObjectType.ARC_CANDIDATE.value,
                    "object_id": selected_arc_id,
                    "relation_kind": "selected_arc",
                },
            ],
            informing_object_links=[],
        )

    def _comparison_id(self, project_id: str) -> str:
        return f"{self._normalize_text(project_id, field_name='project_id')}:comparison:{uuid4().hex}"

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _normalize_optional_text(self, value: object | None, *, field_name: str) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return self._normalize_text(value, field_name=field_name)

    def _lenient_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        return value.strip()

    def _normalize_text_list(self, values: Sequence[str] | None, *, field_name: str) -> list[str]:
        if values is None:
            return []
        if isinstance(values, str):
            values = [values]
        normalized = [self._normalize_text(value, field_name=field_name) for value in values]
        return self._unique_strings(normalized)

    def _unique_strings(self, values: Sequence[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
        return unique

    def _unique_candidates(self, candidates: Sequence[ArcCandidate]) -> list[ArcCandidate]:
        seen: set[str] = set()
        unique: list[ArcCandidate] = []
        for candidate in candidates:
            if candidate.arc_id in seen:
                continue
            seen.add(candidate.arc_id)
            unique.append(candidate)
        return unique

    def _group_relationship_edges_by_character(
        self,
        edges: Sequence[RelationshipEdgeRecord],
    ) -> dict[str, list[RelationshipEdgeRecord]]:
        grouped: dict[str, list[RelationshipEdgeRecord]] = {}
        for edge in edges:
            grouped.setdefault(edge.source_character_id, []).append(edge)
            if edge.target_character_id != edge.source_character_id:
                grouped.setdefault(edge.target_character_id, []).append(edge)
        return grouped
