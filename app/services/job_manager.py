from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..persistence import JobLogRepository, JobRepository
from ..schemas.enums import JobStatus
from ..schemas.jobs import JobCreateRequest, JobLogEntry, JobLogsResponse, JobStatusResponse
from ..settings import settings


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

    def create_job(self, request: JobCreateRequest) -> JobStatusResponse:
        now = _utcnow()
        job_id = uuid4()
        phase = str(request.phase)
        project_id = str(request.payload.get("project_id", "")).strip() or None
        self._jobs.create_job(
            job_id=job_id,
            phase=phase,
            status=JobStatus.PENDING.value,
            payload=dict(request.payload),
            project_id=project_id,
            created_at=now,
        )
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
