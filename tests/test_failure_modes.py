from __future__ import annotations

import sqlite3
from time import sleep

import pytest
from fastapi.testclient import TestClient

from app.main import build_app
from app.persistence import sqlite as sqlite_module
from app.persistence.sqlite import connect
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.protocol import RetryNotAllowedError
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService


def _poll_json(client: TestClient, path: str, *, terminal_statuses: set[str], attempts: int = 12, delay_seconds: float = 0.2) -> dict:
    payload = {}
    for _ in range(attempts):
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in terminal_statuses:
            return payload
        sleep(delay_seconds)
    return payload


def test_duplicate_job_submissions_create_distinct_runs(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)

    first = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    second = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))

    assert first.id != second.id


def test_job_idempotency_key_replays_same_run_for_same_payload(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    request = JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"})

    first = manager.accept_job(request, idempotency_key="job-123")
    second = manager.accept_job(request, idempotency_key="job-123")

    assert first.status.id == second.status.id
    assert first.created_new is True
    assert second.created_new is False


def test_job_idempotency_key_rejects_different_payload(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)

    manager.accept_job(
        JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}),
        idempotency_key="job-123",
    )

    with pytest.raises(ValueError, match="already bound to a different job request"):
        manager.accept_job(
            JobCreateRequest(
                phase="P-100",
                payload={"project_id": "science-fantasy-test", "variant": "alternate"},
            ),
            idempotency_key="job-123",
        )


def test_duplicate_checker_submissions_create_distinct_runs(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    request = RoleModelCheckStartRequest(
        roles=["architect"],
        model_selection={},
        critic_profile="minimal_context",
        save_report=False,
    )

    first = manager.create_run(request)
    second = manager.create_run(request)

    assert first.run_id != second.run_id


def test_checker_idempotency_key_replays_same_run_for_same_payload(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    request = RoleModelCheckStartRequest(
        roles=["architect"],
        model_selection={},
        critic_profile="minimal_context",
        save_report=False,
    )

    first = manager.accept_run(request, idempotency_key="checker-123")
    second = manager.accept_run(request, idempotency_key="checker-123")

    assert first.status.run_id == second.status.run_id
    assert first.created_new is True
    assert second.created_new is False


def test_checker_idempotency_key_rejects_different_payload(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)

    manager.accept_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        ),
        idempotency_key="checker-123",
    )

    with pytest.raises(ValueError, match="already bound to a different checker request"):
        manager.accept_run(
            RoleModelCheckStartRequest(
                roles=["architect"],
                model_selection={"architect": "qwen2.5-32b-instruct-q4_k_m"},
                critic_profile="minimal_context",
                save_report=False,
            ),
            idempotency_key="checker-123",
        )


def test_job_start_endpoint_returns_accepted_and_completes_via_status_polling() -> None:
    with TestClient(build_app()) as client:
        response = client.post("/jobs/create", json={"phase": "P-100", "payload": {"project_id": "science-fantasy-test"}})

        assert response.status_code == 202
        payload = response.json()
        assert response.headers["Location"].endswith(f"/jobs/{payload['id']}/status")

        status_payload = _poll_json(client, response.headers["Location"], terminal_statuses={"COMPLETED", "FAILED"})
        assert status_payload["status"] == "COMPLETED"


def test_job_start_endpoint_replays_terminal_run_with_same_idempotency_key() -> None:
    with TestClient(build_app()) as client:
        first = client.post(
            "/jobs/create",
            headers={"Idempotency-Key": "job-api-123"},
            json={"phase": "P-100", "payload": {"project_id": "science-fantasy-test"}},
        )
        first_payload = first.json()
        status_payload = _poll_json(client, first.headers["Location"], terminal_statuses={"COMPLETED", "FAILED"})
        assert status_payload["status"] == "COMPLETED"

        second = client.post(
            "/jobs/create",
            headers={"Idempotency-Key": "job-api-123"},
            json={"phase": "P-100", "payload": {"project_id": "science-fantasy-test"}},
        )

        assert second.status_code == 200
        assert second.json()["id"] == first_payload["id"]


def test_job_start_endpoint_rejects_key_reuse_for_different_payload() -> None:
    with TestClient(build_app()) as client:
        client.post(
            "/jobs/create",
            headers={"Idempotency-Key": "job-api-456"},
            json={"phase": "P-100", "payload": {"project_id": "science-fantasy-test"}},
        )

        second = client.post(
            "/jobs/create",
            headers={"Idempotency-Key": "job-api-456"},
            json={
                "phase": "P-100",
                "payload": {"project_id": "science-fantasy-test", "variant": "alternate"},
            },
        )

        assert second.status_code == 409


def test_checker_start_endpoint_returns_accepted_and_completes_via_status_polling() -> None:
    with TestClient(build_app()) as client:
        response = client.post(
            "/role-model-checker/start",
            json={
                "roles": ["architect"],
                "model_selection": {},
                "critic_profile": "minimal_context",
                "save_report": False,
            },
        )

        assert response.status_code == 202
        payload = response.json()
        assert response.headers["Location"].endswith(f"/role-model-checker/{payload['run_id']}/status")

        status_payload = _poll_json(client, response.headers["Location"], terminal_statuses={"COMPLETED", "FAILED"})
        assert status_payload["status"] == "COMPLETED"


def test_checker_start_endpoint_replays_terminal_run_with_same_idempotency_key() -> None:
    with TestClient(build_app()) as client:
        first = client.post(
            "/role-model-checker/start",
            headers={"Idempotency-Key": "checker-api-123"},
            json={
                "roles": ["architect"],
                "model_selection": {},
                "critic_profile": "minimal_context",
                "save_report": False,
            },
        )
        first_payload = first.json()
        status_payload = _poll_json(client, first.headers["Location"], terminal_statuses={"COMPLETED", "FAILED"})
        assert status_payload["status"] == "COMPLETED"

        second = client.post(
            "/role-model-checker/start",
            headers={"Idempotency-Key": "checker-api-123"},
            json={
                "roles": ["architect"],
                "model_selection": {},
                "critic_profile": "minimal_context",
                "save_report": False,
            },
        )

        assert second.status_code == 200
        assert second.json()["run_id"] == first_payload["run_id"]


def test_checker_start_endpoint_rejects_key_reuse_for_different_payload() -> None:
    with TestClient(build_app()) as client:
        client.post(
            "/role-model-checker/start",
            headers={"Idempotency-Key": "checker-api-456"},
            json={
                "roles": ["architect"],
                "model_selection": {},
                "critic_profile": "minimal_context",
                "save_report": False,
            },
        )

        second = client.post(
            "/role-model-checker/start",
            headers={"Idempotency-Key": "checker-api-456"},
            json={
                "roles": ["architect"],
                "model_selection": {"architect": "qwen2.5-32b-instruct-q4_k_m"},
                "critic_profile": "minimal_context",
                "save_report": False,
            },
        )

        assert second.status_code == 409


def test_job_manager_rejects_terminal_reactivation(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={}))
    manager.update_job(job.id, status="PROCESSING")
    manager.update_job(job.id, status="COMPLETED")

    with pytest.raises(ValueError, match="Illegal job state transition"):
        manager.update_job(job.id, status="PROCESSING")


def test_checker_manager_rejects_terminal_reactivation(tmp_path) -> None:
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


def test_job_retry_requires_failed_state(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={}))

    with pytest.raises(RetryNotAllowedError, match="cannot be retried"):
        manager.retry_job(job.id)


def test_checker_retry_requires_failed_state(tmp_path) -> None:
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

    with pytest.raises(RetryNotAllowedError, match="cannot be retried"):
        manager.retry_run(run.run_id)


def test_checker_failure_after_result_persistence_keeps_provenance(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    job_manager = JobManager(db_path)
    check_manager = RoleModelCheckManager(db_path)
    check_service = RoleModelCheckerService(tmp_path / "models", tmp_path / "reports")
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=check_manager,
        role_check_service=check_service,
    )
    run = check_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    original_update_run = check_manager._runs.update_run
    failure_triggered = {"raised": False}

    def fail_after_result_insert(run_id, **kwargs):
        heartbeat_only = (
            kwargs.get("status") is None
            and kwargs.get("heartbeat_at") is not None
            and kwargs.get("updated_at") is not None
            and kwargs.get("current_role") is None
            and kwargs.get("detail") is None
            and kwargs.get("report_path") is None
            and kwargs.get("finish_reason") is None
            and kwargs.get("failure_stage") is None
            and kwargs.get("retryable") is None
        )
        if heartbeat_only and not failure_triggered["raised"]:
            failure_triggered["raised"] = True
            raise sqlite3.OperationalError("simulated heartbeat persistence failure")
        return original_update_run(run_id, **kwargs)

    monkeypatch.setattr(check_manager._runs, "update_run", fail_after_result_insert)

    executor._process_checker(run.run_id)

    status = check_manager.get_status(run.run_id)
    attempt = check_manager.get_attempt(run.run_id)
    events = check_manager.list_events(run.run_id)
    with connect(db_path) as connection:
        persisted_results = connection.execute(
            "SELECT COUNT(*) FROM checker_results WHERE run_id = ?",
            (str(run.run_id),),
        ).fetchone()[0]

    assert failure_triggered["raised"] is True
    assert status.status == "FAILED"
    assert status.report_path is None
    assert len(status.results) == 1
    assert status.results[0].role == "architect"
    assert check_manager.get_request_payload(run.run_id)["roles"] == ["architect"]
    assert persisted_results == 1
    assert attempt["finish_reason"] == "executor_error"
    assert attempt["failure_stage"] == "run"
    assert attempt["retryable"] == 0
    assert [event["event_type"] for event in events] == [
        "RUN_ACCEPTED",
        "RUN_STATE_CHANGED",
        "RUN_PROGRESS_UPDATED",
        "STEP_RESULT_RECORDED",
        "RUN_STATE_CHANGED",
    ]
    assert events[-1]["to_state"] == "FAILED"


def test_job_accept_under_sqlite_lock_leaves_no_partial_rows(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)
    monkeypatch.setattr(sqlite_module, "SQLITE_BUSY_TIMEOUT_MS", 25)

    lock_connection = sqlite3.connect(db_path, timeout=0, isolation_level=None)
    try:
        lock_connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            manager.accept_job(
                JobCreateRequest(
                    phase="P-100",
                    payload={"project_id": "science-fantasy-test"},
                )
            )
    finally:
        lock_connection.rollback()
        lock_connection.close()

    with connect(db_path) as connection:
        job_rows = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        event_rows = connection.execute("SELECT COUNT(*) FROM job_events").fetchone()[0]
        attempt_rows = connection.execute("SELECT COUNT(*) FROM job_attempts").fetchone()[0]

    assert job_rows == 0
    assert event_rows == 0
    assert attempt_rows == 0


def test_checker_accept_under_sqlite_lock_leaves_no_partial_rows(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)
    monkeypatch.setattr(sqlite_module, "SQLITE_BUSY_TIMEOUT_MS", 25)

    lock_connection = sqlite3.connect(db_path, timeout=0, isolation_level=None)
    try:
        lock_connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            manager.accept_run(
                RoleModelCheckStartRequest(
                    roles=["architect"],
                    model_selection={},
                    critic_profile="minimal_context",
                    save_report=False,
                )
            )
    finally:
        lock_connection.rollback()
        lock_connection.close()

    with connect(db_path) as connection:
        run_rows = connection.execute("SELECT COUNT(*) FROM checker_runs").fetchone()[0]
        event_rows = connection.execute("SELECT COUNT(*) FROM checker_run_events").fetchone()[0]
        attempt_rows = connection.execute("SELECT COUNT(*) FROM checker_run_attempts").fetchone()[0]

    assert run_rows == 0
    assert event_rows == 0
    assert attempt_rows == 0
