from __future__ import annotations

import pytest

from app.persistence.sqlite import ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonGenerationRequest,
    CanonScope,
    DestinationKind,
    GenerationDestination,
    GenerationMode,
)
from app.schemas.projects import ProjectCreateRequest
from app.services.canon_packet_builder import CanonPacketBuilder
from app.services.job_manager import JobManager
from app.services.projects import ProjectService
from app.services.story_forking import StoryForkingService
from app.services.story_generation_orchestrator import StoryGenerationOrchestrator


def _setup(tmp_path) -> tuple[StoryDevelopmentRepository, ProjectService, JobManager, StoryGenerationOrchestrator]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)
    ensure_operations_db(db_path)
    project_service = ProjectService(tmp_path)
    project_service.create_project(
        ProjectCreateRequest(
            project_id="source-project",
            project_name="Source",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="A kingdom in decline.",
        logline="A disgraced knight returns home.",
    )
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    forking = StoryForkingService(repository=repo, project_service=project_service)
    job_manager = JobManager(db_path)
    orchestrator = StoryGenerationOrchestrator(
        repository=repo,
        project_service=project_service,
        packet_builder=builder,
        forking_service=forking,
        job_manager=job_manager,
    )
    return repo, project_service, job_manager, orchestrator


def _same_project_request(brief: str = "Generate a side story.", idempotency_key: str | None = None) -> CanonGenerationRequest:
    return CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        destination=GenerationDestination(
            destination_kind=DestinationKind.SAME_PROJECT,
            target_project_id="source-project",
        ),
        canon_scope=CanonScope(source_project_id="source-project", character_ids=["char-1"]),
        generation_brief=brief,
        target_chapter_count=2,
        idempotency_key=idempotency_key,
    )


def test_story_generation_orchestrator_submits_jobs(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    assert response.generation_id
    assert response.job_ids


def test_get_generation_returns_run_after_submit(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    fetched = orchestrator.get_generation(response.generation_id)
    assert fetched.generation_id == response.generation_id
    assert fetched.source_project_id == "source-project"
    assert fetched.target_project_id == "source-project"


def test_get_generation_raises_keyerror_for_nonexistent(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    with pytest.raises(KeyError):
        orchestrator.get_generation("nonexistent-id")


def test_list_generations_returns_source_runs(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    orchestrator.submit_generation(_same_project_request())
    runs = orchestrator.list_generations("source-project")
    assert len(runs) >= 1
    assert any(r.source_project_id == "source-project" for r in runs)


def test_list_generations_returns_target_runs(tmp_path) -> None:
    repo, project_service, job_manager, orchestrator = _setup(tmp_path)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked Story",
        ),
        canon_scope=CanonScope(source_project_id="source-project", character_ids=["char-1"]),
        generation_brief="Fork and generate.",
        target_chapter_count=1,
    )
    response = orchestrator.submit_generation(request)
    runs = orchestrator.list_generations(response.target_project_id)
    assert len(runs) >= 1
    assert any(r.target_project_id == response.target_project_id for r in runs)


def test_submit_creates_four_jobs(tmp_path) -> None:
    _, _, job_manager, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    # G-200 plan + G-300 draft + G-350 gate + G-400 compile = 4 jobs
    assert len(response.job_ids) == 4


def test_submit_new_project_triggers_forking(tmp_path) -> None:
    _, project_service, _, orchestrator = _setup(tmp_path)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked Story",
        ),
        canon_scope=CanonScope(source_project_id="source-project", character_ids=["char-1"]),
        generation_brief="Fork and generate.",
        target_chapter_count=1,
    )
    response = orchestrator.submit_generation(request)
    assert response.target_project_id != "source-project"
    # Verify forked project was created
    forked = project_service.get_project(response.target_project_id)
    assert forked is not None


def test_submit_stores_packet_in_db(tmp_path) -> None:
    repo, _, _, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    packets = repo.list_canon_generation_packets_for_generation(response.generation_id)
    assert len(packets) == 1
    assert packets[0].packet_json


def test_run_status_is_queued_on_submit(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    assert str(response.status) == "queued" or response.status == "queued"


def test_created_artifacts_empty_on_submit(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    response = orchestrator.submit_generation(_same_project_request())
    assert response.created_artifacts == []


def test_nonexistent_source_raises_file_not_found(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    request = CanonGenerationRequest(
        source_project_id="nonexistent-project",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        destination=GenerationDestination(
            destination_kind=DestinationKind.SAME_PROJECT,
            target_project_id="nonexistent-project",
        ),
        canon_scope=CanonScope(source_project_id="nonexistent-project", character_ids=["char-1"]),
        generation_brief="Generate.",
        target_chapter_count=1,
    )
    with pytest.raises(FileNotFoundError):
        orchestrator.submit_generation(request)


def test_request_hash_is_deterministic(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    req1 = _same_project_request(brief="Same brief")
    req2 = _same_project_request(brief="Same brief")
    assert orchestrator._request_hash(req1) == orchestrator._request_hash(req2)


def test_request_hash_differs_for_different_briefs(tmp_path) -> None:
    _, _, _, orchestrator = _setup(tmp_path)
    req1 = _same_project_request(brief="Brief one")
    req2 = _same_project_request(brief="Brief two")
    assert orchestrator._request_hash(req1) != orchestrator._request_hash(req2)


def test_chapter_draft_job_includes_correct_chapter_ids(tmp_path) -> None:
    _, _, job_manager, orchestrator = _setup(tmp_path)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        destination=GenerationDestination(
            destination_kind=DestinationKind.SAME_PROJECT,
            target_project_id="source-project",
        ),
        canon_scope=CanonScope(source_project_id="source-project", character_ids=["char-1"]),
        generation_brief="Generate a side story.",
        target_chapter_count=5,
    )
    response = orchestrator.submit_generation(request)
    # G-300 is the 2nd job (after G-200 plan). Get its payload.
    g300_job_id = response.job_ids[1]  # G-200, G-300, G-350, G-400
    from uuid import UUID
    job_data = job_manager.get_request_payload(UUID(g300_job_id))
    assert job_data["phase"] == "G-300"
    payload = job_data["payload"]
    assert "chapter_ids" in payload
    assert len(payload["chapter_ids"]) == 5
    assert payload["chapter_ids"] == ["chapter-1", "chapter-2", "chapter-3", "chapter-4", "chapter-5"]
