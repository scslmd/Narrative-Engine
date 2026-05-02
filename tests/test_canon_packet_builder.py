from __future__ import annotations

import json
from hashlib import sha256

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonGenerationRequest,
    CanonPolicy,
    CanonScope,
    ContinuityStrictness,
    DestinationKind,
    GenerationDestination,
    GenerationMode,
)
from app.schemas.projects import ProjectCreateRequest
from app.services.canon_packet_builder import CanonPacketBuilder
from app.services.projects import ProjectService


def _make_request(
    *,
    project_id: str = "source-project",
    character_ids: list[str] | None = None,
    world_bible_refs: list[dict] | None = None,
    arc_ids: list[str] | None = None,
    continuity_thread_ids: list[str] | None = None,
    scope_mode: str = "selected",
    canon_policy: CanonPolicy | None = None,
) -> CanonGenerationRequest:
    kwargs: dict = {"source_project_id": project_id, "scope_mode": scope_mode}
    if character_ids is not None:
        kwargs["character_ids"] = character_ids
    if world_bible_refs is not None:
        kwargs["world_bible_refs"] = world_bible_refs
    if arc_ids is not None:
        kwargs["arc_ids"] = arc_ids
    if continuity_thread_ids is not None:
        kwargs["continuity_thread_ids"] = continuity_thread_ids

    return CanonGenerationRequest(
        source_project_id=project_id,
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        destination=GenerationDestination(
            destination_kind=DestinationKind.SAME_PROJECT,
            target_project_id=project_id,
        ),
        canon_scope=CanonScope(**kwargs),
        generation_brief="Test brief.",
        target_chapter_count=3,
        canon_policy=canon_policy or CanonPolicy(),
    )


def _setup_project(tmp_path) -> tuple[ProjectService, StoryDevelopmentRepository]:
    project_service = ProjectService(tmp_path)
    repo = StoryDevelopmentRepository(tmp_path / "data" / "state" / "narrative_ops.db")
    project_service.create_project(
        ProjectCreateRequest(
            project_id="source-project",
            project_name="Source Project",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    return project_service, repo


def test_canon_packet_builder_creates_deterministic_packet(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="A kingdom in decline.",
        logline="A disgraced knight returns home.",
    )
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
        continuity_facts=["Aria is heir to the north keep."],
    )
    repo.upsert_world_bible_entry(
        project_id="source-project",
        entry_type="location",
        title="North Keep",
        summary="Ancient border fortress.",
        canonical_facts=["Built before the first war."],
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(
        character_ids=["char-1"],
        world_bible_refs=[{"entry_type": "location", "title": "North Keep"}],
    )
    first = builder.build_packet(request, target_project_id="source-project")
    second = builder.build_packet(request, target_project_id="source-project")
    assert first.packet_id == second.packet_id
    assert first.characters[0].character_id == "char-1"
    assert first.world_bible[0].title == "North Keep"


def test_empty_project_foundation_returns_empty_dict(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.foundation_snapshot == {}


def test_foundation_snapshot_includes_all_10_fields(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="A kingdom in decline.",
        logline="A disgraced knight returns home.",
        thematic_spine="Redemption through sacrifice.",
        emotional_promise="Hope after despair.",
        tone_direction="Grim but hopeful.",
        target_audience="Young adult",
        narrative_constraints=["No magic after act 2"],
        complexity_level="high",
        success_definition="Reader finishes in one sitting.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    fs = packet.foundation_snapshot
    assert fs["premise"] == "A kingdom in decline."
    assert fs["logline"] == "A disgraced knight returns home."
    assert fs["thematic_spine"] == "Redemption through sacrifice."
    assert fs["emotional_promise"] == "Hope after despair."
    assert fs["tone_direction"] == "Grim but hopeful."
    assert fs["target_audience"] == "Young adult"
    assert fs["narrative_constraints"] == ["No magic after act 2"]
    assert fs["complexity_level"] == "high"
    assert fs["success_definition"] == "Reader finishes in one sitting."
    assert fs["project_id"] == "source-project"


def test_multiple_foundation_revisions_selects_latest(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="First premise.",
        logline="First logline.",
    )
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="Second premise.",
        logline="Second logline.",
    )
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="Third premise.",
        logline="Third logline.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.foundation_snapshot["premise"] == "Third premise."
    assert packet.foundation_snapshot["logline"] == "Third logline."


def test_full_project_scope_includes_all_characters(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-2",
        project_id="source-project",
        display_name="Boris",
        role_in_story="antagonist",
    )
    repo.upsert_character_profile(
        character_id="char-3",
        project_id="source-project",
        display_name="Celia",
        role_in_story="mentor",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    ids = [c.character_id for c in packet.characters]
    assert "char-1" in ids
    assert "char-2" in ids
    assert "char-3" in ids


def test_character_scope_filtering_only_selected(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-2",
        project_id="source-project",
        display_name="Boris",
        role_in_story="antagonist",
    )
    repo.upsert_character_profile(
        character_id="char-3",
        project_id="source-project",
        display_name="Celia",
        role_in_story="mentor",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(character_ids=["char-1", "char-3"])
    packet = builder.build_packet(request, target_project_id="source-project")
    ids = [c.character_id for c in packet.characters]
    assert ids == ["char-1", "char-3"]
    assert "char-2" not in ids


def test_character_sorting_alphabetical_case_insensitive(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_character_profile(
        character_id="char-c",
        project_id="source-project",
        display_name="Zara",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-a",
        project_id="source-project",
        display_name="alice",
        role_in_story="mentor",
    )
    repo.upsert_character_profile(
        character_id="char-b",
        project_id="source-project",
        display_name="Bob",
        role_in_story="antagonist",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    names = [c.display_name for c in packet.characters]
    assert names == ["alice", "Bob", "Zara"]


def test_relationships_filtered_to_selected_pairs(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_character_profile(
        character_id="char-a",
        project_id="source-project",
        display_name="Alice",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-b",
        project_id="source-project",
        display_name="Bob",
        role_in_story="antagonist",
    )
    repo.upsert_character_profile(
        character_id="char-c",
        project_id="source-project",
        display_name="Charlie",
        role_in_story="mentor",
    )
    repo.upsert_relationship_edge(
        project_id="source-project",
        source_character_id="char-a",
        target_character_id="char-b",
        relation_kind="rivalry",
        summary="Childhood rivals.",
    )
    repo.upsert_relationship_edge(
        project_id="source-project",
        source_character_id="char-a",
        target_character_id="char-c",
        relation_kind="mentorship",
        summary="Trained by Charlie.",
    )
    repo.upsert_relationship_edge(
        project_id="source-project",
        source_character_id="char-b",
        target_character_id="char-c",
        relation_kind="alliance",
        summary="Secret allies.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(character_ids=["char-a", "char-b"])
    packet = builder.build_packet(request, target_project_id="source-project")
    edges = [(r.source_character_id, r.target_character_id) for r in packet.relationships]
    assert ("char-a", "char-b") in edges
    assert ("char-a", "char-c") not in edges
    assert ("char-b", "char-c") not in edges


def test_relationships_empty_when_none_exist(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(character_ids=["char-1"])
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.relationships == []


def test_arc_snapshots_filtered_to_selected(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_arc_candidate(
        project_id="source-project",
        arc_id="arc-1",
        name="Hero's Journey",
        summary="Classic hero arc.",
    )
    repo.upsert_arc_candidate(
        project_id="source-project",
        arc_id="arc-2",
        name="Villain's Fall",
        summary="Antagonist downfall.",
    )
    repo.upsert_arc_candidate(
        project_id="source-project",
        arc_id="arc-3",
        name="Redemption",
        summary="Character finds redemption.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(arc_ids=["arc-1", "arc-3"])
    packet = builder.build_packet(request, target_project_id="source-project")
    arc_ids = [a.arc_id for a in packet.arcs]
    assert arc_ids == ["arc-1", "arc-3"]
    assert "arc-2" not in arc_ids


def test_arcs_empty_when_none_exist(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.arcs == []


def test_continuity_snapshots_returns_threads_and_findings(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_continuity_thread(
        thread_id="thread-1",
        project_id="source-project",
        title="Magic System Consistency",
        summary="Track magic rules across chapters.",
    )
    repo.upsert_continuity_thread(
        thread_id="thread-2",
        project_id="source-project",
        title="Timeline Alignment",
        summary="Ensure timeline is consistent.",
    )
    repo.upsert_continuity_finding(
        project_id="source-project",
        finding_key="finding-1",
        contradictions=["Chapter 3 contradicts chapter 1 on travel time."],
        unresolved_questions=["Is the prophecy real?"],
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    thread_ids = [t.thread_id for t in packet.continuity_threads]
    assert "thread-1" in thread_ids
    assert "thread-2" in thread_ids
    assert len(packet.continuity_findings) == 1
    assert packet.continuity_findings[0].finding_key == "finding-1"


def test_continuity_filtering_by_thread_ids(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_continuity_thread(
        thread_id="thread-a",
        project_id="source-project",
        title="Alpha Thread",
        summary="First thread.",
    )
    repo.upsert_continuity_thread(
        thread_id="thread-b",
        project_id="source-project",
        title="Beta Thread",
        summary="Second thread.",
    )
    repo.upsert_continuity_thread(
        thread_id="thread-c",
        project_id="source-project",
        title="Gamma Thread",
        summary="Third thread.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(continuity_thread_ids=["thread-a", "thread-c"])
    packet = builder.build_packet(request, target_project_id="source-project")
    thread_ids = [t.thread_id for t in packet.continuity_threads]
    assert thread_ids == ["thread-a", "thread-c"]
    assert "thread-b" not in thread_ids


def _insert_draft_brief(repo, *, brief_id: str, project_id: str) -> None:
    repo.upsert_draft_brief(
        brief_id=brief_id,
        project_id=project_id,
        chapter_id="ch-1",
        objective="Test objective.",
        emotional_turn="Test turn.",
    )


def test_drafting_context_packets_included(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    _insert_draft_brief(repo, brief_id="brief-1", project_id="source-project")
    _insert_draft_brief(repo, brief_id="brief-2", project_id="source-project")
    repo.upsert_drafting_context_packet(
        packet_id="pkt-1",
        project_id="source-project",
        brief_id="brief-1",
        character_anchors=["char-1"],
        world_constraints=["No magic in chapter 1"],
        prior_summaries=["Chapter 1: Introduction."],
    )
    repo.upsert_drafting_context_packet(
        packet_id="pkt-2",
        project_id="source-project",
        brief_id="brief-2",
        character_anchors=["char-2"],
        world_constraints=["Desert setting"],
        prior_summaries=["Chapter 2: Journey begins."],
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    pkt_ids = [p.packet_id for p in packet.drafting_context_packets]
    assert "pkt-1" in pkt_ids
    assert "pkt-2" in pkt_ids


def test_source_hashes_contains_sha256_for_all_packet_parts(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="Test premise.",
        logline="Test logline.",
    )
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(character_ids=["char-1"])
    packet = builder.build_packet(request, target_project_id="source-project")
    expected_keys = {
        "foundation",
        "characters",
        "relationships",
        "world_bible",
        "arcs",
        "continuity_threads",
        "continuity_findings",
        "drafting_packets",
        "mythos_entries",
        "pattern_entries",
        "canon_annotations",
    }
    assert set(packet.source_hashes.keys()) == expected_keys
    for key, hash_val in packet.source_hashes.items():
        assert len(hash_val) == 64


def test_canon_policy_from_request_included_in_packet(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    policy = CanonPolicy(
        locked_character_fields=["display_name", "backstory"],
        allowed_character_changes=["role_in_story"],
        forbidden_contradictions=["No resurrections"],
        continuity_strictness=ContinuityStrictness.BLOCK,
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project", canon_policy=policy)
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.canon_policy.locked_character_fields == ["display_name", "backstory"]
    assert packet.canon_policy.allowed_character_changes == ["role_in_story"]
    assert packet.canon_policy.forbidden_contradictions == ["No resurrections"]
    assert packet.canon_policy.continuity_strictness == ContinuityStrictness.BLOCK


def test_budget_fit_no_truncation_when_payload_fits(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="Short premise.",
        logline="Short logline.",
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert packet.prompt_budget_summary.fit_to_budget is True
    assert packet.prompt_budget_summary.truncated_fields == []
    assert packet.prompt_budget_summary.target_max_chars == 120_000
    assert packet.prompt_budget_summary.estimated_prompt_chars > 0


def test_budget_truncation_drafting_context_packets_first(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    big_text = "x" * 50_000
    _insert_draft_brief(repo, brief_id="brief-1", project_id="source-project")
    repo.upsert_drafting_context_packet(
        packet_id="pkt-1",
        project_id="source-project",
        brief_id="brief-1",
        character_anchors=[big_text],
        world_constraints=[big_text],
        prior_summaries=[big_text],
    )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert "drafting_context_packets" in packet.prompt_budget_summary.truncated_fields


def test_budget_truncation_order_relationships_second_continuity_third(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    big_text = "x" * 40_000
    _insert_draft_brief(repo, brief_id="brief-1", project_id="source-project")
    _insert_draft_brief(repo, brief_id="brief-2", project_id="source-project")
    repo.upsert_drafting_context_packet(
        packet_id="pkt-1",
        project_id="source-project",
        brief_id="brief-1",
        character_anchors=[big_text],
        world_constraints=[big_text],
        prior_summaries=[big_text],
    )
    repo.upsert_drafting_context_packet(
        packet_id="pkt-2",
        project_id="source-project",
        brief_id="brief-2",
        character_anchors=[big_text],
        world_constraints=[big_text],
        prior_summaries=[big_text],
    )
    repo.upsert_character_profile(
        character_id="char-a",
        project_id="source-project",
        display_name="Alice",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-b",
        project_id="source-project",
        display_name="Bob",
        role_in_story="antagonist",
    )
    med_text = "y" * 4_000
    for i in range(15):
        repo.upsert_relationship_edge(
            project_id="source-project",
            source_character_id="char-a",
            target_character_id="char-b",
            relation_kind=f"kind-{i}",
            summary=med_text,
            edge_id=f"edge-{i}",
        )
    for i in range(15):
        repo.upsert_continuity_finding(
            project_id="source-project",
            finding_key=f"finding-{i}",
            contradictions=[med_text],
            unresolved_questions=[med_text],
        )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    truncated = packet.prompt_budget_summary.truncated_fields
    assert "drafting_context_packets" in truncated
    if "relationships" in truncated and "continuity_findings" in truncated:
        assert truncated.index("relationships") < truncated.index("continuity_findings")


def test_budget_truncation_updates_fields_and_fit_false(tmp_path) -> None:
    project_service, repo = _setup_project(tmp_path)
    big_text = "x" * 50_000
    _insert_draft_brief(repo, brief_id="brief-1", project_id="source-project")
    repo.upsert_drafting_context_packet(
        packet_id="pkt-1",
        project_id="source-project",
        brief_id="brief-1",
        character_anchors=[big_text],
        world_constraints=[big_text],
        prior_summaries=[big_text],
    )
    repo.upsert_character_profile(
        character_id="char-a",
        project_id="source-project",
        display_name="Alice",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-b",
        project_id="source-project",
        display_name="Bob",
        role_in_story="antagonist",
    )
    med_text = "y" * 4_000
    for i in range(15):
        repo.upsert_relationship_edge(
            project_id="source-project",
            source_character_id="char-a",
            target_character_id="char-b",
            relation_kind=f"kind-{i}",
            summary=med_text,
            edge_id=f"edge-{i}",
        )
    huge_summary = "z" * 9_000
    for i in range(20):
        repo.upsert_continuity_thread(
            thread_id=f"thread-{i}",
            project_id="source-project",
            title=f"Thread {i}",
            summary=huge_summary,
        )
    builder = CanonPacketBuilder(repository=repo, project_service=project_service)
    request = _make_request(scope_mode="full_project")
    packet = builder.build_packet(request, target_project_id="source-project")
    assert len(packet.prompt_budget_summary.truncated_fields) > 0
    assert packet.prompt_budget_summary.fit_to_budget is False
