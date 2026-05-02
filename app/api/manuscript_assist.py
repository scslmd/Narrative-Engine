from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.manuscript_assist import (
    ApplyAssistSuggestionRequest,
    ApplyAssistSuggestionResponse,
    AssistGateResultListResponse,
    AssistSuggestionListResponse,
    LLMRevisionSuggestion,
    ManuscriptAssistRequest,
    ManuscriptAssistResult,
)
from app.services.drafting import DraftingService
from app.services.job_manager import JobManager
from app.services.manuscript_assist import (
    ManuscriptAssistConflictError,
    ManuscriptAssistNotFoundError,
    ManuscriptAssistService,
)


def build_manuscript_assist_router(
    repository: StoryDevelopmentRepository,
    job_manager: JobManager,
    prefix: str = "/v1/manuscript-assist",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["manuscript-assist"])
    service = ManuscriptAssistService(
        repository=repository,
        drafting_service=DraftingService(repository),
        job_manager=job_manager,
    )

    @router.post("/runs", response_model=ManuscriptAssistResult, status_code=202)
    def submit_assist(request: ManuscriptAssistRequest) -> ManuscriptAssistResult:
        try:
            return service.submit_assist(request)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ManuscriptAssistConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            if "idempotency key conflict" in str(exc):
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/runs", response_model=list[ManuscriptAssistResult])
    def list_runs(
        project_id: str = Query(..., min_length=1),
        document_id: str | None = Query(default=None),
    ) -> list[ManuscriptAssistResult]:
        return service.list_assists(project_id, document_id)

    @router.get("/runs/{assist_id}", response_model=ManuscriptAssistResult)
    def get_run(assist_id: str) -> ManuscriptAssistResult:
        try:
            return service.get_assist(assist_id)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/runs/{assist_id}/retry", response_model=ManuscriptAssistResult)
    def retry_run(assist_id: str) -> ManuscriptAssistResult:
        try:
            return service.get_assist(assist_id)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/runs/{assist_id}/gates", response_model=AssistGateResultListResponse)
    def list_gates(assist_id: str) -> AssistGateResultListResponse:
        return service.list_assist_gates(assist_id)

    @router.get("/suggestions", response_model=AssistSuggestionListResponse)
    def list_suggestions(
        project_id: str = Query(..., min_length=1),
        document_id: str = Query(..., min_length=1),
        status: str | None = Query(default=None),
    ) -> AssistSuggestionListResponse:
        items = service.list_suggestions(project_id, document_id, status)
        return AssistSuggestionListResponse(project_id=project_id, document_id=document_id, items=items)

    @router.post("/suggestions/{suggestion_id}/apply", response_model=ApplyAssistSuggestionResponse)
    def apply_suggestion(suggestion_id: str, request: ApplyAssistSuggestionRequest) -> ApplyAssistSuggestionResponse:
        if suggestion_id != request.suggestion_id:
            raise HTTPException(status_code=400, detail="suggestion_id path/body mismatch")
        try:
            return service.apply_suggestion(request)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ManuscriptAssistConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/suggestions/{suggestion_id}/reject", response_model=LLMRevisionSuggestion)
    def reject_suggestion(
        suggestion_id: str,
        project_id: str = Query(..., min_length=1),
    ) -> LLMRevisionSuggestion:
        try:
            return service.reject_suggestion(project_id, suggestion_id)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/suggestions/{suggestion_id}/archive", response_model=LLMRevisionSuggestion)
    def archive_suggestion(
        suggestion_id: str,
        project_id: str = Query(..., min_length=1),
    ) -> LLMRevisionSuggestion:
        try:
            return service.archive_suggestion(project_id, suggestion_id)
        except ManuscriptAssistNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
