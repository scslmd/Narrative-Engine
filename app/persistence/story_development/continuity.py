from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import (
    ContinuityFindingRecord, ContinuityStateRecord, ContinuityThreadRecord,
    DraftBriefRecord, DraftingContextPacketRecord,
)
from .converters import (
    _continuity_thread_row_to_record, _continuity_state_row_to_record,
    _continuity_finding_row_to_record, _draft_brief_row_to_record,
    _drafting_context_packet_row_to_record,
)

from ..sqlite import connect


class _ContinuityThreadMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_continuity_thread(
        self,
        *,
        thread_id: str,
        project_id: str,
        title: str,
        summary: str,
        status: str = "active",
        chapter_ids: list[str] | None = None,
        character_ids: list[str] | None = None,
        evidence: list[str] | None = None,
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ContinuityThreadRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO continuity_threads (
                    thread_id, project_id, title, summary, status, chapter_ids_json, character_ids_json,
                    evidence_json, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    summary = excluded.summary,
                    status = excluded.status,
                    chapter_ids_json = excluded.chapter_ids_json,
                    character_ids_json = excluded.character_ids_json,
                    evidence_json = excluded.evidence_json,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    thread_id,
                    project_id,
                    title,
                    summary,
                    status,
                    _json_list(chapter_ids),
                    _json_list(character_ids),
                    _json_list(evidence),
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_continuity_thread(thread_id)



    def get_continuity_thread(self, thread_id: str) -> ContinuityThreadRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM continuity_threads
                WHERE thread_id = ?
                """,
                (thread_id,),
            ).fetchone()
        if row is None:
            raise KeyError(thread_id)
        return _continuity_thread_row_to_record(row)



    def list_continuity_threads(self, project_id: str) -> list[ContinuityThreadRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM continuity_threads
                WHERE project_id = ?
                ORDER BY thread_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_continuity_thread_row_to_record(row) for row in rows]


class _ContinuityStateMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_continuity_state(
        self,
        *,
        state_id: str,
        project_id: str,
        chapter_id: str,
        summary: str,
        active_threads: list[str] | None = None,
        resolved_threads: list[str] | None = None,
        character_states: dict[str, str] | None = None,
        world_facts: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        contradictions: list[str] | None = None,
        status: str = "complete",
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ContinuityStateRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO continuity_states (
                    state_id, project_id, chapter_id, summary, active_threads_json, resolved_threads_json,
                    character_states_json, world_facts_json, unresolved_questions_json, contradictions_json,
                    status, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(state_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    summary = excluded.summary,
                    active_threads_json = excluded.active_threads_json,
                    resolved_threads_json = excluded.resolved_threads_json,
                    character_states_json = excluded.character_states_json,
                    world_facts_json = excluded.world_facts_json,
                    unresolved_questions_json = excluded.unresolved_questions_json,
                    contradictions_json = excluded.contradictions_json,
                    status = excluded.status,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    state_id,
                    project_id,
                    chapter_id,
                    summary,
                    _json_list(active_threads),
                    _json_list(resolved_threads),
                    json.dumps(dict(character_states or {}), ensure_ascii=True, sort_keys=True),
                    _json_list(world_facts),
                    _json_list(unresolved_questions),
                    _json_list(contradictions),
                    status,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_continuity_state(state_id)



    def get_continuity_state(self, state_id: str) -> ContinuityStateRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM continuity_states
                WHERE state_id = ?
                """,
                (state_id,),
            ).fetchone()
        if row is None:
            raise KeyError(state_id)
        return _continuity_state_row_to_record(row)



    def list_continuity_states(self, project_id: str) -> list[ContinuityStateRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM continuity_states
                WHERE project_id = ?
                ORDER BY chapter_id ASC, state_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_continuity_state_row_to_record(row) for row in rows]


class _ContinuityFindingMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_continuity_finding(
        self,
        *,
        project_id: str,
        finding_key: str | None = None,
        overall_confidence: float = 0.0,
        status: str = "complete",
        contradictions: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        provenance_note: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ContinuityFindingRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            if finding_key is not None:
                existing = connection.execute(
                    """
                    SELECT finding_id
                    FROM continuity_findings
                    WHERE project_id = ? AND finding_key = ?
                    """,
                    (project_id, finding_key),
                ).fetchone()
                if existing is not None:
                    connection.execute(
                        """
                        UPDATE continuity_findings
                        SET overall_confidence = ?,
                            status = ?,
                            contradictions_json = ?,
                            unresolved_questions_json = ?,
                            provenance_note = ?,
                            updated_at = ?
                        WHERE finding_id = ?
                        """,
                        (
                            overall_confidence,
                            status,
                            _json_list(contradictions),
                            _json_list(unresolved_questions),
                            provenance_note,
                            updated.isoformat(),
                            int(existing["finding_id"]),
                        ),
                    )
                    connection.commit()
                    return self.get_continuity_finding(int(existing["finding_id"]))

            cursor = connection.execute(
                """
                INSERT INTO continuity_findings (
                    project_id, finding_key, overall_confidence, status, contradictions_json, unresolved_questions_json,
                    provenance_note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    finding_key,
                    overall_confidence,
                    status,
                    _json_list(contradictions),
                    _json_list(unresolved_questions),
                    provenance_note,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_continuity_finding(int(cursor.lastrowid))



    def get_continuity_finding(self, finding_id: int) -> ContinuityFindingRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM continuity_findings
                WHERE finding_id = ?
                """,
                (finding_id,),
            ).fetchone()
        if row is None:
            raise KeyError(finding_id)
        return _continuity_finding_row_to_record(row)



    def list_continuity_findings(self, project_id: str) -> list[ContinuityFindingRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM continuity_findings
                WHERE project_id = ?
                ORDER BY created_at ASC, finding_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_continuity_finding_row_to_record(row) for row in rows]


class _DraftBriefMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_draft_brief(
        self,
        *,
        brief_id: str,
        project_id: str,
        chapter_id: str,
        objective: str,
        emotional_turn: str,
        continuity_obligations: list[str] | None = None,
        required_callbacks: list[str] | None = None,
        forbidden_contradictions: list[str] | None = None,
        voice_guidance: str = "",
        status: str = "draft",
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> DraftBriefRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO draft_briefs (
                    brief_id, project_id, chapter_id, objective, emotional_turn, continuity_obligations_json,
                    required_callbacks_json, forbidden_contradictions_json, voice_guidance, status,
                    provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(brief_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    objective = excluded.objective,
                    emotional_turn = excluded.emotional_turn,
                    continuity_obligations_json = excluded.continuity_obligations_json,
                    required_callbacks_json = excluded.required_callbacks_json,
                    forbidden_contradictions_json = excluded.forbidden_contradictions_json,
                    voice_guidance = excluded.voice_guidance,
                    status = excluded.status,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    brief_id,
                    project_id,
                    chapter_id,
                    objective,
                    emotional_turn,
                    _json_list(continuity_obligations),
                    _json_list(required_callbacks),
                    _json_list(forbidden_contradictions),
                    voice_guidance,
                    status,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_draft_brief(brief_id)



    def get_draft_brief(self, brief_id: str) -> DraftBriefRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM draft_briefs
                WHERE brief_id = ?
                """,
                (brief_id,),
            ).fetchone()
        if row is None:
            raise KeyError(brief_id)
        return _draft_brief_row_to_record(row)



    def list_draft_briefs(self, project_id: str) -> list[DraftBriefRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM draft_briefs
                WHERE project_id = ?
                ORDER BY chapter_id ASC, brief_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_draft_brief_row_to_record(row) for row in rows]


class _DraftingContextMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_drafting_context_packet(
        self,
        *,
        packet_id: str,
        project_id: str,
        brief_id: str,
        character_anchors: list[str] | None = None,
        world_constraints: list[str] | None = None,
        prior_summaries: list[str] | None = None,
        pattern_guidance: dict[str, Any] | None = None,
        status: str = "draft",
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> DraftingContextPacketRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO drafting_context_packets (
                    packet_id, project_id, brief_id, character_anchors_json, world_constraints_json,
                    prior_summaries_json, pattern_guidance_json, status, provenance_note, confidence_score,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    brief_id = excluded.brief_id,
                    character_anchors_json = excluded.character_anchors_json,
                    world_constraints_json = excluded.world_constraints_json,
                    prior_summaries_json = excluded.prior_summaries_json,
                    pattern_guidance_json = excluded.pattern_guidance_json,
                    status = excluded.status,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    packet_id,
                    project_id,
                    brief_id,
                    _json_list(character_anchors),
                    _json_list(world_constraints),
                    _json_list(prior_summaries),
                    json.dumps(dict(pattern_guidance or {}), ensure_ascii=True, sort_keys=True),
                    status,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_drafting_context_packet(packet_id)



    def get_drafting_context_packet(self, packet_id: str) -> DraftingContextPacketRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM drafting_context_packets
                WHERE packet_id = ?
                """,
                (packet_id,),
            ).fetchone()
        if row is None:
            raise KeyError(packet_id)
        return _drafting_context_packet_row_to_record(row)



    def list_drafting_context_packets(self, project_id: str) -> list[DraftingContextPacketRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM drafting_context_packets
                WHERE project_id = ?
                ORDER BY brief_id ASC, packet_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_drafting_context_packet_row_to_record(row) for row in rows]
