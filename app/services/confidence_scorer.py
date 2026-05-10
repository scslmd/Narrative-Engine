from __future__ import annotations

from app.settings import settings


class ConfidenceScorer:
    def score_character(
        self,
        display_name: str,
        mention_count: int,
        non_empty_fields: int,
        total_fields: int,
        relationship_count: int,
        llm_confidence: float,
    ) -> float:
        mention_weight = min(mention_count / 5, 1.0)
        description_weight = min(non_empty_fields / max(total_fields, 1), 1.0)
        interaction_weight = min(relationship_count / 3, 1.0)
        return (
            mention_weight * 0.30
            + description_weight * 0.30
            + interaction_weight * 0.25
            + llm_confidence * 0.15
        )

    def score_relationship(
        self,
        explicit_mention: bool,
        dialogue_context: bool,
        llm_confidence: float,
    ) -> float:
        explicit_weight = 1.0 if explicit_mention else 0.4
        context_weight = 1.0 if dialogue_context else 0.5
        return (
            explicit_weight * 0.35
            + context_weight * 0.25
            + llm_confidence * 0.40
        )

    def score_world_entry(
        self,
        mention_count: int,
        description_fields: int,
        total_fields: int,
        llm_confidence: float,
    ) -> float:
        mention_weight = min(mention_count / 5, 1.0)
        description_weight = min(description_fields / max(total_fields, 1), 1.0)
        return (
            mention_weight * 0.30
            + description_weight * 0.35
            + llm_confidence * 0.35
        )

    def classify(self, score: float) -> str:
        if score >= settings.discovery_confidence_threshold_high:
            return "high"
        if score >= settings.discovery_confidence_threshold_medium:
            return "medium"
        return "low"
