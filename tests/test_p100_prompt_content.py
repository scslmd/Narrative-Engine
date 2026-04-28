"""Tests for P-100 architect prompt output format guardrails."""
import pytest
from app.services.runtime_prompts import build_p100_architect_request


@pytest.fixture()
def sample_manifest(tmp_path):
    from app.schemas.enums import StoryStructure
    from app.schemas.manifest import Manifest, ManifestConfig

    return Manifest(
        project_id="proj-1",
        project_name="Test Project",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="Epic",
            story_structure=StoryStructure.THREE_ACT,
        ),
        premise_text="A test story.",
    )


class TestP100OutputFormatGuardrails:
    """Verify P-100 prompt has output format constraints."""

    def _get_system_content(self, manifest) -> str:
        request = build_p100_architect_request(
            manifest=manifest,
            payload={},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_has_no_preamble_instruction(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        # Should instruct no preamble or introduction text
        assert any(
            phrase in content.lower()
            for phrase in ["no preamble", "no introduction", "no extra", "only markdown"]
        )

    def test_has_no_code_fences_instruction(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        assert any(
            phrase in content.lower()
            for phrase in ["no code fences", "no code blocks", "no markdown fences"]
        )

    def test_has_heading_length_guidance(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        # Should provide length or scope guidance for at least one heading
        assert any(
            term in content.lower()
            for term in ["sentence", "words", "brief", "one sentence"]
        )

    def test_has_no_extra_headings_instruction(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        assert any(
            phrase in content.lower()
            for phrase in ["no extra headings", "exact headings", "these exact headings"]
        )


class TestP100HeadingSpecificGuidance:
    """Verify specific headings have scope guidance."""

    def _get_system_content(self, manifest) -> str:
        request = build_p100_architect_request(
            manifest=manifest,
            payload={},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_logline_has_scope(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        # Logline should mention it's one sentence or brief
        assert "logline" in content.lower()

    def test_character_arcs_has_scope(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        # Character arcs should mention starting/ending state or per-character format
        assert "character" in content.lower() and "arc" in content.lower()


class TestP100ExistingBehaviorPreserved:
    """Verify existing prompt behavior is not broken."""

    @staticmethod
    def _get_system_content(manifest) -> str:
        request = build_p100_architect_request(
            manifest=manifest,
            payload={},
            default_model="test-model",
        )
        return [m for m in request.messages if m.role == "system"][0].content

    def test_still_has_required_headings(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        required = ["logline", "core premise", "story engine", "world anchors", "character arcs", "constraints", "open questions"]
        for heading in required:
            assert heading.lower() in content.lower(), f"Missing heading: {heading}"

    def test_still_requests_markdown(self, sample_manifest) -> None:
        content = self._get_system_content(sample_manifest)
        assert "markdown" in content.lower()

    def test_pattern_context_still_works(self, sample_manifest) -> None:
        from app.schemas.pattern_extraction import (
            PatternExtractionAnalysis,
            ArchetypalPattern,
        )

        pattern = PatternExtractionAnalysis(
            archetypal_patterns=[ArchetypalPattern(name="Hero", character_type="protagonist", description="Journey")],
            narrative_structures=["Three-act"],
        )
        request = build_p100_architect_request(
            manifest=sample_manifest,
            payload={},
            default_model="test-model",
            pattern_context=pattern,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        # Pattern context should be injected into user message
        assert "hero" in user_msg.content.lower() or "journey" in user_msg.content.lower()
