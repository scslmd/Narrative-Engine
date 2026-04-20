from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .base import StrictModel


class StoryImportCharacterRequest(StrictModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=100)
    archetype: str = Field(default="unknown", min_length=1, max_length=100)
    external_goal: str = Field(default="", max_length=2000)
    internal_need: str = Field(default="", max_length=2000)
    core_fear: str = Field(default="", max_length=1000)
    primary_strength: str = Field(default="", max_length=1000)
    fatal_flaw: str = Field(default="", max_length=1000)
    backstory: str = Field(default="", max_length=5000)
    voice_notes: str = Field(default="", max_length=2000)
    change_axis: str = Field(default="", max_length=1000)
    contradictions: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    continuity_facts: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_role(cls, data: Any) -> Any:
        if isinstance(data, dict):
            role = str(data.get("role", "")).strip().lower()
            valid_roles = {
                "protagonist", "antagonist", "mentor", "deuteragonist",
                "foil", "supporting", "minor",
            }
            if role and role not in valid_roles:
                data["role"] = "supporting"
        return data


class StoryImportWorldEntry(StrictModel):
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=50000)
    canonical_facts: list[str] = Field(default_factory=list)
    related_character_ids: list[str] = Field(default_factory=list)


class StoryImportArc(StrictModel):
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    stage_map: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _ensure_stage_map(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("stage_map"):
            data["stage_map"] = [
                "status_quo", "inciting_incident", "rising_action",
                "crisis", "climax", "resolution",
            ]
        return data


class StoryImportSequence(StrictModel):
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    chapters: list[str] = Field(default_factory=list)


class StoryImportAnalysis(StrictModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    genre: str = Field(..., min_length=1, max_length=100)
    tone: str = Field(..., min_length=1, max_length=255)
    pov: str = Field(..., min_length=1, max_length=50)
    story_structure: str = Field(..., min_length=1, max_length=100)
    premise: str = Field(..., min_length=1, max_length=10000)
    logline: str = Field(..., min_length=1, max_length=500)
    thematic_spine: str = Field(..., min_length=1, max_length=2000)
    emotional_promise: str = Field(..., min_length=1, max_length=2000)
    target_audience: str = Field(..., min_length=1, max_length=500)
    complexity_level: str = Field(..., min_length=1, max_length=50)
    characters: list[StoryImportCharacterRequest] = Field(..., min_length=1)
    world_bible: list[StoryImportWorldEntry] = Field(default_factory=list)
    story_arcs: list[StoryImportArc] = Field(default_factory=list)
    sequences: list[StoryImportSequence] = Field(default_factory=list)
    narrative_constraints: list[str] = Field(default_factory=list)
    success_definition: str = Field(default="", max_length=2000)
    raw_story_text: str = Field(default="", max_length=5_000_000)

    @model_validator(mode="before")
    @classmethod
    def _normalize_pov(cls, data: Any) -> Any:
        if isinstance(data, dict):
            pov = str(data.get("pov", "")).strip().upper().replace(" ", "_")
            valid_povs = {
                "FIRST", "SECOND", "THIRD_LIMITED", "THIRD_OMNI",
                "THIRD_OBJECTIVE", "THIRD_MULTIPLE", "OTHER",
            }
            if pov and pov not in valid_povs:
                data["pov"] = "THIRD_LIMITED"
        return data

    @model_validator(mode="before")
    @classmethod
    def _normalize_structure(cls, data: Any) -> Any:
        if isinstance(data, dict):
            structure = str(data.get("story_structure", "")).strip().upper().replace(" ", "_")
            valid_structures = {
                "SAVE_THE_CAT", "THREE_ACT", "HERO_JOURNEY",
                "FREYTAGS_PYRAMID", "KISHOTENKETSU", "FICHTEAN_CURVE",
                "SEVEN_POINT_STRUCTURE", "SEVEN_KEY_STEPS",
                "SNOWFLAKE_METHOD", "BRAINDUMP", "OTHER",
            }
            if structure and structure not in valid_structures:
                data["story_structure"] = "THREE_ACT"
        return data


class StoryImportRequest(StrictModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    story_text: str = Field(..., min_length=1, max_length=5_000_000)
    project_id: str | None = Field(None, max_length=255)
    genre: str | None = None
    tone: str | None = None


class StoryImportResponse(StrictModel):
    project_id: str
    status: str
    message: str
    warnings: list[str] = Field(default_factory=list)
