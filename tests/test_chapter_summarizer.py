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
