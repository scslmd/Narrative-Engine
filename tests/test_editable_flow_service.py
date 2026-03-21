from __future__ import annotations

import pytest

from app.schemas import StoryFlowStageConfigurationState, StoryFlowStageProgressState
from app.services.editable_flow import (
    EditableFlowDeletionCheck,
    EditableFlowService,
    EditableFlowValidationError,
    InMemoryEditableFlowRepository,
)


def _make_service() -> EditableFlowService:
    return EditableFlowService(InMemoryEditableFlowRepository())


def test_create_default_flow_builds_canonical_scaffold() -> None:
    service = _make_service()

    flow = service.create_default_flow(project_id="project-1", project_name="Story Project")

    assert flow.project_id == "project-1"
    assert flow.project_name == "Story Project"
    ordered = sorted(flow.stages, key=lambda stage: stage.position)
    assert [stage.stage_kind for stage in ordered] == [
        "brainstorm",
        "foundation",
        "character",
        "world_bible",
        "arc_selection",
        "planning",
        "drafting",
        "review",
    ]
    assert ordered[0].stage_id == "stage-001"
    assert ordered[-1].stage_id == "stage-008"
    assert ordered[0].depends_on == []
    assert ordered[1].depends_on == ["stage-001"]
    assert ordered[-1].stage_configuration_state == StoryFlowStageConfigurationState.ENABLED
    assert ordered[-1].stage_progress_state == StoryFlowStageProgressState.NOT_STARTED

    with pytest.raises(EditableFlowValidationError):
        service.create_default_flow(project_id="project-1", project_name="Duplicate Project")


def test_editable_flow_supports_add_rename_redefine_reorder_disable_and_archive() -> None:
    service = _make_service()
    flow = service.create_default_flow(project_id="project-2", project_name="Story Project")

    custom_stage = service.add_custom_stage(
        project_id="project-2",
        display_name="Continuity Pass",
        description="Check the draft against the bible.",
        writer_notes="Focus on contradictions.",
        custom_prompt_guidance="Always cite the source chapter.",
        insert_after_stage_id="stage-006",
    )
    renamed = service.rename_stage(
        project_id="project-2",
        stage_id=custom_stage.stage_id,
        display_name="Continuity Review",
    )
    redefined = service.redefine_stage(
        project_id="project-2",
        stage_id=custom_stage.stage_id,
        description="Review the draft against canon and arc goals.",
        writer_notes="Prioritize character motivation and scene logic.",
        custom_prompt_guidance="Mention canon sources and scene goals.",
        stage_kind="review_plus",
    )
    reordered = service.reorder_stages(
        project_id="project-2",
        stage_order=[
            "stage-001",
            "stage-002",
            "stage-003",
            "stage-004",
            "stage-005",
            custom_stage.stage_id,
            "stage-006",
            "stage-007",
            "stage-008",
        ],
    )
    disabled = service.disable_stage(project_id="project-2", stage_id=custom_stage.stage_id)
    archived = service.archive_stage(project_id="project-2", stage_id=custom_stage.stage_id)

    assert renamed.display_name == "Continuity Review"
    assert redefined.description == "Review the draft against canon and arc goals."
    assert redefined.writer_notes == "Prioritize character motivation and scene logic."
    assert redefined.custom_prompt_guidance == "Mention canon sources and scene goals."
    assert redefined.stage_kind == "review_plus"
    assert sorted(reordered.stages, key=lambda stage: stage.position)[5].stage_id == custom_stage.stage_id
    assert disabled.stage_configuration_state == StoryFlowStageConfigurationState.DISABLED
    assert archived.stage_configuration_state == StoryFlowStageConfigurationState.ARCHIVED
    assert archived.stage_progress_state == StoryFlowStageProgressState.SUPERSEDED

    persisted = service.get_flow("project-2")
    persisted_stages = {stage.stage_id: stage for stage in persisted.stages}
    reordered_ids = [stage.stage_id for stage in sorted(reordered.stages, key=lambda stage: stage.position)]
    persisted_ids = [stage.stage_id for stage in sorted(persisted.stages, key=lambda stage: stage.position)]
    assert persisted_ids == reordered_ids
    assert persisted_stages[custom_stage.stage_id].stage_configuration_state == StoryFlowStageConfigurationState.ARCHIVED
    assert persisted_stages[custom_stage.stage_id].display_name == "Continuity Review"
    assert persisted_stages[custom_stage.stage_id].description == "Review the draft against canon and arc goals."
    assert flow.project_id == "project-2"


def test_custom_stage_deletion_requires_no_dependents_and_non_active_state() -> None:
    service = _make_service()
    service.create_default_flow(project_id="project-3", project_name="Story Project")
    custom_stage = service.add_custom_stage(
        project_id="project-3",
        display_name="Optional Notes",
        description="A project-specific note stage.",
    )
    dependent_stage = service.add_custom_stage(
        project_id="project-3",
        display_name="Follow-Up",
        depends_on=(custom_stage.stage_id,),
    )

    check = service.can_delete_custom_stage(project_id="project-3", stage_id=custom_stage.stage_id)
    assert check == EditableFlowDeletionCheck(
        allowed=False,
        reasons=("Stage must be disabled or archived before deletion.", f"Stage is still referenced by: {dependent_stage.stage_id}.")
    )

    service.disable_stage(project_id="project-3", stage_id=custom_stage.stage_id)
    service.archive_stage(project_id="project-3", stage_id=dependent_stage.stage_id)
    service.delete_custom_stage(project_id="project-3", stage_id=dependent_stage.stage_id)

    check_after_dependency_removed = service.can_delete_custom_stage(
        project_id="project-3",
        stage_id=custom_stage.stage_id,
    )
    assert check_after_dependency_removed.allowed is True
    removed = service.delete_custom_stage(project_id="project-3", stage_id=custom_stage.stage_id)
    assert removed.stage_id == custom_stage.stage_id
    remaining_flow = service.get_flow("project-3")
    assert custom_stage.stage_id not in {stage.stage_id for stage in remaining_flow.stages}

    with pytest.raises(EditableFlowValidationError):
        service.delete_custom_stage(project_id="project-3", stage_id="stage-001")


def test_redefine_stage_rejects_invalid_dependencies() -> None:
    service = _make_service()
    service.create_default_flow(project_id="project-4", project_name="Story Project")

    with pytest.raises(EditableFlowValidationError, match="Invalid stage dependency references"):
        service.redefine_stage(
            project_id="project-4",
            stage_id="stage-002",
            depends_on=["stage-999"],
        )


def test_deleted_stage_ids_are_not_reused() -> None:
    service = _make_service()
    service.create_default_flow(project_id="project-5", project_name="Story Project")
    first = service.add_custom_stage(project_id="project-5", display_name="Reflection")
    service.disable_stage(project_id="project-5", stage_id=first.stage_id)
    service.delete_custom_stage(project_id="project-5", stage_id=first.stage_id)

    second = service.add_custom_stage(project_id="project-5", display_name="Continuity")

    assert first.stage_id == "stage-009"
    assert second.stage_id == "stage-010"
