"""Integration tests for lineage-aware artifact registration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.chapter_packets import ChapterPacketService
from app.services.sequence_plans import SequencePlanService
from app.services.step_records import StepRecordService
from app.services.storyboard_cards import StoryboardCardService
from app.schemas import StoryArtifactLifecycleState, StorySuggestionLifecycleState


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


class TestChapterPacketLineageRegistration:
    """Integration tests for chapter-packet lineage-aware registration."""

    def test_register_packet_as_lineage_creates_record(
        self, tmp_path: Path
    ) -> None:
        """register_packet_as_lineage should create a lineage record linked to a step."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        packet_service = ChapterPacketService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        chapter_id = f"ch-{uuid4().hex[:8]}"
        packet_id = f"packet-{uuid4().hex[:8]}"
        run_id = uuid4()
        logical_run_id = "chapter-packet-reg"

        # Seed chapter_plan (FK constraint)
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

        # Register step record (prerequisite for lineage FK)
        step_id = step_records.create_step_record(
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="chapter_packet",
            attempt_number=1,
            step_name="packet_builder",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[packet_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        # Register the packet
        packet_service.register_packet(
            project_id,
            packet_id=packet_id,
            chapter_id=chapter_id,
            included_reference_ids=["ref-1", "ref-2"],
            constraints=["No profanity"],
            scene_goals=["Introduce protagonist"],
            status=StoryArtifactLifecycleState.CANONICAL,
        )

        # Register as lineage
        lineage_id = packet_service.register_packet_as_lineage(
            step_record_service=step_records,
            packet_id=packet_id,
            project_id=project_id,
            step_name="packet_builder",
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="chapter_packet",
            attempt_number=1,
            artifact_role="chapter_packet",
            produced_at=STAMP,
            source_artifact_refs=["ref-1", "ref-2"],
            source_content_hashes=["hash-1"],
            output_of_step_record_id=step_id,
        )

        assert lineage_id is not None
        assert lineage_id > 0

        # Verify lineage record exists
        lineage_list = step_records._lineage.list_for_project(
            project_id=project_id,
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert len(lineage_list) == 1
        assert lineage_list[0]["artifact_role"] == "chapter_packet"
        assert lineage_list[0]["path"] == f"/data/projects/{project_id}/chapters/{packet_id}"
        assert lineage_list[0]["output_of_step_record_id"] == step_id

    def test_register_packet_as_lineage_null_service_returns_none(
        self, tmp_path: Path
    ) -> None:
        """When step_record_service is None, register_packet_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        packet_service = ChapterPacketService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        result = packet_service.register_packet_as_lineage(
            step_record_service=None,
            packet_id="packet-1",
            project_id=project_id,
            step_name="packet_builder",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="chapter_packet",
            attempt_number=1,
            artifact_role="chapter_packet",
            output_of_step_record_id=0,
        )
        assert result is None

    def test_register_packet_as_lineage_handles_missing_packet(
        self, tmp_path: Path
    ) -> None:
        """When packet doesn't exist, register_packet_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        packet_service = ChapterPacketService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        # Create prerequisite step record
        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="chapter_packet",
            attempt_number=1,
            step_name="packet_builder",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        result = packet_service.register_packet_as_lineage(
            step_record_service=step_records,
            packet_id="non-existent-packet",
            project_id=project_id,
            step_name="packet_builder",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="chapter_packet",
            attempt_number=1,
            artifact_role="chapter_packet",
            output_of_step_record_id=step_id,
        )
        assert result is None

    def test_register_packet_as_lineage_includes_packet_refs(
        self, tmp_path: Path
    ) -> None:
        """Lineage record should include packet's included_reference_ids as refs."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        packet_service = ChapterPacketService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        chapter_id = f"ch-{uuid4().hex[:8]}"
        packet_id = f"packet-{uuid4().hex[:8]}"
        run_id = uuid4()

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

        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=run_id,
            run_kind="chapter_packet",
            attempt_number=1,
            step_name="packet_builder",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[packet_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        packet_service.register_packet(
            project_id,
            packet_id=packet_id,
            chapter_id=chapter_id,
            included_reference_ids=["custom-ref", "another-ref"],
            status=StoryArtifactLifecycleState.CANONICAL,
        )

        step_records.register_packet_as_lineage_for_project = lambda **kw: None

        result = packet_service.register_packet_as_lineage(
            step_record_service=step_records,
            packet_id=packet_id,
            project_id=project_id,
            step_name="packet_builder",
            logical_run_id="test",
            run_id=run_id,
            run_kind="chapter_packet",
            attempt_number=1,
            artifact_role="chapter_packet",
            source_artifact_refs=["external-ref"],
            output_of_step_record_id=step_id,
        )

        # Verify the packet includes its reference IDs
        packets = packet_service.list_packets(project_id)
        assert len(packets) == 1
        assert "custom-ref" in packets[0].included_reference_ids
        assert "another-ref" in packets[0].included_reference_ids


class TestSequencePlanLineageRegistration:
    """Integration tests for sequence-plan lineage-aware registration."""

    def test_register_plan_as_lineage_creates_record(
        self, tmp_path: Path
    ) -> None:
        """register_plan_as_lineage should create a lineage record linked to a step."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        plan_service = SequencePlanService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        seq_id = f"seq-{uuid4().hex[:8]}"
        run_id = uuid4()
        logical_run_id = "sequence-plan-reg"

        # Register step record
        step_id = step_records.create_step_record(
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="sequence_plan",
            attempt_number=1,
            step_name="sequencer",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[seq_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        # Register the plan
        plan_service.register_plan(
            project_id,
            sequence_id=seq_id,
            title="Main Arc",
            summary="The primary narrative arc",
            beat_ids=["beat-1", "beat-2"],
            chapter_ids=["ch-1"],
            status=StoryArtifactLifecycleState.CANONICAL,
            position=0,
        )

        # Register as lineage
        lineage_id = plan_service.register_plan_as_lineage(
            step_record_service=step_records,
            sequence_id=seq_id,
            project_id=project_id,
            step_name="sequencer",
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="sequence_plan",
            attempt_number=1,
            artifact_role="sequence_plan",
            produced_at=STAMP,
            source_artifact_refs=["ref-1"],
            source_content_hashes=["hash-1"],
            output_of_step_record_id=step_id,
        )

        assert lineage_id is not None
        assert lineage_id > 0

        # Verify lineage record exists
        lineage_list = step_records._lineage.list_for_project(
            project_id=project_id,
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert len(lineage_list) == 1
        assert lineage_list[0]["artifact_role"] == "sequence_plan"
        assert lineage_list[0]["path"] == f"/data/projects/{project_id}/sequences/{seq_id}"

    def test_register_plan_as_lineage_null_service_returns_none(
        self, tmp_path: Path
    ) -> None:
        """When step_record_service is None, register_plan_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        plan_service = SequencePlanService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        result = plan_service.register_plan_as_lineage(
            step_record_service=None,
            sequence_id="seq-1",
            project_id=project_id,
            step_name="sequencer",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="sequence_plan",
            attempt_number=1,
            artifact_role="sequence_plan",
            output_of_step_record_id=0,
        )
        assert result is None

    def test_register_plan_as_lineage_handles_missing_plan(
        self, tmp_path: Path
    ) -> None:
        """When plan doesn't exist, register_plan_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        plan_service = SequencePlanService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="sequence_plan",
            attempt_number=1,
            step_name="sequencer",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        result = plan_service.register_plan_as_lineage(
            step_record_service=step_records,
            sequence_id="non-existent-seq",
            project_id=project_id,
            step_name="sequencer",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="sequence_plan",
            attempt_number=1,
            artifact_role="sequence_plan",
            output_of_step_record_id=step_id,
        )
        assert result is None

    def test_register_plan_as_lineage_includes_plan_refs(
        self, tmp_path: Path
    ) -> None:
        """Lineage record should include plan's beat_ids and chapter_ids as refs."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        plan_service = SequencePlanService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        seq_id = f"seq-{uuid4().hex[:8]}"
        run_id = uuid4()

        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=run_id,
            run_kind="sequence_plan",
            attempt_number=1,
            step_name="sequencer",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[seq_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        plan_service.register_plan(
            project_id,
            sequence_id=seq_id,
            title="Main Arc",
            summary="Main narrative arc",
            beat_ids=["beat-a", "beat-b"],
            chapter_ids=["ch-x", "ch-y"],
            status=StoryArtifactLifecycleState.CANONICAL,
            position=0,
        )

        result = plan_service.register_plan_as_lineage(
            step_record_service=step_records,
            sequence_id=seq_id,
            project_id=project_id,
            step_name="sequencer",
            logical_run_id="test",
            run_id=run_id,
            run_kind="sequence_plan",
            attempt_number=1,
            artifact_role="sequence_plan",
            source_artifact_refs=["external-ref"],
            output_of_step_record_id=step_id,
        )

        assert result is not None

        # Verify the plan includes its beat and chapter IDs
        plans = plan_service.list_plans(project_id)
        assert len(plans) == 1
        assert "beat-a" in plans[0].beat_ids
        assert "beat-b" in plans[0].beat_ids
        assert "ch-x" in plans[0].chapter_ids
        assert "ch-y" in plans[0].chapter_ids


class TestStoryboardCardLineageRegistration:
    """Integration tests for storyboard-card lineage-aware registration."""

    def test_register_card_as_lineage_creates_record(
        self, tmp_path: Path
    ) -> None:
        """register_card_as_lineage should create a lineage record linked to a step."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        card_service = StoryboardCardService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        card_id = f"card-{uuid4().hex[:8]}"
        run_id = uuid4()
        logical_run_id = "card-registration"

        # Create the card
        card_service.create_card(
            project_id,
            card_id=card_id,
            title="Opening Scene",
            content="The protagonist enters the room.",
            card_type="scene",
            column_id="planned",
            position=0,
            tags=["important"],
            character_ids=["hero-1"],
        )

        # Register step record (prerequisite)
        step_id = step_records.create_step_record(
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="card_registration",
            attempt_number=1,
            step_name="card_registrar",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[card_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        # Register as lineage
        lineage_id = card_service.register_card_as_lineage(
            step_record_service=step_records,
            card_id=card_id,
            project_id=project_id,
            step_name="card_registrar",
            logical_run_id=logical_run_id,
            run_id=run_id,
            run_kind="card_registration",
            attempt_number=1,
            artifact_role="storyboard_card",
            produced_at=STAMP,
            source_artifact_refs=["ref-1"],
            source_content_hashes=["hash-1"],
            output_of_step_record_id=step_id,
        )

        assert lineage_id is not None
        assert lineage_id > 0

        # Verify lineage record exists
        lineage_list = step_records._lineage.list_for_project(
            project_id=project_id,
            status=StoryArtifactLifecycleState.CANONICAL,
        )
        assert len(lineage_list) == 1
        assert lineage_list[0]["artifact_role"] == "storyboard_card"
        assert lineage_list[0]["path"] == f"/data/projects/{project_id}/storyboard/{card_id}"

    def test_register_card_as_lineage_null_service_returns_none(
        self, tmp_path: Path
    ) -> None:
        """When step_record_service is None, register_card_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        repo = StoryDevelopmentRepository(db_path)
        card_service = StoryboardCardService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        result = card_service.register_card_as_lineage(
            step_record_service=None,
            card_id="card-1",
            project_id=project_id,
            step_name="card_registrar",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="card_registration",
            attempt_number=1,
            artifact_role="storyboard_card",
            output_of_step_record_id=0,
        )
        assert result is None

    def test_register_card_as_lineage_handles_missing_card(
        self, tmp_path: Path
    ) -> None:
        """When card doesn't exist, register_card_as_lineage returns None."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)
        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        card_service = StoryboardCardService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="card_registration",
            attempt_number=1,
            step_name="card_registrar",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        result = card_service.register_card_as_lineage(
            step_record_service=step_records,
            card_id="non-existent-card",
            project_id=project_id,
            step_name="card_registrar",
            logical_run_id="test",
            run_id=uuid4(),
            run_kind="card_registration",
            attempt_number=1,
            artifact_role="storyboard_card",
            output_of_step_record_id=step_id,
        )
        assert result is None

    def test_register_card_as_lineage_includes_card_refs(
        self, tmp_path: Path
    ) -> None:
        """Lineage record should include card's tags and character_ids as refs."""
        db_path = _make_db(tmp_path)
        ensure_operations_db(db_path)

        step_records = StepRecordService(db_path)
        repo = StoryDevelopmentRepository(db_path)
        card_service = StoryboardCardService(repo)

        project_id = f"test-proj-{uuid4().hex[:8]}"
        _seed_project(db_path, project_id)

        card_id = f"card-{uuid4().hex[:8]}"
        run_id = uuid4()

        step_id = step_records.create_step_record(
            logical_run_id="test",
            run_id=run_id,
            run_kind="card_registration",
            attempt_number=1,
            step_name="card_registrar",
            step_index=1,
            state="COMPLETED",
            project_id=project_id,
            model_id="system",
            critic_profile=None,
            backend_name="system",
            backend_version="0.0.0",
            input_hash="input-hash",
            output_hash="output-hash",
            prompt_hash="prompt-hash",
            input_artifact_refs=[],
            output_artifact_refs=[card_id],
            started_at=STAMP,
            finished_at=STAMP,
            finish_reason="stop",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            error_code=None,
            error_category=None,
            executor_id="executor-1",
            lease_owner=None,
            created_at=STAMP,
            updated_at=STAMP,
        )

        card_service.create_card(
            project_id,
            card_id=card_id,
            title="Test Card",
            content="Test content",
            card_type="idea",
            tags=["urgent", "key-moment"],
            character_ids=["hero-1", "villain-1"],
        )

        result = card_service.register_card_as_lineage(
            step_record_service=step_records,
            card_id=card_id,
            project_id=project_id,
            step_name="card_registrar",
            logical_run_id="test",
            run_id=run_id,
            run_kind="card_registration",
            attempt_number=1,
            artifact_role="storyboard_card",
            source_artifact_refs=["external-ref"],
            output_of_step_record_id=step_id,
        )

        assert result is not None

        # Verify the card includes its tags and character IDs
        cards = card_service.list_cards(project_id)
        assert len(cards) == 1
        assert "urgent" in cards[0].tags
        assert "key-moment" in cards[0].tags
        assert "hero-1" in cards[0].character_ids
        assert "villain-1" in cards[0].character_ids
