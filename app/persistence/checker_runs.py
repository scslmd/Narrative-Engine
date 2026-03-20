from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStatusResponse
from .sqlite import connect, ensure_operations_db


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class CheckerRunRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def create_run(self, *, run_id: UUID, status: str, request_payload: dict, created_at: datetime, project_id: str | None = None) -> None:
        request_json = json.dumps(request_payload, ensure_ascii=True, sort_keys=True)
        logical_run_id = str(run_id)
        attempt_number = 1
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO checker_runs (
                    run_id, logical_run_id, attempt_number, project_id, status, request_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    logical_run_id,
                    attempt_number,
                    project_id,
                    status,
                    request_json,
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
        assignments.append("updated_at = ?")
        values.append(updated_at.isoformat())
        values.append(str(run_id))
        event_payload = {
            "current_role": current_role,
            "detail": detail,
            "report_path": report_path,
        }
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE checker_runs SET {', '.join(assignments)} WHERE run_id = ?",
                values,
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
