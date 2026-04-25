from __future__ import annotations

import pytest
from app.services.entity_intake import NewEntity


def test_new_entity_dataclass():
    entity = NewEntity(
        name="Soraya",
        entity_type="character",
        inferred_archetype="mysterious ally",
        inferred_goal="Protect the caravan",
        raw_evidence="Soraya watched from the shadows, her hand never far from her dagger.",
    )
    assert entity.name == "Soraya"
    assert entity.entity_type == "character"


def test_extract_proper_noun_candidates():
    from app.services.entity_intake import extract_proper_noun_candidates

    text = "Khal marched ahead while Soraya watched from the shadows."
    candidates = extract_proper_noun_candidates(text)
    assert "Soraya" in candidates
