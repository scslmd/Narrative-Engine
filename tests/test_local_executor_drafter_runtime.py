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
from app.services.step_records import StepRecordService

pytestmark = pytest.mark.integration


class FakePipelineInferenceBackend(InferenceBackend):
    def __init__(
        self,
        *,
        content_by_phase: dict[str, str],
        model: str = "pipeline-fake-model",
        failing_phases: set[str] | None = None,
    ) -> None:
        self.requests: list[InferenceRequest] = []
        self._content_by_phase = content_by_phase
        self._failing_phases = failing_phases or set()
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Pipeline Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-pipeline"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        phase = str(request.metadata.get("phase") or "unknown")
        if phase in self._failing_phases:
            raise InferenceBackendError(
                "Fake Pipeline Runtime request failed: timed out",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
            )
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content_by_phase.get(phase, f"{phase} runtime content."),
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=211, completion_tokens=322, total_tokens=533),
            raw_response={"backend": "fake", "backend_version": "2026.05"},
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


def _run_phase(job_manager: JobManager, *, phase: str, project_id: str, payload: dict[str, object] | None = None):
    job = job_manager.create_job(
        JobCreateRequest(
            phase=phase,
            payload={"project_id": project_id, **(payload or {})},
        )
    )
    return job


def test_local_executor_runs_real_drafter_path_for_p300_with_fake_inferencer(tmp_path: Path) -> None:
    project_id = "drafter-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    chapter_content = (
        "# Chapter 1\n"
        "The city changes shape just before dawn.\n\n"
        "## Opening\n"
        "A cartographer follows the first impossible street.\n"
    )
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps(
                {
                    "beats": [
                        {"id": "beat-1", "title": "Opening", "depends_on": []},
                        {"id": "beat-2", "title": "Turn", "depends_on": ["beat-1"]},
                    ]
                },
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            ),
            "P-300": chapter_content,
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    app = _build_test_app(job_manager=job_manager, project_service=project_service)
    output_path = tmp_path / "data" / "projects" / project_id / "chapter.md"

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id, payload={"model_id": "architect-override-model"})
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id, payload={"model_id": "sequencer-override-model"})
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"model_id": "drafter-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p300.id)
    finally:
        executor.stop()

    steps = job_manager.list_step_records(p300.id)
    lineage = job_manager.list_artifact_lineage(p300.id)
    request = inferencer.requests[-1]
    chapter_output = chapter_content.strip() + "\n"

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{p300.id}/steps")
        lineage_response = client.get(f"/jobs/{p300.id}/lineage")
        chapter_response = client.get(f"/projects/{project_id}/chapter-1")

    assert final_status == "COMPLETED"
    assert len(steps) == 1
    assert steps[0]["step_name"] == "drafter"
    assert steps[0]["state"] == "COMPLETED"
    assert steps[0]["model_id"] == "drafter-override-model"
    assert steps[0]["backend_name"] == "Fake Pipeline Runtime"
    assert steps[0]["backend_version"] == "2026.05"
    assert request.metadata["phase"] == "P-300"
    assert request.metadata["role"] == "drafter"
    assert steps[0]["input_artifact_refs"][0] == "manifest"
    assert "sequence" in steps[0]["input_artifact_refs"]
    assert steps[0]["output_artifact_refs"] == ["chapter_1"]
    assert steps[0]["finish_reason"] == "stop"
    assert steps[0]["prompt_hash"] == stable_hash_payload(request.model_dump(mode="json"))
    assert steps[0]["output_hash"] == stable_hash_payload(
        {
            "backend": "openai_compatible",
            "model": "drafter-override-model",
            "content": chapter_output,
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 211,
                "completion_tokens": 322,
                "total_tokens": 533,
            },
            "artifact_path": str(output_path),
        }
    )
    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        telemetry_row = connection.execute(
            """
            SELECT prompt_tokens, completion_tokens, total_tokens
            FROM step_records
            WHERE run_id = ? AND step_name = 'drafter'
            """,
            (str(p300.id),),
        ).fetchone()

    assert telemetry_row is not None
    assert telemetry_row["prompt_tokens"] == 211
    assert telemetry_row["completion_tokens"] == 322
    assert telemetry_row["total_tokens"] == 533
    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "chapter_1"
    assert lineage[0]["artifact_kind"] == "markdown"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["path"] == str(output_path)
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == chapter_output
    assert project_service.read_artifact(project_id, "chapter-1").content == chapter_output
    assert project_service.repository.get_artifact_path(project_id, "chapter_1") == output_path

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        selection_rows = connection.execute(
            """
            SELECT artifact_role, selected_artifact_lineage_id, selected_content
            FROM runtime_artifact_selections
            WHERE run_id = ? AND run_kind = 'pipeline_job' AND step_name = 'drafter'
            ORDER BY selection_id ASC
            """,
            (str(p300.id),),
        ).fetchall()

    assert [row["artifact_role"] for row in selection_rows] == ["sequence", "architect_output"]
    assert all(row["selected_artifact_lineage_id"] is not None for row in selection_rows)
    assert selection_rows[0]["selected_content"] == project_service.read_artifact(project_id, "sequence").content
    assert selection_rows[1]["selected_content"] == project_service.read_artifact(project_id, "architect_p100").content

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["drafter"]
    assert steps_response.json()["meta"]["ordered_by"] == "step_index_asc"
    assert lineage_response.status_code == 200
    assert [item["artifact_role"] for item in lineage_response.json()["items"]] == ["chapter_1"]
    assert lineage_response.json()["meta"]["ordered_by"] == "artifact_lineage_id_asc"
    assert chapter_response.status_code == 200
    assert chapter_response.json()["artifact_name"] == "chapter-1"
    assert chapter_response.json()["content"] == chapter_output


def test_local_executor_persists_mapped_runtime_error_for_p300_failures(tmp_path: Path) -> None:
    project_id = "drafter-timeout"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": []}, ensure_ascii=True),
            "P-300": "unused",
        },
        failing_phases={"P-300"},
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    app = _build_test_app(job_manager=job_manager, project_service=project_service)
    output_path = tmp_path / "data" / "projects" / project_id / "chapter.md"

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id, payload={"model_id": "architect-override-model"})
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id, payload={"model_id": "sequencer-override-model"})
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"model_id": "drafter-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p300.id)
    finally:
        executor.stop()

    status = job_manager.get_status(p300.id)
    steps = job_manager.list_step_records(p300.id)
    lineage = job_manager.list_artifact_lineage(p300.id)

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{p300.id}/steps")
        lineage_response = client.get(f"/jobs/{p300.id}/lineage")
        chapter_response = client.get(f"/projects/{project_id}/chapter-1")

    assert final_status == "FAILED"
    assert status.error == "INFERENCE_TIMEOUT"
    assert status.current_step == "drafter"
    assert len(steps) == 1
    assert steps[0]["step_name"] == "drafter"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "timeout"
    assert steps[0]["error_code"] == "INFERENCE_TIMEOUT"
    assert steps[0]["error_category"] == "timeout"
    assert steps[0]["output_hash"] is None
    assert lineage == []
    assert output_path.read_text(encoding="utf-8") == ""
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "chapter-1")

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["drafter"]
    assert steps_response.json()["items"][0]["state"] == "FAILED"
    assert lineage_response.status_code == 200
    assert lineage_response.json()["items"] == []
    assert chapter_response.status_code == 404
    assert chapter_response.json()["detail"] == "Artifact not found: chapter-1"
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "chapter-1")
