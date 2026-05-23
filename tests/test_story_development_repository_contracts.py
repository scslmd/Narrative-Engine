from __future__ import annotations

import importlib


def test_story_development_repository_import_surface_stable() -> None:
    module = importlib.import_module("app.persistence.story_development")
    assert hasattr(module, "StoryDevelopmentRepository")
    assert hasattr(module, "DraftArtifactRecord")
    assert hasattr(module, "ManuscriptDocumentRecord")
    assert hasattr(module, "StoryboardCardRecord")


def test_story_development_contracts_module_exports_protocols() -> None:
    contracts = importlib.import_module("app.persistence.story_development.contracts")
    assert hasattr(contracts, "PlanningRepository")
    assert hasattr(contracts, "BranchingRepository")
    assert hasattr(contracts, "ReviewRepository")
    assert hasattr(contracts, "DraftingRepository")
    assert hasattr(contracts, "GenerationRepository")
    assert hasattr(contracts, "ManuscriptAssistRepository")
    assert hasattr(contracts, "CanonRepository")
    assert hasattr(contracts, "LibraryRepository")


def test_story_development_domain_modules_are_importable() -> None:
    importlib.import_module("app.persistence.story_development.planning")
    importlib.import_module("app.persistence.story_development.branching")
    importlib.import_module("app.persistence.story_development.review")
    importlib.import_module("app.persistence.story_development.drafting")
    importlib.import_module("app.persistence.story_development.generation")
    importlib.import_module("app.persistence.story_development.manuscript_assist")
    importlib.import_module("app.persistence.story_development.canon")
    importlib.import_module("app.persistence.story_development.libraries")
