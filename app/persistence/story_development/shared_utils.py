from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def now(now_value: datetime | None = None) -> datetime:
    return now_value or datetime.now(timezone.utc)


def json_list(values: list[str] | None) -> str:
    return json.dumps(list(values or []), ensure_ascii=True, sort_keys=True)


def parse_json_list(value: str | None) -> list[str]:
    return list(json.loads(value or "[]"))


def json_objects(values: Sequence[Mapping[str, Any]] | None) -> str:
    return json.dumps([dict(value) for value in values or []], ensure_ascii=True, sort_keys=True)


def json_object(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=True, sort_keys=True)


def parse_json_objects(value: str | None) -> list[dict[str, Any]]:
    raw = json.loads(value or "[]")
    if not isinstance(raw, list):
        raise TypeError("expected a JSON list")
    return [dict(item) for item in raw]


def parse_json_object(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    raw = json.loads(value)
    if not isinstance(raw, dict):
        raise TypeError("expected a JSON object")
    return dict(raw)
