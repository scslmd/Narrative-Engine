from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from .base import StrictModel


class GenerationMode(str, Enum):
    SAME_PROJECT_NEW_ARC = "same_project_new_arc"
    SAME_PROJECT_SEQUEL = "same_project_sequel"
    SAME_PROJECT_PREQUEL = "same_project_prequel"
    SAME_PROJECT_SIDE_STORY = "same_project_side_story"
    SAME_PROJECT_ALTERNATE_ROUTE = "same_project_alternate_route"
    NEW_PROJECT_CHARACTER_FORK = "new_project_character_fork"
    NEW_PROJECT_WORLD_FORK = "new_project_world_fork"
    NEW_PROJECT_HYBRID_FORK = "new_project_hybrid_fork"


class DestinationKind(str, Enum):
    SAME_PROJECT = "same_project"
    NEW_PROJECT = "new_project"


class ContinuityStrictness(str, Enum):
    WARN = "warn"
    BLOCK = "block"
    REPAIR_ONCE = "repair_once"
    REPAIR_TWICE = "repair_twice"


class GenerationRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class GenerationPlanStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    BLOCKED = "blocked"
    FAILED = "failed"


class WorldBibleRef(StrictModel):
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)


class CanonScope(StrictModel):
    source_project_id: str = Field(..., min_length=1, max_length=255)
    scope_mode: str = Field(default="selected", min_length=1, max_length=30)
    character_ids: list[str] = Field(default_factory=list)
    world_bible_refs: list[WorldBibleRef] = Field(default_factory=list)
    continuity_thread_ids: list[str] = Field(default_factory=list)
    arc_ids: list[str] = Field(default_factory=list)
    mythos_ids: list[str] = Field(default_factory=list)
    pattern_ids: list[str] = Field(default_factory=list)
    include_relationships: bool = True
    include_unresolved_questions: bool = True
    include_contradictions_as_forbidden: bool = True

    @model_validator(mode="after")
    def _validate_scope(self) -> CanonScope:
        if self.scope_mode == "full_project":
            return self
        has_scope = any(
            (
                self.character_ids,
                self.world_bible_refs,
                self.continuity_thread_ids,
                self.arc_ids,
                self.mythos_ids,
                self.pattern_ids,
            )
        )
        if not has_scope:
            raise ValueError(
                "at least one canon scope selector is required unless scope_mode is full_project"
            )
        return self


class GenerationDestination(StrictModel):
    destination_kind: DestinationKind
    target_project_id: str | None = Field(default=None, max_length=255)
    target_project_name: str | None = Field(default=None, max_length=255)
    source_branch_id: str | None = Field(default=None, max_length=255)
    target_branch_id: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _validate_destination(self) -> GenerationDestination:
        if self.destination_kind == DestinationKind.SAME_PROJECT and not self.target_project_id:
            raise ValueError("target_project_id is required for same_project destination")
        if self.destination_kind == DestinationKind.NEW_PROJECT and not self.target_project_name:
            raise ValueError("target_project_name is required for new_project destination")
        return self


class CanonPolicy(StrictModel):
    locked_character_fields: list[str] = Field(
        default_factory=lambda: [
            "display_name",
            "role_in_story",
            "backstory",
            "voice_notes",
            "continuity_facts",
            "relationships_json",
        ]
    )
    locked_world_fields: list[str] = Field(
        default_factory=lambda: [
            "entry_type",
            "title",
            "summary",
            "canonical_facts",
        ]
    )
    allowed_character_changes: list[str] = Field(default_factory=list)
    allowed_world_changes: list[str] = Field(default_factory=list)
    forbidden_contradictions: list[str] = Field(default_factory=list)
    continuity_strictness: ContinuityStrictness = ContinuityStrictness.REPAIR_ONCE


class GenerationReviewPolicy(StrictModel):
    require_manual_approval: bool = True
    auto_promote_on_clean_gates: bool = False
    block_on_warnings: bool = False


class CanonicalCharacterSnapshot(StrictModel):
    character_id: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    role_in_story: str = Field(default="", max_length=100)
    continuity_facts: list[str] = Field(default_factory=list)
    voice_notes: str = Field(default="", max_length=5000)


class CanonicalRelationshipSnapshot(StrictModel):
    edge_id: str = Field(..., min_length=1, max_length=255)
    source_character_id: str = Field(..., min_length=1, max_length=255)
    target_character_id: str = Field(..., min_length=1, max_length=255)
    relation_kind: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(default="", max_length=5000)


class CanonicalWorldSnapshot(StrictModel):
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=10000)
    canonical_facts: list[str] = Field(default_factory=list)


class CanonicalArcSnapshot(StrictModel):
    arc_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=10000)


class CanonicalContinuityThreadSnapshot(StrictModel):
    thread_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(default="", max_length=10000)


class CanonicalContinuityFindingSnapshot(StrictModel):
    finding_key: str | None = Field(default=None, max_length=255)
    contradictions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class CanonicalDraftingContextSnapshot(StrictModel):
    packet_id: str = Field(..., min_length=1, max_length=255)
    brief_id: str = Field(..., min_length=1, max_length=255)
    character_anchors: list[str] = Field(default_factory=list)
    world_constraints: list[str] = Field(default_factory=list)
    prior_summaries: list[str] = Field(default_factory=list)


class PromptBudgetSummary(StrictModel):
    estimated_prompt_chars: int = Field(default=0, ge=0)
    target_max_chars: int = Field(default=0, ge=0)
    truncated_fields: list[str] = Field(default_factory=list)
    fit_to_budget: bool = True


class CanonGenerationPacket(StrictModel):
    packet_id: str = Field(..., min_length=1, max_length=255)
    source_project_id: str = Field(..., min_length=1, max_length=255)
    target_project_id: str = Field(..., min_length=1, max_length=255)
    mode: GenerationMode
    generation_brief: str = Field(..., min_length=1, max_length=10000)
    foundation_snapshot: dict[str, object] = Field(default_factory=dict)
    characters: list[CanonicalCharacterSnapshot] = Field(default_factory=list)
    relationships: list[CanonicalRelationshipSnapshot] = Field(default_factory=list)
    world_bible: list[CanonicalWorldSnapshot] = Field(default_factory=list)
    arcs: list[CanonicalArcSnapshot] = Field(default_factory=list)
    continuity_threads: list[CanonicalContinuityThreadSnapshot] = Field(default_factory=list)
    continuity_findings: list[CanonicalContinuityFindingSnapshot] = Field(default_factory=list)
    drafting_context_packets: list[CanonicalDraftingContextSnapshot] = Field(default_factory=list)
    mythos_entries: list[dict[str, object]] = Field(default_factory=list)
    pattern_entries: list[dict[str, object]] = Field(default_factory=list)
    canon_annotations: list[dict[str, object]] = Field(default_factory=list)
    customization_profile_id: str | None = None
    canon_policy: CanonPolicy = Field(default_factory=CanonPolicy)
    prompt_budget_summary: PromptBudgetSummary = Field(default_factory=PromptBudgetSummary)
    source_hashes: dict[str, str] = Field(default_factory=dict)


class GenerationArtifactRef(StrictModel):
    artifact_kind: str = Field(..., min_length=1, max_length=100)
    artifact_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)


class GenerationPlan(StrictModel):
    plan_id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    packet_id: str = Field(..., min_length=1, max_length=255)
    mode: GenerationMode
    premise: str = Field(default="", max_length=10000)
    logline: str = Field(default="", max_length=1000)
    story_arcs: list[dict[str, object]] = Field(default_factory=list)
    chapter_plans: list[dict[str, object]] = Field(default_factory=list)
    canon_obligations: list[str] = Field(default_factory=list)
    intentional_differences: list[str] = Field(default_factory=list)
    forbidden_contradictions: list[str] = Field(default_factory=list)
    status: GenerationPlanStatus = GenerationPlanStatus.DRAFT
    gate_reasons: list[str] = Field(default_factory=list)


class CanonGenerationRequest(StrictModel):
    request_id: str | None = Field(default=None, max_length=255)
    source_project_id: str = Field(..., min_length=1, max_length=255)
    mode: GenerationMode
    destination: GenerationDestination
    canon_scope: CanonScope
    generation_brief: str = Field(..., min_length=1, max_length=10000)
    premise_override: str | None = Field(default=None, max_length=10000)
    tone_override: str | None = Field(default=None, max_length=255)
    pov_override: str | None = Field(default=None, max_length=100)
    target_chapter_count: int = Field(default=12, ge=1, le=100)
    target_words_per_chapter: int | None = Field(default=None, ge=250, le=10000)
    canon_policy: CanonPolicy = Field(default_factory=CanonPolicy)
    review_policy: GenerationReviewPolicy = Field(default_factory=GenerationReviewPolicy)
    model_id: str | None = Field(default=None, max_length=255)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=256, le=64000)
    idempotency_key: str | None = Field(default=None, max_length=255)


class GenerationRunResponse(StrictModel):
    generation_id: str = Field(..., min_length=1, max_length=255)
    source_project_id: str = Field(..., min_length=1, max_length=255)
    target_project_id: str = Field(..., min_length=1, max_length=255)
    job_ids: list[str] = Field(default_factory=list)
    status: GenerationRunStatus = GenerationRunStatus.QUEUED
    warnings: list[str] = Field(default_factory=list)
    created_artifacts: list[GenerationArtifactRef] = Field(default_factory=list)


class CanonForkPreviewResponse(StrictModel):
    source_project_id: str
    mode: GenerationMode
    destination_kind: DestinationKind
    selected_character_ids: list[str] = Field(default_factory=list)
    selected_world_bible_refs: list[WorldBibleRef] = Field(default_factory=list)
    selected_continuity_thread_ids: list[str] = Field(default_factory=list)
    selected_arc_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerationGateResult(StrictModel):
    gate_result_id: str
    generation_id: str
    project_id: str
    artifact_kind: str
    artifact_id: str
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str] = Field(default_factory=list)
    repair_attempted: bool = False
    repair_job_id: str | None = None
    created_at: str


class GenerationGateResultListResponse(StrictModel):
    generation_id: str
    items: list[GenerationGateResult] = Field(default_factory=list)
