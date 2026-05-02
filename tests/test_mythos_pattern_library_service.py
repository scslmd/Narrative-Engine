from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.mythos_library import MythosEntryCreateRequest
from app.schemas.pattern_library import PatternEntryCreateRequest
from app.schemas.projects import ProjectCreateRequest
from app.services.mythos_library import MythosLibraryService
from app.services.pattern_library import PatternLibraryService
from app.services.projects import ProjectService


def _setup(tmp_path):
    project_service = ProjectService(tmp_path)
    project_service.create_project(
        ProjectCreateRequest(
            project_id="project-1",
            project_name="Project One",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    repository = StoryDevelopmentRepository(tmp_path / "data" / "state" / "narrative_ops.db")
    return repository


def test_mythos_service_create_and_list(tmp_path) -> None:
    repository = _setup(tmp_path)
    service = MythosLibraryService(repository)
    service.create_entry(
        MythosEntryCreateRequest(
            project_id="project-1",
            entry_type="motif",
            name="Storm Crown",
        )
    )
    items = service.list_entries("project-1")
    assert len(items) == 1
    assert items[0].name == "Storm Crown"


def test_pattern_service_create_and_list(tmp_path) -> None:
    repository = _setup(tmp_path)
    service = PatternLibraryService(repository)
    service.create_entry(
        PatternEntryCreateRequest(
            project_id="project-1",
            pattern_type="plot",
            name="Hero Return",
        )
    )
    items = service.list_entries("project-1")
    assert len(items) == 1
    assert items[0].name == "Hero Return"
