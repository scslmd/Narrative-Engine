from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any
from uuid import UUID

from ...inference import InferenceBackend, StubInferenceBackend
from ...persistence.story_development import StoryDevelopmentRepository
from ...persistence.steps import stable_hash_payload
from ...settings import settings
from ..generation_gates import GenerationGateService
from ..job_manager import JobManager
from ..projects import ProjectService
from ..role_model_check_manager import RoleModelCheckManager
from ..role_model_checker import RoleModelCheckerService
from ..step_records import StepRecordService
from .helpers import (
    phase_step_name as _phase_step_name,
    require_supported_job_phase as _require_supported_job_phase,
    utcnow as _utcnow,
)

class _WorkerLifecycleMixin:

    def __init__(
        self,
        *,
        job_manager: JobManager,
        role_check_manager: RoleModelCheckManager,
        role_check_service: RoleModelCheckerService,
        inferencer: InferenceBackend | None = None,
        project_service: ProjectService | None = None,
        step_record_service: StepRecordService | None = None,
        story_repository: StoryDevelopmentRepository | None = None,
        scene_context_service: SceneContextService | None = None,
        consistency_critic_service: ConsistencyCriticService | None = None,
        entity_intake_service: EntityIntakeService | None = None,
        chapter_summarizer_service: ChapterSummarizerService | None = None,
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
        self._chapter_summarizer = chapter_summarizer_service
        self._story_repository = story_repository or StoryDevelopmentRepository(settings.operations_db_path)
        self._generation_gates = GenerationGateService()
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
            if phase == "G-200":
                self._run_generation_planner_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "G-300":
                self._run_generation_drafter_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "G-350":
                self._run_generation_gate_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "G-400":
                self._run_generation_compiler_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "M-500":
                self._run_manuscript_assist_phase(
                    job_id=job_id,
                    started_at=started_at,
                    current_phase=phase,
                    attempt=attempt,
                    request_payload=request_payload,
                    project_id=project_id,
                )
                return
            if phase == "M-550":
                self._run_manuscript_assist_repair_phase(
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