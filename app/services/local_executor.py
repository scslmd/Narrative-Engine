from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any
from uuid import UUID

from ..inference import InferenceBackend, InferenceBackendError, StubInferenceBackend
from ..persistence.story_development import StoryDevelopmentRepository
from ..persistence.steps import stable_hash_payload, stable_hash_text
from ..schemas.inference import InferenceMessage, InferenceRequest
from ..schemas.role_model_checker import RoleModelCheckStartRequest
from ..services.file_permissions import FilePermissionValidator
from ..settings import settings
from .job_manager import JobManager
from .projects import ProjectService
from .role_model_check_manager import RoleModelCheckManager
from .role_model_checker import RoleModelCheckerService
from .runtime_prompts import (
    architect_output_path,
    build_p400_compiler_request,
    build_p300_drafter_request,
    build_p100_architect_request,
    build_p200_sequencer_request,
    chapter_output_path,
    sequence_output_path,
    story_bible_output_path,
)
from .step_records import StepRecordService
from .scene_context import SceneContextService
from .consistency_critic import ConsistencyCriticService
from .entity_intake import EntityIntakeService

logger = logging.getLogger(__name__)


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


def _phase_step_name(phase: str) -> str:
    if phase == "P-100":
        return "architect"
    if phase == "P-200":
        return "sequencer"
    if phase == "P-300":
        return "drafter"
    if phase == "P-400":
        return "compiler"
    return phase


def _require_supported_job_phase(phase: str) -> str:
    if phase in {"P-100", "P-200", "P-300", "P-400"}:
        return phase
    raise ValueError(f"Unsupported job phase: {phase}")


def _upstream_artifact_sources(step_name: str) -> list[tuple[str, str]]:
    if step_name == "sequencer":
        return [("architect_output", "architect_p100")]
    if step_name == "drafter":
        return [("sequence", "sequence"), ("architect_output", "architect_p100")]
    if step_name == "compiler":
        return [("architect_output", "architect_p100"), ("sequence", "sequence"), ("chapter_1", "chapter_1")]
    return []


def _normalized_p100_job_request(request_payload: dict[str, object]) -> dict[str, object]:
    payload = dict(request_payload.get("payload", {}))
    return {
        "phase": request_payload.get("phase"),
        "payload": payload,
    }


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
        scene_context_service: SceneContextService | None = None,
        consistency_critic_service: ConsistencyCriticService | None = None,
        entity_intake_service: EntityIntakeService | None = None,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        self._job_manager = job_manager
        self._role_check_manager = role_check_manager
        self._role_check_service = role_check_service
        self._inferencer = inferencer or StubInferenceBackend()
        self._project_service = project_service or ProjectService()
        self._step_records = step_record_service or StepRecordService()
        self._scene_context = scene_context_service
        self._consistency_critic = consistency_critic_service
        self._entity_intake = entity_intake_service
        self._poll_interval_seconds = poll_interval_seconds
        self._stop_event = Event()
        self._threads: list[Thread] = []
        self._start_lock = threading.Lock()

    def start(self) -> None:
        """Start worker threads with thread-safety (REL-03).
        
        Uses a lock to prevent race conditions where multiple calls could
        create duplicate threads. The check and thread creation are atomic.
        """
        with self._start_lock:
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
            phase = _require_supported_job_phase(str(current.phase))
            current_step = _phase_step_name(phase)
            self._job_manager.update_job(
                job_id,
                status="PROCESSING",
                current_phase=phase,
                current_step=current_step,
                detail="Local worker started.",
            )
            self._job_manager.log(job_id, "INFO", f"Job claimed by local worker for phase {phase}.")
            if phase == "P-100":
                self._run_architect_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "P-200":
                self._run_sequencer_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "P-300":
                self._run_drafter_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "P-400":
                self._run_compiler_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
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
                current_step = _phase_step_name(str(self._job_manager.get_status(job_id).phase))
                self._step_records.create_step_record(
                    logical_run_id=str(attempt["logical_run_id"]),
                    run_id=job_id,
                    run_kind="pipeline_job",
                    attempt_number=int(attempt["attempt_number"]),
                    step_name=current_step,
                    step_index=1,
                    state="FAILED",
                    project_id=project_id,
                    model_id=None,
                    critic_profile=None,
                    backend_name="local-job-worker",
                    backend_version="stub",
                    input_hash=stable_hash_payload(request_payload) if request_payload else None,
                    output_hash=stable_hash_payload({"error": str(exc)}),
                    prompt_hash=stable_hash_payload({"failure_stage": "run"}),
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

    def _finalize_generated_job_phase(
        self,
        *,
        job_id: UUID,
        current_phase: str,
        attempt: dict[str, Any],
        project_id: str,
        step_name: str,
        detail: str,
        model_id: str | None,
        backend_name: str,
        backend_version: str | None,
        input_payload: object,
        output_payload: object,
        prompt_payload: object,
        input_artifact_refs: list[str],
        output_artifact_refs: list[str],
        started_at: datetime,
        finished_at: datetime,
        finish_reason: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        artifact_role: str,
        artifact_kind: str,
        output_path: Path,
        staged_output_path: Path,
        content_hash_source: str,
        source_content_hashes: list[str],
        project_artifact_name: str,
    ) -> None:
        step_record_id: int | None = None
        lineage_record_id: int | None = None
        backup_output_path: Path | None = None
        try:
            backup_output_path = self._publish_staged_output(
                staged_output_path=staged_output_path,
                output_path=output_path,
            )
            step_record_id = self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name=step_name,
                step_index=1,
                state="COMPLETED",
                project_id=project_id,
                model_id=model_id,
                critic_profile=None,
                backend_name=backend_name,
                backend_version=backend_version,
                input_hash=stable_hash_payload(input_payload) if input_payload else None,
                output_hash=stable_hash_payload(output_payload) if output_payload else None,
                prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
                input_artifact_refs=input_artifact_refs,
                output_artifact_refs=output_artifact_refs,
                started_at=started_at,
                finished_at=finished_at,
                finish_reason=finish_reason,
                error_code=None,
                error_category=None,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                created_at=started_at,
                updated_at=finished_at,
            )
            lineage_record_id = self._step_records.create_lineage_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                artifact_kind=artifact_kind,
                path=str(output_path),
                content_hash=content_hash_source,
                status="CANONICAL",
                validation_state="PASSED",
                produced_at=finished_at,
                registered_at=finished_at,
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=input_artifact_refs,
                source_content_hashes=source_content_hashes,
                output_of_step_record_id=step_record_id,
            )
            self._project_service.register_generated_artifact(
                project_id,
                project_artifact_name,
                output_path,
            )
        except Exception as exc:
            failure_finished_at = _utcnow()
            if lineage_record_id is not None:
                try:
                    self._step_records.delete_lineage_record(artifact_lineage_id=lineage_record_id)
                except Exception:
                    pass
            self._restore_published_output(
                output_path=output_path,
                staged_output_path=staged_output_path,
                backup_output_path=backup_output_path,
            )
            if step_record_id is not None:
                try:
                    self._step_records.mark_step_record_failed(
                        step_record_id=step_record_id,
                        finish_reason="persistence_error",
                        error_code=str(exc),
                        error_category="persistence",
                        finished_at=failure_finished_at,
                    )
                except Exception:
                    pass
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step=step_name,
                error=str(exc),
                error_category="persistence",
                detail=f"{step_name.capitalize()} phase persistence failed.",
                finish_reason="persistence_error",
                failure_stage="persistence",
                retryable=False,
            )
            if step_record_id is None:
                try:
                    self._step_records.create_step_record(
                        logical_run_id=str(attempt["logical_run_id"]),
                        run_id=job_id,
                        run_kind="pipeline_job",
                        attempt_number=int(attempt["attempt_number"]),
                        step_name=step_name,
                        step_index=1,
                        state="FAILED",
                        project_id=project_id,
                        model_id=model_id,
                        critic_profile=None,
                        backend_name=backend_name,
                        backend_version=backend_version,
                        input_hash=stable_hash_payload(input_payload) if input_payload else None,
                        output_hash=stable_hash_payload({"error": str(exc), "artifact_path": str(output_path)}),
                        prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
                        input_artifact_refs=input_artifact_refs,
                        output_artifact_refs=[],
                        started_at=started_at,
                        finished_at=failure_finished_at,
                        finish_reason="persistence_error",
                        error_code=str(exc),
                        error_category="persistence",
                        executor_id="job-worker-local",
                        lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                    )
                except Exception:
                    pass
            return

        self._finalize_published_output(
            staged_output_path=staged_output_path,
            backup_output_path=backup_output_path,
        )

        self._job_manager.update_job(
            job_id,
            status="COMPLETED",
            current_phase=current_phase,
            current_step=step_name,
            detail=detail,
            progress_current=1,
            progress_total=1,
            finish_reason=finish_reason,
        )

    def _write_staged_output(self, *, output_path: Path, output_text: str) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        validator = FilePermissionValidator(strict=True)
        validator.validate_directory(output_path.parent, check_world_writable=True)
        
        staged_output_path = output_path.with_name(f"{output_path.name}.staged")
        staged_output_path.write_text(output_text, encoding="utf-8")
        return staged_output_path

    def _publish_staged_output(self, *, staged_output_path: Path, output_path: Path) -> Path | None:
        backup_output_path: Path | None = None
        if output_path.exists():
            backup_output_path = output_path.with_name(f"{output_path.name}.bak")
            if backup_output_path.exists():
                backup_output_path.unlink()
            output_path.replace(backup_output_path)
        staged_output_path.replace(output_path)
        return backup_output_path

    def _restore_published_output(
        self,
        *,
        output_path: Path,
        staged_output_path: Path,
        backup_output_path: Path | None,
    ) -> None:
        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass
        try:
            if backup_output_path is not None and backup_output_path.exists():
                backup_output_path.replace(output_path)
        except Exception:
            pass
        try:
            if staged_output_path.exists():
                staged_output_path.unlink()
        except Exception:
            pass

    def _finalize_published_output(
        self,
        *,
        staged_output_path: Path,
        backup_output_path: Path | None,
    ) -> None:
        if staged_output_path.exists():
            staged_output_path.unlink()
        if backup_output_path is not None and backup_output_path.exists():
            backup_output_path.unlink()

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
        try:
            project = self._project_service.get_project(project_id)
        except FileNotFoundError:
            self._project_service.reconcile_projects()
            project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        job_request = _normalized_p100_job_request(request_payload)
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
                input_hash=stable_hash_payload({
                    "job_request": job_request,
                    "manifest": project.manifest.model_dump(mode="json"),
                }),
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
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
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        step_input_payload = {
            "job_request": job_request,
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
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="architect",
            detail="Architect phase finished.",
            model_id=inference_response.model or inference_request.model,
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
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="architect_output",
            artifact_kind="markdown",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=[stable_hash_payload(project.manifest.model_dump(mode="json"))],
            project_artifact_name="architect_p100",
        )

    def _run_sequencer_phase(
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
            raise ValueError("P-200 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="sequencer",
        )
        architect_output = selected_inputs.get("architect_output")
        inference_request = build_p200_sequencer_request(
            manifest=project.manifest,
            payload=payload,
            architect_output=architect_output,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="sequencer",
            detail="Sequencer inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="sequencer",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="sequencer",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=["manifest"] + (["architect_output"] if architect_output is not None else []),
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
        output_path = sequence_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="sequencer",
            detail="Sequencer phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=["sequence"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="sequence",
            artifact_kind="json",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name="sequence",
        )

    def _run_drafter_phase(
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
            raise ValueError("P-300 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="drafter",
        )
        sequence_output = selected_inputs.get("sequence")
        architect_output = selected_inputs.get("architect_output")
        inference_request = build_p300_drafter_request(
            manifest=project.manifest,
            payload=payload,
            sequence_output=sequence_output,
            architect_output=architect_output,
            default_model=self._inferencer.descriptor.default_model,
        )
        # Context injection: assemble character anchors and world constraints
        if self._scene_context:
            try:
                active_chars: list[str] | None = None
                chapter_id = str(payload.get("chapter_id") or "").strip() or None
                if chapter_id:
                    try:
                        _repo = StoryDevelopmentRepository(settings.operations_db_path)
                        chapter_plan = _repo.get_chapter_plan(chapter_id)
                        active_chars = chapter_plan.active_character_ids if chapter_plan else None
                    except (KeyError, AttributeError):
                        pass

                ctx = self._scene_context.assemble_context(
                    project_id=project_id,
                    active_character_ids=active_chars,
                )
                context_prompt = ctx.to_prompt_string()
                if context_prompt:
                    existing_content = inference_request.messages[1].content
                    new_messages = list(inference_request.messages)
                    new_messages[1] = InferenceMessage(
                        role=new_messages[1].role,
                        content=f"{existing_content}\n\n{context_prompt}",
                    )
                    inference_request = inference_request.model_copy(
                        update={"messages": new_messages},
                    )
            except Exception as exc:
                logger.warning("Context assembly failed, proceeding without: %s", exc)
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="drafter",
            detail="Drafter inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="drafter",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            input_artifact_refs = ["manifest"]
            if sequence_output is not None:
                step_input_payload["sequence"] = sequence_output
                input_artifact_refs.append("sequence")
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
                input_artifact_refs.append("architect_output")
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="drafter",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=input_artifact_refs,
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
        output_path = chapter_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"

        # Shared repository for critic check and entity intake
        _repo = StoryDevelopmentRepository(settings.operations_db_path) if project_id else None
        _chars = _repo.list_character_profiles(project_id) if _repo else []

        # Consistency critic check
        rewrite_needed = False
        critic_result = None
        if self._consistency_critic and project_id:
            try:
                bios = {c.display_name: f"archetype: {c.archetype}; voice: {c.voice_notes}" for c in _chars if c.display_name}
                critic_result = self._consistency_critic.check(output_text, bios)

                if not critic_result.passed and critic_result.violations:
                    rewrite_needed = True
                    logger.info("Critic flagged %d violations, triggering rewrite", len(critic_result.violations))
            except Exception as exc:
                logger.warning("Critic check failed, proceeding with draft: %s", exc)

        if rewrite_needed and critic_result:
            # Build rewrite prompt and execute single retry
            try:
                violation_summary = "\n".join(f"- {v.character}: {v.issue} -> {v.suggestion}" for v in critic_result.violations[:3])
                rewrite_prompt = f"The following issues were found in the draft:\n{violation_summary}\n\nPlease rewrite the problematic passages while preserving the overall story flow."
                rewrite_request = InferenceRequest(
                    model=inference_request.model,
                    temperature=0.1,
                    max_tokens=inference_request.max_tokens,
                    messages=[
                        InferenceMessage(role="system", content="You are a narrative editor. Rewrite only the flagged passages to fix consistency issues while preserving story flow."),
                        InferenceMessage(role="user", content=f"Original draft:\n{output_text}\n\n{rewrite_prompt}"),
                    ],
                )
                rewrite_response = self._inferencer.generate_text(rewrite_request)
                rewritten = rewrite_response.content.strip()
                if rewritten:
                    output_text = rewritten + "\n"
                    logger.info("Rewrite applied")
            except Exception as exc:
                logger.warning("Rewrite failed, keeping original draft: %s", exc)

        # Entity intake: detect and persist new characters in the draft
        if self._entity_intake and project_id:
            try:
                known = {c.display_name: c.character_id for c in _chars if c.display_name}
                new_entities = self._entity_intake.intake_new_entities(output_text, known)
                for entity in new_entities:
                    entity_id = f"auto-{entity.name.lower().replace(' ', '-')}"
                    _repo.upsert_character_profile(
                        project_id=project_id,
                        character_id=entity_id,
                        display_name=entity.name,
                        role_in_story="supporting",
                        archetype=entity.inferred_archetype or "unknown",
                        external_goal=entity.inferred_goal or "",
                        internal_need="",
                        core_fear="",
                        writer_notes=f"Auto-detected from draft: {entity.raw_evidence[:200]}",
                    )
                if new_entities:
                    logger.info("Detected and persisted %d new entities in draft", len(new_entities))
            except Exception as exc:
                logger.warning("Entity intake failed: %s", exc)

        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if sequence_output is not None:
            input_artifact_refs.append("sequence")
            source_content_hashes.append(stable_hash_payload(sequence_output))
            step_input_payload["sequence"] = sequence_output
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="drafter",
            detail="Drafter phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=["chapter_1"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="chapter_1",
            artifact_kind="markdown",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name="chapter_1",
        )

    def _read_optional_artifact(self, project_id: str, artifact_name: str) -> str | None:
        try:
            content = self._project_service.read_artifact(project_id, artifact_name).content
        except FileNotFoundError:
            return None
        if not content.strip():
            return None
        return content

    def _resolve_runtime_artifact_inputs(
        self,
        *,
        job_id: UUID,
        attempt: dict[str, Any],
        project_id: str,
        step_name: str,
    ) -> dict[str, str]:
        attempt_number = int(attempt["attempt_number"])
        existing = self._step_records.list_runtime_artifact_selections(
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=attempt_number,
            step_name=step_name,
        )
        if existing:
            return {str(row["artifact_role"]): str(row["selected_content"]) for row in existing}

        resolved: dict[str, str] = {}
        for artifact_role, project_artifact_name in _upstream_artifact_sources(step_name):
            content = self._read_optional_artifact(project_id, project_artifact_name)
            if content is None:
                continue
            lineage = self._step_records.get_latest_canonical_artifact(
                project_id=project_id,
                artifact_role=artifact_role,
            )
            self._step_records.create_runtime_artifact_selection(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=attempt_number,
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                selected_artifact_lineage_id=(
                    int(lineage["artifact_lineage_id"])
                    if lineage is not None and lineage.get("artifact_lineage_id") is not None
                    else None
                ),
                selected_path=str(lineage["path"]) if lineage is not None and lineage.get("path") is not None else None,
                selected_content=content,
            )
            resolved[artifact_role] = content
        return resolved

    def _run_compiler_phase(
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
            raise ValueError("P-400 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="compiler",
        )
        architect_output = selected_inputs.get("architect_output")
        sequence_output = selected_inputs.get("sequence")
        chapter_output = selected_inputs.get("chapter_1")
        inference_request = build_p400_compiler_request(
            manifest=project.manifest,
            payload=payload,
            architect_output=architect_output,
            sequence_output=sequence_output,
            chapter_output=chapter_output,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="compiler",
            detail="Compiler inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="compiler",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            input_artifact_refs = ["manifest"]
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
                input_artifact_refs.append("architect_output")
            if sequence_output is not None:
                step_input_payload["sequence"] = sequence_output
                input_artifact_refs.append("sequence")
            if chapter_output is not None:
                step_input_payload["chapter_1"] = chapter_output
                input_artifact_refs.append("chapter_1")
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="compiler",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=input_artifact_refs,
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
        output_path = story_bible_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        if sequence_output is not None:
            input_artifact_refs.append("sequence")
            source_content_hashes.append(stable_hash_payload(sequence_output))
            step_input_payload["sequence"] = sequence_output
        if chapter_output is not None:
            input_artifact_refs.append("chapter_1")
            source_content_hashes.append(stable_hash_payload(chapter_output))
            step_input_payload["chapter_1"] = chapter_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="compiler",
            detail="Compiler phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=["story_bible"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="story_bible",
            artifact_kind="json",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name="story_bible",
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
