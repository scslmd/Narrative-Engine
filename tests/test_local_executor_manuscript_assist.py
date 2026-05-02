from __future__ import annotations

from time import sleep

from app.persistence.sqlite import connect
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.jobs import JobCreateRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService


def _wait_for_terminal(job_manager: JobManager, job_id, attempts: int = 80) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def test_local_executor_runs_manuscript_assist_phase(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
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
    repo.upsert_manuscript_assist_run(
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        assist_kind="line_edit_selection",
        request_json={
            "project_id": "proj-1",
            "document_id": "doc-1",
            "assist_kind": "line_edit_selection",
            "instruction": "Tighten prose",
            "text_range": {
                "start_offset": 0,
                "end_offset": 5,
                "selected_text": "Hello",
                "anchor_before": "",
                "anchor_after": " world",
            },
        },
        status="queued",
        request_hash="h1",
    )
    jobs = JobManager(db_path)
    project_service = ProjectService(tmp_path)
    role_manager = RoleModelCheckManager(db_path)
    executor = LocalExecutor(
        job_manager=jobs,
        role_check_manager=role_manager,
        role_check_service=RoleModelCheckerService(tmp_path / "data" / "models", tmp_path / "data" / "role_model_checker_runs"),
        project_service=project_service,
        story_repository=repo,
        poll_interval_seconds=0.05,
    )
    job = jobs.create_job(
        JobCreateRequest(
            phase="M-500",
            payload={"project_id": "proj-1", "document_id": "doc-1", "assist_id": "assist-1"},
        )
    )
    executor.start()
    try:
        assert _wait_for_terminal(jobs, job.id) == "COMPLETED"
    finally:
        executor.stop()
