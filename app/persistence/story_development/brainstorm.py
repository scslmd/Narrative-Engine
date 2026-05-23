from __future__ import annotations

from datetime import datetime

from . import BrainstormItemRecord
from .converters import _brainstorm_row_to_record
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from ..sqlite import connect


class _BrainstormMixin:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_brainstorm_item(
        self,
        *,
        project_id: str,
        content: str,
        item_state: str,
        cluster_key: str | None = None,
        tags: list[str] | None = None,
        source_artifact_refs: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO brainstorm_items (
                    project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    cluster_key,
                    content,
                    item_state,
                    _json_list(tags),
                    _json_list(source_artifact_refs),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        row_id = cursor.lastrowid
        assert row_id is not None
        return self.get_brainstorm_item(int(row_id))

    def get_brainstorm_item(self, item_id: int) -> BrainstormItemRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return _brainstorm_row_to_record(row)

    def list_brainstorm_items(self, project_id: str) -> list[BrainstormItemRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE project_id = ?
                ORDER BY item_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_brainstorm_row_to_record(row) for row in rows]

    def update_brainstorm_item_state(
        self,
        item_id: int,
        *,
        item_state: str,
        cluster_key: str | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        updated = _now(updated_at)
        assignments = ["item_state = ?"]
        values: list[object] = [item_state]
        if cluster_key is not None:
            assignments.append("cluster_key = ?")
            values.append(cluster_key)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.append(item_id)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE brainstorm_items
                SET {', '.join(assignments)}
                WHERE item_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(item_id)
        return self.get_brainstorm_item(item_id)
