from __future__ import annotations

import json

import httpx
import pytest

from app.inference.base import InferenceBackendError
from app.inference.openai_compatible import OpenAICompatibleInferenceBackend
from app.schemas.inference import InferenceMessage, InferenceRequest


def _backend(*, timeout_seconds: float = 12.5) -> OpenAICompatibleInferenceBackend:
    return OpenAICompatibleInferenceBackend(
        backend="openai_compatible",
        display_name="Test Runtime",
        base_url="http://127.0.0.1:9000",
        api_key="secret-token",
        default_model="test-model",
        timeout_seconds=timeout_seconds,
    )


def _request() -> InferenceRequest:
    return InferenceRequest(
        model="override-model",
        messages=[
            InferenceMessage(role="user", content="Say hello."),
        ],
        temperature=0.2,
        max_tokens=64,
    )


def test_openai_compatible_adapter_wraps_timeout_errors(monkeypatch) -> None:
    backend = _backend(timeout_seconds=7.0)
    captured: dict[str, object] = {}

    def fake_request(method, url, *, headers, json, timeout):
        captured.update(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        raise httpx.ReadTimeout("timed out", request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake_request)

    with pytest.raises(InferenceBackendError, match=r"Test Runtime request failed: timed out") as exc_info:
        backend.generate_text(_request())

    assert exc_info.value.category == "timeout"
    assert exc_info.value.code == "INFERENCE_TIMEOUT"
    assert exc_info.value.finish_reason == "timeout"
    assert exc_info.value.retryable is True

    assert captured["method"] == "POST"
    assert captured["url"] == "http://127.0.0.1:9000/v1/chat/completions"
    assert captured["timeout"] == 7.0
    assert captured["headers"]["Authorization"] == "Bearer secret-token"


def test_openai_compatible_adapter_wraps_non_2xx_http_errors(monkeypatch) -> None:
    backend = _backend()

    class ErrorResponse:
        def raise_for_status(self) -> None:
            request = httpx.Request("GET", "http://127.0.0.1:9000/v1/models")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("503 Service Unavailable", request=request, response=response)

        def json(self) -> dict[str, object]:
            raise AssertionError("json() should not be called after raise_for_status().")

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: ErrorResponse())

    with pytest.raises(InferenceBackendError, match=r"Test Runtime request failed: 503 Service Unavailable") as exc_info:
        backend.list_models()

    assert exc_info.value.category == "http_status_failure"
    assert exc_info.value.code == "HTTP_503"
    assert exc_info.value.finish_reason == "provider_http_error"
    assert exc_info.value.retryable is True
    assert exc_info.value.http_status == 503


def test_openai_compatible_adapter_wraps_invalid_json_responses(monkeypatch) -> None:
    backend = _backend()

    class InvalidJsonResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            raise json.JSONDecodeError("Expecting value", "not-json", 0)

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: InvalidJsonResponse())

    with pytest.raises(InferenceBackendError, match=r"Test Runtime returned invalid JSON\.") as exc_info:
        backend.list_models()

    assert exc_info.value.category == "invalid_json"
    assert exc_info.value.code == "INVALID_JSON_RESPONSE"
    assert exc_info.value.finish_reason == "invalid_response"
    assert exc_info.value.retryable is True


def test_openai_compatible_adapter_maps_provider_rejected_request_statuses(monkeypatch) -> None:
    backend = _backend()

    class ErrorResponse:
        def raise_for_status(self) -> None:
            request = httpx.Request("POST", "http://127.0.0.1:9000/v1/chat/completions")
            response = httpx.Response(422, request=request)
            raise httpx.HTTPStatusError("422 Unprocessable Entity", request=request, response=response)

        def json(self) -> dict[str, object]:
            raise AssertionError("json() should not be called after raise_for_status().")

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: ErrorResponse())

    with pytest.raises(InferenceBackendError, match=r"422 Unprocessable Entity") as exc_info:
        backend.generate_text(_request())

    assert exc_info.value.category == "provider_rejected_request"
    assert exc_info.value.code == "HTTP_422"
    assert exc_info.value.finish_reason == "request_rejected"
    assert exc_info.value.retryable is False


def test_openai_compatible_adapter_maps_protocol_shape_failures(monkeypatch) -> None:
    backend = _backend()

    class InvalidShapeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"id": "completion-without-choices"}

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: InvalidShapeResponse())

    with pytest.raises(InferenceBackendError, match=r"returned no choices") as exc_info:
        backend.generate_text(_request())

    assert exc_info.value.category == "protocol_shape_failure"
    assert exc_info.value.code == "INVALID_RESPONSE_SHAPE"
    assert exc_info.value.finish_reason == "invalid_response"
    assert exc_info.value.retryable is False


def test_openai_compatible_adapter_maps_missing_model_to_configuration_error() -> None:
    backend = OpenAICompatibleInferenceBackend(
        backend="openai_compatible",
        display_name="Test Runtime",
        base_url="http://127.0.0.1:9000",
        api_key="secret-token",
        default_model=None,
        timeout_seconds=12.5,
    )
    request = InferenceRequest(
        messages=[InferenceMessage(role="user", content="Say hello.")],
    )

    with pytest.raises(InferenceBackendError, match=r"missing a model") as exc_info:
        backend.generate_text(request)

    assert exc_info.value.category == "configuration_error"
    assert exc_info.value.code == "RUNTIME_CONFIGURATION_ERROR"
    assert exc_info.value.finish_reason == "configuration_error"
    assert exc_info.value.retryable is False
