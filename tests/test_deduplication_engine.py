from __future__ import annotations

import pytest

from app.services.deduplication_engine import DeduplicationEngine


@pytest.fixture
def engine():
    return DeduplicationEngine()


# -- match_character --


def test_exact_match(engine):
    existing = [{"character_id": "c1", "display_name": "Annabelle"}]
    result = engine.match_character("Annabelle", existing)
    assert result is not None
    assert result["match_type"] == "exact"
    assert result["character_id"] == "c1"


def test_case_insensitive_exact(engine):
    existing = [{"character_id": "c1", "display_name": "Annabelle"}]
    result = engine.match_character("annabelle", existing)
    assert result is not None
    assert result["match_type"] == "exact"


def test_fuzzy_match(engine):
    existing = [{"character_id": "c1", "display_name": "Annabella"}]
    result = engine.match_character("Annabelle", existing)
    assert result is not None
    assert result["match_type"] == "fuzzy"
    assert 0.85 <= result["confidence"] < 1.0


def test_no_match(engine):
    existing = [{"character_id": "c1", "display_name": "Boromir"}]
    result = engine.match_character("Annabelle", existing)
    assert result is None


def test_alias_exact_match(engine):
    existing = [{"character_id": "c1", "display_name": "Annabelle", "aliases": ["Lady Ann"]}]
    result = engine.match_character("Lady Ann", existing)
    assert result is not None
    assert result["match_type"] == "exact"


def test_fuzzy_alias_match(engine):
    existing = [{"character_id": "c1", "display_name": "Lady Annabelle", "aliases": ["Ann Bell"]}]
    result = engine.match_character("Anna Bell", existing)
    assert result is not None
    assert result["match_type"] == "fuzzy"


# -- match_world_entry --


def test_world_bible_exact(engine):
    existing = [{"entry_type": "location", "title": "Castle of Echoes"}]
    result = engine.match_world_entry("location", "Castle of Echoes", existing)
    assert result is not None
    assert result["match_type"] == "exact"


def test_world_bible_no_match_wrong_type(engine):
    existing = [{"entry_type": "artifact", "title": "Castle of Echoes"}]
    result = engine.match_world_entry("location", "Castle of Echoes", existing)
    assert result is None


def test_world_bible_case_insensitive(engine):
    existing = [{"entry_type": "LOCATION", "title": "castle of echoes"}]
    result = engine.match_world_entry("location", "Castle of Echoes", existing)
    assert result is not None
    assert result["match_type"] == "exact"


# -- deduplicate_relationship_pairs --


def test_relationship_pair_dedup(engine):
    pairs = [("Alice", "Bob"), ("Bob", "Alice")]
    result = engine.deduplicate_relationship_pairs(pairs)
    assert len(result) == 1


def test_relationship_pair_no_duplication(engine):
    pairs = [("A", "B"), ("C", "D")]
    result = engine.deduplicate_relationship_pairs(pairs)
    assert len(result) == 2


def test_relationship_self_pair(engine):
    pairs = [("Alice", "Bob"), ("alice", "bob"), ("BOB", "ALICE")]
    result = engine.deduplicate_relationship_pairs(pairs)
    assert len(result) == 1


# -- enrich_character --


def test_enrich_fills_empty_fields(engine):
    existing = {"character_id": "c1", "project_id": "p1", "display_name": "Annabelle", "backstory_summary": ""}
    new_data = {"backstory_summary": "A wandering knight"}
    result = engine.enrich_character(existing, new_data)
    assert result["backstory_summary"] == "A wandering knight"


def test_enrich_preserves_existing(engine):
    existing = {"character_id": "c1", "project_id": "p1", "display_name": "Annabelle", "backstory_summary": "Original"}
    new_data = {"backstory_summary": "New"}
    result = engine.enrich_character(existing, new_data)
    assert result["backstory_summary"] == "Original"


def test_enrich_appends_to_lists(engine):
    existing = {"character_id": "c1", "project_id": "p1", "aliases": ["Ann"]}
    new_data = {"aliases": ["Lady Ann", "Ann"]}
    result = engine.enrich_character(existing, new_data)
    assert "Ann" in result["aliases"]
    assert "Lady Ann" in result["aliases"]
    assert len(result["aliases"]) == 2


def test_enrich_does_not_override_id(engine):
    existing = {"character_id": "c1", "project_id": "p1", "display_name": "Annabelle"}
    new_data = {"character_id": "c2", "project_id": "p99"}
    result = engine.enrich_character(existing, new_data)
    assert result["character_id"] == "c1"
    assert result["project_id"] == "p1"
