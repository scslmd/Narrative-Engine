from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import Field, field_validator

from app.schemas.base import StrictSchemaModel
from app.schemas.mythos_extraction import (
    ArchetypalPattern,
    NarrativeStructure,
    Relationship,
    SymbolicMotif,
)


SOURCE_TYPES = ("mythology", "narrative")
GENERATION_MODES = ("same_world", "new_characters", "transposed")


@dataclass
class NarrativePattern:
    pacing: str
    chapter_structure: str = ""
    conflict_type: str = ""
    dialogue_style: str = ""
    scene_transition: str = ""


@dataclass
class VoiceProfile:
    narrative_voice: str
    sentence_rhythm: str = ""
    descriptive_density: str = ""
    humor_level: str = ""
    emotional_temperature: str = ""


@dataclass
class ThematicConstraint:
    theme: str
    moral_stance: str = ""
    recurring_questions: list[str] = field(default_factory=list)
    forbidden_elements: list[str] = field(default_factory=list)


@dataclass
class WorldRule:
    rule: str = ""
    enforcement: str = ""
    exceptions: list[str] = field(default_factory=list)


@dataclass
class StoryEntity:
    name: str = ""
    entity_type: str = ""
    archetype: str = ""
    domain_or_power: str = ""
    canonical_facts: list[str] = field(default_factory=list)


@dataclass
class PatternExtractionAnalysis:
    source_type: str = ""
    source_corpus: str = ""
    generation_mode: str = ""

    # Shared pattern layer
    archetypal_patterns: list[ArchetypalPattern] = field(default_factory=list)
    narrative_structures: list[NarrativeStructure] = field(default_factory=list)
    world_rules: list[WorldRule] = field(default_factory=list)
    symbolic_motifs: list[SymbolicMotif] = field(default_factory=list)

    # Thematic layer
    thematic_spine: str = ""
    emotional_promise: str = ""
    tone_and_voice_direction: str = ""

    # Narrative-specific additions (None for mythology source type)
    narrative_pattern: NarrativePattern | None = None
    voice_profile: VoiceProfile | None = None
    thematic_constraints: list[ThematicConstraint] = field(default_factory=list)

    # Entity layer
    key_entities: list[StoryEntity] = field(default_factory=list)
    entity_relationships: list[Relationship] = field(default_factory=list)


class PatternExtractionRequest(StrictSchemaModel):
    text: str = Field(min_length=1, max_length=5_000_000)
    source_type: str = Field(min_length=1, max_length=20)
    generation_mode: str = Field(default="same_world", min_length=1, max_length=20)
    project_id: str | None = Field(default=None, max_length=100)
    source_corpus: str | None = Field(default=None, max_length=200)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SOURCE_TYPES:
            raise ValueError(
                f"source_type must be one of {SOURCE_TYPES}, got '{value}'"
            )
        return normalized

    @field_validator("generation_mode")
    @classmethod
    def validate_generation_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in GENERATION_MODES:
            raise ValueError(
                f"generation_mode must be one of {GENERATION_MODES}, got '{value}'"
            )
        return normalized


class PatternExtractionSummary(StrictSchemaModel):
    source_corpus: str
    archetypal_patterns: int
    narrative_structures: int
    world_rules: int
    symbolic_motifs: int


class ExtractPatternsRequest(StrictSchemaModel):
    """Request body for extract-patterns endpoint.

    Unlike PatternExtractionRequest, this does not require 'text' because
    source text is retrieved from the project's manuscript documents.
    """

    source_type: str = Field(min_length=1, max_length=20)
    generation_mode: str = Field(default="same_world", min_length=1, max_length=20)
    source_corpus: str | None = Field(default=None, max_length=200)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SOURCE_TYPES:
            raise ValueError(
                f"source_type must be one of {SOURCE_TYPES}, got '{value}'"
            )
        return normalized

    @field_validator("generation_mode")
    @classmethod
    def validate_generation_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in GENERATION_MODES:
            raise ValueError(
                f"generation_mode must be one of {GENERATION_MODES}, got '{value}'"
            )
        return normalized


class PatternExtractionResponse(StrictSchemaModel):
    status: str
    project_id: str
    extraction: PatternExtractionSummary | None = None
    error: str | None = None
