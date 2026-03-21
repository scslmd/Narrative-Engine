from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.schemas import (
    StoryArtifactLifecycleState,
    StoryObjectType,
    StoryBranchState,
    StoryFlowStageConfigurationState,
    StoryFlowStageProgressState,
    StorySuggestionLifecycleState,
)
from app.persistence.sqlite import OPERATIONS_DB_VERSION, connect, ensure_operations_db
from app.persistence.story_development import ArcComparisonCandidateRecord, StoryDevelopmentRepository


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
                "Story Development Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def test_story_development_schema_creation_includes_canonical_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        }

    assert version == OPERATIONS_DB_VERSION
    assert {"jobs", "checker_runs", "step_records", "artifact_lineage"}.issubset(tables)
    assert {
        "story_flow_definitions",
        "story_flow_stages",
        "brainstorm_items",
        "foundation_profiles",
        "foundation_revisions",
        "character_profiles",
        "relationship_edges",
        "world_bible_entries",
        "arc_candidates",
        "arc_comparisons",
        "arc_stage_maps",
        "arc_selections",
        "arc_selection_comparisons",
        "beat_plans",
        "sequence_plans",
        "chapter_plans",
        "scene_plans",
        "chapter_packets",
        "planning_dependencies",
        "story_decision_nodes",
        "checker_findings",
        "review_decisions",
        "inspect_run_links",
        "branch_state_refs",
        "draft_artifacts",
        "manuscript_documents",
        "revision_suggestions",
    }.issubset(tables)


def test_story_development_repository_round_trips_representative_objects(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-roundtrip"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    flow = repo.ensure_flow_definition(
        project_id=project_id,
        flow_name="Story Development Flow",
        flow_notes="Editable flow scaffold.",
        created_at=STAMP,
        updated_at=STAMP,
    )
    assert flow.flow_name == "Story Development Flow"

    primary_stage = repo.add_flow_stage(
        project_id=project_id,
        stage_key="brainstorm",
        stage_kind="brainstorm",
        is_custom=False,
        display_name="Brainstorm",
        position=0,
        stage_configuration_state=StoryFlowStageConfigurationState.ENABLED,
        stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
        created_at=STAMP,
        updated_at=STAMP,
    )
    custom_stage = repo.add_flow_stage(
        project_id=project_id,
        stage_key="custom_reflection",
        stage_kind="reflection_pass",
        is_custom=True,
        display_name="Reflection",
        position=1,
        description="Optional return point.",
        depends_on=[primary_stage.stage_key],
        stage_configuration_state=StoryFlowStageConfigurationState.OPTIONAL,
        stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
        custom_prompt_guidance="Revisit if needed.",
        created_at=STAMP,
        updated_at=STAMP,
    )

    renamed = repo.rename_flow_stage(
        project_id,
        stage_id=primary_stage.stage_id,
        display_name="Idea Storm",
        updated_at=STAMP,
    )
    redefined = repo.redefine_flow_stage(
        project_id,
        stage_id=primary_stage.stage_id,
        stage_kind="brainstorm",
        description="Generate and shape starting ideas.",
        writer_notes="Keep this stage lightweight.",
        custom_prompt_guidance="Offer a few alternate directions.",
        updated_at=STAMP,
    )
    reordered = repo.reorder_flow_stages(
        project_id,
        ordered_stage_ids=[custom_stage.stage_id, primary_stage.stage_id],
        updated_at=STAMP,
    )
    staged = repo.set_flow_stage_state(
        project_id,
        stage_id=primary_stage.stage_id,
        stage_configuration_state=StoryFlowStageConfigurationState.DISABLED,
        stage_progress_state=StoryFlowStageProgressState.IN_PROGRESS,
        updated_at=STAMP,
    )

    assert renamed.display_name == "Idea Storm"
    assert redefined.description == "Generate and shape starting ideas."
    assert [stage.stage_id for stage in reordered] == [custom_stage.stage_id, primary_stage.stage_id]
    assert staged.stage_progress_state == StoryFlowStageProgressState.IN_PROGRESS
    assert staged.stage_configuration_state == StoryFlowStageConfigurationState.DISABLED
    assert repo.delete_custom_flow_stage(project_id, stage_id=custom_stage.stage_id) is True
    assert [stage.stage_key for stage in repo.list_flow_stages(project_id)] == ["brainstorm"]
    assert custom_stage.is_custom is True
    assert primary_stage.is_custom is False

    brainstorm_item = repo.create_brainstorm_item(
        project_id=project_id,
        content="A city that rearranges itself each dusk.",
        item_state="open",
        cluster_key="setting",
        tags=["setting", "high-concept"],
        source_artifact_refs=["manifest"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    updated_brainstorm = repo.update_brainstorm_item_state(
        brainstorm_item.item_id,
        item_state="parked",
        cluster_key="world",
        updated_at=STAMP,
    )
    assert updated_brainstorm.item_state == "parked"
    assert updated_brainstorm.cluster_key == "world"
    assert repo.list_brainstorm_items(project_id)[0].content == brainstorm_item.content

    first_revision = repo.upsert_foundation_profile(
        project_id=project_id,
        premise="A cartographer maps a city that changes every dusk.",
        logline="A cartographer must chart a shifting city before it erases the people inside it.",
        thematic_spine="Memory versus control",
        narrative_constraints=["No time travel"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_revision = repo.upsert_foundation_profile(
        project_id=project_id,
        premise="A cartographer maps a city that changes every dusk.",
        logline="The cartographer discovers the city changes to protect a buried truth.",
        thematic_spine="Memory versus control",
        narrative_constraints=["No time travel", "Third-person limited"],
        complexity_level="medium",
        created_at=STAMP,
        updated_at=STAMP,
    )
    foundation_profile = repo.get_foundation_profile(project_id)
    foundation_revisions = repo.list_foundation_revisions(project_id)

    assert first_revision.revision_number == 1
    assert second_revision.revision_number == 2
    assert foundation_profile.current_revision_id == second_revision.revision_id
    assert [revision.revision_number for revision in foundation_revisions] == [1, 2]
    assert foundation_revisions[-1].logline.endswith("buried truth.")

    character = repo.upsert_character_profile(
        project_id=project_id,
        character_id="cartographer",
        display_name="Mara Vale",
        role_in_story="protagonist",
        external_goal="Map the city before dawn.",
        internal_need="Trust the people she maps.",
        contradictions=["Careful planner", "Impulsive explorer"],
        continuity_facts=["Can read hidden street patterns"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    companion = repo.upsert_character_profile(
        project_id=project_id,
        character_id="ally",
        display_name="Orin Vale",
        role_in_story="ally",
        archetype="scholar",
        external_goal="Preserve the city archive.",
        internal_need="Trust change.",
        contradictions=["Careful", "Curious"],
        backstory_summary="A chronicler of the shifting city.",
        voice_notes="Measured and precise.",
        change_axis="From caution to courage",
        created_at=STAMP,
        updated_at=STAMP,
    )
    edge = repo.upsert_relationship_edge(
        project_id=project_id,
        source_character_id=character.character_id,
        target_character_id=companion.character_id,
        relation_kind="ally",
        summary="They rely on each other to preserve the city record.",
        tension="He doubts her improvisation.",
        notes="Keep the partnership cautious but warm.",
        edge_id="mara-orin-ally",
        created_at=STAMP,
        updated_at=STAMP,
    )
    world_entry = repo.upsert_world_bible_entry(
        project_id=project_id,
        entry_type="location",
        title="Shifting City",
        summary="A city that rearranges itself every dusk.",
        canonical_facts=["The gates move at sunset."],
        related_character_ids=["cartographer", "ally"],
        source_artifacts=["manifest", "foundation"],
        continuity_warnings=["Do not treat street layout as stable."],
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert repo.get_character_profile("cartographer").display_name == "Mara Vale"
    assert repo.list_character_profiles(project_id)[0].character_id == "cartographer"
    assert repo.get_character_profile("cartographer").relationship_map == [edge.edge_id]
    assert repo.get_character_profile("ally").relationship_map == [edge.edge_id]
    assert repo.get_relationship_edge(edge.edge_id).summary == edge.summary
    assert [record.edge_id for record in repo.list_relationship_edges(project_id)] == [edge.edge_id]
    assert repo.get_world_bible_entry(project_id, entry_type="location", title="Shifting City").entry_id == world_entry.entry_id
    assert repo.get_world_bible_entry(project_id, entry_type="location", title="Shifting City").related_character_ids == ["cartographer", "ally"]
    assert repo.list_world_bible_entries(project_id)[0].title == "Shifting City"


def test_story_development_repository_round_trips_arc_selection_and_stage_map_state(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-arcs"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    candidate_primary = repo.upsert_arc_candidate(
        project_id=project_id,
        arc_id="arc-primary",
        name="Primary Quest",
        summary="A clear route through escalating trials.",
        stage_map_notes=["Opening", "Midpoint", "Endgame"],
        fit_notes=["Clean escalation", "Strong central goal"],
        tags=["quest", "ensemble"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    candidate_secondary = repo.upsert_arc_candidate(
        project_id=project_id,
        arc_id="arc-secondary",
        name="Secondary Mystery",
        summary="A discovery path that leans into suspense.",
        stage_map_notes=["Reveal", "Reframe"],
        fit_notes=["Fits a slow-burn tone"],
        tags=["mystery"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    stage_map = repo.upsert_arc_stage_map(
        project_id=project_id,
        arc_id=candidate_primary.arc_id,
        stage_kinds=["brainstorm", "character", "world_bible", "arc_selection", "planning"],
        notes="Use the selected arc as the backbone.",
        created_at=STAMP,
        updated_at=STAMP,
    )
    selection = repo.upsert_arc_selection(
        project_id=project_id,
        selection_id=f"{project_id}:selection:001",
        selected_arc=candidate_primary,
        rejected_arc_ids=[candidate_secondary.arc_id],
        comparison_notes=["Primary Quest is easier to stage."],
        comparison_inputs=[candidate_primary, candidate_secondary],
        stage_map=stage_map,
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert [candidate.arc_id for candidate in repo.list_arc_candidates(project_id)] == ["arc-primary", "arc-secondary"]
    assert repo.get_arc_candidate(project_id, arc_id="arc-primary") == candidate_primary
    assert repo.get_arc_stage_map(project_id, arc_id="arc-primary") == stage_map
    assert repo.list_arc_stage_maps(project_id) == [stage_map]
    assert selection.selected_arc == candidate_primary
    assert selection.comparison_record_ids == [f"{project_id}:selection:001:comparison:001"]
    comparison = repo.get_arc_comparison(project_id, comparison_id=selection.comparison_record_ids[0])
    assert comparison.candidate_ids == ["arc-primary", "arc-secondary"]
    assert [item.candidate.arc_id for item in comparison.ranked_candidates] == ["arc-primary", "arc-secondary"]
    assert comparison.ranked_candidates[0].rank == 1
    assert comparison.ranked_candidates[0].notes[0].startswith("Primary Quest:")
    assert selection.stage_map == stage_map
    assert repo.get_arc_selection(project_id, selection_id=f"{project_id}:selection:001") == selection
    assert repo.list_arc_selections(project_id) == [selection]


def test_story_development_repository_round_trips_arc_comparison_record_and_history_order(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-comparisons"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    candidate_a = repo.upsert_arc_candidate(
        project_id=project_id,
        arc_id="arc-a",
        name="Anchor",
        summary="A steady route through the opening.",
        stage_map_notes=["Open", "Turn"],
        fit_notes=["Clean structure"],
        tags=["adventure"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    candidate_b = repo.upsert_arc_candidate(
        project_id=project_id,
        arc_id="arc-b",
        name="Braided",
        summary="Multiple threads move at once.",
        stage_map_notes=["Thread one", "Thread two", "Thread three"],
        fit_notes=["Ensemble energy", "Flexible pacing"],
        tags=["ensemble", "multi-thread"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    candidate_c = repo.upsert_arc_candidate(
        project_id=project_id,
        arc_id="arc-c",
        name="Mystery",
        summary="A slower reveal path.",
        stage_map_notes=["Reveal"],
        fit_notes=["Fits suspense"],
        tags=["mystery"],
        created_at=STAMP,
        updated_at=STAMP,
    )

    comparison_one = repo.upsert_arc_comparison(
        project_id=project_id,
        comparison_id="comparison-one",
        ranked_candidates=[
            ArcComparisonCandidateRecord(candidate=candidate_b, rank=1, score=(3, 2, 2, -5), notes=["Best structural fit."]),
            ArcComparisonCandidateRecord(candidate=candidate_a, rank=2, score=(2, 1, 1, -6), notes=["Simpler but less flexible."]),
        ],
        review_notes=["Prefer the braided shape for this stage."],
        created_at=STAMP,
        updated_at=STAMP,
    )
    comparison_two = repo.upsert_arc_comparison(
        project_id=project_id,
        comparison_id="comparison-two",
        candidates=[candidate_c, candidate_a],
        review_notes=["Smaller candidate set for a later revisit."],
        created_at=STAMP,
        updated_at=STAMP,
    )
    selection = repo.upsert_arc_selection(
        project_id=project_id,
        selection_id=f"{project_id}:selection:002",
        selected_arc=candidate_b,
        rejected_arc_ids=[candidate_a.arc_id, candidate_c.arc_id],
        comparison_notes=["Braided arc has the best fit for the current plan."],
        comparison_inputs=[candidate_b, candidate_a, candidate_c],
        comparison_record_ids=[comparison_one.comparison_id, comparison_two.comparison_id],
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert comparison_one.candidate_ids == ["arc-b", "arc-a"]
    assert [item.candidate.arc_id for item in comparison_one.ranked_candidates] == ["arc-b", "arc-a"]
    assert comparison_one.review_notes == ["Prefer the braided shape for this stage."]
    assert repo.get_arc_comparison(project_id, comparison_id="comparison-one") == comparison_one
    assert [record.comparison_id for record in repo.list_arc_comparisons(project_id)] == ["comparison-one", "comparison-two"]
    assert selection.comparison_record_ids == ["comparison-one", "comparison-two"]
    assert repo.get_arc_selection(project_id, selection_id=f"{project_id}:selection:002").comparison_record_ids == [
        "comparison-one",
        "comparison-two",
    ]


def test_story_development_repository_round_trips_planning_hierarchy_and_packet_context(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "planning-roundtrip"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    beat_late = repo.upsert_beat_plan(
        beat_id="beat-late",
        project_id=project_id,
        objective="Escalate the pursuit.",
        conflict="The lead loses the trail.",
        stakes="The map may be destroyed.",
        dependency_ids=["beat-early"],
        arc_stage="midpoint",
        active_character_ids=["lead", "pursuer"],
        continuity_requirements=["Trail remains visible only at dusk."],
        unresolved_questions=["Who set the decoy?"],
        status="draft",
        position=2,
        created_at=STAMP,
        updated_at=STAMP,
    )
    beat_early = repo.upsert_beat_plan(
        beat_id="beat-early",
        project_id=project_id,
        objective="Open the mystery.",
        conflict="The city shifts before the witness arrives.",
        stakes="The witness may vanish.",
        dependency_ids=[],
        arc_stage="setup",
        active_character_ids=["lead"],
        continuity_requirements=["City must shift at dusk."],
        unresolved_questions=["Where is the witness?"],
        status="draft",
        position=1,
        created_at=STAMP,
        updated_at=STAMP,
    )
    sequence = repo.upsert_sequence_plan(
        sequence_id="sequence-one",
        project_id=project_id,
        title="Opening Sequence",
        summary="The first movement of the story.",
        beat_ids=[beat_early.beat_id, beat_late.beat_id],
        chapter_ids=["chapter-one"],
        status="draft",
        position=1,
        created_at=STAMP,
        updated_at=STAMP,
    )
    chapter = repo.upsert_chapter_plan(
        chapter_id="chapter-one",
        project_id=project_id,
        title="Chapter One",
        summary="The lead enters the shifting city.",
        sequence_id=sequence.sequence_id,
        objective="Find the witness.",
        conflict="The streets do not stay fixed.",
        stakes="The only lead may be lost.",
        active_character_ids=["lead"],
        continuity_requirements=["Use the dusk map."],
        unresolved_questions=["Which district shifts first?"],
        status="draft",
        position=3,
        created_at=STAMP,
        updated_at=STAMP,
    )
    scene = repo.upsert_scene_plan(
        scene_id="scene-one",
        project_id=project_id,
        title="Market Crossing",
        summary="A tense crossing through the moving market.",
        chapter_id=chapter.chapter_id,
        objective="Reach the archive.",
        conflict="Crowds and architecture both change course.",
        stakes="The witness connection could be missed.",
        active_character_ids=["lead", "guide"],
        continuity_requirements=["Market layout must match prior clue."],
        unresolved_questions=["Who follows them?"],
        status="draft",
        position=2,
        created_at=STAMP,
        updated_at=STAMP,
    )
    packet = repo.upsert_chapter_packet(
        packet_id="packet-one",
        project_id=project_id,
        chapter_id=chapter.chapter_id,
        included_reference_ids=["manifest", "foundation", chapter.chapter_id, scene.scene_id],
        constraints=["Third-person limited", "No time travel"],
        scene_goals=["Enter the archive", "Reveal the shifting rule"],
        status="draft",
        created_at=STAMP,
        updated_at=STAMP,
    )
    dependency = repo.upsert_planning_dependency(
        dependency_id="dependency-one",
        project_id=project_id,
        upstream_id=beat_early.beat_id,
        downstream_id=beat_late.beat_id,
        dependency_kind="precedes",
        reason="The opening beat must happen before the escalation beat.",
        created_at=STAMP,
        updated_at=STAMP,
    )

    reloaded = StoryDevelopmentRepository(db_path)
    beats = reloaded.list_beat_plans(project_id)
    sequences = reloaded.list_sequence_plans(project_id)
    chapters = reloaded.list_chapter_plans(project_id)
    scenes = reloaded.list_scene_plans(project_id)
    packets = reloaded.list_chapter_packets(project_id)
    dependencies = reloaded.list_planning_dependencies(project_id)

    assert [beat.beat_id for beat in beats] == ["beat-early", "beat-late"]
    assert beats[0].position == 1
    assert beats[1].dependency_ids == ["beat-early"]
    assert sequences[0].beat_ids == ["beat-early", "beat-late"]
    assert sequences[0].chapter_ids == ["chapter-one"]
    assert chapters[0].sequence_id == sequence.sequence_id
    assert chapters[0].position == 3
    assert scenes[0].chapter_id == chapter.chapter_id
    assert scenes[0].position == 2
    assert packets[0].chapter_id == chapter.chapter_id
    assert packets[0].included_reference_ids == ["manifest", "foundation", chapter.chapter_id, scene.scene_id]
    assert packets[0].scene_goals == ["Enter the archive", "Reveal the shifting rule"]
    assert dependencies[0].upstream_id == beat_early.beat_id
    assert dependencies[0].downstream_id == beat_late.beat_id
    assert dependency.reason is not None
    assert packet.packet_id == "packet-one"


def test_story_development_repository_round_trips_drafting_objects_independently(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "drafting-roundtrip"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    draft = repo.upsert_draft_artifact(
        artifact_id="draft-1",
        project_id=project_id,
        title="Chapter 1 Draft",
        content="The city shifted at dusk.",
        source_plan_ids=["chapter-1", "scene-1"],
        source_context=["foundation", "planning"],
        provenance_note="Generated from the chapter packet.",
        status=StoryArtifactLifecycleState.DRAFT,
        created_at=STAMP,
        updated_at=STAMP,
    )
    chapter = repo.upsert_chapter_plan(
        chapter_id="chapter-1",
        project_id=project_id,
        title="Chapter 1",
        summary="The opening chapter.",
        objective="Open the city shift.",
        conflict="The city changes before the lead arrives.",
        stakes="The witness may be lost.",
        sequence_id=None,
        active_character_ids=["lead"],
        continuity_requirements=["The city must shift at dusk."],
        unresolved_questions=["Where is the witness?"],
        status="draft",
        position=1,
        created_at=STAMP,
        updated_at=STAMP,
    )
    scene = repo.upsert_scene_plan(
        scene_id="scene-1",
        project_id=project_id,
        title="Opening Scene",
        summary="The first scene of the chapter.",
        objective="Introduce the shift.",
        conflict="The streets do not stay still.",
        stakes="The clue may vanish.",
        chapter_id=chapter.chapter_id,
        active_character_ids=["lead", "witness"],
        continuity_requirements=["The market layout must match the clue."],
        unresolved_questions=["Who is following them?"],
        status="draft",
        position=1,
        created_at=STAMP,
        updated_at=STAMP,
    )
    manuscript = repo.upsert_manuscript_document(
        document_id="manuscript-1",
        project_id=project_id,
        title="Chapter 1 Manuscript",
        content="The city shifted at dusk, and Mara watched.",
        chapter_id="chapter-1",
        scene_id="scene-1",
        current_draft_artifact_id=draft.artifact_id,
        version=2,
        created_at=STAMP,
        updated_at=STAMP,
    )
    suggestion = repo.upsert_revision_suggestion(
        suggestion_id="suggestion-1",
        project_id=project_id,
        target_document_id=manuscript.document_id,
        source_text="The city shifted at dusk, and Mara watched.",
        proposed_text="At dusk, the city shifted again while Mara watched.",
        rationale="Tighten the opening rhythm.",
        source_context=["chapter-1", "scene-1"],
        status=StorySuggestionLifecycleState.REQUESTED,
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert draft.status == StoryArtifactLifecycleState.DRAFT
    assert draft.source_plan_ids == ["chapter-1", "scene-1"]
    assert repo.get_draft_artifact(draft.artifact_id) == draft
    assert repo.list_draft_artifacts(project_id) == [draft]

    assert chapter.chapter_id == "chapter-1"
    assert scene.chapter_id == chapter.chapter_id
    assert manuscript.current_draft_artifact_id == draft.artifact_id
    assert manuscript.version == 2
    assert repo.get_manuscript_document(manuscript.document_id) == manuscript
    assert repo.list_manuscript_documents(project_id) == [manuscript]

    assert suggestion.status == StorySuggestionLifecycleState.REQUESTED
    assert suggestion.target_document_id == manuscript.document_id
    assert repo.get_revision_suggestion(suggestion.suggestion_id) == suggestion
    assert repo.list_revision_suggestions(project_id) == [suggestion]
    assert repo.list_revision_suggestions_for_document(project_id, target_document_id=manuscript.document_id) == [suggestion]


def test_story_decision_nodes_round_trip_links_state_and_ordering(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-decisions"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    pivot = repo.record_story_decision_node(
        node_id="node-b",
        project_id=project_id,
        node_type="DECISION",
        change_type="ARC_SELECTION",
        subject_type="ARC_SELECTION",
        subject_id="selection-001",
        parent_node_id="node-a",
        branch_id="branch-main",
        summary="Choose the primary quest arc.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-001", "relation_kind": "primary"},
            {"object_type": "ARC_CANDIDATE", "object_id": "arc-primary", "relation_kind": "selected_arc"},
        ],
        prior_state_ref="arc-candidate:arc-secondary",
        prior_state_summary="Braided mystery was still the active choice.",
        new_state_ref="arc-candidate:arc-primary",
        new_state_summary="Primary Quest becomes the active arc.",
        reason_or_note="Primary Quest has a cleaner escalation path.",
        made_by="writer:alex",
        decision_made_at=STAMP,
        informing_object_links=[
            {"object_type": "ARC_COMPARISON_RECORD", "object_id": "comparison-001", "relation_kind": "informed_by"},
            {"object_type": "CHECKER_FINDING", "object_id": "finding-009", "relation_kind": "considered"},
        ],
        created_at=STAMP,
        updated_at=STAMP,
    )
    stage_change = repo.record_story_decision_node(
        node_id="node-c",
        project_id=project_id,
        node_type="DECISION",
        change_type="STAGE_CONFIGURATION",
        subject_type="STORY_FLOW_STAGE",
        subject_id="brainstorm",
        parent_node_id="node-b",
        branch_id="branch-main",
        summary="Advance the brainstorm stage.",
        related_object_links=[
            {"object_type": "STORY_FLOW_STAGE", "object_id": "brainstorm", "relation_kind": "primary"},
            {"object_type": "STORY_FLOW_DEFINITION", "object_id": project_id, "relation_kind": "project_flow"},
        ],
        prior_state_ref="stage_progress:NOT_STARTED",
        prior_state_summary="Brainstorm stage has not started.",
        new_state_ref="stage_progress:IN_PROGRESS",
        new_state_summary="Brainstorm stage is now underway.",
        reason_or_note="The outline needs one more pass.",
        made_by="writer:alex",
        decision_made_at=STAMP.replace(hour=14),
        informing_object_links=[
            {"object_type": "WORLD_BIBLE_ENTRY", "object_id": "world-bible:city-rule", "relation_kind": "context"},
        ],
        created_at=STAMP.replace(hour=14),
        updated_at=STAMP.replace(hour=14),
    )
    initial = repo.record_story_decision_node(
        node_id="node-a",
        project_id=project_id,
        node_type="DECISION",
        change_type="ARC_SELECTION",
        subject_type="ARC_SELECTION",
        subject_id="selection-001",
        branch_id="branch-main",
        summary="Initial selection favored the mystery arc.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-001", "relation_kind": "primary"},
            {"object_type": "ARC_CANDIDATE", "object_id": "arc-secondary", "relation_kind": "previous_choice"},
        ],
        prior_state_ref="arc-candidate:arc-unknown",
        prior_state_summary="No arc had been selected yet.",
        new_state_ref="arc-candidate:arc-secondary",
        new_state_summary="Braided mystery is selected first.",
        reason_or_note="The mystery arc better fits the opening mood.",
        made_by="writer:alex",
        decision_made_at=STAMP,
        informing_object_links=[
            {"object_type": "ARC_COMPARISON_RECORD", "object_id": "comparison-000", "relation_kind": "informed_by"},
            {"object_type": "DRAFT_ARTIFACT", "object_id": "manifest", "relation_kind": "source_context"},
        ],
        created_at=STAMP,
        updated_at=STAMP,
    )

    reloaded = StoryDevelopmentRepository(db_path)
    ordered = reloaded.list_story_decision_nodes(project_id)
    subject_timeline = reloaded.list_story_decision_nodes_for_subject(
        project_id,
        subject_type="ARC_SELECTION",
        subject_id="selection-001",
    )

    assert [record.node_id for record in ordered] == ["node-a", "node-b", "node-c"]
    assert [record.node_id for record in subject_timeline] == ["node-a", "node-b"]
    assert initial == reloaded.get_story_decision_node(project_id, node_id="node-a")
    assert [link.object_id for link in pivot.related_object_links] == ["selection-001", "arc-primary"]
    assert pivot.parent_node_id == "node-a"
    assert pivot.branch_id == "branch-main"
    assert pivot.prior_state_ref == "arc-candidate:arc-secondary"
    assert pivot.new_state_summary == "Primary Quest becomes the active arc."
    assert pivot.reason_or_note == "Primary Quest has a cleaner escalation path."
    assert pivot.made_by == "writer:alex"
    assert [link.object_id for link in pivot.informing_object_links] == ["comparison-001", "finding-009"]
    assert stage_change.related_object_links[0].object_id == "brainstorm"
    assert stage_change.decision_made_at > pivot.decision_made_at


def test_story_branch_repository_round_trips_branch_identity_and_branch_point_links(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-branches"
    other_project_id = "story-dev-branches-other"
    _seed_project(db_path, project_id)
    _seed_project(db_path, other_project_id)
    repo = StoryDevelopmentRepository(db_path)

    branch_source = repo.record_story_decision_node(
        node_id="branch-node-1",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id="selection-branch-1",
        branch_id="branch-main",
        summary="Fork the main path into an alternate branch.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-branch-1", "relation_kind": "primary"},
        ],
        prior_state_ref="arc:selected:main",
        new_state_ref="arc:selected:branch",
        reason_or_note="Preserve the alternate route for review.",
        made_by="writer:alex",
        decision_made_at=STAMP,
        created_at=STAMP,
        updated_at=STAMP,
    )
    branch_point = repo.upsert_branch_point(
        branch_point_id="branch-point-1",
        project_id=project_id,
        source_node_id=branch_source.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )
    archived_branch = repo.upsert_story_branch(
        branch_id="branch-archive",
        project_id=project_id,
        branch_point_id=branch_point.branch_point_id,
        branch_name="Archive Path",
        branch_state="ARCHIVED",
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )
    active_branch = repo.upsert_story_branch(
        branch_id="branch-main",
        project_id=project_id,
        branch_point_id=branch_point.branch_point_id,
        branch_name="Main Timeline",
        branch_state=StoryBranchState.ACTIVE,
        created_at=STAMP,
        updated_at=STAMP,
    )

    other_branch_source = repo.record_story_decision_node(
        node_id="branch-node-2",
        project_id=other_project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id="selection-branch-2",
        branch_id="branch-other",
        summary="Fork the other project path.",
        related_object_links=[
            {"object_type": "ARC_SELECTION", "object_id": "selection-branch-2", "relation_kind": "primary"},
        ],
        prior_state_ref="arc:selected:other",
        new_state_ref="arc:selected:other-branch",
        reason_or_note="Keep the alternate route isolated.",
        made_by="writer:alex",
        decision_made_at=STAMP,
        created_at=STAMP,
        updated_at=STAMP,
    )
    other_branch_point = repo.upsert_branch_point(
        branch_point_id="branch-point-2",
        project_id=other_project_id,
        source_node_id=other_branch_source.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )
    other_branch = repo.upsert_story_branch(
        branch_id="branch-other",
        project_id=other_project_id,
        branch_point_id=other_branch_point.branch_point_id,
        branch_name="Other Timeline",
        branch_state="ACTIVE",
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert repo.get_branch_point(branch_point.branch_point_id) == branch_point
    assert repo.get_branch_point_for_source_node(project_id, source_node_id=branch_source.node_id) == branch_point
    assert repo.list_branch_points(project_id) == [branch_point]
    assert [branch.branch_id for branch in repo.list_story_branches(project_id)] == [
        active_branch.branch_id,
        archived_branch.branch_id,
    ]
    assert repo.get_story_branch(active_branch.branch_id).branch_state == StoryBranchState.ACTIVE
    assert repo.get_story_branch(archived_branch.branch_id).branch_state == StoryBranchState.ARCHIVED
    assert active_branch.branch_point_id == branch_point.branch_point_id
    assert repo.get_story_branch(active_branch.branch_id) == active_branch
    assert repo.list_story_branches(other_project_id) == [other_branch]
    assert repo.get_branch_point_for_source_node(other_project_id, source_node_id=other_branch_source.node_id) == other_branch_point
    assert repo.get_active_story_branch(project_id) == active_branch

    state_ref = repo.upsert_branch_state_ref(
        branch_state_ref_id="branch-state-ref-1",
        project_id=project_id,
        branch_id=active_branch.branch_id,
        state_object_type=StoryObjectType.ARC_SELECTION,
        state_object_id="selection-branch-1",
        decision_node_id=branch_source.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )
    assert state_ref.branch_id == active_branch.branch_id
    assert state_ref.state_object_type == StoryObjectType.ARC_SELECTION
    assert repo.get_branch_state_ref(state_ref.branch_state_ref_id) == state_ref
    assert repo.get_branch_state_ref_for_object(
        project_id,
        branch_id=active_branch.branch_id,
        state_object_type=StoryObjectType.ARC_SELECTION,
        state_object_id="selection-branch-1",
    ) == state_ref
    assert repo.list_branch_state_refs(project_id, branch_id=active_branch.branch_id) == [state_ref]
    assert repo.list_branch_state_refs_for_decision_node(
        project_id,
        branch_id=active_branch.branch_id,
        decision_node_id=branch_source.node_id,
    ) == [state_ref]

    active_after_switch = repo.set_active_story_branch(project_id, branch_id=archived_branch.branch_id)
    assert active_after_switch.branch_id == archived_branch.branch_id
    assert active_after_switch.branch_state == StoryBranchState.ACTIVE
    assert repo.get_active_story_branch(project_id).branch_id == archived_branch.branch_id
    assert repo.get_story_branch(active_branch.branch_id).branch_state == StoryBranchState.ARCHIVED
    assert repo.get_story_branch(archived_branch.branch_id).branch_state == StoryBranchState.ACTIVE

    try:
        repo.upsert_story_branch(
            branch_id="branch-cross-project",
            project_id=project_id,
            branch_point_id=other_branch_point.branch_point_id,
            branch_name="Invalid Cross Project Branch",
            branch_state="ACTIVE",
            created_at=STAMP,
            updated_at=STAMP,
        )
    except ValueError as exc:
        assert "same project" in str(exc)
    else:
        raise AssertionError("expected cross-project branch point rejection")

    try:
        repo.upsert_branch_state_ref(
            branch_state_ref_id="branch-state-ref-2",
            project_id=project_id,
            branch_id=other_branch.branch_id,
            state_object_type=StoryObjectType.CHAPTER_PLAN,
            state_object_id="chapter-2",
            decision_node_id=other_branch_source.node_id,
            created_at=STAMP,
            updated_at=STAMP,
        )
    except KeyError:
        pass
    else:
        raise AssertionError("expected cross-project branch state ref rejection")


def test_story_branch_upsert_keeps_only_one_active_branch_per_project(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-branches-single-active"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    first_source = repo.record_story_decision_node(
        node_id="single-active-node-1",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id="selection-1",
        branch_id="branch-one",
        summary="Create first branch.",
        related_object_links=[{"object_type": "ARC_SELECTION", "object_id": "selection-1", "relation_kind": "primary"}],
        prior_state_ref="arc:selected:base",
        new_state_ref="arc:selected:branch-one",
        reason_or_note="Test first branch.",
        made_by="writer:test",
        decision_made_at=STAMP,
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_source = repo.record_story_decision_node(
        node_id="single-active-node-2",
        project_id=project_id,
        node_type="BRANCH_POINT",
        change_type="BRANCH_CREATED",
        subject_type="ARC_SELECTION",
        subject_id="selection-2",
        branch_id="branch-two",
        summary="Create second branch.",
        related_object_links=[{"object_type": "ARC_SELECTION", "object_id": "selection-2", "relation_kind": "primary"}],
        prior_state_ref="arc:selected:branch-one",
        new_state_ref="arc:selected:branch-two",
        reason_or_note="Test second branch.",
        made_by="writer:test",
        decision_made_at=STAMP,
        created_at=STAMP,
        updated_at=STAMP,
    )
    first_point = repo.upsert_branch_point(
        branch_point_id="single-active-point-1",
        project_id=project_id,
        source_node_id=first_source.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_point = repo.upsert_branch_point(
        branch_point_id="single-active-point-2",
        project_id=project_id,
        source_node_id=second_source.node_id,
        created_at=STAMP,
        updated_at=STAMP,
    )

    repo.upsert_story_branch(
        branch_id="branch-one",
        project_id=project_id,
        branch_point_id=first_point.branch_point_id,
        branch_name="Branch One",
        branch_state="ACTIVE",
        created_at=STAMP,
        updated_at=STAMP,
    )
    active_branch = repo.upsert_story_branch(
        branch_id="branch-two",
        project_id=project_id,
        branch_point_id=second_point.branch_point_id,
        branch_name="Branch Two",
        branch_state="ACTIVE",
        created_at=STAMP.replace(hour=13),
        updated_at=STAMP.replace(hour=13),
    )

    assert repo.get_active_story_branch(project_id).branch_id == "branch-two"
    assert repo.get_story_branch("branch-one").branch_state == StoryBranchState.ARCHIVED
    assert repo.get_story_branch("branch-two").branch_state == StoryBranchState.ACTIVE
    assert active_branch.branch_state == StoryBranchState.ACTIVE


def test_story_development_repository_round_trips_review_and_inspect_records_independently(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-review"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    draft = repo.upsert_draft_artifact(
        artifact_id="draft-review-1",
        project_id=project_id,
        title="Draft for review",
        content="The city shifted at dusk.",
        source_plan_ids=["chapter-1"],
        source_context=["planning", "foundation"],
        provenance_note="Generated before review.",
        status=StoryArtifactLifecycleState.DRAFT,
        created_at=STAMP,
        updated_at=STAMP,
    )
    manuscript = repo.upsert_manuscript_document(
        document_id="manuscript-review-1",
        project_id=project_id,
        title="Manuscript for review",
        content="The city shifted at dusk, and Mara watched.",
        chapter_id=None,
        scene_id=None,
        current_draft_artifact_id=draft.artifact_id,
        version=1,
        created_at=STAMP,
        updated_at=STAMP,
    )

    finding_primary = repo.upsert_checker_finding(
        finding_id="finding-1",
        project_id=project_id,
        source_object_id="selection-001",
        source_object_kind="ARC_SELECTION",
        severity="warning",
        summary="Arc choice needs a clearer midpoint turn.",
        details="The selected arc does not yet show a strong reversal.",
        source_context=["comparison-001", "checker-run-001"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    finding_secondary = repo.upsert_checker_finding(
        finding_id="finding-2",
        project_id=project_id,
        source_object_id=manuscript.document_id,
        source_object_kind="MANUSCRIPT_DOCUMENT",
        severity="info",
        summary="Opening line could be tightened.",
        details=None,
        source_context=["checker-run-002"],
        created_at=STAMP,
        updated_at=STAMP,
    )

    decision_primary = repo.upsert_review_decision(
        decision_id="decision-1",
        project_id=project_id,
        target_id="selection-001",
        target_kind="ARC_SELECTION",
        decision="accept",
        notes="Keep the current arc but revisit the midpoint.",
        source_context=["finding-1", "comparison-001"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    decision_secondary = repo.upsert_review_decision(
        decision_id="decision-2",
        project_id=project_id,
        target_id=manuscript.document_id,
        target_kind="MANUSCRIPT_DOCUMENT",
        decision="revise",
        notes=None,
        source_context=["finding-2"],
        created_at=STAMP,
        updated_at=STAMP,
    )

    link_primary = repo.upsert_inspect_run_link(
        link_id="inspect-link-1",
        project_id=project_id,
        object_kind="ARC_SELECTION",
        object_id="selection-001",
        logical_run_id="checker-run-001",
        run_id="checker-run-001-attempt-1",
        run_kind="checker",
        attempt_number=1,
        label="Arc selection inspection",
        created_at=STAMP,
        updated_at=STAMP,
    )
    link_secondary = repo.upsert_inspect_run_link(
        link_id="inspect-link-2",
        project_id=project_id,
        object_kind="MANUSCRIPT_DOCUMENT",
        object_id=manuscript.document_id,
        logical_run_id="checker-run-002",
        run_id="checker-run-002-attempt-1",
        run_kind="checker",
        attempt_number=None,
        label=None,
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert repo.list_draft_artifacts(project_id) == [draft]
    assert manuscript.current_draft_artifact_id == draft.artifact_id
    assert repo.list_manuscript_documents(project_id) == [manuscript]

    assert repo.get_checker_finding(finding_primary.finding_id) == finding_primary
    assert repo.list_checker_findings(project_id) == [finding_primary, finding_secondary]
    assert repo.list_checker_findings_for_source(
        project_id,
        source_object_kind="ARC_SELECTION",
        source_object_id="selection-001",
    ) == [finding_primary]

    assert repo.get_review_decision(decision_primary.decision_id) == decision_primary
    assert repo.list_review_decisions(project_id) == [decision_primary, decision_secondary]
    assert repo.list_review_decisions_for_target(
        project_id,
        target_kind="ARC_SELECTION",
        target_id="selection-001",
    ) == [decision_primary]

    assert repo.get_inspect_run_link(link_primary.link_id) == link_primary
    assert repo.list_inspect_run_links(project_id) == [link_primary, link_secondary]
    assert repo.list_inspect_run_links_for_object(
        project_id,
        object_kind="ARC_SELECTION",
        object_id="selection-001",
    ) == [link_primary]
    assert repo.list_inspect_run_links_for_run(
        project_id,
        run_id="checker-run-001-attempt-1",
    ) == [link_primary]
    assert repo.list_inspect_run_links_for_logical_run(
        project_id,
        logical_run_id="checker-run-002",
    ) == [link_secondary]
