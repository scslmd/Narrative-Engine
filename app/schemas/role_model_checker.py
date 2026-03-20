from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import StrictModel
from ..workflow_preferences import CriticExperimentProfile, RoleName


class RoleModelCheckStartRequest(StrictModel):
    roles: list[RoleName] = Field(default_factory=list)
    model_selection: dict[RoleName, str] = Field(default_factory=dict)
    critic_profile: CriticExperimentProfile = 'minimal_context'
    save_report: bool = True


class RoleCheckResult(StrictModel):
    role: RoleName
    passed: bool
    duration_seconds: float = 0.0
    findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    preview: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoleModelCheckStatusResponse(StrictModel):
    run_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    current_role: RoleName | None = None
    detail: str | None = None
    heartbeat_at: datetime | None = None
    report_path: str | None = None
    results: list[RoleCheckResult] = Field(default_factory=list)