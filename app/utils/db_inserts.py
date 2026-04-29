from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value."""
    raw = f"{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{short_hash}"


def json_safe(obj: Any) -> str:
    """Serialize to JSON with consistent formatting for DB storage."""
    return json.dumps(obj, ensure_ascii=True, sort_keys=True)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def next_revision_number(conn, project_id: str) -> int:
    """Compute the next revision number for a project.

    Uses a single SELECT on foundation_revisions. The INSERT that
    follows must be in the same IMMEDIATE transaction to be safe.
    """
    row = conn.execute(
        "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return row[0]


def insert_foundation_profile(
    conn,
    project_id: str,
    now: str,
    next_rev: int,
    premise: str = "",
    logline: str = "",
    thematic_spine: str | None = None,
    emotional_promise: str | None = None,
    tone_direction: str | None = None,
    target_audience: str | None = None,
    constraints_json: str = "[]",
    complexity_level: str | None = None,
    success_definition: str | None = None,
) -> int:
    """Insert foundation_profiles header + foundation_revisions row.

    Returns the rowid of the inserted revision.
    """
    conn.execute(
        """
        INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
        VALUES (?, NULL, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (project_id, now, now),
    )

    conn.execute(
        """
        INSERT INTO foundation_revisions (
            project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
            tone_direction, target_audience, narrative_constraints_json, complexity_level,
            success_definition, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, revision_number) DO UPDATE SET
            premise = excluded.premise,
            logline = excluded.logline,
            thematic_spine = excluded.thematic_spine,
            emotional_promise = excluded.emotional_promise,
            tone_direction = excluded.tone_direction,
            target_audience = excluded.target_audience,
            narrative_constraints_json = excluded.narrative_constraints_json,
            complexity_level = excluded.complexity_level,
            success_definition = excluded.success_definition,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            next_rev,
            premise,
            logline,
            thematic_spine,
            emotional_promise,
            tone_direction,
            target_audience,
            constraints_json,
            complexity_level,
            success_definition,
            now,
            now,
        ),
    )

    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_foundation_revision_id(conn, project_id: str, revision_id: int, now: str) -> None:
    """Set current_revision_id on foundation_profiles."""
    conn.execute(
        "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
        (revision_id, now, project_id),
    )


def insert_world_bible_entry(
    conn,
    project_id: str,
    entry_type: str,
    title: str,
    summary: str | None = None,
    canonical_facts_json: str | None = None,
    related_character_ids_json: str = "[]",
    source_artifacts_json: str = "[]",
    continuity_warnings_json: str = "[]",
    visibility_scope: str = "project",
    writer_notes: str | None = None,
) -> None:
    """Insert a world_bible_entry row."""
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO world_bible_entries (
            project_id, entry_type, title, summary, canonical_facts_json,
            related_character_ids_json, visibility_scope, source_artifacts_json,
            continuity_warnings_json, writer_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
            summary = excluded.summary,
            canonical_facts_json = excluded.canonical_facts_json,
            related_character_ids_json = excluded.related_character_ids_json,
            visibility_scope = excluded.visibility_scope,
            source_artifacts_json = excluded.source_artifacts_json,
            continuity_warnings_json = excluded.continuity_warnings_json,
            writer_notes = excluded.writer_notes,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            entry_type,
            title,
            summary,
            canonical_facts_json or json_safe([]),
            related_character_ids_json,
            visibility_scope,
            source_artifacts_json,
            continuity_warnings_json,
            writer_notes,
            now,
            now,
        ),
    )


def insert_character_profile(
    conn,
    character_id: str,
    project_id: str,
    display_name: str,
    role_in_story: str,
    archetype: str | None = None,
    external_goal: str | None = None,
    internal_need: str | None = None,
    misbelief_or_wound: str | None = None,
    core_fear: str | None = None,
    primary_strength: str | None = None,
    fatal_flaw: str | None = None,
    contradictions_json: str = "[]",
    backstory_summary: str | None = None,
    voice_notes: str | None = None,
    relationship_map_json: str = "[]",
    secrets_json: str = "[]",
    values_json: str = "[]",
    taboos_json: str = "[]",
    change_axis: str | None = None,
    arc_stage_notes: str | None = None,
    continuity_facts_json: str = "[]",
    writer_notes: str | None = None,
    # Deep analysis fields (multi-pass import)
    aliases_json: str = "[]",
    physical_description: str | None = None,
    personality_traits_json: str = "[]",
    motives: str | None = None,
    relationships_json: str = "[]",
    character_arc: str | None = None,
    symbolic_role: str | None = None,
    dialogue_patterns: str | None = None,
    psychological_depth: str | None = None,
    narrative_purpose: str | None = None,
    thematic_significance: str | None = None,
    impact_on_others: str | None = None,
    first_appearance_chapter: str | None = None,
    chapter_appearances_json: str = "[]",
) -> None:
    """Insert a character_profiles row."""
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO character_profiles (
            character_id, project_id, display_name, role_in_story, archetype,
            external_goal, internal_need, misbelief_or_wound, core_fear,
            primary_strength, fatal_flaw_or_limitation, contradictions_json,
            backstory_summary, voice_notes, relationship_map_json, secrets_json,
            values_json, taboos_json, change_axis, arc_stage_notes,
            continuity_facts_json, writer_notes,
            aliases_json, physical_description, personality_traits_json,
            motives, relationships_json, character_arc, symbolic_role,
            dialogue_patterns, psychological_depth, narrative_purpose,
            thematic_significance, impact_on_others, first_appearance_chapter,
            chapter_appearances_json,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(character_id) DO UPDATE SET
            project_id = excluded.project_id,
            display_name = excluded.display_name,
            role_in_story = excluded.role_in_story,
            archetype = excluded.archetype,
            external_goal = excluded.external_goal,
            internal_need = excluded.internal_need,
            misbelief_or_wound = excluded.misbelief_or_wound,
            core_fear = excluded.core_fear,
            primary_strength = excluded.primary_strength,
            fatal_flaw_or_limitation = excluded.fatal_flaw_or_limitation,
            contradictions_json = excluded.contradictions_json,
            backstory_summary = excluded.backstory_summary,
            voice_notes = excluded.voice_notes,
            relationship_map_json = excluded.relationship_map_json,
            secrets_json = excluded.secrets_json,
            values_json = excluded.values_json,
            taboos_json = excluded.taboos_json,
            change_axis = excluded.change_axis,
            arc_stage_notes = excluded.arc_stage_notes,
            continuity_facts_json = excluded.continuity_facts_json,
            writer_notes = excluded.writer_notes,
            aliases_json = excluded.aliases_json,
            physical_description = excluded.physical_description,
            personality_traits_json = excluded.personality_traits_json,
            motives = excluded.motives,
            relationships_json = excluded.relationships_json,
            character_arc = excluded.character_arc,
            symbolic_role = excluded.symbolic_role,
            dialogue_patterns = excluded.dialogue_patterns,
            psychological_depth = excluded.psychological_depth,
            narrative_purpose = excluded.narrative_purpose,
            thematic_significance = excluded.thematic_significance,
            impact_on_others = excluded.impact_on_others,
            first_appearance_chapter = excluded.first_appearance_chapter,
            chapter_appearances_json = excluded.chapter_appearances_json,
            updated_at = excluded.updated_at
        """,
        (
            character_id,
            project_id,
            display_name,
            role_in_story,
            archetype,
            external_goal,
            internal_need,
            misbelief_or_wound,
            core_fear,
            primary_strength,
            fatal_flaw,
            contradictions_json,
            backstory_summary,
            voice_notes,
            relationship_map_json,
            secrets_json,
            values_json,
            taboos_json,
            change_axis,
            arc_stage_notes,
            continuity_facts_json,
            writer_notes,
            aliases_json,
            physical_description,
            personality_traits_json,
            motives,
            relationships_json,
            character_arc,
            symbolic_role,
            dialogue_patterns,
            psychological_depth,
            narrative_purpose,
            thematic_significance,
            impact_on_others,
            first_appearance_chapter,
            chapter_appearances_json,
            now,
            now,
        ),
    )


def insert_relationship_edge(
    conn,
    edge_id: str,
    project_id: str,
    source_character_id: str,
    target_character_id: str,
    relation_kind: str,
    summary: str = "",
    tension: str | None = None,
    notes: str | None = None,
) -> None:
    """Insert a relationship_edges row."""
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO relationship_edges (
            edge_id, project_id, source_character_id, target_character_id,
            relation_kind, summary, tension, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(edge_id) DO UPDATE SET
            project_id = excluded.project_id,
            source_character_id = excluded.source_character_id,
            target_character_id = excluded.target_character_id,
            relation_kind = excluded.relation_kind,
            summary = excluded.summary,
            tension = excluded.tension,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (
            edge_id,
            project_id,
            source_character_id,
            target_character_id,
            relation_kind,
            summary,
            tension,
            notes,
            now,
            now,
        ),
    )
