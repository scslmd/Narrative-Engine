from __future__ import annotations

from typing import Sequence

from app.persistence.story_development import (
    BrainDumpSessionRecord,
    StoryDevelopmentRepository,
)


_ALLOWED_STATE_TRANSITIONS: dict[str, list[str]] = {
    "active": ["organized", "archived"],
    "organized": ["archived"],
}


class BrainDumpServiceError(ValueError):
    pass


class BrainDumpValidationError(BrainDumpServiceError):
    pass


class BrainDumpNotFoundError(BrainDumpServiceError):
    pass


class BrainDumpService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

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

    def _validate_transition(self, from_state: str, to_state: str) -> None:
        allowed = _ALLOWED_STATE_TRANSITIONS.get(from_state, [])
        if to_state not in allowed:
            raise BrainDumpValidationError(
                f"Invalid state transition: {from_state} -> {to_state}. "
                f"Allowed transitions from {from_state}: {', '.join(allowed)}"
            )
