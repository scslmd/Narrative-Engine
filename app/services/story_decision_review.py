from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.persistence.story_development import (
    StoryDecisionNodeLinkRecord,
    StoryDecisionNodeRecord,
    StoryDevelopmentRepository,
)
from app.schemas import StoryDecisionNode, StoryDecisionNodeLink


@dataclass(frozen=True)
class StoryDecisionNodeReview:
    node: StoryDecisionNode
    parent_path: tuple[StoryDecisionNode, ...]


class StoryDecisionReviewServiceError(ValueError):
    pass


class StoryDecisionReviewNotFoundError(StoryDecisionReviewServiceError):
    pass


class StoryDecisionReviewValidationError(StoryDecisionReviewServiceError):
    pass


class StoryDecisionReviewService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def list_story_decision_nodes(
        self,
        project_id: str,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> tuple[StoryDecisionNode, ...]:
        return self.list_story_decision_nodes_for_subject(
            project_id,
            subject_type=subject_type,
            subject_id=subject_id,
        )

    def list_story_decision_nodes_for_subject(
        self,
        project_id: str,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> tuple[StoryDecisionNode, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self._list_records(normalized_project_id, subject_type=subject_type, subject_id=subject_id)
        return tuple(self._node_from_record(record) for record in records)

    def inspect_story_decision_node(self, project_id: str, *, node_id: str) -> StoryDecisionNodeReview:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_node_id = self._normalize_text(node_id, field_name="node_id")
        record = self._get_record(normalized_project_id, normalized_node_id)
        parent_path = self._ancestor_path(normalized_project_id, normalized_node_id)
        return StoryDecisionNodeReview(
            node=self._node_from_record(record),
            parent_path=tuple(self._node_from_record(item) for item in parent_path),
        )

    def get_story_decision_node(self, project_id: str, *, node_id: str) -> StoryDecisionNode:
        return self.inspect_story_decision_node(project_id, node_id=node_id).node

    def get_story_decision(self, project_id: str, *, node_id: str) -> StoryDecisionNode:
        return self.get_story_decision_node(project_id, node_id=node_id)

    def list_story_decision_path(self, project_id: str, *, node_id: str) -> tuple[StoryDecisionNode, ...]:
        review = self.inspect_story_decision_node(project_id, node_id=node_id)
        return review.parent_path + (review.node,)

    def inspect_story_decision(self, project_id: str, *, node_id: str) -> StoryDecisionNodeReview:
        return self.inspect_story_decision_node(project_id, node_id=node_id)

    def _list_records(
        self,
        project_id: str,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> list[StoryDecisionNodeRecord]:
        if subject_type is None and subject_id is None:
            return list(self.repository.list_story_decision_nodes(project_id))
        if subject_type is None or subject_id is None:
            raise StoryDecisionReviewValidationError("subject_type and subject_id must be provided together")
        normalized_subject_type = self._normalize_text(subject_type, field_name="subject_type")
        normalized_subject_id = self._normalize_text(subject_id, field_name="subject_id")
        return list(
            self.repository.list_story_decision_nodes_for_subject(
                project_id,
                subject_type=normalized_subject_type,
                subject_id=normalized_subject_id,
            )
        )

    def _get_record(self, project_id: str, node_id: str) -> StoryDecisionNodeRecord:
        try:
            return self.repository.get_story_decision_node(project_id, node_id=node_id)
        except KeyError as exc:
            raise StoryDecisionReviewNotFoundError(node_id) from exc

    def _ancestor_path(self, project_id: str, node_id: str) -> list[StoryDecisionNodeRecord]:
        records = {record.node_id: record for record in self.repository.list_story_decision_nodes(project_id)}
        if node_id not in records:
            raise StoryDecisionReviewNotFoundError(node_id)

        path: list[StoryDecisionNodeRecord] = []
        current_id = records[node_id].parent_node_id
        seen: set[str] = {node_id}
        while current_id is not None:
            if current_id in seen:
                raise StoryDecisionReviewValidationError("parent_node_id chain contains a cycle")
            seen.add(current_id)
            parent = records.get(current_id)
            if parent is None:
                raise StoryDecisionReviewValidationError(f"missing parent node {current_id!r}")
            path.append(parent)
            current_id = parent.parent_node_id
        path.reverse()
        return path

    def _node_from_record(self, record: StoryDecisionNodeRecord) -> StoryDecisionNode:
        return StoryDecisionNode.model_validate(
            {
                "node_id": record.node_id,
                "project_id": record.project_id,
                "node_type": record.node_type,
                "change_type": record.change_type,
                "subject_type": record.subject_type,
                "subject_id": record.subject_id,
                "parent_node_id": record.parent_node_id,
                "branch_id": record.branch_id,
                "summary": record.summary,
                "prior_state_ref": record.prior_state_ref,
                "prior_state_summary": record.prior_state_summary,
                "new_state_ref": record.new_state_ref,
                "new_state_summary": record.new_state_summary,
                "reason_or_note": record.reason_or_note,
                "decision_made_at": record.decision_made_at,
                "made_by": record.made_by,
                "related_object_links": [self._link_from_record(link) for link in record.related_object_links],
                "informing_object_links": [self._link_from_record(link) for link in record.informing_object_links],
            }
        )

    def _link_from_record(self, record: Mapping[str, str] | StoryDecisionNodeLinkRecord | StoryDecisionNodeLink) -> dict[str, str]:
        if isinstance(record, StoryDecisionNodeLink):
            return {
                "object_type": record.object_type.value,
                "object_id": record.object_id,
                "relation_kind": record.relation_kind,
            }
        if isinstance(record, StoryDecisionNodeLinkRecord):
            return {
                "object_type": self._normalize_text(record.object_type, field_name="object_type"),
                "object_id": self._normalize_text(record.object_id, field_name="object_id"),
                "relation_kind": self._normalize_text(record.relation_kind, field_name="relation_kind"),
            }
        if isinstance(record, Mapping):
            return {
                "object_type": self._normalize_text(record["object_type"], field_name="object_type"),
                "object_id": self._normalize_text(record["object_id"], field_name="object_id"),
                "relation_kind": self._normalize_text(record["relation_kind"], field_name="relation_kind"),
            }
        return {
            "object_type": self._normalize_text(getattr(record, "object_type"), field_name="object_type"),
            "object_id": self._normalize_text(getattr(record, "object_id"), field_name="object_id"),
            "relation_kind": self._normalize_text(getattr(record, "relation_kind"), field_name="relation_kind"),
        }

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized
