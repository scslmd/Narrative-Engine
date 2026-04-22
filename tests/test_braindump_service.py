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
# Organize tests (LLM-based)
# =============================================================================


def _make_mock_inferencer(json_response: str) -> object:
    class MockDescriptor:
        default_model = "test-model"
    class MockInferencer:
        descriptor = MockDescriptor()
        def generate_text(self, request: object) -> object:
            return type('Resp', (), {'content': json_response})()
    return MockInferencer()


class _MockBrainstormService:
    def __init__(self, repository: object) -> None:
        self.repository = repository
        self._counter = 0
        self._items: list[object] = []

    def capture_brainstorm_item(self, project_id: str, content: str, status: str, tags: list[str]) -> object:
        self._counter += 1
        item = type('BrainstormItem', (), {
            'item_id': f'brain-{self._counter}',
            'project_id': project_id,
            'content': content,
            'status': status,
            'tags': tags,
            'source_notes': None,
        })()
        self._items.append(item)
        return item


def test_organize_with_llm_returns_categorized_items(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-llm.sqlite")
    _register_project(repository, "project-20")
    brainstorm_svc = _MockBrainstormService(repository)

    mock_inferencer = _make_mock_inferencer(
        '{"character": ["Alice is brave"], "location": ["The castle"], '
        '"plot_point": [], "theme": [], "conflict": [], "world_building": [], '
        '"dialogue": [], "relationship": [], "object": [], "rule": []}'
    )

    bd_service = BDService(repository, inferencer=mock_inferencer)
    session = bd_service.create_session(
        project_id="project-20",
        raw_text="Alice is brave and lives in the castle.",
    )

    result = bd_service.organize(
        session.session_id,
        "project-20",
        brainstorm_service=brainstorm_svc,
    )

    assert len(result) >= 2
    assert "character" in result
    assert len(result["character"]) >= 1
    assert result["character"][0].content == "Alice is brave"


def test_organize_with_llm_parses_json_response(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-json.sqlite")
    _register_project(repository, "project-21")
    brainstorm_svc = _MockBrainstormService(repository)

    mock_inferencer = _make_mock_inferencer(
        'Here is your result:\n```json\n{"theme": ["honor"], "conflict": ["internal struggle"], '
        '"character": ["Bob"], "location": [], "plot_point": [], "world_building": [], '
        '"dialogue": [], "relationship": [], "object": [], "rule": []}\n```'
    )

    bd_service = BDService(repository, inferencer=mock_inferencer)
    session = bd_service.create_session(
        project_id="project-21",
        raw_text="Some ideas about honor and conflict.",
    )

    result = bd_service.organize(
        session.session_id,
        "project-21",
        brainstorm_service=brainstorm_svc,
    )

    assert "theme" in result
    assert "conflict" in result
    assert "character" in result


def test_organize_creates_brainstorm_items(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-items.sqlite")
    _register_project(repository, "project-22")
    brainstorm_svc = _MockBrainstormService(repository)

    mock_inferencer = _make_mock_inferencer(
        '{"character": ["Alice", "Bob"], "location": ["The castle"], '
        '"plot_point": ["The betrayal"], "theme": [], "conflict": [], "world_building": [], '
        '"dialogue": [], "relationship": [], "object": [], "rule": []}'
    )

    bd_service = BDService(repository, inferencer=mock_inferencer)
    session = bd_service.create_session(
        project_id="project-22",
        raw_text="Alice, Bob, the castle, the betrayal.",
    )

    result = bd_service.organize(
        session.session_id,
        "project-22",
        brainstorm_service=brainstorm_svc,
    )

    total_items = sum(len(items) for items in result.values())
    assert total_items == 4
    for items in result.values():
        for item in items:
            assert item.project_id == "project-22"
            assert len(item.tags) == 1


def test_organize_updates_session_state(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-state2.sqlite")
    _register_project(repository, "project-23")
    brainstorm_svc = _MockBrainstormService(repository)

    mock_inferencer = _make_mock_inferencer(
        '{"character": ["Test"], "location": [], "plot_point": [], "theme": [], '
        '"conflict": [], "world_building": [], "dialogue": [], "relationship": [], '
        '"object": [], "rule": []}'
    )

    bd_service = BDService(repository, inferencer=mock_inferencer)
    session = bd_service.create_session(
        project_id="project-23",
        raw_text="Test text",
    )

    assert session.state == "active"

    bd_service.organize(
        session.session_id,
        "project-23",
        brainstorm_service=brainstorm_svc,
    )

    updated = bd_service.get_session(session.session_id)
    assert updated.state == "organized"


def test_organize_raises_when_no_inferencer(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService, BrainDumpOrganizeError

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-no-inferencer.sqlite")
    _register_project(repository, "project-24")

    bd_service = BDService(repository, inferencer=None)
    session = bd_service.create_session(
        project_id="project-24",
        raw_text="Some text",
    )

    try:
        bd_service.organize(
            session.session_id,
            "project-24",
            brainstorm_service=_MockBrainstormService(repository),
        )
    except BrainDumpOrganizeError as exc:
        assert "LLM inference is not configured" in str(exc)
    else:
        raise AssertionError("Should raise BrainDumpOrganizeError without inferencer")


def test_organize_rejects_non_active_session(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-inactive.sqlite")
    _register_project(repository, "project-25")

    bd_service = BDService(repository)
    session = bd_service.create_session(
        project_id="project-25",
        raw_text="Text",
    )

    bd_service.update_session(session.session_id, state="organized")

    mock_inferencer = _make_mock_inferencer(
        '{"character": [], "location": [], "plot_point": [], "theme": [], '
        '"conflict": [], "world_building": [], "dialogue": [], "relationship": [], '
        '"object": [], "rule": []}'
    )
    bd_service._inferencer = mock_inferencer

    try:
        bd_service.organize(
            session.session_id,
            "project-25",
            brainstorm_service=_MockBrainstormService(repository),
        )
    except BrainDumpValidationError:
        pass
    else:
        raise AssertionError("Non-active sessions should not be organized")


def test_organize_validates_missing_keys(tmp_path) -> None:
    from app.services.braindump import BrainDumpService as BDService, BrainDumpOrganizeError

    repository = StoryDevelopmentRepository(tmp_path / "story-organize-validate.sqlite")
    _register_project(repository, "project-26")
    brainstorm_svc = _MockBrainstormService(repository)

    mock_inferencer = _make_mock_inferencer('{"character": ["Test"]}')

    bd_service = BDService(repository, inferencer=mock_inferencer)
    session = bd_service.create_session(
        project_id="project-26",
        raw_text="Incomplete JSON",
    )

    try:
        bd_service.organize(
            session.session_id,
            "project-26",
            brainstorm_service=brainstorm_svc,
        )
    except BrainDumpOrganizeError as exc:
        assert "missing required keys" in str(exc)
    else:
        raise AssertionError("Should raise BrainDumpOrganizeError for invalid JSON")


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
