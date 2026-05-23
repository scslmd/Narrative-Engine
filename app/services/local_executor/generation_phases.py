from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from ...persistence.steps import stable_hash_payload, stable_hash_text
from ..runtime_prompts import (
    build_g200_story_generation_plan_request,
    build_g300_chapter_generation_request,
    build_g400_manuscript_assembly_request,
)
from .helpers import provider_backend_version as _provider_backend_version, utcnow as _utcnow



class _GenerationPhasesMixin:

    def _run_generation_planner_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.generation import CanonGenerationPacket

        payload = dict(request_payload.get("payload", {}))
        generation_id = str(payload.get("generation_id", "")).strip()
        packet_id = str(payload.get("packet_id", "")).strip()
        if not generation_id or not packet_id:
            raise ValueError("G-200 requires payload.generation_id and payload.packet_id.")
        packet_record = self._story_repository.get_canon_generation_packet(packet_id)
        packet = CanonGenerationPacket.model_validate(packet_record.packet_json)
        inference_request = build_g200_story_generation_plan_request(packet, default_model=None)
        inference_response = self._inferencer.generate_text(inference_request)
        plan_id = f"generation-plan-{stable_hash_text(f'{generation_id}:{packet_id}')[:12]}"
        run = self._story_repository.get_canon_generation_run(generation_id)
        artifacts = [
            *run.created_artifacts,
            {"artifact_kind": "generation_plan", "artifact_id": plan_id, "project_id": packet.target_project_id},
        ]
        self._story_repository.upsert_canon_generation_run(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            mode=run.mode,
            request_json=run.request_json,
            canon_scope_json=run.canon_scope_json,
            canon_policy_json=run.canon_policy_json,
            status="running",
            gate_status=run.gate_status,
            warnings=run.warnings,
            created_job_ids=run.created_job_ids,
            created_artifacts=artifacts,
            idempotency_key=run.idempotency_key,
            request_hash=run.request_hash,
        )
        finished_at = _utcnow()
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="generation_planner",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=inference_response.model or inference_request.model,
            critic_profile=None,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=_provider_backend_version(inference_response.raw_response),
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload({"plan_id": plan_id, "content": inference_response.content}),
            prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
            input_artifact_refs=["canon_generation_packet"],
            output_artifact_refs=["generation_plan"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=inference_response.finish_reason or "completed",
            error_code=None,
            error_category=None,
            executor_id="job-worker-local",
            lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
        )
        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step="generation_planner",
            detail="Generation planner phase finished.",
            finish_reason=inference_response.finish_reason or "completed",
        )
    def _run_generation_drafter_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.generation import CanonGenerationPacket, GenerationPlan

        payload = dict(request_payload.get("payload", {}))
        generation_id = str(payload.get("generation_id", "")).strip()
        packet_id = str(payload.get("packet_id", "")).strip()
        chapter_ids = list(payload.get("chapter_ids") or [])
        if not chapter_ids and isinstance(payload.get("chapter_id"), str):
            chapter_ids = [str(payload["chapter_id"])]
        if not generation_id or not packet_id or not chapter_ids:
            raise ValueError("G-300 requires generation_id, packet_id, and chapter_id(s).")
        packet_record = self._story_repository.get_canon_generation_packet(packet_id)
        packet = CanonGenerationPacket.model_validate(packet_record.packet_json)
        plan = GenerationPlan(
            plan_id=f"generation-plan-{stable_hash_text(f'{generation_id}:{packet_id}')[:12]}",
            project_id=packet.target_project_id,
            packet_id=packet.packet_id,
            mode=packet.mode,
            premise=str(packet.foundation_snapshot.get("premise", "")),
            logline=str(packet.foundation_snapshot.get("logline", "")),
            story_arcs=[],
            chapter_plans=[{"chapter_id": chapter_id} for chapter_id in chapter_ids],
            canon_obligations=[],
            intentional_differences=[],
            forbidden_contradictions=packet.canon_policy.forbidden_contradictions,
            status="draft",
            gate_reasons=[],
        )
        prior_summaries: list[str] = []
        created_artifacts: list[dict[str, str]] = []
        for chapter_id in chapter_ids:
            inference_request = build_g300_chapter_generation_request(
                packet,
                plan,
                str(chapter_id),
                prior_summaries=prior_summaries,
                default_model=None,
            )
            inference_response = self._inferencer.generate_text(inference_request)
            content = inference_response.content.strip() or f"# {chapter_id}\n\nNo content generated."
            artifact_id = f"gen-draft-{stable_hash_text(f'{generation_id}:{chapter_id}')[:12]}"
            self._story_repository.upsert_draft_artifact(
                artifact_id=artifact_id,
                project_id=packet.target_project_id,
                title=f"Generated {chapter_id}",
                content=content,
                source_plan_ids=[plan.plan_id],
                source_context=[generation_id, str(chapter_id)],
                provenance_note=f"Generated from packet {packet.packet_id}",
                status="DRAFT",
            )
            self._story_repository.upsert_manuscript_document(
                document_id=f"manuscript-{artifact_id}",
                project_id=packet.target_project_id,
                title=f"Generated {chapter_id}",
                content=content,
                chapter_id=None,
                scene_id=None,
                current_draft_artifact_id=artifact_id,
            )
            created_artifacts.append(
                {
                    "artifact_kind": "draft_artifact",
                    "artifact_id": artifact_id,
                    "project_id": packet.target_project_id,
                }
            )
            prior_summaries.append(content[:400])
        run = self._story_repository.get_canon_generation_run(generation_id)
        self._story_repository.upsert_canon_generation_run(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            mode=run.mode,
            request_json=run.request_json,
            canon_scope_json=run.canon_scope_json,
            canon_policy_json=run.canon_policy_json,
            status="running",
            gate_status=run.gate_status,
            warnings=run.warnings,
            created_job_ids=run.created_job_ids,
            created_artifacts=[*run.created_artifacts, *created_artifacts],
            idempotency_key=run.idempotency_key,
            request_hash=run.request_hash,
        )
        finished_at = _utcnow()
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="generation_drafter",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=None,
            critic_profile=None,
            backend_name="generation_drafter",
            backend_version="v1",
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload(created_artifacts),
            prompt_hash=stable_hash_payload({"packet_id": packet_id}),
            input_artifact_refs=["generation_plan"],
            output_artifact_refs=["draft_artifact"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason="completed",
            error_code=None,
            error_category=None,
            executor_id="job-worker-local",
            lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
        )
        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step="generation_drafter",
            detail="Generation drafter phase finished.",
            finish_reason="completed",
        )
    def _run_generation_gate_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.generation import CanonGenerationPacket

        payload = dict(request_payload.get("payload", {}))
        generation_id = str(payload.get("generation_id", "")).strip()
        packet_id = str(payload.get("packet_id", "")).strip()
        if not generation_id or not packet_id:
            raise ValueError("G-350 requires generation_id and packet_id.")
        packet_record = self._story_repository.get_canon_generation_packet(packet_id)
        packet = CanonGenerationPacket.model_validate(packet_record.packet_json)
        run = self._story_repository.get_canon_generation_run(generation_id)
        draft_refs = [item for item in run.created_artifacts if item.get("artifact_kind") == "draft_artifact"]
        blocked = False
        for ref in draft_refs:
            artifact_id = str(ref.get("artifact_id", ""))
            if not artifact_id:
                continue
            draft = self._story_repository.get_draft_artifact(artifact_id)
            result = self._generation_gates.check_chapter_draft(packet, artifact_id, draft.content)
            gate_result_id = f"generation-gate-{stable_hash_text(f'{generation_id}:{artifact_id}:{result.gate_name}')[:12]}"
            self._story_repository.upsert_generation_gate_result(
                gate_result_id=gate_result_id,
                generation_id=generation_id,
                project_id=packet.target_project_id,
                artifact_kind="draft_artifact",
                artifact_id=artifact_id,
                gate_name=result.gate_name,
                passed=result.passed,
                severity=result.severity,
                reasons=result.reasons,
                repair_attempted=False,
                repair_job_id=None,
            )
            if self._generation_gates.should_block(result, packet.canon_policy):
                blocked = True
        self._story_repository.upsert_canon_generation_run(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            mode=run.mode,
            request_json=run.request_json,
            canon_scope_json=run.canon_scope_json,
            canon_policy_json=run.canon_policy_json,
            status="blocked" if blocked else "running",
            gate_status="blocked" if blocked else "passed",
            warnings=run.warnings,
            created_job_ids=run.created_job_ids,
            created_artifacts=run.created_artifacts,
            idempotency_key=run.idempotency_key,
            request_hash=run.request_hash,
        )
        finished_at = _utcnow()
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="generation_gate",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=None,
            critic_profile=None,
            backend_name="generation_gate",
            backend_version="v1",
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload({"blocked": blocked}),
            prompt_hash=stable_hash_payload({"packet_id": packet_id}),
            input_artifact_refs=["draft_artifact"],
            output_artifact_refs=["generation_gate_result"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason="completed",
            error_code=None,
            error_category=None,
            executor_id="job-worker-local",
            lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
        )
        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step="generation_gate",
            detail="Generation gate phase finished.",
            finish_reason="completed",
        )
    def _run_generation_compiler_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.generation import CanonGenerationPacket

        payload = dict(request_payload.get("payload", {}))
        generation_id = str(payload.get("generation_id", "")).strip()
        packet_id = str(payload.get("packet_id", "")).strip()
        if not generation_id or not packet_id:
            raise ValueError("G-400 requires generation_id and packet_id.")
        packet_record = self._story_repository.get_canon_generation_packet(packet_id)
        packet = CanonGenerationPacket.model_validate(packet_record.packet_json)
        run = self._story_repository.get_canon_generation_run(generation_id)
        if run.gate_status == "blocked":
            raise ValueError("Generation is blocked by canon gates.")
        draft_refs = [item for item in run.created_artifacts if item.get("artifact_kind") == "draft_artifact"]
        chapter_artifacts: list[dict[str, str]] = []
        for ref in draft_refs:
            artifact_id = str(ref.get("artifact_id", ""))
            if not artifact_id:
                continue
            draft = self._story_repository.get_draft_artifact(artifact_id)
            chapter_artifacts.append({"artifact_id": draft.artifact_id, "content": draft.content})
        inference_request = build_g400_manuscript_assembly_request(packet, chapter_artifacts, default_model=None)
        inference_response = self._inferencer.generate_text(inference_request)
        content = inference_response.content.strip() or "\n\n".join(item["content"] for item in chapter_artifacts)
        document_id = f"generation-manuscript-{stable_hash_text(generation_id)[:12]}"
        self._story_repository.upsert_manuscript_document(
            document_id=document_id,
            project_id=packet.target_project_id,
            title=f"Generated Manuscript {generation_id}",
            content=content,
            chapter_id=None,
            scene_id=None,
            current_draft_artifact_id=None,
        )
        self._story_repository.upsert_canon_generation_run(
            generation_id=run.generation_id,
            source_project_id=run.source_project_id,
            target_project_id=run.target_project_id,
            mode=run.mode,
            request_json=run.request_json,
            canon_scope_json=run.canon_scope_json,
            canon_policy_json=run.canon_policy_json,
            status="completed",
            gate_status=run.gate_status,
            warnings=run.warnings,
            created_job_ids=run.created_job_ids,
            created_artifacts=[
                *run.created_artifacts,
                {
                    "artifact_kind": "manuscript_document",
                    "artifact_id": document_id,
                    "project_id": packet.target_project_id,
                },
            ],
            idempotency_key=run.idempotency_key,
            request_hash=run.request_hash,
        )
        finished_at = _utcnow()
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="generation_compiler",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=inference_response.model or inference_request.model,
            critic_profile=None,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=_provider_backend_version(inference_response.raw_response),
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload({"document_id": document_id}),
            prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
            input_artifact_refs=["draft_artifact"],
            output_artifact_refs=["manuscript_document"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=inference_response.finish_reason or "completed",
            error_code=None,
            error_category=None,
            executor_id="job-worker-local",
            lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
        )
        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step="generation_compiler",
            detail="Generation compiler phase finished.",
            finish_reason=inference_response.finish_reason or "completed",
        )