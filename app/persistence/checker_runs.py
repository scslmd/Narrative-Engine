from __future__ import annotations

import json
from datetime import datetime
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
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO checker_runs (
                    run_id, project_id, status, request_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run_id),
                    project_id,
                    status,
                    json.dumps(request_payload, ensure_ascii=True, sort_keys=True),
                    created_at.isoformat(),
                    created_at.isoformat(),
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
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE checker_runs SET {', '.join(assignments)} WHERE run_id = ?",
                values,
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(str(run_id))

    def add_result(self, run_id: UUID, result: RoleCheckResult) -> None:
        with connect(self.db_path) as connection:
            if connection.execute("SELECT 1 FROM checker_runs WHERE run_id = ?", (str(run_id),)).fetchone() is None:
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
