from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import (
    StoryFlowDefinition,
    StoryFlowStage,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
)
from app.services.editable_flow import (
    EditableFlowError,
    EditableFlowRepository,
    EditableFlowState,
    EditableFlowValidationError,
)


def _now(dt: datetime | None = None) -> datetime:
    if dt is not None:
        return dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _json_list(items: list[str] | None) -> str:
    import json
    return json.dumps(items or [])


def _parse_json_list(value: str | None) -> list[str]:
    import json
    if not value:
        return []
    return json.loads(value)


class SQLiteEditableFlowRepository(EditableFlowRepository):
    """Bridge between EditableFlowService (in-memory state) and StoryDevelopmentRepository (SQLite).

    Implements the EditableFlowRepository protocol by persisting flow stages to the
    story_flow_stages table. Uses full-replacement on save for correctness.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)

    def get(self, project_id: str) -> EditableFlowState | None:
        ensure_operations_db(self._db_path)
        with connect(self._db_path) as connection:
            # Ensure counter table exists (lazy creation)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS editable_flow_counters (
                    project_id TEXT PRIMARY KEY,
                    next_stage_index INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cursor = connection.execute(
                """
                SELECT stage_id, project_id, stage_key, stage_kind, is_custom,
                       display_name, description, position, depends_on_json,
                       stage_configuration_state, stage_progress_state,
                       writer_notes, custom_prompt_guidance, created_at, updated_at
                FROM story_flow_stages
                WHERE project_id = ?
                ORDER BY position ASC, stage_id ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
            # Read persisted counter to preserve next_stage_index across deletions
            counter = connection.execute(
                "SELECT next_stage_index FROM editable_flow_counters WHERE project_id = ?",
                (project_id,),
            ).fetchone()

        if not rows:
            return None

        stages: list[StoryFlowStage] = []
        custom_ids: list[str] = []
        max_index = 0

        for row in rows:
            stage_key = row["stage_key"]
            # Extract numeric index from stage_key like "stage-001"
            try:
                idx = int(stage_key.split("-")[1])
            except (IndexError, ValueError):
                idx = 1

            if idx > max_index:
                max_index = idx

            stage = StoryFlowStage(
                stage_id=stage_key,
                stage_kind=row["stage_kind"],
                display_name=row["display_name"],
                description=row["description"],
                position=row["position"],
                depends_on=_parse_json_list(row["depends_on_json"]),
                stage_configuration_state=StoryFlowStageConfigurationState(
                    row["stage_configuration_state"]
                ),
                stage_progress_state=StoryFlowStageProgressState(
                    row["stage_progress_state"]
                ),
                writer_notes=row["writer_notes"],
                custom_prompt_guidance=row["custom_prompt_guidance"],
            )
            stages.append(stage)
            if row["is_custom"]:
                custom_ids.append(stage_key)

        next_stage_index = counter["next_stage_index"] if counter else max_index + 1

        return EditableFlowState(
            flow=StoryFlowDefinition(
                project_id=project_id,
                project_name="Project Flow",
                stages=stages,
            ),
            custom_stage_ids=frozenset(custom_ids),
            next_stage_index=next_stage_index,
        )

    def save(self, state: EditableFlowState) -> EditableFlowState:
        stored = self._persist_state(state)
        return stored

    def delete(self, project_id: str) -> None:
        ensure_operations_db(self._db_path)
        with connect(self._db_path) as connection:
            connection.execute(
                "DELETE FROM story_flow_stages WHERE project_id = ?",
                (project_id,),
            )
            connection.execute(
                "DELETE FROM editable_flow_counters WHERE project_id = ?",
                (project_id,),
            )
            connection.commit()

    def _persist_state(self, state: EditableFlowState) -> EditableFlowState:
        """Delete all existing stages for the project and re-insert from state.

        Full replacement ensures consistency between the in-memory state
        and the database without complex diffing logic.
        """
        project_id = state.flow.project_id
        now = _now()

        ensure_operations_db(self._db_path)
        with connect(self._db_path) as connection:
            # Delete existing stages for this project
            connection.execute(
                "DELETE FROM story_flow_stages WHERE project_id = ?",
                (project_id,),
            )

            # Re-insert from state
            for stage in state.flow.stages:
                connection.execute(
                    """
                    INSERT INTO story_flow_stages (
                        project_id, stage_key, stage_kind, is_custom,
                        display_name, description, position, depends_on_json,
                        stage_configuration_state, stage_progress_state,
                        writer_notes, custom_prompt_guidance,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        stage.stage_id,
                        stage.stage_kind,
                        1 if stage.stage_id in state.custom_stage_ids else 0,
                        stage.display_name,
                        stage.description,
                        stage.position,
                        _json_list(stage.depends_on),
                        stage.stage_configuration_state,
                        stage.stage_progress_state,
                        stage.writer_notes,
                        stage.custom_prompt_guidance,
                        now.isoformat(),
                        now.isoformat(),
                    ),
                )

            # Persist next_stage_index so it survives stage deletions
            connection.execute(
                """
                INSERT OR REPLACE INTO editable_flow_counters (project_id, next_stage_index)
                VALUES (?, ?)
                """,
                (project_id, state.next_stage_index),
            )

            connection.commit()

        return state
