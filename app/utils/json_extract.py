from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json(content: str) -> Any | None:
    """Extract a top-level JSON value from LLM response text.

    Tries three strategies in order:
    1. Direct JSON parse of the stripped content
    2. Markdown fence stripping (```json` ... `````)
    3. Balanced container detection starting from first '{' or '['

    Returns None if all strategies fail. This is preferred over raising
    because callers handle failures differently (some raise, some return None).
    """
    stripped = content.strip()
    if not stripped:
        return None

    data: Any | None = None

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

    # Strategy 3: Balanced container detection
    if data is None:
        object_start = stripped.find("{")
        array_start = stripped.find("[")
        container_start_candidates = [idx for idx in (object_start, array_start) if idx != -1]
        if container_start_candidates:
            first_container = min(container_start_candidates)
            opening = stripped[first_container]
            closing = "}" if opening == "{" else "]"
            depth = 0
            in_string = False
            escape_next = False
            json_end = -1
            for i in range(first_container, len(stripped)):
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
                if ch == opening:
                    depth += 1
                elif ch == closing:
                    depth -= 1
                    if depth == 0:
                        json_end = i
                        break

            if json_end != -1:
                try:
                    data = json.loads(stripped[first_container : json_end + 1])
                except (json.JSONDecodeError, ValueError):
                    pass

    if data is None:
        return None

    if not isinstance(data, (dict, list)):
        return None

    return data


def parse_llm_json(content: str) -> Any | None:
    """Alias for extract_json (backward compat with story_import naming)."""
    return extract_json(content)
