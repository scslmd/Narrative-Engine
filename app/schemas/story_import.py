from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .base import StrictModel


# Phase 1: Structure Detection schemas
class ChapterBoundary(StrictModel):
    id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    section_type: str = Field(..., min_length=1, max_length=20)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_pos: int = Field(ge=0)
    end_pos: int = Field(ge=0)
    estimated_word_count: int = Field(ge=0, default=0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> ChapterBoundary:
        if self.end_line < self.start_line:
            self.end_line = self.start_line
        if self.end_pos < self.start_pos:
            self.end_pos = self.start_pos
        return self


class StructureHint(StrictModel):
    character_names: list[str] = Field(default_factory=list)
    location_names: list[str] = Field(default_factory=list)
    pov_hints: list[str] = Field(default_factory=list)
    thematic_keywords: list[str] = Field(default_factory=list)


class StoryStructureDetection(StrictModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    total_estimated_words: int = Field(ge=0, default=0)
    structure_type: str = Field(..., min_length=1, max_length=30)
    chapters: list[ChapterBoundary] = Field(default_factory=list)
    hints: StructureHint = Field(default_factory=StructureHint)
    narrative_voice: str | None = Field(None, max_length=100)


# Phase 2: Chapter Analysis schemas
class CharacterMention(StrictModel):
    name: str = Field(..., min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    role: str = Field(default="supporting", min_length=1, max_length=100)
    is_first_introduction: bool = False
    physical_description: str = Field(default="", max_length=2000)
    personality_traits: list[str] = Field(default_factory=list)
    actions_in_chunk: list[str] = Field(default_factory=list)
    dialogue_samples: list[str] = Field(default_factory=list, max_length=3)
    relationships_mentioned: list[str] = Field(default_factory=list)
    emotional_state: str = Field(default="", max_length=500)
    motives_observed: str | None = Field(None, max_length=2000)
    development_notes: str | None = Field(None, max_length=2000)


class WorldDetail(StrictModel):
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    canonical_facts: list[str] = Field(default_factory=list)


class PlotEvent(StrictModel):
    summary: str = Field(..., min_length=1, max_length=2000)
    characters_involved: list[str] = Field(default_factory=list)
    significance: str = Field(default="development", min_length=1, max_length=30)
    unresolved_threads: list[str] = Field(default_factory=list)


class ChapterAnalysisResult(StrictModel):
    chapter_id: str = Field(..., min_length=1, max_length=100)
    chapter_title: str = Field(default="", max_length=500)
    section_type: str = Field(default="chapter", min_length=1, max_length=20)
    summary: str = Field(default="", max_length=3000)
    key_events: list[str] = Field(default_factory=list)
    characters: list[CharacterMention] = Field(default_factory=list)
    world_details: list[WorldDetail] = Field(default_factory=list)
    plot_events: list[PlotEvent] = Field(default_factory=list)
    thematic_elements: list[str] = Field(default_factory=list)
    tone_shifts: list[str] | None = Field(None)
    narrative_perspective: str | None = Field(None, max_length=200)


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

    # Deep character analysis fields (multi-pass import)
    aliases: list[str] = Field(default_factory=list)
    physical_description: str = Field(default="", max_length=2000)
    personality_traits: list[str] = Field(default_factory=list)
    motives: str = Field(default="", max_length=2000)
    relationships: list[str] = Field(default_factory=list)
    character_arc: str = Field(default="", max_length=5000)
    symbolic_role: str = Field(default="", max_length=1000)
    dialogue_patterns: str = Field(default="", max_length=2000)
    psychological_depth: str = Field(default="", max_length=3000)
    narrative_purpose: str = Field(default="", max_length=2000)
    thematic_significance: str = Field(default="", max_length=2000)
    impact_on_others: str = Field(default="", max_length=2000)
    first_appearance_chapter: str = Field(default="", max_length=100)
    chapter_appearances: list[str] = Field(default_factory=list)

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
    provenance_note: str = Field(default="", max_length=1000)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class StoryImportChapterSummary(StrictModel):
    chapter_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(default="", max_length=3000)
    section_type: str = Field(default="chapter", min_length=1, max_length=20)
    analysis_status: str = Field(default="complete", min_length=1, max_length=50)
    objective: str = Field(default="", max_length=3000)
    conflict: str = Field(default="", max_length=3000)
    stakes: str = Field(default="", max_length=3000)
    active_character_names: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    plot_events: list[PlotEvent] = Field(default_factory=list)
    estimated_word_count: int | None = Field(default=None, ge=0)
    provenance_note: str = Field(default="", max_length=1000)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class StoryImportPlanningSynthesis(StrictModel):
    sequences: list[StoryImportSequence] = Field(default_factory=list)
    chapter_summaries: list[StoryImportChapterSummary] = Field(default_factory=list)


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
    chapter_summaries: list[StoryImportChapterSummary] = Field(default_factory=list)
    narrative_constraints: list[str] = Field(default_factory=list)
    success_definition: str = Field(default="", max_length=2000)
    completed_chunk_count: int = Field(default=0, ge=0)
    total_estimated_chunks: int = Field(default=0, ge=0)

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
    project_name: str = Field(default="", max_length=255)
    story_text: str = Field(..., min_length=1, max_length=5_000_000)
    project_id: str | None = Field(None, max_length=255)
    genre: str | None = None
    tone: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _require_project_target(cls, data: Any) -> Any:
        if isinstance(data, dict):
            project_name = str(data.get("project_name", "") or "").strip()
            project_id = str(data.get("project_id", "") or "").strip()
            if not project_name and not project_id:
                raise ValueError("project_name is required when project_id is not provided")
            if project_name:
                data["project_name"] = project_name
            if project_id:
                data["project_id"] = project_id
        return data


class StoryImportResponse(StrictModel):
    project_id: str
    status: str
    message: str
    warnings: list[str] = Field(default_factory=list)
    chapters_processed: int = Field(default=0, ge=0)
    total_estimated_chapters: int = Field(default=0, ge=0)
    chunks_processed: int = Field(default=0, ge=0)
    total_estimated_chunks: int = Field(default=0, ge=0)
    analysis_mode: str = Field(default="single_pass", min_length=1, max_length=20)


class ImportSubmitResponse(StrictModel):
    """Response when import job is submitted (202 Accepted)."""
    import_id: str
    status: str = "pending"


class ImportProgressResponse(StrictModel):
    """Response from polling endpoint — progress or final result."""
    import_id: str
    status: str  # pending | running | completed | failed
    phase: str = ""
    chapters_processed: int = 0
    total_estimated_chapters: int = 0
    chunks_processed: int = 0
    total_estimated_chunks: int = 0
    result: StoryImportResponse | None = None
    error: str | None = None
