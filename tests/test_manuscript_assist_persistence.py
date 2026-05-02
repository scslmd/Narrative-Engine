from __future__ import annotations

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository


def _seed_project(db_path) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("proj-1", "Project 1", "manifest.json", "project.db", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()


def test_manuscript_assist_tables_created(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        tables = {
            row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
    assert "manuscript_assist_runs" in tables
    assert "manuscript_assist_suggestions" in tables
    assert "manuscript_assist_gate_results" in tables


def test_manuscript_assist_repository_upserts(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
    _seed_project(db_path)
    repo.upsert_manuscript_document(
        document_id="doc-1",
        project_id="proj-1",
        title="Chapter 1",
        content="Hello world",
    )
    run = repo.upsert_manuscript_assist_run(
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        assist_kind="line_edit_selection",
        request_json={"assist_kind": "line_edit_selection"},
        status="queued",
        idempotency_key="idem-1",
        request_hash="hash-1",
    )
    assert run.assist_id == "assist-1"
    suggestion = repo.upsert_manuscript_assist_suggestion(
        suggestion_id="sug-1",
        assist_id="assist-1",
        project_id="proj-1",
        target_document_id="doc-1",
        suggestion_kind="line_edit_selection",
        source_text="Hello",
        proposed_text="Hi",
        rationale="Tighter",
        range_json={"start_offset": 0, "end_offset": 5, "selected_text": "Hello", "anchor_before": "", "anchor_after": " world"},
    )
    assert suggestion.suggestion_id == "sug-1"
    gate = repo.upsert_manuscript_assist_gate_result(
        gate_result_id="gate-1",
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        gate_name="canon_risk",
        passed=True,
        severity="info",
        reasons=[],
    )
    assert gate.gate_result_id == "gate-1"
    assert repo.list_manuscript_assist_suggestions("proj-1", "doc-1")
    assert repo.list_manuscript_assist_gate_results("assist-1")


def test_manuscript_assist_idempotency_conflict(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
    _seed_project(db_path)
    repo.upsert_manuscript_document(
        document_id="doc-1",
        project_id="proj-1",
        title="Chapter 1",
        content="Hello world",
    )
    repo.upsert_manuscript_assist_run(
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        assist_kind="line_edit_selection",
        request_json={},
        status="queued",
        idempotency_key="idem-1",
        request_hash="hash-1",
    )
    with pytest.raises(ValueError, match="idempotency key conflict"):
        repo.upsert_manuscript_assist_run(
            assist_id="assist-2",
            project_id="proj-1",
            document_id="doc-1",
            assist_kind="line_edit_selection",
            request_json={},
            status="queued",
            idempotency_key="idem-1",
            request_hash="hash-2",
        )
