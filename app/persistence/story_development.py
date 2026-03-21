from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.schemas import (
    ArcCandidate,
    ArcSelection,
    ArcStageMap,
    RelationshipEdge,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StoryArtifactLifecycleState,
    StorySuggestionLifecycleState,
)

from .sqlite import connect, ensure_operations_db


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(UTC)


def _json_list(values: list[str] | None) -> str:
    import json

    return json.dumps(list(values or []), ensure_ascii=True, sort_keys=True)


def _parse_json_list(value: str | None) -> list[str]:
    import json

    return list(json.loads(value or "[]"))


def _json_objects(values: Sequence[Mapping[str, Any]] | None) -> str:
    return json.dumps([dict(value) for value in values or []], ensure_ascii=True, sort_keys=True)


def _json_object(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=True, sort_keys=True)


def _parse_json_objects(value: str | None) -> list[dict[str, Any]]:
    raw = json.loads(value or "[]")
    if not isinstance(raw, list):
        raise TypeError("expected a JSON list")
    return [dict(item) for item in raw]


@dataclass(frozen=True)
class StoryFlowDefinitionRecord:
    project_id: str
    flow_name: str
    flow_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryFlowStageRecord:
    stage_id: int
    project_id: str
    stage_key: str
    stage_kind: str
    is_custom: bool
    display_name: str
    description: str | None
    position: int
    depends_on: list[str]
    stage_configuration_state: StoryFlowStageConfigurationState
    stage_progress_state: StoryFlowStageProgressState
    writer_notes: str | None
    custom_prompt_guidance: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BrainstormItemRecord:
    item_id: int
    project_id: str
    cluster_key: str | None
    content: str
    item_state: str
    tags: list[str]
    source_artifact_refs: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationRevisionRecord:
    revision_id: int
    project_id: str
    revision_number: int
    premise: str
    logline: str
    thematic_spine: str | None
    emotional_promise: str | None
    tone_direction: str | None
    target_audience: str | None
    narrative_constraints: list[str]
    complexity_level: str | None
    success_definition: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationProfileRecord:
    project_id: str
    current_revision_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CharacterProfileRecord:
    character_id: str
    project_id: str
    display_name: str
    role_in_story: str | None
    archetype: str | None
    external_goal: str | None
    internal_need: str | None
    misbelief_or_wound: str | None
    core_fear: str | None
    primary_strength: str | None
    fatal_flaw_or_limitation: str | None
    contradictions: list[str]
    backstory_summary: str | None
    voice_notes: str | None
    relationship_map: list[str]
    secrets: list[str]
    values: list[str]
    taboos: list[str]
    change_axis: str | None
    arc_stage_notes: str | None
    continuity_facts: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WorldBibleEntryRecord:
    entry_id: int
    project_id: str
    entry_type: str
    title: str
    summary: str | None
    canonical_facts: list[str]
    related_character_ids: list[str]
    visibility_scope: str
    source_artifacts: list[str]
    continuity_warnings: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RelationshipEdgeRecord:
    edge_id: str
    project_id: str
    source_character_id: str
    target_character_id: str
    relation_kind: str
    summary: str
    tension: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcCandidateRecord:
    arc_id: str
    project_id: str
    name: str
    summary: str
    stage_map_notes: list[str]
    fit_notes: list[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcComparisonCandidateRecord:
    candidate: ArcCandidateRecord
    rank: int
    score: tuple[int, int, int, int]
    notes: list[str]


@dataclass(frozen=True)
class ArcComparisonRecord:
    comparison_id: str
    project_id: str
    candidate_ids: list[str]
    candidate_set: list[ArcCandidateRecord]
    ranked_candidates: list[ArcComparisonCandidateRecord]
    review_notes: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcStageMapRecord:
    arc_stage_map_id: str
    project_id: str
    arc_id: str
    stage_kinds: list[str]
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcSelectionRecord:
    selection_id: str
    project_id: str
    selected_arc_id: str
    selected_arc: ArcCandidateRecord
    rejected_arc_ids: list[str]
    comparison_notes: list[str]
    comparison_record_ids: list[str]
    stage_map_id: str | None
    stage_map: ArcStageMapRecord | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryDecisionNodeLinkRecord:
    object_type: str
    object_id: str
    relation_kind: str


@dataclass(frozen=True)
class StoryDecisionNodeRecord:
    node_record_id: int
    node_id: str
    project_id: str
    node_type: str
    change_type: str
    subject_type: str
    subject_id: str
    parent_node_id: str | None
    branch_id: str | None
    summary: str
    prior_state_ref: str | None
    prior_state_summary: str | None
    new_state_ref: str | None
    new_state_summary: str | None
    reason_or_note: str | None
    decision_made_at: datetime
    made_by: str
    related_object_links: list[StoryDecisionNodeLinkRecord]
    informing_object_links: list[StoryDecisionNodeLinkRecord]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CheckerFindingRecord:
    finding_id: str
    project_id: str
    source_object_id: str
    source_object_kind: str
    severity: str
    summary: str
    details: str | None
    source_context: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ReviewDecisionRecord:
    decision_id: str
    project_id: str
    target_id: str
    target_kind: str
    decision: str
    notes: str | None
    source_context: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class InspectRunLinkRecord:
    link_id: str
    project_id: str
    object_kind: str
    object_id: str
    logical_run_id: str
    run_id: str
    run_kind: str
    attempt_number: int | None
    label: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BeatPlanRecord:
    beat_id: str
    project_id: str
    objective: str
    conflict: str
    stakes: str
    dependency_ids: list[str]
    arc_stage: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SequencePlanRecord:
    sequence_id: str
    project_id: str
    title: str
    summary: str
    beat_ids: list[str]
    chapter_ids: list[str]
    status: str
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ChapterPlanRecord:
    chapter_id: str
    project_id: str
    sequence_id: str | None
    title: str
    summary: str
    objective: str
    conflict: str
    stakes: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ScenePlanRecord:
    scene_id: str
    project_id: str
    chapter_id: str | None
    title: str
    summary: str
    objective: str
    conflict: str
    stakes: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ChapterPacketRecord:
    packet_id: str
    project_id: str
    chapter_id: str
    included_reference_ids: list[str]
    constraints: list[str]
    scene_goals: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PlanningDependencyRecord:
    dependency_id: str
    project_id: str
    upstream_id: str
    downstream_id: str
    dependency_kind: str
    reason: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DraftArtifactRecord:
    artifact_id: str
    project_id: str
    title: str
    content: str
    source_plan_ids: list[str]
    source_context: list[str]
    provenance_note: str | None
    status: StoryArtifactLifecycleState
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ManuscriptDocumentRecord:
    document_id: str
    project_id: str
    title: str
    content: str
    chapter_id: str | None
    scene_id: str | None
    current_draft_artifact_id: str | None
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RevisionSuggestionRecord:
    suggestion_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    source_context: list[str]
    status: StorySuggestionLifecycleState
    created_at: datetime
    updated_at: datetime


class StoryDevelopmentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def ensure_flow_definition(
        self,
        *,
        project_id: str,
        flow_name: str,
        flow_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowDefinitionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO story_flow_definitions (
                    project_id, flow_name, flow_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    flow_name = excluded.flow_name,
                    flow_notes = excluded.flow_notes,
                    updated_at = excluded.updated_at
                """,
                (project_id, flow_name, flow_notes, now.isoformat(), updated.isoformat()),
            )
            connection.commit()
        return self.get_flow_definition(project_id)

    def get_flow_definition(self, project_id: str) -> StoryFlowDefinitionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT project_id, flow_name, flow_notes, created_at, updated_at
                FROM story_flow_definitions
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return StoryFlowDefinitionRecord(
            project_id=row["project_id"],
            flow_name=row["flow_name"],
            flow_notes=row["flow_notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def add_flow_stage(
        self,
        *,
        project_id: str,
        stage_key: str,
        stage_kind: str,
        is_custom: bool,
        display_name: str,
        position: int,
        description: str | None = None,
        depends_on: list[str] | None = None,
        stage_configuration_state: str,
        stage_progress_state: str,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO story_flow_stages (
                    project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                    stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    stage_key,
                    stage_kind,
                    1 if is_custom else 0,
                    display_name,
                    description,
                    position,
                    _json_list(depends_on),
                    stage_configuration_state,
                    stage_progress_state,
                    writer_notes,
                    custom_prompt_guidance,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_flow_stage(project_id, stage_key=stage_key)

    def get_flow_stage(
        self,
        project_id: str,
        *,
        stage_id: int | None = None,
        stage_key: str | None = None,
    ) -> StoryFlowStageRecord:
        if stage_id is None and stage_key is None:
            raise ValueError("stage_id or stage_key is required")
        query = """
            SELECT stage_id, project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                   stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance, created_at, updated_at
            FROM story_flow_stages
            WHERE project_id = ?
        """
        params: list[object] = [project_id]
        if stage_id is not None:
            query += " AND stage_id = ?"
            params.append(stage_id)
        if stage_key is not None:
            query += " AND stage_key = ?"
            params.append(stage_key)
        with connect(self.db_path) as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        if row is None:
            raise KeyError(stage_id if stage_id is not None else stage_key)
        return _stage_row_to_record(row)

    def list_flow_stages(self, project_id: str) -> list[StoryFlowStageRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT stage_id, project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                       stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance, created_at, updated_at
                FROM story_flow_stages
                WHERE project_id = ?
                ORDER BY position ASC, stage_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_stage_row_to_record(row) for row in rows]

    def rename_flow_stage(self, project_id: str, *, stage_id: int, display_name: str, updated_at: datetime | None = None) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                UPDATE story_flow_stages
                SET display_name = ?, updated_at = ?
                WHERE project_id = ? AND stage_id = ?
                """,
                (display_name, updated.isoformat(), project_id, stage_id),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)

    def redefine_flow_stage(
        self,
        project_id: str,
        *,
        stage_id: int,
        stage_kind: str | None = None,
        description: str | None = None,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        assignments: list[str] = []
        values: list[object] = []
        for column, value in (
            ("stage_kind", stage_kind),
            ("description", description),
            ("writer_notes", writer_notes),
            ("custom_prompt_guidance", custom_prompt_guidance),
        ):
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if not assignments:
            return self.get_flow_stage(project_id, stage_id=stage_id)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.extend([project_id, stage_id])
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE story_flow_stages
                SET {', '.join(assignments)}
                WHERE project_id = ? AND stage_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)

    def reorder_flow_stages(self, project_id: str, *, ordered_stage_ids: list[int], updated_at: datetime | None = None) -> list[StoryFlowStageRecord]:
        updated = _now(updated_at)
        with connect(self.db_path) as connection:
            for position, stage_id in enumerate(ordered_stage_ids):
                connection.execute(
                    """
                    UPDATE story_flow_stages
                    SET position = ?, updated_at = ?
                    WHERE project_id = ? AND stage_id = ?
                    """,
                    (position, updated.isoformat(), project_id, stage_id),
                )
            connection.commit()
        return self.list_flow_stages(project_id)

    def set_flow_stage_state(
        self,
        project_id: str,
        *,
        stage_id: int,
        stage_configuration_state: StoryFlowStageConfigurationState | str | None = None,
        stage_progress_state: StoryFlowStageProgressState | str | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        assignments: list[str] = []
        values: list[object] = []
        if stage_configuration_state is not None:
            assignments.append("stage_configuration_state = ?")
            values.append(stage_configuration_state)
        if stage_progress_state is not None:
            assignments.append("stage_progress_state = ?")
            values.append(stage_progress_state)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.extend([project_id, stage_id])
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE story_flow_stages
                SET {', '.join(assignments)}
                WHERE project_id = ? AND stage_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)

    def delete_custom_flow_stage(self, project_id: str, *, stage_id: int) -> bool:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT is_custom
                FROM story_flow_stages
                WHERE project_id = ? AND stage_id = ?
                """,
                (project_id, stage_id),
            ).fetchone()
            if row is None:
                raise KeyError(stage_id)
            if int(row["is_custom"]) != 1:
                raise ValueError("Only custom stages may be deleted")
            connection.execute(
                "DELETE FROM story_flow_stages WHERE project_id = ? AND stage_id = ?",
                (project_id, stage_id),
            )
            connection.commit()
        return True

    def create_brainstorm_item(
        self,
        *,
        project_id: str,
        content: str,
        item_state: str,
        cluster_key: str | None = None,
        tags: list[str] | None = None,
        source_artifact_refs: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO brainstorm_items (
                    project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    cluster_key,
                    content,
                    item_state,
                    _json_list(tags),
                    _json_list(source_artifact_refs),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_brainstorm_item(int(cursor.lastrowid))

    def get_brainstorm_item(self, item_id: int) -> BrainstormItemRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return _brainstorm_row_to_record(row)

    def list_brainstorm_items(self, project_id: str) -> list[BrainstormItemRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE project_id = ?
                ORDER BY item_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_brainstorm_row_to_record(row) for row in rows]

    def update_brainstorm_item_state(
        self,
        item_id: int,
        *,
        item_state: str,
        cluster_key: str | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        updated = _now(updated_at)
        assignments = ["item_state = ?"]
        values: list[object] = [item_state]
        if cluster_key is not None:
            assignments.append("cluster_key = ?")
            values.append(cluster_key)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.append(item_id)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE brainstorm_items
                SET {', '.join(assignments)}
                WHERE item_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(item_id)
        return self.get_brainstorm_item(item_id)

    def upsert_foundation_profile(
        self,
        *,
        project_id: str,
        premise: str,
        logline: str,
        thematic_spine: str | None = None,
        emotional_promise: str | None = None,
        tone_direction: str | None = None,
        target_audience: str | None = None,
        narrative_constraints: list[str] | None = None,
        complexity_level: str | None = None,
        success_definition: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        ) -> FoundationRevisionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        revision_number = self._next_foundation_revision_number(project_id)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO foundation_profiles (
                    project_id, current_revision_id, created_at, updated_at
                ) VALUES (?, NULL, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    updated_at = excluded.updated_at
                """,
                (project_id, now.isoformat(), updated.isoformat()),
            )
            cursor = connection.execute(
                """
                INSERT INTO foundation_revisions (
                    project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                    tone_direction, target_audience, narrative_constraints_json, complexity_level,
                    success_definition, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    revision_number,
                    premise,
                    logline,
                    thematic_spine,
                    emotional_promise,
                    tone_direction,
                    target_audience,
                    _json_list(narrative_constraints),
                    complexity_level,
                    success_definition,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            revision_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
                (revision_id, updated.isoformat(), project_id),
            )
            connection.commit()
        return self.get_foundation_revision(revision_id)

    def get_foundation_profile(self, project_id: str) -> FoundationProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT project_id, current_revision_id, created_at, updated_at
                FROM foundation_profiles
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return FoundationProfileRecord(
            project_id=row["project_id"],
            current_revision_id=row["current_revision_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_foundation_revisions(self, project_id: str) -> list[FoundationRevisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE project_id = ?
                ORDER BY revision_number ASC, revision_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_foundation_revision_row_to_record(row) for row in rows]

    def get_foundation_revision(self, revision_id: int) -> FoundationRevisionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE revision_id = ?
                """,
                (revision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        return _foundation_revision_row_to_record(row)

    def upsert_character_profile(
        self,
        *,
        project_id: str,
        character_id: str,
        display_name: str,
        role_in_story: str | None = None,
        archetype: str | None = None,
        external_goal: str | None = None,
        internal_need: str | None = None,
        misbelief_or_wound: str | None = None,
        core_fear: str | None = None,
        primary_strength: str | None = None,
        fatal_flaw_or_limitation: str | None = None,
        contradictions: list[str] | None = None,
        backstory_summary: str | None = None,
        voice_notes: str | None = None,
        relationship_map: list[str] | None = None,
        secrets: list[str] | None = None,
        values: list[str] | None = None,
        taboos: list[str] | None = None,
        change_axis: str | None = None,
        arc_stage_notes: str | None = None,
        continuity_facts: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CharacterProfileRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO character_profiles (
                    character_id, project_id, display_name, role_in_story, archetype, external_goal, internal_need,
                    misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, contradictions_json,
                    backstory_summary, voice_notes, relationship_map_json, secrets_json, values_json, taboos_json,
                    change_axis, arc_stage_notes, continuity_facts_json, writer_notes, created_at, updated_at
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
                    character_id,
                    project_id,
                    display_name,
                    role_in_story,
                    archetype,
                    external_goal,
                    internal_need,
                    misbelief_or_wound,
                    core_fear,
                    primary_strength,
                    fatal_flaw_or_limitation,
                    _json_list(contradictions),
                    backstory_summary,
                    voice_notes,
                    _json_list(relationship_map),
                    _json_list(secrets),
                    _json_list(values),
                    _json_list(taboos),
                    change_axis,
                    arc_stage_notes,
                    _json_list(continuity_facts),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_character_profile(character_id)

    def upsert_relationship_edge(
        self,
        *,
        project_id: str,
        source_character_id: str,
        target_character_id: str,
        relation_kind: str,
        summary: str,
        tension: str | None = None,
        notes: str | None = None,
        edge_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> RelationshipEdgeRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_project_id = project_id
        normalized_edge_id = edge_id or f"{source_character_id}->{target_character_id}:{relation_kind}"
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO relationship_edges (
                    edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                    tension, notes, created_at, updated_at
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
                    normalized_edge_id,
                    normalized_project_id,
                    source_character_id,
                    target_character_id,
                    relation_kind,
                    summary,
                    tension,
                    notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            self._append_relationship_edge_to_character_map(
                connection,
                source_character_id=source_character_id,
                target_character_id=target_character_id,
                edge_id=normalized_edge_id,
                updated_at=updated,
            )
            connection.commit()
        return self.get_relationship_edge(normalized_edge_id)

    def get_relationship_edge(self, edge_id: str) -> RelationshipEdgeRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE edge_id = ?
                """,
                (edge_id,),
            ).fetchone()
        if row is None:
            raise KeyError(edge_id)
        return _relationship_edge_row_to_record(row)

    def list_relationship_edges(self, project_id: str) -> list[RelationshipEdgeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE project_id = ?
                ORDER BY edge_id COLLATE NOCASE
                """,
                (project_id,),
            ).fetchall()
        return [_relationship_edge_row_to_record(row) for row in rows]

    def list_relationship_edges_for_character(self, project_id: str, character_id: str) -> list[RelationshipEdgeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE project_id = ? AND (source_character_id = ? OR target_character_id = ?)
                ORDER BY edge_id COLLATE NOCASE
                """,
                (project_id, character_id, character_id),
            ).fetchall()
        return [_relationship_edge_row_to_record(row) for row in rows]

    def get_character_profile(self, character_id: str) -> CharacterProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM character_profiles WHERE character_id = ?", (character_id,)).fetchone()
        if row is None:
            raise KeyError(character_id)
        return _character_row_to_record(row)

    def list_character_profiles(self, project_id: str) -> list[CharacterProfileRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM character_profiles
                WHERE project_id = ?
                ORDER BY display_name COLLATE NOCASE, character_id
                """,
                (project_id,),
            ).fetchall()
        return [_character_row_to_record(row) for row in rows]

    def upsert_world_bible_entry(
        self,
        *,
        project_id: str,
        entry_type: str,
        title: str,
        summary: str | None = None,
        canonical_facts: list[str] | None = None,
        related_character_ids: list[str] | None = None,
        visibility_scope: str = "project",
        source_artifacts: list[str] | None = None,
        continuity_warnings: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> WorldBibleEntryRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json, related_character_ids_json, visibility_scope,
                    source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
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
                    entry_type,
                    title,
                    summary,
                    _json_list(canonical_facts),
                    _json_list(related_character_ids),
                    visibility_scope,
                    _json_list(source_artifacts),
                    _json_list(continuity_warnings),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_world_bible_entry(project_id, entry_type=entry_type, title=title)

    def upsert_arc_candidate(
        self,
        *,
        project_id: str,
        arc_id: str,
        name: str,
        summary: str,
        stage_map_notes: list[str] | None = None,
        fit_notes: list[str] | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcCandidateRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_candidates (
                    arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
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
                    name,
                    summary,
                    _json_list(stage_map_notes),
                    _json_list(fit_notes),
                    _json_list(tags),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_candidate(project_id, arc_id=arc_id)

    def get_arc_candidate(self, project_id: str, *, arc_id: str) -> ArcCandidateRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json,
                       created_at, updated_at
                FROM arc_candidates
                WHERE project_id = ? AND arc_id = ?
                """,
                (project_id, arc_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, arc_id))
        return _arc_candidate_row_to_record(row)

    def list_arc_candidates(self, project_id: str) -> list[ArcCandidateRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json,
                       created_at, updated_at
                FROM arc_candidates
                WHERE project_id = ?
                ORDER BY name COLLATE NOCASE, arc_id
                """,
                (project_id,),
            ).fetchall()
        return [_arc_candidate_row_to_record(row) for row in rows]

    def upsert_arc_comparison(
        self,
        *,
        project_id: str,
        comparison_id: str,
        candidates: Sequence[ArcCandidate | ArcCandidateRecord | Mapping[str, Any]] | None = None,
        ranked_candidates: Sequence[ArcComparisonCandidateRecord | Mapping[str, Any]] | None = None,
        review_notes: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcComparisonRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        if ranked_candidates is None:
            if candidates is None:
                raise ValueError("candidates or ranked_candidates is required")
            candidate_records = [
                self._persist_arc_candidate(project_id, candidate, created_at=now, updated_at=updated)
                for candidate in candidates
            ]
            unique_candidates = _unique_arc_candidate_records(candidate_records)
            if len(unique_candidates) < 2:
                raise ValueError("At least two arc candidates are required.")
            candidate_records = unique_candidates
            ranked_candidate_records = _rank_arc_comparison_candidates(unique_candidates)
        else:
            ranked_candidate_records = [
                _coerce_arc_comparison_candidate(project_id, item)
                for item in ranked_candidates
            ]
            ranked_candidate_records = _unique_arc_comparison_ranked_candidates(ranked_candidate_records)
            if len(ranked_candidate_records) < 2:
                raise ValueError("At least two arc candidates are required.")
            candidate_records = [ranked.candidate for ranked in ranked_candidate_records]

        candidate_ids = [candidate.arc_id for candidate in candidate_records]
        review_notes_payload = _json_list(list(review_notes))
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_comparisons (
                    comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                    review_notes_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comparison_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    candidate_ids_json = excluded.candidate_ids_json,
                    candidate_set_json = excluded.candidate_set_json,
                    ranked_candidates_json = excluded.ranked_candidates_json,
                    review_notes_json = excluded.review_notes_json,
                    updated_at = excluded.updated_at
                """,
                (
                    comparison_id,
                    project_id,
                    _json_list(candidate_ids),
                    _json_objects([_arc_candidate_record_to_mapping(candidate) for candidate in candidate_records]),
                    _json_objects([_arc_comparison_candidate_record_to_mapping(record) for record in ranked_candidate_records]),
                    review_notes_payload,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_comparison(project_id, comparison_id=comparison_id)

    def get_arc_comparison(self, project_id: str, *, comparison_id: str) -> ArcComparisonRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                       review_notes_json, created_at, updated_at
                FROM arc_comparisons
                WHERE project_id = ? AND comparison_id = ?
                """,
                (project_id, comparison_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, comparison_id))
        return _arc_comparison_row_to_record(row)

    def list_arc_comparisons(self, project_id: str) -> list[ArcComparisonRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                       review_notes_json, created_at, updated_at
                FROM arc_comparisons
                WHERE project_id = ?
                ORDER BY created_at ASC, comparison_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_arc_comparison_row_to_record(row) for row in rows]

    def upsert_arc_stage_map(
        self,
        *,
        project_id: str,
        arc_id: str,
        stage_kinds: list[str] | None = None,
        notes: str | None = None,
        arc_stage_map_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcStageMapRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_arc_stage_map_id = arc_stage_map_id or f"{project_id}:{arc_id}:stage-map"
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_stage_maps (
                    arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, arc_id) DO UPDATE SET
                    arc_stage_map_id = excluded.arc_stage_map_id,
                    stage_kinds_json = excluded.stage_kinds_json,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized_arc_stage_map_id,
                    project_id,
                    arc_id,
                    _json_list(stage_kinds),
                    notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_stage_map(project_id, arc_id=arc_id)

    def get_arc_stage_map(self, project_id: str, *, arc_id: str) -> ArcStageMapRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                FROM arc_stage_maps
                WHERE project_id = ? AND arc_id = ?
                """,
                (project_id, arc_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, arc_id))
        return _arc_stage_map_row_to_record(row)

    def list_arc_stage_maps(self, project_id: str) -> list[ArcStageMapRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                FROM arc_stage_maps
                WHERE project_id = ?
                ORDER BY arc_id COLLATE NOCASE
                """,
                (project_id,),
            ).fetchall()
        return [_arc_stage_map_row_to_record(row) for row in rows]

    def upsert_arc_selection(
        self,
        *,
        project_id: str,
        selection_id: str,
        selected_arc: ArcCandidate | ArcCandidateRecord | Mapping[str, Any],
        rejected_arc_ids: list[str] | None = None,
        comparison_notes: list[str] | None = None,
        comparison_inputs: Sequence[ArcCandidate | ArcCandidateRecord | Mapping[str, Any]] | None = None,
        comparison_record_ids: Sequence[str] | None = None,
        stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcSelectionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        selected_record = self._persist_arc_candidate(project_id, selected_arc, created_at=now, updated_at=updated)
        comparison_records = [
            self._persist_arc_candidate(project_id, candidate, created_at=now, updated_at=updated)
            for candidate in comparison_inputs or []
        ]
        linked_comparison_ids = _normalize_text_list(list(comparison_record_ids or []), field_name="comparison_record_ids")
        if not linked_comparison_ids and len(comparison_records) >= 2:
            auto_comparison_id = f"{selection_id}:comparison:001"
            auto_comparison = self.upsert_arc_comparison(
                project_id=project_id,
                comparison_id=auto_comparison_id,
                candidates=comparison_records,
                review_notes=comparison_notes,
                created_at=now,
                updated_at=updated,
            )
            linked_comparison_ids = [auto_comparison.comparison_id]
        for comparison_id in linked_comparison_ids:
            self.get_arc_comparison(project_id, comparison_id=comparison_id)
        if stage_map is not None:
            normalized_stage_map = _coerce_arc_stage_map(project_id, stage_map)
            if normalized_stage_map.arc_id != selected_record.arc_id:
                raise ValueError("stage_map.arc_id must match the selected arc")
        selected_stage_map = self._persist_arc_stage_map(project_id, stage_map, created_at=now, updated_at=updated)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_selections (
                    selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                    comparison_notes_json, stage_map_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(selection_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    selected_arc_id = excluded.selected_arc_id,
                    selected_arc_json = excluded.selected_arc_json,
                    rejected_candidate_ids_json = excluded.rejected_candidate_ids_json,
                    comparison_notes_json = excluded.comparison_notes_json,
                    stage_map_id = excluded.stage_map_id,
                    updated_at = excluded.updated_at
                """,
                (
                    selection_id,
                    project_id,
                    selected_record.arc_id,
                    _json_object(_arc_candidate_record_to_mapping(selected_record)),
                    _json_list(rejected_arc_ids),
                    _json_list(comparison_notes),
                    selected_stage_map.arc_stage_map_id if selected_stage_map is not None else None,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        self._replace_arc_selection_comparison_links(
            selection_id=selection_id,
            project_id=project_id,
            comparison_record_ids=linked_comparison_ids,
            created_at=now,
            updated_at=updated,
        )
        return self.get_arc_selection(project_id, selection_id=selection_id)

    def get_arc_selection(self, project_id: str, *, selection_id: str) -> ArcSelectionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                       comparison_notes_json, stage_map_id, created_at, updated_at
                FROM arc_selections
                WHERE project_id = ? AND selection_id = ?
                """,
                (project_id, selection_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, selection_id))
        return _arc_selection_row_to_record(row, repository=self)

    def list_arc_selections(self, project_id: str) -> list[ArcSelectionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                       comparison_notes_json, stage_map_id, created_at, updated_at
                FROM arc_selections
                WHERE project_id = ?
                ORDER BY created_at ASC, selection_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_arc_selection_row_to_record(row, repository=self) for row in rows]

    def _arc_selection_comparison_ids(self, selection_id: str) -> list[str]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT comparison_id
                FROM arc_selection_comparisons
                WHERE selection_id = ?
                ORDER BY link_order ASC, comparison_id ASC
                """,
                (selection_id,),
            ).fetchall()
        return [row["comparison_id"] for row in rows]

    def _replace_arc_selection_comparison_links(
        self,
        *,
        selection_id: str,
        project_id: str,
        comparison_record_ids: Sequence[str],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_ids = _normalize_text_list(list(comparison_record_ids), field_name="comparison_record_ids")
        with connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM arc_selection_comparisons WHERE selection_id = ?",
                (selection_id,),
            )
            for link_order, comparison_id in enumerate(normalized_ids):
                comparison_row = connection.execute(
                    """
                    SELECT comparison_id
                    FROM arc_comparisons
                    WHERE project_id = ? AND comparison_id = ?
                    """,
                    (project_id, comparison_id),
                ).fetchone()
                if comparison_row is None:
                    raise KeyError((project_id, comparison_id))
                connection.execute(
                    """
                    INSERT INTO arc_selection_comparisons (
                        selection_id, comparison_id, link_order, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        selection_id,
                        comparison_id,
                        link_order,
                        now.isoformat(),
                        updated.isoformat(),
                    ),
                )
            connection.commit()

    def record_story_decision_node(
        self,
        *,
        node_id: str,
        project_id: str,
        node_type: str,
        change_type: str,
        subject_type: str,
        subject_id: str,
        made_by: str,
        decision_made_at: datetime | None = None,
        parent_node_id: str | None = None,
        branch_id: str | None = None,
        summary: str | None = None,
        prior_state_ref: str | None = None,
        prior_state_summary: str | None = None,
        new_state_ref: str | None = None,
        new_state_summary: str | None = None,
        reason_or_note: str | None = None,
        related_object_links: Sequence[Mapping[str, Any]] | None = None,
        informing_object_links: Sequence[Mapping[str, Any]] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryDecisionNodeRecord:
        created = _now(created_at or decision_made_at)
        updated = _now(updated_at or created_at or decision_made_at)
        made_at = _now(decision_made_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO story_decision_nodes (
                    node_id, project_id, node_type, change_type, subject_type, subject_id, parent_node_id,
                    branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref, new_state_summary,
                    reason_or_note, decision_made_at, made_by, related_object_links_json,
                    informing_object_links_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    project_id,
                    node_type,
                    change_type,
                    subject_type,
                    subject_id,
                    parent_node_id,
                    branch_id,
                    summary or reason_or_note or f"{change_type}:{subject_type}:{subject_id}",
                    prior_state_ref,
                    prior_state_summary,
                    new_state_ref,
                    new_state_summary,
                    reason_or_note,
                    made_at.isoformat(),
                    made_by,
                    _json_objects(related_object_links),
                    _json_objects(informing_object_links),
                    created.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_story_decision_node(project_id, node_id=node_id)

    def get_story_decision_node(self, project_id: str, *, node_id: str) -> StoryDecisionNodeRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
                       parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
                       new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
                       informing_object_links_json, created_at, updated_at
                FROM story_decision_nodes
                WHERE project_id = ? AND node_id = ?
                """,
                (project_id, node_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, node_id))
        return _story_decision_node_row_to_record(row)

    def list_story_decision_nodes(self, project_id: str) -> list[StoryDecisionNodeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
                       parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
                       new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
                       informing_object_links_json, created_at, updated_at
                FROM story_decision_nodes
                WHERE project_id = ?
                ORDER BY decision_made_at ASC, node_id ASC, node_record_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_story_decision_node_row_to_record(row) for row in rows]

    def list_story_decision_nodes_for_subject(self, project_id: str, *, subject_type: str, subject_id: str) -> list[StoryDecisionNodeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
                       parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
                       new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
                       informing_object_links_json, created_at, updated_at
                FROM story_decision_nodes
                WHERE project_id = ? AND subject_type = ? AND subject_id = ?
                ORDER BY decision_made_at ASC, node_id ASC, node_record_id ASC
                """,
                (project_id, subject_type, subject_id),
            ).fetchall()
        return [_story_decision_node_row_to_record(row) for row in rows]

    def upsert_checker_finding(
        self,
        *,
        finding_id: str,
        project_id: str,
        source_object_id: str,
        source_object_kind: str,
        severity: str,
        summary: str,
        details: str | None = None,
        source_context: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CheckerFindingRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO checker_findings (
                    finding_id, project_id, source_object_id, source_object_kind, severity, summary, details,
                    source_context_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(finding_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_object_id = excluded.source_object_id,
                    source_object_kind = excluded.source_object_kind,
                    severity = excluded.severity,
                    summary = excluded.summary,
                    details = excluded.details,
                    source_context_json = excluded.source_context_json,
                    updated_at = excluded.updated_at
                """,
                (
                    finding_id,
                    project_id,
                    source_object_id,
                    source_object_kind,
                    severity,
                    summary,
                    details,
                    _json_list(list(source_context or [])),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_checker_finding(finding_id)

    def get_checker_finding(self, finding_id: str) -> CheckerFindingRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE finding_id = ?
                """,
                (finding_id,),
            ).fetchone()
        if row is None:
            raise KeyError(finding_id)
        return _checker_finding_row_to_record(row)

    def list_checker_findings(self, project_id: str) -> list[CheckerFindingRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE project_id = ?
                ORDER BY created_at ASC, finding_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_checker_finding_row_to_record(row) for row in rows]

    def list_checker_findings_for_source(self, project_id: str, *, source_object_kind: str, source_object_id: str) -> list[CheckerFindingRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM checker_findings
                WHERE project_id = ? AND source_object_kind = ? AND source_object_id = ?
                ORDER BY created_at ASC, finding_id ASC
                """,
                (project_id, source_object_kind, source_object_id),
            ).fetchall()
        return [_checker_finding_row_to_record(row) for row in rows]

    def upsert_review_decision(
        self,
        *,
        decision_id: str,
        project_id: str,
        target_id: str,
        target_kind: str,
        decision: str,
        notes: str | None = None,
        source_context: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ReviewDecisionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO review_decisions (
                    decision_id, project_id, target_id, target_kind, decision, notes, source_context_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    target_id = excluded.target_id,
                    target_kind = excluded.target_kind,
                    decision = excluded.decision,
                    notes = excluded.notes,
                    source_context_json = excluded.source_context_json,
                    updated_at = excluded.updated_at
                """,
                (
                    decision_id,
                    project_id,
                    target_id,
                    target_kind,
                    decision,
                    notes,
                    _json_list(list(source_context or [])),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_review_decision(decision_id)

    def get_review_decision(self, decision_id: str) -> ReviewDecisionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return _review_decision_row_to_record(row)

    def list_review_decisions(self, project_id: str) -> list[ReviewDecisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE project_id = ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_review_decision_row_to_record(row) for row in rows]

    def list_review_decisions_for_target(self, project_id: str, *, target_kind: str, target_id: str) -> list[ReviewDecisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM review_decisions
                WHERE project_id = ? AND target_kind = ? AND target_id = ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (project_id, target_kind, target_id),
            ).fetchall()
        return [_review_decision_row_to_record(row) for row in rows]

    def upsert_inspect_run_link(
        self,
        *,
        link_id: str,
        project_id: str,
        object_kind: str,
        object_id: str,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int | None = None,
        label: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> InspectRunLinkRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO inspect_run_links (
                    link_id, project_id, object_kind, object_id, logical_run_id, run_id, run_kind,
                    attempt_number, label, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    object_kind = excluded.object_kind,
                    object_id = excluded.object_id,
                    logical_run_id = excluded.logical_run_id,
                    run_id = excluded.run_id,
                    run_kind = excluded.run_kind,
                    attempt_number = excluded.attempt_number,
                    label = excluded.label,
                    updated_at = excluded.updated_at
                """,
                (
                    link_id,
                    project_id,
                    object_kind,
                    object_id,
                    logical_run_id,
                    run_id,
                    run_kind,
                    attempt_number,
                    label,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_inspect_run_link(link_id)

    def get_inspect_run_link(self, link_id: str) -> InspectRunLinkRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE link_id = ?
                """,
                (link_id,),
            ).fetchone()
        if row is None:
            raise KeyError(link_id)
        return _inspect_run_link_row_to_record(row)

    def list_inspect_run_links(self, project_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]

    def list_inspect_run_links_for_object(self, project_id: str, *, object_kind: str, object_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND object_kind = ? AND object_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, object_kind, object_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]

    def list_inspect_run_links_for_run(self, project_id: str, *, run_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND run_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, run_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]

    def list_inspect_run_links_for_logical_run(self, project_id: str, *, logical_run_id: str) -> list[InspectRunLinkRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM inspect_run_links
                WHERE project_id = ? AND logical_run_id = ?
                ORDER BY created_at ASC, link_id ASC
                """,
                (project_id, logical_run_id),
            ).fetchall()
        return [_inspect_run_link_row_to_record(row) for row in rows]

    def get_world_bible_entry(self, project_id: str, *, entry_type: str, title: str) -> WorldBibleEntryRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ? AND entry_type = ? AND title = ?
                """,
                (project_id, entry_type, title),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, entry_type, title))
        return _world_bible_row_to_record(row)

    def list_world_bible_entries(self, project_id: str) -> list[WorldBibleEntryRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ?
                ORDER BY entry_type COLLATE NOCASE, title COLLATE NOCASE, entry_id
                """,
                (project_id,),
            ).fetchall()
        return [_world_bible_row_to_record(row) for row in rows]

    def upsert_beat_plan(
        self,
        *,
        beat_id: str,
        project_id: str,
        objective: str,
        conflict: str,
        stakes: str,
        dependency_ids: list[str] | None = None,
        arc_stage: str,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BeatPlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO beat_plans (
                    beat_id, project_id, objective, conflict, stakes, dependency_ids_json, arc_stage,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    updated_at = excluded.updated_at
                """,
                (
                    beat_id,
                    project_id,
                    objective,
                    conflict,
                    stakes,
                    _json_list(dependency_ids),
                    arc_stage,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_beat_plan(beat_id)

    def get_beat_plan(self, beat_id: str) -> BeatPlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM beat_plans
                WHERE beat_id = ?
                """,
                (beat_id,),
            ).fetchone()
        if row is None:
            raise KeyError(beat_id)
        return _beat_plan_row_to_record(row)

    def list_beat_plans(self, project_id: str) -> list[BeatPlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM beat_plans
                WHERE project_id = ?
                ORDER BY position ASC, beat_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_beat_plan_row_to_record(row) for row in rows]

    def upsert_sequence_plan(
        self,
        *,
        sequence_id: str,
        project_id: str,
        title: str,
        summary: str,
        beat_ids: list[str] | None = None,
        chapter_ids: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> SequencePlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO sequence_plans (
                    sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json,
                    status, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sequence_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    summary = excluded.summary,
                    beat_ids_json = excluded.beat_ids_json,
                    chapter_ids_json = excluded.chapter_ids_json,
                    status = excluded.status,
                    position = excluded.position,
                    updated_at = excluded.updated_at
                """,
                (
                    sequence_id,
                    project_id,
                    title,
                    summary,
                    _json_list(beat_ids),
                    _json_list(chapter_ids),
                    status,
                    position,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_sequence_plan(sequence_id)

    def get_sequence_plan(self, sequence_id: str) -> SequencePlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sequence_plans
                WHERE sequence_id = ?
                """,
                (sequence_id,),
            ).fetchone()
        if row is None:
            raise KeyError(sequence_id)
        return _sequence_plan_row_to_record(row)

    def list_sequence_plans(self, project_id: str) -> list[SequencePlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sequence_plans
                WHERE project_id = ?
                ORDER BY position ASC, sequence_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_sequence_plan_row_to_record(row) for row in rows]

    def upsert_chapter_plan(
        self,
        *,
        chapter_id: str,
        project_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        sequence_id: str | None = None,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ChapterPlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO chapter_plans (
                    chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    updated_at = excluded.updated_at
                """,
                (
                    chapter_id,
                    project_id,
                    sequence_id,
                    title,
                    summary,
                    objective,
                    conflict,
                    stakes,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_chapter_plan(chapter_id)

    def get_chapter_plan(self, chapter_id: str) -> ChapterPlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM chapter_plans
                WHERE chapter_id = ?
                """,
                (chapter_id,),
            ).fetchone()
        if row is None:
            raise KeyError(chapter_id)
        return _chapter_plan_row_to_record(row)

    def list_chapter_plans(self, project_id: str) -> list[ChapterPlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM chapter_plans
                WHERE project_id = ?
                ORDER BY position ASC, chapter_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chapter_plan_row_to_record(row) for row in rows]

    def upsert_scene_plan(
        self,
        *,
        scene_id: str,
        project_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        chapter_id: str | None = None,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ScenePlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO scene_plans (
                    scene_id, project_id, chapter_id, title, summary, objective, conflict, stakes,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    updated_at = excluded.updated_at
                """,
                (
                    scene_id,
                    project_id,
                    chapter_id,
                    title,
                    summary,
                    objective,
                    conflict,
                    stakes,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_scene_plan(scene_id)

    def get_scene_plan(self, scene_id: str) -> ScenePlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM scene_plans
                WHERE scene_id = ?
                """,
                (scene_id,),
            ).fetchone()
        if row is None:
            raise KeyError(scene_id)
        return _scene_plan_row_to_record(row)

    def list_scene_plans(self, project_id: str) -> list[ScenePlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM scene_plans
                WHERE project_id = ?
                ORDER BY position ASC, scene_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_scene_plan_row_to_record(row) for row in rows]

    def upsert_chapter_packet(
        self,
        *,
        packet_id: str,
        project_id: str,
        chapter_id: str,
        included_reference_ids: list[str] | None = None,
        constraints: list[str] | None = None,
        scene_goals: list[str] | None = None,
        status: str = "draft",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ChapterPacketRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO chapter_packets (
                    packet_id, project_id, chapter_id, included_reference_ids_json, constraints_json,
                    scene_goals_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    included_reference_ids_json = excluded.included_reference_ids_json,
                    constraints_json = excluded.constraints_json,
                    scene_goals_json = excluded.scene_goals_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    packet_id,
                    project_id,
                    chapter_id,
                    _json_list(included_reference_ids),
                    _json_list(constraints),
                    _json_list(scene_goals),
                    status,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_chapter_packet(packet_id)

    def get_chapter_packet(self, packet_id: str) -> ChapterPacketRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM chapter_packets
                WHERE packet_id = ?
                """,
                (packet_id,),
            ).fetchone()
        if row is None:
            raise KeyError(packet_id)
        return _chapter_packet_row_to_record(row)

    def list_chapter_packets(self, project_id: str) -> list[ChapterPacketRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM chapter_packets
                WHERE project_id = ?
                ORDER BY chapter_id ASC, packet_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chapter_packet_row_to_record(row) for row in rows]

    def upsert_planning_dependency(
        self,
        *,
        dependency_id: str,
        project_id: str,
        upstream_id: str,
        downstream_id: str,
        dependency_kind: str,
        reason: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> PlanningDependencyRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO planning_dependencies (
                    dependency_id, project_id, upstream_id, downstream_id, dependency_kind, reason,
                    created_at, updated_at
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
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_planning_dependency(dependency_id)

    def get_planning_dependency(self, dependency_id: str) -> PlanningDependencyRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM planning_dependencies
                WHERE dependency_id = ?
                """,
                (dependency_id,),
            ).fetchone()
        if row is None:
            raise KeyError(dependency_id)
        return _planning_dependency_row_to_record(row)

    def list_planning_dependencies(self, project_id: str) -> list[PlanningDependencyRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM planning_dependencies
                WHERE project_id = ?
                ORDER BY dependency_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_planning_dependency_row_to_record(row) for row in rows]

    def upsert_draft_artifact(
        self,
        *,
        artifact_id: str,
        project_id: str,
        title: str,
        content: str,
        source_plan_ids: Sequence[str] | None = None,
        source_context: Sequence[str] | None = None,
        provenance_note: str | None = None,
        status: StoryArtifactLifecycleState = StoryArtifactLifecycleState.DRAFT,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> DraftArtifactRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO draft_artifacts (
                    artifact_id, project_id, title, content, source_plan_ids_json, source_context_json,
                    provenance_note, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    content = excluded.content,
                    source_plan_ids_json = excluded.source_plan_ids_json,
                    source_context_json = excluded.source_context_json,
                    provenance_note = excluded.provenance_note,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    artifact_id,
                    project_id,
                    title,
                    content,
                    _json_list(list(source_plan_ids or [])),
                    _json_list(list(source_context or [])),
                    provenance_note,
                    status.value if isinstance(status, StoryArtifactLifecycleState) else str(status),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_draft_artifact(artifact_id)

    def get_draft_artifact(self, artifact_id: str) -> DraftArtifactRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM draft_artifacts
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            raise KeyError(artifact_id)
        return _draft_artifact_row_to_record(row)

    def list_draft_artifacts(self, project_id: str) -> list[DraftArtifactRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM draft_artifacts
                WHERE project_id = ?
                ORDER BY title COLLATE NOCASE, artifact_id
                """,
                (project_id,),
            ).fetchall()
        return [_draft_artifact_row_to_record(row) for row in rows]

    def upsert_manuscript_document(
        self,
        *,
        document_id: str,
        project_id: str,
        title: str,
        content: str,
        chapter_id: str | None = None,
        scene_id: str | None = None,
        current_draft_artifact_id: str | None = None,
        version: int = 1,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ManuscriptDocumentRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        if chapter_id is not None:
            chapter = self.get_chapter_plan(chapter_id)
            if chapter.project_id != project_id:
                raise ValueError("chapter_id must belong to the same project")
        if scene_id is not None:
            scene = self.get_scene_plan(scene_id)
            if scene.project_id != project_id:
                raise ValueError("scene_id must belong to the same project")
        if current_draft_artifact_id is not None:
            draft = self.get_draft_artifact(current_draft_artifact_id)
            if draft.project_id != project_id:
                raise ValueError("current_draft_artifact_id must belong to the same project")
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO manuscript_documents (
                    document_id, project_id, title, content, chapter_id, scene_id, current_draft_artifact_id,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    content = excluded.content,
                    chapter_id = excluded.chapter_id,
                    scene_id = excluded.scene_id,
                    current_draft_artifact_id = excluded.current_draft_artifact_id,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    document_id,
                    project_id,
                    title,
                    content,
                    chapter_id,
                    scene_id,
                    current_draft_artifact_id,
                    int(version),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_manuscript_document(document_id)

    def get_manuscript_document(self, document_id: str) -> ManuscriptDocumentRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM manuscript_documents
                WHERE document_id = ?
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            raise KeyError(document_id)
        return _manuscript_document_row_to_record(row)

    def list_manuscript_documents(self, project_id: str) -> list[ManuscriptDocumentRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM manuscript_documents
                WHERE project_id = ?
                ORDER BY title COLLATE NOCASE, document_id
                """,
                (project_id,),
            ).fetchall()
        return [_manuscript_document_row_to_record(row) for row in rows]

    def upsert_revision_suggestion(
        self,
        *,
        suggestion_id: str,
        project_id: str,
        target_document_id: str,
        source_text: str,
        proposed_text: str,
        rationale: str,
        source_context: Sequence[str] | None = None,
        status: StorySuggestionLifecycleState = StorySuggestionLifecycleState.REQUESTED,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> RevisionSuggestionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        document = self.get_manuscript_document(target_document_id)
        if document.project_id != project_id:
            raise ValueError("target_document_id must belong to the same project")
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO revision_suggestions (
                    suggestion_id, project_id, target_document_id, source_text, proposed_text, rationale,
                    source_context_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(suggestion_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    target_document_id = excluded.target_document_id,
                    source_text = excluded.source_text,
                    proposed_text = excluded.proposed_text,
                    rationale = excluded.rationale,
                    source_context_json = excluded.source_context_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    suggestion_id,
                    project_id,
                    target_document_id,
                    source_text,
                    proposed_text,
                    rationale,
                    _json_list(list(source_context or [])),
                    status.value if isinstance(status, StorySuggestionLifecycleState) else str(status),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_revision_suggestion(suggestion_id)

    def get_revision_suggestion(self, suggestion_id: str) -> RevisionSuggestionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE suggestion_id = ?
                """,
                (suggestion_id,),
            ).fetchone()
        if row is None:
            raise KeyError(suggestion_id)
        return _revision_suggestion_row_to_record(row)

    def list_revision_suggestions(self, project_id: str) -> list[RevisionSuggestionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE project_id = ?
                ORDER BY suggestion_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_revision_suggestion_row_to_record(row) for row in rows]

    def list_revision_suggestions_for_document(self, project_id: str, *, target_document_id: str) -> list[RevisionSuggestionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM revision_suggestions
                WHERE project_id = ? AND target_document_id = ?
                ORDER BY suggestion_id ASC
                """,
                (project_id, target_document_id),
            ).fetchall()
        return [_revision_suggestion_row_to_record(row) for row in rows]

    def _next_foundation_revision_number(self, project_id: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(revision_number), 0) AS revision_number FROM foundation_revisions WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return int(row["revision_number"]) + 1

    def _persist_arc_candidate(
        self,
        project_id: str,
        candidate: ArcCandidate | ArcCandidateRecord | Mapping[str, Any],
        *,
        created_at: datetime,
        updated_at: datetime,
    ) -> ArcCandidateRecord:
        normalized = _coerce_arc_candidate(project_id, candidate)
        return self.upsert_arc_candidate(
            project_id=normalized.project_id,
            arc_id=normalized.arc_id,
            name=normalized.name,
            summary=normalized.summary,
            stage_map_notes=normalized.stage_map_notes,
            fit_notes=normalized.fit_notes,
            tags=normalized.tags,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _persist_arc_stage_map(
        self,
        project_id: str,
        stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any] | None,
        *,
        created_at: datetime,
        updated_at: datetime,
    ) -> ArcStageMapRecord | None:
        if stage_map is None:
            return None
        normalized = _coerce_arc_stage_map(project_id, stage_map)
        self.upsert_arc_stage_map(
            project_id=normalized.project_id,
            arc_id=normalized.arc_id,
            stage_kinds=normalized.stage_kinds,
            notes=normalized.notes,
            arc_stage_map_id=normalized.arc_stage_map_id,
            created_at=created_at,
            updated_at=updated_at,
        )
        return self.get_arc_stage_map(project_id, arc_id=normalized.arc_id)

    def _append_relationship_edge_to_character_map(
        self,
        connection,
        *,
        source_character_id: str,
        target_character_id: str,
        edge_id: str,
        updated_at: datetime,
    ) -> None:
        for character_id in (source_character_id, target_character_id):
            row = connection.execute(
                """
                SELECT relationship_map_json
                FROM character_profiles
                WHERE character_id = ?
                """,
                (character_id,),
            ).fetchone()
            if row is None:
                continue
            existing = _parse_json_list(row["relationship_map_json"])
            if edge_id in existing:
                continue
            existing.append(edge_id)
            connection.execute(
                """
                UPDATE character_profiles
                SET relationship_map_json = ?, updated_at = ?
                WHERE character_id = ?
                """,
                (_json_list(existing), updated_at.isoformat(), character_id),
            )


def _relationship_edge_row_to_record(row) -> RelationshipEdgeRecord:
    return RelationshipEdgeRecord(
        edge_id=row["edge_id"],
        project_id=row["project_id"],
        source_character_id=row["source_character_id"],
        target_character_id=row["target_character_id"],
        relation_kind=row["relation_kind"],
        summary=row["summary"],
        tension=row["tension"],
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_candidate_row_to_record(row) -> ArcCandidateRecord:
    return ArcCandidateRecord(
        arc_id=row["arc_id"],
        project_id=row["project_id"],
        name=row["name"],
        summary=row["summary"],
        stage_map_notes=_parse_json_list(row["stage_map_notes_json"]),
        fit_notes=_parse_json_list(row["fit_notes_json"]),
        tags=_parse_json_list(row["tags_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_stage_map_row_to_record(row) -> ArcStageMapRecord:
    return ArcStageMapRecord(
        arc_stage_map_id=row["arc_stage_map_id"],
        project_id=row["project_id"],
        arc_id=row["arc_id"],
        stage_kinds=_parse_json_list(row["stage_kinds_json"]),
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_selection_row_to_record(row, *, repository: StoryDevelopmentRepository | None = None) -> ArcSelectionRecord:
    selected_arc = _arc_candidate_record_from_json(row["selected_arc_json"])
    comparison_record_ids = repository._arc_selection_comparison_ids(row["selection_id"]) if repository is not None else []
    stage_map = None
    if repository is not None and row["stage_map_id"] is not None:
        try:
            stage_map = repository.get_arc_stage_map(row["project_id"], arc_id=selected_arc.arc_id)
        except KeyError:
            stage_map = None
    return ArcSelectionRecord(
        selection_id=row["selection_id"],
        project_id=row["project_id"],
        selected_arc_id=row["selected_arc_id"],
        selected_arc=selected_arc,
        rejected_arc_ids=_parse_json_list(row["rejected_candidate_ids_json"]),
        comparison_notes=_parse_json_list(row["comparison_notes_json"]),
        comparison_record_ids=comparison_record_ids,
        stage_map_id=row["stage_map_id"],
        stage_map=stage_map,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _story_decision_node_link_records(value: str | None) -> list[StoryDecisionNodeLinkRecord]:
    return [
        StoryDecisionNodeLinkRecord(
            object_type=str(item.get("object_type") or item.get("subject_type") or item.get("object_kind") or ""),
            object_id=str(item.get("object_id") or item.get("subject_id") or ""),
            relation_kind=str(item.get("relation_kind") or "related"),
        )
        for item in _parse_json_objects(value)
    ]


def _story_decision_node_row_to_record(row) -> StoryDecisionNodeRecord:
    return StoryDecisionNodeRecord(
        node_record_id=row["node_record_id"],
        node_id=row["node_id"],
        project_id=row["project_id"],
        node_type=row["node_type"],
        change_type=row["change_type"],
        subject_type=row["subject_type"],
        subject_id=row["subject_id"],
        parent_node_id=row["parent_node_id"],
        branch_id=row["branch_id"],
        summary=row["summary"],
        prior_state_ref=row["prior_state_ref"],
        prior_state_summary=row["prior_state_summary"],
        new_state_ref=row["new_state_ref"],
        new_state_summary=row["new_state_summary"],
        reason_or_note=row["reason_or_note"],
        decision_made_at=datetime.fromisoformat(row["decision_made_at"]),
        made_by=row["made_by"],
        related_object_links=_story_decision_node_link_records(row["related_object_links_json"]),
        informing_object_links=_story_decision_node_link_records(row["informing_object_links_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _checker_finding_row_to_record(row) -> CheckerFindingRecord:
    return CheckerFindingRecord(
        finding_id=row["finding_id"],
        project_id=row["project_id"],
        source_object_id=row["source_object_id"],
        source_object_kind=row["source_object_kind"],
        severity=row["severity"],
        summary=row["summary"],
        details=row["details"],
        source_context=_parse_json_list(row["source_context_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _review_decision_row_to_record(row) -> ReviewDecisionRecord:
    return ReviewDecisionRecord(
        decision_id=row["decision_id"],
        project_id=row["project_id"],
        target_id=row["target_id"],
        target_kind=row["target_kind"],
        decision=row["decision"],
        notes=row["notes"],
        source_context=_parse_json_list(row["source_context_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _inspect_run_link_row_to_record(row) -> InspectRunLinkRecord:
    attempt_number = row["attempt_number"]
    return InspectRunLinkRecord(
        link_id=row["link_id"],
        project_id=row["project_id"],
        object_kind=row["object_kind"],
        object_id=row["object_id"],
        logical_run_id=row["logical_run_id"],
        run_id=row["run_id"],
        run_kind=row["run_kind"],
        attempt_number=int(attempt_number) if attempt_number is not None else None,
        label=row["label"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _draft_artifact_row_to_record(row) -> DraftArtifactRecord:
    return DraftArtifactRecord(
        artifact_id=row["artifact_id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        source_plan_ids=_parse_json_list(row["source_plan_ids_json"]),
        source_context=_parse_json_list(row["source_context_json"]),
        provenance_note=row["provenance_note"],
        status=StoryArtifactLifecycleState(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _manuscript_document_row_to_record(row) -> ManuscriptDocumentRecord:
    return ManuscriptDocumentRecord(
        document_id=row["document_id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        chapter_id=row["chapter_id"],
        scene_id=row["scene_id"],
        current_draft_artifact_id=row["current_draft_artifact_id"],
        version=int(row["version"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _revision_suggestion_row_to_record(row) -> RevisionSuggestionRecord:
    return RevisionSuggestionRecord(
        suggestion_id=row["suggestion_id"],
        project_id=row["project_id"],
        target_document_id=row["target_document_id"],
        source_text=row["source_text"],
        proposed_text=row["proposed_text"],
        rationale=row["rationale"],
        source_context=_parse_json_list(row["source_context_json"]),
        status=StorySuggestionLifecycleState(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_candidate_record_to_mapping(record: ArcCandidateRecord) -> dict[str, Any]:
    return {
        "arc_id": record.arc_id,
        "project_id": record.project_id,
        "name": record.name,
        "summary": record.summary,
        "stage_map_notes": list(record.stage_map_notes),
        "fit_notes": list(record.fit_notes),
        "tags": list(record.tags),
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def _arc_candidate_record_from_mapping(value: Mapping[str, Any]) -> ArcCandidateRecord:
    candidate_payload = {
        key: value[key]
        for key in ("arc_id", "project_id", "name", "summary", "stage_map_notes", "fit_notes", "tags")
        if key in value
    }
    candidate = ArcCandidate.model_validate(candidate_payload)
    return ArcCandidateRecord(
        arc_id=candidate.arc_id,
        project_id=candidate.project_id,
        name=candidate.name,
        summary=candidate.summary,
        stage_map_notes=list(candidate.stage_map_notes),
        fit_notes=list(candidate.fit_notes),
        tags=list(candidate.tags),
        created_at=datetime.fromisoformat(str(value["created_at"])) if "created_at" in value else datetime.now(UTC),
        updated_at=datetime.fromisoformat(str(value["updated_at"])) if "updated_at" in value else datetime.now(UTC),
    )


def _arc_candidate_record_from_json(value: str) -> ArcCandidateRecord:
    return _arc_candidate_record_from_mapping(json.loads(value))


def _arc_comparison_candidate_record_to_mapping(record: ArcComparisonCandidateRecord) -> dict[str, Any]:
    return {
        "candidate": _arc_candidate_record_to_mapping(record.candidate),
        "rank": record.rank,
        "score": list(record.score),
        "notes": list(record.notes),
    }


def _arc_comparison_candidate_record_from_mapping(value: Mapping[str, Any]) -> ArcComparisonCandidateRecord:
    if "candidate" in value and isinstance(value["candidate"], Mapping):
        candidate_mapping = value["candidate"]
    else:
        candidate_mapping = value
    candidate = _arc_candidate_record_from_mapping(candidate_mapping)
    rank = int(value.get("rank", 0))
    score_raw = value.get("score", (0, 0, 0, 0))
    if isinstance(score_raw, (list, tuple)):
        score_values = list(score_raw)
    else:
        score_values = [score_raw]
    score = tuple(int(item) for item in score_values)
    if len(score) != 4:
        raise ValueError("score must contain four integers")
    notes = _parse_notes(value.get("notes", []))
    return ArcComparisonCandidateRecord(
        candidate=candidate,
        rank=rank,
        score=score,  # type: ignore[arg-type]
        notes=notes,
    )


def _arc_comparison_row_to_record(row) -> ArcComparisonRecord:
    candidate_set = [
        _arc_candidate_record_from_mapping(item)
        for item in _parse_json_objects(row["candidate_set_json"])
    ]
    ranked_candidates = [
        _arc_comparison_candidate_record_from_mapping(item)
        for item in _parse_json_objects(row["ranked_candidates_json"])
    ]
    return ArcComparisonRecord(
        comparison_id=row["comparison_id"],
        project_id=row["project_id"],
        candidate_ids=_parse_json_list(row["candidate_ids_json"]),
        candidate_set=candidate_set,
        ranked_candidates=ranked_candidates,
        review_notes=_parse_json_list(row["review_notes_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _coerce_arc_candidate(project_id: str, candidate: ArcCandidate | ArcCandidateRecord | Mapping[str, Any]) -> ArcCandidateRecord:
    if isinstance(candidate, ArcCandidateRecord):
        if candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return candidate
    if isinstance(candidate, ArcCandidate):
        if candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return ArcCandidateRecord(
            arc_id=candidate.arc_id,
            project_id=candidate.project_id,
            name=candidate.name,
            summary=candidate.summary,
            stage_map_notes=list(candidate.stage_map_notes),
            fit_notes=list(candidate.fit_notes),
            tags=list(candidate.tags),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    normalized = ArcCandidate.model_validate(
        {
            key: candidate[key]
            for key in ("arc_id", "project_id", "name", "summary", "stage_map_notes", "fit_notes", "tags")
            if key in candidate
        }
    )
    if normalized.project_id != project_id:
        raise ValueError("candidate.project_id must match the selected project")
    return ArcCandidateRecord(
        arc_id=normalized.arc_id,
        project_id=normalized.project_id,
        name=normalized.name,
        summary=normalized.summary,
        stage_map_notes=list(normalized.stage_map_notes),
        fit_notes=list(normalized.fit_notes),
        tags=list(normalized.tags),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _coerce_arc_comparison_candidate(
    project_id: str,
    candidate: ArcComparisonCandidateRecord | Mapping[str, Any],
) -> ArcComparisonCandidateRecord:
    if isinstance(candidate, ArcComparisonCandidateRecord):
        if candidate.candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return candidate
    normalized = _arc_comparison_candidate_record_from_mapping(candidate)
    if normalized.candidate.project_id != project_id:
        raise ValueError("candidate.project_id must match the selected project")
    return normalized


def _rank_arc_comparison_candidates(candidates: Sequence[ArcCandidateRecord]) -> list[ArcComparisonCandidateRecord]:
    scored = [
        (
            _candidate_score(candidate),
            candidate,
            _candidate_notes(candidate),
        )
        for candidate in _unique_arc_candidate_records(list(candidates))
    ]
    scored.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2], item[0][3], item[1].arc_id))
    return [
        ArcComparisonCandidateRecord(candidate=candidate, rank=index, score=score, notes=list(notes))
        for index, (score, candidate, notes) in enumerate(scored, start=1)
    ]


def _unique_arc_candidate_records(candidates: Sequence[ArcCandidateRecord]) -> list[ArcCandidateRecord]:
    unique: dict[str, ArcCandidateRecord] = {}
    for candidate in candidates:
        unique.setdefault(candidate.arc_id, candidate)
    return list(unique.values())


def _unique_arc_comparison_ranked_candidates(
    candidates: Sequence[ArcComparisonCandidateRecord],
) -> list[ArcComparisonCandidateRecord]:
    unique: dict[str, ArcComparisonCandidateRecord] = {}
    ordered = sorted(candidates, key=lambda item: (item.rank, item.candidate.arc_id))
    for candidate in ordered:
        unique.setdefault(candidate.candidate.arc_id, candidate)
    return list(unique.values())


def _candidate_score(candidate: ArcCandidateRecord) -> tuple[int, int, int, int]:
    return (
        len(candidate.stage_map_notes),
        len(candidate.fit_notes),
        len(candidate.tags),
        -len(candidate.summary.split()),
    )


def _candidate_notes(candidate: ArcCandidateRecord) -> tuple[str, ...]:
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


def _normalize_text_list(values: Sequence[str] | None, *, field_name: str) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a list of strings")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{field_name} must not contain blank values")
        if stripped in seen:
            continue
        seen.add(stripped)
        normalized.append(stripped)
    return normalized


def _parse_notes(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_arc_stage_map(
    project_id: str,
    stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any],
) -> ArcStageMapRecord:
    if isinstance(stage_map, ArcStageMapRecord):
        if stage_map.project_id != project_id:
            raise ValueError("stage_map.project_id must match the selected project")
        return stage_map
    if isinstance(stage_map, ArcStageMap):
        if stage_map.project_id != project_id:
            raise ValueError("stage_map.project_id must match the selected project")
        return ArcStageMapRecord(
            arc_stage_map_id=stage_map.arc_stage_map_id,
            project_id=stage_map.project_id,
            arc_id=stage_map.arc_id,
            stage_kinds=list(stage_map.stage_kinds),
            notes=stage_map.notes,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    normalized = ArcStageMap.model_validate(
        {
            key: stage_map[key]
            for key in ("arc_stage_map_id", "project_id", "arc_id", "stage_kinds", "notes")
            if key in stage_map
        }
    )
    if normalized.project_id != project_id:
        raise ValueError("stage_map.project_id must match the selected project")
    return ArcStageMapRecord(
        arc_stage_map_id=normalized.arc_stage_map_id,
        project_id=normalized.project_id,
        arc_id=normalized.arc_id,
        stage_kinds=list(normalized.stage_kinds),
        notes=normalized.notes,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _beat_plan_row_to_record(row) -> BeatPlanRecord:
    return BeatPlanRecord(
        beat_id=row["beat_id"],
        project_id=row["project_id"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        dependency_ids=_parse_json_list(row["dependency_ids_json"]),
        arc_stage=row["arc_stage"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _sequence_plan_row_to_record(row) -> SequencePlanRecord:
    return SequencePlanRecord(
        sequence_id=row["sequence_id"],
        project_id=row["project_id"],
        title=row["title"],
        summary=row["summary"],
        beat_ids=_parse_json_list(row["beat_ids_json"]),
        chapter_ids=_parse_json_list(row["chapter_ids_json"]),
        status=row["status"],
        position=int(row["position"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _chapter_plan_row_to_record(row) -> ChapterPlanRecord:
    return ChapterPlanRecord(
        chapter_id=row["chapter_id"],
        project_id=row["project_id"],
        sequence_id=row["sequence_id"],
        title=row["title"],
        summary=row["summary"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _scene_plan_row_to_record(row) -> ScenePlanRecord:
    return ScenePlanRecord(
        scene_id=row["scene_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        title=row["title"],
        summary=row["summary"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _chapter_packet_row_to_record(row) -> ChapterPacketRecord:
    return ChapterPacketRecord(
        packet_id=row["packet_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        included_reference_ids=_parse_json_list(row["included_reference_ids_json"]),
        constraints=_parse_json_list(row["constraints_json"]),
        scene_goals=_parse_json_list(row["scene_goals_json"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _planning_dependency_row_to_record(row) -> PlanningDependencyRecord:
    return PlanningDependencyRecord(
        dependency_id=row["dependency_id"],
        project_id=row["project_id"],
        upstream_id=row["upstream_id"],
        downstream_id=row["downstream_id"],
        dependency_kind=row["dependency_kind"],
        reason=row["reason"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _stage_row_to_record(row) -> StoryFlowStageRecord:
    return StoryFlowStageRecord(
        stage_id=int(row["stage_id"]),
        project_id=row["project_id"],
        stage_key=row["stage_key"],
        stage_kind=row["stage_kind"],
        is_custom=bool(row["is_custom"]),
        display_name=row["display_name"],
        description=row["description"],
        position=int(row["position"]),
        depends_on=_parse_json_list(row["depends_on_json"]),
        stage_configuration_state=StoryFlowStageConfigurationState(row["stage_configuration_state"]),
        stage_progress_state=StoryFlowStageProgressState(row["stage_progress_state"]),
        writer_notes=row["writer_notes"],
        custom_prompt_guidance=row["custom_prompt_guidance"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _brainstorm_row_to_record(row) -> BrainstormItemRecord:
    return BrainstormItemRecord(
        item_id=int(row["item_id"]),
        project_id=row["project_id"],
        cluster_key=row["cluster_key"],
        content=row["content"],
        item_state=row["item_state"],
        tags=_parse_json_list(row["tags_json"]),
        source_artifact_refs=_parse_json_list(row["source_artifact_refs_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _foundation_revision_row_to_record(row) -> FoundationRevisionRecord:
    return FoundationRevisionRecord(
        revision_id=int(row["revision_id"]),
        project_id=row["project_id"],
        revision_number=int(row["revision_number"]),
        premise=row["premise"],
        logline=row["logline"],
        thematic_spine=row["thematic_spine"],
        emotional_promise=row["emotional_promise"],
        tone_direction=row["tone_direction"],
        target_audience=row["target_audience"],
        narrative_constraints=_parse_json_list(row["narrative_constraints_json"]),
        complexity_level=row["complexity_level"],
        success_definition=row["success_definition"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _character_row_to_record(row) -> CharacterProfileRecord:
    return CharacterProfileRecord(
        character_id=row["character_id"],
        project_id=row["project_id"],
        display_name=row["display_name"],
        role_in_story=row["role_in_story"],
        archetype=row["archetype"],
        external_goal=row["external_goal"],
        internal_need=row["internal_need"],
        misbelief_or_wound=row["misbelief_or_wound"],
        core_fear=row["core_fear"],
        primary_strength=row["primary_strength"],
        fatal_flaw_or_limitation=row["fatal_flaw_or_limitation"],
        contradictions=_parse_json_list(row["contradictions_json"]),
        backstory_summary=row["backstory_summary"],
        voice_notes=row["voice_notes"],
        relationship_map=_parse_json_list(row["relationship_map_json"]),
        secrets=_parse_json_list(row["secrets_json"]),
        values=_parse_json_list(row["values_json"]),
        taboos=_parse_json_list(row["taboos_json"]),
        change_axis=row["change_axis"],
        arc_stage_notes=row["arc_stage_notes"],
        continuity_facts=_parse_json_list(row["continuity_facts_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _world_bible_row_to_record(row) -> WorldBibleEntryRecord:
    return WorldBibleEntryRecord(
        entry_id=int(row["entry_id"]),
        project_id=row["project_id"],
        entry_type=row["entry_type"],
        title=row["title"],
        summary=row["summary"],
        canonical_facts=_parse_json_list(row["canonical_facts_json"]),
        related_character_ids=_parse_json_list(row["related_character_ids_json"]),
        visibility_scope=row["visibility_scope"],
        source_artifacts=_parse_json_list(row["source_artifacts_json"]),
        continuity_warnings=_parse_json_list(row["continuity_warnings_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
