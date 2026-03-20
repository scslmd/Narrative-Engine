from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import httpx
import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.inference.openai_compatible import OpenAICompatibleInferenceBackend
from app.schemas.inference import InferenceMessage, InferenceProviderDescriptor, InferenceRequest
from app.schemas.jobs import JobCreateRequest
from app.schemas.manifest import Manifest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService


class StructuredInferenceFailure(InferenceBackendError):
    pass


class FailingArchitectInferenceBackend(InferenceBackend):
    def __init__(self, failure: BaseException, *, model: str = "architect-fake-model") -> None:
        self._failure = failure
        self.requests: list[InferenceRequest] = []
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Failing Architect Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["failing-architect"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest):
        self.requests.append(request)
        raise self._failure


def _backend(*, timeout_seconds: float = 12.5) -> OpenAICompatibleInferenceBackend:
    return OpenAICompatibleInferenceBackend(
        backend="openai_compatible",
        display_name="Test Runtime",
        base_url="http://127.0.0.1:9000",
        api_key="secret-token",
        default_model="test-model",
        timeout_seconds=timeout_seconds,
    )


def _request() -> InferenceRequest:
    return InferenceRequest(
        model="override-model",
        messages=[InferenceMessage(role="user", content="Say hello.")],
        temperature=0.2,
        max_tokens=64,
    )


def _mapped_category(exc: BaseException) -> str | None:
    return getattr(exc, "error_category", getattr(exc, "category", None))


def _mapped_code(exc: BaseException) -> str | None:
    return getattr(exc, "error_code", getattr(exc, "code", None))


def _mapped_finish_reason(exc: BaseException) -> str | None:
    return getattr(exc, "finish_reason", None)


def _mapped_retryable(exc: BaseException) -> bool | None:
    return getattr(exc, "retryable", None)


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


def _run_failed_architect_job(
    tmp_path: Path,
    *,
    failure: StructuredInferenceFailure,
) -> tuple[JobManager, ProjectService, UUID]:
    project_id = "aurora-failure-test"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    backend = FailingArchitectInferenceBackend(failure)
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=backend)
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
    claimed = job_manager.claim_next_pending(worker_id="job-worker-local")
    assert claimed == job.id

    executor._process_job(job.id)

    return job_manager, project_service, job.id


def test_openai_compatible_adapter_maps_timeout_to_structured_runtime_error(monkeypatch) -> None:
    backend = _backend(timeout_seconds=7.0)

    def fake_request(method, url, *, headers, json, timeout):
        raise httpx.ReadTimeout("timed out", request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake_request)

    with pytest.raises(InferenceBackendError) as exc_info:
        backend.generate_text(_request())

    error = exc_info.value
    assert _mapped_category(error) == "timeout"
    assert _mapped_code(error) == "INFERENCE_TIMEOUT"
    assert _mapped_finish_reason(error) == "timeout"
    assert _mapped_retryable(error) is True


def test_openai_compatible_adapter_maps_retryable_http_failure_to_structured_runtime_error(monkeypatch) -> None:
    backend = _backend()

    class ErrorResponse:
        def raise_for_status(self) -> None:
            request = httpx.Request("GET", "http://127.0.0.1:9000/v1/models")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("503 Service Unavailable", request=request, response=response)

        def json(self) -> dict[str, object]:
            raise AssertionError("json() should not be called after raise_for_status().")

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: ErrorResponse())

    with pytest.raises(InferenceBackendError) as exc_info:
        backend.list_models()

    error = exc_info.value
    assert _mapped_category(error) == "http_status_failure"
    assert _mapped_code(error) == "HTTP_503"
    assert _mapped_finish_reason(error) == "provider_http_error"
    assert _mapped_retryable(error) is True


def test_openai_compatible_adapter_maps_invalid_json_to_structured_runtime_error(monkeypatch) -> None:
    backend = _backend()

    class InvalidJsonResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            raise json.JSONDecodeError("Expecting value", "not-json", 0)

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: InvalidJsonResponse())

    with pytest.raises(InferenceBackendError) as exc_info:
        backend.list_models()

    error = exc_info.value
    assert _mapped_category(error) == "invalid_json"
    assert _mapped_code(error) == "INVALID_JSON_RESPONSE"
    assert _mapped_finish_reason(error) == "invalid_response"
    assert _mapped_retryable(error) is True


def test_openai_compatible_adapter_maps_invalid_response_shape_to_structured_runtime_error(monkeypatch) -> None:
    backend = _backend()

    class InvalidShapeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": []}

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: InvalidShapeResponse())

    with pytest.raises(InferenceBackendError) as exc_info:
        backend.generate_text(_request())

    error = exc_info.value
    assert _mapped_category(error) == "protocol_shape_failure"
    assert _mapped_code(error) == "INVALID_RESPONSE_SHAPE"
    assert _mapped_finish_reason(error) == "invalid_response"
    assert _mapped_retryable(error) is False


@pytest.mark.parametrize(
    ("failure", "expected_finish_reason", "expected_category", "expected_code", "expected_retryable"),
    [
        (
            StructuredInferenceFailure(
                "timed out",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
            ),
            "timeout",
            "timeout",
            "INFERENCE_TIMEOUT",
            True,
        ),
        (
            StructuredInferenceFailure(
                "503 Service Unavailable",
                category="http_status_failure",
                code="HTTP_503",
                finish_reason="provider_http_error",
                retryable=True,
            ),
            "provider_http_error",
            "http_status_failure",
            "HTTP_503",
            True,
        ),
        (
            StructuredInferenceFailure(
                "invalid response shape",
                category="protocol_shape_failure",
                code="INVALID_RESPONSE_SHAPE",
                finish_reason="invalid_response",
                retryable=False,
            ),
            "invalid_response",
            "protocol_shape_failure",
            "INVALID_RESPONSE_SHAPE",
            False,
        ),
    ],
)
def test_p100_architect_failure_persists_mapped_runtime_failure_without_canonical_success(
    tmp_path: Path,
    *,
    failure: StructuredInferenceFailure,
    expected_finish_reason: str,
    expected_category: str,
    expected_code: str,
    expected_retryable: bool,
) -> None:
    job_manager, project_service, job_id = _run_failed_architect_job(tmp_path, failure=failure)

    status = job_manager.get_status(job_id)
    attempt = job_manager.get_attempt(job_id)
    steps = job_manager.list_step_records(job_id)
    lineage = job_manager.list_artifact_lineage(job_id)

    assert str(status.status) == "FAILED"
    assert attempt["status"] == "FAILED"
    assert attempt["failure_stage"] == "inference"
    assert attempt["finish_reason"] == expected_finish_reason
    assert bool(attempt["retryable"]) is expected_retryable
    assert attempt["error_code"] == expected_code
    assert attempt["error_category"] == expected_category

    assert len(steps) == 1
    assert steps[0]["step_name"] == "architect"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == expected_finish_reason
    assert steps[0]["error_code"] == expected_code
    assert steps[0]["error_category"] == expected_category

    assert lineage == []
    assert project_service.repository.get_artifact_path("aurora-failure-test", "architect_p100") is None
