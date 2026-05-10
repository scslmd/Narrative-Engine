from __future__ import annotations

from typing import Any

import httpx

from ..schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from ..services.circuit_breaker import get_circuit_breaker, CircuitBreakerError
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
        
        # Circuit breaker for this backend (REL-01)
        self._circuit_breaker = get_circuit_breaker(backend)

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url must not be blank")
        if normalized.endswith("/v1"):
            return normalized
        return f"{normalized}/v1"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _configuration_error(self, message: str) -> InferenceBackendError:
        return InferenceBackendError(
            message,
            category="configuration_error",
            code="RUNTIME_CONFIGURATION_ERROR",
            finish_reason="configuration_error",
            retryable=False,
        )

    def _protocol_shape_error(self, message: str) -> InferenceBackendError:
        return InferenceBackendError(
            message,
            category="protocol_shape_failure",
            code="INVALID_RESPONSE_SHAPE",
            finish_reason="invalid_response",
            retryable=False,
        )

    def _http_status_error(self, exc: httpx.HTTPStatusError) -> InferenceBackendError:
        status_code = int(exc.response.status_code)
        provider_message = str(exc)
        category = "http_status_failure"
        finish_reason = "provider_http_error"
        retryable = status_code in {408, 409, 425, 429, 500, 502, 503, 504}
        if status_code in {400, 401, 403, 404, 422}:
            category = "provider_rejected_request"
            finish_reason = "request_rejected"
            retryable = False
        return InferenceBackendError(
            f"{self._descriptor.display_name} request failed: {provider_message}",
            category=category,
            code=f"HTTP_{status_code}",
            finish_reason=finish_reason,
            retryable=retryable,
            http_status=status_code,
            provider_message=provider_message,
        )

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
                raise self._protocol_shape_error("Inference backend returned a non-object JSON payload.")
            return payload
        except httpx.TimeoutException as exc:
            raise InferenceBackendError(
                f"{self._descriptor.display_name} request failed: {exc}",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
                provider_message=str(exc),
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise self._http_status_error(exc) from exc
        except httpx.TransportError as exc:
            raise InferenceBackendError(
                f"{self._descriptor.display_name} request failed: {exc}",
                category="transport_failure",
                code="INFERENCE_TRANSPORT_FAILURE",
                finish_reason="transport_failed",
                retryable=True,
                provider_message=str(exc),
            ) from exc
        except httpx.HTTPError as exc:
            raise InferenceBackendError(
                f"{self._descriptor.display_name} request failed: {exc}",
                category="transport_failure",
                code="INFERENCE_TRANSPORT_FAILURE",
                finish_reason="transport_failed",
                retryable=True,
                provider_message=str(exc),
            ) from exc
        except ValueError as exc:
            raise InferenceBackendError(
                f"{self._descriptor.display_name} returned invalid JSON.",
                category="invalid_json",
                code="INVALID_JSON_RESPONSE",
                finish_reason="invalid_response",
                retryable=True,
                provider_message=str(exc),
            ) from exc

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
        """Generate text using inference backend with circuit breaker protection (REL-01)."""
        if not self._base_url.strip():
            raise self._configuration_error("Inference backend base URL is not configured.")
        
        messages = []
        for msg in request.messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.cache_control is not None:
                d["cache_control"] = msg.cache_control
            messages.append(d)

        payload = {
            "model": request.model or self._descriptor.default_model,
            "messages": messages,
        }
        if not payload["model"]:
            raise self._configuration_error("Inference request is missing a model and no default model is configured.")
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.metadata:
            payload["metadata"] = request.metadata

        # Wrap inference call with circuit breaker (REL-01)
        try:
            response_payload = self._circuit_breaker.call(
                lambda: self._request("POST", "/chat/completions", json_payload=payload)
            )
        except CircuitBreakerError as e:
            # Circuit is open - fail fast with clear error
            raise InferenceBackendError(
                f"Inference backend {self._descriptor.display_name} circuit breaker open: {e.message}",
                category="circuit_open",
                code="INFERENCE_CIRCUIT_OPEN",
                finish_reason="circuit_breaker_open",
                retryable=False,
            ) from e
        
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise self._protocol_shape_error(f"{self._descriptor.display_name} returned no choices.")
        first_choice = choices[0] if isinstance(choices[0], dict) else {}
        finish_reason = first_choice.get("finish_reason") if isinstance(first_choice, dict) else None
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

        # Detect truncated or empty responses caused by token budget exhaustion
        reasoning_content = message.get("reasoning_content", "") if isinstance(message, dict) else ""
        if finish_reason == "length" or (not content and reasoning_content):
            raise InferenceBackendError(
                f"{self._descriptor.display_name} response was truncated or empty "
                f"(max_tokens={payload['max_tokens']}, finish_reason={finish_reason}). "
                f"Increase NARRATIVE_MAX_TOKENS_DEFAULT or NARRATIVE_MAX_TOKENS_<PHASE> in your .env file (current minimum: 8192).",
                category="truncated_response",
                code="INFERENCE_TRUNCATED",
                finish_reason="length",
                retryable=False,
            )

        usage_payload = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
        return InferenceResponse(
            backend=self._descriptor.backend,
            model=str(response_payload.get("model") or payload["model"]) if payload["model"] else None,
            content=content,
            finish_reason=str(first_choice.get("finish_reason")) if isinstance(first_choice, dict) and first_choice.get("finish_reason") is not None else None,
            usage=InferenceUsage(
                prompt_tokens=int(usage_payload.get("prompt_tokens", 0)) if usage_payload.get("prompt_tokens") else None,
                completion_tokens=int(usage_payload.get("completion_tokens", 0)) if usage_payload.get("completion_tokens") else None,
                total_tokens=int(usage_payload.get("total_tokens", 0)) if usage_payload.get("total_tokens") else None,
                cached_prompt_tokens=usage_payload.get("cached_prompt_tokens") or usage_payload.get("prompt_cache_read_tokens"),
                prompt_cache_write_tokens=usage_payload.get("prompt_cache_write_tokens"),
            ),
            raw_response=response_payload,
        )
