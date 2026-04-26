from __future__ import annotations

import pytest
from app.services.chapter_summarizer import ChapterSummarizerService


def test_summarizer_service_construction():
    from unittest.mock import MagicMock
    from app.inference.base import InferenceBackend
    from app.schemas.inference import InferenceProviderDescriptor

    mock_inferencer = MagicMock(spec=InferenceBackend)
    mock_inferencer.descriptor = InferenceProviderDescriptor(
        backend="stub",
        display_name="Stub",
        transport="stub",
        default_model="test-model",
    )

    service = ChapterSummarizerService(inferencer=mock_inferencer)
    assert service._inferencer is mock_inferencer
