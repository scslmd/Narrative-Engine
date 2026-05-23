from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.services.drafting import DraftingService
from app.services.planning import PlanningService
from app.services.review_routing import ReviewRoutingService
from app.services.story_branching import StoryBranchingService


def build_planning_service(repository: StoryDevelopmentRepository) -> PlanningService:
    return PlanningService(repository)


def build_drafting_service(repository: StoryDevelopmentRepository) -> DraftingService:
    return DraftingService(repository)


def build_branching_service(repository: StoryDevelopmentRepository) -> StoryBranchingService:
    return StoryBranchingService(repository)


def build_review_routing_service(repository: StoryDevelopmentRepository) -> ReviewRoutingService:
    return ReviewRoutingService(repository)


__all__ = [
    "build_branching_service",
    "build_drafting_service",
    "build_planning_service",
    "build_review_routing_service",
]
