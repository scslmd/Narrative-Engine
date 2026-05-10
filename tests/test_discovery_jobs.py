from __future__ import annotations

import uuid
from app.services.discovery_jobs import CascadeJobManager


def test_create_job():
    manager = CascadeJobManager()
    job = manager.create_job(project_id="proj-1")
    assert job.job_id is not None
    assert len(job.job_id) == 36
    assert job.project_id == "proj-1"
    assert job.status == "pending"
    assert job.chunk_index is None
    assert job.total_chunks is None
    assert job.stage_id is None
    assert job.error is None


def test_update_progress():
    manager = CascadeJobManager()
    job = manager.create_job(project_id="proj-1")
    manager.update_progress(job.job_id, "chunking", chunk_index=0, total_chunks=5)
    fetched = manager.get_job(job.job_id)
    assert fetched is not None
    assert fetched.status == "chunking"
    assert fetched.chunk_index == 0
    assert fetched.total_chunks == 5


def test_complete_job():
    manager = CascadeJobManager()
    job = manager.create_job(project_id="proj-1")
    manager.complete(job.job_id, stage_id="stage-abc")
    fetched = manager.get_job(job.job_id)
    assert fetched is not None
    assert fetched.status == "completed"
    assert fetched.stage_id == "stage-abc"


def test_fail_job():
    manager = CascadeJobManager()
    job = manager.create_job(project_id="proj-1")
    manager.fail(job.job_id, error="timeout")
    fetched = manager.get_job(job.job_id)
    assert fetched is not None
    assert fetched.status == "failed"
    assert fetched.error == "timeout"


def test_job_not_found():
    manager = CascadeJobManager()
    result = manager.get_job(str(uuid.uuid4()))
    assert result is None
