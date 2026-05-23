from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
    parse_json_list as _parse_json_list,
)
from . import CharacterProfileRecord, RelationshipEdgeRecord
from .converters import _character_row_to_record, _relationship_edge_row_to_record

from ..sqlite import connect


class _CharacterMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_character_profile(
        self,
        *,
        project_id: str,
        character_id: str,
        display_name: str,
        role_in_story: str | None = None,
        archetype: str | None = None,
        external_goal: str | None = None,
        internal_need: str | None = None,
        misbelief_or_wound: str | None = None,
        core_fear: str | None = None,
        primary_strength: str | None = None,
        fatal_flaw_or_limitation: str | None = None,
        contradictions: list[str] | None = None,
        backstory_summary: str | None = None,
        voice_notes: str | None = None,
        relationship_map: list[str] | None = None,
        secrets: list[str] | None = None,
        values: list[str] | None = None,
        taboos: list[str] | None = None,
        change_axis: str | None = None,
        arc_stage_notes: str | None = None,
        continuity_facts: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CharacterProfileRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO character_profiles (
                    character_id, project_id, display_name, role_in_story, archetype, external_goal, internal_need,
                    misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, contradictions_json,
                    backstory_summary, voice_notes, relationship_map_json, secrets_json, values_json, taboos_json,
                    change_axis, arc_stage_notes, continuity_facts_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    fatal_flaw_or_limitation,
                    _json_list(contradictions),
                    backstory_summary,
                    voice_notes,
                    _json_list(relationship_map),
                    _json_list(secrets),
                    _json_list(values),
                    _json_list(taboos),
                    change_axis,
                    arc_stage_notes,
                    _json_list(continuity_facts),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_character_profile(character_id)



    def get_character_profile(self, character_id: str) -> CharacterProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM character_profiles WHERE character_id = ?", (character_id,)).fetchone()
        if row is None:
            raise KeyError(character_id)
        return _character_row_to_record(row)



    def list_character_profiles(self, project_id: str) -> list[CharacterProfileRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM character_profiles
                WHERE project_id = ?
                ORDER BY display_name COLLATE NOCASE, character_id
                """,
                (project_id,),
            ).fetchall()
        return [_character_row_to_record(row) for row in rows]


class _RelationshipMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_relationship_edge(
        self,
        *,
        project_id: str,
        source_character_id: str,
        target_character_id: str,
        relation_kind: str,
        summary: str,
        tension: str | None = None,
        notes: str | None = None,
        edge_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> RelationshipEdgeRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_project_id = project_id
        normalized_edge_id = edge_id or f"{source_character_id}->{target_character_id}:{relation_kind}"
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO relationship_edges (
                    edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                    tension, notes, created_at, updated_at
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
                    normalized_edge_id,
                    normalized_project_id,
                    source_character_id,
                    target_character_id,
                    relation_kind,
                    summary,
                    tension,
                    notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            self._append_relationship_edge_to_character_map(
                connection,
                source_character_id=source_character_id,
                target_character_id=target_character_id,
                edge_id=normalized_edge_id,
                updated_at=updated,
            )
            connection.commit()
        return self.get_relationship_edge(normalized_edge_id)



    def get_relationship_edge(self, edge_id: str) -> RelationshipEdgeRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE edge_id = ?
                """,
                (edge_id,),
            ).fetchone()
        if row is None:
            raise KeyError(edge_id)
        return _relationship_edge_row_to_record(row)



    def list_relationship_edges(self, project_id: str) -> list[RelationshipEdgeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE project_id = ?
                ORDER BY edge_id COLLATE NOCASE
                """,
                (project_id,),
            ).fetchall()
        return [_relationship_edge_row_to_record(row) for row in rows]



    def list_relationship_edges_for_character(self, project_id: str, character_id: str) -> list[RelationshipEdgeRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                       tension, notes, created_at, updated_at
                FROM relationship_edges
                WHERE project_id = ? AND (source_character_id = ? OR target_character_id = ?)
                ORDER BY edge_id COLLATE NOCASE
                """,
                (project_id, character_id, character_id),
            ).fetchall()
        return [_relationship_edge_row_to_record(row) for row in rows]



    def delete_relationship_edge(self, project_id: str, *, edge_id: str) -> None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT edge_id FROM relationship_edges WHERE project_id = ? AND edge_id = ?",
                (project_id, edge_id),
            ).fetchone()
            if row is None:
                raise KeyError((project_id, edge_id))
            connection.execute(
                "DELETE FROM relationship_edges WHERE project_id = ? AND edge_id = ?",
                (project_id, edge_id),
            )
            connection.commit()



    def _append_relationship_edge_to_character_map(
        self,
        connection,
        *,
        source_character_id: str,
        target_character_id: str,
        edge_id: str,
        updated_at: datetime,
    ) -> None:
        for character_id in (source_character_id, target_character_id):
            row = connection.execute(
                """
                SELECT relationship_map_json
                FROM character_profiles
                WHERE character_id = ?
                """,
                (character_id,),
            ).fetchone()
            if row is None:
                continue
            existing = _parse_json_list(row["relationship_map_json"])
            if edge_id in existing:
                continue
            existing.append(edge_id)
            connection.execute(
                """
                UPDATE character_profiles
                SET relationship_map_json = ?, updated_at = ?
                WHERE character_id = ?
                """,
                (_json_list(existing), updated_at.isoformat(), character_id),
            )


