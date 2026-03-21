from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import (
    ArtifactLineage,
    DraftArtifact,
    RevisionSuggestion,
    StoryArtifactLifecycleState,
    StoryFlowDefinition,
    StoryFlowStage,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StorySuggestionLifecycleState,
)


def test_story_development_enum_values_are_canonical() -> None:
    assert StoryFlowStageConfigurationState.ENABLED.value == "ENABLED"
    assert StoryFlowStageProgressState.NEEDS_REVIEW.value == "NEEDS_REVIEW"
    assert StoryArtifactLifecycleState.CANONICAL.value == "CANONICAL"
    assert StorySuggestionLifecycleState.REFINE_REQUESTED.value == "REFINE_REQUESTED"


def test_story_flow_stage_and_definition_validate_canonical_shape() -> None:
    stage = StoryFlowStage.model_validate(
        {
            "stage_id": "  brainstorm  ",
            "stage_kind": "brainstorm",
            "display_name": "  Brainstorm  ",
            "description": "  Capture raw ideas  ",
            "position": 0,
            "depends_on": ["  intake  ", "outline"],
            "writer_notes": "  Keep it loose  ",
            "custom_prompt_guidance": "  Encourage fragments  ",
        }
    )
    definition = StoryFlowDefinition.model_validate(
        {
            "project_id": "  project-123  ",
            "project_name": "  Project Aurora  ",
            "stages": [stage.model_dump()],
        }
    )

    assert stage.stage_id == "brainstorm"
    assert stage.display_name == "Brainstorm"
    assert stage.depends_on == ["intake", "outline"]
    assert stage.stage_configuration_state == StoryFlowStageConfigurationState.ENABLED.value
    assert stage.stage_progress_state == StoryFlowStageProgressState.NOT_STARTED.value
    assert definition.project_id == "project-123"
    assert definition.project_name == "Project Aurora"
    assert definition.stages[0].stage_id == "brainstorm"


def test_draft_and_revision_models_keep_generated_and_proposed_content_separate() -> None:
    artifact = DraftArtifact.model_validate(
        {
            "artifact_id": "draft-1",
            "project_id": "project-123",
            "title": "Chapter 1 Draft",
            "content": "The city shifted at dusk.",
            "source_plan_ids": ["chapter-1"],
            "source_context": ["manifest", "sequence"],
            "status": "CANONICAL",
        }
    )
    revision = RevisionSuggestion.model_validate(
        {
            "suggestion_id": "suggestion-1",
            "project_id": "project-123",
            "target_document_id": "manuscript-1",
            "source_text": "The city shifted at dusk.",
            "proposed_text": "At dusk, the city shifted again.",
            "rationale": "Tighten the opening beat.",
            "source_context": ["chapter-1", "scene-4"],
        }
    )
    lineage = ArtifactLineage.model_validate(
        {
            "artifact_lineage_id": 10,
            "logical_run_id": "run-1",
            "run_id": "run-1-attempt-1",
            "run_kind": "job",
            "attempt_number": 1,
            "step_name": "architect",
            "artifact_role": "architect_output",
            "artifact_kind": "markdown",
            "path": "exports/p100_architect_output.md",
            "status": "CANONICAL",
            "validation_state": "PASSED",
            "produced_at": "2026-03-20T00:00:00Z",
            "output_of_step_record_id": 22,
        }
    )

    assert artifact.status == StoryArtifactLifecycleState.CANONICAL.value
    assert revision.status == StorySuggestionLifecycleState.REQUESTED.value
    assert lineage.status == StoryArtifactLifecycleState.CANONICAL.value
    assert lineage.path == "exports/p100_architect_output.md"


def test_story_development_models_reject_extra_fields() -> None:
    with pytest.raises(ValidationError):
        StoryFlowStage.model_validate(
            {
                "stage_id": "brainstorm",
                "stage_kind": "brainstorm",
                "display_name": "Brainstorm",
                "position": 0,
                "unexpected": "value",
            }
        )
