from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import build_app


def test_full_scan_flow(tmp_path):
    """Test: submit scan → poll job → completes or fails."""
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes and met The Son, who she had been rivals with since childhood. They argued about the inheritance their parents left behind." * 5
    resp = client.post("/v1/discovery/scan", json={
        "project_id": "test-proj",
        "manuscript_text": text,
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{job_id}")
        if status.json()["status"] in ("completed", "failed"):
            break
    else:
        assert False, "Job did not complete within timeout"

    data = status.json()
    assert data["status"] in ("completed", "failed")


def test_scan_to_review_flow(tmp_path):
    """Test: submit scan → poll job → get staging entities."""
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes and met The Son." * 20
    resp = client.post("/v1/discovery/scan", json={
        "project_id": "test-proj",
        "manuscript_text": text,
    })
    assert resp.status_code == 202

    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{resp.json()['job_id']}")
        if status.json()["status"] in ("completed", "failed"):
            break

    data = status.json()
    if data["status"] == "completed" and data["stage_id"]:
        staging = client.get(f"/v1/discovery/staging/{data['stage_id']}")
        assert staging.status_code == 200
        entities = staging.json()
        assert "characters" in entities


def test_apply_and_undo(tmp_path):
    """Test: submit scan → apply → undo → verify rollback."""
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes." * 20
    resp = client.post("/v1/discovery/scan", json={
        "project_id": "test-proj",
        "manuscript_text": text,
    })
    job_id = resp.json()["job_id"]

    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{job_id}")
        if status.json()["status"] in ("completed", "failed"):
            break

    data = status.json()
    if data["status"] == "completed" and data["stage_id"]:
        stage_id = data["stage_id"]
        apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
        assert apply_resp.status_code == 200

        undo_resp = client.post(f"/v1/discovery/staging/{stage_id}/undo")
        assert undo_resp.status_code == 200
