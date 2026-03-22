from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from ..request_identity import checker_request_scope, request_hash
from ..persistence import CheckerRunRepository
from ..schemas.inspect import (
    RoleModelCheckAttemptHistoryResponse,
    RoleModelCheckLineageResponse,
    RoleModelCheckStepsResponse,
)
from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStartRequest
from ..settings import settings
from .protocol import CheckerRunAcceptance, IdempotencyConflictError, RetryNotAllowedError
from .step_records import StepRecordService


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
        operations_db_path = db_path or settings.operations_db_path
        self._runs = CheckerRunRepository(operations_db_path)
        self._step_records = StepRecordService(operations_db_path)

    def accept_run(
        self,
        request: RoleModelCheckStartRequest | dict | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> CheckerRunAcceptance:
        now = _utcnow()
        if isinstance(request, RoleModelCheckStartRequest):
            request_payload = request.model_dump(mode="json")
        else:
            request_payload = request or {}
        request_scope = checker_request_scope(
            roles=[str(role) for role in request_payload.get("roles", [])],
            critic_profile=str(request_payload.get("critic_profile", "minimal_context")),
        )
        request_payload_hash = request_hash(request_payload)
        if idempotency_key:
            existing = self._runs.find_by_idempotency_key(
                request_scope=request_scope,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                if existing["request_hash"] != request_payload_hash:
                    raise IdempotencyConflictError(
                        f"Idempotency key {idempotency_key!r} is already bound to a different checker request."
                    )
                return CheckerRunAcceptance(
                    status=self.get_status(UUID(str(existing["run_id"]))),
                    created_new=False,
                )

        run_id = uuid4()
        self._runs.create_run(
            run_id=run_id,
            status="PENDING",
            request_payload=request_payload,
            request_hash=request_payload_hash,
            request_scope=request_scope,
            idempotency_key=idempotency_key,
            created_at=now,
        )
        return CheckerRunAcceptance(status=self.get_status(run_id), created_new=True)

    def create_run(
        self,
        request: RoleModelCheckStartRequest | dict | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> RoleModelCheckStatusResponse:
        return self.accept_run(request, idempotency_key=idempotency_key).status

    def retry_run(self, run_id: UUID, *, retry_reason: str = "operator_retry") -> RoleModelCheckStatusResponse:
        current = self.get_status(run_id)
        if str(current.status) != "FAILED":
            raise RetryNotAllowedError(
                f"Checker run {run_id} cannot be retried while status is {current.status}."
            )
        updated_at = _utcnow()
        self._runs.retry_run(run_id, retry_reason=retry_reason, updated_at=updated_at)
        return self.get_status(run_id)

    def update_run(
        self,
        run_id: UUID,
        *,
        status: str | None = None,
        current_role: str | None = None,
        detail: str | None = None,
        report_path: str | None = None,
        finish_reason: str | None = None,
        failure_stage: str | None = None,
        retryable: bool | None = None,
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
            finish_reason=finish_reason,
            failure_stage=failure_stage,
            retryable=retryable,
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

    def claim_next_pending(self, *, worker_id: str, lease_seconds: int = 30) -> UUID | None:
        now = _utcnow()
        lease_expires_at = now + timedelta(seconds=lease_seconds)
        return self._runs.claim_next_pending(
            worker_id=worker_id,
            now=now,
            lease_expires_at=lease_expires_at,
        )

    def get_request_payload(self, run_id: UUID) -> dict[str, object]:
        return self._runs.get_request_payload(run_id)

    def get_attempt(self, run_id: UUID) -> dict[str, object]:
        return self._runs.get_attempt(run_id)

    def list_step_records(
        self,
        run_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self._step_records.list_step_records(
            run_id=run_id,
            run_kind="role_model_check",
            attempt_number=attempt_number,
            limit=limit,
            offset=offset,
        )

    def list_artifact_lineage(
        self,
        run_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        return self._step_records.list_artifact_lineage(
            run_id=run_id,
            run_kind="role_model_check",
            attempt_number=attempt_number,
            limit=limit,
            offset=offset,
        )

    def get_steps_projection(
        self,
        run_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> RoleModelCheckStepsResponse:
        self.get_status(run_id)
        meta = {"ordered_by": "step_index_asc"}
        if attempt_number is not None:
            meta["attempt_number"] = attempt_number
        if limit is not None:
            meta["limit"] = limit
            meta["offset"] = offset
        items = self.list_step_records(run_id, attempt_number=attempt_number, limit=limit, offset=offset)
        if limit is not None:
            meta["returned_count"] = len(items)
        return RoleModelCheckStepsResponse(run_id=run_id, items=items, meta=meta)

    def get_lineage_projection(
        self,
        run_id: UUID,
        *,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> RoleModelCheckLineageResponse:
        self.get_status(run_id)
        meta = {"ordered_by": "artifact_lineage_id_asc"}
        if attempt_number is not None:
            meta["attempt_number"] = attempt_number
        if limit is not None:
            meta["limit"] = limit
            meta["offset"] = offset
        items = self.list_artifact_lineage(run_id, attempt_number=attempt_number, limit=limit, offset=offset)
        if limit is not None:
            meta["returned_count"] = len(items)
        return RoleModelCheckLineageResponse(run_id=run_id, items=items, meta=meta)

    def get_attempt_history_projection(self, run_id: UUID) -> RoleModelCheckAttemptHistoryResponse:
        self.get_status(run_id)
        meta = {"ordered_by": "attempt_number_asc"}
        items = self._runs.list_attempts(run_id)
        formatted_items = []
        for item in items:
            formatted_items.append({
                "attempt_number": item.get("attempt_number", 0),
                "status": item.get("status", ""),
                "executor_name": item.get("executor_name"),
                "executor_instance_id": item.get("executor_instance_id"),
                "queue_delay_ms": item.get("queue_delay_ms"),
                "lease_owner": item.get("lease_owner"),
                "lease_expires_at": item.get("lease_expires_at"),
                "claimed_at": item.get("claimed_at"),
                "started_at": item.get("started_at"),
                "finished_at": item.get("finished_at"),
                "last_heartbeat_at": item.get("last_heartbeat_at"),
                "finish_reason": item.get("finish_reason"),
                "failure_stage": item.get("failure_stage"),
                "retryable": bool(item.get("retryable", 0)) if item.get("retryable") is not None else None,
                "retry_reason": item.get("retry_reason"),
                "error_code": item.get("error_code"),
                "error_category": item.get("error_category"),
            })
        return RoleModelCheckAttemptHistoryResponse(run_id=run_id, items=formatted_items, meta=meta)