from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import BrainstormItem, BrainstormPromotion
from app.schemas.base import StrictModel
from app.services.brainstorm import BrainstormNotFoundError, BrainstormService, BrainstormValidationError
from pydantic import Field


class BrainstormItemCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    content: str = Field(..., min_length=1, max_length=10000)
    status: str = Field(default="keep", max_length=20)
    cluster_key: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    source_artifact_refs: list[str] = Field(default_factory=list)


class BrainstormItemClusterRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    item_ids: list[str] = Field(..., min_length=1)
    cluster_key: str | None = Field(None, max_length=100)


class BrainstormItemPromoteRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    item_id: str = Field(..., min_length=1)
    target_object_kind: str = Field(..., min_length=1, max_length=100)
    target_object_id: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=2000)


class BrainstormItemListResponse(StrictModel):
    project_id: str
    items: list[BrainstormItem] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BrainstormPromotionListResponse(StrictModel):
    project_id: str
    items: list[BrainstormPromotion] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "BrainstormItemListResponse",
    "BrainstormItemClusterRequest",
    "BrainstormItemCreateRequest",
    "BrainstormItemPromoteRequest",
    "BrainstormPromotionListResponse",
    "register_brainstorm_routes",
]


def register_brainstorm_routes(
    router: APIRouter,
    brainstorm_service: BrainstormService,
    repository: object,
) -> None:
    @router.get("/brainstorm/items", response_model=BrainstormItemListResponse)
    def list_brainstorm_items(project_id: str) -> BrainstormItemListResponse:
        """List all brainstorm items for a project."""
        items = list(repository.list_brainstorm_items(project_id))
        return BrainstormItemListResponse(
            project_id=project_id,
            items=[brainstorm_service._to_schema(item) for item in items],
            meta={"ordered_by": "created_at_asc"},
        )

    @router.post("/brainstorm/items", response_model=BrainstormItem, status_code=201)
    def create_brainstorm_item(payload: BrainstormItemCreateRequest) -> BrainstormItem:
        """Create a new brainstorm item."""
        try:
            return brainstorm_service.capture_brainstorm_item(
                project_id=payload.project_id,
                content=payload.content,
                status=payload.status,
                cluster_key=payload.cluster_key,
                tags=payload.tags,
                source_artifact_refs=payload.source_artifact_refs,
            )
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/brainstorm/items/cluster", response_model=list[BrainstormItem])
    def cluster_brainstorm_items(payload: BrainstormItemClusterRequest) -> list[BrainstormItem]:
        """Cluster multiple brainstorm items together."""
        try:
            return brainstorm_service.cluster_brainstorm_items(
                project_id=payload.project_id,
                item_ids=payload.item_ids,
                cluster_key=payload.cluster_key,
            )
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/brainstorm/items/promote", response_model=BrainstormPromotion, status_code=201)
    def promote_brainstorm_item(payload: BrainstormItemPromoteRequest) -> BrainstormPromotion:
        """Promote a brainstorm item to a target object."""
        try:
            return brainstorm_service.promote_brainstorm_item(
                project_id=payload.project_id,
                item_id=payload.item_id,
                target_object_kind=payload.target_object_kind,
                target_object_id=payload.target_object_id,
                notes=payload.notes,
            )
        except BrainstormNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brainstorm item not found.") from exc
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/brainstorm/promotions", response_model=BrainstormPromotionListResponse)
    def list_brainstorm_promotions(project_id: str) -> BrainstormPromotionListResponse:
        """List all brainstorm promotions for a project."""
        promotions = brainstorm_service.list_promotions(project_id)
        return BrainstormPromotionListResponse(
            project_id=project_id,
            items=list(promotions),
            meta={"ordered_by": "created_at_asc"},
        )
