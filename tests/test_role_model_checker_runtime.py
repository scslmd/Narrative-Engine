from __future__ import annotations

from pathlib import Path

from app.inference.base import InferenceBackend
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.role_model_checker import RoleModelCheckerService


class FakeRoleRuntime(InferenceBackend):
    def __init__(self, *, content_by_role: dict[str, str] | None = None) -> None:
        self.requests: list[InferenceRequest] = []
        self._content_by_role = content_by_role or {
            "architect": "Architect runtime verdict.",
            "sequencer": "Sequencer runtime verdict.",
            "drafter": "Drafter runtime verdict.",
            "critic": "Critic runtime verdict.",
        }
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Role Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model="role-runtime-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-role-runtime"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        role = str(request.metadata.get("role", "unknown"))
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content_by_role.get(role, f"{role.title()} runtime verdict."),
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=12, completion_tokens=18, total_tokens=30),
            raw_response={"provider": "fake-runtime"},
        )


class FailingRoleRuntime(FakeRoleRuntime):
    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        raise RuntimeError("simulated runtime failure")


def test_role_model_checker_runs_runtime_backed_roles_and_keeps_critic_profile_metadata(tmp_path: Path) -> None:
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        inferencer=FakeRoleRuntime(),
    )

    results = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["architect", "sequencer", "drafter", "critic"],
            model_selection={
                "architect": "architect-override-model",
                "sequencer": "sequencer-override-model",
                "drafter": "drafter-override-model",
                "critic": "critic-override-model",
            },
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    architect, sequencer, drafter, critic = results

    assert architect.role == "architect"
    assert architect.metadata["execution_mode"] == "runtime_backed"
    assert architect.metadata["execution_source"] == "generalized_inferencer"
    assert architect.metadata["selected_model"] == "architect-override-model"
    assert architect.metadata["runtime_response"]["model"] == "architect-override-model"
    assert architect.metadata["inference_request"]["metadata"]["mode"] == "role_model_check_runtime"
    assert architect.preview == "Architect runtime verdict."

    assert sequencer.role == "sequencer"
    assert sequencer.metadata["execution_mode"] == "runtime_backed"
    assert sequencer.metadata["execution_source"] == "generalized_inferencer"
    assert sequencer.metadata["selected_model"] == "sequencer-override-model"
    assert sequencer.metadata["runtime_response"]["model"] == "sequencer-override-model"
    assert sequencer.metadata["inference_request"]["metadata"]["role"] == "sequencer"
    assert sequencer.preview == "Sequencer runtime verdict."

    assert drafter.role == "drafter"
    assert drafter.metadata["execution_mode"] == "runtime_backed"
    assert drafter.metadata["execution_source"] == "generalized_inferencer"
    assert drafter.metadata["selected_model"] == "drafter-override-model"
    assert drafter.metadata["runtime_response"]["model"] == "drafter-override-model"
    assert drafter.metadata["inference_request"]["metadata"]["role"] == "drafter"
    assert drafter.preview == "Drafter runtime verdict."

    assert critic.role == "critic"
    assert critic.metadata["execution_mode"] == "runtime_backed"
    assert critic.metadata["execution_source"] == "generalized_inferencer"
    assert critic.metadata["selected_model"] == "critic-override-model"
    assert critic.metadata["critic_profile"] == "minimal_context"
    assert critic.metadata["runtime_response"]["model"] == "critic-override-model"
    assert critic.metadata["inference_request"]["metadata"]["role"] == "critic"
    assert critic.preview == "Critic runtime verdict."


def test_role_model_checker_keeps_stub_fallback_when_runtime_backend_is_unavailable(tmp_path: Path) -> None:
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
    )

    [sequencer] = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["sequencer"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    assert sequencer.metadata["execution_mode"] == "stub_fallback"
    assert sequencer.metadata["stub_reason"] == "runtime_backend_unavailable"
    assert sequencer.metadata["execution_source"] == "stub_checker"
    assert "using stub fallback" in sequencer.warnings[-1].lower()


def test_role_model_checker_keeps_stub_fallback_when_runtime_execution_errors(tmp_path: Path) -> None:
    runtime = FailingRoleRuntime()
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        inferencer=runtime,
    )

    [drafter] = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["drafter"],
            model_selection={"drafter": "drafter-override-model"},
            critic_profile="minimal_context",
            save_report=False,
        )
    )

    assert len(runtime.requests) == 1
    assert drafter.metadata["execution_mode"] == "stub_fallback"
    assert drafter.metadata["stub_reason"] == "runtime_execution_error"
    assert drafter.metadata["runtime_error"] == "simulated runtime failure"
    assert "runtime failed" in drafter.warnings[-1].lower()


def test_role_model_checker_critic_deterministic_only_uses_stub_fallback(tmp_path: Path) -> None:
    runtime = FakeRoleRuntime()
    service = RoleModelCheckerService(
        models_root=tmp_path / "models",
        reports_root=tmp_path / "reports",
        inferencer=runtime,
    )

    [critic] = service.run_checks(
        RoleModelCheckStartRequest(
            roles=["critic"],
            model_selection={"critic": "critic-override-model"},
            critic_profile="deterministic_only",
            save_report=False,
        )
    )

    assert runtime.requests == []
    assert critic.metadata["execution_mode"] == "stub_fallback"
    assert critic.metadata["stub_reason"] == "deterministic_only_profile"
    assert critic.metadata["critic_profile"] == "deterministic_only"
    assert critic.metadata["execution_source"] == "stub_checker"


def test_role_model_checker_falls_back_to_stub_when_runtime_backend_is_stub_backend(tmp_path: Path) -> None:
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
