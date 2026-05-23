from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import BrainstormItem
from app.schemas.base import StrictModel
from app.services.braindump import (
    BrainDumpNotFoundError,
    BrainDumpOrganizeError,
    BrainDumpService,
    BrainDumpValidationError,
)
from pydantic import Field


class BrainDumpSessionCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str | None = Field(None, max_length=500)
    raw_text: str = Field("", max_length=100000)


class BrainDumpSessionPatchRequest(StrictModel):
    raw_text: str | None = Field(None, max_length=100000)
    title: str | None = Field(None, max_length=500)
    state: str | None = Field(None, max_length=20)


class BrainDumpSessionResponse(StrictModel):
    session_id: int
    project_id: str
    title: str | None = None
    raw_text: str = ""
    state: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


class BrainDumpSessionListResponse(StrictModel):
    project_id: str
    sessions: list[BrainDumpSessionResponse] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BrainDumpOrganizeResponse(StrictModel):
    session_id: int
    categorized_items: dict[str, list[BrainstormItem]] = Field(default_factory=dict)
    total_items: int = 0


def _session_to_response(session) -> BrainDumpSessionResponse:
    return BrainDumpSessionResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        title=session.title,
        raw_text=session.raw_text,
        state=session.state,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
    )


__all__ = [
    "BrainDumpOrganizeResponse",
    "BrainDumpSessionCreateRequest",
    "BrainDumpSessionListResponse",
    "BrainDumpSessionPatchRequest",
    "BrainDumpSessionResponse",
    "_session_to_response",
    "register_braindump_routes",
]


def register_braindump_routes(
    router: APIRouter,
    braindump_service: BrainDumpService,
    brainstorm_service: object,
) -> None:
    @router.post("/braindump/sessions", response_model=BrainDumpSessionResponse, status_code=201)
    def create_brain_dump_session(payload: BrainDumpSessionCreateRequest) -> BrainDumpSessionResponse:
        """Create a new brain dump session for a project."""
        try:
            session = braindump_service.create_session(
                project_id=payload.project_id,
                title=payload.title,
                raw_text=payload.raw_text,
            )
            return _session_to_response(session)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/braindump/sessions", response_model=BrainDumpSessionListResponse)
    def list_brain_dump_sessions(project_id: str) -> BrainDumpSessionListResponse:
        """List all brain dump sessions for a project."""
        sessions = braindump_service.list_sessions(project_id)
        return BrainDumpSessionListResponse(
            project_id=project_id,
            sessions=[_session_to_response(s) for s in sessions],
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/braindump/sessions/{session_id}", response_model=BrainDumpSessionResponse)
    def get_brain_dump_session(session_id: int, project_id: str) -> BrainDumpSessionResponse:
        """Get a specific brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            return _session_to_response(session)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.patch("/braindump/sessions/{session_id}", response_model=BrainDumpSessionResponse)
    def patch_brain_dump_session(
        session_id: int,
        project_id: str,
        payload: BrainDumpSessionPatchRequest,
    ) -> BrainDumpSessionResponse:
        """Update a brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            updated = braindump_service.update_session(
                session_id,
                raw_text=payload.raw_text,
                title=payload.title,
                state=payload.state,
            )
            return _session_to_response(updated)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.delete("/braindump/sessions/{session_id}", status_code=204)
    def delete_brain_dump_session(session_id: int, project_id: str) -> None:
        """Delete a brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            braindump_service.delete_session(session_id)
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.post("/braindump/sessions/{session_id}/organize", response_model=BrainDumpOrganizeResponse, status_code=201)
    def organize_brain_dump_session(
        session_id: int,
        project_id: str,
    ) -> BrainDumpOrganizeResponse:
        """Organize a brain dump session by categorizing raw text into brainstorm items."""
        try:
            categorized_items = braindump_service.organize(
                session_id,
                project_id,
                brainstorm_service=brainstorm_service,
            )

            # Wrap items with item_type for response schema
            response_items: dict[str, list[BrainstormItem]] = {}
            total = 0
            for category, items in categorized_items.items():
                wrapped: list[BrainstormItem] = []
                for item in items:
                    wrapped.append(BrainstormItem(
                        item_id=item.item_id,
                        project_id=item.project_id,
                        content=item.content,
                        status=item.status,
                        tags=item.tags,
                        source_notes=item.source_notes,
                        item_type=category,
                    ))
                    total += 1
                if wrapped:
                    response_items[category] = wrapped

            return BrainDumpOrganizeResponse(
                session_id=session_id,
                categorized_items=response_items,
                total_items=total,
            )
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc
        except BrainDumpOrganizeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
