from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from app.persistence.story_development import (
    DraftArtifactRecord,
    ManuscriptDocumentRecord,
    RevisionSuggestionRecord,
    StoryDevelopmentRepository,
)
from app.schemas import (
    DraftArtifact,
    ManuscriptDocument,
    RevisionSuggestion,
    StoryArtifactLifecycleState,
    StorySuggestionLifecycleState,
)


class DraftingServiceError(ValueError):
    pass


class DraftingValidationError(DraftingServiceError):
    pass


class DraftingNotFoundError(DraftingServiceError):
    pass


@dataclass(frozen=True)
class DraftingContext:
    source_plan_ids: tuple[str, ...] = ()
    source_context: tuple[str, ...] = ()


class DraftingService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def register_draft_artifact(
        self,
        project_id: str,
        *,
        artifact_id: str,
        title: str,
        content: str,
        source_plan_ids: Sequence[str] | None = None,
        source_context: Sequence[str] | None = None,
        provenance_note: str | None = None,
        status: StoryArtifactLifecycleState | str = StoryArtifactLifecycleState.DRAFT,
    ) -> DraftArtifact:
        context = self._drafting_context_from_planning(source_plan_ids=source_plan_ids, source_context=source_context)
        record = self.repository.upsert_draft_artifact(
            artifact_id=self._normalize_text(artifact_id, field_name="artifact_id"),
            project_id=self._normalize_text(project_id, field_name="project_id"),
            title=self._normalize_text(title, field_name="title"),
            content=self._normalize_text(content, field_name="content"),
            source_plan_ids=context.source_plan_ids,
            source_context=context.source_context,
            provenance_note=self._normalize_optional_text(provenance_note, field_name="provenance_note"),
            status=self._normalize_artifact_status(status),
        )
        return self._draft_from_record(record)

    def continue_draft(
        self,
        project_id: str,
        *,
        artifact_id: str,
        title: str,
        content: str,
        prior_draft_artifact_id: str | None = None,
        prior_manuscript_document_id: str | None = None,
        source_plan_ids: Sequence[str] | None = None,
        source_context: Sequence[str] | None = None,
        provenance_note: str | None = None,
    ) -> DraftArtifact:
        source_record, continuation_context = self._resolve_continuation_source(
            project_id,
            prior_draft_artifact_id=prior_draft_artifact_id,
            prior_manuscript_document_id=prior_manuscript_document_id,
        )
        inherited_source_plan_ids = self._source_plan_ids_for_record(source_record)
        context = self._drafting_context_from_planning(
            source_plan_ids=source_plan_ids,
            source_context=source_context,
        )
        merged_source_plan_ids = self._merge_unique_strings(
            inherited_source_plan_ids,
            context.source_plan_ids,
        )
        merged_source_context = self._merge_unique_strings(
            continuation_context,
            context.source_context,
        )
        record = self.repository.upsert_draft_artifact(
            artifact_id=self._normalize_text(artifact_id, field_name="artifact_id"),
            project_id=self._normalize_text(project_id, field_name="project_id"),
            title=self._normalize_text(title, field_name="title"),
            content=self._normalize_text(content, field_name="content"),
            source_plan_ids=merged_source_plan_ids,
            source_context=merged_source_context,
            provenance_note=self._normalize_optional_text(provenance_note, field_name="provenance_note"),
            status=StoryArtifactLifecycleState.DRAFT,
        )
        return self._draft_from_record(record)

    def create_alternate_variant(
        self,
        project_id: str,
        *,
        artifact_id: str,
        title: str,
        content: str,
        base_draft_artifact_id: str | None = None,
        base_manuscript_document_id: str | None = None,
        source_plan_ids: Sequence[str] | None = None,
        source_context: Sequence[str] | None = None,
        provenance_note: str | None = None,
    ) -> DraftArtifact:
        source_record, variant_context = self._resolve_variant_source(
            project_id,
            base_draft_artifact_id=base_draft_artifact_id,
            base_manuscript_document_id=base_manuscript_document_id,
        )
        inherited_source_plan_ids = self._source_plan_ids_for_record(source_record)
        context = self._drafting_context_from_planning(
            source_plan_ids=source_plan_ids,
            source_context=source_context,
        )
        merged_source_plan_ids = self._merge_unique_strings(
            inherited_source_plan_ids,
            context.source_plan_ids,
        )
        merged_source_context = self._merge_unique_strings(
            variant_context,
            context.source_context,
        )
        record = self.repository.upsert_draft_artifact(
            artifact_id=self._normalize_text(artifact_id, field_name="artifact_id"),
            project_id=self._normalize_text(project_id, field_name="project_id"),
            title=self._normalize_text(title, field_name="title"),
            content=self._normalize_text(content, field_name="content"),
            source_plan_ids=merged_source_plan_ids,
            source_context=merged_source_context,
            provenance_note=self._normalize_optional_text(provenance_note, field_name="provenance_note"),
            status=StoryArtifactLifecycleState.PROPOSED,
        )
        return self._draft_from_record(record)

    def save_manuscript_document(
        self,
        project_id: str,
        *,
        document_id: str,
        content: str,
        title: str | None = None,
        display_title: str | None = None,
        chapter_id: str | None = None,
        scene_id: str | None = None,
        current_draft_artifact_id: str | None = None,
        version: int | None = None,
    ) -> ManuscriptDocument:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_document_id = self._normalize_text(document_id, field_name="document_id")
        normalized_content = self._normalize_text(content, field_name="content")
        existing = self._existing_manuscript_document(normalized_project_id, normalized_document_id)
        if existing is None and title is None:
            raise DraftingValidationError("title is required when creating a new manuscript document")

        normalized_title = self._normalize_text(title, field_name="title") if title is not None else existing.title
        # Extract display_title from content's first markdown heading if not provided
        if display_title is None:
            heading_match = re.match(r'^#\s+(.+)$', normalized_content, re.MULTILINE)
            display_title = heading_match.group(1).strip() if heading_match else None
        normalized_display_title = self._normalize_optional_text(display_title, field_name="display_title")
        normalized_chapter_id = (
            self._normalize_optional_text(chapter_id, field_name="chapter_id")
            if chapter_id is not None
            else (existing.chapter_id if existing is not None else None)
        )
        normalized_scene_id = (
            self._normalize_optional_text(scene_id, field_name="scene_id")
            if scene_id is not None
            else (existing.scene_id if existing is not None else None)
        )
        if current_draft_artifact_id is None:
            normalized_current_draft_artifact_id = (
                existing.current_draft_artifact_id if existing is not None else None
            )
        else:
            normalized_current_draft_artifact_id = self._normalize_optional_text(
                current_draft_artifact_id,
                field_name="current_draft_artifact_id",
            )
            self._require_draft_artifact(normalized_project_id, normalized_current_draft_artifact_id)

        next_version = self._normalize_version(version)
        if next_version is None:
            next_version = 1 if existing is None else existing.version + 1

        record = self.repository.upsert_manuscript_document(
            document_id=normalized_document_id,
            project_id=normalized_project_id,
            title=normalized_title,
            display_title=normalized_display_title,
            content=normalized_content,
            chapter_id=normalized_chapter_id,
            scene_id=normalized_scene_id,
            current_draft_artifact_id=normalized_current_draft_artifact_id,
            version=next_version,
        )
        return self._manuscript_from_record(record)

    def promote_draft_to_manuscript(
        self,
        project_id: str,
        *,
        document_id: str,
        draft_artifact_id: str,
        title: str | None = None,
        chapter_id: str | None = None,
        scene_id: str | None = None,
        version: int | None = None,
    ) -> ManuscriptDocument:
        draft = self._require_draft_artifact(project_id, draft_artifact_id)
        return self.save_manuscript_document(
            project_id,
            document_id=document_id,
            content=draft.content,
            title=title if title is not None else draft.title,
            chapter_id=chapter_id,
            scene_id=scene_id,
            current_draft_artifact_id=draft.artifact_id,
            version=version,
        )

    def create_revision_suggestion(
        self,
        project_id: str,
        *,
        suggestion_id: str,
        target_document_id: str,
        source_text: str,
        proposed_text: str,
        rationale: str,
        source_context: Sequence[str] | None = None,
        status: StorySuggestionLifecycleState | str = StorySuggestionLifecycleState.REQUESTED,
    ) -> RevisionSuggestion:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        target_document = self._require_manuscript_document(normalized_project_id, target_document_id)
        context = self._merge_unique_strings(
            [f"manuscript:{target_document.document_id}"],
            self._normalize_text_list(source_context, field_name="source_context"),
        )
        record = self.repository.upsert_revision_suggestion(
            suggestion_id=self._normalize_text(suggestion_id, field_name="suggestion_id"),
            project_id=normalized_project_id,
            target_document_id=target_document.document_id,
            source_text=self._normalize_text(source_text, field_name="source_text"),
            proposed_text=self._normalize_text(proposed_text, field_name="proposed_text"),
            rationale=self._normalize_text(rationale, field_name="rationale"),
            source_context=context,
            status=self._normalize_suggestion_status(status),
        )
        return self._revision_from_record(record)

    def get_draft_artifact(self, project_id: str, *, artifact_id: str) -> DraftArtifact:
        return self._draft_from_record(self._require_draft_artifact(project_id, artifact_id))

    def list_draft_artifacts(self, project_id: str) -> tuple[DraftArtifact, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        return tuple(self._draft_from_record(record) for record in self.repository.list_draft_artifacts(normalized_project_id))

    def get_manuscript_document(self, project_id: str, *, document_id: str) -> ManuscriptDocument:
        return self._manuscript_from_record(self._require_manuscript_document(project_id, document_id))

    def list_manuscript_documents(self, project_id: str) -> tuple[ManuscriptDocument, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        return tuple(
            self._manuscript_from_record(record)
            for record in self.repository.list_manuscript_documents(normalized_project_id)
        )

    def get_revision_suggestion(self, project_id: str, *, suggestion_id: str) -> RevisionSuggestion:
        return self._revision_from_record(self._require_revision_suggestion(project_id, suggestion_id))

    def list_revision_suggestions(self, project_id: str) -> tuple[RevisionSuggestion, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        return tuple(
            self._revision_from_record(record)
            for record in self.repository.list_revision_suggestions(normalized_project_id)
        )

    def list_revision_suggestions_for_document(
        self,
        project_id: str,
        *,
        target_document_id: str,
    ) -> tuple[RevisionSuggestion, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_target_document_id = self._normalize_text(target_document_id, field_name="target_document_id")
        return tuple(
            self._revision_from_record(record)
            for record in self.repository.list_revision_suggestions_for_document(
                normalized_project_id,
                target_document_id=normalized_target_document_id,
            )
        )

    def _drafting_context_from_planning(
        self,
        *,
        source_plan_ids: Sequence[str] | None,
        source_context: Sequence[str] | None,
    ) -> DraftingContext:
        normalized_plan_ids = self._normalize_text_list(source_plan_ids, field_name="source_plan_ids")
        normalized_context = self._normalize_text_list(source_context, field_name="source_context")
        if not normalized_context and normalized_plan_ids:
            normalized_context = [f"plan:{plan_id}" for plan_id in normalized_plan_ids]
        return DraftingContext(
            source_plan_ids=tuple(normalized_plan_ids),
            source_context=tuple(normalized_context),
        )

    def _resolve_continuation_source(
        self,
        project_id: str,
        *,
        prior_draft_artifact_id: str | None,
        prior_manuscript_document_id: str | None,
    ) -> tuple[DraftArtifactRecord | ManuscriptDocumentRecord, tuple[str, ...]]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        if prior_draft_artifact_id is not None and prior_manuscript_document_id is not None:
            raise DraftingValidationError("prior_draft_artifact_id and prior_manuscript_document_id are mutually exclusive")
        if prior_draft_artifact_id is None and prior_manuscript_document_id is None:
            raise DraftingValidationError("one prior draft or manuscript source is required for continuation")
        if prior_draft_artifact_id is not None:
            draft = self._require_draft_artifact(normalized_project_id, prior_draft_artifact_id)
            return draft, (f"draft:{draft.artifact_id}",)
        manuscript = self._require_manuscript_document(normalized_project_id, prior_manuscript_document_id or "")
        context = [f"manuscript:{manuscript.document_id}"]
        if manuscript.current_draft_artifact_id is not None:
            context.append(f"draft:{manuscript.current_draft_artifact_id}")
        return manuscript, tuple(context)

    def _resolve_variant_source(
        self,
        project_id: str,
        *,
        base_draft_artifact_id: str | None,
        base_manuscript_document_id: str | None,
    ) -> tuple[DraftArtifactRecord | ManuscriptDocumentRecord, tuple[str, ...]]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        if base_draft_artifact_id is not None and base_manuscript_document_id is not None:
            raise DraftingValidationError("base_draft_artifact_id and base_manuscript_document_id are mutually exclusive")
        if base_draft_artifact_id is None and base_manuscript_document_id is None:
            raise DraftingValidationError("one base draft or manuscript source is required for an alternate variant")
        if base_draft_artifact_id is not None:
            draft = self._require_draft_artifact(normalized_project_id, base_draft_artifact_id)
            return draft, (f"draft:{draft.artifact_id}",)
        manuscript = self._require_manuscript_document(normalized_project_id, base_manuscript_document_id or "")
        context = [f"manuscript:{manuscript.document_id}"]
        if manuscript.current_draft_artifact_id is not None:
            context.append(f"draft:{manuscript.current_draft_artifact_id}")
        return manuscript, tuple(context)

    def _source_plan_ids_for_record(self, record: DraftArtifactRecord | ManuscriptDocumentRecord) -> tuple[str, ...]:
        if isinstance(record, DraftArtifactRecord):
            return tuple(record.source_plan_ids)
        if record.current_draft_artifact_id is None:
            return ()
        try:
            draft = self.repository.get_draft_artifact(record.current_draft_artifact_id)
        except KeyError:
            return ()
        return tuple(draft.source_plan_ids)

    def _require_draft_artifact(self, project_id: str, artifact_id: str) -> DraftArtifactRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_artifact_id = self._normalize_text(artifact_id, field_name="artifact_id")
        try:
            record = self.repository.get_draft_artifact(normalized_artifact_id)
        except KeyError as exc:
            raise DraftingNotFoundError(normalized_artifact_id) from exc
        if record.project_id != normalized_project_id:
            raise DraftingNotFoundError(normalized_artifact_id)
        return record

    def _require_manuscript_document(self, project_id: str, document_id: str) -> ManuscriptDocumentRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_document_id = self._normalize_text(document_id, field_name="document_id")
        try:
            record = self.repository.get_manuscript_document(normalized_document_id)
        except KeyError as exc:
            raise DraftingNotFoundError(normalized_document_id) from exc
        if record.project_id != normalized_project_id:
            raise DraftingNotFoundError(normalized_document_id)
        return record

    def _require_revision_suggestion(self, project_id: str, suggestion_id: str) -> RevisionSuggestionRecord:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_suggestion_id = self._normalize_text(suggestion_id, field_name="suggestion_id")
        try:
            record = self.repository.get_revision_suggestion(normalized_suggestion_id)
        except KeyError as exc:
            raise DraftingNotFoundError(normalized_suggestion_id) from exc
        if record.project_id != normalized_project_id:
            raise DraftingNotFoundError(normalized_suggestion_id)
        return record

    def _existing_manuscript_document(self, project_id: str, document_id: str) -> ManuscriptDocumentRecord | None:
        try:
            record = self.repository.get_manuscript_document(document_id)
        except KeyError:
            return None
        if record.project_id != self._normalize_text(project_id, field_name="project_id"):
            raise DraftingNotFoundError(document_id)
        return record

    def _draft_from_record(self, record: DraftArtifactRecord) -> DraftArtifact:
        return DraftArtifact.model_validate(
            {
                "artifact_id": record.artifact_id,
                "project_id": record.project_id,
                "title": record.title,
                "content": record.content,
                "source_plan_ids": list(record.source_plan_ids),
                "source_context": list(record.source_context),
                "provenance_note": record.provenance_note,
                "status": record.status,
            }
        )

    def _manuscript_from_record(self, record: ManuscriptDocumentRecord) -> ManuscriptDocument:
        return ManuscriptDocument.model_validate(
            {
                "document_id": record.document_id,
                "project_id": record.project_id,
                "title": record.title,
                "display_title": record.display_title,
                "content": record.content,
                "chapter_id": record.chapter_id,
                "scene_id": record.scene_id,
                "current_draft_artifact_id": record.current_draft_artifact_id,
                "version": record.version,
            }
        )

    def _revision_from_record(self, record: RevisionSuggestionRecord) -> RevisionSuggestion:
        return RevisionSuggestion.model_validate(
            {
                "suggestion_id": record.suggestion_id,
                "project_id": record.project_id,
                "target_document_id": record.target_document_id,
                "source_text": record.source_text,
                "proposed_text": record.proposed_text,
                "rationale": record.rationale,
                "source_context": list(record.source_context),
                "status": record.status,
            }
        )

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _normalize_optional_text(self, value: object, *, field_name: str) -> str | None:
        if value is None:
            return None
        return self._normalize_text(value, field_name=field_name)

    def _normalize_text_list(self, values: Sequence[str] | None, *, field_name: str) -> list[str]:
        if values is None:
            return []
        normalized: list[str] = []
        for value in values:
            normalized.append(self._normalize_text(value, field_name=field_name))
        return normalized

    def _normalize_artifact_status(self, status: StoryArtifactLifecycleState | str) -> StoryArtifactLifecycleState:
        if isinstance(status, StoryArtifactLifecycleState):
            return status
        normalized = self._normalize_text(status, field_name="status").upper()
        try:
            return StoryArtifactLifecycleState[normalized]
        except KeyError as exc:
            allowed = ", ".join(state.value for state in StoryArtifactLifecycleState)
            raise DraftingValidationError(f"status must be one of: {allowed}") from exc

    def _normalize_suggestion_status(
        self,
        status: StorySuggestionLifecycleState | str,
    ) -> StorySuggestionLifecycleState:
        if isinstance(status, StorySuggestionLifecycleState):
            return status
        normalized = self._normalize_text(status, field_name="status").upper()
        try:
            return StorySuggestionLifecycleState[normalized]
        except KeyError as exc:
            allowed = ", ".join(state.value for state in StorySuggestionLifecycleState)
            raise DraftingValidationError(f"status must be one of: {allowed}") from exc

    def _normalize_version(self, version: int | None) -> int | None:
        if version is None:
            return None
        if not isinstance(version, int):
            raise TypeError("version must be an integer")
        if version < 1:
            raise ValueError("version must be greater than or equal to 1")
        return version

    def _merge_unique_strings(self, *groups: Sequence[str]) -> tuple[str, ...]:
        merged: list[str] = []
        seen: set[str] = set()
        for group in groups:
            for value in group:
                normalized = self._normalize_text(value, field_name="value")
                if normalized in seen:
                    continue
                seen.add(normalized)
                merged.append(normalized)
        return tuple(merged)
