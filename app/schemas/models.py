from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import StrictModel
from ..workflow_preferences import CriticExperimentProfile, RoleName


class ModelCatalogResponse(StrictModel):
    discovered_models: list[str] = Field(default_factory=list)
    default_selection: dict[RoleName, str | None] = Field(default_factory=dict)
    recommended_selection: dict[RoleName, str | None] = Field(default_factory=dict)
    workflow_order: list[RoleName] = Field(default_factory=list)
    workflow_guidance: list[str] = Field(default_factory=list)
    critic_profiles: dict[CriticExperimentProfile, str] = Field(default_factory=dict)
    default_critic_profile: CriticExperimentProfile
    override_warning: str


class ModelSelectionWarning(StrictModel):
    role: RoleName
    selected_model: str
    recommended_model: str | None = None
    warning: str
