from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import CanonGenerationRequest, WorldBibleRef
from app.schemas.projects import ProjectCreateRequest
from app.services.projects import ProjectService
from app.utils.db_inserts import hash_id


class StoryForkingService:
    def __init__(
        self,
        *,
        repository: StoryDevelopmentRepository,
        project_service: ProjectService,
    ) -> None:
        self._repository = repository
        self._project_service = project_service

    def create_fork_project(self, request: CanonGenerationRequest) -> str:
        target_name = request.destination.target_project_name or "Forked Story"
        project_id = hash_id(
            "fork-project",
            f"{request.source_project_id}:{target_name}:{getattr(request.mode, 'value', request.mode)}",
        )
        create_request = ProjectCreateRequest(
            project_id=project_id,
            project_name=target_name,
            genre="Derived",
            tone_profile=request.tone_override or "Neutral",
            story_structure="THREE_ACT",
            premise_text=request.premise_override or request.generation_brief,
        )
        try:
            self._project_service.get_project(project_id)
        except FileNotFoundError:
            self._project_service.create_project(create_request)
        return project_id

    def copy_selected_characters(
        self,
        source_project_id: str,
        target_project_id: str,
        character_ids: list[str],
    ) -> list[str]:
        if not character_ids:
            return []
        source_records = {
            record.character_id: record
            for record in self._repository.list_character_profiles(source_project_id)
        }
        now = datetime.now(timezone.utc).isoformat()
        rows: list[tuple] = []
        copied_ids: list[str] = []
        for source_character_id in character_ids:
            record = source_records.get(source_character_id)
            if record is None:
                continue
            target_character_id = hash_id(
                "fork-character",
                f"{source_project_id}:{target_project_id}:{source_character_id}",
            )
            rows.append((
                target_character_id,
                target_project_id,
                record.display_name,
                record.role_in_story or "",
                record.archetype,
                record.external_goal,
                record.internal_need,
                record.misbelief_or_wound,
                record.core_fear,
                record.primary_strength,
                record.fatal_flaw_or_limitation,
                json.dumps(list(record.contradictions or []), ensure_ascii=True, sort_keys=True),
                record.backstory_summary,
                f"{record.voice_notes or ''}\n\nforked from {source_project_id}:{source_character_id}".strip(),
                json.dumps(list(record.relationship_map or []), ensure_ascii=True, sort_keys=True),
                json.dumps(list(record.secrets or []), ensure_ascii=True, sort_keys=True),
                json.dumps(list(record.values or []), ensure_ascii=True, sort_keys=True),
                json.dumps(list(record.taboos or []), ensure_ascii=True, sort_keys=True),
                record.change_axis,
                record.arc_stage_notes,
                json.dumps(list(record.continuity_facts or []), ensure_ascii=True, sort_keys=True),
                record.writer_notes,
                now,
                now,
            ))
            copied_ids.append(target_character_id)
        if rows:
            db_path = self._repository.db_path
            conn = sqlite3.connect(str(db_path), timeout=30)
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.executemany(
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
                    rows,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        return copied_ids

    def copy_selected_relationships(
        self,
        source_project_id: str,
        target_project_id: str,
        character_ids: list[str],
    ) -> list[str]:
        if not character_ids:
            return []
        selected = set(character_ids)
        records = self._repository.list_relationship_edges(source_project_id)
        source_target_map = {
            source_id: hash_id("fork-character", f"{source_project_id}:{target_project_id}:{source_id}")
            for source_id in selected
        }
        now = datetime.now(timezone.utc).isoformat()
        edge_rows: list[tuple] = []
        edge_map_updates: list[tuple] = []
        copied_edges: list[str] = []
        for record in records:
            if record.source_character_id not in selected or record.target_character_id not in selected:
                continue
            edge_id = hash_id("fork-edge", f"{source_project_id}:{target_project_id}:{record.edge_id}")
            forked_source = source_target_map[record.source_character_id]
            forked_target = source_target_map[record.target_character_id]
            edge_rows.append((
                edge_id,
                target_project_id,
                forked_source,
                forked_target,
                record.relation_kind,
                record.summary,
                record.tension,
                f"{record.notes or ''}\nforked from {source_project_id}:{record.edge_id}".strip(),
                now,
                now,
            ))
            for char_id in (forked_source, forked_target):
                edge_map_updates.append((edge_id, char_id, now))
            copied_edges.append(edge_id)
        if edge_rows:
            db_path = self._repository.db_path
            conn = sqlite3.connect(str(db_path), timeout=30)
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.executemany(
                    """
                    INSERT INTO relationship_edges (
                        edge_id, project_id, source_character_id, target_character_id, relation_kind, summary,
                        tension, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(edge_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        source_character_id = excluded.source_character_id,
                        target_character_id = excluded.target_character_id,
                        relation_kind = excluded.relation_kind,
                        summary = excluded.summary,
                        tension = excluded.tension,
                        notes = excluded.notes,
                        updated_at = excluded.updated_at
                    """,
                    edge_rows,
                )
                for edge_id, char_id, updated_at in edge_map_updates:
                    row = conn.execute(
                        "SELECT relationship_map_json FROM character_profiles WHERE character_id = ?",
                        (char_id,),
                    ).fetchone()
                    if row is None:
                        continue
                    existing = json.loads(row[0] or "[]")
                    if edge_id in existing:
                        continue
                    existing.append(edge_id)
                    conn.execute(
                        "UPDATE character_profiles SET relationship_map_json = ?, updated_at = ? WHERE character_id = ?",
                        (json.dumps(existing, ensure_ascii=True, sort_keys=True), updated_at, char_id),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        return copied_edges

    def copy_selected_world_entries(
        self,
        source_project_id: str,
        target_project_id: str,
        refs: list[WorldBibleRef | dict[str, str]],
    ) -> list[str]:
        if not refs:
            return []
        normalized_refs = [
            item if isinstance(item, WorldBibleRef) else WorldBibleRef.model_validate(item)
            for item in refs
        ]
        selected = {(item.entry_type, item.title) for item in normalized_refs}
        records = self._repository.list_world_bible_entries(source_project_id)
        now = datetime.now(timezone.utc).isoformat()
        entry_rows: list[tuple] = []
        copied_titles: list[str] = []
        for record in records:
            if (record.entry_type, record.title) not in selected:
                continue
            entry_rows.append((
                target_project_id,
                record.entry_type,
                record.title,
                record.summary or "",
                json.dumps(list(record.canonical_facts or []), ensure_ascii=True, sort_keys=True),
                json.dumps(list(record.related_character_ids or []), ensure_ascii=True, sort_keys=True),
                record.visibility_scope,
                json.dumps(list(record.source_artifacts or []), ensure_ascii=True, sort_keys=True),
                json.dumps(list(record.continuity_warnings or []), ensure_ascii=True, sort_keys=True),
                f"{record.writer_notes or ''}\nforked from {source_project_id}:{record.entry_type}:{record.title}".strip(),
                now,
                now,
            ))
            copied_titles.append(f"{record.entry_type}:{record.title}")
        if entry_rows:
            db_path = self._repository.db_path
            conn = sqlite3.connect(str(db_path), timeout=30)
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.executemany(
                    """
                    INSERT INTO world_bible_entries (
                        project_id, entry_type, title, summary, canonical_facts_json, related_character_ids_json, visibility_scope,
                        source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                        summary = excluded.summary,
                        canonical_facts_json = excluded.canonical_facts_json,
                        related_character_ids_json = excluded.related_character_ids_json,
                        visibility_scope = excluded.visibility_scope,
                        source_artifacts_json = excluded.source_artifacts_json,
                        continuity_warnings_json = excluded.continuity_warnings_json,
                        writer_notes = excluded.writer_notes,
                        updated_at = excluded.updated_at
                    """,
                    entry_rows,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        return copied_titles

    def create_fork_foundation(
        self,
        source_project_id: str,
        target_project_id: str,
        request: CanonGenerationRequest,
    ) -> str:
        source_revisions = self._repository.list_foundation_revisions(source_project_id)
        if not source_revisions:
            return ""
        source_latest = source_revisions[-1]
        revision = self._repository.upsert_foundation_profile(
            project_id=target_project_id,
            premise=request.premise_override or source_latest.premise,
            logline=source_latest.logline,
            thematic_spine=source_latest.thematic_spine,
            emotional_promise=source_latest.emotional_promise,
            tone_direction=request.tone_override or source_latest.tone_direction,
            target_audience=source_latest.target_audience,
            narrative_constraints=source_latest.narrative_constraints,
            complexity_level=source_latest.complexity_level,
            success_definition=source_latest.success_definition,
        )
        return str(revision.revision_id)

    def record_source_link(self, source_project_id: str, target_project_id: str, generation_id: str) -> None:
        self._repository.upsert_checker_finding(
            finding_id=hash_id("fork-link", f"{source_project_id}:{target_project_id}:{generation_id}"),
            project_id=target_project_id,
            source_object_id=source_project_id,
            source_object_kind="source_project",
            severity="info",
            summary=f"Forked from {source_project_id}",
            details=f"generation_id={generation_id}",
            source_context=[generation_id],
        )
