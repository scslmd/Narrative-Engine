from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..persistence import CheckerRunRepository
from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStatusResponse
from ..settings import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RoleModelCheckManager:
    def __init__(self, db_path: Path | None = None) -> None:
        self._runs = CheckerRunRepository(db_path or settings.operations_db_path)

    def create_run(self) -> RoleModelCheckStatusResponse:
        now = _utcnow()
        run_id = uuid4()
        self._runs.create_run(run_id=run_id, status="PENDING", request_payload={}, created_at=now)
        return self.get_status(run_id)

    def update_run(
        self,
        run_id: UUID,
        *,
        status: str | None = None,
        current_role: str | None = None,
        detail: str | None = None,
        report_path: str | None = None,
    ) -> RoleModelCheckStatusResponse:
        updated_at = _utcnow()
        self._runs.update_run(
            run_id,
            status=status,
            current_role=current_role,
            detail=detail,
            report_path=report_path,
            heartbeat_at=updated_at,
            updated_at=updated_at,
        )
        return self.get_status(run_id)

    def add_result(self, run_id: UUID, result: RoleCheckResult) -> RoleModelCheckStatusResponse:
        timestamp = _utcnow()
        self._runs.add_result(run_id, result)
        self._runs.update_run(run_id, heartbeat_at=timestamp, updated_at=timestamp)
        return self.get_status(run_id)

    def get_status(self, run_id: UUID) -> RoleModelCheckStatusResponse:
        return self._runs.get_run(run_id)
