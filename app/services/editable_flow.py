from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Protocol

from app.schemas import (
    StoryFlowDefinition,
    StoryFlowStage,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
)


DEFAULT_FLOW_STAGES: tuple[tuple[str, str, str], ...] = (
    ("brainstorm", "Brainstorm", "Capture raw ideas and premise sparks."),
    ("foundation", "Story Foundation", "Define the stable promise of the story."),
    ("character", "Character Background", "Build character motivation, flaw, and change."),
    ("world_bible", "World Bible", "Store canon, rules, and continuity anchors."),
    ("arc_selection", "Story Arc Selection", "Compare arc options and choose a planning lens."),
    ("planning", "Sequence and Chapter Planning", "Turn story intent into beats and scenes."),
    ("drafting", "Drafting", "Generate and revise manuscript prose."),
    ("review", "Review and Suggestions", "Inspect findings and revision suggestions."),
)


@dataclass(frozen=True, slots=True)
class EditableFlowDeletionCheck:
    allowed: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EditableFlowState:
    flow: StoryFlowDefinition
    custom_stage_ids: frozenset[str]
    next_stage_index: int


class EditableFlowRepository(Protocol):
    def get(self, project_id: str) -> EditableFlowState | None:
        ...

    def save(self, state: EditableFlowState) -> EditableFlowState:
        ...

    def delete(self, project_id: str) -> None:
        ...


class InMemoryEditableFlowRepository:
    def __init__(self) -> None:
        self._flows: dict[str, EditableFlowState] = {}

    def get(self, project_id: str) -> EditableFlowState | None:
        state = self._flows.get(project_id)
        return deepcopy(state) if state is not None else None

    def save(self, state: EditableFlowState) -> EditableFlowState:
        stored = deepcopy(state)
        self._flows[state.flow.project_id] = stored
        return deepcopy(stored)

    def delete(self, project_id: str) -> None:
        self._flows.pop(project_id, None)


class EditableFlowError(ValueError):
    pass


class EditableFlowNotFoundError(EditableFlowError):
    pass


class EditableFlowValidationError(EditableFlowError):
    pass


class EditableFlowService:
    def __init__(self, repository: EditableFlowRepository | None = None) -> None:
        self.repository = repository or InMemoryEditableFlowRepository()

    def create_default_flow(self, *, project_id: str, project_name: str) -> StoryFlowDefinition:
        if self.repository.get(project_id) is not None:
            raise EditableFlowValidationError(f"Flow already exists for project_id={project_id}")

        stages: list[StoryFlowStage] = []
        previous_stage_id: str | None = None
        for index, (stage_kind, display_name, description) in enumerate(DEFAULT_FLOW_STAGES, start=1):
            stage_id = self._stage_id(index)
            depends_on = [previous_stage_id] if previous_stage_id is not None else []
            stages.append(
                StoryFlowStage(
                    stage_id=stage_id,
                    stage_kind=stage_kind,
                    display_name=display_name,
                    description=description,
                    position=index - 1,
                    depends_on=depends_on,
                    stage_configuration_state=StoryFlowStageConfigurationState.ENABLED,
                    stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
                )
            )
            previous_stage_id = stage_id

        state = EditableFlowState(
            flow=StoryFlowDefinition(project_id=project_id, project_name=project_name, stages=stages),
            custom_stage_ids=frozenset(),
            next_stage_index=len(stages) + 1,
        )
        return self.repository.save(state).flow

    def get_flow(self, project_id: str) -> StoryFlowDefinition:
        return self._require_state(project_id).flow

    def add_custom_stage(
        self,
        *,
        project_id: str,
        display_name: str,
        description: str | None = None,
        stage_kind: str = "custom",
        depends_on: tuple[str, ...] | list[str] | None = None,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        insert_after_stage_id: str | None = None,
    ) -> StoryFlowStage:
        state = self._require_state(project_id)
        depends_on_ids = list(depends_on or [])
        if insert_after_stage_id is not None:
            self._stage_by_id(state.flow, insert_after_stage_id)
            if not depends_on_ids:
                depends_on_ids = [insert_after_stage_id]
        self._validate_dependencies(state.flow, depends_on_ids)

        stage_id = self._stage_id(state.next_stage_index)
        stages = self._ordered_stages(state.flow)
        insert_at = len(stages) if insert_after_stage_id is None else self._index_for_stage(stages, insert_after_stage_id) + 1
        new_stage = StoryFlowStage(
            stage_id=stage_id,
            stage_kind=stage_kind,
            display_name=display_name,
            description=description,
            position=insert_at,
            depends_on=depends_on_ids,
            writer_notes=writer_notes,
            custom_prompt_guidance=custom_prompt_guidance,
            stage_configuration_state=StoryFlowStageConfigurationState.ENABLED,
            stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
        )
        stages.insert(insert_at, new_stage)
        saved = self.repository.save(
            EditableFlowState(
                flow=self._rebuild_flow(state.flow, stages),
                custom_stage_ids=state.custom_stage_ids | {stage_id},
                next_stage_index=state.next_stage_index + 1,
            )
        )
        return self._stage_by_id(saved.flow, stage_id)

    def rename_stage(self, *, project_id: str, stage_id: str, display_name: str) -> StoryFlowStage:
        return self._update_stage(project_id, stage_id, display_name=display_name)

    def redefine_stage(
        self,
        *,
        project_id: str,
        stage_id: str,
        display_name: str | None = None,
        description: str | None = None,
        depends_on: tuple[str, ...] | list[str] | None = None,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        stage_kind: str | None = None,
        stage_configuration_state: str | None = None,
    ) -> StoryFlowStage:
        state = self._require_state(project_id)
        if depends_on is not None:
            candidate_deps = list(depends_on)
            self._validate_dependencies(state.flow, candidate_deps, allow_self=stage_id)
        config_state = None
        if stage_configuration_state is not None:
            config_state = StoryFlowStageConfigurationState(stage_configuration_state)
        return self._update_stage(
            project_id,
            stage_id,
            display_name=display_name,
            description=description,
            depends_on=list(depends_on) if depends_on is not None else None,
            writer_notes=writer_notes,
            custom_prompt_guidance=custom_prompt_guidance,
            stage_kind=stage_kind,
            stage_configuration_state=config_state,
        )

    def reorder_stages(self, *, project_id: str, stage_order: list[str] | tuple[str, ...]) -> StoryFlowDefinition:
        state = self._require_state(project_id)
        ordered_ids = list(stage_order)
        current_ids = [stage.stage_id for stage in self._ordered_stages(state.flow)]
        if set(ordered_ids) != set(current_ids) or len(ordered_ids) != len(current_ids):
            raise EditableFlowValidationError("Reorder list must contain exactly the current stage ids once each.")
        if ordered_ids == current_ids:
            return state.flow

        stage_map = {stage.stage_id: stage for stage in state.flow.stages}
        reordered = [stage_map[stage_id] for stage_id in ordered_ids]
        saved = self.repository.save(
            EditableFlowState(
                flow=self._rebuild_flow(state.flow, reordered),
                custom_stage_ids=state.custom_stage_ids,
                next_stage_index=state.next_stage_index,
            )
        )
        return saved.flow

    def disable_stage(self, *, project_id: str, stage_id: str) -> StoryFlowStage:
        return self._update_stage(
            project_id,
            stage_id,
            stage_configuration_state=StoryFlowStageConfigurationState.DISABLED,
        )

    def archive_stage(self, *, project_id: str, stage_id: str) -> StoryFlowStage:
        return self._update_stage(
            project_id,
            stage_id,
            stage_configuration_state=StoryFlowStageConfigurationState.ARCHIVED,
            stage_progress_state=StoryFlowStageProgressState.SUPERSEDED,
        )

    def can_delete_custom_stage(self, *, project_id: str, stage_id: str) -> EditableFlowDeletionCheck:
        state = self._require_state(project_id)
        stage = self._stage_by_id(state.flow, stage_id)
        reasons: list[str] = []
        if stage_id not in state.custom_stage_ids:
            reasons.append("Stage is not custom and cannot be deleted.")
        if stage.stage_configuration_state == StoryFlowStageConfigurationState.ENABLED:
            reasons.append("Stage must be disabled or archived before deletion.")
        dependents = tuple(
            candidate.stage_id for candidate in state.flow.stages if stage_id in candidate.depends_on
        )
        if dependents:
            reasons.append(f"Stage is still referenced by: {', '.join(dependents)}.")
        return EditableFlowDeletionCheck(allowed=not reasons, reasons=tuple(reasons))

    def delete_custom_stage(self, *, project_id: str, stage_id: str) -> StoryFlowStage:
        state = self._require_state(project_id)
        stage = self._stage_by_id(state.flow, stage_id)
        check = self.can_delete_custom_stage(project_id=project_id, stage_id=stage_id)
        if not check.allowed:
            raise EditableFlowValidationError(" ".join(check.reasons))

        kept_stages = [candidate for candidate in self._ordered_stages(state.flow) if candidate.stage_id != stage_id]
        self.repository.save(
            EditableFlowState(
                flow=self._rebuild_flow(state.flow, kept_stages),
                custom_stage_ids=frozenset(item for item in state.custom_stage_ids if item != stage_id),
                next_stage_index=state.next_stage_index,
            )
        )
        return stage

    def list_stages(self, project_id: str) -> list[StoryFlowStage]:
        return self._ordered_stages(self._require_state(project_id).flow)

    def _update_stage(
        self,
        project_id: str,
        stage_id: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        depends_on: list[str] | None = None,
        writer_notes: str | None = None,
        custom_prompt_guidance: str | None = None,
        stage_kind: str | None = None,
        stage_configuration_state: StoryFlowStageConfigurationState | None = None,
        stage_progress_state: StoryFlowStageProgressState | None = None,
    ) -> StoryFlowStage:
        state = self._require_state(project_id)
        stages = self._ordered_stages(state.flow)
        index = self._index_for_stage(stages, stage_id)
        current = stages[index]
        updated = current.model_copy(
            update={
                "display_name": display_name if display_name is not None else current.display_name,
                "description": description if description is not None else current.description,
                "depends_on": depends_on if depends_on is not None else current.depends_on,
                "writer_notes": writer_notes if writer_notes is not None else current.writer_notes,
                "custom_prompt_guidance": (
                    custom_prompt_guidance if custom_prompt_guidance is not None else current.custom_prompt_guidance
                ),
                "stage_kind": stage_kind if stage_kind is not None else current.stage_kind,
                "stage_configuration_state": (
                    stage_configuration_state
                    if stage_configuration_state is not None
                    else current.stage_configuration_state
                ),
                "stage_progress_state": (
                    stage_progress_state if stage_progress_state is not None else current.stage_progress_state
                ),
            }
        )
        stages[index] = updated
        saved = self.repository.save(
            EditableFlowState(
                flow=self._rebuild_flow(state.flow, stages),
                custom_stage_ids=state.custom_stage_ids,
                next_stage_index=state.next_stage_index,
            )
        )
        return self._stage_by_id(saved.flow, stage_id)

    def _require_state(self, project_id: str) -> EditableFlowState:
        state = self.repository.get(project_id)
        if state is None:
            raise EditableFlowNotFoundError(f"No editable flow exists for project_id={project_id}")
        return state

    def _validate_dependencies(
        self,
        flow: StoryFlowDefinition,
        depends_on: list[str],
        *,
        allow_self: str | None = None,
    ) -> None:
        known_ids = {stage.stage_id for stage in flow.stages}
        invalid = sorted(dep for dep in depends_on if dep not in known_ids or dep == allow_self)
        if invalid:
            raise EditableFlowValidationError(f"Invalid stage dependency references: {', '.join(invalid)}.")

    @staticmethod
    def _ordered_stages(flow: StoryFlowDefinition) -> list[StoryFlowStage]:
        return sorted(flow.stages, key=lambda stage: (stage.position, stage.stage_id))

    @staticmethod
    def _index_for_stage(stages: list[StoryFlowStage], stage_id: str) -> int:
        for index, stage in enumerate(stages):
            if stage.stage_id == stage_id:
                return index
        raise EditableFlowNotFoundError(f"Stage not found: {stage_id}")

    @staticmethod
    def _stage_by_id(flow: StoryFlowDefinition, stage_id: str) -> StoryFlowStage:
        for stage in flow.stages:
            if stage.stage_id == stage_id:
                return stage
        raise EditableFlowNotFoundError(f"Stage not found: {stage_id}")

    @staticmethod
    def _rebuild_flow(flow: StoryFlowDefinition, ordered_stages: list[StoryFlowStage]) -> StoryFlowDefinition:
        normalized = [
            stage.model_copy(update={"position": position}) for position, stage in enumerate(ordered_stages)
        ]
        return flow.model_copy(update={"stages": normalized})

    @staticmethod
    def _stage_id(index: int) -> str:
        return f"stage-{index:03d}"
