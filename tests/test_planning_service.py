from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
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


def _service(tmp_path: Path) -> tuple[PlanningService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return PlanningService(repository), repository


def test_planning_service_preserves_parent_child_relationships_reorders_chapters_and_dependencies(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "planning-service-1"
    _seed_project(repository.db_path, project_id)

    sequence = service.create_sequence_plan(
        project_id,
        sequence_id="sequence-1",
        title="Opening Sequence",
        summary="The story opens with a hard pivot.",
        beat_ids=["beat-1"],
        chapter_ids=[],
        status="draft",
    )
    chapter_one = service.create_chapter_plan(
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
    chapter_two = service.create_chapter_plan(
        project_id,
        chapter_id="chapter-2",
        title="Chapter Two",
        summary="The lead reaches the archive.",
        sequence_id=sequence.sequence_id,
        objective="Secure the archive key.",
        conflict="The archive is under lockdown.",
        stakes="The only route to answers may close.",
        active_character_ids=["lead", "guide"],
        continuity_requirements=["The archive seals at sunset."],
        unresolved_questions=["Who opened the side passage?"],
        status="draft",
    )
    scene = service.create_scene_plan(
        project_id,
        scene_id="scene-1",
        title="Market Crossing",
        summary="A dangerous crossing through the moving market.",
        chapter_id=chapter_one.chapter_id,
        objective="Reach the archive.",
        conflict="Crowds and architecture both change course.",
        stakes="The witness connection could be missed.",
        active_character_ids=["lead", "guide"],
        continuity_requirements=["Market layout must match the prior clue."],
        unresolved_questions=["Who follows them?"],
        status="draft",
    )
    dependency = service.add_planning_dependency(
        project_id,
        dependency_id="dependency-1",
        upstream_id=chapter_one.chapter_id,
        downstream_id=scene.scene_id,
        dependency_kind="precedes",
        reason="The chapter must establish the market route before the scene.",
    )

    assert repository.get_sequence_plan(sequence.sequence_id).chapter_ids == [chapter_one.chapter_id, chapter_two.chapter_id]
    assert chapter_one.sequence_id == sequence.sequence_id
    assert scene.chapter_id == chapter_one.chapter_id
    assert dependency.reason == "The chapter must establish the market route before the scene."

    reordered = service.reorder_plan_objects(
        project_id,
        plan_kind="chapter",
        ordered_plan_ids=[chapter_two.chapter_id, chapter_one.chapter_id],
    )

    assert [chapter.chapter_id for chapter in reordered] == [chapter_two.chapter_id, chapter_one.chapter_id]
    assert [chapter.chapter_id for chapter in repository.list_chapter_plans(project_id)] == [
        chapter_two.chapter_id,
        chapter_one.chapter_id,
    ]
    assert repository.get_sequence_plan(sequence.sequence_id).chapter_ids == [
        chapter_two.chapter_id,
        chapter_one.chapter_id,
    ]
    assert repository.get_scene_plan(scene.scene_id).chapter_id == chapter_one.chapter_id
    assert repository.get_planning_dependency(dependency.dependency_id).dependency_kind == "precedes"


def test_planning_service_builds_deterministic_chapter_packet_from_repository_context(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path)
    project_id = "planning-service-2"
    _seed_project(repository.db_path, project_id)

    sequence = service.create_sequence_plan(
        project_id,
        sequence_id="sequence-1",
        title="Opening Sequence",
        summary="The first movement of the story.",
        beat_ids=[],
        chapter_ids=[],
        status="draft",
    )
    chapter = service.create_chapter_plan(
        project_id,
        chapter_id="chapter-1",
        title="Chapter One",
        summary="The lead crosses the market.",
        sequence_id=sequence.sequence_id,
        objective="Reach the archive.",
        conflict="The market keeps shifting.",
        stakes="The route may be lost.",
        active_character_ids=["lead"],
        continuity_requirements=["The archive must remain sealed until sunset."],
        unresolved_questions=["Who is tracking the lead?"],
        status="draft",
    )
    scene_one = service.create_scene_plan(
        project_id,
        scene_id="scene-1",
        title="Approach",
        summary="The lead approaches the archive.",
        chapter_id=chapter.chapter_id,
        objective="Get inside the market corridor.",
        conflict="The route folds back on itself.",
        stakes="A wrong turn may expose the lead.",
        active_character_ids=["lead"],
        continuity_requirements=["The corridor opens only once."],
        unresolved_questions=["Which guard is compromised?"],
        status="draft",
    )
    scene_two = service.create_scene_plan(
        project_id,
        scene_id="scene-2",
        title="Reveal",
        summary="The witness clue is revealed.",
        chapter_id=chapter.chapter_id,
        objective="Reveal the archive clue.",
        conflict="The witness is already gone.",
        stakes="The next step must be immediate.",
        active_character_ids=["lead", "guide"],
        continuity_requirements=["The clue must follow the corridor scene."],
        unresolved_questions=["What did the witness hide?"],
        status="draft",
    )
    dependency_one = service.add_planning_dependency(
        project_id,
        dependency_id="dependency-1",
        upstream_id=chapter.chapter_id,
        downstream_id=scene_one.scene_id,
        dependency_kind="precedes",
        reason="The chapter needs to set up the corridor route.",
    )
    dependency_two = service.add_planning_dependency(
        project_id,
        dependency_id="dependency-2",
        upstream_id=scene_one.scene_id,
        downstream_id=scene_two.scene_id,
        dependency_kind="precedes",
        reason="The corridor scene must come before the reveal.",
    )

    packet = service.build_chapter_packet(project_id, chapter.chapter_id)
    packet_again = PlanningService(repository).build_chapter_packet(project_id, chapter.chapter_id)

    assert packet.packet_id == f"{project_id}:{chapter.chapter_id}:packet"
    assert packet == packet_again
    stored_packet = repository.get_chapter_packet(packet.packet_id)
    assert stored_packet.packet_id == packet.packet_id
    assert stored_packet.project_id == packet.project_id
    assert stored_packet.chapter_id == packet.chapter_id
    assert stored_packet.included_reference_ids == packet.included_reference_ids
    assert stored_packet.constraints == packet.constraints
    assert stored_packet.scene_goals == packet.scene_goals
    assert stored_packet.status == packet.status
    assert repository.list_chapter_packets(project_id) == [stored_packet]
    assert packet.included_reference_ids == [
        chapter.chapter_id,
        sequence.sequence_id,
        scene_one.scene_id,
        scene_two.scene_id,
        dependency_one.dependency_id,
        dependency_two.dependency_id,
    ]
    assert packet.constraints == [
        "Chapter objective: Reach the archive.",
        "Chapter conflict: The market keeps shifting.",
        "Chapter stakes: The route may be lost.",
        "The archive must remain sealed until sunset.",
        "The corridor opens only once.",
        "The clue must follow the corridor scene.",
        "Dependency dependency-1: The chapter needs to set up the corridor route.",
        "Dependency dependency-2: The corridor scene must come before the reveal.",
    ]
    assert packet.scene_goals == ["Get inside the market corridor.", "Reveal the archive clue."]
    assert packet.status == "draft"
