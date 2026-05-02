from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.story_generation import build_story_generation_router
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.projects import ProjectCreateRequest
from app.services.job_manager import JobManager
from app.services.projects import ProjectService


def _build_app(tmp_path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    project_service = ProjectService(tmp_path)
    job_manager = JobManager(db_path)

    project_service.create_project(
        ProjectCreateRequest(
            project_id="source-project",
            project_name="Source",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    repository.upsert_foundation_profile(
        project_id="source-project",
        premise="A kingdom in decline.",
        logline="A disgraced knight returns home.",
    )
    repository.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )

    app = FastAPI()
    app.include_router(build_story_generation_router(repository, project_service, job_manager))
    return TestClient(app), repository


def _base_payload(source_project_id: str = "source-project") -> dict:
    return {
        "source_project_id": source_project_id,
        "mode": "same_project_side_story",
        "destination": {
            "destination_kind": "same_project",
            "target_project_id": source_project_id,
        },
        "canon_scope": {
            "source_project_id": source_project_id,
            "character_ids": ["char-1"],
        },
        "generation_brief": "Generate a side story.",
        "target_chapter_count": 2,
    }


def test_story_generation_api_create_and_fetch_run(tmp_path) -> None:
    client, _ = _build_app(tmp_path)
    payload = _base_payload()
    create_response = client.post("/v1/story-generation/runs", json=payload)
    assert create_response.status_code == 201
    generation_id = create_response.json()["generation_id"]

    fetch_response = client.get(f"/v1/story-generation/runs/{generation_id}")
    assert fetch_response.status_code == 200

    list_response = client.get("/v1/story-generation/runs", params={"project_id": "source-project"})
    assert list_response.status_code == 200
    assert list_response.json()


def test_story_generation_post_runs_404_nonexistent_source(tmp_path) -> None:
    """POST /runs returns 404 when source project doesn't exist."""
    client, _ = _build_app(tmp_path)
    payload = {
        "source_project_id": "nonexistent-project",
        "mode": "same_project_side_story",
        "destination": {
            "destination_kind": "same_project",
            "target_project_id": "nonexistent-project",
        },
        "canon_scope": {
            "source_project_id": "nonexistent-project",
            "character_ids": ["char-1"],
        },
        "generation_brief": "Generate a side story.",
        "target_chapter_count": 2,
    }
    response = client.post("/v1/story-generation/runs", json=payload)
    assert response.status_code == 404


def test_story_generation_post_runs_409_idempotency_conflict(tmp_path) -> None:
    """POST /runs returns 409 on idempotency key conflict (same key, different payload)."""
    client, _ = _build_app(tmp_path)
    payload1 = _base_payload()
    payload1["idempotency_key"] = "idem-key-1"
    response1 = client.post("/v1/story-generation/runs", json=payload1)
    assert response1.status_code == 201

    payload2 = _base_payload()
    payload2["idempotency_key"] = "idem-key-1"
    payload2["generation_brief"] = "A different brief to change the request hash."
    response2 = client.post("/v1/story-generation/runs", json=payload2)
    assert response2.status_code == 409
    assert "idempotency key conflict" in response2.json()["detail"].lower()


def test_story_generation_post_runs_422_empty_scope(tmp_path) -> None:
    """POST /runs returns 422 on validation error (empty scope without full_project)."""
    client, _ = _build_app(tmp_path)
    payload = {
        "source_project_id": "source-project",
        "mode": "same_project_side_story",
        "destination": {
            "destination_kind": "same_project",
            "target_project_id": "source-project",
        },
        "canon_scope": {
            "source_project_id": "source-project",
        },
        "generation_brief": "Generate a side story.",
    }
    response = client.post("/v1/story-generation/runs", json=payload)
    assert response.status_code == 422


def test_story_generation_get_run_404_nonexistent(tmp_path) -> None:
    """GET /runs/{id} returns 404 for nonexistent generation_id."""
    client, _ = _build_app(tmp_path)
    response = client.get("/v1/story-generation/runs/nonexistent-gen-id")
    assert response.status_code == 404


def test_story_generation_retry_run_200_existing(tmp_path) -> None:
    """POST /runs/{id}/retry returns 200 with existing run data."""
    client, _ = _build_app(tmp_path)
    create_resp = client.post("/v1/story-generation/runs", json=_base_payload())
    assert create_resp.status_code == 201
    generation_id = create_resp.json()["generation_id"]

    retry_resp = client.post(f"/v1/story-generation/runs/{generation_id}/retry")
    assert retry_resp.status_code == 200
    data = retry_resp.json()
    assert data["generation_id"] == generation_id
    assert data["source_project_id"] == "source-project"


def test_story_generation_retry_run_404_nonexistent(tmp_path) -> None:
    """POST /runs/{id}/retry returns 404 for nonexistent generation_id."""
    client, _ = _build_app(tmp_path)
    response = client.post("/v1/story-generation/runs/nonexistent-gen-id/retry")
    assert response.status_code == 404


def test_story_generation_get_packet_200_after_submit(tmp_path) -> None:
    """GET /runs/{id}/packet returns 200 with CanonGenerationPacket after submit."""
    client, _ = _build_app(tmp_path)
    create_resp = client.post("/v1/story-generation/runs", json=_base_payload())
    assert create_resp.status_code == 201
    generation_id = create_resp.json()["generation_id"]

    packet_resp = client.get(f"/v1/story-generation/runs/{generation_id}/packet")
    assert packet_resp.status_code == 200
    data = packet_resp.json()
    assert "packet_id" in data
    assert data["source_project_id"] == "source-project"


def test_story_generation_get_packet_404_no_packet(tmp_path) -> None:
    """GET /runs/{id}/packet returns 404 when no packet exists."""
    client, _ = _build_app(tmp_path)
    response = client.get("/v1/story-generation/runs/nonexistent-gen-id/packet")
    assert response.status_code == 404


def test_story_generation_get_gates_200_empty(tmp_path) -> None:
    """GET /runs/{id}/gates returns 200 with empty items list (no gates yet)."""
    client, _ = _build_app(tmp_path)
    create_resp = client.post("/v1/story-generation/runs", json=_base_payload())
    assert create_resp.status_code == 201
    generation_id = create_resp.json()["generation_id"]

    gates_resp = client.get(f"/v1/story-generation/runs/{generation_id}/gates")
    assert gates_resp.status_code == 200
    data = gates_resp.json()
    assert data["generation_id"] == generation_id
    assert data["items"] == []


def test_story_generation_fork_preview_200(tmp_path) -> None:
    """POST /fork-preview returns 200 with selected scope echoed back."""
    client, _ = _build_app(tmp_path)
    payload = _base_payload()
    response = client.post("/v1/story-generation/fork-preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source_project_id"] == "source-project"
    assert data["mode"] == "same_project_side_story"
    assert data["destination_kind"] == "same_project"
    assert data["selected_character_ids"] == ["char-1"]


def test_story_generation_fork_project_no_generation(tmp_path) -> None:
    """POST /fork-project with start_generation=false creates project only, empty job_ids."""
    client, _ = _build_app(tmp_path)
    payload = {
        "source_project_id": "source-project",
        "mode": "new_project_character_fork",
        "destination": {
            "destination_kind": "new_project",
            "target_project_name": "Forked Story",
        },
        "canon_scope": {
            "source_project_id": "source-project",
            "character_ids": ["char-1"],
        },
        "generation_brief": "Generate a fork.",
    }
    response = client.post(
        "/v1/story-generation/fork-project?start_generation=false",
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_project_id"] == "source-project"
    assert data["job_ids"] == []


def test_story_generation_list_runs_both_roles(tmp_path) -> None:
    """GET /runs?project_id= returns runs for both source and target roles."""
    client, _ = _build_app(tmp_path)

    # Create a run where source-project is both source and target (same_project destination)
    create_resp = client.post("/v1/story-generation/runs", json=_base_payload())
    assert create_resp.status_code == 201
    generation_id = create_resp.json()["generation_id"]

    # List runs for source-project - should find the run above
    list_resp = client.get("/v1/story-generation/runs", params={"project_id": "source-project"})
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1

    found_ids = {run["generation_id"] for run in runs}
    assert generation_id in found_ids
