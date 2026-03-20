from __future__ import annotations

from dataclasses import dataclass

from ..schemas.jobs import JobStatusResponse
from ..schemas.role_model_checker import RoleModelCheckStatusResponse


class IdempotencyConflictError(ValueError):
    pass


class RetryNotAllowedError(ValueError):
    pass


@dataclass(frozen=True)
class JobAcceptance:
    status: JobStatusResponse
    created_new: bool


@dataclass(frozen=True)
class CheckerRunAcceptance:
    status: RoleModelCheckStatusResponse
    created_new: bool
