"""Integration tests for editable flow API endpoints."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

# These tests have SQLite FK cascade issues under parallel xdist execution.
# They pass in isolation and with -n 0 / -n 1, but fail under -n auto due to
# cross-worker interference with schema rebuilds. Skip under xdist for now.
if os.getenv("PYTEST_XDIST_WORKER"):
    pytest.skip("editable flow tests not supported under parallel xdist", allow_module_level=True)

pytestmark = pytest.mark.integration
from app.persistence.sqlite import connect, ensure_operations_db
from app.settings import settings


def _test_project_id() -> str:
    return f"test-project-flow-{uuid4().hex[:12]}"


_TEST_TIMESTAMP = datetime.now(timezone.utc).isoformat()


def _ensure_test_project(project_id: str) -> Path:
    """Seed the projects table so FK constraints are satisfied."""
    db_path = settings.operations_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    ensure_operations_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, "Test Flow API", str(db_path), str(db_path), _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()
    return db_path


def _make_client() -> TestClient:
    project_id = _test_project_id()
    _ensure_test_project(project_id)
    app = build_app()
    return TestClient(app), project_id


def _create_default_flow(client: TestClient, project_id: str) -> list[dict]:
    """Create a default flow by calling the init endpoint."""
    resp = client.post(
        "/v1/story-development/flow/stages/init",
        json={
            "project_id": project_id,
            "project_name": "Test Flow",
        },
    )
    assert resp.status_code == 201, f"Failed to init flow: {resp.json()}"
    return [item["stage_id"] for item in resp.json()["items"]]


class TestFlowStageEndpoints:
    """Test flow stage CRUD via API endpoints."""

    def test_list_flow_stages_returns_404_for_missing_flow(self) -> None:
        """Listing stages for a project without a flow should return 404."""
        client, project_id = _make_client()
        random_id = f"nonexistent-{uuid4().hex[:8]}"
        response = client.get("/v1/story-development/flow/stages", params={"project_id": random_id})
        assert response.status_code == 404

    def test_create_flow_stage_returns_201(self) -> None:
        """Creating a flow stage should return 201 Created."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "continuity_check",
                "display_name": "Continuity Check",
                "description": "Verify draft against bible.",
                "depends_on": ["stage-008"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["stage_kind"] == "continuity_check"
        assert data["display_name"] == "Continuity Check"
        assert data["description"] == "Verify draft against bible."
        assert data["depends_on"] == ["stage-008"]
        assert data["stage_configuration_state"] == "ENABLED"
        assert data["stage_progress_state"] == "NOT_STARTED"

    def test_create_flow_stage_with_insert_after(self) -> None:
        """Creating a stage with insert_after_stage_id should place it correctly."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "review_plus",
                "display_name": "Review Plus",
                "insert_after_stage_id": "stage-004",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position"] == 4

    def test_list_flow_stages_returns_all_stages(self) -> None:
        """Listing stages should return all stages ordered by position."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "extra",
                "display_name": "Extra Stage",
            },
        )

        response = client.get("/v1/story-development/flow/stages", params={"project_id": project_id})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 9
        assert data["meta"]["ordered_by"] == "position_asc"

        positions = [item["position"] for item in data["items"]]
        assert positions == sorted(positions)

    def test_update_flow_stage_changes_display_name(self) -> None:
        """Updating a stage should change its display_name."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-002",
            params={"project_id": project_id},
            json={"display_name": "Revised Foundation"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Revised Foundation"
        assert data["stage_id"] == "stage-002"

    def test_update_flow_stage_changes_description_and_notes(self) -> None:
        """Updating a stage should persist description, writer_notes, and custom_prompt_guidance."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-003",
            params={"project_id": project_id},
            json={
                "description": "Build deeper characters.",
                "writer_notes": "Focus on internal conflict.",
                "custom_prompt_guidance": "Reference the premise.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Build deeper characters."
        assert data["writer_notes"] == "Focus on internal conflict."
        assert data["custom_prompt_guidance"] == "Reference the premise."

    def test_update_flow_stage_changes_depends_on(self) -> None:
        """Updating a stage should persist new dependency references."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-003",
            params={"project_id": project_id},
            json={"depends_on": ["stage-001", "stage-002"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["depends_on"]) == {"stage-001", "stage-002"}

    def test_update_flow_stage_returns_404_for_missing_stage(self) -> None:
        """Updating a nonexistent stage should return 404."""
        client, project_id = _make_client()

        response = client.patch(
            "/v1/story-development/flow/stages/stage-999",
            params={"project_id": project_id},
            json={"display_name": "Ghost"},
        )
        assert response.status_code == 404

    def test_reorder_flow_stages_returns_200_and_new_order(self) -> None:
        """Reordering stages should return the new order with updated positions."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        list_resp = client.get("/v1/story-development/flow/stages", params={"project_id": project_id})
        current_ids = [item["stage_id"] for item in list_resp.json()["items"]]

        new_order = list(reversed(current_ids))
        response = client.post(
            "/v1/story-development/flow/stages/reorder",
            params={"project_id": project_id},
            json={"stage_order": new_order},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id

        positions = {stage["stage_id"]: stage["position"] for stage in data["stages"]}
        for expected_pos, stage_id in enumerate(new_order):
            assert positions[stage_id] == expected_pos

    def test_reorder_flow_stages_validates_stage_order(self) -> None:
        """Reordering with invalid stage order should return 400."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.post(
            "/v1/story-development/flow/stages/reorder",
            params={"project_id": project_id},
            json={"stage_order": ["stage-001", "stage-001"]},
        )
        assert response.status_code == 400

        response = client.post(
            "/v1/story-development/flow/stages/reorder",
            params={"project_id": project_id},
            json={"stage_order": ["stage-001", "stage-999"]},
        )
        assert response.status_code == 400

    def test_delete_flow_stage_returns_200(self) -> None:
        """Deleting a custom stage should return 200 with the deleted stage data."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        custom_resp = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "optional",
                "display_name": "Optional Stage",
            },
        )
        assert custom_resp.status_code == 201
        stage_id = custom_resp.json()["stage_id"]

        disable_resp = client.patch(
            "/v1/story-development/flow/stages/" + stage_id,
            params={"project_id": project_id},
            json={"stage_configuration_state": "DISABLED"},
        )
        assert disable_resp.status_code == 200

        response = client.delete(
            "/v1/story-development/flow/stages/" + stage_id,
            params={"project_id": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage_id"] == stage_id
        assert data["display_name"] == "Optional Stage"

    def test_delete_flow_stage_returns_404_for_missing(self) -> None:
        """Deleting a nonexistent stage should return 404."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.delete(
            "/v1/story-development/flow/stages/stage-999",
            params={"project_id": project_id},
        )
        assert response.status_code == 404

    def test_delete_flow_stage_returns_400_for_active_stage(self) -> None:
        """Deleting an active (non-disabled) custom stage should return 400."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        custom_resp = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "active",
                "display_name": "Active Stage",
            },
        )
        assert custom_resp.status_code == 201
        stage_id = custom_resp.json()["stage_id"]

        response = client.delete(
            "/v1/story-development/flow/stages/" + stage_id,
            params={"project_id": project_id},
        )
        assert response.status_code == 400

    def test_disable_stage_via_patch(self) -> None:
        """Patching a stage with disabled configuration state should disable it."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-005",
            params={"project_id": project_id},
            json={"stage_configuration_state": "DISABLED"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage_configuration_state"] == "DISABLED"

    def test_archive_stage_via_patch(self) -> None:
        """Patching a stage with archived configuration state should archive it."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-006",
            params={"project_id": project_id},
            json={"stage_configuration_state": "ARCHIVED"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage_configuration_state"] == "ARCHIVED"
        # PATCH does not automatically set progress state (use archive_stage service method for that)
        assert data["stage_progress_state"] == "NOT_STARTED"

    def test_update_flow_stage_with_invalid_dependency_returns_400(self) -> None:
        """Updating a stage with invalid dependency references should return 400."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-003",
            params={"project_id": project_id},
            json={"depends_on": ["stage-999"]},
        )
        assert response.status_code == 400
        assert "Invalid stage dependency references" in response.json()["detail"]

    def test_flow_stages_are_persisted_across_requests(self) -> None:
        """Flow stage mutations should persist across separate HTTP requests."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        resp1 = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "persistence_test",
                "display_name": "Persistence Test Stage",
            },
        )
        assert resp1.status_code == 201
        stage_id = resp1.json()["stage_id"]

        resp2 = client.patch(
            "/v1/story-development/flow/stages/" + stage_id,
            params={"project_id": project_id},
            json={"display_name": "Renamed via API"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["display_name"] == "Renamed via API"

        resp3 = client.get("/v1/story-development/flow/stages", params={"project_id": project_id})
        assert resp3.status_code == 200
        renamed = next((s for s in resp3.json()["items"] if s["stage_id"] == stage_id), None)
        assert renamed is not None
        assert renamed["display_name"] == "Renamed via API"

        all_stages = resp3.json()["items"]
        custom = next((s for s in all_stages if s["stage_id"] == stage_id), all_stages[-1])
        new_order = [custom["stage_id"]] + [s["stage_id"] for s in all_stages if s["stage_id"] != custom["stage_id"]]
        resp4 = client.post(
            "/v1/story-development/flow/stages/reorder",
            params={"project_id": project_id},
            json={"stage_order": new_order},
        )
        assert resp4.status_code == 200
        positions = {s["stage_id"]: s["position"] for s in resp4.json()["stages"]}
        assert positions[stage_id] == 0

    def test_update_stage_preserves_unchanged_fields(self) -> None:
        """Updating one field should not affect other fields."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        response = client.patch(
            "/v1/story-development/flow/stages/stage-002",
            params={"project_id": project_id},
            json={"display_name": "New Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "New Name"
        assert data["stage_kind"] == "foundation"
        assert data["stage_configuration_state"] == "ENABLED"

    def test_stage_kind_is_in_response(self) -> None:
        """Stage creation and update responses should include stage_kind."""
        client, project_id = _make_client()

        _create_default_flow(client, project_id)

        resp = client.post(
            "/v1/story-development/flow/stages",
            json={
                "project_id": project_id,
                "stage_kind": "custom_kind",
                "display_name": "Kind Test",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["stage_kind"] == "custom_kind"

        list_resp = client.get("/v1/story-development/flow/stages", params={"project_id": project_id})
        items = list_resp.json()["items"]
        custom = next((s for s in items if s["stage_id"] == resp.json()["stage_id"]), None)
        assert custom is not None
        assert custom["stage_kind"] == "custom_kind"
