from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import ResearchItem
from app.schemas.base import StrictModel
from app.schemas.story_development import (
    ResearchItemCreateRequest,
    ResearchItemUpdateRequest,
    ResearchItemListResponse,
)
from app.services.research import (
    ResearchNotFoundError,
    ResearchService,
    ResearchServiceError,
)
from pydantic import Field


__all__ = [
    "register_research_routes",
]


def register_research_routes(
    router: APIRouter,
    service: ResearchService,
) -> None:
    @router.get("/research/items", response_model=ResearchItemListResponse)
    def list_research_items(
        project_id: str,
        status: str | None = None,
        genre_tag: str | None = None,
    ) -> ResearchItemListResponse:
        """List all research items for a project."""
        items = service.list_items(project_id=project_id, status=status, genre_tag=genre_tag)
        return ResearchItemListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/research/items/{item_id}", response_model=ResearchItem)
    def get_research_item(item_id: str, project_id: str) -> ResearchItem:
        """Get a specific research item."""
        try:
            item = service.get_item(item_id)
            if item.project_id != project_id:
                raise ResearchNotFoundError(item_id)
            return item
        except ResearchNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Research item not found.") from exc

    @router.post("/research/items", response_model=ResearchItem, status_code=201)
    def create_research_item(payload: ResearchItemCreateRequest) -> ResearchItem:
        """Create a new research item."""
        try:
            return service.create_item(
                project_id=payload.project_id,
                title=payload.title,
                content=payload.content,
                source_url=payload.source_url,
                source_type=payload.source_type,
                genre_tags=payload.genre_tags,
                citations=payload.citations,
                status=payload.status,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (ResearchServiceError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/research/items/{item_id}", response_model=ResearchItem)
    def update_research_item(
        item_id: str,
        project_id: str,
        payload: ResearchItemUpdateRequest,
    ) -> ResearchItem:
        """Update a research item."""
        try:
            existing = service.get_item(item_id)
            if existing.project_id != project_id:
                raise ResearchNotFoundError(item_id)
            updates: dict[str, object] = {}
            if payload.title is not None:
                updates["title"] = payload.title
            if payload.content is not None:
                updates["content"] = payload.content
            if payload.source_url is not None:
                updates["source_url"] = payload.source_url
            if payload.source_type is not None:
                updates["source_type"] = payload.source_type
            if payload.genre_tags is not None:
                updates["genre_tags_json"] = payload.genre_tags
            if payload.status is not None:
                updates["status"] = payload.status
            if payload.citations is not None:
                updates["citations_json"] = payload.citations
            if not updates:
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            return service.update_item(item_id, **updates)
        except ResearchNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Research item not found.") from exc
        except (ResearchServiceError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/research/items/{item_id}", status_code=204)
    def delete_research_item(item_id: str, project_id: str) -> None:
        """Delete (soft archive) a research item."""
        try:
            item = service.get_item(item_id)
            if item.project_id != project_id:
                raise ResearchNotFoundError(item_id)
            service.delete_item(item_id)
        except ResearchNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Research item not found.") from exc
