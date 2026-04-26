from __future__ import annotations

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
