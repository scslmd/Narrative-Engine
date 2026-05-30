from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.story_development import (
    ExportRequest,
    ExportStatus,
    PolishAnalyzeRequest,
    PolishReport,
    PolishReportListResponse,
)
from app.services.polish import PolishNotFoundError, PolishService, PolishServiceError


__all__ = [
    "register_polish_routes",
]


def register_polish_routes(router: APIRouter, service: PolishService) -> None:
    @router.post("/polish/analyze", response_model=PolishReport)
    def analyze_document(payload: PolishAnalyzeRequest) -> PolishReport:
        try:
            return service.analyze_document(payload.text, payload.document_id, payload.project_id)
        except PolishNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PolishServiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    @router.post("/polish/export", status_code=202, response_model=ExportStatus)
    def export_manuscript(payload: ExportRequest) -> ExportStatus:
        try:
            return service.export_manuscript(payload.project_id, payload.document_id, payload.format)
        except PolishNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PolishServiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/polish/export/{export_id}", response_model=ExportStatus)
    def get_export_status(export_id: str, project_id: str) -> ExportStatus:
        try:
            status = service.get_export_status(export_id)
            if status.project_id != project_id:
                raise PolishNotFoundError(export_id)
        except PolishNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return status
