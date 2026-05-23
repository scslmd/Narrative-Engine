from __future__ import annotations

from datetime import datetime
from typing import Any

from . import StoryboardCardRecord
from .converters import _storyboard_card_row_to_record
from .shared_utils import (
    json_list as _json_list,
    json_object as _json_object,
    now as _now,
)
from ..sqlite import connect


class _StoryboardMixin:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_storyboard_card(
        self,
        *,
        card_id: str,
        project_id: str,
        title: str,
        content: str,
        card_type: str = "idea",
        column_id: str | None = None,
        position: int = 0,
        tags: list[str] | None = None,
        character_ids: list[str] | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryboardCardRecord:
        """Create a new storyboard card."""
        now = _now(created_at)
        updated = _now(updated_at or created_at)

        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO storyboard_cards (
                    card_id, project_id, title, content, card_type, column_id, position,
                    tags, character_ids, dependencies, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    project_id,
                    title,
                    content,
                    card_type,
                    column_id,
                    position,
                    _json_list(tags),
                    _json_list(character_ids),
                    _json_list(dependencies),
                    _json_object(metadata or {}),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_storyboard_card(card_id)

    def upsert_storyboard_card(
        self,
        *,
        card_id: str,
        project_id: str,
        title: str,
        content: str,
        card_type: str = "idea",
        column_id: str | None = None,
        position: int = 0,
        tags: list[str] | None = None,
        character_ids: list[str] | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryboardCardRecord:
        """Create or update a storyboard card."""
        now = _now(created_at)
        updated = _now(updated_at or created_at)

        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO storyboard_cards (
                    card_id, project_id, title, content, card_type, column_id, position,
                    tags, character_ids, dependencies, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    content = excluded.content,
                    card_type = excluded.card_type,
                    column_id = excluded.column_id,
                    position = excluded.position,
                    tags = excluded.tags,
                    character_ids = excluded.character_ids,
                    dependencies = excluded.dependencies,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
                """,
                (
                    card_id,
                    project_id,
                    title,
                    content,
                    card_type,
                    column_id,
                    position,
                    _json_list(tags),
                    _json_list(character_ids),
                    _json_list(dependencies),
                    _json_object(metadata or {}),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_storyboard_card(card_id)

    def get_storyboard_card(self, card_id: str) -> StoryboardCardRecord:
        """Get a storyboard card by ID."""
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM storyboard_cards WHERE card_id = ?",
                (card_id,),
            ).fetchone()

        if row is None:
            raise KeyError(f"Storyboard card not found: {card_id}")

        return _storyboard_card_row_to_record(row)

    def list_storyboard_cards(
        self,
        project_id: str,
        *,
        column_id: str | None = None,
        card_type: str | None = None,
        tag: str | None = None,
    ) -> list[StoryboardCardRecord]:
        """List storyboard cards with optional filters."""
        query = "SELECT * FROM storyboard_cards WHERE project_id = ?"
        params: list[str | int] = [project_id]

        if column_id is not None:
            query += " AND column_id = ?"
            params.append(column_id)

        if card_type is not None:
            query += " AND card_type = ?"
            params.append(card_type)

        if tag is not None:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")

        query += " ORDER BY column_id ASC, position ASC, card_id ASC"

        with connect(self.db_path) as connection:
            rows = connection.execute(query, params).fetchall()

        return [_storyboard_card_row_to_record(row) for row in rows]

    def delete_storyboard_card(self, card_id: str) -> None:
        """Delete a storyboard card."""
        with connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM storyboard_cards WHERE card_id = ?",
                (card_id,),
            )
            connection.commit()

    def update_storyboard_card_position(
        self,
        *,
        card_id: str,
        column_id: str | None,
        position: int,
    ) -> StoryboardCardRecord:
        """Update a card's position (for drag-and-drop reordering)."""
        now = _now()

        with connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE storyboard_cards
                SET column_id = ?, position = ?, updated_at = ?
                WHERE card_id = ?
                """,
                (column_id, position, now.isoformat(), card_id),
            )
            connection.commit()
        return self.get_storyboard_card(card_id)

    def update_storyboard_card_content(
        self,
        *,
        card_id: str,
        title: str | None = None,
        content: str | None = None,
        card_type: str | None = None,
        tags: list[str] | None = None,
        character_ids: list[str] | None = None,
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        updated_at: datetime | None = None,
    ) -> StoryboardCardRecord:
        """Update specific fields of a storyboard card."""
        now = _now(updated_at)

        with connect(self.db_path) as connection:
            updates = ["updated_at = ?"]
            params: list[str | int | dict | list] = [now.isoformat()]

            if title is not None:
                updates.append("title = ?")
                params.append(title)

            if content is not None:
                updates.append("content = ?")
                params.append(content)

            if card_type is not None:
                updates.append("card_type = ?")
                params.append(card_type)

            if tags is not None:
                updates.append("tags = ?")
                params.append(_json_list(tags))

            if character_ids is not None:
                updates.append("character_ids = ?")
                params.append(_json_list(character_ids))

            if dependencies is not None:
                updates.append("dependencies = ?")
                params.append(_json_list(dependencies))

            if metadata is not None:
                updates.append("metadata = ?")
                params.append(_json_object(metadata))

            updates.append("WHERE card_id = ?")
            params.append(card_id)

            query = f"UPDATE storyboard_cards SET {', '.join(updates[:-1])} {updates[-1]}"
            connection.execute(query, params)
            connection.commit()

        return self.get_storyboard_card(card_id)
