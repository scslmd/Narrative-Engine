from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.jobs import build_jobs_router
from app.api.role_model_checker import build_role_model_checker_router
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService
from app.persistence.steps import stable_hash_payload


def _build_test_app(*, job_manager: JobManager, checker_manager: RoleModelCheckManager, reports_root: Path) -> FastAPI:
    app = FastAPI()
    app.include_router(build_jobs_router(job_manager))
    app.include_router(
        build_role_model_checker_router(
            checker_manager,
            RoleModelCheckerService(reports_root.parent / "models", reports_root),
        )
    )
    return app


def test_job_steps_endpoint_returns_empty_items_for_existing_job_without_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    reports_root.mkdir(parents=True, exist_ok=True)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    app = _build_test_app(job_manager=job_manager, checker_manager=checker_manager, reports_root=reports_root)

    with TestClient(app) as client:
        response = client.get(f"/jobs/{job.id}/steps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == str(job.id)
    assert payload["items"] == []
    assert payload["meta"]["ordered_by"] == "step_index_asc"


def test_missing_projection_endpoints_return_404(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    reports_root.mkdir(parents=True, exist_ok=True)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    app = _build_test_app(job_manager=job_manager, checker_manager=checker_manager, reports_root=reports_root)
    missing_id = uuid4()

    with TestClient(app) as client:
        job_response = client.get(f"/jobs/{missing_id}/lineage")
        checker_response = client.get(f"/role-model-checker/{missing_id}/steps")

    assert job_response.status_code == 404
    assert checker_response.status_code == 404


def test_checker_lineage_and_steps_endpoints_return_persisted_rows_in_ascending_order(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    reports_root.mkdir(parents=True, exist_ok=True)
    job_manager = JobManager(db_path)
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
    attempt = checker_manager.get_attempt(run.run_id)
    now = datetime.now(timezone.utc)
    second_step_id = step_records.create_step_record(
        logical_run_id=str(attempt["logical_run_id"]),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=int(attempt["attempt_number"]),
        step_name="critic",
        step_index=2,
        state="COMPLETED",
        project_id=None,
        model_id="model-b",
        critic_profile="minimal_context",
        backend_name="test-runtime",
        backend_version="v1",
        input_hash=stable_hash_payload({"role": "critic"}) if {"role": "critic"} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"step": "critic"}) if {"step": "critic"} else None,
        input_artifact_refs=[],
        output_artifact_refs=["checker_result:critic"],
        started_at=now,
        finished_at=now,
        finish_reason="passed",
        error_code=None,
        error_category=None,
        executor_id="tester",
        lease_owner="tester",
    )
    first_step_id = step_records.create_step_record(
        logical_run_id=str(attempt["logical_run_id"]),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=int(attempt["attempt_number"]),
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id=None,
        model_id="model-a",
        critic_profile=None,
        backend_name="test-runtime",
        backend_version="v1",
        input_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"step": "architect"}) if {"step": "architect"} else None,
        input_artifact_refs=[],
        output_artifact_refs=["checker_result:architect"],
        started_at=now,
        finished_at=now,
        finish_reason="passed",
        error_code=None,
        error_category=None,
        executor_id="tester",
        lease_owner="tester",
    )
    step_records.create_lineage_record(
        logical_run_id=str(attempt["logical_run_id"]),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=int(attempt["attempt_number"]),
        step_name="architect",
        project_id=None,
        artifact_role="checker_result",
        artifact_kind="json",
        path="reports/a.json",
        content_hash="a",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=now,
        registered_at=now,
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=[],
        source_content_hashes=[],
        output_of_step_record_id=first_step_id,
    )
    step_records.create_lineage_record(
        logical_run_id=str(attempt["logical_run_id"]),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=int(attempt["attempt_number"]),
        step_name="critic",
        project_id=None,
        artifact_role="checker_result",
        artifact_kind="json",
        path="reports/b.json",
        content_hash="b",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=now,
        registered_at=now,
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=[],
        source_content_hashes=[],
        output_of_step_record_id=second_step_id,
    )
    app = _build_test_app(job_manager=job_manager, checker_manager=checker_manager, reports_root=reports_root)

    with TestClient(app) as client:
        steps_response = client.get(f"/role-model-checker/{run.run_id}/steps")
        lineage_response = client.get(f"/role-model-checker/{run.run_id}/lineage")

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["architect", "critic"]
    assert steps_response.json()["meta"]["ordered_by"] == "step_index_asc"
    assert lineage_response.status_code == 200
    assert [item["path"] for item in lineage_response.json()["items"]] == ["reports/a.json", "reports/b.json"]
    assert lineage_response.json()["meta"]["ordered_by"] == "artifact_lineage_id_asc"
