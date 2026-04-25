from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_jobs_router, build_role_model_checker_router

pytestmark = pytest.mark.integration
from app.inference.base import InferenceBackend
from app.persistence import sqlite as sqlite_module
from app.persistence.sqlite import connect
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.jobs import JobCreateRequest
from app.schemas.manifest import Manifest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService
from app.persistence.steps import stable_hash_payload


def _utc(iso_value: str) -> datetime:
    return datetime.fromisoformat(iso_value).astimezone(timezone.utc)


class _FakeArchitectInferenceBackend(InferenceBackend):
    def __init__(self, *, content: str = "## Architect Output\nStable.") -> None:
        self._content = content
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Failure Test Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model="architect-failure-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["failure-test"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"backend": "failure-test"},
        )


def _make_manifest(project_id: str) -> Manifest:
    return Manifest.model_validate(
        {
            "project_id": project_id,
            "project_name": "Project Aurora",
            "genre": "Science Fantasy",
            "tone": "Wonder-driven",
            "story_structure": "THREE_ACT",
            "constraints": ["No time travel"],
            "premise_text": "A city reorders itself every dusk.",
        }
    )


def _build_projection_client(tmp_path: Path, *, raise_server_exceptions: bool = True) -> tuple[TestClient, JobManager, RoleModelCheckManager, StepRecordService]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "models"
    reports_root = tmp_path / "reports"
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    checker_service = RoleModelCheckerService(models_root=models_root, reports_root=reports_root)
    app = FastAPI()
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_role_model_checker_router(checker_manager, checker_service))
    return TestClient(app, raise_server_exceptions=raise_server_exceptions), job_manager, checker_manager, step_records


def _build_executor(tmp_path: Path, *, inferencer: InferenceBackend) -> tuple[LocalExecutor, JobManager, ProjectService]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    project_service = ProjectService(tmp_path)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=inferencer),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )
    return executor, job_manager, project_service


def _insert_job_step_and_lineage(step_records: StepRecordService, *, job_id: UUID) -> None:
    step_record_id = step_records.create_step_record(
        logical_run_id=str(job_id),
        run_id=job_id,
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id="science-fantasy-test",
        model_id="model-a",
        critic_profile=None,
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"manifest": True}) if {"manifest": True} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"phase": "P-100"}) if {"phase": "P-100"} else None,
        input_artifact_refs=["manifest"],
        output_artifact_refs=["architect_output"],
        started_at=_utc("2026-03-20T12:00:00+00:00"),
        finished_at=_utc("2026-03-20T12:00:03+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-a",
        lease_owner="worker-a",
    )
    step_records.create_lineage_record(
        logical_run_id=str(job_id),
        run_id=job_id,
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        project_id="science-fantasy-test",
        artifact_role="architect_output",
        artifact_kind="markdown",
        path="data/projects/science-fantasy-test/exports/p100_architect_output.md",
        content_hash="stable-output",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T12:00:03+00:00"),
        registered_at=_utc("2026-03-20T12:00:03+00:00"),
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=["manifest"],
        source_content_hashes=["manifest-hash"],
        output_of_step_record_id=step_record_id,
    )


def _insert_checker_step_and_lineage(step_records: StepRecordService, *, run_id: UUID) -> None:
    step_record_id = step_records.create_step_record(
        logical_run_id=str(run_id),
        run_id=run_id,
        run_kind="role_model_check",
        attempt_number=1,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id=None,
        model_id="model-a",
        critic_profile=None,
        backend_name="role-model-checker",
        backend_version="stub",
        input_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        output_hash=stable_hash_payload({"passed": True}) if {"passed": True} else None,
        prompt_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        input_artifact_refs=[],
        output_artifact_refs=["checker_report"],
        started_at=_utc("2026-03-20T12:10:00+00:00"),
        finished_at=_utc("2026-03-20T12:10:03+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-b",
        lease_owner="worker-b",
    )
    step_records.create_lineage_record(
        logical_run_id=str(run_id),
        run_id=run_id,
        run_kind="role_model_check",
        attempt_number=1,
        step_name="architect",
        project_id=None,
        artifact_role="checker_report",
        artifact_kind="json",
        path="data/role_model_checker_runs/report.json",
        content_hash="checker-report",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T12:10:03+00:00"),
        registered_at=_utc("2026-03-20T12:10:03+00:00"),
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=[],
        source_content_hashes=[],
        output_of_step_record_id=step_record_id,
    )


def _job_snapshot(db_path: Path, job_id: UUID) -> dict[str, object]:
    with connect(db_path) as connection:
        job_row = connection.execute(
            "SELECT status, updated_at FROM jobs WHERE job_id = ?",
            (str(job_id),),
        ).fetchone()
        return {
            "status": job_row["status"],
            "updated_at": job_row["updated_at"],
            "job_event_count": connection.execute("SELECT COUNT(*) FROM job_events WHERE job_id = ?", (str(job_id),)).fetchone()[0],
            "step_count": connection.execute(
                "SELECT COUNT(*) FROM step_records WHERE run_id = ? AND run_kind = 'pipeline_job'",
                (str(job_id),),
            ).fetchone()[0],
            "lineage_count": connection.execute(
                "SELECT COUNT(*) FROM artifact_lineage WHERE run_id = ? AND run_kind = 'pipeline_job'",
                (str(job_id),),
            ).fetchone()[0],
        }


def _checker_snapshot(db_path: Path, run_id: UUID) -> dict[str, object]:
    with connect(db_path) as connection:
        run_row = connection.execute(
            "SELECT status, updated_at FROM checker_runs WHERE run_id = ?",
            (str(run_id),),
        ).fetchone()
        return {
            "status": run_row["status"],
            "updated_at": run_row["updated_at"],
            "run_event_count": connection.execute(
                "SELECT COUNT(*) FROM checker_run_events WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()[0],
            "step_count": connection.execute(
                "SELECT COUNT(*) FROM step_records WHERE run_id = ? AND run_kind = 'role_model_check'",
                (str(run_id),),
            ).fetchone()[0],
            "lineage_count": connection.execute(
                "SELECT COUNT(*) FROM artifact_lineage WHERE run_id = ? AND run_kind = 'role_model_check'",
                (str(run_id),),
            ).fetchone()[0],
        }


@pytest.mark.parametrize(
    ("path_factory", "seed_run", "snapshot_factory", "failure_target"),
    [
        (
            lambda job_id, _run_id: f"/jobs/{job_id}/steps",
            lambda job_manager, _checker_manager, step_records: (
                (job := job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))).id,
                _insert_job_step_and_lineage(step_records, job_id=job.id),
                None,
            )[0],
            _job_snapshot,
            "job_steps",
        ),
        (
            lambda job_id, _run_id: f"/jobs/{job_id}/lineage",
            lambda job_manager, _checker_manager, step_records: (
                (job := job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))).id,
                _insert_job_step_and_lineage(step_records, job_id=job.id),
                None,
            )[0],
            _job_snapshot,
            "job_lineage",
        ),
        (
            lambda _job_id, run_id: f"/role-model-checker/{run_id}/steps",
            lambda _job_manager, checker_manager, step_records: (
                (
                    run := checker_manager.create_run(
                        RoleModelCheckStartRequest(
                            roles=["architect"],
                            model_selection={},
                            critic_profile="minimal_context",
                            save_report=False,
                        )
                    )
                ).run_id,
                _insert_checker_step_and_lineage(step_records, run_id=run.run_id),
                    None,
                )[0],
                _checker_snapshot,
                "checker_steps",
            ),
        (
            lambda _job_id, run_id: f"/role-model-checker/{run_id}/lineage",
            lambda _job_manager, checker_manager, step_records: (
                (
                    run := checker_manager.create_run(
                        RoleModelCheckStartRequest(
                            roles=["architect"],
                            model_selection={},
                            critic_profile="minimal_context",
                            save_report=False,
                        )
                    )
                ).run_id,
                _insert_checker_step_and_lineage(step_records, run_id=run.run_id),
                    None,
                )[0],
                _checker_snapshot,
                "checker_lineage",
            ),
        ],
)
def test_projection_endpoints_remain_read_only_when_projection_read_fails(
    tmp_path,
    monkeypatch,
    path_factory,
    seed_run,
    snapshot_factory,
    failure_target,
) -> None:
    client, job_manager, checker_manager, step_records = _build_projection_client(
        tmp_path,
        raise_server_exceptions=False,
    )
    run_id = seed_run(job_manager, checker_manager, step_records)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    if failure_target == "job_steps":
        monkeypatch.setattr(job_manager, "get_steps_projection", lambda job_id: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked")))
        path = path_factory(run_id, None)
    elif failure_target == "job_lineage":
        monkeypatch.setattr(job_manager, "get_lineage_projection", lambda job_id: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked")))
        path = path_factory(run_id, None)
    elif failure_target == "checker_steps":
        monkeypatch.setattr(checker_manager, "get_steps_projection", lambda run_id: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked")))
        path = path_factory(None, run_id)
    else:
        monkeypatch.setattr(checker_manager, "get_lineage_projection", lambda run_id: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked")))
        path = path_factory(None, run_id)
    before = snapshot_factory(db_path, run_id)
    response = client.get(path)
    assert response.status_code == 500

    after = snapshot_factory(db_path, run_id)
    assert after == before


def test_runtime_backed_p100_lineage_failure_does_not_emit_canonical_lineage_success(tmp_path, monkeypatch) -> None:
    project_id = "aurora-failure"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    executor, job_manager, project_service = _build_executor(
        tmp_path,
        inferencer=_FakeArchitectInferenceBackend(),
    )
    project_service.reconcile_projects()
    job = job_manager.create_job(
        JobCreateRequest(
            phase="P-100",
            payload={"project_id": project_id},
        )
    )

    def fail_lineage_registration(**kwargs):
        raise RuntimeError("simulated lineage registration failure")

    monkeypatch.setattr(executor._step_records, "create_lineage_record", fail_lineage_registration)

    executor._process_job(job.id)

    status = job_manager.get_status(job.id)
    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)
    output_path = tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"

    assert str(status.status) == "FAILED"
    assert status.error == "simulated lineage registration failure"
    assert not output_path.exists()
    assert lineage == []
    assert len(steps) == 1
    assert steps[0]["step_name"] == "architect"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "persistence_error"
    assert steps[0]["error_category"] == "persistence"
    assert project_service.repository.get_artifact_path(project_id, "architect_p100") is None
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "architect_p100")


def test_job_lineage_persistence_under_lock_leaves_job_state_non_corrupt(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    job_manager = JobManager(db_path)
    step_records = StepRecordService(db_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    job_manager.update_job(job.id, status="PROCESSING", current_step="architect")
    step_record_id = step_records.create_step_record(
        logical_run_id=str(job.id),
        run_id=job.id,
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id="science-fantasy-test",
        model_id="model-a",
        critic_profile=None,
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"manifest": True}) if {"manifest": True} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"phase": "P-100"}) if {"phase": "P-100"} else None,
        input_artifact_refs=["manifest"],
        output_artifact_refs=["architect_output"],
        started_at=_utc("2026-03-20T13:00:00+00:00"),
        finished_at=_utc("2026-03-20T13:00:01+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-a",
        lease_owner="worker-a",
    )
    before = _job_snapshot(db_path, job.id)
    monkeypatch.setattr(sqlite_module, "SQLITE_BUSY_TIMEOUT_MS", 25)

    lock_connection = sqlite3.connect(db_path, timeout=0, isolation_level=None)
    try:
        lock_connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            step_records.create_lineage_record(
                logical_run_id=str(job.id),
                run_id=job.id,
                run_kind="pipeline_job",
                attempt_number=1,
                step_name="architect",
                project_id="science-fantasy-test",
                artifact_role="architect_output",
                artifact_kind="markdown",
                path="data/projects/science-fantasy-test/exports/p100_architect_output.md",
                content_hash="locked-output",
                status="CANONICAL",
                validation_state="PASSED",
                produced_at=_utc("2026-03-20T13:00:01+00:00"),
                registered_at=_utc("2026-03-20T13:00:01+00:00"),
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=["manifest"],
                source_content_hashes=["manifest-hash"],
                output_of_step_record_id=step_record_id,
            )
    finally:
        lock_connection.rollback()
        lock_connection.close()

    after = _job_snapshot(db_path, job.id)
    assert after == before


def test_checker_lineage_persistence_under_lock_leaves_checker_state_non_corrupt(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    checker_manager.update_run(run.run_id, status="RUNNING", current_role="architect")
    step_record_id = step_records.create_step_record(
        logical_run_id=str(run.run_id),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=1,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id=None,
        model_id="model-a",
        critic_profile=None,
        backend_name="role-model-checker",
        backend_version="stub",
        input_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        output_hash=stable_hash_payload({"passed": True}) if {"passed": True} else None,
        prompt_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        input_artifact_refs=[],
        output_artifact_refs=["checker_report"],
        started_at=_utc("2026-03-20T13:10:00+00:00"),
        finished_at=_utc("2026-03-20T13:10:01+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-b",
        lease_owner="worker-b",
    )
    before = _checker_snapshot(db_path, run.run_id)
    monkeypatch.setattr(sqlite_module, "SQLITE_BUSY_TIMEOUT_MS", 25)

    lock_connection = sqlite3.connect(db_path, timeout=0, isolation_level=None)
    try:
        lock_connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            step_records.create_lineage_record(
                logical_run_id=str(run.run_id),
                run_id=run.run_id,
                run_kind="role_model_check",
                attempt_number=1,
                step_name="architect",
                project_id=None,
                artifact_role="checker_report",
                artifact_kind="json",
                path="data/role_model_checker_runs/report.json",
                content_hash="checker-report",
                status="CANONICAL",
                validation_state="PASSED",
                produced_at=_utc("2026-03-20T13:10:01+00:00"),
                registered_at=_utc("2026-03-20T13:10:01+00:00"),
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=[],
                source_content_hashes=[],
                output_of_step_record_id=step_record_id,
            )
    finally:
        lock_connection.rollback()
        lock_connection.close()

    after = _checker_snapshot(db_path, run.run_id)
    assert after == before
