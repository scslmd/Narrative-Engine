from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..request_identity import job_request_scope, request_hash
from ..persistence import JobLogRepository, JobRepository
from ..schemas.enums import JobStatus
from ..schemas.inspect import JobLineageResponse, JobStepsResponse
from ..schemas.jobs import JobCreateRequest, JobLogEntry, JobLogsResponse, JobStatusResponse
from ..settings import settings
from .protocol import IdempotencyConflictError, JobAcceptance, RetryNotAllowedError
from .step_records import StepRecordService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_ALLOWED_JOB_TRANSITIONS: dict[str, set[str]] = {
    JobStatus.PENDING.value: {JobStatus.PROCESSING.value, JobStatus.FAILED.value},
    JobStatus.PROCESSING.value: {JobStatus.COMPLETED.value, JobStatus.FAILED.value},
    JobStatus.COMPLETED.value: set(),
    JobStatus.FAILED.value: set(),
}


class JobManager:
    def __init__(self, db_path: Path | None = None) -> None:
        operations_db_path = db_path or settings.operations_db_path
        self._jobs = JobRepository(operations_db_path)
        self._logs = JobLogRepository(operations_db_path)
        self._step_records = StepRecordService(operations_db_path)

    def accept_job(self, request: JobCreateRequest, *, idempotency_key: str | None = None) -> JobAcceptance:
        now = _utcnow()
        request_payload = request.model_dump(mode="json")
        phase = str(request.phase)
        project_id = str(request.payload.get("project_id", "")).strip() or None
        request_scope = job_request_scope(phase=phase, project_id=project_id)
        request_payload_hash = request_hash(request_payload)
        if idempotency_key:
            existing = self._jobs.find_by_idempotency_key(
                request_scope=request_scope,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                if existing["request_hash"] != request_payload_hash:
                    raise IdempotencyConflictError(
                        f"Idempotency key {idempotency_key!r} is already bound to a different job request."
                    )
                return JobAcceptance(
                    status=self.get_status(UUID(str(existing["job_id"]))),
                    created_new=False,
                )

        job_id = uuid4()
        self._jobs.create_job(
            job_id=job_id,
            phase=phase,
            status=JobStatus.PENDING.value,
            payload=dict(request.payload),
            request_payload=request_payload,
            request_hash=request_payload_hash,
            request_scope=request_scope,
            idempotency_key=idempotency_key,
            project_id=project_id,
            created_at=now,
        )
        return JobAcceptance(status=self.get_status(job_id), created_new=True)

    def create_job(self, request: JobCreateRequest, *, idempotency_key: str | None = None) -> JobStatusResponse:
        return self.accept_job(request, idempotency_key=idempotency_key).status

    def retry_job(self, job_id: UUID, *, retry_reason: str = "operator_retry") -> JobStatusResponse:
        current = self.get_status(job_id)
        if str(current.status) != JobStatus.FAILED.value:
            raise RetryNotAllowedError(
                f"Job {job_id} cannot be retried while status is {current.status}."
            )
        updated_at = _utcnow()
        self._jobs.retry_job(job_id, retry_reason=retry_reason, updated_at=updated_at)
        return self.get_status(job_id)

    def update_job(
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        current_phase: str | None = None,
        current_step: str | None = None,
        detail: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        error: str | None = None,
        error_category: str | None = None,
        finish_reason: str | None = None,
        failure_stage: str | None = None,
        retryable: bool | None = None,
    ) -> JobStatusResponse:
        current = self.get_status(job_id)
        if status is not None:
            allowed = _ALLOWED_JOB_TRANSITIONS.get(str(current.status), set())
            if status != str(current.status) and status not in allowed:
                raise ValueError(
                    f"Illegal job state transition for {job_id}: {current.status} -> {status}"
                )
        updated_at = _utcnow()
        self._jobs.update_job(
            job_id,
            status=status,
            current_phase=current_phase,
            current_step=current_step,
            detail=detail,
            progress_current=progress_current,
            progress_total=progress_total,
            heartbeat_at=updated_at,
            error=error,
            error_category=error_category,
            finish_reason=finish_reason,
            failure_stage=failure_stage,
            retryable=retryable,
            updated_at=updated_at,
        )
        return self.get_status(job_id)

    def log(self, job_id: UUID, level: str, message: str) -> None:
        entry = JobLogEntry(timestamp=_utcnow(), level=level, message=message)
        self._logs.append(job_id, entry)
        self._jobs.update_job(job_id, heartbeat_at=entry.timestamp, updated_at=entry.timestamp)

    def get_status(self, job_id: UUID) -> JobStatusResponse:
        return self._jobs.get_job(job_id)

    def get_logs(self, job_id: UUID) -> JobLogsResponse:
        return self._logs.list_for_job(job_id)

    def list_events(self, job_id: UUID) -> list[dict[str, object]]:
        return self._jobs.list_events(job_id)

    def claim_next_pending(self, *, worker_id: str, lease_seconds: int = 30) -> UUID | None:
        now = _utcnow()
        lease_expires_at = now + timedelta(seconds=lease_seconds)
        return self._jobs.claim_next_pending(
            worker_id=worker_id,
            now=now,
            lease_expires_at=lease_expires_at,
        )

    def get_request_payload(self, job_id: UUID) -> dict[str, object]:
        return self._jobs.get_request_payload(job_id)

    def get_attempt(self, job_id: UUID) -> dict[str, object]:
        return self._jobs.get_attempt(job_id)

    def list_step_records(
        self,
        job_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self._step_records.list_step_records(
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=attempt_number,
            limit=limit,
            offset=offset,
        )

    def list_artifact_lineage(
        self,
        job_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self._step_records.list_artifact_lineage(
            run_id=job_id,
            run_kind="pipeline_job",
            attempt_number=attempt_number,
            limit=limit,
            offset=offset,
        )

    def get_steps_projection(
        self,
        job_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> JobStepsResponse:
        self.get_status(job_id)
        meta = {"ordered_by": "step_index_asc"}
        if attempt_number is not None:
            meta["attempt_number"] = attempt_number
        if limit is not None:
            meta["limit"] = limit
            meta["offset"] = offset
        items = self.list_step_records(job_id, attempt_number=attempt_number, limit=limit, offset=offset)
        if limit is not None:
            meta["returned_count"] = len(items)
        return JobStepsResponse(job_id=job_id, items=items, meta=meta)

    def get_lineage_projection(
        self,
        job_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> JobLineageResponse:
        self.get_status(job_id)
        meta = {"ordered_by": "artifact_lineage_id_asc"}
        if attempt_number is not None:
            meta["attempt_number"] = attempt_number
        if limit is not None:
            meta["limit"] = limit
            meta["offset"] = offset
        items = self.list_artifact_lineage(job_id, attempt_number=attempt_number, limit=limit, offset=offset)
        if limit is not None:
            meta["returned_count"] = len(items)
        return JobLineageResponse(job_id=job_id, items=items, meta=meta)
