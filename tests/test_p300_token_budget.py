from __future__ import annotations

from app.schemas.manifest import Manifest
from app.services.runtime_prompts import build_p300_drafter_request


def _make_manifest() -> Manifest:
    return Manifest.model_validate({
        "project_id": "test-project",
        "project_name": "Test Project",
        "genre": "Science Fiction",
        "tone": "Contemplative",
        "story_structure": "THREE_ACT",
        "constraints": [],
        "premise_text": "A test story.",
    })


def test_p300_default_max_tokens_is_8192():
    manifest = _make_manifest()
    request = build_p300_drafter_request(
        manifest=manifest,
        payload={"project_id": "test-project"},
        default_model=None,
    )
    assert request.max_tokens == 8192


def test_p300_max_tokens_overridable_via_payload():
    manifest = _make_manifest()
    request = build_p300_drafter_request(
        manifest=manifest,
        payload={"project_id": "test-project", "max_tokens": 16000},
        default_model=None,
    )
    assert request.max_tokens == 16000
