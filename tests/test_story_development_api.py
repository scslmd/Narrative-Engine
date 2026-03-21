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


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)


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
                "Story Development API Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-api"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


def _seed_story_development_data(repository: StoryDevelopmentRepository, *, project_id: str) -> dict[str, str]:
    planning_service = PlanningService(repository)
    drafting_service = DraftingService(repository)

    decision_parent = repository.record_story_decision_node(
        node_id="decision-root",
        project_id=project_id,
        node_type="DECISION",
        change_type="ARC_SELECTION",
        subject_type="ARC_SELECTION",
        subject_id="arc-selection-1",
        made_by="writer:test",
        decision_made_at=STAMP,
        summary="Choose the primary arc.",
        prior_state_ref="arc:before",
        new_state_ref="arc:after",
        reason_or_note="Best fit for the current draft.",
        related_object_links=[{"object_type": "ARC_SELECTION", "object_id": "arc-selection-1", "relation_kind": "primary"}],
        informing_object_links=[{"object_type": "ARC_COMPARISON_RECORD", "object_id": "arc-comp-1", "relation_kind": "evidence"}],
        created_at=STAMP,
        updated_at=STAMP,
    )
    decision_child = repository.record_story_decision_node(
        node_id="decision-child",
        project_id=project_id,
        node_type="DECISION",
        change_type="STAGE_REDEFINE",
        subject_type="STORY_FLOW_STAGE",
        subject_id="stage-2",
        parent_node_id=decision_parent.node_id,
        branch_id="branch-1",
        made_by="writer:test",
        decision_made_at=STAMP.replace(hour=13),
        summary="Redefine the stage flow.",
        prior_state_summary="Old flow",
        new_state_summary="New flow",
        reason_or_note="Tighten the pacing.",
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )

    sequence = planning_service.create_sequence_plan(
        project_id,
        sequence_id="sequence-1",
        title="Sequence One",
        summary="First planning sequence.",
        beat_ids=["beat-1"],
        chapter_ids=[],
        position=0,
    )
    chapter = planning_service.create_chapter_plan(
        project_id,
        chapter_id="chapter-1",
        title="Chapter One",
        summary="Opening chapter.",
        objective="Establish the premise.",
        conflict="A small disruption.",
        stakes="The lead must adapt.",
        sequence_id=sequence.sequence_id,
        active_character_ids=["character-1"],
        continuity_requirements=["Keep the opening tone consistent."],
        unresolved_questions=["Who opened the door?"],
        position=0,
    )
    scene = planning_service.create_scene_plan(
        project_id,
        scene_id="scene-1",
        title="Scene One",
        summary="Opening scene.",
        objective="Introduce the lead.",
        conflict="A brief interruption.",
        stakes="The lead stays on task.",
        chapter_id=chapter.chapter_id,
        active_character_ids=["character-1"],
        continuity_requirements=["Keep the opening tone consistent."],
        unresolved_questions=["Who opened the door?"],
        position=0,
    )
    dependency = planning_service.add_planning_dependency(
        project_id,
        dependency_id="dependency-1",
        upstream_id=chapter.chapter_id,
        downstream_id=scene.scene_id,
        dependency_kind="scene_continuity",
        reason="Scene depends on chapter setup.",
    )
    packet = planning_service.build_chapter_packet(project_id, chapter.chapter_id)

    draft = drafting_service.register_draft_artifact(
        project_id,
        artifact_id="draft-1",
        title="Draft One",
        content="A bright opening paragraph.",
        source_plan_ids=[sequence.sequence_id, chapter.chapter_id],
        provenance_note="Seeded for the API test.",
        status=StoryArtifactLifecycleState.DRAFT,
    )
    manuscript = drafting_service.promote_draft_to_manuscript(
        project_id,
        document_id="manuscript-1",
        draft_artifact_id=draft.artifact_id,
        title="Manuscript One",
        chapter_id=chapter.chapter_id,
    )
    revision = drafting_service.create_revision_suggestion(
        project_id,
        suggestion_id="revision-1",
        target_document_id=manuscript.document_id,
        source_text=manuscript.content,
        proposed_text="A sharper opening paragraph.",
        rationale="Improve momentum.",
    )

    repository.upsert_checker_finding(
        finding_id="finding-1",
        project_id=project_id,
        source_object_kind="MANUSCRIPT_DOCUMENT",
        source_object_id=manuscript.document_id,
        severity="medium",
        summary="Opening needs a continuity check.",
        details="The scene should state the weather clearly.",
        source_context=[f"manuscript:{manuscript.document_id}"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    repository.upsert_review_decision(
        decision_id="review-decision-1",
        project_id=project_id,
        target_id=manuscript.document_id,
        target_kind="MANUSCRIPT_DOCUMENT",
        decision="refine",
        notes="Route toward revision.",
        source_context=[f"finding:finding-1"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    repository.upsert_inspect_run_link(
        link_id="inspect-link-1",
        project_id=project_id,
        object_kind="REVISION_SUGGESTION",
        object_id=revision.suggestion_id,
        logical_run_id="finding-1",
        run_id="review-decision-1",
        run_kind="review-routing",
        attempt_number=1,
        label="API review link",
        created_at=STAMP,
        updated_at=STAMP,
    )

    return {
        "decision_parent": decision_parent.node_id,
        "decision_child": decision_child.node_id,
        "sequence_id": sequence.sequence_id,
        "chapter_id": chapter.chapter_id,
        "scene_id": scene.scene_id,
        "packet_id": packet.packet_id,
        "draft_id": draft.artifact_id,
        "manuscript_id": manuscript.document_id,
        "revision_id": revision.suggestion_id,
    }


def test_story_development_api_returns_projected_lists_and_items(tmp_path: Path) -> None:
    client, repository = _build_client(tmp_path)
    project_id = "story-dev-api"
    seeded = _seed_story_development_data(repository, project_id=project_id)

    decision_response = client.get(f"/story-development/decisions?project_id={project_id}")
    review_finding_response = client.get(f"/story-development/review/findings?project_id={project_id}")
    planning_response = client.get(f"/story-development/planning/chapter-plans?project_id={project_id}")
    drafting_response = client.get(f"/story-development/drafting/draft-artifacts?project_id={project_id}")

    assert decision_response.status_code == 200
    assert [item["node_id"] for item in decision_response.json()["items"]] == [
        seeded["decision_parent"],
        seeded["decision_child"],
    ]
    assert decision_response.json()["meta"]["ordered_by"] == "decision_made_at_asc"

    decision_detail = client.get(f"/story-development/decisions/{seeded['decision_child']}?project_id={project_id}")
    decision_path = client.get(f"/story-development/decisions/{seeded['decision_child']}/path?project_id={project_id}")
    assert decision_detail.status_code == 200
    assert decision_detail.json()["node_id"] == seeded["decision_child"]
    assert decision_path.status_code == 200
    assert [item["node_id"] for item in decision_path.json()["parent_path"]] == [seeded["decision_parent"]]
    assert decision_path.json()["node"]["node_id"] == seeded["decision_child"]

    assert review_finding_response.status_code == 200
    assert review_finding_response.json()["items"][0]["finding_id"] == "finding-1"
    assert planning_response.status_code == 200
    assert [item["chapter_id"] for item in planning_response.json()["items"]] == [seeded["chapter_id"]]
    assert drafting_response.status_code == 200
    assert [item["artifact_id"] for item in drafting_response.json()["items"]] == [seeded["draft_id"]]

    chapter_packet_response = client.get(f"/story-development/planning/chapter-packets/{seeded['packet_id']}?project_id={project_id}")
    manuscript_response = client.get(f"/story-development/drafting/manuscript-documents/{seeded['manuscript_id']}?project_id={project_id}")
    revision_response = client.get(f"/story-development/drafting/revision-suggestions/{seeded['revision_id']}?project_id={project_id}")

    assert chapter_packet_response.status_code == 200
    assert chapter_packet_response.json()["chapter_id"] == seeded["chapter_id"]
    assert manuscript_response.status_code == 200
    assert manuscript_response.json()["document_id"] == seeded["manuscript_id"]
    assert revision_response.status_code == 200
    assert revision_response.json()["suggestion_id"] == seeded["revision_id"]


def test_story_development_api_validates_filter_pairs_and_returns_404s(tmp_path: Path) -> None:
    client, repository = _build_client(tmp_path)
    project_id = "story-dev-api"
    seeded = _seed_story_development_data(repository, project_id=project_id)

    bad_filter = client.get(f"/story-development/decisions?project_id={project_id}&subject_type=ARC_SELECTION")
    assert bad_filter.status_code == 400

    missing_routes = [
        f"/story-development/decisions/missing-node?project_id={project_id}",
        f"/story-development/review/findings/missing-finding?project_id={project_id}",
        f"/story-development/review/decisions/missing-decision?project_id={project_id}",
        f"/story-development/review/inspect-links/missing-link?project_id={project_id}",
        f"/story-development/planning/sequence-plans/missing-sequence?project_id={project_id}",
        f"/story-development/planning/chapter-plans/missing-chapter?project_id={project_id}",
        f"/story-development/planning/scene-plans/missing-scene?project_id={project_id}",
        f"/story-development/planning/dependencies/missing-dependency?project_id={project_id}",
        f"/story-development/planning/chapter-packets/missing-packet?project_id={project_id}",
        f"/story-development/drafting/draft-artifacts/missing-draft?project_id={project_id}",
        f"/story-development/drafting/manuscript-documents/missing-manuscript?project_id={project_id}",
        f"/story-development/drafting/revision-suggestions/missing-revision?project_id={project_id}",
    ]

    for path in missing_routes:
        response = client.get(path)
        assert response.status_code == 404

    cross_project = client.get(
        f"/story-development/drafting/manuscript-documents/{seeded['manuscript_id']}?project_id=wrong-project"
    )
    assert cross_project.status_code == 404
