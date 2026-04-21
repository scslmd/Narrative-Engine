"""Integration tests for SQLiteEditableFlowRepository persistence layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.schemas import (
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
)
from app.services.editable_flow import (
    EditableFlowDeletionCheck,
    EditableFlowService,
    EditableFlowValidationError,
    InMemoryEditableFlowRepository,
)
from app.services.editable_flow_persistence import SQLiteEditableFlowRepository


_TEST_PROJECT_ID = "test-project-flow-persist"
_TEST_TIMESTAMP = "2026-01-15T12:00:00+00:00"


def _ensure_test_project(db_path: Path) -> None:
    """Seed the projects table so FK constraints are satisfied."""
    ensure_operations_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_TEST_PROJECT_ID, "Test Flow Persist", str(db_path), str(db_path), _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()


class BaseFlowPersistTest:
    """Shared setup for flow persistence tests."""

    def _make_repo(self, tmp_path: Path) -> SQLiteEditableFlowRepository:
        db_path = tmp_path / "operations.db"
        _ensure_test_project(db_path)
        return SQLiteEditableFlowRepository(str(db_path))

    def _make_service(self, tmp_path: Path) -> EditableFlowService:
        repo = self._make_repo(tmp_path)
        return EditableFlowService(repo)


class TestSQLiteEditableFlowRepositoryRoundTrip(BaseFlowPersistTest):
    """Test that flow state survives full save/read cycles through SQLite."""

    def test_create_default_flow_persists_stages(self, tmp_path: Path) -> None:
        """Creating a default flow via service should persist all stages to SQLite."""
        service = self._make_service(tmp_path)
        flow = service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        assert len(flow.stages) == 8
        assert flow.stages[0].stage_id == "stage-001"
        assert flow.stages[-1].stage_id == "stage-008"

        # Verify persistence: reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        assert len(loaded_state.flow.stages) == 8
        assert loaded_state.flow.stages[0].stage_id == "stage-001"
        assert loaded_state.flow.stages[-1].stage_id == "stage-008"
        assert loaded_state.flow.project_id == _TEST_PROJECT_ID

    def test_add_custom_stage_persists_to_database(self, tmp_path: Path) -> None:
        """Adding a custom stage should be persisted and survive reload."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        custom_stage = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Continuity Pass",
            description="Check the draft against the bible.",
            stage_kind="continuity",
            depends_on=["stage-006"],
            insert_after_stage_id="stage-006",
        )

        # Verify the custom stage is in the returned flow
        assert custom_stage.stage_kind == "continuity"
        assert custom_stage.stage_id.startswith("stage-")
        assert custom_stage.display_name == "Continuity Pass"
        assert custom_stage.description == "Check the draft against the bible."

        # Verify persistence
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        assert len(loaded_state.flow.stages) == 9
        stage_ids = [s.stage_id for s in loaded_state.flow.stages]
        assert custom_stage.stage_id in stage_ids

        loaded_custom = next(s for s in loaded_state.flow.stages if s.stage_id == custom_stage.stage_id)
        assert loaded_custom.stage_kind == "continuity"
        assert loaded_custom.stage_configuration_state == StoryFlowStageConfigurationState.ENABLED
        assert loaded_custom.stage_progress_state == StoryFlowStageProgressState.NOT_STARTED

    def test_renamed_stage_persists_display_name(self, tmp_path: Path) -> None:
        """Renaming a stage should persist the new display_name."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        renamed = service.rename_stage(
            project_id=_TEST_PROJECT_ID,
            stage_id="stage-002",
            display_name="Revised Foundation",
        )
        assert renamed.display_name == "Revised Foundation"

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        foundation = next(s for s in loaded_state.flow.stages if s.stage_id == "stage-002")
        assert foundation.display_name == "Revised Foundation"

    def test_redefine_stage_persists_all_fields(self, tmp_path: Path) -> None:
        """Redefining a stage should persist all updated fields."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        redefined = service.redefine_stage(
            project_id=_TEST_PROJECT_ID,
            stage_id="stage-003",
            display_name="Character Deep Dive",
            description="Build character motivation, flaw, and change arc.",
            writer_notes="Focus on internal conflict.",
            custom_prompt_guidance="Always reference the foundation.",
            stage_kind="character_deep",
        )

        assert redefined.display_name == "Character Deep Dive"
        assert redefined.stage_kind == "character_deep"
        assert redefined.writer_notes == "Focus on internal conflict."
        assert redefined.custom_prompt_guidance == "Always reference the foundation."

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        stage = next(s for s in loaded_state.flow.stages if s.stage_id == "stage-003")
        assert stage.display_name == "Character Deep Dive"
        assert stage.stage_kind == "character_deep"
        assert stage.writer_notes == "Focus on internal conflict."
        assert stage.custom_prompt_guidance == "Always reference the foundation."

    def test_reorder_stages_persists_order(self, tmp_path: Path) -> None:
        """Reordering stages should persist the new order."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        new_order = ["stage-008", "stage-001", "stage-002", "stage-003", "stage-004", "stage-005", "stage-006", "stage-007"]
        reordered = service.reorder_stages(project_id=_TEST_PROJECT_ID, stage_order=new_order)

        positions = {stage.stage_id: stage.position for stage in reordered.stages}
        assert positions["stage-008"] == 0
        assert positions["stage-001"] == 1
        assert positions["stage-007"] == 7

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        loaded_positions = {s.stage_id: s.position for s in loaded_state.flow.stages}
        assert loaded_positions == positions

    def test_disable_stage_persists_configuration_state(self, tmp_path: Path) -> None:
        """Disabling a stage should persist the DISABLED configuration state."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        disabled = service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id="stage-002")
        assert disabled.stage_configuration_state == StoryFlowStageConfigurationState.DISABLED

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        stage = next(s for s in loaded_state.flow.stages if s.stage_id == "stage-002")
        assert stage.stage_configuration_state == StoryFlowStageConfigurationState.DISABLED

    def test_archive_stage_persists_configuration_and_progress_state(self, tmp_path: Path) -> None:
        """Archiving a stage should persist ARCHIVED state and SUPERSEDED progress."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        archived = service.archive_stage(project_id=_TEST_PROJECT_ID, stage_id="stage-003")
        assert archived.stage_configuration_state == StoryFlowStageConfigurationState.ARCHIVED
        assert archived.stage_progress_state == StoryFlowStageProgressState.SUPERSEDED

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        stage = next(s for s in loaded_state.flow.stages if s.stage_id == "stage-003")
        assert stage.stage_configuration_state == StoryFlowStageConfigurationState.ARCHIVED
        assert stage.stage_progress_state == StoryFlowStageProgressState.SUPERSEDED

    def test_delete_custom_stage_removes_from_database(self, tmp_path: Path) -> None:
        """Deleting a custom stage should remove it from SQLite."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        custom = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Optional Note Stage",
        )
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=custom.stage_id)
        removed = service.delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=custom.stage_id)

        assert removed.stage_id == custom.stage_id

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        stage_ids = {s.stage_id for s in loaded_state.flow.stages}
        assert custom.stage_id not in stage_ids
        assert len(loaded_state.flow.stages) == 8

    def test_custom_stage_ids_are_tracked_across_save_cycle(self, tmp_path: Path) -> None:
        """Custom stage IDs should survive save/read cycles."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        custom = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Brain Dump",
        )
        # Mark as deleted-ready
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=custom.stage_id)

        # Verify can_delete_custom_stage works after reload
        repo = self._make_repo(tmp_path)
        fresh_service = EditableFlowService(repo)

        check = fresh_service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=custom.stage_id)
        assert check.allowed is True

    def test_can_delete_prevents_deletion_of_active_custom_stage(self, tmp_path: Path) -> None:
        """An active (enabled) custom stage should not be deletable."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        custom = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Active Custom Stage",
        )

        check = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=custom.stage_id)
        assert check.allowed is False
        assert "Stage must be disabled or archived before deletion" in check.reasons[0]

    def test_can_delete_prevents_deletion_with_active_dependents(self, tmp_path: Path) -> None:
        """A custom stage with active dependents should not be deletable."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        parent = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Parent Stage",
        )
        child = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Child Stage",
            depends_on=[parent.stage_id],
        )

        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)

        check = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)
        assert check.allowed is False
        assert child.stage_id in check.reasons[0]

    def test_delete_default_stage_raises_validation_error(self, tmp_path: Path) -> None:
        """Deleting a default (non-custom) stage should raise EditableFlowValidationError."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        check = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id="stage-001")
        assert check.allowed is False
        assert "Stage is not custom" in check.reasons[0]

    def test_delete_requires_dependent_stages_to_be_inactive(self, tmp_path: Path) -> None:
        """A custom stage with dependents cannot be deleted until dependents are removed."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        parent = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Parent",
        )
        child = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Child",
            depends_on=[parent.stage_id],
        )

        # Parent is active and has active dependent child
        check = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)
        assert check.allowed is False
        assert "Stage must be disabled or archived" in check.reasons[0]
        assert child.stage_id in check.reasons[1]

        # Disabling dependent does NOT allow deletion - dependent must be deleted
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=child.stage_id)
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)

        check_after = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)
        assert check_after.allowed is False
        assert child.stage_id in check_after.reasons[0]

        # Only deleting the dependent allows parent deletion
        service.delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=child.stage_id)
        check_final = service.can_delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=parent.stage_id)
        assert check_final.allowed is True

    def test_reorder_preserves_dependency_references(self, tmp_path: Path) -> None:
        """Reordering stages should not change their dependency references."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        # Add a custom stage with explicit dependencies
        custom = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Dependent Stage",
            depends_on=["stage-001", "stage-003"],
        )

        # Reorder
        all_ids = [s.stage_id for s in service._require_state(_TEST_PROJECT_ID).flow.stages]
        reordered_ids = [all_ids[-1]] + all_ids[:-1]  # Move last to first
        service.reorder_stages(project_id=_TEST_PROJECT_ID, stage_order=reordered_ids)

        # Reload from repo
        repo = self._make_repo(tmp_path)
        loaded_state = repo.get(_TEST_PROJECT_ID)
        assert loaded_state is not None
        loaded_custom = next(s for s in loaded_state.flow.stages if s.stage_id == custom.stage_id)
        assert set(loaded_custom.depends_on) == {"stage-001", "stage-003"}

    def test_stage_is_custom_flag_is_persisted_correctly(self, tmp_path: Path) -> None:
        """Default stages should be persisted with is_custom=0, custom stages with is_custom=1."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        custom = service.add_custom_stage(
            project_id=_TEST_PROJECT_ID,
            display_name="Custom Custom Stage",
        )

        repo = self._make_repo(tmp_path)
        with connect(repo._db_path) as conn:
            row = conn.execute(
                "SELECT is_custom FROM story_flow_stages WHERE project_id = ? AND stage_key = ?",
                (_TEST_PROJECT_ID, "stage-001"),
            ).fetchone()
            assert row is not None
            assert row["is_custom"] == 0  # Default stage

            row2 = conn.execute(
                "SELECT is_custom FROM story_flow_stages WHERE project_id = ? AND stage_key = ?",
                (_TEST_PROJECT_ID, custom.stage_id),
            ).fetchone()
            assert row2 is not None
            assert row2["is_custom"] == 1  # Custom stage

    def test_delete_nonexistent_stage_raises_not_found(self, tmp_path: Path) -> None:
        """Deleting a stage that doesn't exist should raise EditableFlowNotFoundError."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        from app.services.editable_flow import EditableFlowNotFoundError

        with pytest.raises(EditableFlowNotFoundError):
            service.delete_custom_stage(
                project_id=_TEST_PROJECT_ID,
                stage_id="stage-999",
            )

    def test_get_nonexistent_project_returns_none(self, tmp_path: Path) -> None:
        """Getting flow for a project with no flow should return None."""
        repo = self._make_repo(tmp_path)
        result = repo.get("nonexistent-project")
        assert result is None

    def test_stage_ids_are_not_reused_after_deletion(self, tmp_path: Path) -> None:
        """After adding and deleting a custom stage, the next stage ID should not duplicate."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        first = service.add_custom_stage(project_id=_TEST_PROJECT_ID, display_name="First")
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=first.stage_id)
        service.delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=first.stage_id)

        second = service.add_custom_stage(project_id=_TEST_PROJECT_ID, display_name="Second")

        assert first.stage_id != second.stage_id

    def test_next_stage_index_increments_after_deletion(self, tmp_path: Path) -> None:
        """After deleting a stage, the next_stage_index should still increment."""
        service = self._make_service(tmp_path)
        service.create_default_flow(project_id=_TEST_PROJECT_ID, project_name="Story Project")

        first = service.add_custom_stage(project_id=_TEST_PROJECT_ID, display_name="First")
        service.disable_stage(project_id=_TEST_PROJECT_ID, stage_id=first.stage_id)
        service.delete_custom_stage(project_id=_TEST_PROJECT_ID, stage_id=first.stage_id)

        # Reload service from fresh repo
        repo = self._make_repo(tmp_path)
        fresh_service = EditableFlowService(repo)

        second = fresh_service.add_custom_stage(project_id=_TEST_PROJECT_ID, display_name="Second")

        # The second stage should have a higher index than the first
        assert int(second.stage_id.split("-")[1]) > int(first.stage_id.split("-")[1])
