"""Tests for consistency critic prompt content."""
import pytest
from app.schemas.inference import InferenceRequest
from app.services.runtime_prompts import build_critic_check_request


class TestCriticPromptBasic:
    """Verify basic structure of the critic prompt builder."""

    def test_returns_inference_request(self) -> None:
        request = build_critic_check_request(
            draft_text="Test draft passage.",
            character_bios={"Hero": "Brave warrior"},
            default_model="test-model",
        )
        assert isinstance(request, InferenceRequest)

    def test_has_system_and_user_messages(self) -> None:
        request = build_critic_check_request(
            draft_text="Test draft passage.",
            character_bios={"Hero": "Brave warrior"},
            default_model="test-model",
        )
        roles = [m.role for m in request.messages]
        assert "system" in roles
        assert "user" in roles

    def test_system_prompt_contains_json_schema(self) -> None:
        request = build_critic_check_request(
            draft_text="Test draft passage.",
            character_bios={"Hero": "Brave warrior"},
            default_model="test-model",
        )
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content = system_msg.content

        assert "passed" in content
        assert "violations" in content
        assert "character" in content
        assert "issue" in content
        assert "suggestion" in content


class TestCriticPromptCheckForSection:
    """Verify CHECK FOR section with specific violation criteria."""

    def _get_system_content(self) -> str:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_has_check_for_section(self) -> None:
        content = self._get_system_content()
        assert "CHECK FOR" in content or "check for" in content.lower()

    def test_checks_voice_consistency(self) -> None:
        content = self._get_system_content()
        # Should mention voice, word choice, vocabulary
        assert "voice" in content.lower()
        assert any(term in content.lower() for term in ["word choice", "vocabulary", "sentence"])

    def test_checks_behavior_consistency(self) -> None:
        content = self._get_system_content()
        assert "behavior" in content.lower() or "actions" in content.lower()
        assert any(term in content.lower() for term in ["goals", "fears", "traits"])

    def test_checks_knowledge_consistency(self) -> None:
        content = self._get_system_content()
        assert "knowledge" in content.lower()

    def test_checks_conflict_or_values(self) -> None:
        content = self._get_system_content()
        # Should mention values, stance, or conflict consistency
        assert any(term in content.lower() for term in ["values", "stance", "conflict"])


class TestCriticPromptNotViolationsSection:
    """Verify NOT VIOLATIONS section to reduce false positives."""

    def _get_system_content(self) -> str:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_has_not_violations_section(self) -> None:
        content = self._get_system_content()
        # Should have a section that clarifies what is NOT a violation
        assert any(
            phrase in content.lower()
            for phrase in ["not violations", "not a violation", "are not violations"]
        )

    def test_mentions_arc_progression(self) -> None:
        content = self._get_system_content()
        # Should clarify that character growth is not a violation
        assert any(
            term in content.lower()
            for term in ["growth", "arc", "development", "progression"]
        )

    def test_mentions_subtlety(self) -> None:
        content = self._get_system_content()
        # Should clarify that subtlety is not a violation
        assert any(
            term in content.lower()
            for term in ["subtlety", "understatement", "not all feelings"]
        )


class TestCriticPromptConservativeGuidance:
    """Verify conservative flagging guidance."""

    def _get_system_content(self) -> str:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_guides_conservative_flagging(self) -> None:
        content = self._get_system_content()
        # Should advise being conservative about flagging violations
        assert any(
            term in content.lower()
            for term in ["conservative", "clear contradictions", "only flag"]
        )


class TestCriticPromptUserMessage:
    """Verify user message structure."""

    def test_includes_character_profiles(self) -> None:
        request = build_critic_check_request(
            draft_text="Test draft.",
            character_bios={"Hero": "Brave warrior", "Villain": "Cunning foe"},
            default_model="test-model",
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        assert "Hero" in user_msg.content
        assert "Villain" in user_msg.content

    def test_includes_draft_text(self) -> None:
        draft = "The hero fought bravely against the villain."
        request = build_critic_check_request(
            draft_text=draft,
            character_bios={"Hero": "Brave warrior"},
            default_model="test-model",
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        assert draft in user_msg.content

    def test_handles_empty_character_bios(self) -> None:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={},
            default_model="test-model",
        )
        # Should not crash with empty bios
        assert isinstance(request, InferenceRequest)


class TestCriticPromptMetadata:
    """Verify request metadata."""

    def test_has_critic_metadata(self) -> None:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        assert request.metadata is not None
        assert "consistency_critic" in request.metadata.get("mode", "")

    def test_temperature_is_deterministic(self) -> None:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        assert request.temperature == 0.1

    def test_max_tokens_is_reasonable(self) -> None:
        request = build_critic_check_request(
            draft_text="Test.",
            character_bios={"Hero": "Brave"},
            default_model="test-model",
        )
        assert request.max_tokens >= 2048
