from __future__ import annotations

import pytest
from app.schemas.story_development import PriorChapterSummary


def test_prior_chapter_summary_dataclass():
    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves the village", "Meets Soraya at the crossroads"],
        character_states={"Kael": "restless, seeking purpose", "Soraya": "mysterious, evasive"},
        unresolved_threads=["Who is Soraya really?", "What is in the package?"],
    )
    assert len(summary.key_events) == 2
    assert "Kael" in summary.character_states


def test_prior_chapter_summary_to_context_string():
    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves"],
        character_states={"Kael": "restless"},
        unresolved_threads=["Where is he going?"],
    )
    ctx = summary.to_context_string()
    assert "The Departure" in ctx
    assert "Kael leaves" in ctx


def test_prior_chapter_summary_truncation_respects_limits():
    events = [f"Event {i}" for i in range(15)]
    states = {f"Char{i}": f"state {i}" for i in range(12)}
    threads = [f"Thread {i}" for i in range(8)]

    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="Long Chapter",
        key_events=events,
        character_states=states,
        unresolved_threads=threads,
    )
    ctx = summary.to_context_string()

    event_lines = [l for l in ctx.splitlines() if l.startswith("  - ") and "Event" in l]
    assert len(event_lines) <= 10, f"Expected at most 10 events, got {len(event_lines)}"

    char_lines = [l for l in ctx.splitlines() if l.startswith("  - Char")]
    assert len(char_lines) <= 10, f"Expected at most 10 character states, got {len(char_lines)}"

    thread_lines = [l for l in ctx.splitlines() if l.startswith("  ? ")]
    assert len(thread_lines) <= 5, f"Expected at most 5 threads, got {len(thread_lines)}"


def test_prior_chapter_summary_empty_collections():
    summary = PriorChapterSummary(
        chapter_id="ch-001",
        title="Empty Chapter",
        key_events=[],
        character_states={},
        unresolved_threads=[],
    )
    ctx = summary.to_context_string()
    assert ctx == "PRIOR CHAPTER: Empty Chapter"
