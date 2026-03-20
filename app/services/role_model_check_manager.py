from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..persistence import CheckerRunRepository
from ..schemas.role_model_checker import RoleModelCheckStartRequest
from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStatusResponse
from ..settings import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_ALLOWED_CHECKER_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"RUNNING", "FAILED"},
    "RUNNING": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
}


class RoleModelCheckManager:
    def __init__(self, db_path: Path | None = None) -> None:
        self._runs = CheckerRunRepository(db_path or settings.operations_db_path)

    def create_run(self, request: RoleModelCheckStartRequest | dict | None = None) -> RoleModelCheckStatusResponse:
        now = _utcnow()
        run_id = uuid4()
        if isinstance(request, RoleModelCheckStartRequest):
            request_payload = request.model_dump(mode="json")
        else:
            request_payload = request or {}
        self._runs.create_run(run_id=run_id, status="PENDING", request_payload=request_payload, created_at=now)
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
        current = self.get_status(run_id)
        if status is not None:
            allowed = _ALLOWED_CHECKER_TRANSITIONS.get(str(current.status), set())
            if status != str(current.status) and status not in allowed:
                raise ValueError(
                    f"Illegal checker run state transition for {run_id}: {current.status} -> {status}"
                )
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
        current = self.get_status(run_id)
        if str(current.status) != "RUNNING":
            raise ValueError(
                f"Cannot record checker result for {run_id} while run is {current.status}"
            )
        timestamp = _utcnow()
        self._runs.add_result(run_id, result)
        self._runs.update_run(run_id, heartbeat_at=timestamp, updated_at=timestamp)
        return self.get_status(run_id)

    def get_status(self, run_id: UUID) -> RoleModelCheckStatusResponse:
        return self._runs.get_run(run_id)

    def list_events(self, run_id: UUID) -> list[dict[str, object]]:
        return self._runs.list_events(run_id)
