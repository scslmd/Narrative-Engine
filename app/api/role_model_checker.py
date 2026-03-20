from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from ..schemas.role_model_checker import RoleModelCheckStartRequest, RoleModelCheckStatusResponse
from ..services.role_model_check_manager import RoleModelCheckManager
from ..services.role_model_checker import RoleModelCheckerService


def build_role_model_checker_router(manager: RoleModelCheckManager, service: RoleModelCheckerService) -> APIRouter:
    router = APIRouter(prefix='/role-model-checker', tags=['role-model-checker'])

    def _run_checker_stub(run_id: UUID, request: RoleModelCheckStartRequest) -> None:
        try:
            manager.update_run(run_id, status='RUNNING', detail='Recovered checker run started.')
            for role_result in service.run_checks(request):
                manager.update_run(run_id, current_role=role_result.role, detail=f'Testing {role_result.role}.')
                manager.add_result(run_id, role_result)
            final_status = manager.update_run(run_id, status='COMPLETED', detail='Recovered checker run finished.')
            if request.save_report:
                report_path = service.save_report(run_id, request, final_status.results)
                manager.update_run(run_id, report_path=str(report_path), detail='Recovered checker run finished and report saved.')
        except Exception as exc:
            manager.update_run(run_id, status='FAILED', detail='Recovered checker run failed.', report_path=None)
            raise exc

    def _accept_run(request: RoleModelCheckStartRequest, background_tasks: BackgroundTasks, response: Response) -> RoleModelCheckStatusResponse:
        run = manager.create_run(request)
        background_tasks.add_task(_run_checker_stub, run.run_id, request)
        response.headers['Location'] = f'/role-model-checker/{run.run_id}/status'
        return run

    @router.post('/run', response_model=RoleModelCheckStatusResponse, status_code=202)
    def run_check(request: RoleModelCheckStartRequest, background_tasks: BackgroundTasks, response: Response) -> RoleModelCheckStatusResponse:
        return _accept_run(request, background_tasks, response)

    @router.post('/start', response_model=RoleModelCheckStatusResponse, status_code=202)
    def start_check(request: RoleModelCheckStartRequest, background_tasks: BackgroundTasks, response: Response) -> RoleModelCheckStatusResponse:
        return _accept_run(request, background_tasks, response)

    @router.get('/{run_id}/status', response_model=RoleModelCheckStatusResponse)
    def get_status(run_id: UUID) -> RoleModelCheckStatusResponse:
        try:
            return manager.get_status(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    return router
