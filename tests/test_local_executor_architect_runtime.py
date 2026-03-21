from __future__ import annotations

from pathlib import Path
from time import sleep

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


class FakeArchitectInferenceBackend(InferenceBackend):
    def __init__(self, *, content: str, model: str = "architect-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Architect Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
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
            model=request.model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=101, completion_tokens=202, total_tokens=303),
            raw_response={"backend": "fake", "backend_version": "2026.03"},
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


def _wait_for_terminal_status(job_manager: JobManager, job_id, *, attempts: int = 40) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def test_local_executor_runs_real_architect_path_for_p100_with_fake_inferencer(tmp_path: Path) -> None:
    project_id = "aurora-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    executor_backend = FakeArchitectInferenceBackend(
        content=(
            "## Logline\n"
            "A mapmaker learns her city is alive.\n\n"
            "## Core Premise\n"
            "The city rearranges itself every dusk."
        )
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=executor_backend)
    project_service.reconcile_projects()

    job = job_manager.create_job(
        JobCreateRequest(
            phase="P-100",
            payload={
                "project_id": project_id,
                "premise_text": "Override: the city is sentient and testing its citizens.",
                "model_id": "architect-override-model",
            },
        )
    )
    executor.start()
    try:
        final_status = _wait_for_terminal_status(job_manager, job.id)
    finally:
        executor.stop()

    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)
    output_path = tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"

    assert final_status == "COMPLETED"
    assert len(executor_backend.requests) == 1
    request = executor_backend.requests[0]
    assert request.model == "architect-override-model"
    assert request.metadata["phase"] == "P-100"
    assert request.metadata["role"] == "architect"
    assert request.metadata["project_id"] == project_id
    assert "Project Aurora" in request.messages[1].content
    assert "Override: the city is sentient and testing its citizens." in request.messages[1].content

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith("## Logline")

    assert len(steps) == 1
    assert steps[0]["step_name"] == "architect"
    assert steps[0]["state"] == "COMPLETED"
    assert steps[0]["model_id"] == "architect-override-model"
    assert steps[0]["backend_name"] == "Fake Architect Runtime"
    assert steps[0]["backend_version"] == "2026.03"
    assert steps[0]["input_artifact_refs"] == ["manifest"]
    assert steps[0]["output_artifact_refs"] == ["architect_output"]
    assert steps[0]["finish_reason"] == "stop"
    assert steps[0]["prompt_hash"] == stable_hash_payload(request.model_dump(mode="json"))
    assert steps[0]["input_hash"] == stable_hash_payload(
        {
            "job_request": {
                "phase": "P-100",
                "payload": {
                    "project_id": project_id,
                    "premise_text": "Override: the city is sentient and testing its citizens.",
                    "model_id": "architect-override-model",
                },
            },
            "manifest": manifest.model_dump(mode="json"),
        }
    )
    assert steps[0]["output_hash"] == stable_hash_payload(
        {
            "backend": "openai_compatible",
            "model": "architect-override-model",
            "content": output_path.read_text(encoding="utf-8"),
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 101,
                "completion_tokens": 202,
                "total_tokens": 303,
            },
            "artifact_path": str(output_path),
        }
    )

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        telemetry_row = connection.execute(
            """
            SELECT prompt_tokens, completion_tokens, total_tokens
            FROM step_records
            WHERE run_id = ? AND step_name = 'architect'
            """,
            (str(job.id),),
        ).fetchone()

    assert telemetry_row is not None
    assert telemetry_row["prompt_tokens"] == 101
    assert telemetry_row["completion_tokens"] == 202
    assert telemetry_row["total_tokens"] == 303

    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "architect_output"
    assert lineage[0]["artifact_kind"] == "markdown"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["registered_at"] is not None
    assert lineage[0]["path"] == str(output_path)

    architect_artifact = project_service.read_artifact(project_id, "architect_p100")
    assert architect_artifact.content.startswith("## Logline")
    assert project_service.repository.get_artifact_path(project_id, "architect_p100") == output_path


def test_local_executor_runs_real_compiler_path_for_p400_instead_of_stub_completion(tmp_path: Path) -> None:
    project_id = "stub-phase-test"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    executor_backend = FakeArchitectInferenceBackend(content="unused")
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=executor_backend)
    project_service.reconcile_projects()

    job = job_manager.create_job(JobCreateRequest(phase="P-400", payload={"project_id": project_id}))
    executor.start()
    try:
        final_status = _wait_for_terminal_status(job_manager, job.id)
    finally:
        executor.stop()

    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)

    assert final_status == "COMPLETED"
    assert len(executor_backend.requests) == 1
    assert len(steps) == 1
    assert steps[0]["step_name"] == "compiler"
    assert steps[0]["state"] == "COMPLETED"
    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "story_bible"


def test_local_executor_persists_mapped_runtime_error_for_p100_failures(tmp_path: Path) -> None:
    class FailingArchitectInferenceBackend(FakeArchitectInferenceBackend):
        def generate_text(self, request: InferenceRequest) -> InferenceResponse:
            self.requests.append(request)
            raise InferenceBackendError(
                "Fake Architect Runtime request failed: timed out",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
            )

    project_id = "architect-timeout"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    executor_backend = FailingArchitectInferenceBackend(content="unused")
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=executor_backend)
    project_service.reconcile_projects()

    job = job_manager.create_job(
        JobCreateRequest(
            phase="P-100",
            payload={"project_id": project_id},
        )
    )
    executor.start()
    try:
        final_status = _wait_for_terminal_status(job_manager, job.id)
    finally:
        executor.stop()

    status = job_manager.get_status(job.id)
    attempt = job_manager.get_attempt(job.id)
    steps = job_manager.list_step_records(job.id)
    lineage = job_manager.list_artifact_lineage(job.id)
    output_path = tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"

    assert final_status == "FAILED"
    assert status.error == "INFERENCE_TIMEOUT"
    assert attempt["finish_reason"] == "timeout"
    assert attempt["failure_stage"] == "inference"
    assert attempt["retryable"] == 1
    assert attempt["error_code"] == "INFERENCE_TIMEOUT"
    assert attempt["error_category"] == "timeout"
    assert len(steps) == 1
    assert steps[0]["step_name"] == "architect"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "timeout"
    assert steps[0]["error_code"] == "INFERENCE_TIMEOUT"
    assert steps[0]["error_category"] == "timeout"
    assert steps[0]["prompt_hash"] is not None
    assert steps[0]["input_hash"] is not None
    assert steps[0]["output_hash"] is None
    assert lineage == []
    assert not output_path.exists()
