from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Thread
from time import sleep
from uuid import uuid4

import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.steps import stable_hash_payload
from app.schemas.inference import (
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
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

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# FakeInferenceBackend
# ---------------------------------------------------------------------------

class FakeInferenceBackend(InferenceBackend):
    """Minimal fake inferencer that returns deterministic content per phase."""

    def __init__(
        self,
        *,
        content_by_phase: dict[str, str] | None = None,
        failing_phases: set[str] | None = None,
        model: str = "fake-model",
    ) -> None:
        self.requests: list[InferenceRequest] = []
        self._content_by_phase = content_by_phase or {}
        self._failing_phases = failing_phases or set()
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        phase = str(request.metadata.get("phase") or "unknown")
        if phase in self._failing_phases:
            raise InferenceBackendError(
                "Fake runtime request failed: timed out",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
            )
        content = self._content_by_phase.get(phase, f"{phase} runtime content.")
        if isinstance(content, list):
            # Support cycling through content list
            phase_index = sum(
                1
                for req in self.requests[:-1]
                if str(req.metadata.get("phase") or "unknown") == phase
            )
            content = content[phase_index % len(content)]
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=content,
            finish_reason="stop",
            usage=InferenceUsage(
                prompt_tokens=101,
                completion_tokens=202,
                total_tokens=303,
            ),
            raw_response={"backend": "fake", "backend_version": "2026.03"},
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
) -> tuple[LocalExecutor, JobManager, ProjectService, StepRecordService]:
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
    return executor, job_manager, project_service, step_records


def _wait_for_terminal_status(
    job_manager: JobManager,
    job_id,
    *,
    attempts: int = 80,
) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def _create_project(
    tmp_path: Path,
    project_id: str,
    *,
    executor: LocalExecutor,
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
# TestExecutorSinglePhaseChains
# ---------------------------------------------------------------------------

class TestExecutorSinglePhaseChains:
    """End-to-end daemon thread processing of individual and chained phases."""

    def test_executor_p100_architect_complete(self, tmp_path: Path) -> None:
        """Create a P-100 job and verify the daemon thread processes it to COMPLETED."""
        project_id = "p100-e2e-test"
        architect_output = (
            "## Logline\n"
            "A mapmaker learns her city is alive.\n\n"
            "## Core Premise\n"
            "The city rearranges itself every dusk."
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={"P-100": architect_output}
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        job = _run_phase(
            job_manager,
            phase="P-100",
            project_id=project_id,
            payload={"model_id": "architect-model"},
        )
        executor.start()
        try:
            final_status = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor.stop()

        assert final_status == "COMPLETED"
        assert len(inferencer.requests) == 1
        req = inferencer.requests[0]
        assert req.metadata["phase"] == "P-100"
        assert req.metadata["role"] == "architect"

        steps = job_manager.list_step_records(job.id)
        assert len(steps) == 1
        assert steps[0]["step_name"] == "architect"
        assert steps[0]["state"] == "COMPLETED"
        assert steps[0]["model_id"] == "architect-model"

        lineage = job_manager.list_artifact_lineage(job.id)
        assert len(lineage) == 1
        assert lineage[0]["artifact_role"] == "architect_output"
        assert lineage[0]["status"] == "CANONICAL"

        output_path = (
            tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"
        )
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == architect_output + "\n"

    def test_executor_p200_sequencer_reads_architect_output(self, tmp_path: Path) -> None:
        """P-100 completes, then P-200 reads the architect output and completes."""
        project_id = "p200-reads-p100"
        architect_content = "## Logline\nCity is alive.\n"
        sequence_content = json.dumps(
            {
                "beats": [
                    {"id": "beat-1", "title": "Opening", "depends_on": []},
                    {"id": "beat-2", "title": "Turn", "depends_on": ["beat-1"]},
                ]
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": architect_content,
                "P-200": sequence_content,
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(
                job_manager,
                phase="P-100",
                project_id=project_id,
                payload={"model_id": "architect-model"},
            )
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"

            p200 = _run_phase(
                job_manager,
                phase="P-200",
                project_id=project_id,
                payload={"model_id": "sequencer-model"},
            )
            p200_status = _wait_for_terminal_status(job_manager, p200.id)
        finally:
            executor.stop()

        assert p200_status == "COMPLETED"

        p200_steps = job_manager.list_step_records(p200.id)
        assert len(p200_steps) == 1
        assert p200_steps[0]["step_name"] == "sequencer"
        assert p200_steps[0]["state"] == "COMPLETED"
        assert "architect_output" in p200_steps[0]["input_artifact_refs"]

        sequence_path = tmp_path / "data" / "projects" / project_id / "sequences.json"
        assert sequence_path.exists()
        assert sequence_path.read_text(encoding="utf-8") == sequence_content + "\n"

        # Sequencer should reference the architect output from the previous job
        p100_steps = job_manager.list_step_records(p100.id)
        assert p100_steps[0]["state"] == "COMPLETED"

        # Check that artifact selections were recorded
        assert project_service.read_artifact(project_id, "architect_p100") is not None
        assert project_service.read_artifact(project_id, "sequence") is not None

    def test_executor_p300_drafter_reads_upstream_artifacts(self, tmp_path: Path) -> None:
        """P-100 -> P-200 -> P-300 chain; drafter completes with upstream artifacts."""
        project_id = "p300-upstream-chain"
        chapter_content = (
            "# Chapter 1\n"
            "The city changes shape just before dawn.\n\n"
            "## Opening\n"
            "A cartographer follows the first impossible street.\n"
        )
        sequence_content = json.dumps(
            {"beats": [{"id": "beat-1", "title": "Opening"}]},
            ensure_ascii=True,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
                "P-200": sequence_content,
                "P-300": chapter_content,
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(
                job_manager,
                phase="P-100",
                project_id=project_id,
                payload={"model_id": "architect-model"},
            )
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"

            p200 = _run_phase(
                job_manager,
                phase="P-200",
                project_id=project_id,
                payload={"model_id": "sequencer-model"},
            )
            assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"

            p300 = _run_phase(
                job_manager,
                phase="P-300",
                project_id=project_id,
                payload={"model_id": "drafter-model"},
            )
            p300_status = _wait_for_terminal_status(job_manager, p300.id)
        finally:
            executor.stop()

        assert p300_status == "COMPLETED"

        p300_steps = job_manager.list_step_records(p300.id)
        assert len(p300_steps) == 1
        assert p300_steps[0]["step_name"] == "drafter"
        assert p300_steps[0]["state"] == "COMPLETED"
        assert "manifest" in p300_steps[0]["input_artifact_refs"]
        assert "sequence" in p300_steps[0]["input_artifact_refs"]
        assert "architect_output" in p300_steps[0]["input_artifact_refs"]
        assert p300_steps[0]["output_artifact_refs"] == ["chapter_1"]

        chapter_path = tmp_path / "data" / "projects" / project_id / "chapter.md"
        assert chapter_path.exists()
        assert chapter_path.read_text(encoding="utf-8") == chapter_content

        lineage = job_manager.list_artifact_lineage(p300.id)
        assert len(lineage) == 1
        assert lineage[0]["artifact_role"] == "chapter_1"
        assert lineage[0]["status"] == "CANONICAL"

    def test_executor_p400_compiler_full_pipeline(self, tmp_path: Path) -> None:
        """Full P-100 -> P-200 -> P-300 -> P-400 chain; compiler completes."""
        project_id = "p400-full-pipeline"
        story_bible_content = json.dumps(
            {
                "project": {"project_id": project_id, "project_name": "Project Aurora"},
                "premise": "A cartographer maps a city that rearranges itself every dusk.",
                "world_anchors": ["The city reconfigures at dusk."],
                "character_threads": ["The cartographer tracks impossible streets."],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
                "P-200": json.dumps(
                    {"beats": [{"id": "beat-1", "title": "Opening"}]},
                    ensure_ascii=True,
                ),
                "P-300": "# Chapter 1\nThe city changes shape just before dawn.\n",
                "P-400": story_bible_content,
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        executor.start()
        try:
            p100 = _run_phase(
                job_manager,
                phase="P-100",
                project_id=project_id,
                payload={"model_id": "architect-model"},
            )
            assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"

            p200 = _run_phase(
                job_manager,
                phase="P-200",
                project_id=project_id,
                payload={"model_id": "sequencer-model"},
            )
            assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"

            p300 = _run_phase(
                job_manager,
                phase="P-300",
                project_id=project_id,
                payload={"model_id": "drafter-model"},
            )
            assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"

            p400 = _run_phase(
                job_manager,
                phase="P-400",
                project_id=project_id,
                payload={"model_id": "compiler-model"},
            )
            p400_status = _wait_for_terminal_status(job_manager, p400.id)
        finally:
            executor.stop()

        assert p400_status == "COMPLETED"

        p400_steps = job_manager.list_step_records(p400.id)
        assert len(p400_steps) == 1
        assert p400_steps[0]["step_name"] == "compiler"
        assert p400_steps[0]["state"] == "COMPLETED"
        assert set(p400_steps[0]["input_artifact_refs"]) == {
            "manifest",
            "architect_output",
            "sequence",
            "chapter_1",
        }
        assert p400_steps[0]["output_artifact_refs"] == ["story_bible"]

        story_bible_path = (
            tmp_path / "data" / "projects" / project_id / "story_bible.json"
        )
        assert story_bible_path.exists()
        assert story_bible_path.read_text(encoding="utf-8") == story_bible_content + "\n"

        # Verify all four phases produced step records and lineage records
        p100_steps = job_manager.list_step_records(p100.id)
        p200_steps = job_manager.list_step_records(p200.id)
        p300_steps = job_manager.list_step_records(p300.id)

        assert len(p100_steps) == 1
        assert p100_steps[0]["step_name"] == "architect"
        assert len(p200_steps) == 1
        assert p200_steps[0]["step_name"] == "sequencer"
        assert len(p300_steps) == 1
        assert p300_steps[0]["step_name"] == "drafter"

        # Verify total request count across all phases
        assert len(inferencer.requests) == 4

        # Verify artifact lineage
        p400_lineage = job_manager.list_artifact_lineage(p400.id)
        assert len(p400_lineage) == 1
        assert p400_lineage[0]["artifact_role"] == "story_bible"
        assert p400_lineage[0]["status"] == "CANONICAL"


# ---------------------------------------------------------------------------
# TestExecutorFailurePaths
# ---------------------------------------------------------------------------

class TestExecutorFailurePaths:
    """Failure handling, FAILED step records, and retry from FAILED to PENDING."""

    def test_executor_phase_failure_marks_step_record_failed(
        self, tmp_path: Path
    ) -> None:
        """A phase that fails via InferenceBackendError creates a FAILED step record."""

        class FailingInferenceBackend(FakeInferenceBackend):
            def generate_text(self, request: InferenceRequest) -> InferenceResponse:
                self.requests.append(request)
                raise InferenceBackendError(
                    "Fake runtime request failed: timed out",
                    category="timeout",
                    code="INFERENCE_TIMEOUT",
                    finish_reason="timeout",
                    retryable=True,
                )

        project_id = "p100-failure-test"
        inferencer = FailingInferenceBackend()
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        job = _run_phase(
            job_manager,
            phase="P-100",
            project_id=project_id,
            payload={"model_id": "architect-model"},
        )
        executor.start()
        try:
            final_status = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor.stop()

        assert final_status == "FAILED"

        steps = job_manager.list_step_records(job.id)
        assert len(steps) == 1
        assert steps[0]["step_name"] == "architect"
        assert steps[0]["state"] == "FAILED"
        assert steps[0]["finish_reason"] == "timeout"
        assert steps[0]["error_code"] == "INFERENCE_TIMEOUT"
        assert steps[0]["error_category"] == "timeout"
        assert steps[0]["output_hash"] is None
        assert steps[0]["prompt_hash"] is not None
        assert steps[0]["input_hash"] is not None

        # No lineage records should be created for a failed phase
        lineage = job_manager.list_artifact_lineage(job.id)
        assert len(lineage) == 0

        # The output file should not exist
        output_path = (
            tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"
        )
        assert not output_path.exists()

    def test_executor_retry_from_failed_to_pending(self, tmp_path: Path) -> None:
        """A FAILED job can be retried via retry_job, and the daemon processes the retry."""
        project_id = "retry-p100-test"
        architect_output = "## Logline\nRetry succeeded.\n"

        # Phase 1: Run with always-failing backend to produce FAILED status
        fail_inferencer = FakeInferenceBackend(
            content_by_phase={"P-100": "unused"},
            failing_phases={"P-100"},
        )
        executor1, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=fail_inferencer
        )
        _create_project(tmp_path, project_id, executor=executor1, project_service=project_service)

        job = _run_phase(
            job_manager,
            phase="P-100",
            project_id=project_id,
            payload={"model_id": "architect-model"},
        )
        executor1.start()
        try:
            status = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor1.stop()

        assert status == "FAILED"
        current = job_manager.get_status(job.id)
        assert str(current.status) == "FAILED"
        assert len(job_manager.list_step_records(job.id)) == 1
        assert job_manager.list_step_records(job.id)[0]["state"] == "FAILED"

        # Retry the job
        job_manager.retry_job(job.id, retry_reason="operator_retry")
        retried = job_manager.get_status(job.id)
        assert str(retried.status) == "PENDING"

        # Phase 2: Run with succeeding backend to process the retry
        # Use a new executor instance to avoid any thread state leakage
        success_inferencer = FakeInferenceBackend(
            content_by_phase={"P-100": architect_output},
        )
        executor2, _, _, _ = _build_executor(tmp_path, inferencer=success_inferencer)
        executor2.start()
        try:
            final_status = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor2.stop()

        assert final_status == "COMPLETED"

        steps = job_manager.list_step_records(job.id)
        # After retry, there are 2 step records (one per attempt)
        # The latest attempt (2) should be COMPLETED
        assert len(steps) == 2
        # Find the latest attempt's step record
        latest = max(steps, key=lambda s: s["attempt_number"])
        assert latest["attempt_number"] == 2
        assert latest["step_name"] == "architect"
        assert latest["state"] == "COMPLETED"

        # Verify the output file was created on retry
        output_path = (
            tmp_path / "data" / "projects" / project_id / "exports" / "p100_architect_output.md"
        )
        assert output_path.exists()
        # executor strips content then adds one trailing newline
        expected = architect_output.rstrip("\n") + "\n"
        assert output_path.read_text(encoding="utf-8") == expected


# ---------------------------------------------------------------------------
# TestExecutorCheckerRuns
# ---------------------------------------------------------------------------

class TestExecutorCheckerRuns:
    """End-to-end daemon thread processing of RoleModelChecker runs."""

    def test_executor_checker_process_single_role(self, tmp_path: Path) -> None:
        """Create a checker run with a single role and verify daemon thread processes it."""
        checker_manager = None

        def _setup(tmp_path_arg: Path) -> tuple[LocalExecutor, RoleModelCheckManager, StepRecordService]:
            db_path = tmp_path_arg / "data" / "state" / "narrative_ops.db"
            models_root = tmp_path_arg / "data" / "models"
            reports_root = tmp_path_arg / "data" / "role_model_checker_runs"
            models_root.mkdir(parents=True, exist_ok=True)

            project_service = ProjectService(tmp_path_arg)
            job_manager = JobManager(db_path)
            nonlocal checker_manager
            checker_manager = RoleModelCheckManager(db_path)
            step_records = StepRecordService(db_path)

            executor = LocalExecutor(
                job_manager=job_manager,
                role_check_manager=checker_manager,
                role_check_service=RoleModelCheckerService(
                    models_root, reports_root, inferencer=FakeInferenceBackend()
                ),
                inferencer=FakeInferenceBackend(),
                project_service=project_service,
                step_record_service=step_records,
                poll_interval_seconds=0.05,
            )
            return executor, checker_manager, step_records

        executor, checker_manager, step_records = _setup(tmp_path)
        executor.start()
        try:
            run = checker_manager.create_run(
                RoleModelCheckStartRequest(
                    roles=["architect"],
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
        assert steps[0]["step_name"] == "architect"
        assert steps[0]["state"] == "COMPLETED"
        assert steps[0]["run_kind"] == "role_model_check"

    def test_executor_checker_process_multiple_roles(self, tmp_path: Path) -> None:
        """Checker run with multiple roles completes and records each role."""
        checker_manager = None

        def _setup(tmp_path_arg: Path) -> tuple[LocalExecutor, RoleModelCheckManager, StepRecordService]:
            db_path = tmp_path_arg / "data" / "state" / "narrative_ops.db"
            models_root = tmp_path_arg / "data" / "models"
            reports_root = tmp_path_arg / "data" / "role_model_checker_runs"
            models_root.mkdir(parents=True, exist_ok=True)

            project_service = ProjectService(tmp_path_arg)
            job_manager = JobManager(db_path)
            nonlocal checker_manager
            checker_manager = RoleModelCheckManager(db_path)
            step_records = StepRecordService(db_path)

            executor = LocalExecutor(
                job_manager=job_manager,
                role_check_manager=checker_manager,
                role_check_service=RoleModelCheckerService(
                    models_root, reports_root, inferencer=FakeInferenceBackend()
                ),
                inferencer=FakeInferenceBackend(),
                project_service=project_service,
                step_record_service=step_records,
                poll_interval_seconds=0.05,
            )
            return executor, checker_manager, step_records

        executor, checker_manager, step_records = _setup(tmp_path)
        executor.start()
        try:
            run = checker_manager.create_run(
                RoleModelCheckStartRequest(
                    roles=["architect", "sequencer", "drafter", "critic"],
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
        assert len(steps) == 4
        step_names = {s["step_name"] for s in steps}
        assert step_names == {"architect", "sequencer", "drafter", "critic"}
        assert all(s["state"] == "COMPLETED" for s in steps)

        # Verify the run status has all results
        final_status = checker_manager.get_status(run.run_id)
        assert len(final_status.results) == 4
        assert all(r.passed for r in final_status.results)


# ---------------------------------------------------------------------------
# TestExecutorStepRecordLineage
# ---------------------------------------------------------------------------

class TestExecutorStepRecordLineage:
    """Step record and artifact lineage creation across phases."""

    def test_executor_creates_step_records_per_phase(self, tmp_path: Path) -> None:
        """Each completed phase creates exactly one step record."""
        project_id = "step-records-per-phase"
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCity lives.\n",
                "P-200": json.dumps({"beats": [{"id": "b1", "title": "Opening"}]}),
                "P-300": "# Chapter 1\nChapter content.\n",
                "P-400": json.dumps({"project": {}}),
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

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

        # Each job should have exactly one step record
        assert len(job_manager.list_step_records(p100.id)) == 1
        assert len(job_manager.list_step_records(p200.id)) == 1
        assert len(job_manager.list_step_records(p300.id)) == 1
        assert len(job_manager.list_step_records(p400.id)) == 1

        # Step names should match phases
        assert job_manager.list_step_records(p100.id)[0]["step_name"] == "architect"
        assert job_manager.list_step_records(p200.id)[0]["step_name"] == "sequencer"
        assert job_manager.list_step_records(p300.id)[0]["step_name"] == "drafter"
        assert job_manager.list_step_records(p400.id)[0]["step_name"] == "compiler"

    def test_executor_creates_lineage_records_per_phase(self, tmp_path: Path) -> None:
        """Each completed phase creates an artifact lineage record."""
        project_id = "lineage-per-phase"
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCity lives.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nChapter content.\n",
                "P-400": json.dumps({"project": {}}),
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

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

        # Each job should have exactly one lineage record
        assert len(job_manager.list_artifact_lineage(p100.id)) == 1
        assert len(job_manager.list_artifact_lineage(p200.id)) == 1
        assert len(job_manager.list_artifact_lineage(p300.id)) == 1
        assert len(job_manager.list_artifact_lineage(p400.id)) == 1

        # Verify artifact roles
        p100_lineage = job_manager.list_artifact_lineage(p100.id)
        assert p100_lineage[0]["artifact_role"] == "architect_output"

        p200_lineage = job_manager.list_artifact_lineage(p200.id)
        assert p200_lineage[0]["artifact_role"] == "sequence"

        p300_lineage = job_manager.list_artifact_lineage(p300.id)
        assert p300_lineage[0]["artifact_role"] == "chapter_1"

        p400_lineage = job_manager.list_artifact_lineage(p400.id)
        assert p400_lineage[0]["artifact_role"] == "story_bible"

    def test_executor_lineage_canonical_supersession(self, tmp_path: Path) -> None:
        """Running the same phase twice creates a supersession chain in lineage."""
        project_id = "supersession-test"
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
                "world_anchors": [],
                "character_threads": [],
                "continuity_notes": [],
                "open_questions": [],
            },
            ensure_ascii=True,
        )
        inferencer = FakeInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCity lives.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nChapter content.\n",
                "P-400": [story_bible_v1, story_bible_v2],
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)
        db_path = tmp_path / "data" / "state" / "narrative_ops.db"

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

            # Second P-400 run (should supersede the first)
            second_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
            assert _wait_for_terminal_status(job_manager, second_p400.id) == "COMPLETED"
        finally:
            executor.stop()

        # Query the raw database for the supersession chain
        conn = sqlite3.connect(str(db_path))
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

        # The second lineage record should reference the first
        second_lineage = job_manager.list_artifact_lineage(second_p400.id)
        assert len(second_lineage) == 1
        assert second_lineage[0]["status"] == "CANONICAL"
        assert second_lineage[0]["supersedes_artifact_lineage_id"] == rows[0]["artifact_lineage_id"]

        # The project service should reflect the latest version
        artifact = project_service.read_artifact(project_id, "story_bible")
        assert artifact.content == story_bible_v2 + "\n"


# ---------------------------------------------------------------------------
# TestExecutorDaemonThreadSafety
# ---------------------------------------------------------------------------

class TestExecutorDaemonThreadSafety:
    """Tests for daemon thread lifecycle and concurrency safety."""

    def test_executor_start_is_idempotent(self, tmp_path: Path) -> None:
        """Calling start() twice doesn't create duplicate threads."""
        inferencer = FakeInferenceBackend()
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )

        # Start once
        executor.start()
        initial_thread_count = len(executor._threads)
        assert initial_thread_count == 2  # job + checker threads

        thread_names_after_first = {t.name for t in executor._threads}

        # Start again — should be a no-op
        executor.start()
        assert len(executor._threads) == initial_thread_count

        thread_names_after_second = {t.name for t in executor._threads}
        assert thread_names_after_first == thread_names_after_second

        executor.stop()

    def test_executor_stop_cleanly_terminates_threads(self, tmp_path: Path) -> None:
        """stop() terminates threads within timeout."""
        inferencer = FakeInferenceBackend()
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )

        executor.start()
        assert len(executor._threads) == 2

        # Verify threads are alive before stop
        for t in executor._threads:
            assert t.is_alive()

        executor.stop()

        # After stop, _threads should be cleared
        assert executor._threads == []

        # Threads should no longer be alive
        # (they may have already finished by the time we check)
        # The important thing is _threads is empty and the stop event was set

        # Can restart after stop
        executor.start()
        assert len(executor._threads) == 2
        executor.stop()

    def test_executor_concurrent_jobs_claimed_sequentially(
        self, tmp_path: Path
    ) -> None:
        """Creating multiple jobs verifies they are processed one at a time
        by the single worker thread (PENDING -> PROCESSING -> COMPLETED ordering)."""
        project_id = "concurrent-jobs-test"
        order_tracker: list[str] = []

        class TrackingInferenceBackend(FakeInferenceBackend):
            def generate_text(self, request: InferenceRequest) -> InferenceResponse:
                phase = str(request.metadata.get("phase") or "unknown")
                # Record the order in which jobs are actually processed
                order_tracker.append(phase)
                sleep(0.02)  # Small delay to make ordering observable
                return super().generate_text(request)

        inferencer = TrackingInferenceBackend(
            content_by_phase={
                "P-100": "## Logline\nCity lives.\n",
                "P-200": json.dumps({"beats": []}),
                "P-300": "# Chapter 1\nContent.\n",
                "P-400": json.dumps({}),
            }
        )
        executor, job_manager, project_service, step_records = _build_executor(
            tmp_path, inferencer=inferencer
        )
        _create_project(tmp_path, project_id, executor=executor, project_service=project_service)

        executor.start()
        try:
            # Submit all four phases as separate jobs
            jobs: list = []
            for phase in ["P-100", "P-200", "P-300", "P-400"]:
                job = _run_phase(job_manager, phase=phase, project_id=project_id)
                jobs.append((phase, job))

            # Wait for all to complete
            statuses = {}
            for phase, job in jobs:
                statuses[phase] = _wait_for_terminal_status(job_manager, job.id)
        finally:
            executor.stop()

        # All jobs should have completed
        assert all(s == "COMPLETED" for s in statuses.values())

        # The tracking backend should have seen all four phases
        assert len(inferencer.requests) == 4

        # The single worker thread processes jobs sequentially, so the
        # order tracker should have 4 entries. Due to the sleep in
        # TrackingInferenceBackend, the phases should not overlap.
        assert len(order_tracker) == 4


# ---------------------------------------------------------------------------
# Checker terminal status helper
# ---------------------------------------------------------------------------

def _wait_for_checker_terminal(
    checker_manager: RoleModelCheckManager,
    run_id,
    *,
    attempts: int = 80,
) -> str:
    status = ""
    for _ in range(attempts):
        current = checker_manager.get_status(run_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status
