from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from .shared_utils import (
    json_list as _json_list,
    now as _now,
)
from . import (
    StoryFlowDefinitionRecord,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StoryFlowStageRecord,
)
from .converters import _stage_row_to_record

from ..sqlite import connect


class _FlowMixin:

    def __init__(self, db_path):

        self.db_path = db_path



    def ensure_flow_definition(
        self,
        *,
        project_id: str,
        flow_name: str,
        flow_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowDefinitionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO story_flow_definitions (
                    project_id, flow_name, flow_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    flow_name = excluded.flow_name,
                    flow_notes = excluded.flow_notes,
                    updated_at = excluded.updated_at
                """,
                (project_id, flow_name, flow_notes, now.isoformat(), updated.isoformat()),
            )
            connection.commit()
        return self.get_flow_definition(project_id)



    def get_flow_definition(self, project_id: str) -> StoryFlowDefinitionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT project_id, flow_name, flow_notes, created_at, updated_at
                FROM story_flow_definitions
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return StoryFlowDefinitionRecord(
            project_id=row["project_id"],
            flow_name=row["flow_name"],
            flow_notes=row["flow_notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )



    def add_flow_stage(
        self,
        *,
        project_id: str,
        stage_key: str,
        stage_kind: str,
        is_custom: bool,
        display_name: str,
        position: int,
        description: str | None = None,
        depends_on: list[str] | None = None,
        stage_configuration_state: str,
        stage_progress_state: str,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO story_flow_stages (
                    project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                    stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    stage_key,
                    stage_kind,
                    1 if is_custom else 0,
                    display_name,
                    description,
                    position,
                    _json_list(depends_on),
                    stage_configuration_state,
                    stage_progress_state,
                    writer_notes,
                    custom_prompt_guidance,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_flow_stage(project_id, stage_key=stage_key)



    def get_flow_stage(
        self,
        project_id: str,
        *,
        stage_id: int | None = None,
        stage_key: str | None = None,
    ) -> StoryFlowStageRecord:
        if stage_id is None and stage_key is None:
            raise ValueError("stage_id or stage_key is required")
        query = """
            SELECT stage_id, project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                   stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance, created_at, updated_at
            FROM story_flow_stages
            WHERE project_id = ?
        """
        params: list[object] = [project_id]
        if stage_id is not None:
            query += " AND stage_id = ?"
            params.append(stage_id)
        if stage_key is not None:
            query += " AND stage_key = ?"
            params.append(stage_key)
        with connect(self.db_path) as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        if row is None:
            raise KeyError(stage_id if stage_id is not None else stage_key)
        return _stage_row_to_record(row)



    def list_flow_stages(self, project_id: str) -> list[StoryFlowStageRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT stage_id, project_id, stage_key, stage_kind, is_custom, display_name, description, position, depends_on_json,
                       stage_configuration_state, stage_progress_state, writer_notes, custom_prompt_guidance, created_at, updated_at
                FROM story_flow_stages
                WHERE project_id = ?
                ORDER BY position ASC, stage_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_stage_row_to_record(row) for row in rows]



    def rename_flow_stage(self, project_id: str, *, stage_id: int, display_name: str, updated_at: datetime | None = None) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                UPDATE story_flow_stages
                SET display_name = ?, updated_at = ?
                WHERE project_id = ? AND stage_id = ?
                """,
                (display_name, updated.isoformat(), project_id, stage_id),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)



    def redefine_flow_stage(
        self,
        project_id: str,
        *,
        stage_id: int,
        stage_kind: str | None = None,
        description: str | None = None,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        assignments: list[str] = []
        values: list[object] = []
        for column, value in (
            ("stage_kind", stage_kind),
            ("description", description),
            ("writer_notes", writer_notes),
            ("custom_prompt_guidance", custom_prompt_guidance),
        ):
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if not assignments:
            return self.get_flow_stage(project_id, stage_id=stage_id)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.extend([project_id, stage_id])
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE story_flow_stages
                SET {', '.join(assignments)}
                WHERE project_id = ? AND stage_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)



    def reorder_flow_stages(self, project_id: str, *, ordered_stage_ids: list[int], updated_at: datetime | None = None) -> list[StoryFlowStageRecord]:
        updated = _now(updated_at)
        with connect(self.db_path) as connection:
            for position, stage_id in enumerate(ordered_stage_ids):
                connection.execute(
                    """
                    UPDATE story_flow_stages
                    SET position = ?, updated_at = ?
                    WHERE project_id = ? AND stage_id = ?
                    """,
                    (position, updated.isoformat(), project_id, stage_id),
                )
            connection.commit()
        return self.list_flow_stages(project_id)



    def set_flow_stage_state(
        self,
        project_id: str,
        *,
        stage_id: int,
        stage_configuration_state: StoryFlowStageConfigurationState | str | None = None,
        stage_progress_state: StoryFlowStageProgressState | str | None = None,
        updated_at: datetime | None = None,
    ) -> StoryFlowStageRecord:
        updated = _now(updated_at)
        assignments: list[str] = []
        values: list[object] = []
        if stage_configuration_state is not None:
            assignments.append("stage_configuration_state = ?")
            values.append(stage_configuration_state)
        if stage_progress_state is not None:
            assignments.append("stage_progress_state = ?")
            values.append(stage_progress_state)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.extend([project_id, stage_id])
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE story_flow_stages
                SET {', '.join(assignments)}
                WHERE project_id = ? AND stage_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(stage_id)
        return self.get_flow_stage(project_id, stage_id=stage_id)



    def delete_custom_flow_stage(self, project_id: str, *, stage_id: int) -> bool:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT is_custom
                FROM story_flow_stages
                WHERE project_id = ? AND stage_id = ?
                """,
                (project_id, stage_id),
            ).fetchone()
            if row is None:
                raise KeyError(stage_id)
            if int(row["is_custom"]) != 1:
                raise ValueError("Only custom stages may be deleted")
            connection.execute(
                "DELETE FROM story_flow_stages WHERE project_id = ? AND stage_id = ?",
                (project_id, stage_id),
            )
            connection.commit()
        return True
