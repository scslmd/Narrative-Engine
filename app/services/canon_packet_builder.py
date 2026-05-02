from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonGenerationPacket,
    CanonGenerationRequest,
    CanonicalArcSnapshot,
    CanonicalCharacterSnapshot,
    CanonicalContinuityFindingSnapshot,
    CanonicalContinuityThreadSnapshot,
    CanonicalDraftingContextSnapshot,
    CanonicalRelationshipSnapshot,
    CanonicalWorldSnapshot,
    CanonPolicy,
    CanonScope,
    PromptBudgetSummary,
)
from app.services.projects import ProjectService
from app.utils.db_inserts import hash_id


class CanonPacketBuilder:
    def __init__(
        self,
        *,
        repository: StoryDevelopmentRepository,
        project_service: ProjectService,
    ) -> None:
        self._repository = repository
        self._project_service = project_service

    def build_packet(self, request: CanonGenerationRequest, target_project_id: str) -> CanonGenerationPacket:
        scope = request.canon_scope
        foundation = self._load_foundation_snapshot(scope.source_project_id)
        characters = self._load_character_snapshots(scope)
        relationships = self._load_relationship_snapshots(scope)
        world_bible = self._load_world_snapshots(scope)
        arcs = self._load_arc_snapshots(scope)
        continuity_threads, continuity_findings = self._load_continuity_snapshots(scope)
        drafting_packets = self._load_drafting_context_snapshots(scope.source_project_id, scope)
        mythos_entries = self._load_mythos_snapshots(scope)
        pattern_entries = self._load_pattern_snapshots(scope)
        canon_annotations = self._load_annotation_snapshots(scope)
        canon_policy = self._load_annotation_policy(scope.source_project_id, canon_annotations, request.canon_policy)

        packet_parts = {
            "foundation": foundation,
            "characters": [item.model_dump(mode="json") for item in characters],
            "relationships": [item.model_dump(mode="json") for item in relationships],
            "world_bible": [item.model_dump(mode="json") for item in world_bible],
            "arcs": [item.model_dump(mode="json") for item in arcs],
            "continuity_threads": [item.model_dump(mode="json") for item in continuity_threads],
            "continuity_findings": [item.model_dump(mode="json") for item in continuity_findings],
            "drafting_packets": [item.model_dump(mode="json") for item in drafting_packets],
            "mythos_entries": mythos_entries,
            "pattern_entries": pattern_entries,
            "canon_annotations": canon_annotations,
        }
        source_hashes = self._compute_source_hashes(packet_parts)
        scope_hash = sha256(
            json.dumps(scope.model_dump(mode="json"), ensure_ascii=True, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        brief_hash = sha256(request.generation_brief.encode("utf-8")).hexdigest()[:16]
        packet_id = hash_id(
            "canon-generation-packet",
            f"{request.source_project_id}:{target_project_id}:{getattr(request.mode, 'value', request.mode)}:{scope_hash}:{brief_hash}",
        )
        packet = CanonGenerationPacket(
            packet_id=packet_id,
            source_project_id=request.source_project_id,
            target_project_id=target_project_id,
            mode=request.mode,
            generation_brief=request.generation_brief,
            foundation_snapshot=foundation,
            characters=characters,
            relationships=relationships,
            world_bible=world_bible,
            arcs=arcs,
            continuity_threads=continuity_threads,
            continuity_findings=continuity_findings,
            drafting_context_packets=drafting_packets,
            mythos_entries=mythos_entries,
            pattern_entries=pattern_entries,
            canon_annotations=canon_annotations,
            canon_policy=canon_policy,
            prompt_budget_summary=PromptBudgetSummary(
                estimated_prompt_chars=0,
                target_max_chars=120_000,
                truncated_fields=[],
                fit_to_budget=True,
            ),
            source_hashes=source_hashes,
        )
        return self._fit_prompt_budget(packet, max_chars=120_000)

    def _load_foundation_snapshot(self, project_id: str) -> dict[str, object]:
        revisions = self._repository.list_foundation_revisions(project_id)
        if not revisions:
            return {}
        latest = revisions[-1]
        return {
            "project_id": latest.project_id,
            "premise": latest.premise,
            "logline": latest.logline,
            "thematic_spine": latest.thematic_spine,
            "emotional_promise": latest.emotional_promise,
            "tone_direction": latest.tone_direction,
            "target_audience": latest.target_audience,
            "narrative_constraints": latest.narrative_constraints,
            "complexity_level": latest.complexity_level,
            "success_definition": latest.success_definition,
        }

    def _load_character_snapshots(self, scope: CanonScope) -> list[CanonicalCharacterSnapshot]:
        records = self._repository.list_character_profiles(scope.source_project_id)
        selected = set(scope.character_ids)
        if scope.scope_mode != "full_project":
            records = [record for record in records if record.character_id in selected]
        records.sort(key=lambda record: record.display_name.lower())
        return [
            CanonicalCharacterSnapshot(
                character_id=record.character_id,
                display_name=record.display_name,
                role_in_story=record.role_in_story or "",
                continuity_facts=record.continuity_facts,
                voice_notes=record.voice_notes or "",
            )
            for record in records
        ]

    def _load_relationship_snapshots(self, scope: CanonScope) -> list[CanonicalRelationshipSnapshot]:
        records = self._repository.list_relationship_edges(scope.source_project_id)
        selected = set(scope.character_ids)
        if scope.scope_mode != "full_project" and selected:
            records = [
                record
                for record in records
                if record.source_character_id in selected and record.target_character_id in selected
            ]
        records.sort(key=lambda record: (record.source_character_id, record.target_character_id, record.edge_id))
        return [
            CanonicalRelationshipSnapshot(
                edge_id=record.edge_id,
                source_character_id=record.source_character_id,
                target_character_id=record.target_character_id,
                relation_kind=record.relation_kind,
                summary=record.summary,
            )
            for record in records
        ]

    def _load_world_snapshots(self, scope: CanonScope) -> list[CanonicalWorldSnapshot]:
        records = self._repository.list_world_bible_entries(scope.source_project_id)
        selected = {(item.entry_type, item.title) for item in scope.world_bible_refs}
        if scope.scope_mode != "full_project" and selected:
            records = [record for record in records if (record.entry_type, record.title) in selected]
        records.sort(key=lambda record: (record.entry_type.lower(), record.title.lower()))
        return [
            CanonicalWorldSnapshot(
                entry_type=record.entry_type,
                title=record.title,
                summary=record.summary or "",
                canonical_facts=record.canonical_facts,
            )
            for record in records
        ]

    def _load_arc_snapshots(self, scope: CanonScope) -> list[CanonicalArcSnapshot]:
        records = self._repository.list_arc_candidates(scope.source_project_id)
        selected = set(scope.arc_ids)
        if scope.scope_mode != "full_project" and selected:
            records = [record for record in records if record.arc_id in selected]
        records.sort(key=lambda record: record.name.lower())
        return [
            CanonicalArcSnapshot(
                arc_id=record.arc_id,
                name=record.name,
                summary=record.summary,
            )
            for record in records
        ]

    def _load_continuity_snapshots(
        self,
        scope: CanonScope,
    ) -> tuple[list[CanonicalContinuityThreadSnapshot], list[CanonicalContinuityFindingSnapshot]]:
        threads = self._repository.list_continuity_threads(scope.source_project_id)
        selected = set(scope.continuity_thread_ids)
        if scope.scope_mode != "full_project" and selected:
            threads = [thread for thread in threads if thread.thread_id in selected]
        threads.sort(key=lambda thread: thread.title.lower())
        thread_snapshots = [
            CanonicalContinuityThreadSnapshot(
                thread_id=thread.thread_id,
                title=thread.title,
                summary=thread.summary,
            )
            for thread in threads
        ]
        findings = self._repository.list_continuity_findings(scope.source_project_id)
        finding_snapshots = [
            CanonicalContinuityFindingSnapshot(
                finding_key=finding.finding_key,
                contradictions=finding.contradictions,
                unresolved_questions=finding.unresolved_questions,
            )
            for finding in findings
        ]
        return thread_snapshots, finding_snapshots

    def _load_drafting_context_snapshots(
        self,
        project_id: str,
        scope: CanonScope,
    ) -> list[CanonicalDraftingContextSnapshot]:
        packets = self._repository.list_drafting_context_packets(project_id)
        packets.sort(key=lambda packet: packet.packet_id)
        return [
            CanonicalDraftingContextSnapshot(
                packet_id=packet.packet_id,
                brief_id=packet.brief_id,
                character_anchors=packet.character_anchors,
                world_constraints=packet.world_constraints,
                prior_summaries=packet.prior_summaries,
            )
            for packet in packets
        ]

    def _compute_source_hashes(self, packet_parts: dict[str, Any]) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for key, value in packet_parts.items():
            normalized = json.dumps(value, ensure_ascii=True, sort_keys=True)
            hashes[key] = sha256(normalized.encode("utf-8")).hexdigest()
        return hashes

    def _load_mythos_snapshots(self, scope: CanonScope) -> list[dict[str, object]]:
        records = self._repository.list_mythos_entries(scope.source_project_id)
        selected_ids = set(scope.mythos_ids)
        if scope.scope_mode != "full_project" and selected_ids:
            records = [item for item in records if item.mythos_id in selected_ids]
        records.sort(key=lambda item: (item.entry_type.lower(), item.name.lower()))
        return [
            {
                **record.__dict__,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
            for record in records
        ]

    def _load_pattern_snapshots(self, scope: CanonScope) -> list[dict[str, object]]:
        records = self._repository.list_pattern_entries(scope.source_project_id)
        selected_ids = set(scope.pattern_ids)
        if scope.scope_mode != "full_project" and selected_ids:
            records = [item for item in records if item.pattern_id in selected_ids]
        records.sort(key=lambda item: (item.pattern_type.lower(), item.name.lower()))
        return [
            {
                **record.__dict__,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
            for record in records
        ]

    def _load_annotation_snapshots(self, scope: CanonScope) -> list[dict[str, object]]:
        records = self._repository.list_canon_annotations(scope.source_project_id)
        records.sort(key=lambda item: (item.target_kind, item.target_id, item.field_path, item.annotation_kind))
        return [
            {
                **record.__dict__,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
            for record in records
        ]

    def _load_annotation_policy(
        self,
        project_id: str,
        annotations: list[dict[str, object]],
        base_policy: CanonPolicy,
    ) -> CanonPolicy:
        policy = base_policy.model_copy(deep=True)
        if not annotations:
            return policy
        _ = project_id
        locked_character: set[str] = set(policy.locked_character_fields)
        locked_world: set[str] = set(policy.locked_world_fields)
        mutable_character: set[str] = set(policy.allowed_character_changes)
        mutable_world: set[str] = set(policy.allowed_world_changes)
        forbidden: set[str] = set(policy.forbidden_contradictions)
        for item in annotations:
            target_kind = str(item.get("target_kind", ""))
            field_path = str(item.get("field_path", ""))
            annotation_kind = str(item.get("annotation_kind", ""))
            note = str(item.get("note", "") or "")
            field_ref = f"{target_kind}.{field_path}".strip(".")
            if annotation_kind == "locked":
                if target_kind == "character":
                    locked_character.add(field_ref)
                if target_kind == "world_bible":
                    locked_world.add(field_ref)
            if annotation_kind == "mutable":
                if target_kind == "character":
                    mutable_character.add(field_ref)
                if target_kind == "world_bible":
                    mutable_world.add(field_ref)
            if annotation_kind == "forbidden_contradiction":
                forbidden.add(note or field_ref)
        return policy.model_copy(
            update={
                "locked_character_fields": sorted(locked_character),
                "locked_world_fields": sorted(locked_world),
                "allowed_character_changes": sorted(mutable_character),
                "allowed_world_changes": sorted(mutable_world),
                "forbidden_contradictions": sorted(forbidden),
            }
        )

    def _fit_prompt_budget(self, packet: CanonGenerationPacket, max_chars: int) -> CanonGenerationPacket:
        payload = packet.model_dump(mode="json")
        encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        if len(encoded) <= max_chars:
            return packet.model_copy(
                update={
                    "prompt_budget_summary": PromptBudgetSummary(
                        estimated_prompt_chars=len(encoded),
                        target_max_chars=max_chars,
                        truncated_fields=[],
                        fit_to_budget=True,
                    )
                }
            )
        trimmed = payload.copy()
        truncated_fields: list[str] = []
        if trimmed.get("drafting_context_packets"):
            trimmed["drafting_context_packets"] = []
            truncated_fields.append("drafting_context_packets")
        if len(json.dumps(trimmed, ensure_ascii=True, sort_keys=True)) > max_chars and trimmed.get("relationships"):
            trimmed["relationships"] = []
            truncated_fields.append("relationships")
        if len(json.dumps(trimmed, ensure_ascii=True, sort_keys=True)) > max_chars and trimmed.get("continuity_findings"):
            trimmed["continuity_findings"] = []
            truncated_fields.append("continuity_findings")
        updated = CanonGenerationPacket.model_validate(trimmed)
        final_encoded = json.dumps(updated.model_dump(mode="json"), ensure_ascii=True, sort_keys=True)
        return updated.model_copy(
            update={
                "prompt_budget_summary": PromptBudgetSummary(
                    estimated_prompt_chars=len(final_encoded),
                    target_max_chars=max_chars,
                    truncated_fields=truncated_fields,
                    fit_to_budget=len(final_encoded) <= max_chars,
                )
            }
        )
