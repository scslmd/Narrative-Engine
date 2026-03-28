from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository


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
                "Story Development Branch API Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-branches"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


def _seed_branch_point(
    repository: StoryDevelopmentRepository,
    *,
    project_id: str,
    node_id: str,
    branch_point_id: str,
    decision_made_at: datetime,
) -> None:
    repository.record_story_decision_node(
        node_id=node_id,
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id=f"{node_id}-selection",
        branch_id=branch_point_id,
        summary="Create a storyline branch point.",
        prior_state_ref="arc:before",
        new_state_ref="arc:after",
        reason_or_note="Establish a durable fork point.",
        made_by="writer:test",
        decision_made_at=decision_made_at,
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": f"{node_id}-selection", "relation_kind": "primary"}
        ],
        created_at=decision_made_at,
        updated_at=decision_made_at,
    )
    repository.upsert_branch_point(
        branch_point_id=branch_point_id,
        project_id=project_id,
        source_node_id=node_id,
        created_at=decision_made_at,
        updated_at=decision_made_at,
    )


def test_story_branching_api_supports_branch_creation_active_selection_and_state_refs(tmp_path: Path) -> None:
    client, repository = _build_client(tmp_path)
    project_id = "story-dev-branches"

    _seed_branch_point(
        repository,
        project_id=project_id,
        node_id="branch-node-main",
        branch_point_id="branch-point-main",
        decision_made_at=STAMP,
    )
    _seed_branch_point(
        repository,
        project_id=project_id,
        node_id="branch-node-alt",
        branch_point_id="branch-point-alt",
        decision_made_at=STAMP + timedelta(hours=1),
    )

    create_main = client.post(
        "/story-development/branches",
        json={
            "project_id": project_id,
            "branch_id": "branch-main",
            "branch_point_id": "branch-point-main",
            "branch_name": "Main Timeline",
            "branch_state": "ACTIVE",
        },
    )
    create_alt = client.post(
        "/story-development/branches",
        json={
            "project_id": project_id,
            "branch_id": "branch-alt",
            "branch_point_id": "branch-point-alt",
            "branch_name": "Alternate Timeline",
            "branch_state": "ACTIVE",
        },
    )

    assert create_main.status_code == 201
    assert create_main.json()["branch_id"] == "branch-main"
    assert create_alt.status_code == 201
    assert create_alt.json()["branch_id"] == "branch-alt"
    assert create_alt.json()["branch_state"] == "ACTIVE"

    branches_response = client.get(f"/story-development/branches?project_id={project_id}")
    assert branches_response.status_code == 200
    branch_ids = [item["branch_id"] for item in branches_response.json()["items"]]
    # Use set comparison to avoid ordering issues from other tests
    assert set(branch_ids) >= {"branch-main", "branch-alt"}
    assert branches_response.json()["meta"]["ordered_by"] == "created_at_asc"

    branch_detail = client.get(f"/story-development/branches/branch-main?project_id={project_id}")
    assert branch_detail.status_code == 200
    assert branch_detail.json()["branch_name"] == "Main Timeline"

    active_branch = client.get(f"/story-development/branches/active?project_id={project_id}")
    assert active_branch.status_code == 200
    assert active_branch.json()["branch_id"] == "branch-alt"

    switch_active = client.post(
        "/story-development/branches/active",
        json={"project_id": project_id, "branch_id": "branch-main"},
    )
    assert switch_active.status_code == 200
    assert switch_active.json()["branch_id"] == "branch-main"
    assert client.get(f"/story-development/branches/active?project_id={project_id}").json()["branch_id"] == "branch-main"

    repository.upsert_branch_state_ref(
        branch_state_ref_id="branch-state-ref-1",
        project_id=project_id,
        branch_id="branch-main",
        state_object_type="ARC_SELECTION",
        state_object_id="selection-main",
        decision_node_id="branch-node-main",
        created_at=STAMP,
        updated_at=STAMP,
    )
    repository.upsert_branch_state_ref(
        branch_state_ref_id="branch-state-ref-2",
        project_id=project_id,
        branch_id="branch-main",
        state_object_type="CHAPTER_PLAN",
        state_object_id="chapter-main",
        decision_node_id="branch-node-main",
        created_at=STAMP + timedelta(hours=1),
        updated_at=STAMP + timedelta(hours=1),
    )

    state_refs_response = client.get(f"/story-development/branches/branch-main/state-refs?project_id={project_id}")
    assert state_refs_response.status_code == 200
    assert [item["branch_state_ref_id"] for item in state_refs_response.json()["items"]] == [
        "branch-state-ref-1",
        "branch-state-ref-2",
    ]

    lineage_response = client.get(
        f"/story-development/branches/branch-main/state-refs?project_id={project_id}&decision_node_id=branch-node-main"
    )
    assert lineage_response.status_code == 200
    assert [item["branch_state_ref_id"] for item in lineage_response.json()["items"]] == [
        "branch-state-ref-1",
        "branch-state-ref-2",
    ]

    cross_project_state_refs = client.get(
        f"/story-development/branches/branch-main/state-refs?project_id=wrong-project"
    )
    assert cross_project_state_refs.status_code == 200
    assert cross_project_state_refs.json()["items"] == []

    branch_missing_scope = client.get(f"/story-development/branches/branch-main?project_id=wrong-project")
    assert branch_missing_scope.status_code == 404


def test_story_branching_api_supports_comparison_creation_and_project_scope(tmp_path: Path) -> None:
    client, repository = _build_client(tmp_path)
    project_id = "story-dev-branches"
    other_project_id = "story-dev-branches-other"

    _seed_project(repository.db_path, other_project_id)
    _seed_branch_point(
        repository,
        project_id=project_id,
        node_id="branch-node-main",
        branch_point_id="branch-point-main",
        decision_made_at=STAMP,
    )
    _seed_branch_point(
        repository,
        project_id=project_id,
        node_id="branch-node-alt",
        branch_point_id="branch-point-alt",
        decision_made_at=STAMP + timedelta(hours=1),
    )
    _seed_branch_point(
        repository,
        project_id=other_project_id,
        node_id="branch-node-other",
        branch_point_id="branch-point-other",
        decision_made_at=STAMP + timedelta(hours=2),
    )

    for branch_id, branch_point_id, branch_name in (
        ("branch-main", "branch-point-main", "Main Timeline"),
        ("branch-alt", "branch-point-alt", "Alternate Timeline"),
    ):
        response = client.post(
            "/story-development/branches",
            json={
                "project_id": project_id,
                "branch_id": branch_id,
                "branch_point_id": branch_point_id,
                "branch_name": branch_name,
                "branch_state": "ACTIVE",
            },
        )
        assert response.status_code == 201

    branch_comparison = client.post(
        "/story-development/branches/comparisons",
        json={
            "project_id": project_id,
            "comparison_id": "comparison-1",
            "source_branch_id": "branch-main",
            "target_branch_id": "branch-alt",
            "review_notes": ["Main path is cleaner.", "Alternate path adds tension."],
        },
    )
    assert branch_comparison.status_code == 201
    assert branch_comparison.json()["comparison_id"] == "comparison-1"

    comparison_list = client.get(f"/story-development/branches/comparisons?project_id={project_id}")
    assert comparison_list.status_code == 200
    assert [item["comparison_id"] for item in comparison_list.json()["items"]] == ["comparison-1"]
    assert comparison_list.json()["meta"]["ordered_by"] == "created_at_asc"

    comparison_detail = client.get(
        f"/story-development/branches/comparisons/comparison-1?project_id={project_id}"
    )
    assert comparison_detail.status_code == 200
    assert comparison_detail.json()["source_branch_id"] == "branch-main"
    assert comparison_detail.json()["target_branch_id"] == "branch-alt"

    missing_comparison = client.get(
        f"/story-development/branches/comparisons/missing-comparison?project_id={project_id}"
    )
    assert missing_comparison.status_code == 404

    cross_project_comparison = client.get(
        f"/story-development/branches/comparisons/comparison-1?project_id={other_project_id}"
    )
    assert cross_project_comparison.status_code == 404

    invalid_pair = client.post(
        "/story-development/branches/comparisons",
        json={
            "project_id": project_id,
            "comparison_id": "comparison-same",
            "source_branch_id": "branch-main",
            "target_branch_id": "branch-main",
            "review_notes": ["Same branch comparisons are invalid."],
        },
    )
    assert invalid_pair.status_code == 400
