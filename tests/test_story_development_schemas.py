from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import (
    ArtifactLineage,
    ArcCandidate,
    ArcComparisonRecord,
    ArcSelection,
    BranchPoint,
    BranchStateRef,
    DraftArtifact,
    RevisionSuggestion,
    StoryArtifactLifecycleState,
    StoryDecisionChangeType,
    StoryDecisionNode,
    StoryDecisionNodeType,
    StoryBranch,
    StoryBranchState,
    StoryFlowDefinition,
    StoryFlowStage,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StoryObjectType,
    StorySuggestionLifecycleState,
)


def test_story_development_enum_values_are_canonical() -> None:
    assert StoryFlowStageConfigurationState.ENABLED.value == "ENABLED"
    assert StoryFlowStageProgressState.NEEDS_REVIEW.value == "NEEDS_REVIEW"
    assert StoryArtifactLifecycleState.CANONICAL.value == "CANONICAL"
    assert StorySuggestionLifecycleState.REFINE_REQUESTED.value == "REFINE_REQUESTED"
    assert StoryDecisionNodeType.BRANCH_POINT.value == "BRANCH_POINT"
    assert StoryDecisionChangeType.ARC_PIVOT.value == "ARC_PIVOT"
    assert StoryObjectType.ARC_SELECTION.value == "ARC_SELECTION"


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


def test_arc_comparison_selection_and_decision_models_validate_reviewable_history() -> None:
    candidate_primary = ArcCandidate.model_validate(
        {
            "arc_id": "  arc-primary  ",
            "project_id": "  project-123  ",
            "name": "  Primary Quest  ",
            "summary": "  A steady route through the opening.  ",
            "stage_map_notes": ["  Open the story  "],
            "fit_notes": ["  Strong structural fit  "],
            "tags": ["  adventure  "],
        }
    )
    candidate_secondary = ArcCandidate.model_validate(
        {
            "arc_id": "arc-secondary",
            "project_id": "project-123",
            "name": "Braided Mystery",
            "summary": "Threads move in parallel.",
            "stage_map_notes": ["Reveal", "Reframe"],
            "fit_notes": ["Fits a suspenseful tone"],
            "tags": ["mystery"],
        }
    )
    comparison = ArcComparisonRecord.model_validate(
        {
            "comparison_id": "  comparison-1  ",
            "project_id": "  project-123  ",
            "candidate_ids": ["  arc-primary  ", "arc-secondary"],
            "candidate_set": [candidate_primary.model_dump(), candidate_secondary.model_dump()],
            "ranked_candidates": [
                {
                    "candidate": candidate_primary.model_dump(),
                    "rank": 1,
                    "score": [4, 3, 2, 1],
                    "notes": ["  Best overall fit  "],
                },
                {
                    "candidate": candidate_secondary.model_dump(),
                    "rank": 2,
                    "score": [2, 2, 1, 0],
                    "notes": ["  Stronger later revisit candidate  "],
                },
            ],
            "review_notes": ["  Choose the cleaner opening path.  "],
        }
    )
    selection = ArcSelection.model_validate(
        {
            "selection_id": "  selection-1  ",
            "project_id": "  project-123  ",
            "selected_arc": candidate_primary.model_dump(),
            "rejected_arc_ids": ["  arc-secondary  "],
            "comparison_notes": ["  Comparison recorded for review.  "],
            "comparison_record_ids": ["  comparison-1  "],
        }
    )
    decision = StoryDecisionNode.model_validate(
        {
            "node_id": "  node-1  ",
            "project_id": "  project-123  ",
            "node_type": "  DECISION  ",
            "change_type": "  ARC_SELECTION  ",
            "subject_type": "  ARC_SELECTION  ",
            "subject_id": "  selection-1  ",
            "parent_node_id": "  root-node  ",
            "branch_id": "  branch-main  ",
            "summary": "  Select primary quest arc  ",
            "prior_state_ref": "  arc:compare:primary-secondary  ",
            "new_state_ref": "  arc:selected:primary  ",
            "reason_or_note": "  The primary arc preserves the strongest opening shape.  ",
            "decision_made_at": "2026-03-20T12:00:00Z",
            "made_by": "  writer-1  ",
            "related_object_links": [
                {"object_type": "ARC_SELECTION", "object_id": "selection-1", "relation_kind": "primary"},
                {"object_type": "ARC_CANDIDATE", "object_id": "arc-primary", "relation_kind": "selected_arc"},
            ],
            "informing_object_links": [
                {"object_type": "ARC_COMPARISON_RECORD", "object_id": "comparison-1", "relation_kind": "informed_by"},
                {"object_type": "CHECKER_FINDING", "object_id": "finding-1", "relation_kind": "considered"},
            ],
        }
    )

    assert comparison.candidate_ids == ["arc-primary", "arc-secondary"]
    assert comparison.review_notes == ["Choose the cleaner opening path."]
    assert comparison.ranked_candidates[0].candidate.arc_id == "arc-primary"
    assert selection.comparison_record_ids == ["comparison-1"]
    assert selection.selected_arc.arc_id == "arc-primary"
    assert decision.node_type == StoryDecisionNodeType.DECISION.value
    assert decision.change_type == StoryDecisionChangeType.ARC_SELECTION.value
    assert decision.subject_type == StoryObjectType.ARC_SELECTION.value
    assert decision.parent_node_id == "root-node"
    assert decision.branch_id == "branch-main"
    assert decision.summary == "Select primary quest arc"
    assert decision.prior_state_ref == "arc:compare:primary-secondary"
    assert decision.new_state_ref == "arc:selected:primary"
    assert decision.informing_object_links[0].object_type == StoryObjectType.ARC_COMPARISON_RECORD.value
    assert decision.informing_object_links[1].object_id == "finding-1"
    assert decision.related_object_links[1].object_id == "arc-primary"

    with pytest.raises(ValidationError):
        StoryDecisionNode.model_validate(
            {
                "node_id": "node-2",
                "project_id": "project-123",
                "node_type": "DECISION",
                "change_type": "ARC_SELECTION",
                "subject_type": "ARC_SELECTION",
                "subject_id": "selection-1",
                "summary": "Missing timeline anchors.",
                "decision_made_at": "2026-03-20T12:00:00Z",
                "made_by": "writer-1",
            }
        )


def test_branch_models_validate_canonical_fork_identity() -> None:
    branch_point = BranchPoint.model_validate(
        {
            "branch_point_id": "  branch-point-1  ",
            "project_id": "  project-123  ",
            "source_node_id": "  node-branch-1  ",
        }
    )
    branch = StoryBranch.model_validate(
        {
            "branch_id": "  branch-main  ",
            "project_id": "  project-123  ",
            "branch_point_id": "  branch-point-1  ",
            "branch_name": "  Main Timeline  ",
            "branch_state": "  ACTIVE  ",
        }
    )

    assert branch_point.branch_point_id == "branch-point-1"
    assert branch_point.project_id == "project-123"
    assert branch_point.source_node_id == "node-branch-1"
    assert branch.branch_id == "branch-main"
    assert branch.project_id == "project-123"
    assert branch.branch_point_id == "branch-point-1"
    assert branch.branch_name == "Main Timeline"
    assert branch.branch_state == StoryBranchState.ACTIVE.value

    branch_state_ref = BranchStateRef.model_validate(
        {
            "branch_state_ref_id": "  branch-state-ref-1  ",
            "project_id": "  project-123  ",
            "branch_id": "  branch-main  ",
            "state_object_type": "  arc_selection  ",
            "state_object_id": "  selection-1  ",
            "decision_node_id": "  node-branch-1  ",
        }
    )

    assert branch_state_ref.branch_state_ref_id == "branch-state-ref-1"
    assert branch_state_ref.project_id == "project-123"
    assert branch_state_ref.branch_id == "branch-main"
    assert branch_state_ref.state_object_type == StoryObjectType.ARC_SELECTION.value
    assert branch_state_ref.state_object_id == "selection-1"
    assert branch_state_ref.decision_node_id == "node-branch-1"


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
