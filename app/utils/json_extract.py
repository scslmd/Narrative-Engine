from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json(content: str) -> dict[str, Any] | None:
    """Extract a JSON object from LLM response text.

    Tries three strategies in order:
    1. Direct JSON parse of the stripped content
    2. Markdown fence stripping (```json` ... `````)
    3. Balanced brace detection starting from first '{'

    Returns None if all strategies fail. This is preferred over raising
    because callers handle failures differently (some raise, some return None).
    """
    stripped = content.strip()
    if not stripped:
        return None

    data: dict[str, Any] | None = None

    # Strategy 1: Direct parse
    try:
        data = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: Strip markdown fences
    if data is None:
        fenced = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE
        )
        fenced = fenced.strip()
        if fenced:
            try:
                data = json.loads(fenced)
            except (json.JSONDecodeError, ValueError):
                pass

    # Strategy 3: Balanced brace detection
    if data is None:
        first_brace = stripped.find("{")
        if first_brace != -1:
            depth = 0
            in_string = False
            escape_next = False
            json_end = -1
            for i in range(first_brace, len(stripped)):
                ch = stripped[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\":
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        json_end = i
                        break

            if json_end != -1:
                try:
                    data = json.loads(stripped[first_brace : json_end + 1])
                except (json.JSONDecodeError, ValueError):
                    pass

    if data is None:
        return None

    if not isinstance(data, dict):
        return None

    return data


def parse_llm_json(content: str) -> dict[str, Any] | None:
    """Alias for extract_json (backward compat with story_import naming)."""
    return extract_json(content)