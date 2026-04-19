from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryArtifactLifecycleState, StorySuggestionLifecycleState
from app.services.drafting import DraftingNotFoundError, DraftingService, DraftingValidationError
from app.services.planning import PlanningService


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


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


def _service(tmp_path: Path) -> tuple[DraftingService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return DraftingService(repository), repository


def _planning_context(repository: StoryDevelopmentRepository, project_id: str) -> tuple[str, str]:
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
    return sequence.sequence_id, chapter.chapter_id


def test_drafting_service_registers_continuations_and_variants_with_provenance(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "drafting-service-1"
    _seed_project(repository.db_path, project_id)
    sequence_id, chapter_id = _planning_context(repository, project_id)

    draft = service.register_draft_artifact(
        project_id,
        artifact_id="draft-1",
        title="Opening Draft",
        content="The city rearranges itself at dusk.",
        source_plan_ids=[sequence_id, chapter_id],
        provenance_note="Generated from the opening plan.",
        status=StoryArtifactLifecycleState.DRAFT,
    )
    continuation = service.continue_draft(
        project_id,
        artifact_id="draft-2",
        title="Continuation Draft",
        content="The lead follows the shifting street pattern.",
        prior_draft_artifact_id=draft.artifact_id,
        provenance_note="Continuation from the opening draft.",
    )
    variant = service.create_alternate_variant(
        project_id,
        artifact_id="draft-3",
        title="Alternate Variant",
        content="The city reveals itself through the archive instead.",
        base_draft_artifact_id=draft.artifact_id,
        provenance_note="Alternate path from the opening draft.",
    )

    assert draft.status == StoryArtifactLifecycleState.DRAFT
    assert draft.source_plan_ids == [sequence_id, chapter_id]
    assert draft.provenance_note == "Generated from the opening plan."
    assert draft.source_context == ["plan:sequence-1", "plan:chapter-1"]

    assert continuation.status == StoryArtifactLifecycleState.DRAFT
    assert continuation.source_context[0] == "draft:draft-1"
    assert continuation.source_plan_ids == [sequence_id, chapter_id]
    assert variant.status == StoryArtifactLifecycleState.PROPOSED
    assert variant.source_context[0] == "draft:draft-1"

    stored_titles = [item.title for item in service.list_draft_artifacts(project_id)]
    assert stored_titles == ["Alternate Variant", "Continuation Draft", "Opening Draft"]


def test_drafting_service_merges_inherited_and_explicit_planning_context(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "drafting-service-merge"
    _seed_project(repository.db_path, project_id)
    sequence_id, chapter_id = _planning_context(repository, project_id)

    draft = service.register_draft_artifact(
        project_id,
        artifact_id="draft-merge-1",
        title="Base Draft",
        content="The city shifts at dusk.",
        source_plan_ids=[sequence_id],
        source_context=["foundation"],
    )

    continuation = service.continue_draft(
        project_id,
        artifact_id="draft-merge-2",
        title="Merged Continuation",
        content="The lead follows the hidden map.",
        prior_draft_artifact_id=draft.artifact_id,
        source_plan_ids=[chapter_id],
        source_context=["planning-note"],
    )
    variant = service.create_alternate_variant(
        project_id,
        artifact_id="draft-merge-3",
        title="Merged Variant",
        content="The lead goes through the archive instead.",
        base_draft_artifact_id=draft.artifact_id,
        source_plan_ids=[chapter_id],
        source_context=["alternate-angle"],
    )

    assert continuation.source_plan_ids == [sequence_id, chapter_id]
    assert continuation.source_context == [
        f"draft:{draft.artifact_id}",
        "planning-note",
    ]
    assert variant.source_plan_ids == [sequence_id, chapter_id]
    assert variant.source_context == [
        f"draft:{draft.artifact_id}",
        "alternate-angle",
    ]


def test_drafting_service_promotes_draft_into_manuscript_without_erasing_source_artifact(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "drafting-service-2"
    _seed_project(repository.db_path, project_id)
    sequence_id, chapter_id = _planning_context(repository, project_id)

    draft = service.register_draft_artifact(
        project_id,
        artifact_id="draft-10",
        title="Chapter Draft",
        content="The witness leaves a mapped clue.",
        source_plan_ids=[sequence_id, chapter_id],
        provenance_note="First-pass generated prose.",
    )

    manuscript = service.promote_draft_to_manuscript(
        project_id,
        document_id="manuscript-1",
        draft_artifact_id=draft.artifact_id,
        chapter_id=chapter_id,
        title="Chapter Manuscript",
    )
    edited = service.save_manuscript_document(
        project_id,
        document_id=manuscript.document_id,
        title=manuscript.title,
        content="The witness leaves a mapped clue, and the lead follows it carefully.",
        chapter_id=chapter_id,
    )

    assert manuscript.content == draft.content
    assert manuscript.current_draft_artifact_id == draft.artifact_id
    assert manuscript.version == 1
    assert edited.version == 2
    assert edited.current_draft_artifact_id == draft.artifact_id
    assert service.get_draft_artifact(project_id, artifact_id=draft.artifact_id).content == draft.content
    assert service.get_manuscript_document(project_id, document_id=manuscript.document_id).content == edited.content


def test_drafting_service_records_revision_suggestions_without_mutating_manuscripts(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "drafting-service-3"
    _seed_project(repository.db_path, project_id)
    _, chapter_id = _planning_context(repository, project_id)

    draft = service.register_draft_artifact(
        project_id,
        artifact_id="draft-20",
        title="Draft for Revisions",
        content="The city shifts too quickly to follow.",
        source_plan_ids=[chapter_id],
        provenance_note="Draft for revision testing.",
    )
    manuscript = service.promote_draft_to_manuscript(
        project_id,
        document_id="manuscript-20",
        draft_artifact_id=draft.artifact_id,
        chapter_id=chapter_id,
        title="Revision Target",
    )

    suggestion = service.create_revision_suggestion(
        project_id,
        suggestion_id="suggestion-1",
        target_document_id=manuscript.document_id,
        source_text=manuscript.content,
        proposed_text="The city shifts slowly enough for the lead to track it.",
        rationale="Reduce the pace so the clue can be followed.",
    )

    assert suggestion.status == StorySuggestionLifecycleState.REQUESTED
    assert suggestion.target_document_id == manuscript.document_id
    assert suggestion.source_context == [f"manuscript:{manuscript.document_id}"]
    assert service.get_manuscript_document(project_id, document_id=manuscript.document_id).content == manuscript.content
    assert service.list_revision_suggestions_for_document(project_id, target_document_id=manuscript.document_id) == (suggestion,)


def test_drafting_service_rejects_cross_project_sources_and_missing_documents(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "drafting-service-4"
    other_project_id = "drafting-service-4b"
    _seed_project(repository.db_path, project_id)
    _seed_project(repository.db_path, other_project_id)
    _, chapter_id = _planning_context(repository, project_id)
    _planning_context(repository, other_project_id)

    service.register_draft_artifact(
        project_id,
        artifact_id="draft-30",
        title="Primary Draft",
        content="A clean test draft.",
        source_plan_ids=[chapter_id],
    )

    try:
        service.continue_draft(
            project_id,
            artifact_id="draft-31",
            title="Bad Continuation",
            content="This should fail.",
            prior_draft_artifact_id="missing-draft",
        )
    except DraftingNotFoundError:
        pass
    else:
        raise AssertionError("expected missing draft error")

    try:
        service.create_revision_suggestion(
            project_id,
            suggestion_id="suggestion-2",
            target_document_id="missing-manuscript",
            source_text="x",
            proposed_text="y",
            rationale="z",
        )
    except DraftingNotFoundError:
        pass
    else:
        raise AssertionError("expected missing manuscript error")

    try:
        service.continue_draft(
            other_project_id,
            artifact_id="draft-33",
            title="Cross Project Continuation",
            content="This should fail too.",
            prior_draft_artifact_id="draft-30",
        )
    except DraftingNotFoundError:
        pass
    else:
        raise AssertionError("expected cross-project source error")

    try:
        service.continue_draft(
            project_id,
            artifact_id="draft-32",
            title="Bad Continuation",
            content="This should also fail.",
            prior_draft_artifact_id="draft-30",
            prior_manuscript_document_id="manuscript-1",
        )
    except DraftingValidationError:
        pass
    else:
        raise AssertionError("expected mutually exclusive source validation error")
