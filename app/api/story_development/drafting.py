from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import (
    AlternateVariantRequest,
    DraftArtifact,
    DraftArtifactCreateRequest,
    DraftContinuationRequest,
    ManuscriptDocument,
    ManuscriptDocumentUpdateRequest,
    ManuscriptReviewResponse,
    RevisionSuggestion,
    StorySuggestionLifecycleState,
)
from app.schemas.base import StrictModel
from app.services.drafting import DraftingNotFoundError, DraftingService, DraftingValidationError
from app.services.manuscript_review import ManuscriptReviewError, ManuscriptReviewService
from pydantic import Field


class ManuscriptDocumentCreateRequest(StrictModel):
    document_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    chapter_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    scene_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    current_draft_artifact_id: str | None = Field(None, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    version: int | None = Field(None, ge=1)


class PromoteDraftToManuscriptRequest(StrictModel):
    project_id: str
    document_id: str
    draft_artifact_id: str
    title: str | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    version: int | None = None


class RevisionSuggestionCreateRequest(StrictModel):
    suggestion_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    source_context: list[str] = Field(default_factory=list)
    status: str = StorySuggestionLifecycleState.REQUESTED.value


__all__ = [
    "ManuscriptDocumentCreateRequest",
    "PromoteDraftToManuscriptRequest",
    "RevisionSuggestionCreateRequest",
    "register_drafting_routes",
]


def register_drafting_routes(
    router: APIRouter,
    drafting_service: DraftingService,
    manuscript_review_service: ManuscriptReviewService,
) -> None:
    @router.get("/drafting/draft-artifacts", response_model=None)
    def list_draft_artifacts(project_id: str):
        from app.api.story_development.common_models import DraftArtifactListResponse
        return DraftArtifactListResponse(
            project_id=project_id,
            items=list(drafting_service.list_draft_artifacts(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/draft-artifacts/{artifact_id}", response_model=DraftArtifact)
    def get_draft_artifact(artifact_id: str, project_id: str) -> DraftArtifact:
        try:
            return drafting_service.get_draft_artifact(project_id, artifact_id=artifact_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.post("/drafting/draft-artifacts", response_model=DraftArtifact, status_code=201)
    def create_draft_artifact(payload: DraftArtifactCreateRequest) -> DraftArtifact:
        """Create a new draft artifact for a project.

        Registers a draft artifact with content and provenance metadata.
        Optionally links to planning artifacts via source_plan_ids.

        Args:
            payload: Draft artifact creation request with ID, title, content, and optional metadata.

        Returns:
            The created DraftArtifact object.

        Raises:
            HTTPException 400: If the status value is invalid.
        """
        try:
            return drafting_service.register_draft_artifact(
                payload.project_id,
                artifact_id=payload.artifact_id,
                title=payload.title,
                content=payload.content,
                source_plan_ids=payload.source_plan_ids,
                source_context=payload.source_context,
                provenance_note=payload.provenance_note,
                status=payload.status,
            )
        except DraftingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/drafting/draft-artifacts/continue", response_model=DraftArtifact, status_code=201)
    def continue_draft_artifact(payload: DraftContinuationRequest) -> DraftArtifact:
        """Continue a draft from a prior draft or manuscript document.

        Creates a new draft artifact that extends an existing one, inheriting
        source plan IDs and context provenance from the base artifact.

        Args:
            payload: Continuation request with target artifact ID, content, and prior source reference.

        Returns:
            The created DraftArtifact object with merged provenance.

        Raises:
            HTTPException 400: If both or neither prior_draft/prior_manuscript IDs are provided.
            HTTPException 404: If the referenced prior artifact or manuscript does not exist.
        """
        try:
            return drafting_service.continue_draft(
                payload.project_id,
                artifact_id=payload.artifact_id,
                title=payload.title,
                content=payload.content,
                prior_draft_artifact_id=payload.prior_draft_artifact_id,
                prior_manuscript_document_id=payload.prior_manuscript_document_id,
                source_plan_ids=payload.source_plan_ids,
                source_context=payload.source_context,
                provenance_note=payload.provenance_note,
            )
        except DraftingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Prior draft or manuscript not found.") from exc

    @router.post("/drafting/draft-artifacts/alternate-variant", response_model=DraftArtifact, status_code=201)
    def create_alternate_variant(payload: AlternateVariantRequest) -> DraftArtifact:
        """Create an alternate variant of an existing draft or manuscript document.

        Creates a new draft artifact in PROPOSED status that branches from an
        existing draft artifact or manuscript document, inheriting provenance.

        Args:
            payload: Alternate variant request with target artifact ID, content, and base source reference.

        Returns:
            The created DraftArtifact object with PROPOSED status and merged provenance.

        Raises:
            HTTPException 400: If both or neither base_draft/base_manuscript IDs are provided.
            HTTPException 404: If the referenced base artifact or manuscript does not exist.
        """
        try:
            return drafting_service.create_alternate_variant(
                payload.project_id,
                artifact_id=payload.artifact_id,
                title=payload.title,
                content=payload.content,
                base_draft_artifact_id=payload.base_draft_artifact_id,
                base_manuscript_document_id=payload.base_manuscript_document_id,
                source_plan_ids=payload.source_plan_ids,
                source_context=payload.source_context,
                provenance_note=payload.provenance_note,
            )
        except DraftingValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Base draft or manuscript not found.") from exc

    @router.get("/drafting/manuscript-documents", response_model=None)
    def list_manuscript_documents(project_id: str):
        from app.api.story_development.common_models import ManuscriptDocumentListResponse
        return ManuscriptDocumentListResponse(
            project_id=project_id,
            items=list(drafting_service.list_manuscript_documents(project_id)),
            meta={"ordered_by": "title_asc"},
        )

    @router.get("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
    def get_manuscript_document(document_id: str, project_id: str) -> ManuscriptDocument:
        try:
            return drafting_service.get_manuscript_document(project_id, document_id=document_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Manuscript document not found.") from exc

    @router.get("/drafting/revision-suggestions", response_model=None)
    def list_revision_suggestions(project_id: str, target_document_id: str | None = None):
        from app.api.story_development.common_models import RevisionSuggestionListResponse
        if target_document_id is None:
            items = list(drafting_service.list_revision_suggestions(project_id))
        else:
            items = list(
                drafting_service.list_revision_suggestions_for_document(
                    project_id,
                    target_document_id=target_document_id,
                )
            )
        return RevisionSuggestionListResponse(project_id=project_id, items=items, meta={"ordered_by": "suggestion_id_asc"})

    @router.get("/drafting/revision-suggestions/{suggestion_id}", response_model=RevisionSuggestion)
    def get_revision_suggestion(suggestion_id: str, project_id: str) -> RevisionSuggestion:
        try:
            return drafting_service.get_revision_suggestion(project_id, suggestion_id=suggestion_id)
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Revision suggestion not found.") from exc

    @router.post("/drafting/manuscript-documents", response_model=ManuscriptDocument, status_code=201)
    def create_manuscript_document(payload: ManuscriptDocumentCreateRequest) -> ManuscriptDocument:
        """Create a new manuscript document.

        Creates a manuscript document with the specified content and metadata.
        Optionally links to an existing draft artifact for provenance tracking.

        Args:
            payload: Manuscript document creation request with ID, title, content, and optional chapter/scene references.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.save_manuscript_document(
                payload.project_id,
                document_id=payload.document_id,
                content=payload.content,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                current_draft_artifact_id=payload.current_draft_artifact_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Referenced draft artifact not found.") from exc

    @router.patch("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
    def update_manuscript_document(
        document_id: str,
        project_id: str,
        payload: ManuscriptDocumentUpdateRequest,
    ) -> ManuscriptDocument:
        """Partially update a manuscript document's content or title.

        Updates only the fields that are provided in the request body.
        Version is automatically incremented.

        Args:
            document_id: The manuscript document identifier.
            project_id: The project identifier.
            payload: Partial update with optional 'content' and 'title' fields.

        Returns:
            The updated ManuscriptDocument object.

        Raises:
            HTTPException 400: If no fields are provided.
            HTTPException 404: If the document or project does not exist.
        """
        if payload.content is None and payload.title is None:
            raise HTTPException(status_code=400, detail="At least one of 'content' or 'title' must be provided.")
        try:
            existing = drafting_service.get_manuscript_document(project_id, document_id=document_id)
        except DraftingNotFoundError:
            raise HTTPException(status_code=404, detail="Manuscript document not found.")
        update_content = payload.content if payload.content is not None else existing.content
        update_title = payload.title if payload.title is not None else existing.title
        try:
            return drafting_service.save_manuscript_document(
                project_id,
                document_id=document_id,
                content=update_content,
                title=update_title,
                chapter_id=existing.chapter_id,
                scene_id=existing.scene_id,
                current_draft_artifact_id=existing.current_draft_artifact_id,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Manuscript document not found.") from exc

    @router.post(
        "/drafting/manuscript-documents/{document_id}/review",
        response_model=ManuscriptReviewResponse,
        status_code=202,
    )
    def trigger_manuscript_review(
        document_id: str,
        project_id: str,
    ) -> ManuscriptReviewResponse:
        """Trigger an AI review of the manuscript document.

        Analyzes the manuscript content for repetition, blank paragraph gaps,
        and potential new characters not yet listed in the project's character records.

        Args:
            document_id: The manuscript document identifier.
            project_id: The project identifier.

        Returns:
            A response containing any generated revision suggestions.

        Raises:
            HTTPException 404: If the document or project does not exist.
        """
        try:
            findings = manuscript_review_service.analyze_manuscript(
                project_id, document_id=document_id
            )
        except ManuscriptReviewError:
            raise HTTPException(status_code=404, detail="Manuscript document not found.")

        def _to_dict(finding):
            return {
                "suggestion_id": finding.suggestion_id,
                "project_id": finding.project_id,
                "target_document_id": finding.target_document_id,
                "source_text": finding.source_text,
                "proposed_text": finding.proposed_text,
                "rationale": finding.rationale,
                "source_context": finding.source_context,
                "status": finding.status,
            }

        return ManuscriptReviewResponse(
            document_id=document_id,
            project_id=project_id,
            findings=[_to_dict(finding) for finding in findings],
        )

    @router.post("/drafting/promote-draft", response_model=ManuscriptDocument, status_code=201)
    def promote_draft_to_manuscript(payload: PromoteDraftToManuscriptRequest) -> ManuscriptDocument:
        """Promote a draft artifact to a manuscript document.

        Creates a new manuscript document from an existing draft artifact,
        preserving the draft's content and optionally updating metadata.

        Args:
            payload: Promotion request with project ID, target document ID, and source draft artifact ID.

        Returns:
            The created ManuscriptDocument object.

        Raises:
            HTTPException 404: If the referenced draft artifact does not exist.
        """
        try:
            return drafting_service.promote_draft_to_manuscript(
                payload.project_id,
                document_id=payload.document_id,
                draft_artifact_id=payload.draft_artifact_id,
                title=payload.title,
                chapter_id=payload.chapter_id,
                scene_id=payload.scene_id,
                version=payload.version,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Draft artifact not found.") from exc

    @router.post("/drafting/revision-suggestions", response_model=RevisionSuggestion, status_code=201)
    def create_revision_suggestion(payload: RevisionSuggestionCreateRequest) -> RevisionSuggestion:
        """Create a revision suggestion for a manuscript document.

        Proposes text changes to an existing manuscript document with rationale
        and source context for review.

        Args:
            payload: Revision suggestion request with target document, source/proposed text, and rationale.

        Returns:
            The created RevisionSuggestion object.

        Raises:
            HTTPException 404: If the target manuscript document does not exist.
        """
        try:
            return drafting_service.create_revision_suggestion(
                payload.project_id,
                suggestion_id=payload.suggestion_id,
                target_document_id=payload.target_document_id,
                source_text=payload.source_text,
                proposed_text=payload.proposed_text,
                rationale=payload.rationale,
                source_context=payload.source_context,
                status=payload.status,
            )
        except DraftingNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Target manuscript document not found.") from exc
