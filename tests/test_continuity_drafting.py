from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import (
    ContinuityFindingRecord,
    ContinuityStateRecord,
    ContinuityThreadRecord,
    DraftBriefRecord,
    DraftingContextPacketRecord,
    StoryDevelopmentRepository,
)
from app.schemas.inference import (
    InferenceMessage,
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from app.schemas.story_import import (
    ContinuityFinding,
    ContinuityState,
    ContinuityThread,
    StoryImportChapterSummary,
)
from app.services.multi_pass_import import MultiPassImportService
from app.services.runtime_prompts import (
    build_continuity_analysis_request,
    build_draft_brief_request,
)


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


class StubInferenceBackend(InferenceBackend):
    """Minimal inference backend for gating tests."""

    def __init__(self, *, model: str = "stub-model") -> None:
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="stub",
            display_name="Stub Backend",
            transport="stub",
            base_url="",
            default_model=model,
            timeout_seconds=10.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["stub"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        raise NotImplementedError("Stub backend should not be called in gating tests")


def _seed_project(db_path: Path, project_id: str) -> None:
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                "Continuity Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


# ---------------------------------------------------------------------------
# Continuity Persistence Tests (repository round-trips)
# ---------------------------------------------------------------------------

def test_continuity_thread_upsert_and_get(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-thread"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    record = repo.upsert_continuity_thread(
        thread_id="thread-1",
        project_id=project_id,
        title="The Missing Heirloom",
        summary="A family heirloom is stolen and must be recovered.",
        status="active",
        chapter_ids=["ch-1", "ch-3"],
        character_ids=["char-alice"],
        evidence=["Chapter 1 mentions the locket", "Chapter 3 reveals its theft"],
        provenance_note="manual test",
        confidence_score=0.85,
        created_at=STAMP,
    )

    assert record.thread_id == "thread-1"
    assert record.project_id == project_id
    assert record.title == "The Missing Heirloom"
    assert record.summary == "A family heirloom is stolen and must be recovered."
    assert record.status == "active"
    assert record.chapter_ids == ["ch-1", "ch-3"]
    assert record.character_ids == ["char-alice"]
    assert record.evidence == ["Chapter 1 mentions the locket", "Chapter 3 reveals its theft"]
    assert record.provenance_note == "manual test"
    assert record.confidence_score == 0.85

    fetched = repo.get_continuity_thread("thread-1")
    assert fetched.thread_id == "thread-1"
    assert fetched.chapter_ids == record.chapter_ids
    assert fetched.confidence_score == record.confidence_score


def test_continuity_state_upsert_and_get(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-state"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    record = repo.upsert_continuity_state(
        state_id="state-ch1",
        project_id=project_id,
        chapter_id="ch-1",
        summary="End of chapter 1: Alice has left home.",
        active_threads=["thread-1"],
        resolved_threads=[],
        character_states={"alice": "has left home, carrying the locket"},
        world_facts=["The village is near the river"],
        unresolved_questions=["Who stole the locket?"],
        contradictions=[],
        status="complete",
        provenance_note="manual test",
        confidence_score=0.9,
        created_at=STAMP,
    )

    assert record.state_id == "state-ch1"
    assert record.chapter_id == "ch-1"
    assert record.character_states == {"alice": "has left home, carrying the locket"}
    assert record.active_threads == ["thread-1"]
    assert record.world_facts == ["The village is near the river"]
    assert record.unresolved_questions == ["Who stole the locket?"]

    fetched = repo.get_continuity_state("state-ch1")
    assert fetched.character_states == record.character_states
    assert fetched.confidence_score == 0.9


def test_continuity_finding_upsert_and_get(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-finding"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    record = repo.upsert_continuity_finding(
        project_id=project_id,
        overall_confidence=0.72,
        status="complete",
        contradictions=["Timeline mismatch in chapter 3"],
        unresolved_questions=["What happened to the locket?"],
        provenance_note="manual test",
        created_at=STAMP,
    )

    assert record.finding_id >= 1
    assert record.project_id == project_id
    assert record.overall_confidence == 0.72
    assert record.status == "complete"
    assert record.contradictions == ["Timeline mismatch in chapter 3"]
    assert record.unresolved_questions == ["What happened to the locket?"]

    fetched = repo.get_continuity_finding(record.finding_id)
    assert fetched.overall_confidence == record.overall_confidence
    assert fetched.contradictions == record.contradictions


def test_draft_brief_upsert_and_get(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-brief"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    record = repo.upsert_draft_brief(
        brief_id="brief-ch1",
        project_id=project_id,
        chapter_id="ch-1",
        objective="Introduce Alice and establish the mystery of the missing locket.",
        emotional_turn="From comfort to unease as Alice discovers the theft.",
        continuity_obligations=["Alice must carry the locket at start"],
        required_callbacks=["Reference the grandmother's warning"],
        forbidden_contradictions=["Alice cannot already know about the thief"],
        voice_guidance="Third-person limited, atmospheric prose.",
        status="approved",
        provenance_note="manual test",
        confidence_score=0.95,
        created_at=STAMP,
    )

    assert record.brief_id == "brief-ch1"
    assert record.chapter_id == "ch-1"
    assert record.objective == "Introduce Alice and establish the mystery of the missing locket."
    assert record.emotional_turn == "From comfort to unease as Alice discovers the theft."
    assert record.continuity_obligations == ["Alice must carry the locket at start"]
    assert record.required_callbacks == ["Reference the grandmother's warning"]
    assert record.forbidden_contradictions == ["Alice cannot already know about the thief"]
    assert record.voice_guidance == "Third-person limited, atmospheric prose."
    assert record.status == "approved"

    fetched = repo.get_draft_brief("brief-ch1")
    assert fetched.objective == record.objective
    assert fetched.confidence_score == 0.95


def test_drafting_context_packet_upsert_and_get(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-packet"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_draft_brief(
        brief_id="brief-ch1",
        project_id=project_id,
        chapter_id="ch-1",
        objective="Placeholder.",
        emotional_turn="Placeholder.",
        created_at=STAMP,
    )

    pattern_guidance = {
        "archetypal_patterns": ["hero's journey", "coming of age"],
        "narrative_structure": "three_act",
        "voice_profile": {"tone": "melancholy", "pacing": "deliberate"},
    }

    record = repo.upsert_drafting_context_packet(
        packet_id="packet-ch1",
        project_id=project_id,
        brief_id="brief-ch1",
        character_anchors=["alice", "grandmother"],
        world_constraints=["The village is isolated by mountains"],
        prior_summaries=["Prologue: the grandmother's prophecy"],
        pattern_guidance=pattern_guidance,
        status="ready",
        provenance_note="manual test",
        confidence_score=0.88,
        created_at=STAMP,
    )

    assert record.packet_id == "packet-ch1"
    assert record.brief_id == "brief-ch1"
    assert record.character_anchors == ["alice", "grandmother"]
    assert record.world_constraints == ["The village is isolated by mountains"]
    assert record.prior_summaries == ["Prologue: the grandmother's prophecy"]
    assert record.pattern_guidance["archetypal_patterns"] == ["hero's journey", "coming of age"]
    assert record.pattern_guidance["voice_profile"]["tone"] == "melancholy"

    fetched = repo.get_drafting_context_packet("packet-ch1")
    assert fetched.pattern_guidance == pattern_guidance


# ---------------------------------------------------------------------------
# Continuity Gating Tests
# ---------------------------------------------------------------------------

def test_continuity_gate_passes_with_high_confidence() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=[],
        unresolved_questions=["What happens next?"],
        overall_confidence=0.8,
        status="complete",
    )

    passed, reasons = service._check_continuity_gate(finding)
    assert passed is True
    assert reasons == []


def test_continuity_gate_fails_with_low_confidence() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=[],
        unresolved_questions=[],
        overall_confidence=0.3,
        status="complete",
    )

    passed, reasons = service._check_continuity_gate(finding)
    assert passed is False
    assert len(reasons) >= 1
    assert "below threshold" in reasons[0]


def test_continuity_gate_fails_with_critical_contradiction() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=["The character identity of Alice contradicts earlier chapters"],
        unresolved_questions=[],
        overall_confidence=0.8,
        status="complete",
    )

    passed, reasons = service._check_continuity_gate(finding)
    assert passed is False
    assert any("Critical contradiction" in r for r in reasons)


def test_continuity_normalization_caps_confidence_without_evidence() -> None:
    from unittest.mock import MagicMock, patch

    service = MultiPassImportService(StubInferenceBackend())
    raw = {
        "threads": [
            {
                "thread_id": "t1",
                "title": "Test Thread",
                "summary": "A test thread",
                "chapter_ids": ["ch-1"],
                "evidence": [],
                "confidence_score": 0.95,
            }
        ],
        "states": [],
        "contradictions": [],
        "unresolved_questions": [],
        "overall_confidence": 0.8,
    }

    with patch("app.services.multi_pass_import.ContinuityThread", autospec=False) as mock_thread, \
         patch("app.services.multi_pass_import.ContinuityState", autospec=False) as mock_state, \
         patch("app.services.multi_pass_import.ContinuityFinding", autospec=False) as mock_finding:
        mock_thread.return_value = MagicMock()
        mock_state.return_value = MagicMock()
        mock_finding.return_value = MagicMock()
        service._normalize_continuity_finding(raw, known_chapter_ids={"ch-1"})
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs["confidence_score"] == 0.5


def test_continuity_normalization_rejects_unknown_chapter_ids() -> None:
    from unittest.mock import MagicMock, patch

    service = MultiPassImportService(StubInferenceBackend())
    raw = {
        "threads": [
            {
                "thread_id": "t1",
                "title": "Test Thread",
                "summary": "A test thread",
                "chapter_ids": ["ch-1", "ch-nonexistent"],
                "evidence": ["some evidence"],
                "confidence_score": 0.8,
            }
        ],
        "states": [],
        "contradictions": [],
        "unresolved_questions": [],
        "overall_confidence": 0.8,
    }

    with patch("app.services.multi_pass_import.ContinuityThread", autospec=False) as mock_thread, \
         patch("app.services.multi_pass_import.ContinuityState", autospec=False) as mock_state, \
         patch("app.services.multi_pass_import.ContinuityFinding", autospec=False) as mock_finding:
        mock_thread.return_value = MagicMock()
        mock_state.return_value = MagicMock()
        mock_finding.return_value = MagicMock()
        service._normalize_continuity_finding(raw, known_chapter_ids={"ch-1"})
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs["chapter_ids"] == ["ch-1"]


# ---------------------------------------------------------------------------
# Drafting Readiness Tests
# ---------------------------------------------------------------------------

def test_drafting_readiness_passes_all_gates() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=[],
        unresolved_questions=[],
        overall_confidence=0.7,
        status="complete",
    )
    chapters = [
        StoryImportChapterSummary(chapter_id="ch-1", title="Ch 1", summary="First chapter."),
        StoryImportChapterSummary(chapter_id="ch-2", title="Ch 2", summary="Second chapter."),
    ]

    passed, reasons = service._check_drafting_readiness(
        continuity_finding=finding,
        chapter_summaries=chapters,
        foundation_pov="THIRD_LIMITED",
        foundation_tone="melancholy",
    )
    assert passed is True
    assert reasons == []


def test_drafting_readiness_fails_weak_continuity() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=[],
        unresolved_questions=[],
        overall_confidence=0.2,
        status="complete",
    )
    chapters = [
        StoryImportChapterSummary(chapter_id="ch-1", title="Ch 1", summary="First chapter."),
    ]

    passed, reasons = service._check_drafting_readiness(
        continuity_finding=finding,
        chapter_summaries=chapters,
        foundation_pov="THIRD_LIMITED",
        foundation_tone="melancholy",
    )
    assert passed is False
    assert any("below drafting threshold" in r for r in reasons)


def test_drafting_readiness_fails_critical_contradictions() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=["Timeline is impossible: Alice dies in ch-1 but appears in ch-3"],
        unresolved_questions=[],
        overall_confidence=0.7,
        status="complete",
    )
    chapters = [
        StoryImportChapterSummary(chapter_id="ch-1", title="Ch 1", summary="First chapter."),
    ]

    passed, reasons = service._check_drafting_readiness(
        continuity_finding=finding,
        chapter_summaries=chapters,
        foundation_pov="THIRD_LIMITED",
        foundation_tone="melancholy",
    )
    assert passed is False
    assert any("Critical contradiction" in r for r in reasons)


def test_drafting_readiness_fails_unstable_voice() -> None:
    service = MultiPassImportService(StubInferenceBackend())
    finding = ContinuityFinding(
        project_id="proj",
        threads=[],
        states=[],
        contradictions=[],
        unresolved_questions=[],
        overall_confidence=0.7,
        status="complete",
    )
    chapters = [
        StoryImportChapterSummary(chapter_id="ch-1", title="Ch 1", summary="First chapter."),
    ]

    passed, reasons = service._check_drafting_readiness(
        continuity_finding=finding,
        chapter_summaries=chapters,
        foundation_pov=None,
        foundation_tone=None,
    )
    assert passed is False
    assert any("voice guidance" in r.lower() for r in reasons)


# ---------------------------------------------------------------------------
# Prompt Builder Tests
# ---------------------------------------------------------------------------

def test_continuity_prompt_builder_returns_valid_request() -> None:
    req = build_continuity_analysis_request(
        model="test-model",
        chapter_summaries=[
            "Chapter 1: Alice leaves home with the locket.",
            "Chapter 2: The village is attacked at night.",
        ],
        planning_json='{"sequences": []}',
    )

    assert req.model == "test-model"
    assert req.temperature == 0.1
    assert len(req.messages) >= 2
    system_msg = req.messages[0]
    user_msg = req.messages[1]
    assert system_msg.role == "system"
    assert user_msg.role == "user"
    assert "continuity" in system_msg.content.lower()
    assert "Alice leaves home" in user_msg.content


def test_draft_brief_prompt_builder_returns_valid_request() -> None:
    req = build_draft_brief_request(
        model="test-model",
        chapter_id="ch-1",
        chapter_title="The Departure",
        chapter_summary="Alice leaves home carrying the family locket.",
        continuity_threads="Thread 1: The Missing Heirloom",
        character_roster="Alice (protagonist)",
        voice_guidance="Third-person limited, atmospheric prose.",
    )

    assert req.model == "test-model"
    assert req.temperature == 0.2
    assert len(req.messages) >= 2
    system_msg = req.messages[0]
    user_msg = req.messages[1]
    assert system_msg.role == "system"
    assert user_msg.role == "user"
    assert "writer-facing" in system_msg.content.lower()
    assert "ch-1" in user_msg.content
    assert "The Departure" in user_msg.content


# ---------------------------------------------------------------------------
# Idempotency Tests
# ---------------------------------------------------------------------------

def test_continuity_thread_upsert_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-idem-thread"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    first = repo.upsert_continuity_thread(
        thread_id="thread-1",
        project_id=project_id,
        title="Original Title",
        summary="Original summary.",
        status="active",
        confidence_score=0.8,
        created_at=STAMP,
    )

    second = repo.upsert_continuity_thread(
        thread_id="thread-1",
        project_id=project_id,
        title="Updated Title",
        summary="Updated summary.",
        status="resolved",
        confidence_score=0.9,
        created_at=STAMP,
    )

    assert first.thread_id == second.thread_id
    assert second.title == "Updated Title"
    assert second.summary == "Updated summary."
    assert second.status == "resolved"
    assert second.confidence_score == 0.9

    threads = repo.list_continuity_threads(project_id)
    assert len(threads) == 1


def test_draft_brief_upsert_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "ops.db"
    project_id = "proj-idem-brief"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    first = repo.upsert_draft_brief(
        brief_id="brief-1",
        project_id=project_id,
        chapter_id="ch-1",
        objective="Original objective.",
        emotional_turn="Original turn.",
        voice_guidance="Original voice.",
        status="draft",
        confidence_score=0.7,
        created_at=STAMP,
    )

    second = repo.upsert_draft_brief(
        brief_id="brief-1",
        project_id=project_id,
        chapter_id="ch-1",
        objective="Updated objective.",
        emotional_turn="Updated turn.",
        voice_guidance="Updated voice.",
        status="approved",
        confidence_score=0.95,
        created_at=STAMP,
    )

    assert first.brief_id == second.brief_id
    assert second.objective == "Updated objective."
    assert second.status == "approved"
    assert second.confidence_score == 0.95

    briefs = repo.list_draft_briefs(project_id)
    assert len(briefs) == 1
