from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.canon_customization import CanonAnnotationCreateRequest, CanonCustomizationProfileCreateRequest


def test_canon_annotation_rejects_empty_target_id() -> None:
    with pytest.raises(ValidationError):
        CanonAnnotationCreateRequest.model_validate(
            {
                "project_id": "project-1",
                "target_kind": "character",
                "target_id": "",
                "field_path": "voice_notes",
                "annotation_kind": "locked",
            }
        )


def test_canon_profile_validates_with_scope() -> None:
    profile = CanonCustomizationProfileCreateRequest.model_validate(
        {
            "project_id": "project-1",
            "name": "default",
            "canon_scope": {
                "source_project_id": "project-1",
                "scope_mode": "selected",
                "character_ids": ["char-1"],
            },
        }
    )
    assert profile.name == "default"
