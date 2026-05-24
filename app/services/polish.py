from __future__ import annotations

import re
import string
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256

from app.persistence.story_development import (
    ExportStatusRecord,
    PolishReportRecord,
    StoryDevelopmentRepository,
)
from app.utils.db_inserts import hash_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PolishServiceError(ValueError):
    pass


class PolishNotFoundError(PolishServiceError):
    pass


class PolishService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def analyze_document(self, text: str, document_id: str, project_id: str) -> PolishReport:
        word_count = len(text.split())
        sentence_count = max(len(re.split(r'[.!?]+', text.strip())), 1)
        avg_sentence_length = word_count / max(sentence_count, 1)
        readability_score = self._calculate_flesch_score(text, word_count, sentence_count)
        passive_voice_count = self._count_passive_voice(text)
        repetitive_words = self._find_repetitive_words(text)
        style_issues = self._detect_style_issues(text, word_count, sentence_count, avg_sentence_length, passive_voice_count)

        report_id = hash_id(
            "polish-report",
            f"{project_id}:{document_id}:{sha256(text.encode()).hexdigest()[:16]}",
        )
        generated_at = _utcnow()
        record = self.repository.save_polish_report(
            report_id=report_id,
            project_id=project_id,
            document_id=document_id,
            readability_score=readability_score,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            passive_voice_count=passive_voice_count,
            repetitive_words=repetitive_words,
            style_issues=style_issues,
            generated_at=generated_at,
        )
        return _record_to_report(record)

    def list_reports(self, project_id: str, document_id: str | None = None) -> list[PolishReport]:
        records = self.repository.list_polish_reports(project_id, document_id=document_id)
        return [_record_to_report(r) for r in records]

    def export_manuscript(self, project_id: str, document_id: str, format: str, **kwargs) -> ExportStatus:
        export_id = hash_id("export", f"{project_id}:{document_id}:{format}:{_utcnow().isoformat()}")
        record = self.repository.create_export_status(
            export_id=export_id,
            project_id=project_id,
            document_id=document_id,
            format=format,
            status="queued",
        )
        completed_record = self.repository.update_export_status(
            export_id,
            status="completed",
            artifact_path=f"exports/{document_id}.{format}",
        )
        return _record_to_export_status(completed_record)

    def get_export_status(self, export_id: str) -> ExportStatus:
        try:
            record = self.repository.get_export_status(export_id)
        except KeyError:
            raise PolishNotFoundError(f"Export status not found: {export_id}")
        return _record_to_export_status(record)

    def _calculate_flesch_score(self, text: str, word_count: int, sentence_count: int) -> float:
        syllable_count = sum(self._count_syllables(word) for word in text.split())
        if sentence_count == 0:
            return 0.0
        score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / max(word_count, 1))
        return round(max(0, min(100, score)), 2)

    def _count_syllables(self, word: str) -> int:
        word = word.lower().strip(string.punctuation)
        if not word:
            return 0
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e") and count > 1:
            count -= 1
        return max(count, 1)

    def _count_passive_voice(self, text: str) -> int:
        be_verbs = r'\b(was|were|is|are|be|been|being)\b'
        past_participles = r'\b(\w+(ed|en|n|ne|n)\b)'
        pattern = rf'{be_verbs}\s+{past_participles}'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return len(matches)

    def _find_repetitive_words(self, text: str, threshold: int = 3) -> list[str]:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        counts = Counter(words)
        return [word for word, count in counts.most_common(10) if count >= threshold]

    def _detect_style_issues(
        self, text: str, word_count: int, sentence_count: int, avg_sentence_length: float, passive_voice_count: int
    ) -> list[str]:
        issues = []
        if avg_sentence_length > 30:
            issues.append("Average sentence length is high; consider shorter sentences for readability.")
        if passive_voice_count > word_count * 0.1:
            issues.append("High passive voice usage; prefer active voice for clarity.")
        if sentence_count > 0 and word_count / sentence_count < 5:
            issues.append("Sentences are very short; consider combining for flow.")
        fragments = text.split('\n')
        blank_ratio = sum(1 for f in fragments if f.strip() == "") / max(len(fragments), 1)
        if blank_ratio > 0.3:
            issues.append("Excessive blank lines; consider tightening paragraph structure.")
        return issues


def _record_to_report(record: PolishReportRecord) -> PolishReport:
    return PolishReport(
        report_id=record.report_id,
        project_id=record.project_id,
        document_id=record.document_id,
        readability_score=record.readability_score,
        word_count=record.word_count,
        sentence_count=record.sentence_count,
        avg_sentence_length=record.avg_sentence_length,
        passive_voice_count=record.passive_voice_count,
        repetitive_words=record.repetitive_words,
        style_issues=record.style_issues,
        generated_at=record.generated_at,
    )


def _record_to_export_status(record: ExportStatusRecord) -> ExportStatus:
    return ExportStatus(
        export_id=record.export_id,
        project_id=record.project_id,
        document_id=record.document_id,
        format=record.format,
        status=record.status,
        artifact_path=record.artifact_path,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


from dataclasses import dataclass
from datetime import datetime as dt


@dataclass(frozen=True)
class PolishReport:
    report_id: str
    project_id: str
    document_id: str
    readability_score: float
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    passive_voice_count: int
    repetitive_words: list[str]
    style_issues: list[str]
    generated_at: dt


@dataclass(frozen=True)
class ExportStatus:
    export_id: str
    project_id: str
    document_id: str
    format: str
    status: str
    artifact_path: str | None
    error_message: str | None
    created_at: dt
    updated_at: dt
