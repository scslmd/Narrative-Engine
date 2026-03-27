from __future__ import annotations

from fastapi import APIRouter

from ..schemas.models import ModelCatalogResponse
from ..services.model_registry import ModelRegistry


def build_models_router(model_registry: ModelRegistry) -> APIRouter:
    router = APIRouter(prefix='/v1', tags=['models'])

    @router.get('/models', response_model=ModelCatalogResponse)
    def get_models() -> ModelCatalogResponse:
        return model_registry.build_catalog()

    return router
