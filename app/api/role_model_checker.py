from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Response

from ..schemas.inspect import (
    RoleModelCheckAttemptHistoryResponse,
    RoleModelCheckLineageResponse,
    RoleModelCheckStepsResponse,
)
from ..schemas.role_model_checker import (
    RoleModelCheckRetryRequest,
    RoleModelCheckStartRequest,
    RoleModelCheckStatusResponse,
)
from ..services.role_model_check_manager import RoleModelCheckManager
from ..services.role_model_checker import RoleModelCheckerService
from ..services.protocol import IdempotencyConflictError, RetryNotAllowedError


def build_role_model_checker_router(manager: RoleModelCheckManager, service: RoleModelCheckerService) -> APIRouter:
    router = APIRouter(prefix='/v1/role-model-checker', tags=['role-model-checker'])

    def _accept_run(
        request: RoleModelCheckStartRequest,
        response: Response,
        idempotency_key: str | None,
    ) -> RoleModelCheckStatusResponse:
        acceptance = manager.accept_run(request, idempotency_key=idempotency_key)
        run = acceptance.status
        response.headers['Location'] = f'/role-model-checker/{run.run_id}/status'
        if not acceptance.created_new and str(run.status) in {'COMPLETED', 'FAILED'}:
            response.status_code = 200
        return run

    @router.post('/run', response_model=RoleModelCheckStatusResponse, status_code=202)
    def run_check(
        request: RoleModelCheckStartRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
    ) -> RoleModelCheckStatusResponse:
        try:
            return _accept_run(request, response, idempotency_key)
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post('/start', response_model=RoleModelCheckStatusResponse, status_code=202)
    def start_check(
        request: RoleModelCheckStartRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
    ) -> RoleModelCheckStatusResponse:
        try:
            return _accept_run(request, response, idempotency_key)
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get('/{run_id}/status', response_model=RoleModelCheckStatusResponse)
    def get_status(run_id: UUID) -> RoleModelCheckStatusResponse:
        try:
            return manager.get_status(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    @router.get('/{run_id}/steps', response_model=RoleModelCheckStepsResponse)
    def get_steps(
        run_id: UUID,
        attempt: int | None = Query(default=None, ge=1),
        limit: int | None = Query(default=None, ge=1),
        offset: int = Query(default=0, ge=0),
    ) -> RoleModelCheckStepsResponse:
        try:
            return manager.get_steps_projection(run_id, attempt_number=attempt, limit=limit, offset=offset)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    @router.get('/{run_id}/lineage', response_model=RoleModelCheckLineageResponse)
    def get_lineage(
        run_id: UUID,
        attempt: int | None = Query(default=None, ge=1),
        limit: int | None = Query(default=None, ge=1),
        offset: int = Query(default=0, ge=0),
    ) -> RoleModelCheckLineageResponse:
        try:
            return manager.get_lineage_projection(run_id, attempt_number=attempt, limit=limit, offset=offset)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    @router.get('/{run_id}/attempts', response_model=RoleModelCheckAttemptHistoryResponse)
    def get_attempts(run_id: UUID) -> RoleModelCheckAttemptHistoryResponse:
        try:
            return manager.get_attempt_history_projection(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    @router.post('/{run_id}/retry', response_model=RoleModelCheckStatusResponse, status_code=202)
    def retry_run(run_id: UUID, request: RoleModelCheckRetryRequest, response: Response) -> RoleModelCheckStatusResponse:
        try:
            run = manager.retry_run(run_id, retry_reason=request.retry_reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc
        except RetryNotAllowedError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        response.headers['Location'] = f'/role-model-checker/{run.run_id}/status'
        return run

    return router