from __future__ import annotations

from fastapi import APIRouter

from app.persistence.story_development import StoryDevelopmentRepository
from app.services.braindump import BrainDumpService
from app.services.brainstorm import BrainstormService
from app.services.relationship_extraction import RelationshipExtractionService
from app.services.drafting import DraftingService
from app.services.manuscript_review import ManuscriptReviewService
from app.services.editable_flow import EditableFlowService
from app.services.editable_flow_persistence import SQLiteEditableFlowRepository
from app.services.foundation import FoundationService
from app.services.planning import PlanningService
from app.services.review_routing import ReviewRoutingService
from app.services.story_branching import StoryBranchingService
from app.services.story_decision_review import StoryDecisionReviewService
from app.services.story_knowledge import StoryKnowledgeService
from app.services.chapter_packets import ChapterPacketService
from app.services.sequence_plans import SequencePlanService
from app.services.storyboard_cards import StoryboardCardService
from .arcs import register_arc_routes
from .braindump import register_braindump_routes
from .brainstorm import register_brainstorm_routes
from .branches import register_branch_routes
from .characters import register_character_routes
from .drafting import register_drafting_routes
from .flow import register_flow_routes
from .foundation import register_foundation_routes
from .planning import register_planning_routes
from .review import register_review_routes
from .storyboard import register_storyboard_routes
from .world_bible import register_world_bible_routes


def build_story_development_router(
    repository: StoryDevelopmentRepository,
    prefix: str = "/story-development",
    inferencer: object | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix.rstrip("/") if prefix else "", tags=["story-development"])

    # Instantiate services
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
    braindump_service = BrainDumpService(repository, inferencer=inferencer)
    foundation_service = FoundationService(repository)
    story_knowledge_service = StoryKnowledgeService(repository)
    relationship_extraction_service = RelationshipExtractionService(
        story_knowledge_service=story_knowledge_service,
        inferencer=inferencer,
    )
    chapter_packet_service = ChapterPacketService(repository)
    sequence_plan_service = SequencePlanService(repository)
    storyboard_card_service = StoryboardCardService(repository)

    # Register domain routes
    register_branch_routes(router, branching_service)
    register_flow_routes(router, flow_service)
    register_foundation_routes(router, foundation_service)
    register_brainstorm_routes(router, brainstorm_service, repository)
    register_braindump_routes(router, braindump_service, brainstorm_service)
    register_character_routes(router, story_knowledge_service, relationship_extraction_service)
    register_world_bible_routes(router, story_knowledge_service)
    register_arc_routes(router, story_knowledge_service)
    register_review_routes(router, decision_service, review_service)
    register_planning_routes(router, planning_service, chapter_packet_service, sequence_plan_service, repository)
    register_drafting_routes(router, drafting_service, manuscript_review_service)
    register_storyboard_routes(router, storyboard_card_service)

    return router
