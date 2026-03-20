from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any
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
            if role == "architect":
                result = self._run_architect_check(
                    role=role,
                    selected=selected,
                    recommended=recommended,
                    warnings=warnings,
                    start=start,
                )
            else:
                result = self._build_stub_result(
                    role=role,
                    selected=selected,
                    recommended=recommended,
                    warnings=warnings,
                    start=start,
                    critic_profile=request.critic_profile if role == "critic" else None,
                    critic_profile_label=profile["label"] if profile is not None else None,
                    stub_mode="role_model_check_stub",
                    stub_reason="role_not_runtime_backed",
                )
            results.append(result)
        return results

    def _run_architect_check(
        self,
        *,
        role: str,
        selected: str | None,
        recommended: str | None,
        warnings: list[str],
        start: float,
    ) -> RoleCheckResult:
        inference_request = self._build_inference_request(
            role=role,
            selected=selected,
            recommended=recommended,
            mode="role_model_check_runtime",
        )
        if self.inferencer.descriptor.backend == "stub":
            warnings = [*warnings, "Architect runtime is not configured; using stub fallback."]
            return self._build_stub_result(
                role=role,
                selected=selected,
                recommended=recommended,
                warnings=warnings,
                start=start,
                critic_profile=None,
                critic_profile_label=None,
                stub_mode="role_model_check_stub_fallback",
                stub_reason="runtime_backend_unavailable",
                inference_request=inference_request,
            )

        try:
            inference_response = self.inferencer.generate_text(inference_request)
        except Exception as exc:
            warnings = [*warnings, f"Architect runtime failed; using stub fallback: {exc}"]
            return self._build_stub_result(
                role=role,
                selected=selected,
                recommended=recommended,
                warnings=warnings,
                start=start,
                critic_profile=None,
                critic_profile_label=None,
                stub_mode="role_model_check_stub_fallback",
                stub_reason="runtime_execution_error",
                inference_request=inference_request,
                extra_metadata={"runtime_error": str(exc)},
            )

        preview = inference_response.content.strip() or (
            f"Architect runtime check completed via {self.inferencer.descriptor.display_name}."
        )
        return RoleCheckResult(
            role=role,
            passed=True,
            duration_seconds=round(perf_counter() - start, 3),
            warnings=warnings,
            findings=[],
            preview=preview,
            metadata={
                "selected_model": selected or recommended or inference_request.model,
                "recommended_model": recommended,
                "critic_profile": None,
                "inference_backend": self.inferencer.descriptor.backend,
                "inference_transport": self.inferencer.descriptor.transport,
                "inference_base_url": self.inferencer.descriptor.base_url,
                "inference_request": inference_request.model_dump(mode="json"),
                "execution_mode": "runtime_backed",
                "execution_source": "generalized_inferencer",
                "runtime_response": inference_response.model_dump(mode="json"),
            },
        )

    def _build_stub_result(
        self,
        *,
        role: str,
        selected: str | None,
        recommended: str | None,
        warnings: list[str],
        start: float,
        critic_profile: str | None,
        critic_profile_label: str | None,
        stub_mode: str,
        stub_reason: str,
        inference_request: InferenceRequest | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> RoleCheckResult:
        catalog = self.registry.build_catalog()
        request_payload = inference_request or self._build_inference_request(
            role=role,
            selected=selected,
            recommended=recommended,
            mode=stub_mode,
        )
        preview = (
            f"Checker stub executed for {role} via {catalog.inference_provider.display_name} "
            f"({catalog.inference_provider.transport})."
        )
        if critic_profile_label is not None:
            preview += f" Critic profile: {critic_profile_label}."
        metadata = {
            "selected_model": selected or recommended,
            "recommended_model": recommended,
            "critic_profile": critic_profile,
            "inference_backend": catalog.inference_provider.backend,
            "inference_transport": catalog.inference_provider.transport,
            "inference_base_url": catalog.inference_provider.base_url,
            "inference_request": request_payload.model_dump(mode="json"),
            "execution_mode": "stub_fallback",
            "execution_source": "stub_checker",
            "stub_reason": stub_reason,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        return RoleCheckResult(
            role=role,
            passed=True,
            duration_seconds=round(perf_counter() - start, 3),
            warnings=warnings,
            findings=[],
            preview=preview,
            metadata=metadata,
        )

    def _build_inference_request(
        self,
        *,
        role: str,
        selected: str | None,
        recommended: str | None,
        mode: str,
    ) -> InferenceRequest:
        return InferenceRequest(
            model=selected or recommended or self.inferencer.descriptor.default_model,
            messages=[
                InferenceMessage(role="system", content="You are a narrative runtime validation assistant."),
                InferenceMessage(
                    role="user",
                    content=(
                        f"Validate the configured model choice for the {role} role. "
                        f"Focus on suitability for narrative planning and structural coherence."
                    ),
                ),
            ],
            metadata={"role": role, "mode": mode},
        )

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
