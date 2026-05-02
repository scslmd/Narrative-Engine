from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.pattern_library import PatternEntry, PatternEntryCreateRequest, PatternEntryUpdateRequest
from app.utils.db_inserts import hash_id


class PatternLibraryService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def list_entries(self, project_id: str, pattern_type: str | None = None) -> list[PatternEntry]:
        return [self._to_schema(item) for item in self.repository.list_pattern_entries(project_id, pattern_type)]

    def create_entry(self, payload: PatternEntryCreateRequest) -> PatternEntry:
        pattern_id = hash_id("pattern-entry", f"{payload.project_id}:{payload.pattern_type}:{payload.name}")
        record = self.repository.upsert_pattern_entry(
            pattern_id=pattern_id,
            project_id=payload.project_id,
            pattern_type=str(payload.pattern_type.value if hasattr(payload.pattern_type, "value") else payload.pattern_type),
            name=payload.name,
            summary=payload.summary,
            source_type=str(payload.source_type.value if hasattr(payload.source_type, "value") else payload.source_type),
            generation_modes=payload.generation_modes,
            beats=payload.beats,
            constraints=payload.constraints,
            transposition_notes=payload.transposition_notes,
            writer_notes=payload.writer_notes,
        )
        return self._to_schema(record)

    def update_entry(self, pattern_id: str, project_id: str, payload: PatternEntryUpdateRequest) -> PatternEntry:
        current = self.repository.get_pattern_entry(pattern_id)
        if current.project_id != project_id:
            raise KeyError(pattern_id)
        record = self.repository.upsert_pattern_entry(
            pattern_id=pattern_id,
            project_id=current.project_id,
            pattern_type=str(payload.pattern_type.value if payload.pattern_type is not None and hasattr(payload.pattern_type, "value") else payload.pattern_type or current.pattern_type),
            name=payload.name if payload.name is not None else current.name,
            summary=payload.summary if payload.summary is not None else current.summary,
            source_type=str(payload.source_type.value if payload.source_type is not None and hasattr(payload.source_type, "value") else payload.source_type or current.source_type),
            generation_modes=payload.generation_modes if payload.generation_modes is not None else current.generation_modes,
            beats=payload.beats if payload.beats is not None else current.beats,
            constraints=payload.constraints if payload.constraints is not None else current.constraints,
            transposition_notes=payload.transposition_notes if payload.transposition_notes is not None else current.transposition_notes,
            writer_notes=payload.writer_notes if payload.writer_notes is not None else current.writer_notes,
        )
        return self._to_schema(record)

    def delete_entry(self, project_id: str, pattern_id: str) -> None:
        current = self.repository.get_pattern_entry(pattern_id)
        if current.project_id != project_id:
            raise KeyError(pattern_id)
        self.repository.delete_pattern_entry(pattern_id)

    def materialize_extraction(self, project_id: str, extraction_id: str) -> list[PatternEntry]:
        return self.list_entries(project_id)

    def _to_schema(self, record) -> PatternEntry:
        return PatternEntry.model_validate(
            {
                **record.__dict__,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )
