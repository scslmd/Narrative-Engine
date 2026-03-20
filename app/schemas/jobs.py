from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from .base import StrictModel
from .enums import JobPhase, JobStatus


class JobCreateRequest(StrictModel):
    phase: JobPhase
    payload: dict[str, Any] = Field(default_factory=dict)


class JobStatusResponse(StrictModel):
    id: UUID
    phase: JobPhase
    status: JobStatus
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
