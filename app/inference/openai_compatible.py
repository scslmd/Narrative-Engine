from __future__ import annotations

from typing import Any

import httpx

from ..schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from .base import InferenceBackend, InferenceBackendError


class OpenAICompatibleInferenceBackend(InferenceBackend):
    def __init__(
        self,
        *,
        backend: str,
        display_name: str,
        base_url: str,
        api_key: str | None,
        default_model: str | None,
        timeout_seconds: float,
        aliases: list[str] | None = None,
    ) -> None:
        self._base_url = self._normalize_base_url(base_url)
        self._api_key = api_key
        self._descriptor = InferenceProviderDescriptor(
            backend=backend,
            display_name=display_name,
            transport="openai_compatible_http",
            base_url=self._base_url,
            default_model=default_model,
            timeout_seconds=timeout_seconds,
            supports_model_listing=True,
            supports_chat_completions=True,
            aliases=aliases or [],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/v1"):
            return normalized
        return f"{normalized}/v1"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _request(self, method: str, path: str, *, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                f"{self._base_url}{path}",
                headers=self._headers(),
                json=json_payload,
                timeout=self._descriptor.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise InferenceBackendError("Inference backend returned a non-object JSON payload.")
            return payload
        except httpx.HTTPError as exc:
            raise InferenceBackendError(f"{self._descriptor.display_name} request failed: {exc}") from exc
        except ValueError as exc:
            raise InferenceBackendError(f"{self._descriptor.display_name} returned invalid JSON.") from exc

    def list_models(self) -> list[str]:
        payload = self._request("GET", "/models")
        items = payload.get("data")
        if not isinstance(items, list):
            return []
        models: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if isinstance(model_id, str) and model_id.strip():
                models.append(model_id.strip())
        return sorted(set(models))

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        payload = {
            "model": request.model or self._descriptor.default_model,
            "messages": [message.model_dump(mode="json") for message in request.messages],
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.metadata:
            payload["metadata"] = request.metadata

        response_payload = self._request("POST", "/chat/completions", json_payload=payload)
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise InferenceBackendError(f"{self._descriptor.display_name} returned no choices.")
        first_choice = choices[0] if isinstance(choices[0], dict) else {}
        message = first_choice.get("message") if isinstance(first_choice, dict) else {}
        content = ""
        if isinstance(message, dict):
            message_content = message.get("content")
            if isinstance(message_content, str):
                content = message_content
            elif isinstance(message_content, list):
                content = "".join(
                    item.get("text", "")
                    for item in message_content
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                )
        usage_payload = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
        return InferenceResponse(
            backend=self._descriptor.backend,
            model=str(response_payload.get("model") or payload["model"]) if payload["model"] else None,
            content=content,
            finish_reason=str(first_choice.get("finish_reason")) if isinstance(first_choice, dict) and first_choice.get("finish_reason") is not None else None,
            usage=InferenceUsage(
                prompt_tokens=usage_payload.get("prompt_tokens"),
                completion_tokens=usage_payload.get("completion_tokens"),
                total_tokens=usage_payload.get("total_tokens"),
            ),
            raw_response=response_payload,
        )
