from __future__ import annotations

import uuid
from datetime import datetime

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.story_development import (
    RevisionChecklistItem,
    RevisionPass,
    RevisionPassListResponse,
)


class RevisionServiceError(ValueError):
    pass


class RevisionNotFoundError(RevisionServiceError):
    pass


class RevisionConflictError(RevisionServiceError):
    pass


class RevisionService:
    DEFAULT_CHECKLISTS = {
        "structural": [
            {"item_id": "structure-1", "label": "Check plot structure", "done": False},
            {"item_id": "structure-2", "label": "Verify pacing", "done": False},
            {"item_id": "structure-3", "label": "Review scene transitions", "done": False},
        ],
        "character": [
            {"item_id": "character-1", "label": "Check character consistency", "done": False},
            {"item_id": "character-2", "label": "Verify character arcs", "done": False},
            {"item_id": "character-3", "label": "Review dialogue authenticity", "done": False},
        ],
        "scene": [
            {"item_id": "scene-1", "label": "Check scene purpose", "done": False},
            {"item_id": "scene-2", "label": "Verify sensory details", "done": False},
            {"item_id": "scene-3", "label": "Review scene flow", "done": False},
        ],
        "line_edit": [
            {"item_id": "line-1", "label": "Check sentence variety", "done": False},
            {"item_id": "line-2", "label": "Remove redundant phrases", "done": False},
            {"item_id": "line-3", "label": "Improve word choice", "done": False},
        ],
        "copy_edit": [
            {"item_id": "copy-1", "label": "Check grammar and spelling", "done": False},
            {"item_id": "copy-2", "label": "Verify punctuation", "done": False},
            {"item_id": "copy-3", "label": "Check formatting consistency", "done": False},
        ],
    }

    def __init__(self, repository: StoryDevelopmentRepository):
        self._repository = repository

    def create_pass(
        self,
        project_id: str,
        pass_type: str,
        status: str = "pending",
        notes: str | None = None,
    ) -> RevisionPass:
        pass_id = str(uuid.uuid4())
        checklist = self.DEFAULT_CHECKLISTS.get(pass_type, [])
        record = self._repository.create_revision_pass(
            project_id=project_id,
            pass_id=pass_id,
            pass_type=pass_type,
            status=status,
            checklist=checklist,
            notes=notes,
        )
        return self._record_to_pass(record)

    def get_pass(self, pass_id: str) -> RevisionPass:
        try:
            record = self._repository.get_revision_pass(pass_id)
        except KeyError:
            raise RevisionNotFoundError(f"Revision pass {pass_id} not found") from None
        return self._record_to_pass(record)

    def list_passes(
        self,
        project_id: str,
        pass_type: str | None = None,
        status: str | None = None,
    ) -> list[RevisionPass]:
        records = self._repository.list_revision_passes(
            project_id,
            pass_type=pass_type,
            status=status,
        )
        return [self._record_to_pass(record) for record in records]

    def update_pass(
        self,
        pass_id: str,
        *,
        status: str | None = None,
        notes: str | None = None,
        checklist: list[dict[str, object]] | None = None,
    ) -> RevisionPass:
        try:
            current = self._repository.get_revision_pass(pass_id)
        except KeyError:
            raise RevisionNotFoundError(f"Revision pass {pass_id} not found") from None

        if current.completed_at and checklist is not None:
            raise RevisionConflictError(
                f"Cannot modify checklist after pass {pass_id} is completed"
            )

        record = self._repository.update_revision_pass(
            pass_id,
            status=status,
            checklist=checklist,
            notes=notes,
        )
        return self._record_to_pass(record)

    def complete_pass(self, pass_id: str) -> RevisionPass:
        try:
            self._repository.get_revision_pass(pass_id)
        except KeyError:
            raise RevisionNotFoundError(f"Revision pass {pass_id} not found") from None

        record = self._repository.complete_revision_pass(pass_id)
        return self._record_to_pass(record)

    def get_checklist(self, pass_type: str) -> list[RevisionChecklistItem]:
        items = self.DEFAULT_CHECKLISTS.get(pass_type, [])
        return [RevisionChecklistItem(**item) for item in items]

    def _record_to_pass(self, record) -> RevisionPass:
        from app.persistence.story_development.records import RevisionPassRecord
        if isinstance(record, RevisionPassRecord):
            return RevisionPass(
                pass_id=record.pass_id,
                project_id=record.project_id,
                pass_type=record.pass_type,
                status=record.status,
                checklist=[
                    RevisionChecklistItem(
                        item_id=item.item_id,
                        label=item.label,
                        done=item.done,
                    )
                    for item in record.checklist
                ],
                notes=record.notes,
                created_at=record.created_at,
                completed_at=record.completed_at,
            )
        return RevisionPass.model_validate(record)
