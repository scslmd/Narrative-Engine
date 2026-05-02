from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import StrictModel
from .generation import CanonPolicy, CanonScope


class CanonTargetKind(str, Enum):
    CHARACTER = "character"
    RELATIONSHIP = "relationship"
    WORLD_BIBLE = "world_bible"
    MYTHOS = "mythos"
    PATTERN = "pattern"
    CONTINUITY = "continuity"
    FOUNDATION = "foundation"


class CanonAnnotationKind(str, Enum):
    LOCKED = "locked"
    SOFT_GUIDANCE = "soft_guidance"
    MUTABLE = "mutable"
    FORBIDDEN_CONTRADICTION = "forbidden_contradiction"
    GENERATION_NOTE = "generation_note"


class CanonProfileStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CanonAnnotation(StrictModel):
    annotation_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    target_kind: CanonTargetKind
    target_id: str = Field(..., min_length=1, max_length=255)
    field_path: str = Field(..., min_length=1, max_length=255)
    annotation_kind: CanonAnnotationKind
    note: str = ""
    applies_to_modes: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class CanonAnnotationCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255)
    target_kind: CanonTargetKind
    target_id: str = Field(..., min_length=1, max_length=255)
    field_path: str = Field(..., min_length=1, max_length=255)
    annotation_kind: CanonAnnotationKind
    note: str = ""
    applies_to_modes: list[str] = Field(default_factory=list)


class CanonCustomizationProfile(StrictModel):
    profile_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    default_generation_mode: str = Field(..., min_length=1, max_length=100)
    canon_scope: CanonScope
    canon_policy: CanonPolicy
    generation_brief_template: str = ""
    selected_annotation_ids: list[str] = Field(default_factory=list)
    status: CanonProfileStatus = CanonProfileStatus.DRAFT


class CanonCustomizationProfileCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    default_generation_mode: str = Field("same_project_side_story", min_length=1, max_length=100)
    canon_scope: CanonScope
    canon_policy: CanonPolicy = Field(default_factory=CanonPolicy)
    generation_brief_template: str = ""
    selected_annotation_ids: list[str] = Field(default_factory=list)
    status: CanonProfileStatus = CanonProfileStatus.DRAFT


class CanonCustomizationProfileUpdateRequest(StrictModel):
    name: str | None = None
    description: str | None = None
    default_generation_mode: str | None = None
    canon_scope: CanonScope | None = None
    canon_policy: CanonPolicy | None = None
    generation_brief_template: str | None = None
    selected_annotation_ids: list[str] | None = None
    status: CanonProfileStatus | None = None
