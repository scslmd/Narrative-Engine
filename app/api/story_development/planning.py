from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import BeatPlan, ChapterPacket, ChapterPlan, PlanningDependency, ScenePlan, SequencePlan
from app.schemas.base import StrictModel
from app.services.chapter_packets import (
    ChapterPacketNotFoundError,
    ChapterPacketService,
    ChapterPacketValidationError,
)
from app.services.planning import PlanningNotFoundError, PlanningService, PlanningValidationError
from app.services.sequence_plans import (
    SequencePlanNotFoundError,
    SequencePlanService,
    SequencePlanValidationError,
)
from pydantic import Field


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


class PlanningDependencyCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    dependency_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    upstream_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    downstream_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    dependency_kind: str = Field(..., min_length=1, max_length=100)
    reason: str | None = Field(None, max_length=5000)


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


class PlanningReorderRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    plan_kind: str = Field(..., min_length=1, max_length=20)
    ordered_plan_ids: list[str] = Field(..., min_length=1)


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


def _get_beat_plan_record(beat_id: str, repository: object) -> "app.persistence.story_development.BeatPlanRecord":
    from app.persistence.story_development import BeatPlanRecord
    return repository.get_beat_plan(beat_id)


def _list_beat_plans_for_project(project_id: str, repository: object) -> list["app.persistence.story_development.BeatPlanRecord"]:
    return repository.list_beat_plans(project_id)


def _upsert_beat_plan(
    repository: object,
    *,
    beat_id: str,
    project_id: str,
    objective: str,
    conflict: str,
    stakes: str,
    arc_stage: str,
    active_character_ids: list[str] | None = None,
    continuity_requirements: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
    status: str = "draft",
    position: int | None = None,
) -> "app.persistence.story_development.BeatPlanRecord":
    pos = position if position is not None else len(repository.list_beat_plans(project_id))
    return repository.upsert_beat_plan(
        beat_id=beat_id,
        project_id=project_id,
        objective=objective,
        conflict=conflict,
        stakes=stakes,
        dependency_ids=None,
        arc_stage=arc_stage,
        active_character_ids=active_character_ids or [],
        continuity_requirements=continuity_requirements or [],
        unresolved_questions=unresolved_questions or [],
        status=status,
        position=pos,
    )


def _beat_plan_to_schema(record: "app.persistence.story_development.BeatPlanRecord") -> BeatPlan:
    return BeatPlan(
        beat_id=record.beat_id,
        project_id=record.project_id,
        objective=record.objective,
        conflict=record.conflict,
        stakes=record.stakes,
        dependency_ids=list(record.dependency_ids),
        arc_stage=record.arc_stage,
        active_character_ids=list(record.active_character_ids),
        continuity_requirements=list(record.continuity_requirements),
        unresolved_questions=list(record.unresolved_questions),
        status=record.status,
    )


def _get_beat_plan_schema(beat_id: str, repository: object) -> BeatPlan:
    record = _get_beat_plan_record(beat_id, repository)
    return _beat_plan_to_schema(record)


__all__ = [
    "BeatPlanCreateRequest",
    "BeatPlanUpdateRequest",
    "ChapterPacketCreateRequest",
    "ChapterPacketUpdateRequest",
    "ChapterPlanCreateRequest",
    "ChapterPlanUpdateRequest",
    "PlanningDependencyCreateRequest",
    "PlanningReorderRequest",
    "ScenePlanCreateRequest",
    "ScenePlanUpdateRequest",
    "SequencePlanCreateRequest",
    "SequencePlanUpdateRequest",
    "_packet_to_schema",
    "_sequence_to_schema",
    "register_planning_routes",
]


def register_planning_routes(
    router: APIRouter,
    planning_service: PlanningService,
    chapter_packet_service: ChapterPacketService,
    sequence_plan_service: SequencePlanService,
    repository: object,
) -> None:
    @router.get("/planning/sequence-plans", response_model=None)
    def list_sequence_plans(project_id: str):
        from app.api.story_development.common_models import SequencePlanListResponse
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

    @router.get("/planning/chapter-plans", response_model=None)
    def list_chapter_plans(project_id: str):
        from app.api.story_development.common_models import ChapterPlanListResponse
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

    @router.get("/planning/scene-plans", response_model=None)
    def list_scene_plans(project_id: str):
        from app.api.story_development.common_models import ScenePlanListResponse
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

    @router.post("/planning/chapter-plans", response_model=ChapterPlan, status_code=201)
    def create_chapter_plan(payload: ChapterPlanCreateRequest) -> ChapterPlan:
        """Create a new chapter plan."""
        try:
            plan = planning_service.create_chapter_plan(
                project_id=payload.project_id,
                chapter_id=payload.chapter_id,
                title=payload.title,
                summary=payload.summary or "",
                objective=payload.objective,
                conflict=payload.conflict,
                stakes=payload.stakes,
                sequence_id=payload.sequence_id,
                active_character_ids=payload.active_character_ids,
                continuity_requirements=payload.continuity_requirements,
                unresolved_questions=payload.unresolved_questions,
                status=payload.status,
                position=payload.position,
            )
            return plan
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PlanningValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/planning/chapter-plans/{chapter_id}", response_model=ChapterPlan)
    def update_chapter_plan(
        chapter_id: str,
        project_id: str,
        payload: ChapterPlanUpdateRequest,
    ) -> ChapterPlan:
        """Update an existing chapter plan."""
        try:
            existing = planning_service.get_chapter_plan(project_id, chapter_id=chapter_id)
        except PlanningNotFoundError:
            raise HTTPException(status_code=404, detail="Chapter plan not found.")
        
        title = payload.title if payload.title is not None else existing.title
        summary = payload.summary if payload.summary is not None else existing.summary
        objective = payload.objective if payload.objective is not None else existing.objective
        conflict = payload.conflict if payload.conflict is not None else existing.conflict
        stakes = payload.stakes if payload.stakes is not None else existing.stakes
        active_character_ids = payload.active_character_ids if payload.active_character_ids is not None else list(existing.active_character_ids)
        continuity_requirements = payload.continuity_requirements if payload.continuity_requirements is not None else list(existing.continuity_requirements)
        unresolved_questions = payload.unresolved_questions if payload.unresolved_questions is not None else list(existing.unresolved_questions)
        status = payload.status if payload.status is not None else existing.status
        position = payload.position if payload.position is not None else existing.position
        
        plan = planning_service.create_chapter_plan(
            project_id=project_id,
            chapter_id=chapter_id,
            title=title,
            summary=summary,
            objective=objective,
            conflict=conflict,
            stakes=stakes,
            sequence_id=existing.sequence_id,
            active_character_ids=active_character_ids,
            continuity_requirements=continuity_requirements,
            unresolved_questions=unresolved_questions,
            status=status,
            position=position,
        )
        return plan

    @router.post("/planning/scene-plans", response_model=ScenePlan, status_code=201)
    def create_scene_plan(payload: ScenePlanCreateRequest) -> ScenePlan:
        """Create a new scene plan."""
        try:
            plan = planning_service.create_scene_plan(
                project_id=payload.project_id,
                scene_id=payload.scene_id,
                title=payload.title,
                summary=payload.summary or "",
                objective=payload.objective,
                conflict=payload.conflict,
                stakes=payload.stakes,
                chapter_id=payload.chapter_id,
                active_character_ids=payload.active_character_ids,
                continuity_requirements=payload.continuity_requirements,
                unresolved_questions=payload.unresolved_questions,
                status=payload.status,
                position=payload.position,
            )
            return plan
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PlanningValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/planning/scene-plans/{scene_id}", response_model=ScenePlan)
    def update_scene_plan(
        scene_id: str,
        project_id: str,
        payload: ScenePlanUpdateRequest,
    ) -> ScenePlan:
        """Update an existing scene plan."""
        try:
            existing = planning_service.get_scene_plan(project_id, scene_id=scene_id)
        except PlanningNotFoundError:
            raise HTTPException(status_code=404, detail="Scene plan not found.")
        
        title = payload.title if payload.title is not None else existing.title
        summary = payload.summary if payload.summary is not None else existing.summary
        objective = payload.objective if payload.objective is not None else existing.objective
        conflict = payload.conflict if payload.conflict is not None else existing.conflict
        stakes = payload.stakes if payload.stakes is not None else existing.stakes
        active_character_ids = payload.active_character_ids if payload.active_character_ids is not None else list(existing.active_character_ids)
        continuity_requirements = payload.continuity_requirements if payload.continuity_requirements is not None else list(existing.continuity_requirements)
        unresolved_questions = payload.unresolved_questions if payload.unresolved_questions is not None else list(existing.unresolved_questions)
        status = payload.status if payload.status is not None else existing.status
        position = payload.position if payload.position is not None else existing.position
        
        plan = planning_service.create_scene_plan(
            project_id=project_id,
            scene_id=scene_id,
            title=title,
            summary=summary,
            objective=objective,
            conflict=conflict,
            stakes=stakes,
            chapter_id=existing.chapter_id,
            active_character_ids=active_character_ids,
            continuity_requirements=continuity_requirements,
            unresolved_questions=unresolved_questions,
            status=status,
            position=position,
        )
        return plan

    @router.get("/planning/beat-plans", response_model=None)
    def list_beat_plans(project_id: str):
        from app.api.story_development.common_models import BeatPlanListResponse
        return BeatPlanListResponse(
            project_id=project_id,
            items=list(_list_beat_plans_for_project(project_id, repository)),
            meta={"ordered_by": "position_asc"},
        )

    @router.get("/planning/beat-plans/{beat_id}", response_model=BeatPlan)
    def get_beat_plan(beat_id: str, project_id: str) -> BeatPlan:
        try:
            return _get_beat_plan_schema(beat_id, repository)
        except KeyError:
            raise HTTPException(status_code=404, detail="Beat plan not found.")

    @router.post("/planning/beat-plans", response_model=BeatPlan, status_code=201)
    def create_beat_plan(payload: BeatPlanCreateRequest) -> BeatPlan:
        """Create a new beat plan."""
        try:
            plan = _upsert_beat_plan(
                repository,
                beat_id=payload.beat_id,
                project_id=payload.project_id,
                objective=payload.objective,
                conflict=payload.conflict,
                stakes=payload.stakes,
                arc_stage=payload.arc_stage or "unspecified",
                active_character_ids=payload.active_character_ids,
                continuity_requirements=payload.continuity_requirements,
                unresolved_questions=payload.unresolved_questions,
                status=payload.status,
                position=payload.position if payload.position is not None else None,
            )
            return _beat_plan_to_schema(plan)
        except PlanningValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/planning/beat-plans/{beat_id}", response_model=BeatPlan)
    def update_beat_plan(
        beat_id: str,
        project_id: str,
        payload: BeatPlanUpdateRequest,
    ) -> BeatPlan:
        """Update an existing beat plan."""
        try:
            existing = _get_beat_plan_record(beat_id, repository)
        except KeyError:
            raise HTTPException(status_code=404, detail="Beat plan not found.")
        
        objective = payload.objective if payload.objective is not None else existing.objective
        conflict = payload.conflict if payload.conflict is not None else existing.conflict
        stakes = payload.stakes if payload.stakes is not None else existing.stakes
        arc_stage = payload.arc_stage if payload.arc_stage is not None else existing.arc_stage
        active_character_ids = payload.active_character_ids if payload.active_character_ids is not None else list(existing.active_character_ids)
        continuity_requirements = payload.continuity_requirements if payload.continuity_requirements is not None else list(existing.continuity_requirements)
        unresolved_questions = payload.unresolved_questions if payload.unresolved_questions is not None else list(existing.unresolved_questions)
        status = payload.status if payload.status is not None else existing.status
        position = payload.position if payload.position is not None else existing.position
        
        plan = _upsert_beat_plan(
            repository,
            beat_id=beat_id,
            project_id=existing.project_id,
            objective=objective,
            conflict=conflict,
            stakes=stakes,
            arc_stage=arc_stage,
            active_character_ids=active_character_ids,
            continuity_requirements=continuity_requirements,
            unresolved_questions=unresolved_questions,
            status=status,
            position=position,
        )
        return _beat_plan_to_schema(plan)

    @router.get("/planning/dependencies", response_model=None)
    def list_planning_dependencies(project_id: str):
        from app.api.story_development.common_models import PlanningDependencyListResponse
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

    @router.get("/planning/chapter-packets", response_model=None)
    def list_chapter_packets(project_id: str):
        from app.api.story_development.common_models import ChapterPacketListResponse
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

    @router.post("/planning/reorder", response_model=None)
    def reorder_plan_objects(payload: PlanningReorderRequest):
        """Reorder sequences, chapters, or scene plans."""
        from app.api.story_development.common_models import PlanningDependencyListResponse
        try:
            if payload.plan_kind not in ("sequence", "chapter", "scene"):
                raise HTTPException(status_code=400, detail="plan_kind must be 'sequence', 'chapter', or 'scene'.")
            if payload.plan_kind == "sequence":
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="sequence", ordered_plan_ids=payload.ordered_plan_ids)
            elif payload.plan_kind == "chapter":
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="chapter", ordered_plan_ids=payload.ordered_plan_ids)
            else:
                planning_service.reorder_plan_objects(payload.project_id, plan_kind="scene", ordered_plan_ids=payload.ordered_plan_ids)
            return PlanningDependencyListResponse(
                project_id=payload.project_id,
                items=[],
                meta={"reordered_kind": payload.plan_kind, "ordered_count": str(len(payload.ordered_plan_ids))},
            )
        except PlanningValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PlanningNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"{payload.plan_kind} plan not found.") from exc

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
