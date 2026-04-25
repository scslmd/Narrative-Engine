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
    STOP_WORDS = {
        "the", "this", "that", "with", "from", "after", "before", "chapter",
        "then", "when", "where", "what", "which", "while", "who", "how",
        "upon", "within", "without", "against", "among", "between",
        "during", "since", "until", "toward", "through", "along",
        "also", "only", "even", "just", "very", "much", "more", "most",
    }
    candidates: set[str] = set()
    for match in re.finditer(r'(?:^|(?<=[\s,"\'\-\n]))([A-Z][a-z]{2,})(?=\s)', text):
        word = match.group(1)
        if word.lower() not in STOP_WORDS:
            candidates.add(word)
    return sorted(candidates)


def truncate_at_sentence(text: str, max_chars: int = 500) -> str:
    """Truncate text at a sentence boundary to avoid cutting mid-sentence."""
    if len(text) <= max_chars:
        return text
    # Try to find sentence end within budget
    for delim in (". ", "!\n", "?\n", ".\n", "!\t", "?\t"):
        last = text.rfind(delim, 0, max_chars)
        if last >= 0:
            return text[: last + len(delim)].rstrip()
    # Fallback: truncate at last space
    last_space = text.rfind(" ", 0, max_chars)
    if last_space >= 0:
        return text[:last_space]
    return text[:max_chars]


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
                        raw_evidence=truncate_at_sentence(draft_text, max_chars=500),
                    )
                )
            except (InferenceBackendError, json.JSONDecodeError) as exc:
                logger.warning("Entity intake failed for '%s': %s", name, exc)

        return entities
