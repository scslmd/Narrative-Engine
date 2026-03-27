from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from .base import StrictModel
from .enums import JobPhase, JobStatus


# Maximum payload size: 5 MB
MAX_PAYLOAD_SIZE = 5 * 1024 * 1024


class JobCreateRequest(StrictModel):
    phase: JobPhase
    payload: dict[str, Any] = Field(default_factory=dict)

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
