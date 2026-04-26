from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from app.inference.base import InferenceBackend
from app.schemas.inference import InferenceProviderDescriptor
from app.services.chapter_summarizer import ChapterSummarizerService


def test_chapter_summarizer_init_stores_inferencer():
    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    assert service._inferencer is mock_inferencer


def test_build_chapter_summarize_request_structure():
    from app.services.runtime_prompts import build_chapter_summarize_request

    request = build_chapter_summarize_request(
        chapter_id="ch-001",
        chapter_text="# Chapter 1\nSome story text here.",
        character_names=["Kael", "Soraya"],
        default_model="test-model",
    )

    assert request.temperature == 0.1
    assert request.max_tokens == 2000
    assert len(request.messages) == 2
    assert request.messages[0].role == "system"
    assert request.messages[1].role == "user"
    assert "Kael" in request.messages[1].content
    assert "Soraya" in request.messages[1].content
    assert request.metadata["chapter_id"] == "ch-001"


def test_summarize_returns_prior_chapter_summary():
    from app.schemas.story_development import PriorChapterSummary

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )

    # Mock successful LLM response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "chapter_id": "ch-001",
        "title": "The Departure",
        "key_events": ["Kael leaves the village"],
        "character_states": {"Kael": "restless, seeking purpose"},
        "unresolved_threads": ["Who is Soraya?"],
    })
    mock_inferencer.generate_text.return_value = mock_response

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# The Departure\nKael left the village at dawn.",
        character_names=["Kael", "Soraya"],
    )

    assert isinstance(result, PriorChapterSummary)
    assert result.chapter_id == "ch-001"
    assert result.title == "The Departure"
    assert len(result.key_events) == 1
    assert "Kael" in result.character_states


def test_summarize_returns_none_on_llm_error():
    from app.inference.base import InferenceBackendError

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )
    mock_inferencer.generate_text.side_effect = InferenceBackendError(
        code="timeout",
        category="backend",
        message="Connection timeout",
        finish_reason="error",
        retryable=True,
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# Chapter\nSome text.",
        character_names=["Kael"],
    )

    assert result is None


def test_summarize_returns_none_on_invalid_json():
    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )

    mock_response = MagicMock()
    mock_response.content = "not valid json {{{"
    mock_inferencer.generate_text.return_value = mock_response

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="# Chapter\nSome text.",
        character_names=["Kael"],
    )

    assert result is None


def test_summarize_skips_on_empty_text():
    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    result = service.summarize(
        chapter_id="ch-001",
        chapter_text="",
        character_names=["Kael"],
    )

    assert result is None
    mock_inferencer.generate_text.assert_not_called()


def test_executor_accepts_chapter_summarizer_parameter():
    import inspect
    from app.services.local_executor import LocalExecutor

    sig = inspect.signature(LocalExecutor.__init__)
    params = list(sig.parameters.keys())
    assert "chapter_summarizer_service" in params, f"Missing parameter. Got: {params}"
