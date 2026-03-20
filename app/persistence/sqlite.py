from __future__ import annotations

import sqlite3
from pathlib import Path


OPERATIONS_DB_VERSION = 3
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
    current_phase TEXT,
    current_step TEXT,
    detail TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    heartbeat_at TEXT,
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
    current_role TEXT,
    detail TEXT,
    heartbeat_at TEXT,
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
"""


OPERATIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);
CREATE INDEX IF NOT EXISTS idx_project_artifacts_project_type ON project_artifacts(project_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_jobs_project_status ON jobs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_logical_attempt ON jobs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_jobs_status_updated_at ON jobs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_job_logs_job_id_log_id ON job_logs(job_id, log_id);
CREATE INDEX IF NOT EXISTS idx_job_events_job_id_event_id ON job_events(job_id, event_id);
CREATE INDEX IF NOT EXISTS idx_job_events_logical_attempt ON job_events(logical_run_id, attempt_number, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_runs_project_status ON checker_runs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_checker_runs_logical_attempt ON checker_runs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_runs_status_updated_at ON checker_runs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_checker_results_run_id_result_id ON checker_results(run_id, result_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_run_id_event_id ON checker_run_events(run_id, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_logical_attempt ON checker_run_events(logical_run_id, attempt_number, event_id);
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
        _rename_table_if_exists(connection, "job_events", "job_events__legacy")
        _rename_table_if_exists(connection, "checker_runs", "checker_runs__legacy")
        _rename_table_if_exists(connection, "checker_results", "checker_results__legacy")
        _rename_table_if_exists(connection, "checker_run_events", "checker_run_events__legacy")

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
        _copy_if_exists(
            connection,
            "job_logs__legacy",
            """
            INSERT INTO job_logs (log_id, job_id, timestamp, level, message)
            SELECT log_id, job_id, timestamp, level, message
            FROM job_logs__legacy
            """,
        )
        _copy_job_events_legacy(connection)
        _copy_checker_runs_legacy(connection)
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
        _copy_checker_run_events_legacy(connection)

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
        ("checker_results", "checker_results__legacy"),
        ("checker_run_events", "checker_run_events__legacy"),
        ("checker_runs", "checker_runs__legacy"),
    ):
        if _table_exists(connection, legacy_name) and _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


def _rename_table_if_exists(connection: sqlite3.Connection, table_name: str, legacy_name: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")


def _copy_if_exists(connection: sqlite3.Connection, table_name: str, sql: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(sql)


def _copy_jobs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "jobs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "jobs__legacy", "logical_run_id") else "job_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "jobs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "jobs__legacy", "request_json") else "payload_json"
    connection.execute(
        f"""
        INSERT INTO jobs (
            job_id, logical_run_id, attempt_number, project_id, phase, status, payload_json, request_json,
            current_phase, current_step, detail, progress_current, progress_total,
            heartbeat_at, error, created_at, updated_at
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
            current_phase,
            current_step,
            detail,
            progress_current,
            progress_total,
            heartbeat_at,
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


def _copy_checker_runs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_runs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "checker_runs__legacy", "logical_run_id") else "run_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "checker_runs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "checker_runs__legacy", "request_json") else "'{}'"
    connection.execute(
        f"""
        INSERT INTO checker_runs (
            run_id, logical_run_id, attempt_number, project_id, status, request_json, current_role, detail,
            heartbeat_at, report_path, created_at, updated_at
        )
        SELECT
            run_id,
            COALESCE({logical_run_expr}, run_id),
            COALESCE({attempt_expr}, 1),
            project_id,
            status,
            COALESCE({request_expr}, '{{}}'),
            current_role,
            detail,
            heartbeat_at,
            report_path,
            created_at,
            updated_at
        FROM checker_runs__legacy
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


def _drop_legacy_tables(connection: sqlite3.Connection) -> None:
    for table_name in (
        "project_artifacts__legacy",
        "projects__legacy",
        "job_logs__legacy",
        "job_events__legacy",
        "jobs__legacy",
        "checker_results__legacy",
        "checker_run_events__legacy",
        "checker_runs__legacy",
    ):
        if _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


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
