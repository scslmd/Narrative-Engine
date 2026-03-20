from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_request_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def request_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_request_json(payload).encode("utf-8")).hexdigest()


def job_request_scope(*, phase: str, project_id: str | None) -> str:
    return f"{phase}:{project_id or '-'}"


def checker_request_scope(*, roles: list[str], critic_profile: str) -> str:
    ordered_roles = ",".join(sorted(str(role) for role in roles))
    return f"checker:{ordered_roles}:{critic_profile}"
