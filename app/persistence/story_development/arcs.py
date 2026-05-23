from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping, Sequence
from .shared_utils import (
    json_list as _json_list,
    json_object as _json_object,
    json_objects as _json_objects,
    now as _now,
)
from . import (
    ArcCandidateRecord,
    ArcComparisonCandidateRecord,
    ArcComparisonRecord,
    ArcSelectionRecord,
    ArcStageMapRecord,
)
from .converters import (
    _arc_candidate_record_from_mapping,
    _arc_candidate_record_to_mapping,
    _arc_comparison_candidate_record_from_mapping,
    _arc_comparison_candidate_record_to_mapping,
    _arc_candidate_row_to_record, _arc_comparison_row_to_record,
    _arc_selection_row_to_record, _arc_stage_map_row_to_record,
    _coerce_arc_candidate, _coerce_arc_comparison_candidate, _coerce_arc_stage_map,
    _normalize_text_list, _rank_arc_comparison_candidates,
    _unique_arc_candidate_records, _unique_arc_comparison_ranked_candidates,
)
from app.schemas.story_development import ArcCandidate, ArcStageMap

from ..sqlite import connect


class _ArcMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_arc_candidate(
        self,
        *,
        project_id: str,
        arc_id: str,
        name: str,
        summary: str,
        stage_map_notes: list[str] | None = None,
        fit_notes: list[str] | None = None,
        tags: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcCandidateRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_candidates (
                    arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(arc_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    name = excluded.name,
                    summary = excluded.summary,
                    stage_map_notes_json = excluded.stage_map_notes_json,
                    fit_notes_json = excluded.fit_notes_json,
                    tags_json = excluded.tags_json,
                    updated_at = excluded.updated_at
                """,
                (
                    arc_id,
                    project_id,
                    name,
                    summary,
                    _json_list(stage_map_notes),
                    _json_list(fit_notes),
                    _json_list(tags),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_candidate(project_id, arc_id=arc_id)



    def get_arc_candidate(self, project_id: str, *, arc_id: str) -> ArcCandidateRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json,
                       created_at, updated_at
                FROM arc_candidates
                WHERE project_id = ? AND arc_id = ?
                """,
                (project_id, arc_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, arc_id))
        return _arc_candidate_row_to_record(row)



    def list_arc_candidates(self, project_id: str) -> list[ArcCandidateRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json,
                       created_at, updated_at
                FROM arc_candidates
                WHERE project_id = ?
                ORDER BY name COLLATE NOCASE, arc_id
                """,
                (project_id,),
            ).fetchall()
        return [_arc_candidate_row_to_record(row) for row in rows]



    def upsert_arc_comparison(
        self,
        *,
        project_id: str,
        comparison_id: str,
        candidates: Sequence[ArcCandidate | ArcCandidateRecord | Mapping[str, Any]] | None = None,
        ranked_candidates: Sequence[ArcComparisonCandidateRecord | Mapping[str, Any]] | None = None,
        review_notes: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcComparisonRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        if ranked_candidates is None:
            if candidates is None:
                raise ValueError("candidates or ranked_candidates is required")
            candidate_records = [
                self._persist_arc_candidate(project_id, candidate, created_at=now, updated_at=updated)
                for candidate in candidates
            ]
            unique_candidates = _unique_arc_candidate_records(candidate_records)
            if len(unique_candidates) < 2:
                raise ValueError("At least two arc candidates are required.")
            candidate_records = unique_candidates
            ranked_candidate_records = _rank_arc_comparison_candidates(unique_candidates)
        else:
            ranked_candidate_records = [
                _coerce_arc_comparison_candidate(project_id, item)
                for item in ranked_candidates
            ]
            ranked_candidate_records = _unique_arc_comparison_ranked_candidates(ranked_candidate_records)
            if len(ranked_candidate_records) < 2:
                raise ValueError("At least two arc candidates are required.")
            candidate_records = [ranked.candidate for ranked in ranked_candidate_records]

        candidate_ids = [candidate.arc_id for candidate in candidate_records]
        review_notes_payload = _json_list(list(review_notes))
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_comparisons (
                    comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                    review_notes_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comparison_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    candidate_ids_json = excluded.candidate_ids_json,
                    candidate_set_json = excluded.candidate_set_json,
                    ranked_candidates_json = excluded.ranked_candidates_json,
                    review_notes_json = excluded.review_notes_json,
                    updated_at = excluded.updated_at
                """,
                (
                    comparison_id,
                    project_id,
                    _json_list(candidate_ids),
                    _json_objects([_arc_candidate_record_to_mapping(candidate) for candidate in candidate_records]),
                    _json_objects([_arc_comparison_candidate_record_to_mapping(record) for record in ranked_candidate_records]),
                    review_notes_payload,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_comparison(project_id, comparison_id=comparison_id)



    def get_arc_comparison(self, project_id: str, *, comparison_id: str) -> ArcComparisonRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                       review_notes_json, created_at, updated_at
                FROM arc_comparisons
                WHERE project_id = ? AND comparison_id = ?
                """,
                (project_id, comparison_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, comparison_id))
        return _arc_comparison_row_to_record(row)



    def list_arc_comparisons(self, project_id: str) -> list[ArcComparisonRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                       review_notes_json, created_at, updated_at
                FROM arc_comparisons
                WHERE project_id = ?
                ORDER BY created_at ASC, comparison_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_arc_comparison_row_to_record(row) for row in rows]



    def upsert_arc_stage_map(
        self,
        *,
        project_id: str,
        arc_id: str,
        stage_kinds: list[str] | None = None,
        notes: str | None = None,
        arc_stage_map_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcStageMapRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_arc_stage_map_id = arc_stage_map_id or f"{project_id}:{arc_id}:stage-map"
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_stage_maps (
                    arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, arc_id) DO UPDATE SET
                    arc_stage_map_id = excluded.arc_stage_map_id,
                    stage_kinds_json = excluded.stage_kinds_json,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized_arc_stage_map_id,
                    project_id,
                    arc_id,
                    _json_list(stage_kinds),
                    notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_arc_stage_map(project_id, arc_id=arc_id)



    def get_arc_stage_map(self, project_id: str, *, arc_id: str) -> ArcStageMapRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                FROM arc_stage_maps
                WHERE project_id = ? AND arc_id = ?
                """,
                (project_id, arc_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, arc_id))
        return _arc_stage_map_row_to_record(row)



    def list_arc_stage_maps(self, project_id: str) -> list[ArcStageMapRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT arc_stage_map_id, project_id, arc_id, stage_kinds_json, notes, created_at, updated_at
                FROM arc_stage_maps
                WHERE project_id = ?
                ORDER BY arc_id COLLATE NOCASE
                """,
                (project_id,),
            ).fetchall()
        return [_arc_stage_map_row_to_record(row) for row in rows]



    def upsert_arc_selection(
        self,
        *,
        project_id: str,
        selection_id: str,
        selected_arc: ArcCandidate | ArcCandidateRecord | Mapping[str, Any],
        rejected_arc_ids: list[str] | None = None,
        comparison_notes: list[str] | None = None,
        comparison_inputs: Sequence[ArcCandidate | ArcCandidateRecord | Mapping[str, Any]] | None = None,
        comparison_record_ids: Sequence[str] | None = None,
        stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> ArcSelectionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        selected_record = self._persist_arc_candidate(project_id, selected_arc, created_at=now, updated_at=updated)
        comparison_records = [
            self._persist_arc_candidate(project_id, candidate, created_at=now, updated_at=updated)
            for candidate in comparison_inputs or []
        ]
        linked_comparison_ids = _normalize_text_list(list(comparison_record_ids or []), field_name="comparison_record_ids")
        if not linked_comparison_ids and len(comparison_records) >= 2:
            auto_comparison_id = f"{selection_id}:comparison:001"
            auto_comparison = self.upsert_arc_comparison(
                project_id=project_id,
                comparison_id=auto_comparison_id,
                candidates=comparison_records,
                review_notes=comparison_notes,
                created_at=now,
                updated_at=updated,
            )
            linked_comparison_ids = [auto_comparison.comparison_id]
        for comparison_id in linked_comparison_ids:
            self.get_arc_comparison(project_id, comparison_id=comparison_id)
        if stage_map is not None:
            normalized_stage_map = _coerce_arc_stage_map(project_id, stage_map)
            if normalized_stage_map.arc_id != selected_record.arc_id:
                raise ValueError("stage_map.arc_id must match the selected arc")
        selected_stage_map = self._persist_arc_stage_map(project_id, stage_map, created_at=now, updated_at=updated)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO arc_selections (
                    selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                    comparison_notes_json, stage_map_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(selection_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    selected_arc_id = excluded.selected_arc_id,
                    selected_arc_json = excluded.selected_arc_json,
                    rejected_candidate_ids_json = excluded.rejected_candidate_ids_json,
                    comparison_notes_json = excluded.comparison_notes_json,
                    stage_map_id = excluded.stage_map_id,
                    updated_at = excluded.updated_at
                """,
                (
                    selection_id,
                    project_id,
                    selected_record.arc_id,
                    _json_object(_arc_candidate_record_to_mapping(selected_record)),
                    _json_list(rejected_arc_ids),
                    _json_list(comparison_notes),
                    selected_stage_map.arc_stage_map_id if selected_stage_map is not None else None,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        self._replace_arc_selection_comparison_links(
            selection_id=selection_id,
            project_id=project_id,
            comparison_record_ids=linked_comparison_ids,
            created_at=now,
            updated_at=updated,
        )
        return self.get_arc_selection(project_id, selection_id=selection_id)



    def get_arc_selection(self, project_id: str, *, selection_id: str) -> ArcSelectionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                       comparison_notes_json, stage_map_id, created_at, updated_at
                FROM arc_selections
                WHERE project_id = ? AND selection_id = ?
                """,
                (project_id, selection_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, selection_id))
        return _arc_selection_row_to_record(row, repository=self)



    def list_arc_selections(self, project_id: str) -> list[ArcSelectionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                       comparison_notes_json, stage_map_id, created_at, updated_at
                FROM arc_selections
                WHERE project_id = ?
                ORDER BY created_at ASC, selection_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_arc_selection_row_to_record(row, repository=self) for row in rows]



    def delete_arc_selection(self, project_id: str, *, selection_id: str) -> None:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT selection_id FROM arc_selections WHERE project_id = ? AND selection_id = ?",
                (project_id, selection_id),
            ).fetchone()
            if row is None:
                raise KeyError((project_id, selection_id))
            connection.execute(
                "DELETE FROM arc_selection_comparisons WHERE selection_id = ?",
                (selection_id,),
            )
            connection.execute(
                "DELETE FROM arc_selections WHERE project_id = ? AND selection_id = ?",
                (project_id, selection_id),
            )
            connection.commit()



    def update_arc_selection_notes(self, project_id: str, *, selection_id: str, comparison_notes: list[str]) -> ArcSelectionRecord:
        updated = _now()
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT selection_id FROM arc_selections WHERE project_id = ? AND selection_id = ?",
                (project_id, selection_id),
            ).fetchone()
            if row is None:
                raise KeyError((project_id, selection_id))
            connection.execute(
                "UPDATE arc_selections SET comparison_notes_json = ?, updated_at = ? WHERE project_id = ? AND selection_id = ?",
                (json.dumps(comparison_notes), updated.isoformat(), project_id, selection_id),
            )
            connection.commit()
        return self.get_arc_selection(project_id, selection_id=selection_id)



    def _arc_selection_comparison_ids(self, selection_id: str) -> list[str]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT comparison_id
                FROM arc_selection_comparisons
                WHERE selection_id = ?
                ORDER BY link_order ASC, comparison_id ASC
                """,
                (selection_id,),
            ).fetchall()
        return [row["comparison_id"] for row in rows]



    def _replace_arc_selection_comparison_links(
        self,
        *,
        selection_id: str,
        project_id: str,
        comparison_record_ids: Sequence[str],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        normalized_ids = _normalize_text_list(list(comparison_record_ids), field_name="comparison_record_ids")
        with connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM arc_selection_comparisons WHERE selection_id = ?",
                (selection_id,),
            )
            for link_order, comparison_id in enumerate(normalized_ids):
                comparison_row = connection.execute(
                    """
                    SELECT comparison_id
                    FROM arc_comparisons
                    WHERE project_id = ? AND comparison_id = ?
                    """,
                    (project_id, comparison_id),
                ).fetchone()
                if comparison_row is None:
                    raise KeyError((project_id, comparison_id))
                connection.execute(
                    """
                    INSERT INTO arc_selection_comparisons (
                        selection_id, comparison_id, link_order, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        selection_id,
                        comparison_id,
                        link_order,
                        now.isoformat(),
                        updated.isoformat(),
                    ),
                )
            connection.commit()



    def _persist_arc_candidate(
        self,
        project_id: str,
        candidate: ArcCandidate | ArcCandidateRecord | Mapping[str, Any],
        *,
        created_at: datetime,
        updated_at: datetime,
    ) -> ArcCandidateRecord:
        normalized = _coerce_arc_candidate(project_id, candidate)
        return self.upsert_arc_candidate(
            project_id=normalized.project_id,
            arc_id=normalized.arc_id,
            name=normalized.name,
            summary=normalized.summary,
            stage_map_notes=normalized.stage_map_notes,
            fit_notes=normalized.fit_notes,
            tags=normalized.tags,
            created_at=created_at,
            updated_at=updated_at,
        )



    def _persist_arc_stage_map(
        self,
        project_id: str,
        stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any] | None,
        *,
        created_at: datetime,
        updated_at: datetime,
    ) -> ArcStageMapRecord | None:
        if stage_map is None:
            return None
        normalized = _coerce_arc_stage_map(project_id, stage_map)
        self.upsert_arc_stage_map(
            project_id=normalized.project_id,
            arc_id=normalized.arc_id,
            stage_kinds=normalized.stage_kinds,
            notes=normalized.notes,
            arc_stage_map_id=normalized.arc_stage_map_id,
            created_at=created_at,
            updated_at=updated_at,
        )
        return self.get_arc_stage_map(project_id, arc_id=normalized.arc_id)
