from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.manuscript_assist import build_manuscript_assist_router
from app.persistence.sqlite import connect
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.job_manager import JobManager


def _client(tmp_path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
    jobs = JobManager(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("proj-1", "Project 1", "manifest.json", "project.db", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()
    repo.upsert_manuscript_document(
        document_id="doc-1",
        project_id="proj-1",
        title="Chapter 1",
        content="Hello world",
        version=1,
    )
    app = FastAPI()
    app.include_router(build_manuscript_assist_router(repo, jobs))
    return TestClient(app), repo


def test_manuscript_assist_api_submit_and_list(tmp_path) -> None:
    client, _ = _client(tmp_path)
    payload = {
        "project_id": "proj-1",
        "document_id": "doc-1",
        "assist_kind": "line_edit_selection",
        "instruction": "Tighten this line",
        "text_range": {
            "start_offset": 0,
            "end_offset": 5,
            "selected_text": "Hello",
            "anchor_before": "",
            "anchor_after": " world",
        },
    }
    response = client.post("/v1/manuscript-assist/runs", json=payload)
    assert response.status_code == 202
    assist_id = response.json()["assist_id"]
    fetch = client.get(f"/v1/manuscript-assist/runs/{assist_id}")
    assert fetch.status_code == 200
    listed = client.get("/v1/manuscript-assist/runs", params={"project_id": "proj-1"})
    assert listed.status_code == 200
    assert listed.json()


def test_manuscript_assist_api_apply_409_conflict(tmp_path) -> None:
    client, repo = _client(tmp_path)
    repo.upsert_manuscript_assist_run(
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        assist_kind="line_edit_selection",
        request_json={},
        status="completed",
        request_hash="h",
    )
    repo.upsert_manuscript_assist_suggestion(
        suggestion_id="sug-1",
        assist_id="assist-1",
        project_id="proj-1",
        target_document_id="doc-1",
        suggestion_kind="line_edit_selection",
        source_text="Hello",
        proposed_text="Hi",
        rationale="Shorter",
        range_json={
            "start_offset": 0,
            "end_offset": 5,
            "selected_text": "Hello",
            "anchor_before": "",
            "anchor_after": " world",
        },
        status="PENDING",
    )
    response = client.post(
        "/v1/manuscript-assist/suggestions/sug-1/apply",
        json={
            "project_id": "proj-1",
            "document_id": "doc-1",
            "suggestion_id": "sug-1",
            "expected_document_version": 99,
            "apply_mode": "replace_range",
        },
    )
    assert response.status_code == 409
