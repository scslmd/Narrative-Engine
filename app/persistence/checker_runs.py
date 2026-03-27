from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from ..request_identity import canonical_request_json
from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStatusResponse
from .sqlite import connect, ensure_operations_db

LOCAL_EXECUTOR_NAME = "local_executor"


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class CheckerRunRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def create_run(
        self,
        *,
        run_id: UUID,
        status: str,
        request_payload: dict,
        request_hash: str,
        request_scope: str,
        idempotency_key: str | None,
        created_at: datetime,
        project_id: str | None = None,
    ) -> None:
        request_json = canonical_request_json(request_payload)
        logical_run_id = str(run_id)
        attempt_number = 1
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO checker_runs (
                    run_id, logical_run_id, attempt_number, project_id, status, request_json,
                    idempotency_key, request_hash, request_scope, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    logical_run_id,
                    attempt_number,
                    project_id,
                    status,
                    request_json,
                    idempotency_key,
                    request_hash,
                    request_scope,
                    created_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO checker_run_attempts (
                    run_id, logical_run_id, attempt_number, status, executor_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    logical_run_id,
                    attempt_number,
                    status,
                    None,
                    created_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO checker_run_events (
                    run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    logical_run_id,
                    attempt_number,
                    "RUN_ACCEPTED",
                    None,
                    status,
                    created_at.isoformat(),
                    request_json,
                ),
            )
            connection.commit()

    def update_run(
        self,
        run_id: UUID,
        *,
        status: str | None = None,
        current_role: str | None = None,
        detail: str | None = None,
        report_path: str | None = None,
        heartbeat_at: datetime | None = None,
        finish_reason: str | None = None,
        failure_stage: str | None = None,
        retryable: bool | None = None,
        updated_at: datetime,
    ) -> None:
        with connect(self.db_path) as connection:
            existing = connection.execute(
                "SELECT status, logical_run_id, attempt_number FROM checker_runs WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
            if existing is None:
                raise KeyError(str(run_id))

        assignments: list[str] = []
        values: list[object] = []
        attempt_assignments: list[str] = []
        attempt_values: list[object] = []
        for column, value in (
            ("status", status),
            ("current_role", current_role),
            ("detail", detail),
            ("report_path", report_path),
        ):
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if heartbeat_at is not None:
            assignments.append("heartbeat_at = ?")
            values.append(heartbeat_at.isoformat())
            attempt_assignments.append("last_heartbeat_at = ?")
            attempt_values.append(heartbeat_at.isoformat())
        if status in {"COMPLETED", "FAILED"}:
            assignments.append("lease_owner = NULL")
            assignments.append("lease_expires_at = NULL")
            attempt_assignments.append("lease_owner = NULL")
            attempt_assignments.append("lease_expires_at = NULL")
            attempt_assignments.append("finished_at = ?")
            attempt_values.append(updated_at.isoformat())
        elif status == "RUNNING":
            attempt_assignments.append("started_at = COALESCE(started_at, ?)")
            attempt_values.append(updated_at.isoformat())
        if status is not None:
            attempt_assignments.append("status = ?")
            attempt_values.append(status)
        if finish_reason is not None:
            attempt_assignments.append("finish_reason = ?")
            attempt_values.append(finish_reason)
        if failure_stage is not None:
            attempt_assignments.append("failure_stage = ?")
            attempt_values.append(failure_stage)
        if retryable is not None:
            attempt_assignments.append("retryable = ?")
            attempt_values.append(1 if retryable else 0)
        assignments.append("updated_at = ?")
        values.append(updated_at.isoformat())
        values.append(str(run_id))
        if not attempt_assignments:
            attempt_assignments.append("updated_at = ?")
            attempt_values.append(updated_at.isoformat())
        event_payload = {
            "current_role": current_role,
            "detail": detail,
            "report_path": report_path,
            "finish_reason": finish_reason,
            "failure_stage": failure_stage,
            "retryable": retryable,
        }
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE checker_runs SET {', '.join(assignments)} WHERE run_id = ?",
                values,
            )
            attempt_update_values = [*attempt_values, updated_at.isoformat(), str(run_id), existing["attempt_number"]]
            connection.execute(
                f"UPDATE checker_run_attempts SET {', '.join(attempt_assignments)}, updated_at = ? WHERE run_id = ? AND attempt_number = ?",
                attempt_update_values,
            )
            if status is not None:
                connection.execute(
                    """
                    INSERT INTO checker_run_events (
                        run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(run_id),
                        existing["logical_run_id"],
                        existing["attempt_number"],
                        "RUN_STATE_CHANGED",
                        existing["status"],
                        status,
                        updated_at.isoformat(),
                        json.dumps(event_payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
            elif any(value is not None for value in (current_role, detail, report_path, heartbeat_at)):
                connection.execute(
                    """
                    INSERT INTO checker_run_events (
                        run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(run_id),
                        existing["logical_run_id"],
                        existing["attempt_number"],
                        "RUN_PROGRESS_UPDATED",
                        existing["status"],
                        existing["status"],
                        updated_at.isoformat(),
                        json.dumps(event_payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(str(run_id))

    def add_result(self, run_id: UUID, result: RoleCheckResult) -> None:
        with connect(self.db_path) as connection:
            existing = connection.execute(
                "SELECT logical_run_id, attempt_number FROM checker_runs WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
            if existing is None:
                raise KeyError(str(run_id))
            connection.execute(
                """
                INSERT INTO checker_results (
                    run_id, role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    result.role,
                    1 if result.passed else 0,
                    result.duration_seconds,
                    json.dumps(result.findings, ensure_ascii=True),
                    json.dumps(result.warnings, ensure_ascii=True),
                    result.preview,
                    json.dumps(result.metadata, ensure_ascii=True, sort_keys=True),
                ),
            )
            connection.execute(
                """
                INSERT INTO checker_run_events (
                    run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    existing["logical_run_id"],
                    existing["attempt_number"],
                    "STEP_RESULT_RECORDED",
                    None,
                    None,
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(result.model_dump(mode="json"), ensure_ascii=True, sort_keys=True),
                ),
            )
            connection.commit()

    def get_run(self, run_id: UUID) -> RoleModelCheckStatusResponse:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM checker_runs WHERE run_id = ?", (str(run_id),)).fetchone()
            if row is None:
                raise KeyError(str(run_id))
            result_rows = connection.execute(
                """
                SELECT role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
                FROM checker_results
                WHERE run_id = ?
                ORDER BY result_id ASC
                """,
                (str(run_id),),
            ).fetchall()
        return RoleModelCheckStatusResponse(
            run_id=UUID(row["run_id"]),
            status=row["status"],
            attempt_number=int(row["attempt_number"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            current_role=row["current_role"],
            detail=row["detail"],
            heartbeat_at=_parse_datetime(row["heartbeat_at"]),
            report_path=row["report_path"],
            results=[
                RoleCheckResult(
                    role=result_row["role"],
                    passed=bool(result_row["passed"]),
                    duration_seconds=float(result_row["duration_seconds"]),
                    findings=list(json.loads(result_row["findings_json"])),
                    warnings=list(json.loads(result_row["warnings_json"])),
                    preview=result_row["preview"],
                    metadata=dict(json.loads(result_row["metadata_json"])),
                )
                for result_row in result_rows
            ],
        )

    def get_attempt(self, run_id: UUID) -> dict[str, object]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category
                FROM checker_run_attempts
                WHERE run_id = ?
                ORDER BY attempt_number DESC
                LIMIT 1
                """,
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise KeyError(str(run_id))
        return dict(row)

    def retry_run(self, run_id: UUID, *, retry_reason: str, updated_at: datetime) -> None:
        with connect(self.db_path) as connection:
            existing = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status
                FROM checker_runs
                WHERE run_id = ?
                """,
                (str(run_id),),
            ).fetchone()
            if existing is None:
                raise KeyError(str(run_id))
            next_attempt_number = int(existing["attempt_number"]) + 1
            connection.execute(
                """
                UPDATE checker_runs
                SET attempt_number = ?, status = ?, current_role = NULL, detail = ?, heartbeat_at = NULL,
                    lease_owner = NULL, lease_expires_at = NULL, claimed_at = NULL, report_path = NULL, updated_at = ?
                WHERE run_id = ?
                """,
                (
                    next_attempt_number,
                    "PENDING",
                    f"Retry queued: {retry_reason}",
                    updated_at.isoformat(),
                    str(run_id),
                ),
            )
            connection.execute(
                """
                INSERT INTO checker_run_attempts (
                    run_id, logical_run_id, attempt_number, status, executor_name, retry_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    existing["logical_run_id"],
                    next_attempt_number,
                    "PENDING",
                    None,
                    retry_reason,
                    updated_at.isoformat(),
                    updated_at.isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO checker_run_events (
                    run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    existing["logical_run_id"],
                    next_attempt_number,
                    "RUN_REQUEUED",
                    existing["status"],
                    "PENDING",
                    updated_at.isoformat(),
                    json.dumps(
                        {
                            "previous_attempt_number": existing["attempt_number"],
                            "retry_reason": retry_reason,
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                ),
            )
            connection.commit()

    def get_request_payload(self, run_id: UUID) -> dict[str, object]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT request_json FROM checker_runs WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise KeyError(str(run_id))
        return dict(json.loads(row["request_json"]))

    def find_by_idempotency_key(self, *, request_scope: str, idempotency_key: str) -> dict[str, object] | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT run_id, request_hash, status
                FROM checker_runs
                WHERE request_scope = ? AND idempotency_key = ?
                """,
                (request_scope, idempotency_key),
            ).fetchone()
        return dict(row) if row is not None else None

    def claim_next_pending(self, *, worker_id: str, now: datetime, lease_expires_at: datetime) -> UUID | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT run_id, logical_run_id, attempt_number, status, lease_owner, lease_expires_at, created_at
                FROM checker_runs
                WHERE status = 'PENDING'
                  AND (lease_expires_at IS NULL OR lease_expires_at <= ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (now.isoformat(),),
            ).fetchone()
            if row is None:
                return None
            run_id = row["run_id"]
            previous_lease_owner = row["lease_owner"]
            previous_lease_expires_at = row["lease_expires_at"]
            if previous_lease_owner and previous_lease_expires_at is not None:
                expired_payload = {
                    "attempt_number": row["attempt_number"],
                    "expired_lease_owner": previous_lease_owner,
                    "expired_lease_expires_at": previous_lease_expires_at,
                    "retry_reason": "stale_lease_reclaimed",
                }
                connection.execute(
                    """
                    INSERT INTO checker_run_events (
                        run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        row["logical_run_id"],
                        row["attempt_number"],
                        "LEASE_EXPIRED",
                        row["status"],
                        row["status"],
                        now.isoformat(),
                        json.dumps(expired_payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO checker_run_events (
                        run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        row["logical_run_id"],
                        row["attempt_number"],
                        "RUN_REQUEUED",
                        row["status"],
                        row["status"],
                        now.isoformat(),
                        json.dumps(expired_payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
            cursor = connection.execute(
                """
                UPDATE checker_runs
                SET lease_owner = ?, lease_expires_at = ?, claimed_at = ?, updated_at = ?
                WHERE run_id = ?
                  AND status = 'PENDING'
                  AND (lease_expires_at IS NULL OR lease_expires_at <= ?)
                """,
                (
                    worker_id,
                    lease_expires_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    run_id,
                    now.isoformat(),
                ),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return None
            queue_delay_ms = int((now - datetime.fromisoformat(row["created_at"])).total_seconds() * 1000)
            connection.execute(
                """
                UPDATE checker_run_attempts
                SET executor_name = ?, executor_instance_id = ?, queue_delay_ms = ?, lease_owner = ?, lease_expires_at = ?, claimed_at = ?, updated_at = ?
                WHERE run_id = ? AND attempt_number = ?
                """,
                (
                    LOCAL_EXECUTOR_NAME,
                    worker_id,
                    queue_delay_ms,
                    worker_id,
                    lease_expires_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    run_id,
                    row["attempt_number"],
                ),
            )
            event_payload = {
                "attempt_number": row["attempt_number"],
                "executor_name": LOCAL_EXECUTOR_NAME,
                "executor_instance_id": worker_id,
                "queue_delay_ms": queue_delay_ms,
                "lease_owner": worker_id,
                "lease_expires_at": lease_expires_at.isoformat(),
            }
            connection.execute(
                """
                INSERT INTO checker_run_events (
                    run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["logical_run_id"],
                    row["attempt_number"],
                    "RUN_CLAIMED",
                    row["status"],
                    row["status"],
                    now.isoformat(),
                    json.dumps(event_payload, ensure_ascii=True, sort_keys=True),
                ),
            )
            connection.commit()
        return UUID(run_id)

    def list_events(self, run_id: UUID) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT event_type, from_state, to_state, occurred_at, attempt_number, payload_json
                FROM checker_run_events
                WHERE run_id = ?
                ORDER BY event_id ASC
                """,
                (str(run_id),),
            ).fetchall()
        return [
            {
                "event_type": row["event_type"],
                "from_state": row["from_state"],
                "to_state": row["to_state"],
                "occurred_at": row["occurred_at"],
                "attempt_number": row["attempt_number"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def list_attempts(self, run_id: UUID) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category
                FROM checker_run_attempts
                WHERE run_id = ?
                ORDER BY attempt_number ASC
                """,
                (str(run_id),),
            ).fetchall()
        return [dict(row) for row in rows]