from __future__ import annotations

from typing import Sequence

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import (
    BranchComparisonRecord,
    BranchMergeDecision,
    BranchStateRef,
    StoryBranch,
    StoryBranchState,
)


class StoryBranchingServiceError(ValueError):
    pass


class StoryBranchingNotFoundError(StoryBranchingServiceError):
    pass


class StoryBranchingValidationError(StoryBranchingServiceError):
    pass


class StoryBranchingService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def create_story_branch(
        self,
        project_id: str,
        *,
        branch_id: str,
        branch_point_id: str,
        branch_name: str,
        branch_state: StoryBranchState | str = StoryBranchState.ACTIVE,
    ) -> StoryBranch:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        normalized_branch_point_id = self._normalize_text(branch_point_id, field_name="branch_point_id")
        normalized_branch_name = self._normalize_text(branch_name, field_name="branch_name")
        normalized_branch_state = self._normalize_branch_state(branch_state, field_name="branch_state")
        try:
            record = self.repository.upsert_story_branch(
                branch_id=normalized_branch_id,
                project_id=normalized_project_id,
                branch_point_id=normalized_branch_point_id,
                branch_name=normalized_branch_name,
                branch_state=normalized_branch_state,
            )
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_branch_point_id) from exc
        except ValueError as exc:
            raise StoryBranchingValidationError(str(exc)) from exc
        return self._branch_from_record(record)

    def list_story_branches(self, project_id: str) -> tuple[StoryBranch, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self.repository.list_story_branches(normalized_project_id)
        return tuple(self._branch_from_record(record) for record in records)

    def get_story_branch(self, project_id: str, *, branch_id: str) -> StoryBranch:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        try:
            record = self.repository.get_story_branch(normalized_branch_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_branch_id) from exc
        if record.project_id != normalized_project_id:
            raise StoryBranchingNotFoundError(normalized_branch_id)
        return self._branch_from_record(record)

    def get_active_story_branch(self, project_id: str) -> StoryBranch:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        try:
            record = self.repository.get_active_story_branch(normalized_project_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_project_id) from exc
        return self._branch_from_record(record)

    def compare_story_branches(
        self,
        project_id: str,
        *,
        comparison_id: str,
        source_branch_id: str,
        target_branch_id: str,
        review_notes: Sequence[str] | None = None,
    ) -> BranchComparisonRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_comparison_id = self._normalize_text(comparison_id, field_name="comparison_id")
        normalized_source_branch_id = self._normalize_text(source_branch_id, field_name="source_branch_id")
        normalized_target_branch_id = self._normalize_text(target_branch_id, field_name="target_branch_id")
        try:
            record = self.repository.upsert_branch_comparison(
                comparison_id=normalized_comparison_id,
                project_id=normalized_project_id,
                source_branch_id=normalized_source_branch_id,
                target_branch_id=normalized_target_branch_id,
                review_notes=self._normalize_text_list(review_notes, field_name="review_notes"),
            )
        except KeyError as exc:
            raise StoryBranchingNotFoundError(
                f"{normalized_source_branch_id}:{normalized_target_branch_id}"
            ) from exc
        except ValueError as exc:
            raise StoryBranchingValidationError(str(exc)) from exc
        return self._comparison_from_record(record)

    def get_branch_comparison(self, project_id: str, *, comparison_id: str) -> BranchComparisonRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_comparison_id = self._normalize_text(comparison_id, field_name="comparison_id")
        try:
            record = self.repository.get_branch_comparison(normalized_project_id, comparison_id=normalized_comparison_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_comparison_id) from exc
        return self._comparison_from_record(record)

    def list_branch_comparisons(self, project_id: str) -> tuple[BranchComparisonRecord, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self.repository.list_branch_comparisons(normalized_project_id)
        return tuple(self._comparison_from_record(record) for record in records)

    def select_active_branch(self, project_id: str, *, branch_id: str) -> StoryBranch:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        try:
            record = self.repository.set_active_story_branch(normalized_project_id, branch_id=normalized_branch_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_branch_id) from exc
        return self._branch_from_record(record)

    def get_branch_state_ref(self, project_id: str, *, branch_state_ref_id: str) -> BranchStateRef:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_state_ref_id = self._normalize_text(branch_state_ref_id, field_name="branch_state_ref_id")
        try:
            record = self.repository.get_branch_state_ref(normalized_branch_state_ref_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_branch_state_ref_id) from exc
        if record.project_id != normalized_project_id:
            raise StoryBranchingNotFoundError(normalized_branch_state_ref_id)
        return self._branch_state_ref_from_record(record)

    def list_branch_state_refs(self, project_id: str, *, branch_id: str | None = None) -> tuple[BranchStateRef, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = None if branch_id is None else self._normalize_text(branch_id, field_name="branch_id")
        records = self.repository.list_branch_state_refs(normalized_project_id, branch_id=normalized_branch_id)
        return tuple(self._branch_state_ref_from_record(record) for record in records)

    def list_branch_state_refs_for_decision_node(
        self,
        project_id: str,
        *,
        branch_id: str,
        decision_node_id: str,
    ) -> tuple[BranchStateRef, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_branch_id = self._normalize_text(branch_id, field_name="branch_id")
        normalized_decision_node_id = self._normalize_text(decision_node_id, field_name="decision_node_id")
        records = self.repository.list_branch_state_refs_for_decision_node(
            normalized_project_id,
            branch_id=normalized_branch_id,
            decision_node_id=normalized_decision_node_id,
        )
        return tuple(self._branch_state_ref_from_record(record) for record in records)

    def record_branch_merge_decision(
        self,
        project_id: str,
        *,
        merge_decision_id: str,
        source_branch_id: str,
        target_branch_id: str,
        merge_rationale: str,
        resulting_decision_node_ids: Sequence[str] | None = None,
    ) -> BranchMergeDecision:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_merge_decision_id = self._normalize_text(merge_decision_id, field_name="merge_decision_id")
        normalized_source_branch_id = self._normalize_text(source_branch_id, field_name="source_branch_id")
        normalized_target_branch_id = self._normalize_text(target_branch_id, field_name="target_branch_id")
        normalized_merge_rationale = self._normalize_text(merge_rationale, field_name="merge_rationale")
        try:
            record = self.repository.upsert_branch_merge_decision(
                merge_decision_id=normalized_merge_decision_id,
                project_id=normalized_project_id,
                source_branch_id=normalized_source_branch_id,
                target_branch_id=normalized_target_branch_id,
                merge_rationale=normalized_merge_rationale,
                resulting_decision_node_ids=self._normalize_text_list(
                    resulting_decision_node_ids,
                    field_name="resulting_decision_node_ids",
                ),
            )
        except KeyError as exc:
            raise StoryBranchingNotFoundError(
                f"{normalized_source_branch_id}:{normalized_target_branch_id}"
            ) from exc
        except ValueError as exc:
            raise StoryBranchingValidationError(str(exc)) from exc
        return self._merge_decision_from_record(record)

    def get_branch_merge_decision(self, project_id: str, *, merge_decision_id: str) -> BranchMergeDecision:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_merge_decision_id = self._normalize_text(merge_decision_id, field_name="merge_decision_id")
        try:
            record = self.repository.get_branch_merge_decision(normalized_project_id, merge_decision_id=normalized_merge_decision_id)
        except KeyError as exc:
            raise StoryBranchingNotFoundError(normalized_merge_decision_id) from exc
        return self._merge_decision_from_record(record)

    def list_branch_merge_decisions(self, project_id: str) -> tuple[BranchMergeDecision, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self.repository.list_branch_merge_decisions(normalized_project_id)
        return tuple(self._merge_decision_from_record(record) for record in records)

    def _branch_from_record(self, record) -> StoryBranch:
        return StoryBranch.model_validate(
            {
                "branch_id": record.branch_id,
                "project_id": record.project_id,
                "branch_point_id": record.branch_point_id,
                "branch_name": record.branch_name,
                "branch_state": record.branch_state.value,
            }
        )

    def _comparison_from_record(self, record) -> BranchComparisonRecord:
        return BranchComparisonRecord.model_validate(
            {
                "comparison_id": record.comparison_id,
                "project_id": record.project_id,
                "source_branch_id": record.source_branch_id,
                "target_branch_id": record.target_branch_id,
                "review_notes": list(record.review_notes),
            }
        )

    def _merge_decision_from_record(self, record) -> BranchMergeDecision:
        return BranchMergeDecision.model_validate(
            {
                "merge_decision_id": record.merge_decision_id,
                "project_id": record.project_id,
                "source_branch_id": record.source_branch_id,
                "target_branch_id": record.target_branch_id,
                "merge_rationale": record.merge_rationale,
                "resulting_decision_node_ids": list(record.resulting_decision_node_ids),
            }
        )

    def _branch_state_ref_from_record(self, record) -> BranchStateRef:
        return BranchStateRef.model_validate(
            {
                "branch_state_ref_id": record.branch_state_ref_id,
                "project_id": record.project_id,
                "branch_id": record.branch_id,
                "state_object_type": record.state_object_type.value,
                "state_object_id": record.state_object_id,
                "decision_node_id": record.decision_node_id,
            }
        )

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _normalize_text_list(self, values: Sequence[str] | None, *, field_name: str) -> list[str]:
        if values is None:
            return []
        normalized: list[str] = []
        for value in values:
            normalized.append(self._normalize_text(value, field_name=field_name))
        if len(set(normalized)) != len(normalized):
            raise StoryBranchingValidationError(f"{field_name} must not contain duplicates")
        return normalized

    def _normalize_branch_state(self, value: StoryBranchState | str, *, field_name: str) -> StoryBranchState:
        if isinstance(value, StoryBranchState):
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            try:
                return StoryBranchState[normalized]
            except KeyError as exc:
                allowed = ", ".join(member.value for member in StoryBranchState)
                raise StoryBranchingValidationError(f"{field_name} must be one of: {allowed}") from exc
        raise TypeError(f"{field_name} must be a StoryBranchState or string")
