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

    with pytest.raises(InferenceBackendError, match=r"Test Runtime request failed: timed out"):
        backend.generate_text(_request())

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

    with pytest.raises(InferenceBackendError, match=r"Test Runtime request failed: 503 Service Unavailable"):
        backend.list_models()


def test_openai_compatible_adapter_wraps_invalid_json_responses(monkeypatch) -> None:
    backend = _backend()

    class InvalidJsonResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            raise json.JSONDecodeError("Expecting value", "not-json", 0)

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: InvalidJsonResponse())

    with pytest.raises(InferenceBackendError, match=r"Test Runtime returned invalid JSON\."):
        backend.list_models()
