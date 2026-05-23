from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas import StoryboardCard
from app.schemas.base import StrictModel
from app.services.storyboard_cards import (
    StoryboardCardNotFoundError,
    StoryboardCardService,
    StoryboardCardValidationError,
)
from pydantic import Field


class StoryboardCardListResponse(StrictModel):
    project_id: str
    items: list[StoryboardCard] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class StoryboardCardCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    card_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=50000)
    card_type: str = Field(default="idea", min_length=1, max_length=20)
    column_id: str | None = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    position: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    character_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StoryboardCardUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1, max_length=50000)
    card_type: str | None = Field(None, min_length=1, max_length=20)
    column_id: str | None = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    position: int | None = Field(None, ge=0)
    tags: list[str] | None = None
    character_ids: list[str] | None = None
    dependencies: list[str] | None = None
    metadata: dict[str, Any] | None = None


class StoryboardCardReindexRequest(StrictModel):
    card_ids: list[str] = Field(..., min_length=1)


def _card_to_schema(card) -> StoryboardCard:
    from app.persistence.story_development import StoryboardCardRecord as _Record
    if isinstance(card, _Record):
        return StoryboardCard(
            card_id=card.card_id,
            project_id=card.project_id,
            title=card.title,
            content=card.content,
            card_type=card.card_type,
            column_id=card.column_id,
            position=card.position,
            tags=list(card.tags) if card.tags else [],
            character_ids=list(card.character_ids) if card.character_ids else [],
            dependencies=list(card.dependencies) if card.dependencies else [],
            metadata=card.metadata or {},
        )
    return StoryboardCard(
        card_id=card.card_id,
        project_id=card.project_id,
        title=card.title,
        content=card.content,
        card_type=card.card_type,
        column_id=card.column_id,
        position=card.position,
        tags=list(card.tags) if card.tags else [],
        character_ids=list(card.character_ids) if card.character_ids else [],
        dependencies=list(card.dependencies) if card.dependencies else [],
        metadata=card.metadata or {},
    )


__all__ = [
    "StoryboardCardCreateRequest",
    "StoryboardCardListResponse",
    "StoryboardCardReindexRequest",
    "StoryboardCardUpdateRequest",
    "_card_to_schema",
    "register_storyboard_routes",
]


def register_storyboard_routes(
    router: APIRouter,
    storyboard_card_service: StoryboardCardService,
) -> None:
    @router.get("/storyboard/cards", response_model=StoryboardCardListResponse)
    def list_storyboard_cards(
        project_id: str,
        card_type: str | None = None,
        column_id: str | None = None,
        tag: str | None = None,
    ) -> StoryboardCardListResponse:
        """List storyboard cards for a project with optional filters."""
        try:
            from app.services.storyboard_cards import CardFilterOptions
            filter_opts = None
            if card_type or column_id or tag:
                filter_opts = CardFilterOptions(
                    card_type=card_type,
                    column_id=column_id,
                    tag=tag,
                )
            items = storyboard_card_service.list_cards(project_id, filter_options=filter_opts)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryboardCardListResponse(
            project_id=project_id,
            items=[_card_to_schema(c) for c in items],
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def get_storyboard_card(card_id: str, project_id: str) -> StoryboardCard:
        """Get a specific storyboard card."""
        try:
            card = storyboard_card_service.get_card(card_id)
            return _card_to_schema(card)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc

    @router.post("/storyboard/cards", response_model=StoryboardCard, status_code=201)
    def create_storyboard_card(payload: StoryboardCardCreateRequest) -> StoryboardCard:
        """Create a new storyboard card."""
        try:
            card = storyboard_card_service.create_card(
                project_id=payload.project_id,
                card_id=payload.card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                column_id=payload.column_id,
                position=payload.position,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def update_storyboard_card(
        card_id: str,
        project_id: str,
        payload: StoryboardCardUpdateRequest,
    ) -> StoryboardCard:
        """Update a storyboard card."""
        try:
            existing = storyboard_card_service.get_card(card_id)
            if existing.project_id != project_id:
                raise StoryboardCardNotFoundError(card_id)
            card = storyboard_card_service.update_card_content(
                card_id=card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.put("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def upsert_storyboard_card(
        card_id: str,
        project_id: str,
        payload: StoryboardCardCreateRequest,
    ) -> StoryboardCard:
        """Create or update a storyboard card."""
        try:
            card = storyboard_card_service.upsert_card(
                project_id=payload.project_id,
                card_id=card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                column_id=payload.column_id,
                position=payload.position,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/storyboard/cards/{card_id}", status_code=204)
    def delete_storyboard_card(card_id: str, project_id: str) -> None:
        """Delete a storyboard card."""
        try:
            card = storyboard_card_service.get_card(card_id)
            if card.project_id != project_id:
                raise StoryboardCardNotFoundError(card_id)
            storyboard_card_service.delete_card(card_id)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc

    @router.put("/storyboard/cards/{column_id}/reindex", response_model=StoryboardCardListResponse)
    def reindex_storyboard_column(
        column_id: str,
        project_id: str,
        payload: StoryboardCardReindexRequest,
    ) -> StoryboardCardListResponse:
        """Reindex cards within a column."""
        try:
            results = storyboard_card_service.reindex_column(
                project_id=project_id,
                column_id=column_id,
                card_ids=payload.card_ids,
            )
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryboardCardListResponse(
            project_id=project_id,
            items=[_card_to_schema(c) for c in results],
            meta={"ordered_by": "position_asc"},
        )
