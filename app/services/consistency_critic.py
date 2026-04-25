from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from ..inference.base import InferenceBackend, InferenceBackendError
from .runtime_prompts import build_critic_check_request

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Violation:
    character: str
    issue: str
    suggestion: str


@dataclass(slots=True)
class CriticResult:
    passed: bool
    violations: list[Violation]


class ConsistencyCriticService:
    def __init__(self, inferencer: InferenceBackend) -> None:
        self._inferencer = inferencer

    def check(
        self,
        draft_text: str,
        character_bios: dict[str, str],
    ) -> CriticResult:
        if not character_bios:
            return CriticResult(passed=True, violations=[])

        try:
            request = build_critic_check_request(
                draft_text=draft_text,
                character_bios=character_bios,
                default_model=self._inferencer.descriptor.default_model,
            )
            response = self._inferencer.generate_text(request)
            result = json.loads(response.content)

            violations = []
            for v in result.get("violations", []):
                violations.append(Violation(
                    character=v["character"],
                    issue=v["issue"],
                    suggestion=v["suggestion"],
                ))
            return CriticResult(passed=result.get("passed", True), violations=violations)

        except (InferenceBackendError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("Critic check failed, proceeding with draft: %s", exc)
            return CriticResult(passed=True, violations=[])
