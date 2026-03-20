from __future__ import annotations

from pathlib import Path

from app.inference.base import InferenceBackend
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.role_model_checker import RoleModelCheckerService


class FakeArchitectRuntime(InferenceBackend):
    def __init__(self, *, content: str = "Architect runtime verdict.") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Architect Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model="architect-runtime-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-architect-runtime"],
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
            usage=InferenceUsage(prompt_tokens=12, completion_tokens=18, total_tokens=30),
            raw_response={"provider": "fake-runtime"},
        )


class FailingArchitectRuntime(FakeArchitectRuntime):
    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        raise RuntimeError("simulated architect runtime failure")


def test_role_model_checker_runs_architect_over_runtime_and_keeps_other_roles_stub(tmp_path: Path) -> None:
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        inferencer=FakeArchitectRuntime(),
    )

    results = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["architect", "sequencer", "critic"],
            model_selection={"architect": "architect-override-model"},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    architect, sequencer, critic = results

    assert architect.role == "architect"
    assert architect.metadata["execution_mode"] == "runtime_backed"
    assert architect.metadata["execution_source"] == "generalized_inferencer"
    assert architect.metadata["selected_model"] == "architect-override-model"
    assert architect.metadata["runtime_response"]["model"] == "architect-override-model"
    assert architect.metadata["inference_request"]["metadata"]["mode"] == "role_model_check_runtime"
    assert architect.preview == "Architect runtime verdict."

    assert sequencer.role == "sequencer"
    assert sequencer.metadata["execution_mode"] == "stub_fallback"
    assert sequencer.metadata["stub_reason"] == "role_not_runtime_backed"
    assert sequencer.metadata["execution_source"] == "stub_checker"

    assert critic.role == "critic"
    assert critic.metadata["execution_mode"] == "stub_fallback"
    assert critic.metadata["stub_reason"] == "role_not_runtime_backed"
    assert critic.metadata["critic_profile"] == "minimal_context"


def test_role_model_checker_falls_back_to_stub_when_architect_runtime_is_stub_backend(tmp_path: Path) -> None:
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
    )

    [architect] = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    assert architect.metadata["execution_mode"] == "stub_fallback"
    assert architect.metadata["stub_reason"] == "runtime_backend_unavailable"
    assert architect.metadata["execution_source"] == "stub_checker"
    assert "using stub fallback" in architect.warnings[-1].lower()
    assert architect.metadata["inference_request"]["metadata"]["mode"] == "role_model_check_runtime"


def test_role_model_checker_falls_back_to_stub_when_architect_runtime_errors(tmp_path: Path) -> None:
    runtime = FailingArchitectRuntime()
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        inferencer=runtime,
    )

    [architect] = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    assert len(runtime.requests) == 1
    assert architect.metadata["execution_mode"] == "stub_fallback"
    assert architect.metadata["stub_reason"] == "runtime_execution_error"
    assert architect.metadata["runtime_error"] == "simulated architect runtime failure"
    assert "runtime failed" in architect.warnings[-1].lower()
