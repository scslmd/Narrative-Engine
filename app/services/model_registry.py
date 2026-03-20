from __future__ import annotations

from pathlib import Path

from ..schemas.models import ModelCatalogResponse
from ..workflow_preferences import (
    CRITIC_PROFILE_DEFINITIONS,
    DEFAULT_CRITIC_PROFILE,
    MODEL_ROLE_PATTERNS,
    OVERRIDE_WARNING,
    WORKFLOW_GUIDANCE,
    WORKFLOW_ORDER,
)


class ModelRegistry:
    def __init__(self, models_root: Path) -> None:
        self.models_root = models_root

    def discover_models(self) -> list[str]:
        if not self.models_root.exists():
            return []
        return sorted(str(path.relative_to(self.models_root)).replace('\\', '/') for path in self.models_root.rglob('*.gguf'))

    def _pick_for_role(self, discovered: list[str], role: str) -> str | None:
        patterns = MODEL_ROLE_PATTERNS.get(role, [])
        lowered = [(item, item.lower()) for item in discovered]
        for pattern in patterns:
            for original, lowered_value in lowered:
                if pattern in lowered_value:
                    return original
        return discovered[0] if discovered else None

    def build_catalog(self) -> ModelCatalogResponse:
        discovered = self.discover_models()
        recommended = {role: self._pick_for_role(discovered, role) for role in WORKFLOW_ORDER}
        default = dict(recommended)
        return ModelCatalogResponse(
            discovered_models=discovered,
            default_selection=default,
            recommended_selection=recommended,
            workflow_order=list(WORKFLOW_ORDER),
            workflow_guidance=list(WORKFLOW_GUIDANCE),
            critic_profiles={key: value['label'] for key, value in CRITIC_PROFILE_DEFINITIONS.items()},
            default_critic_profile=DEFAULT_CRITIC_PROFILE,
            override_warning=OVERRIDE_WARNING,
        )
