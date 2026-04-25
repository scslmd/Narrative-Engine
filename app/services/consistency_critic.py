from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Violation:
    character: str
    issue: str
    suggestion: str


@dataclass(slots=True)
class CriticResult:
    passed: bool
    violations: list[Violation]
