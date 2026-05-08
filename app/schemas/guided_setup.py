from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from .base import StrictModel


class ChatMessage(StrictModel):
    """A single message in the guided setup conversation."""
    role: str = Field(..., min_length=1, max_length=20)
    content: str = Field(..., min_length=1, max_length=10000)
    turn: int = Field(ge=1)

    @field_validator("role", mode="before")
    @classmethod
    def _normalize_role(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "user"
        role = v.strip().lower()
        if role not in {"user", "system", "assistant"}:
            return "user"
        return role


class GuidedCharacter(StrictModel):
    """Character profile extracted from conversation."""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="supporting", min_length=1, max_length=100)
    archetype: str = Field(default="", max_length=100)
    age_range: str = Field(default="", max_length=100)
    external_goal: str = Field(default="", max_length=2000)
    internal_need: str = Field(default="", max_length=2000)
    core_fear: str = Field(default="", max_length=1000)
    primary_strength: str = Field(default="", max_length=1000)
    fatal_flaw: str = Field(default="", max_length=1000)
    backstory_summary: str = Field(default="", max_length=5000)
    voice_notes: str = Field(default="", max_length=2000)
    contradictions: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    change_axis: str = Field(default="", max_length=1000)

    @field_validator("role", mode="before")
    @classmethod
    def _normalize_role(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "supporting"
        role = v.strip().lower()
        valid_roles = {
            "protagonist", "antagonist", "mentor", "deuteragonist",
            "foil", "supporting", "minor",
        }
        return role if role in valid_roles else "supporting"


class GuidedWorldEntry(StrictModel):
    """World bible entry extracted from conversation."""
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=50000)
    canonical_facts: list[str] = Field(default_factory=list)


class GuidedArc(StrictModel):
    """Story arc extracted from conversation."""
    character_name: str = Field(..., min_length=1, max_length=255)
    arc_type: str = Field(default="transformation", min_length=1, max_length=100)
    summary: str = Field(default="", max_length=5000)
    stages: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("arc_type", mode="before")
    @classmethod
    def _normalize_arc_type(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "transformation"
        arc_type = v.strip().lower()
        valid_types = {
            "transformation", "positive_change", "negative_change",
            "flat", "tragic", "redemption",
        }
        return arc_type if arc_type in valid_types else "transformation"

    @field_validator("stages", mode="before")
    @classmethod
    def _ensure_stages(cls, v: Any) -> list[str]:
        if isinstance(v, list) and len(v) > 0:
            return v
        return [
            "status_quo", "inciting_incident", "rising_action",
            "crisis", "climax", "resolution",
        ]

    @model_validator(mode="after")
    def _ensure_stages_after_default(self) -> GuidedArc:
        if not self.stages:
            object.__setattr__(self, "stages", [
                "status_quo", "inciting_incident", "rising_action",
                "crisis", "climax", "resolution",
            ])
        return self


class GuidedSequence(StrictModel):
    """Sequence (act/section) extracted from conversation."""
    sequence_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    chapter_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="guided", max_length=50)


class GuidedChapter(StrictModel):
    """Chapter plan extracted from conversation."""
    chapter_id: str = Field(..., min_length=1, max_length=255)
    sequence_id: str | None = None
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    objective: str = Field(default="", max_length=2000)
    conflict: str = Field(default="", max_length=2000)
    stakes: str = Field(default="", max_length=2000)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    position: int = Field(default=0, ge=0)
    status: str = Field(default="guided", max_length=50)


class GuidedConfig(StrictModel):
    """Project configuration extracted from conversation."""
    project_name: str = Field(default="", max_length=255)
    genre: str = Field(default="", max_length=100)
    tone_profile: str = Field(default="Neutral", max_length=255)
    pov: str = Field(default="Third_Limited", max_length=50)
    story_structure: str = Field(default="THREE_ACT", max_length=100)
    primary_language: str = Field(default="English", max_length=100)
    secondary_language: str | None = None
    constraints: list[str] = Field(default_factory=list)

    @field_validator("pov", mode="before")
    @classmethod
    def _normalize_pov(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "Third_Limited"
        pov = v.strip().upper().replace(" ", "_")
        valid_povs = {
            "FIRST", "SECOND", "THIRD_LIMITED", "THIRD_OMNI",
            "THIRD_OBJECTIVE", "THIRD_MULTIPLE", "OTHER",
        }
        # Convert to Title_Case format used by PovMode enum
        normalized = {"FIRST": "First", "SECOND": "Second", "THIRD_LIMITED": "Third_Limited",
                      "THIRD_OMNI": "Third_Omni", "THIRD_OBJECTIVE": "Third_Objective",
                      "THIRD_MULTIPLE": "Third_Multiple", "OTHER": "Other"}.get(pov)
        return normalized if normalized else "Third_Limited"

    @field_validator("story_structure", mode="before")
    @classmethod
    def _normalize_structure(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "THREE_ACT"
        structure = v.strip().upper().replace(" ", "_")
        valid_structures = {
            "SAVE_THE_CAT", "THREE_ACT", "HERO_JOURNEY",
            "FREYTAGS_PYRAMID", "KISHOTENKETSU", "FICHTEAN_CURVE",
            "SEVEN_POINT_STRUCTURE", "SEVEN_KEY_STEPS",
            "SNOWFLAKE_METHOD", "BRAINDUMP", "OTHER",
        }
        return structure if structure in valid_structures else "THREE_ACT"


class GuidedFoundation(StrictModel):
    """Foundation profile extracted from conversation."""
    premise_text: str = Field(default="", max_length=10000)
    logline: str = Field(default="", max_length=500)
    thematic_spine: str = Field(default="", max_length=2000)
    emotional_promise: str = Field(default="", max_length=2000)
    target_audience: str = Field(default="", max_length=500)
    complexity_level: str = Field(default="", max_length=50)
    success_definition: str = Field(default="", max_length=2000)
    narrative_constraints: list[str] = Field(default_factory=list)


class ExtractedFields(StrictModel):
    """All fields extracted from the conversation so far."""
    config: GuidedConfig = Field(default_factory=GuidedConfig)
    foundation: GuidedFoundation = Field(default_factory=GuidedFoundation)
    characters: list[GuidedCharacter] = Field(default_factory=list)
    world_bible: list[GuidedWorldEntry] = Field(default_factory=list)
    arcs: list[GuidedArc] = Field(default_factory=list)
    sequences: list[GuidedSequence] = Field(default_factory=list)
    chapters: list[GuidedChapter] = Field(default_factory=list)


class CategoryProgress(StrictModel):
    """Completion status for a category of fields."""
    category: str = Field(..., min_length=1, max_length=50)
    completeness: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    fields_collected: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)


class GuidedSetupAnalyzeRequest(StrictModel):
    """Request to analyze a conversation turn."""
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    current_answer: str = Field(..., min_length=1, max_length=10000)
    accumulated_fields: ExtractedFields = Field(default_factory=ExtractedFields)


class GuidedSetupAnalyzeResponse(StrictModel):
    """Response from analyzing a conversation turn."""
    extracted_fields: ExtractedFields
    next_question: str = Field(..., min_length=1, max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    progress: float = Field(ge=0.0, le=100.0)
    ready_to_create: bool = False
    category_progress: list[CategoryProgress] = Field(default_factory=list)


class GuidedSetupCreateRequest(StrictModel):
    """Request to create a project from accumulated fields."""
    accumulated_fields: ExtractedFields

    @model_validator(mode="after")
    def _validate_minimum_requirements(self) -> GuidedSetupCreateRequest:
        config = self.accumulated_fields.config
        if not config.project_name.strip():
            raise ValueError("project_name is required")
        if not config.genre.strip():
            raise ValueError("genre is required")
        return self


class GuidedSetupCreateResponse(StrictModel):
    """Response after creating a project from guided setup."""
    project_id: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    characters_created: int = Field(ge=0)
    world_entries_created: int = Field(ge=0)
    arcs_created: int = Field(ge=0)
    foundation_created: bool = False
    sequences_created: int = Field(ge=0, default=0)
    chapters_created: int = Field(ge=0, default=0)
    message: str = Field(default="Project created successfully")
