from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.base import StrictSchemaModel
from app.schemas.enums import PovMode, StoryStructure


class ManifestConfig(StrictSchemaModel):
    genre: str = Field(min_length=1)
    tone_profile: str = Field(min_length=1)
    pov: PovMode = PovMode.THIRD_LIMITED
    primary_language: str = Field(default="English", min_length=1)
    secondary_language: str | None = Field(default=None, min_length=0)
    story_structure: StoryStructure
    mythos_source_corpus: str = ""
    mythos_generation_mode: str = ""
    pattern_source_type: str = ""
    pattern_generation_mode: str = ""
    pattern_source_corpus: str = ""
    target_word_count: int | None = Field(default=None, ge=100)

    @field_validator("genre", "tone_profile", "primary_language")
    @classmethod
    def validate_non_blank_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    @field_validator("secondary_language")
    @classmethod
    def validate_secondary_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class Manifest(StrictSchemaModel):
    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    config: ManifestConfig
    constraints: list[str] = Field(default_factory=list)
    premise_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        payload["project_id"] = str(payload.get("project_id", "")).strip()

        if "config" not in payload:
            payload["config"] = {
                "genre": payload.get("genre", ""),
                "tone_profile": payload.get("tone_profile") or payload.get("tone", ""),
                "pov": payload.get("pov", PovMode.THIRD_LIMITED.value),
                "primary_language": payload.get("primary_language", "English"),
                "secondary_language": payload.get("secondary_language") or "None",
                "story_structure": payload.get("story_structure", StoryStructure.THREE_ACT.value),
            }

        for legacy_key in (
            "genre",
            "tone",
            "tone_profile",
            "story_structure",
            "pov",
            "primary_language",
            "secondary_language",
        ):
            payload.pop(legacy_key, None)

        if not payload.get("project_name"):
            genre = str((payload.get("config") or {}).get("genre", "")).strip()
            if genre:
                payload["project_name"] = f"{genre} Project"
            elif payload["project_id"]:
                payload["project_name"] = payload["project_id"]

        payload.setdefault("constraints", [])
        return payload

    @field_validator("project_id", "project_name")
    @classmethod
    def validate_non_blank_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be blank")
        return normalized

    @field_validator("constraints")
    @classmethod
    def validate_constraints(cls, value: list[str]) -> list[str]:
        normalized_constraints: list[str] = []
        for item in value:
            normalized = item.strip()
            if not normalized:
                raise ValueError("constraints must not contain blank values")
            normalized_constraints.append(normalized)
        return normalized_constraints
