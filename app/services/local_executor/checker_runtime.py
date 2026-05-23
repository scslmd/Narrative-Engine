from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from ...persistence.steps import stable_hash_payload
from ...schemas.role_model_checker import RoleModelCheckStartRequest
from .helpers import checker_runtime_response as _checker_runtime_response, provider_backend_version as _provider_backend_version, utcnow as _utcnow



class _CheckerRuntimeMixin:

    def _process_checker(self, run_id: UUID) -> None:
        try:
            payload = self._role_check_manager.get_request_payload(run_id)
            request = RoleModelCheckStartRequest.model_validate(payload)
            attempt = self._role_check_manager.get_attempt(run_id)
            self._role_check_manager.update_run(run_id, status="RUNNING", detail="Checker run started.")
            for index, role_result in enumerate(self._role_check_service.run_checks(request), start=1):
                runtime_response = _checker_runtime_response(role_result)
                runtime_request = role_result.metadata.get("inference_request")
                is_runtime_backed = role_result.metadata.get("execution_mode") == "runtime_backed" and runtime_response is not None
                backend_name = "role-model-checker"
                backend_version = "stub"
                model_id = str(role_result.metadata.get("selected_model") or "")
                prompt_payload: object = {
                    "role": role_result.role,
                    "critic_profile": request.critic_profile if role_result.role == "critic" else None,
                }
                input_payload: object = payload
                output_payload: object = role_result.model_dump(mode="json")
                finish_reason = "passed" if role_result.passed else "validation_failed"
                prompt_tokens: int | None = None
                completion_tokens: int | None = None
                total_tokens: int | None = None

                if is_runtime_backed:
                    backend_name = str(
                        role_result.metadata.get("inference_backend")
                        or runtime_response.get("backend")
                        or backend_name
                    )
                    backend_version = _provider_backend_version(runtime_response.get("raw_response")) or backend_version
                    model_id = str(runtime_response.get("model") or role_result.metadata.get("selected_model") or "")
                    prompt_payload = runtime_request if isinstance(runtime_request, dict) else prompt_payload
                    input_payload = {
                        "checker_request": payload,
                        "runtime_request": prompt_payload,
                    }
                    finish_reason = str(runtime_response.get("finish_reason") or "runtime_completed")
                    usage = runtime_response.get("usage")
                    if isinstance(usage, dict):
                        prompt_tokens = usage.get("prompt_tokens")
                        completion_tokens = usage.get("completion_tokens")
                        total_tokens = usage.get("total_tokens")

                self._role_check_manager.update_run(
                    run_id,
                    current_role=role_result.role,
                    detail=f"Testing {role_result.role}.",
                )
                self._role_check_manager.add_result(run_id, role_result)
                finished_at = _utcnow()
                started_at = finished_at - timedelta(seconds=float(role_result.duration_seconds))
                step_record_id = self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=run_id,
                    run_kind="role_model_check",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name=str(role_result.role),
                    step_index=index,
                    state="COMPLETED" if role_result.passed else "FAILED",
                    project_id=None,
                    model_id=model_id or None,
                    critic_profile=request.critic_profile if role_result.role == "critic" else None,
                    backend_name=backend_name,
                    backend_version=backend_version,
                    input_hash=stable_hash_payload(input_payload) if input_payload else None,
                    output_hash=stable_hash_payload(output_payload) if output_payload else None,
                    prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
                    input_artifact_refs=[],
                    output_artifact_refs=[f"checker_result:{role_result.role}"],
                    started_at=started_at,
                    finished_at=finished_at,
                    finish_reason=finish_reason,
                    error_code=None if role_result.passed else "CHECKER_FAILED",
                    error_category=None if role_result.passed else "deterministic_validation",
                    executor_id="checker-worker-local",
                    lease_owner=str(attempt.get("lease_owner") or "checker-worker-local"),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
            final_detail = "Checker run finished."
            report_path: Path | None = None
            interim_status = self._role_check_manager.get_status(run_id)
            if request.save_report:
                report_path = self._role_check_service.save_report(run_id, request, interim_status.results)
                final_detail = "Checker run finished and report saved."
            if report_path is not None:
                persist_finished_at = _utcnow()
                persist_started_at = persist_finished_at
                persist_step_record_id = self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=run_id,
                    run_kind="role_model_check",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="report_persist",
                    step_index=len(interim_status.results) + 1,
                    state="COMPLETED",
                    project_id=None,
                    model_id=None,
                    critic_profile=None,
                    backend_name="role-model-checker",
                    backend_version="stub",
                    input_hash=stable_hash_payload([result.model_dump(mode="json") for result in interim_status.results]),
                    output_hash=stable_hash_payload({"report_path": str(report_path)}),
                    prompt_hash=stable_hash_payload({"save_report": True}),
                    input_artifact_refs=[f"checker_result:{result.role}" for result in interim_status.results],
                    output_artifact_refs=["checker_report"],
                    started_at=persist_started_at,
                    finished_at=persist_finished_at,
                    finish_reason="report_saved",
                    error_code=None,
                    error_category=None,
                    executor_id="checker-worker-local",
                    lease_owner=str(attempt.get("lease_owner") or "checker-worker-local"),
                )
                self._step_records.create_lineage_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=run_id,
                    run_kind="role_model_check",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="report_persist",
                    project_id=None,
                    artifact_role="checker_report",
                    artifact_kind="json",
                    path=str(report_path),
                    content_hash=report_path.read_text(encoding="utf-8"),
                    status="CANONICAL",
                    validation_state="PASSED",
                    produced_at=persist_finished_at,
                    registered_at=persist_finished_at,
                    supersedes_artifact_lineage_id=None,
                    source_artifact_refs=[f"checker_result:{result.role}" for result in interim_status.results],
                    source_content_hashes=[],
                    output_of_step_record_id=persist_step_record_id,
                )
            final_status = self._role_check_manager.update_run(
                run_id,
                status="COMPLETED",
                detail=final_detail,
                report_path=str(report_path) if report_path is not None else None,
                finish_reason="stub_completed",
            )
        except Exception as exc:
            self._role_check_manager.update_run(
                run_id,
                status="FAILED",
                detail="Checker run failed.",
                finish_reason="executor_error",
                failure_stage="run",
                retryable=False,
            )
            try:
                attempt = self._role_check_manager.get_attempt(run_id)
                payload = self._role_check_manager.get_request_payload(run_id)
                self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=run_id,
                    run_kind="role_model_check",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="checker_run",
                    step_index=1,
                    state="FAILED",
                    project_id=None,
                    model_id=None,
                    critic_profile=None,
                    backend_name="role-model-checker",
                    backend_version="stub",
                    input_hash=stable_hash_payload(payload) if payload else None,
                    output_hash=stable_hash_payload({"error": str(exc)}),
                    prompt_hash=stable_hash_payload({"failure_stage": "run"}),
                    input_artifact_refs=[],
                    output_artifact_refs=[],
                    started_at=_utcnow(),
                    finished_at=_utcnow(),
                    finish_reason="executor_error",
                    error_code=str(exc),
                    error_category="executor",
                    executor_id="checker-worker-local",
                    lease_owner=str(attempt.get("lease_owner") or "checker-worker-local"),
                )
            except Exception:
                pass