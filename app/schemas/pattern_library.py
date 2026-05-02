from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import StrictModel


class PatternEntryType(str, Enum):
    PLOT = "plot"
    CHARACTER = "character"
    RELATIONSHIP = "relationship"
    WORLD = "world"
    THEME = "theme"
    SCENE = "scene"
    STRUCTURE = "structure"


class PatternSourceType(str, Enum):
    NARRATIVE = "narrative"
    MYTHOLOGY = "mythology"
    MANUAL = "manual"


class PatternEntry(StrictModel):
    pattern_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    pattern_type: PatternEntryType
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = ""
    source_type: PatternSourceType = PatternSourceType.MANUAL
    generation_modes: list[str] = Field(default_factory=list)
    beats: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    transposition_notes: str = ""
    writer_notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PatternEntryCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255)
    pattern_type: PatternEntryType
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = ""
    source_type: PatternSourceType = PatternSourceType.MANUAL
    generation_modes: list[str] = Field(default_factory=list)
    beats: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    transposition_notes: str = ""
    writer_notes: str | None = None


class PatternEntryUpdateRequest(StrictModel):
    pattern_type: PatternEntryType | None = None
    name: str | None = None
    summary: str | None = None
    source_type: PatternSourceType | None = None
    generation_modes: list[str] | None = None
    beats: list[str] | None = None
    constraints: list[str] | None = None
    transposition_notes: str | None = None
    writer_notes: str | None = None
