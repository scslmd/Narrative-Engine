from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any
from uuid import UUID

from ..inference import InferenceBackend, InferenceBackendError, StubInferenceBackend
from ..persistence.steps import stable_hash_payload
from ..schemas.role_model_checker import RoleModelCheckStartRequest
from .job_manager import JobManager
from .projects import ProjectService
from .role_model_check_manager import RoleModelCheckManager
from .role_model_checker import RoleModelCheckerService
from .runtime_prompts import architect_output_path, build_p100_architect_request
from .step_records import StepRecordService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _provider_backend_version(raw_response: dict[str, Any]) -> str | None:
    for key in ("backend_version", "provider_version", "version"):
        value = raw_response.get(key)
        if value is not None:
            return str(value)
    return None


def _checker_runtime_response(role_result: Any) -> dict[str, Any] | None:
    runtime_response = role_result.metadata.get("runtime_response")
    return runtime_response if isinstance(runtime_response, dict) else None


class LocalExecutor:
    def __init__(
        self,
        *,
        job_manager: JobManager,
        role_check_manager: RoleModelCheckManager,
        role_check_service: RoleModelCheckerService,
        inferencer: InferenceBackend | None = None,
        project_service: ProjectService | None = None,
        step_record_service: StepRecordService | None = None,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        self._job_manager = job_manager
        self._role_check_manager = role_check_manager
        self._role_check_service = role_check_service
        self._inferencer = inferencer or StubInferenceBackend()
        self._project_service = project_service or ProjectService()
        self._step_records = step_record_service or StepRecordService()
        self._poll_interval_seconds = poll_interval_seconds
        self._stop_event = Event()
        self._threads: list[Thread] = []

    def start(self) -> None:
        if self._threads:
            return
        self._threads = [
            Thread(target=self._job_loop, name="narrative-job-worker", daemon=True),
            Thread(target=self._checker_loop, name="narrative-checker-worker", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads = []
        self._stop_event.clear()

    def _job_loop(self) -> None:
        worker_id = "job-worker-local"
        while not self._stop_event.is_set():
            job_id = self._job_manager.claim_next_pending(worker_id=worker_id)
            if job_id is None:
                sleep(self._poll_interval_seconds)
                continue
            self._process_job(job_id)

    def _checker_loop(self) -> None:
        worker_id = "checker-worker-local"
        while not self._stop_event.is_set():
            run_id = self._role_check_manager.claim_next_pending(worker_id=worker_id)
            if run_id is None:
                sleep(self._poll_interval_seconds)
                continue
            self._process_checker(run_id)

    def _process_job(self, job_id: UUID) -> None:
        started_at = _utcnow()
        try:
            current = self._job_manager.get_status(job_id)
            attempt = self._job_manager.get_attempt(job_id)
            request_payload = self._job_manager.get_request_payload(job_id)
            project_id = str(request_payload.get("payload", {}).get("project_id", "")).strip() or None
            self._job_manager.update_job(
                job_id,
                status="PROCESSING",
                current_phase=str(current.phase),
                current_step="architect" if str(current.phase) == "P-100" else str(current.phase),
                detail="Local worker started.",
            )
            self._job_manager.log(job_id, "INFO", f"Job claimed by local worker for phase {current.phase}.")
            if str(current.phase) == "P-100":
                self._run_architect_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=str(current.phase),
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            self._job_manager.update_job(
                job_id,
                status="COMPLETED",
                detail="Local worker finished.",
                progress_current=1,
                progress_total=1,
                finish_reason="stub_completed",
            )
            finished_at = _utcnow()
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name=str(current.phase),
                step_index=1,
                state="COMPLETED",
                project_id=project_id,
                model_id=None,
                critic_profile=None,
                backend_name="local-job-worker",
                backend_version="stub",
                input_payload=request_payload,
                output_payload={
                    "status": "COMPLETED",
                    "phase": str(current.phase),
                    "detail": "Local worker finished.",
                },
                prompt_payload={"phase": str(current.phase), "step_name": str(current.phase)},
                input_artifact_refs=["manifest"] if project_id else [],
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=finished_at,
                finish_reason="stub_completed",
                error_code=None,
                error_category=None,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
        except Exception as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                error=str(exc),
                detail="Local worker failed.",
                finish_reason="executor_error",
                failure_stage="run",
                retryable=False,
            )
            try:
                attempt = self._job_manager.get_attempt(job_id)
                request_payload = self._job_manager.get_request_payload(job_id)
                project_id = str(request_payload.get("payload", {}).get("project_id", "")).strip() or None
                self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=job_id,
                    run_kind="pipeline_job",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="architect" if str(self._job_manager.get_status(job_id).phase) == "P-100" else str(self._job_manager.get_status(job_id).phase),
                    step_index=1,
                    state="FAILED",
                    project_id=project_id,
                    model_id=None,
                    critic_profile=None,
                    backend_name="local-job-worker",
                    backend_version="stub",
                    input_payload=request_payload,
                    output_payload={"error": str(exc)},
                    prompt_payload={"failure_stage": "run"},
                    input_artifact_refs=["manifest"] if project_id else [],
                    output_artifact_refs=[],
                    started_at=started_at,
                    finished_at=_utcnow(),
                    finish_reason="executor_error",
                    error_code=str(exc),
                    error_category="executor",
                    executor_id="job-worker-local",
                    lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                )
            except Exception:
                pass

    def _run_architect_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str | None,
    ) -> None:
        if not project_id:
            raise ValueError("P-100 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        inference_request = build_p100_architect_request(
            manifest=project.manifest,
            payload=payload,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="architect",
            detail="Architect inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="architect",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="architect",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_payload={
                    "job_request": request_payload,
                    "manifest": project.manifest.model_dump(mode="json"),
                },
                output_payload=None,
                prompt_payload=inference_request.model_dump(mode="json"),
                input_artifact_refs=["manifest"],
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=exc.finish_reason,
                error_code=exc.code,
                error_category=exc.category,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            return
        output_path = architect_output_path(Path(project.project_dir))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        output_path.write_text(output_text, encoding="utf-8")
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step="architect",
            detail="Architect phase finished.",
            progress_current=1,
            progress_total=1,
            finish_reason=normalized_finish_reason,
        )
        finished_at = _utcnow()
        step_record_id = self._step_records.create_step_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="architect",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id=inference_response.model or inference_request.model,
            critic_profile=None,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=["manifest"],
            output_artifact_refs=["architect_output"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            error_code=None,
            error_category=None,
            executor_id="job-worker-local",
            lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
        )
        self._step_records.create_lineage_record(
            logical_run_id=str(attempt["logical_run_id"]),
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=int(attempt["attempt_number"]),
            step_name="architect",
            project_id=project_id,
            artifact_role="architect_output",
            artifact_kind="markdown",
            path=str(output_path),
            content_hash_source=output_text,
            status="CANONICAL",
            validation_state="PASSED",
            produced_at=finished_at,
            registered_at=finished_at,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=["manifest"],
            source_content_hashes=[stable_hash_payload(project.manifest.model_dump(mode="json"))],
            output_of_step_record_id=step_record_id,
        )
        self._project_service.register_generated_artifact(
            project_id,
            "architect_p100",
            output_path,
        )

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
                    input_payload=input_payload,
                    output_payload=output_payload,
                    prompt_payload=prompt_payload,
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
            final_status = self._role_check_manager.update_run(
                run_id,
                status="COMPLETED",
                detail="Checker run finished.",
                finish_reason="stub_completed",
            )
            if request.save_report:
                report_path = self._role_check_service.save_report(run_id, request, final_status.results)
                persist_finished_at = _utcnow()
                persist_started_at = persist_finished_at
                persist_step_record_id = self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=run_id,
                    run_kind="role_model_check",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name="report_persist",
                    step_index=len(final_status.results) + 1,
                    state="COMPLETED",
                    project_id=None,
                    model_id=None,
                    critic_profile=None,
                    backend_name="role-model-checker",
                    backend_version="stub",
                    input_payload=[result.model_dump(mode="json") for result in final_status.results],
                    output_payload={"report_path": str(report_path)},
                    prompt_payload={"save_report": True},
                    input_artifact_refs=[f"checker_result:{result.role}" for result in final_status.results],
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
                    content_hash_source=report_path.read_text(encoding="utf-8"),
                    status="CANONICAL",
                    validation_state="PASSED",
                    produced_at=persist_finished_at,
                    registered_at=persist_finished_at,
                    supersedes_artifact_lineage_id=None,
                    source_artifact_refs=[f"checker_result:{result.role}" for result in final_status.results],
                    source_content_hashes=[],
                    output_of_step_record_id=persist_step_record_id,
                )
                self._role_check_manager.update_run(
                    run_id,
                    report_path=str(report_path),
                    detail="Checker run finished and report saved.",
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
                    input_payload=payload,
                    output_payload={"error": str(exc)},
                    prompt_payload={"failure_stage": "run"},
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
