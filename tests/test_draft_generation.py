from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.manuscript_assist import ManuscriptAssistKind, ManuscriptAssistPacket, ManuscriptAssistRequest
from app.services.runtime_prompts import build_m500_draft_generation_request


def _build_packet(**overrides) -> ManuscriptAssistPacket:
    base = {
        "assist_id": "assist-test",
        "project_id": "proj-1",
        "document_id": "doc-1",
        "assist_kind": "ai_generate_draft",
        "instruction": "Write a chapter about the hero leaving home.",
        "document_title": "Chapter 2",
        "document_content": "Existing content...",
    }
    base.update(overrides)
    return ManuscriptAssistPacket.model_validate(base)


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


def test_prompt_builder_returns_valid_request() -> None:
    """Prompt builder returns an InferenceRequest with correct params."""
    packet = _build_packet()
    req = build_m500_draft_generation_request(packet, default_model="test-model")

    assert req.model == "test-model"
    assert req.temperature == 0.7
    assert req.max_tokens == 8000
    assert len(req.messages) == 2
    assert req.messages[0].role == "system"
    assert req.messages[1].role == "user"


def test_prompt_builder_system_mentions_json_output() -> None:
    """System prompt instructs LLM to return JSON with full_content key."""
    packet = _build_packet()
    req = build_m500_draft_generation_request(packet, default_model=None)

    system_text = req.messages[0].content
    assert "full_content" in system_text
    assert "JSON" in system_text.upper()


def test_prompt_builder_user_message_contains_instruction() -> None:
    """User message JSON packet contains the instruction."""
    packet = _build_packet(instruction="Write about the forest.")
    req = build_m500_draft_generation_request(packet, default_model=None)

    user_content = req.messages[1].content
    assert "Write about the forest" in user_content


def test_prompt_builder_metadata_has_phase() -> None:
    """Request metadata identifies M-500 draft generation phase."""
    packet = _build_packet()
    req = build_m500_draft_generation_request(packet, default_model=None)

    assert req.metadata["phase"] == "M-500"
    assert req.metadata["role"] == "draft_generator"


def test_prompt_builder_uses_packet_temperature_override() -> None:
    """Packet temperature override is respected."""
    packet = _build_packet(temperature=0.9)
    req = build_m500_draft_generation_request(packet, default_model=None)

    assert req.temperature == 0.9


def test_prompt_builder_uses_packet_max_tokens_override() -> None:
    """Packet max_tokens override is respected."""
    packet = _build_packet(max_tokens=12000)
    req = build_m500_draft_generation_request(packet, default_model=None)

    assert req.max_tokens == 12000


def test_prompt_builder_uses_packet_model_id() -> None:
    """Packet model_id takes precedence over default."""
    packet = _build_packet(model_id="custom-model")
    req = build_m500_draft_generation_request(packet, default_model="fallback")

    assert req.model == "custom-model"
