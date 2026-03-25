from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryArtifactLifecycleState
from app.services.drafting import DraftingService
from app.services.planning import PlanningService
from app.services.review_routing import ReviewRoutingService

# Fixed timestamp for deterministic test runs
STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)


def _seed_project(db_path: Path, project_id: str) -> None:
    """Seeds a basic project record into the database."""
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
                "Integration Flow Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    """Builds a FastAPI test client and repository for a new project."""
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "int-flow-test"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


def test_story_development_integration_flow(tmp_path: Path) -> None:
    """
    End-to-end integration test for the story development flow.
    This test covers:
    1. Creating canonical project context
    2. Persisting planning objects (sequence, chapter, scene)
    3. Generating drafting/manuscript state
    4. Routing a review finding to a revision suggestion
    5. Proving API projection reflects the resulting persisted state
    """
    # --- 1. Setup & Canonical Project Context ---
    client, repository = _build_client(tmp_path)
    project_id = "int-flow-test"

    # Initialize services
    planning_service = PlanningService(repository)
    drafting_service = DraftingService(repository)
    review_service = ReviewRoutingService(repository, drafting_service=drafting_service, planning_service=planning_service)

    # --- 2. Persist Planning Objects ---
    # Create a sequence plan
    sequence = planning_service.create_sequence_plan(
        project_id,
        sequence_id="seq-1",
        title="Main Narrative Arc",
        summary="The primary sequence for the story.",
        beat_ids=["beat-1", "beat-2"],
        chapter_ids=[],
        position=0,
    )
    assert sequence.sequence_id == "seq-1"
    assert sequence.project_id == project_id

    # Create a chapter plan
    chapter = planning_service.create_chapter_plan(
        project_id,
        chapter_id="ch-1",
        title="The Beginning",
        summary="Chapter one, the start of the adventure.",
        objective="Introduce the protagonist.",
        conflict="A mysterious event occurs.",
        stakes="The protagonist's world changes.",
        sequence_id=sequence.sequence_id,
        active_character_ids=["hero-1"],
        continuity_requirements=["Tone must be mysterious."],
        unresolved_questions=["What was the event?"],
        position=0,
    )
    assert chapter.chapter_id == "ch-1"
    assert chapter.sequence_id == sequence.sequence_id

    # Create a scene plan
    scene = planning_service.create_scene_plan(
        project_id,
        scene_id="sc-1",
        title="The Mysterious Event",
        summary="The scene where the event happens.",
        objective="Show the protagonist's reaction.",
        conflict="Immediate danger.",
        stakes="Personal safety.",
        chapter_id=chapter.chapter_id,
        active_character_ids=["hero-1"],
        continuity_requirements=["Tone must be mysterious."],
        unresolved_questions=["What was the event?"],
        position=0,
    )
    assert scene.scene_id == "sc-1"
    assert scene.chapter_id == chapter.chapter_id

    # Build a chapter packet (a derived planning artifact)
    packet = planning_service.build_chapter_packet(project_id, chapter.chapter_id)
    assert packet.chapter_id == chapter.chapter_id
    assert packet.status == "draft"

    # --- 3. Generate Drafting/Manuscript State ---
    # Register a draft artifact
    draft = drafting_service.register_draft_artifact(
        project_id,
        artifact_id="draft-1",
        title="Chapter One - First Draft",
        content="The sun was setting, casting long shadows. The event was about to unfold.",
        source_plan_ids=[sequence.sequence_id, chapter.chapter_id],
        provenance_note="Initial draft based on chapter plan.",
        status=StoryArtifactLifecycleState.DRAFT,
    )
    assert draft.artifact_id == "draft-1"
    assert draft.project_id == project_id

    # Promote to manuscript document
    manuscript = drafting_service.promote_draft_to_manuscript(
        project_id,
        document_id="manuscript-1",
        draft_artifact_id=draft.artifact_id,
        title="Chapter One",
        chapter_id=chapter.chapter_id,
    )
    assert manuscript.document_id == "manuscript-1"
    assert manuscript.chapter_id == chapter.chapter_id
    assert manuscript.current_draft_artifact_id == draft.artifact_id

    # --- 4. Route a Review Finding ---
    # Create a "checker finding" (simulating a quality check)
    finding = repository.upsert_checker_finding(
        finding_id="finding-1",
        project_id=project_id,
        source_object_kind="MANUSCRIPT_DOCUMENT",
        source_object_id=manuscript.document_id,
        severity="high",
        summary="Pacing issue in the opening scene.",
        details="The description of the setting is too long and delays the conflict.",
        source_context=[f"manuscript:{manuscript.document_id}"],
        created_at=STAMP,
        updated_at=STAMP,
    )

    # Route the finding to drafting, which creates a review decision, revision suggestion, and inspect link
    routing_result = review_service.route_finding_to_drafting(
        project_id,
        finding_id=finding.finding_id,
        target_document_id=manuscript.document_id,
        decision_id="review-decision-1",
        suggestion_id="suggestion-1",
        proposed_text="The sun set. Shadows lengthened. A sudden noise broke the silence.",
        decision="refine",
        source_text=manuscript.content,
        rationale="Improve pacing by shortening the opening.",
        inspect_link_id="inspect-link-1",
        logical_run_id="run-1",
        run_id="review-1",
        run_kind="review-routing",
        label="Pacing review",
        attempt_number=1,
    )

    # Assert the routing result contains all expected objects
    assert routing_result.finding.finding_id == finding.finding_id
    assert routing_result.decision.decision_id == "review-decision-1"
    assert routing_result.decision.target_id == manuscript.document_id
    assert routing_result.decision.decision == "refine"
    assert routing_result.revision_suggestion.suggestion_id == "suggestion-1"
    assert routing_result.revision_suggestion.target_document_id == manuscript.document_id
    assert routing_result.inspect_link.link_id == "inspect-link-1"

    # --- 5. Prove API Projection Reflects Persisted State ---
    # Make API calls to verify the state persisted in steps 2-4 is correctly projected

    # 5a. Verify planning objects are accessible via API
    sequence_response = client.get(f"/story-development/planning/sequence-plans/{sequence.sequence_id}?project_id={project_id}")
    assert sequence_response.status_code == 200
    assert sequence_response.json()["sequence_id"] == sequence.sequence_id

    chapter_response = client.get(f"/story-development/planning/chapter-plans/{chapter.chapter_id}?project_id={project_id}")
    assert chapter_response.status_code == 200
    assert chapter_response.json()["chapter_id"] == chapter.chapter_id
    assert chapter_response.json()["sequence_id"] == sequence.sequence_id

    scene_response = client.get(f"/story-development/planning/scene-plans/{scene.scene_id}?project_id={project_id}")
    assert scene_response.status_code == 200
    assert scene_response.json()["scene_id"] == scene.scene_id
    assert scene_response.json()["chapter_id"] == chapter.chapter_id

    packet_response = client.get(f"/story-development/planning/chapter-packets/{packet.packet_id}?project_id={project_id}")
    assert packet_response.status_code == 200
    assert packet_response.json()["chapter_id"] == chapter.chapter_id

    # 5b. Verify drafting objects are accessible via API
    draft_response = client.get(f"/story-development/drafting/draft-artifacts/{draft.artifact_id}?project_id={project_id}")
    assert draft_response.status_code == 200
    assert draft_response.json()["artifact_id"] == draft.artifact_id
    assert draft_response.json()["title"] == draft.title

    manuscript_response = client.get(f"/story-development/drafting/manuscript-documents/{manuscript.document_id}?project_id={project_id}")
    assert manuscript_response.status_code == 200
    assert manuscript_response.json()["document_id"] == manuscript.document_id
    assert manuscript_response.json()["chapter_id"] == chapter.chapter_id

    # 5c. Verify review routing artifacts are accessible via API
    finding_response = client.get(f"/story-development/review/findings/{finding.finding_id}?project_id={project_id}")
    assert finding_response.status_code == 200
    assert finding_response.json()["finding_id"] == finding.finding_id
    assert finding_response.json()["source_object_id"] == manuscript.document_id

    decision_response = client.get(f"/story-development/review/decisions/{routing_result.decision.decision_id}?project_id={project_id}")
    assert decision_response.status_code == 200
    assert decision_response.json()["decision_id"] == routing_result.decision.decision_id
    assert decision_response.json()["target_id"] == manuscript.document_id

    suggestion_response = client.get(f"/story-development/drafting/revision-suggestions/{routing_result.revision_suggestion.suggestion_id}?project_id={project_id}")
    assert suggestion_response.status_code == 200
    assert suggestion_response.json()["suggestion_id"] == routing_result.revision_suggestion.suggestion_id
    assert suggestion_response.json()["target_document_id"] == manuscript.document_id

    link_response = client.get(f"/story-development/review/inspect-links/{routing_result.inspect_link.link_id}?project_id={project_id}")
    assert link_response.status_code == 200
    assert link_response.json()["link_id"] == routing_result.inspect_link.link_id

    # 5d. Verify list endpoints reflect the state
    chapters_list_response = client.get(f"/story-development/planning/chapter-plans?project_id={project_id}")
    assert chapters_list_response.status_code == 200
    chapter_ids_in_list = [item["chapter_id"] for item in chapters_list_response.json()["items"]]
    assert chapter.chapter_id in chapter_ids_in_list

    manuscripts_list_response = client.get(f"/story-development/drafting/manuscript-documents?project_id={project_id}")
    assert manuscripts_list_response.status_code == 200
    manuscript_ids_in_list = [item["document_id"] for item in manuscripts_list_response.json()["items"]]
    assert manuscript.document_id in manuscript_ids_in_list

    # --- Mission Accomplishment Report ---
    # status: complete
    # files_changed: F:\Dev\Narrative-Engine\tests\test_story_development_integration_flow.py
    # summary: One deterministic end-to-end integration flow created, covering planning, drafting, review routing, and API projection.
    # tests_run: 1
    # blockers_or_risks: None
