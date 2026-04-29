from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractionProgressResult(BaseModel):
    """Result returned when extraction completes."""
    project_id: str = ""
    source_corpus: str = ""
    archetypal_patterns: int = 0
    narrative_structures: int = 0
    world_rules: int = 0
    symbolic_motifs: int = 0
    warnings: list[str] = Field(default_factory=list)


class ExtractionProgressResponse(BaseModel):
    """Response for polling extraction job status."""
    extraction_id: str
    status: str  # pending | running | completed | failed
    phase: str = ""
    result: ExtractionProgressResult | None = None
    error: str | None = None


class ExtractionSubmitResponse(BaseModel):
    """Response when submitting an async extraction job."""
    extraction_id: str
