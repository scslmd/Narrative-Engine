from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_jobs_router, build_role_model_checker_router
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.persistence.steps import stable_hash_payload
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


def _assert_job_envelope(payload: dict, *, job_id: UUID, ordered_by: str) -> None:
    assert set(payload.keys()) == {"job_id", "items", "meta"}
    assert payload["job_id"] == str(job_id)
    assert isinstance(payload["items"], list)
    assert payload["meta"]["ordered_by"] == ordered_by


def _assert_run_envelope(payload: dict, *, run_id: UUID, ordered_by: str) -> None:
    assert set(payload.keys()) == {"run_id", "items", "meta"}
    assert payload["run_id"] == str(run_id)
    assert isinstance(payload["items"], list)
    assert payload["meta"]["ordered_by"] == ordered_by


def _insert_job_step_records(step_records: StepRecordService, *, job_id: UUID, attempt_number: int = 1) -> tuple[int, int]:
    logical_run_id = str(job_id)
    first_id = step_records.create_step_record(
        logical_run_id=logical_run_id,
        run_id=job_id,
        run_kind="pipeline_job",
        attempt_number=attempt_number,
        step_name="critic",
        step_index=2,
        state="COMPLETED",
        project_id="science-fantasy-test",
        model_id="model-b",
        critic_profile="minimal_context",
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"stage": "late"}) if {"stage": "late"} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"prompt": "late"}) if {"prompt": "late"} else None,
        input_artifact_refs=["sequence"],
        output_artifact_refs=["chapter_1"],
        started_at=_utc("2026-03-20T10:00:05+00:00"),
        finished_at=_utc("2026-03-20T10:00:09+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-a",
        lease_owner="worker-a",
    )
    second_id = step_records.create_step_record(
        logical_run_id=logical_run_id,
        run_id=job_id,
        run_kind="pipeline_job",
        attempt_number=attempt_number,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id="science-fantasy-test",
        model_id="model-a",
        critic_profile=None,
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"stage": "early"}) if {"stage": "early"} else None,
        output_hash=stable_hash_payload({"ok": True}) if {"ok": True} else None,
        prompt_hash=stable_hash_payload({"prompt": "early"}) if {"prompt": "early"} else None,
        input_artifact_refs=["manifest"],
        output_artifact_refs=["story_bible"],
        started_at=_utc("2026-03-20T10:00:00+00:00"),
        finished_at=_utc("2026-03-20T10:00:04+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-a",
        lease_owner="worker-a",
    )
    return first_id, second_id


def _insert_checker_step_records(step_records: StepRecordService, *, run_id: UUID, attempt_number: int = 1) -> tuple[int, int]:
    logical_run_id = str(run_id)
    first_id = step_records.create_step_record(
        logical_run_id=logical_run_id,
        run_id=run_id,
        run_kind="role_model_check",
        attempt_number=attempt_number,
        step_name="critic",
        step_index=2,
        state="FAILED",
        project_id="science-fantasy-test",
        model_id="model-b",
        critic_profile="minimal_context",
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"role": "critic"}) if {"role": "critic"} else None,
        output_hash=stable_hash_payload({"passed": False}) if {"passed": False} else None,
        prompt_hash=stable_hash_payload({"prompt": "critic"}) if {"prompt": "critic"} else None,
        input_artifact_refs=["story_bible", "chapter_1"],
        output_artifact_refs=["checker_report"],
        started_at=_utc("2026-03-20T11:00:05+00:00"),
        finished_at=_utc("2026-03-20T11:00:09+00:00"),
        finish_reason="validation_failed",
        error_code="CHECKER_FAILED",
        error_category="deterministic_validation",
        executor_id="worker-b",
        lease_owner="worker-b",
    )
    second_id = step_records.create_step_record(
        logical_run_id=logical_run_id,
        run_id=run_id,
        run_kind="role_model_check",
        attempt_number=attempt_number,
        step_name="architect",
        step_index=1,
        state="COMPLETED",
        project_id="science-fantasy-test",
        model_id="model-a",
        critic_profile=None,
        backend_name="openai_compatible",
        backend_version="test",
        input_hash=stable_hash_payload({"role": "architect"}) if {"role": "architect"} else None,
        output_hash=stable_hash_payload({"passed": True}) if {"passed": True} else None,
        prompt_hash=stable_hash_payload({"prompt": "architect"}) if {"prompt": "architect"} else None,
        input_artifact_refs=["manifest"],
        output_artifact_refs=["checker_report"],
        started_at=_utc("2026-03-20T11:00:00+00:00"),
        finished_at=_utc("2026-03-20T11:00:04+00:00"),
        finish_reason="success",
        error_code=None,
        error_category=None,
        executor_id="worker-b",
        lease_owner="worker-b",
    )
    return first_id, second_id


def _insert_job_lineage(step_records: StepRecordService, *, job_id: UUID, step_record_id: int, attempt_number: int = 1) -> int:
    return step_records.create_lineage_record(
        logical_run_id=str(job_id),
        run_id=job_id,
        run_kind="pipeline_job",
        attempt_number=attempt_number,
        step_name="architect",
        project_id="science-fantasy-test",
        artifact_role="story_bible",
        artifact_kind="json",
        path="data/projects/science-fantasy-test/story_bible.json",
        content_hash="story-bible-v1",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T10:00:03+00:00"),
        registered_at=_utc("2026-03-20T10:00:04+00:00"),
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=["manifest"],
        source_content_hashes=["manifest-hash"],
        output_of_step_record_id=step_record_id,
    )


def _insert_checker_lineage(step_records: StepRecordService, *, run_id: UUID, step_record_id: int, attempt_number: int = 1) -> int:
    return step_records.create_lineage_record(
        logical_run_id=str(run_id),
        run_id=run_id,
        run_kind="role_model_check",
        attempt_number=attempt_number,
        step_name="critic",
        project_id="science-fantasy-test",
        artifact_role="checker_report",
        artifact_kind="json",
        path="data/role_model_checker_runs/report.json",
        content_hash="checker-report-v1",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T11:00:08+00:00"),
        registered_at=_utc("2026-03-20T11:00:09+00:00"),
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=["story_bible", "chapter_1"],
        source_content_hashes=["story-bible-hash", "chapter-hash"],
        output_of_step_record_id=step_record_id,
    )


def test_job_steps_endpoint_returns_persisted_rows_in_ascending_order(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    _insert_job_step_records(step_records, job_id=job.id)

    response = client.get(f"/jobs/{job.id}/steps")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="step_index_asc")
    assert [item["step_index"] for item in payload["items"]] == [1, 2]
    assert [item["step_name"] for item in payload["items"]] == ["architect", "critic"]
    assert all(item["run_kind"] == "pipeline_job" for item in payload["items"])
    assert all(set(item.keys()) == {
        "step_record_id",
        "logical_run_id",
        "run_id",
        "run_kind",
        "attempt_number",
        "step_name",
        "step_index",
        "state",
        "project_id",
        "model_id",
        "critic_profile",
        "backend_name",
        "backend_version",
        "input_hash",
        "output_hash",
        "prompt_hash",
        "input_artifact_refs",
        "output_artifact_refs",
        "started_at",
        "finished_at",
        "duration_seconds",
        "finish_reason",
        "error_code",
        "error_category",
        "executor_id",
        "lease_owner",
    } for item in payload["items"])


def test_job_lineage_endpoint_returns_persisted_rows_in_ascending_order(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    first_step_id, second_step_id = _insert_job_step_records(step_records, job_id=job.id)
    second_lineage_id = _insert_job_lineage(step_records, job_id=job.id, step_record_id=second_step_id)
    step_records.create_lineage_record(
        logical_run_id=str(job.id),
        run_id=job.id,
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="critic",
        project_id="science-fantasy-test",
        artifact_role="chapter_1",
        artifact_kind="markdown",
        path="data/projects/science-fantasy-test/chapter_001.md",
        content_hash="chapter-v1",
        status="CANDIDATE",
        validation_state="PENDING",
        produced_at=_utc("2026-03-20T10:00:07+00:00"),
        registered_at=None,
        supersedes_artifact_lineage_id=second_lineage_id,
        source_artifact_refs=["sequence"],
        source_content_hashes=["sequence-hash"],
        output_of_step_record_id=first_step_id,
    )

    response = client.get(f"/jobs/{job.id}/lineage")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="artifact_lineage_id_asc")
    assert [item["artifact_lineage_id"] for item in payload["items"]] == sorted(
        item["artifact_lineage_id"] for item in payload["items"]
    )
    assert payload["items"][0]["artifact_role"] == "story_bible"
    assert all(set(item.keys()) == {
        "artifact_lineage_id",
        "logical_run_id",
        "run_id",
        "run_kind",
        "attempt_number",
        "step_name",
        "project_id",
        "artifact_role",
        "artifact_kind",
        "path",
        "content_hash",
        "status",
        "validation_state",
        "produced_at",
        "registered_at",
        "supersedes_artifact_lineage_id",
        "source_artifact_refs",
        "source_content_hashes",
        "output_of_step_record_id",
    } for item in payload["items"])


def test_checker_steps_endpoint_returns_persisted_rows_in_ascending_order(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect", "critic"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    _insert_checker_step_records(step_records, run_id=run.run_id)

    response = client.get(f"/role-model-checker/{run.run_id}/steps")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="step_index_asc")
    assert [item["step_index"] for item in payload["items"]] == [1, 2]
    assert [item["step_name"] for item in payload["items"]] == ["architect", "critic"]
    assert all(item["run_kind"] == "role_model_check" for item in payload["items"])


def test_checker_lineage_endpoint_returns_persisted_rows_in_ascending_order(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    first_step_id, second_step_id = _insert_checker_step_records(step_records, run_id=run.run_id)
    first_lineage_id = _insert_checker_lineage(step_records, run_id=run.run_id, step_record_id=first_step_id)
    step_records.create_lineage_record(
        logical_run_id=str(run.run_id),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=1,
        step_name="architect",
        project_id="science-fantasy-test",
        artifact_role="checker_report",
        artifact_kind="json",
        path="data/role_model_checker_runs/report_v2.json",
        content_hash="checker-report-v2",
        status="SUPERSEDED",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T11:00:10+00:00"),
        registered_at=_utc("2026-03-20T11:00:11+00:00"),
        supersedes_artifact_lineage_id=first_lineage_id,
        source_artifact_refs=["story_bible"],
        source_content_hashes=["story-bible-hash"],
        output_of_step_record_id=second_step_id,
    )

    response = client.get(f"/role-model-checker/{run.run_id}/lineage")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="artifact_lineage_id_asc")
    assert [item["artifact_lineage_id"] for item in payload["items"]] == sorted(
        item["artifact_lineage_id"] for item in payload["items"]
    )
    assert all(item["run_kind"] == "role_model_check" for item in payload["items"])


@pytest.mark.parametrize(
    ("path_template", "create_run"),
    [
        ("/jobs/{run_id}/steps", lambda job_manager, _checker_manager: job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"})).id),
        ("/jobs/{run_id}/lineage", lambda job_manager, _checker_manager: job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"})).id),
        ("/role-model-checker/{run_id}/steps", lambda _job_manager, checker_manager: checker_manager.create_run(RoleModelCheckStartRequest(roles=["architect"], model_selection={}, critic_profile="minimal_context", save_report=False)).run_id),
        ("/role-model-checker/{run_id}/lineage", lambda _job_manager, checker_manager: checker_manager.create_run(RoleModelCheckStartRequest(roles=["architect"], model_selection={}, critic_profile="minimal_context", save_report=False)).run_id),
    ],
)
def test_projection_endpoints_return_empty_items_for_existing_runs_without_rows(tmp_path, path_template, create_run) -> None:
    client, job_manager, checker_manager, _step_records = _build_test_client(tmp_path)
    run_id = create_run(job_manager, checker_manager)

    response = client.get(path_template.format(run_id=run_id))

    assert response.status_code == 200
    payload = response.json()
    if path_template.startswith("/jobs/"):
        _assert_job_envelope(
            payload,
            job_id=run_id,
            ordered_by="step_index_asc" if path_template.endswith("/steps") else "artifact_lineage_id_asc",
        )
    else:
        _assert_run_envelope(
            payload,
            run_id=run_id,
            ordered_by="step_index_asc" if path_template.endswith("/steps") else "artifact_lineage_id_asc",
        )
    assert payload["items"] == []


@pytest.mark.parametrize(
    "path",
    [
        "/jobs/{id}/steps",
        "/jobs/{id}/lineage",
        "/role-model-checker/{id}/steps",
        "/role-model-checker/{id}/lineage",
    ],
)
def test_projection_endpoints_return_404_for_missing_run_ids(tmp_path, path) -> None:
    client, _, _, _ = _build_test_client(tmp_path)

    response = client.get(path.format(id=uuid4()))

    assert response.status_code == 404


def test_job_steps_endpoint_supports_attempt_filter(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    _insert_job_step_records(step_records, job_id=job.id, attempt_number=1)
    _insert_job_step_records(step_records, job_id=job.id, attempt_number=2)

    response = client.get(f"/jobs/{job.id}/steps?attempt=2")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="step_index_asc")
    assert payload["meta"]["attempt_number"] == 2
    assert [item["attempt_number"] for item in payload["items"]] == [2, 2]
    assert [item["step_name"] for item in payload["items"]] == ["architect", "critic"]


def test_job_lineage_endpoint_supports_attempt_filter(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    _, second_step_attempt_one = _insert_job_step_records(step_records, job_id=job.id, attempt_number=1)
    _, second_step_attempt_two = _insert_job_step_records(step_records, job_id=job.id, attempt_number=2)
    _insert_job_lineage(step_records, job_id=job.id, step_record_id=second_step_attempt_one, attempt_number=1)
    _insert_job_lineage(step_records, job_id=job.id, step_record_id=second_step_attempt_two, attempt_number=2)

    response = client.get(f"/jobs/{job.id}/lineage?attempt=2")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="artifact_lineage_id_asc")
    assert payload["meta"]["attempt_number"] == 2
    assert [item["attempt_number"] for item in payload["items"]] == [2]
    assert [item["artifact_role"] for item in payload["items"]] == ["story_bible"]


def test_job_steps_endpoint_supports_limit_and_offset_pagination(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    _insert_job_step_records(step_records, job_id=job.id)

    response = client.get(f"/jobs/{job.id}/steps?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="step_index_asc")
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["offset"] == 1
    assert payload["meta"]["returned_count"] == 1
    assert [item["step_name"] for item in payload["items"]] == ["critic"]


def test_job_lineage_endpoint_supports_limit_and_offset_pagination(tmp_path) -> None:
    client, job_manager, _, step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    first_step_id, second_step_id = _insert_job_step_records(step_records, job_id=job.id)
    second_lineage_id = _insert_job_lineage(step_records, job_id=job.id, step_record_id=second_step_id)
    step_records.create_lineage_record(
        logical_run_id=str(job.id),
        run_id=job.id,
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="critic",
        project_id="science-fantasy-test",
        artifact_role="chapter_1",
        artifact_kind="markdown",
        path="data/projects/science-fantasy-test/chapter_001.md",
        content_hash="chapter-v1",
        status="CANDIDATE",
        validation_state="PENDING",
        produced_at=_utc("2026-03-20T10:00:07+00:00"),
        registered_at=None,
        supersedes_artifact_lineage_id=second_lineage_id,
        source_artifact_refs=["sequence"],
        source_content_hashes=["sequence-hash"],
        output_of_step_record_id=first_step_id,
    )

    response = client.get(f"/jobs/{job.id}/lineage?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    _assert_job_envelope(payload, job_id=job.id, ordered_by="artifact_lineage_id_asc")
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["offset"] == 1
    assert payload["meta"]["returned_count"] == 1
    assert [item["artifact_role"] for item in payload["items"]] == ["chapter_1"]


def test_checker_steps_endpoint_supports_attempt_filter(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect", "critic"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    _insert_checker_step_records(step_records, run_id=run.run_id, attempt_number=1)
    _insert_checker_step_records(step_records, run_id=run.run_id, attempt_number=2)

    response = client.get(f"/role-model-checker/{run.run_id}/steps?attempt=2")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="step_index_asc")
    assert payload["meta"]["attempt_number"] == 2
    assert [item["attempt_number"] for item in payload["items"]] == [2, 2]
    assert [item["step_name"] for item in payload["items"]] == ["architect", "critic"]


def test_checker_lineage_endpoint_supports_attempt_filter(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    first_step_attempt_one, _ = _insert_checker_step_records(step_records, run_id=run.run_id, attempt_number=1)
    first_step_attempt_two, _ = _insert_checker_step_records(step_records, run_id=run.run_id, attempt_number=2)
    _insert_checker_lineage(step_records, run_id=run.run_id, step_record_id=first_step_attempt_one, attempt_number=1)
    _insert_checker_lineage(step_records, run_id=run.run_id, step_record_id=first_step_attempt_two, attempt_number=2)

    response = client.get(f"/role-model-checker/{run.run_id}/lineage?attempt=2")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="artifact_lineage_id_asc")
    assert payload["meta"]["attempt_number"] == 2
    assert [item["attempt_number"] for item in payload["items"]] == [2]
    assert [item["artifact_role"] for item in payload["items"]] == ["checker_report"]


def test_checker_steps_endpoint_supports_limit_and_offset_pagination(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect", "critic"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    _insert_checker_step_records(step_records, run_id=run.run_id)

    response = client.get(f"/role-model-checker/{run.run_id}/steps?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="step_index_asc")
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["offset"] == 1
    assert payload["meta"]["returned_count"] == 1
    assert [item["step_name"] for item in payload["items"]] == ["critic"]


def test_checker_lineage_endpoint_supports_limit_and_offset_pagination(tmp_path) -> None:
    client, _, checker_manager, step_records = _build_test_client(tmp_path)
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    first_step_id, second_step_id = _insert_checker_step_records(step_records, run_id=run.run_id)
    first_lineage_id = _insert_checker_lineage(step_records, run_id=run.run_id, step_record_id=first_step_id)
    step_records.create_lineage_record(
        logical_run_id=str(run.run_id),
        run_id=run.run_id,
        run_kind="role_model_check",
        attempt_number=1,
        step_name="architect",
        project_id="science-fantasy-test",
        artifact_role="checker_report",
        artifact_kind="json",
        path="data/role_model_checker_runs/report_v2.json",
        content_hash="checker-report-v2",
        status="SUPERSEDED",
        validation_state="PASSED",
        produced_at=_utc("2026-03-20T11:00:10+00:00"),
        registered_at=_utc("2026-03-20T11:00:11+00:00"),
        supersedes_artifact_lineage_id=first_lineage_id,
        source_artifact_refs=["story_bible"],
        source_content_hashes=["story-bible-hash"],
        output_of_step_record_id=second_step_id,
    )

    response = client.get(f"/role-model-checker/{run.run_id}/lineage?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    _assert_run_envelope(payload, run_id=run.run_id, ordered_by="artifact_lineage_id_asc")
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["offset"] == 1
    assert payload["meta"]["returned_count"] == 1
    assert [item["path"] for item in payload["items"]] == ["data/role_model_checker_runs/report_v2.json"]


@pytest.mark.parametrize(
    "path_template",
    [
        "/jobs/{id}/steps?attempt=0",
        "/jobs/{id}/lineage?attempt=0",
        "/role-model-checker/{id}/steps?attempt=0",
        "/role-model-checker/{id}/lineage?attempt=0",
        "/jobs/{id}/steps?limit=0",
        "/jobs/{id}/lineage?limit=0",
        "/role-model-checker/{id}/steps?limit=0",
        "/role-model-checker/{id}/lineage?limit=0",
        "/jobs/{id}/steps?offset=-1",
        "/jobs/{id}/lineage?offset=-1",
        "/role-model-checker/{id}/steps?offset=-1",
        "/role-model-checker/{id}/lineage?offset=-1",
    ],
)
def test_projection_endpoints_reject_non_positive_attempt_filter(tmp_path, path_template) -> None:
    client, job_manager, checker_manager, _step_records = _build_test_client(tmp_path)
    job = job_manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    run = checker_manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    identifier = job.id if path_template.startswith("/jobs/") else run.run_id

    response = client.get(path_template.format(id=identifier))

    assert response.status_code == 422
