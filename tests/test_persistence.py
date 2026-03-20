from __future__ import annotations

import json
from pathlib import Path

from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleCheckResult
from app.services.job_manager import JobManager
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager


def test_job_manager_persists_status_and_logs(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    manager.update_job(job.id, status="PROCESSING", current_step="persisted")
    manager.log(job.id, "INFO", "persisted log entry")

    reloaded = JobManager(db_path)
    status = reloaded.get_status(job.id)
    logs = reloaded.get_logs(job.id)

    assert status.status == "PROCESSING"
    assert status.current_step == "persisted"
    assert len(logs.entries) == 1
    assert logs.entries[0].message == "persisted log entry"


def test_role_model_check_manager_persists_runs_and_results(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    run = manager.create_run()
    manager.update_run(run.run_id, status="RUNNING", current_role="architect", detail="Checking architect.")
    manager.add_result(
        run.run_id,
        RoleCheckResult(
            role="architect",
            passed=True,
            duration_seconds=0.25,
            warnings=[],
            findings=[],
            preview="ok",
            metadata={"selected_model": "qwen"},
        ),
    )

    reloaded = RoleModelCheckManager(db_path)
    status = reloaded.get_status(run.run_id)

    assert status.status == "RUNNING"
    assert status.current_role == "architect"
    assert len(status.results) == 1
    assert status.results[0].metadata["selected_model"] == "qwen"


def test_project_service_registers_existing_artifacts_and_normalizes_chapter_name(tmp_path: Path) -> None:
    root_dir = tmp_path
    project_id = "demo-project"
    project_dir = root_dir / "data" / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = project_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "project_id": project_id,
                "project_name": "Demo Project",
                "genre": "Fantasy",
                "tone": "Warm",
                "story_structure": "THREE_ACT",
                "premise_text": "Recovered premise.",
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "sequences.json").write_text("[]", encoding="utf-8")
    (project_dir / "chapter_001.md").write_text("# Chapter 1", encoding="utf-8")
    (project_dir / "telemetry.log").write_text("started", encoding="utf-8")
    (project_dir / "exports").mkdir(parents=True, exist_ok=True)

    service = ProjectService(root_dir)
    chapter = service.read_artifact(project_id, "chapter-1")
    detail = service.get_project(project_id)

    assert chapter.content == "# Chapter 1"
    assert detail.chapter_exists is True
    assert (project_dir / "bible.db").exists()


def test_initialize_project_artifacts_creates_default_chapter_and_database(tmp_path: Path) -> None:
    paths = initialize_project_artifacts("project-x", root_dir=tmp_path)
    assert paths["chapter_1"].exists()
    assert paths["database"].exists()
