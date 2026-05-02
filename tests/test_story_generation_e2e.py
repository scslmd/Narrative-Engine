from __future__ import annotations

from time import sleep

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
from app.services.local_executor import LocalExecutor
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.story_forking import StoryForkingService
from app.services.story_generation_orchestrator import StoryGenerationOrchestrator


def _wait(job_manager: JobManager, job_id, attempts: int = 120) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def test_story_generation_end_to_end(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
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
    repository.upsert_foundation_profile(
        project_id="source-project",
        premise="A kingdom in decline.",
        logline="A disgraced knight returns home.",
    )
    repository.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    job_manager = JobManager(db_path)
    orchestrator = StoryGenerationOrchestrator(
        repository=repository,
        project_service=project_service,
        packet_builder=CanonPacketBuilder(repository=repository, project_service=project_service),
        forking_service=StoryForkingService(repository=repository, project_service=project_service),
        job_manager=job_manager,
    )
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        destination=GenerationDestination(
            destination_kind=DestinationKind.SAME_PROJECT,
            target_project_id="source-project",
        ),
        canon_scope=CanonScope(source_project_id="source-project", character_ids=["char-1"]),
        generation_brief="Generate a side story.",
        target_chapter_count=1,
    )
    response = orchestrator.submit_generation(request)
    role_manager = RoleModelCheckManager(db_path)
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=role_manager,
        role_check_service=RoleModelCheckerService(tmp_path / "data" / "models", tmp_path / "data" / "role_model_checker_runs"),
        project_service=project_service,
        story_repository=repository,
        poll_interval_seconds=0.05,
    )
    executor.start()
    try:
        for job_id in response.job_ids:
            assert _wait(job_manager, job_id) == "COMPLETED"
    finally:
        executor.stop()
    run = repository.get_canon_generation_run(response.generation_id)
    assert run.status == "completed"
    manuscript_refs = [item for item in run.created_artifacts if item.get("artifact_kind") == "manuscript_document"]
    assert manuscript_refs
