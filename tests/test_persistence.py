from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.persistence.sqlite import (
    OPERATIONS_DB_VERSION,
    PROJECT_DB_VERSION,
    connect,
    ensure_operations_db,
    ensure_project_db,
)
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleCheckResult, RoleModelCheckStartRequest
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
    events = reloaded.list_events(job.id)
    assert events[0]["event_type"] == "RUN_ACCEPTED"
    assert events[0]["to_state"] == "PENDING"
    assert events[-1]["event_type"] in {"RUN_PROGRESS_UPDATED", "RUN_STATE_CHANGED"}
    assert events[0]["payload"]["project_id"] == "science-fantasy-test"


def test_role_model_check_manager_persists_runs_and_results(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    request = RoleModelCheckStartRequest(
        roles=["architect", "critic"],
        model_selection={"architect": "qwen"},
        critic_profile="minimal_context",
        save_report=True,
    )
    run = manager.create_run(request)
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
    events = reloaded.list_events(run.run_id)
    assert events[0]["event_type"] == "RUN_ACCEPTED"
    assert events[0]["payload"]["roles"] == ["architect", "critic"]
    assert any(event["event_type"] == "STEP_RESULT_RECORDED" for event in events)


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
    reconciled = service.reconcile_projects()
    chapter = service.read_artifact(project_id, "chapter-1")
    detail = service.get_project(project_id)

    assert reconciled == 1
    assert chapter.content == "# Chapter 1"
    assert detail.chapter_exists is True
    assert (project_dir / "bible.db").exists()


def test_project_service_constructor_does_not_reconcile_projects_until_explicitly_requested(tmp_path: Path) -> None:
    root_dir = tmp_path
    project_id = "explicit-sync-project"
    project_dir = root_dir / "data" / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "manifest.json").write_text(
        json.dumps(
            {
                "project_id": project_id,
                "project_name": "Explicit Sync Project",
                "genre": "Mystery",
                "tone": "Taut",
                "story_structure": "THREE_ACT",
            }
        ),
        encoding="utf-8",
    )

    service = ProjectService(root_dir)

    assert service.list_projects() == []
    assert service.repository.get_project_projection(project_id) is None

    reconciled = service.reconcile_projects()

    assert reconciled == 1
    assert len(service.list_projects()) == 1
    assert service.repository.get_project_projection(project_id) is not None


def test_initialize_project_artifacts_creates_default_chapter_and_database(tmp_path: Path) -> None:
    paths = initialize_project_artifacts("project-x", root_dir=tmp_path)
    assert paths["chapter_1"].exists()
    assert paths["database"].exists()


def test_job_manager_rejects_illegal_terminal_transition(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    manager.update_job(job.id, status="PROCESSING")
    manager.update_job(job.id, status="COMPLETED")

    with pytest.raises(ValueError, match="Illegal job state transition"):
        manager.update_job(job.id, status="PROCESSING")


def test_job_manager_rejects_skipping_processing_state(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))

    with pytest.raises(ValueError, match="Illegal job state transition"):
        manager.update_job(job.id, status="COMPLETED")


def test_role_model_check_manager_rejects_illegal_terminal_transition(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    run = manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    manager.update_run(run.run_id, status="RUNNING")
    manager.update_run(run.run_id, status="COMPLETED")

    with pytest.raises(ValueError, match="Illegal checker run state transition"):
        manager.update_run(run.run_id, status="RUNNING")


def test_role_model_check_manager_rejects_result_recording_outside_running(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    run = manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    with pytest.raises(ValueError, match="Cannot record checker result"):
        manager.add_result(
            run.run_id,
            RoleCheckResult(
                role="architect",
                passed=True,
                duration_seconds=0.1,
                warnings=[],
                findings=[],
                preview="ok",
                metadata={},
            ),
        )


def test_operations_db_applies_pragmas_versions_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)

    with connect(db_path) as connection:
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        indexes = {
            row["name"]
            for row in connection.execute("PRAGMA index_list('jobs')").fetchall()
        }

    assert user_version == OPERATIONS_DB_VERSION
    assert foreign_keys == 1
    assert busy_timeout == 5000
    assert str(journal_mode).lower() == "wal"
    assert "idx_jobs_status_updated_at" in indexes
    assert "idx_jobs_project_status" in indexes


def test_project_db_applies_version_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "projects" / "demo" / "bible.db"
    ensure_project_db(db_path)

    with connect(db_path) as connection:
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        indexes = {
            row["name"]
            for row in connection.execute("PRAGMA index_list('artifacts')").fetchall()
        }

    assert user_version == PROJECT_DB_VERSION
    assert "idx_artifacts_updated_at" in indexes


def test_operations_db_enforces_foreign_keys_and_cascades(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={}))
    manager.log(job.id, "INFO", "entry")

    with connect(db_path) as connection:
        connection.execute("DELETE FROM jobs WHERE job_id = ?", (str(job.id),))
        connection.commit()
        log_rows = connection.execute(
            "SELECT COUNT(*) FROM job_logs WHERE job_id = ?",
            (str(job.id),),
        ).fetchone()[0]
        event_rows = connection.execute(
            "SELECT COUNT(*) FROM job_events WHERE job_id = ?",
            (str(job.id),),
        ).fetchone()[0]

    assert log_rows == 0
    assert event_rows == 0
