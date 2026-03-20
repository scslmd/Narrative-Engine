from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response

from ..schemas.jobs import JobCreateRequest, JobLogsResponse, JobRetryRequest, JobStatusResponse
from ..services.job_manager import JobManager
from ..services.protocol import IdempotencyConflictError, RetryNotAllowedError


def build_jobs_router(job_manager: JobManager) -> APIRouter:
    router = APIRouter(prefix='/jobs', tags=['jobs'])

    @router.post('/create', response_model=JobStatusResponse, status_code=202)
    def create_job(
        request: JobCreateRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
    ) -> JobStatusResponse:
        try:
            acceptance = job_manager.accept_job(request, idempotency_key=idempotency_key)
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        job = acceptance.status
        response.headers['Location'] = f'/jobs/{job.id}/status'
        if not acceptance.created_new and str(job.status) in {'COMPLETED', 'FAILED'}:
            response.status_code = 200
        return job

    @router.get('/{job_id}/status', response_model=JobStatusResponse)
    def get_status(job_id: UUID) -> JobStatusResponse:
        try:
            return job_manager.get_status(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Job not found.') from exc

    @router.get('/{job_id}/logs', response_model=JobLogsResponse)
    def get_logs(job_id: UUID) -> JobLogsResponse:
        try:
            return job_manager.get_logs(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Job not found.') from exc

    @router.post('/{job_id}/retry', response_model=JobStatusResponse, status_code=202)
    def retry_job(job_id: UUID, request: JobRetryRequest, response: Response) -> JobStatusResponse:
        try:
            job = job_manager.retry_job(job_id, retry_reason=request.retry_reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Job not found.') from exc
        except RetryNotAllowedError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        response.headers['Location'] = f'/jobs/{job.id}/status'
        return job

    return router
