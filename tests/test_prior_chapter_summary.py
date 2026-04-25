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
