from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EntityTypeName = Literal["character", "relationship", "world_bible"]
DedupActionType = Literal["new", "exact_merge", "fuzzy_merge", "enrich"]
JobStatusType = Literal["pending", "chunking", "extracting", "deduplicating", "staging", "completed", "failed"]


class CascadeScanRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    manuscript_text: str = Field(..., min_length=50)
    chunk_size: int = Field(default=8000, ge=1000, le=50000)
    include_types: list[EntityTypeName] = Field(
        default=["character", "relationship", "world_bible"],
    )


class CascadeJobResponse(BaseModel):
    job_id: str
    status: JobStatusType
    phase: JobStatusType
    chunk_index: int | None = None
    total_chunks: int | None = None
    stage_id: str | None = None
    error: str | None = None


class StagedEntity(BaseModel):
    entity_id: str
    entity_type: EntityTypeName
    entity_json: dict[str, object]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_excerpt: str | None = None
    approved: bool = False
    dedup_action: DedupActionType


class EntityApprovalUpdate(BaseModel):
    entity_id: str
    approved: bool


class CascadeApplyResponse(BaseModel):
    characters_added: int = 0
    relationships_added: int = 0
    world_bible_added: int = 0
    characters_enriched: int = 0


class StagedEntitiesResponse(BaseModel):
    stage_id: str
    project_id: str
    characters: list[StagedEntity] = []
    relationships: list[StagedEntity] = []
    world_bible: list[StagedEntity] = []


class CascadeUndoResponse(BaseModel):
    stage_id: str
    entities_reverted: int
