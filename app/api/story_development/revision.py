from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.story_development import (
    RevisionPass,
    RevisionPassCreateRequest,
    RevisionPassListResponse,
    RevisionPassUpdateRequest,
    RevisionChecklistItem,
)
from app.services.revision import (
    RevisionConflictError,
    RevisionNotFoundError,
    RevisionService,
)


def register_revision_routes(
    router: APIRouter,
    service: RevisionService,
) -> None:
    @router.get("/revision/passes", response_model=RevisionPassListResponse)
    def list_revision_passes(
        project_id: str,
        pass_type: str | None = None,
        status: str | None = None,
    ) -> RevisionPassListResponse:
        items = service.list_passes(
            project_id,
            pass_type=pass_type,
            status=status,
        )
        return RevisionPassListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "created_at_desc"},
        )

    @router.get("/revision/passes/{pass_id}", response_model=RevisionPass)
    def get_revision_pass(pass_id: str, project_id: str) -> RevisionPass:
        try:
            revision_pass = service.get_pass(pass_id)
            if revision_pass.project_id != project_id:
                raise RevisionNotFoundError(pass_id)
            return revision_pass
        except RevisionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/revision/passes", response_model=RevisionPass, status_code=201)
    def create_revision_pass(payload: RevisionPassCreateRequest) -> RevisionPass:
        return service.create_pass(
            payload.project_id,
            pass_type=payload.pass_type,
            status=payload.status,
            notes=payload.notes,
        )

    @router.patch("/revision/passes/{pass_id}", response_model=RevisionPass)
    def update_revision_pass(
        pass_id: str,
        project_id: str,
        payload: RevisionPassUpdateRequest,
    ) -> RevisionPass:
        try:
            existing = service.get_pass(pass_id)
            if existing.project_id != project_id:
                raise RevisionNotFoundError(pass_id)
            return service.update_pass(
                pass_id,
                status=payload.status,
                notes=payload.notes,
                checklist=payload.checklist,
            )
        except RevisionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RevisionConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/revision/passes/{pass_id}/complete", response_model=RevisionPass)
    def complete_revision_pass(pass_id: str, project_id: str) -> RevisionPass:
        try:
            existing = service.get_pass(pass_id)
            if existing.project_id != project_id:
                raise RevisionNotFoundError(pass_id)
            return service.complete_pass(pass_id)
        except RevisionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/revision/checklists/{pass_type}")
    def get_checklist(pass_type: str) -> list[RevisionChecklistItem]:
        return service.get_checklist(pass_type)
