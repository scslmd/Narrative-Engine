from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    json_objects as _json_objects,
    now as _now,
)
from . import (
    BranchComparisonRecord, BranchMergeDecisionRecord, BranchPointRecord,
    BranchStateRefRecord, StoryBranchRecord, StoryBranchState,
    StoryDecisionNodeRecord, StoryObjectType,
)
from .converters import (
    _normalize_text_list,
    _story_decision_node_row_to_record, _branch_point_row_to_record,
    _story_branch_row_to_record, _branch_state_ref_row_to_record,
    _branch_comparison_row_to_record, _branch_merge_decision_row_to_record,
)

from ..sqlite import connect


class _DecisionNodeMixin:

    def __init__(self, db_path):

        self.db_path = db_path



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


class _BranchPointMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_branch_point(
        self,
        *,
        branch_point_id: str,
        project_id: str,
        source_node_id: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BranchPointRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO branch_points (
                    branch_point_id, project_id, source_node_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(branch_point_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_node_id = excluded.source_node_id,
                    updated_at = excluded.updated_at
                """,
                (
                    branch_point_id,
                    project_id,
                    source_node_id,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_branch_point(branch_point_id)



    def get_branch_point(self, branch_point_id: str) -> BranchPointRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_points
                WHERE branch_point_id = ?
                """,
                (branch_point_id,),
            ).fetchone()
        if row is None:
            raise KeyError(branch_point_id)
        return _branch_point_row_to_record(row)



    def get_branch_point_for_source_node(self, project_id: str, *, source_node_id: str) -> BranchPointRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_points
                WHERE project_id = ? AND source_node_id = ?
                """,
                (project_id, source_node_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, source_node_id))
        return _branch_point_row_to_record(row)



    def list_branch_points(self, project_id: str) -> list[BranchPointRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM branch_points
                WHERE project_id = ?
                ORDER BY created_at ASC, branch_point_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_branch_point_row_to_record(row) for row in rows]


class _StoryBranchMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_story_branch(
        self,
        *,
        branch_id: str,
        project_id: str,
        branch_point_id: str,
        branch_name: str,
        branch_state: StoryBranchState | str = StoryBranchState.ACTIVE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryBranchRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_state = self._normalize_branch_state(branch_state)
        branch_point = self.get_branch_point(branch_point_id)
        if branch_point.project_id != project_id:
            raise ValueError("branch_point_id must belong to the same project as the branch")
        with connect(self.db_path) as connection:
            if normalized_state == StoryBranchState.ACTIVE:
                connection.execute(
                    """
                    UPDATE story_branches
                    SET branch_state = ?, updated_at = ?
                    WHERE project_id = ? AND branch_state = ? AND branch_id <> ?
                    """,
                    (
                        StoryBranchState.ARCHIVED.value,
                        updated.isoformat(),
                        project_id,
                        StoryBranchState.ACTIVE.value,
                        branch_id,
                    ),
                )
            connection.execute(
                """
                INSERT INTO story_branches (
                    branch_id, project_id, branch_point_id, branch_name, branch_state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(branch_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    branch_point_id = excluded.branch_point_id,
                    branch_name = excluded.branch_name,
                    branch_state = excluded.branch_state,
                    updated_at = excluded.updated_at
                """,
                (
                    branch_id,
                    project_id,
                    branch_point_id,
                    branch_name,
                    normalized_state.value,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_story_branch(branch_id)



    def get_story_branch(self, branch_id: str) -> StoryBranchRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM story_branches
                WHERE branch_id = ?
                """,
                (branch_id,),
            ).fetchone()
        if row is None:
            raise KeyError(branch_id)
        return _story_branch_row_to_record(row)



    def list_story_branches(self, project_id: str) -> list[StoryBranchRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM story_branches
                WHERE project_id = ?
                ORDER BY created_at ASC, branch_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_story_branch_row_to_record(row) for row in rows]



    def get_active_story_branch(self, project_id: str) -> StoryBranchRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM story_branches
                WHERE project_id = ? AND branch_state = ?
                ORDER BY created_at ASC, branch_id ASC
                LIMIT 1
                """,
                (project_id, StoryBranchState.ACTIVE.value),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return _story_branch_row_to_record(row)



    def set_active_story_branch(self, project_id: str, *, branch_id: str) -> StoryBranchRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        branch = self.get_story_branch(normalized_branch_id)
        if branch.project_id != normalized_project_id:
            raise KeyError(normalized_branch_id)
        updated_at = _now()
        with connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE story_branches
                SET branch_state = ?, updated_at = ?
                WHERE project_id = ? AND branch_state = ? AND branch_id <> ?
                """,
                (
                    StoryBranchState.ARCHIVED.value,
                    updated_at.isoformat(),
                    normalized_project_id,
                    StoryBranchState.ACTIVE.value,
                    normalized_branch_id,
                ),
            )
            connection.execute(
                """
                UPDATE story_branches
                SET branch_state = ?, updated_at = ?
                WHERE project_id = ? AND branch_id = ?
                """,
                (
                    StoryBranchState.ACTIVE.value,
                    updated_at.isoformat(),
                    normalized_project_id,
                    normalized_branch_id,
                ),
            )
            connection.commit()
        return self.get_story_branch(normalized_branch_id)


class _BranchStateRefMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_branch_state_ref(
        self,
        *,
        branch_state_ref_id: str,
        project_id: str,
        branch_id: str,
        state_object_type: StoryObjectType | str,
        state_object_id: str,
        decision_node_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BranchStateRefRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        normalized_state_object_type = self._normalize_story_object_type(
            state_object_type,
            field_name="state_object_type",
        )
        normalized_state_object_id = self._normalize_text(state_object_id, field_name="state_object_id")
        normalized_decision_node_id = self._normalize_optional_text(decision_node_id, field_name="decision_node_id")
        branch = self.get_story_branch(normalized_branch_id)
        if branch.project_id != normalized_project_id:
            raise KeyError(normalized_branch_id)
        if normalized_decision_node_id is not None:
            try:
                decision_node = self.get_story_decision_node(normalized_project_id, node_id=normalized_decision_node_id)
            except KeyError as exc:
                raise KeyError(normalized_decision_node_id) from exc
            if decision_node.project_id != normalized_project_id:
                raise KeyError(normalized_decision_node_id)
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO branch_state_refs (
                    branch_state_ref_id, project_id, branch_id, state_object_type, state_object_id, decision_node_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(branch_state_ref_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    branch_id = excluded.branch_id,
                    state_object_type = excluded.state_object_type,
                    state_object_id = excluded.state_object_id,
                    decision_node_id = excluded.decision_node_id,
                    updated_at = excluded.updated_at
                """,
                (
                    branch_state_ref_id,
                    normalized_project_id,
                    normalized_branch_id,
                    normalized_state_object_type.value,
                    normalized_state_object_id,
                    normalized_decision_node_id,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_branch_state_ref(branch_state_ref_id)



    def get_branch_state_ref(self, branch_state_ref_id: str) -> BranchStateRefRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_state_refs
                WHERE branch_state_ref_id = ?
                """,
                (branch_state_ref_id,),
            ).fetchone()
        if row is None:
            raise KeyError(branch_state_ref_id)
        return _branch_state_ref_row_to_record(row)



    def list_branch_state_refs(self, project_id: str, *, branch_id: str | None = None) -> list[BranchStateRefRecord]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        if branch_id is None:
            query = """
                SELECT *
                FROM branch_state_refs
                WHERE project_id = ?
                ORDER BY created_at ASC, branch_id ASC, branch_state_ref_id ASC
            """
            params = (normalized_project_id,)
        else:
            normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
            query = """
                SELECT *
                FROM branch_state_refs
                WHERE project_id = ? AND branch_id = ?
                ORDER BY created_at ASC, state_object_type ASC, state_object_id ASC, branch_state_ref_id ASC
            """
            params = (normalized_project_id, normalized_branch_id)
        with connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [_branch_state_ref_row_to_record(row) for row in rows]



    def get_branch_state_ref_for_object(
        self,
        project_id: str,
        *,
        branch_id: str,
        state_object_type: StoryObjectType | str,
        state_object_id: str,
    ) -> BranchStateRefRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        normalized_state_object_type = self._normalize_story_object_type(
            state_object_type,
            field_name="state_object_type",
        )
        normalized_state_object_id = self._normalize_text(state_object_id, field_name="state_object_id")
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_state_refs
                WHERE project_id = ? AND branch_id = ? AND state_object_type = ? AND state_object_id = ?
                """,
                (
                    normalized_project_id,
                    normalized_branch_id,
                    normalized_state_object_type.value,
                    normalized_state_object_id,
                ),
            ).fetchone()
        if row is None:
            raise KeyError((normalized_project_id, normalized_branch_id, normalized_state_object_type.value, normalized_state_object_id))
        return _branch_state_ref_row_to_record(row)



    def list_branch_state_refs_for_decision_node(
        self,
        project_id: str,
        *,
        branch_id: str,
        decision_node_id: str,
    ) -> list[BranchStateRefRecord]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        normalized_decision_node_id = self._normalize_text(decision_node_id, field_name="decision_node_id")
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM branch_state_refs
                WHERE project_id = ? AND branch_id = ? AND decision_node_id = ?
                ORDER BY created_at ASC, state_object_type ASC, state_object_id ASC, branch_state_ref_id ASC
                """,
                (normalized_project_id, normalized_branch_id, normalized_decision_node_id),
            ).fetchall()
        return [_branch_state_ref_row_to_record(row) for row in rows]


class _BranchComparisonMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_branch_comparison(
        self,
        *,
        comparison_id: str,
        project_id: str,
        source_branch_id: str,
        target_branch_id: str,
        review_notes: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BranchComparisonRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_source_branch_id = self._normalize_text(source_branch_id, field_name="source_branch_id")
        normalized_target_branch_id = self._normalize_text(target_branch_id, field_name="target_branch_id")
        if normalized_source_branch_id == normalized_target_branch_id:
            raise ValueError("source_branch_id and target_branch_id must differ")
        source_branch = self.get_story_branch(normalized_source_branch_id)
        target_branch = self.get_story_branch(normalized_target_branch_id)
        if source_branch.project_id != normalized_project_id or target_branch.project_id != normalized_project_id:
            raise KeyError((normalized_project_id, normalized_source_branch_id, normalized_target_branch_id))
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO branch_comparisons (
                    comparison_id, project_id, source_branch_id, target_branch_id, review_notes_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comparison_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_branch_id = excluded.source_branch_id,
                    target_branch_id = excluded.target_branch_id,
                    review_notes_json = excluded.review_notes_json,
                    updated_at = excluded.updated_at
                """,
                (
                    comparison_id,
                    normalized_project_id,
                    normalized_source_branch_id,
                    normalized_target_branch_id,
                    _json_list(_normalize_text_list(review_notes, field_name="review_notes")),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_branch_comparison(normalized_project_id, comparison_id=comparison_id)



    def get_branch_comparison(self, project_id: str, *, comparison_id: str) -> BranchComparisonRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_comparison_id = self._normalize_text(comparison_id, field_name="comparison_id")
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_comparisons
                WHERE project_id = ? AND comparison_id = ?
                """,
                (normalized_project_id, normalized_comparison_id),
            ).fetchone()
        if row is None:
            raise KeyError((normalized_project_id, normalized_comparison_id))
        return _branch_comparison_row_to_record(row)



    def list_branch_comparisons(self, project_id: str) -> list[BranchComparisonRecord]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM branch_comparisons
                WHERE project_id = ?
                ORDER BY created_at ASC, comparison_id ASC
                """,
                (normalized_project_id,),
            ).fetchall()
        return [_branch_comparison_row_to_record(row) for row in rows]


class _BranchMergeDecisionMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_branch_merge_decision(
        self,
        *,
        merge_decision_id: str,
        project_id: str,
        source_branch_id: str,
        target_branch_id: str,
        merge_rationale: str,
        resulting_decision_node_ids: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BranchMergeDecisionRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_source_branch_id = self._normalize_text(source_branch_id, field_name="source_branch_id")
        normalized_target_branch_id = self._normalize_text(target_branch_id, field_name="target_branch_id")
        normalized_merge_rationale = self._normalize_text(merge_rationale, field_name="merge_rationale")
        normalized_resulting_decision_node_ids = _normalize_text_list(
            list(resulting_decision_node_ids or []),
            field_name="resulting_decision_node_ids",
        )
        if normalized_source_branch_id == normalized_target_branch_id:
            raise ValueError("source_branch_id and target_branch_id must differ")
        if len(set(normalized_resulting_decision_node_ids)) != len(normalized_resulting_decision_node_ids):
            raise ValueError("resulting_decision_node_ids must not contain duplicates")
        source_branch = self.get_story_branch(normalized_source_branch_id)
        target_branch = self.get_story_branch(normalized_target_branch_id)
        if source_branch.project_id != normalized_project_id or target_branch.project_id != normalized_project_id:
            raise KeyError((normalized_project_id, normalized_source_branch_id, normalized_target_branch_id))
        for decision_node_id in normalized_resulting_decision_node_ids:
            decision_node = self.get_story_decision_node(normalized_project_id, node_id=decision_node_id)
            if decision_node.project_id != normalized_project_id:
                raise KeyError(decision_node_id)
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO branch_merge_decisions (
                    merge_decision_id, project_id, source_branch_id, target_branch_id, merge_rationale,
                    resulting_decision_node_ids_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(merge_decision_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    source_branch_id = excluded.source_branch_id,
                    target_branch_id = excluded.target_branch_id,
                    merge_rationale = excluded.merge_rationale,
                    resulting_decision_node_ids_json = excluded.resulting_decision_node_ids_json,
                    updated_at = excluded.updated_at
                """,
                (
                    merge_decision_id,
                    normalized_project_id,
                    normalized_source_branch_id,
                    normalized_target_branch_id,
                    normalized_merge_rationale,
                    _json_list(normalized_resulting_decision_node_ids),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_branch_merge_decision(normalized_project_id, merge_decision_id=merge_decision_id)



    def get_branch_merge_decision(self, project_id: str, *, merge_decision_id: str) -> BranchMergeDecisionRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_merge_decision_id = self._normalize_text(merge_decision_id, field_name="merge_decision_id")
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM branch_merge_decisions
                WHERE project_id = ? AND merge_decision_id = ?
                """,
                (normalized_project_id, normalized_merge_decision_id),
            ).fetchone()
        if row is None:
            raise KeyError((normalized_project_id, normalized_merge_decision_id))
        return _branch_merge_decision_row_to_record(row)



    def list_branch_merge_decisions(self, project_id: str) -> list[BranchMergeDecisionRecord]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM branch_merge_decisions
                WHERE project_id = ?
                ORDER BY created_at ASC, merge_decision_id ASC
                """,
                (normalized_project_id,),
            ).fetchall()
        return [_branch_merge_decision_row_to_record(row) for row in rows]
