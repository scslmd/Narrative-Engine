from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from ...persistence.story_development import StoryDevelopmentRepository
from ...persistence.steps import stable_hash_payload, stable_hash_text
from ...settings import settings
from ..manuscript_assist_gates import ManuscriptAssistGateService
from ..runtime_prompts import (
    build_m500_draft_generation_request,
    build_m500_manuscript_assist_request,
    build_m550_manuscript_repair_request,
)
from .helpers import provider_backend_version as _provider_backend_version, utcnow as _utcnow



class _ManuscriptAssistPhasesMixin:

    def _run_manuscript_assist_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.manuscript_assist import (
            AssistSuggestionStatus,
            LLMRevisionSuggestion,
            ManuscriptAssistKind,
            ManuscriptAssistPacket,
            ManuscriptAssistRequest,
            TextRange,
        )
        from app.utils.json_extract import extract_json

        payload = dict(request_payload.get("payload", {}))
        assist_id = str(payload.get("assist_id", "")).strip()
        if not assist_id:
            raise ValueError("M-500 requires payload.assist_id.")
        run = self._story_repository.get_manuscript_assist_run(assist_id)
        document = self._story_repository.get_manuscript_document(run.document_id)
        request = ManuscriptAssistRequest.model_validate(run.request_json)
        packet = ManuscriptAssistPacket(
            assist_id=run.assist_id,
            project_id=run.project_id,
            document_id=run.document_id,
            assist_kind=request.assist_kind,
            instruction=request.instruction,
            document_title=document.title,
            document_content=document.content,
            text_range=request.text_range,
            canon_scope=request.canon_scope,
            canon_policy=request.canon_policy,
            model_id=request.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        # Draft generation path — uses full-content prompt instead of suggestions prompt
        if request.create_draft_artifact and request.assist_kind == ManuscriptAssistKind.AI_GENERATE_DRAFT:
            inference_request = build_m500_draft_generation_request(packet, default_model=None)
        else:
            inference_request = build_m500_manuscript_assist_request(packet, default_model=None)

        inference_response = self._inferencer.generate_text(inference_request)

        # Draft artifact creation path (NEW)
        if request.create_draft_artifact and request.assist_kind == ManuscriptAssistKind.AI_GENERATE_DRAFT:
            from app.services.drafting import DraftingService

            extracted = extract_json(inference_response.content)
            parsed: dict[str, Any] = extracted if isinstance(extracted, dict) else {}
            full_content = str(parsed.get("full_content") or "").strip()
            summary = str(parsed.get("summary") or "").strip()
            warnings = [str(item) for item in parsed.get("warnings", []) if isinstance(item, str)]

            if not full_content:
                self._story_repository.upsert_manuscript_assist_run(
                    assist_id=run.assist_id,
                    project_id=run.project_id,
                    document_id=run.document_id,
                    assist_kind=run.assist_kind,
                    request_json=run.request_json,
                    status="failed",
                    summary="LLM response did not contain full_content.",
                    created_draft_artifact_id=None,
                    created_branch_id=run.created_branch_id,
                    created_manuscript_document_id=run.created_manuscript_document_id,
                    job_ids=run.job_ids,
                    warnings=warnings,
                    idempotency_key=run.idempotency_key,
                    request_hash=run.request_hash,
                )
                finished_at = _utcnow()
                self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=job_id,
                    run_kind="pipeline_job",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="manuscript_assist",
                    step_index=1,
                    state="FAILED",
                    project_id=project_id,
                    model_id=inference_response.model or inference_request.model,
                    critic_profile=None,
                    backend_name=self._inferencer.descriptor.display_name,
                    backend_version=_provider_backend_version(inference_response.raw_response),
                    input_hash=stable_hash_payload(request_payload),
                    output_hash=stable_hash_payload({"error": "no full_content in LLM response"}),
                    prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                    input_artifact_refs=["manuscript_document"],
                    output_artifact_refs=[],
                    started_at=started_at,
                    finished_at=finished_at,
                    finish_reason="invalid_llm_response",
                    error_code="missing_full_content",
                    error_category="llm_output",
                    executor_id="job-worker-local",
                    lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                )
                self._job_manager.update_job(
                    job_id, status="FAILED", current_phase=current_phase,
                    current_step="manuscript_assist", error="missing_full_content",
                    error_category="llm_output", detail="LLM response did not contain full_content key.",
                    finish_reason="invalid_llm_response", failure_stage="parsing", retryable=True,
                )
                return

            title = (document.title or request.instruction.split("\n")[0]).strip()[:255] or "Generated Draft"
            draft_id = f"draft-{stable_hash_text(f'{run.project_id}:{title}')[:16]}"

            _drafting_repo = StoryDevelopmentRepository(settings.operations_db_path)
            drafting_svc = DraftingService(repository=_drafting_repo)
            drafting_svc.register_draft_artifact(
                project_id=run.project_id,
                artifact_id=draft_id,
                title=title,
                content=full_content,
                provenance_note=f"AI-generated via assist {assist_id}",
                status="DRAFT",
            )

            self._story_repository.upsert_manuscript_assist_run(
                assist_id=run.assist_id,
                project_id=run.project_id,
                document_id=run.document_id,
                assist_kind=run.assist_kind,
                request_json=run.request_json,
                status="completed",
                summary=summary,
                created_draft_artifact_id=draft_id,
                created_branch_id=run.created_branch_id,
                created_manuscript_document_id=run.created_manuscript_document_id,
                job_ids=run.job_ids,
                warnings=warnings,
                idempotency_key=run.idempotency_key,
                request_hash=run.request_hash,
            )
            finished_at = _utcnow()
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="manuscript_assist",
                step_index=1,
                state="COMPLETED",
                project_id=project_id,
                model_id=inference_response.model or inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=_provider_backend_version(inference_response.raw_response),
                input_hash=stable_hash_payload(request_payload),
                output_hash=stable_hash_payload({"draft_artifact_id": draft_id}),
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=["manuscript_document"],
                output_artifact_refs=["draft_artifact"],
                started_at=started_at,
                finished_at=finished_at,
                finish_reason=inference_response.finish_reason or "completed",
                error_code=None,
                error_category=None,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            self._job_manager.update_job(
                job_id, status="COMPLETED", current_phase=current_phase,
                current_step="manuscript_assist",
                detail=f"Draft artifact {draft_id} created via AI generation.",
                finish_reason=inference_response.finish_reason or "completed",
            )
            return

        extracted = extract_json(inference_response.content)
        parsed: dict[str, Any] = extracted if isinstance(extracted, dict) else {}
        summary = str(parsed.get("summary") or "").strip()
        warnings = [str(item) for item in parsed.get("warnings", []) if isinstance(item, str)]
        suggestions_raw = parsed.get("suggestions", [])
        gate_service = ManuscriptAssistGateService()
        created_suggestion_ids: list[str] = []
        for index, raw in enumerate(suggestions_raw if isinstance(suggestions_raw, list) else []):
            if not isinstance(raw, dict):
                continue
            source_text = str(raw.get("source_text") or "")
            proposed_text = str(raw.get("proposed_text") or "")
            rationale = str(raw.get("rationale") or "")
            if not source_text.strip() or not proposed_text.strip():
                continue
            range_json = request.text_range.model_dump(mode="json") if request.text_range is not None else None
            suggestion_id = f"assist-suggestion-{stable_hash_text(f'{assist_id}:{index}:{source_text}:{proposed_text}')[:16]}"
            suggestion = self._story_repository.upsert_manuscript_assist_suggestion(
                suggestion_id=suggestion_id,
                assist_id=assist_id,
                project_id=run.project_id,
                target_document_id=run.document_id,
                suggestion_kind=request.assist_kind.value if hasattr(request.assist_kind, "value") else str(request.assist_kind),
                source_text=source_text,
                proposed_text=proposed_text,
                rationale=rationale or "Generated manuscript assist suggestion.",
                range_json=range_json,
                canon_risk=str(raw.get("canon_risk") or "none"),
                confidence_score=float(raw.get("confidence_score") or 0.0),
                source_context=[str(item) for item in raw.get("source_context", []) if isinstance(item, str)],
                status=AssistSuggestionStatus.PENDING.value,
            )
            created_suggestion_ids.append(suggestion.suggestion_id)
            llm_suggestion = LLMRevisionSuggestion(
                suggestion_id=suggestion.suggestion_id,
                assist_id=suggestion.assist_id,
                project_id=suggestion.project_id,
                target_document_id=suggestion.target_document_id,
                source_text=suggestion.source_text,
                proposed_text=suggestion.proposed_text,
                rationale=suggestion.rationale,
                suggestion_kind=request.assist_kind,
                range=TextRange.model_validate(suggestion.range_json) if suggestion.range_json else None,
                canon_risk=suggestion.canon_risk,
                confidence_score=suggestion.confidence_score,
                status=suggestion.status,
                source_context=suggestion.source_context,
            )
            gate = gate_service.check_suggestion_against_canon(llm_suggestion)
            gate_result_id = f"assist-gate-{stable_hash_text(f'{assist_id}:{suggestion_id}:{gate.gate_name}')[:16]}"
            self._story_repository.upsert_manuscript_assist_gate_result(
                gate_result_id=gate_result_id,
                assist_id=assist_id,
                project_id=run.project_id,
                document_id=run.document_id,
                gate_name=gate.gate_name,
                passed=gate.passed,
                severity=gate.severity,
                reasons=gate.reasons,
            )
        self._story_repository.upsert_manuscript_assist_run(
            assist_id=run.assist_id,
            project_id=run.project_id,
            document_id=run.document_id,
            assist_kind=run.assist_kind,
            request_json=run.request_json,
            status="completed",
            summary=summary,
            created_draft_artifact_id=run.created_draft_artifact_id,
            created_branch_id=run.created_branch_id,
            created_manuscript_document_id=run.created_manuscript_document_id,
            job_ids=run.job_ids,
            warnings=warnings,
            idempotency_key=run.idempotency_key,
            request_hash=run.request_hash,
        )
        finished_at = _utcnow()
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="manuscript_assist",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=inference_response.model or inference_request.model,
            critic_profile=None,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=_provider_backend_version(inference_response.raw_response),
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload({"suggestion_ids": created_suggestion_ids}),
            prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
            input_artifact_refs=["manuscript_document"],
            output_artifact_refs=["manuscript_assist_suggestion", "manuscript_assist_gate_result"],
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
            current_step="manuscript_assist",
            detail="Manuscript assist phase finished.",
            finish_reason=inference_response.finish_reason or "completed",
        )
    def _run_manuscript_assist_repair_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, Any],
        project_id: str | None,
    ) -> None:
        from app.schemas.manuscript_assist import ManuscriptAssistPacket, ManuscriptAssistRequest

        payload = dict(request_payload.get("payload", {}))
        assist_id = str(payload.get("assist_id", "")).strip()
        gate_result_id = str(payload.get("gate_result_id", "")).strip()
        if not assist_id or not gate_result_id:
            raise ValueError("M-550 requires payload.assist_id and payload.gate_result_id.")
        run = self._story_repository.get_manuscript_assist_run(assist_id)
        request = ManuscriptAssistRequest.model_validate(run.request_json)
        packet = ManuscriptAssistPacket(
            assist_id=run.assist_id,
            project_id=run.project_id,
            document_id=run.document_id,
            assist_kind=request.assist_kind,
            instruction=request.instruction,
            text_range=request.text_range,
            canon_scope=request.canon_scope,
            canon_policy=request.canon_policy,
            model_id=request.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        gate_result = self._story_repository.get_manuscript_assist_gate_result(gate_result_id)
        inference_request = build_m550_manuscript_repair_request(packet, gate_result.reasons, default_model=None)
        inference_response = self._inferencer.generate_text(inference_request)
        self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="manuscript_assist_repair",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=inference_response.model or inference_request.model,
            critic_profile=None,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=_provider_backend_version(inference_response.raw_response),
            input_hash=stable_hash_payload(request_payload),
            output_hash=stable_hash_payload({"assist_id": assist_id, "gate_result_id": gate_result_id}),
            prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
            input_artifact_refs=["manuscript_assist_gate_result"],
            output_artifact_refs=["manuscript_assist_suggestion"],
            started_at=started_at,
            finished_at=_utcnow(),
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
            current_step="manuscript_assist_repair",
            detail="Manuscript assist repair phase finished.",
            finish_reason=inference_response.finish_reason or "completed",
        )