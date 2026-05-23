from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.schemas import (
    ArcCandidate,
    ArcSelection,
    ArcStageMap,
    RelationshipEdge,
    StoryBranchState,
    StoryObjectType,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StoryArtifactLifecycleState,
    StorySuggestionLifecycleState,
)

@dataclass(frozen=True)
class StoryFlowDefinitionRecord:
    project_id: str
    flow_name: str
    flow_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryFlowStageRecord:
    stage_id: int
    project_id: str
    stage_key: str
    stage_kind: str
    is_custom: bool
    display_name: str
    description: str | None
    position: int
    depends_on: list[str]
    stage_configuration_state: StoryFlowStageConfigurationState
    stage_progress_state: StoryFlowStageProgressState
    writer_notes: str | None
    custom_prompt_guidance: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BrainDumpSessionRecord:
    session_id: int
    project_id: str
    title: str | None
    raw_text: str
    state: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BrainstormItemRecord:
    item_id: int
    project_id: str
    cluster_key: str | None
    content: str
    item_state: str
    tags: list[str]
    source_artifact_refs: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationRevisionRecord:
    revision_id: int
    project_id: str
    revision_number: int
    premise: str
    logline: str
    thematic_spine: str | None
    emotional_promise: str | None
    tone_direction: str | None
    target_audience: str | None
    narrative_constraints: list[str]
    complexity_level: str | None
    success_definition: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationProfileRecord:
    project_id: str
    current_revision_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CharacterProfileRecord:
    character_id: str
    project_id: str
    display_name: str
    role_in_story: str | None
    archetype: str | None
    external_goal: str | None
    internal_need: str | None
    misbelief_or_wound: str | None
    core_fear: str | None
    primary_strength: str | None
    fatal_flaw_or_limitation: str | None
    contradictions: list[str]
    backstory_summary: str | None
    voice_notes: str | None
    relationship_map: list[str]
    secrets: list[str]
    values: list[str]
    taboos: list[str]
    change_axis: str | None
    arc_stage_notes: str | None
    continuity_facts: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WorldBibleEntryRecord:
    entry_id: int
    project_id: str
    entry_type: str
    title: str
    summary: str | None
    canonical_facts: list[str]
    related_character_ids: list[str]
    visibility_scope: str
    source_artifacts: list[str]
    continuity_warnings: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RelationshipEdgeRecord:
    edge_id: str
    project_id: str
    source_character_id: str
    target_character_id: str
    relation_kind: str
    summary: str
    tension: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcCandidateRecord:
    arc_id: str
    project_id: str
    name: str
    summary: str
    stage_map_notes: list[str]
    fit_notes: list[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcComparisonCandidateRecord:
    candidate: ArcCandidateRecord
    rank: int
    score: tuple[int, int, int, int]
    notes: list[str]


@dataclass(frozen=True)
class ArcComparisonRecord:
    comparison_id: str
    project_id: str
    candidate_ids: list[str]
    candidate_set: list[ArcCandidateRecord]
    ranked_candidates: list[ArcComparisonCandidateRecord]
    review_notes: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcStageMapRecord:
    arc_stage_map_id: str
    project_id: str
    arc_id: str
    stage_kinds: list[str]
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ArcSelectionRecord:
    selection_id: str
    project_id: str
    selected_arc_id: str
    selected_arc: ArcCandidateRecord
    rejected_arc_ids: list[str]
    comparison_notes: list[str]
    comparison_record_ids: list[str]
    stage_map_id: str | None
    stage_map: ArcStageMapRecord | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryDecisionNodeLinkRecord:
    object_type: str
    object_id: str
    relation_kind: str


@dataclass(frozen=True)
class StoryDecisionNodeRecord:
    node_record_id: int
    node_id: str
    project_id: str
    node_type: str
    change_type: str
    subject_type: str
    subject_id: str
    parent_node_id: str | None
    branch_id: str | None
    summary: str
    prior_state_ref: str | None
    prior_state_summary: str | None
    new_state_ref: str | None
    new_state_summary: str | None
    reason_or_note: str | None
    decision_made_at: datetime
    made_by: str
    related_object_links: list[StoryDecisionNodeLinkRecord]
    informing_object_links: list[StoryDecisionNodeLinkRecord]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BranchPointRecord:
    branch_point_id: str
    project_id: str
    source_node_id: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryBranchRecord:
    branch_id: str
    project_id: str
    branch_point_id: str
    branch_name: str
    branch_state: StoryBranchState
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BranchStateRefRecord:
    branch_state_ref_id: str
    project_id: str
    branch_id: str
    state_object_type: StoryObjectType
    state_object_id: str
    decision_node_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BranchComparisonRecord:
    comparison_id: str
    project_id: str
    source_branch_id: str
    target_branch_id: str
    review_notes: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BranchMergeDecisionRecord:
    merge_decision_id: str
    project_id: str
    source_branch_id: str
    target_branch_id: str
    merge_rationale: str
    resulting_decision_node_ids: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CheckerFindingRecord:
    finding_id: str
    project_id: str
    source_object_id: str
    source_object_kind: str
    severity: str
    summary: str
    details: str | None
    source_context: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ReviewDecisionRecord:
    decision_id: str
    project_id: str
    target_id: str
    target_kind: str
    decision: str
    notes: str | None
    source_context: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class InspectRunLinkRecord:
    link_id: str
    project_id: str
    object_kind: str
    object_id: str
    logical_run_id: str
    run_id: str
    run_kind: str
    attempt_number: int | None
    label: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BeatPlanRecord:
    beat_id: str
    project_id: str
    objective: str
    conflict: str
    stakes: str
    dependency_ids: list[str]
    arc_stage: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SequencePlanRecord:
    sequence_id: str
    project_id: str
    title: str
    summary: str
    beat_ids: list[str]
    chapter_ids: list[str]
    status: str
    position: int
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ChapterPlanRecord:
    chapter_id: str
    project_id: str
    sequence_id: str | None
    title: str
    summary: str
    objective: str
    conflict: str
    stakes: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime
    target_word_count: int | None = None


@dataclass(frozen=True)
class ScenePlanRecord:
    scene_id: str
    project_id: str
    chapter_id: str | None
    title: str
    summary: str
    objective: str
    conflict: str
    stakes: str
    active_character_ids: list[str]
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    status: str
    position: int
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ChapterPacketRecord:
    packet_id: str
    project_id: str
    chapter_id: str
    included_reference_ids: list[str]
    constraints: list[str]
    scene_goals: list[str]
    status: str
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PlanningDependencyRecord:
    dependency_id: str
    project_id: str
    upstream_id: str
    downstream_id: str
    dependency_kind: str
    reason: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ContinuityThreadRecord:
    thread_id: str
    project_id: str
    title: str
    summary: str
    status: str
    chapter_ids: list[str]
    character_ids: list[str]
    evidence: list[str]
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ContinuityStateRecord:
    state_id: str
    project_id: str
    chapter_id: str
    summary: str
    active_threads: list[str]
    resolved_threads: list[str]
    character_states: dict[str, str]
    world_facts: list[str]
    unresolved_questions: list[str]
    contradictions: list[str]
    status: str
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ContinuityFindingRecord:
    finding_id: int
    project_id: str
    finding_key: str | None
    overall_confidence: float
    status: str
    contradictions: list[str]
    unresolved_questions: list[str]
    provenance_note: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DraftBriefRecord:
    brief_id: str
    project_id: str
    chapter_id: str
    objective: str
    emotional_turn: str
    continuity_obligations: list[str]
    required_callbacks: list[str]
    forbidden_contradictions: list[str]
    voice_guidance: str
    status: str
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DraftingContextPacketRecord:
    packet_id: str
    project_id: str
    brief_id: str
    character_anchors: list[str]
    world_constraints: list[str]
    prior_summaries: list[str]
    pattern_guidance: dict[str, Any]
    status: str
    provenance_note: str | None
    confidence_score: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CanonGenerationRunRecord:
    generation_id: str
    source_project_id: str
    target_project_id: str
    mode: str
    request_json: dict[str, Any]
    canon_scope_json: dict[str, Any]
    canon_policy_json: dict[str, Any]
    status: str
    gate_status: str
    warnings: list[str]
    created_job_ids: list[str]
    created_artifacts: list[dict[str, Any]]
    idempotency_key: str | None
    request_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CanonGenerationPacketRecord:
    packet_id: str
    generation_id: str
    source_project_id: str
    target_project_id: str
    packet_json: dict[str, Any]
    source_hashes_json: dict[str, str]
    prompt_budget_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class GenerationGateResultRecord:
    gate_result_id: str
    generation_id: str
    project_id: str
    artifact_kind: str
    artifact_id: str
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str]
    repair_attempted: bool
    repair_job_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class ManuscriptAssistRunRecord:
    assist_id: str
    project_id: str
    document_id: str
    assist_kind: str
    request_json: dict[str, Any]
    status: str
    summary: str
    created_draft_artifact_id: str | None
    created_branch_id: str | None
    created_manuscript_document_id: str | None
    job_ids: list[str]
    warnings: list[str]
    idempotency_key: str | None
    request_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ManuscriptAssistSuggestionRecord:
    suggestion_id: str
    assist_id: str
    project_id: str
    target_document_id: str
    suggestion_kind: str
    source_text: str
    proposed_text: str
    rationale: str
    range_json: dict[str, Any] | None
    canon_risk: str
    confidence_score: float
    source_context: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ManuscriptAssistGateResultRecord:
    gate_result_id: str
    assist_id: str
    project_id: str
    document_id: str
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str]
    created_at: datetime


@dataclass(frozen=True)
class CanonAnnotationRecord:
    annotation_id: str
    project_id: str
    target_kind: str
    target_id: str
    field_path: str
    annotation_kind: str
    note: str
    applies_to_modes: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CanonCustomizationProfileRecord:
    profile_id: str
    project_id: str
    name: str
    description: str
    default_generation_mode: str
    canon_scope_json: dict[str, Any]
    canon_policy_json: dict[str, Any]
    generation_brief_template: str
    selected_annotation_ids: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MythosEntryRecord:
    mythos_id: str
    project_id: str
    entry_type: str
    name: str
    summary: str
    canonical_facts: list[str]
    pattern_notes: list[str]
    source_corpus: str | None
    generation_guidance: str
    visibility_scope: str
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PatternEntryRecord:
    pattern_id: str
    project_id: str
    pattern_type: str
    name: str
    summary: str
    source_type: str
    generation_modes: list[str]
    beats: list[str]
    constraints: list[str]
    transposition_notes: str
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DraftArtifactRecord:
    artifact_id: str
    project_id: str
    title: str
    content: str
    source_plan_ids: list[str]
    source_context: list[str]
    provenance_note: str | None
    status: StoryArtifactLifecycleState
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ManuscriptDocumentRecord:
    document_id: str
    project_id: str
    title: str
    display_title: str | None
    content: str
    chapter_id: str | None
    scene_id: str | None
    current_draft_artifact_id: str | None
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RevisionSuggestionRecord:
    suggestion_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    source_context: list[str]
    status: StorySuggestionLifecycleState
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryboardCardRecord:
    """Record for storyboard cards used in planning workspace.
    
    Storyboard cards represent individual planning elements (scenes, beats, ideas)
    that can be arranged, reordered, and organized on a visual board.
    """
    card_id: str
    project_id: str
    title: str
    content: str
    card_type: str  # 'scene', 'beat', 'idea', 'note', etc.
    column_id: str | None  # Column on the board (e.g., 'planned', 'drafting', 'done')
    position: int  # Position within column for ordering
    tags: list[str]
    character_ids: list[str]  # Associated characters
    dependencies: list[str]  # Card IDs this card depends on
    metadata: dict[str, Any]  # Flexible metadata field
    created_at: datetime
    updated_at: datetime


