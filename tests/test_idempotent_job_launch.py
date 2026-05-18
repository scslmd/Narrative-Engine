from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


def test_job_create_deduplicates_with_idempotency_key(client: TestClient):
    """Two identical job creates with same idempotency key return same job."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }
    headers = {"Idempotency-Key": "idem-test-1"}

    r1 = client.post("/v1/jobs/create", json=payload, headers=headers)
    assert r1.status_code == 202, f"First create failed: {r1.status_code}"
    job_id_1 = r1.json()["id"]

    r2 = client.post("/v1/jobs/create", json=payload, headers=headers)
    assert r2.status_code in (200, 202), f"Second create failed: {r2.status_code}"
    job_id_2 = r2.json()["id"]

    assert job_id_1 == job_id_2, "Duplicate job created despite idempotency key"


def test_job_create_allows_different_idempotency_keys(client: TestClient):
    """Two creates with different idempotency keys create separate jobs."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }

    r1 = client.post("/v1/jobs/create", json=payload, headers={"Idempotency-Key": "key-a"})
    assert r1.status_code == 202
    job_id_1 = r1.json()["id"]

    r2 = client.post("/v1/jobs/create", json=payload, headers={"Idempotency-Key": "key-b"})
    assert r2.status_code == 202
    job_id_2 = r2.json()["id"]

    assert job_id_1 != job_id_2, "Different idempotency keys should create different jobs"


def test_job_create_conflicts_on_different_payload(client: TestClient):
    """Same idempotency key + scope but different payload hash returns 409."""
    headers = {"Idempotency-Key": "idem-conflict"}

    r1 = client.post("/v1/jobs/create", json={
        "phase": "P-100",
        "payload": {"project_id": "test-proj", "extra": "value-a"},
    }, headers=headers)
    assert r1.status_code == 202

    r2 = client.post("/v1/jobs/create", json={
        "phase": "P-100",
        "payload": {"project_id": "test-proj", "extra": "value-b"},
    }, headers=headers)
    assert r2.status_code == 409, "Different payloads with same key+scope should conflict"


def test_job_create_without_key_always_creates_new(client: TestClient):
    """Requests without idempotency key always create new jobs."""
    payload = {
        "phase": "P-100",
        "payload": {"project_id": "test-proj"},
    }

    r1 = client.post("/v1/jobs/create", json=payload)
    assert r1.status_code == 202
    job_id_1 = r1.json()["id"]

    r2 = client.post("/v1/jobs/create", json=payload)
    assert r2.status_code == 202
    job_id_2 = r2.json()["id"]

    assert job_id_1 != job_id_2
