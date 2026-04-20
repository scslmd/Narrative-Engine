from __future__ import annotations

import re
import uuid
from typing import Any, Sequence

from app.persistence.story_development import (
    ManuscriptDocumentRecord,
    StoryDevelopmentRepository,
)
from app.schemas import StorySuggestionLifecycleState


class ManuscriptReviewError(ValueError):
    pass


class RevisionSuggestion:
    __slots__ = (
        "suggestion_id",
        "project_id",
        "target_document_id",
        "source_text",
        "proposed_text",
        "rationale",
        "source_context",
        "status",
    )

    def __init__(
        self,
        *,
        suggestion_id: str,
        project_id: str,
        target_document_id: str,
        source_text: str,
        proposed_text: str,
        rationale: str,
        source_context: list[str] | None = None,
        status: str = StorySuggestionLifecycleState.REQUESTED.value,
    ) -> None:
        self.suggestion_id = suggestion_id
        self.project_id = project_id
        self.target_document_id = target_document_id
        self.source_text = source_text
        self.proposed_text = proposed_text
        self.rationale = rationale
        self.source_context = source_context or []
        self.status = status

    def __repr__(self) -> str:
        return (
            f"RevisionSuggestion(id={self.suggestion_id!r}, "
            f"target={self.target_document_id!r})"
        )


class ManuscriptReviewService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def analyze_manuscript(
        self,
        project_id: str,
        *,
        document_id: str,
    ) -> tuple[RevisionSuggestion, ...]:
        normalized_project_id = self._normalize_text(project_id, field_name="project_id")
        normalized_document_id = self._normalize_text(document_id, field_name="document_id")
        document = self._require_manuscript(normalized_project_id, normalized_document_id)

        findings: list[RevisionSuggestion] = []
        findings.extend(
            self._check_repetition(document.content, normalized_project_id, normalized_document_id)
        )
        findings.extend(
            self._check_blank_paragraphs(document.content, normalized_project_id, normalized_document_id)
        )
        findings.extend(
            self._check_potential_new_characters(
                document.content, normalized_project_id, normalized_document_id
            )
        )

        self._persist_findings(normalized_project_id, findings)

        return tuple(findings)

    # ------------------------------------------------------------------
    # Rule-based checks
    # ------------------------------------------------------------------

    def _check_repetition(
        self,
        content: str,
        project_id: str,
        document_id: str,
    ) -> list[RevisionSuggestion]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        suggestions: list[RevisionSuggestion] = []
        seen: dict[str, int] = {}
        flagged: set[str] = set()
        for idx, line in enumerate(lines):
            if len(line) < 15:
                continue
            if line in seen and line not in flagged:
                first_seen = seen[line]
                repeat_count = sum(1 for l in lines if l == line)
                if repeat_count >= 3:
                    suggestion = self._suggest_revision(
                        project_id,
                        document_id,
                        source_text=line,
                        proposed_text=f"Consider revising line {first_seen + 1}: {line}",
                        rationale=(
                            f"Repetition detected: this sentence appears {repeat_count} times in "
                            f"the manuscript. Review for accidental duplication."
                        ),
                        source_context=[f"line:{first_seen + 1}", f"line:{idx + 1}"],
                    )
                    suggestions.append(suggestion)
                    flagged.add(line)
            else:
                seen[line] = idx
        return suggestions

    def _check_blank_paragraphs(
        self,
        content: str,
        project_id: str,
        document_id: str,
    ) -> list[RevisionSuggestion]:
        blank_runs = re.findall(r'\n{4,}', content)
        if not blank_runs:
            return []
        suggestions: list[RevisionSuggestion] = []
        for idx, blank_run in enumerate(blank_runs):
            run_len = len(blank_run)
            if run_len > 4:
                suggestion = self._suggest_revision(
                    project_id,
                    document_id,
                    source_text=blank_run.replace('\n', '[blank line]'),
                    proposed_text='---',
                    rationale=(
                        f"Excessive blank lines detected ({run_len} consecutive newlines). "
                        f"This may indicate a gap or placeholder. Review paragraph breaks."
                    ),
                    source_context=[f"blank_run:{idx + 1}"],
                )
                suggestions.append(suggestion)
        return suggestions

    def _check_potential_new_characters(
        self,
        content: str,
        project_id: str,
        document_id: str,
    ) -> list[RevisionSuggestion]:
        all_chars = self.repository.list_character_profiles(project_id)
        known_names: set[str] = set()
        for char in all_chars:
            name: str = char.name.lower()
            known_names.add(name)
            alias: Any = getattr(char, "alias", None)
            if alias:
                known_names.add(alias.lower())

        sentence_starts: set[str] = set()
        for sent in re.split(r'[.!?]+\s+', content):
            first_word = re.match(r'\b([A-Z][a-zA-Z]+)', sent.strip())
            if first_word:
                sentence_starts.add(first_word.group(1).lower())

        proper_nouns: set[str] = set()
        for word in re.findall(r'\b([A-Z][a-z]{2,})\b', content):
            lower = word.lower()
            if lower not in sentence_starts and lower not in known_names:
                proper_nouns.add(word)

        if not proper_nouns:
            return []

        suggestions: list[RevisionSuggestion] = []
        sample_names = sorted(proper_nouns)[:5]
        for name in sample_names:
            suggestion = self._suggest_revision(
                project_id,
                document_id,
                source_text=name,
                proposed_text=f"Consider adding {name} as a character entry in the character roster.",
                rationale=(
                    f"Potential new character detected: '{name}' appears as a proper noun "
                    f"but is not listed in the project's character records. If intentional, "
                    f"add a character profile to maintain continuity."
                ),
                source_context=[f"potential_character:{name}"],
            )
            suggestions.append(suggestion)
        return suggestions

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist_findings(self, project_id: str, findings: list[RevisionSuggestion]) -> None:
        for finding in findings:
            self.repository.upsert_revision_suggestion(
                suggestion_id=finding.suggestion_id,
                project_id=project_id,
                target_document_id=finding.target_document_id,
                source_text=finding.source_text,
                proposed_text=finding.proposed_text,
                rationale=finding.rationale,
                source_context=finding.source_context,
                status=finding.status,
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_id(self) -> str:
        return f"review-{uuid.uuid4().hex[:12]}"

    def _suggest_revision(
        self,
        project_id: str,
        target_document_id: str,
        *,
        source_text: str,
        proposed_text: str,
        rationale: str,
        source_context: Sequence[str] | None = None,
    ) -> RevisionSuggestion:
        suggestion_id = self._generate_id()
        return RevisionSuggestion(
            suggestion_id=suggestion_id,
            project_id=project_id,
            target_document_id=target_document_id,
            source_text=source_text,
            proposed_text=proposed_text,
            rationale=rationale,
            source_context=list(source_context) if source_context else [],
            status=StorySuggestionLifecycleState.REQUESTED.value,
        )

    def _normalize_text(self, value: Any, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _require_manuscript(self, project_id: str, document_id: str) -> ManuscriptDocumentRecord:
        try:
            record = self.repository.get_manuscript_document(document_id)
        except KeyError as exc:
            raise ManuscriptReviewError(
                f"Manuscript document '{document_id}' not found."
            ) from exc
        if record.project_id != project_id:
            raise ManuscriptReviewError(
                f"Manuscript document '{document_id}' does not belong to project '{project_id}'."
            )
        return record
