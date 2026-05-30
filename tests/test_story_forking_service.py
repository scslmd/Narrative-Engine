from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.generation import (
    CanonGenerationRequest,
    CanonScope,
    DestinationKind,
    GenerationDestination,
    GenerationMode,
)
from app.schemas.projects import ProjectCreateRequest
from app.services.projects import ProjectService
from app.services.story_forking import StoryForkingService
from app.utils.db_inserts import hash_id


def test_story_forking_service_copies_selected_canon(tmp_path) -> None:
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    repo.upsert_world_bible_entry(
        project_id="source-project",
        entry_type="location",
        title="North Keep",
        summary="Ancient border fortress.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1"],
            world_bible_refs=[{"entry_type": "location", "title": "North Keep"}],
        ),
        generation_brief="Fork story",
        target_chapter_count=2,
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters("source-project", target_project_id, ["char-1"])
    copied_world = service.copy_selected_world_entries(
        "source-project",
        target_project_id,
        [{"entry_type": "location", "title": "North Keep"}],
    )
    assert copied_chars
    assert copied_world == ["location:North Keep"]


def test_relationship_id_remapping(tmp_path) -> None:
    """copy_selected_relationships remaps character IDs to forked IDs."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-2",
        project_id="source-project",
        display_name="Bjorn",
        role_in_story="antagonist",
    )
    source_edge = repo.upsert_relationship_edge(
        project_id="source-project",
        source_character_id="char-1",
        target_character_id="char-2",
        relation_kind="rivalry",
        summary="They are rivals.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1", "char-2"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters("source-project", target_project_id, ["char-1", "char-2"])
    copied_edges = service.copy_selected_relationships(
        "source-project", target_project_id, ["char-1", "char-2"]
    )
    assert len(copied_edges) == 1
    forked_char_1 = hash_id("fork-character", f"source-project:{target_project_id}:char-1")
    forked_char_2 = hash_id("fork-character", f"source-project:{target_project_id}:char-2")
    forked_edge_id = hash_id("fork-edge", f"source-project:{target_project_id}:{source_edge.edge_id}")
    assert copied_edges[0] == forked_edge_id
    forked_edge = repo.get_relationship_edge(forked_edge_id)
    assert forked_edge.source_character_id == forked_char_1
    assert forked_edge.target_character_id == forked_char_2
    assert forked_edge.relation_kind == "rivalry"


def test_relationships_empty_when_no_match(tmp_path) -> None:
    """Returns [] when no relationships match selected characters."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_edges = service.copy_selected_relationships(
        "source-project", target_project_id, ["char-1"]
    )
    assert copied_edges == []


def test_foundation_with_overrides(tmp_path) -> None:
    """create_fork_foundation applies premise_override and tone_override."""
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
    repo.upsert_foundation_profile(
        project_id="source-project",
        premise="Original premise",
        logline="Original logline",
        tone_direction="Dark",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[],
            scope_mode="full_project",
        ),
        generation_brief="Fork story",
        premise_override="New overridden premise",
        tone_override="Light-hearted",
    )
    target_project_id = service.create_fork_project(request)
    revision_id = service.create_fork_foundation("source-project", target_project_id, request)
    assert revision_id != ""
    revisions = repo.list_foundation_revisions(target_project_id)
    assert len(revisions) == 1
    latest = revisions[-1]
    assert latest.premise == "New overridden premise"
    assert latest.tone_direction == "Light-hearted"
    assert latest.logline == "Original logline"


def test_foundation_without_source_returns_empty(tmp_path) -> None:
    """Returns '' when source has no foundation revisions."""
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
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[],
            scope_mode="full_project",
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    revision_id = service.create_fork_foundation("source-project", target_project_id, request)
    assert revision_id == ""


def test_source_link_recording(tmp_path) -> None:
    """record_source_link creates checker finding with correct provenance."""
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
    project_service.create_project(
        ProjectCreateRequest(
            project_id="target-project",
            project_name="Target Project",
            genre="Fantasy",
            tone_profile="Neutral",
            story_structure="THREE_ACT",
        )
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    generation_id = "gen-abc-123"
    service.record_source_link("source-project", "target-project", generation_id)
    expected_finding_id = hash_id("fork-link", f"source-project:target-project:{generation_id}")
    finding = repo.get_checker_finding(expected_finding_id)
    assert finding.finding_id == expected_finding_id
    assert finding.project_id == "target-project"
    assert finding.source_object_id == "source-project"
    assert finding.source_object_kind == "source_project"
    assert finding.severity == "info"
    assert finding.summary == "Forked from source-project"
    assert finding.details == f"generation_id={generation_id}"
    assert generation_id in finding.source_context


def test_fork_project_idempotent(tmp_path) -> None:
    """Second create_fork_project call returns same project_id (no duplicate)."""
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
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[],
            scope_mode="full_project",
        ),
        generation_brief="Fork story",
    )
    first_id = service.create_fork_project(request)
    second_id = service.create_fork_project(request)
    assert first_id == second_id
    projects = project_service.list_projects()
    forked_count = sum(1 for p in projects if p.project_id == first_id)
    assert forked_count == 1


def test_skip_nonexistent_characters(tmp_path) -> None:
    """copy_selected_characters skips IDs that don't exist in source."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters(
        "source-project", target_project_id, ["char-1", "nonexistent-char"]
    )
    assert len(copied_chars) == 1
    forked_char_1 = hash_id("fork-character", f"source-project:{target_project_id}:char-1")
    assert copied_chars[0] == forked_char_1
    target_chars = repo.list_character_profiles(target_project_id)
    assert len(target_chars) == 1


def test_fork_provenance_in_voice_notes(tmp_path) -> None:
    """Copied character has 'forked from {source}:{id}' appended to voice_notes."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
        voice_notes="Original voice notes here.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters("source-project", target_project_id, ["char-1"])
    forked_char = repo.get_character_profile(copied_chars[0])
    assert "Original voice notes here." in (forked_char.voice_notes or "")
    assert f"forked from source-project:char-1" in (forked_char.voice_notes or "")


def test_world_entry_normalization(tmp_path) -> None:
    """Dict refs are normalized to WorldBibleRef objects and work correctly."""
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
    repo.upsert_world_bible_entry(
        project_id="source-project",
        entry_type="location",
        title="North Keep",
        summary="Ancient border fortress.",
    )
    repo.upsert_world_bible_entry(
        project_id="source-project",
        entry_type="culture",
        title="Northern Dialect",
        summary="Language spoken in the north.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[],
            scope_mode="full_project",
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    dict_refs: list[dict[str, str]] = [
        {"entry_type": "location", "title": "North Keep"},
        {"entry_type": "culture", "title": "Northern Dialect"},
    ]
    copied_world = service.copy_selected_world_entries(
        "source-project", target_project_id, dict_refs
    )
    assert len(copied_world) == 2
    assert "location:North Keep" in copied_world
    assert "culture:Northern Dialect" in copied_world


def test_all_character_fields_copied(tmp_path) -> None:
    """Verify external_goal, internal_need, etc. are preserved on copy."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
        archetype="hero",
        external_goal="Defeat the dark lord",
        internal_need="Learn to trust others",
        misbelief_or_wound="I must do everything alone",
        core_fear="Abandonment",
        primary_strength="Resilience",
        fatal_flaw_or_limitation="Stubborn pride",
        contradictions=["brave but reckless", "loyal but secretive"],
        backstory_summary="Orphaned at a young age.",
        voice_notes="Speaks with measured calm.",
        secrets=["Knows the true name of the dark lord"],
        values=["Honor", "Justice"],
        taboos=["Never kills children"],
        change_axis="Isolation -> Connection",
        arc_stage_notes="Act 2 turning point approaching",
        continuity_facts=["Has a scar on left cheek", "Carries a silver locket"],
        writer_notes="Keep her dialogue concise.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters("source-project", target_project_id, ["char-1"])
    forked_char = repo.get_character_profile(copied_chars[0])
    assert forked_char.display_name == "Aria"
    assert forked_char.role_in_story == "protagonist"
    assert forked_char.archetype == "hero"
    assert forked_char.external_goal == "Defeat the dark lord"
    assert forked_char.internal_need == "Learn to trust others"
    assert forked_char.misbelief_or_wound == "I must do everything alone"
    assert forked_char.core_fear == "Abandonment"
    assert forked_char.primary_strength == "Resilience"
    assert forked_char.fatal_flaw_or_limitation == "Stubborn pride"
    assert forked_char.contradictions == ["brave but reckless", "loyal but secretive"]
    assert forked_char.backstory_summary == "Orphaned at a young age."
    assert "Speaks with measured calm." in (forked_char.voice_notes or "")
    assert forked_char.secrets == ["Knows the true name of the dark lord"]
    assert forked_char.values == ["Honor", "Justice"]
    assert forked_char.taboos == ["Never kills children"]
    assert forked_char.change_axis == "Isolation -> Connection"
    assert forked_char.arc_stage_notes == "Act 2 turning point approaching"
    assert forked_char.continuity_facts == ["Has a scar on left cheek", "Carries a silver locket"]
    assert forked_char.writer_notes == "Keep her dialogue concise."


def test_edge_ids_are_deterministic(tmp_path) -> None:
    """Same input produces same fork-edge hash."""
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
    repo.upsert_character_profile(
        character_id="char-1",
        project_id="source-project",
        display_name="Aria",
        role_in_story="protagonist",
    )
    repo.upsert_character_profile(
        character_id="char-2",
        project_id="source-project",
        display_name="Bjorn",
        role_in_story="antagonist",
    )
    source_edge = repo.upsert_relationship_edge(
        project_id="source-project",
        source_character_id="char-1",
        target_character_id="char-2",
        relation_kind="rivalry",
        summary="They are rivals.",
    )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=["char-1", "char-2"],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    service.copy_selected_characters("source-project", target_project_id, ["char-1", "char-2"])
    edges_first = service.copy_selected_relationships(
        "source-project", target_project_id, ["char-1", "char-2"]
    )
    expected_edge_id = hash_id("fork-edge", f"source-project:{target_project_id}:{source_edge.edge_id}")
    assert edges_first[0] == expected_edge_id
    edges_second = service.copy_selected_relationships(
        "source-project", target_project_id, ["char-1", "char-2"]
    )
    assert edges_second[0] == edges_first[0]


def test_batch_character_inserts_single_transaction(tmp_path) -> None:
    """copy_selected_characters uses a single shared connection for all inserts."""
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
    for i in range(5):
        repo.upsert_character_profile(
            character_id=f"char-{i}",
            project_id="source-project",
            display_name=f"Character {i}",
            role_in_story="supporting",
        )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[f"char-{i}" for i in range(5)],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    copied_chars = service.copy_selected_characters(
        "source-project", target_project_id, [f"char-{i}" for i in range(5)]
    )
    assert len(copied_chars) == 5
    target_chars = repo.list_character_profiles(target_project_id)
    assert len(target_chars) == 5
    for i, char in enumerate(target_chars):
        assert char.display_name == f"Character {i}"
        assert f"forked from source-project:char-{i}" in (char.voice_notes or "")


def test_batch_world_entry_inserts_single_transaction(tmp_path) -> None:
    """copy_selected_world_entries uses a single shared connection for all inserts."""
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
    for i in range(5):
        repo.upsert_world_bible_entry(
            project_id="source-project",
            entry_type="location",
            title=f"Location {i}",
            summary=f"Summary for location {i}.",
            canonical_facts=[f"Fact {i}"],
        )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[],
            scope_mode="full_project",
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    refs = [{"entry_type": "location", "title": f"Location {i}"} for i in range(5)]
    copied_world = service.copy_selected_world_entries(
        "source-project", target_project_id, refs
    )
    assert len(copied_world) == 5
    target_entries = repo.list_world_bible_entries(target_project_id)
    assert len(target_entries) == 5
    for i, entry in enumerate(target_entries):
        assert entry.title == f"Location {i}"
        assert entry.summary == f"Summary for location {i}."
        assert entry.canonical_facts == [f"Fact {i}"]
        assert f"forked from source-project:location:Location {i}" in (entry.writer_notes or "")


def test_batch_relationship_inserts_single_transaction(tmp_path) -> None:
    """copy_selected_relationships uses a single shared connection for all inserts."""
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
    for i in range(5):
        repo.upsert_character_profile(
            character_id=f"char-{i}",
            project_id="source-project",
            display_name=f"Character {i}",
            role_in_story="supporting",
        )
    for i in range(4):
        repo.upsert_relationship_edge(
            project_id="source-project",
            source_character_id=f"char-{i}",
            target_character_id=f"char-{i+1}",
            relation_kind="ally",
            summary=f"Alliance {i}.",
        )
    service = StoryForkingService(repository=repo, project_service=project_service)
    request = CanonGenerationRequest(
        source_project_id="source-project",
        mode=GenerationMode.NEW_PROJECT_CHARACTER_FORK,
        destination=GenerationDestination(
            destination_kind=DestinationKind.NEW_PROJECT,
            target_project_name="Forked",
        ),
        canon_scope=CanonScope(
            source_project_id="source-project",
            character_ids=[f"char-{i}" for i in range(5)],
        ),
        generation_brief="Fork story",
    )
    target_project_id = service.create_fork_project(request)
    service.copy_selected_characters(
        "source-project", target_project_id, [f"char-{i}" for i in range(5)]
    )
    copied_edges = service.copy_selected_relationships(
        "source-project", target_project_id, [f"char-{i}" for i in range(5)]
    )
    assert len(copied_edges) == 4
    for edge_id in copied_edges:
        edge = repo.get_relationship_edge(edge_id)
        assert edge.relation_kind == "ally"
        assert edge.source_character_id.startswith("fork-character-")
        assert edge.target_character_id.startswith("fork-character-")
