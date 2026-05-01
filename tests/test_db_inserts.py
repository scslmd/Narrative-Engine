from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.utils.db_inserts import (
    CharacterInsertData,
    hash_id,
    insert_character_profile,
    insert_foundation_profile,
    insert_relationship_edge,
    insert_world_bible_entry,
    json_safe,
    next_revision_number,
    update_foundation_revision_id,
)

SCHEMA_SQL = """
CREATE TABLE foundation_profiles (
    project_id TEXT PRIMARY KEY,
    current_revision_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE foundation_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    revision_number INTEGER NOT NULL,
    premise TEXT NOT NULL,
    logline TEXT NOT NULL,
    thematic_spine TEXT,
    emotional_promise TEXT,
    tone_direction TEXT,
    target_audience TEXT,
    narrative_constraints_json TEXT NOT NULL DEFAULT '[]',
    complexity_level TEXT,
    success_definition TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, revision_number)
);

CREATE TABLE character_profiles (
    character_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role_in_story TEXT,
    archetype TEXT,
    external_goal TEXT,
    internal_need TEXT,
    misbelief_or_wound TEXT,
    core_fear TEXT,
    primary_strength TEXT,
    fatal_flaw_or_limitation TEXT,
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    backstory_summary TEXT,
    voice_notes TEXT,
    relationship_map_json TEXT NOT NULL DEFAULT '[]',
    secrets_json TEXT NOT NULL DEFAULT '[]',
    values_json TEXT NOT NULL DEFAULT '[]',
    taboos_json TEXT NOT NULL DEFAULT '[]',
    change_axis TEXT,
    arc_stage_notes TEXT,
    continuity_facts_json TEXT NOT NULL DEFAULT '[]',
    writer_notes TEXT,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    physical_description TEXT,
    personality_traits_json TEXT NOT NULL DEFAULT '[]',
    motives TEXT,
    relationships_json TEXT NOT NULL DEFAULT '[]',
    character_arc TEXT,
    symbolic_role TEXT,
    dialogue_patterns TEXT,
    psychological_depth TEXT,
    narrative_purpose TEXT,
    thematic_significance TEXT,
    impact_on_others TEXT,
    first_appearance_chapter TEXT,
    chapter_appearances_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE relationship_edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_character_id TEXT NOT NULL,
    target_character_id TEXT NOT NULL,
    relation_kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    tension TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE world_bible_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    canonical_facts_json TEXT NOT NULL DEFAULT '[]',
    related_character_ids_json TEXT NOT NULL DEFAULT '[]',
    visibility_scope TEXT NOT NULL DEFAULT 'project',
    source_artifacts_json TEXT NOT NULL DEFAULT '[]',
    continuity_warnings_json TEXT NOT NULL DEFAULT '[]',
    writer_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, entry_type, title)
);
"""


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.db"
    c = sqlite3.connect(str(db_path))
    c.executescript(SCHEMA_SQL)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# hash_id
# ---------------------------------------------------------------------------

class TestHashId:
    def test_stable_id(self):
        assert hash_id("prefix", "value") == hash_id("prefix", "value")

    def test_different_prefixes_produce_different_ids(self):
        id_a = hash_id("prefix-a", "value")
        id_b = hash_id("prefix-b", "value")
        assert id_a != id_b
        assert id_a.startswith("prefix-a-")
        assert id_b.startswith("prefix-b-")

    def test_different_values_produce_different_ids(self):
        id_a = hash_id("prefix", "value-a")
        id_b = hash_id("prefix", "value-b")
        assert id_a != id_b

    def test_case_insensitive_value(self):
        assert hash_id("p", "Hello") == hash_id("p", "hello")

    def test_whitespace_stripped(self):
        assert hash_id("p", "  value  ") == hash_id("p", "value")

    def test_format_prefix_dash_hash(self):
        result = hash_id("my-prefix", "test")
        parts = result.split("-")
        assert len(parts) >= 3  # prefix parts + hash


# ---------------------------------------------------------------------------
# json_safe
# ---------------------------------------------------------------------------

class TestJsonSafe:
    def test_serializes_dict(self):
        result = json_safe({"b": 2, "a": 1})
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_sort_keys(self):
        result = json_safe({"z": 1, "a": 2})
        assert '"a"' in result and result.index('"a"') < result.index('"z"')

    def test_ensure_ascii(self):
        result = json_safe({"key": "café"})
        assert "caf\\u00e9" in result

    def test_serializes_list(self):
        assert json_safe([1, 2, 3]) == "[1, 2, 3]"

    def test_empty_list(self):
        assert json_safe([]) == "[]"


# ---------------------------------------------------------------------------
# next_revision_number
# ---------------------------------------------------------------------------

class TestNextRevisionNumber:
    def test_first_revision(self, conn):
        conn.execute(
            "INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at) "
            "VALUES ('p1', NULL, 'now', 'now')"
        )
        assert next_revision_number(conn, "p1") == 1

    def test_second_revision(self, conn):
        conn.execute(
            "INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at) "
            "VALUES ('p1', NULL, 'now', 'now')"
        )
        conn.execute(
            "INSERT INTO foundation_revisions (project_id, revision_number, premise, logline, "
            "narrative_constraints_json, created_at, updated_at) VALUES ('p1', 1, '', '', '[]', 'now', 'now')"
        )
        assert next_revision_number(conn, "p1") == 2

    def test_skips_gaps(self, conn):
        conn.execute(
            "INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at) "
            "VALUES ('p1', NULL, 'now', 'now')"
        )
        conn.execute(
            "INSERT INTO foundation_revisions (project_id, revision_number, premise, logline, "
            "narrative_constraints_json, created_at, updated_at) VALUES ('p1', 3, '', '', '[]', 'now', 'now')"
        )
        assert next_revision_number(conn, "p1") == 4

    def test_no_revisions_yet(self, conn):
        # No foundation_profiles row either -- still returns 1
        assert next_revision_number(conn, "nonexistent") == 1


# ---------------------------------------------------------------------------
# insert_foundation_profile
# ---------------------------------------------------------------------------

class TestInsertFoundationProfile:
    def test_creates_profile_and_revision(self, conn):
        now = "2026-01-01T00:00:00+00:00"
        next_rev = next_revision_number(conn, "p1")
        rev_id = insert_foundation_profile(
            conn, "p1", now, next_rev, thematic_spine="test spine"
        )

        row = conn.execute("SELECT project_id, current_revision_id FROM foundation_profiles WHERE project_id = ?", ("p1",)).fetchone()
        assert row[0] == "p1"

        rev_row = conn.execute(
            "SELECT revision_number, thematic_spine FROM foundation_revisions WHERE revision_id = ?", (rev_id,)
        ).fetchone()
        assert rev_row[0] == 1
        assert rev_row[1] == "test spine"

    def test_upsert_updates_existing_revision(self, conn):
        now = "2026-01-01T00:00:00+00:00"
        insert_foundation_profile(conn, "p1", now, 1, premise="first")
        insert_foundation_profile(conn, "p1", now, 1, premise="updated")

        row = conn.execute(
            "SELECT premise FROM foundation_revisions WHERE project_id = ? AND revision_number = 1", ("p1",)
        ).fetchone()
        assert row[0] == "updated"

    def test_returns_revision_id(self, conn):
        now = "2026-01-01T00:00:00+00:00"
        next_rev = next_revision_number(conn, "p1")
        rev_id = insert_foundation_profile(conn, "p1", now, next_rev)
        assert isinstance(rev_id, int) and rev_id > 0

    def test_full_params(self, conn):
        now = "2026-01-01T00:00:00+00:00"
        next_rev = next_revision_number(conn, "p1")
        rev_id = insert_foundation_profile(
            conn, "p1", now, next_rev,
            premise="A story", logline="Short line", thematic_spine="Spine",
            emotional_promise="Promise", tone_direction="Dark",
            target_audience="Adults", constraints_json='{"key": "val"}',
            complexity_level="high", success_definition="win",
        )
        row = conn.execute(
            "SELECT premise, logline, thematic_spine, emotional_promise, tone_direction, "
            "target_audience, narrative_constraints_json, complexity_level, success_definition "
            "FROM foundation_revisions WHERE revision_id = ?", (rev_id,)
        ).fetchone()
        assert row[0] == "A story"
        assert row[1] == "Short line"
        assert row[2] == "Spine"
        assert row[3] == "Promise"
        assert row[4] == "Dark"
        assert row[5] == "Adults"
        assert row[6] == '{"key": "val"}'
        assert row[7] == "high"
        assert row[8] == "win"


# ---------------------------------------------------------------------------
# update_foundation_revision_id
# ---------------------------------------------------------------------------

class TestUpdateFoundationRevisionId:
    def test_sets_revision_id(self, conn):
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at) "
            "VALUES ('p1', NULL, ?, ?)", (now, now)
        )
        update_foundation_revision_id(conn, "p1", 42, now)

        row = conn.execute(
            "SELECT current_revision_id FROM foundation_profiles WHERE project_id = ?", ("p1",)
        ).fetchone()
        assert row[0] == 42


# ---------------------------------------------------------------------------
# insert_world_bible_entry
# ---------------------------------------------------------------------------

class TestInsertWorldBibleEntry:
    def test_creates_entry(self, conn):
        insert_world_bible_entry(conn, "p1", "concept", "Test Title", summary="A summary")

        row = conn.execute(
            "SELECT entry_type, title, summary FROM world_bible_entries WHERE project_id = ?", ("p1",)
        ).fetchone()
        assert row[0] == "concept"
        assert row[1] == "Test Title"
        assert row[2] == "A summary"

    def test_defaults_for_optional_fields(self, conn):
        insert_world_bible_entry(conn, "p1", "location", "Some Place")

        row = conn.execute(
            "SELECT summary, canonical_facts_json, visibility_scope FROM world_bible_entries WHERE project_id = ?", ("p1",)
        ).fetchone()
        assert row[0] is None
        assert row[1] == json_safe([])
        assert row[2] == "project"

    def test_upsert_updates_existing_entry(self, conn):
        insert_world_bible_entry(conn, "p1", "concept", "Title", summary="old")
        insert_world_bible_entry(conn, "p1", "concept", "Title", summary="new")

        row = conn.execute(
            "SELECT summary FROM world_bible_entries WHERE project_id = ? AND title = ?", ("p1", "Title")
        ).fetchone()
        assert row[0] == "new"

    def test_canonical_facts_default(self, conn):
        insert_world_bible_entry(conn, "p1", "concept", "Title")
        row = conn.execute(
            "SELECT canonical_facts_json FROM world_bible_entries WHERE project_id = ?", ("p1",)
        ).fetchone()
        assert row[0] == json_safe([])


# ---------------------------------------------------------------------------
# insert_character_profile
# ---------------------------------------------------------------------------

class TestInsertCharacterProfile:
    def test_creates_profile(self, conn):
        insert_character_profile(conn, CharacterInsertData(
            character_id="char-1", project_id="p1",
            display_name="Hero", role_in_story="protagonist",
        ))

        row = conn.execute(
            "SELECT display_name, role_in_story FROM character_profiles WHERE character_id = ?", ("char-1",)
        ).fetchone()
        assert row[0] == "Hero"
        assert row[1] == "protagonist"

    def test_full_params(self, conn):
        insert_character_profile(conn, CharacterInsertData(
            character_id="char-2", project_id="p1",
            display_name="Villain", role_in_story="antagonist",
            archetype="shadow", external_goal="destroy", core_fear="failure",
            fatal_flaw="pride", contradictions_json='["brave but cautious"]',
        ))

        row = conn.execute(
            "SELECT archetype, external_goal, core_fear, fatal_flaw_or_limitation, contradictions_json "
            "FROM character_profiles WHERE character_id = ?", ("char-2",)
        ).fetchone()
        assert row[0] == "shadow"
        assert row[1] == "destroy"
        assert row[2] == "failure"
        assert row[3] == "pride"
        assert row[4] == '["brave but cautious"]'

    def test_upsert_updates(self, conn):
        insert_character_profile(conn, CharacterInsertData(
            character_id="char-1", project_id="p1",
            display_name="Old Name", role_in_story="role",
        ))
        insert_character_profile(conn, CharacterInsertData(
            character_id="char-1", project_id="p1",
            display_name="New Name", role_in_story="updated role",
        ))

        row = conn.execute(
            "SELECT display_name, role_in_story FROM character_profiles WHERE character_id = ?", ("char-1",)
        ).fetchone()
        assert row[0] == "New Name"
        assert row[1] == "updated role"


# ---------------------------------------------------------------------------
# insert_relationship_edge
# ---------------------------------------------------------------------------

class TestInsertRelationshipEdge:
    def test_creates_edge(self, conn):
        insert_relationship_edge(conn, "edge-1", "p1", "char-a", "char-b", "rivalry", "They fight")

        row = conn.execute(
            "SELECT source_character_id, target_character_id, relation_kind, summary "
            "FROM relationship_edges WHERE edge_id = ?", ("edge-1",)
        ).fetchone()
        assert row[0] == "char-a"
        assert row[1] == "char-b"
        assert row[2] == "rivalry"
        assert row[3] == "They fight"

    def test_defaults_for_optional_fields(self, conn):
        insert_relationship_edge(conn, "edge-2", "p1", "a", "b", "ally")

        row = conn.execute(
            "SELECT summary, tension, notes FROM relationship_edges WHERE edge_id = ?", ("edge-2",)
        ).fetchone()
        assert row[0] == ""
        assert row[1] is None
        assert row[2] is None

    def test_upsert_updates(self, conn):
        insert_relationship_edge(conn, "edge-1", "p1", "a", "b", "rivalry", "old")
        insert_relationship_edge(conn, "edge-1", "p1", "x", "y", "ally", "new")

        row = conn.execute(
            "SELECT source_character_id, relation_kind, summary FROM relationship_edges WHERE edge_id = ?", ("edge-1",)
        ).fetchone()
        assert row[0] == "x"
        assert row[1] == "ally"
        assert row[2] == "new"
