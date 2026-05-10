from __future__ import annotations

import pytest

from app.services.runtime_prompts import build_cascade_extraction_request


def test_prompt_builder_basic():
    req = build_cascade_extraction_request("The quick brown fox jumps over the lazy dog.")
    sys_content = req.messages[0].content
    assert "characters" in sys_content
    assert "relationships" in sys_content
    assert "world_entries" in sys_content or "world" in sys_content.lower()


def test_prompt_builder_includes_text():
    text = "Once upon a time there was a fox."
    req = build_cascade_extraction_request(text)
    user_content = req.messages[1].content
    assert text in user_content


def test_prompt_builder_with_existing_characters():
    chars = ["Alice", "Bob"]
    req = build_cascade_extraction_request("Some text.", existing_characters=chars)
    user_content = req.messages[1].content
    assert "## Existing Characters" in user_content
    assert "- Alice" in user_content
    assert "- Bob" in user_content


def test_prompt_temperature():
    req = build_cascade_extraction_request("test")
    assert req.temperature == 0.1
