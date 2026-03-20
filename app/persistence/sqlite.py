from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..request_identity import checker_request_scope, job_request_scope, request_hash

OPERATIONS_DB_VERSION = 9
PROJECT_DB_VERSION = 1
SQLITE_BUSY_TIMEOUT_MS = 5000


OPERATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    db_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT,
    size_bytes INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, artifact_type),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    project_id TEXT,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    request_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL DEFAULT '',
    request_scope TEXT NOT NULL DEFAULT '',
    current_phase TEXT,
    current_step TEXT,
    detail TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    heartbeat_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS job_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    executor_name TEXT,
    executor_instance_id TEXT,
    queue_delay_ms INTEGER,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    last_heartbeat_at TEXT,
    finish_reason TEXT,
    failure_stage TEXT,
    retryable INTEGER,
    retry_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(logical_run_id, attempt_number),
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_runs (
    run_id TEXT PRIMARY KEY,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    project_id TEXT,
    status TEXT NOT NULL,
    request_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL DEFAULT '',
    request_scope TEXT NOT NULL DEFAULT '',
    current_role TEXT,
    detail TEXT,
    heartbeat_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    report_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS checker_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    role TEXT NOT NULL,
    passed INTEGER NOT NULL,
    duration_seconds REAL NOT NULL,
    findings_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    preview TEXT,
    metadata_json TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_run_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    executor_name TEXT,
    executor_instance_id TEXT,
    queue_delay_ms INTEGER,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    last_heartbeat_at TEXT,
    finish_reason TEXT,
    failure_stage TEXT,
    retryable INTEGER,
    retry_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(logical_run_id, attempt_number),
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_run_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS step_records (
    step_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    state TEXT NOT NULL,
    project_id TEXT,
    model_id TEXT,
    critic_profile TEXT,
    backend_name TEXT,
    backend_version TEXT,
    input_hash TEXT,
    output_hash TEXT,
    prompt_hash TEXT,
    input_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    output_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    started_at TEXT,
    finished_at TEXT,
    duration_seconds REAL,
    finish_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    executor_id TEXT,
    lease_owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_lineage (
    artifact_lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    project_id TEXT,
    artifact_role TEXT NOT NULL,
    artifact_kind TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT,
    status TEXT NOT NULL,
    validation_state TEXT NOT NULL,
    produced_at TEXT NOT NULL,
    registered_at TEXT,
    supersedes_artifact_lineage_id INTEGER,
    source_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    source_content_hashes_json TEXT NOT NULL DEFAULT '[]',
    output_of_step_record_id INTEGER NOT NULL,
    FOREIGN KEY(supersedes_artifact_lineage_id) REFERENCES artifact_lineage(artifact_lineage_id) ON DELETE SET NULL,
    FOREIGN KEY(output_of_step_record_id) REFERENCES step_records(step_record_id) ON DELETE CASCADE
);
"""


OPERATIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);
CREATE INDEX IF NOT EXISTS idx_project_artifacts_project_type ON project_artifacts(project_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_jobs_project_status ON jobs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_logical_attempt ON jobs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_jobs_status_updated_at ON jobs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status_lease ON jobs(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_request_scope_hash ON jobs(request_scope, request_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_scope_idempotency_key ON jobs(request_scope, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_logs_job_id_log_id ON job_logs(job_id, log_id);
CREATE INDEX IF NOT EXISTS idx_job_attempts_job_id_attempt ON job_attempts(job_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_job_attempts_logical_attempt ON job_attempts(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_job_attempts_status_lease ON job_attempts(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_job_events_job_id_event_id ON job_events(job_id, event_id);
CREATE INDEX IF NOT EXISTS idx_job_events_logical_attempt ON job_events(logical_run_id, attempt_number, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_runs_project_status ON checker_runs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_checker_runs_logical_attempt ON checker_runs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_runs_status_updated_at ON checker_runs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_checker_runs_status_lease ON checker_runs(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_checker_runs_request_scope_hash ON checker_runs(request_scope, request_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_checker_runs_scope_idempotency_key ON checker_runs(request_scope, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_checker_results_run_id_result_id ON checker_results(run_id, result_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_run_id_attempt ON checker_run_attempts(run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_logical_attempt ON checker_run_attempts(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_status_lease ON checker_run_attempts(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_run_id_event_id ON checker_run_events(run_id, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_logical_attempt ON checker_run_events(logical_run_id, attempt_number, event_id);
CREATE INDEX IF NOT EXISTS idx_step_records_run ON step_records(run_kind, run_id, step_index, step_record_id);
CREATE INDEX IF NOT EXISTS idx_step_records_logical_attempt ON step_records(logical_run_id, attempt_number, step_index);
CREATE INDEX IF NOT EXISTS idx_artifact_lineage_run ON artifact_lineage(run_kind, run_id, artifact_lineage_id);
CREATE INDEX IF NOT EXISTS idx_artifact_lineage_step_record ON artifact_lineage(output_of_step_record_id, artifact_lineage_id);
"""


PROJECT_SCHEMA = """
CREATE TABLE IF NOT EXISTS project_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_type TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


PROJECT_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    _configure_connection(connection)
    return connection


def ensure_operations_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        _migrate_operations_db(connection)
        connection.commit()
    return db_path


def ensure_project_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        _migrate_project_db(connection)
        connection.commit()
    return db_path


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")


def _migrate_operations_db(connection: sqlite3.Connection) -> None:
    version = _get_user_version(connection)
    if version == 0:
        connection.executescript(OPERATIONS_SCHEMA)
        _apply_operations_indexes(connection)
        _set_user_version(connection, OPERATIONS_DB_VERSION)
        return

    if version < OPERATIONS_DB_VERSION:
        _rebuild_operations_schema(connection)
        _set_user_version(connection, OPERATIONS_DB_VERSION)
        return

    connection.executescript(OPERATIONS_SCHEMA)
    _apply_operations_indexes(connection)


def _migrate_project_db(connection: sqlite3.Connection) -> None:
    version = _get_user_version(connection)
    if version == 0:
        connection.executescript(PROJECT_SCHEMA)
        connection.executescript(PROJECT_INDEXES)
        _set_user_version(connection, PROJECT_DB_VERSION)
        return

    connection.executescript(PROJECT_SCHEMA)
    connection.executescript(PROJECT_INDEXES)
    if version < PROJECT_DB_VERSION:
        _set_user_version(connection, PROJECT_DB_VERSION)


def _rebuild_operations_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        _reset_partial_rebuild_state(connection)
        _rename_table_if_exists(connection, "projects", "projects__legacy")
        _rename_table_if_exists(connection, "project_artifacts", "project_artifacts__legacy")
        _rename_table_if_exists(connection, "jobs", "jobs__legacy")
        _rename_table_if_exists(connection, "job_logs", "job_logs__legacy")
        _rename_table_if_exists(connection, "job_attempts", "job_attempts__legacy")
        _rename_table_if_exists(connection, "job_events", "job_events__legacy")
        _rename_table_if_exists(connection, "checker_runs", "checker_runs__legacy")
        _rename_table_if_exists(connection, "checker_results", "checker_results__legacy")
        _rename_table_if_exists(connection, "checker_run_attempts", "checker_run_attempts__legacy")
        _rename_table_if_exists(connection, "checker_run_events", "checker_run_events__legacy")
        _rename_table_if_exists(connection, "step_records", "step_records__legacy")
        _rename_table_if_exists(connection, "artifact_lineage", "artifact_lineage__legacy")

        connection.executescript(OPERATIONS_SCHEMA)

        _copy_if_exists(
            connection,
            "projects__legacy",
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            )
            SELECT project_id, project_name, manifest_path, db_path, created_at, updated_at
            FROM projects__legacy
            """,
        )
        _copy_if_exists(
            connection,
            "project_artifacts__legacy",
            """
            INSERT INTO project_artifacts (
                artifact_id, project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
            )
            SELECT artifact_id, project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
            FROM project_artifacts__legacy
            """,
        )
        _copy_jobs_legacy(connection)
        _backfill_job_request_identity(connection)
        _copy_if_exists(
            connection,
            "job_logs__legacy",
            """
            INSERT INTO job_logs (log_id, job_id, timestamp, level, message)
            SELECT log_id, job_id, timestamp, level, message
            FROM job_logs__legacy
            """,
        )
        _copy_job_attempts_legacy(connection)
        if not _table_exists(connection, "job_attempts__legacy"):
            _backfill_job_attempts(connection)
        _copy_job_events_legacy(connection)
        _copy_checker_runs_legacy(connection)
        _backfill_checker_run_request_identity(connection)
        _copy_if_exists(
            connection,
            "checker_results__legacy",
            """
            INSERT INTO checker_results (
                result_id, run_id, role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
            )
            SELECT result_id, run_id, role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
            FROM checker_results__legacy
            """,
        )
        _copy_checker_run_attempts_legacy(connection)
        if not _table_exists(connection, "checker_run_attempts__legacy"):
            _backfill_checker_run_attempts(connection)
        _copy_checker_run_events_legacy(connection)
        _copy_step_records_legacy(connection)
        _copy_artifact_lineage_legacy(connection)

        _apply_operations_indexes(connection)
        _drop_legacy_tables(connection)
    except Exception:
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def _apply_operations_indexes(connection: sqlite3.Connection) -> None:
    connection.executescript(OPERATIONS_INDEXES)


def _reset_partial_rebuild_state(connection: sqlite3.Connection) -> None:
    for table_name, legacy_name in (
        ("project_artifacts", "project_artifacts__legacy"),
        ("projects", "projects__legacy"),
        ("job_logs", "job_logs__legacy"),
        ("job_events", "job_events__legacy"),
        ("jobs", "jobs__legacy"),
        ("job_attempts", "jobs__legacy"),
        ("checker_results", "checker_results__legacy"),
        ("checker_run_events", "checker_run_events__legacy"),
        ("checker_runs", "checker_runs__legacy"),
        ("checker_run_attempts", "checker_runs__legacy"),
        ("step_records", "step_records__legacy"),
        ("artifact_lineage", "artifact_lineage__legacy"),
    ):
        if _table_exists(connection, legacy_name) and _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


def _rename_table_if_exists(connection: sqlite3.Connection, table_name: str, legacy_name: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")


def _copy_if_exists(connection: sqlite3.Connection, table_name: str, sql: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(sql)


def _backfill_job_attempts(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO job_attempts (
            job_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            job_id,
            logical_run_id,
            attempt_number,
            status,
            NULL,
            NULL,
            NULL,
            lease_owner,
            lease_expires_at,
            claimed_at,
            CASE WHEN status IN ('PROCESSING', 'COMPLETED', 'FAILED') THEN COALESCE(claimed_at, created_at) ELSE NULL END,
            CASE WHEN status IN ('COMPLETED', 'FAILED') THEN updated_at ELSE NULL END,
            heartbeat_at,
            CASE WHEN status = 'COMPLETED' THEN 'completed' WHEN status = 'FAILED' THEN 'failed' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 'run' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 0 ELSE NULL END,
            NULL,
            NULL,
            NULL,
            created_at,
            updated_at
        FROM jobs
        """
    )


def _backfill_checker_run_attempts(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO checker_run_attempts (
            run_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            run_id,
            logical_run_id,
            attempt_number,
            status,
            NULL,
            NULL,
            NULL,
            lease_owner,
            lease_expires_at,
            claimed_at,
            CASE WHEN status IN ('RUNNING', 'COMPLETED', 'FAILED') THEN COALESCE(claimed_at, created_at) ELSE NULL END,
            CASE WHEN status IN ('COMPLETED', 'FAILED') THEN updated_at ELSE NULL END,
            heartbeat_at,
            CASE WHEN status = 'COMPLETED' THEN 'completed' WHEN status = 'FAILED' THEN 'failed' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 'run' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 0 ELSE NULL END,
            NULL,
            NULL,
            NULL,
            created_at,
            updated_at
        FROM checker_runs
        """
    )


def _copy_jobs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "jobs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "jobs__legacy", "logical_run_id") else "job_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "jobs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "jobs__legacy", "request_json") else "payload_json"
    lease_owner_expr = "lease_owner" if _column_exists(connection, "jobs__legacy", "lease_owner") else "NULL"
    lease_expires_expr = "lease_expires_at" if _column_exists(connection, "jobs__legacy", "lease_expires_at") else "NULL"
    claimed_at_expr = "claimed_at" if _column_exists(connection, "jobs__legacy", "claimed_at") else "NULL"
    connection.execute(
        f"""
        INSERT INTO jobs (
            job_id, logical_run_id, attempt_number, project_id, phase, status, payload_json, request_json,
            idempotency_key, request_hash, request_scope, current_phase, current_step, detail, progress_current, progress_total,
            heartbeat_at, lease_owner, lease_expires_at, claimed_at, error, created_at, updated_at
        )
        SELECT
            job_id,
            COALESCE({logical_run_expr}, job_id),
            COALESCE({attempt_expr}, 1),
            project_id,
            phase,
            status,
            payload_json,
            COALESCE({request_expr}, payload_json, '{{}}'),
            NULL,
            '',
            '',
            current_phase,
            current_step,
            detail,
            progress_current,
            progress_total,
            heartbeat_at,
            {lease_owner_expr},
            {lease_expires_expr},
            {claimed_at_expr},
            error,
            created_at,
            updated_at
        FROM jobs__legacy
        """
    )


def _copy_job_events_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "job_events__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "job_events__legacy", "logical_run_id") else "job_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "job_events__legacy", "attempt_number") else "1"
    payload_expr = "payload_json" if _column_exists(connection, "job_events__legacy", "payload_json") else "'{}'"
    connection.execute(
        f"""
        INSERT INTO job_events (
            event_id, job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
        )
        SELECT
            event_id,
            job_id,
            COALESCE({logical_run_expr}, job_id),
            COALESCE({attempt_expr}, 1),
            event_type,
            from_state,
            to_state,
            occurred_at,
            COALESCE({payload_expr}, '{{}}')
        FROM job_events__legacy
        """
    )


def _copy_job_attempts_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "job_attempts__legacy"):
        return
    connection.execute(
        """
        INSERT INTO job_attempts (
            attempt_id, job_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            attempt_id, job_id, logical_run_id, attempt_number, status,
            NULL, NULL, NULL,
            lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at,
            NULL, NULL, NULL, NULL,
            retry_reason, error_code, error_category, created_at, updated_at
        FROM job_attempts__legacy
        """
    )


def _copy_checker_runs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_runs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "checker_runs__legacy", "logical_run_id") else "run_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "checker_runs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "checker_runs__legacy", "request_json") else "'{}'"
    lease_owner_expr = "lease_owner" if _column_exists(connection, "checker_runs__legacy", "lease_owner") else "NULL"
    lease_expires_expr = "lease_expires_at" if _column_exists(connection, "checker_runs__legacy", "lease_expires_at") else "NULL"
    claimed_at_expr = "claimed_at" if _column_exists(connection, "checker_runs__legacy", "claimed_at") else "NULL"
    connection.execute(
        f"""
        INSERT INTO checker_runs (
            run_id, logical_run_id, attempt_number, project_id, status, request_json, idempotency_key, request_hash, request_scope, current_role, detail,
            heartbeat_at, lease_owner, lease_expires_at, claimed_at, report_path, created_at, updated_at
        )
        SELECT
            run_id,
            COALESCE({logical_run_expr}, run_id),
            COALESCE({attempt_expr}, 1),
            project_id,
            status,
            COALESCE({request_expr}, '{{}}'),
            NULL,
            '',
            '',
            current_role,
            detail,
            heartbeat_at,
            {lease_owner_expr},
            {lease_expires_expr},
            {claimed_at_expr},
            report_path,
            created_at,
            updated_at
        FROM checker_runs__legacy
        """
    )


def _copy_checker_run_attempts_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_run_attempts__legacy"):
        return
    connection.execute(
        """
        INSERT INTO checker_run_attempts (
            attempt_id, run_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            attempt_id, run_id, logical_run_id, attempt_number, status,
            NULL, NULL, NULL,
            lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at,
            NULL, NULL, NULL, NULL,
            retry_reason, error_code, error_category, created_at, updated_at
        FROM checker_run_attempts__legacy
        """
    )


def _copy_checker_run_events_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_run_events__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "checker_run_events__legacy", "logical_run_id") else "run_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "checker_run_events__legacy", "attempt_number") else "1"
    payload_expr = "payload_json" if _column_exists(connection, "checker_run_events__legacy", "payload_json") else "'{}'"
    connection.execute(
        f"""
        INSERT INTO checker_run_events (
            event_id, run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
        )
        SELECT
            event_id,
            run_id,
            COALESCE({logical_run_expr}, run_id),
            COALESCE({attempt_expr}, 1),
            event_type,
            from_state,
            to_state,
            occurred_at,
            COALESCE({payload_expr}, '{{}}')
        FROM checker_run_events__legacy
        """
    )


def _copy_step_records_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "step_records__legacy"):
        return
    connection.execute(
        """
        INSERT INTO step_records (
            step_record_id, logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id,
            model_id, critic_profile, backend_name, backend_version, input_hash, output_hash, prompt_hash,
            input_artifact_refs_json, output_artifact_refs_json, started_at, finished_at, duration_seconds,
            finish_reason, error_code, error_category, executor_id, lease_owner, created_at, updated_at
        )
        SELECT
            step_record_id, logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id,
            model_id, critic_profile, backend_name, backend_version, input_hash, output_hash, prompt_hash,
            input_artifact_refs_json, output_artifact_refs_json, started_at, finished_at, duration_seconds,
            finish_reason, error_code, error_category, executor_id, lease_owner, created_at, updated_at
        FROM step_records__legacy
        """
    )


def _copy_artifact_lineage_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "artifact_lineage__legacy"):
        return
    connection.execute(
        """
        INSERT INTO artifact_lineage (
            artifact_lineage_id, logical_run_id, run_id, run_kind, attempt_number, step_name, project_id, artifact_role,
            artifact_kind, path, content_hash, status, validation_state, produced_at, registered_at,
            supersedes_artifact_lineage_id, source_artifact_refs_json, source_content_hashes_json, output_of_step_record_id
        )
        SELECT
            artifact_lineage_id, logical_run_id, run_id, run_kind, attempt_number, step_name, project_id, artifact_role,
            artifact_kind, path, content_hash, status, validation_state, produced_at, registered_at,
            supersedes_artifact_lineage_id, source_artifact_refs_json, source_content_hashes_json, output_of_step_record_id
        FROM artifact_lineage__legacy
        """
    )


def _drop_legacy_tables(connection: sqlite3.Connection) -> None:
    for table_name in (
        "project_artifacts__legacy",
        "projects__legacy",
        "job_logs__legacy",
        "job_events__legacy",
        "jobs__legacy",
        "job_attempts__legacy",
        "checker_results__legacy",
        "checker_run_events__legacy",
        "checker_runs__legacy",
        "checker_run_attempts__legacy",
        "step_records__legacy",
        "artifact_lineage__legacy",
    ):
        if _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


def _backfill_job_request_identity(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT job_id, phase, project_id, payload_json, request_json FROM jobs"
    ).fetchall()
    for row in rows:
        request_payload = _normalize_job_request_payload(
            phase=row["phase"],
            payload_json=row["payload_json"],
            request_json=row["request_json"],
        )
        connection.execute(
            """
            UPDATE jobs
            SET request_json = ?, request_hash = ?, request_scope = ?
            WHERE job_id = ?
            """,
            (
                json.dumps(request_payload, ensure_ascii=True, sort_keys=True),
                request_hash(request_payload),
                job_request_scope(phase=row["phase"], project_id=row["project_id"]),
                row["job_id"],
            ),
        )


def _backfill_checker_run_request_identity(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT run_id, request_json FROM checker_runs"
    ).fetchall()
    for row in rows:
        request_payload = json.loads(row["request_json"] or "{}")
        roles = [str(role) for role in request_payload.get("roles", [])]
        critic_profile = str(request_payload.get("critic_profile", "minimal_context"))
        connection.execute(
            """
            UPDATE checker_runs
            SET request_hash = ?, request_scope = ?
            WHERE run_id = ?
            """,
            (
                request_hash(request_payload),
                checker_request_scope(roles=roles, critic_profile=critic_profile),
                row["run_id"],
            ),
        )


def _normalize_job_request_payload(*, phase: str, payload_json: str, request_json: str) -> dict[str, object]:
    payload = json.loads(payload_json or "{}")
    request_payload = json.loads(request_json or "{}")
    if "phase" in request_payload and "payload" in request_payload:
        return request_payload
    return {
        "phase": phase,
        "payload": payload,
    }


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def _get_user_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def _set_user_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")
