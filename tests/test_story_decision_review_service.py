from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.story_decision_review import (
    StoryDecisionReviewNotFoundError,
    StoryDecisionReviewService,
    StoryDecisionReviewValidationError,
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


def _service(tmp_path: Path) -> tuple[StoryDecisionReviewService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return StoryDecisionReviewService(repository), repository


def _seed_decision_nodes(repository: StoryDevelopmentRepository, project_id: str) -> None:
    repository.record_story_decision_node(
        node_id="node-a",
        project_id=project_id,
        node_type="DECISION",
        change_type="ARC_SELECTION",
        subject_type="ARC_SELECTION",
        subject_id="selection-001",
        branch_id="branch-main",
        summary="Initial arc selection.",
        prior_state_summary="No arc had been selected yet.",
        new_state_summary="Mystery arc becomes active.",
        reason_or_note="The mystery arc fits the opening mood.",
        made_by="writer:alex",
        decision_made_at=STAMP,
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-001", "relation_kind": "primary"},
            {"object_type": "ARC_CANDIDATE", "object_id": "arc-secondary", "relation_kind": "previous_choice"},
        ],
        informing_object_links=[
            {"object_type": "ARC_COMPARISON_RECORD", "object_id": "comparison-000", "relation_kind": "informed_by"},
        ],
        created_at=STAMP,
        updated_at=STAMP,
    )
    repository.record_story_decision_node(
        node_id="node-b",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="ARC_PIVOT",
        subject_type="ARC_SELECTION",
        subject_id="selection-001",
        parent_node_id="node-a",
        branch_id="branch-main",
        summary="Pivot toward the primary arc.",
        prior_state_ref="arc:secondary",
        prior_state_summary="Secondary arc was active.",
        new_state_ref="arc:primary",
        new_state_summary="Primary arc becomes active.",
        reason_or_note="The primary arc has cleaner escalation.",
        made_by="writer:alex",
        decision_made_at=STAMP.replace(hour=13),
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-001", "relation_kind": "primary"},
            {"object_type": "ARC_CANDIDATE", "object_id": "arc-primary", "relation_kind": "selected_arc"},
        ],
        informing_object_links=[
            {"object_type": "ARC_COMPARISON_RECORD", "object_id": "comparison-001", "relation_kind": "informed_by"},
            {"object_type": "CHECKER_FINDING", "object_id": "finding-009", "relation_kind": "considered"},
        ],
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )
    repository.record_story_decision_node(
        node_id="node-c",
        project_id=project_id,
        node_type="DECISION",
        change_type="STAGE_REDEFINE",
        subject_type="STORY_FLOW_STAGE",
        subject_id="brainstorm",
        parent_node_id="node-b",
        branch_id="branch-main",
        summary="Redefine the brainstorm stage.",
        prior_state_ref="stage:v1",
        prior_state_summary="Lightweight ideation only.",
        new_state_ref="stage:v2",
        new_state_summary="Add clustering guidance.",
        reason_or_note="The flow needs a stronger early structure.",
        made_by="writer:alex",
        decision_made_at=STAMP.replace(hour=14),
        related_object_links=[
            {"object_type": "STORY_FLOW_STAGE", "object_id": "brainstorm", "relation_kind": "primary"},
        ],
        informing_object_links=[
            {"object_type": "STORY_FLOW_DEFINITION", "object_id": project_id, "relation_kind": "project_flow"},
        ],
        created_at=STAMP.replace(hour=14),
        updated_at=STAMP.replace(hour=14),
    )


def test_story_decision_review_lists_and_filters_nodes_in_timeline_order(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "decision-review-list"
    _seed_project(repository.db_path, project_id)
    _seed_decision_nodes(repository, project_id)

    all_nodes = service.list_story_decision_nodes(project_id)
    filtered_nodes = service.list_story_decision_nodes(project_id, subject_type="ARC_SELECTION", subject_id="selection-001")

    assert [node.node_id for node in all_nodes] == ["node-a", "node-b", "node-c"]
    assert [node.node_id for node in filtered_nodes] == ["node-a", "node-b"]
    assert filtered_nodes[1].change_type == "ARC_PIVOT"
    assert filtered_nodes[1].informing_object_links[0].object_id == "comparison-001"
    assert filtered_nodes[0].related_object_links[1].relation_kind == "previous_choice"


def test_story_decision_review_reconstructs_parent_path(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "decision-review-path"
    _seed_project(repository.db_path, project_id)
    _seed_decision_nodes(repository, project_id)

    review = service.inspect_story_decision_node(project_id, node_id="node-c")
    path = service.list_story_decision_path(project_id, node_id="node-c")

    assert [node.node_id for node in review.parent_path] == ["node-a", "node-b"]
    assert [node.node_id for node in path] == ["node-a", "node-b", "node-c"]
    assert review.node.parent_node_id == "node-b"
    assert review.node.branch_id == "branch-main"
    assert review.node.related_object_links[0].object_id == "brainstorm"


def test_story_decision_review_rejects_bad_inputs_and_missing_nodes(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "decision-review-errors"
    _seed_project(repository.db_path, project_id)
    _seed_decision_nodes(repository, project_id)

    try:
        service.list_story_decision_nodes(project_id, subject_type="ARC_SELECTION")
    except StoryDecisionReviewValidationError:
        pass
    else:
        raise AssertionError("expected subject filter validation error")

    try:
        service.inspect_story_decision_node(project_id, node_id="missing-node")
    except StoryDecisionReviewNotFoundError:
        pass
    else:
        raise AssertionError("expected missing node error")
