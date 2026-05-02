from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.generation import (
    CanonGenerationRequest,
    DestinationKind,
    GenerationDestination,
    GenerationMode,
)


def _base_request_payload() -> dict[str, object]:
    return {
        "source_project_id": "source-project",
        "mode": GenerationMode.SAME_PROJECT_SIDE_STORY,
        "destination": {
            "destination_kind": DestinationKind.SAME_PROJECT,
            "target_project_id": "source-project",
        },
        "canon_scope": {
            "source_project_id": "source-project",
            "character_ids": ["char-a"],
        },
        "generation_brief": "Generate a side story focused on character growth.",
        "target_chapter_count": 6,
    }


def test_generation_request_rejects_empty_selected_scope() -> None:
    payload = _base_request_payload()
    payload["canon_scope"] = {"source_project_id": "source-project"}

    with pytest.raises(ValidationError):
        CanonGenerationRequest.model_validate(payload)


def test_generation_request_accepts_full_project_scope_without_selectors() -> None:
    payload = _base_request_payload()
    payload["canon_scope"] = {
        "source_project_id": "source-project",
        "scope_mode": "full_project",
    }

    model = CanonGenerationRequest.model_validate(payload)

    assert model.canon_scope.scope_mode == "full_project"
    assert model.canon_scope.character_ids == []


def test_generation_destination_rejects_invalid_same_project_combination() -> None:
    with pytest.raises(ValidationError):
        GenerationDestination.model_validate(
            {
                "destination_kind": DestinationKind.SAME_PROJECT,
                "target_project_name": "Ignored Name",
            }
        )


def test_generation_destination_rejects_invalid_new_project_combination() -> None:
    with pytest.raises(ValidationError):
        GenerationDestination.model_validate({"destination_kind": DestinationKind.NEW_PROJECT})


def test_generation_request_rejects_invalid_numeric_bounds() -> None:
    payload = _base_request_payload()
    payload["target_chapter_count"] = 0

    with pytest.raises(ValidationError):
        CanonGenerationRequest.model_validate(payload)

    payload = _base_request_payload()
    payload["temperature"] = 1.5
    with pytest.raises(ValidationError):
        CanonGenerationRequest.model_validate(payload)


def test_generation_request_accepts_valid_new_project_request() -> None:
    payload = _base_request_payload()
    payload["mode"] = GenerationMode.NEW_PROJECT_CHARACTER_FORK
    payload["destination"] = {
        "destination_kind": DestinationKind.NEW_PROJECT,
        "target_project_name": "Forked Story",
    }

    model = CanonGenerationRequest.model_validate(payload)

    assert model.destination.destination_kind == DestinationKind.NEW_PROJECT
    assert model.destination.target_project_name == "Forked Story"
