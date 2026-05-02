from __future__ import annotations

from time import sleep

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.jobs import JobCreateRequest
from app.schemas.projects import ProjectCreateRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService


def _wait_for_terminal(job_manager: JobManager, job_id, attempts: int = 80) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def test_local_executor_runs_generation_phases(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(db_path)
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
    repository.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-project",
        target_project_id="source-project",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        request_hash="hash",
    )
    repository.upsert_canon_generation_packet(
        packet_id="packet-1",
        generation_id="gen-1",
        source_project_id="source-project",
        target_project_id="source-project",
        packet_json={
            "packet_id": "packet-1",
            "source_project_id": "source-project",
            "target_project_id": "source-project",
            "mode": "same_project_side_story",
            "generation_brief": "brief",
            "foundation_snapshot": {"premise": "premise", "logline": "logline"},
            "characters": [{"character_id": "char-1", "display_name": "Aria"}],
            "relationships": [],
            "world_bible": [],
            "arcs": [],
            "continuity_threads": [],
            "continuity_findings": [],
            "drafting_context_packets": [],
            "canon_policy": {"forbidden_contradictions": []},
            "prompt_budget_summary": {"estimated_prompt_chars": 0, "target_max_chars": 10000, "truncated_fields": [], "fit_to_budget": True},
            "source_hashes": {},
        },
        source_hashes_json={},
        prompt_budget_json={},
    )
    job_manager = JobManager(db_path)
    role_manager = RoleModelCheckManager(db_path)
    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=role_manager,
        role_check_service=RoleModelCheckerService(tmp_path / "data" / "models", tmp_path / "data" / "role_model_checker_runs"),
        project_service=project_service,
        story_repository=repository,
        poll_interval_seconds=0.05,
    )
    planner = job_manager.create_job(JobCreateRequest(phase="G-200", payload={"generation_id": "gen-1", "packet_id": "packet-1", "project_id": "source-project"}))
    drafter = job_manager.create_job(JobCreateRequest(phase="G-300", payload={"generation_id": "gen-1", "packet_id": "packet-1", "chapter_ids": ["chapter-1"], "project_id": "source-project"}))
    gate = job_manager.create_job(JobCreateRequest(phase="G-350", payload={"generation_id": "gen-1", "packet_id": "packet-1", "artifact_refs": [], "project_id": "source-project"}))
    compiler = job_manager.create_job(JobCreateRequest(phase="G-400", payload={"generation_id": "gen-1", "packet_id": "packet-1", "chapter_artifact_ids": [], "project_id": "source-project"}))
    executor.start()
    try:
        assert _wait_for_terminal(job_manager, planner.id) == "COMPLETED"
        assert _wait_for_terminal(job_manager, drafter.id) == "COMPLETED"
        assert _wait_for_terminal(job_manager, gate.id) == "COMPLETED"
        assert _wait_for_terminal(job_manager, compiler.id) == "COMPLETED"
    finally:
        executor.stop()
