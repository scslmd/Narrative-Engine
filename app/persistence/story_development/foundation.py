from __future__ import annotations

from datetime import datetime

from . import FoundationProfileRecord, FoundationRevisionRecord
from .converters import _foundation_revision_row_to_record
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from ..sqlite import connect


class _FoundationMixin:
    def __init__(self, db_path):
        self.db_path = db_path

    def upsert_foundation_profile(
        self,
        *,
        project_id: str,
        premise: str,
        logline: str,
        thematic_spine: str | None = None,
        emotional_promise: str | None = None,
        tone_direction: str | None = None,
        target_audience: str | None = None,
        narrative_constraints: list[str] | None = None,
        complexity_level: str | None = None,
        success_definition: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> FoundationRevisionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        revision_number = self._next_foundation_revision_number(project_id)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO foundation_profiles (
                    project_id, current_revision_id, created_at, updated_at
                ) VALUES (?, NULL, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    updated_at = excluded.updated_at
                """,
                (project_id, now.isoformat(), updated.isoformat()),
            )
            cursor = connection.execute(
                """
                INSERT INTO foundation_revisions (
                    project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                    tone_direction, target_audience, narrative_constraints_json, complexity_level,
                    success_definition, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    revision_number,
                    premise,
                    logline,
                    thematic_spine,
                    emotional_promise,
                    tone_direction,
                    target_audience,
                    _json_list(narrative_constraints),
                    complexity_level,
                    success_definition,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            row_id = cursor.lastrowid
            assert row_id is not None
            revision_id = int(row_id)
            connection.execute(
                "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
                (revision_id, updated.isoformat(), project_id),
            )
            connection.commit()
        return self.get_foundation_revision(revision_id)

    def get_foundation_profile(self, project_id: str) -> FoundationProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT project_id, current_revision_id, created_at, updated_at
                FROM foundation_profiles
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return FoundationProfileRecord(
            project_id=row["project_id"],
            current_revision_id=row["current_revision_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_foundation_revisions(self, project_id: str) -> list[FoundationRevisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE project_id = ?
                ORDER BY revision_number ASC, revision_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_foundation_revision_row_to_record(row) for row in rows]

    def get_foundation_revision(self, revision_id: int) -> FoundationRevisionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE revision_id = ?
                """,
                (revision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        return _foundation_revision_row_to_record(row)

    def _next_foundation_revision_number(self, project_id: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(revision_number), 0) AS revision_number FROM foundation_revisions WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return int(row["revision_number"]) + 1
