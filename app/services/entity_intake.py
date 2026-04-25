from __future__ import annotations

import re
from dataclasses import dataclass


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
    for match in re.finditer(r'(?<=[\s,"\'\-\n])([A-Z][a-z]{2,})(?=\s)', text):
        word = match.group(1)
        # Filter out common non-name capitalized words
        if word.lower() not in {"the", "this", "that", "with", "from", "after", "before"}:
            candidates.add(word)
    return sorted(candidates)
