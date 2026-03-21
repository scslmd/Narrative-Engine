from __future__ import annotations

from collections import defaultdict
from typing import Literal, Sequence

from app.persistence.story_development import PlanningDependencyRecord, StoryDevelopmentRepository
from app.schemas import ChapterPacket, ChapterPlan, PlanningDependency, ScenePlan, SequencePlan


PlanKind = Literal["sequence", "chapter", "scene"]


class PlanningServiceError(ValueError):
    pass


class PlanningValidationError(PlanningServiceError):
    pass


class PlanningNotFoundError(PlanningServiceError):
    pass


class PlanningService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def create_sequence_plan(
        self,
        project_id: str,
        *,
        sequence_id: str,
        title: str,
        summary: str,
        beat_ids: Sequence[str] | None = None,
        chapter_ids: Sequence[str] | None = None,
        status: str = "draft",
        position: int | None = None,
    ) -> SequencePlan:
        normalized_sequence_id = self._normalize_text(sequence_id, field_name="sequence_id")
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_title = self._normalize_text(title, field_name="title")
        normalized_summary = self._normalize_text(summary, field_name="summary")
        record = self.repository.upsert_sequence_plan(
            sequence_id=normalized_sequence_id,
            project_id=normalized_project_id,
            title=normalized_title,
            summary=normalized_summary,
            beat_ids=self._normalize_text_list(beat_ids, field_name="beat_ids"),
            chapter_ids=self._normalize_text_list(chapter_ids, field_name="chapter_ids"),
            status=self._normalize_text(status, field_name="status"),
            position=self._next_position(project_id, "sequence") if position is None else position,
        )
        return self._sequence_from_record(record)

    def create_chapter_plan(
        self,
        project_id: str,
        *,
        chapter_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        sequence_id: str | None = None,
        active_character_ids: Sequence[str] | None = None,
        continuity_requirements: Sequence[str] | None = None,
        unresolved_questions: Sequence[str] | None = None,
        status: str = "draft",
        position: int | None = None,
    ) -> ChapterPlan:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_sequence_id = self._normalize_optional_text(sequence_id, field_name="sequence_id")
        if normalized_sequence_id is not None:
            self._require_sequence_plan(normalized_project_id, normalized_sequence_id)

        record = self.repository.upsert_chapter_plan(
            chapter_id=self._normalize_text(chapter_id, field_name="chapter_id"),
            project_id=normalized_project_id,
            title=self._normalize_text(title, field_name="title"),
            summary=self._normalize_text(summary, field_name="summary"),
            objective=self._normalize_text(objective, field_name="objective"),
            conflict=self._normalize_text(conflict, field_name="conflict"),
            stakes=self._normalize_text(stakes, field_name="stakes"),
            sequence_id=normalized_sequence_id,
            active_character_ids=self._normalize_text_list(active_character_ids, field_name="active_character_ids"),
            continuity_requirements=self._normalize_text_list(
                continuity_requirements,
                field_name="continuity_requirements",
            ),
            unresolved_questions=self._normalize_text_list(unresolved_questions, field_name="unresolved_questions"),
            status=self._normalize_text(status, field_name="status"),
            position=self._next_position(project_id, "chapter") if position is None else position,
        )
        self._sync_sequence_chapter_ids(normalized_project_id)
        return self._chapter_from_record(record)

    def create_scene_plan(
        self,
        project_id: str,
        *,
        scene_id: str,
        title: str,
        summary: str,
        objective: str,
        conflict: str,
        stakes: str,
        chapter_id: str | None = None,
        active_character_ids: Sequence[str] | None = None,
        continuity_requirements: Sequence[str] | None = None,
        unresolved_questions: Sequence[str] | None = None,
        status: str = "draft",
        position: int | None = None,
    ) -> ScenePlan:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_chapter_id = self._normalize_optional_text(chapter_id, field_name="chapter_id")
        if normalized_chapter_id is not None:
            self._require_chapter_plan(normalized_project_id, normalized_chapter_id)

        record = self.repository.upsert_scene_plan(
            scene_id=self._normalize_text(scene_id, field_name="scene_id"),
            project_id=normalized_project_id,
            title=self._normalize_text(title, field_name="title"),
            summary=self._normalize_text(summary, field_name="summary"),
            objective=self._normalize_text(objective, field_name="objective"),
            conflict=self._normalize_text(conflict, field_name="conflict"),
            stakes=self._normalize_text(stakes, field_name="stakes"),
            chapter_id=normalized_chapter_id,
            active_character_ids=self._normalize_text_list(active_character_ids, field_name="active_character_ids"),
            continuity_requirements=self._normalize_text_list(
                continuity_requirements,
                field_name="continuity_requirements",
            ),
            unresolved_questions=self._normalize_text_list(unresolved_questions, field_name="unresolved_questions"),
            status=self._normalize_text(status, field_name="status"),
            position=self._next_position(project_id, "scene") if position is None else position,
        )
        return self._scene_from_record(record)

    def reorder_plan_objects(
        self,
        project_id: str,
        *,
        plan_kind: PlanKind,
        ordered_plan_ids: Sequence[str],
    ) -> tuple[SequencePlan | ChapterPlan | ScenePlan, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_ids = [self._normalize_text(plan_id, field_name="ordered_plan_ids") for plan_id in ordered_plan_ids]
        if len(normalized_ids) != len(set(normalized_ids)):
            raise PlanningValidationError("ordered_plan_ids must not contain duplicates.")

        if plan_kind == "sequence":
            records = self.repository.list_sequence_plans(normalized_project_id)
            self._ensure_exact_plan_set(records, normalized_ids, kind="sequence")
            for position, sequence_id in enumerate(normalized_ids):
                record = self._require_sequence_plan(normalized_project_id, sequence_id)
                self.repository.upsert_sequence_plan(
                    sequence_id=record.sequence_id,
                    project_id=record.project_id,
                    title=record.title,
                    summary=record.summary,
                    beat_ids=list(record.beat_ids),
                    chapter_ids=list(record.chapter_ids),
                    status=record.status,
                    position=position,
                )
            return tuple(self._sequence_from_record(self.repository.get_sequence_plan(sequence_id)) for sequence_id in normalized_ids)

        if plan_kind == "chapter":
            records = self.repository.list_chapter_plans(normalized_project_id)
            self._ensure_exact_plan_set(records, normalized_ids, kind="chapter")
            for position, chapter_id in enumerate(normalized_ids):
                record = self._require_chapter_plan(normalized_project_id, chapter_id)
                self.repository.upsert_chapter_plan(
                    chapter_id=record.chapter_id,
                    project_id=record.project_id,
                    title=record.title,
                    summary=record.summary,
                    objective=record.objective,
                    conflict=record.conflict,
                    stakes=record.stakes,
                    sequence_id=record.sequence_id,
                    active_character_ids=list(record.active_character_ids),
                    continuity_requirements=list(record.continuity_requirements),
                    unresolved_questions=list(record.unresolved_questions),
                    status=record.status,
                    position=position,
                )
            self._sync_sequence_chapter_ids(normalized_project_id)
            return tuple(self._chapter_from_record(self.repository.get_chapter_plan(chapter_id)) for chapter_id in normalized_ids)

        records = self.repository.list_scene_plans(normalized_project_id)
        self._ensure_exact_plan_set(records, normalized_ids, kind="scene")
        for position, scene_id in enumerate(normalized_ids):
            record = self._require_scene_plan(normalized_project_id, scene_id)
            self.repository.upsert_scene_plan(
                scene_id=record.scene_id,
                project_id=record.project_id,
                title=record.title,
                summary=record.summary,
                objective=record.objective,
                conflict=record.conflict,
                stakes=record.stakes,
                chapter_id=record.chapter_id,
                active_character_ids=list(record.active_character_ids),
                continuity_requirements=list(record.continuity_requirements),
                unresolved_questions=list(record.unresolved_questions),
                status=record.status,
                position=position,
            )
        return tuple(self._scene_from_record(self.repository.get_scene_plan(scene_id)) for scene_id in normalized_ids)

    def add_planning_dependency(
        self,
        project_id: str,
        *,
        dependency_id: str,
        upstream_id: str,
        downstream_id: str,
        dependency_kind: str,
        reason: str | None = None,
    ) -> PlanningDependency:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_upstream_id = self._normalize_text(upstream_id, field_name="upstream_id")
        normalized_downstream_id = self._normalize_text(downstream_id, field_name="downstream_id")
        self._require_plan_object(normalized_project_id, normalized_upstream_id)
        self._require_plan_object(normalized_project_id, normalized_downstream_id)

        record = self.repository.upsert_planning_dependency(
            dependency_id=self._normalize_text(dependency_id, field_name="dependency_id"),
            project_id=normalized_project_id,
            upstream_id=normalized_upstream_id,
            downstream_id=normalized_downstream_id,
            dependency_kind=self._normalize_text(dependency_kind, field_name="dependency_kind"),
            reason=self._normalize_optional_text(reason, field_name="reason"),
        )
        return self._dependency_from_record(record)

    def build_chapter_packet(
        self,
        project_id: str,
        chapter_plan_id: str,
        *,
        packet_id: str | None = None,
        status: str = "draft",
    ) -> ChapterPacket:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        chapter = self._require_chapter_plan(normalized_project_id, chapter_plan_id)
        sequence = None
        if chapter.sequence_id is not None:
            sequence = self._require_sequence_plan(normalized_project_id, chapter.sequence_id)

        scenes = [
            scene
            for scene in self.repository.list_scene_plans(normalized_project_id)
            if scene.chapter_id == chapter.chapter_id
        ]
        relevant_dependency_ids = self._relevant_dependency_ids(
            normalized_project_id,
            chapter_id=chapter.chapter_id,
            sequence_id=chapter.sequence_id,
            scene_ids=[scene.scene_id for scene in scenes],
        )
        included_reference_ids = self._unique_texts(
            [
                chapter.chapter_id,
                sequence.sequence_id if sequence is not None else None,
                *[scene.scene_id for scene in scenes],
                *relevant_dependency_ids,
            ]
        )
        constraints = self._unique_texts(
            [
                f"Chapter objective: {chapter.objective}",
                f"Chapter conflict: {chapter.conflict}",
                f"Chapter stakes: {chapter.stakes}",
                *chapter.continuity_requirements,
                *(requirement for scene in scenes for requirement in scene.continuity_requirements),
                *(
                    f"Dependency {dependency.dependency_id}: {dependency.reason}"
                    for dependency in self._dependencies_for_ids(normalized_project_id, relevant_dependency_ids)
                    if dependency.reason is not None
                ),
            ]
        )
        scene_goals = [scene.objective for scene in scenes] or [chapter.objective]
        record = self.repository.upsert_chapter_packet(
            packet_id=self._normalize_text(
                packet_id or self._chapter_packet_id(normalized_project_id, chapter.chapter_id),
                field_name="packet_id",
            ),
            project_id=normalized_project_id,
            chapter_id=chapter.chapter_id,
            included_reference_ids=included_reference_ids,
            constraints=constraints,
            scene_goals=scene_goals,
            status=self._normalize_text(status, field_name="status"),
        )
        return self._packet_from_record(record)

    def _next_position(self, project_id: str, plan_kind: PlanKind) -> int:
        if plan_kind == "sequence":
            return len(self.repository.list_sequence_plans(self._normalize_text(project_id, field_name="project_id")))
        if plan_kind == "chapter":
            return len(self.repository.list_chapter_plans(self._normalize_text(project_id, field_name="project_id")))
        return len(self.repository.list_scene_plans(self._normalize_text(project_id, field_name="project_id")))

    def _sync_sequence_chapter_ids(self, project_id: str) -> None:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        chapters_by_sequence: dict[str, list[str]] = defaultdict(list)
        for chapter in self.repository.list_chapter_plans(normalized_project_id):
            if chapter.sequence_id is None:
                continue
            chapters_by_sequence[chapter.sequence_id].append(chapter.chapter_id)
        for sequence in self.repository.list_sequence_plans(normalized_project_id):
            ordered_chapter_ids = chapters_by_sequence.get(sequence.sequence_id, [])
            if ordered_chapter_ids == list(sequence.chapter_ids):
                continue
            self.repository.upsert_sequence_plan(
                sequence_id=sequence.sequence_id,
                project_id=sequence.project_id,
                title=sequence.title,
                summary=sequence.summary,
                beat_ids=list(sequence.beat_ids),
                chapter_ids=ordered_chapter_ids,
                status=sequence.status,
                position=sequence.position,
            )

    def _relevant_dependency_ids(
        self,
        project_id: str,
        *,
        chapter_id: str,
        sequence_id: str | None,
        scene_ids: Sequence[str],
    ) -> list[str]:
        scope_ids = {chapter_id, *scene_ids}
        if sequence_id is not None:
            scope_ids.add(sequence_id)
        relevant: list[str] = []
        for dependency in self.repository.list_planning_dependencies(project_id):
            if dependency.upstream_id in scope_ids or dependency.downstream_id in scope_ids:
                relevant.append(dependency.dependency_id)
        return self._unique_texts(relevant)

    def _dependencies_for_ids(
        self,
        project_id: str,
        dependency_ids: Sequence[str],
    ) -> list[PlanningDependencyRecord]:
        dependencies = {dependency.dependency_id: dependency for dependency in self.repository.list_planning_dependencies(project_id)}
        return [dependencies[dependency_id] for dependency_id in dependency_ids if dependency_id in dependencies]

    def _require_plan_object(self, project_id: str, plan_id: str) -> None:
        try:
            self._require_sequence_plan(project_id, plan_id)
            return
        except PlanningNotFoundError:
            pass
        try:
            self._require_chapter_plan(project_id, plan_id)
            return
        except PlanningNotFoundError:
            pass
        try:
            self._require_scene_plan(project_id, plan_id)
            return
        except PlanningNotFoundError as exc:
            raise PlanningNotFoundError(plan_id) from exc

    def _require_sequence_plan(self, project_id: str, sequence_id: str):
        try:
            record = self.repository.get_sequence_plan(sequence_id)
        except KeyError as exc:
            raise PlanningNotFoundError(sequence_id) from exc
        if record.project_id != project_id:
            raise PlanningNotFoundError(sequence_id)
        return record

    def _require_chapter_plan(self, project_id: str, chapter_id: str):
        try:
            record = self.repository.get_chapter_plan(chapter_id)
        except KeyError as exc:
            raise PlanningNotFoundError(chapter_id) from exc
        if record.project_id != project_id:
            raise PlanningNotFoundError(chapter_id)
        return record

    def _require_scene_plan(self, project_id: str, scene_id: str):
        try:
            record = self.repository.get_scene_plan(scene_id)
        except KeyError as exc:
            raise PlanningNotFoundError(scene_id) from exc
        if record.project_id != project_id:
            raise PlanningNotFoundError(scene_id)
        return record

    def _ensure_exact_plan_set(self, records: Sequence[object], ordered_ids: Sequence[str], *, kind: str) -> None:
        existing_ids = {getattr(record, f"{kind}_id") for record in records}
        if existing_ids != set(ordered_ids):
            raise PlanningValidationError(f"ordered_plan_ids must contain exactly the existing {kind} ids.")

    def _sequence_from_record(self, record) -> SequencePlan:
        return SequencePlan(
            sequence_id=record.sequence_id,
            project_id=record.project_id,
            title=record.title,
            summary=record.summary,
            beat_ids=list(record.beat_ids),
            chapter_ids=list(record.chapter_ids),
            status=record.status,
        )

    def _chapter_from_record(self, record) -> ChapterPlan:
        return ChapterPlan(
            chapter_id=record.chapter_id,
            project_id=record.project_id,
            title=record.title,
            summary=record.summary,
            sequence_id=record.sequence_id,
            objective=record.objective,
            conflict=record.conflict,
            stakes=record.stakes,
            active_character_ids=list(record.active_character_ids),
            continuity_requirements=list(record.continuity_requirements),
            unresolved_questions=list(record.unresolved_questions),
            status=record.status,
        )

    def _scene_from_record(self, record) -> ScenePlan:
        return ScenePlan(
            scene_id=record.scene_id,
            project_id=record.project_id,
            title=record.title,
            summary=record.summary,
            chapter_id=record.chapter_id,
            objective=record.objective,
            conflict=record.conflict,
            stakes=record.stakes,
            active_character_ids=list(record.active_character_ids),
            continuity_requirements=list(record.continuity_requirements),
            unresolved_questions=list(record.unresolved_questions),
            status=record.status,
        )

    def _packet_from_record(self, record) -> ChapterPacket:
        return ChapterPacket(
            packet_id=record.packet_id,
            project_id=record.project_id,
            chapter_id=record.chapter_id,
            included_reference_ids=list(record.included_reference_ids),
            constraints=list(record.constraints),
            scene_goals=list(record.scene_goals),
            status=record.status,
        )

    def _dependency_from_record(self, record) -> PlanningDependency:
        return PlanningDependency(
            dependency_id=record.dependency_id,
            project_id=record.project_id,
            upstream_id=record.upstream_id,
            downstream_id=record.downstream_id,
            dependency_kind=record.dependency_kind,
            reason=record.reason,
        )

    def _chapter_packet_id(self, project_id: str, chapter_id: str) -> str:
        return f"{project_id}:{chapter_id}:packet"

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _normalize_optional_text(self, value: object | None, *, field_name: str) -> str | None:
        if value is None:
            return None
        return self._normalize_text(value, field_name=field_name)

    def _normalize_text_list(self, values: Sequence[str] | None, *, field_name: str) -> list[str]:
        if values is None:
            return []
        if isinstance(values, str):
            values = [values]
        return self._unique_texts([self._normalize_text(value, field_name=field_name) for value in values])

    def _unique_texts(self, values: Sequence[str | None]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            if value is None:
                continue
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
        return unique
