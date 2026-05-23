from __future__ import annotations

from datetime import datetime

from . import BrainDumpSessionRecord
from .converters import _brain_dump_session_row_to_record
from .shared_utils import (
    now as _now,
)
from ..sqlite import connect


class _BraindumpMixin:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_brain_dump_session(
        self,
        *,
        project_id: str,
        title: str | None = None,
        raw_text: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BrainDumpSessionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO brain_dump_sessions (
                    project_id, title, raw_text, state, created_at, updated_at
                ) VALUES (?, ?, ?, 'active', ?, ?)
                """,
                (
                    project_id,
                    title,
                    raw_text,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        row_id = cursor.lastrowid
        assert row_id is not None
        return self.get_brain_dump_session(int(row_id))

    def get_brain_dump_session(self, session_id: int) -> BrainDumpSessionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT session_id, project_id, title, raw_text, state, created_at, updated_at
                FROM brain_dump_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError(session_id)
        return _brain_dump_session_row_to_record(row)

    def list_brain_dump_sessions(self, project_id: str) -> list[BrainDumpSessionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT session_id, project_id, title, raw_text, state, created_at, updated_at
                FROM brain_dump_sessions
                WHERE project_id = ?
                ORDER BY session_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_brain_dump_session_row_to_record(row) for row in rows]

    def update_brain_dump_session(
        self,
        session_id: int,
        *,
        raw_text: str | None = None,
        title: str | None = None,
        state: str | None = None,
        updated_at: datetime | None = None,
    ) -> BrainDumpSessionRecord:
        assignments: list[str] = []
        values: list[object] = []
        if raw_text is not None:
            assignments.append("raw_text = ?")
            values.append(raw_text)
        if title is not None:
            assignments.append("title = ?")
            values.append(title)
        if state is not None:
            assignments.append("state = ?")
            values.append(state)
        assignments.append("updated_at = ?")
        updated = _now(updated_at)
        values.append(updated.isoformat())
        values.append(session_id)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE brain_dump_sessions
                SET {', '.join(assignments)}
                WHERE session_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(session_id)
        return self.get_brain_dump_session(session_id)

    def delete_brain_dump_session(self, session_id: int) -> None:
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM brain_dump_sessions WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(session_id)
