from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import build_app
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleCheckResult, RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.role_model_check_manager import RoleModelCheckManager


def test_duplicate_job_creation_uses_distinct_ids(tmp_path: Path) -> None:
    manager = JobManager(tmp_path / "data" / "state" / "narrative_ops.db")
    request = JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"})

    first = manager.create_job(request)
    second = manager.create_job(request)

    assert first.id != second.id
    assert first.status == "PENDING"
    assert second.status == "PENDING"


def test_duplicate_checker_run_creation_uses_distinct_ids(tmp_path: Path) -> None:
    manager = RoleModelCheckManager(tmp_path / "data" / "state" / "narrative_ops.db")
    request = RoleModelCheckStartRequest(
        roles=["architect", "critic"],
        model_selection={"architect": "qwen"},
        critic_profile="minimal_context",
        save_report=False,
    )

    first = manager.create_run(request)
    second = manager.create_run(request)

    assert first.run_id != second.run_id
    assert first.status == "PENDING"
    assert second.status == "PENDING"


def test_job_manager_rejects_terminal_reactivation(tmp_path: Path) -> None:
    manager = JobManager(tmp_path / "data" / "state" / "narrative_ops.db")
    job = manager.create_job(JobCreateRequest(phase="P-100", payload={}))
    manager.update_job(job.id, status="PROCESSING")
    manager.update_job(job.id, status="COMPLETED")

    with pytest.raises(ValueError, match="Illegal job state transition"):
        manager.update_job(job.id, status="PROCESSING")


def test_role_model_check_manager_rejects_result_recording_outside_running(tmp_path: Path) -> None:
    manager = RoleModelCheckManager(tmp_path / "data" / "state" / "narrative_ops.db")
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


def test_jobs_create_returns_acceptance_and_status_polling_contract() -> None:
    client = TestClient(build_app())

    response = client.post("/jobs/create", json={"phase": "P-100", "payload": {"project_id": "science-fantasy-test"}})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert response.headers["Location"] == f"/jobs/{payload['id']}/status"

    status_response = client.get(f"/jobs/{payload['id']}/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["phase"] == "P-100"
    assert status_payload["status"] in {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}


def test_role_model_checker_start_returns_acceptance_and_status_polling_contract() -> None:
    client = TestClient(build_app())

    response = client.post(
        "/role-model-checker/start",
        json={
            "roles": ["architect", "critic"],
            "model_selection": {},
            "critic_profile": "minimal_context",
            "save_report": False,
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert response.headers["Location"] == f"/role-model-checker/{payload['run_id']}/status"

    status_response = client.get(f"/role-model-checker/{payload['run_id']}/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] in {"PENDING", "RUNNING", "COMPLETED", "FAILED"}
