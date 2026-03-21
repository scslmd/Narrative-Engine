from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from app.persistence.story_development import BrainstormItemRecord, StoryDevelopmentRepository
from app.schemas import BrainstormItem, BrainstormPromotion


_ALLOWED_BRAINSTORM_STATUSES = {"keep", "discard", "park"}


class BrainstormServiceError(ValueError):
    pass


class BrainstormValidationError(BrainstormServiceError):
    pass


class BrainstormNotFoundError(BrainstormServiceError):
    pass


class BrainstormService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository
        self._promotion_journal: dict[str, list[BrainstormPromotion]] = defaultdict(list)
        self._promotion_counter: dict[str, int] = defaultdict(int)

    def capture_brainstorm_item(
        self,
        *,
        project_id: str,
        content: str,
        status: str = "keep",
        cluster_key: str | None = None,
        tags: Sequence[str] | None = None,
        source_artifact_refs: Sequence[str] | None = None,
    ) -> BrainstormItem:
        normalized_status = self._normalize_status(status)
        record = self.repository.create_brainstorm_item(
            project_id=project_id,
            content=content,
            item_state=normalized_status,
            cluster_key=cluster_key,
            tags=list(tags) if tags is not None else None,
            source_artifact_refs=list(source_artifact_refs) if source_artifact_refs is not None else None,
        )
        return self._to_schema(record)

    def cluster_brainstorm_items(
        self,
        *,
        project_id: str,
        item_ids: Sequence[str],
        cluster_key: str | None = None,
    ) -> list[BrainstormItem]:
        normalized_item_ids = [self._normalize_item_id(item_id) for item_id in item_ids]
        if not normalized_item_ids:
            raise BrainstormValidationError("At least one brainstorm item id is required.")

        if cluster_key is None:
            cluster_key = self._next_cluster_key(project_id)

        updated_items: list[BrainstormItem] = []
        for item_id in normalized_item_ids:
            record = self._require_item(project_id, item_id)
            updated_record = self.repository.update_brainstorm_item_state(
                record.item_id,
                item_state=record.item_state,
                cluster_key=cluster_key,
            )
            updated_items.append(self._to_schema(updated_record))
        return updated_items

    def promote_brainstorm_item(
        self,
        *,
        project_id: str,
        item_id: str,
        target_object_kind: str,
        target_object_id: str,
        notes: str | None = None,
    ) -> BrainstormPromotion:
        record = self._require_item(project_id, self._normalize_item_id(item_id))
        if record.item_state == "discard":
            raise BrainstormValidationError("Discarded brainstorm items cannot be promoted.")

        source_item_ids = self._source_item_ids_for_promotion(project_id, record)
        promotion = BrainstormPromotion(
            promotion_id=self._next_promotion_id(project_id),
            project_id=project_id,
            source_item_ids=source_item_ids,
            target_object_kind=self._normalize_text(target_object_kind, field_name="target_object_kind"),
            target_object_id=self._normalize_text(target_object_id, field_name="target_object_id"),
            notes=notes,
        )
        self._promotion_journal[project_id].append(promotion)
        return promotion

    def list_promotions(self, project_id: str) -> tuple[BrainstormPromotion, ...]:
        return tuple(self._promotion_journal.get(project_id, ()))

    def _source_item_ids_for_promotion(self, project_id: str, record: BrainstormItemRecord) -> list[str]:
        if record.cluster_key is None:
            return [str(record.item_id)]

        clustered_records = [
            item
            for item in self.repository.list_brainstorm_items(project_id)
            if item.cluster_key == record.cluster_key
        ]
        clustered_records.sort(key=lambda item: item.item_id)
        return [str(item.item_id) for item in clustered_records]

    def _next_promotion_id(self, project_id: str) -> str:
        self._promotion_counter[project_id] += 1
        return f"promotion-{self._promotion_counter[project_id]:03d}"

    def _next_cluster_key(self, project_id: str) -> str:
        existing = {
            item.cluster_key
            for item in self.repository.list_brainstorm_items(project_id)
            if item.cluster_key is not None
        }
        index = 1
        while f"cluster-{index:03d}" in existing:
            index += 1
        return f"cluster-{index:03d}"

    def _require_item(self, project_id: str, item_id: int) -> BrainstormItemRecord:
        try:
            record = self.repository.get_brainstorm_item(item_id)
        except KeyError as exc:
            raise BrainstormNotFoundError(item_id) from exc
        if record.project_id != project_id:
            raise BrainstormNotFoundError(item_id)
        return record

    def _to_schema(self, record: BrainstormItemRecord) -> BrainstormItem:
        return BrainstormItem(
            item_id=str(record.item_id),
            project_id=record.project_id,
            content=record.content,
            status=record.item_state,
            tags=list(record.tags),
        )

    def _normalize_item_id(self, item_id: str) -> int:
        normalized = self._normalize_text(item_id, field_name="item_id")
        try:
            return int(normalized)
        except ValueError as exc:
            raise BrainstormValidationError("item_id must be numeric.") from exc

    def _normalize_status(self, status: str) -> str:
        normalized = self._normalize_text(status, field_name="status").lower()
        if normalized not in _ALLOWED_BRAINSTORM_STATUSES:
            allowed = ", ".join(sorted(_ALLOWED_BRAINSTORM_STATUSES))
            raise BrainstormValidationError(f"status must be one of: {allowed}")
        return normalized

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized
