from __future__ import annotations

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
        copied_ids: list[str] = []
        for source_character_id in character_ids:
            record = source_records.get(source_character_id)
            if record is None:
                continue
            target_character_id = hash_id(
                "fork-character",
                f"{source_project_id}:{target_project_id}:{source_character_id}",
            )
            self._repository.upsert_character_profile(
                character_id=target_character_id,
                project_id=target_project_id,
                display_name=record.display_name,
                role_in_story=record.role_in_story or "",
                archetype=record.archetype,
                external_goal=record.external_goal,
                internal_need=record.internal_need,
                misbelief_or_wound=record.misbelief_or_wound,
                core_fear=record.core_fear,
                primary_strength=record.primary_strength,
                fatal_flaw_or_limitation=record.fatal_flaw_or_limitation,
                contradictions=record.contradictions,
                backstory_summary=record.backstory_summary,
                voice_notes=f"{record.voice_notes or ''}\n\nforked from {source_project_id}:{source_character_id}".strip(),
                relationship_map=record.relationship_map,
                secrets=record.secrets,
                values=record.values,
                taboos=record.taboos,
                change_axis=record.change_axis,
                arc_stage_notes=record.arc_stage_notes,
                continuity_facts=record.continuity_facts,
                writer_notes=record.writer_notes,
            )
            copied_ids.append(target_character_id)
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
        copied_edges: list[str] = []
        for record in records:
            if record.source_character_id not in selected or record.target_character_id not in selected:
                continue
            source_target_map = {
                source_id: hash_id("fork-character", f"{source_project_id}:{target_project_id}:{source_id}")
                for source_id in selected
            }
            edge_id = hash_id("fork-edge", f"{source_project_id}:{target_project_id}:{record.edge_id}")
            self._repository.upsert_relationship_edge(
                edge_id=edge_id,
                project_id=target_project_id,
                source_character_id=source_target_map[record.source_character_id],
                target_character_id=source_target_map[record.target_character_id],
                relation_kind=record.relation_kind,
                summary=record.summary,
                tension=record.tension,
                notes=f"{record.notes or ''}\nforked from {source_project_id}:{record.edge_id}".strip(),
            )
            copied_edges.append(edge_id)
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
        copied_titles: list[str] = []
        for record in records:
            if (record.entry_type, record.title) not in selected:
                continue
            self._repository.upsert_world_bible_entry(
                project_id=target_project_id,
                entry_type=record.entry_type,
                title=record.title,
                summary=record.summary or "",
                canonical_facts=record.canonical_facts,
                related_character_ids=record.related_character_ids,
                visibility_scope=record.visibility_scope,
                source_artifacts=record.source_artifacts,
                continuity_warnings=record.continuity_warnings,
                writer_notes=f"{record.writer_notes or ''}\nforked from {source_project_id}:{record.entry_type}:{record.title}".strip(),
            )
            copied_titles.append(f"{record.entry_type}:{record.title}")
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
