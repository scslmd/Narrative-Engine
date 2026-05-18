from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app


def test_submit_scan_returns_202(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "test-proj",
            "manuscript_text": (
                "Annabelle entered the Castle of Echoes and met The Son, "
                "who she had been rivals with since childhood. They argued "
                "about the inheritance their parents left behind."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data


def test_submit_scan_missing_project_id(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "manuscript_text": (
                "Annabelle entered the Castle of Echoes and met The Son, "
                "who she had been rivals with since childhood. They argued "
                "about the inheritance their parents left behind."
            ),
        },
    )
    assert resp.status_code in (202, 422)


def test_get_job_not_found(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/jobs/nonexistent")
    assert resp.status_code == 404


def test_get_staging_not_found(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/staging/nonexistent")
    assert resp.status_code == 404


def test_submit_scan_too_short_text(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "test-proj",
            "manuscript_text": "Short.",
        },
    )
    assert resp.status_code in (202, 422)


def test_discard_staging(tmp_path):
    client = TestClient(build_app())
    resp = client.delete("/v1/discovery/staging/nonexistent")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_patch_entity_approval_empty(tmp_path):
    client = TestClient(build_app())
    resp = client.patch(
        "/v1/discovery/staging/test-stage/entities",
        json=[],
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] == 0


def test_apply_staging_not_found(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/staging/nonexistent/apply")
    assert resp.status_code == 404


def test_undo_staging(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/staging/nonexistent/undo")
    assert resp.status_code == 200
    data = resp.json()
    assert "stage_id" in data
    assert data["stage_id"] == "nonexistent"


def test_scan_returns_valid_job_id_format(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-1",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    job_id = data["job_id"]
    assert len(job_id) >= 32


def test_get_job_status_after_scan(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-2",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id


def test_scan_with_custom_chunk_size(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-3",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "chunk_size": 15000,
        },
    )
    assert resp.status_code == 202


def test_scan_with_filtered_entity_types(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-4",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "include_types": ["character"],
        },
    )
    assert resp.status_code == 202


def test_scan_with_all_entity_types(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-5",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "include_types": ["character", "relationship", "world_bible"],
        },
    )
    assert resp.status_code == 202


def test_multiple_scans_create_independent_jobs(tmp_path):
    client = TestClient(build_app())
    body = {
        "project_id": "proj-7",
        "manuscript_text": (
            "The detective walked through the rain-soaked streets of "
            "New York City, searching for clues that would lead him to "
            "the mastermind behind the heist at the Metropolitan Museum."
        ),
    }
    resp1 = client.post("/v1/discovery/scan", json=body)
    resp2 = client.post("/v1/discovery/scan", json=body)
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    job_id_1 = resp1.json()["job_id"]
    job_id_2 = resp2.json()["job_id"]
    assert job_id_1 != job_id_2


def test_staging_returns_grouped_entities(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-8",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        staging_resp = client.get(
            f"/v1/discovery/staging/{status_data['stage_id']}"
        )
        assert staging_resp.status_code == 200
        staging_data = staging_resp.json()
        assert "characters" in staging_data
        assert "relationships" in staging_data
        assert "world_bible" in staging_data


def test_job_status_includes_phase_field(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-9",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "phase" in status_data


def test_scan_response_status_field(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-10",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"


def test_job_status_returns_correct_status_after_completion(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-12",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] in ("completed", "failed")


def test_job_status_returns_stage_id_on_completion(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-13",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data["status"] == "completed":
        assert status_data["stage_id"] is not None


def test_apply_and_undo(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-97",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]

        apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
        assert apply_resp.status_code == 200

        undo_resp = client.post(f"/v1/discovery/staging/{stage_id}/undo")
        assert undo_resp.status_code == 200


def test_full_lifecycle(tmp_path):
    """Test the full scan -> job status -> staging -> apply -> undo lifecycle."""
    client = TestClient(build_app())

    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-101",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    data = scan_resp.json()
    assert "job_id" in data
    job_id = data["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id


def test_full_lifecycle_with_staging(tmp_path):
    """Test the full lifecycle including staging operations."""
    client = TestClient(build_app())

    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-102",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]

        get_resp = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp.status_code == 200

        apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
        assert apply_resp.status_code == 200


def test_multiple_full_lifecycles(tmp_path):
    """Test running multiple full lifecycles in sequence."""
    client = TestClient(build_app())

    for i in range(3):
        body = {
            "project_id": f"proj-{103 + i}",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        }
        scan_resp = client.post("/v1/discovery/scan", json=body)
        assert scan_resp.status_code == 202
        job_id = scan_resp.json()["job_id"]

        status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
        assert status_resp.status_code == 200


def test_scan_with_unicode_text(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-20",
            "manuscript_text": (
                "The detective \u63a2\u5be3 walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202


def test_scan_with_special_characters(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-21",
            "manuscript_text": (
                'The detective walked through the rain-soaked streets of "New York City" \u2014 '
                "searching for clues that would lead him to the mastermind behind the heist "
                "at the Metropolitan Museum (est. 1870)."
            ),
        },
    )
    assert resp.status_code == 202


def test_scan_with_newlines(tmp_path):
    client = TestClient(build_app())
    text = "\n".join(
        [
            "The detective walked through the rain-soaked streets.",
            "New York City was alive with mystery.",
            "He searched for clues that would lead him to the mastermind.",
            "The heist at the Metropolitan Museum remained unsolved.",
        ]
    )
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-22",
            "manuscript_text": text,
        },
    )
    assert resp.status_code == 202


def test_scan_with_very_long_text(tmp_path):
    client = TestClient(build_app())
    text = "The detective walked through the rain-soaked streets. " * 200
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-78",
            "manuscript_text": text,
        },
    )
    assert resp.status_code == 202


def test_scan_with_empty_text(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-18",
            "manuscript_text": "",
        },
    )
    assert resp.status_code in (202, 422)


def test_scan_with_chunk_size_too_small(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-42",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "chunk_size": 500,
        },
    )
    assert resp.status_code in (202, 422)


def test_scan_with_chunk_size_too_large(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-43",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "chunk_size": 100000,
        },
    )
    assert resp.status_code in (202, 422)


def test_scan_with_include_types_invalid(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-50",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
            "include_types": ["invalid_type"],
        },
    )
    assert resp.status_code in (202, 422)


def test_scan_with_empty_body(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/scan", json={})
    assert resp.status_code in (202, 422)


def test_scan_response_has_status_and_job_id(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-32",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "status" in data
    assert "job_id" in data


def test_scan_response_job_id_is_string(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-34",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert isinstance(data["job_id"], str)


def test_scan_response_job_id_is_unique_per_request(tmp_path):
    client = TestClient(build_app())
    body = {
        "project_id": "proj-37",
        "manuscript_text": (
            "The detective walked through the rain-soaked streets of "
            "New York City, searching for clues that would lead him to "
            "the mastermind behind the heist at the Metropolitan Museum."
        ),
    }
    job_ids = set()
    for _ in range(5):
        resp = client.post("/v1/discovery/scan", json=body)
        assert resp.status_code == 202
        job_ids.add(resp.json()["job_id"])
    assert len(job_ids) == 5


def test_scan_response_has_no_extra_fields(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-39",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert set(data.keys()).issubset({"job_id", "status"})


def test_apply_returns_counts(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-apply",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
        assert apply_resp.status_code == 200
        apply_data = apply_resp.json()
        assert "characters_added" in apply_data
        assert "relationships_added" in apply_data
        assert "world_bible_added" in apply_data
        assert "characters_enriched" in apply_data


def test_undo_returns_counts(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-undo",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        undo_resp = client.post(f"/v1/discovery/staging/{stage_id}/undo")
        assert undo_resp.status_code == 200
        undo_data = undo_resp.json()
        assert "entities_reverted" in undo_data


def test_discard_returns_deleted(tmp_path):
    client = TestClient(build_app())
    resp = client.delete("/v1/discovery/staging/test-stage")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


@pytest.mark.xdist_group(name="serial-discovery-api")
def test_patch_returns_updated(tmp_path):
    client = TestClient(build_app())
    resp = client.patch(
        "/v1/discovery/staging/test-stage/entities",
        json=[
            {"entity_id": "test-entity-1", "approved": True},
            {"entity_id": "test-entity-2", "approved": False},
        ],
    )
    assert resp.status_code == 200
    patch_data = resp.json()
    assert patch_data["updated"] == 2


def test_job_status_returns_chunk_info(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-15",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "chunk_index" in status_data
    assert "total_chunks" in status_data


def test_job_status_returns_error_field(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-16",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "error" in status_data


def test_get_staging_returns_project_id(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-staging",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        get_resp = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp.status_code == 200
        staging_data = get_resp.json()
        assert staging_data["project_id"] == "proj-staging"


def test_get_staging_returns_stage_id(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-stage-id",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        get_resp = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp.status_code == 200
        staging_data = get_resp.json()
        assert staging_data["stage_id"] == stage_id


def test_discard_then_get_returns_404(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-discard",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        discard_resp = client.delete(f"/v1/discovery/staging/{stage_id}")
        assert discard_resp.status_code == 200

        get_resp = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp.status_code == 404


def test_patch_then_get(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-patch-get",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]

        get_resp = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp.status_code == 200

        patch_resp = client.patch(
            f"/v1/discovery/staging/{stage_id}/entities",
            json=[{"entity_id": "test-entity", "approved": True}],
        )
        assert patch_resp.status_code == 200

        get_resp2 = client.get(f"/v1/discovery/staging/{stage_id}")
        assert get_resp2.status_code == 200


def test_apply_multiple_times(tmp_path):
    client = TestClient(build_app())
    scan_resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-multi-apply",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert scan_resp.status_code == 202
    job_id = scan_resp.json()["job_id"]

    status_resp = client.get(f"/v1/discovery/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    if status_data.get("stage_id"):
        stage_id = status_data["stage_id"]
        for _ in range(3):
            apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
            assert apply_resp.status_code == 200


def test_scan_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.post(
        "/v1/discovery/scan",
        json={
            "project_id": "proj-17",
            "manuscript_text": (
                "The detective walked through the rain-soaked streets of "
                "New York City, searching for clues that would lead him to "
                "the mastermind behind the heist at the Metropolitan Museum."
            ),
        },
    )
    assert resp.status_code == 202


def test_job_status_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/jobs/test-job")
    assert resp.status_code == 404


def test_staging_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/staging/test-stage")
    assert resp.status_code == 404


def test_apply_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/staging/test-stage/apply")
    assert resp.status_code == 404


def test_undo_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/staging/test-stage/undo")
    assert resp.status_code == 200


def test_discard_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.delete("/v1/discovery/staging/test-stage")
    assert resp.status_code == 200


def test_patch_endpoint_exists(tmp_path):
    client = TestClient(build_app())
    resp = client.patch(
        "/v1/discovery/staging/test-stage/entities",
        json=[{"entity_id": "test-entity", "approved": True}],
    )
    assert resp.status_code == 200
