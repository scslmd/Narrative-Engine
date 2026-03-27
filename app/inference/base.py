from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from ..schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse


RuntimeErrorCategory = Literal[
    "timeout",
    "transport_failure",
    "http_status_failure",
    "invalid_json",
    "protocol_shape_failure",
    "provider_rejected_request",
    "configuration_error",
    "circuit_open",  # REL-01: Circuit breaker is open
]


class InferenceBackendError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: RuntimeErrorCategory,
        code: str,
        finish_reason: str,
        retryable: bool,
        http_status: int | None = None,
        provider_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.code = code
        self.finish_reason = finish_reason
        self.retryable = retryable
        self.http_status = http_status
        self.provider_message = provider_message or message


class InferenceBackend(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> InferenceProviderDescriptor:
        raise NotImplementedError

    def list_models(self) -> list[str]:
        return []

    @abstractmethod
    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        raise NotImplementedError
