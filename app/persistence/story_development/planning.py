from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import (
    BeatPlanRecord, ChapterPacketRecord, ChapterPlanRecord,
    PlanningDependencyRecord, ScenePlanRecord, SequencePlanRecord,
)
from .converters import (
    _beat_plan_row_to_record, _sequence_plan_row_to_record,
    _chapter_plan_row_to_record, _scene_plan_row_to_record,
    _chapter_packet_row_to_record, _planning_dependency_row_to_record,
)

from ..sqlite import connect


class _PlanningBeatPlanMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_beat_plan(
        self,
        *,
        beat_id: str,
        project_id: str,
        objective: str,
        conflict: str,
        stakes: str,
        dependency_ids: list[str] | None = None,
        arc_stage: str,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BeatPlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO beat_plans (
                    beat_id, project_id, objective, conflict, stakes, dependency_ids_json, arc_stage,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(beat_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    objective = excluded.objective,
                    conflict = excluded.conflict,
                    stakes = excluded.stakes,
                    dependency_ids_json = excluded.dependency_ids_json,
                    arc_stage = excluded.arc_stage,
                    active_character_ids_json = excluded.active_character_ids_json,
                    continuity_requirements_json = excluded.continuity_requirements_json,
                    unresolved_questions_json = excluded.unresolved_questions_json,
                    status = excluded.status,
                    position = excluded.position,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    beat_id,
                    project_id,
                    objective,
                    conflict,
                    stakes,
                    _json_list(dependency_ids),
                    arc_stage,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_beat_plan(beat_id)



    def get_beat_plan(self, beat_id: str) -> BeatPlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM beat_plans
                WHERE beat_id = ?
                """,
                (beat_id,),
            ).fetchone()
        if row is None:
            raise KeyError(beat_id)
        return _beat_plan_row_to_record(row)



    def list_beat_plans(self, project_id: str) -> list[BeatPlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM beat_plans
                WHERE project_id = ?
                ORDER BY position ASC, beat_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_beat_plan_row_to_record(row) for row in rows]


class _PlanningSequencePlanMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_sequence_plan(
        self,
        *,
        sequence_id: str,
        project_id: str,
        title: str,
        summary: str,
        beat_ids: list[str] | None = None,
        chapter_ids: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> SequencePlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO sequence_plans (
                    sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json,
                    status, position, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sequence_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    title = excluded.title,
                    summary = excluded.summary,
                    beat_ids_json = excluded.beat_ids_json,
                    chapter_ids_json = excluded.chapter_ids_json,
                    status = excluded.status,
                    position = excluded.position,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    sequence_id,
                    project_id,
                    title,
                    summary,
                    _json_list(beat_ids),
                    _json_list(chapter_ids),
                    status,
                    position,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_sequence_plan(sequence_id)



    def get_sequence_plan(self, sequence_id: str) -> SequencePlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sequence_plans
                WHERE sequence_id = ?
                """,
                (sequence_id,),
            ).fetchone()
        if row is None:
            raise KeyError(sequence_id)
        return _sequence_plan_row_to_record(row)



    def list_sequence_plans(self, project_id: str) -> list[SequencePlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sequence_plans
                WHERE project_id = ?
                ORDER BY position ASC, sequence_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_sequence_plan_row_to_record(row) for row in rows]


class _PlanningChapterPlanMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_chapter_plan(
        self,
        *,
        chapter_id: str,
        project_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        sequence_id: str | None = None,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        target_word_count: int | None = None,
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ChapterPlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO chapter_plans (
                    chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, provenance_note, confidence_score, created_at, updated_at, target_word_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chapter_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    sequence_id = excluded.sequence_id,
                    title = excluded.title,
                    summary = excluded.summary,
                    objective = excluded.objective,
                    conflict = excluded.conflict,
                    stakes = excluded.stakes,
                    active_character_ids_json = excluded.active_character_ids_json,
                    continuity_requirements_json = excluded.continuity_requirements_json,
                    unresolved_questions_json = excluded.unresolved_questions_json,
                    status = excluded.status,
                    position = excluded.position,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at,
                    target_word_count = excluded.target_word_count
                """,
                (
                    chapter_id,
                    project_id,
                    sequence_id,
                    title,
                    summary,
                    objective,
                    conflict,
                    stakes,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                    target_word_count,
                ),
            )
            connection.commit()
        return self.get_chapter_plan(chapter_id)



    def get_chapter_plan(self, chapter_id: str) -> ChapterPlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM chapter_plans
                WHERE chapter_id = ?
                """,
                (chapter_id,),
            ).fetchone()
        if row is None:
            raise KeyError(chapter_id)
        return _chapter_plan_row_to_record(row)



    def list_chapter_plans(self, project_id: str) -> list[ChapterPlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM chapter_plans
                WHERE project_id = ?
                ORDER BY position ASC, chapter_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chapter_plan_row_to_record(row) for row in rows]


class _PlanningScenePlanMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_scene_plan(
        self,
        *,
        scene_id: str,
        project_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        chapter_id: str | None = None,
        active_character_ids: list[str] | None = None,
        continuity_requirements: list[str] | None = None,
        unresolved_questions: list[str] | None = None,
        status: str = "draft",
        position: int = 0,
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ScenePlanRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO scene_plans (
                    scene_id, project_id, chapter_id, title, summary, objective, conflict, stakes,
                    active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
                    status, position, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scene_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    title = excluded.title,
                    summary = excluded.summary,
                    objective = excluded.objective,
                    conflict = excluded.conflict,
                    stakes = excluded.stakes,
                    active_character_ids_json = excluded.active_character_ids_json,
                    continuity_requirements_json = excluded.continuity_requirements_json,
                    unresolved_questions_json = excluded.unresolved_questions_json,
                    status = excluded.status,
                    position = excluded.position,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    scene_id,
                    project_id,
                    chapter_id,
                    title,
                    summary,
                    objective,
                    conflict,
                    stakes,
                    _json_list(active_character_ids),
                    _json_list(continuity_requirements),
                    _json_list(unresolved_questions),
                    status,
                    position,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_scene_plan(scene_id)



    def get_scene_plan(self, scene_id: str) -> ScenePlanRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM scene_plans
                WHERE scene_id = ?
                """,
                (scene_id,),
            ).fetchone()
        if row is None:
            raise KeyError(scene_id)
        return _scene_plan_row_to_record(row)



    def list_scene_plans(self, project_id: str) -> list[ScenePlanRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM scene_plans
                WHERE project_id = ?
                ORDER BY position ASC, scene_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_scene_plan_row_to_record(row) for row in rows]


class _PlanningChapterPacketMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_chapter_packet(
        self,
        *,
        packet_id: str,
        project_id: str,
        chapter_id: str,
        included_reference_ids: list[str] | None = None,
        constraints: list[str] | None = None,
        scene_goals: list[str] | None = None,
        status: str = "draft",
        provenance_note: str | None = None,
        confidence_score: float = 0.0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ChapterPacketRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO chapter_packets (
                    packet_id, project_id, chapter_id, included_reference_ids_json, constraints_json,
                    scene_goals_json, status, provenance_note, confidence_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(packet_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    chapter_id = excluded.chapter_id,
                    included_reference_ids_json = excluded.included_reference_ids_json,
                    constraints_json = excluded.constraints_json,
                    scene_goals_json = excluded.scene_goals_json,
                    status = excluded.status,
                    provenance_note = excluded.provenance_note,
                    confidence_score = excluded.confidence_score,
                    updated_at = excluded.updated_at
                """,
                (
                    packet_id,
                    project_id,
                    chapter_id,
                    _json_list(included_reference_ids),
                    _json_list(constraints),
                    _json_list(scene_goals),
                    status,
                    provenance_note,
                    confidence_score,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_chapter_packet(packet_id)



    def get_chapter_packet(self, packet_id: str) -> ChapterPacketRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM chapter_packets
                WHERE packet_id = ?
                """,
                (packet_id,),
            ).fetchone()
        if row is None:
            raise KeyError(packet_id)
        return _chapter_packet_row_to_record(row)



    def list_chapter_packets(self, project_id: str) -> list[ChapterPacketRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM chapter_packets
                WHERE project_id = ?
                ORDER BY chapter_id ASC, packet_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chapter_packet_row_to_record(row) for row in rows]


class _PlanningDependencyMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_planning_dependency(
        self,
        *,
        dependency_id: str,
        project_id: str,
        upstream_id: str,
        downstream_id: str,
        dependency_kind: str,
        reason: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> PlanningDependencyRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO planning_dependencies (
                    dependency_id, project_id, upstream_id, downstream_id, dependency_kind, reason,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dependency_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    upstream_id = excluded.upstream_id,
                    downstream_id = excluded.downstream_id,
                    dependency_kind = excluded.dependency_kind,
                    reason = excluded.reason,
                    updated_at = excluded.updated_at
                """,
                (
                    dependency_id,
                    project_id,
                    upstream_id,
                    downstream_id,
                    dependency_kind,
                    reason,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_planning_dependency(dependency_id)



    def get_planning_dependency(self, dependency_id: str) -> PlanningDependencyRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM planning_dependencies
                WHERE dependency_id = ?
                """,
                (dependency_id,),
            ).fetchone()
        if row is None:
            raise KeyError(dependency_id)
        return _planning_dependency_row_to_record(row)



    def list_planning_dependencies(self, project_id: str) -> list[PlanningDependencyRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM planning_dependencies
                WHERE project_id = ?
                ORDER BY dependency_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_planning_dependency_row_to_record(row) for row in rows]
