from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.story_development.common_models import StrictModel
from app.services.polish import PolishNotFoundError, PolishService, PolishServiceError
from pydantic import Field


class PolishAnalyzeRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    document_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    text: str = Field(..., min_length=1, max_length=1_000_000)


class ExportRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    document_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    format: str = Field(default="markdown", min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_\-]+$')
    include_frontmatter: bool = False
    include_toc: bool = False
    stylesheet: str | None = None


class PolishReportListResponse(StrictModel):
    project_id: str
    items: list[dict] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


__all__ = [
    "PolishAnalyzeRequest",
    "ExportRequest",
    "PolishReportListResponse",
    "register_polish_routes",
]


def register_polish_routes(router: APIRouter, service: PolishService) -> None:
    @router.post("/polish/analyze")
    def analyze_document(payload: PolishAnalyzeRequest):
        report = service.analyze_document(payload.text, payload.document_id, payload.project_id)
        return {
            "report_id": report.report_id,
            "project_id": report.project_id,
            "document_id": report.document_id,
            "readability_score": report.readability_score,
            "word_count": report.word_count,
            "sentence_count": report.sentence_count,
            "avg_sentence_length": report.avg_sentence_length,
            "passive_voice_count": report.passive_voice_count,
            "repetitive_words": report.repetitive_words,
            "style_issues": report.style_issues,
            "generated_at": report.generated_at.isoformat(),
        }

    @router.get("/polish/reports")
    def list_reports(project_id: str = Query(..., min_length=1), document_id: str | None = Query(None)):
        try:
            reports = service.list_reports(project_id, document_id=document_id)
        except PolishServiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return PolishReportListResponse(
            project_id=project_id,
            items=[
                {
                    "report_id": r.report_id,
                    "project_id": r.project_id,
                    "document_id": r.document_id,
                    "readability_score": r.readability_score,
                    "word_count": r.word_count,
                    "sentence_count": r.sentence_count,
                    "avg_sentence_length": r.avg_sentence_length,
                    "passive_voice_count": r.passive_voice_count,
                    "repetitive_words": r.repetitive_words,
                    "style_issues": r.style_issues,
                    "generated_at": r.generated_at.isoformat(),
                }
                for r in reports
            ],
            meta={"ordered_by": "generated_at_desc"},
        )

    @router.post("/polish/export", status_code=202)
    def export_manuscript(payload: ExportRequest):
        status = service.export_manuscript(payload.project_id, payload.document_id, payload.format)
        return {
            "export_id": status.export_id,
            "project_id": status.project_id,
            "document_id": status.document_id,
            "format": status.format,
            "status": status.status,
            "artifact_path": status.artifact_path,
            "error_message": status.error_message,
            "created_at": status.created_at.isoformat(),
            "updated_at": status.updated_at.isoformat(),
        }

    @router.get("/polish/export/{export_id}")
    def get_export_status(export_id: str, project_id: str | None = None):
        try:
            status = service.get_export_status(export_id)
        except PolishNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "export_id": status.export_id,
            "project_id": status.project_id,
            "document_id": status.document_id,
            "format": status.format,
            "status": status.status,
            "artifact_path": status.artifact_path,
            "error_message": status.error_message,
            "created_at": status.created_at.isoformat(),
            "updated_at": status.updated_at.isoformat(),
        }
