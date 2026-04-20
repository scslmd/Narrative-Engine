from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.schemas.jobs import (
    ArtifactLineageRecord,
    ArtifactLineageResponse,
    JobAttempt,
    JobAttemptHistoryResponse,
    JobAttemptSummaryStats,
    JobEvent,
    JobLogsResponse,
    JobLogEntry,
    StepRecord,
    StepRecordsResponse,
)


# -- JobAttempt --

def test_job_attempt_minimal():
    """JobAttempt with only required fields."""
    attempt = JobAttempt(
        logical_run_id="run-123",
        attempt_number=1,
        status="COMPLETED",
    )
    assert attempt.logical_run_id == "run-123"
    assert attempt.attempt_number == 1
    assert attempt.status == "COMPLETED"
    assert attempt.executor_name is None
    assert attempt.duration_seconds is None
    assert attempt.events == []


def test_job_attempt_full():
    """JobAttempt with all optional fields populated."""
    now = datetime.now(timezone.utc)
    attempt = JobAttempt(
        logical_run_id="run-456",
        attempt_number=2,
        status="FAILED",
        executor_name="job-worker-local",
        executor_instance_id="worker-1",
        queue_delay_ms=150.5,
        lease_owner="worker-1",
        lease_expires_at=now,
        claimed_at=now,
        started_at=now,
        finished_at=now,
        last_heartbeat_at=now,
        finish_reason="completed",
        failure_stage=None,
        retryable=False,
        retry_reason=None,
        error_code=None,
        error_category=None,
        duration_seconds=3.14,
        events=[{"event_type": "job_started"}],
        parent_attempt_number=1,
    )
    assert attempt.executor_name == "job-worker-local"
    assert attempt.duration_seconds == 3.14
    assert attempt.events == [{"event_type": "job_started"}]
    assert attempt.parent_attempt_number == 1


def test_job_attempt_none_defaults():
    """All optional fields default to None or empty."""
    attempt = JobAttempt(
        logical_run_id="r",
        attempt_number=1,
        status="PENDING",
    )
    assert attempt.executor_name is None
    assert attempt.queue_delay_ms is None
    assert attempt.lease_owner is None
    assert attempt.started_at is None
    assert attempt.finished_at is None
    assert attempt.finish_reason is None
    assert attempt.error_code is None
    assert attempt.error_category is None
    assert attempt.duration_seconds is None
    assert attempt.parent_attempt_number is None


# -- JobEvent --

def test_job_event_basic():
    """JobEvent with required fields."""
    now = datetime.now(timezone.utc)
    event = JobEvent(
        event_type="job_started",
        occurred_at=now,
        attempt_number=1,
    )
    assert event.event_type == "job_started"
    assert event.from_state is None
    assert event.to_state is None
    assert event.attempt_number == 1
    assert event.payload == {}


def test_job_event_full():
    """JobEvent with all fields."""
    now = datetime.now(timezone.utc)
    event = JobEvent(
        event_type="state_transition",
        from_state="PENDING",
        to_state="PROCESSING",
        occurred_at=now,
        attempt_number=2,
        payload={"detail": "claiming lease"},
    )
    assert event.from_state == "PENDING"
    assert event.to_state == "PROCESSING"
    assert event.payload == {"detail": "claiming lease"}


# -- JobAttemptHistoryResponse --

def test_job_attempt_history_empty():
    """JobAttemptHistoryResponse with no attempts."""
    response = JobAttemptHistoryResponse(
        id=uuid4(),
        phase="P-100",
        status="PENDING",
    )
    assert response.id is not None
    assert response.attempts == []
    assert response.summary == {}


def test_job_attempt_history_with_data():
    """JobAttemptHistoryResponse with populated data."""
    now = datetime.now(timezone.utc)
    attempt = JobAttempt(
        logical_run_id="run-1",
        attempt_number=1,
        status="COMPLETED",
        duration_seconds=10.5,
    )
    response = JobAttemptHistoryResponse(
        id=uuid4(),
        phase="P-200",
        status="COMPLETED",
        attempts=[attempt],
        summary={"total": 1},
    )
    assert len(response.attempts) == 1
    assert response.attempts[0].duration_seconds == 10.5
    assert response.summary == {"total": 1}


# -- JobAttemptSummaryStats --

def test_job_attempt_summary_stats_zero():
    """Summary stats with zero attempts."""
    stats = JobAttemptSummaryStats(
        total_attempts=0,
        successful_attempts=0,
        failed_attempts=0,
        total_duration_seconds=0.0,
        last_attempt_number=0,
        last_attempt_status="PENDING",
    )
    assert stats.total_attempts == 0
    assert stats.successful_attempts == 0
    assert stats.failed_attempts == 0


def test_job_attempt_summary_stats_mixed():
    """Summary stats with mixed results."""
    stats = JobAttemptSummaryStats(
        total_attempts=5,
        successful_attempts=3,
        failed_attempts=2,
        total_duration_seconds=120.5,
        last_attempt_number=5,
        last_attempt_status="COMPLETED",
    )
    assert stats.total_attempts == 5
    assert stats.successful_attempts == 3
    assert stats.failed_attempts == 2
    assert stats.total_duration_seconds == 120.5


# -- StepRecord --

def test_step_record_minimal():
    """StepRecord with required fields only."""
    record = StepRecord(
        step_record_id=1,
        logical_run_id="run-1",
        run_id="job-1",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        step_index=0,
        state="COMPLETED",
    )
    assert record.step_record_id == 1
    assert record.step_name == "architect"
    assert record.state == "COMPLETED"
    assert record.model_id is None
    assert record.input_artifact_refs == []
    assert record.output_artifact_refs == []


def test_step_record_telemetry():
    """StepRecord with runtime telemetry fields."""
    now = datetime.now(timezone.utc)
    record = StepRecord(
        step_record_id=2,
        logical_run_id="run-2",
        run_id="job-2",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="sequencer",
        step_index=1,
        state="COMPLETED",
        model_id="llama-3.1-8b",
        backend_name="llama.cpp",
        backend_version="0.2.0",
        input_hash="abc123",
        output_hash="def456",
        prompt_hash="ghi789",
        started_at=now,
        finished_at=now,
        duration_seconds=5.2,
        finish_reason="stop",
        prompt_tokens=1024,
        completion_tokens=512,
        total_tokens=1536,
    )
    assert record.model_id == "llama-3.1-8b"
    assert record.backend_name == "llama.cpp"
    assert record.duration_seconds == 5.2
    assert record.prompt_tokens == 1024
    assert record.total_tokens == 1536


def test_step_record_failure():
    """StepRecord with failure fields."""
    record = StepRecord(
        step_record_id=3,
        logical_run_id="run-3",
        run_id="job-3",
        run_kind="pipeline_job",
        attempt_number=2,
        step_name="drafter",
        step_index=2,
        state="FAILED",
        finish_reason="timeout",
        error_code="TIMEOUT",
        error_category="inference",
        executor_id="job-worker-local",
        lease_owner="worker-2",
    )
    assert record.state == "FAILED"
    assert record.finish_reason == "timeout"
    assert record.error_code == "TIMEOUT"
    assert record.error_category == "inference"


# -- ArtifactLineageRecord --

def test_artifact_lineage_record_minimal():
    """ArtifactLineageRecord with required fields."""
    record = ArtifactLineageRecord(
        artifact_lineage_id=1,
        logical_run_id="run-1",
        run_id="job-1",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        artifact_role="architect_output",
        artifact_kind="markdown",
        path="/data/projects/abc/chapter.md",
        status="CANONICAL",
    )
    assert record.artifact_lineage_id == 1
    assert record.artifact_role == "architect_output"
    assert record.artifact_kind == "markdown"
    assert record.path == "/data/projects/abc/chapter.md"
    assert record.content_hash is None
    assert record.source_artifact_refs == []
    assert record.source_content_hashes == []


def test_artifact_lineage_record_full():
    """ArtifactLineageRecord with all fields."""
    now = datetime.now(timezone.utc)
    record = ArtifactLineageRecord(
        artifact_lineage_id=2,
        logical_run_id="run-2",
        run_id="job-2",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="sequencer",
        artifact_role="sequence",
        artifact_kind="json",
        path="/data/projects/def/sequences.json",
        content_hash="sha256:abc123",
        status="CANONICAL",
        validation_state="PASSED",
        produced_at=now,
        registered_at=now,
        supersedes_artifact_lineage_id=None,
        source_artifact_refs=["manifest", "foundation"],
        source_content_hashes=["sha256:manifest", "sha256:foundation"],
        output_of_step_record_id=1,
    )
    assert record.content_hash == "sha256:abc123"
    assert record.validation_state == "PASSED"
    assert len(record.source_artifact_refs) == 2
    assert record.output_of_step_record_id == 1


def test_artifact_lineage_record_superseded():
    """ArtifactLineageRecord with superseded status."""
    record = ArtifactLineageRecord(
        artifact_lineage_id=3,
        logical_run_id="run-3",
        run_id="job-3",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="drafter",
        artifact_role="chapter_1",
        artifact_kind="markdown",
        path="/data/projects/ghi/chapter.md",
        status="SUPERSEDED",
        supersedes_artifact_lineage_id=2,
    )
    assert record.status == "SUPERSEDED"
    assert record.supersedes_artifact_lineage_id == 2


# -- Response wrappers --

def test_step_records_response_empty():
    """StepRecordsResponse with no records."""
    response = StepRecordsResponse()
    assert response.records == []


def test_step_records_response_with_records():
    """StepRecordsResponse with records."""
    record = StepRecord(
        step_record_id=1,
        logical_run_id="r",
        run_id="j",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        step_index=0,
        state="COMPLETED",
    )
    response = StepRecordsResponse(records=[record])
    assert len(response.records) == 1


def test_artifact_lineage_response_empty():
    """ArtifactLineageResponse with no records."""
    response = ArtifactLineageResponse()
    assert response.records == []


def test_artifact_lineage_response_with_records():
    """ArtifactLineageResponse with records."""
    record = ArtifactLineageRecord(
        artifact_lineage_id=1,
        logical_run_id="r",
        run_id="j",
        run_kind="pipeline_job",
        attempt_number=1,
        step_name="architect",
        artifact_role="architect_output",
        artifact_kind="markdown",
        path="/data/p.md",
        status="CANONICAL",
    )
    response = ArtifactLineageResponse(records=[record])
    assert len(response.records) == 1


# -- JobLogEntry --

def test_job_log_entry_info():
    """JobLogEntry with INFO level."""
    now = datetime.now(timezone.utc)
    entry = JobLogEntry(
        timestamp=now,
        level="INFO",
        message="Job created",
    )
    assert entry.level == "INFO"
    assert entry.message == "Job created"


def test_job_log_entry_error():
    """JobLogEntry with ERROR level."""
    now = datetime.now(timezone.utc)
    entry = JobLogEntry(
        timestamp=now,
        level="ERROR",
        message="Connection timeout",
    )
    assert entry.level == "ERROR"


def test_job_logs_response_empty():
    """JobLogsResponse with no entries."""
    response = JobLogsResponse(id=uuid4())
    assert response.entries == []


def test_job_logs_response_with_entries():
    """JobLogsResponse with entries."""
    now = datetime.now(timezone.utc)
    entries = [
        JobLogEntry(timestamp=now, level="INFO", message="Starting"),
        JobLogEntry(timestamp=now, level="ERROR", message="Failed"),
    ]
    response = JobLogsResponse(id=uuid4(), entries=entries)
    assert len(response.entries) == 2
