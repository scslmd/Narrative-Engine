from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStatusResponse


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _RunRecord:
    run_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    current_role: str | None = None
    detail: str | None = None
    heartbeat_at: datetime | None = None
    report_path: str | None = None
    results: list[RoleCheckResult] = field(default_factory=list)


class RoleModelCheckManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._runs: dict[UUID, _RunRecord] = {}

    def create_run(self) -> RoleModelCheckStatusResponse:
        now = _utcnow()
        record = _RunRecord(run_id=uuid4(), status='PENDING', created_at=now, updated_at=now)
        with self._lock:
            self._runs[record.run_id] = record
        return self.get_status(record.run_id)

    def update_run(self, run_id: UUID, *, status: str | None = None, current_role: str | None = None, detail: str | None = None, report_path: str | None = None) -> RoleModelCheckStatusResponse:
        with self._lock:
            record = self._runs[run_id]
            if status is not None:
                record.status = status
            if current_role is not None:
                record.current_role = current_role
            if detail is not None:
                record.detail = detail
            if report_path is not None:
                record.report_path = report_path
            record.updated_at = _utcnow()
            record.heartbeat_at = record.updated_at
        return self.get_status(run_id)

    def add_result(self, run_id: UUID, result: RoleCheckResult) -> RoleModelCheckStatusResponse:
        with self._lock:
            record = self._runs[run_id]
            record.results.append(result)
            record.updated_at = _utcnow()
            record.heartbeat_at = record.updated_at
        return self.get_status(run_id)

    def get_status(self, run_id: UUID) -> RoleModelCheckStatusResponse:
        with self._lock:
            record = self._runs[run_id]
            return RoleModelCheckStatusResponse(
                run_id=record.run_id,
                status=record.status,
                created_at=record.created_at,
                updated_at=record.updated_at,
                current_role=record.current_role,
                detail=record.detail,
                heartbeat_at=record.heartbeat_at,
                report_path=record.report_path,
                results=list(record.results),
            )