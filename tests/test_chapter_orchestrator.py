from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.chapter_orchestrator import ChapterOrchestrator, ChapterResult


class FakeJobManager:
    def __init__(self, outcomes: dict[str, str] | None = None):
        self._outcomes = outcomes or {}
        self.created_jobs: list[dict] = []

    def create_job(self, request):
        job_id = str(uuid4())
        self.created_jobs.append(
            {"id": job_id, "phase": request.phase, "payload": request.payload}
        )
        return type("Job", (), {"id": job_id})()

    def get_status(self, job_id):
        outcome = self._outcomes.get(job_id, "COMPLETED")
        return type("Status", (), {"status": outcome})()


def test_orchestrator_creates_sequential_jobs():
    manager = FakeJobManager()
    orch = ChapterOrchestrator(
        project_id="proj-1",
        chapter_ids=["ch-001", "ch-002", "ch-003"],
        job_manager=manager,
    )
    results = orch.run_all()

    assert len(results) == 3
    assert all(r.success for r in results)
    assert len(manager.created_jobs) == 3
    for i, job in enumerate(manager.created_jobs):
        assert job["payload"]["chapter_id"] == f"ch-00{i + 1}"


def test_orchestrator_handles_failed_chapter():
    manager = FakeJobManager()
    orch = ChapterOrchestrator(
        project_id="proj-1",
        chapter_ids=["ch-001", "ch-002"],
        job_manager=manager,
    )

    original_get = manager.get_status

    def failing_get(job_id):
        if len(manager.created_jobs) >= 2:
            return type("Status", (), {"status": "FAILED"})()
        return original_get(job_id)

    manager.get_status = failing_get

    results = orch.run_all()
    assert results[0].success is True
    assert results[1].success is False


def test_chapter_result_dataclass():
    result = ChapterResult(
        chapter_id="ch-001",
        success=True,
        output_path="/path/to/chapter.md",
    )
    assert result.chapter_id == "ch-001"
    assert result.success is True
    assert result.output_path == "/path/to/chapter.md"
    assert result.error is None
