from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from ..schemas.jobs import JobCreateRequest, JobLogEntry, JobLogsResponse, JobStatusResponse
from ..schemas.enums import JobStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _JobRecord:
    id: UUID
    phase: str
    status: str
    created_at: datetime
    updated_at: datetime
    current_phase: str | None = None
    current_step: str | None = None
    detail: str | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    heartbeat_at: datetime | None = None
    error: str | None = None
    logs: list[JobLogEntry] = field(default_factory=list)


class JobManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[UUID, _JobRecord] = {}

    def create_job(self, request: JobCreateRequest) -> JobStatusResponse:
        now = _utcnow()
        phase = str(request.phase)
        record = _JobRecord(
            id=uuid4(),
            phase=phase,
            status=JobStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[record.id] = record
        return self.get_status(record.id)

    def update_job(self, job_id: UUID, *, status: str | None = None, current_phase: str | None = None, current_step: str | None = None, detail: str | None = None, progress_current: int | None = None, progress_total: int | None = None, error: str | None = None) -> JobStatusResponse:
        with self._lock:
            record = self._jobs[job_id]
            if status is not None:
                record.status = status
            if current_phase is not None:
                record.current_phase = current_phase
            if current_step is not None:
                record.current_step = current_step
            if detail is not None:
                record.detail = detail
            if progress_current is not None:
                record.progress_current = progress_current
            if progress_total is not None:
                record.progress_total = progress_total
            if error is not None:
                record.error = error
            record.updated_at = _utcnow()
            record.heartbeat_at = record.updated_at
        return self.get_status(job_id)

    def log(self, job_id: UUID, level: str, message: str) -> None:
        with self._lock:
            record = self._jobs[job_id]
            entry = JobLogEntry(timestamp=_utcnow(), level=level, message=message)
            record.logs.append(entry)
            record.updated_at = entry.timestamp
            record.heartbeat_at = entry.timestamp

    def get_status(self, job_id: UUID) -> JobStatusResponse:
        with self._lock:
            record = self._jobs[job_id]
            return JobStatusResponse(
                id=record.id,
                phase=record.phase,
                status=record.status,
                created_at=record.created_at,
                updated_at=record.updated_at,
                current_phase=record.current_phase,
                current_step=record.current_step,
                detail=record.detail,
                progress_current=record.progress_current,
                progress_total=record.progress_total,
                heartbeat_at=record.heartbeat_at,
                error=record.error,
            )

    def get_logs(self, job_id: UUID) -> JobLogsResponse:
        with self._lock:
            record = self._jobs[job_id]
            return JobLogsResponse(id=record.id, entries=list(record.logs))