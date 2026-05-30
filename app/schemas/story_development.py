from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, model_validator

from .base import StrictSchemaModel
from .enums import (
    StoryDecisionChangeType,
    StoryDecisionNodeType,
    StoryObjectType,
    StoryArtifactLifecycleState,
    StoryBranchState,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StorySuggestionLifecycleState,
)


def _normalize_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _normalize_optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, field_name=field_name)


def _normalize_text_list(value: object, *, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    return [_normalize_text(item, field_name=field_name) for item in value]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StoryFlowStage(StrictSchemaModel):
    stage_id: str = Field(min_length=1)
    stage_kind: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    description: str | None = None
    position: int = Field(ge=0)
    depends_on: list[str] = Field(default_factory=list)
    stage_configuration_state: StoryFlowStageConfigurationState = StoryFlowStageConfigurationState.ENABLED
    stage_progress_state: StoryFlowStageProgressState = StoryFlowStageProgressState.NOT_STARTED
    writer_notes: str | None = None
    custom_prompt_guidance: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("stage_id", "stage_kind", "display_name"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("description", "writer_notes", "custom_prompt_guidance"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        payload["depends_on"] = _normalize_text_list(payload.get("depends_on", []), field_name="depends_on")
        return payload


class StoryFlowDefinition(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    stages: list[StoryFlowStage] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("project_id", "project_name"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload.setdefault("stages", [])
        return payload


class StoryFlowEdge(StrictSchemaModel):
    edge_id: str = Field(min_length=1)
    source_stage_id: str = Field(min_length=1)
    target_stage_id: str = Field(min_length=1)
    relationship_kind: str = Field(default="dependency", min_length=1)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("edge_id", "source_stage_id", "target_stage_id", "relationship_kind"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        return payload


class StoryFlowRule(StrictSchemaModel):
    rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    stage_id: str | None = None
    enabled: bool = True
    condition: str | None = None
    effect: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("rule_id", "name", "description"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("stage_id", "condition", "effect"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload


class BrainstormItem(StrictSchemaModel):
    item_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    status: str = Field(default="keep", min_length=1)
    tags: list[str] = Field(default_factory=list)
    source_notes: str | None = None
    item_type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("item_id", "project_id", "content", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["tags"] = _normalize_text_list(payload.get("tags", []), field_name="tags")
        if "source_notes" in payload:
            payload["source_notes"] = _normalize_optional_text(payload["source_notes"], field_name="source_notes")
        if "item_type" in payload and payload["item_type"] is not None:
            payload["item_type"] = _normalize_text(payload["item_type"], field_name="item_type")
        return payload


class BrainstormPromotion(StrictSchemaModel):
    promotion_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_item_ids: list[str] = Field(default_factory=list)
    target_object_kind: str = Field(min_length=1)
    target_object_id: str = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("promotion_id", "project_id", "target_object_kind", "target_object_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["source_item_ids"] = _normalize_text_list(payload.get("source_item_ids", []), field_name="source_item_ids")
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        return payload


@dataclass(slots=True)
class PriorChapterSummary:
    """Summary of a prior chapter for cross-chapter continuity context.

    Forward-compatible: same structure used for book summaries in multi-book mode.
    """
    chapter_id: str
    title: str
    key_events: list[str]
    character_states: dict[str, str]
    unresolved_threads: list[str]

    def to_context_string(self) -> str:
        lines = [f"PRIOR CHAPTER: {self.title}", ""]
        if self.key_events:
            lines.append("Key events:")
            for event in self.key_events[:10]:
                lines.append(f"  - {event}")
            lines.append("")
        if self.character_states:
            lines.append("Character states at chapter end:")
            for name, state in list(self.character_states.items())[:10]:
                lines.append(f"  - {name}: {state}")
            lines.append("")
        if self.unresolved_threads:
            lines.append("Unresolved threads:")
            for thread in self.unresolved_threads[:5]:
                lines.append(f"  ? {thread}")
            lines.append("")
        return "\n".join(lines).rstrip()


class FoundationProfile(StrictSchemaModel):
    foundation_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    premise: str = Field(min_length=1)
    logline: str = Field(min_length=1)
    thematic_spine: str = ""
    emotional_promise: str = ""
    tone_and_voice_direction: str = ""
    target_audience: str = ""
    narrative_constraints: list[str] = Field(default_factory=list)
    complexity_level: str = ""
    success_definition: str = ""
    version: int = Field(default=1, ge=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in (
            "foundation_id",
            "project_id",
            "premise",
            "logline",
        ):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in (
            "thematic_spine",
            "emotional_promise",
            "tone_and_voice_direction",
            "target_audience",
            "complexity_level",
            "success_definition",
        ):
            if field_name in payload:
                val = payload[field_name]
                payload[field_name] = val.strip() if isinstance(val, str) else ""
        payload["narrative_constraints"] = _normalize_text_list(
            payload.get("narrative_constraints", []),
            field_name="narrative_constraints",
        )
        return payload


class FoundationRevision(StrictSchemaModel):
    revision_id: str = Field(min_length=1)
    foundation_id: str = Field(min_length=1)
    snapshot: FoundationProfile
    change_summary: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("revision_id", "foundation_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "change_summary" in payload:
            payload["change_summary"] = _normalize_optional_text(payload["change_summary"], field_name="change_summary")
        return payload


class RelationshipEdge(StrictSchemaModel):
    edge_id: str = Field(min_length=1)
    source_character_id: str = Field(min_length=1)
    target_character_id: str = Field(min_length=1)
    relation_kind: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tension: str | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in (
            "edge_id",
            "source_character_id",
            "target_character_id",
            "relation_kind",
            "summary",
        ):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("tension", "notes"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload


class CharacterProfile(StrictSchemaModel):
    character_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    role_in_story: str = Field(min_length=1)
    archetype: str = ""
    external_goal: str = ""
    internal_need: str = ""
    misbelief_or_wound: str = ""
    core_fear: str = ""
    primary_strength: str = ""
    fatal_flaw_or_limitation: str = ""
    contradictions: list[str] = Field(default_factory=list)
    backstory_summary: str = ""
    voice_notes: str = ""
    relationship_edges: list[RelationshipEdge] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    change_axis: str = ""
    arc_stage_notes: list[str] = Field(default_factory=list)
    continuity_facts: list[str] = Field(default_factory=list)
    writer_notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in (
            "character_id",
            "project_id",
            "display_name",
            "role_in_story",
        ):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in (
            "archetype",
            "external_goal",
            "internal_need",
            "misbelief_or_wound",
            "core_fear",
            "primary_strength",
            "fatal_flaw_or_limitation",
            "backstory_summary",
            "voice_notes",
            "change_axis",
        ):
            if field_name in payload and isinstance(payload[field_name], str):
                payload[field_name] = payload[field_name].strip()
        for field_name in ("contradictions", "secrets", "values", "taboos", "arc_stage_notes", "continuity_facts"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        if "writer_notes" in payload:
            payload["writer_notes"] = _normalize_optional_text(payload["writer_notes"], field_name="writer_notes")
        return payload


class WorldBibleEntry(StrictSchemaModel):
    entry_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    entry_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    canonical_facts: list[str] = Field(default_factory=list)
    related_character_ids: list[str] = Field(default_factory=list)
    source_artifacts: list[str] = Field(default_factory=list)
    visibility_scope: str = Field(default="project", min_length=1)
    continuity_warnings: list[str] = Field(default_factory=list)
    writer_notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("entry_id", "project_id", "entry_type", "title", "summary", "visibility_scope"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("canonical_facts", "related_character_ids", "source_artifacts", "continuity_warnings"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        if "writer_notes" in payload:
            payload["writer_notes"] = _normalize_optional_text(payload["writer_notes"], field_name="writer_notes")
        return payload


class ArcCandidate(StrictSchemaModel):
    arc_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    stage_map_notes: list[str] = Field(default_factory=list)
    fit_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("arc_id", "project_id", "name", "summary"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("stage_map_notes", "fit_notes", "tags"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload


class ArcComparisonCandidateRecord(StrictSchemaModel):
    candidate: ArcCandidate
    rank: int = Field(ge=1)
    score: tuple[int, int, int, int]
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        payload["notes"] = _normalize_text_list(payload.get("notes", []), field_name="notes")
        return payload


class ArcComparisonRecord(StrictSchemaModel):
    comparison_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    candidate_ids: list[str]
    candidate_set: list[ArcCandidate]
    ranked_candidates: list[ArcComparisonCandidateRecord]
    review_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("comparison_id", "project_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("candidate_ids", "review_notes"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload

    @model_validator(mode="after")
    def validate_candidate_comparison(self) -> "ArcComparisonRecord":
        if len(self.candidate_ids) < 2:
            raise ValueError("candidate_ids must include at least two arc candidates")
        if len(self.candidate_set) < 2:
            raise ValueError("candidate_set must include at least two arc candidates")
        if len(self.ranked_candidates) < 2:
            raise ValueError("ranked_candidates must include at least two ranked candidates")

        candidate_id_list = [candidate.arc_id for candidate in self.candidate_set]
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate_ids must not contain duplicates")
        if len(set(candidate_id_list)) != len(candidate_id_list):
            raise ValueError("candidate_set must not contain duplicate arc ids")

        candidate_ids = set(candidate_id_list)
        if set(self.candidate_ids) != candidate_ids:
            raise ValueError("candidate_ids must match candidate_set arc ids")
        ranked_id_list = [ranked.candidate.arc_id for ranked in self.ranked_candidates]
        ranked_ids = set(ranked_id_list)
        if ranked_ids != candidate_ids:
            raise ValueError("ranked_candidates must include each candidate exactly once")
        if len(ranked_ids) != len(ranked_id_list):
            raise ValueError("ranked_candidates must not repeat candidates")
        ranks = [ranked.rank for ranked in self.ranked_candidates]
        if sorted(ranks) != list(range(1, len(self.ranked_candidates) + 1)):
            raise ValueError("ranked_candidates must use contiguous unique ranks starting at 1")
        return self


class ArcStageMap(StrictSchemaModel):
    arc_stage_map_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    arc_id: str = Field(min_length=1)
    stage_kinds: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("arc_stage_map_id", "project_id", "arc_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["stage_kinds"] = _normalize_text_list(payload.get("stage_kinds", []), field_name="stage_kinds")
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        return payload


class ArcSelection(StrictSchemaModel):
    selection_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    selected_arc: ArcCandidate
    rejected_arc_ids: list[str] = Field(default_factory=list)
    comparison_notes: list[str] = Field(default_factory=list)
    comparison_record_ids: list[str] = Field(default_factory=list)
    stage_map: ArcStageMap | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("selection_id", "project_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["rejected_arc_ids"] = _normalize_text_list(payload.get("rejected_arc_ids", []), field_name="rejected_arc_ids")
        payload["comparison_notes"] = _normalize_text_list(payload.get("comparison_notes", []), field_name="comparison_notes")
        payload["comparison_record_ids"] = _normalize_text_list(
            payload.get("comparison_record_ids", []),
            field_name="comparison_record_ids",
        )
        return payload


class BeatPlan(StrictSchemaModel):
    beat_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    conflict: str = Field(min_length=1)
    stakes: str = Field(min_length=1)
    dependency_ids: list[str] = Field(default_factory=list)
    arc_stage: str = Field(min_length=1)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1)
    provenance_note: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("beat_id", "project_id", "objective", "conflict", "stakes", "arc_stage", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("dependency_ids", "active_character_ids", "continuity_requirements", "unresolved_questions"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload


class SequencePlan(StrictSchemaModel):
    sequence_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    beat_ids: list[str] = Field(default_factory=list)
    chapter_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1)
    provenance_note: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("sequence_id", "project_id", "title", "summary", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["beat_ids"] = _normalize_text_list(payload.get("beat_ids", []), field_name="beat_ids")
        payload["chapter_ids"] = _normalize_text_list(payload.get("chapter_ids", []), field_name="chapter_ids")
        return payload


class ChapterPlan(StrictSchemaModel):
    chapter_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sequence_id: str | None = None
    objective: str = Field(min_length=1)
    conflict: str = Field(min_length=1)
    stakes: str = Field(min_length=1)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1)
    provenance_note: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("chapter_id", "project_id", "title", "summary", "objective", "conflict", "stakes", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "sequence_id" in payload:
            payload["sequence_id"] = _normalize_optional_text(payload["sequence_id"], field_name="sequence_id")
        for field_name in ("active_character_ids", "continuity_requirements", "unresolved_questions"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload


class ScenePlan(StrictSchemaModel):
    scene_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    chapter_id: str | None = None
    objective: str = Field(min_length=1)
    conflict: str = Field(min_length=1)
    stakes: str = Field(min_length=1)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1)
    provenance_note: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("scene_id", "project_id", "title", "summary", "objective", "conflict", "stakes", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "chapter_id" in payload:
            payload["chapter_id"] = _normalize_optional_text(payload["chapter_id"], field_name="chapter_id")
        for field_name in ("active_character_ids", "continuity_requirements", "unresolved_questions"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload


class ChapterPacket(StrictSchemaModel):
    packet_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    included_reference_ids: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    scene_goals: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1)
    provenance_note: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("packet_id", "project_id", "chapter_id", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("included_reference_ids", "constraints", "scene_goals"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        return payload


class PlanningDependency(StrictSchemaModel):
    dependency_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    upstream_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    dependency_kind: str = Field(min_length=1)
    reason: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("dependency_id", "project_id", "upstream_id", "downstream_id", "dependency_kind"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "reason" in payload:
            payload["reason"] = _normalize_optional_text(payload["reason"], field_name="reason")
        return payload


class DraftArtifact(StrictSchemaModel):
    artifact_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    source_plan_ids: list[str] = Field(default_factory=list)
    source_context: list[str] = Field(default_factory=list)
    provenance_note: str | None = Field(None, max_length=2000)
    status: StoryArtifactLifecycleState = StoryArtifactLifecycleState.DRAFT
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("artifact_id", "project_id", "title", "content"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("source_plan_ids", "source_context"):
            payload[field_name] = _normalize_text_list(payload.get(field_name, []), field_name=field_name)
        if "provenance_note" in payload:
            payload["provenance_note"] = _normalize_optional_text(payload["provenance_note"], field_name="provenance_note")
        return payload


class ManuscriptDocument(StrictSchemaModel):
    document_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    display_title: str | None = None
    content: str = Field(min_length=1)
    chapter_id: str | None = None
    scene_id: str | None = None
    current_draft_artifact_id: str | None = None
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("document_id", "project_id", "title", "content"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("chapter_id", "scene_id", "current_draft_artifact_id", "display_title"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload


class ManuscriptDocumentUpdateRequest(StrictSchemaModel):
    content: str | None = Field(None, max_length=1_000_000)
    title: str | None = Field(None, max_length=500)
    display_title: str | None = Field(None, max_length=500)


class DraftArtifactCreateRequest(StrictSchemaModel):
    artifact_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    source_plan_ids: list[str] = Field(default_factory=list)
    source_context: list[str] = Field(default_factory=list)
    provenance_note: str | None = Field(None, max_length=2000)
    status: str = Field(default=StoryArtifactLifecycleState.DRAFT.value)


class DraftContinuationRequest(StrictSchemaModel):
    artifact_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    prior_draft_artifact_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    prior_manuscript_document_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    source_plan_ids: list[str] = Field(default_factory=list)
    source_context: list[str] = Field(default_factory=list)
    provenance_note: str | None = Field(None, max_length=2000)


class AlternateVariantRequest(StrictSchemaModel):
    artifact_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    base_draft_artifact_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    base_manuscript_document_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    source_plan_ids: list[str] = Field(default_factory=list)
    source_context: list[str] = Field(default_factory=list)
    provenance_note: str | None = Field(None, max_length=2000)


class ManuscriptReviewResponse(StrictSchemaModel):
    document_id: str
    project_id: str
    findings: list[RevisionSuggestion] = Field(default_factory=list)


class RevisionSuggestion(StrictSchemaModel):
    suggestion_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    target_document_id: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    proposed_text: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source_context: list[str] = Field(default_factory=list)
    status: StorySuggestionLifecycleState = StorySuggestionLifecycleState.REQUESTED

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("suggestion_id", "project_id", "target_document_id", "source_text", "proposed_text", "rationale"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["source_context"] = _normalize_text_list(payload.get("source_context", []), field_name="source_context")
        return payload


class ReviewDecision(StrictSchemaModel):
    decision_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    target_kind: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    notes: str | None = None
    source_context: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("decision_id", "project_id", "target_id", "target_kind", "decision"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        payload["source_context"] = _normalize_text_list(payload.get("source_context", []), field_name="source_context")
        return payload


class StoryDecisionNodeLink(StrictSchemaModel):
    object_type: StoryObjectType
    object_id: str = Field(min_length=1)
    relation_kind: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        if "object_type" in payload:
            payload["object_type"] = _normalize_text(payload["object_type"], field_name="object_type")
        for field_name in ("object_id", "relation_kind"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        return payload


class StoryDecisionNode(StrictSchemaModel):
    node_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    node_type: StoryDecisionNodeType
    change_type: StoryDecisionChangeType
    subject_type: StoryObjectType
    subject_id: str = Field(min_length=1)
    parent_node_id: str | None = Field(default=None, min_length=1)
    branch_id: str | None = Field(default=None, min_length=1)
    summary: str = Field(min_length=1)
    prior_state_ref: str | None = Field(default=None, min_length=1)
    prior_state_summary: str | None = Field(default=None, min_length=1)
    new_state_ref: str | None = Field(default=None, min_length=1)
    new_state_summary: str | None = Field(default=None, min_length=1)
    reason_or_note: str | None = Field(default=None, min_length=1)
    decision_made_at: datetime
    made_by: str = Field(min_length=1)
    related_object_links: list[StoryDecisionNodeLink] = Field(default_factory=list)
    informing_object_links: list[StoryDecisionNodeLink] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("node_type", "change_type", "subject_type"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in (
            "node_id",
            "project_id",
            "subject_id",
            "summary",
            "made_by",
        ):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("parent_node_id", "branch_id", "prior_state_ref", "prior_state_summary", "new_state_ref", "new_state_summary", "reason_or_note"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload

    @model_validator(mode="after")
    def validate_timeline_fields(self) -> "StoryDecisionNode":
        has_prior_ref = self.prior_state_ref is not None
        has_prior_summary = self.prior_state_summary is not None
        has_new_ref = self.new_state_ref is not None
        has_new_summary = self.new_state_summary is not None
        if not (has_prior_ref or has_prior_summary or has_new_ref or has_new_summary):
            raise ValueError("at least one prior or new state reference or summary is required")
        return self


class BranchPoint(StrictSchemaModel):
    branch_point_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_node_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("branch_point_id", "project_id", "source_node_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        return payload


class StoryBranch(StrictSchemaModel):
    branch_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_point_id: str = Field(min_length=1)
    branch_name: str = Field(min_length=1)
    branch_state: StoryBranchState = StoryBranchState.ACTIVE

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("branch_id", "project_id", "branch_point_id", "branch_name"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "branch_state" in payload:
            payload["branch_state"] = _normalize_text(payload["branch_state"], field_name="branch_state").upper()
        return payload


class BranchStateRef(StrictSchemaModel):
    branch_state_ref_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branch_id: str = Field(min_length=1)
    state_object_type: StoryObjectType
    state_object_id: str = Field(min_length=1)
    decision_node_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        if "state_object_type" in payload:
            payload["state_object_type"] = _normalize_text(payload["state_object_type"], field_name="state_object_type").upper()
        for field_name in ("branch_state_ref_id", "project_id", "branch_id", "state_object_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "decision_node_id" in payload:
            payload["decision_node_id"] = _normalize_optional_text(payload["decision_node_id"], field_name="decision_node_id")
        return payload


class BranchComparisonRecord(StrictSchemaModel):
    comparison_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_branch_id: str = Field(min_length=1)
    target_branch_id: str = Field(min_length=1)
    review_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("comparison_id", "project_id", "source_branch_id", "target_branch_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["review_notes"] = _normalize_text_list(payload.get("review_notes", []), field_name="review_notes")
        return payload

    @model_validator(mode="after")
    def validate_pair(self) -> "BranchComparisonRecord":
        if self.source_branch_id == self.target_branch_id:
            raise ValueError("source_branch_id and target_branch_id must differ")
        return self


class BranchMergeDecision(StrictSchemaModel):
    merge_decision_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_branch_id: str = Field(min_length=1)
    target_branch_id: str = Field(min_length=1)
    merge_rationale: str = Field(min_length=1)
    resulting_decision_node_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("merge_decision_id", "project_id", "source_branch_id", "target_branch_id", "merge_rationale"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["resulting_decision_node_ids"] = _normalize_text_list(
            payload.get("resulting_decision_node_ids", []),
            field_name="resulting_decision_node_ids",
        )
        return payload

    @model_validator(mode="after")
    def validate_branch_pair(self) -> "BranchMergeDecision":
        if self.source_branch_id == self.target_branch_id:
            raise ValueError("source_branch_id and target_branch_id must differ")
        if len(set(self.resulting_decision_node_ids)) != len(self.resulting_decision_node_ids):
            raise ValueError("resulting_decision_node_ids must not contain duplicates")
        return self


class CheckerFinding(StrictSchemaModel):
    finding_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    source_object_id: str = Field(min_length=1)
    source_object_kind: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    details: str | None = None
    source_context: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("finding_id", "project_id", "source_object_id", "source_object_kind", "severity", "summary"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "details" in payload:
            payload["details"] = _normalize_optional_text(payload["details"], field_name="details")
        payload["source_context"] = _normalize_text_list(payload.get("source_context", []), field_name="source_context")
        return payload


class StepRecord(StrictSchemaModel):
    step_record_id: int | None = None
    logical_run_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    run_kind: str = Field(min_length=1)
    attempt_number: int = Field(ge=1)
    step_name: str = Field(min_length=1)
    step_index: int = Field(ge=0)
    state: str = Field(min_length=1)
    project_id: str | None = None
    model_id: str | None = None
    critic_profile: str | None = None
    backend_name: str | None = None
    backend_version: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    prompt_hash: str | None = None
    input_artifact_refs: list[str] = Field(default_factory=list)
    output_artifact_refs: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    finish_reason: str | None = None
    error_code: str | None = None
    error_category: str | None = None
    executor_id: str | None = None
    lease_owner: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("logical_run_id", "run_id", "run_kind", "step_name", "state"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in (
            "project_id",
            "model_id",
            "critic_profile",
            "backend_name",
            "backend_version",
            "input_hash",
            "output_hash",
            "prompt_hash",
            "finish_reason",
            "error_code",
            "error_category",
            "executor_id",
            "lease_owner",
        ):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        payload["input_artifact_refs"] = _normalize_text_list(payload.get("input_artifact_refs", []), field_name="input_artifact_refs")
        payload["output_artifact_refs"] = _normalize_text_list(payload.get("output_artifact_refs", []), field_name="output_artifact_refs")
        return payload


class ArtifactLineage(StrictSchemaModel):
    artifact_lineage_id: int | None = None
    logical_run_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    run_kind: str = Field(min_length=1)
    attempt_number: int = Field(ge=1)
    step_name: str = Field(min_length=1)
    project_id: str | None = None
    artifact_role: str = Field(min_length=1)
    artifact_kind: str = Field(min_length=1)
    path: str = Field(min_length=1)
    content_hash: str | None = None
    status: StoryArtifactLifecycleState = StoryArtifactLifecycleState.DRAFT
    validation_state: str = Field(min_length=1)
    produced_at: datetime
    registered_at: datetime | None = None
    supersedes_artifact_lineage_id: int | None = None
    source_artifact_refs: list[str] = Field(default_factory=list)
    source_content_hashes: list[str] = Field(default_factory=list)
    output_of_step_record_id: int

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("logical_run_id", "run_id", "run_kind", "step_name", "artifact_role", "artifact_kind", "path", "validation_state"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("project_id", "content_hash"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        payload["source_artifact_refs"] = _normalize_text_list(payload.get("source_artifact_refs", []), field_name="source_artifact_refs")
        payload["source_content_hashes"] = _normalize_text_list(payload.get("source_content_hashes", []), field_name="source_content_hashes")
        return payload


class InspectRunLink(StrictSchemaModel):
    link_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    object_kind: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    logical_run_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    run_kind: str = Field(min_length=1)
    attempt_number: int | None = None
    label: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("link_id", "project_id", "object_kind", "object_id", "logical_run_id", "run_id", "run_kind"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "label" in payload:
            payload["label"] = _normalize_optional_text(payload["label"], field_name="label")
        return payload


class WorkspaceNote(StrictSchemaModel):
    note_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    pinned_object_ids: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("note_id", "project_id", "content"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["pinned_object_ids"] = _normalize_text_list(payload.get("pinned_object_ids", []), field_name="pinned_object_ids")
        return payload


class StoryboardCard(StrictSchemaModel):
    card_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    card_type: str = Field(default="idea", min_length=1)
    column_id: str | None = None
    position: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    character_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("card_id", "project_id", "title", "content", "card_type"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "column_id" in payload:
            payload["column_id"] = _normalize_optional_text(payload["column_id"], field_name="column_id")
        payload["tags"] = _normalize_text_list(payload.get("tags", []), field_name="tags")
        payload["character_ids"] = _normalize_text_list(payload.get("character_ids", []), field_name="character_ids")
        payload["dependencies"] = _normalize_text_list(payload.get("dependencies", []), field_name="dependencies")
        if "metadata" in payload and payload["metadata"] is not None:
            payload["metadata"] = payload["metadata"] if isinstance(payload["metadata"], dict) else {}
        else:
            payload["metadata"] = {}
        return payload


# --- Research ---


class ResearchItem(StrictSchemaModel):
    item_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_url: str | None = None
    source_type: str = Field(default="other", min_length=1)
    genre_tags: list[str] = Field(default_factory=list)
    status: str = Field(default="active", min_length=1)
    citations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("item_id", "project_id", "title", "content"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("source_url", "source_type", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        payload["genre_tags"] = _normalize_text_list(payload.get("genre_tags", []), field_name="genre_tags")
        payload["citations"] = _normalize_text_list(payload.get("citations", []), field_name="citations")
        return payload


class ResearchItemCreateRequest(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_url: str | None = None
    source_type: str = Field(default="other", min_length=1)
    status: str = Field(default="active", min_length=1)
    genre_tags: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("project_id", "title", "content"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "source_url" in payload:
            payload["source_url"] = _normalize_optional_text(payload["source_url"], field_name="source_url")
        if "source_type" in payload:
            payload["source_type"] = _normalize_optional_text(payload["source_type"], field_name="source_type")
        payload["genre_tags"] = _normalize_text_list(payload.get("genre_tags", []), field_name="genre_tags")
        payload["citations"] = _normalize_text_list(payload.get("citations", []), field_name="citations")
        return payload


class ResearchItemUpdateRequest(StrictSchemaModel):
    title: str | None = Field(None, min_length=1)
    content: str | None = Field(None, min_length=1)
    source_url: str | None = None
    source_type: str | None = None
    genre_tags: list[str] | None = None
    status: str | None = None
    citations: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("title", "content", "source_url", "source_type", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        if "genre_tags" in payload:
            payload["genre_tags"] = _normalize_text_list(payload["genre_tags"], field_name="genre_tags")
        if "citations" in payload:
            payload["citations"] = _normalize_text_list(payload["citations"], field_name="citations")
        return payload


class ResearchItemListResponse(StrictSchemaModel):
    project_id: str
    items: list[ResearchItem] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# --- Revision ---


class RevisionChecklistItem(StrictSchemaModel):
    item_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    done: bool = False


class RevisionPass(StrictSchemaModel):
    pass_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    pass_type: str = Field(min_length=1)
    status: str = Field(default="pending", min_length=1)
    checklist: list[RevisionChecklistItem] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("pass_id", "project_id", "pass_type", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        return payload


class RevisionPassCreateRequest(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    pass_type: str = Field(min_length=1)
    status: str = Field(default="pending", min_length=1)
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("project_id", "pass_type", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "notes" in payload:
            payload["notes"] = _normalize_optional_text(payload["notes"], field_name="notes")
        return payload


class RevisionPassUpdateRequest(StrictSchemaModel):
    status: str | None = None
    notes: str | None = None
    checklist: list[RevisionChecklistItem] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("status", "notes"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload


class RevisionPassListResponse(StrictSchemaModel):
    project_id: str
    items: list[RevisionPass] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# --- Polish ---


class PolishReport(StrictSchemaModel):
    report_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    readability_score: float = 0.0
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    passive_voice_count: int = 0
    repetitive_words: list[str] = Field(default_factory=list)
    style_issues: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("report_id", "project_id", "document_id"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        payload["repetitive_words"] = _normalize_text_list(payload.get("repetitive_words", []), field_name="repetitive_words")
        payload["style_issues"] = _normalize_text_list(payload.get("style_issues", []), field_name="style_issues")
        return payload


class ExportRequest(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    format: Literal["docx", "epub", "pdf", "markdown"] = "markdown"
    include_frontmatter: bool = False
    include_toc: bool = False
    stylesheet: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("project_id", "document_id", "format"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        if "stylesheet" in payload:
            payload["stylesheet"] = _normalize_optional_text(payload["stylesheet"], field_name="stylesheet")
        return payload

    @model_validator(mode="after")
    def validate_unsupported_options(self) -> ExportRequest:
        unsupported = []
        if self.include_frontmatter:
            unsupported.append("include_frontmatter")
        if self.include_toc:
            unsupported.append("include_toc")
        if self.stylesheet is not None:
            unsupported.append("stylesheet")
        if unsupported:
            raise ValueError(
                f"Export options are not supported: {', '.join(unsupported)}"
            )
        return self


class PolishAnalyzeRequest(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    text: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("project_id", "document_id", "text"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        return payload


class ExportStatus(StrictSchemaModel):
    export_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    format: str = Field(min_length=1)
    status: str = Field(default="queued", min_length=1)
    artifact_path: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        for field_name in ("export_id", "project_id", "document_id", "format", "status"):
            if field_name in payload:
                payload[field_name] = _normalize_text(payload[field_name], field_name=field_name)
        for field_name in ("artifact_path", "error_message"):
            if field_name in payload:
                payload[field_name] = _normalize_optional_text(payload[field_name], field_name=field_name)
        return payload


class PolishReportListResponse(StrictSchemaModel):
    project_id: str
    items: list[PolishReport] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)
