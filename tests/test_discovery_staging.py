from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.persistence.sqlite import ensure_operations_db


def test_discovery_staging_table_created(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    conn = sqlite3.connect(str(db_path))
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='discovery_staging'"
    ).fetchall()
    conn.close()
    assert len(tables) == 1, "discovery_staging table should exist after ensure_operations_db"


def test_discovery_staging_insert_and_query(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert a project first (FK requirement)
    conn.execute(
        """INSERT OR IGNORE INTO projects
           (project_id, project_name, manifest_path, db_path, created_at, updated_at)
           VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))""",
        ("test-project-1", "Test Project", "/tmp/manifest.json", "/tmp/bible.db"),
    )
    conn.commit()

    # Insert a staging row
    conn.execute(
        """INSERT INTO discovery_staging
           (stage_id, project_id, entity_type, entity_id, entity_json, confidence, source_excerpt, source_chunk, approved, dedup_action, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("stage-1", "test-project-1", "character", "char-1", '{"name": "Alice"}', 0.85, "Alice walked in", 0, 1, "new", datetime.now().isoformat()),
    )
    conn.commit()

    # Query it back
    row = conn.execute(
        "SELECT stage_id, project_id, entity_type, entity_id, confidence, source_excerpt, source_chunk, approved, dedup_action FROM discovery_staging WHERE stage_id=? AND entity_id=?",
        ("stage-1", "char-1"),
    ).fetchone()
    conn.close()

    assert row is not None, "Row should be queryable"
    assert row[0] == "stage-1"
    assert row[1] == "test-project-1"
    assert row[2] == "character"
    assert row[3] == "char-1"
    assert row[4] == 0.85
    assert row[5] == "Alice walked in"
    assert row[6] == 0
    assert row[7] == 1
    assert row[8] == "new"
