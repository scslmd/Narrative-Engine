from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from app.persistence.story_development import (
    SequencePlanRecord,
    StoryDevelopmentRepository,
)
from app.schemas import StoryArtifactLifecycleState


class SequencePlanServiceError(ValueError):
    pass


class SequencePlanNotFoundError(SequencePlanServiceError):
    pass


class SequencePlanValidationError(SequencePlanServiceError):
    pass


@dataclass(frozen=True)
class SequencePlanContext:
    beat_ids: tuple[str, ...] = ()
    chapter_ids: tuple[str, ...] = ()


class SequencePlanService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def register_plan(
        self,
        project_id: str,
        *,
        sequence_id: str,
        title: str,
        summary: str | None = None,
        beat_ids: Sequence[str] | None = None,
        chapter_ids: Sequence[str] | None = None,
        status: str = StoryArtifactLifecycleState.DRAFT,
        position: int | None = None,
        created_at: datetime | None = None,
    ) -> SequencePlanRecord:
        context = self._plan_context(
            beat_ids=beat_ids,
            chapter_ids=chapter_ids,
        )
        record = self.repository.upsert_sequence_plan(
            sequence_id=self._normalize_text(sequence_id, field_name="sequence_id"),
            project_id=self._normalize_text(project_id, field_name="project_id"),
            title=self._normalize_text(title, field_name="title"),
            summary=self._normalize_optional_text(summary, field_name="summary"),
            beat_ids=context.beat_ids,
            chapter_ids=context.chapter_ids,
            status=self._normalize_status(status),
            position=position,
            created_at=created_at,
        )
        return record

    def get_plan(self, sequence_id: str) -> SequencePlanRecord:
        record = self.repository.get_sequence_plan(sequence_id)
        if record is None:
            raise SequencePlanNotFoundError(sequence_id)
        return record

    def list_plans(self, project_id: str) -> list[SequencePlanRecord]:
        return self.repository.list_sequence_plans(
            self._normalize_text(project_id, field_name="project_id"),
        )

    def update_plan_status(
        self,
        sequence_id: str,
        status: str,
    ) -> SequencePlanRecord:
        existing = self.get_plan(sequence_id)
        return self.repository.upsert_sequence_plan(
            sequence_id=existing.sequence_id,
            project_id=existing.project_id,
            title=existing.title,
            summary=existing.summary,
            beat_ids=existing.beat_ids,
            chapter_ids=existing.chapter_ids,
            status=self._normalize_status(status),
            position=existing.position,
        )

    def _plan_context(
        self,
        *,
        beat_ids: Sequence[str] | None = None,
        chapter_ids: Sequence[str] | None = None,
    ) -> SequencePlanContext:
        return SequencePlanContext(
            beat_ids=tuple(beat_ids or []),
            chapter_ids=tuple(chapter_ids or []),
        )

    def _normalize_text(self, value: str, *, field_name: str) -> str:
        sanitized = value.strip()
        if not sanitized:
            raise SequencePlanValidationError(
                f"{field_name} must not be empty"
            )
        return sanitized

    def _normalize_optional_text(
        self,
        value: str | None,
        *,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None
        sanitized = value.strip()
        if not sanitized:
            return None
        return sanitized

    def _normalize_status(self, status: str) -> str:
        if isinstance(status, StoryArtifactLifecycleState):
            return status.value
        return status

    def register_plan_as_lineage(
        self,
        *,
        step_record_service: object,
        sequence_id: str,
        project_id: str,
        step_name: str,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int,
        artifact_role: str,
        produced_at: datetime | None = None,
        source_artifact_refs: list[str] | None = None,
        source_content_hashes: list[str] | None = None,
        output_of_step_record_id: int = 0,
    ) -> int | None:
        if step_record_service is None:
            return None
        produced = produced_at or datetime.now(timezone.utc)
        registered_at = datetime.now(timezone.utc)
        reference_ids = list(source_artifact_refs or [])
        content_hashes = list(source_content_hashes or [])
        try:
            plan = self.get_plan(sequence_id)
            refs = list(reference_ids)
            for beat_id in plan.beat_ids:
                if beat_id not in refs:
                    refs.append(beat_id)
            for chapter_id in plan.chapter_ids:
                if chapter_id not in refs:
                    refs.append(chapter_id)
            plan_hash = _stable_hash_text(plan.sequence_id)
            hashes = list(content_hashes)
            if plan_hash not in hashes:
                hashes.append(plan_hash)
            lineage_id = step_record_service.create_lineage_record(
                logical_run_id=logical_run_id,
                run_id=run_id,
                run_kind=run_kind,
                attempt_number=attempt_number,
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                artifact_kind="json",
                path=f"/data/projects/{project_id}/sequences/{sequence_id}",
                content_hash=sequence_id,
                status=StoryArtifactLifecycleState.CANONICAL,
                validation_state="validated",
                produced_at=produced,
                registered_at=registered_at,
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=refs,
                source_content_hashes=hashes,
                output_of_step_record_id=output_of_step_record_id,
            )
            return lineage_id
        except Exception:
            return None


def _stable_hash_text(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
