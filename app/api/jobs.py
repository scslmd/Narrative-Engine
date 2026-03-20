from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..schemas.jobs import JobCreateRequest, JobLogsResponse, JobStatusResponse
from ..services.job_manager import JobManager


def build_jobs_router(job_manager: JobManager) -> APIRouter:
    router = APIRouter(prefix='/jobs', tags=['jobs'])

    @router.post('/create', response_model=JobStatusResponse)
    def create_job(request: JobCreateRequest) -> JobStatusResponse:
        phase = str(request.phase)
        job = job_manager.create_job(request)
        job_manager.update_job(job.id, status='PROCESSING', current_phase=phase, current_step='recovered_stub', detail='Recovered background execution stub started.')
        job_manager.log(job.id, 'INFO', f'Recovered job created for phase {phase}.')
        job_manager.update_job(job.id, status='COMPLETED', detail='Recovered stub completed immediately.', progress_current=1, progress_total=1)
        return job_manager.get_status(job.id)

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

    return router