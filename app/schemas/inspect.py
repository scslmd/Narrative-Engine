from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from .base import StrictModel


class StepRecordView(StrictModel):
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
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    finish_reason: str | None = None
    error_code: str | None = None
    error_category: str | None = None
    executor_id: str | None = None
    lease_owner: str | None = None


class ArtifactLineageView(StrictModel):
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
    validation_state: str
    produced_at: str
    registered_at: str | None = None
    supersedes_artifact_lineage_id: int | None = None
    source_artifact_refs: list[str] = Field(default_factory=list)
    source_content_hashes: list[str] = Field(default_factory=list)
    output_of_step_record_id: int


class JobStepsResponse(StrictModel):
    job_id: UUID
    items: list[StepRecordView] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "step_index_asc"})


class JobLineageResponse(StrictModel):
    job_id: UUID
    items: list[ArtifactLineageView] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "artifact_lineage_id_asc"})


class RoleModelCheckStepsResponse(StrictModel):
    run_id: UUID
    items: list[StepRecordView] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "step_index_asc"})


class RoleModelCheckLineageResponse(StrictModel):
    run_id: UUID
    items: list[ArtifactLineageView] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "artifact_lineage_id_asc"})


class AttemptHistoryItem(StrictModel):
    attempt_number: int
    status: str
    executor_name: str | None = None
    executor_instance_id: str | None = None
    queue_delay_ms: int | None = None
    lease_owner: str | None = None
    lease_expires_at: str | None = None
    claimed_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_heartbeat_at: str | None = None
    finish_reason: str | None = None
    failure_stage: str | None = None
    retryable: bool | None = None
    retry_reason: str | None = None
    error_code: str | None = None
    error_category: str | None = None


class JobAttemptHistoryResponse(StrictModel):
    job_id: UUID
    items: list[AttemptHistoryItem] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "attempt_number_asc"})


class RoleModelCheckAttemptHistoryResponse(StrictModel):
    run_id: UUID
    items: list[AttemptHistoryItem] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=lambda: {"ordered_by": "attempt_number_asc"})
