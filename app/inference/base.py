from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse


class InferenceBackendError(RuntimeError):
    pass


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
