from __future__ import annotations

import sqlite3
from pathlib import Path


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
    UNIQUE(project_id, artifact_type)
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    project_id TEXT,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    current_phase TEXT,
    current_step TEXT,
    detail TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    heartbeat_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checker_runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT,
    status TEXT NOT NULL,
    request_json TEXT NOT NULL DEFAULT '{}',
    current_role TEXT,
    detail TEXT,
    heartbeat_at TEXT,
    report_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
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
    metadata_json TEXT NOT NULL
);
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


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def ensure_operations_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        connection.executescript(OPERATIONS_SCHEMA)
        connection.commit()
    return db_path


def ensure_project_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        connection.executescript(PROJECT_SCHEMA)
        connection.commit()
    return db_path
