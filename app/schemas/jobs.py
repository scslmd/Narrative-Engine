from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from .base import StrictModel
from .enums import JobPhase, JobStatus


# Maximum payload size: 5 MB
MAX_PAYLOAD_SIZE = 5 * 1024 * 1024


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
