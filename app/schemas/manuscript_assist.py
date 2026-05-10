from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from .base import StrictModel
from .generation import CanonPolicy, CanonScope
from .story_development import ManuscriptDocument


class ManuscriptAssistKind(str, Enum):
    DEVELOPMENTAL_REVIEW = "developmental_review"
    CANON_CHECK = "canon_check"
    CHARACTER_VOICE_CHECK = "character_voice_check"
    PACING_REVIEW = "pacing_review"
    THEME_REVIEW = "theme_review"
    LINE_EDIT_SELECTION = "line_edit_selection"
    EXPAND_SELECTION = "expand_selection"
    EXPAND_SENSORY_SIGHT = "expand_sensory_sight"
    EXPAND_SENSORY_SOUND = "expand_sensory_sound"
    EXPAND_SENSORY_SMELL = "expand_sensory_smell"
    EXPAND_SENSORY_TEXTURE = "expand_sensory_texture"
    EXPAND_SENSORY_TASTE = "expand_sensory_taste"
    EXPAND_METAPHOR = "expand_metaphor"
    EXPAND_SHOW_DONT_TELL = "expand_show_dont_tell"
    COMPRESS_SELECTION = "compress_selection"
    REWRITE_SELECTION_SAME_VOICE = "rewrite_selection_same_voice"
    ALTERNATE_SELECTION = "alternate_selection"
    CONTINUE_FROM_SELECTION = "continue_from_selection"
    FORK_FROM_SELECTION = "fork_from_selection"
    GENERATE_NEXT_CHAPTER = "generate_next_chapter"
    GENERATE_ALTERNATE_CHAPTER = "generate_alternate_chapter"
    CONTINUITY_REPAIR = "continuity_repair"
    AI_GENERATE_DRAFT = "ai_generate_draft"


class ManuscriptAssistStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class AssistCanonRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKING = "blocking"


class AssistSuggestionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ApplyAssistMode(str, Enum):
    REPLACE_RANGE = "replace_range"
    APPEND_AFTER_RANGE = "append_after_range"
    CREATE_DRAFT = "create_draft"
    CREATE_BRANCH = "create_branch"


class TextRange(StrictModel):
    start_offset: int = Field(..., ge=0)
    end_offset: int = Field(..., ge=0)
    selected_text: str = Field(..., min_length=1, max_length=100000)
    anchor_before: str = Field(default="", max_length=1000)
    anchor_after: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def _validate_bounds(self) -> TextRange:
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self


class ManuscriptAssistRequest(StrictModel):
    assist_id: str | None = Field(default=None, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    document_id: str = Field(..., min_length=1, max_length=255)
    assist_kind: ManuscriptAssistKind
    instruction: str = Field(default="", max_length=5000)
    text_range: TextRange | None = None
    canon_scope: CanonScope | None = None
    canon_policy: CanonPolicy | None = None
    target_branch_id: str | None = Field(default=None, max_length=255)
    create_branch: bool = False
    create_draft_artifact: bool = False
    model_id: str | None = Field(default=None, max_length=255)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1, le=64000)
    idempotency_key: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _validate_requirements(self) -> ManuscriptAssistRequest:
        selection_kinds = {
            ManuscriptAssistKind.LINE_EDIT_SELECTION,
            ManuscriptAssistKind.EXPAND_SELECTION,
            ManuscriptAssistKind.EXPAND_SENSORY_SIGHT,
            ManuscriptAssistKind.EXPAND_SENSORY_SOUND,
            ManuscriptAssistKind.EXPAND_SENSORY_SMELL,
            ManuscriptAssistKind.EXPAND_SENSORY_TEXTURE,
            ManuscriptAssistKind.EXPAND_SENSORY_TASTE,
            ManuscriptAssistKind.EXPAND_METAPHOR,
            ManuscriptAssistKind.EXPAND_SHOW_DONT_TELL,
            ManuscriptAssistKind.COMPRESS_SELECTION,
            ManuscriptAssistKind.REWRITE_SELECTION_SAME_VOICE,
            ManuscriptAssistKind.ALTERNATE_SELECTION,
            ManuscriptAssistKind.CONTINUE_FROM_SELECTION,
            ManuscriptAssistKind.FORK_FROM_SELECTION,
        }
        if self.assist_kind in selection_kinds and self.text_range is None:
            raise ValueError("text_range is required for selection assist actions")
        if self.assist_kind == ManuscriptAssistKind.FORK_FROM_SELECTION:
            if not self.create_branch and not self.create_draft_artifact:
                raise ValueError(
                    "fork_from_selection requires create_branch=true or create_draft_artifact=true"
                )
        return self


class ManuscriptAssistPacket(StrictModel):
    assist_id: str
    project_id: str
    document_id: str
    assist_kind: ManuscriptAssistKind
    instruction: str = ""
    document_title: str = ""
    document_content: str = ""
    text_range: TextRange | None = None
    canon_scope: CanonScope | None = None
    canon_policy: CanonPolicy | None = None
    model_id: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1, le=64000)


class AssistGateResult(StrictModel):
    gate_result_id: str
    assist_id: str
    project_id: str
    document_id: str
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str] = Field(default_factory=list)
    created_at: str


class LLMRevisionSuggestion(StrictModel):
    suggestion_id: str
    assist_id: str
    project_id: str
    target_document_id: str
    source_text: str
    proposed_text: str
    rationale: str
    suggestion_kind: ManuscriptAssistKind
    range: TextRange | None = None
    canon_risk: AssistCanonRisk = AssistCanonRisk.NONE
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: AssistSuggestionStatus = AssistSuggestionStatus.REQUESTED
    source_context: list[str] = Field(default_factory=list)


class ManuscriptAssistResult(StrictModel):
    assist_id: str
    project_id: str
    document_id: str
    assist_kind: ManuscriptAssistKind
    status: ManuscriptAssistStatus
    summary: str = ""
    suggestions: list[LLMRevisionSuggestion] = Field(default_factory=list)
    created_draft_artifact_id: str | None = None
    created_branch_id: str | None = None
    created_manuscript_document_id: str | None = None
    gate_results: list[AssistGateResult] = Field(default_factory=list)
    job_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ApplyAssistSuggestionRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255)
    document_id: str = Field(..., min_length=1, max_length=255)
    suggestion_id: str = Field(..., min_length=1, max_length=255)
    expected_document_version: int = Field(..., ge=1)
    apply_mode: ApplyAssistMode = ApplyAssistMode.REPLACE_RANGE


class AssistGateResultListResponse(StrictModel):
    assist_id: str
    items: list[AssistGateResult] = Field(default_factory=list)


class AssistSuggestionListResponse(StrictModel):
    project_id: str
    document_id: str
    items: list[LLMRevisionSuggestion] = Field(default_factory=list)


class ApplyAssistSuggestionResponse(StrictModel):
    suggestion: LLMRevisionSuggestion
    manuscript: ManuscriptDocument
