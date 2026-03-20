from __future__ import annotations

from pydantic import Field

from .base import StrictModel
from .inference import InferenceProviderDescriptor
from ..workflow_preferences import CriticExperimentProfile, RoleName


class ModelCatalogResponse(StrictModel):
    discovered_models: list[str] = Field(default_factory=list)
    local_discovered_models: list[str] = Field(default_factory=list)
    runtime_discovered_models: list[str] = Field(default_factory=list)
    default_selection: dict[RoleName, str | None] = Field(default_factory=dict)
    recommended_selection: dict[RoleName, str | None] = Field(default_factory=dict)
    workflow_order: list[RoleName] = Field(default_factory=list)
    workflow_guidance: list[str] = Field(default_factory=list)
    critic_profiles: dict[CriticExperimentProfile, str] = Field(default_factory=dict)
    default_critic_profile: CriticExperimentProfile
    override_warning: str
    inference_provider: InferenceProviderDescriptor


class ModelSelectionWarning(StrictModel):
    role: RoleName
    selected_model: str
    recommended_model: str | None = None
    warning: str
