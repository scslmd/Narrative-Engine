from __future__ import annotations

from typing import Sequence

from app.inference import InferenceBackend, InferenceBackendError
from app.persistence.story_development import (
    BrainDumpSessionRecord,
    StoryDevelopmentRepository,
)
from app.schemas import BrainstormItem
from app.schemas.inference import InferenceMessage
from app.services.runtime_prompts import build_brain_dump_organize_request
from app.utils.json_extract import extract_json


_ALLOWABLE_STATE_TRANSITIONS: dict[str, list[str]] = {
    "active": ["organized", "archived"],
    "organized": ["archived"],
}


class BrainDumpServiceError(ValueError):
    pass


class BrainDumpValidationError(BrainDumpServiceError):
    pass


class BrainDumpNotFoundError(BrainDumpServiceError):
    pass


class BrainDumpOrganizeError(BrainDumpServiceError):
    pass


class BrainDumpService:
    def __init__(
        self,
        repository: StoryDevelopmentRepository,
        inferencer: InferenceBackend | None = None,
    ) -> None:
        self.repository = repository
        self._inferencer = inferencer

    def create_session(
        self,
        *,
        project_id: str,
        title: str | None = None,
        raw_text: str = "",
    ) -> BrainDumpSessionRecord:
        return self.repository.create_brain_dump_session(
            project_id=project_id,
            title=title,
            raw_text=raw_text,
        )

    def get_session(self, session_id: int) -> BrainDumpSessionRecord:
        try:
            return self.repository.get_brain_dump_session(session_id)
        except KeyError:
            raise BrainDumpNotFoundError(session_id)

    def list_sessions(self, project_id: str) -> tuple[BrainDumpSessionRecord, ...]:
        return tuple(self.repository.list_brain_dump_sessions(project_id))

    def update_session(
        self,
        session_id: int,
        *,
        raw_text: str | None = None,
        title: str | None = None,
        state: str | None = None,
    ) -> BrainDumpSessionRecord:
        current = self.get_session(session_id)
        if state is not None and state != current.state:
            self._validate_transition(current.state, state)
        return self.repository.update_brain_dump_session(
            session_id,
            raw_text=raw_text,
            title=title,
            state=state,
        )

    def delete_session(self, session_id: int) -> None:
        self.repository.delete_brain_dump_session(session_id)

    def organize(
        self,
        session_id: int,
        project_id: str,
        *,
        brainstorm_service: object,
    ) -> dict[str, list[BrainstormItem]]:
        session = self.get_session(session_id)
        if session.project_id != project_id:
            raise BrainDumpNotFoundError(session_id)
        if session.state != "active":
            raise BrainDumpValidationError("Only active sessions can be organized.")

        if self._inferencer is None:
            raise BrainDumpOrganizeError(
                "LLM inference is not configured. Cannot organize brain dump."
            )

        inference_request = build_brain_dump_organize_request(
            raw_text=session.raw_text,
            default_model=self._inferencer.descriptor.default_model,
        )

        try:
            response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            raise BrainDumpOrganizeError(
                f"LLM inference failed: {exc.provider_message}"
            ) from exc

        categorized_text: dict[str, list[str]] = self._parse_llm_json(response.content)
        self._validate_organize_response(categorized_text)

        created_items: dict[str, list[BrainstormItem]] = {}
        for category, text_blocks in categorized_text.items():
            items: list[BrainstormItem] = []
            for text in text_blocks:
                stripped = text.strip()
                if not stripped:
                    continue
                item = brainstorm_service.capture_brainstorm_item(
                    project_id=project_id,
                    content=stripped,
                    status="keep",
                    tags=[category],
                )
                items.append(item)
            if items:
                created_items[category] = items

        self.update_session(session_id, state="organized")
        return created_items

    @staticmethod
    def _parse_llm_json(content: str) -> dict[str, list[str]]:
        if not content or not content.strip():
            raise BrainDumpOrganizeError("Empty LLM response.")

        data = extract_json(content)
        if data is None:
            raise BrainDumpOrganizeError("Could not extract JSON from LLM response.")
        return data

    @staticmethod
    def _validate_organize_response(data: dict[str, list[str]]) -> None:
        required_keys = {
            "character", "location", "plot_point", "theme", "conflict",
            "world_building", "dialogue", "relationship", "object", "rule",
        }
        found_keys = set(data.keys())
        missing = required_keys - found_keys
        if missing:
            raise BrainDumpOrganizeError(
                f"LLM response missing required keys: {', '.join(sorted(missing))}"
            )
        for key, value in data.items():
            if not isinstance(value, list):
                raise BrainDumpOrganizeError(
                    f"LLM response key '{key}' must be an array, got {type(value).__name__}"
                )

    def _validate_transition(self, from_state: str, to_state: str) -> None:
        allowed = _ALLOWABLE_STATE_TRANSITIONS.get(from_state, [])
        if to_state not in allowed:
            raise BrainDumpValidationError(
                f"Invalid state transition: {from_state} -> {to_state}. "
                f"Allowed transitions from {from_state}: {', '.join(allowed)}"
            )
