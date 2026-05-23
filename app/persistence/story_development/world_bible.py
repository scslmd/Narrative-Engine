from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import WorldBibleEntryRecord
from .converters import _world_bible_row_to_record

from ..sqlite import connect


class _WorldBibleMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_world_bible_entry(
        self,
        *,
        project_id: str,
        entry_type: str,
        title: str,
        summary: str | None = None,
        canonical_facts: list[str] | None = None,
        related_character_ids: list[str] | None = None,
        visibility_scope: str = "project",
        source_artifacts: list[str] | None = None,
        continuity_warnings: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> WorldBibleEntryRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json, related_character_ids_json, visibility_scope,
                    source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
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
                    _json_list(canonical_facts),
                    _json_list(related_character_ids),
                    visibility_scope,
                    _json_list(source_artifacts),
                    _json_list(continuity_warnings),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_world_bible_entry(project_id, entry_type=entry_type, title=title)



    def get_world_bible_entry(self, project_id: str, *, entry_type: str, title: str) -> WorldBibleEntryRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ? AND entry_type = ? AND title = ?
                """,
                (project_id, entry_type, title),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, entry_type, title))
        return _world_bible_row_to_record(row)



    def list_world_bible_entries(self, project_id: str) -> list[WorldBibleEntryRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ?
                ORDER BY entry_type COLLATE NOCASE, title COLLATE NOCASE, entry_id
                """,
                (project_id,),
            ).fetchall()
        return [_world_bible_row_to_record(row) for row in rows]
