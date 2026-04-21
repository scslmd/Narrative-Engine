from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import (
    ArcCandidate,
    ArcSelection,
    ArcStageMap,
    BranchComparisonRecord,
    BranchMergeDecision,
    BranchStateRef,
    BrainstormItem,
    BrainstormPromotion,
    ChapterPacket,
    ChapterPlan,
    CheckerFinding,
    DraftArtifact,
    FoundationProfile,
    FoundationRevision,
    InspectRunLink,
    ManuscriptDocument,
    ManuscriptDocumentUpdateRequest,
    ManuscriptReviewResponse,
    PlanningDependency,
    ReviewDecision,
    RevisionSuggestion,
    ScenePlan,
    SequencePlan,
    StoryBranch,
    StoryBranchState,
    StoryDecisionNode,
    StoryFlowDefinition,
    StoryFlowStage,
    StorySuggestionLifecycleState,
    StoryboardCard,
    CharacterProfile,
    RelationshipEdge,
    WorldBibleEntry,
)
from app.schemas.base import StrictModel
from app.services.braindump import BrainDumpNotFoundError, BrainDumpService, BrainDumpValidationError
from app.services.brainstorm import BrainstormNotFoundError, BrainstormService, BrainstormValidationError
from app.services.drafting import DraftingNotFoundError, DraftingService
from app.services.manuscript_review import ManuscriptReviewError, ManuscriptReviewService
from app.services.editable_flow import (
    EditableFlowNotFoundError,
    EditableFlowService,
    EditableFlowValidationError,
)
from app.services.editable_flow_persistence import SQLiteEditableFlowRepository
from app.services.foundation import (
    FoundationNotFoundError,
    FoundationService,
    FoundationValidationError,
)
from app.services.planning import PlanningNotFoundError, PlanningService, PlanningValidationError
from app.services.review_routing import ReviewRoutingNotFoundError, ReviewRoutingService, ReviewRoutingValidationError
from app.services.story_branching import (
    StoryBranchingNotFoundError,
    StoryBranchingService,
    StoryBranchingValidationError,
)
from app.services.story_decision_review import (
    StoryDecisionReviewNotFoundError,
    StoryDecisionReviewService,
    StoryDecisionReviewValidationError,
)
from app.services.story_knowledge import (
    StoryKnowledgeNotFoundError,
    StoryKnowledgeService,
    StoryKnowledgeValidationError,
)
from app.services.chapter_packets import (
    ChapterPacketNotFoundError,
    ChapterPacketService,
    ChapterPacketValidationError,
)
from app.services.sequence_plans import (
    SequencePlanNotFoundError,
    SequencePlanService,
    SequencePlanValidationError,
)
from app.services.storyboard_cards import (
    StoryboardCardNotFoundError,
    StoryboardCardService,
    StoryboardCardValidationError,
)


class StoryDecisionNodeListResponse(StrictModel):
    project_id: str
    items: list[StoryDecisionNode] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class StoryDecisionPathResponse(StrictModel):
    project_id: str
    node: StoryDecisionNode
    parent_path: list[StoryDecisionNode] = Field(default_factory=list)


class CheckerFindingListResponse(StrictModel):
    project_id: str
    items: list[CheckerFinding] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ReviewDecisionListResponse(StrictModel):
    project_id: str
    items: list[ReviewDecision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class InspectRunLinkListResponse(StrictModel):
    project_id: str
    items: list[InspectRunLink] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class SequencePlanListResponse(StrictModel):
    project_id: str
    items: list[SequencePlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ChapterPlanListResponse(StrictModel):
    project_id: str
    items: list[ChapterPlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ScenePlanListResponse(StrictModel):
    project_id: str
    items: list[ScenePlan] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class PlanningDependencyListResponse(StrictModel):
    project_id: str
    items: list[PlanningDependency] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ChapterPacketListResponse(StrictModel):
    project_id: str
    items: list[ChapterPacket] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class DraftArtifactListResponse(StrictModel):
    project_id: str
    items: list[DraftArtifact] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ManuscriptDocumentListResponse(StrictModel):
    project_id: str
    items: list[ManuscriptDocument] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class RevisionSuggestionListResponse(StrictModel):
    project_id: str
    items: list[RevisionSuggestion] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ManuscriptDocumentCreateRequest(StrictModel):
    document_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    chapter_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    scene_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    current_draft_artifact_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    version: int | None = Field(None, ge=1)


class PromoteDraftToManuscriptRequest(StrictModel):
    project_id: str
    document_id: str
    draft_artifact_id: str
    title: str | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    version: int | None = None


class ReviewDecisionCreateRequest(StrictModel):
    decision_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    target_kind: str = Field(..., min_length=1, max_length=100)
    target_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    decision: str = Field(..., min_length=1, max_length=50)
    notes: str | None = Field(None, max_length=5000)
    source_context: list[str] = Field(default_factory=list)


class RevisionSuggestionCreateRequest(StrictModel):
    suggestion_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    source_context: list[str] = Field(default_factory=list)
    status: str = StorySuggestionLifecycleState.REQUESTED.value


class StoryBranchListResponse(StrictModel):
    project_id: str
    items: list[StoryBranch] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BranchStateRefListResponse(StrictModel):
    project_id: str
    items: list[BranchStateRef] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BranchComparisonListResponse(StrictModel):
    project_id: str
    items: list[BranchComparisonRecord] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class StoryBranchCreateRequest(StrictModel):
    project_id: str
    branch_id: str
    branch_point_id: str
    branch_name: str
    branch_state: StoryBranchState = StoryBranchState.ACTIVE


class StoryBranchActiveRequest(StrictModel):
    project_id: str
    branch_id: str


class BranchComparisonCreateRequest(StrictModel):
    project_id: str
    comparison_id: str
    source_branch_id: str
    target_branch_id: str
    review_notes: list[str] = Field(default_factory=list)


class BranchMergeDecisionCreateRequest(StrictModel):
    project_id: str
    merge_decision_id: str
    source_branch_id: str
    target_branch_id: str
    merge_rationale: str
    resulting_decision_node_ids: list[str] = Field(default_factory=list)


class BranchMergeDecisionListResponse(StrictModel):
    project_id: str
    items: list[BranchMergeDecision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FlowStageListResponse(StrictModel):
    project_id: str
    items: list[StoryFlowStage] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FlowStageCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    stage_kind: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] = Field(default_factory=list)
    insert_after_stage_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')


class FlowStageUpdateRequest(StrictModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    depends_on: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)
    custom_prompt_guidance: str | None = Field(None, max_length=10000)
    stage_configuration_state: str | None = Field(None, max_length=20)


class FlowStageReorderRequest(StrictModel):
    stage_order: list[str] = Field(..., min_length=1)


class FlowInitRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_name: str = Field(..., min_length=1, max_length=255)


# Brainstorm schemas
class BrainstormItemCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    content: str = Field(..., min_length=1, max_length=10000)
    status: str = Field(default="keep", max_length=20)
    cluster_key: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    source_artifact_refs: list[str] = Field(default_factory=list)


class BrainstormItemClusterRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    item_ids: list[str] = Field(..., min_length=1)
    cluster_key: str | None = Field(None, max_length=100)


class BrainstormItemPromoteRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    item_id: str = Field(..., min_length=1)
    target_object_kind: str = Field(..., min_length=1, max_length=100)
    target_object_id: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=2000)


class BrainstormItemListResponse(StrictModel):
    project_id: str
    items: list[BrainstormItem] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# Brain dump schemas
class BrainDumpSessionCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str | None = Field(None, max_length=500)
    raw_text: str = Field("", max_length=100000)


class BrainDumpSessionPatchRequest(StrictModel):
    raw_text: str | None = Field(None, max_length=100000)
    title: str | None = Field(None, max_length=500)
    state: str | None = Field(None, max_length=20)


class BrainDumpSessionResponse(StrictModel):
    session_id: int
    project_id: str
    title: str | None = None
    raw_text: str = ""
    state: str = "active"
    created_at: str | None = None
    updated_at: str | None = None


class BrainDumpSessionListResponse(StrictModel):
    project_id: str
    sessions: list[BrainDumpSessionResponse] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class BrainDumpOrganizeResponse(StrictModel):
    session_id: int
    categorized_items: dict[str, list[BrainstormItem]] = Field(default_factory=dict)
    total_items: int = 0


class BrainstormPromotionListResponse(StrictModel):
    project_id: str
    items: list[BrainstormPromotion] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# Foundation schemas
class FoundationCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    premise: str = Field(..., min_length=1, max_length=10000)
    logline: str = Field(..., min_length=1, max_length=500)
    thematic_spine: str = Field(..., min_length=1, max_length=2000)
    emotional_promise: str = Field(..., min_length=1, max_length=2000)
    tone_and_voice_direction: str = Field(..., min_length=1, max_length=2000)
    target_audience: str = Field(..., min_length=1, max_length=500)
    narrative_constraints: list[str] = Field(default_factory=list)
    complexity_level: str = Field(..., min_length=1, max_length=50)
    success_definition: str = Field(..., min_length=1, max_length=2000)


class FoundationUpdateRequest(StrictModel):
    premise: str | None = Field(None, min_length=1, max_length=10000)
    logline: str | None = Field(None, min_length=1, max_length=500)
    thematic_spine: str | None = Field(None, min_length=1, max_length=2000)
    emotional_promise: str | None = Field(None, min_length=1, max_length=2000)
    tone_and_voice_direction: str | None = Field(None, min_length=1, max_length=2000)
    target_audience: str | None = Field(None, min_length=1, max_length=500)
    narrative_constraints: list[str] | None = None
    complexity_level: str | None = Field(None, min_length=1, max_length=50)
    success_definition: str | None = Field(None, min_length=1, max_length=2000)


class FoundationRevisionListResponse(StrictModel):
    project_id: str
    items: list[FoundationRevision] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FoundationReviewCue(StrictModel):
    impacted_area: str
    reason: str
    triggering_revision_id: str
    triggering_fields: list[str] = Field(default_factory=list)


class FoundationReviewCueListResponse(StrictModel):
    project_id: str
    items: list[FoundationReviewCue] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class FoundationReadResponse(StrictModel):
    project_id: str
    foundation_id: str
    active_profile: FoundationProfile | None = None
    current_revision_id: str | None = None
    revision_history: list[FoundationRevision] = Field(default_factory=list)
    downstream_review_cues: list[FoundationReviewCue] = Field(default_factory=list)


class FoundationWriteResponse(FoundationReadResponse):
    created_revision: FoundationRevision


# ============================================================================
# Storyboard Card schemas
# ============================================================================

class StoryboardCardListResponse(StrictModel):
    project_id: str
    items: list[StoryboardCard] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class StoryboardCardCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    card_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=50000)
    card_type: str = Field(default="idea", min_length=1, max_length=20)
    column_id: str | None = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    position: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    character_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StoryboardCardUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1, max_length=50000)
    card_type: str | None = Field(None, min_length=1, max_length=20)
    column_id: str | None = Field(None, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    position: int | None = Field(None, ge=0)
    tags: list[str] | None = None
    character_ids: list[str] | None = None
    dependencies: list[str] | None = None
    metadata: dict[str, Any] | None = None


class StoryboardCardReindexRequest(StrictModel):
    card_ids: list[str] = Field(..., min_length=1)


# ============================================================================
# Chapter Packet schemas (write/update)
# ============================================================================

class ChapterPacketCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    packet_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    chapter_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    included_reference_ids: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    scene_goals: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=30)


class ChapterPacketUpdateRequest(StrictModel):
    included_reference_ids: list[str] | None = None
    constraints: list[str] | None = None
    scene_goals: list[str] | None = None
    status: str | None = Field(None, max_length=30)


# ============================================================================
# Sequence Plan schemas (write/update)
# ============================================================================

class SequencePlanCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    sequence_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    beat_ids: list[str] = Field(default_factory=list)
    chapter_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=30)
    position: int | None = Field(None, ge=0)


class SequencePlanUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    beat_ids: list[str] | None = None
    chapter_ids: list[str] | None = None
    status: str | None = Field(None, max_length=30)
    position: int | None = Field(None, ge=0)


# ============================================================================
# Chapter Plan schemas (write/update)
# ============================================================================

class ChapterPlanCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    chapter_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    objective: str = Field(..., min_length=1, max_length=5000)
    conflict: str = Field(..., min_length=1, max_length=5000)
    stakes: str = Field(..., min_length=1, max_length=5000)
    sequence_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=30)
    position: int | None = Field(None, ge=0)


class ChapterPlanUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    objective: str | None = Field(None, max_length=5000)
    conflict: str | None = Field(None, max_length=5000)
    stakes: str | None = Field(None, max_length=5000)
    active_character_ids: list[str] | None = None
    continuity_requirements: list[str] | None = None
    unresolved_questions: list[str] | None = None
    status: str | None = Field(None, max_length=30)
    position: int | None = Field(None, ge=0)


# ============================================================================
# Scene Plan schemas (write/update)
# ============================================================================

class ScenePlanCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    scene_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    objective: str = Field(..., min_length=1, max_length=5000)
    conflict: str = Field(..., min_length=1, max_length=5000)
    stakes: str = Field(..., min_length=1, max_length=5000)
    chapter_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=30)
    position: int | None = Field(None, ge=0)


class ScenePlanUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    summary: str | None = Field(None, max_length=10000)
    objective: str | None = Field(None, max_length=5000)
    conflict: str | None = Field(None, max_length=5000)
    stakes: str | None = Field(None, max_length=5000)
    active_character_ids: list[str] | None = None
    continuity_requirements: list[str] | None = None
    unresolved_questions: list[str] | None = None
    status: str | None = Field(None, max_length=30)
    position: int | None = Field(None, ge=0)


# ============================================================================
# Planning Dependency schemas
# ============================================================================

class PlanningDependencyCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    dependency_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    upstream_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    downstream_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    dependency_kind: str = Field(..., min_length=1, max_length=100)
    reason: str | None = Field(None, max_length=5000)


# ============================================================================
# Beat Plan schemas
# ============================================================================

class BeatPlanCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    beat_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    objective: str = Field(..., min_length=1, max_length=5000)
    conflict: str = Field(..., min_length=1, max_length=5000)
    stakes: str = Field(..., min_length=1, max_length=5000)
    arc_stage: str | None = Field(None, max_length=100)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=30)
    position: int | None = Field(None, ge=0)


class BeatPlanUpdateRequest(StrictModel):
    objective: str | None = Field(None, max_length=5000)
    conflict: str | None = Field(None, max_length=5000)
    stakes: str | None = Field(None, max_length=5000)
    arc_stage: str | None = Field(None, max_length=100)
    active_character_ids: list[str] | None = None
    continuity_requirements: list[str] | None = None
    unresolved_questions: list[str] | None = None
    status: str | None = Field(None, max_length=30)
    position: int | None = Field(None, ge=0)


# ============================================================================
# Planning Reorder schema
# ============================================================================

class PlanningReorderRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    plan_kind: str = Field(..., min_length=1, max_length=20)
    ordered_plan_ids: list[str] = Field(..., min_length=1)


# Character schemas
class CharacterProfileCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    character_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    display_name: str = Field(..., min_length=1, max_length=255)
    role_in_story: str = Field(..., min_length=1, max_length=255)
    archetype: str = Field(..., min_length=1, max_length=100)
    external_goal: str = Field(..., min_length=1, max_length=2000)
    internal_need: str = Field(..., min_length=1, max_length=2000)
    misbelief_or_wound: str = Field(..., min_length=1, max_length=2000)
    core_fear: str = Field(..., min_length=1, max_length=1000)
    primary_strength: str = Field(..., min_length=1, max_length=1000)
    fatal_flaw_or_limitation: str = Field(..., min_length=1, max_length=1000)
    contradictions: list[str] = Field(default_factory=list)
    backstory_summary: str = Field(..., min_length=1, max_length=5000)
    voice_notes: str = Field(..., min_length=1, max_length=2000)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    change_axis: str = Field(..., min_length=1, max_length=1000)
    arc_stage_notes: list[str] = Field(default_factory=list)
    continuity_facts: list[str] = Field(default_factory=list)
    writer_notes: str | None = Field(None, max_length=5000)


class CharacterProfileUpdateRequest(StrictModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    role_in_story: str | None = Field(None, min_length=1, max_length=255)
    archetype: str | None = Field(None, min_length=1, max_length=100)
    external_goal: str | None = Field(None, min_length=1, max_length=2000)
    internal_need: str | None = Field(None, min_length=1, max_length=2000)
    misbelief_or_wound: str | None = Field(None, min_length=1, max_length=2000)
    core_fear: str | None = Field(None, min_length=1, max_length=1000)
    primary_strength: str | None = Field(None, min_length=1, max_length=1000)
    fatal_flaw_or_limitation: str | None = Field(None, min_length=1, max_length=1000)
    contradictions: list[str] | None = None
    backstory_summary: str | None = Field(None, min_length=1, max_length=5000)
    voice_notes: str | None = Field(None, min_length=1, max_length=2000)
    secrets: list[str] | None = None
    values: list[str] | None = None
    taboos: list[str] | None = None
    change_axis: str | None = Field(None, min_length=1, max_length=1000)
    arc_stage_notes: list[str] | None = None
    continuity_facts: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)
    # Note: relationship_edges is excluded from updates - it's auto-populated from relationship edges


class CharacterProfileListResponse(StrictModel):
    project_id: str
    items: list[CharacterProfile] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class RelationshipEdgeCreateRequest(StrictModel):
    edge_id: str | None = Field(None, min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    source_character_id: str = Field(..., min_length=1, max_length=255)
    target_character_id: str = Field(..., min_length=1, max_length=255)
    relation_kind: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1, max_length=2000)
    tension: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class RelationshipEdgeUpdateRequest(StrictModel):
    source_character_id: str | None = None
    target_character_id: str | None = None
    relation_kind: str | None = None
    summary: str | None = Field(None, min_length=1, max_length=2000)
    tension: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class RelationshipEdgeListResponse(StrictModel):
    project_id: str
    items: list[RelationshipEdge] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# World Bible schemas
class WorldBibleEntryCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    entry_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1, max_length=50000)
    canonical_facts: list[str] = Field(default_factory=list)
    related_character_ids: list[str] = Field(default_factory=list)
    source_artifacts: list[str] = Field(default_factory=list)
    visibility_scope: str = Field(default="project", min_length=1, max_length=50)
    continuity_warnings: list[str] = Field(default_factory=list)
    writer_notes: str | None = Field(None, max_length=5000)


class WorldBibleEntryUpdateRequest(StrictModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    summary: str | None = Field(None, min_length=1, max_length=50000)
    canonical_facts: list[str] | None = None
    related_character_ids: list[str] | None = None
    source_artifacts: list[str] | None = None
    visibility_scope: str | None = Field(None, min_length=1, max_length=50)
    continuity_warnings: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)


class WorldBibleEntryListResponse(StrictModel):
    project_id: str
    items: list[WorldBibleEntry] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


# Arc schemas
class ArcCandidateListResponse(StrictModel):
    project_id: str
    items: list[ArcCandidate] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcSelectionListResponse(StrictModel):
    project_id: str
    items: list[ArcSelection] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcStageMapListResponse(StrictModel):
    project_id: str
    items: list[ArcStageMap] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class ArcCandidateCreateRequest(StrictModel):
    arc_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=1, max_length=500)
    summary: str = Field(..., min_length=1, max_length=5000)
    stage_map_notes: list[str] = Field(default_factory=list)
    fit_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ArcSelectionCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    selected_arc: ArcCandidateCreateRequest | str = Field(...)
    rejected_arc_ids: list[str] = Field(default_factory=list)
    comparison_notes: list[str] = Field(default_factory=list)
    stage_map: ArcStageMapCreateRequest | None = None


class ArcSelectionUpdateRequest(StrictModel):
    comparison_notes: list[str] | None = None
    stage_map: ArcStageMapCreateRequest | None = None


class ArcStageMapCreateRequest(StrictModel):
    arc_id: str = Field(..., min_length=1, max_length=255)
    stage_kinds: list[str] = Field(..., min_length=1)
    notes: str | None = None


class ArcComparisonRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    candidates: list[str | ArcCandidateCreateRequest] = Field(..., min_length=2)


def build_story_development_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/story-development",
) -> APIRouter:
    router = APIRouter(prefix=prefix.rstrip("/") if prefix else "", tags=["story-development"])
    decision_service = StoryDecisionReviewService(repository)
    drafting_service = DraftingService(repository)
    manuscript_review_service = ManuscriptReviewService(repository)
    planning_service = PlanningService(repository)
    branching_service = StoryBranchingService(repository)
    review_service = ReviewRoutingService(repository, drafting_service=drafting_service, planning_service=planning_service)
    flow_service = EditableFlowService(
        SQLiteEditableFlowRepository(str(repository.db_path)),
    )
    brainstorm_service = BrainstormService(repository)
    braindump_service = BrainDumpService(repository)
    foundation_service = FoundationService(repository)
    story_knowledge_service = StoryKnowledgeService(repository)
    chapter_packet_service = ChapterPacketService(repository)
    sequence_plan_service = SequencePlanService(repository)
    storyboard_card_service = StoryboardCardService(repository)

    @router.get("/branches", response_model=StoryBranchListResponse)
    def list_story_branches(project_id: str) -> StoryBranchListResponse:
        try:
            items = list(branching_service.list_story_branches(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryBranchListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.post("/branches", response_model=StoryBranch, status_code=201)
    def create_story_branch(payload: StoryBranchCreateRequest) -> StoryBranch:
        try:
            return branching_service.create_story_branch(
                payload.project_id,
                branch_id=payload.branch_id,
                branch_point_id=payload.branch_point_id,
                branch_name=payload.branch_name,
                branch_state=payload.branch_state,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch point not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/active", response_model=StoryBranch)
    def get_active_story_branch(project_id: str) -> StoryBranch:
        try:
            return branching_service.get_active_story_branch(project_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Active story branch not found.") from exc

    @router.post("/branches/active", response_model=StoryBranch)
    def select_active_story_branch(payload: StoryBranchActiveRequest) -> StoryBranch:
        try:
            return branching_service.select_active_branch(payload.project_id, branch_id=payload.branch_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc

    @router.post("/branches/comparisons", response_model=BranchComparisonRecord, status_code=201)
    def create_branch_comparison(payload: BranchComparisonCreateRequest) -> BranchComparisonRecord:
        try:
            return branching_service.compare_story_branches(
                payload.project_id,
                comparison_id=payload.comparison_id,
                source_branch_id=payload.source_branch_id,
                target_branch_id=payload.target_branch_id,
                review_notes=payload.review_notes,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="One or more story branches were not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/comparisons", response_model=BranchComparisonListResponse)
    def list_branch_comparisons(project_id: str) -> BranchComparisonListResponse:
        try:
            items = list(branching_service.list_branch_comparisons(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchComparisonListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/comparisons/{comparison_id}", response_model=BranchComparisonRecord)
    def get_branch_comparison(comparison_id: str, project_id: str) -> BranchComparisonRecord:
        try:
            return branching_service.get_branch_comparison(project_id, comparison_id=comparison_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch comparison not found.") from exc

    @router.post("/branches/merge-decisions", response_model=BranchMergeDecision, status_code=201)
    def record_branch_merge_decision(payload: BranchMergeDecisionCreateRequest) -> BranchMergeDecision:
        try:
            return branching_service.record_branch_merge_decision(
                payload.project_id,
                merge_decision_id=payload.merge_decision_id,
                source_branch_id=payload.source_branch_id,
                target_branch_id=payload.target_branch_id,
                merge_rationale=payload.merge_rationale,
                resulting_decision_node_ids=payload.resulting_decision_node_ids,
            )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="One or more story branches were not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/branches/merge-decisions", response_model=BranchMergeDecisionListResponse)
    def list_branch_merge_decisions(project_id: str) -> BranchMergeDecisionListResponse:
        try:
            items = list(branching_service.list_branch_merge_decisions(project_id))
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchMergeDecisionListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/merge-decisions/{merge_decision_id}", response_model=BranchMergeDecision)
    def get_branch_merge_decision(merge_decision_id: str, project_id: str) -> BranchMergeDecision:
        try:
            return branching_service.get_branch_merge_decision(project_id, merge_decision_id=merge_decision_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Branch merge decision not found.") from exc

    @router.get("/branches/{branch_id}/state-refs", response_model=BranchStateRefListResponse)
    def list_branch_state_refs(
        branch_id: str,
        project_id: str,
        decision_node_id: str | None = None,
    ) -> BranchStateRefListResponse:
        try:
            if decision_node_id is None:
                items = list(branching_service.list_branch_state_refs(project_id, branch_id=branch_id))
            else:
                items = list(
                    branching_service.list_branch_state_refs_for_decision_node(
                        project_id,
                        branch_id=branch_id,
                        decision_node_id=decision_node_id,
                    )
                )
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc
        except StoryBranchingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return BranchStateRefListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/branches/{branch_id}", response_model=StoryBranch)
    def get_story_branch(branch_id: str, project_id: str) -> StoryBranch:
        try:
            return branching_service.get_story_branch(project_id, branch_id=branch_id)
        except StoryBranchingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story branch not found.") from exc

    # Flow stage endpoints
    @router.post("/flow/stages/init", response_model=FlowStageListResponse, status_code=201)
    def init_flow_stages(payload: FlowInitRequest) -> FlowStageListResponse:
        """Initialize a default flow for a project."""
        try:
            flow = flow_service.create_default_flow(
                project_id=payload.project_id,
                project_name=payload.project_name,
            )
            items = flow_service.list_stages(payload.project_id)
            return FlowStageListResponse(project_id=payload.project_id, items=items, meta={"source": "default"})
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/flow/stages", response_model=FlowStageListResponse)
    def list_flow_stages(project_id: str) -> FlowStageListResponse:
        try:
            items = flow_service.list_stages(project_id)
            return FlowStageListResponse(project_id=project_id, items=items, meta={"ordered_by": "position_asc"})
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc

    @router.post("/flow/stages", response_model=StoryFlowStage, status_code=201)
    def create_flow_stage(payload: FlowStageCreateRequest) -> StoryFlowStage:
        try:
            return flow_service.add_custom_stage(
                project_id=payload.project_id,
                display_name=payload.display_name or f"{payload.stage_kind.replace('_', ' ').title()} Stage",
                description=payload.description,
                stage_kind=payload.stage_kind,
                depends_on=payload.depends_on,
                insert_after_stage_id=payload.insert_after_stage_id,
            )
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def update_flow_stage(stage_id: str, project_id: str, payload: FlowStageUpdateRequest) -> StoryFlowStage:
        try:
            updates: dict[str, Any] = {}
            if payload.display_name is not None:
                updates["display_name"] = payload.display_name
            if payload.description is not None:
                updates["description"] = payload.description
            if payload.depends_on is not None:
                updates["depends_on"] = payload.depends_on
            if payload.writer_notes is not None:
                updates["writer_notes"] = payload.writer_notes
            if payload.custom_prompt_guidance is not None:
                updates["custom_prompt_guidance"] = payload.custom_prompt_guidance
            if payload.stage_configuration_state is not None:
                updates["stage_configuration_state"] = payload.stage_configuration_state

            return flow_service.redefine_stage(project_id=project_id, stage_id=stage_id, **updates)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/flow/stages/reorder", response_model=StoryFlowDefinition)
    def reorder_flow_stages(project_id: str, payload: FlowStageReorderRequest) -> StoryFlowDefinition:
        try:
            return flow_service.reorder_stages(project_id=project_id, stage_order=payload.stage_order)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Flow not found for project.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/flow/stages/{stage_id}", response_model=StoryFlowStage)
    def delete_flow_stage(stage_id: str, project_id: str) -> StoryFlowStage:
        try:
            return flow_service.delete_custom_stage(project_id=project_id, stage_id=stage_id)
        except EditableFlowNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Stage not found.") from exc
        except EditableFlowValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/decisions", response_model=StoryDecisionNodeListResponse)
    def list_story_decisions(
        project_id: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
    ) -> StoryDecisionNodeListResponse:
        try:
            items = list(
                decision_service.list_story_decision_nodes(
                    project_id,
                    subject_type=subject_type,
                    subject_id=subject_id,
                )
            )
        except StoryDecisionReviewValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryDecisionNodeListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "decision_made_at_asc"},
        )

    @router.get("/decisions/{node_id}", response_model=StoryDecisionNode)
    def get_story_decision(node_id: str, project_id: str) -> StoryDecisionNode:
        try:
            return decision_service.get_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc

    @router.get("/decisions/{node_id}/path", response_model=StoryDecisionPathResponse)
    def get_story_decision_path(node_id: str, project_id: str) -> StoryDecisionPathResponse:
        try:
            review = decision_service.inspect_story_decision(project_id, node_id=node_id)
        except StoryDecisionReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Story decision node not found.") from exc
        return StoryDecisionPathResponse(
            project_id=project_id,
            node=review.node,
            parent_path=list(review.parent_path),
        )

    @router.get("/review/findings", response_model=CheckerFindingListResponse)
    def list_checker_findings(
        project_id: str,
        source_object_kind: str | None = None,
        source_object_id: str | None = None,
    ) -> CheckerFindingListResponse:
        try:
            items = list(
                review_service.list_checker_findings(
                    project_id,
                    source_object_kind=source_object_kind,
                    source_object_id=source_object_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return CheckerFindingListResponse(
            project_id=project_id,
            items=items,
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/review/findings/{finding_id}", response_model=CheckerFinding)
    def get_checker_finding(finding_id: str, project_id: str) -> CheckerFinding:
        try:
            return review_service.get_checker_finding(project_id, finding_id=finding_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Checker finding not found.") from exc

    @router.get("/review/decisions", response_model=ReviewDecisionListResponse)
    def list_review_decisions(
        project_id: str,
        target_kind: str | None = None,
        target_id: str | None = None,
    ) -> ReviewDecisionListResponse:
        try:
            items = list(
                review_service.list_review_decisions(
                    project_id,
                    target_kind=target_kind,
                    target_id=target_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ReviewDecisionListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/review/decisions/{decision_id}", response_model=ReviewDecision)
    def get_review_decision(decision_id: str, project_id: str) -> ReviewDecision:
        try:
            return review_service.get_review_decision(project_id, decision_id=decision_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Review decision not found.") from exc

    @router.get("/review/inspect-links", response_model=InspectRunLinkListResponse)
    def list_inspect_links(
        project_id: str,
        object_kind: str | None = None,
        object_id: str | None = None,
        run_id: str | None = None,
        logical_run_id: str | None = None,
    ) -> InspectRunLinkListResponse:
        try:
            items = list(
                review_service.list_inspect_run_links(
                    project_id,
                    object_kind=object_kind,
                    object_id=object_id,
                    run_id=run_id,
                    logical_run_id=logical_run_id,
                )
            )
        except ReviewRoutingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return InspectRunLinkListResponse(project_id=project_id, items=items, meta={"ordered_by": "created_at_asc"})

    @router.get("/review/inspect-links/{link_id}", response_model=InspectRunLink)
    def get_inspect_link(link_id: str, project_id: str) -> InspectRunLink:
        try:
            return review_service.get_inspect_run_link(project_id, link_id=link_id)
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Inspect link not found.") from exc

    @router.get("/planning/sequence-plans", response_model=SequencePlanListResponse)
    def list_sequence_plans(project_id: str) -> SequencePlanListResponse:
        return SequencePlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_sequence_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/sequence-plans/{sequence_id}", response_model=SequencePlan)
    def get_sequence_plan(sequence_id: str, project_id: str) -> SequencePlan:
        try:
            return planning_service.get_sequence_plan(project_id, sequence_id=sequence_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Sequence plan not found.") from exc

    @router.get("/planning/chapter-plans", response_model=ChapterPlanListResponse)
    def list_chapter_plans(project_id: str) -> ChapterPlanListResponse:
        return ChapterPlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_chapter_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/chapter-plans/{chapter_id}", response_model=ChapterPlan)
    def get_chapter_plan(chapter_id: str, project_id: str) -> ChapterPlan:
        try:
            return planning_service.get_chapter_plan(project_id, chapter_id=chapter_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Chapter plan not found.") from exc

    @router.get("/planning/scene-plans", response_model=ScenePlanListResponse)
    def list_scene_plans(project_id: str) -> ScenePlanListResponse:
        return ScenePlanListResponse(
            project_id=project_id,
            items=list(planning_service.list_scene_plans(project_id)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/scene-plans/{scene_id}", response_model=ScenePlan)
    def get_scene_plan(scene_id: str, project_id: str) -> ScenePlan:
        try:
            return planning_service.get_scene_plan(project_id, scene_id=scene_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Scene plan not found.") from exc

    @router.get("/planning/dependencies", response_model=PlanningDependencyListResponse)
    def list_planning_dependencies(project_id: str) -> PlanningDependencyListResponse:
        return PlanningDependencyListResponse(
            project_id=project_id,
            items=list(planning_service.list_planning_dependencies(project_id)),
            meta={"ordered_by": "dependency_id_asc"},
        )

    @router.get("/planning/dependencies/{dependency_id}", response_model=PlanningDependency)
    def get_planning_dependency(dependency_id: str, project_id: str) -> PlanningDependency:
        try:
            return planning_service.get_planning_dependency(project_id, dependency_id=dependency_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Planning dependency not found.") from exc

    @router.get("/planning/chapter-packets", response_model=ChapterPacketListResponse)
    def list_chapter_packets(project_id: str) -> ChapterPacketListResponse:
        return ChapterPacketListResponse(
            project_id=project_id,
            items=list(planning_service.list_chapter_packets(project_id)),
            meta={"ordered_by": "chapter_id_asc"},
        )

    @router.get("/planning/chapter-packets/{packet_id}", response_model=ChapterPacket)
    def get_chapter_packet(packet_id: str, project_id: str) -> ChapterPacket:
        try:
            return planning_service.get_chapter_packet(project_id, packet_id=packet_id)
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Chapter packet not found.") from exc

    @router.post("/planning/reorder", response_model=PlanningDependencyListResponse)
    def reorder_plan_objects(payload: PlanningReorderRequest) -> PlanningDependencyListResponse:
        """Reorder sequences, chapters, or scene plans."""
        try:
            if payload.plan_kind not in ("sequence", "chapter", "scene"):
                raise HTTPException(status_code=400, detail="plan_kind must be 'sequence', 'chapter', or 'scene'.")
            if payload.plan_kind == "sequence":
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="sequence", ordered_plan_ids=payload.ordered_plan_ids)
                items = list(planning_service.list_sequence_plans(payload.project_id))
            elif payload.plan_kind == "chapter":
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="chapter", ordered_plan_ids=payload.ordered_plan_ids)
                items = list(planning_service.list_chapter_plans(payload.project_id))
            else:
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="scene", ordered_plan_ids=payload.ordered_plan_ids)
                items = list(planning_service.list_scene_plans(payload.project_id))
            return PlanningDependencyListResponse(
                project_id=payload.project_id,
                items=[],
                meta={"reordered_kind": payload.plan_kind, "ordered_count": str(len(payload.ordered_plan_ids))},
            )
        except PlanningValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"{payload.plan_kind} plan not found.") from exc

    @router.get("/drafting/draft-artifacts", response_model=DraftArtifactListResponse)
    def list_draft_artifacts(project_id: str) -> DraftArtifactListResponse:
        return DraftArtifactListResponse(
            project_id=project_id,
            items=list(drafting_service.list_draft_artifacts(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/draft-artifacts/{artifact_id}", response_model=DraftArtifact)
    def get_draft_artifact(artifact_id: str, project_id: str) -> DraftArtifact:
        try:
            return drafting_service.get_draft_artifact(project_id, artifact_id=artifact_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.get("/drafting/manuscript-documents", response_model=ManuscriptDocumentListResponse)
    def list_manuscript_documents(project_id: str) -> ManuscriptDocumentListResponse:
        return ManuscriptDocumentListResponse(
            project_id=project_id,
            items=list(drafting_service.list_manuscript_documents(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
    def get_manuscript_document(document_id: str, project_id: str) -> ManuscriptDocument:
        try:
            return drafting_service.get_manuscript_document(project_id, document_id=document_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Manuscript document not found.") from exc

    @router.get("/drafting/revision-suggestions", response_model=RevisionSuggestionListResponse)
    def list_revision_suggestions(project_id: str, target_document_id: str | None = None) -> RevisionSuggestionListResponse:
        if target_document_id is None:
            items = list(drafting_service.list_revision_suggestions(project_id))
        else:
            items = list(
                drafting_service.list_revision_suggestions_for_document(
                    project_id,
                    target_document_id=target_document_id,
                )
            )
        return RevisionSuggestionListResponse(project_id=project_id, items=items, meta={"ordered_by": "suggestion_id_asc"})

    @router.get("/drafting/revision-suggestions/{suggestion_id}", response_model=RevisionSuggestion)
    def get_revision_suggestion(suggestion_id: str, project_id: str) -> RevisionSuggestion:
        try:
            return drafting_service.get_revision_suggestion(project_id, suggestion_id=suggestion_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Revision suggestion not found.") from exc

    @router.post("/drafting/manuscript-documents", response_model=ManuscriptDocument, status_code=201)
    def create_manuscript_document(payload: ManuscriptDocumentCreateRequest) -> ManuscriptDocument:
        """Create a new manuscript document.

        Creates a manuscript document with the specified content and metadata.
        Optionally links to an existing draft artifact for provenance tracking.

        Args:
            payload: Manuscript document creation request with ID, title, content, and optional chapter/scene references.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.save_manuscript_document(
                payload.project_id,
                document_id=payload.document_id,
                content=payload.content,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                current_draft_artifact_id=payload.current_draft_artifact_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Referenced draft artifact not found.") from exc

    @router.patch("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
    def update_manuscript_document(
        document_id: str,
        project_id: str,
        payload: ManuscriptDocumentUpdateRequest,
    ) -> ManuscriptDocument:
        """Partially update a manuscript document's content or title.

        Updates only the fields that are provided in the request body.
        Version is automatically incremented.

        Args:
            document_id: The manuscript document identifier.
            project_id: The project identifier.
            payload: Partial update with optional 'content' and 'title' fields.

        Returns:
            The updated ManuscriptDocument object.

        Raises:
            HTTPException 400: If no fields are provided.
            HTTPException 404: If the document or project does not exist.
        """
        if payload.content is None and payload.title is None:
            raise HTTPException(status_code=400, detail="At least one of 'content' or 'title' must be provided.")
        try:
            existing = drafting_service.get_manuscript_document(project_id, document_id=document_id)
        except DraftingNotFoundError:
            raise HTTPException(status_code=404, detail="Manuscript document not found.")
        update_content = payload.content if payload.content is not None else existing.content
        update_title = payload.title if payload.title is not None else existing.title
        try:
            return drafting_service.save_manuscript_document(
                project_id,
                document_id=document_id,
                content=update_content,
                title=update_title,
                chapter_id=existing.chapter_id,
                scene_id=existing.scene_id,
                current_draft_artifact_id=existing.current_draft_artifact_id,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Manuscript document not found.") from exc

    @router.post(
        "/drafting/manuscript-documents/{document_id}/review",
        response_model=ManuscriptReviewResponse,
        status_code=202,
    )
    def trigger_manuscript_review(
        document_id: str,
        project_id: str,
    ) -> ManuscriptReviewResponse:
        """Trigger an AI review of the manuscript document.

        Analyzes the manuscript content for repetition, blank paragraph gaps,
        and potential new characters not yet listed in the project's character records.

        Args:
            document_id: The manuscript document identifier.
            project_id: The project identifier.

        Returns:
            A response containing any generated revision suggestions.

        Raises:
            HTTPException 404: If the document or project does not exist.
        """
        try:
            findings = manuscript_review_service.analyze_manuscript(
                project_id, document_id=document_id
            )
        except ManuscriptReviewError:
            raise HTTPException(status_code=404, detail="Manuscript document not found.")

        def _to_dict(finding):
            return {
                "suggestion_id": finding.suggestion_id,
                "project_id": finding.project_id,
                "target_document_id": finding.target_document_id,
                "source_text": finding.source_text,
                "proposed_text": finding.proposed_text,
                "rationale": finding.rationale,
                "source_context": finding.source_context,
                "status": finding.status,
            }

        return ManuscriptReviewResponse(
            document_id=document_id,
            project_id=project_id,
            findings=[_to_dict(finding) for finding in findings],
        )

    @router.post("/drafting/promote-draft", response_model=ManuscriptDocument, status_code=201)
    def promote_draft_to_manuscript(payload: PromoteDraftToManuscriptRequest) -> ManuscriptDocument:
        """Promote a draft artifact to a manuscript document.

        Creates a new manuscript document from an existing draft artifact,
        preserving the draft's content and optionally updating metadata.

        Args:
            payload: Promotion request with project ID, target document ID, and source draft artifact ID.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.promote_draft_to_manuscript(
                payload.project_id,
                document_id=payload.document_id,
                draft_artifact_id=payload.draft_artifact_id,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.post("/drafting/revision-suggestions", response_model=RevisionSuggestion, status_code=201)
    def create_revision_suggestion(payload: RevisionSuggestionCreateRequest) -> RevisionSuggestion:
        """Create a revision suggestion for a manuscript document.

        Proposes text changes to an existing manuscript document with rationale
        and source context for review.

        Args:
            payload: Revision suggestion request with target document, source/proposed text, and rationale.

        Returns:
            The created RevisionSuggestion object.

        Raises:
            HTTPException 404: If the target manuscript document does not exist.
        """
        try:
            return drafting_service.create_revision_suggestion(
                payload.project_id,
                suggestion_id=payload.suggestion_id,
                target_document_id=payload.target_document_id,
                source_text=payload.source_text,
                proposed_text=payload.proposed_text,
                rationale=payload.rationale,
                source_context=payload.source_context,
                status=payload.status,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target manuscript document not found.") from exc

    @router.post("/review/decisions", response_model=ReviewDecision, status_code=201)
    def record_review_decision(payload: ReviewDecisionCreateRequest) -> ReviewDecision:
        """Record a review decision for a target object.

        Records an accept/reject/defer decision on checker findings, artifacts,
        or other reviewable objects with optional notes and context.

        Args:
            payload: Review decision request with target kind/id, decision action, and optional notes.

        Returns:
            The created ReviewDecision object.

        Raises:
            HTTPException 404: If the target object does not exist.
        """
        try:
            return review_service.record_review_decision(
                payload.project_id,
                decision_id=payload.decision_id,
                target_kind=payload.target_kind,
                target_id=payload.target_id,
                decision=payload.decision,
                notes=payload.notes,
                source_context=payload.source_context,
            )
        except ReviewRoutingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target object not found.") from exc

    # ============================================================================
    # Brainstorm Endpoints
    # ============================================================================

    @router.get("/brainstorm/items", response_model=BrainstormItemListResponse)
    def list_brainstorm_items(project_id: str) -> BrainstormItemListResponse:
        """List all brainstorm items for a project."""
        items = list(repository.list_brainstorm_items(project_id))
        return BrainstormItemListResponse(
            project_id=project_id,
            items=[brainstorm_service._to_schema(item) for item in items],
            meta={"ordered_by": "created_at_asc"},
        )

    @router.post("/brainstorm/items", response_model=BrainstormItem, status_code=201)
    def create_brainstorm_item(payload: BrainstormItemCreateRequest) -> BrainstormItem:
        """Create a new brainstorm item."""
        try:
            return brainstorm_service.capture_brainstorm_item(
                project_id=payload.project_id,
                content=payload.content,
                status=payload.status,
                cluster_key=payload.cluster_key,
                tags=payload.tags,
                source_artifact_refs=payload.source_artifact_refs,
            )
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/brainstorm/items/cluster", response_model=list[BrainstormItem])
    def cluster_brainstorm_items(payload: BrainstormItemClusterRequest) -> list[BrainstormItem]:
        """Cluster multiple brainstorm items together."""
        try:
            return brainstorm_service.cluster_brainstorm_items(
                project_id=payload.project_id,
                item_ids=payload.item_ids,
                cluster_key=payload.cluster_key,
            )
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/brainstorm/items/promote", response_model=BrainstormPromotion, status_code=201)
    def promote_brainstorm_item(payload: BrainstormItemPromoteRequest) -> BrainstormPromotion:
        """Promote a brainstorm item to a target object."""
        try:
            return brainstorm_service.promote_brainstorm_item(
                project_id=payload.project_id,
                item_id=payload.item_id,
                target_object_kind=payload.target_object_kind,
                target_object_id=payload.target_object_id,
                notes=payload.notes,
            )
        except BrainstormNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brainstorm item not found.") from exc
        except BrainstormValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/brainstorm/promotions", response_model=BrainstormPromotionListResponse)
    def list_brainstorm_promotions(project_id: str) -> BrainstormPromotionListResponse:
        """List all brainstorm promotions for a project."""
        promotions = brainstorm_service.list_promotions(project_id)
        return BrainstormPromotionListResponse(
            project_id=project_id,
            items=list(promotions),
            meta={"ordered_by": "created_at_asc"},
        )

    # ============================================================================
    # Brain Dump Endpoints
    # ============================================================================

    @router.post("/braindump/sessions", response_model=BrainDumpSessionResponse, status_code=201)
    def create_brain_dump_session(payload: BrainDumpSessionCreateRequest) -> BrainDumpSessionResponse:
        """Create a new brain dump session for a project."""
        try:
            session = braindump_service.create_session(
                project_id=payload.project_id,
                title=payload.title,
                raw_text=payload.raw_text,
            )
            return _session_to_response(session)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/braindump/sessions", response_model=BrainDumpSessionListResponse)
    def list_brain_dump_sessions(project_id: str) -> BrainDumpSessionListResponse:
        """List all brain dump sessions for a project."""
        sessions = braindump_service.list_sessions(project_id)
        return BrainDumpSessionListResponse(
            project_id=project_id,
            sessions=[_session_to_response(s) for s in sessions],
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/braindump/sessions/{session_id}", response_model=BrainDumpSessionResponse)
    def get_brain_dump_session(session_id: int, project_id: str) -> BrainDumpSessionResponse:
        """Get a specific brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            return _session_to_response(session)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.patch("/braindump/sessions/{session_id}", response_model=BrainDumpSessionResponse)
    def patch_brain_dump_session(
        session_id: int,
        project_id: str,
        payload: BrainDumpSessionPatchRequest,
    ) -> BrainDumpSessionResponse:
        """Update a brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            updated = braindump_service.update_session(
                session_id,
                raw_text=payload.raw_text,
                title=payload.title,
                state=payload.state,
            )
            return _session_to_response(updated)
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.delete("/braindump/sessions/{session_id}", status_code=204)
    def delete_brain_dump_session(session_id: int, project_id: str) -> None:
        """Delete a brain dump session."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            braindump_service.delete_session(session_id)
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    @router.post("/braindump/sessions/{session_id}/organize", response_model=BrainDumpOrganizeResponse, status_code=201)
    def organize_brain_dump_session(
        session_id: int,
        project_id: str,
    ) -> BrainDumpOrganizeResponse:
        """Organize a brain dump session by categorizing raw text into brainstorm items."""
        try:
            session = braindump_service.get_session(session_id)
            if session.project_id != project_id:
                raise BrainDumpNotFoundError(session_id)
            if session.state != "active":
                raise BrainDumpValidationError("Only active sessions can be organized.")

            items = _mock_organize_raw_text(session.raw_text)
            created_items: list[BrainstormItem] = []
            for item_type, text_blocks in items.items():
                for idx, text in enumerate(text_blocks):
                    brainstorm_item = brainstorm_service.capture_brainstorm_item(
                        project_id=project_id,
                        content=text,
                        status="keep",
                        tags=[item_type.lower()],
                    )
                    # Attach item_type to the response schema
                    braindump_item = BrainstormItem(
                        item_id=brainstorm_item.item_id,
                        project_id=brainstorm_item.project_id,
                        content=brainstorm_item.content,
                        status=brainstorm_item.status,
                        tags=brainstorm_item.tags,
                        source_notes=brainstorm_item.source_notes,
                        item_type=item_type,
                    )
                    created_items.append(braindump_item)

            braindump_service.update_session(session_id, state="organized")

            categorized: dict[str, list[BrainstormItem]] = {}
            for item in created_items:
                if item.item_type:
                    categorized.setdefault(item.item_type, []).append(item)

            return BrainDumpOrganizeResponse(
                session_id=session_id,
                categorized_items=categorized,
                total_items=len(created_items),
            )
        except BrainDumpValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BrainDumpNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Brain dump session not found.") from exc

    # ============================================================================
    # Foundation Endpoints
    # ============================================================================

    @router.get("/foundation", response_model=FoundationReadResponse)
    def get_foundation(project_id: str) -> FoundationReadResponse:
        """Get the active foundation profile for a project."""
        try:
            result = foundation_service.read_active_foundation(project_id)
            return FoundationReadResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=[
                    FoundationReviewCue(
                        impacted_area=cue.impacted_area,
                        reason=cue.reason,
                        triggering_revision_id=cue.triggering_revision_id,
                        triggering_fields=list(cue.triggering_fields),
                    )
                    for cue in result.downstream_review_cues
                ],
            )
        except FoundationNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Foundation not found.") from exc

    @router.post("/foundation", response_model=FoundationWriteResponse, status_code=201)
    def create_foundation(payload: FoundationCreateRequest) -> FoundationWriteResponse:
        """Create a new foundation profile for a project."""
        try:
            foundation_data = {
                "premise": payload.premise,
                "logline": payload.logline,
                "thematic_spine": payload.thematic_spine,
                "emotional_promise": payload.emotional_promise,
                "tone_and_voice_direction": payload.tone_and_voice_direction,
                "target_audience": payload.target_audience,
                "narrative_constraints": payload.narrative_constraints,
                "complexity_level": payload.complexity_level,
                "success_definition": payload.success_definition,
            }
            result = foundation_service.create_foundation_revision(payload.project_id, foundation_data)
            return FoundationWriteResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=[
                    FoundationReviewCue(
                        impacted_area=cue.impacted_area,
                        reason=cue.reason,
                        triggering_revision_id=cue.triggering_revision_id,
                        triggering_fields=list(cue.triggering_fields),
                    )
                    for cue in result.downstream_review_cues
                ],
                created_revision=result.created_revision,
            )
        except FoundationValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/foundation", response_model=FoundationWriteResponse)
    def update_foundation(project_id: str, payload: FoundationUpdateRequest) -> FoundationWriteResponse:
        """Update the active foundation profile for a project."""
        try:
            foundation_data = {
                key: value for key, value in (
                    ("premise", payload.premise),
                    ("logline", payload.logline),
                    ("thematic_spine", payload.thematic_spine),
                    ("emotional_promise", payload.emotional_promise),
                    ("tone_and_voice_direction", payload.tone_and_voice_direction),
                    ("target_audience", payload.target_audience),
                    ("narrative_constraints", payload.narrative_constraints),
                    ("complexity_level", payload.complexity_level),
                    ("success_definition", payload.success_definition),
                ) if value is not None
            }
            if not foundation_data:
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            result = foundation_service.update_foundation_revision(project_id, foundation_data)
            return FoundationWriteResponse(
                project_id=result.project_id,
                foundation_id=result.foundation_id,
                active_profile=result.active_profile,
                current_revision_id=result.current_revision_id,
                revision_history=list(result.revision_history),
                downstream_review_cues=[
                    FoundationReviewCue(
                        impacted_area=cue.impacted_area,
                        reason=cue.reason,
                        triggering_revision_id=cue.triggering_revision_id,
                        triggering_fields=list(cue.triggering_fields),
                    )
                    for cue in result.downstream_review_cues
                ],
                created_revision=result.created_revision,
            )
        except FoundationNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Foundation not found.") from exc
        except FoundationValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/foundation/revisions", response_model=FoundationRevisionListResponse)
    def list_foundation_revisions(project_id: str) -> FoundationRevisionListResponse:
        """List all foundation revisions for a project."""
        revisions = foundation_service.list_foundation_revisions(project_id)
        return FoundationRevisionListResponse(
            project_id=project_id,
            items=list(revisions),
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/foundation/review-cues", response_model=FoundationReviewCueListResponse)
    def list_foundation_review_cues(project_id: str) -> FoundationReviewCueListResponse:
        """List downstream review cues triggered by foundation changes."""
        cues = foundation_service.list_downstream_review_cues(project_id)
        return FoundationReviewCueListResponse(
            project_id=project_id,
            items=[
                FoundationReviewCue(
                    impacted_area=cue.impacted_area,
                    reason=cue.reason,
                    triggering_revision_id=cue.triggering_revision_id,
                    triggering_fields=list(cue.triggering_fields),
                )
                for cue in cues
            ],
            meta={"ordered_by": "created_at_asc"},
        )

    # ============================================================================
    # Character Endpoints
    # ============================================================================

    @router.get("/characters", response_model=CharacterProfileListResponse)
    def list_characters(project_id: str) -> CharacterProfileListResponse:
        """List all character profiles for a project."""
        characters = list(story_knowledge_service.list_character_profiles(project_id))
        return CharacterProfileListResponse(
            project_id=project_id,
            items=characters,
            meta={"ordered_by": "character_id_asc"},
        )

    @router.get("/characters/{character_id}", response_model=CharacterProfile)
    def get_character(character_id: str, project_id: str) -> CharacterProfile:
        """Get a specific character profile."""
        try:
            return story_knowledge_service.get_character_profile(project_id, character_id=character_id)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Character not found.") from exc

    @router.post("/characters", response_model=CharacterProfile, status_code=201)
    def create_character(payload: CharacterProfileCreateRequest) -> CharacterProfile:
        """Create a new character profile."""
        try:
            return story_knowledge_service.upsert_character_profile(
                payload.project_id,
                character_id=payload.character_id,
                display_name=payload.display_name,
                role_in_story=payload.role_in_story,
                archetype=payload.archetype,
                external_goal=payload.external_goal,
                internal_need=payload.internal_need,
                misbelief_or_wound=payload.misbelief_or_wound,
                core_fear=payload.core_fear,
                primary_strength=payload.primary_strength,
                fatal_flaw_or_limitation=payload.fatal_flaw_or_limitation,
                contradictions=payload.contradictions,
                backstory_summary=payload.backstory_summary,
                voice_notes=payload.voice_notes,
                secrets=payload.secrets,
                values=payload.values,
                taboos=payload.taboos,
                change_axis=payload.change_axis,
                arc_stage_notes=payload.arc_stage_notes,
                continuity_facts=payload.continuity_facts,
                writer_notes=payload.writer_notes,
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/characters/{character_id}", response_model=CharacterProfile)
    def update_character(character_id: str, project_id: str, payload: CharacterProfileUpdateRequest) -> CharacterProfile:
        """Update a character profile."""
        try:
            updates = {
                key: value for key, value in (
                    ("display_name", payload.display_name),
                    ("role_in_story", payload.role_in_story),
                    ("archetype", payload.archetype),
                    ("external_goal", payload.external_goal),
                    ("internal_need", payload.internal_need),
                    ("misbelief_or_wound", payload.misbelief_or_wound),
                    ("core_fear", payload.core_fear),
                    ("primary_strength", payload.primary_strength),
                    ("fatal_flaw_or_limitation", payload.fatal_flaw_or_limitation),
                    ("contradictions", payload.contradictions),
                    ("backstory_summary", payload.backstory_summary),
                    ("voice_notes", payload.voice_notes),
                    ("secrets", payload.secrets),
                    ("values", payload.values),
                    ("taboos", payload.taboos),
                    ("change_axis", payload.change_axis),
                    ("arc_stage_notes", payload.arc_stage_notes),
                    ("continuity_facts", payload.continuity_facts),
                    ("writer_notes", payload.writer_notes),
                ) if value is not None
            }
            if not updates:
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            # Get existing character and merge with updates
            existing = story_knowledge_service.get_character_profile(project_id, character_id=character_id)
            all_fields = {
                "character_id": character_id,
                **dict(existing),
                **updates,
            }
            # Filter out relationship_edges (auto-populated by service) and project_id
            # Note: relationship_edges is intentionally excluded - it's auto-populated from relationship edges
            upsert_fields = {
                k: v for k, v in all_fields.items()
                if v is not None and k not in ("project_id", "relationship_edges")
            }
            # Call upsert with merged data
            return story_knowledge_service.upsert_character_profile(project_id, **upsert_fields)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Character not found.") from exc
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/characters/{character_id}/relationships", response_model=RelationshipEdgeListResponse)
    def list_character_relationships(character_id: str, project_id: str) -> RelationshipEdgeListResponse:
        """List all relationships for a character."""
        try:
            relationships = list(story_knowledge_service.list_relationship_edges_for_character(project_id, character_id))
            return RelationshipEdgeListResponse(
                project_id=project_id,
                items=relationships,
                meta={"ordered_by": "edge_id_asc"},
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/relationships", response_model=RelationshipEdge, status_code=201)
    def create_relationship(payload: RelationshipEdgeCreateRequest) -> RelationshipEdge:
        """Create a new relationship between characters."""
        try:
            return story_knowledge_service.upsert_relationship_edge(
                payload.project_id,
                edge_id=payload.edge_id,
                source_character_id=payload.source_character_id,
                target_character_id=payload.target_character_id,
                relation_kind=payload.relation_kind,
                summary=payload.summary,
                tension=payload.tension,
                notes=payload.notes,
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/relationships", response_model=RelationshipEdgeListResponse)
    def list_all_relationships(project_id: str) -> RelationshipEdgeListResponse:
        """List all relationship edges for a project."""
        try:
            relationships = list(story_knowledge_service.list_all_relationship_edges(project_id))
            return RelationshipEdgeListResponse(
                project_id=project_id,
                items=relationships,
                meta={"ordered_by": "edge_id_asc"},
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/relationships/{edge_id}", response_model=RelationshipEdge)
    def update_relationship(edge_id: str, project_id: str, payload: RelationshipEdgeUpdateRequest) -> RelationshipEdge:
        """Update an existing relationship."""
        try:
            source = payload.source_character_id if payload.source_character_id is not None else None
            target = payload.target_character_id if payload.target_character_id is not None else None
            kind = payload.relation_kind if payload.relation_kind is not None else None
            summary = payload.summary if payload.summary is not None else None
            tension = payload.tension
            notes = payload.notes
            if not any(v is not None for v in [source, target, kind, summary, tension, notes]):
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            return story_knowledge_service.upsert_relationship_edge(
                project_id,
                edge_id=edge_id,
                source_character_id=source if source else "",
                target_character_id=target if target else "",
                relation_kind=kind if kind else "",
                summary=summary if summary else "",
                tension=tension,
                notes=notes,
            )
        except HTTPException:
            raise
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/relationships/{edge_id}", status_code=200)
    def delete_relationship(edge_id: str, project_id: str) -> dict[str, str]:
        """Delete a relationship edge."""
        try:
            story_knowledge_service.delete_relationship_edge(project_id, edge_id)
            return {"status": "deleted", "edge_id": edge_id}
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Relationship not found.") from exc
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ============================================================================
    # World Bible Endpoints
    # ============================================================================

    @router.get("/world-bible", response_model=WorldBibleEntryListResponse)
    def list_world_bible_entries(
        project_id: str,
        entry_type: str | None = None,
    ) -> WorldBibleEntryListResponse:
        """List all world bible entries for a project."""
        entries = list(story_knowledge_service.list_world_bible_entries(project_id))
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        return WorldBibleEntryListResponse(
            project_id=project_id,
            items=entries,
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/world-bible/{entry_type}/{title}", response_model=WorldBibleEntry)
    def get_world_bible_entry(entry_type: str, title: str, project_id: str) -> WorldBibleEntry:
        """Get a specific world bible entry."""
        try:
            return story_knowledge_service.get_world_bible_entry(project_id, entry_type=entry_type, title=title)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="World bible entry not found.") from exc

    @router.post("/world-bible", response_model=WorldBibleEntry, status_code=201)
    def create_world_bible_entry(payload: WorldBibleEntryCreateRequest) -> WorldBibleEntry:
        """Create a new world bible entry."""
        try:
            return story_knowledge_service.upsert_world_bible_entry(
                payload.project_id,
                entry_type=payload.entry_type,
                title=payload.title,
                summary=payload.summary,
                canonical_facts=payload.canonical_facts,
                related_character_ids=payload.related_character_ids,
                source_artifacts=payload.source_artifacts,
                visibility_scope=payload.visibility_scope,
                continuity_warnings=payload.continuity_warnings,
                writer_notes=payload.writer_notes,
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/world-bible/{entry_type}/{title}", response_model=WorldBibleEntry)
    def update_world_bible_entry(entry_type: str, title: str, project_id: str, payload: WorldBibleEntryUpdateRequest) -> WorldBibleEntry:
        """Update a world bible entry."""
        try:
            # Get existing entry
            existing = story_knowledge_service.get_world_bible_entry(project_id, entry_type=entry_type, title=title)
            
            # Helper to compare list fields (handles tuple vs list comparison)
            def lists_equal(a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> bool:
                return set(a) == set(b)
            
            # Merge updates - use explicit type annotations to avoid union type issues
            new_title: str = payload.title if payload.title is not None else title
            new_summary: str = payload.summary if payload.summary is not None else existing.summary
            new_canonical_facts: list[str] = payload.canonical_facts if payload.canonical_facts is not None else existing.canonical_facts
            new_related_character_ids: list[str] = payload.related_character_ids if payload.related_character_ids is not None else existing.related_character_ids
            new_source_artifacts: list[str] = payload.source_artifacts if payload.source_artifacts is not None else existing.source_artifacts
            new_visibility_scope: str = payload.visibility_scope if payload.visibility_scope is not None else existing.visibility_scope
            new_continuity_warnings: list[str] = payload.continuity_warnings if payload.continuity_warnings is not None else existing.continuity_warnings
            new_writer_notes: str | None = payload.writer_notes if payload.writer_notes is not None else existing.writer_notes
            
            # Check if at least one field is being updated (use set comparison for lists)
            if (new_title == title and new_summary == existing.summary and 
                lists_equal(new_canonical_facts, existing.canonical_facts) and 
                lists_equal(new_related_character_ids, existing.related_character_ids) and
                lists_equal(new_source_artifacts, existing.source_artifacts) and
                new_visibility_scope == existing.visibility_scope and
                lists_equal(new_continuity_warnings, existing.continuity_warnings) and
                new_writer_notes == existing.writer_notes):
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            
            # Call upsert with merged data
            return story_knowledge_service.upsert_world_bible_entry(
                project_id,
                entry_type=entry_type,
                summary=new_summary,
                title=new_title,
                canonical_facts=new_canonical_facts,
                related_character_ids=new_related_character_ids,
                source_artifacts=new_source_artifacts,
                visibility_scope=new_visibility_scope,
                continuity_warnings=new_continuity_warnings,
                writer_notes=new_writer_notes,
            )
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="World bible entry not found.") from exc
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ============================================================================
    # Arc Endpoints
    # ============================================================================

    @router.get("/arcs/candidates", response_model=ArcCandidateListResponse)
    def list_arc_candidates(project_id: str) -> ArcCandidateListResponse:
        """List all arc candidates for a project."""
        try:
            candidates = list(story_knowledge_service.list_arc_candidates(project_id))
            return ArcCandidateListResponse(
                project_id=project_id,
                items=candidates,
                meta={"ordered_by": "candidate_id_asc"},
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/arcs/selections", response_model=ArcSelectionListResponse)
    def list_arc_selections(project_id: str) -> ArcSelectionListResponse:
        """List all arc selections for a project."""
        selections = list(story_knowledge_service.list_arc_selections(project_id))
        return ArcSelectionListResponse(
            project_id=project_id,
            items=selections,
            meta={"ordered_by": "created_at_asc"},
        )

    @router.get("/arcs/stage-maps", response_model=ArcStageMapListResponse)
    def list_arc_stage_maps(project_id: str) -> ArcStageMapListResponse:
        """List all arc stage maps for a project."""
        try:
            stage_maps = list(story_knowledge_service.list_arc_stage_maps(project_id))
            return ArcStageMapListResponse(
                project_id=project_id,
                items=stage_maps,
                meta={"ordered_by": "stage_id_asc"},
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/candidates", response_model=ArcCandidate, status_code=201)
    def create_arc_candidate(payload: ArcCandidateCreateRequest) -> ArcCandidate:
        """Create a new arc candidate for a project."""
        try:
            candidate = story_knowledge_service.upsert_arc_candidate(
                project_id=payload.project_id,
                arc_id=payload.arc_id,
                name=payload.name,
                summary=payload.summary,
                stage_map_notes=payload.stage_map_notes,
                fit_notes=payload.fit_notes,
                tags=payload.tags,
            )
            return candidate
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/comparisons", response_model=ArcCandidateListResponse)
    def compare_arc_candidates_endpoint(payload: ArcComparisonRequest) -> ArcCandidateListResponse:
        """Score and rank arc candidates for a project."""
        try:
            normalized_candidates: list = []
            for candidate in payload.candidates:
                if isinstance(candidate, ArcCandidateCreateRequest):
                    normalized_candidates.append({
                        "arc_id": candidate.arc_id,
                        "project_id": candidate.project_id,
                        "name": candidate.name,
                        "summary": candidate.summary,
                        "stage_map_notes": candidate.stage_map_notes,
                        "fit_notes": candidate.fit_notes,
                        "tags": candidate.tags,
                    })
                else:
                    normalized_candidates.append(candidate)
            comparisons = story_knowledge_service.compare_arc_candidates(
                project_id=payload.project_id,
                candidates=normalized_candidates,
            )
            ranked_candidates = sorted(comparisons, key=lambda c: c.rank)
            return ArcCandidateListResponse(
                project_id=payload.project_id,
                items=[c.candidate for c in ranked_candidates],
                meta={"comparison_count": str(len(comparisons))},
            )
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/arcs/selections", response_model=ArcSelection, status_code=201)
    def select_arc_candidate_endpoint(payload: ArcSelectionCreateRequest) -> ArcSelection:
        """Select an arc candidate, rejecting the others."""
        try:
            selected_arc: ArcCandidate | str = payload.selected_arc
            if isinstance(selected_arc, ArcCandidateCreateRequest):
                selected_arc = ArcCandidate(
                    arc_id=selected_arc.arc_id,
                    project_id=selected_arc.project_id,
                    name=selected_arc.name,
                    summary=selected_arc.summary,
                    stage_map_notes=selected_arc.stage_map_notes,
                    fit_notes=selected_arc.fit_notes,
                    tags=selected_arc.tags,
                )
            rejected_ids = list(payload.rejected_arc_ids) if payload.rejected_arc_ids else None
            comparison_notes = list(payload.comparison_notes) if payload.comparison_notes else None
            stage_map = None
            if payload.stage_map:
                stage_map = ArcStageMap(
                    arc_id=payload.stage_map.arc_id,
                    stage_kinds=payload.stage_map.stage_kinds,
                    notes=payload.stage_map.notes,
                )
            selection = story_knowledge_service.select_arc_candidate(
                project_id=payload.project_id,
                selected_arc=selected_arc,
                rejected_arc_ids=rejected_ids,
                comparison_notes=comparison_notes,
                stage_map=stage_map,
            )
            return selection
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/arcs/selections/{selection_id}", response_model=ArcSelection)
    def update_arc_selection(
        selection_id: str,
        project_id: str,
        payload: ArcSelectionUpdateRequest,
    ) -> ArcSelection:
        """Update an arc selection's notes or stage map."""
        try:
            selection = story_knowledge_service.get_arc_selection(project_id, selection_id)
            if selection is None:
                raise StoryKnowledgeNotFoundError(selection_id)
            if payload.stage_map is not None:
                story_knowledge_service.update_arc_stage_map(
                    project_id=project_id,
                    arc_id=payload.stage_map.arc_id,
                    stage_kinds=payload.stage_map.stage_kinds,
                    notes=payload.stage_map.notes,
                )
            comparison_notes = payload.comparison_notes if payload.comparison_notes is not None else list(selection.comparison_notes)
            updated = story_knowledge_service._update_selection_notes(
                project_id,
                selection_id,
                comparison_notes,
            )
            return updated
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc selection not found.") from exc
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/arcs/selections/{selection_id}", status_code=200)
    def delete_arc_selection(selection_id: str, project_id: str) -> dict[str, str]:
        """Remove an arc selection."""
        try:
            story_knowledge_service.delete_arc_selection(project_id, selection_id)
            return {"status": "deleted", "selection_id": selection_id}
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc selection not found.") from exc

    @router.post("/arcs/stage-maps", response_model=ArcStageMap, status_code=201)
    def create_arc_stage_map(project_id: str, payload: ArcStageMapCreateRequest) -> ArcStageMap:
        """Create or update a stage map for an arc candidate."""
        try:
            stage_map = story_knowledge_service.update_arc_stage_map(
                project_id=project_id,
                arc_id=payload.arc_id,
                stage_kinds=payload.stage_kinds,
                notes=payload.notes,
            )
            return stage_map
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Arc candidate not found for stage map.") from exc
        except StoryKnowledgeValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ============================================================================
    # Storyboard Card Endpoints
    # ============================================================================

    @router.get("/storyboard/cards", response_model=StoryboardCardListResponse)
    def list_storyboard_cards(
        project_id: str,
        card_type: str | None = None,
        column_id: str | None = None,
        tag: str | None = None,
    ) -> StoryboardCardListResponse:
        """List storyboard cards for a project with optional filters."""
        try:
            from app.services.storyboard_cards import CardFilterOptions
            filter_opts = None
            if card_type or column_id or tag:
                filter_opts = CardFilterOptions(
                    card_type=card_type,
                    column_id=column_id,
                    tag=tag,
                )
            items = storyboard_card_service.list_cards(project_id, filter_options=filter_opts)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryboardCardListResponse(
            project_id=project_id,
            items=[_card_to_schema(c) for c in items],
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def get_storyboard_card(card_id: str, project_id: str) -> StoryboardCard:
        """Get a specific storyboard card."""
        try:
            card = storyboard_card_service.get_card(card_id)
            return _card_to_schema(card)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc

    @router.post("/storyboard/cards", response_model=StoryboardCard, status_code=201)
    def create_storyboard_card(payload: StoryboardCardCreateRequest) -> StoryboardCard:
        """Create a new storyboard card."""
        try:
            card = storyboard_card_service.create_card(
                project_id=payload.project_id,
                card_id=payload.card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                column_id=payload.column_id,
                position=payload.position,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def update_storyboard_card(
        card_id: str,
        project_id: str,
        payload: StoryboardCardUpdateRequest,
    ) -> StoryboardCard:
        """Update a storyboard card."""
        try:
            existing = storyboard_card_service.get_card(card_id)
            if existing.project_id != project_id:
                raise StoryboardCardNotFoundError(card_id)
            card = storyboard_card_service.update_card_content(
                card_id=card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.put("/storyboard/cards/{card_id}", response_model=StoryboardCard)
    def upsert_storyboard_card(
        card_id: str,
        project_id: str,
        payload: StoryboardCardCreateRequest,
    ) -> StoryboardCard:
        """Create or update a storyboard card."""
        try:
            card = storyboard_card_service.upsert_card(
                project_id=payload.project_id,
                card_id=card_id,
                title=payload.title,
                content=payload.content,
                card_type=payload.card_type,
                column_id=payload.column_id,
                position=payload.position,
                tags=payload.tags,
                character_ids=payload.character_ids,
                dependencies=payload.dependencies,
                metadata=payload.metadata,
            )
            return _card_to_schema(card)
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/storyboard/cards/{card_id}", status_code=204)
    def delete_storyboard_card(card_id: str, project_id: str) -> None:
        """Delete a storyboard card."""
        try:
            card = storyboard_card_service.get_card(card_id)
            if card.project_id != project_id:
                raise StoryboardCardNotFoundError(card_id)
            storyboard_card_service.delete_card(card_id)
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc

    @router.put("/storyboard/cards/{column_id}/reindex", response_model=StoryboardCardListResponse)
    def reindex_storyboard_column(
        column_id: str,
        project_id: str,
        payload: StoryboardCardReindexRequest,
    ) -> StoryboardCardListResponse:
        """Reindex cards within a column."""
        try:
            results = storyboard_card_service.reindex_column(
                project_id=project_id,
                column_id=column_id,
                card_ids=payload.card_ids,
            )
        except StoryboardCardNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Storyboard card not found.") from exc
        except StoryboardCardValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StoryboardCardListResponse(
            project_id=project_id,
            items=[_card_to_schema(c) for c in results],
            meta={"ordered_by": "position_asc"},
        )

    # ============================================================================
    # Chapter Packet Write Endpoints
    # ============================================================================

    @router.post("/planning/chapter-packets", response_model=ChapterPacket, status_code=201)
    def create_chapter_packet(payload: ChapterPacketCreateRequest) -> ChapterPacket:
        """Create a new chapter packet."""
        try:
            packet = chapter_packet_service.register_packet(
                project_id=payload.project_id,
                packet_id=payload.packet_id,
                chapter_id=payload.chapter_id,
                included_reference_ids=payload.included_reference_ids,
                constraints=payload.constraints,
                scene_goals=payload.scene_goals,
                status=payload.status,
            )
            return _packet_to_schema(packet)
        except ChapterPacketValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/planning/chapter-packets/{packet_id}", response_model=ChapterPacket)
    def update_chapter_packet(
        packet_id: str,
        project_id: str,
        payload: ChapterPacketUpdateRequest,
    ) -> ChapterPacket:
        """Update a chapter packet."""
        try:
            try:
                existing = chapter_packet_service.get_packet(packet_id)
            except ChapterPacketNotFoundError:
                raise HTTPException(status_code=404, detail="Chapter packet not found.")
            except KeyError:
                raise HTTPException(status_code=404, detail="Chapter packet not found.")
            if existing.project_id != project_id:
                raise ChapterPacketNotFoundError(packet_id)
            
            included_reference_ids = (
                payload.included_reference_ids
                if payload.included_reference_ids is not None
                else list(existing.included_reference_ids)
            )
            constraints = (
                payload.constraints
                if payload.constraints is not None
                else list(existing.constraints)
            )
            scene_goals = (
                payload.scene_goals
                if payload.scene_goals is not None
                else list(existing.scene_goals)
            )
            status = payload.status if payload.status is not None else existing.status
            
            packet = chapter_packet_service.register_packet(
                project_id=existing.project_id,
                packet_id=existing.packet_id,
                chapter_id=existing.chapter_id,
                included_reference_ids=included_reference_ids,
                constraints=constraints,
                scene_goals=scene_goals,
                status=status,
            )
            return _packet_to_schema(packet)
        except ChapterPacketNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Chapter packet not found.") from exc
        except ChapterPacketValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ============================================================================
    # Sequence Plan Write Endpoints
    # ============================================================================

    @router.post("/planning/sequence-plans", response_model=SequencePlan, status_code=201)
    def create_sequence_plan(payload: SequencePlanCreateRequest) -> SequencePlan:
        """Create a new sequence plan."""
        try:
            plan = sequence_plan_service.register_plan(
                project_id=payload.project_id,
                sequence_id=payload.sequence_id,
                title=payload.title,
                summary=payload.summary,
                beat_ids=payload.beat_ids,
                chapter_ids=payload.chapter_ids,
                status=payload.status,
                position=payload.position,
            )
            return _sequence_to_schema(plan)
        except SequencePlanValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/planning/sequence-plans/{sequence_id}", response_model=SequencePlan)
    def update_sequence_plan(
        sequence_id: str,
        project_id: str,
        payload: SequencePlanUpdateRequest,
    ) -> SequencePlan:
        """Update a sequence plan."""
        try:
            try:
                existing = sequence_plan_service.get_plan(sequence_id)
            except SequencePlanNotFoundError:
                raise HTTPException(status_code=404, detail="Sequence plan not found.")
            except KeyError:
                raise HTTPException(status_code=404, detail="Sequence plan not found.")
            if existing.project_id != project_id:
                raise SequencePlanNotFoundError(sequence_id)
            
            beat_ids = payload.beat_ids if payload.beat_ids is not None else list(existing.beat_ids)
            chapter_ids = payload.chapter_ids if payload.chapter_ids is not None else list(existing.chapter_ids)
            title = payload.title if payload.title is not None else existing.title
            summary = payload.summary if payload.summary is not None else existing.summary
            status = payload.status if payload.status is not None else existing.status
            position = payload.position if payload.position is not None else existing.position
            
            plan = sequence_plan_service.register_plan(
                project_id=existing.project_id,
                sequence_id=existing.sequence_id,
                title=title,
                summary=summary,
                beat_ids=beat_ids,
                chapter_ids=chapter_ids,
                status=status,
                position=position,
            )
            return _sequence_to_schema(plan)
        except SequencePlanNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Sequence plan not found.") from exc
        except SequencePlanValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


# ============================================================================
# Brain Dump Helper Functions (module-level for route access)
# ============================================================================

# ============================================================================
# Storyboard Card, Chapter Packet, and Sequence Plan Helper Functions
# ============================================================================

def _card_to_schema(card) -> StoryboardCard:
    from app.persistence.story_development import StoryboardCardRecord as _Record
    if isinstance(card, _Record):
        return StoryboardCard(
            card_id=card.card_id,
            project_id=card.project_id,
            title=card.title,
            content=card.content,
            card_type=card.card_type,
            column_id=card.column_id,
            position=card.position,
            tags=list(card.tags) if card.tags else [],
            character_ids=list(card.character_ids) if card.character_ids else [],
            dependencies=list(card.dependencies) if card.dependencies else [],
            metadata=card.metadata or {},
        )
    return StoryboardCard(
        card_id=card.card_id,
        project_id=card.project_id,
        title=card.title,
        content=card.content,
        card_type=card.card_type,
        column_id=card.column_id,
        position=card.position,
        tags=list(card.tags) if card.tags else [],
        character_ids=list(card.character_ids) if card.character_ids else [],
        dependencies=list(card.dependencies) if card.dependencies else [],
        metadata=card.metadata or {},
    )


def _packet_to_schema(packet) -> ChapterPacket:
    from app.persistence.story_development import ChapterPacketRecord as _Record
    if isinstance(packet, _Record):
        return ChapterPacket(
            packet_id=packet.packet_id,
            project_id=packet.project_id,
            chapter_id=packet.chapter_id,
            included_reference_ids=list(packet.included_reference_ids) if packet.included_reference_ids else [],
            constraints=list(packet.constraints) if packet.constraints else [],
            scene_goals=list(packet.scene_goals) if packet.scene_goals else [],
            status=packet.status,
        )
    return ChapterPacket(
        packet_id=packet.packet_id,
        project_id=packet.project_id,
        chapter_id=packet.chapter_id,
        included_reference_ids=list(packet.included_reference_ids) if packet.included_reference_ids else [],
        constraints=list(packet.constraints) if packet.constraints else [],
        scene_goals=list(packet.scene_goals) if packet.scene_goals else [],
        status=packet.status,
    )


def _sequence_to_schema(plan) -> SequencePlan:
    from app.persistence.story_development import SequencePlanRecord as _Record
    if isinstance(plan, _Record):
        return SequencePlan(
            sequence_id=plan.sequence_id,
            project_id=plan.project_id,
            title=plan.title,
            summary=plan.summary,
            beat_ids=list(plan.beat_ids) if plan.beat_ids else [],
            chapter_ids=list(plan.chapter_ids) if plan.chapter_ids else [],
            status=plan.status,
        )
    return SequencePlan(
        sequence_id=plan.sequence_id,
        project_id=plan.project_id,
        title=plan.title,
        summary=plan.summary,
        beat_ids=list(plan.beat_ids) if plan.beat_ids else [],
        chapter_ids=list(plan.chapter_ids) if plan.chapter_ids else [],
        status=plan.status,
    )


# TODO: Replace with real LLM-based categorization when AI pipeline is available.
# Current implementation splits raw text by double-newlines and round-robins
# across categories. This provides a structural placeholder for the organize
# endpoint so the frontend workflow can be tested end-to-end.
_CATEGORY_KEYS = ["CHARACTER", "LOCATION", "PLOT_POINT", "THEME", "CONFLICT",
                  "WORLD_BUILDING", "DIALOGUE", "RELATIONSHIP", "OBJECT", "RULE"]


def _session_to_response(session) -> BrainDumpSessionResponse:
    return BrainDumpSessionResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        title=session.title,
        raw_text=session.raw_text,
        state=session.state,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
    )


def _mock_organize_raw_text(raw_text: str) -> dict[str, list[str]]:
    """Organize raw brain dump text into categories.

    TODO: Replace with LLM-based NLP pipeline.
    Current logic: split by double-newlines, round-robin assign to categories.
    """
    blocks = [b.strip() for b in raw_text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [raw_text.strip()] if raw_text.strip() else []

    result: dict[str, list[str]] = {}
    for i, block in enumerate(blocks):
        category = _CATEGORY_KEYS[i % len(_CATEGORY_KEYS)]
        result.setdefault(category, []).append(block)
    return result
