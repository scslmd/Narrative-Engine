from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from ..schemas.jobs import JobCreateRequest, JobLogsResponse, JobStatusResponse
from ..services.job_manager import JobManager


def build_jobs_router(job_manager: JobManager) -> APIRouter:
    router = APIRouter(prefix='/jobs', tags=['jobs'])

    def _run_job_stub(job_id: UUID, phase: str) -> None:
        try:
            job_manager.update_job(
                job_id,
                status='PROCESSING',
                current_phase=phase,
                current_step='recovered_stub',
                detail='Recovered background execution stub started.',
            )
            job_manager.log(job_id, 'INFO', f'Recovered job created for phase {phase}.')
            job_manager.update_job(
                job_id,
                status='COMPLETED',
                detail='Recovered stub completed in background.',
                progress_current=1,
                progress_total=1,
            )
        except Exception as exc:
            job_manager.update_job(job_id, status='FAILED', error=str(exc), detail='Recovered background execution stub failed.')

    @router.post('/create', response_model=JobStatusResponse, status_code=202)
    def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks, response: Response) -> JobStatusResponse:
        phase = str(request.phase)
        job = job_manager.create_job(request)
        background_tasks.add_task(_run_job_stub, job.id, phase)
        response.headers['Location'] = f'/jobs/{job.id}/status'
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

    return router
