"""Tests for chapter summarizer prompt content."""
import pytest
from app.services.runtime_prompts import build_chapter_summarize_request


class TestSummarizerPromptGranularity:
    """Verify granularity guidance for key events."""

    def _get_system_content(self) -> str:
        request = build_chapter_summarize_request(
            chapter_id="ch-1",
            chapter_text="Test chapter text.",
            character_names=["Hero"],
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_has_granularity_guidance(self) -> None:
        content = self._get_system_content()
        # Should clarify what counts as a key event (major plot turns, not scene transitions)
        assert any(
            term in content.lower()
            for term in ["plot turn", "pivotal", "major", "significant", "what happened"]
        )


class TestSummarizerPromptCharacterStates:
    """Verify improved character state format."""

    def _get_system_content(self) -> str:
        request = build_chapter_summarize_request(
            chapter_id="ch-1",
            chapter_text="Test chapter text.",
            character_names=["Hero"],
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_character_states_include_goal_or_emotional_state(self) -> None:
        content = self._get_system_content()
        # Should guide character states to include goal + emotional state + key change
        assert any(
            term in content.lower()
            for term in ["goal", "emotional", "change", "current"]
        )


class TestSummarizerPromptNoChapterId:
    """Verify chapter_id is removed from JSON schema (ISSUE 16)."""

    def _get_system_content(self) -> str:
        request = build_chapter_summarize_request(
            chapter_id="ch-1",
            chapter_text="Test chapter text.",
            character_names=["Hero"],
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_chapter_id_not_in_json_schema(self) -> None:
        content = self._get_system_content()
        # chapter_id should NOT be in the JSON schema — caller already has it
        # The system prompt should not ask LLM to repeat chapter_id
        json_section = content.lower()
        # Look for chapter_id in the JSON template section (not elsewhere)
        assert '"chapter_id"' not in content


class TestSummarizerPromptExistingBehavior:
    """Verify existing behavior is preserved."""

    def _get_request(self):
        return build_chapter_summarize_request(
            chapter_id="ch-1",
            chapter_text="Test chapter text.",
            character_names=["Hero", "Villain"],
            default_model="test-model",
        )

    def test_has_required_json_keys(self) -> None:
        request = self._get_request()
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content = system_msg.content

        assert "key_events" in content
        assert "character_states" in content
        assert "unresolved_threads" in content
        assert "title" in content

    def test_has_limits(self) -> None:
        request = self._get_request()
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content = system_msg.content

        # Should mention limits (up to 10 events, etc.)
        assert "10" in content or "up to" in content.lower()

    def test_user_message_includes_chapter_id(self) -> None:
        request = self._get_request()
        user_msg = [m for m in request.messages if m.role == "user"][0]
        assert "ch-1" in user_msg.content

    def test_user_message_includes_characters(self) -> None:
        request = self._get_request()
        user_msg = [m for m in request.messages if m.role == "user"][0]
        assert "Hero" in user_msg.content
        assert "Villain" in user_msg.content

    def test_temperature_is_deterministic(self) -> None:
        request = self._get_request()
        assert request.temperature == 0.1
