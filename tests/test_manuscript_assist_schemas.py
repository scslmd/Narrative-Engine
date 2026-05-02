from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.manuscript_assist import ApplyAssistSuggestionRequest, ManuscriptAssistRequest


def _base_request() -> dict:
    return {
        "project_id": "proj-1",
        "document_id": "doc-1",
        "assist_kind": "line_edit_selection",
        "instruction": "Tighten prose.",
        "text_range": {
            "start_offset": 0,
            "end_offset": 5,
            "selected_text": "Hello",
            "anchor_before": "",
            "anchor_after": " world",
        },
    }


def test_selection_assist_requires_range() -> None:
    payload = _base_request()
    payload.pop("text_range")
    with pytest.raises(ValidationError):
        ManuscriptAssistRequest.model_validate(payload)


def test_fork_assist_requires_creation_mode() -> None:
    payload = _base_request()
    payload["assist_kind"] = "fork_from_selection"
    with pytest.raises(ValidationError):
        ManuscriptAssistRequest.model_validate(payload)


def test_apply_request_validates_expected_version() -> None:
    with pytest.raises(ValidationError):
        ApplyAssistSuggestionRequest.model_validate(
            {
                "project_id": "proj-1",
                "document_id": "doc-1",
                "suggestion_id": "sug-1",
                "expected_document_version": 0,
                "apply_mode": "replace_range",
            }
        )
