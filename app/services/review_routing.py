from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.persistence.story_development import (
    CheckerFindingRecord,
    InspectRunLinkRecord,
    ReviewDecisionRecord,
)
from app.persistence.story_development.contracts import ReviewRepository
from app.schemas import (
    ChapterPacket,
    CheckerFinding,
    InspectRunLink,
    ManuscriptDocument,
    ReviewDecision,
    RevisionSuggestion,
    StoryObjectType,
)
from app.services.drafting import DraftingService
from app.services.planning import PlanningService


ALLOWED_REVIEW_DECISIONS = ("accept", "defer", "escalate", "reject", "refine")


@dataclass(frozen=True)
class DraftingRoutingResult:
    finding: CheckerFinding
    decision: ReviewDecision
    revision_suggestion: RevisionSuggestion
    inspect_link: InspectRunLink


@dataclass(frozen=True)
class PlanningRoutingResult:
    finding: CheckerFinding
    decision: ReviewDecision
    chapter_packet: ChapterPacket
    inspect_link: InspectRunLink


class ReviewRoutingServiceError(ValueError):
    pass


class ReviewRoutingNotFoundError(ReviewRoutingServiceError):
    pass


class ReviewRoutingValidationError(ReviewRoutingServiceError):
    pass


class ReviewRoutingService:
    def __init__(
        self,
        repository: ReviewRepository,
        *,
        drafting_service: DraftingService | None = None,
        planning_service: PlanningService | None = None,
    ) -> None:
        self.repository = repository
        self.drafting_service = drafting_service or DraftingService(repository)
        self.planning_service = planning_service or PlanningService(repository)

    def record_review_decision(
        self,
        project_id: str,
        *,
        decision_id: str,
        target_kind: StoryObjectType | str,
        target_id: str,
        decision: str,
        notes: str | None = None,
        source_context: Sequence[str] | None = None,
    ) -> ReviewDecision:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_target_kind = self._normalize_object_type(target_kind, field_name="target_kind")
        normalized_target_id = self._normalize_text(target_id, field_name="target_id")
        self._require_target(normalized_project_id, normalized_target_kind, normalized_target_id)

        record = self.repository.upsert_review_decision(
            decision_id=self._normalize_text(decision_id, field_name="decision_id"),
            project_id=normalized_project_id,
            target_id=normalized_target_id,
            target_kind=normalized_target_kind.value,
            decision=self._normalize_decision(decision),
            notes=self._normalize_optional_text(notes, field_name="notes"),
            source_context=self._normalize_text_list(source_context, field_name="source_context"),
        )
        return self._decision_from_record(record)

    def create_inspect_link(
        self,
        project_id: str,
        *,
        link_id: str,
        object_kind: str,
        object_id: str,
        logical_run_id: str,
        run_id: str,
        run_kind: str,
        attempt_number: int | None = None,
        label: str | None = None,
    ) -> InspectRunLink:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_object_kind = self._normalize_text(object_kind, field_name="object_kind")
        normalized_object_id = self._normalize_text(object_id, field_name="object_id")

        record = self.repository.upsert_inspect_run_link(
            link_id=self._normalize_text(link_id, field_name="link_id"),
            project_id=normalized_project_id,
            object_kind=normalized_object_kind,
            object_id=normalized_object_id,
            logical_run_id=self._normalize_text(logical_run_id, field_name="logical_run_id"),
            run_id=self._normalize_text(run_id, field_name="run_id"),
            run_kind=self._normalize_text(run_kind, field_name="run_kind"),
            attempt_number=attempt_number,
            label=self._normalize_optional_text(label, field_name="label"),
        )
        return self._inspect_link_from_record(record)

    def list_checker_findings(
        self,
        project_id: str,
        *,
        source_object_kind: StoryObjectType | str | None = None,
        source_object_id: str | None = None,
    ) -> tuple[CheckerFinding, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self._list_checker_finding_records(
            normalized_project_id,
            source_object_kind=source_object_kind,
            source_object_id=source_object_id,
        )
        return tuple(self._finding_from_record(record) for record in records)

    def get_checker_finding(self, project_id: str, *, finding_id: str) -> CheckerFinding:
        return self._require_checker_finding(self._normalize_text(project_id, field_name="project_id"), finding_id)

    def list_review_decisions(
        self,
        project_id: str,
        *,
        target_kind: StoryObjectType | str | None = None,
        target_id: str | None = None,
    ) -> tuple[ReviewDecision, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self._list_review_decision_records(
            normalized_project_id,
            target_kind=target_kind,
            target_id=target_id,
        )
        return tuple(self._decision_from_record(record) for record in records)

    def get_review_decision(self, project_id: str, *, decision_id: str) -> ReviewDecision:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_decision_id = self._normalize_text(decision_id, field_name="decision_id")
        try:
            record = self.repository.get_review_decision(normalized_decision_id)
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(normalized_decision_id) from exc
        if record.project_id != normalized_project_id:
            raise ReviewRoutingNotFoundError(normalized_decision_id)
        return self._decision_from_record(record)

    def list_inspect_run_links(
        self,
        project_id: str,
        *,
        object_kind: StoryObjectType | str | None = None,
        object_id: str | None = None,
        run_id: str | None = None,
        logical_run_id: str | None = None,
    ) -> tuple[InspectRunLink, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        records = self._list_inspect_run_link_records(
            normalized_project_id,
            object_kind=object_kind,
            object_id=object_id,
            run_id=run_id,
            logical_run_id=logical_run_id,
        )
        return tuple(self._inspect_link_from_record(record) for record in records)

    def get_inspect_run_link(self, project_id: str, *, link_id: str) -> InspectRunLink:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_link_id = self._normalize_text(link_id, field_name="link_id")
        try:
            record = self.repository.get_inspect_run_link(normalized_link_id)
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(normalized_link_id) from exc
        if record.project_id != normalized_project_id:
            raise ReviewRoutingNotFoundError(normalized_link_id)
        return self._inspect_link_from_record(record)

    def route_finding_to_drafting(
        self,
        project_id: str,
        *,
        finding_id: str,
        target_document_id: str,
        decision_id: str,
        suggestion_id: str,
        proposed_text: str,
        decision: str = "refine",
        source_text: str | None = None,
        rationale: str | None = None,
        inspect_link_id: str | None = None,
        logical_run_id: str | None = None,
        run_id: str | None = None,
        run_kind: str = "review-routing",
        label: str | None = None,
        attempt_number: int | None = None,
    ) -> DraftingRoutingResult:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        finding = self._require_checker_finding(normalized_project_id, finding_id)
        manuscript = self._require_manuscript_document(normalized_project_id, target_document_id)
        review_decision = self.record_review_decision(
            normalized_project_id,
            decision_id=decision_id,
            target_kind=StoryObjectType.MANUSCRIPT_DOCUMENT,
            target_id=manuscript.document_id,
            decision=decision,
            notes=self._normalize_optional_text(rationale, field_name="rationale"),
            source_context=self._merge_unique_strings(
                [f"finding:{finding.finding_id}", f"source:{finding.source_object_kind}:{finding.source_object_id}"],
                finding.source_context,
            ),
        )
        revision_suggestion = self.drafting_service.create_revision_suggestion(
            normalized_project_id,
            suggestion_id=suggestion_id,
            target_document_id=manuscript.document_id,
            source_text=self._normalize_text(source_text or manuscript.content, field_name="source_text"),
            proposed_text=self._normalize_text(proposed_text, field_name="proposed_text"),
            rationale=self._normalize_text(
                rationale or self._finding_rationale(finding),
                field_name="rationale",
            ),
            source_context=self._merge_unique_strings(
                [f"finding:{finding.finding_id}", f"decision:{review_decision.decision_id}"],
                finding.source_context,
            ),
        )
        inspect_link = self.create_inspect_link(
            normalized_project_id,
            link_id=inspect_link_id or f"{revision_suggestion.suggestion_id}:inspect",
            object_kind=StoryObjectType.REVISION_SUGGESTION,
            object_id=revision_suggestion.suggestion_id,
            logical_run_id=logical_run_id or finding.finding_id,
            run_id=run_id or review_decision.decision_id,
            run_kind=run_kind,
            label=label or f"Drafting route for {manuscript.document_id}",
            attempt_number=attempt_number,
        )
        return DraftingRoutingResult(
            finding=finding,
            decision=review_decision,
            revision_suggestion=revision_suggestion,
            inspect_link=inspect_link,
        )

    def route_finding_to_planning(
        self,
        project_id: str,
        *,
        finding_id: str,
        target_kind: StoryObjectType | str,
        target_id: str,
        decision_id: str,
        decision: str = "refine",
        packet_id: str | None = None,
        inspect_link_id: str | None = None,
        logical_run_id: str | None = None,
        run_id: str | None = None,
        run_kind: str = "review-routing",
        label: str | None = None,
        attempt_number: int | None = None,
    ) -> PlanningRoutingResult:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_target_kind = self._normalize_object_type(target_kind, field_name="target_kind")
        normalized_target_id = self._normalize_text(target_id, field_name="target_id")
        finding = self._require_checker_finding(normalized_project_id, finding_id)
        chapter_id = self._chapter_id_for_planning_target(normalized_project_id, normalized_target_kind, normalized_target_id)
        self._require_target(normalized_project_id, normalized_target_kind, normalized_target_id)
        review_decision = self.record_review_decision(
            normalized_project_id,
            decision_id=decision_id,
            target_kind=normalized_target_kind,
            target_id=normalized_target_id,
            decision=decision,
            notes=self._finding_rationale(finding),
            source_context=self._merge_unique_strings(
                [f"finding:{finding.finding_id}", f"source:{finding.source_object_kind}:{finding.source_object_id}"],
                finding.source_context,
            ),
        )
        chapter_packet = self.planning_service.build_chapter_packet(
            normalized_project_id,
            chapter_id,
            packet_id=packet_id,
        )
        inspect_link = self.create_inspect_link(
            normalized_project_id,
            link_id=inspect_link_id or f"{chapter_packet.packet_id}:inspect",
            object_kind=StoryObjectType.CHAPTER_PACKET,
            object_id=chapter_packet.packet_id,
            logical_run_id=logical_run_id or finding.finding_id,
            run_id=run_id or review_decision.decision_id,
            run_kind=run_kind,
            label=label or f"Planning route for {normalized_target_id}",
            attempt_number=attempt_number,
        )
        return PlanningRoutingResult(
            finding=finding,
            decision=review_decision,
            chapter_packet=chapter_packet,
            inspect_link=inspect_link,
        )

    def _list_checker_finding_records(
        self,
        project_id: str,
        *,
        source_object_kind: StoryObjectType | str | None = None,
        source_object_id: str | None = None,
    ) -> list[CheckerFindingRecord]:
        if source_object_kind is None and source_object_id is None:
            return list(self.repository.list_checker_findings(project_id))
        if source_object_kind is None or source_object_id is None:
            raise ReviewRoutingValidationError("source_object_kind and source_object_id must be provided together")
        normalized_source_object_kind = self._normalize_object_type(source_object_kind, field_name="source_object_kind")
        normalized_source_object_id = self._normalize_text(source_object_id, field_name="source_object_id")
        return list(
            self.repository.list_checker_findings_for_source(
                project_id,
                source_object_kind=normalized_source_object_kind.value,
                source_object_id=normalized_source_object_id,
            )
        )

    def _list_review_decision_records(
        self,
        project_id: str,
        *,
        target_kind: StoryObjectType | str | None = None,
        target_id: str | None = None,
    ) -> list[ReviewDecisionRecord]:
        if target_kind is None and target_id is None:
            return list(self.repository.list_review_decisions(project_id))
        if target_kind is None or target_id is None:
            raise ReviewRoutingValidationError("target_kind and target_id must be provided together")
        normalized_target_kind = self._normalize_object_type(target_kind, field_name="target_kind")
        normalized_target_id = self._normalize_text(target_id, field_name="target_id")
        return list(
            self.repository.list_review_decisions_for_target(
                project_id,
                target_kind=normalized_target_kind.value,
                target_id=normalized_target_id,
            )
        )

    def _list_inspect_run_link_records(
        self,
        project_id: str,
        *,
        object_kind: StoryObjectType | str | None = None,
        object_id: str | None = None,
        run_id: str | None = None,
        logical_run_id: str | None = None,
    ) -> list[InspectRunLinkRecord]:
        if object_kind is not None or object_id is not None:
            if object_kind is None or object_id is None:
                raise ReviewRoutingValidationError("object_kind and object_id must be provided together")
            if run_id is not None or logical_run_id is not None:
                raise ReviewRoutingValidationError("object filters cannot be combined with run filters")
            normalized_object_kind = self._normalize_object_type(object_kind, field_name="object_kind")
            normalized_object_id = self._normalize_text(object_id, field_name="object_id")
            return list(
                self.repository.list_inspect_run_links_for_object(
                    project_id,
                    object_kind=normalized_object_kind.value,
                    object_id=normalized_object_id,
                )
            )
        if run_id is not None and logical_run_id is not None:
            raise ReviewRoutingValidationError("run_id and logical_run_id must not be provided together")
        if run_id is not None:
            return list(
                self.repository.list_inspect_run_links_for_run(
                    project_id,
                    run_id=self._normalize_text(run_id, field_name="run_id"),
                )
            )
        if logical_run_id is not None:
            return list(
                self.repository.list_inspect_run_links_for_logical_run(
                    project_id,
                    logical_run_id=self._normalize_text(logical_run_id, field_name="logical_run_id"),
                )
            )
        return list(self.repository.list_inspect_run_links(project_id))

    def _require_checker_finding(self, project_id: str, finding_id: str) -> CheckerFinding:
        try:
            record = self.repository.get_checker_finding(self._normalize_text(finding_id, field_name="finding_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(finding_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(finding_id)
        return self._finding_from_record(record)

    def _require_manuscript_document(self, project_id: str, document_id: str) -> ManuscriptDocument:
        try:
            record = self.repository.get_manuscript_document(self._normalize_text(document_id, field_name="document_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(document_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(document_id)
        return ManuscriptDocument.model_validate(
            {
                "document_id": record.document_id,
                "project_id": record.project_id,
                "title": record.title,
                "content": record.content,
                "chapter_id": record.chapter_id,
                "scene_id": record.scene_id,
                "current_draft_artifact_id": record.current_draft_artifact_id,
                "version": record.version,
            }
        )

    def _chapter_id_for_planning_target(
        self,
        project_id: str,
        target_kind: StoryObjectType,
        target_id: str,
    ) -> str:
        if target_kind == StoryObjectType.CHAPTER_PLAN:
            self._require_chapter_plan(project_id, target_id)
            return target_id
        if target_kind == StoryObjectType.SCENE_PLAN:
            scene = self._require_scene_plan(project_id, target_id)
            if scene.chapter_id is None:
                raise ReviewRoutingValidationError("scene targets must belong to a chapter")
            return scene.chapter_id
        raise ReviewRoutingValidationError("planning routing currently supports chapter or scene targets")

    def _require_target(self, project_id: str, target_kind: StoryObjectType, target_id: str) -> object:
        if target_kind == StoryObjectType.CHECKER_FINDING:
            return self._require_checker_finding(project_id, target_id)
        if target_kind == StoryObjectType.MANUSCRIPT_DOCUMENT:
            return self._require_manuscript_document(project_id, target_id)
        if target_kind == StoryObjectType.DRAFT_ARTIFACT:
            return self._require_draft_artifact(project_id, target_id)
        if target_kind == StoryObjectType.REVISION_SUGGESTION:
            return self._require_revision_suggestion(project_id, target_id)
        if target_kind == StoryObjectType.CHAPTER_PLAN:
            return self._require_chapter_plan(project_id, target_id)
        if target_kind == StoryObjectType.SCENE_PLAN:
            return self._require_scene_plan(project_id, target_id)
        if target_kind == StoryObjectType.SEQUENCE_PLAN:
            return self._require_sequence_plan(project_id, target_id)
        if target_kind == StoryObjectType.BEAT_PLAN:
            return self._require_beat_plan(project_id, target_id)
        if target_kind == StoryObjectType.CHAPTER_PACKET:
            return self._require_chapter_packet(project_id, target_id)
        if target_kind == StoryObjectType.ARC_SELECTION:
            return self._require_arc_selection(project_id, target_id)
        if target_kind == StoryObjectType.ARC_COMPARISON_RECORD:
            return self._require_arc_comparison(project_id, target_id)
        if target_kind == StoryObjectType.STORY_DECISION_NODE:
            return self._require_story_decision_node(project_id, target_id)
        if target_kind == StoryObjectType.REVIEW_DECISION:
            return self._require_review_decision(project_id, target_id)
        if target_kind == StoryObjectType.INSPECT_RUN_LINK:
            return self._require_inspect_run_link(project_id, target_id)
        raise ReviewRoutingValidationError(f"unsupported target kind: {target_kind.value}")

    def _require_draft_artifact(self, project_id: str, artifact_id: str):
        try:
            record = self.repository.get_draft_artifact(self._normalize_text(artifact_id, field_name="artifact_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(artifact_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(artifact_id)
        return record

    def _require_revision_suggestion(self, project_id: str, suggestion_id: str):
        try:
            record = self.repository.get_revision_suggestion(self._normalize_text(suggestion_id, field_name="suggestion_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(suggestion_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(suggestion_id)
        return record

    def _require_chapter_plan(self, project_id: str, chapter_id: str):
        try:
            record = self.repository.get_chapter_plan(self._normalize_text(chapter_id, field_name="chapter_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(chapter_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(chapter_id)
        return record

    def _require_scene_plan(self, project_id: str, scene_id: str):
        try:
            record = self.repository.get_scene_plan(self._normalize_text(scene_id, field_name="scene_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(scene_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(scene_id)
        return record

    def _require_sequence_plan(self, project_id: str, sequence_id: str):
        try:
            record = self.repository.get_sequence_plan(self._normalize_text(sequence_id, field_name="sequence_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(sequence_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(sequence_id)
        return record

    def _require_beat_plan(self, project_id: str, beat_id: str):
        try:
            record = self.repository.get_beat_plan(self._normalize_text(beat_id, field_name="beat_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(beat_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(beat_id)
        return record

    def _require_chapter_packet(self, project_id: str, packet_id: str):
        try:
            record = self.repository.get_chapter_packet(self._normalize_text(packet_id, field_name="packet_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(packet_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(packet_id)
        return record

    def _require_arc_selection(self, project_id: str, selection_id: str):
        try:
            record = self.repository.get_arc_selection(project_id, selection_id=self._normalize_text(selection_id, field_name="selection_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(selection_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(selection_id)
        return record

    def _require_arc_comparison(self, project_id: str, comparison_id: str):
        try:
            record = self.repository.get_arc_comparison(project_id, comparison_id=self._normalize_text(comparison_id, field_name="comparison_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(comparison_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(comparison_id)
        return record

    def _require_story_decision_node(self, project_id: str, node_id: str):
        try:
            record = self.repository.get_story_decision_node(project_id, node_id=self._normalize_text(node_id, field_name="node_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(node_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(node_id)
        return record

    def _require_review_decision(self, project_id: str, decision_id: str):
        try:
            record = self.repository.get_review_decision(self._normalize_text(decision_id, field_name="decision_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(decision_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(decision_id)
        return record

    def _require_inspect_run_link(self, project_id: str, link_id: str):
        try:
            record = self.repository.get_inspect_run_link(self._normalize_text(link_id, field_name="link_id"))
        except KeyError as exc:
            raise ReviewRoutingNotFoundError(link_id) from exc
        if record.project_id != project_id:
            raise ReviewRoutingNotFoundError(link_id)
        return record

    def _finding_from_record(self, record: CheckerFindingRecord) -> CheckerFinding:
        return CheckerFinding.model_validate(
            {
                "finding_id": record.finding_id,
                "project_id": record.project_id,
                "source_object_id": record.source_object_id,
                "source_object_kind": record.source_object_kind,
                "severity": record.severity,
                "summary": record.summary,
                "details": record.details,
                "source_context": list(record.source_context),
            }
        )

    def _decision_from_record(self, record: ReviewDecisionRecord) -> ReviewDecision:
        return ReviewDecision.model_validate(
            {
                "decision_id": record.decision_id,
                "project_id": record.project_id,
                "target_id": record.target_id,
                "target_kind": record.target_kind,
                "decision": record.decision,
                "notes": record.notes,
                "source_context": list(record.source_context),
            }
        )

    def _inspect_link_from_record(self, record: InspectRunLinkRecord) -> InspectRunLink:
        return InspectRunLink.model_validate(
            {
                "link_id": record.link_id,
                "project_id": record.project_id,
                "object_kind": record.object_kind,
                "object_id": record.object_id,
                "logical_run_id": record.logical_run_id,
                "run_id": record.run_id,
                "run_kind": record.run_kind,
                "attempt_number": record.attempt_number,
                "label": record.label,
            }
        )

    def _finding_rationale(self, finding: CheckerFinding) -> str:
        if finding.details:
            return f"{finding.summary} {finding.details}".strip()
        return finding.summary

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
        normalized = [self._normalize_text(value, field_name=field_name) for value in values]
        return self._merge_unique_strings(normalized)

    def _merge_unique_strings(self, *groups: Sequence[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for group in groups:
            for value in group:
                normalized = self._normalize_text(value, field_name="value")
                if normalized in seen:
                    continue
                seen.add(normalized)
                unique.append(normalized)
        return unique

    def _normalize_object_type(self, value: StoryObjectType | str, *, field_name: str) -> StoryObjectType:
        if isinstance(value, StoryObjectType):
            return value
        normalized = self._normalize_text(value, field_name=field_name).upper()
        try:
            return StoryObjectType[normalized]
        except KeyError as exc:
            allowed = ", ".join(item.value for item in StoryObjectType)
            raise ReviewRoutingValidationError(f"{field_name} must be one of: {allowed}") from exc

    def _normalize_decision(self, decision: str) -> str:
        normalized = self._normalize_text(decision, field_name="decision").lower()
        if normalized not in ALLOWED_REVIEW_DECISIONS:
            allowed = ", ".join(ALLOWED_REVIEW_DECISIONS)
            raise ReviewRoutingValidationError(f"decision must be one of: {allowed}")
        return normalized
