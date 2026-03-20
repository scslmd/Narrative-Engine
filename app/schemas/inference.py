from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import StrictModel


InferenceBackend = Literal["stub", "llama.cpp", "lmstudio", "vllm", "openai_compatible"]
InferenceTransport = Literal["stub", "openai_compatible_http"]


class InferenceProviderDescriptor(StrictModel):
    backend: InferenceBackend
    display_name: str
    transport: InferenceTransport
    base_url: str | None = None
    default_model: str | None = None
    timeout_seconds: float = 120.0
    supports_model_listing: bool = False
    supports_chat_completions: bool = False
    aliases: list[str] = Field(default_factory=list)


class InferenceMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str


class InferenceRequest(StrictModel):
    messages: list[InferenceMessage] = Field(default_factory=list)
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InferenceUsage(StrictModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class InferenceResponse(StrictModel):
    backend: InferenceBackend
    model: str | None = None
    content: str
    finish_reason: str | None = None
    usage: InferenceUsage = Field(default_factory=InferenceUsage)
    raw_response: dict[str, Any] = Field(default_factory=dict)
