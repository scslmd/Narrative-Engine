from __future__ import annotations

from ..settings import Settings
from .base import InferenceBackend
from .openai_compatible import OpenAICompatibleInferenceBackend
from .stub import StubInferenceBackend


def build_inference_backend(settings: Settings) -> InferenceBackend:
    backend = settings.inference_backend
    if backend == "stub":
        return StubInferenceBackend()

    display_name = {
        "llama.cpp": "llama.cpp Server",
        "lmstudio": "LM Studio",
        "vllm": "vLLM",
        "openai_compatible": "OpenAI-Compatible Runtime",
    }.get(backend, "OpenAI-Compatible Runtime")

    return OpenAICompatibleInferenceBackend(
        backend=backend,
        display_name=display_name,
        base_url=settings.inference_base_url,
        api_key=settings.inference_api_key,
        default_model=settings.inference_default_model,
        timeout_seconds=settings.inference_timeout_seconds,
        aliases=settings.inference_aliases,
    )
