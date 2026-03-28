from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import ArcCandidate, ArcStageMap
from app.services.story_knowledge import StoryKnowledgeService


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


def _service(tmp_path: Path) -> tuple[StoryKnowledgeService, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    return StoryKnowledgeService(repository), repository


def _character_kwargs(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "character_id": "mara-vale",
        "display_name": "Mara Vale",
        "role_in_story": "protagonist",
        "archetype": "reluctant cartographer",
        "external_goal": "Map the shifting city before dawn.",
        "internal_need": "Trust the people she maps.",
        "misbelief_or_wound": "Control keeps everyone safe.",
        "core_fear": "Losing the city and everyone in it.",
        "primary_strength": "Pattern recognition",
        "fatal_flaw_or_limitation": "Overplans every uncertain step.",
        "contradictions": ["Careful planner", "Impulse to explore"],
        "backstory_summary": "Raised by archive keepers who taught her to preserve every map.",
        "voice_notes": "Precise, observant, and quietly vulnerable.",
        "secrets": ["She once altered a map to hide a friend."],
        "values": ["Truth", "Loyalty"],
        "taboos": ["Erase history"],
        "change_axis": "From control to trust",
        "arc_stage_notes": ["Start with isolation", "Move toward alliance"],
        "continuity_facts": ["Can read hidden street patterns"],
        "writer_notes": "Keep her skepticism grounded.",
    }
    payload.update(overrides)
    return payload


def test_story_knowledge_service_stores_source_linked_world_facts_and_relationship_edges(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "story-knowledge-1"
    _seed_project(repository.db_path, project_id)

    service.upsert_character_profile(project_id, **_character_kwargs())
    service.upsert_character_profile(
        project_id,
        **_character_kwargs(
            character_id="orin-vale",
            display_name="Orin Vale",
            role_in_story="ally",
            archetype="skeptical scholar",
            external_goal="Keep the archive intact.",
            internal_need="Accept that change is inevitable.",
            misbelief_or_wound="If he records everything, he can preserve it.",
            core_fear="Forgetting what matters.",
            primary_strength="Memory",
            fatal_flaw_or_limitation="Hesitates when facts conflict.",
            contradictions=["Cautious keeper", "Secretly curious"],
            backstory_summary="A chronicler who believes records can outlast ruin.",
            voice_notes="Measured, dry, and precise.",
            secrets=["He hid a torn page from the archive."],
            values=["Truth", "Preservation"],
            taboos=["Destroy records"],
            change_axis="From caution to courage",
            arc_stage_notes=["Remain support", "Challenge assumptions"],
            continuity_facts=["Knows the archive vault layout"],
        ),
    )

    world_entry = service.upsert_world_bible_entry(
        project_id,
        entry_type="location",
        title="Shifting City",
        summary="A city that rearranges itself every dusk.",
        canonical_facts=["The gates move at sunset.", "No street stays fixed overnight."],
        related_character_ids=["mara-vale", "orin-vale"],
        source_artifacts=["manifest", "foundation-revision-2"],
        continuity_warnings=["Do not treat the street grid as stable."],
    )
    edge = service.upsert_relationship_edge(
        project_id,
        source_character_id="mara-vale",
        target_character_id="orin-vale",
        relation_kind="ally",
        summary="They rely on each other to preserve the city record.",
        tension="He doubts her improvisation.",
        notes="Keep the partnership cautious but warm.",
    )

    assert world_entry.source_artifacts == ["manifest", "foundation-revision-2"]
    assert world_entry.canonical_facts == ["The gates move at sunset.", "No street stays fixed overnight."]
    assert world_entry.related_character_ids == ["mara-vale", "orin-vale"]
    assert service.get_world_bible_entry(project_id, entry_type="location", title="Shifting City").entry_id == world_entry.entry_id
    assert repository.get_world_bible_entry(project_id, entry_type="location", title="Shifting City").related_character_ids == ["mara-vale", "orin-vale"]

    mara = service.get_character_profile(project_id, "mara-vale")
    orin = service.get_character_profile(project_id, "orin-vale")

    assert [relationship.edge_id for relationship in mara.relationship_edges] == [edge.edge_id]
    assert [relationship.edge_id for relationship in orin.relationship_edges] == [edge.edge_id]
    assert mara.relationship_edges[0].summary == "They rely on each other to preserve the city record."
    assert repository.get_character_profile("mara-vale").relationship_map == [edge.edge_id]
    assert repository.get_character_profile("orin-vale").relationship_map == [edge.edge_id]


def test_compare_arc_candidates_ranks_options_deterministically(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "story-knowledge-2"
    _seed_project(repository.db_path, project_id)

    later = ArcCandidate(
        arc_id="arc-c",
        project_id=project_id,
        name="Corruption",
        summary="A slow fall into compromise.",
        stage_map_notes=["Escalate pressure"],
        fit_notes=["Strong moral descent", "Fits the tone"],
        tags=["tragedy"],
    )
    earlier = ArcCandidate(
        arc_id="arc-a",
        project_id=project_id,
        name="Quest",
        summary="A clear path toward recovery.",
        stage_map_notes=["Opening", "Midpoint", "Endgame"],
        fit_notes=["Broad audience fit"],
        tags=["adventure", "ensemble"],
    )

    comparisons = service.compare_arc_candidates(project_id, candidates=[later, earlier])

    assert [comparison.candidate.arc_id for comparison in comparisons] == ["arc-a", "arc-c"]
    assert comparisons[0].rank == 1
    assert comparisons[0].score == (3, 1, 2, -5)
    assert "Quest" in comparisons[0].notes[0]
    assert {record.arc_id for record in repository.list_arc_candidates(project_id)} == {"arc-a", "arc-c"}
    comparison_records = repository.list_arc_comparisons(project_id)
    assert len(comparison_records) == 1
    assert re.fullmatch(r"story-knowledge-2:comparison:[0-9a-f]{32}", comparison_records[0].comparison_id)
    assert service.list_arc_comparisons(project_id) == (comparisons,)


def test_select_arc_candidate_remains_advisory_and_inspectable(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "story-knowledge-3"
    _seed_project(repository.db_path, project_id)

    candidate_a = ArcCandidate(
        arc_id="arc-heroic",
        project_id=project_id,
        name="Heroic Quest",
        summary="A path of escalating trials.",
        stage_map_notes=["Trial", "Allies"],
        fit_notes=["Clear escalation"],
        tags=["quest"],
    )
    candidate_b = ArcCandidate(
        arc_id="arc-braided",
        project_id=project_id,
        name="Braided Arc",
        summary="An ensemble route with multiple threads.",
        stage_map_notes=["Threading"],
        fit_notes=["Complex structure", "Many viewpoints"],
        tags=["ensemble", "multi-thread"],
    )

    service.compare_arc_candidates(project_id, candidates=[candidate_a, candidate_b])
    selection = service.select_arc_candidate(
        project_id,
        selected_arc="arc-braided",
        rejected_arc_ids=["arc-heroic"],
    )

    assert selection.selected_arc.arc_id == "arc-braided"
    assert selection.rejected_arc_ids == ["arc-heroic"]
    assert selection.comparison_notes[0].startswith("Braided Arc:")
    assert len(selection.comparison_record_ids) == 1
    assert re.fullmatch(r"story-knowledge-3:comparison:[0-9a-f]{32}", selection.comparison_record_ids[0])
    comparison_records = repository.list_arc_comparisons(project_id)
    assert len(comparison_records) == 1
    assert selection.comparison_record_ids == [comparison_records[0].comparison_id]
    decision_nodes = repository.list_story_decision_nodes(project_id)
    assert len(decision_nodes) == 1
    assert decision_nodes[0].node_id == f"{selection.selection_id}:decision"
    assert decision_nodes[0].change_type == "ARC_SELECTION"
    assert decision_nodes[0].subject_type == "ARC_SELECTION"
    assert decision_nodes[0].subject_id == selection.selection_id
    assert service.list_arc_selections(project_id) == (selection,)


def test_update_arc_stage_map_updates_latest_selection_view(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "story-knowledge-4"
    _seed_project(repository.db_path, project_id)

    candidate = ArcCandidate(
        arc_id="arc-mystery",
        project_id=project_id,
        name="Mystery Arc",
        summary="A discovery-led structure.",
        stage_map_notes=["Reveal", "Reframe"],
        fit_notes=["Fits the premise"],
        tags=["mystery"],
    )

    service.compare_arc_candidates(project_id, candidates=[candidate, candidate.model_copy(update={"arc_id": "arc-alternate", "name": "Alternate"})])
    selection = service.select_arc_candidate(project_id, selected_arc="arc-mystery")
    stage_map = service.update_arc_stage_map(
        project_id,
        arc_id="arc-mystery",
        stage_kinds=["brainstorm", "character", "world_bible", "arc_selection", "planning"],
        notes="Use a slow-burn reveal structure.",
    )

    latest_selection = service.list_arc_selections(project_id)[-1]
    persisted_selection = repository.get_arc_selection(project_id, selection_id=latest_selection.selection_id)

    assert stage_map.arc_stage_map_id == f"{project_id}:arc-mystery:stage-map"
    assert stage_map.stage_kinds == ["brainstorm", "character", "world_bible", "arc_selection", "planning"]
    assert latest_selection.stage_map == stage_map
    assert len(latest_selection.comparison_record_ids) == 1
    assert re.fullmatch(r"story-knowledge-4:comparison:[0-9a-f]{32}", latest_selection.comparison_record_ids[0])
    assert selection.selected_arc.arc_id == "arc-mystery"
    assert service.get_arc_stage_map(project_id, arc_id="arc-mystery") == stage_map
    assert persisted_selection.stage_map == repository.get_arc_stage_map(project_id, arc_id="arc-mystery")
    decision_nodes = repository.list_story_decision_nodes(project_id)
    assert [node.change_type for node in decision_nodes] == ["ARC_SELECTION", "PLANNING_PIVOT"]
    assert decision_nodes[-1].subject_type == "ARC_STAGE_MAP"
    assert decision_nodes[-1].subject_id == f"{project_id}:arc-mystery:stage-map"


def test_list_character_profiles_batches_relationship_edge_reads(tmp_path: Path) -> None:
    service, repository = _service(tmp_path)
    project_id = "story-knowledge-5"
    _seed_project(repository.db_path, project_id)

    service.upsert_character_profile(project_id, **_character_kwargs())
    service.upsert_character_profile(
        project_id,
        **_character_kwargs(
            character_id="orin-vale",
            display_name="Orin Vale",
            role_in_story="ally",
            archetype="skeptical scholar",
            external_goal="Keep the archive intact.",
            internal_need="Accept that change is inevitable.",
            misbelief_or_wound="If he records everything, he can preserve it.",
            core_fear="Forgetting what matters.",
            primary_strength="Memory",
            fatal_flaw_or_limitation="Hesitates when facts conflict.",
            contradictions=["Cautious keeper", "Secretly curious"],
            backstory_summary="A chronicler who believes records can outlast ruin.",
            voice_notes="Measured, dry, and precise.",
            secrets=["He hid a torn page from the archive."],
            values=["Truth", "Preservation"],
            taboos=["Destroy records"],
            change_axis="From caution to courage",
            arc_stage_notes=["Remain support", "Challenge assumptions"],
            continuity_facts=["Knows the archive vault layout"],
        ),
    )
    edge = service.upsert_relationship_edge(
        project_id,
        source_character_id="mara-vale",
        target_character_id="orin-vale",
        relation_kind="ally",
        summary="They rely on each other to preserve the city record.",
    )

    list_relationship_edges_calls = 0
    list_relationship_edges_for_character_calls = 0

    original_list_relationship_edges = repository.list_relationship_edges
    original_list_relationship_edges_for_character = repository.list_relationship_edges_for_character

    def counted_list_relationship_edges(project_id_arg: str):
        nonlocal list_relationship_edges_calls
        list_relationship_edges_calls += 1
        return original_list_relationship_edges(project_id_arg)

    def counted_list_relationship_edges_for_character(project_id_arg: str, character_id_arg: str):
        nonlocal list_relationship_edges_for_character_calls
        list_relationship_edges_for_character_calls += 1
        return original_list_relationship_edges_for_character(project_id_arg, character_id_arg)

    repository.list_relationship_edges = counted_list_relationship_edges
    repository.list_relationship_edges_for_character = counted_list_relationship_edges_for_character
    try:
        profiles = service.list_character_profiles(project_id)
    finally:
        repository.list_relationship_edges = original_list_relationship_edges
        repository.list_relationship_edges_for_character = original_list_relationship_edges_for_character

    assert list_relationship_edges_calls == 1
    assert list_relationship_edges_for_character_calls == 0
    assert [profile.character_id for profile in profiles] == ["mara-vale", "orin-vale"]
    assert [relationship.edge_id for relationship in profiles[0].relationship_edges] == [edge.edge_id]
    assert [relationship.edge_id for relationship in profiles[1].relationship_edges] == [edge.edge_id]
