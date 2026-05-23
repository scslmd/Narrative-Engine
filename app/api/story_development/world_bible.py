from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import WorldBibleEntry
from app.schemas.base import StrictModel
from app.services.story_knowledge import (
    StoryKnowledgeNotFoundError,
    StoryKnowledgeService,
    StoryKnowledgeValidationError,
)
from pydantic import Field


class WorldBibleEntryCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1, max_length=50000)
    canonical_facts: list[str] = Field(default_factory=list)
    related_character_ids: list[str] = Field(default_factory=list)
    source_artifacts: list[str] = Field(default_factory=list)
    visibility_scope: str = Field(default="project", min_length=1, max_length=50)
    continuity_warnings: list[str] = Field(default_factory=list)
    writer_notes: str | None = Field(None, max_length=5000)


class WorldBibleEntryUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    summary: str | None = Field(None, min_length=1, max_length=50000)
    canonical_facts: list[str] | None = None
    related_character_ids: list[str] | None = None
    source_artifacts: list[str] | None = None
    visibility_scope: str | None = Field(None, min_length=1, max_length=50)
    continuity_warnings: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)


class WorldBibleEntryListResponse(StrictModel):
    project_id: str
    items: list[WorldBibleEntry] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "WorldBibleEntryCreateRequest",
    "WorldBibleEntryListResponse",
    "WorldBibleEntryUpdateRequest",
    "register_world_bible_routes",
]


def register_world_bible_routes(
    router: APIRouter,
    story_knowledge_service: StoryKnowledgeService,
) -> None:
    @router.get("/world-bible", response_model=WorldBibleEntryListResponse)
    def list_world_bible_entries(
        project_id: str,
        entry_type: str | None = None,
    ) -> WorldBibleEntryListResponse:
        """List all world bible entries for a project."""
        entries = list(story_knowledge_service.list_world_bible_entries(project_id))
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        return WorldBibleEntryListResponse(
            project_id=project_id,
            items=entries,
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/world-bible/{entry_type}/{title}", response_model=WorldBibleEntry)
    def get_world_bible_entry(entry_type: str, title: str, project_id: str) -> WorldBibleEntry:
        """Get a specific world bible entry."""
        try:
            return story_knowledge_service.get_world_bible_entry(project_id, entry_type=entry_type, title=title)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="World bible entry not found.") from exc

    @router.post("/world-bible", response_model=WorldBibleEntry, status_code=201)
    def create_world_bible_entry(payload: WorldBibleEntryCreateRequest) -> WorldBibleEntry:
        """Create a new world bible entry."""
        try:
            return story_knowledge_service.upsert_world_bible_entry(
                payload.project_id,
                entry_type=payload.entry_type,
                title=payload.title,
                summary=payload.summary,
                canonical_facts=payload.canonical_facts,
                related_character_ids=payload.related_character_ids,
                source_artifacts=payload.source_artifacts,
                visibility_scope=payload.visibility_scope,
                continuity_warnings=payload.continuity_warnings,
                writer_notes=payload.writer_notes,
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/world-bible/{entry_type}/{title}", response_model=WorldBibleEntry)
    def update_world_bible_entry(entry_type: str, title: str, project_id: str, payload: WorldBibleEntryUpdateRequest) -> WorldBibleEntry:
        """Update a world bible entry."""
        try:
            # Get existing entry
            existing = story_knowledge_service.get_world_bible_entry(project_id, entry_type=entry_type, title=title)
            
            # Helper to compare list fields (handles tuple vs list comparison)
            def lists_equal(a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> bool:
                return set(a) == set(b)
            
            # Merge updates - use explicit type annotations to avoid union type issues
            new_title: str = payload.title if payload.title is not None else title
            new_summary: str = payload.summary if payload.summary is not None else existing.summary
            new_canonical_facts: list[str] = payload.canonical_facts if payload.canonical_facts is not None else existing.canonical_facts
            new_related_character_ids: list[str] = payload.related_character_ids if payload.related_character_ids is not None else existing.related_character_ids
            new_source_artifacts: list[str] = payload.source_artifacts if payload.source_artifacts is not None else existing.source_artifacts
            new_visibility_scope: str = payload.visibility_scope if payload.visibility_scope is not None else existing.visibility_scope
            new_continuity_warnings: list[str] = payload.continuity_warnings if payload.continuity_warnings is not None else existing.continuity_warnings
            new_writer_notes: str | None = payload.writer_notes if payload.writer_notes is not None else existing.writer_notes
            
            # Check if at least one field is being updated (use set comparison for lists)
            if (new_title == title and new_summary == existing.summary and 
                lists_equal(new_canonical_facts, existing.canonical_facts) and 
                lists_equal(new_related_character_ids, existing.related_character_ids) and
                lists_equal(new_source_artifacts, existing.source_artifacts) and
                new_visibility_scope == existing.visibility_scope and
                lists_equal(new_continuity_warnings, existing.continuity_warnings) and
                new_writer_notes == existing.writer_notes):
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            
            # Call upsert with merged data
            return story_knowledge_service.upsert_world_bible_entry(
                project_id,
                entry_type=entry_type,
                summary=new_summary,
                title=new_title,
                canonical_facts=new_canonical_facts,
                related_character_ids=new_related_character_ids,
                source_artifacts=new_source_artifacts,
                visibility_scope=new_visibility_scope,
                continuity_warnings=new_continuity_warnings,
                writer_notes=new_writer_notes,
            )
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="World bible entry not found.") from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
