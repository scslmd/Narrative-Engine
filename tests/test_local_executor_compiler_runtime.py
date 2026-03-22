from __future__ import annotations

import json
from pathlib import Path
from time import sleep
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import build_jobs_router
from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.sqlite import connect
from app.persistence.steps import stable_hash_payload
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
from app.schemas.jobs import JobCreateRequest
from app.schemas.manifest import Manifest
from app.services.job_manager import JobManager
from app.services.local_executor import LocalExecutor
from app.services.project_bootstrap import initialize_project_artifacts
from app.services.projects import ProjectService
from app.services.role_model_check_manager import RoleModelCheckManager
from app.services.role_model_checker import RoleModelCheckerService
from app.services.runtime_prompts import build_p400_compiler_request, story_bible_output_path
from app.services.step_records import StepRecordService


class FakePipelineInferenceBackend(InferenceBackend):
    def __init__(
        self,
        *,
        content_by_phase: dict[str, str | list[str]],
        model: str = "pipeline-fake-model",
        failing_phases: set[str] | None = None,
    ) -> None:
        self.requests: list[InferenceRequest] = []
        self._content_by_phase = content_by_phase
        self._failing_phases = failing_phases or set()
        self._phase_call_counts: dict[str, int] = {}
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Pipeline Runtime",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-pipeline"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        phase = str(request.metadata.get("phase") or "unknown")
        if phase in self._failing_phases:
            raise InferenceBackendError(
                "Fake Pipeline Runtime request failed: timed out",
                category="timeout",
                code="INFERENCE_TIMEOUT",
                finish_reason="timeout",
                retryable=True,
            )
        phase_index = self._phase_call_counts.get(phase, 0)
        self._phase_call_counts[phase] = phase_index + 1
        phase_content = self._content_by_phase.get(phase, f"{phase} runtime content.")
        if isinstance(phase_content, list):
            content = phase_content[min(phase_index, len(phase_content) - 1)]
        else:
            content = phase_content
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=377, completion_tokens=455, total_tokens=832),
            raw_response={"backend": "fake", "backend_version": "2026.06"},
        )


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


def _build_executor(tmp_path: Path, *, inferencer: InferenceBackend) -> tuple[LocalExecutor, JobManager, ProjectService]:
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
        role_check_service=RoleModelCheckerService(models_root, reports_root, inferencer=inferencer),
        inferencer=inferencer,
        project_service=project_service,
        step_record_service=step_records,
        poll_interval_seconds=0.05,
    )
    return executor, job_manager, project_service


def _build_test_app(*, job_manager: JobManager) -> FastAPI:
    app = FastAPI()
    app.include_router(build_jobs_router(job_manager))
    return app


def _wait_for_terminal_status(job_manager: JobManager, job_id, *, attempts: int = 40) -> str:
    status = ""
    for _ in range(attempts):
        current = job_manager.get_status(job_id)
        status = str(current.status)
        if status in {"COMPLETED", "FAILED"}:
            return status
        sleep(0.05)
    return status


def _run_phase(job_manager: JobManager, *, phase: str, project_id: str, payload: dict[str, object] | None = None):
    return job_manager.create_job(
        JobCreateRequest(
            phase=phase,
            payload={"project_id": project_id, **(payload or {})},
        )
    )


def test_local_executor_runs_real_compiler_path_for_p400_with_fake_inferencer(tmp_path: Path) -> None:
    project_id = "compiler-test"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    story_bible_content = json.dumps(
        {
            "project": {"project_id": project_id, "project_name": "Project Aurora"},
            "premise": "A cartographer maps a city that rearranges itself every dusk.",
            "world_anchors": ["The city reconfigures at dusk."],
            "character_threads": ["The cartographer tracks impossible streets."],
            "continuity_notes": ["Chapter 1 opens after the sequence foundation."],
            "open_questions": ["Why is the city alive?"],
        },
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": [{"id": "beat-1", "title": "Opening"}]}, ensure_ascii=True, indent=2, sort_keys=True),
            "P-300": "# Chapter 1\nThe city changes shape just before dawn.\n",
            "P-400": story_bible_content,
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    app = _build_test_app(job_manager=job_manager)

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id, payload={"model_id": "architect-override-model"})
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id, payload={"model_id": "sequencer-override-model"})
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id, payload={"model_id": "drafter-override-model"})
        assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"
        p400 = _run_phase(job_manager, phase="P-400", project_id=project_id, payload={"model_id": "compiler-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p400.id)
    finally:
        executor.stop()

    request_payload = job_manager.get_request_payload(p400.id)
    expected_request = build_p400_compiler_request(
        manifest=manifest,
        payload=dict(request_payload.get("payload", {})),
        architect_output=project_service.read_artifact(project_id, "architect_p100").content,
        sequence_output=project_service.read_artifact(project_id, "sequence").content,
        chapter_output=project_service.read_artifact(project_id, "chapter_1").content,
        default_model=inferencer.descriptor.default_model,
    )
    output_path = story_bible_output_path(Path(tmp_path) / "data" / "projects" / project_id)
    steps = job_manager.list_step_records(p400.id)
    lineage = job_manager.list_artifact_lineage(p400.id)
    request = inferencer.requests[-1]

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{p400.id}/steps")
        lineage_response = client.get(f"/jobs/{p400.id}/lineage")

    assert final_status == "COMPLETED"
    assert request.model == expected_request.model
    assert request.temperature == expected_request.temperature
    assert request.max_tokens == expected_request.max_tokens
    assert request.metadata == expected_request.metadata
    assert "Compiler role for Narrative-Engine" in request.messages[0].content
    assert "P-400 compiler story bible snapshot" in request.messages[1].content
    assert request.metadata["phase"] == "P-400"
    assert request.metadata["role"] == "compiler"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == story_bible_content + "\n"

    assert len(steps) == 1
    assert steps[0]["step_name"] == "compiler"
    assert steps[0]["state"] == "COMPLETED"
    assert steps[0]["model_id"] == "compiler-override-model"
    assert steps[0]["backend_name"] == "Fake Pipeline Runtime"
    assert steps[0]["backend_version"] == "2026.06"
    assert steps[0]["input_artifact_refs"] == ["manifest", "architect_output", "sequence", "chapter_1"]
    assert steps[0]["output_artifact_refs"] == ["story_bible"]
    assert steps[0]["finish_reason"] == "stop"
    assert steps[0]["prompt_hash"] == stable_hash_payload(request.model_dump(mode="json"))
    assert steps[0]["output_hash"] == stable_hash_payload(
        {
            "backend": "openai_compatible",
            "model": "compiler-override-model",
            "content": story_bible_content + "\n",
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 377,
                "completion_tokens": 455,
                "total_tokens": 832,
            },
            "artifact_path": str(output_path),
        }
    )

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        telemetry_row = connection.execute(
            """
            SELECT prompt_tokens, completion_tokens, total_tokens
            FROM step_records
            WHERE run_id = ? AND step_name = 'compiler'
            """,
            (str(p400.id),),
        ).fetchone()

    assert telemetry_row is not None
    assert telemetry_row["prompt_tokens"] == 377
    assert telemetry_row["completion_tokens"] == 455
    assert telemetry_row["total_tokens"] == 832

    assert len(lineage) == 1
    assert lineage[0]["artifact_role"] == "story_bible"
    assert lineage[0]["artifact_kind"] == "json"
    assert lineage[0]["status"] == "CANONICAL"
    assert lineage[0]["validation_state"] == "PASSED"
    assert lineage[0]["path"] == str(output_path)
    assert project_service.read_artifact(project_id, "story_bible").content == story_bible_content + "\n"
    assert project_service.repository.get_artifact_path(project_id, "story_bible") == output_path

    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        selection_rows = connection.execute(
            """
            SELECT artifact_role, selected_artifact_lineage_id, selected_content
            FROM runtime_artifact_selections
            WHERE run_id = ? AND run_kind = 'pipeline_job' AND step_name = 'compiler'
            ORDER BY selection_id ASC
            """,
            (str(p400.id),),
        ).fetchall()

    assert [row["artifact_role"] for row in selection_rows] == ["architect_output", "sequence", "chapter_1"]
    assert all(row["selected_artifact_lineage_id"] is not None for row in selection_rows)
    assert selection_rows[0]["selected_content"] == project_service.read_artifact(project_id, "architect_p100").content
    assert selection_rows[1]["selected_content"] == project_service.read_artifact(project_id, "sequence").content
    assert selection_rows[2]["selected_content"] == project_service.read_artifact(project_id, "chapter_1").content

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["compiler"]
    assert steps_response.json()["meta"]["ordered_by"] == "step_index_asc"
    assert lineage_response.status_code == 200
    assert [item["artifact_role"] for item in lineage_response.json()["items"]] == ["story_bible"]
    assert lineage_response.json()["meta"]["ordered_by"] == "artifact_lineage_id_asc"


def test_local_executor_supersedes_story_bible_lineage_on_repeated_p400_runs(tmp_path: Path) -> None:
    project_id = "story-bible-supersession"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    story_bible_v1 = json.dumps(
        {
            "project": {"project_id": project_id, "project_name": "Project Aurora"},
            "premise": "v1",
            "world_anchors": [],
            "character_threads": [],
            "continuity_notes": [],
            "open_questions": [],
        },
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    story_bible_v2 = json.dumps(
        {
            "project": {"project_id": project_id, "project_name": "Project Aurora"},
            "premise": "v2",
            "world_anchors": [],
            "character_threads": [],
            "continuity_notes": [],
            "open_questions": [],
        },
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    )
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": [{"id": "beat-1", "title": "Opening"}]}, ensure_ascii=True, indent=2, sort_keys=True),
            "P-300": "# Chapter 1\nThe city changes shape just before dawn.\n",
            "P-400": [story_bible_v1, story_bible_v2],
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"
        first_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, first_p400.id) == "COMPLETED"
        second_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, second_p400.id) == "COMPLETED"
    finally:
        executor.stop()

    first_lineage = job_manager.list_artifact_lineage(first_p400.id)
    second_lineage = job_manager.list_artifact_lineage(second_p400.id)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT artifact_lineage_id, status, supersedes_artifact_lineage_id
            FROM artifact_lineage
            WHERE project_id = ? AND artifact_role = 'story_bible'
            ORDER BY artifact_lineage_id ASC
            """,
            (project_id,),
        ).fetchall()

    assert len(rows) == 2
    assert rows[0]["status"] == "SUPERSEDED"
    assert rows[1]["status"] == "CANONICAL"
    assert rows[1]["supersedes_artifact_lineage_id"] == rows[0]["artifact_lineage_id"]
    assert first_lineage[0]["status"] == "SUPERSEDED"
    assert second_lineage[0]["status"] == "CANONICAL"
    assert second_lineage[0]["supersedes_artifact_lineage_id"] == rows[0]["artifact_lineage_id"]
    assert project_service.read_artifact(project_id, "story_bible").content == story_bible_v2 + "\n"
    assert project_service.repository.get_artifact_path(project_id, "story_bible") == story_bible_output_path(
        Path(tmp_path) / "data" / "projects" / project_id
    )


def test_local_executor_p400_uses_latest_registered_upstream_artifacts(tmp_path: Path) -> None:
    project_id = "compiler-latest-upstream"
    manifest = _make_manifest(project_id)
    initialize_project_artifacts(project_id, manifest=manifest, root_dir=tmp_path)
    sequence_v1 = json.dumps({"beats": [{"id": "beat-1", "title": "Sequence v1"}]}, ensure_ascii=True, indent=2, sort_keys=True)
    sequence_v2 = json.dumps({"beats": [{"id": "beat-2", "title": "Sequence v2"}]}, ensure_ascii=True, indent=2, sort_keys=True)
    chapter_v1 = "# Chapter 1\nChapter v1 follows the first impossible street.\n"
    chapter_v2 = "# Chapter 1\nChapter v2 maps the city's second impossible turn.\n"
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": [sequence_v1, sequence_v2],
            "P-300": [chapter_v1, chapter_v2],
            "P-400": [
                json.dumps({"project": {"project_id": project_id}, "premise": "first compiler run", "world_anchors": [], "character_threads": [], "continuity_notes": [], "open_questions": []}, ensure_ascii=True, indent=2, sort_keys=True),
                json.dumps({"project": {"project_id": project_id}, "premise": "second compiler run", "world_anchors": [], "character_threads": [], "continuity_notes": [], "open_questions": []}, ensure_ascii=True, indent=2, sort_keys=True),
            ],
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        first_p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, first_p200.id) == "COMPLETED"
        first_p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, first_p300.id) == "COMPLETED"
        first_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, first_p400.id) == "COMPLETED"
        second_p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, second_p200.id) == "COMPLETED"
        second_p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, second_p300.id) == "COMPLETED"
        second_p400 = _run_phase(job_manager, phase="P-400", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, second_p400.id) == "COMPLETED"
    finally:
        executor.stop()

    second_compiler_request = inferencer.requests[-1]
    second_lineage = job_manager.list_artifact_lineage(second_p400.id)
    with connect(tmp_path / "data" / "state" / "narrative_ops.db") as connection:
        selection_rows = connection.execute(
            """
            SELECT artifact_role, selected_content
            FROM runtime_artifact_selections
            WHERE run_id = ? AND run_kind = 'pipeline_job' AND step_name = 'compiler'
            ORDER BY selection_id ASC
            """,
            (str(second_p400.id),),
        ).fetchall()

    assert "Sequence v2" in second_compiler_request.messages[1].content
    assert "Chapter v2 maps the city's second impossible turn." in second_compiler_request.messages[1].content
    assert "Sequence v1" not in second_compiler_request.messages[1].content
    assert "Chapter v1 follows the first impossible street." not in second_compiler_request.messages[1].content
    assert [row["artifact_role"] for row in selection_rows] == ["architect_output", "sequence", "chapter_1"]
    assert selection_rows[1]["selected_content"] == project_service.read_artifact(project_id, "sequence").content
    assert selection_rows[2]["selected_content"] == project_service.read_artifact(project_id, "chapter_1").content
    assert second_lineage[0]["source_content_hashes"] == [
        stable_hash_payload(manifest.model_dump(mode="json")),
        stable_hash_payload(project_service.read_artifact(project_id, "architect_p100").content),
        stable_hash_payload(project_service.read_artifact(project_id, "sequence").content),
        stable_hash_payload(project_service.read_artifact(project_id, "chapter_1").content),
    ]


def test_local_executor_persists_mapped_runtime_error_for_p400_failures(tmp_path: Path) -> None:
    project_id = "compiler-timeout"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": []}, ensure_ascii=True),
            "P-300": "# Chapter 1\nA placeholder chapter.\n",
            "P-400": "unused",
        },
        failing_phases={"P-400"},
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    app = _build_test_app(job_manager=job_manager)

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"
        p400 = _run_phase(job_manager, phase="P-400", project_id=project_id, payload={"model_id": "compiler-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p400.id)
    finally:
        executor.stop()

    status = job_manager.get_status(p400.id)
    attempt = job_manager.get_attempt(p400.id)
    steps = job_manager.list_step_records(p400.id)
    lineage = job_manager.list_artifact_lineage(p400.id)
    output_path = story_bible_output_path(Path(tmp_path) / "data" / "projects" / project_id)

    with TestClient(app) as client:
        steps_response = client.get(f"/jobs/{p400.id}/steps")
        lineage_response = client.get(f"/jobs/{p400.id}/lineage")

    assert final_status == "FAILED"
    assert status.error == "INFERENCE_TIMEOUT"
    assert status.current_step == "compiler"
    assert attempt["finish_reason"] == "timeout"
    assert attempt["failure_stage"] == "inference"
    assert attempt["retryable"] == 1
    assert attempt["error_code"] == "INFERENCE_TIMEOUT"
    assert attempt["error_category"] == "timeout"
    assert len(steps) == 1
    assert steps[0]["step_name"] == "compiler"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "timeout"
    assert steps[0]["error_code"] == "INFERENCE_TIMEOUT"
    assert steps[0]["error_category"] == "timeout"
    assert steps[0]["output_hash"] is None
    assert steps[0]["input_artifact_refs"] == ["manifest", "architect_output", "sequence", "chapter_1"]
    assert lineage == []
    assert not output_path.exists()
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "story_bible")

    assert steps_response.status_code == 200
    assert [item["step_name"] for item in steps_response.json()["items"]] == ["compiler"]
    assert steps_response.json()["items"][0]["state"] == "FAILED"
    assert lineage_response.status_code == 200
    assert lineage_response.json()["items"] == []


def test_local_executor_removes_story_bible_file_when_p400_finalization_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = "compiler-persistence-failure"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": [{"id": "beat-1", "title": "Opening"}]}, ensure_ascii=True, indent=2, sort_keys=True),
            "P-300": "# Chapter 1\nThe city changes shape just before dawn.\n",
            "P-400": json.dumps(
                {
                    "project": {"project_id": project_id, "project_name": "Project Aurora"},
                    "premise": "persistence failure path",
                    "world_anchors": [],
                    "character_threads": [],
                    "continuity_notes": [],
                    "open_questions": [],
                },
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            ),
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    output_path = story_bible_output_path(Path(tmp_path) / "data" / "projects" / project_id)

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"

        original_create_lineage_record = executor._step_records.create_lineage_record

        def failing_create_lineage_record(**kwargs):
            if kwargs.get("artifact_role") == "story_bible":
                raise RuntimeError("simulated lineage persistence failure")
            return original_create_lineage_record(**kwargs)

        monkeypatch.setattr(executor._step_records, "create_lineage_record", failing_create_lineage_record)

        p400 = _run_phase(job_manager, phase="P-400", project_id=project_id, payload={"model_id": "compiler-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p400.id)
    finally:
        executor.stop()

    status = job_manager.get_status(p400.id)
    attempt = job_manager.get_attempt(p400.id)
    lineage = job_manager.list_artifact_lineage(p400.id)

    assert final_status == "FAILED"
    assert status.current_step == "compiler"
    assert status.error == "simulated lineage persistence failure"
    assert attempt["failure_stage"] == "persistence"
    assert attempt["error_category"] == "persistence"
    assert lineage == []
    steps = job_manager.list_step_records(p400.id)
    assert len(steps) == 1
    assert steps[0]["step_name"] == "compiler"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "persistence_error"
    assert steps[0]["error_category"] == "persistence"
    assert not output_path.exists()
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "story_bible")


def test_local_executor_rolls_back_story_bible_projection_when_project_db_registration_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = "compiler-project-db-failure"
    initialize_project_artifacts(project_id, manifest=_make_manifest(project_id), root_dir=tmp_path)
    inferencer = FakePipelineInferenceBackend(
        content_by_phase={
            "P-100": "## Logline\nA mapmaker learns her city is alive.\n",
            "P-200": json.dumps({"beats": [{"id": "beat-1", "title": "Opening"}]}, ensure_ascii=True, indent=2, sort_keys=True),
            "P-300": "# Chapter 1\nThe city changes shape just before dawn.\n",
            "P-400": json.dumps(
                {
                    "project": {"project_id": project_id, "project_name": "Project Aurora"},
                    "premise": "project db registration failure path",
                    "world_anchors": [],
                    "character_threads": [],
                    "continuity_notes": [],
                    "open_questions": [],
                },
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            ),
        },
    )
    executor, job_manager, project_service = _build_executor(tmp_path, inferencer=inferencer)
    project_service.reconcile_projects()
    output_path = story_bible_output_path(Path(tmp_path) / "data" / "projects" / project_id)
    original_upsert_project_db_artifact = project_service.repository._upsert_project_db_artifact

    def fail_project_db_write(**kwargs):
        if kwargs.get("artifact_type") == "story_bible":
            raise RuntimeError("simulated project db artifact registration failure")
        return original_upsert_project_db_artifact(**kwargs)

    monkeypatch.setattr(project_service.repository, "_upsert_project_db_artifact", fail_project_db_write)

    executor.start()
    try:
        p100 = _run_phase(job_manager, phase="P-100", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p100.id) == "COMPLETED"
        p200 = _run_phase(job_manager, phase="P-200", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p200.id) == "COMPLETED"
        p300 = _run_phase(job_manager, phase="P-300", project_id=project_id)
        assert _wait_for_terminal_status(job_manager, p300.id) == "COMPLETED"
        p400 = _run_phase(job_manager, phase="P-400", project_id=project_id, payload={"model_id": "compiler-override-model"})
        final_status = _wait_for_terminal_status(job_manager, p400.id)
    finally:
        executor.stop()

    status = job_manager.get_status(p400.id)
    attempt = job_manager.get_attempt(p400.id)
    steps = job_manager.list_step_records(p400.id)
    lineage = job_manager.list_artifact_lineage(p400.id)

    assert final_status == "FAILED"
    assert status.error == "simulated project db artifact registration failure"
    assert attempt["failure_stage"] == "persistence"
    assert attempt["error_category"] == "persistence"
    assert len(steps) == 1
    assert steps[0]["step_name"] == "compiler"
    assert steps[0]["state"] == "FAILED"
    assert steps[0]["finish_reason"] == "persistence_error"
    assert steps[0]["error_category"] == "persistence"
    assert lineage == []
    assert not output_path.exists()
    assert project_service.repository.get_artifact_path(project_id, "story_bible") is None
    with pytest.raises(FileNotFoundError):
        project_service.read_artifact(project_id, "story_bible")


def test_local_executor_fails_unsupported_job_phases_instead_of_stub_completing() -> None:
    job_id = uuid4()

    class FakeJobManager:
        def __init__(self) -> None:
            self.updates: list[dict[str, object]] = []

        def get_status(self, _job_id):
            return SimpleNamespace(phase="P-900", status="PENDING")

        def get_attempt(self, _job_id):
            return {
                "logical_run_id": str(job_id),
                "attempt_number": 1,
                "lease_owner": "job-worker-local",
            }

        def get_request_payload(self, _job_id):
            return {"payload": {"project_id": "science-fantasy-test"}}

        def update_job(self, _job_id, **kwargs):
            self.updates.append(kwargs)
            return SimpleNamespace(phase="P-900", status=kwargs.get("status", "PENDING"))

        def log(self, _job_id, _level, _message) -> None:
            return None

    class FakeStepRecords:
        def __init__(self) -> None:
            self.rows: list[dict[str, object]] = []

        def create_step_record(self, **kwargs):
            self.rows.append(kwargs)
            return 1

    fake_job_manager = FakeJobManager()
    fake_step_records = FakeStepRecords()
    executor = LocalExecutor(
        job_manager=fake_job_manager,  # type: ignore[arg-type]
        role_check_manager=SimpleNamespace(),  # type: ignore[arg-type]
        role_check_service=SimpleNamespace(),  # type: ignore[arg-type]
        step_record_service=fake_step_records,  # type: ignore[arg-type]
    )

    executor._process_job(job_id)

    assert len(fake_job_manager.updates) == 1
    assert fake_job_manager.updates[-1]["status"] == "FAILED"
    assert fake_job_manager.updates[-1]["finish_reason"] == "executor_error"
    assert fake_job_manager.updates[-1]["failure_stage"] == "run"
    assert "Unsupported job phase: P-900" in str(fake_job_manager.updates[-1]["error"])
    assert len(fake_step_records.rows) == 1
    assert fake_step_records.rows[0]["state"] == "FAILED"
    assert fake_step_records.rows[0]["step_name"] == "P-900"
    assert fake_step_records.rows[0]["finish_reason"] == "executor_error"
    assert "Unsupported job phase: P-900" in str(fake_step_records.rows[0]["output_payload"])
