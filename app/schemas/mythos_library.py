from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import StrictModel


class MythosEntryType(str, Enum):
    ARCHETYPE = "archetype"
    MOTIF = "motif"
    COSMIC_RULE = "cosmic_rule"
    SYMBOL = "symbol"
    RITUAL = "ritual"
    DEITY = "deity"
    CYCLE = "cycle"
    THEME = "theme"


class MythosVisibilityScope(str, Enum):
    PROJECT = "project"
    FORKABLE = "forkable"
    PRIVATE = "private"


class MythosEntry(StrictModel):
    mythos_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    entry_type: MythosEntryType
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = ""
    canonical_facts: list[str] = Field(default_factory=list)
    pattern_notes: list[str] = Field(default_factory=list)
    source_corpus: str | None = None
    generation_guidance: str = ""
    visibility_scope: MythosVisibilityScope = MythosVisibilityScope.PROJECT
    writer_notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MythosEntryCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255)
    entry_type: MythosEntryType
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = ""
    canonical_facts: list[str] = Field(default_factory=list)
    pattern_notes: list[str] = Field(default_factory=list)
    source_corpus: str | None = None
    generation_guidance: str = ""
    visibility_scope: MythosVisibilityScope = MythosVisibilityScope.PROJECT
    writer_notes: str | None = None


class MythosEntryUpdateRequest(StrictModel):
    entry_type: MythosEntryType | None = None
    name: str | None = None
    summary: str | None = None
    canonical_facts: list[str] | None = None
    pattern_notes: list[str] | None = None
    source_corpus: str | None = None
    generation_guidance: str | None = None
    visibility_scope: MythosVisibilityScope | None = None
    writer_notes: str | None = None
