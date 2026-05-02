from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonGenerationPacket,
    CanonGenerationRequest,
    GenerationArtifactRef,
    GenerationRunResponse,
    GenerationRunStatus,
)
from app.schemas.jobs import JobCreateRequest
from app.services.canon_packet_builder import CanonPacketBuilder
from app.services.job_manager import JobManager
from app.services.projects import ProjectService
from app.services.story_forking import StoryForkingService
from app.utils.db_inserts import hash_id


@dataclass(frozen=True)
class _GenerationRunContext:
    generation_id: str
    source_project_id: str
    target_project_id: str


class StoryGenerationOrchestrator:
    def __init__(
        self,
        *,
        repository: StoryDevelopmentRepository,
        project_service: ProjectService,
        packet_builder: CanonPacketBuilder,
        forking_service: StoryForkingService,
        job_manager: JobManager,
    ) -> None:
        self._repository = repository
        self._project_service = project_service
        self._packet_builder = packet_builder
        self._forking_service = forking_service
        self._job_manager = job_manager

    def submit_generation(self, request: CanonGenerationRequest) -> GenerationRunResponse:
        self._project_service.get_project(request.source_project_id)
        target_project_id = self._resolve_destination(request)
        run = self._create_generation_run(request, target_project_id)
        packet = self._build_and_store_packet(run, request)
        plan_job_id = self._create_generation_plan_job(run, packet)
        chapter_job_ids = self._create_chapter_draft_jobs(run, request, packet)
        gate_job_id = self._create_gate_job(run, packet)
        compile_job_id = self._create_compiler_job(run, packet)
        all_job_ids = [plan_job_id, *chapter_job_ids, gate_job_id, compile_job_id]

        record = self._repository.upsert_canon_generation_run(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            mode=self._enum_value(request.mode),
            request_json=request.model_dump(mode="json"),
            canon_scope_json=request.canon_scope.model_dump(mode="json"),
            canon_policy_json=request.canon_policy.model_dump(mode="json"),
            status=GenerationRunStatus.QUEUED.value,
            gate_status="pending",
            warnings=[],
            created_job_ids=all_job_ids,
            created_artifacts=[],
            idempotency_key=request.idempotency_key,
            request_hash=self._request_hash(request),
        )
        return GenerationRunResponse(
            generation_id=record.generation_id,
            source_project_id=record.source_project_id,
            target_project_id=record.target_project_id,
            job_ids=record.created_job_ids,
            status=GenerationRunStatus(record.status),
            warnings=record.warnings,
            created_artifacts=[GenerationArtifactRef.model_validate(item) for item in record.created_artifacts],
        )

    def get_generation(self, generation_id: str) -> GenerationRunResponse:
        run = self._repository.get_canon_generation_run(generation_id)
        return GenerationRunResponse(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            job_ids=run.created_job_ids,
            status=GenerationRunStatus(run.status),
            warnings=run.warnings,
            created_artifacts=[GenerationArtifactRef.model_validate(item) for item in run.created_artifacts],
        )

    def list_generations(self, project_id: str) -> list[GenerationRunResponse]:
        runs = self._repository.list_canon_generation_runs(project_id, role="either")
        return [
            GenerationRunResponse(
                generation_id=run.generation_id,
                source_project_id=run.source_project_id,
                target_project_id=run.target_project_id,
                job_ids=run.created_job_ids,
                status=GenerationRunStatus(run.status),
                warnings=run.warnings,
                created_artifacts=[GenerationArtifactRef.model_validate(item) for item in run.created_artifacts],
            )
            for run in runs
        ]

    def _resolve_destination(self, request: CanonGenerationRequest) -> str:
        if self._enum_value(request.destination.destination_kind) == "same_project":
            return str(request.destination.target_project_id)
        target_project_id = self._forking_service.create_fork_project(request)
        self._forking_service.copy_selected_characters(
            request.source_project_id,
            target_project_id,
            request.canon_scope.character_ids,
        )
        self._forking_service.copy_selected_relationships(
            request.source_project_id,
            target_project_id,
            request.canon_scope.character_ids,
        )
        self._forking_service.copy_selected_world_entries(
            request.source_project_id,
            target_project_id,
            request.canon_scope.world_bible_refs,
        )
        self._forking_service.create_fork_foundation(
            request.source_project_id,
            target_project_id,
            request,
        )
        return target_project_id

    def _create_generation_run(self, request: CanonGenerationRequest, target_project_id: str) -> _GenerationRunContext:
        request_hash = self._request_hash(request)
        generation_id = hash_id(
            "generation-run",
            f"{request.source_project_id}:{target_project_id}:{self._enum_value(request.mode)}:{request_hash}",
        )
        self._repository.upsert_canon_generation_run(
            generation_id=generation_id,
            source_project_id=request.source_project_id,
            target_project_id=target_project_id,
            mode=self._enum_value(request.mode),
            request_json=request.model_dump(mode="json"),
            canon_scope_json=request.canon_scope.model_dump(mode="json"),
            canon_policy_json=request.canon_policy.model_dump(mode="json"),
            status=GenerationRunStatus.QUEUED.value,
            gate_status="pending",
            warnings=[],
            created_job_ids=[],
            created_artifacts=[],
            idempotency_key=request.idempotency_key,
            request_hash=request_hash,
        )
        return _GenerationRunContext(
            generation_id=generation_id,
            source_project_id=request.source_project_id,
            target_project_id=target_project_id,
        )

    def _build_and_store_packet(
        self,
        run: _GenerationRunContext,
        request: CanonGenerationRequest,
    ) -> CanonGenerationPacket:
        packet = self._packet_builder.build_packet(request, run.target_project_id)
        self._repository.upsert_canon_generation_packet(
            packet_id=packet.packet_id,
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            packet_json=packet.model_dump(mode="json"),
            source_hashes_json=packet.source_hashes,
            prompt_budget_json=packet.prompt_budget_summary.model_dump(mode="json"),
        )
        return packet

    def _create_generation_plan_job(self, run: _GenerationRunContext, packet: CanonGenerationPacket) -> str:
        status = self._job_manager.create_job(
            JobCreateRequest(
                phase="G-200",
                payload={
                    "generation_id": run.generation_id,
                    "packet_id": packet.packet_id,
                    "project_id": run.target_project_id,
                },
            )
        )
        return str(status.id)

    def _create_chapter_draft_jobs(
        self,
        run: _GenerationRunContext,
        request: CanonGenerationRequest,
        packet: CanonGenerationPacket,
    ) -> list[str]:
        chapter_ids = [f"chapter-{index}" for index in range(1, request.target_chapter_count + 1)]
        status = self._job_manager.create_job(
            JobCreateRequest(
                phase="G-300",
                payload={
                    "generation_id": run.generation_id,
                    "packet_id": packet.packet_id,
                    "project_id": run.target_project_id,
                    "chapter_ids": chapter_ids,
                    "target_words_per_chapter": request.target_words_per_chapter,
                },
            )
        )
        return [str(status.id)]

    def _create_gate_job(self, run: _GenerationRunContext, packet: CanonGenerationPacket) -> str:
        status = self._job_manager.create_job(
            JobCreateRequest(
                phase="G-350",
                payload={
                    "generation_id": run.generation_id,
                    "packet_id": packet.packet_id,
                    "project_id": run.target_project_id,
                    "artifact_refs": [],
                },
            )
        )
        return str(status.id)

    def _create_compiler_job(self, run: _GenerationRunContext, packet: CanonGenerationPacket) -> str:
        status = self._job_manager.create_job(
            JobCreateRequest(
                phase="G-400",
                payload={
                    "generation_id": run.generation_id,
                    "packet_id": packet.packet_id,
                    "project_id": run.target_project_id,
                    "chapter_artifact_ids": [],
                },
            )
        )
        return str(status.id)

    def _request_hash(self, request: CanonGenerationRequest) -> str:
        normalized = json.dumps(request.model_dump(mode="json"), ensure_ascii=True, sort_keys=True)
        return sha256(normalized.encode("utf-8")).hexdigest()

    def _enum_value(self, value: Any) -> str:
        if hasattr(value, "value"):
            return str(getattr(value, "value"))
        raw = str(value)
        if "." in raw:
            return raw.split(".")[-1].lower()
        return raw
