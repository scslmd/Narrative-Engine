from __future__ import annotations

import json
from pathlib import Path
from time import sleep

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import build_jobs_router, build_projects_router
from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.sqlite import connect
from app.persistence.steps import stable_hash_payload
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.jobs import JobCreateRequest
from app.schemas.manifest import Manifest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.runtime_prompts import build_p200_sequencer_request, sequence_output_path
from app.services.step_records import StepRecordService

pytestmark = pytest.mark.integration


class FakeSequencerInferenceBackend(InferenceBackend):
    def __init__(self, *, content: str, model: str = "sequencer-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Sequencer Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-sequencer"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=131, completion_tokens=232, total_tokens=363),
            raw_response={"backend": "fake", "backend_version": "2026.04"},
        )


class FailingSequencerInferenceBackend(FakeSequencerInferenceBackend):
    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        raise InferenceBackendError(
            "Fake Sequencer Runtime request failed: timed out",
            category="timeout",
            code="INFERENCE_TIMEOUT",
            finish_reason="timeout",
            retryable=True,
        )


def _make_manifest(project_id: str) -> Manifest:
    return Manifest.model_validate(
        {
            "project_id": project_id,
            "project_name": "Project Aurora",
            "genre": "Science Fantasy",
            "tone": "Wonder-driven",
            "story_structure": "THREE_ACT",
            "constraints": ["No time travel", "Third-person limited only"],
            "premise_text": "A cartographer maps a city that rearranges itself every dusk.",
        }
    )


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


def _build_test_app(*, job_manager: JobManager, project_service: ProjectService) -> FastAPI:
    app = FastAPI()
    app.include_router(build_jobs_router(job_manager))
    app.include_router(build_projects_router(project_service))
    return app


def _wait_for_terminal_status(job_manager: JobManager, job_id, *, attempts: int = 40) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def test_local_executor_runs_real_sequencer_path_for_p200_with_fake_inferencer(tmp_path: Path) -> None:
    project_id = "sequencer-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    sequence_content = json.dumps(
        {
            "beats": [
                {"id": "beat-1", "title": "Opening", "depends_on": []},
                {"id": "beat-2", "title": "Turn", "depends_on": ["beat-1"]},
            ]
        },
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    inferencer = FakeSequencerInferenceBackend(content=sequence_content)
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()

    job = job_manager.create_job(
        JobCreateRequest(
            phase="P-200",
            payload={
                "project_id": project_id,
                "premise_text": "Override: the sequence must preserve causal dependencies.",
                "model_id": "sequencer-override-model",
            },
        )
    )
    request_payload = job_manager.get_request_payload(job.id)
    expected_request = build_p200_sequencer_request(
        manifest=manifest,
        payload=dict(request_payload.get("payload", {})),
        default_model=inferencer.descriptor.default_model,
    )
    output_path = sequence_output_path(Path(tmp_path) / "data" / "projects" / project_id)
    app = _build_test_app(job_manager=job_manager, project_service=project_service)

    executor.start()
    try:
        final_status = _wait_for_terminal_status(job_manager, job.id)
    finally:
        executor.stop()

    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{job.id}/steps")
        lineage_response = client.get(f"/jobs/{job.id}/lineage")
        sequence_response = client.get(f"/projects/{project_id}/sequence")

    assert final_status == "COMPLETED"
    assert len(inferencer.requests) == 1
    request = inferencer.requests[0]
    assert request.model == expected_request.model
    assert request.temperature == expected_request.temperature
    assert request.max_tokens == expected_request.max_tokens
    assert request.metadata == expected_request.metadata
    assert len(request.messages) == 2
    assert request.messages[0].role == "system"
    assert "Sequencer role for Narrative-Engine" in request.messages[0].content
    assert "P-200 sequence foundation" in request.messages[0].content
    assert request.messages[1].role == "user"
    assert "Build the P-200 sequencer foundation" in request.messages[1].content
    assert "Project Aurora" in request.messages[1].content
    assert "Override: the sequence must preserve causal dependencies." in request.messages[1].content
    assert request.metadata["phase"] == "P-200"
    assert request.metadata["role"] == "sequencer"
    assert request.metadata["project_id"] == project_id
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == sequence_content + "\n"

    assert len(steps) == 1
    assert steps[0]["step_name"] == "sequencer"
    assert steps[0]["state"] == "COMPLETED"
    assert steps[0]["model_id"] == "sequencer-override-model"
    assert steps[0]["backend_name"] == "Fake Sequencer Runtime"
    assert steps[0]["backend_version"] == "2026.04"
    assert steps[0]["input_artifact_refs"] == ["manifest"]
    assert steps[0]["output_artifact_refs"] == ["sequence"]
    assert steps[0]["finish_reason"] == "stop"
    assert steps[0]["prompt_hash"] == stable_hash_payload(request.model_dump(mode="json"))
    assert steps[0]["input_hash"] == stable_hash_payload(
        {
            "job_request": request_payload,
            "manifest": manifest.model_dump(mode="json"),
        }
    )
    assert steps[0]["output_hash"] == stable_hash_payload(
        {
            "backend": "openai_compatible",
            "model": "sequencer-override-model",
            "content": output_path.read_text(encoding="utf-8"),
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 131,
                "completion_tokens": 232,
                "total_tokens": 363,
            },
            "artifact_path": str(output_path),
        }
    )

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        telemetry_row = connection.execute(
            """
            SELECT prompt_tokens, completion_tokens, total_tokens
            FROM step_records
            WHERE run_id = ? AND step_name = 'sequencer'
            """,
            (str(job.id),),
        ).fetchone()

    assert telemetry_row is not None
    assert telemetry_row["prompt_tokens"] == 131
    assert telemetry_row["completion_tokens"] == 232
    assert telemetry_row["total_tokens"] == 363

    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "sequence"
    assert lineage[0]["artifact_kind"] == "json"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["registered_at"] is not None
    assert lineage[0]["path"] == str(output_path)

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["sequencer"]
    assert steps_response.json()["meta"]["ordered_by"] == "step_index_asc"
    assert lineage_response.status_code == 200
    assert [item["artifact_role"] for item in lineage_response.json()["items"]] == ["sequence"]
    assert lineage_response.json()["meta"]["ordered_by"] == "artifact_lineage_id_asc"
    assert sequence_response.status_code == 200
    assert sequence_response.json()["artifact_name"] == "sequence"
    assert sequence_response.json()["content"] == sequence_content + "\n"


def test_local_executor_persists_selected_upstream_artifacts_for_p200(tmp_path: Path) -> None:
    project_id = "sequencer-selection-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    inferencer = FakeSequencerInferenceBackend(
        content=json.dumps({"beats": [{"id": "beat-1", "title": "Opening"}]}, ensure_ascii=True, indent=2, sort_keys=True)
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()

    executor.start()
    try:
        p100 = job_manager.create_job(
            JobCreateRequest(phase="P-100", payload={"project_id": project_id, "model_id": "architect-override-model"})
        )
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = job_manager.create_job(
            JobCreateRequest(phase="P-200", payload={"project_id": project_id, "model_id": "sequencer-override-model"})
        )
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
    finally:
        executor.stop()

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        selection_rows = connection.execute(
            """
            SELECT artifact_role, selected_artifact_lineage_id, selected_content
            FROM runtime_artifact_selections
            WHERE run_id = ? AND run_kind = 'pipeline_job' AND step_name = 'sequencer'
            ORDER BY selection_id ASC
            """,
            (str(p200.id),),
        ).fetchall()

    assert len(selection_rows) == 1
    assert selection_rows[0]["artifact_role"] == "architect_output"
    assert selection_rows[0]["selected_artifact_lineage_id"] is not None
    assert selection_rows[0]["selected_content"] == project_service.read_artifact(project_id, "architect_p100").content
    sequence_artifact = project_service.read_artifact(project_id, "sequence")
    assert json.loads(sequence_artifact.content) == {"beats": [{"id": "beat-1", "title": "Opening"}]}
    assert project_service.repository.get_artifact_path(project_id, "sequence") == (
        tmp_path / "data" / "projects" / project_id / "sequences.json"
    )


def test_local_executor_persists_mapped_runtime_error_for_p200_failures(tmp_path: Path) -> None:
    project_id = "sequencer-timeout"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    inferencer = FailingSequencerInferenceBackend(content="unused")
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()

    job = job_manager.create_job(
        JobCreateRequest(
            phase="P-200",
            payload={
                "project_id": project_id,
                "model_id": "sequencer-override-model",
            },
        )
    )
    request_payload = job_manager.get_request_payload(job.id)
    output_path = sequence_output_path(Path(tmp_path) / "data" / "projects" / project_id)
    app = _build_test_app(job_manager=job_manager, project_service=project_service)

    executor.start()
    try:
        final_status = _wait_for_terminal_status(job_manager, job.id)
    finally:
        executor.stop()

    status = job_manager.get_status(job.id)
    attempt = job_manager.get_attempt(job.id)
    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{job.id}/steps")
        lineage_response = client.get(f"/jobs/{job.id}/lineage")
        sequence_response = client.get(f"/projects/{project_id}/sequence")

    assert final_status == "FAILED"
    assert status.error == "INFERENCE_TIMEOUT"
    assert status.current_step == "sequencer"
    assert attempt["finish_reason"] == "timeout"
    assert attempt["failure_stage"] == "inference"
    assert attempt["retryable"] == 1
    assert attempt["error_code"] == "INFERENCE_TIMEOUT"
    assert attempt["error_category"] == "timeout"
    assert len(inferencer.requests) == 1
    assert len(steps) == 1
    assert steps[0]["step_name"] == "sequencer"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "timeout"
    assert steps[0]["error_code"] == "INFERENCE_TIMEOUT"
    assert steps[0]["error_category"] == "timeout"
    assert steps[0]["prompt_hash"] is not None
    assert steps[0]["input_hash"] is not None
    assert steps[0]["output_hash"] is None
    assert steps[0]["input_artifact_refs"] == ["manifest"]
    assert lineage == []
    assert output_path.read_text(encoding="utf-8") == ""

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["sequencer"]
    assert steps_response.json()["items"][0]["state"] == "FAILED"
    assert lineage_response.status_code == 200
    assert lineage_response.json()["items"] == []
    assert sequence_response.status_code == 404
    assert sequence_response.json()["detail"] == "Artifact not found: sequence"
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "sequence")
