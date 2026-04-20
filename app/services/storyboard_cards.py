from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Sequence

from app.persistence.story_development import (
    StoryboardCardRecord,
    StoryDevelopmentRepository,
)


class StoryboardCardServiceError(ValueError):
    pass


class StoryboardCardNotFoundError(StoryboardCardServiceError):
    pass


class StoryboardCardValidationError(StoryboardCardServiceError):
    pass


@dataclass(frozen=True)
class CardFilterOptions:
    card_type: str | None = None
    column_id: str | None = None
    tag: str | None = None


class StoryboardCardService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def create_card(
        self,
        project_id: str,
        *,
        card_id: str,
        title: str,
        content: str,
        card_type: str = "idea",
        column_id: str | None = None,
        position: int = 0,
        tags: Sequence[str] | None = None,
        character_ids: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoryboardCardRecord:
        self._validate_card_input(
            card_id=card_id,
            title=title,
            content=content,
            card_type=card_type,
        )
        return self.repository.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title=title,
            content=content,
            card_type=card_type,
            column_id=column_id,
            position=position,
            tags=list(tags) if tags else None,
            character_ids=list(character_ids) if character_ids else None,
            dependencies=list(dependencies) if dependencies else None,
            metadata=metadata,
        )

    def upsert_card(
        self,
        project_id: str,
        *,
        card_id: str,
        title: str,
        content: str,
        card_type: str = "idea",
        column_id: str | None = None,
        position: int = 0,
        tags: Sequence[str] | None = None,
        character_ids: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoryboardCardRecord:
        return self.repository.upsert_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title=title,
            content=content,
            card_type=card_type,
            column_id=column_id,
            position=position,
            tags=list(tags) if tags else None,
            character_ids=list(character_ids) if character_ids else None,
            dependencies=list(dependencies) if dependencies else None,
            metadata=metadata,
        )

    def get_card(self, card_id: str) -> StoryboardCardRecord:
        try:
            return self.repository.get_storyboard_card(card_id)
        except KeyError:
            raise StoryboardCardNotFoundError(card_id)

    def list_cards(
        self,
        project_id: str,
        *,
        filter_options: CardFilterOptions | None = None,
    ) -> list[StoryboardCardRecord]:
        card_type = filter_options.card_type if filter_options else None
        column_id = filter_options.column_id if filter_options else None
        tag = filter_options.tag if filter_options else None
        return self.repository.list_storyboard_cards(
            project_id,
            card_type=card_type,
            column_id=column_id,
            tag=tag,
        )

    def delete_card(self, card_id: str) -> None:
        self.repository.delete_storyboard_card(card_id)

    def update_card_position(
        self,
        card_id: str,
        position: int,
    ) -> StoryboardCardRecord:
        self.repository.update_storyboard_card_position(card_id, position)
        return self.get_card(card_id)

    def update_card_content(
        self,
        card_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        card_type: str | None = None,
        tags: Sequence[str] | None = None,
        character_ids: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoryboardCardRecord:
        return self.repository.update_storyboard_card_content(
            card_id=card_id,
            title=title,
            content=content,
            card_type=card_type,
            tags=list(tags) if tags else None,
            character_ids=list(character_ids) if character_ids else None,
            dependencies=list(dependencies) if dependencies else None,
            metadata=metadata,
        )

    def reindex_column(
        self,
        project_id: str,
        column_id: str,
        card_ids: Sequence[str],
    ) -> list[StoryboardCardRecord]:
        results: list[StoryboardCardRecord] = []
        for idx, cid in enumerate(card_ids):
            results.append(self.update_card_position(cid, idx))
        return results

    def _validate_card_input(
        self,
        *,
        card_id: str,
        title: str,
        content: str,
        card_type: str,
    ) -> None:
        errors: list[str] = []
        if not card_id.strip():
            errors.append("card_id must not be empty")
        if not title.strip():
            errors.append("title must not be empty")
        valid_types = {"scene", "beat", "idea", "note", "chapter"}
        if card_type not in valid_types:
            errors.append(
                f"card_type must be one of {sorted(valid_types)}, got '{card_type}'"
            )
        if errors:
            raise StoryboardCardValidationError(
                "; ".join(errors)
            )
