from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas import (
    BeatPlan,
    ChapterPacket,
    ChapterPlan,
    CheckerFinding,
    DraftArtifact,
    InspectRunLink,
    ManuscriptDocument,
    PlanningDependency,
    ReviewDecision,
    RevisionSuggestion,
    ScenePlan,
    SequencePlan,
    StoryDecisionNode,
)
from app.schemas.base import StrictModel


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


class BeatPlanListResponse(StrictModel):
    project_id: str
    items: list[BeatPlan] = Field(default_factory=list)
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

