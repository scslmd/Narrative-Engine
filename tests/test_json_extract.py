from __future__ import annotations

import json

from app.utils.json_extract import extract_json, parse_llm_json


class TestDirectParse:
    def test_simple_object(self):
        result = extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_nested_object(self):
        raw = json.dumps({"a": {"b": {"c": 1}}})
        result = extract_json(raw)
        assert result == {"a": {"b": {"c": 1}}}

    def test_empty_object(self):
        result = extract_json("{}")
        assert result == {}

    def test_array_in_object(self):
        raw = json.dumps({"items": [1, 2, 3]})
        result = extract_json(raw)
        assert result == {"items": [1, 2, 3]}

    def test_with_whitespace(self):
        result = extract_json('  {"key": "value"}  ')
        assert result == {"key": "value"}


class TestEmptyInput:
    def test_empty_string(self):
        assert extract_json("") is None

    def test_whitespace_only(self):
        assert extract_json("   \n\t  ") is None


class TestInvalidJson:
    def test_garbage_text(self):
        assert extract_json("this is not json at all") is None

    def test_malformed_braces(self):
        assert extract_json("{key: value}") is None

    def test_truncated_object(self):
        assert extract_json('{"key": "val') is None


class TestMarkdownFences:
    def test_with_json_tag(self):
        result = extract_json("```json\n{\"a\": 1}\n```")
        assert result == {"a": 1}

    def test_without_language_tag(self):
        result = extract_json("```\n{\"b\": 2}\n```")
        assert result == {"b": 2}

    def test_with_surrounding_whitespace(self):
        result = extract_json("  ```json\n{\"c\": 3}\n```  ")
        assert result == {"c": 3}

    def test_fenced_invalid_json_returns_none(self):
        assert extract_json("```json\n{invalid}\n```") is None


class TestBalancedBrace:
    def test_text_before_json(self):
        result = extract_json("Here is the result: {\"x\": 10}")
        assert result == {"x": 10}

    def test_text_after_json(self):
        result = extract_json('{"y": 20} and then some more text')
        assert result == {"y": 20}

    def test_nested_braces_in_strings(self):
        inner = json.dumps({"desc": "contains {braces}"})
        raw = f"prefix {inner} suffix"
        result = extract_json(raw)
        assert result == {"desc": "contains {braces}"}

    def test_escaped_quotes_in_strings(self):
        inner = json.dumps({"quote": "she said \"hello\""})
        raw = f"start {inner} end"
        result = extract_json(raw)
        assert result == {"quote": 'she said "hello"'}

    def test_deeply_nested_object(self):
        obj = {"a": {"b": {"c": {"d": "deep"}}}}
        raw = f"prefix {json.dumps(obj)} suffix"
        result = extract_json(raw)
        assert result == obj


class TestEdgeCases:
    def test_no_opening_brace(self):
        assert extract_json("just plain text without braces") is None

    def test_unclosed_brace(self):
        assert extract_json('{"key": "value"') is None

    def test_top_level_array_returns_none(self):
        assert extract_json("[1, 2, 3]") is None

    def test_top_level_string_returns_none(self):
        assert extract_json('"just a string"') is None

    def test_top_level_number_returns_none(self):
        assert extract_json("42") is None


class TestAlias:
    def test_parse_llm_json_is_alias(self):
        result = parse_llm_json('{"k": "v"}')
        assert result == {"k": "v"}

    def test_parse_llm_json_returns_none_on_failure(self):
        assert parse_llm_json("garbage") is None

    def test_parse_llm_json_same_as_extract_json(self):
        sample = "```json\n{\"test\": true}\n```"
        assert parse_llm_json(sample) == extract_json(sample)