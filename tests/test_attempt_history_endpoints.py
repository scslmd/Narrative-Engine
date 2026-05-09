from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_jobs_router, build_role_model_checker_router
from app.schemas.inspect import AttemptHistoryItem, JobAttemptHistoryResponse, RoleModelCheckAttemptHistoryResponse
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService

pytestmark = pytest.mark.integration


def _utc(iso_value: str) -> datetime:
    return datetime.fromisoformat(iso_value).astimezone(timezone.utc)


def _build_test_client(tmp_path) -> tuple[TestClient, JobManager, RoleModelCheckManager, StepRecordService]:
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
    return TestClient(app), job_manager, checker_manager, step_records


def _create_job_with_multiple_attempts(job_manager: JobManager):
    """Create a job and simulate multiple attempts through the retry mechanism."""
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    
    # First update the job to FAILED status so we can retry it
    job_manager.update_job(job.id, status="FAILED")
    
    # Retry to create second attempt
    job_manager.retry_job(job.id, retry_reason="manual_retry_1")
    
    # Update the second attempt to FAILED so we can retry again
    job_manager.update_job(job.id, status="FAILED")
    
    # Retry again to create third attempt
    job_manager.retry_job(job.id, retry_reason="manual_retry_2")
    
    return job


def _create_checker_with_multiple_attempts(checker_manager: RoleModelCheckManager):
    """Create a checker run and simulate multiple attempts through the retry mechanism."""
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    
    # First update the run to FAILED status so we can retry it
    checker_manager.update_run(run.run_id, status="FAILED")
    
    # Retry to create second attempt
    checker_manager.retry_run(run.run_id, retry_reason="manual_retry_1")
    
    return run


def test_job_attempts_endpoint_returns_all_attempts_in_order(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    job = _create_job_with_multiple_attempts(job_manager)
    
    response = client.get(f"/jobs/{job.id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    # Verify response structure
    assert set(payload.keys()) == {"job_id", "items", "meta"}
    assert payload["job_id"] == str(job.id)
    assert payload["meta"]["ordered_by"] == "attempt_number_asc"
    
    # Verify items count and ordering
    items = payload["items"]
    assert len(items) == 3
    assert [item["attempt_number"] for item in items] == [1, 2, 3]
    
    # Verify attempt history item structure
    for item in items:
        assert isinstance(item, dict)
        assert "attempt_number" in item
        assert "status" in item
        assert "executor_name" in item


def test_checker_attempts_endpoint_returns_all_attempts_in_order(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    run = _create_checker_with_multiple_attempts(checker_manager)
    
    response = client.get(f"/role-model-checker/{run.run_id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    # Verify response structure
    assert set(payload.keys()) == {"run_id", "items", "meta"}
    assert payload["run_id"] == str(run.run_id)
    assert payload["meta"]["ordered_by"] == "attempt_number_asc"
    
    # Verify items count and ordering
    items = payload["items"]
    assert len(items) == 2
    assert [item["attempt_number"] for item in items] == [1, 2]
    
    # Verify attempt history item structure
    for item in items:
        assert isinstance(item, dict)
        assert "attempt_number" in item
        assert "status" in item


def test_job_attempts_endpoint_returns_404_for_missing_job(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    
    response = client.get(f"/jobs/{uuid4()}/attempts")
    
    assert response.status_code == 404


def test_checker_attempts_endpoint_returns_404_for_missing_run(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    
    response = client.get(f"/role-model-checker/{uuid4()}/attempts")
    
    assert response.status_code == 404


def test_job_attempts_endpoint_empty_for_job_without_retries(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    
    response = client.get(f"/jobs/{job.id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    assert payload["job_id"] == str(job.id)
    assert len(payload["items"]) == 1  # Initial attempt
    assert payload["items"][0]["attempt_number"] == 1


def test_checker_attempts_endpoint_empty_for_run_without_retries(tmp_path) -> None:
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    
    response = client.get(f"/role-model-checker/{run.run_id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    assert payload["run_id"] == str(run.run_id)
    assert len(payload["items"]) == 1  # Initial attempt
    assert payload["items"][0]["attempt_number"] == 1


def test_job_attempts_schema_conformance(tmp_path) -> None:
    """Test that the response matches the expected schema."""
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    job = _create_job_with_multiple_attempts(job_manager)
    
    response = client.get(f"/jobs/{job.id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    # Validate against schema
    response_model = JobAttemptHistoryResponse(**payload)
    
    assert response_model.job_id == job.id
    assert len(response_model.items) == 3
    assert response_model.meta["ordered_by"] == "attempt_number_asc"
    
    # Verify each item matches the schema
    for item in response_model.items:
        assert isinstance(item, AttemptHistoryItem)
        assert item.attempt_number is not None
        assert item.status is not None


def test_checker_attempts_schema_conformance(tmp_path) -> None:
    """Test that the response matches the expected schema."""
    client, job_manager, checker_manager, step_records = _build_test_client(tmp_path)
    run = _create_checker_with_multiple_attempts(checker_manager)
    
    response = client.get(f"/role-model-checker/{run.run_id}/attempts")
    
    assert response.status_code == 200
    payload = response.json()
    
    # Validate against schema
    response_model = RoleModelCheckAttemptHistoryResponse(**payload)
    
    assert response_model.run_id == run.run_id
    assert len(response_model.items) == 2
    assert response_model.meta["ordered_by"] == "attempt_number_asc"
    
    # Verify each item matches the schema
    for item in response_model.items:
        assert isinstance(item, AttemptHistoryItem)
        assert item.attempt_number is not None
        assert item.status is not None
