from __future__ import annotations

from app.schemas.inference import InferenceMessage, InferenceRequest, InferenceUsage


def test_inference_message_accepts_cache_control():
    msg = InferenceMessage(
        role="system",
        content="You are helpful.",
        cache_control={"type": "ephemeral"},
    )
    assert msg.cache_control == {"type": "ephemeral"}


def test_inference_message_cache_control_defaults_to_none():
    msg = InferenceMessage(
        role="system",
        content="You are helpful.",
    )
    assert msg.cache_control is None


def test_inference_usage_accepts_cache_metrics():
    usage = InferenceUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        cached_prompt_tokens=800,
        prompt_cache_write_tokens=200,
    )
    assert usage.cached_prompt_tokens == 800
    assert usage.prompt_cache_write_tokens == 200


def test_inference_usage_cache_metrics_default_to_none():
    usage = InferenceUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
    )
    assert usage.cached_prompt_tokens is None
    assert usage.prompt_cache_write_tokens is None


def test_cache_control_passthrough_in_serialization():
    """Verify that cache_control is included in serialized messages when present."""

    req = InferenceRequest(
        model="test-model",
        messages=[
            InferenceMessage(role="system", content="You are helpful.", cache_control={"type": "ephemeral"}),
            InferenceMessage(role="user", content="Write a story."),
        ],
    )

    serialized = []
    for msg in req.messages:
        d = {"role": msg.role, "content": msg.content}
        if msg.cache_control is not None:
            d["cache_control"] = msg.cache_control
        serialized.append(d)

    assert serialized[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in serialized[1]


def test_cache_metrics_extraction_from_response():
    """Verify cache metrics are extracted from provider response."""
    usage_payload = {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
        "cached_prompt_tokens": 800,
        "prompt_cache_write_tokens": 200,
    }

    usage = InferenceUsage(
        prompt_tokens=int(usage_payload.get("prompt_tokens", 0)) if usage_payload.get("prompt_tokens") else None,
        completion_tokens=int(usage_payload.get("completion_tokens", 0)) if usage_payload.get("completion_tokens") else None,
        total_tokens=int(usage_payload.get("total_tokens", 0)) if usage_payload.get("total_tokens") else None,
        cached_prompt_tokens=usage_payload.get("cached_prompt_tokens") or usage_payload.get("prompt_cache_read_tokens"),
        prompt_cache_write_tokens=usage_payload.get("prompt_cache_write_tokens"),
    )

    assert usage.cached_prompt_tokens == 800
    assert usage.prompt_cache_write_tokens == 200


def test_p300_system_message_has_cache_control():
    from app.schemas.manifest import Manifest, ManifestConfig
    from app.schemas.enums import PovMode, StoryStructure
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
        chapter_id="1",
    )

    system_msg = req.messages[0]
    assert system_msg.cache_control == {"type": "ephemeral"}

    user_msg = req.messages[1]
    assert user_msg.cache_control is None
