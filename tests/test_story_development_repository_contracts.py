from __future__ import annotations

import importlib


def test_repository_import_surface_and_contracts() -> None:
    module = importlib.import_module("app.persistence.story_development")
    assert hasattr(module, "StoryDevelopmentRepository")
    assert hasattr(module, "DraftArtifactRecord")
    assert hasattr(module, "ManuscriptDocumentRecord")
    assert hasattr(module, "StoryboardCardRecord")

    contracts = importlib.import_module("app.persistence.story_development.contracts")
    for name in ("PlanningRepository", "BranchingRepository", "ReviewRepository",
                 "DraftingRepository", "GenerationRepository", "ManuscriptAssistRepository",
                 "CanonRepository", "LibraryRepository"):
        assert hasattr(contracts, name)

    for name in ("planning", "branching", "review", "drafting", "generation",
                 "manuscript_assist", "canon", "libraries"):
        importlib.import_module(f"app.persistence.story_development.{name}")
