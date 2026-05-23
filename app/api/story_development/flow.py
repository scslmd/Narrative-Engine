from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas import StoryFlowDefinition, StoryFlowStage
from app.schemas.base import StrictModel
from pydantic import Field
from app.services.editable_flow import (
    EditableFlowNotFoundError,
    EditableFlowService,
    EditableFlowValidationError,
)


class FlowStageListResponse(StrictModel):
    project_id: str
    items: list[StoryFlowStage] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FlowStageCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    stage_kind: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] = Field(default_factory=list)
    insert_after_stage_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')


class FlowStageUpdateRequest(StrictModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)
    custom_prompt_guidance: str | None = Field(None, max_length=10000)
    stage_configuration_state: str | None = Field(None, max_length=20)


class FlowStageReorderRequest(StrictModel):
    stage_order: list[str] = Field(..., min_length=1)


class FlowInitRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_name: str = Field(..., min_length=1, max_length=255)


__all__ = [
    "FlowInitRequest",
    "FlowStageCreateRequest",
    "FlowStageListResponse",
    "FlowStageReorderRequest",
    "FlowStageUpdateRequest",
    "register_flow_routes",
]


def register_flow_routes(
    router: APIRouter,
    flow_service: EditableFlowService,
) -> None:
    @router.post("/flow/stages/init", response_model=FlowStageListResponse, status_code=201)
    def init_flow_stages(payload: FlowInitRequest) -> FlowStageListResponse:
        """Initialize a default flow for a project."""
        try:
            flow_service.create_default_flow(
                project_id=payload.project_id,
                project_name=payload.project_name,
            )
            items = flow_service.list_stages(payload.project_id)
            return FlowStageListResponse(project_id=payload.project_id, items=items, meta={"source": "default"})
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/flow/stages", response_model=FlowStageListResponse)
    def list_flow_stages(project_id: str) -> FlowStageListResponse:
        try:
            items = flow_service.list_stages(project_id)
            return FlowStageListResponse(project_id=project_id, items=items, meta={"ordered_by": "position_asc"})
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc

    @router.post("/flow/stages", response_model=StoryFlowStage, status_code=201)
    def create_flow_stage(payload: FlowStageCreateRequest) -> StoryFlowStage:
        try:
            return flow_service.add_custom_stage(
                project_id=payload.project_id,
                display_name=payload.display_name or f"{payload.stage_kind.replace('_', ' ').title()} Stage",
                description=payload.description,
                stage_kind=payload.stage_kind,
                depends_on=payload.depends_on,
                insert_after_stage_id=payload.insert_after_stage_id,
            )
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def update_flow_stage(stage_id: str, project_id: str, payload: FlowStageUpdateRequest) -> StoryFlowStage:
        try:
            updates: dict[str, Any] = {}
            if payload.display_name is not None:
                updates["display_name"] = payload.display_name
            if payload.description is not None:
                updates["description"] = payload.description
            if payload.depends_on is not None:
                updates["depends_on"] = payload.depends_on
            if payload.writer_notes is not None:
                updates["writer_notes"] = payload.writer_notes
            if payload.custom_prompt_guidance is not None:
                updates["custom_prompt_guidance"] = payload.custom_prompt_guidance
            if payload.stage_configuration_state is not None:
                updates["stage_configuration_state"] = payload.stage_configuration_state

            return flow_service.redefine_stage(project_id=project_id, stage_id=stage_id, **updates)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/flow/stages/reorder", response_model=StoryFlowDefinition)
    def reorder_flow_stages(project_id: str, payload: FlowStageReorderRequest) -> StoryFlowDefinition:
        try:
            return flow_service.reorder_stages(project_id=project_id, stage_order=payload.stage_order)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def delete_flow_stage(stage_id: str, project_id: str) -> StoryFlowStage:
        try:
            return flow_service.delete_custom_stage(project_id=project_id, stage_id=stage_id)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
