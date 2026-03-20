from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from uuid import UUID

from ..inference import InferenceBackend, StubInferenceBackend
from ..schemas.inference import InferenceRequest, InferenceMessage
from ..schemas.role_model_checker import RoleCheckResult, RoleModelCheckStartRequest
from ..settings import settings
from ..workflow_preferences import CRITIC_PROFILE_DEFINITIONS, WORKFLOW_ORDER, build_override_warning
from .model_registry import ModelRegistry


class RoleModelCheckerService:
    def __init__(
        self,
        models_root: Path,
        reports_root: Path | None = None,
        inferencer: InferenceBackend | None = None,
        model_registry: ModelRegistry | None = None,
    ) -> None:
        self.inferencer = inferencer or StubInferenceBackend()
        self.registry = model_registry or ModelRegistry(models_root, inferencer=self.inferencer)
        self.reports_root = reports_root or settings.role_model_reports_dir

    def run_checks(self, request: RoleModelCheckStartRequest) -> list[RoleCheckResult]:
        catalog = self.registry.build_catalog()
        roles = request.roles or list(WORKFLOW_ORDER)
        results: list[RoleCheckResult] = []
        for role in roles:
            start = perf_counter()
            selected = request.model_selection.get(role)
            recommended = catalog.recommended_selection.get(role)
            warnings: list[str] = []
            if selected and selected != recommended:
                warnings.append(build_override_warning(role, selected, recommended))
            elif selected is None and recommended is None:
                warnings.append('No discovered model matched this role.')
            profile = CRITIC_PROFILE_DEFINITIONS[request.critic_profile] if role == 'critic' else None
            inference_request = InferenceRequest(
                model=selected or recommended or self.inferencer.descriptor.default_model,
                messages=[
                    InferenceMessage(role="system", content="You are a narrative runtime validation assistant."),
                    InferenceMessage(role="user", content=f"Validate the configured model choice for the {role} role."),
                ],
                metadata={"role": role, "mode": "role_model_check_stub"},
            )
            preview = (
                f"Checker stub executed for {role} via {catalog.inference_provider.display_name} "
                f"({catalog.inference_provider.transport})."
            )
            if profile is not None:
                preview += f" Critic profile: {profile['label']}."
            results.append(
                RoleCheckResult(
                    role=role,
                    passed=True,
                    duration_seconds=round(perf_counter() - start, 3),
                    warnings=warnings,
                    findings=[],
                    preview=preview,
                    metadata={
                        'selected_model': selected or recommended,
                        'recommended_model': recommended,
                        'critic_profile': request.critic_profile if role == 'critic' else None,
                        'inference_backend': catalog.inference_provider.backend,
                        'inference_transport': catalog.inference_provider.transport,
                        'inference_base_url': catalog.inference_provider.base_url,
                        'inference_request': inference_request.model_dump(mode='json'),
                    },
                )
            )
        return results

    def save_report(self, run_id: UUID, request: RoleModelCheckStartRequest, results: list[RoleCheckResult]) -> Path:
        self.reports_root.mkdir(parents=True, exist_ok=True)
        report_path = self.reports_root / f'{run_id}.json'
        payload = {
            'run_id': str(run_id),
            'roles': request.roles or list(WORKFLOW_ORDER),
            'model_selection': dict(request.model_selection),
            'critic_profile': request.critic_profile,
            'save_report': request.save_report,
            'results': [result.model_dump(mode='json') for result in results],
            'catalog': self.registry.build_catalog().model_dump(mode='json'),
            'inference_provider': self.inferencer.descriptor.model_dump(mode='json'),
        }
        report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding='utf-8')
        return report_path
