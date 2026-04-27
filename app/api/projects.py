from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.exceptions import RequestValidationError

from app.schemas.projects import (
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from app.services.projects import ProjectService

logger = logging.getLogger(__name__)


def build_projects_router(
    project_service: ProjectService,
    import_service: Any = None,
    mythos_service: Any = None,
) -> APIRouter:
    from ..schemas.story_import import StoryImportRequest, StoryImportResponse
    from ..services.story_import import StoryImportError

    router = APIRouter(prefix="/projects", tags=["projects"])

    @router.post("/create", response_model=ProjectDetailResponse, status_code=201)
    def create_project(request: ProjectCreateRequest) -> ProjectDetailResponse:
        try:
            return project_service.create_project(request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("", response_model=list[ProjectSummaryResponse])
    def list_projects() -> list[ProjectSummaryResponse]:
        return project_service.list_projects()

    @router.get("/{project_id}", response_model=ProjectDetailResponse)
    def get_project(project_id: str) -> ProjectDetailResponse:
        try:
            return project_service.get_project(project_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/manifest", response_model=ProjectArtifactResponse)
    def get_manifest(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "manifest")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/sequence", response_model=ProjectArtifactResponse)
    def get_sequence(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "sequence")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/{project_id}/chapter-1", response_model=ProjectArtifactResponse)
    def get_chapter(project_id: str) -> ProjectArtifactResponse:
        try:
            return project_service.read_artifact(project_id, "chapter-1")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    if import_service is not None:
        @router.post("/import-story", response_model=StoryImportResponse, status_code=201)
        def import_story(request: StoryImportRequest) -> StoryImportResponse:
            try:
                return import_service.import_story(request)
            except StoryImportError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc

    if mythos_service is not None:
        from ..schemas.mythos_extraction import MythosExtractionRequest, MythosExtractionResponse
        from ..services.mythos_extraction import MythosExtractionError

        @router.post("/import-mythos", response_model=MythosExtractionResponse, status_code=201)
        def import_mythos(request: MythosExtractionRequest) -> MythosExtractionResponse:
            try:
                return mythos_service.extract(request)
            except MythosExtractionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router
