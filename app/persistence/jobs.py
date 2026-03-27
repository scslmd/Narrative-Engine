from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from ..request_identity import canonical_request_json
from ..schemas.jobs import JobLogEntry, JobLogsResponse, JobStatusResponse
from .sqlite import connect, ensure_operations_db

LOCAL_EXECUTOR_NAME = "local_executor"


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class JobRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def create_job(
        self,
        *,
        job_id: UUID,
        phase: str,
        status: str,
        payload: dict,
        request_payload: dict,
        request_hash: str,
        request_scope: str,
        idempotency_key: str | None,
        project_id: str | None,
        created_at: datetime,
    ) -> None:
        payload_json = canonical_request_json(payload)
        request_json = canonical_request_json(request_payload)
        logical_run_id = str(job_id)
        attempt_number = 1
        with connect(self.db_path) as connection:
            persisted_project_id = _project_id_if_registered(connection, project_id)
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, logical_run_id, attempt_number, project_id, phase, status, payload_json, request_json,
                    idempotency_key, request_hash, request_scope,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
                    logical_run_id,
                    attempt_number,
                    persisted_project_id,
                    phase,
                    status,
                    payload_json,
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
                INSERT INTO job_attempts (
                    job_id, logical_run_id, attempt_number, status, executor_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
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
                INSERT INTO job_events (
                    job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
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
        heartbeat_at: datetime | None = None,
        error: str | None = None,
        error_category: str | None = None,
        finish_reason: str | None = None,
        failure_stage: str | None = None,
        retryable: bool | None = None,
        updated_at: datetime,
    ) -> None:
        with connect(self.db_path) as connection:
            existing = connection.execute(
                "SELECT status, logical_run_id, attempt_number FROM jobs WHERE job_id = ?",
                (str(job_id),),
            ).fetchone()
            if existing is None:
                raise KeyError(str(job_id))

        assignments: list[str] = []
        values: list[object] = []
        attempt_assignments: list[str] = []
        attempt_values: list[object] = []
        for column, value in (
            ("status", status),
            ("current_phase", current_phase),
            ("current_step", current_step),
            ("detail", detail),
            ("progress_current", progress_current),
            ("progress_total", progress_total),
            ("error", error),
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
        elif status == "PROCESSING":
            attempt_assignments.append("started_at = COALESCE(started_at, ?)")
            attempt_values.append(updated_at.isoformat())
        if status is not None:
            attempt_assignments.append("status = ?")
            attempt_values.append(status)
        if error is not None:
            attempt_assignments.append("error_code = ?")
            attempt_values.append(error)
        if error_category is not None:
            attempt_assignments.append("error_category = ?")
            attempt_values.append(error_category)
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
        values.append(str(job_id))
        if not attempt_assignments:
            attempt_assignments.append("updated_at = ?")
            attempt_values.append(updated_at.isoformat())
        event_payload = {
            "current_phase": current_phase,
            "current_step": current_step,
            "detail": detail,
            "progress_current": progress_current,
            "progress_total": progress_total,
            "error": error,
            "error_category": error_category,
            "finish_reason": finish_reason,
            "failure_stage": failure_stage,
            "retryable": retryable,
        }
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE jobs SET {', '.join(assignments)} WHERE job_id = ?",
                values,
            )
            attempt_update_values = [*attempt_values, updated_at.isoformat(), str(job_id), existing["attempt_number"]]
            connection.execute(
                f"UPDATE job_attempts SET {', '.join(attempt_assignments)}, updated_at = ? WHERE job_id = ? AND attempt_number = ?",
                attempt_update_values,
            )
            if status is not None:
                connection.execute(
                    """
                    INSERT INTO job_events (
                        job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(job_id),
                        existing["logical_run_id"],
                        existing["attempt_number"],
                        "RUN_STATE_CHANGED",
                        existing["status"],
                        status,
                        updated_at.isoformat(),
                        json.dumps(event_payload, ensure_ascii=True, sort_keys=True),
                    ),
                )
            elif any(value is not None for value in (current_phase, current_step, detail, progress_current, progress_total, error, heartbeat_at)):
                connection.execute(
                    """
                    INSERT INTO job_events (
                        job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(job_id),
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
            raise KeyError(str(job_id))

    def get_job(self, job_id: UUID) -> JobStatusResponse:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (str(job_id),)).fetchone()
        if row is None:
            raise KeyError(str(job_id))
        return JobStatusResponse(
            id=UUID(row["job_id"]),
            phase=row["phase"],
            status=row["status"],
            attempt_number=int(row["attempt_number"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            current_phase=row["current_phase"],
            current_step=row["current_step"],
            detail=row["detail"],
            progress_current=row["progress_current"],
            progress_total=row["progress_total"],
            heartbeat_at=_parse_datetime(row["heartbeat_at"]),
            error=row["error"],
        )

    def get_request_payload(self, job_id: UUID) -> dict[str, object]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT request_json FROM jobs WHERE job_id = ?",
                (str(job_id),),
            ).fetchone()
        if row is None:
            raise KeyError(str(job_id))
        return dict(json.loads(row["request_json"]))

    def find_by_idempotency_key(self, *, request_scope: str, idempotency_key: str) -> dict[str, object] | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT job_id, request_hash, status
                FROM jobs
                WHERE request_scope = ? AND idempotency_key = ?
                """,
                (request_scope, idempotency_key),
            ).fetchone()
        return dict(row) if row is not None else None

    def claim_next_pending(self, *, worker_id: str, now: datetime, lease_expires_at: datetime) -> UUID | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT job_id, logical_run_id, attempt_number, status, lease_owner, lease_expires_at, created_at
                FROM jobs
                WHERE status = 'PENDING'
                  AND (lease_expires_at IS NULL OR lease_expires_at <= ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (now.isoformat(),),
            ).fetchone()
            if row is None:
                return None
            job_id = row["job_id"]
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
                    INSERT INTO job_events (
                        job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
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
                    INSERT INTO job_events (
                        job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
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
                UPDATE jobs
                SET lease_owner = ?, lease_expires_at = ?, claimed_at = ?, updated_at = ?
                WHERE job_id = ?
                  AND status = 'PENDING'
                  AND (lease_expires_at IS NULL OR lease_expires_at <= ?)
                """,
                (
                    worker_id,
                    lease_expires_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    job_id,
                    now.isoformat(),
                ),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return None
            queue_delay_ms = int((now - datetime.fromisoformat(row["created_at"])).total_seconds() * 1000)
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
                UPDATE job_attempts
                SET executor_name = ?, executor_instance_id = ?, queue_delay_ms = ?, lease_owner = ?, lease_expires_at = ?, claimed_at = ?, updated_at = ?
                WHERE job_id = ? AND attempt_number = ?
                """,
                (
                    LOCAL_EXECUTOR_NAME,
                    worker_id,
                    queue_delay_ms,
                    worker_id,
                    lease_expires_at.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    job_id,
                    row["attempt_number"],
                ),
            )
            connection.execute(
                """
                INSERT INTO job_events (
                    job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
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
        return UUID(job_id)

    def get_attempt(self, job_id: UUID) -> dict[str, object]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category
                FROM job_attempts
                WHERE job_id = ?
                ORDER BY attempt_number DESC
                LIMIT 1
                """,
                (str(job_id),),
            ).fetchone()
        if row is None:
            raise KeyError(str(job_id))
        return dict(row)

    def retry_job(self, job_id: UUID, *, retry_reason: str, updated_at: datetime) -> None:
        with connect(self.db_path) as connection:
            existing = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status
                FROM jobs
                WHERE job_id = ?
                """,
                (str(job_id),),
            ).fetchone()
            if existing is None:
                raise KeyError(str(job_id))
            next_attempt_number = int(existing["attempt_number"]) + 1
            connection.execute(
                """
                UPDATE jobs
                SET attempt_number = ?, status = ?, current_phase = NULL, current_step = NULL, detail = ?, progress_current = NULL,
                    progress_total = NULL, heartbeat_at = NULL, lease_owner = NULL, lease_expires_at = NULL, claimed_at = NULL,
                    error = NULL, updated_at = ?
                WHERE job_id = ?
                """,
                (
                    next_attempt_number,
                    "PENDING",
                    f"Retry queued: {retry_reason}",
                    updated_at.isoformat(),
                    str(job_id),
                ),
            )
            connection.execute(
                """
                INSERT INTO job_attempts (
                    job_id, logical_run_id, attempt_number, status, executor_name, retry_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
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
                INSERT INTO job_events (
                    job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
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

    def list_events(self, job_id: UUID) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT event_type, from_state, to_state, occurred_at, attempt_number, payload_json
                FROM job_events
                WHERE job_id = ?
                ORDER BY event_id ASC
                """,
                (str(job_id),),
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

    def list_attempts(self, job_id: UUID) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category
                FROM job_attempts
                WHERE job_id = ?
                ORDER BY attempt_number ASC
                """,
                (str(job_id),),
            ).fetchall()
        return [dict(row) for row in rows]


class JobLogRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def append(self, job_id: UUID, entry: JobLogEntry) -> None:
        with connect(self.db_path) as connection:
            if connection.execute("SELECT 1 FROM jobs WHERE job_id = ?", (str(job_id),)).fetchone() is None:
                raise KeyError(str(job_id))
            connection.execute(
                "INSERT INTO job_logs (job_id, timestamp, level, message) VALUES (?, ?, ?, ?)",
                (str(job_id), entry.timestamp.isoformat(), entry.level, entry.message),
            )
            connection.commit()

    def list_for_job(self, job_id: UUID) -> JobLogsResponse:
        with connect(self.db_path) as connection:
            if connection.execute("SELECT 1 FROM jobs WHERE job_id = ?", (str(job_id),)).fetchone() is None:
                raise KeyError(str(job_id))
            rows = connection.execute(
                "SELECT timestamp, level, message FROM job_logs WHERE job_id = ? ORDER BY log_id ASC",
                (str(job_id),),
            ).fetchall()
        return JobLogsResponse(
            id=job_id,
            entries=[
                JobLogEntry(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    level=row["level"],
                    message=row["message"],
                )
                for row in rows
            ],
        )


def _project_id_if_registered(connection, project_id: str | None) -> str | None:
    if not project_id:
        return None
    row = connection.execute(
        "SELECT 1 FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return project_id if row is not None else None