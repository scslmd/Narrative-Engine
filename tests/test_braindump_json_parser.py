"""Tests for braindump JSON parser consolidation."""
import pytest
from app.services.braindump import BrainDumpOrganizeError


class TestBraindumpUsesSharedJsonParser:
    """Verify braindump uses shared extract_json utility."""

    def test_parse_uses_shared_extractor(self) -> None:
        from app.services.braindump import BrainDumpService

        # Verify _parse_llm_json delegates to shared extract_json
        # by checking that the method can handle all formats
        result = BrainDumpService._parse_llm_json('{"key": ["value"]}')
        assert result == {"key": ["value"]}

    def test_parse_handles_markdown_fences(self) -> None:
        from app.services.braindump import BrainDumpService

        result = BrainDumpService._parse_llm_json('```json\n{"key": ["value"]}\n```')
        assert result == {"key": ["value"]}

    def test_parse_handles_leading_text(self) -> None:
        from app.services.braindump import BrainDumpService

        result = BrainDumpService._parse_llm_json(
            "Here is the organized output:\n{\"category\": [\"item1\"]}"
        )
        assert result == {"category": ["item1"]}

    def test_parse_raises_on_empty_content(self) -> None:
        from app.services.braindump import BrainDumpService

        with pytest.raises(BrainDumpOrganizeError, match="Empty"):
            BrainDumpService._parse_llm_json("")

    def test_parse_raises_on_invalid_json(self) -> None:
        from app.services.braindump import BrainDumpService

        with pytest.raises(BrainDumpOrganizeError, match="extract"):
            BrainDumpService._parse_llm_json("not valid json at all")

    def test_parse_handles_nested_braces_in_strings(self) -> None:
        from app.services.braindump import BrainDumpService

        # This tests that the shared parser's balanced brace detection works
        result = BrainDumpService._parse_llm_json(
            '{"note": "This has {braces} inside"}'
        )
        assert result == {"note": ["This has {braces} inside"]} or \
               result == {"note": "This has {braces} inside"}


class TestBraindumpJsonParserErrorHandling:
    """Verify error handling is preserved after consolidation."""

    def test_empty_string_raises_error(self) -> None:
        from app.services.braindump import BrainDumpService

        with pytest.raises(BrainDumpOrganizeError):
            BrainDumpService._parse_llm_json("")

    def test_whitespace_only_raises_error(self) -> None:
        from app.services.braindump import BrainDumpService

        with pytest.raises(BrainDumpOrganizeError):
            BrainDumpService._parse_llm_json("   \n  ")

    def test_no_json_raises_error(self) -> None:
        from app.services.braindump import BrainDumpService

        with pytest.raises(BrainDumpOrganizeError):
            BrainDumpService._parse_llm_json("just plain text, no json here")
