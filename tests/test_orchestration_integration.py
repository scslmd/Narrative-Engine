"""Integration tests for orchestration persistence and runtime behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.persistence.steps import (
    ArtifactLineageRepository,
    RuntimeArtifactSelectionRepository,
    StepRecordRepository,
)
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.chapter_packets import ChapterPacketService
from app.services.drafting import DraftingService
from app.services.sequence_plans import SequencePlanService
from app.services.storyboard_cards import StoryboardCardService
from app.schemas import StoryArtifactLifecycleState

from app.persistence.sqlite import connect, ensure_operations_db


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _make_db(tmp_path: Path) -> Path:
    return tmp_path / "data" / "state" / "narrative_ops.db"


def _seed_project(db_path: Path, project_id: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                f"Test Project {project_id[:8]}",
                f"data/projects/{project_id}/manifest.json",
                f"data/projects/{project_id}/bible.db",
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


class TestOrchestrationPersistenceIntegration:
    """Test that orchestration persistence layers work together correctly."""

    def test_step_record_and_lineage_lifecycle(self, tmp_path: Path) -> None:
        """A step record followed by a lineage record should be queryable by both run and project."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        steps_repo = StepRecordRepository(db_path)
        lineage_repo = ArtifactLineageRepository(db_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        run_id = f"run-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        # Create a step record
        step_id = steps_repo.create_step_record(
            logical_run_id="architect-p100",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="architect",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="llama-3",
            critic_profile=None,
            backend_name="llama.cpp",
            backend_version="0.2.0",
            input_hash="hash-abc",
            output_hash="hash-def",
            prompt_hash="hash-pmt",
            input_artifact_refs=[],
            output_artifact_refs=["architect-output"],
            started_at=STAMP,
            finished_at=STAMP,
            duration_seconds=2.5,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )
        assert step_id > 0

        # Create a lineage record pointing to that step
        lineage_id = lineage_repo.create_lineage_record(
            logical_run_id="architect-p100",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="architect",
            project_id=project_id,
            artifact_role="architect_output",
            artifact_kind="json",
            path=f"/data/projects/{project_id}/architect.json",
            content_hash="content-hash-1",
            status=StoryArtifactLifecycleState.CANONICAL,
            validation_state="validated",
            produced_at=STAMP,
            registered_at=STAMP,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=[],
            source_content_hashes=[],
            output_of_step_record_id=step_id,
        )
        assert lineage_id > 0

        # Query by run
        steps_by_run = steps_repo.list_for_run(
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
        )
        assert len(steps_by_run) == 1
        assert steps_by_run[0]["step_name"] == "architect"

        lineage_by_run = lineage_repo.list_for_run(
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
        )
        assert len(lineage_by_run) == 1
        assert lineage_by_run[0]["artifact_role"] == "architect_output"

        # Query by project
        lineage_by_project = lineage_repo.list_for_project(
            project_id=project_id,
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert len(lineage_by_project) == 1
        assert lineage_by_project[0]["artifact_role"] == "architect_output"

        # Latest canonical for project
        latest = lineage_repo.latest_canonical_for_project(project_id=project_id)
        assert latest is not None
        assert latest["artifact_role"] == "architect_output"

    def test_canonical_supersession_by_project(self, tmp_path: Path) -> None:
        """Successive CANONICAL artifacts for the same role should supersede prior ones."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        steps_repo = StepRecordRepository(db_path)
        lineage_repo = ArtifactLineageRepository(db_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        run_id = f"run-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        # Create prerequisite step records (FK requires output_of_step_record_id)
        first_step_id = steps_repo.create_step_record(
            logical_run_id="p100-1",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="architect",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="llama-3",
            critic_profile=None,
            backend_name="llama.cpp",
            backend_version="0.2.0",
            input_hash="hash-abc",
            output_hash="hash-def",
            prompt_hash="hash-pmt",
            input_artifact_refs=[],
            output_artifact_refs=["architect-output"],
            started_at=STAMP,
            finished_at=STAMP,
            duration_seconds=2.5,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )
        second_step_id = steps_repo.create_step_record(
            logical_run_id="p100-2",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=2,
            step_name="architect",
            step_index=2,
            state="COMPLETED",
            project_id=project_id,
            model_id="llama-3",
            critic_profile=None,
            backend_name="llama.cpp",
            backend_version="0.2.0",
            input_hash="hash-abc",
            output_hash="hash-def",
            prompt_hash="hash-pmt",
            input_artifact_refs=[],
            output_artifact_refs=["architect-output"],
            started_at=STAMP,
            finished_at=STAMP,
            duration_seconds=2.5,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        first_id = lineage_repo.create_lineage_record(
            logical_run_id="p100-1",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="architect",
            project_id=project_id,
            artifact_role="architect_output",
            artifact_kind="json",
            path="/first.json",
            content_hash="h1",
            status=StoryArtifactLifecycleState.CANONICAL,
            validation_state="validated",
            produced_at=STAMP,
            registered_at=STAMP,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=[],
            source_content_hashes=[],
            output_of_step_record_id=first_step_id,
        )

        second_id = lineage_repo.create_lineage_record(
            logical_run_id="p100-2",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=2,
            step_name="architect",
            project_id=project_id,
            artifact_role="architect_output",
            artifact_kind="json",
            path="/second.json",
            content_hash="h2",
            status=StoryArtifactLifecycleState.CANONICAL,
            validation_state="validated",
            produced_at=STAMP,
            registered_at=STAMP,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=[],
            source_content_hashes=[],
            output_of_step_record_id=second_step_id,
        )

        assert second_id > first_id

        # Only the second should be CANONICAL now
        canonical_rows = lineage_repo.list_for_project(
            project_id=project_id,
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert len(canonical_rows) == 1
        assert canonical_rows[0]["artifact_lineage_id"] == second_id

        # First should be SUPERSEDED
        superseded_rows = lineage_repo.list_for_project(
            project_id=project_id,
            status="SUPERSEDED",
        )
        assert len(superseded_rows) == 1
        assert superseded_rows[0]["artifact_lineage_id"] == first_id

    def test_runtime_artifact_selections_project_scoped(self, tmp_path: Path) -> None:
        """Selections should be listable by project and by run."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        steps_repo = StepRecordRepository(db_path)
        lineage_repo = ArtifactLineageRepository(db_path)
        selections_repo = RuntimeArtifactSelectionRepository(db_path)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        run_id = f"run-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        # Create prerequisite step records
        step_id = steps_repo.create_step_record(
            logical_run_id="sequencer-p200",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="llama-3",
            critic_profile=None,
            backend_name="llama.cpp",
            backend_version="0.2.0",
            input_hash="hash-abc",
            output_hash="hash-def",
            prompt_hash="hash-pmt",
            input_artifact_refs=[],
            output_artifact_refs=["architect-output"],
            started_at=STAMP,
            finished_at=STAMP,
            duration_seconds=2.5,
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        # Create prerequisite lineage records (FK requires selected_artifact_lineage_id to exist)
        first_lineage_id = lineage_repo.create_lineage_record(
            logical_run_id="sequencer-p200",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
            project_id=project_id,
            artifact_role="architect_output",
            artifact_kind="json",
            path="/data/architect.json",
            content_hash="hash-abc",
            status=StoryArtifactLifecycleState.CANONICAL,
            validation_state="validated",
            produced_at=STAMP,
            registered_at=STAMP,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=[],
            source_content_hashes=[],
            output_of_step_record_id=step_id,
        )
        second_lineage_id = lineage_repo.create_lineage_record(
            logical_run_id="sequencer-p200",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
            project_id=project_id,
            artifact_role="sequence",
            artifact_kind="json",
            path="/data/sequence.json",
            content_hash="hash-def",
            status=StoryArtifactLifecycleState.CANONICAL,
            validation_state="validated",
            produced_at=STAMP,
            registered_at=STAMP,
            supersedes_artifact_lineage_id=None,
            source_artifact_refs=[],
            source_content_hashes=[],
            output_of_step_record_id=step_id,
        )

        selections_repo.create_or_replace_selection(
            logical_run_id="sequencer-p200",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
            project_id=project_id,
            artifact_role="architect_output",
            selected_artifact_lineage_id=first_lineage_id,
            selected_path="/data/architect.json",
            selected_content_hash="hash-abc",
            selected_content="architect content here",
            selected_at=STAMP,
        )

        selections_repo.create_or_replace_selection(
            logical_run_id="sequencer-p200",
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
            project_id=project_id,
            artifact_role="sequence",
            selected_artifact_lineage_id=second_lineage_id,
            selected_path="/data/sequence.json",
            selected_content_hash="hash-def",
            selected_content="sequence content here",
            selected_at=STAMP,
        )

        # List by run
        by_run = selections_repo.list_for_run(
            run_id=run_id,
            run_kind="pipeline_job",
            attempt_number=1,
            step_name="sequencer",
        )
        assert len(by_run) == 2

        # List by project
        by_project = selections_repo.list_selections_by_project(project_id=project_id)
        assert len(by_project) == 2

        # List by project with artifact_role filter
        by_project_role = selections_repo.list_selections_by_project(
            project_id=project_id,
            artifact_role="sequence",
        )
        assert len(by_project_role) == 1
        assert by_project_role[0]["artifact_role"] == "sequence"


class TestServiceLayerIntegration:
    """Test service layer integration with persistence."""

    def test_chapter_packet_service_with_repository(self, tmp_path: Path) -> None:
        """ChapterPacketService should correctly interact with the repository."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        service = ChapterPacketService(repo)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)
        packet_id = f"packet-{uuid4().hex[:8]}"
        chapter_id = f"ch-{uuid4().hex[:8]}"

        # Seed chapter_plan (FK constraint: chapter_packets.chapter_id -> chapter_plans.chapter_id)
        with connect(db_path) as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO chapter_plans (
                    chapter_id, project_id, sequence_id, title, summary,
                    objective, conflict, stakes, status, position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chapter_id,
                    project_id,
                    None,
                    f"Chapter {chapter_id[-4:]}",
                    "Chapter summary",
                    "Chapter objective",
                    "Chapter conflict",
                    "Chapter stakes",
                    "draft",
                    0,
                    STAMP.isoformat(),
                    STAMP.isoformat(),
                ),
            )
            connection.commit()

        record = service.register_packet(
            project_id,
            packet_id=packet_id,
            chapter_id=chapter_id,
            included_reference_ids=["ref-1", "ref-2"],
            constraints=["No profanity"],
            scene_goals=["Introduce protagonist", "Establish setting"],
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert record.packet_id == packet_id
        assert record.project_id == project_id
        assert record.chapter_id == chapter_id
        assert len(record.included_reference_ids) == 2
        assert len(record.constraints) == 1
        assert len(record.scene_goals) == 2

        packets = service.list_packets(project_id)
        assert len(packets) == 1
        assert packets[0].packet_id == packet_id

    def test_sequence_plan_service_with_repository(self, tmp_path: Path) -> None:
        """SequencePlanService should correctly interact with the repository."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        service = SequencePlanService(repo)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)
        seq_id = f"seq-{uuid4().hex[:8]}"

        record = service.register_plan(
            project_id,
            sequence_id=seq_id,
            title="Main Arc",
            summary="The primary narrative arc",
            beat_ids=["beat-1"],
            chapter_ids=["ch-1"],
            position=0,
        )
        assert record.sequence_id == seq_id
        assert record.title == "Main Arc"

        # Update status
        updated = service.update_plan_status(seq_id, StoryArtifactLifecycleState.CANONICAL)
        assert updated.status == StoryArtifactLifecycleState.CANONICAL

        # List should include the plan
        plans = service.list_plans(project_id)
        assert len(plans) == 1

        # Non-existent plan should raise
        with pytest.raises(Exception):
            service.get_plan("non-existent-seq")

    def test_storyboard_card_service_with_repository(self, tmp_path: Path) -> None:
        """StoryboardCardService should correctly interact with the repository."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        service = StoryboardCardService(repo)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)
        card_id = f"card-{uuid4().hex[:8]}"

        record = service.create_card(
            project_id,
            card_id=card_id,
            title="Opening Scene",
            content="The protagonist enters the room.",
            card_type="scene",
            column_id="planned",
            position=0,
            tags=["important"],
            character_ids=["hero-1"],
            metadata={"scene_number": 1},
        )
        assert record.card_id == card_id
        assert record.card_type == "scene"
        assert "important" in record.tags

        # Get by ID
        fetched = service.get_card(card_id)
        assert fetched.card_id == card_id

        # List with filter
        cards = service.list_cards(project_id, filter_options=None)
        assert len(cards) == 1

        # Update content
        updated = service.update_card_content(
            card_id,
            title="Updated Title",
            content="New content here",
            card_type="scene",
        )
        assert updated.title == "Updated Title"

        # Validation error on bad card_type
        with pytest.raises(Exception):
            service.create_card(
                project_id,
                card_id=f"card-bad-{uuid4().hex[:8]}",
                title="Bad Card",
                content="Bad content",
                card_type="invalid_type",
            )

    def test_drafting_service_integration(self, tmp_path: Path) -> None:
        """DraftingService should correctly create and retrieve artifacts."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        service = DraftingService(repo)
        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)
        artifact_id = f"draft-{uuid4().hex[:8]}"

        draft = service.register_draft_artifact(
            project_id,
            artifact_id=artifact_id,
            title="Chapter One Draft",
            content="Once upon a time...",
            source_plan_ids=["ch-1"],
            provenance_note="Generated from chapter plan",
            status=StoryArtifactLifecycleState.DRAFT,
        )
        assert draft.artifact_id == artifact_id
        assert draft.project_id == project_id
        assert draft.content == "Once upon a time..."

        # List artifacts
        artifacts = service.list_draft_artifacts(project_id)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_id == artifact_id
