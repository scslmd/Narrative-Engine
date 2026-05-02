from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.mythos_library import MythosEntryCreateRequest
from app.schemas.pattern_library import PatternEntryCreateRequest


def test_mythos_entry_schema_rejects_invalid_entry_type() -> None:
    with pytest.raises(ValidationError):
        MythosEntryCreateRequest.model_validate(
            {
                "project_id": "project-1",
                "entry_type": "bad_type",
                "name": "X",
            }
        )


def test_pattern_entry_schema_rejects_invalid_pattern_type() -> None:
    with pytest.raises(ValidationError):
        PatternEntryCreateRequest.model_validate(
            {
                "project_id": "project-1",
                "pattern_type": "bad_type",
                "name": "X",
            }
        )
