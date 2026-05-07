from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID

from app.persistence.story_development import (
    FoundationRevisionRecord,
    StoryDevelopmentRepository,
)
from app.schemas.story_development import FoundationProfile, FoundationRevision
from app.settings import settings


FOUNDATION_FIELDS: tuple[str, ...] = (
    "premise",
    "logline",
    "thematic_spine",
    "emotional_promise",
    "tone_and_voice_direction",
    "target_audience",
    "narrative_constraints",
    "complexity_level",
    "success_definition",
)

IMPACT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("story_arc", ("premise", "logline", "thematic_spine", "success_definition")),
    ("character_background", ("thematic_spine", "emotional_promise", "tone_and_voice_direction")),
    ("world_bible", ("narrative_constraints", "complexity_level")),
    ("planning", ("premise", "logline", "thematic_spine", "narrative_constraints", "complexity_level", "success_definition")),
    ("drafting", FOUNDATION_FIELDS),
    ("review", ("emotional_promise", "tone_and_voice_direction", "target_audience", "success_definition")),
)


def _normalize_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _normalize_optional_text(value: object | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, field_name=field_name)


def _lenient_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value.strip()


def _normalize_text_list(value: object, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values: Sequence[object] = (value,)
    elif isinstance(value, Sequence):
        values = value
    else:
        raise TypeError(f"{field_name} must be a sequence of strings")
    return tuple(_normalize_text(item, field_name=field_name) for item in values)


def _foundation_id(project_id: str) -> str:
    return f"foundation:{project_id}"


def _revision_id(project_id: str, revision_number: int) -> str:
    return f"{_foundation_id(project_id)}:revision:{revision_number:03d}"


def _summarize_changed_fields(changed_fields: Sequence[str], *, initial: bool) -> str:
    if initial:
        return "Initial foundation profile"
    if not changed_fields:
        return "Foundation revision with no field changes"
    if len(changed_fields) == 1:
        return f"Updated {changed_fields[0]}"
    if len(changed_fields) == 2:
        return f"Updated {changed_fields[0]} and {changed_fields[1]}"
    return "Updated " + ", ".join(changed_fields[:-1]) + f", and {changed_fields[-1]}"


def _changed_fields(previous: FoundationProfileInput | None, current: FoundationProfileInput) -> tuple[str, ...]:
    if previous is None:
        return FOUNDATION_FIELDS
    changed: list[str] = []
    for field_name in FOUNDATION_FIELDS:
        if getattr(previous, field_name) != getattr(current, field_name):
            changed.append(field_name)
    return tuple(changed)


def _impact_reason(impacted_area: str, changed_fields: Sequence[str]) -> str:
    field_list = ", ".join(changed_fields)
    return f"Changed {field_list}; review {impacted_area.replace('_', ' ')}."


@dataclass(frozen=True)
class FoundationProfileInput:
    premise: str
    logline: str
    thematic_spine: str
    emotional_promise: str
    tone_and_voice_direction: str
    target_audience: str
    narrative_constraints: tuple[str, ...]
    complexity_level: str
    success_definition: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FoundationProfileInput":
        return cls(
            premise=_normalize_text(payload["premise"], field_name="premise"),
            logline=_normalize_text(payload["logline"], field_name="logline"),
            thematic_spine=_lenient_text(payload.get("thematic_spine", ""), field_name="thematic_spine"),
            emotional_promise=_lenient_text(payload.get("emotional_promise", ""), field_name="emotional_promise"),
            tone_and_voice_direction=_lenient_text(
                payload.get("tone_and_voice_direction", ""), field_name="tone_and_voice_direction"
            ),
            target_audience=_lenient_text(payload.get("target_audience", ""), field_name="target_audience"),
            narrative_constraints=_normalize_text_list(payload.get("narrative_constraints", ()), field_name="narrative_constraints"),
            complexity_level=_lenient_text(payload.get("complexity_level", ""), field_name="complexity_level"),
            success_definition=_lenient_text(payload.get("success_definition", ""), field_name="success_definition"),
        )

    @classmethod
    def from_schema(cls, profile: FoundationProfile) -> "FoundationProfileInput":
        return cls(
            premise=profile.premise,
            logline=profile.logline,
            thematic_spine=profile.thematic_spine,
            emotional_promise=profile.emotional_promise,
            tone_and_voice_direction=profile.tone_and_voice_direction,
            target_audience=profile.target_audience,
            narrative_constraints=tuple(profile.narrative_constraints),
            complexity_level=profile.complexity_level,
            success_definition=profile.success_definition,
        )

    def to_repo_kwargs(self) -> dict[str, Any]:
        return {
            "premise": self.premise,
            "logline": self.logline,
            "thematic_spine": self.thematic_spine,
            "emotional_promise": self.emotional_promise,
            "tone_direction": self.tone_and_voice_direction,
            "target_audience": self.target_audience,
            "narrative_constraints": list(self.narrative_constraints),
            "complexity_level": self.complexity_level,
            "success_definition": self.success_definition,
        }

    def merged_with(self, patch: "FoundationProfilePatch") -> "FoundationProfileInput":
        return FoundationProfileInput(
            premise=patch.premise if patch.premise is not None else self.premise,
            logline=patch.logline if patch.logline is not None else self.logline,
            thematic_spine=patch.thematic_spine if patch.thematic_spine is not None else self.thematic_spine,
            emotional_promise=patch.emotional_promise if patch.emotional_promise is not None else self.emotional_promise,
            tone_and_voice_direction=(
                patch.tone_and_voice_direction
                if patch.tone_and_voice_direction is not None
                else self.tone_and_voice_direction
            ),
            target_audience=patch.target_audience if patch.target_audience is not None else self.target_audience,
            narrative_constraints=(
                patch.narrative_constraints
                if patch.narrative_constraints is not None
                else self.narrative_constraints
            ),
            complexity_level=patch.complexity_level if patch.complexity_level is not None else self.complexity_level,
            success_definition=patch.success_definition if patch.success_definition is not None else self.success_definition,
        )


@dataclass(frozen=True)
class FoundationProfilePatch:
    premise: str | None = None
    logline: str | None = None
    thematic_spine: str | None = None
    emotional_promise: str | None = None
    tone_and_voice_direction: str | None = None
    target_audience: str | None = None
    narrative_constraints: tuple[str, ...] | None = None
    complexity_level: str | None = None
    success_definition: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FoundationProfilePatch":
        return cls(
            premise=_normalize_optional_text(payload.get("premise"), field_name="premise"),
            logline=_normalize_optional_text(payload.get("logline"), field_name="logline"),
            thematic_spine=_normalize_optional_text(payload.get("thematic_spine"), field_name="thematic_spine"),
            emotional_promise=_normalize_optional_text(payload.get("emotional_promise"), field_name="emotional_promise"),
            tone_and_voice_direction=_normalize_optional_text(
                payload.get("tone_and_voice_direction"),
                field_name="tone_and_voice_direction",
            ),
            target_audience=_normalize_optional_text(payload.get("target_audience"), field_name="target_audience"),
            narrative_constraints=(
                None
                if "narrative_constraints" not in payload
                else _normalize_text_list(payload.get("narrative_constraints"), field_name="narrative_constraints")
            ),
            complexity_level=_normalize_optional_text(payload.get("complexity_level"), field_name="complexity_level"),
            success_definition=_normalize_optional_text(payload.get("success_definition"), field_name="success_definition"),
        )

    def is_empty(self) -> bool:
        return all(
            value is None
            for value in (
                self.premise,
                self.logline,
                self.thematic_spine,
                self.emotional_promise,
                self.tone_and_voice_direction,
                self.target_audience,
                self.narrative_constraints,
                self.complexity_level,
                self.success_definition,
            )
        )


@dataclass(frozen=True)
class FoundationDownstreamReviewCue:
    impacted_area: str
    reason: str
    triggering_revision_id: str
    triggering_fields: tuple[str, ...]


@dataclass(frozen=True)
class FoundationReadResult:
    project_id: str
    foundation_id: str
    active_profile: FoundationProfile | None
    current_revision_id: str | None
    revision_history: tuple[FoundationRevision, ...]
    downstream_review_cues: tuple[FoundationDownstreamReviewCue, ...]


@dataclass(frozen=True)
class FoundationWriteResult(FoundationReadResult):
    created_revision: FoundationRevision


class FoundationServiceError(ValueError):
    pass


class FoundationNotFoundError(FoundationServiceError):
    pass


class FoundationValidationError(FoundationServiceError):
    pass


class FoundationService:
    def __init__(
        self,
        repository: StoryDevelopmentRepository | None = None,
        *,
        db_path: Path | None = None,
    ) -> None:
        if repository is not None and db_path is not None:
            raise ValueError("Pass either repository or db_path, not both.")
        if repository is None:
            resolved_db_path = db_path or settings.operations_db_path
            repository = StoryDevelopmentRepository(resolved_db_path)
        self.repository = repository

    def read_active_foundation(self, project_id: str | UUID) -> FoundationReadResult:
        project_key = str(project_id)
        foundation_id = _foundation_id(project_key)
        revision_records = self.repository.list_foundation_revisions(project_key)
        revisions = tuple(self._to_revision(project_key, record) for record in revision_records)
        active_revision = revisions[-1] if revisions else None
        cues = self._build_downstream_review_cues(project_key, revision_records)
        return FoundationReadResult(
            project_id=project_key,
            foundation_id=foundation_id,
            active_profile=active_revision.snapshot if active_revision is not None else None,
            current_revision_id=active_revision.revision_id if active_revision is not None else None,
            revision_history=revisions,
            downstream_review_cues=cues,
        )

    def list_foundation_revisions(self, project_id: str | UUID) -> tuple[FoundationRevision, ...]:
        return self.read_active_foundation(project_id).revision_history

    def list_downstream_review_cues(self, project_id: str | UUID) -> tuple[FoundationDownstreamReviewCue, ...]:
        return self.read_active_foundation(project_id).downstream_review_cues

    def create_foundation_revision(
        self,
        project_id: str | UUID,
        foundation: FoundationProfileInput | Mapping[str, Any],
    ) -> FoundationWriteResult:
        project_key = str(project_id)
        input_profile = self._coerce_input(foundation)
        revision_record = self.repository.upsert_foundation_profile(
            project_id=project_key,
            **input_profile.to_repo_kwargs(),
        )
        created_revision = self._to_revision(project_key, revision_record)
        read_result = self.read_active_foundation(project_key)
        return FoundationWriteResult(
            project_id=read_result.project_id,
            foundation_id=read_result.foundation_id,
            active_profile=read_result.active_profile,
            current_revision_id=read_result.current_revision_id,
            revision_history=read_result.revision_history,
            downstream_review_cues=read_result.downstream_review_cues,
            created_revision=created_revision,
        )

    def update_foundation_revision(
        self,
        project_id: str | UUID,
        changes: FoundationProfilePatch | Mapping[str, Any],
    ) -> FoundationWriteResult:
        project_key = str(project_id)
        current = self.read_active_foundation(project_key)
        if current.active_profile is None:
            raise FoundationNotFoundError(f"No active foundation exists for project_id={project_key}")
        patch = self._coerce_patch(changes)
        if patch.is_empty():
            raise FoundationValidationError("At least one foundation field change is required.")
        current_input = FoundationProfileInput.from_schema(current.active_profile)
        merged_input = current_input.merged_with(patch)
        return self.create_foundation_revision(project_key, merged_input)

    def _coerce_input(self, foundation: FoundationProfileInput | Mapping[str, Any]) -> FoundationProfileInput:
        if isinstance(foundation, FoundationProfileInput):
            return foundation
        try:
            return FoundationProfileInput.from_mapping(foundation)
        except KeyError as exc:
            # Missing required key in input mapping
            raise FoundationValidationError(f"Missing required field in foundation input: {exc}") from exc
        except (TypeError, ValueError) as exc:
            # Type/value errors during field coercion - likely invalid input data
            raise FoundationValidationError(f"Invalid foundation input data: {exc}") from exc

    def _coerce_patch(self, changes: FoundationProfilePatch | Mapping[str, Any]) -> FoundationProfilePatch:
        if isinstance(changes, FoundationProfilePatch):
            return changes
        try:
            return FoundationProfilePatch.from_mapping(changes)
        except KeyError as exc:
            # Missing required key in patch mapping
            raise FoundationValidationError(f"Missing required field in foundation patch: {exc}") from exc
        except (TypeError, ValueError) as exc:
            # Type/value errors during field coercion - likely invalid input data
            raise FoundationValidationError(f"Invalid foundation patch data: {exc}") from exc

    def _to_profile(self, project_id: str, record: FoundationRevisionRecord) -> FoundationProfile:
        foundation_id = _foundation_id(project_id)
        return FoundationProfile(
            foundation_id=foundation_id,
            project_id=project_id,
            premise=record.premise,
            logline=record.logline,
            thematic_spine=record.thematic_spine,
            emotional_promise=record.emotional_promise,
            tone_and_voice_direction=record.tone_direction,
            target_audience=record.target_audience,
            narrative_constraints=list(record.narrative_constraints),
            complexity_level=record.complexity_level,
            success_definition=record.success_definition,
            version=record.revision_number,
        )

    def _to_revision(self, project_id: str, record: FoundationRevisionRecord) -> FoundationRevision:
        foundation_id = _foundation_id(project_id)
        return FoundationRevision(
            revision_id=_revision_id(project_id, record.revision_number),
            foundation_id=foundation_id,
            snapshot=self._to_profile(project_id, record),
            change_summary=_summarize_changed_fields(self._record_changed_fields(record, project_id), initial=record.revision_number == 1),
        )

    def _build_downstream_review_cues(
        self,
        project_id: str,
        revision_records: Sequence[FoundationRevisionRecord],
    ) -> tuple[FoundationDownstreamReviewCue, ...]:
        if not revision_records:
            return ()

        current_record = revision_records[-1]
        previous_record = revision_records[-2] if len(revision_records) > 1 else None
        current_profile = FoundationProfileInput.from_schema(self._to_profile(project_id, current_record))
        previous_profile = (
            FoundationProfileInput.from_schema(self._to_profile(project_id, previous_record))
            if previous_record is not None
            else None
        )
        changed_fields = _changed_fields(previous_profile, current_profile)
        revision_id = _revision_id(project_id, current_record.revision_number)
        cues: list[FoundationDownstreamReviewCue] = []
        for impacted_area, trigger_fields in IMPACT_RULES:
            matched_fields = tuple(field for field in trigger_fields if field in changed_fields)
            if not matched_fields:
                continue
            cues.append(
                FoundationDownstreamReviewCue(
                    impacted_area=impacted_area,
                    reason=_impact_reason(impacted_area, matched_fields),
                    triggering_revision_id=revision_id,
                    triggering_fields=matched_fields,
                )
            )
        return tuple(cues)

    def _record_changed_fields(self, record: FoundationRevisionRecord, project_id: str) -> tuple[str, ...]:
        revision_number = record.revision_number
        if revision_number <= 1:
            return FOUNDATION_FIELDS
        all_records = self.repository.list_foundation_revisions(project_id)
        if len(all_records) < 2:
            return FOUNDATION_FIELDS
        previous_record = all_records[-2]
        previous_profile = FoundationProfileInput.from_schema(self._to_profile(project_id, previous_record))
        current_profile = FoundationProfileInput.from_schema(self._to_profile(project_id, record))
        return _changed_fields(previous_profile, current_profile)
