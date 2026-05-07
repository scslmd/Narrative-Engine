from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.manuscript_assist import ManuscriptAssistKind, ManuscriptAssistRequest


def test_ai_generate_draft_kind_exists() -> None:
    """AI_GENERATE_DRAFT enum value exists."""
    assert hasattr(ManuscriptAssistKind, "AI_GENERATE_DRAFT")
    assert ManuscriptAssistKind.AI_GENERATE_DRAFT.value == "ai_generate_draft"


def test_ai_generate_draft_request_without_text_range() -> None:
    """ai_generate_draft does NOT require text_range (like generate_next_chapter)."""
    request = ManuscriptAssistRequest.model_validate({
        "project_id": "proj-1",
        "document_id": "doc-1",
        "assist_kind": "ai_generate_draft",
        "instruction": "Write a chapter about the hero leaving home.",
        "create_draft_artifact": True,
    })
    assert request.assist_kind == ManuscriptAssistKind.AI_GENERATE_DRAFT
    assert request.text_range is None
    assert request.create_draft_artifact is True


def test_ai_generate_draft_request_with_optional_text_range() -> None:
    """ai_generate_draft accepts text_range if provided (not required)."""
    request = ManuscriptAssistRequest.model_validate({
        "project_id": "proj-1",
        "document_id": "doc-1",
        "assist_kind": "ai_generate_draft",
        "instruction": "Write a chapter.",
        "text_range": {
            "start_offset": 0,
            "end_offset": 100,
            "selected_text": "some context text",
        },
    })
    assert request.text_range is not None
