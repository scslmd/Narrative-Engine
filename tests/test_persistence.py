from __future__ import annotations

import json
from pathlib import Path
from time import sleep

import pytest

from app.inference.base import InferenceBackend
from app.persistence.sqlite import (
    OPERATIONS_DB_VERSION,
    PROJECT_DB_VERSION,
    connect,
    ensure_operations_db,
    ensure_project_db,
)
from app.persistence.steps import stable_hash_payload
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleCheckResult, RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService


class FakeArchitectInferencer(InferenceBackend):
    def __init__(self) -> None:
        self.requests: list[InferenceRequest] = []
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Architect Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9999/v1",
            default_model="architect-test-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-architect"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model or "architect-test-model",
            content="## Logline\nA test architect output.\n",
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=11, completion_tokens=22, total_tokens=33),
            raw_response={"provider": "fake", "backend_version": "2026.03"},
        )


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
    assert events[0]["payload"]["payload"]["project_id"] == "science-fantasy-test"
    assert reloaded.get_request_payload(job.id)["phase"] == "P-100"


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
                "premise_text": "Project premise.",
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
    assert "idx_jobs_scope_idempotency_key" in indexes


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


def test_job_retry_creates_new_attempt_and_preserves_prior_attempt_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    manager.update_job(
        job.id,
        status="FAILED",
        error="stub failure",
        finish_reason="executor_error",
        failure_stage="run",
        retryable=True,
    )

    retried = manager.retry_job(job.id, retry_reason="operator_retry")

    assert retried.id == job.id
    assert retried.status == "PENDING"
    assert retried.attempt_number == 2

    with connect(db_path) as connection:
        attempts = connection.execute(
            """
            SELECT attempt_number, status, retryable, retry_reason, finish_reason, failure_stage
            FROM job_attempts
            WHERE job_id = ?
            ORDER BY attempt_number ASC
            """,
            (str(job.id),),
        ).fetchall()

    assert len(attempts) == 2
    assert attempts[0]["attempt_number"] == 1
    assert attempts[0]["status"] == "FAILED"
    assert attempts[0]["retryable"] == 1
    assert attempts[0]["finish_reason"] == "executor_error"
    assert attempts[1]["attempt_number"] == 2
    assert attempts[1]["status"] == "PENDING"
    assert attempts[1]["retry_reason"] == "operator_retry"

    events = manager.list_events(job.id)
    assert events[-1]["event_type"] == "RUN_REQUEUED"
    assert events[-1]["attempt_number"] == 2


def test_checker_retry_creates_new_attempt_and_preserves_prior_attempt_metadata(tmp_path: Path) -> None:
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
    manager.update_run(
        run.run_id,
        status="FAILED",
        detail="stub failure",
        finish_reason="executor_error",
        failure_stage="run",
        retryable=True,
    )

    retried = manager.retry_run(run.run_id, retry_reason="operator_retry")

    assert retried.run_id == run.run_id
    assert retried.status == "PENDING"
    assert retried.attempt_number == 2

    with connect(db_path) as connection:
        attempts = connection.execute(
            """
            SELECT attempt_number, status, retryable, retry_reason, finish_reason, failure_stage
            FROM checker_run_attempts
            WHERE run_id = ?
            ORDER BY attempt_number ASC
            """,
            (str(run.run_id),),
        ).fetchall()

    assert len(attempts) == 2
    assert attempts[0]["attempt_number"] == 1
    assert attempts[0]["status"] == "FAILED"
    assert attempts[0]["retryable"] == 1
    assert attempts[0]["finish_reason"] == "executor_error"
    assert attempts[1]["attempt_number"] == 2
    assert attempts[1]["status"] == "PENDING"
    assert attempts[1]["retry_reason"] == "operator_retry"

    events = manager.list_events(run.run_id)
    assert events[-1]["event_type"] == "RUN_REQUEUED"
    assert events[-1]["attempt_number"] == 2


def test_job_claim_reuses_expired_lease_and_emits_reclaim_events(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))

    first_claim = manager.claim_next_pending(worker_id="worker-a", lease_seconds=0)
    second_claim = manager.claim_next_pending(worker_id="worker-b", lease_seconds=30)
    events = manager.list_events(job.id)
    attempt = manager.get_attempt(job.id)

    assert first_claim == job.id
    assert second_claim == job.id
    assert [event["event_type"] for event in events][-3:] == [
        "LEASE_EXPIRED",
        "RUN_REQUEUED",
        "RUN_CLAIMED",
    ]
    assert events[-3]["payload"]["retry_reason"] == "stale_lease_reclaimed"
    assert events[-2]["payload"]["retry_reason"] == "stale_lease_reclaimed"
    assert attempt["lease_owner"] == "worker-b"


def test_checker_claim_reuses_expired_lease_and_emits_reclaim_events(tmp_path: Path) -> None:
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

    first_claim = manager.claim_next_pending(worker_id="worker-a", lease_seconds=0)
    second_claim = manager.claim_next_pending(worker_id="worker-b", lease_seconds=30)
    events = manager.list_events(run.run_id)
    attempt = manager.get_attempt(run.run_id)

    assert first_claim == run.run_id
    assert second_claim == run.run_id
    assert [event["event_type"] for event in events][-3:] == [
        "LEASE_EXPIRED",
        "RUN_REQUEUED",
        "RUN_CLAIMED",
    ]
    assert events[-3]["payload"]["retry_reason"] == "stale_lease_reclaimed"
    assert events[-2]["payload"]["retry_reason"] == "stale_lease_reclaimed"
    assert attempt["lease_owner"] == "worker-b"


def test_job_claim_does_not_reclaim_live_lease(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))

    first_claim = manager.claim_next_pending(worker_id="worker-a", lease_seconds=30)
    second_claim = manager.claim_next_pending(worker_id="worker-b", lease_seconds=30)
    events = manager.list_events(job.id)

    assert first_claim == job.id
    assert second_claim is None
    assert [event["event_type"] for event in events] == ["RUN_ACCEPTED", "RUN_CLAIMED"]


def test_checker_claim_does_not_reclaim_live_lease(tmp_path: Path) -> None:
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

    first_claim = manager.claim_next_pending(worker_id="worker-a", lease_seconds=30)
    second_claim = manager.claim_next_pending(worker_id="worker-b", lease_seconds=30)
    events = manager.list_events(run.run_id)

    assert first_claim == run.run_id
    assert second_claim is None
    assert [event["event_type"] for event in events] == ["RUN_ACCEPTED", "RUN_CLAIMED"]


def test_job_attempt_records_executor_telemetry(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))

    claimed = manager.claim_next_pending(worker_id="worker-a", lease_seconds=30)
    manager.update_job(job.id, status="PROCESSING", detail="started")
    manager.update_job(job.id, status="COMPLETED", finish_reason="manual_complete")
    attempt = manager.get_attempt(job.id)
    events = manager.list_events(job.id)

    assert claimed == job.id
    assert attempt["executor_name"] == "local_executor"
    assert attempt["executor_instance_id"] == "worker-a"
    assert isinstance(attempt["queue_delay_ms"], int)
    assert attempt["finish_reason"] == "manual_complete"
    assert events[1]["payload"]["executor_name"] == "local_executor"
    assert events[1]["payload"]["executor_instance_id"] == "worker-a"
    assert isinstance(events[1]["payload"]["queue_delay_ms"], int)


def test_checker_attempt_records_executor_telemetry(tmp_path: Path) -> None:
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

    claimed = manager.claim_next_pending(worker_id="worker-a", lease_seconds=30)
    manager.update_run(run.run_id, status="RUNNING", detail="started")
    manager.update_run(run.run_id, status="COMPLETED", finish_reason="manual_complete")
    attempt = manager.get_attempt(run.run_id)
    events = manager.list_events(run.run_id)

    assert claimed == run.run_id
    assert attempt["executor_name"] == "local_executor"
    assert attempt["executor_instance_id"] == "worker-a"
    assert isinstance(attempt["queue_delay_ms"], int)
    assert attempt["finish_reason"] == "manual_complete"
    assert events[1]["payload"]["executor_name"] == "local_executor"
    assert events[1]["payload"]["executor_instance_id"] == "worker-a"
    assert isinstance(events[1]["payload"]["queue_delay_ms"], int)


def test_local_executor_persists_pipeline_step_records(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root),
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )

    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    executor.start()
    try:
        for _ in range(40):
            status = job_manager.get_status(job.id)
            if status.status in {"COMPLETED", "FAILED"}:
                break
            sleep(0.05)
    finally:
        executor.stop()

    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)

    assert len(steps) == 1
    assert steps[0]["run_kind"] == "pipeline_job"
    assert steps[0]["step_name"] == "architect"
    assert steps[0]["state"] == "COMPLETED"
    assert steps[0]["input_artifact_refs"] == ["manifest"]
    assert steps[0]["output_artifact_refs"] == ["architect_output"]
    assert steps[0]["executor_id"] == "job-worker-local"
    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "architect_output"
    assert lineage[0]["artifact_kind"] == "markdown"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["registered_at"] is not None
    assert lineage[0]["output_of_step_record_id"] == steps[0]["step_record_id"]


def test_local_executor_runs_real_p100_architect_call_with_inferencer(tmp_path: Path) -> None:
    root_dir = tmp_path
    project_id = "architect-demo"
    project_dir = root_dir / "data" / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "manifest.json").write_text(
        json.dumps(
            {
                "project_id": project_id,
                "project_name": "Architect Demo",
                "genre": "Science Fantasy",
                "tone": "Wonder with menace",
                "story_structure": "THREE_ACT",
                "premise_text": "A courier finds a living map to a dead star.",
            }
        ),
        encoding="utf-8",
    )
    (project_dir / "sequences.json").write_text("[]", encoding="utf-8")
    (project_dir / "chapter_001.md").write_text("# Chapter 1", encoding="utf-8")
    (project_dir / "telemetry.log").write_text("started", encoding="utf-8")
    (project_dir / "exports").mkdir(parents=True, exist_ok=True)

    project_service = ProjectService(root_dir)
    assert project_service.reconcile_projects() == 1

    db_path = root_dir / "data" / "state" / "narrative_ops.db"
    models_root = root_dir / "data" / "models"
    reports_root = root_dir / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    inferencer = FakeArchitectInferencer()
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=inferencer),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )

    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": project_id}))
    executor.start()
    try:
        for _ in range(40):
            status = job_manager.get_status(job.id)
            if status.status in {"COMPLETED", "FAILED"}:
                break
            sleep(0.05)
    finally:
        executor.stop()

    status = job_manager.get_status(job.id)
    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)
    output_path = project_dir / "exports" / "p100_architect_output.md"

    assert status.status == "COMPLETED"
    assert status.current_step == "architect"
    assert inferencer.requests
    assert inferencer.requests[0].metadata["phase"] == "P-100"
    assert inferencer.requests[0].metadata["role"] == "architect"
    assert output_path.exists()
    assert "A test architect output." in output_path.read_text(encoding="utf-8")
    assert steps[0]["model_id"] == "architect-test-model"
    assert steps[0]["backend_name"] == "Fake Architect Runtime"
    assert lineage[0]["path"] == str(output_path)
    assert lineage[0]["artifact_role"] == "architect_output"
    assert lineage[0]["status"] == "CANONICAL"
    assert project_service.read_artifact(project_id, "architect_p100").content.startswith("## Logline")
    assert project_service.repository.get_artifact_path(project_id, "architect_p100") == output_path


def test_local_executor_persists_checker_step_records_and_report_lineage(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)
    runtime_inferencer = FakeArchitectInferencer()
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=runtime_inferencer),
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )

    request = RoleModelCheckStartRequest(
        roles=["architect", "critic"],
        model_selection={},
        critic_profile="minimal_context",
        save_report=True,
    )
    run = checker_manager.create_run(request)
    executor.start()
    try:
        for _ in range(40):
            status = checker_manager.get_status(run.run_id)
            if status.status in {"COMPLETED", "FAILED"} and status.report_path:
                break
            sleep(0.05)
    finally:
        executor.stop()

    steps = checker_manager.list_step_records(run.run_id)
    lineage = checker_manager.list_artifact_lineage(run.run_id)
    runtime_request = runtime_inferencer.requests[0]
    final_status = checker_manager.get_status(run.run_id)
    architect_result = final_status.results[0]

    assert len(steps) == 3
    assert [step["step_name"] for step in steps] == ["architect", "critic", "report_persist"]
    assert steps[0]["run_kind"] == "role_model_check"
    assert steps[0]["backend_name"] == "openai_compatible"
    assert steps[0]["backend_version"] == "2026.03"
    assert steps[0]["model_id"] == "architect-test-model"
    assert steps[0]["finish_reason"] == "stop"
    assert steps[0]["prompt_hash"] == stable_hash_payload(runtime_request.model_dump(mode="json"))
    assert steps[0]["input_hash"] == stable_hash_payload(
        {
            "checker_request": request.model_dump(mode="json"),
            "runtime_request": runtime_request.model_dump(mode="json"),
        }
    )
    assert steps[0]["output_hash"] == stable_hash_payload(architect_result.model_dump(mode="json"))
    assert steps[-1]["output_artifact_refs"] == ["checker_report"]
    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "checker_report"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["output_of_step_record_id"] == steps[-1]["step_record_id"]

    with connect(db_path) as connection:
        telemetry_row = connection.execute(
            """
            SELECT prompt_tokens, completion_tokens, total_tokens
            FROM step_records
            WHERE run_id = ? AND run_kind = 'role_model_check' AND step_name = 'architect'
            """,
            (str(run.run_id),),
        ).fetchone()

    assert telemetry_row is not None
    assert telemetry_row["prompt_tokens"] == 11
    assert telemetry_row["completion_tokens"] == 22
    assert telemetry_row["total_tokens"] == 33
