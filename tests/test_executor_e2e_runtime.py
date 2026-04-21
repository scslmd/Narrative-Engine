from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from time import sleep
from uuid import uuid4

from app.inference.base import InferenceBackend
from app.persistence.steps import stable_hash_payload
from app.schemas.jobs import JobCreateRequest
from app.schemas.manifest import Manifest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.step_records import StepRecordService

from .test_executor_integration import (
    FakeInferenceBackend,
    _wait_for_checker_terminal,
    _wait_for_terminal_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(project_id: str) -> Manifest:
    return Manifest.model_validate(
        {
            "project_id": project_id,
            "project_name": "Project Aurora",
            "genre": "Science Fantasy",
            "tone": "Wonder-driven",
            "story_structure": "THREE_ACT",
            "constraints": ["No time travel", "Third-person limited only"],
            "premise_text": "A cartographer maps a city that rearranges itself every dusk.",
        }
    )


def _build_executor(
    tmp_path: Path,
    *,
    inferencer: InferenceBackend,
) -> tuple[LocalExecutor, JobManager, ProjectService, StepRecordService, RoleModelCheckManager]:
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
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    project_service.reconcile_projects()


def _run_phase(
    job_manager: JobManager,
    phase: str,
    project_id: str,
    payload: dict[str, object] | None = None,
):
    return job_manager.create_job(
        JobCreateRequest(
            phase=phase,
            payload={"project_id": project_id, **(payload or {})},
        )
    )


# ---------------------------------------------------------------------------
# TestExecutorCheckerReportPersistence
# ---------------------------------------------------------------------------

class TestExecutorCheckerReportPersistence:
    """E2E tests for checker run report persistence via daemon thread."""

    def test_executor_checker_with_report_persistence(self, tmp_path: Path) -> None:
        """Checker run with save_report=True produces report file and lineage record."""
        reports_root = tmp_path / "data" / "role_model_checker_runs"

        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=FakeInferenceBackend()
        )
        executor.start()
        try:
            run = checker_manager.create_run(
                RoleModelCheckStartRequest(
                    roles=["architect", "critic"],
                    save_report=True,
                )
            )
            run_status = _wait_for_checker_terminal(checker_manager, run.run_id)
        finally:
            executor.stop()

        assert run_status == "COMPLETED"
        assert run_status == "COMPLETED"

        # Verify report file was created
        report_files = list(reports_root.glob("*.json"))
        assert len(report_files) == 1
        report_content = json.loads(report_files[0].read_text(encoding="utf-8"))
        assert "run_id" in report_content or "results" in report_content

        # Verify the run has a report_path recorded
        final_status = checker_manager.get_status(run.run_id)
        assert final_status.report_path is not None

        # Verify step records: 2 roles + 1 report_persist = 3
        steps = step_records.list_step_records(
            run_id=run.run_id,
            run_kind="role_model_check",
            attempt_number=1,
        )
        assert len(steps) == 3
        step_names = {s["step_name"] for s in steps}
        assert step_names == {"architect", "critic", "report_persist"}

        # Verify lineage record for checker_report
        lineage = step_records.list_artifact_lineage(
            run_id=run.run_id,
            run_kind="role_model_check",
        )
        assert len(lineage) == 1
        assert lineage[0]["artifact_role"] == "checker_report"
        assert lineage[0]["status"] == "CANONICAL"

    def test_executor_checker_deterministic_critic(self, tmp_path: Path) -> None:
        """Checker with critic_profile='deterministic_only' skips LLM for critic role."""
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=FakeInferenceBackend()
        )
        executor.start()
        try:
            run = checker_manager.create_run(
                RoleModelCheckStartRequest(
                    roles=["critic"],
                    critic_profile="deterministic_only",
                    save_report=False,
                )
            )
            run_status = _wait_for_checker_terminal(checker_manager, run.run_id)
        finally:
            executor.stop()

        assert run_status == "COMPLETED"

        steps = step_records.list_step_records(
            run_id=run.run_id,
            run_kind="role_model_check",
            attempt_number=1,
        )
        assert len(steps) == 1
        assert steps[0]["step_name"] == "critic"

        # Verify the single result passed (deterministic critic always passes)
        final_status = checker_manager.get_status(run.run_id)
        assert len(final_status.results) == 1
        assert final_status.results[0].role == "critic"
        assert final_status.results[0].passed is True


# ---------------------------------------------------------------------------
# TestExecutorMissingUpstreamArtifacts
# ---------------------------------------------------------------------------

class TestExecutorMissingUpstreamArtifacts:
    """Tests for phase behavior when upstream artifacts are missing."""

    def test_executor_p400_with_all_missing_upstreams(self, tmp_path: Path) -> None:
        """P-400 without architect_output, sequence, or chapter_1 still produces story_bible."""
        project_id = "p400-no-upstreams"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id, "project_name": "Project Aurora"},
                "premise": "No upstreams available — generated from manifest alone.",
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": ["What happened to the cartographer?"],
            },
            ensure_ascii=True,
            indent=2,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCity lives.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nChapter content.\n",
                "P-400": story_bible_content,
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        # Do NOT run P-100, P-200, P-300 — go straight to P-400
        executor.start()
        try:
            p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            status = _wait_for_terminal_status(job_manager, p400.id)
        finally:
            executor.stop()

        assert status == "COMPLETED"
        assert len(inferencer.requests) == 1
        assert inferencer.requests[0].metadata["phase"] == "P-400"

        # Verify step record exists
        steps = job_manager.list_step_records(p400.id)
        assert len(steps) == 1
        assert steps[0]["step_name"] == "compiler"
        assert steps[0]["state"] == "COMPLETED"

        # Verify story_bible lineage
        lineage = job_manager.list_artifact_lineage(p400.id)
        assert len(lineage) == 1
        assert lineage[0]["artifact_role"] == "story_bible"
        assert lineage[0]["status"] == "CANONICAL"

        # Verify story_bible.json was created
        story_bible_path = tmp_path / "data" / "projects" / project_id / "story_bible.json"
        assert story_bible_path.exists()
        parsed = json.loads(story_bible_path.read_text(encoding="utf-8"))
        assert parsed["project"]["project_id"] == project_id

        # Verify artifact registration in project
        artifact = project_service.read_artifact(project_id, "story_bible")
        assert artifact is not None
        assert artifact.content == story_bible_content + "\n"

    def test_executor_p400_with_partial_upstreams(self, tmp_path: Path) -> None:
        """P-400 with only architect_output (missing sequence and chapter) still produces story_bible."""
        project_id = "p400-partial-upstreams"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id},
                "premise": "Partial upstreams — only architect available.",
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
            indent=2,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nOnly architect.\n",
                "P-400": story_bible_content,
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        executor.start()
        try:
            # Only run P-100, skip P-200 and P-300, go to P-400
            p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
            p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            status = _wait_for_terminal_status(job_manager, p400.id)
        finally:
            executor.stop()

        assert status == "COMPLETED"

        # Verify runtime artifact selections include only what was available
        p400_steps = job_manager.list_step_records(p400.id)
        assert len(p400_steps) == 1
        # Input refs should include "manifest" and "architect_output", but not "sequence" or "chapter_1"
        input_refs = p400_steps[0]["input_artifact_refs"]
        assert "manifest" in input_refs
        assert "architect_output" in input_refs

        # story_bible should still be created
        story_bible_path = tmp_path / "data" / "projects" / project_id / "story_bible.json"
        assert story_bible_path.exists()


# ---------------------------------------------------------------------------
# TestExecutorFileCleanup
# ---------------------------------------------------------------------------

class TestExecutorFileCleanup:
    """Tests for staged/backup file cleanup after phase completion."""

    def test_executor_staged_backup_cleanup_after_p400(self, tmp_path: Path) -> None:
        """After P-400 completes, .staged and .bak files are absent."""
        project_id = "cleanup-p400"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id},
                "premise": "Cleanup test.",
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
            indent=2,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCleanup.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nContent.\n",
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

        # Verify no .staged or .bak files exist for story_bible
        project_dir = tmp_path / "data" / "projects" / project_id
        staged_files = list(project_dir.rglob("*.staged"))
        bak_files = list(project_dir.rglob("*.bak"))
        assert len(staged_files) == 0, f"Expected no .staged files, found: {staged_files}"
        assert len(bak_files) == 0, f"Expected no .bak files, found: {bak_files}"

        # Verify final output exists
        story_bible_path = project_dir / "story_bible.json"
        assert story_bible_path.exists()

    def test_executor_staged_backup_cleanup_after_p100(self, tmp_path: Path) -> None:
        """After P-100 completes, .staged and .bak files are absent."""
        project_id = "cleanup-p100"
        inferencer = FakeInferenceBackend(
            content_by_phase={"P-100": "## Logline\nCleanup test.\n"}
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        finally:
            executor.stop()

        project_dir = tmp_path / "data" / "projects" / project_id
        staged_files = list(project_dir.rglob("*.staged"))
        bak_files = list(project_dir.rglob("*.bak"))
        assert len(staged_files) == 0
        assert len(bak_files) == 0


# ---------------------------------------------------------------------------
# TestExecutorProjectIsolation
# ---------------------------------------------------------------------------

class TestExecutorProjectIsolation:
    """Tests for project isolation when multiple projects have jobs."""

    def test_executor_multiple_projects_isolated(self, tmp_path: Path) -> None:
        """Jobs for different projects produce independent artifacts with no cross-contamination."""
        project_id_a = "isolation-project-a"
        project_id_b = "isolation-project-b"

        story_bible_a = json.dumps(
            {"project": {"project_id": project_id_a}, "premise": "Project A bible."},
            ensure_ascii=True,
        )
        story_bible_b = json.dumps(
            {"project": {"project_id": project_id_b}, "premise": "Project B bible."},
            ensure_ascii=True,
        )

        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": ["## Logline\nA.\n", "## Logline\nB.\n"],
                "P-200": [json.dumps({"beats": []}), json.dumps({"beats": []})],
                "P-300": ["# Chapter 1\nA.\n", "# Chapter 1\nB.\n"],
                "P-400": [story_bible_a, story_bible_b],
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id_a, project_service=project_service)
        _create_project(tmp_path, project_id_b, project_service=project_service)

        executor.start()
        try:
            # Create P-400 jobs for both projects
            p400_a = _run_phase(job_manager, phase="P-400", project_id=project_id_a)
            p400_b = _run_phase(job_manager, phase="P-400", project_id=project_id_b)

            status_a = _wait_for_terminal_status(job_manager, p400_a.id)
            status_b = _wait_for_terminal_status(job_manager, p400_b.id)
        finally:
            executor.stop()

        assert status_a == "COMPLETED"
        assert status_b == "COMPLETED"

        # Verify each project has its own story_bible.json with correct content
        bible_a_path = tmp_path / "data" / "projects" / project_id_a / "story_bible.json"
        bible_b_path = tmp_path / "data" / "projects" / project_id_b / "story_bible.json"

        assert bible_a_path.exists()
        assert bible_b_path.exists()
        assert bible_a_path.read_text(encoding="utf-8").strip() == story_bible_a
        assert bible_b_path.read_text(encoding="utf-8").strip() == story_bible_b

        # Verify lineage records are project-scoped
        conn = sqlite3.connect(str(tmp_path / "data" / "state" / "narrative_ops.db"))
        conn.row_factory = sqlite3.Row
        try:
            rows_a = conn.execute(
                "SELECT artifact_role, status FROM artifact_lineage WHERE project_id = ?",
                (project_id_a,),
            ).fetchall()
            rows_b = conn.execute(
                "SELECT artifact_role, status FROM artifact_lineage WHERE project_id = ?",
                (project_id_b,),
            ).fetchall()
        finally:
            conn.close()

        # Each project should have its own lineage records (P-100 through P-400)
        roles_a = {r["artifact_role"] for r in rows_a}
        roles_b = {r["artifact_role"] for r in rows_b}
        assert "story_bible" in roles_a
        assert "story_bible" in roles_b

        # Verify read_artifact returns project-scoped content
        artifact_a = project_service.read_artifact(project_id_a, "story_bible")
        artifact_b = project_service.read_artifact(project_id_b, "story_bible")
        assert artifact_a.content.strip() == story_bible_a
        assert artifact_b.content.strip() == story_bible_b


# ---------------------------------------------------------------------------
# TestExecutorJobAPIEndpoints
# ---------------------------------------------------------------------------

class TestExecutorJobAPIEndpoints:
    """Tests for job API endpoint coverage."""

    def test_executor_job_status_transitions(self, tmp_path: Path) -> None:
        """Job status transitions from PENDING through PROCESSING to COMPLETED."""
        project_id = "status-transitions"
        inferencer = FakeInferenceBackend(
            content_by_phase={"P-100": "## Logline\nStatus test.\n"}
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        # Job starts as PENDING
        job = job_manager.create_job(
            JobCreateRequest(
                phase="P-100",
                payload={"project_id": project_id, "model_id": "test-model"},
            )
        )
        initial_status = job_manager.get_status(job.id)
        assert str(initial_status.status) == "PENDING"

        executor.start()
        try:
            final_status_str = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor.stop()

        assert final_status_str == "COMPLETED"

        # Verify the final status shows COMPLETED
        final_status = job_manager.get_status(job.id)
        assert str(final_status.status) == "COMPLETED"

    def test_executor_job_attempts_after_retry(self, tmp_path: Path) -> None:
        """Job attempt tracking verifies attempt_number increments on retry."""
        project_id = "attempts-test"

        # First attempt fails, second succeeds
        call_count = {"count": 0}

        class FailingThenSucceedingInferenceBackend(FakeInferenceBackend):
            def generate_text(self, request):
                phase = str(request.metadata.get("phase") or "unknown")
                call_count["count"] += 1
                if call_count["count"] == 1:
                    # First call fails
                    from app.inference.base import InferenceBackendError
                    raise InferenceBackendError(
                        "First attempt failed",
                        category="error",
                        code="TEST_FAILURE",
                        finish_reason="error",
                        retryable=True,
                    )
                return super().generate_text(request)

        inferencer = FailingThenSucceedingInferenceBackend(
            content_by_phase={"P-100": "## Logline\nRetried.\n"}
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        executor.start()
        try:
            job = job_manager.create_job(
                JobCreateRequest(
                    phase="P-100",
                    payload={"project_id": project_id, "model_id": "test-model"},
                )
            )
            # Wait for first attempt to fail
            for _ in range(80):
                current = job_manager.get_status(job.id)
                if str(current.status) == "FAILED":
                    break
                sleep(0.05)

            # Retry the job
            job_manager.retry_job(job.id, retry_reason="manual_retry")

            # Wait for second attempt to succeed
            final_status = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor.stop()

        assert final_status == "COMPLETED"

        # Verify attempts show the retry history
        attempts = job_manager.get_attempt_history_projection(job.id)
        assert len(attempts.items) >= 2

        # The step records should show both failure and success
        steps = job_manager.list_step_records(job.id)
        assert len(steps) >= 2
        assert any(s["state"] == "FAILED" for s in steps)
        assert any(s["state"] == "COMPLETED" for s in steps)


# ---------------------------------------------------------------------------
# TestExecutorP400EmptyOutput
# ---------------------------------------------------------------------------

class TestExecutorP400EmptyOutput:
    """Tests for P-400 with empty or whitespace-only LLM output."""

    def test_executor_p400_empty_output(self, tmp_path: Path) -> None:
        """P-400 with empty LLM output still produces story_bible.json (with trailing newline)."""
        project_id = "p400-empty-output"
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nEmpty output test.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nContent.\n",
                "P-400": "",  # Empty output
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
            status = _wait_for_terminal_status(job_manager, p400.id)
        finally:
            executor.stop()

        # P-400 should still complete even with empty LLM output
        # (the executor appends a newline to any output)
        assert status == "COMPLETED"

        steps = job_manager.list_step_records(p400.id)
        assert len(steps) == 1
        assert steps[0]["state"] == "COMPLETED"

        # Verify step_bible.json was created (even if just a newline)
        story_bible_path = tmp_path / "data" / "projects" / project_id / "story_bible.json"
        assert story_bible_path.exists()


# ---------------------------------------------------------------------------
# TestExecutorFullPipelineOrder
# ---------------------------------------------------------------------------

class TestExecutorFullPipelineOrder:
    """Tests for full pipeline execution order guarantees."""

    def test_executor_full_pipeline_p100_before_p400(self, tmp_path: Path) -> None:
        """Full P-100 -> P-200 -> P-300 -> P-400 pipeline produces all artifacts in order."""
        project_id = "full-pipeline-order"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id},
                "premise": "Full pipeline bible.",
                "world_anchors": ["city"],
                "character_threads": ["cartographer"],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
            indent=2,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nFull pipeline test.\n",
                "P-200": json.dumps({"beats": [{"id": "b1", "title": "Opening"}]}),
                "P-300": "# Chapter 1\nFull pipeline chapter.\n",
                "P-400": story_bible_content,
            }
        )
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, project_service=project_service)

        execution_order: list[str] = []

        class TrackingBackend(FakeInferenceBackend):
            def generate_text(self, request):
                phase = str(request.metadata.get("phase") or "unknown")
                execution_order.append(phase)
                return super().generate_text(request)

        tracking_inferencer = TrackingBackend(
            content_by_phase={
                "P-100": "## Logline\nFull pipeline test.\n",
                "P-200": json.dumps({"beats": [{"id": "b1", "title": "Opening"}]}),
                "P-300": "# Chapter 1\nFull pipeline chapter.\n",
                "P-400": story_bible_content,
            }
        )
        # Rebuild executor with tracking inferencer
        executor, job_manager, project_service, step_records, checker_manager = _build_executor(
            tmp_path, inferencer=tracking_inferencer
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
            status = _wait_for_terminal_status(job_manager, p400.id)
        finally:
            executor.stop()

        assert status == "COMPLETED"

        # Verify execution order respects pipeline sequence
        assert execution_order == ["P-100", "P-200", "P-300", "P-400"]

        # Verify all expected files exist
        project_dir = tmp_path / "data" / "projects" / project_id
        assert (project_dir / "exports" / "p100_architect_output.md").exists()
        assert (project_dir / "sequences.json").exists()
        assert (project_dir / "chapter.md").exists()
        assert (project_dir / "story_bible.json").exists()

        # Verify all lineage records
        lineage_count = 0
        for job_id in [p100.id, p200.id, p300.id, p400.id]:
            lineage = job_manager.list_artifact_lineage(job_id)
            assert len(lineage) == 1
            lineage_count += 1
        assert lineage_count == 4


# ---------------------------------------------------------------------------
# Helper to access inferencer requests from the checker service

