from pathlib import Path

from fastapi.testclient import TestClient

from app.inference.base import InferenceBackend
from app.inference.factory import build_inference_backend
from app.inference.openai_compatible import OpenAICompatibleInferenceBackend
from app.main import build_app
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse
from app.services.model_registry import ModelRegistry
from app.settings import Settings


class FakeInferenceBackend(InferenceBackend):
    def __init__(self, models: list[str]) -> None:
        self._models = list(models)
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake OpenAI Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model="fake-model",
            timeout_seconds=30.0,
            supports_model_listing=True,
            supports_chat_completions=True,
            aliases=["fake"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def list_models(self) -> list[str]:
        return list(self._models)

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(backend="openai_compatible", model=request.model, content="ok")


def test_openai_compatible_backend_normalizes_base_url() -> None:
    backend = OpenAICompatibleInferenceBackend(
        backend="lmstudio",
        display_name="LM Studio",
        base_url="http://127.0.0.1:1234",
        api_key=None,
        default_model="local-model",
        timeout_seconds=60.0,
    )
    assert backend.descriptor.base_url == "http://127.0.0.1:1234/v1"


def test_build_inference_backend_uses_provider_defaults(monkeypatch) -> None:
    monkeypatch.setenv("NARRATIVE_INFERENCE_BACKEND", "llama.cpp")
    monkeypatch.delenv("NARRATIVE_INFERENCE_BASE_URL", raising=False)
    backend = build_inference_backend(Settings())
    assert backend.descriptor.backend == "llama.cpp"
    assert backend.descriptor.base_url == "http://127.0.0.1:8080/v1"
    assert backend.descriptor.transport == "openai_compatible_http"


def test_model_registry_merges_local_and_runtime_models(tmp_path: Path) -> None:
    models_root = tmp_path / "models"
    (models_root / "Qwen2.5-32B-Instruct-Q4_K_M.gguf").parent.mkdir(parents=True, exist_ok=True)
    (models_root / "Qwen2.5-32B-Instruct-Q4_K_M.gguf").write_text("placeholder", encoding="utf-8")
    registry = ModelRegistry(models_root, inferencer=FakeInferenceBackend(["remote-qwen", "remote-critic"]))

    catalog = registry.build_catalog()

    assert "Qwen2.5-32B-Instruct-Q4_K_M.gguf" in catalog.local_discovered_models
    assert catalog.runtime_discovered_models == ["remote-critic", "remote-qwen"]
    assert "remote-qwen" in catalog.discovered_models
    assert catalog.inference_provider.display_name == "Fake OpenAI Runtime"


def test_models_endpoint_reports_inference_provider() -> None:
    client = TestClient(build_app())
    response = client.get("/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["inference_provider"]["backend"] == "stub"
    assert payload["inference_provider"]["transport"] == "stub"
