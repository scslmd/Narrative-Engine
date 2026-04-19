from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.foundation import (
    FoundationProfileInput,
    FoundationProfilePatch,
    FoundationService,
)


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _register_project(db_path: Path, project_id: str) -> None:
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
                f"Project {project_id}",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _foundation_input() -> FoundationProfileInput:
    return FoundationProfileInput(
        premise="A cartographer maps a city that changes every dusk.",
        logline="A cartographer must chart the shifting city before it erases everyone inside it.",
        thematic_spine="Memory versus control",
        emotional_promise="The story rewards trust, sacrifice, and chosen memory.",
        tone_and_voice_direction="Lyric and tense",
        target_audience="Adult fantasy readers",
        narrative_constraints=("No time travel", "Keep the city physically coherent"),
        complexity_level="Medium",
        success_definition="The draft resolves the city mystery without breaking continuity.",
    )


def test_foundation_service_reads_active_profile_and_preserves_revision_history(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "foundation-project-1"
    _register_project(db_path, project_id)
    service = FoundationService(repository=StoryDevelopmentRepository(db_path))

    first_result = service.create_foundation_revision(project_id, _foundation_input())
    second_result = service.update_foundation_revision(
        project_id,
        FoundationProfilePatch(
            premise="A cartographer maps a city that changes every dawn.",
            narrative_constraints=("No time travel", "Keep the city physically coherent", "No silent retcons"),
        ),
    )

    active_result = service.read_active_foundation(project_id)

    assert active_result.foundation_id == f"foundation:{project_id}"
    assert active_result.current_revision_id == second_result.created_revision.revision_id
    assert [revision.revision_id for revision in active_result.revision_history] == [
        first_result.created_revision.revision_id,
        second_result.created_revision.revision_id,
    ]
    assert active_result.revision_history[0].snapshot.premise == _foundation_input().premise
    assert active_result.revision_history[0].snapshot.version == 1
    assert active_result.revision_history[1].snapshot.premise == "A cartographer maps a city that changes every dawn."
    assert active_result.revision_history[1].snapshot.version == 2
    assert active_result.active_profile == active_result.revision_history[-1].snapshot


def test_foundation_service_generates_downstream_review_cues_for_changed_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "foundation-project-2"
    _register_project(db_path, project_id)
    service = FoundationService(repository=StoryDevelopmentRepository(db_path))

    service.create_foundation_revision(project_id, _foundation_input())
    write_result = service.update_foundation_revision(
        project_id,
        FoundationProfilePatch(
            premise="A cartographer maps a city that changes every dawn.",
            thematic_spine="Memory must be chosen rather than inherited.",
            tone_and_voice_direction="Sharper and more urgent",
            narrative_constraints=("No time travel", "Keep the city physically coherent", "No silent retcons"),
        ),
    )

    cue_areas = [cue.impacted_area for cue in write_result.downstream_review_cues]
    assert cue_areas == [
        "story_arc",
        "character_background",
        "world_bible",
        "planning",
        "drafting",
        "review",
    ]
    assert all(cue.triggering_revision_id == write_result.created_revision.revision_id for cue in write_result.downstream_review_cues)
    assert write_result.downstream_review_cues[0].triggering_fields == ("premise", "thematic_spine")
    assert write_result.downstream_review_cues[1].triggering_fields == ("thematic_spine", "tone_and_voice_direction")
    assert write_result.downstream_review_cues[2].triggering_fields == ("narrative_constraints",)
    assert write_result.downstream_review_cues[3].triggering_fields == (
        "premise",
        "thematic_spine",
        "narrative_constraints",
    )
    assert write_result.downstream_review_cues[4].triggering_fields == (
        "premise",
        "thematic_spine",
        "tone_and_voice_direction",
        "narrative_constraints",
    )
    assert write_result.downstream_review_cues[5].triggering_fields == ("tone_and_voice_direction",)
    assert "story arc" in write_result.downstream_review_cues[0].reason
    assert service.list_downstream_review_cues(project_id) == write_result.downstream_review_cues

