from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from ..schemas.jobs import JobLogEntry, JobLogsResponse, JobStatusResponse
from .sqlite import connect, ensure_operations_db


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class JobRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def create_job(self, *, job_id: UUID, phase: str, status: str, payload: dict, project_id: str | None, created_at: datetime) -> None:
        payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        logical_run_id = str(job_id)
        attempt_number = 1
        with connect(self.db_path) as connection:
            persisted_project_id = _project_id_if_registered(connection, project_id)
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, logical_run_id, attempt_number, project_id, phase, status, payload_json, request_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job_id),
                    logical_run_id,
                    attempt_number,
                    persisted_project_id,
                    phase,
                    status,
                    payload_json,
                    payload_json,
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
                    payload_json,
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
        assignments.append("updated_at = ?")
        values.append(updated_at.isoformat())
        values.append(str(job_id))
        event_payload = {
            "current_phase": current_phase,
            "current_step": current_step,
            "detail": detail,
            "progress_current": progress_current,
            "progress_total": progress_total,
            "error": error,
        }
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE jobs SET {', '.join(assignments)} WHERE job_id = ?",
                values,
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
