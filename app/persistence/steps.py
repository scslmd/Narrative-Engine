from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from .sqlite import connect, ensure_operations_db


def _json_list(value: list[str]) -> str:
    return json.dumps(list(value), ensure_ascii=True, sort_keys=True)


def _parse_json_list(value: str) -> list[str]:
    return list(json.loads(value or "[]"))


def stable_hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_hash_payload(payload: object) -> str:
    return stable_hash_text(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))


class StepRecordRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)
        self._ensure_runtime_telemetry_columns()

    def _ensure_runtime_telemetry_columns(self) -> None:
        required_columns = {
            "prompt_tokens": "ALTER TABLE step_records ADD COLUMN prompt_tokens INTEGER",
            "completion_tokens": "ALTER TABLE step_records ADD COLUMN completion_tokens INTEGER",
            "total_tokens": "ALTER TABLE step_records ADD COLUMN total_tokens INTEGER",
        }
        with connect(self.db_path) as connection:
            existing_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info('step_records')").fetchall()
            }
            for column_name, ddl in required_columns.items():
                if column_name not in existing_columns:
                    connection.execute(ddl)
            connection.commit()

    def create_step_record(
        self,
        *,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int,
        step_name: str,
        step_index: int,
        state: str,
        project_id: str | None,
        model_id: str | None,
        critic_profile: str | None,
        backend_name: str | None,
        backend_version: str | None,
        input_hash: str | None,
        output_hash: str | None,
        prompt_hash: str | None,
        input_artifact_refs: list[str],
        output_artifact_refs: list[str],
        started_at: datetime | None,
        finished_at: datetime | None,
        duration_seconds: float | None,
        finish_reason: str | None,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        error_code: str | None,
        error_category: str | None,
        executor_id: str | None,
        lease_owner: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> int:
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO step_records (
                    logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id,
                    model_id, critic_profile, backend_name, backend_version, input_hash, output_hash, prompt_hash,
                    input_artifact_refs_json, output_artifact_refs_json, started_at, finished_at, duration_seconds,
                    finish_reason, prompt_tokens, completion_tokens, total_tokens, error_code, error_category,
                    executor_id, lease_owner, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    logical_run_id,
                    run_id,
                    run_kind,
                    attempt_number,
                    step_name,
                    step_index,
                    state,
                    project_id,
                    model_id,
                    critic_profile,
                    backend_name,
                    backend_version,
                    input_hash,
                    output_hash,
                    prompt_hash,
                    _json_list(input_artifact_refs),
                    _json_list(output_artifact_refs),
                    started_at.isoformat() if started_at is not None else None,
                    finished_at.isoformat() if finished_at is not None else None,
                    duration_seconds,
                    finish_reason,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    error_code,
                    error_category,
                    executor_id,
                    lease_owner,
                    created_at.isoformat(),
                    updated_at.isoformat(),
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def list_for_run(
        self,
        *,
        run_id: str,
        run_kind: str,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        where_clause = "WHERE run_id = ? AND run_kind = ?"
        params: list[object] = [run_id, run_kind]
        if attempt_number is not None:
            where_clause += " AND attempt_number = ?"
            params.append(attempt_number)
        limit_clause = ""
        if limit is not None:
            limit_clause = " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM step_records
                """ + where_clause + """
                ORDER BY step_index ASC, step_record_id ASC
                """ + limit_clause,
                tuple(params),
            ).fetchall()
        return [
            {
                "step_record_id": row["step_record_id"],
                "logical_run_id": row["logical_run_id"],
                "run_id": row["run_id"],
                "run_kind": row["run_kind"],
                "attempt_number": row["attempt_number"],
                "step_name": row["step_name"],
                "step_index": row["step_index"],
                "state": row["state"],
                "project_id": row["project_id"],
                "model_id": row["model_id"],
                "critic_profile": row["critic_profile"],
                "backend_name": row["backend_name"],
                "backend_version": row["backend_version"],
                "input_hash": row["input_hash"],
                "output_hash": row["output_hash"],
                "prompt_hash": row["prompt_hash"],
                "input_artifact_refs": _parse_json_list(row["input_artifact_refs_json"]),
                "output_artifact_refs": _parse_json_list(row["output_artifact_refs_json"]),
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "duration_seconds": row["duration_seconds"],
                "finish_reason": row["finish_reason"],
                "error_code": row["error_code"],
                "error_category": row["error_category"],
                "executor_id": row["executor_id"],
                "lease_owner": row["lease_owner"],
            }
            for row in rows
        ]


class ArtifactLineageRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def _supersede_existing_canonical_rows(
        self,
        connection,
        *,
        project_id: str,
        artifact_role: str,
    ) -> int | None:
        rows = connection.execute(
            """
            SELECT artifact_lineage_id
            FROM artifact_lineage
            WHERE project_id = ? AND artifact_role = ? AND status = 'CANONICAL'
            ORDER BY artifact_lineage_id ASC
            """,
            (project_id, artifact_role),
        ).fetchall()
        if not rows:
            return None
        connection.execute(
            """
            UPDATE artifact_lineage
            SET status = 'SUPERSEDED'
            WHERE project_id = ? AND artifact_role = ? AND status = 'CANONICAL'
            """,
            (project_id, artifact_role),
        )
        return int(rows[-1]["artifact_lineage_id"])

    def latest_canonical_for_project_artifact(self, *, project_id: str, artifact_role: str) -> dict[str, object] | None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM artifact_lineage
                WHERE project_id = ? AND artifact_role = ? AND status = 'CANONICAL'
                ORDER BY artifact_lineage_id DESC
                LIMIT 1
                """,
                (project_id, artifact_role),
            ).fetchone()
        if row is None:
            return None
        return {
            "artifact_lineage_id": row["artifact_lineage_id"],
            "logical_run_id": row["logical_run_id"],
            "run_id": row["run_id"],
            "run_kind": row["run_kind"],
            "attempt_number": row["attempt_number"],
            "step_name": row["step_name"],
            "project_id": row["project_id"],
            "artifact_role": row["artifact_role"],
            "artifact_kind": row["artifact_kind"],
            "path": row["path"],
            "content_hash": row["content_hash"],
            "status": row["status"],
            "validation_state": row["validation_state"],
            "produced_at": row["produced_at"],
            "registered_at": row["registered_at"],
            "supersedes_artifact_lineage_id": row["supersedes_artifact_lineage_id"],
            "source_artifact_refs": _parse_json_list(row["source_artifact_refs_json"]),
            "source_content_hashes": _parse_json_list(row["source_content_hashes_json"]),
            "output_of_step_record_id": row["output_of_step_record_id"],
        }

    def create_lineage_record(
        self,
        *,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int,
        step_name: str,
        project_id: str | None,
        artifact_role: str,
        artifact_kind: str,
        path: str,
        content_hash: str | None,
        status: str,
        validation_state: str,
        produced_at: datetime,
        registered_at: datetime | None,
        supersedes_artifact_lineage_id: int | None,
        source_artifact_refs: list[str],
        source_content_hashes: list[str],
        output_of_step_record_id: int,
    ) -> int:
        with connect(self.db_path) as connection:
            supersedes_id = supersedes_artifact_lineage_id
            if supersedes_id is None and status == "CANONICAL" and project_id is not None:
                supersedes_id = self._supersede_existing_canonical_rows(
                    connection,
                    project_id=project_id,
                    artifact_role=artifact_role,
                )
            cursor = connection.execute(
                """
                INSERT INTO artifact_lineage (
                    logical_run_id, run_id, run_kind, attempt_number, step_name, project_id, artifact_role,
                    artifact_kind, path, content_hash, status, validation_state, produced_at, registered_at,
                    supersedes_artifact_lineage_id, source_artifact_refs_json, source_content_hashes_json, output_of_step_record_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    logical_run_id,
                    run_id,
                    run_kind,
                    attempt_number,
                    step_name,
                    project_id,
                    artifact_role,
                    artifact_kind,
                    path,
                    content_hash,
                    status,
                    validation_state,
                    produced_at.isoformat(),
                    registered_at.isoformat() if registered_at is not None else None,
                    supersedes_id,
                    _json_list(source_artifact_refs),
                    _json_list(source_content_hashes),
                    output_of_step_record_id,
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def list_for_run(
        self,
        *,
        run_id: str,
        run_kind: str,
        attempt_number: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        where_clause = "WHERE run_id = ? AND run_kind = ?"
        params: list[object] = [run_id, run_kind]
        if attempt_number is not None:
            where_clause += " AND attempt_number = ?"
            params.append(attempt_number)
        limit_clause = ""
        if limit is not None:
            limit_clause = " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM artifact_lineage
                """ + where_clause + """
                ORDER BY artifact_lineage_id ASC
                """ + limit_clause,
                tuple(params),
            ).fetchall()
        return [
            {
                "artifact_lineage_id": row["artifact_lineage_id"],
                "logical_run_id": row["logical_run_id"],
                "run_id": row["run_id"],
                "run_kind": row["run_kind"],
                "attempt_number": row["attempt_number"],
                "step_name": row["step_name"],
                "project_id": row["project_id"],
                "artifact_role": row["artifact_role"],
                "artifact_kind": row["artifact_kind"],
                "path": row["path"],
                "content_hash": row["content_hash"],
                "status": row["status"],
                "validation_state": row["validation_state"],
                "produced_at": row["produced_at"],
                "registered_at": row["registered_at"],
                "supersedes_artifact_lineage_id": row["supersedes_artifact_lineage_id"],
                "source_artifact_refs": _parse_json_list(row["source_artifact_refs_json"]),
                "source_content_hashes": _parse_json_list(row["source_content_hashes_json"]),
                "output_of_step_record_id": row["output_of_step_record_id"],
            }
            for row in rows
        ]


class RuntimeArtifactSelectionRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

    def create_or_replace_selection(
        self,
        *,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int,
        step_name: str,
        project_id: str | None,
        artifact_role: str,
        selected_artifact_lineage_id: int | None,
        selected_path: str | None,
        selected_content_hash: str,
        selected_content: str,
        selected_at: datetime,
    ) -> int:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO runtime_artifact_selections (
                    logical_run_id, run_id, run_kind, attempt_number, step_name, project_id,
                    artifact_role, selected_artifact_lineage_id, selected_path, selected_content_hash,
                    selected_content, selected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, run_kind, attempt_number, step_name, artifact_role) DO UPDATE SET
                    selected_artifact_lineage_id = excluded.selected_artifact_lineage_id,
                    selected_path = excluded.selected_path,
                    selected_content_hash = excluded.selected_content_hash,
                    selected_content = excluded.selected_content,
                    selected_at = excluded.selected_at
                """,
                (
                    logical_run_id,
                    run_id,
                    run_kind,
                    attempt_number,
                    step_name,
                    project_id,
                    artifact_role,
                    selected_artifact_lineage_id,
                    selected_path,
                    selected_content_hash,
                    selected_content,
                    selected_at.isoformat(),
                ),
            )
            row = connection.execute(
                """
                SELECT selection_id
                FROM runtime_artifact_selections
                WHERE run_id = ? AND run_kind = ? AND attempt_number = ? AND step_name = ? AND artifact_role = ?
                """,
                (run_id, run_kind, attempt_number, step_name, artifact_role),
            ).fetchone()
            connection.commit()
        assert row is not None
        return int(row["selection_id"])

    def list_for_run(
        self,
        *,
        run_id: str,
        run_kind: str,
        attempt_number: int,
        step_name: str,
    ) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM runtime_artifact_selections
                WHERE run_id = ? AND run_kind = ? AND attempt_number = ? AND step_name = ?
                ORDER BY selection_id ASC
                """,
                (run_id, run_kind, attempt_number, step_name),
            ).fetchall()
        return [
            {
                "selection_id": row["selection_id"],
                "logical_run_id": row["logical_run_id"],
                "run_id": row["run_id"],
                "run_kind": row["run_kind"],
                "attempt_number": row["attempt_number"],
                "step_name": row["step_name"],
                "project_id": row["project_id"],
                "artifact_role": row["artifact_role"],
                "selected_artifact_lineage_id": row["selected_artifact_lineage_id"],
                "selected_path": row["selected_path"],
                "selected_content_hash": row["selected_content_hash"],
                "selected_content": row["selected_content"],
                "selected_at": row["selected_at"],
            }
            for row in rows
        ]
