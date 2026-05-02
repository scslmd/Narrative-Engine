from __future__ import annotations

from dataclasses import dataclass

from app.persistence.story_development import ManuscriptDocumentRecord
from app.schemas.manuscript_assist import LLMRevisionSuggestion, TextRange


@dataclass(frozen=True)
class AssistGateOutcome:
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str]


class ManuscriptAssistGateService:
    def check_selection_still_matches(
        self,
        document: ManuscriptDocumentRecord,
        text_range: TextRange,
    ) -> AssistGateOutcome:
        content = document.content
        if text_range.end_offset > len(content):
            return AssistGateOutcome(
                gate_name="selection_bounds",
                passed=False,
                severity="blocking",
                reasons=["selection is out of document bounds"],
            )
        selected = content[text_range.start_offset:text_range.end_offset]
        if selected == text_range.selected_text:
            return AssistGateOutcome(
                gate_name="selection_match",
                passed=True,
                severity="info",
                reasons=[],
            )
        return AssistGateOutcome(
            gate_name="selection_match",
            passed=False,
            severity="blocking",
            reasons=["selection text no longer matches document content"],
        )

    def check_suggestion_against_canon(
        self,
        suggestion: LLMRevisionSuggestion,
    ) -> AssistGateOutcome:
        if suggestion.canon_risk.value == "blocking":
            return AssistGateOutcome(
                gate_name="canon_risk",
                passed=False,
                severity="blocking",
                reasons=["suggestion canon risk is blocking"],
            )
        if suggestion.canon_risk.value in {"high", "medium"}:
            return AssistGateOutcome(
                gate_name="canon_risk",
                passed=True,
                severity="warning",
                reasons=[f"suggestion canon risk is {suggestion.canon_risk.value}"],
            )
        return AssistGateOutcome(
            gate_name="canon_risk",
            passed=True,
            severity="info",
            reasons=[],
        )

    def check_branch_fork(self, draft_text: str) -> AssistGateOutcome:
        if not draft_text.strip():
            return AssistGateOutcome(
                gate_name="fork_payload",
                passed=False,
                severity="blocking",
                reasons=["fork payload is empty"],
            )
        return AssistGateOutcome(
            gate_name="fork_payload",
            passed=True,
            severity="info",
            reasons=[],
        )
