from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import (
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
)

from .sqlite import connect, ensure_operations_db


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(UTC)


def _json_list(values: list[str] | None) -> str:
    import json

    return json.dumps(list(values or []), ensure_ascii=True, sort_keys=True)


def _parse_json_list(value: str | None) -> list[str]:
    import json

    return list(json.loads(value or "[]"))


@dataclass(frozen=True)
class StoryFlowDefinitionRecord:
    project_id: str
    flow_name: str
    flow_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StoryFlowStageRecord:
    stage_id: int
    project_id: str
    stage_key: str
    stage_kind: str
    is_custom: bool
    display_name: str
    description: str | None
    position: int
    depends_on: list[str]
    stage_configuration_state: StoryFlowStageConfigurationState
    stage_progress_state: StoryFlowStageProgressState
    writer_notes: str | None
    custom_prompt_guidance: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BrainstormItemRecord:
    item_id: int
    project_id: str
    cluster_key: str | None
    content: str
    item_state: str
    tags: list[str]
    source_artifact_refs: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationRevisionRecord:
    revision_id: int
    project_id: str
    revision_number: int
    premise: str
    logline: str
    thematic_spine: str | None
    emotional_promise: str | None
    tone_direction: str | None
    target_audience: str | None
    narrative_constraints: list[str]
    complexity_level: str | None
    success_definition: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FoundationProfileRecord:
    project_id: str
    current_revision_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CharacterProfileRecord:
    character_id: str
    project_id: str
    display_name: str
    role_in_story: str | None
    archetype: str | None
    external_goal: str | None
    internal_need: str | None
    misbelief_or_wound: str | None
    core_fear: str | None
    primary_strength: str | None
    fatal_flaw_or_limitation: str | None
    contradictions: list[str]
    backstory_summary: str | None
    voice_notes: str | None
    relationship_map: list[str]
    secrets: list[str]
    values: list[str]
    taboos: list[str]
    change_axis: str | None
    arc_stage_notes: str | None
    continuity_facts: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WorldBibleEntryRecord:
    entry_id: int
    project_id: str
    entry_type: str
    title: str
    summary: str | None
    canonical_facts: list[str]
    visibility_scope: str
    source_artifacts: list[str]
    continuity_warnings: list[str]
    writer_notes: str | None
    created_at: datetime
    updated_at: datetime


class StoryDevelopmentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = ensure_operations_db(db_path)

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

    def create_brainstorm_item(
        self,
        *,
        project_id: str,
        content: str,
        item_state: str,
        cluster_key: str | None = None,
        tags: list[str] | None = None,
        source_artifact_refs: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO brainstorm_items (
                    project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    cluster_key,
                    content,
                    item_state,
                    _json_list(tags),
                    _json_list(source_artifact_refs),
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_brainstorm_item(int(cursor.lastrowid))

    def get_brainstorm_item(self, item_id: int) -> BrainstormItemRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return _brainstorm_row_to_record(row)

    def list_brainstorm_items(self, project_id: str) -> list[BrainstormItemRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT item_id, project_id, cluster_key, content, item_state, tags_json, source_artifact_refs_json, created_at, updated_at
                FROM brainstorm_items
                WHERE project_id = ?
                ORDER BY item_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_brainstorm_row_to_record(row) for row in rows]

    def update_brainstorm_item_state(
        self,
        item_id: int,
        *,
        item_state: str,
        cluster_key: str | None = None,
        updated_at: datetime | None = None,
    ) -> BrainstormItemRecord:
        updated = _now(updated_at)
        assignments = ["item_state = ?"]
        values: list[object] = [item_state]
        if cluster_key is not None:
            assignments.append("cluster_key = ?")
            values.append(cluster_key)
        assignments.append("updated_at = ?")
        values.append(updated.isoformat())
        values.append(item_id)
        with connect(self.db_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE brainstorm_items
                SET {', '.join(assignments)}
                WHERE item_id = ?
                """,
                tuple(values),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(item_id)
        return self.get_brainstorm_item(item_id)

    def upsert_foundation_profile(
        self,
        *,
        project_id: str,
        premise: str,
        logline: str,
        thematic_spine: str | None = None,
        emotional_promise: str | None = None,
        tone_direction: str | None = None,
        target_audience: str | None = None,
        narrative_constraints: list[str] | None = None,
        complexity_level: str | None = None,
        success_definition: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        ) -> FoundationRevisionRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        revision_number = self._next_foundation_revision_number(project_id)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO foundation_profiles (
                    project_id, current_revision_id, created_at, updated_at
                ) VALUES (?, NULL, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    updated_at = excluded.updated_at
                """,
                (project_id, now.isoformat(), updated.isoformat()),
            )
            cursor = connection.execute(
                """
                INSERT INTO foundation_revisions (
                    project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                    tone_direction, target_audience, narrative_constraints_json, complexity_level,
                    success_definition, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    revision_number,
                    premise,
                    logline,
                    thematic_spine,
                    emotional_promise,
                    tone_direction,
                    target_audience,
                    _json_list(narrative_constraints),
                    complexity_level,
                    success_definition,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            revision_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
                (revision_id, updated.isoformat(), project_id),
            )
            connection.commit()
        return self.get_foundation_revision(revision_id)

    def get_foundation_profile(self, project_id: str) -> FoundationProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT project_id, current_revision_id, created_at, updated_at
                FROM foundation_profiles
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return FoundationProfileRecord(
            project_id=row["project_id"],
            current_revision_id=row["current_revision_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def list_foundation_revisions(self, project_id: str) -> list[FoundationRevisionRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE project_id = ?
                ORDER BY revision_number ASC, revision_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [_foundation_revision_row_to_record(row) for row in rows]

    def get_foundation_revision(self, revision_id: int) -> FoundationRevisionRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT revision_id, project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                       tone_direction, target_audience, narrative_constraints_json, complexity_level, success_definition,
                       created_at, updated_at
                FROM foundation_revisions
                WHERE revision_id = ?
                """,
                (revision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        return _foundation_revision_row_to_record(row)

    def upsert_character_profile(
        self,
        *,
        project_id: str,
        character_id: str,
        display_name: str,
        role_in_story: str | None = None,
        archetype: str | None = None,
        external_goal: str | None = None,
        internal_need: str | None = None,
        misbelief_or_wound: str | None = None,
        core_fear: str | None = None,
        primary_strength: str | None = None,
        fatal_flaw_or_limitation: str | None = None,
        contradictions: list[str] | None = None,
        backstory_summary: str | None = None,
        voice_notes: str | None = None,
        relationship_map: list[str] | None = None,
        secrets: list[str] | None = None,
        values: list[str] | None = None,
        taboos: list[str] | None = None,
        change_axis: str | None = None,
        arc_stage_notes: str | None = None,
        continuity_facts: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> CharacterProfileRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO character_profiles (
                    character_id, project_id, display_name, role_in_story, archetype, external_goal, internal_need,
                    misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, contradictions_json,
                    backstory_summary, voice_notes, relationship_map_json, secrets_json, values_json, taboos_json,
                    change_axis, arc_stage_notes, continuity_facts_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(character_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    display_name = excluded.display_name,
                    role_in_story = excluded.role_in_story,
                    archetype = excluded.archetype,
                    external_goal = excluded.external_goal,
                    internal_need = excluded.internal_need,
                    misbelief_or_wound = excluded.misbelief_or_wound,
                    core_fear = excluded.core_fear,
                    primary_strength = excluded.primary_strength,
                    fatal_flaw_or_limitation = excluded.fatal_flaw_or_limitation,
                    contradictions_json = excluded.contradictions_json,
                    backstory_summary = excluded.backstory_summary,
                    voice_notes = excluded.voice_notes,
                    relationship_map_json = excluded.relationship_map_json,
                    secrets_json = excluded.secrets_json,
                    values_json = excluded.values_json,
                    taboos_json = excluded.taboos_json,
                    change_axis = excluded.change_axis,
                    arc_stage_notes = excluded.arc_stage_notes,
                    continuity_facts_json = excluded.continuity_facts_json,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    character_id,
                    project_id,
                    display_name,
                    role_in_story,
                    archetype,
                    external_goal,
                    internal_need,
                    misbelief_or_wound,
                    core_fear,
                    primary_strength,
                    fatal_flaw_or_limitation,
                    _json_list(contradictions),
                    backstory_summary,
                    voice_notes,
                    _json_list(relationship_map),
                    _json_list(secrets),
                    _json_list(values),
                    _json_list(taboos),
                    change_axis,
                    arc_stage_notes,
                    _json_list(continuity_facts),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_character_profile(character_id)

    def get_character_profile(self, character_id: str) -> CharacterProfileRecord:
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT * FROM character_profiles WHERE character_id = ?", (character_id,)).fetchone()
        if row is None:
            raise KeyError(character_id)
        return _character_row_to_record(row)

    def list_character_profiles(self, project_id: str) -> list[CharacterProfileRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM character_profiles
                WHERE project_id = ?
                ORDER BY display_name COLLATE NOCASE, character_id
                """,
                (project_id,),
            ).fetchall()
        return [_character_row_to_record(row) for row in rows]

    def upsert_world_bible_entry(
        self,
        *,
        project_id: str,
        entry_type: str,
        title: str,
        summary: str | None = None,
        canonical_facts: list[str] | None = None,
        visibility_scope: str = "project",
        source_artifacts: list[str] | None = None,
        continuity_warnings: list[str] | None = None,
        writer_notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> WorldBibleEntryRecord:
        now = _now(created_at)
        updated = _now(updated_at or created_at)
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json, visibility_scope,
                    source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                    summary = excluded.summary,
                    canonical_facts_json = excluded.canonical_facts_json,
                    visibility_scope = excluded.visibility_scope,
                    source_artifacts_json = excluded.source_artifacts_json,
                    continuity_warnings_json = excluded.continuity_warnings_json,
                    writer_notes = excluded.writer_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    entry_type,
                    title,
                    summary,
                    _json_list(canonical_facts),
                    visibility_scope,
                    _json_list(source_artifacts),
                    _json_list(continuity_warnings),
                    writer_notes,
                    now.isoformat(),
                    updated.isoformat(),
                ),
            )
            connection.commit()
        return self.get_world_bible_entry(project_id, entry_type=entry_type, title=title)

    def get_world_bible_entry(self, project_id: str, *, entry_type: str, title: str) -> WorldBibleEntryRecord:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ? AND entry_type = ? AND title = ?
                """,
                (project_id, entry_type, title),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, entry_type, title))
        return _world_bible_row_to_record(row)

    def list_world_bible_entries(self, project_id: str) -> list[WorldBibleEntryRecord]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM world_bible_entries
                WHERE project_id = ?
                ORDER BY entry_type COLLATE NOCASE, title COLLATE NOCASE, entry_id
                """,
                (project_id,),
            ).fetchall()
        return [_world_bible_row_to_record(row) for row in rows]

    def _next_foundation_revision_number(self, project_id: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(revision_number), 0) AS revision_number FROM foundation_revisions WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return int(row["revision_number"]) + 1


def _stage_row_to_record(row) -> StoryFlowStageRecord:
    return StoryFlowStageRecord(
        stage_id=int(row["stage_id"]),
        project_id=row["project_id"],
        stage_key=row["stage_key"],
        stage_kind=row["stage_kind"],
        is_custom=bool(row["is_custom"]),
        display_name=row["display_name"],
        description=row["description"],
        position=int(row["position"]),
        depends_on=_parse_json_list(row["depends_on_json"]),
        stage_configuration_state=StoryFlowStageConfigurationState(row["stage_configuration_state"]),
        stage_progress_state=StoryFlowStageProgressState(row["stage_progress_state"]),
        writer_notes=row["writer_notes"],
        custom_prompt_guidance=row["custom_prompt_guidance"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _brainstorm_row_to_record(row) -> BrainstormItemRecord:
    return BrainstormItemRecord(
        item_id=int(row["item_id"]),
        project_id=row["project_id"],
        cluster_key=row["cluster_key"],
        content=row["content"],
        item_state=row["item_state"],
        tags=_parse_json_list(row["tags_json"]),
        source_artifact_refs=_parse_json_list(row["source_artifact_refs_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _foundation_revision_row_to_record(row) -> FoundationRevisionRecord:
    return FoundationRevisionRecord(
        revision_id=int(row["revision_id"]),
        project_id=row["project_id"],
        revision_number=int(row["revision_number"]),
        premise=row["premise"],
        logline=row["logline"],
        thematic_spine=row["thematic_spine"],
        emotional_promise=row["emotional_promise"],
        tone_direction=row["tone_direction"],
        target_audience=row["target_audience"],
        narrative_constraints=_parse_json_list(row["narrative_constraints_json"]),
        complexity_level=row["complexity_level"],
        success_definition=row["success_definition"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _character_row_to_record(row) -> CharacterProfileRecord:
    return CharacterProfileRecord(
        character_id=row["character_id"],
        project_id=row["project_id"],
        display_name=row["display_name"],
        role_in_story=row["role_in_story"],
        archetype=row["archetype"],
        external_goal=row["external_goal"],
        internal_need=row["internal_need"],
        misbelief_or_wound=row["misbelief_or_wound"],
        core_fear=row["core_fear"],
        primary_strength=row["primary_strength"],
        fatal_flaw_or_limitation=row["fatal_flaw_or_limitation"],
        contradictions=_parse_json_list(row["contradictions_json"]),
        backstory_summary=row["backstory_summary"],
        voice_notes=row["voice_notes"],
        relationship_map=_parse_json_list(row["relationship_map_json"]),
        secrets=_parse_json_list(row["secrets_json"]),
        values=_parse_json_list(row["values_json"]),
        taboos=_parse_json_list(row["taboos_json"]),
        change_axis=row["change_axis"],
        arc_stage_notes=row["arc_stage_notes"],
        continuity_facts=_parse_json_list(row["continuity_facts_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _world_bible_row_to_record(row) -> WorldBibleEntryRecord:
    return WorldBibleEntryRecord(
        entry_id=int(row["entry_id"]),
        project_id=row["project_id"],
        entry_type=row["entry_type"],
        title=row["title"],
        summary=row["summary"],
        canonical_facts=_parse_json_list(row["canonical_facts_json"]),
        visibility_scope=row["visibility_scope"],
        source_artifacts=_parse_json_list(row["source_artifacts_json"]),
        continuity_warnings=_parse_json_list(row["continuity_warnings_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
