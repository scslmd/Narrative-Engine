from __future__ import annotations

from uuid import uuid4

from app.persistence.story_development import (
    ResearchItemRecord,
    StoryDevelopmentRepository,
)
from app.schemas.story_development import ResearchItem


class ResearchServiceError(ValueError):
    pass


class ResearchNotFoundError(ResearchServiceError):
    pass


class ResearchService:
    VALID_SOURCE_TYPES = {"book", "article", "paper", "site", "note", "other"}
    VALID_STATUSES = {"active", "archived", "cited"}

    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def create_item(
        self,
        project_id: str,
        title: str,
        content: str,
        source_url: str | None = None,
        source_type: str = "other",
        genre_tags: list[str] | None = None,
        citations: list[str] | None = None,
        status: str = "active",
    ) -> ResearchItem:
        if source_type not in self.VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of: {', '.join(sorted(self.VALID_SOURCE_TYPES))}")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(self.VALID_STATUSES))}")
        item_id = str(uuid4())
        record = self.repository.create_research_item(
            project_id=project_id,
            item_id=item_id,
            title=title,
            content=content,
            source_url=source_url,
            source_type=source_type,
            genre_tags=genre_tags,
            citations=citations,
            status=status,
        )
        return self._to_schema(record)

    def get_item(self, item_id: str) -> ResearchItem:
        try:
            record = self.repository.get_research_item(item_id)
        except KeyError:
            raise ResearchNotFoundError(f"Research item not found: {item_id}") from None
        return self._to_schema(record)

    def list_items(
        self,
        project_id: str,
        status: str | None = None,
        genre_tag: str | None = None,
    ) -> list[ResearchItem]:
        records = self.repository.list_research_items(
            project_id=project_id,
            status=status,
            genre_tag=genre_tag,
        )
        return [self._to_schema(record) for record in records]

    def update_item(self, item_id: str, **kwargs: object) -> ResearchItem:
        try:
            record = self.repository.update_research_item(item_id, **kwargs)
        except KeyError:
            raise ResearchNotFoundError(f"Research item not found: {item_id}") from None
        return self._to_schema(record)

    def delete_item(self, item_id: str) -> None:
        try:
            self.repository.delete_research_item(item_id)
        except KeyError:
            raise ResearchNotFoundError(f"Research item not found: {item_id}") from None

    def _to_schema(self, record: ResearchItemRecord) -> ResearchItem:
        return ResearchItem(
            item_id=record.item_id,
            project_id=record.project_id,
            title=record.title,
            content=record.content,
            source_url=record.source_url,
            source_type=record.source_type,
            genre_tags=list(record.genre_tags),
            status=record.status,
            citations=list(record.citations),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
