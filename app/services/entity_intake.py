from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from ..inference.base import InferenceBackend, InferenceBackendError
from .runtime_prompts import build_entity_intake_request

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NewEntity:
    name: str
    entity_type: str  # "character" or "location"
    inferred_archetype: str
    inferred_goal: str
    raw_evidence: str


def extract_proper_noun_candidates(text: str) -> list[str]:
    """Extract potential character names from text (capitalized words that look like names)."""
    # Match capitalized words at start of sentences or after quotes
    candidates: set[str] = set()
    for match in re.finditer(r'(?:^|(?<=[\s,"\'\-\n]))([A-Z][a-z]{2,})(?=\s)', text):
        word = match.group(1)
        # Filter out common non-name capitalized words
        if word.lower() not in {"the", "this", "that", "with", "from", "after", "before"}:
            candidates.add(word)
    return sorted(candidates)


class EntityIntakeService:
    MAX_ENTITIES_PER_DRAFT = 3

    def __init__(self, inferencer: InferenceBackend) -> None:
        self._inferencer = inferencer

    def intake_new_entities(
        self,
        draft_text: str,
        known_character_ids: dict[str, str],
    ) -> list[NewEntity]:
        candidates = extract_proper_noun_candidates(draft_text)
        unknowns = [c for c in candidates if c not in known_character_ids]

        if not unknowns:
            return []

        entities: list[NewEntity] = []
        for name in unknowns[: self.MAX_ENTITIES_PER_DRAFT]:
            try:
                request = build_entity_intake_request(
                    candidate_name=name,
                    draft_excerpt=draft_text[:4000],
                    default_model=self._inferencer.descriptor.default_model,
                )
                response = self._inferencer.generate_text(request)
                result = json.loads(response.content)

                entities.append(
                    NewEntity(
                        name=result.get("name", name),
                        entity_type="character",
                        inferred_archetype=result.get("archetype", "unknown"),
                        inferred_goal=result.get("goal", ""),
                        raw_evidence=draft_text[:500],
                    )
                )
            except (InferenceBackendError, json.JSONDecodeError) as exc:
                logger.warning("Entity intake failed for '%s': %s", name, exc)

        return entities
