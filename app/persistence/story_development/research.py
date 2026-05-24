from __future__ import annotations

from datetime import datetime
from .shared_utils import (
    json_list as _json_list,
    now as _now,
    parse_json_list as _parse_json_list,
)
from .records import ResearchItemRecord
from .converters import _research_item_row_to_record

from ..sqlite import connect


class _ResearchMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def create_research_item(
        self,
        *,
        project_id: str,
        item_id: str,
        title: str,
        content: str,
        source_url: str | None = None,
        source_type: str = "other",
        genre_tags: list[str] | None = None,
        citations: list[str] | None = None,
        status: str = "active",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ResearchItemRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO research_items (
                    item_id, project_id, title, content, source_url, source_type,
                    genre_tags_json, status, citations_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    content = excluded.content,
                    source_url = excluded.source_url,
                    source_type = excluded.source_type,
                    genre_tags_json = excluded.genre_tags_json,
                    status = excluded.status,
                    citations_json = excluded.citations_json,
                    updated_at = excluded.updated_at
                """,
                (
                    item_id,
                    project_id,
                    title,
                    content,
                    source_url,
                    source_type,
                    _json_list(genre_tags),
                    status,
                    _json_list(citations),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_research_item(item_id)



    def get_research_item(self, item_id: str) -> ResearchItemRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM research_items WHERE item_id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return _research_item_row_to_record(row)



    def list_research_items(
        self,
        project_id: str,
        status: str | None = None,
        genre_tag: str | None = None,
    ) -> list[ResearchItemRecord]:
        query = "SELECT * FROM research_items WHERE project_id = ?"
        params: list[str] = [project_id]

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        if genre_tag is not None:
            query += " AND genre_tags_json LIKE ?"
            params.append(f"%\"{genre_tag}\"%")

        query += " ORDER BY title COLLATE NOCASE, item_id"

        with connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [_research_item_row_to_record(row) for row in rows]



    def update_research_item(
        self,
        item_id: str,
        **kwargs: object,
    ) -> ResearchItemRecord:
        allowed = {
            "title", "content", "source_url", "source_type",
            "genre_tags_json", "status", "citations_json", "updated_at",
        }
        updates: dict[str, object] = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_research_item(item_id)

        if "genre_tags_json" in updates:
            updates["genre_tags_json"] = _json_list(list(updates["genre_tags_json"]) if isinstance(updates["genre_tags_json"], list) else [])
        if "citations_json" in updates:
            updates["citations_json"] = _json_list(list(updates["citations_json"]) if isinstance(updates["citations_json"], list) else [])
        if "updated_at" not in updates:
            updates["updated_at"] = _now().isoformat()

        set_clauses = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        values.append(item_id)

        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"UPDATE research_items SET {set_clauses} WHERE item_id = ?",
                values,
            )
            if cursor.rowcount == 0:
                connection.rollback()
                raise KeyError(item_id)
            connection.commit()
        return self.get_research_item(item_id)



    def delete_research_item(self, item_id: str) -> None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT item_id FROM research_items WHERE item_id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                raise KeyError(item_id)
            connection.execute(
                "UPDATE research_items SET status = 'archived', updated_at = ? WHERE item_id = ?",
                (_now().isoformat(), item_id),
            )
            connection.commit()
