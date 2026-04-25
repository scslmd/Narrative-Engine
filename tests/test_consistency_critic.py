from __future__ import annotations

import pytest
from app.services.consistency_critic import CriticResult, Violation


def test_critic_result_passed():
    result = CriticResult(passed=True, violations=[])
    assert result.passed is True
    assert len(result.violations) == 0


def test_critic_result_with_violations():
    v = Violation(character="Khal", issue="Uses flowery language", suggestion="Make dialogue more terse")
    result = CriticResult(passed=False, violations=[v])
    assert result.passed is False
    assert len(result.violations) == 1
    assert result.violations[0].character == "Khal"
