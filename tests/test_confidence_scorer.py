from __future__ import annotations

import pytest

from app.services.confidence_scorer import ConfidenceScorer


@pytest.fixture
def scorer():
    return ConfidenceScorer()


def test_high_confidence_character(scorer):
    score = scorer.score_character(
        display_name="Test Character",
        mention_count=10,
        non_empty_fields=8,
        total_fields=12,
        relationship_count=3,
        llm_confidence=0.9,
    )
    assert score >= 0.7


def test_low_confidence_character(scorer):
    score = scorer.score_character(
        display_name="Test Character",
        mention_count=1,
        non_empty_fields=2,
        total_fields=12,
        relationship_count=0,
        llm_confidence=0.3,
    )
    assert score < 0.4


def test_relationship_confidence(scorer):
    score = scorer.score_relationship(
        explicit_mention=True,
        dialogue_context=True,
        llm_confidence=0.85,
    )
    assert score >= 0.6


def test_world_entry_confidence(scorer):
    score = scorer.score_world_entry(
        mention_count=5,
        description_fields=4,
        total_fields=5,
        llm_confidence=0.7,
    )
    assert score >= 0.6


def test_threshold_classification(scorer):
    assert scorer.classify(0.85) == "high"
    assert scorer.classify(0.55) == "medium"
    assert scorer.classify(0.25) == "low"
