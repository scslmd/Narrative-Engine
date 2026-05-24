from __future__ import annotations

import json
from datetime import datetime
from typing import Sequence

from .shared_utils import (
    json_objects as _json_objects,
    now as _now,
)
from .records import RevisionPassRecord
from .converters import _revision_pass_row_to_record

from ..sqlite import connect


class _RevisionMixin:

    def __init__(self, db_path):
        self.db_path = db_path

    def create_revision_pass(
        self,
        *,
        project_id: str,
        pass_id: str,
        pass_type: str,
        status: str = "pending",
        checklist: Sequence[dict[str, object]] | None = None,
        notes: str | None = None,
        created_at: datetime | None = None,
    ) -> RevisionPassRecord:
        now = _now(created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO revision_passes (
                    pass_id, project_id, pass_type, status, checklist_json, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pass_id,
                    project_id,
                    pass_type,
                    status,
                    _json_objects(list(checklist or [])),
                    notes,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            connection.commit()
        return self.get_revision_pass(pass_id)

    def get_revision_pass(self, pass_id: str) -> RevisionPassRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM revision_passes
                WHERE pass_id = ?
                """,
                (pass_id,),
            ).fetchone()
        if row is None:
            raise KeyError(pass_id)
        return _revision_pass_row_to_record(row)

    def list_revision_passes(
        self,
        project_id: str,
        pass_type: str | None = None,
        status: str | None = None,
    ) -> list[RevisionPassRecord]:
        query = """
            SELECT *
            FROM revision_passes
            WHERE project_id = ?
        """
        params: list[str] = [project_id]

        if pass_type is not None:
            query += " AND pass_type = ?"
            params.append(pass_type)
        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [_revision_pass_row_to_record(row) for row in rows]

    def update_revision_pass(
        self,
        pass_id: str,
        *,
        status: str | None = None,
        checklist: Sequence[dict[str, object]] | None = None,
        notes: str | None = None,
        completed_at: datetime | None = None,
    ) -> RevisionPassRecord:
        updates: list[str] = []
        params: list[object] = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if checklist is not None:
            updates.append("checklist_json = ?")
            params.append(_json_objects(list(checklist)))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())

        if not updates:
            return self.get_revision_pass(pass_id)

        updates.append("updated_at = ?")
        params.append(_now().isoformat())
        params.append(pass_id)

        with connect(self.db_path) as connection:
            connection.execute(
                f"UPDATE revision_passes SET {', '.join(updates)} WHERE pass_id = ?",
                params,
            )
            connection.commit()
        return self.get_revision_pass(pass_id)

    def complete_revision_pass(
        self,
        pass_id: str,
        *,
        completed_at: datetime | None = None,
    ) -> RevisionPassRecord:
        completed = _now(completed_at)
        return self.update_revision_pass(
            pass_id,
            status="completed",
            completed_at=completed,
        )

    def get_checklist(self, pass_type: str) -> list[dict[str, object]]:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT checklist_json
                FROM revision_passes
                WHERE pass_type = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (pass_type,),
            ).fetchone()
        if row is None:
            return []
        return json.loads(row["checklist_json"] or "[]")
