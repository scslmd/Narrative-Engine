from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import MythosEntryRecord, PatternEntryRecord
from .converters import _mythos_entry_row_to_record, _pattern_entry_row_to_record

from ..sqlite import connect


class _MythosMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_mythos_entry(
        self,
        *,
        mythos_id: str,
        project_id: str,
        entry_type: str,
        name: str,
        summary: str = "",
        canonical_facts: list[str] | None = None,
        pattern_notes: list[str] | None = None,
        source_corpus: str | None = None,
        generation_guidance: str = "",
        visibility_scope: str = "project",
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> MythosEntryRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO mythos_entries (
                    mythos_id, project_id, entry_type, name, summary, canonical_facts_json, pattern_notes_json,
                    source_corpus, generation_guidance, visibility_scope, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mythos_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    entry_type = excluded.entry_type,
                    name = excluded.name,
                    summary = excluded.summary,
                    canonical_facts_json = excluded.canonical_facts_json,
                    pattern_notes_json = excluded.pattern_notes_json,
                    source_corpus = excluded.source_corpus,
                    generation_guidance = excluded.generation_guidance,
                    visibility_scope = excluded.visibility_scope,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    mythos_id,
                    project_id,
                    entry_type,
                    name,
                    summary,
                    _json_list(canonical_facts),
                    _json_list(pattern_notes),
                    source_corpus,
                    generation_guidance,
                    visibility_scope,
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_mythos_entry(mythos_id)



    def get_mythos_entry(self, mythos_id: str) -> MythosEntryRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM mythos_entries WHERE mythos_id = ?", (mythos_id,)).fetchone()
        if row is None:
            raise KeyError(mythos_id)
        return _mythos_entry_row_to_record(row)



    def list_mythos_entries(self, project_id: str, entry_type: str | None = None) -> list[MythosEntryRecord]:
        with connect(self.db_path) as connection:
            if entry_type is None:
                rows = connection.execute(
                    "SELECT * FROM mythos_entries WHERE project_id = ? ORDER BY entry_type ASC, name ASC",
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM mythos_entries WHERE project_id = ? AND entry_type = ? ORDER BY name ASC",
                    (project_id, entry_type),
                ).fetchall()
        return [_mythos_entry_row_to_record(row) for row in rows]



    def delete_mythos_entry(self, mythos_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute("DELETE FROM mythos_entries WHERE mythos_id = ?", (mythos_id,))
            connection.commit()


class _PatternMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_pattern_entry(
        self,
        *,
        pattern_id: str,
        project_id: str,
        pattern_type: str,
        name: str,
        summary: str = "",
        source_type: str = "manual",
        generation_modes: list[str] | None = None,
        beats: list[str] | None = None,
        constraints: list[str] | None = None,
        transposition_notes: str = "",
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> PatternEntryRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO pattern_entries (
                    pattern_id, project_id, pattern_type, name, summary, source_type,
                    generation_modes_json, beats_json, constraints_json, transposition_notes,
                    writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    pattern_type = excluded.pattern_type,
                    name = excluded.name,
                    summary = excluded.summary,
                    source_type = excluded.source_type,
                    generation_modes_json = excluded.generation_modes_json,
                    beats_json = excluded.beats_json,
                    constraints_json = excluded.constraints_json,
                    transposition_notes = excluded.transposition_notes,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    pattern_id,
                    project_id,
                    pattern_type,
                    name,
                    summary,
                    source_type,
                    _json_list(generation_modes),
                    _json_list(beats),
                    _json_list(constraints),
                    transposition_notes,
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_pattern_entry(pattern_id)



    def get_pattern_entry(self, pattern_id: str) -> PatternEntryRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM pattern_entries WHERE pattern_id = ?", (pattern_id,)).fetchone()
        if row is None:
            raise KeyError(pattern_id)
        return _pattern_entry_row_to_record(row)



    def list_pattern_entries(self, project_id: str, pattern_type: str | None = None) -> list[PatternEntryRecord]:
        with connect(self.db_path) as connection:
            if pattern_type is None:
                rows = connection.execute(
                    "SELECT * FROM pattern_entries WHERE project_id = ? ORDER BY pattern_type ASC, name ASC",
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM pattern_entries WHERE project_id = ? AND pattern_type = ? ORDER BY name ASC",
                    (project_id, pattern_type),
                ).fetchall()
        return [_pattern_entry_row_to_record(row) for row in rows]



    def delete_pattern_entry(self, pattern_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute("DELETE FROM pattern_entries WHERE pattern_id = ?", (pattern_id,))
            connection.commit()
