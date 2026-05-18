from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.step_records import StepRecordService

pytestmark = pytest.mark.integration

from .test_executor_integration import FakeInferenceBackend, _wait_for_terminal_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(project_id: str) -> dict:
    return {
        "project_id": project_id,
        "project_name": "Project Aurora",
        "genre": "Science Fantasy",
        "tone": "Wonder-driven",
        "story_structure": "THREE_ACT",
        "constraints": ["No time travel", "Third-person limited only"],
        "premise_text": "A cartographer maps a city that rearranges itself every dusk.",
    }


def _build_executor(
    tmp_path: Path,
    *,
    inferencer: FakeInferenceBackend,
) -> tuple[LocalExecutor, JobManager, ProjectService, StepRecordService, RoleModelCheckManager]:
    from app.services.projects import ProjectService
    from app.services.role_model_checker import RoleModelCheckerService
    from app.schemas.inference import InferenceProviderDescriptor

    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    models_root = tmp_path / "data" / "models"
    reports_root = tmp_path / "data" / "role_model_checker_runs"
    models_root.mkdir(parents=True, exist_ok=True)

    project_service = ProjectService(tmp_path)
    job_manager = JobManager(db_path)
    checker_manager = RoleModelCheckManager(db_path)
    step_records = StepRecordService(db_path)

    executor = LocalExecutor(
        job_manager=job_manager,
        role_check_manager=checker_manager,
        role_check_service=RoleModelCheckerService(
            models_root, reports_root, inferencer=inferencer
        ),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )
    return executor, job_manager, project_service, step_records, checker_manager


def _create_project(
    tmp_path: Path,
    project_id: str,
    *,
    project_service: ProjectService,
) -> None:
    from app.schemas.manifest import Manifest
    manifest = Manifest.model_validate(_make_manifest(project_id))
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    project_service.reconcile_projects()


def _run_phase(
    job_manager: JobManager,
    phase: str,
    project_id: str,
    payload: dict[str, object] | None = None,
):
    from app.schemas.jobs import JobCreateRequest
    return job_manager.create_job(
        JobCreateRequest(
            phase=phase,
            payload={"project_id": project_id, **(payload or {})},
        )
    )


# ---------------------------------------------------------------------------
# TestStoryBibleLineageContentHash
# ---------------------------------------------------------------------------

@pytest.mark.xdist_group(name="serial-story-bible-lineage")
class TestStoryBibleLineageContentHash:
    """Tests for story-bible lineage content_hash stability."""

    def test_story_bible_content_hash_matches_file_content(self, tmp_path: Path) -> None:
        """The content_hash in the lineage record equals the story_bible.json file content."""
        project_id = "content-hash-test"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id, "project_name": "Project Aurora"},
                "premise": "Story bible content for hash testing.",
                "world_anchors": ["the city", "the cartographer"],
                "character_threads": ["identity crisis"],
                "continuity_notes": ["City shifts at dusk, stabilizes at dawn."],
                "open_questions": ["Who designed the city?"],
            },
            ensure_ascii=True,
            indent=2,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nContent hash test.\n",
                "P-200": json.dumps({"beats": [{"id": "b1", "title": "Opening"}]}),
                "P-300": "# Chapter 1\nChapter content for hash.\n",
                "P-400": story_bible_content,
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
            p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
            p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"
            p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p400.id) == "COMPLETED"
        finally:
            executor.stop()

        # Verify the story_bible.json file content
        story_bible_path = tmp_path / "data" / "projects" / project_id / "story_bible.json"
        assert story_bible_path.exists()
        file_content = story_bible_path.read_text(encoding="utf-8")
        assert file_content.strip() == story_bible_content

        # Verify lineage record exists
        lineage = job_manager.list_artifact_lineage(p400.id)
        assert len(lineage) == 1
        assert lineage[0]["artifact_role"] == "story_bible"

        # The content_hash in the lineage record should equal the file content
        # (the executor passes the raw output text as content_hash)
        lineage_content_hash = lineage[0]["content_hash"]
        assert lineage_content_hash == file_content

        # Verify via project service read_artifact
        artifact = project_service.read_artifact(project_id, "story_bible")
        assert artifact is not None
        assert artifact.content == file_content


# ---------------------------------------------------------------------------
# TestStoryBibleFallbackFileRead
# ---------------------------------------------------------------------------

class TestStoryBibleFallbackFileRead:
    """Tests for story-bible fallback file read without lineage."""

    def test_story_bible_fallback_file_read_via_register_artifact(
        self, tmp_path: Path
    ) -> None:
        """read_artifact('story_bible') falls back to file read when no lineage exists
        but artifact has been registered via register_generated_artifact()."""
        from app.schemas.manifest import Manifest

        project_id = "fallback-with-registration"
        manifest = Manifest.model_validate(_make_manifest(project_id))
        initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
        project_service = ProjectService(tmp_path)
        project_service.reconcile_projects()

        # Create story_bible.json directly without running the executor
        story_bible_path = tmp_path / "data" / "projects" / project_id / "story_bible.json"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id, "project_name": "Project Aurora"},
                "premise": "Manually created story bible without executor.",
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": ["What is the fallback behavior?"],
            },
            ensure_ascii=True,
            indent=2,
        )
        story_bible_path.write_text(story_bible_content + "\n", encoding="utf-8")

        # Register the artifact so it appears in the projection
        project_service.register_generated_artifact(
            project_id, "story_bible", story_bible_path
        )

        # Verify read_artifact returns content via file fallback (no lineage registered)
        artifact = project_service.read_artifact(project_id, "story_bible")
        assert artifact is not None
        assert artifact.content == story_bible_content + "\n"


# ---------------------------------------------------------------------------
# TestStoryBibleLineageSupersession
# ---------------------------------------------------------------------------

class TestStoryBibleLineageSupersession:
    """Tests for story-bible lineage supersession chain."""

    def test_story_bible_supersession_chain_via_project_service(
        self, tmp_path: Path
    ) -> None:
        """Two P-400 runs verify project_service.read_artifact returns latest version."""
        project_id = "supersession-pservice-test"
        story_bible_v1 = json.dumps(
            {
                "project": {"project_id": project_id},
                "premise": "v1",
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
        )
        story_bible_v2 = json.dumps(
            {
                "project": {"project_id": project_id},
                "premise": "v2",
                "world_anchors": ["updated"],
                "character_threads": ["updated"],
                "continuity_notes": ["updated notes"],
                "open_questions": [],
            },
            ensure_ascii=True,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nSupersession test.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nContent.\n",
                "P-400": [story_bible_v1, story_bible_v2],
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
            p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
            p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"

            # First P-400 run
            first_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, first_p400.id) == "COMPLETED"

            # First run: read_artifact returns v1
            artifact_v1 = project_service.read_artifact(project_id, "story_bible")
            assert artifact_v1.content == story_bible_v1 + "\n"

            # Second P-400 run (should supersede the first)
            second_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, second_p400.id) == "COMPLETED"

            # After second run: read_artifact returns v2
            artifact_v2 = project_service.read_artifact(project_id, "story_bible")
            assert artifact_v2.content == story_bible_v2 + "\n"
            # Verify file content matches v2
            final_file = (tmp_path / "data" / "projects" / project_id / "story_bible.json").read_text(
                encoding="utf-8"
            )
            assert final_file.strip() == story_bible_v2
        finally:
            executor.stop()

        # Verify the supersession chain in raw DB
        import sqlite3
        conn = sqlite3.connect(str(tmp_path / "data" / "state" / "narrative_ops.db"))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT artifact_lineage_id, status, supersedes_artifact_lineage_id
                FROM artifact_lineage
                WHERE project_id = ? AND artifact_role = 'story_bible'
                ORDER BY artifact_lineage_id ASC
                """,
                (project_id,),
            ).fetchall()
        finally:
            conn.close()

        assert len(rows) == 2
        assert rows[0]["status"] == "SUPERSEDED"
        assert rows[1]["status"] == "CANONICAL"
        assert rows[1]["supersedes_artifact_lineage_id"] == rows[0]["artifact_lineage_id"]
