from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryBranchState
from app.services.story_branching import (
    StoryBranchingNotFoundError,
    StoryBranchingService,
    StoryBranchingValidationError,
)


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)


def _seed_project(db_path: Path, project_id: str) -> None:
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                f"Project {project_id}",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _service(tmp_path: Path) -> tuple[StoryBranchingService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return StoryBranchingService(repository), repository


def _branch_context(
    repository: StoryDevelopmentRepository,
    project_id: str,
    *,
    prefix: str,
) -> tuple[str, str, str, str, str, str]:
    first_node = repository.record_story_decision_node(
        node_id=f"{prefix}-node-1",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id=f"{prefix}-selection-1",
        branch_id=f"{prefix}-branch-main",
        summary="Create the main storyline branch.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": f"{prefix}-selection-1", "relation_kind": "primary"}
        ],
        prior_state_ref="arc:selected:base",
        new_state_ref=f"arc:selected:{prefix}:main",
        reason_or_note="Fork the story at the first decision point.",
        made_by="writer:test",
        decision_made_at=STAMP,
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_node = repository.record_story_decision_node(
        node_id=f"{prefix}-node-2",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id=f"{prefix}-selection-2",
        branch_id=f"{prefix}-branch-alt",
        summary="Create the alternate storyline branch.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": f"{prefix}-selection-2", "relation_kind": "primary"}
        ],
        prior_state_ref=f"arc:selected:{prefix}:main",
        new_state_ref=f"arc:selected:{prefix}:alt",
        reason_or_note="Keep an alternate path under review.",
        made_by="writer:test",
        decision_made_at=STAMP.replace(hour=13),
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )
    first_point = repository.upsert_branch_point(
        branch_point_id=f"{prefix}-branch-point-1",
        project_id=project_id,
        source_node_id=first_node.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_point = repository.upsert_branch_point(
        branch_point_id=f"{prefix}-branch-point-2",
        project_id=project_id,
        source_node_id=second_node.node_id,
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )
    first_branch = repository.upsert_story_branch(
        branch_id=f"{prefix}-branch-main",
        project_id=project_id,
        branch_point_id=first_point.branch_point_id,
        branch_name="Main Timeline",
        branch_state=StoryBranchState.ACTIVE,
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_branch = repository.upsert_story_branch(
        branch_id=f"{prefix}-branch-alt",
        project_id=project_id,
        branch_point_id=second_point.branch_point_id,
        branch_name="Alternate Timeline",
        branch_state=StoryBranchState.ARCHIVED,
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )
    return (
        first_node.node_id,
        second_node.node_id,
        first_point.branch_point_id,
        second_point.branch_point_id,
        first_branch.branch_id,
        second_branch.branch_id,
    )


def test_story_branching_service_can_fork_compare_select_and_merge(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "branching-service-1"
    _seed_project(repository.db_path, project_id)

    first_node_id, second_node_id, first_point_id, second_point_id, first_branch_id, second_branch_id = _branch_context(
        repository,
        project_id,
        prefix="project-one",
    )

    branches = service.list_story_branches(project_id)
    assert [branch.branch_id for branch in branches] == [first_branch_id, second_branch_id]
    assert branches[0].branch_state == StoryBranchState.ACTIVE.value
    assert branches[1].branch_state == StoryBranchState.ARCHIVED.value

    comparison = service.compare_story_branches(
        project_id,
        comparison_id="comparison-1",
        source_branch_id=first_branch_id,
        target_branch_id=second_branch_id,
        review_notes=["Main path is cleaner.", "Alternate path adds tension."],
    )
    assert comparison.comparison_id == "comparison-1"
    assert comparison.source_branch_id == first_branch_id
    assert comparison.target_branch_id == second_branch_id
    assert comparison.review_notes == ["Main path is cleaner.", "Alternate path adds tension."]
    stored_comparison = repository.get_branch_comparison(project_id, comparison_id="comparison-1")
    assert stored_comparison.comparison_id == comparison.comparison_id
    assert stored_comparison.project_id == comparison.project_id
    assert stored_comparison.source_branch_id == comparison.source_branch_id
    assert stored_comparison.target_branch_id == comparison.target_branch_id
    assert stored_comparison.review_notes == comparison.review_notes

    active_branch = service.select_active_branch(project_id, branch_id=second_branch_id)
    assert active_branch.branch_id == second_branch_id
    assert active_branch.branch_state == StoryBranchState.ACTIVE.value
    assert repository.get_story_branch(first_branch_id).branch_state == StoryBranchState.ARCHIVED
    assert repository.get_story_branch(second_branch_id).branch_state == StoryBranchState.ACTIVE

    merge_decision = service.record_branch_merge_decision(
        project_id,
        merge_decision_id="merge-1",
        source_branch_id=first_branch_id,
        target_branch_id=second_branch_id,
        merge_rationale="Keep the opening from the main path and the midpoint from the alternate path.",
        resulting_decision_node_ids=[first_node_id, second_node_id],
    )
    assert merge_decision.merge_decision_id == "merge-1"
    assert merge_decision.source_branch_id == first_branch_id
    assert merge_decision.target_branch_id == second_branch_id
    assert merge_decision.resulting_decision_node_ids == [first_node_id, second_node_id]
    stored_merge = repository.get_branch_merge_decision(project_id, merge_decision_id="merge-1")
    assert stored_merge.merge_decision_id == merge_decision.merge_decision_id
    assert stored_merge.project_id == merge_decision.project_id
    assert stored_merge.source_branch_id == merge_decision.source_branch_id
    assert stored_merge.target_branch_id == merge_decision.target_branch_id
    assert stored_merge.merge_rationale == merge_decision.merge_rationale
    assert stored_merge.resulting_decision_node_ids == merge_decision.resulting_decision_node_ids
    assert [record.merge_decision_id for record in repository.list_branch_merge_decisions(project_id)] == ["merge-1"]


def test_story_branching_service_rejects_branch_scope_and_pairing_errors(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "branching-service-2"
    other_project_id = "branching-service-2-other"
    _seed_project(repository.db_path, project_id)
    _seed_project(repository.db_path, other_project_id)

    _, _, _, _, first_branch_id, _ = _branch_context(repository, project_id, prefix="project-two")
    other_node_id, _, other_point_id, _, other_branch_id, _ = _branch_context(repository, other_project_id, prefix="other-project")

    with pytest.raises(StoryBranchingValidationError):
        service.create_story_branch(
            project_id,
            branch_id="branch-invalid",
            branch_point_id=other_point_id,
            branch_name="Cross Project Branch",
            branch_state=StoryBranchState.ACTIVE,
        )

    with pytest.raises(StoryBranchingValidationError):
        service.compare_story_branches(
            project_id,
            comparison_id="comparison-same",
            source_branch_id=first_branch_id,
            target_branch_id=first_branch_id,
            review_notes=["Same branch comparisons are invalid."],
        )

    with pytest.raises(StoryBranchingNotFoundError):
        service.compare_story_branches(
            project_id,
            comparison_id="comparison-cross-project",
            source_branch_id=first_branch_id,
            target_branch_id=other_branch_id,
            review_notes=["Cross project compare should fail."],
        )

    with pytest.raises(StoryBranchingValidationError):
        service.record_branch_merge_decision(
            project_id,
            merge_decision_id="merge-same",
            source_branch_id=first_branch_id,
            target_branch_id=first_branch_id,
            merge_rationale="Same-branch merge should be rejected.",
        )

    with pytest.raises(StoryBranchingNotFoundError):
        service.record_branch_merge_decision(
            project_id,
            merge_decision_id="merge-cross-project",
            source_branch_id=first_branch_id,
            target_branch_id=other_branch_id,
            merge_rationale="Cross project merge should fail.",
            resulting_decision_node_ids=[other_node_id],
        )
