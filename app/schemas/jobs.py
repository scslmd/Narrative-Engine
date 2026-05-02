from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .base import StrictModel
from .enums import JobPhase, JobStatus

from ..constants import MAX_PAYLOAD_SIZE


class JobCreateRequest(StrictModel):
    phase: JobPhase
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)  # REL-02

    @field_validator('payload')
    @classmethod
    def validate_payload_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that payload doesn't exceed maximum size."""
        serialized = json.dumps(v)
        if len(serialized.encode('utf-8')) > MAX_PAYLOAD_SIZE:
            raise ValueError(
                f"Payload exceeds maximum allowed size of {MAX_PAYLOAD_SIZE / (1024 * 1024):.0f} MB"
            )
        return v

    @model_validator(mode='after')
    def validate_phase_specific_payload(self) -> 'JobCreateRequest':
        """Validate phase-specific payload requirements (REL-08).
        
        For phases P-100, P-200, P-300, and P-400, the payload must contain
        a non-empty string 'project_id'. Optional runtime override keys are
        type-checked when present.
        """
        # JobPhase is a str, Enum so self.phase is already a string
        if self.phase in ('P-100', 'P-200', 'P-300', 'P-400'):
            project_id = self.payload.get('project_id')
            if project_id is None:
                raise ValueError(
                    f"Payload must contain 'project_id' for phase {self.phase}"
                )
            if not isinstance(project_id, str):
                raise ValueError(
                    f"Payload 'project_id' must be a string for phase {self.phase}"
                )
            if not project_id.strip():
                raise ValueError(
                    f"Payload 'project_id' must be a non-empty string for phase {self.phase}"
                )
            
            # Validate optional runtime override keys when present
            model_id = self.payload.get('model_id')
            if model_id is not None and not isinstance(model_id, str):
                raise ValueError("Payload 'model_id' must be a string")
            
            model = self.payload.get('model')
            if model is not None and not isinstance(model, str):
                raise ValueError("Payload 'model' must be a string")
            
            premise_text = self.payload.get('premise_text')
            if premise_text is not None and not isinstance(premise_text, str):
                raise ValueError("Payload 'premise_text' must be a string")
            
            temperature = self.payload.get('temperature')
            if temperature is not None and not isinstance(temperature, (int, float)):
                raise ValueError("Payload 'temperature' must be a number")
            
            max_tokens = self.payload.get('max_tokens')
            if max_tokens is not None:
                if not isinstance(max_tokens, int):
                    raise ValueError("Payload 'max_tokens' must be an integer")
                if max_tokens < 1:
                    raise ValueError("Payload 'max_tokens' must be >= 1")
        elif self.phase in ("G-200", "G-300", "G-350", "G-400"):
            generation_id = self.payload.get("generation_id")
            if generation_id is None:
                raise ValueError(
                    f"Payload must contain 'generation_id' for phase {self.phase}"
                )
            if not isinstance(generation_id, str):
                raise ValueError(
                    f"Payload 'generation_id' must be a string for phase {self.phase}"
                )
            if not generation_id.strip():
                raise ValueError(
                    f"Payload 'generation_id' must be a non-empty string for phase {self.phase}"
                )

            if self.phase == "G-300":
                chapter_id = self.payload.get("chapter_id")
                chapter_ids = self.payload.get("chapter_ids")
                if chapter_id is None and chapter_ids is None:
                    raise ValueError(
                        "Payload must contain 'chapter_id' or 'chapter_ids' for phase G-300"
                    )
                if chapter_id is not None:
                    if not isinstance(chapter_id, str) or not chapter_id.strip():
                        raise ValueError("Payload 'chapter_id' must be a non-empty string")
                if chapter_ids is not None:
                    if not isinstance(chapter_ids, list) or not chapter_ids:
                        raise ValueError("Payload 'chapter_ids' must be a non-empty list")
                    if any(not isinstance(chapter, str) or not chapter.strip() for chapter in chapter_ids):
                        raise ValueError("Payload 'chapter_ids' must contain only non-empty strings")

            if self.phase == "G-350":
                artifact_refs = self.payload.get("artifact_refs")
                if artifact_refs is None:
                    raise ValueError("Payload must contain 'artifact_refs' for phase G-350")
                if not isinstance(artifact_refs, list):
                    raise ValueError("Payload 'artifact_refs' must be a list")

            if self.phase == "G-400":
                chapter_artifact_ids = self.payload.get("chapter_artifact_ids")
                if chapter_artifact_ids is None:
                    raise ValueError("Payload must contain 'chapter_artifact_ids' for phase G-400")
                if not isinstance(chapter_artifact_ids, list):
                    raise ValueError("Payload 'chapter_artifact_ids' must be a list")
        return self


class JobRetryRequest(StrictModel):
    retry_reason: str = "operator_retry"


class JobStatusResponse(StrictModel):
    id: UUID
    phase: JobPhase
    status: JobStatus
    attempt_number: int = 1
    created_at: datetime
    updated_at: datetime
    current_phase: str | None = None
    current_step: str | None = None
    detail: str | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    heartbeat_at: datetime | None = None
    error: str | None = None


class JobLogEntry(StrictModel):
    timestamp: datetime
    level: Literal['INFO', 'WARNING', 'ERROR']
    message: str


class JobLogsResponse(StrictModel):
    id: UUID
    entries: list[JobLogEntry] = Field(default_factory=list)


class JobAttempt(StrictModel):
    """Pydantic model for a single job attempt record."""
    logical_run_id: str
    attempt_number: int
    status: str
    executor_name: str | None = None
    executor_instance_id: str | None = None
    queue_delay_ms: float | None = None
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    claimed_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    finish_reason: str | None = None
    failure_stage: str | None = None
    retryable: bool | None = None
    retry_reason: str | None = None
    error_code: str | None = None
    error_category: str | None = None
    duration_seconds: float | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    parent_attempt_number: int | None = None


class JobEvent(StrictModel):
    """Pydantic model for a job event record."""
    event_type: str
    from_state: str | None = None
    to_state: str | None = None
    occurred_at: datetime
    attempt_number: int
    payload: dict[str, Any] = Field(default_factory=dict)


class JobAttemptHistoryResponse(StrictModel):
    """Response for enriched attempt history with metadata."""
    id: UUID
    phase: JobPhase
    status: JobStatus
    attempts: list[JobAttempt] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class JobAttemptSummaryStats(StrictModel):
    """Summary statistics for job attempt history."""
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    total_duration_seconds: float
    last_attempt_number: int
    last_attempt_status: str


class StepRecord(StrictModel):
    """Pydantic model for a step record."""
    step_record_id: int
    logical_run_id: str
    run_id: str
    run_kind: str
    attempt_number: int
    step_name: str
    step_index: int
    state: str
    project_id: str | None = None
    model_id: str | None = None
    critic_profile: str | None = None
    backend_name: str | None = None
    backend_version: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    prompt_hash: str | None = None
    input_artifact_refs: list[str] = Field(default_factory=list)
    output_artifact_refs: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    error_code: str | None = None
    error_category: str | None = None
    executor_id: str | None = None
    lease_owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArtifactLineageRecord(StrictModel):
    """Pydantic model for an artifact lineage record."""
    artifact_lineage_id: int
    logical_run_id: str
    run_id: str
    run_kind: str
    attempt_number: int
    step_name: str
    project_id: str | None = None
    artifact_role: str
    artifact_kind: str
    path: str
    content_hash: str | None = None
    status: str
    validation_state: str | None = None
    produced_at: datetime | None = None
    registered_at: datetime | None = None
    supersedes_artifact_lineage_id: int | None = None
    source_artifact_refs: list[str] = Field(default_factory=list)
    source_content_hashes: list[str] = Field(default_factory=list)
    output_of_step_record_id: int | None = None


class StepRecordsResponse(StrictModel):
    """Response for step record listing."""
    records: list[StepRecord] = Field(default_factory=list)


class ArtifactLineageResponse(StrictModel):
    """Response for artifact lineage listing."""
    records: list[ArtifactLineageRecord] = Field(default_factory=list)
