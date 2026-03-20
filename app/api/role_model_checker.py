from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..schemas.role_model_checker import RoleModelCheckStartRequest, RoleModelCheckStatusResponse
from ..services.role_model_check_manager import RoleModelCheckManager
from ..services.role_model_checker import RoleModelCheckerService


def build_role_model_checker_router(manager: RoleModelCheckManager, service: RoleModelCheckerService) -> APIRouter:
    router = APIRouter(prefix='/role-model-checker', tags=['role-model-checker'])

    @router.post('/run', response_model=RoleModelCheckStatusResponse)
    def run_check(request: RoleModelCheckStartRequest) -> RoleModelCheckStatusResponse:
        run = manager.create_run()
        manager.update_run(run.run_id, status='RUNNING', detail='Recovered checker run started.')
        for role_result in service.run_checks(request):
            manager.update_run(run.run_id, current_role=role_result.role, detail=f'Testing {role_result.role}.')
            manager.add_result(run.run_id, role_result)
        final_status = manager.update_run(run.run_id, status='COMPLETED', detail='Recovered checker run finished.')
        if request.save_report:
            report_path = service.save_report(run.run_id, request, final_status.results)
            final_status = manager.update_run(run.run_id, report_path=str(report_path), detail='Recovered checker run finished and report saved.')
        return final_status

    @router.post('/start', response_model=RoleModelCheckStatusResponse)
    def start_check(request: RoleModelCheckStartRequest) -> RoleModelCheckStatusResponse:
        return run_check(request)

    @router.get('/{run_id}/status', response_model=RoleModelCheckStatusResponse)
    def get_status(run_id: UUID) -> RoleModelCheckStatusResponse:
        try:
            return manager.get_status(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail='Role-model check run not found.') from exc

    return router