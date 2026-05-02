from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonForkPreviewResponse,
    CanonGenerationPacket,
    CanonGenerationRequest,
    GenerationGateResult,
    GenerationGateResultListResponse,
    GenerationRunResponse,
)
from app.services.canon_packet_builder import CanonPacketBuilder
from app.services.job_manager import JobManager
from app.services.projects import ProjectService
from app.services.story_forking import StoryForkingService
from app.services.story_generation_orchestrator import StoryGenerationOrchestrator
from app.utils.db_inserts import hash_id


def build_story_generation_router(
    repository: StoryDevelopmentRepository,
    project_service: ProjectService,
    job_manager: JobManager,
    prefix: str = "/v1/story-generation",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["story-generation"])
    packet_builder = CanonPacketBuilder(repository=repository, project_service=project_service)
    forking_service = StoryForkingService(repository=repository, project_service=project_service)
    orchestrator = StoryGenerationOrchestrator(
        repository=repository,
        project_service=project_service,
        packet_builder=packet_builder,
        forking_service=forking_service,
        job_manager=job_manager,
    )

    @router.post("/runs", response_model=GenerationRunResponse, status_code=201)
    def create_generation_run(request: CanonGenerationRequest) -> GenerationRunResponse:
        try:
            return orchestrator.submit_generation(request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            message = str(exc)
            if "idempotency key conflict" in message:
                raise HTTPException(status_code=409, detail=message) from exc
            raise HTTPException(status_code=400, detail=message) from exc

    @router.get("/runs", response_model=list[GenerationRunResponse])
    def list_generation_runs(project_id: str = Query(..., min_length=1)) -> list[GenerationRunResponse]:
        return orchestrator.list_generations(project_id)

    @router.get("/runs/{generation_id}", response_model=GenerationRunResponse)
    def get_generation_run(generation_id: str) -> GenerationRunResponse:
        try:
            return orchestrator.get_generation(generation_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"generation not found: {generation_id}") from exc

    @router.post("/runs/{generation_id}/retry", response_model=GenerationRunResponse)
    def retry_generation_run(generation_id: str) -> GenerationRunResponse:
        try:
            return orchestrator.get_generation(generation_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"generation not found: {generation_id}") from exc

    @router.get("/runs/{generation_id}/packet", response_model=CanonGenerationPacket)
    def get_generation_packet(generation_id: str) -> CanonGenerationPacket:
        try:
            packet_records = repository.list_canon_generation_packets_for_generation(generation_id)
            if not packet_records:
                raise KeyError(generation_id)
            return CanonGenerationPacket.model_validate(packet_records[0].packet_json)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"generation packet not found: {generation_id}") from exc

    @router.get("/runs/{generation_id}/gates", response_model=GenerationGateResultListResponse)
    def get_generation_gates(generation_id: str) -> GenerationGateResultListResponse:
        items = repository.list_generation_gate_results(generation_id)
        return GenerationGateResultListResponse(
            generation_id=generation_id,
            items=[
                GenerationGateResult(
                    gate_result_id=item.gate_result_id,
                    generation_id=item.generation_id,
                    project_id=item.project_id,
                    artifact_kind=item.artifact_kind,
                    artifact_id=item.artifact_id,
                    gate_name=item.gate_name,
                    passed=item.passed,
                    severity=item.severity,
                    reasons=item.reasons,
                    repair_attempted=item.repair_attempted,
                    repair_job_id=item.repair_job_id,
                    created_at=item.created_at.isoformat(),
                )
                for item in items
            ],
        )

    @router.post("/fork-preview", response_model=CanonForkPreviewResponse)
    def preview_fork(request: CanonGenerationRequest) -> CanonForkPreviewResponse:
        return CanonForkPreviewResponse(
            source_project_id=request.source_project_id,
            mode=request.mode,
            destination_kind=request.destination.destination_kind,
            selected_character_ids=request.canon_scope.character_ids,
            selected_world_bible_refs=request.canon_scope.world_bible_refs,
            selected_continuity_thread_ids=request.canon_scope.continuity_thread_ids,
            selected_arc_ids=request.canon_scope.arc_ids,
            warnings=[],
        )

    @router.post("/fork-project", response_model=GenerationRunResponse, status_code=201)
    def create_fork_project(request: CanonGenerationRequest, start_generation: bool = True) -> GenerationRunResponse:
        if start_generation:
            return create_generation_run(request)
        target_project_id = forking_service.create_fork_project(request)
        generation_id = hash_id(
            "fork-only", f"{request.source_project_id}:{target_project_id}"
        )
        return GenerationRunResponse(
            generation_id=generation_id,
            source_project_id=request.source_project_id,
            target_project_id=target_project_id,
            job_ids=[],
            status="queued",
            warnings=[],
            created_artifacts=[],
        )

    return router
