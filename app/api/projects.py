from __future__ import annotations

import logging
from typing import Any, Callable, Protocol, TypeVar

from fastapi import APIRouter, HTTPException
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)

R = TypeVar("R")


def handle_service_error(
    func: Callable[[], R],
    specific_error: type[Exception],
) -> R:
    """Execute a service function and translate errors to HTTP exceptions.

    Args:
        func: Zero-argument callable that performs the service operation.
        specific_error: Exception class that maps to 400 Bad Request.

    Returns:
        The result of func() on success.

    Raises:
        HTTPException: 400 for specific_error, 500 for unexpected failures.
    """
    try:
        return func()
    except specific_error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class _ImportServiceProtocol(Protocol):
    def import_story(self, request: Any) -> Any: ...


class _MythosServiceProtocol(Protocol):
    def extract(self, request: Any) -> Any: ...


class _PatternServiceProtocol(Protocol):
    def extract(
        self,
        text: str,
        source_type: str,
        generation_mode: str,
        project_id: str | None,
        source_corpus: str | None,
    ) -> Any: ...

    def extract_from_project(
        self,
        project_id: str,
        source_type: str,
        generation_mode: str,
        source_corpus: str | None,
    ) -> Any: ...

from app.schemas.projects import (
    ProjectArtifactResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectSummaryResponse,
)
from app.schemas.mythos_extraction import (
    MythosExtractionRequest,
    MythosExtractionResponse,
)
from app.schemas.pattern_extraction import (
    ExtractPatternsRequest,
    PatternExtractionRequest,
    PatternExtractionResponse,
)
from app.services.mythos_extraction import MythosExtractionError
from app.services.pattern_extraction import PatternExtractionError
from app.services.projects import ProjectService

logger = logging.getLogger(__name__)


def build_projects_router(
    project_service: ProjectService,
    import_service: _ImportServiceProtocol | None = None,
    mythos_service: _MythosServiceProtocol | None = None,
    pattern_service: _PatternServiceProtocol | None = None,
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
            return handle_service_error(
                lambda: import_service.import_story(request),
                StoryImportError,
            )

    if mythos_service is not None:
        @router.post("/import-mythos", response_model=MythosExtractionResponse, status_code=201)
        def import_mythos(request: MythosExtractionRequest) -> MythosExtractionResponse:
            return handle_service_error(
                lambda: mythos_service.extract(request),
                MythosExtractionError,
            )

    if pattern_service is not None:
        @router.post("/import-patterns", response_model=PatternExtractionResponse, status_code=201)
        def import_patterns(request: PatternExtractionRequest) -> PatternExtractionResponse:
            return handle_service_error(
                lambda: pattern_service.extract(
                    text=request.text,
                    source_type=request.source_type,
                    generation_mode=request.generation_mode,
                    project_id=request.project_id,
                    source_corpus=request.source_corpus,
                ),
                PatternExtractionError,
            )

        @router.post("/{project_id}/extract-patterns", response_model=PatternExtractionResponse, status_code=201)
        def extract_patterns(
            project_id: str,
            request: ExtractPatternsRequest,
        ) -> PatternExtractionResponse:
            return handle_service_error(
                lambda: pattern_service.extract_from_project(
                    project_id=project_id,
                    source_type=request.source_type,
                    generation_mode=request.generation_mode,
                    source_corpus=request.source_corpus,
                ),
                PatternExtractionError,
            )

    return router
