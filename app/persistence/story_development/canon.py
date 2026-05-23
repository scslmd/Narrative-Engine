from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    json_object as _json_object,
    now as _now,
)
from . import CanonAnnotationRecord, CanonCustomizationProfileRecord
from .converters import (
    _canon_annotation_row_to_record, _canon_customization_profile_row_to_record,
)

from ..sqlite import connect


class _CanonAnnotationMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_canon_annotation(
        self,
        *,
        annotation_id: str,
        project_id: str,
        target_kind: str,
        target_id: str,
        field_path: str,
        annotation_kind: str,
        note: str = "",
        applies_to_modes: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CanonAnnotationRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO canon_annotations (
                    annotation_id, project_id, target_kind, target_id, field_path, annotation_kind,
                    note, applies_to_modes_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(annotation_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    target_kind = excluded.target_kind,
                    target_id = excluded.target_id,
                    field_path = excluded.field_path,
                    annotation_kind = excluded.annotation_kind,
                    note = excluded.note,
                    applies_to_modes_json = excluded.applies_to_modes_json,
                    updated_at = excluded.updated_at
                """,
                (
                    annotation_id,
                    project_id,
                    target_kind,
                    target_id,
                    field_path,
                    annotation_kind,
                    note,
                    _json_list(applies_to_modes),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_canon_annotation(annotation_id)



    def get_canon_annotation(self, annotation_id: str) -> CanonAnnotationRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM canon_annotations WHERE annotation_id = ?", (annotation_id,)).fetchone()
        if row is None:
            raise KeyError(annotation_id)
        return _canon_annotation_row_to_record(row)



    def delete_canon_annotation(self, annotation_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute("DELETE FROM canon_annotations WHERE annotation_id = ?", (annotation_id,))
            connection.commit()



    def list_canon_annotations(
        self,
        project_id: str,
        target_kind: str | None = None,
        target_id: str | None = None,
    ) -> list[CanonAnnotationRecord]:
        query = "SELECT * FROM canon_annotations WHERE project_id = ?"
        params: list[str] = [project_id]
        if target_kind is not None:
            query += " AND target_kind = ?"
            params.append(target_kind)
        if target_id is not None:
            query += " AND target_id = ?"
            params.append(target_id)
        query += " ORDER BY target_kind ASC, target_id ASC, field_path ASC, annotation_kind ASC"
        with connect(self.db_path) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_canon_annotation_row_to_record(row) for row in rows]


class _CanonProfileMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def upsert_canon_customization_profile(
        self,
        *,
        profile_id: str,
        project_id: str,
        name: str,
        description: str,
        default_generation_mode: str,
        canon_scope_json: Mapping[str, Any],
        canon_policy_json: Mapping[str, Any],
        generation_brief_template: str = "",
        selected_annotation_ids: list[str] | None = None,
        status: str = "draft",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CanonCustomizationProfileRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO canon_customization_profiles (
                    profile_id, project_id, name, description, default_generation_mode,
                    canon_scope_json, canon_policy_json, generation_brief_template,
                    selected_annotation_ids_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    name = excluded.name,
                    description = excluded.description,
                    default_generation_mode = excluded.default_generation_mode,
                    canon_scope_json = excluded.canon_scope_json,
                    canon_policy_json = excluded.canon_policy_json,
                    generation_brief_template = excluded.generation_brief_template,
                    selected_annotation_ids_json = excluded.selected_annotation_ids_json,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    profile_id,
                    project_id,
                    name,
                    description,
                    default_generation_mode,
                    _json_object(canon_scope_json),
                    _json_object(canon_policy_json),
                    generation_brief_template,
                    _json_list(selected_annotation_ids),
                    status,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_canon_customization_profile(profile_id)



    def get_canon_customization_profile(self, profile_id: str) -> CanonCustomizationProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM canon_customization_profiles WHERE profile_id = ?", (profile_id,)).fetchone()
        if row is None:
            raise KeyError(profile_id)
        return _canon_customization_profile_row_to_record(row)



    def list_canon_customization_profiles(self, project_id: str) -> list[CanonCustomizationProfileRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT * FROM canon_customization_profiles WHERE project_id = ? ORDER BY updated_at DESC",
                (project_id,),
            ).fetchall()
        return [_canon_customization_profile_row_to_record(row) for row in rows]



    def delete_canon_customization_profile(self, profile_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute("DELETE FROM canon_customization_profiles WHERE profile_id = ?", (profile_id,))
            connection.commit()
