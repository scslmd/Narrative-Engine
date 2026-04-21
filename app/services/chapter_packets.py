from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from app.persistence.story_development import (
    ChapterPacketRecord,
    StoryDevelopmentRepository,
)
from app.schemas import StoryArtifactLifecycleState


class ChapterPacketServiceError(ValueError):
    pass


class ChapterPacketNotFoundError(ChapterPacketServiceError):
    pass


class ChapterPacketValidationError(ChapterPacketServiceError):
    pass


@dataclass(frozen=True)
class ChapterPacketContext:
    included_reference_ids: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    scene_goals: tuple[str, ...] = ()


class ChapterPacketService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def register_packet(
        self,
        project_id: str,
        *,
        packet_id: str,
        chapter_id: str,
        included_reference_ids: Sequence[str] | None = None,
        constraints: Sequence[str] | None = None,
        scene_goals: Sequence[str] | None = None,
        status: str = StoryArtifactLifecycleState.DRAFT,
        created_at: datetime | None = None,
    ) -> ChapterPacketRecord:
        context = self._packet_context(
            included_reference_ids=included_reference_ids,
            constraints=constraints,
            scene_goals=scene_goals,
        )
        record = self.repository.upsert_chapter_packet(
            packet_id=self._normalize_text(packet_id, field_name="packet_id"),
            project_id=self._normalize_text(project_id, field_name="project_id"),
            chapter_id=self._normalize_text(chapter_id, field_name="chapter_id"),
            included_reference_ids=context.included_reference_ids,
            constraints=context.constraints,
            scene_goals=context.scene_goals,
            status=self._normalize_status(status),
            created_at=created_at,
        )
        return record

    def get_packet(self, packet_id: str) -> ChapterPacketRecord:
        record = self.repository.get_chapter_packet(packet_id)
        return record

    def list_packets(self, project_id: str) -> list[ChapterPacketRecord]:
        return self.repository.list_chapter_packets(
            self._normalize_text(project_id, field_name="project_id"),
        )

    def list_packets_by_chapter(
        self,
        project_id: str,
        chapter_id: str,
    ) -> list[ChapterPacketRecord]:
        all_packets = self.list_packets(project_id)
        normalized_chapter_id = self._normalize_text(chapter_id, field_name="chapter_id")
        return [
            pkt for pkt in all_packets
            if pkt.chapter_id == normalized_chapter_id
        ]

    def register_packet_as_lineage(
        self,
        *,
        step_record_service: object,
        packet_id: str,
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
        try:
            packet = self.get_packet(packet_id)
            produced = produced_at or datetime.now(timezone.utc)
            registered_at = datetime.now(timezone.utc)
            reference_ids = list(source_artifact_refs or [])
            content_hashes = list(source_content_hashes or [])
            packet_refs = self._build_packet_lineage_refs(packet, reference_ids)
            packet_hashes = self._build_packet_lineage_hashes(packet, content_hashes)
            lineage_id = step_record_service.create_lineage_record(
                logical_run_id=logical_run_id,
                run_id=run_id,
                run_kind=run_kind,
                attempt_number=attempt_number,
                step_name=step_name,
                project_id=project_id,
                artifact_role=artifact_role,
                artifact_kind="json",
                path=f"/data/projects/{project_id}/chapters/{packet_id}",
                content_hash=packet_id,
                status=StoryArtifactLifecycleState.CANONICAL,
                validation_state="validated",
                produced_at=produced,
                registered_at=registered_at,
                supersedes_artifact_lineage_id=None,
                source_artifact_refs=packet_refs,
                source_content_hashes=packet_hashes,
                output_of_step_record_id=output_of_step_record_id,
            )
            return lineage_id
        except Exception as exc:
            return None

    def _packet_context(
        self,
        *,
        included_reference_ids: Sequence[str] | None = None,
        constraints: Sequence[str] | None = None,
        scene_goals: Sequence[str] | None = None,
    ) -> ChapterPacketContext:
        return ChapterPacketContext(
            included_reference_ids=tuple(included_reference_ids or []),
            constraints=tuple(constraints or []),
            scene_goals=tuple(scene_goals or []),
        )

    def _normalize_text(self, value: str, *, field_name: str) -> str:
        sanitized = value.strip()
        if not sanitized:
            raise ChapterPacketValidationError(
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

    def _build_packet_lineage_refs(
        self,
        record: ChapterPacketRecord,
        existing_refs: list[str],
    ) -> list[str]:
        refs = list(existing_refs)
        for ref_id in record.included_reference_ids:
            if ref_id not in refs:
                refs.append(ref_id)
        return refs

    def _build_packet_lineage_hashes(
        self,
        record: ChapterPacketRecord,
        existing_hashes: list[str],
    ) -> list[str]:
        packet_hash = _stable_hash_text(record.packet_id)
        hashes = list(existing_hashes)
        if packet_hash not in hashes:
            hashes.append(packet_hash)
        return hashes


def _stable_hash_text(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
