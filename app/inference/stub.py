from __future__ import annotations

from ..schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse
from .base import InferenceBackend


class StubInferenceBackend(InferenceBackend):
    def __init__(self) -> None:
        self._descriptor = InferenceProviderDescriptor(
            backend="stub",
            display_name="Stub Runtime",
            transport="stub",
            base_url=None,
            default_model=None,
            timeout_seconds=0.0,
            supports_model_listing=False,
            supports_chat_completions=False,
            aliases=["local-stub"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        role_hint = request.metadata.get("role") or "runtime"
        return InferenceResponse(
            backend="stub",
            model=request.model,
            content=f"Stub inference response for {role_hint}.",
            finish_reason="stub_completed",
            raw_response={"messages": [message.model_dump(mode="json") for message in request.messages]},
        )
