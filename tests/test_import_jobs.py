from __future__ import annotations

import time

import pytest

from app.schemas.story_import import StoryImportResponse
from app.services.import_jobs import ImportJob, ImportJobManager


def test_create_and_get_job():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test-text")

    status = manager.get_status(job_id)
    assert status.import_id == job_id
    assert status.status == "pending"
    assert status.phase == ""
    assert status.chapters_processed == 0
    assert status.result is None


def test_get_nonexistent_job_raises():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    with pytest.raises(KeyError):
        manager.get_status("nonexistent-id")


def test_cleanup_removes_expired_completed_jobs():
    manager = ImportJobManager(max_workers=2, ttl_seconds=0)
    job_id = manager.submit("test")
    manager.complete(job_id, StoryImportResponse(project_id="p1", status="completed", message="ok"))
    time.sleep(0.05)  # ensure created_at is strictly in the past for ttl_seconds=0

    removed = manager.cleanup_expired()
    assert removed == 1

    with pytest.raises(KeyError):
        manager.get_status(job_id)


def test_cleanup_keeps_running_jobs():
    manager = ImportJobManager(max_workers=2, ttl_seconds=0)
    job_id = manager.submit("test")
    manager.update_progress(job_id, status="running", phase="analysis")

    removed = manager.cleanup_expired()
    assert removed == 0
    status = manager.get_status(job_id)
    assert status.status == "running"


def test_update_progress_sets_fields():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test")

    manager.update_progress(
        job_id,
        status="running",
        phase="chapter_analysis",
        chapters_processed=5,
        total_estimated_chapters=12,
        chunks_processed=9,
        total_estimated_chunks=15,
    )

    status = manager.get_status(job_id)
    assert status.status == "running"
    assert status.phase == "chapter_analysis"
    assert status.chapters_processed == 5
    assert status.total_estimated_chapters == 12
    assert status.chunks_processed == 9
    assert status.total_estimated_chunks == 15


def test_fail_sets_error_message():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)
    job_id = manager.submit("test")

    manager.fail(job_id, "LLM unavailable")

    status = manager.get_status(job_id)
    assert status.status == "failed"
    assert status.error == "LLM unavailable"


def test_worker_runs_function_and_updates_status():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)

    def my_worker(text: str, import_id: str):
        return StoryImportResponse(project_id="p1", status="completed", message="ok")

    job_id = manager.submit("test-text", my_worker, text="test-text")
    time.sleep(0.5)

    status = manager.get_status(job_id)
    assert status.status == "completed"
    assert status.result.status == "completed"

    manager.shutdown(wait=False)


def test_worker_catches_exception_and_marks_failed():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)

    def failing_worker(text: str, import_id: str):
        raise RuntimeError("boom")

    job_id = manager.submit("test-text", failing_worker, text="test-text")
    time.sleep(0.5)

    status = manager.get_status(job_id)
    assert status.status == "failed"
    assert "boom" in (status.error or "")

    manager.shutdown(wait=False)


def test_worker_propagates_failed_story_import_response():
    manager = ImportJobManager(max_workers=2, ttl_seconds=60)

    def failed_worker(text: str, import_id: str):
        return StoryImportResponse(project_id="p1", status="failed", message="invalid llm output")

    job_id = manager.submit("test-text", failed_worker, text="test-text")
    time.sleep(0.5)

    status = manager.get_status(job_id)
    assert status.status == "failed"
    assert status.result is not None
    assert status.result.status == "failed"
    assert status.error == "invalid llm output"

    manager.shutdown(wait=False)


# --- Endpoint tests ---

def test_import_story_returns_202_with_import_id(tmp_path):
    from app.main import build_app
    from fastapi.testclient import TestClient

    client = TestClient(build_app())

    response = client.post(
        "/projects/import-story",
        data={
            "story_text": "A" * 100,
            "project_name": "Test Project",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "import_id" in data
    assert data["status"] == "pending"


def test_import_story_rejects_short_text(tmp_path):
    from app.main import build_app
    from fastapi.testclient import TestClient

    client = TestClient(build_app())

    response = client.post(
        "/projects/import-story",
        data={
            "story_text": "too short",
            "project_name": "Test",
        },
    )
    assert response.status_code == 400


def test_get_import_status_returns_progress(tmp_path):
    from app.main import build_app
    from fastapi.testclient import TestClient

    client = TestClient(build_app())

    submit = client.post(
        "/projects/import-story",
        data={"story_text": "A" * 100, "project_name": "Test"},
    )
    import_id = submit.json()["import_id"]
    time.sleep(2)  # wait for worker to complete

    response = client.get(f"/projects/import/{import_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == import_id


def test_get_import_status_404_for_unknown_id(tmp_path):
    from app.main import build_app
    from fastapi.testclient import TestClient

    client = TestClient(build_app())

    response = client.get("/projects/import/nonexistent-id")
    assert response.status_code == 404
