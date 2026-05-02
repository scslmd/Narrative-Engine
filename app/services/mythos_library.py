from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.mythos_library import MythosEntry, MythosEntryCreateRequest, MythosEntryUpdateRequest
from app.utils.db_inserts import hash_id


class MythosLibraryService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def list_entries(self, project_id: str, entry_type: str | None = None) -> list[MythosEntry]:
        return [self._to_schema(item) for item in self.repository.list_mythos_entries(project_id, entry_type)]

    def create_entry(self, payload: MythosEntryCreateRequest) -> MythosEntry:
        mythos_id = hash_id("mythos-entry", f"{payload.project_id}:{payload.entry_type}:{payload.name}")
        record = self.repository.upsert_mythos_entry(
            mythos_id=mythos_id,
            project_id=payload.project_id,
            entry_type=str(payload.entry_type.value if hasattr(payload.entry_type, "value") else payload.entry_type),
            name=payload.name,
            summary=payload.summary,
            canonical_facts=payload.canonical_facts,
            pattern_notes=payload.pattern_notes,
            source_corpus=payload.source_corpus,
            generation_guidance=payload.generation_guidance,
            visibility_scope=str(payload.visibility_scope.value if hasattr(payload.visibility_scope, "value") else payload.visibility_scope),
            writer_notes=payload.writer_notes,
        )
        return self._to_schema(record)

    def update_entry(self, mythos_id: str, project_id: str, payload: MythosEntryUpdateRequest) -> MythosEntry:
        current = self.repository.get_mythos_entry(mythos_id)
        if current.project_id != project_id:
            raise KeyError(mythos_id)
        record = self.repository.upsert_mythos_entry(
            mythos_id=mythos_id,
            project_id=current.project_id,
            entry_type=str(payload.entry_type.value if payload.entry_type is not None and hasattr(payload.entry_type, "value") else payload.entry_type or current.entry_type),
            name=payload.name if payload.name is not None else current.name,
            summary=payload.summary if payload.summary is not None else current.summary,
            canonical_facts=payload.canonical_facts if payload.canonical_facts is not None else current.canonical_facts,
            pattern_notes=payload.pattern_notes if payload.pattern_notes is not None else current.pattern_notes,
            source_corpus=payload.source_corpus if payload.source_corpus is not None else current.source_corpus,
            generation_guidance=payload.generation_guidance if payload.generation_guidance is not None else current.generation_guidance,
            visibility_scope=str(payload.visibility_scope.value if payload.visibility_scope is not None and hasattr(payload.visibility_scope, "value") else payload.visibility_scope or current.visibility_scope),
            writer_notes=payload.writer_notes if payload.writer_notes is not None else current.writer_notes,
        )
        return self._to_schema(record)

    def delete_entry(self, project_id: str, mythos_id: str) -> None:
        current = self.repository.get_mythos_entry(mythos_id)
        if current.project_id != project_id:
            raise KeyError(mythos_id)
        self.repository.delete_mythos_entry(mythos_id)

    def materialize_extraction(self, project_id: str, extraction_id: str) -> list[MythosEntry]:
        return self.list_entries(project_id)

    def _to_schema(self, record) -> MythosEntry:
        return MythosEntry.model_validate(
            {
                **record.__dict__,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )
