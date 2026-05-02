from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from app.persistence.story_development import (
    ManuscriptAssistRunRecord,
    ManuscriptAssistSuggestionRecord,
    ManuscriptDocumentRecord,
    StoryDevelopmentRepository,
)
from app.schemas.jobs import JobCreateRequest
from app.schemas.manuscript_assist import (
    ApplyAssistSuggestionRequest,
    ApplyAssistSuggestionResponse,
    AssistGateResult,
    AssistGateResultListResponse,
    AssistSuggestionStatus,
    LLMRevisionSuggestion,
    ManuscriptAssistKind,
    ManuscriptAssistRequest,
    ManuscriptAssistResult,
    ManuscriptAssistStatus,
    TextRange,
)
from app.services.drafting import DraftingService
from app.services.job_manager import JobManager
from app.services.manuscript_assist_gates import ManuscriptAssistGateService
from app.utils.db_inserts import hash_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ManuscriptAssistServiceError(ValueError):
    pass


class ManuscriptAssistNotFoundError(ManuscriptAssistServiceError):
    pass


class ManuscriptAssistConflictError(ManuscriptAssistServiceError):
    pass


@dataclass(frozen=True)
class _ApplyResolution:
    updated_content: str
    applied_range: TextRange


class ManuscriptAssistService:
    def __init__(
        self,
        *,
        repository: StoryDevelopmentRepository,
        drafting_service: DraftingService,
        job_manager: JobManager,
        gate_service: ManuscriptAssistGateService | None = None,
    ) -> None:
        self._repository = repository
        self._drafting = drafting_service
        self._job_manager = job_manager
        self._gates = gate_service or ManuscriptAssistGateService()

    def submit_assist(self, request: ManuscriptAssistRequest) -> ManuscriptAssistResult:
        document = self._resolve_document(request.project_id, request.document_id)
        if request.text_range is not None:
            gate = self._gates.check_selection_still_matches(document, request.text_range)
            if not gate.passed:
                raise ManuscriptAssistConflictError("; ".join(gate.reasons))
        assist_id = request.assist_id or hash_id(
            "manuscript-assist",
            f"{request.project_id}:{request.document_id}:{self._assist_kind_value(request.assist_kind)}:{self._request_hash(request)}",
        )
        job = self._job_manager.create_job(
            JobCreateRequest(
                phase="M-500",
                payload={
                    "project_id": request.project_id,
                    "document_id": request.document_id,
                    "assist_id": assist_id,
                },
            )
        )
        record = self._repository.upsert_manuscript_assist_run(
            assist_id=assist_id,
            project_id=request.project_id,
            document_id=request.document_id,
            assist_kind=self._assist_kind_value(request.assist_kind),
            request_json=request.model_dump(mode="json"),
            status=ManuscriptAssistStatus.QUEUED.value,
            summary="",
            created_draft_artifact_id=None,
            created_branch_id=None,
            created_manuscript_document_id=None,
            job_ids=[str(job.id)],
            warnings=[],
            idempotency_key=request.idempotency_key,
            request_hash=self._request_hash(request),
        )
        return self.get_assist(record.assist_id)

    def get_assist(self, assist_id: str) -> ManuscriptAssistResult:
        try:
            run = self._repository.get_manuscript_assist_run(assist_id)
        except KeyError as exc:
            raise ManuscriptAssistNotFoundError(assist_id) from exc
        return self._result_from_run(run)

    def list_assists(self, project_id: str, document_id: str | None = None) -> list[ManuscriptAssistResult]:
        runs = self._repository.list_manuscript_assist_runs(project_id, document_id)
        return [self._result_from_run(run) for run in runs]

    def list_assist_gates(self, assist_id: str) -> AssistGateResultListResponse:
        items = self._repository.list_manuscript_assist_gate_results(assist_id)
        return AssistGateResultListResponse(
            assist_id=assist_id,
            items=[
                AssistGateResult(
                    gate_result_id=item.gate_result_id,
                    assist_id=item.assist_id,
                    project_id=item.project_id,
                    document_id=item.document_id,
                    gate_name=item.gate_name,
                    passed=item.passed,
                    severity=item.severity,
                    reasons=item.reasons,
                    created_at=item.created_at.isoformat(),
                )
                for item in items
            ],
        )

    def list_suggestions(
        self,
        project_id: str,
        document_id: str,
        status: str | None = None,
    ) -> list[LLMRevisionSuggestion]:
        items = self._repository.list_manuscript_assist_suggestions(project_id, document_id, status)
        return [self._suggestion_from_record(item) for item in items]

    def apply_suggestion(self, request: ApplyAssistSuggestionRequest) -> ApplyAssistSuggestionResponse:
        document = self._resolve_document(request.project_id, request.document_id)
        if document.version != request.expected_document_version:
            raise ManuscriptAssistConflictError("document version conflict")
        try:
            suggestion = self._repository.get_manuscript_assist_suggestion(request.suggestion_id)
        except KeyError as exc:
            raise ManuscriptAssistNotFoundError(request.suggestion_id) from exc
        if suggestion.project_id != request.project_id or suggestion.target_document_id != request.document_id:
            raise ManuscriptAssistNotFoundError(request.suggestion_id)
        if suggestion.status in {AssistSuggestionStatus.REJECTED.value, AssistSuggestionStatus.ARCHIVED.value}:
            raise ManuscriptAssistConflictError("suggestion is not applyable in current status")
        llm_suggestion = self._suggestion_from_record(suggestion)
        if llm_suggestion.range is None:
            raise ManuscriptAssistConflictError("suggestion does not include an applyable text range")
        gate = self._gates.check_selection_still_matches(document, llm_suggestion.range)
        if not gate.passed:
            raise ManuscriptAssistConflictError("; ".join(gate.reasons))
        resolved = self._apply_text_range(
            content=document.content,
            text_range=llm_suggestion.range,
            proposed_text=llm_suggestion.proposed_text,
        )
        manuscript = self._drafting.save_manuscript_document(
            request.project_id,
            document_id=request.document_id,
            title=document.title,
            content=resolved.updated_content,
            chapter_id=document.chapter_id,
            scene_id=document.scene_id,
            current_draft_artifact_id=document.current_draft_artifact_id,
            version=document.version + 1,
        )
        updated = self._repository.update_manuscript_assist_suggestion_status(
            request.suggestion_id,
            AssistSuggestionStatus.ACCEPTED.value,
        )
        return ApplyAssistSuggestionResponse(
            suggestion=self._suggestion_from_record(updated),
            manuscript=manuscript,
        )

    def reject_suggestion(self, project_id: str, suggestion_id: str) -> LLMRevisionSuggestion:
        item = self._repository.update_manuscript_assist_suggestion_status(
            suggestion_id,
            AssistSuggestionStatus.REJECTED.value,
        )
        if item.project_id != project_id:
            raise ManuscriptAssistNotFoundError(suggestion_id)
        return self._suggestion_from_record(item)

    def archive_suggestion(self, project_id: str, suggestion_id: str) -> LLMRevisionSuggestion:
        item = self._repository.update_manuscript_assist_suggestion_status(
            suggestion_id,
            AssistSuggestionStatus.ARCHIVED.value,
        )
        if item.project_id != project_id:
            raise ManuscriptAssistNotFoundError(suggestion_id)
        return self._suggestion_from_record(item)

    def _resolve_document(self, project_id: str, document_id: str) -> ManuscriptDocumentRecord:
        try:
            document = self._repository.get_manuscript_document(document_id)
        except KeyError as exc:
            raise ManuscriptAssistNotFoundError(document_id) from exc
        if document.project_id != project_id:
            raise ManuscriptAssistNotFoundError(document_id)
        return document

    def _apply_text_range(self, *, content: str, text_range: TextRange, proposed_text: str) -> _ApplyResolution:
        start = text_range.start_offset
        end = text_range.end_offset
        if end > len(content) or start < 0 or end < start:
            raise ManuscriptAssistConflictError("text range is invalid")
        selected = content[start:end]
        if selected != text_range.selected_text:
            candidate = f"{text_range.anchor_before}{text_range.selected_text}{text_range.anchor_after}"
            location = content.find(candidate)
            if location < 0:
                raise ManuscriptAssistConflictError("unable to resolve range by anchors")
            start = location + len(text_range.anchor_before)
            end = start + len(text_range.selected_text)
            selected = content[start:end]
            if selected != text_range.selected_text:
                raise ManuscriptAssistConflictError("resolved anchor selection mismatch")
        updated_content = f"{content[:start]}{proposed_text}{content[end:]}"
        return _ApplyResolution(
            updated_content=updated_content,
            applied_range=TextRange(
                start_offset=start,
                end_offset=end,
                selected_text=text_range.selected_text,
                anchor_before=text_range.anchor_before,
                anchor_after=text_range.anchor_after,
            ),
        )

    def _result_from_run(self, run: ManuscriptAssistRunRecord) -> ManuscriptAssistResult:
        suggestions = self._repository.list_manuscript_assist_suggestions(
            run.project_id,
            run.document_id,
            None,
        )
        gate_results = self._repository.list_manuscript_assist_gate_results(run.assist_id)
        return ManuscriptAssistResult(
            assist_id=run.assist_id,
            project_id=run.project_id,
            document_id=run.document_id,
            assist_kind=ManuscriptAssistKind(run.assist_kind),
            status=ManuscriptAssistStatus(run.status),
            summary=run.summary,
            suggestions=[self._suggestion_from_record(item) for item in suggestions],
            created_draft_artifact_id=run.created_draft_artifact_id,
            created_branch_id=run.created_branch_id,
            created_manuscript_document_id=run.created_manuscript_document_id,
            gate_results=[
                AssistGateResult(
                    gate_result_id=item.gate_result_id,
                    assist_id=item.assist_id,
                    project_id=item.project_id,
                    document_id=item.document_id,
                    gate_name=item.gate_name,
                    passed=item.passed,
                    severity=item.severity,
                    reasons=item.reasons,
                    created_at=item.created_at.isoformat(),
                )
                for item in gate_results
            ],
            job_ids=run.job_ids,
            warnings=run.warnings,
        )

    def _suggestion_from_record(self, item: ManuscriptAssistSuggestionRecord) -> LLMRevisionSuggestion:
        return LLMRevisionSuggestion(
            suggestion_id=item.suggestion_id,
            assist_id=item.assist_id,
            project_id=item.project_id,
            target_document_id=item.target_document_id,
            source_text=item.source_text,
            proposed_text=item.proposed_text,
            rationale=item.rationale,
            suggestion_kind=ManuscriptAssistKind(item.suggestion_kind),
            range=TextRange.model_validate(item.range_json) if item.range_json is not None else None,
            canon_risk=item.canon_risk,
            confidence_score=item.confidence_score,
            status=item.status,
            source_context=item.source_context,
        )

    def _request_hash(self, request: ManuscriptAssistRequest) -> str:
        normalized = json.dumps(request.model_dump(mode="json"), ensure_ascii=True, sort_keys=True)
        return sha256(normalized.encode("utf-8")).hexdigest()

    def _assist_kind_value(self, value: Any) -> str:
        if hasattr(value, "value"):
            return str(getattr(value, "value"))
        return str(value)
