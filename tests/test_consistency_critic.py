from __future__ import annotations

import json
import pytest
from app.schemas.inference import InferenceResponse, InferenceUsage
from app.services.consistency_critic import ConsistencyCriticService, CriticResult, Violation


class FakeInferencerPassed:
    descriptor = type('Descriptor', (), {'default_model': 'test'})()

    def generate_text(self, request):
        return InferenceResponse(
            model='test', content=json.dumps({"passed": True, "violations": []}),
            backend='stub', finish_reason='completed', usage=InferenceUsage(),
        )


class FakeInferencerFailed:
    descriptor = type('Descriptor', (), {'default_model': 'test'})()

    def generate_text(self, request):
        return InferenceResponse(
            model='test',
            content=json.dumps({
                "passed": False,
                "violations": [
                    {"character": "Khal", "issue": "Uses flowery language", "suggestion": "Make terse"}
                ]
            }),
            backend='stub', finish_reason='completed', usage=InferenceUsage(),
        )


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


def test_critic_passes_consistent_draft():
    service = ConsistencyCriticService(inferencer=FakeInferencerPassed())
    result = service.check(
        draft_text="Khal said, 'We need to move.'",
        character_bios={"Khal": "archetype: reluctant hero; voice: direct, terse"},
    )
    assert result.passed is True


def test_critic_fails_inconsistent_draft():
    service = ConsistencyCriticService(inferencer=FakeInferencerFailed())
    result = service.check(
        draft_text="Khal said, 'Oh, the beautiful sunset paints the sky with whispers of amber.'",
        character_bios={"Khal": "archetype: reluctant hero; voice: direct, terse"},
    )
    assert result.passed is False
    assert len(result.violations) == 1


def test_critic_empty_bios_passes():
    service = ConsistencyCriticService(inferencer=FakeInferencerPassed())
    result = service.check(
        draft_text="Some dialogue here.",
        character_bios={},
    )
    assert result.passed is True
    assert len(result.violations) == 0
