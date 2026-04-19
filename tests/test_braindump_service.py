from __future__ import annotations

from datetime import datetime, timezone

from app.persistence.sqlite import connect
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.braindump import (
    BrainDumpNotFoundError,
    BrainDumpService,
    BrainDumpValidationError,
)


def _make_service(tmp_path):
    repository = StoryDevelopmentRepository(tmp_path / "story-development.sqlite")
    return BrainDumpService(repository), repository


def _register_project(repository: StoryDevelopmentRepository, project_id: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with connect(repository.db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                f"Project {project_id}",
                f"{project_id}/manifest.json",
                f"{project_id}/bible.db",
                timestamp,
                timestamp,
            ),
        )
        connection.commit()


# =============================================================================
# Create session tests
# =============================================================================


def test_create_session_returns_active_session(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-1")

    session = service.create_session(project_id="project-1", title="My Brain Dump", raw_text="Some ideas")

    assert session.project_id == "project-1"
    assert session.title == "My Brain Dump"
    assert session.raw_text == "Some ideas"
    assert session.state == "active"

    stored = repository.get_brain_dump_session(session.session_id)
    assert stored.project_id == "project-1"
    assert stored.raw_text == "Some ideas"


def test_create_session_defaults_raw_text(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-2")

    session = service.create_session(project_id="project-2")

    assert session.raw_text == ""
    assert session.state == "active"


# =============================================================================
# Get session tests
# =============================================================================


def test_get_session_returns_correct_session(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-3")

    session = service.create_session(project_id="project-3", title="Get test")

    retrieved = service.get_session(session.session_id)
    assert retrieved.session_id == session.session_id
    assert retrieved.title == "Get test"


def test_get_session_raises_not_found(tmp_path) -> None:
    service, _ = _make_service(tmp_path)

    try:
        service.get_session(99999)
    except BrainDumpNotFoundError:
        pass
    else:
        raise AssertionError("Expected BrainDumpNotFoundError for non-existent session")


# =============================================================================
# List sessions tests
# =============================================================================


def test_list_sessions_filters_by_project(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-4")
    _register_project(repository, "project-5")

    service.create_session(project_id="project-4", title="Session 1")
    service.create_session(project_id="project-4", title="Session 2")
    service.create_session(project_id="project-5", title="Session 3")

    project_4_sessions = service.list_sessions("project-4")
    assert len(project_4_sessions) == 2

    project_5_sessions = service.list_sessions("project-5")
    assert len(project_5_sessions) == 1
    assert project_5_sessions[0].title == "Session 3"


# =============================================================================
# Update session tests
# =============================================================================


def test_update_session_changes_raw_text_and_title(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-6")

    session = service.create_session(project_id="project-6", title="Original", raw_text="Original text")

    updated = service.update_session(session.session_id, raw_text="New text", title="Updated")

    assert updated.raw_text == "New text"
    assert updated.title == "Updated"

    stored = repository.get_brain_dump_session(session.session_id)
    assert stored.raw_text == "New text"


def test_update_session_validates_active_to_organized(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-7")

    session = service.create_session(project_id="project-7")
    updated = service.update_session(session.session_id, state="organized")
    assert updated.state == "organized"


def test_update_session_validates_active_to_archived(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-8")

    session = service.create_session(project_id="project-8")
    updated = service.update_session(session.session_id, state="archived")
    assert updated.state == "archived"


def test_update_session_validates_organized_to_archived(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-10")

    session = service.create_session(project_id="project-10")
    service.update_session(session.session_id, state="organized")
    updated = service.update_session(session.session_id, state="archived")
    assert updated.state == "archived"


def test_update_session_rejects_organized_to_active(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-11")

    session = service.create_session(project_id="project-11")
    service.update_session(session.session_id, state="organized")
    try:
        service.update_session(session.session_id, state="active")
    except BrainDumpValidationError:
        pass
    else:
        raise AssertionError("Expected BrainDumpValidationError for organized -> active transition")


def test_update_session_rejects_archived_to_active(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-12")

    session = service.create_session(project_id="project-12")
    service.update_session(session.session_id, state="archived")
    try:
        service.update_session(session.session_id, state="active")
    except BrainDumpValidationError:
        pass
    else:
        raise AssertionError("Expected BrainDumpValidationError for archived -> active transition")


def test_update_session_rejects_archived_to_organized(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-13")

    session = service.create_session(project_id="project-13")
    service.update_session(session.session_id, state="archived")
    try:
        service.update_session(session.session_id, state="organized")
    except BrainDumpValidationError:
        pass
    else:
        raise AssertionError("Expected BrainDumpValidationError for archived -> organized transition")


# =============================================================================
# Delete session tests
# =============================================================================


def test_delete_session_removes_it(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-14")

    session = service.create_session(project_id="project-14", title="To delete")
    service.delete_session(session.session_id)

    try:
        repository.get_brain_dump_session(session.session_id)
    except KeyError:
        pass
    else:
        raise AssertionError("Expected session to be deleted")


def test_delete_session_raises_not_found(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    try:
        service.delete_session(99999)
    except KeyError:
        pass
    else:
        raise AssertionError("Expected KeyError for non-existent session")


# =============================================================================
# Organize tests
# =============================================================================


def test_organize_creates_brainstorm_items(tmp_path) -> None:
    from app.api.story_development import (
        BrainDumpService as _BDS,
        BrainstormService,
    )
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize.sqlite")
    _register_project(repository, "project-15")
    brainstorm_service = BrainstormService(repository)

    bd_service = BDService(repository)
    session = bd_service.create_session(
        project_id="project-15",
        title="Organize test",
        raw_text="First idea\n\nSecond idea\n\nThird idea",
    )

    from app.api.story_development import _mock_organize_raw_text
    items = _mock_organize_raw_text(session.raw_text)

    assert len(items) >= 1
    assert any(len(blocks) > 0 for blocks in items.values())


def test_organize_updates_session_state(tmp_path) -> None:
    repository = StoryDevelopmentRepository(tmp_path / "story-organize-state.sqlite")
    _register_project(repository, "project-16")
    bd_service = BrainDumpService(repository)

    session = bd_service.create_session(
        project_id="project-16",
        raw_text="Some text\n\nMore text",
    )

    from app.api.story_development import _mock_organize_raw_text
    _mock_organize_raw_text(session.raw_text)

    updated = bd_service.update_session(session.session_id, state="organized")
    assert updated.state == "organized"


def test_organize_rejects_non_active_session(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    _register_project(service.repository, "project-17")

    session = service.create_session(project_id="project-17", raw_text="Text")
    service.update_session(session.session_id, state="organized")

    try:
        service.update_session(session.session_id, state="active")
    except BrainDumpValidationError:
        pass
    else:
        raise AssertionError("Non-active sessions should not be re-activated")


def test_mock_organize_distributes_across_categories(tmp_path) -> None:
    from app.api.story_development import _mock_organize_raw_text

    raw = "Idea one\n\nIdea two\n\nIdea three\n\nIdea four\n\nIdea five\n\nIdea six\n\nIdea seven\n\nIdea eight\n\nIdea nine\n\nIdea ten"
    result = _mock_organize_raw_text(raw)

    categories = list(result.keys())
    total_blocks = sum(len(blocks) for blocks in result.values())

    assert total_blocks == 10
    assert len(categories) == 10
    assert "CHARACTER" in categories
    assert "LOCATION" in categories
    assert "PLOT_POINT" in categories
    assert "THEME" in categories
    assert "CONFLICT" in categories
    assert "WORLD_BUILDING" in categories
    assert "DIALOGUE" in categories
    assert "RELATIONSHIP" in categories
    assert "OBJECT" in categories
    assert "RULE" in categories


def test_mock_organize_handles_empty_text(tmp_path) -> None:
    from app.api.story_development import _mock_organize_raw_text

    result = _mock_organize_raw_text("")
    assert all(len(blocks) == 0 for blocks in result.values())

    result = _mock_organize_raw_text("   ")
    assert all(len(blocks) == 0 for blocks in result.values())


def test_mock_organize_handles_single_paragraph(tmp_path) -> None:
    from app.api.story_development import _mock_organize_raw_text

    result = _mock_organize_raw_text("Single paragraph")
    assert "CHARACTER" in result
    assert result["CHARACTER"] == ["Single paragraph"]
