from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryObjectType
from app.services.drafting import DraftingService
from app.services.planning import PlanningService
from app.services.review_routing import (
    ReviewRoutingNotFoundError,
    ReviewRoutingService,
    ReviewRoutingValidationError,
)


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
                f"Project {project_id}",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _service(tmp_path: Path) -> tuple[ReviewRoutingService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return ReviewRoutingService(repository), repository


def _drafting_context(repository: StoryDevelopmentRepository, project_id: str) -> tuple[str, str, str]:
    planning = PlanningService(repository)
    sequence = planning.create_sequence_plan(
        project_id,
        sequence_id="sequence-1",
        title="Opening Sequence",
        summary="The opening movement of the story.",
        beat_ids=["beat-1"],
        chapter_ids=[],
        status="draft",
    )
    chapter = planning.create_chapter_plan(
        project_id,
        chapter_id="chapter-1",
        title="Chapter One",
        summary="The lead enters the shifting city.",
        sequence_id=sequence.sequence_id,
        objective="Find the witness.",
        conflict="The streets will not hold still.",
        stakes="The witness may disappear.",
        active_character_ids=["lead"],
        continuity_requirements=["Use the dusk map."],
        unresolved_questions=["Which district shifts first?"],
        status="draft",
    )
    draft_service = DraftingService(repository)
    draft = draft_service.register_draft_artifact(
        project_id,
        artifact_id="draft-1",
        title="Opening Draft",
        content="The city rearranges itself at dusk.",
        source_plan_ids=[sequence.sequence_id, chapter.chapter_id],
        provenance_note="Generated from the opening plan.",
    )
    manuscript = draft_service.promote_draft_to_manuscript(
        project_id,
        document_id="manuscript-1",
        draft_artifact_id=draft.artifact_id,
        chapter_id=chapter.chapter_id,
        title="Opening Manuscript",
    )
    return sequence.sequence_id, chapter.chapter_id, manuscript.document_id


def test_review_routing_records_decisions_and_inspect_links(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "review-routing-1"
    _seed_project(repository.db_path, project_id)
    _, _, manuscript_id = _drafting_context(repository, project_id)

    decisions = []
    for index, decision in enumerate(("accept", "reject", "defer", "escalate", "refine"), start=1):
        decisions.append(
            service.record_review_decision(
                project_id,
                decision_id=f"decision-{index}",
                target_kind=StoryObjectType.MANUSCRIPT_DOCUMENT,
                target_id=manuscript_id,
                decision=decision,
                notes=f"{decision.title()} the current manuscript.",
                source_context=[f"context-{index}"],
            )
        )

    link = service.create_inspect_link(
        project_id,
        link_id="inspect-link-1",
        object_kind=StoryObjectType.MANUSCRIPT_DOCUMENT,
        object_id=manuscript_id,
        logical_run_id="logical-review-1",
        run_id="run-review-1",
        run_kind="review-routing",
        attempt_number=1,
        label="Manuscript review",
    )

    assert [decision.decision for decision in decisions] == ["accept", "reject", "defer", "escalate", "refine"]
    assert [item.decision_id for item in service.list_review_decisions(project_id, target_kind=StoryObjectType.MANUSCRIPT_DOCUMENT, target_id=manuscript_id)] == [
        "decision-1",
        "decision-2",
        "decision-3",
        "decision-4",
        "decision-5",
    ]
    assert link.object_kind == StoryObjectType.MANUSCRIPT_DOCUMENT.value
    assert service.list_inspect_run_links(project_id, object_kind=StoryObjectType.MANUSCRIPT_DOCUMENT, object_id=manuscript_id) == (link,)
    assert service.list_inspect_run_links(project_id, run_id="run-review-1") == (link,)


def test_review_routing_routes_finding_back_into_drafting_without_mutating_source_manuscript(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "review-routing-2"
    _seed_project(repository.db_path, project_id)
    _, _, manuscript_id = _drafting_context(repository, project_id)

    finding = repository.upsert_checker_finding(
        finding_id="finding-1",
        project_id=project_id,
        source_object_id=manuscript_id,
        source_object_kind=StoryObjectType.MANUSCRIPT_DOCUMENT.value,
        severity="warning",
        summary="Opening rhythm needs tightening.",
        details="The lead arrives before the scene has enough pressure.",
        source_context=["checker-run-1"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    original_manuscript = repository.get_manuscript_document(manuscript_id)

    result = service.route_finding_to_drafting(
        project_id,
        finding_id=finding.finding_id,
        target_document_id=manuscript_id,
        decision_id="decision-route-1",
        suggestion_id="suggestion-route-1",
        proposed_text="The lead waits longer before the city shifts into focus.",
        rationale="Tighten the opening rhythm.",
        label="Drafting routing",
    )

    assert result.finding.finding_id == finding.finding_id
    assert result.decision.target_kind == StoryObjectType.MANUSCRIPT_DOCUMENT.value
    assert result.decision.decision == "refine"
    assert result.revision_suggestion.target_document_id == manuscript_id
    assert result.revision_suggestion.rationale == "Tighten the opening rhythm."
    assert result.inspect_link.object_kind == StoryObjectType.REVISION_SUGGESTION.value
    assert repository.get_manuscript_document(manuscript_id).content == original_manuscript.content
    assert service.list_review_decisions(project_id, target_kind=StoryObjectType.MANUSCRIPT_DOCUMENT, target_id=manuscript_id)[0].decision_id == "decision-route-1"
    assert service.list_inspect_run_links(
        project_id,
        object_kind=StoryObjectType.REVISION_SUGGESTION,
        object_id="suggestion-route-1",
    )[0].link_id == result.inspect_link.link_id


def test_review_routing_routes_finding_back_into_planning_without_mutating_plan_state(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "review-routing-3"
    _seed_project(repository.db_path, project_id)

    planning = PlanningService(repository)
    sequence = planning.create_sequence_plan(
        project_id,
        sequence_id="sequence-1",
        title="Opening Sequence",
        summary="The first movement of the story.",
        beat_ids=[],
        chapter_ids=[],
        status="draft",
    )
    chapter = planning.create_chapter_plan(
        project_id,
        chapter_id="chapter-1",
        title="Chapter One",
        summary="The lead enters the shifting city.",
        sequence_id=sequence.sequence_id,
        objective="Find the witness.",
        conflict="The streets will not hold still.",
        stakes="The witness may disappear.",
        active_character_ids=["lead"],
        continuity_requirements=["Use the dusk map."],
        unresolved_questions=["Which district shifts first?"],
        status="draft",
    )
    scene = planning.create_scene_plan(
        project_id,
        scene_id="scene-1",
        title="Market Crossing",
        summary="A dangerous crossing through the moving market.",
        chapter_id=chapter.chapter_id,
        objective="Reach the archive.",
        conflict="Crowds and architecture both change course.",
        stakes="The witness connection could be missed.",
        active_character_ids=["lead", "guide"],
        continuity_requirements=["Market layout must match the prior clue."],
        unresolved_questions=["Who follows them?"],
        status="draft",
    )
    finding = repository.upsert_checker_finding(
        finding_id="finding-2",
        project_id=project_id,
        source_object_id=scene.scene_id,
        source_object_kind=StoryObjectType.SCENE_PLAN.value,
        severity="warning",
        summary="Scene pacing needs a stronger turn.",
        details="The cross-market beat should trigger a new obstacle.",
        source_context=["checker-run-2"],
        created_at=STAMP,
        updated_at=STAMP,
    )

    result = service.route_finding_to_planning(
        project_id,
        finding_id=finding.finding_id,
        target_kind=StoryObjectType.SCENE_PLAN,
        target_id=scene.scene_id,
        decision_id="decision-route-2",
        packet_id="packet-route-1",
        label="Planning routing",
    )

    assert result.finding.finding_id == finding.finding_id
    assert result.decision.target_kind == StoryObjectType.SCENE_PLAN.value
    assert result.decision.decision == "refine"
    assert result.chapter_packet.chapter_id == chapter.chapter_id
    assert result.chapter_packet.packet_id == "packet-route-1"
    assert result.inspect_link.object_kind == StoryObjectType.CHAPTER_PACKET.value
    assert repository.get_scene_plan(scene.scene_id).chapter_id == chapter.chapter_id
    assert repository.get_chapter_packet("packet-route-1").scene_goals == ["Reach the archive."]
    assert service.list_review_decisions(project_id, target_kind=StoryObjectType.SCENE_PLAN, target_id=scene.scene_id)[0].decision_id == "decision-route-2"


def test_review_routing_rejects_partial_filters_and_missing_targets(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "review-routing-4"
    _seed_project(repository.db_path, project_id)

    try:
        service.list_checker_findings(project_id, source_object_kind=StoryObjectType.MANUSCRIPT_DOCUMENT)
    except ReviewRoutingValidationError:
        pass
    else:
        raise AssertionError("expected paired source filter validation error")

    try:
        service.record_review_decision(
            project_id,
            decision_id="decision-missing",
            target_kind=StoryObjectType.MANUSCRIPT_DOCUMENT,
            target_id="missing-manuscript",
            decision="refine",
        )
    except ReviewRoutingNotFoundError:
        pass
    else:
        raise AssertionError("expected missing target error")
