from __future__ import annotations

import pytest
from app.schemas.story_development import CharacterProfile, PriorChapterSummary
from app.services.scene_context import SceneContext, SceneContextService, CharacterAnchor, WorldConstraint


class FakeRepository:
    def list_character_profiles(self, project_id: str):
        return []

    def get_character_profile(self, character_id: str):
        return CharacterProfile(
            character_id=character_id,
            project_id="proj-1",
            display_name="Khal",
            role_in_story="protagonist",
            archetype="reluctant hero",
            external_goal="Survive the journey",
            internal_need="Trust others",
            misbelief_or_wound="People will leave",
            core_fear="Abandonment",
            primary_strength="Resilience",
            fatal_flaw_or_limitation="Refuses to ask for help",
            backstory_summary="Orphaned young",
            voice_notes="Direct, terse",
            change_axis="Learns to trust",
        )

    def list_world_bible_entries(self, project_id: str):
        return []


def test_character_anchor_dataclass():
    anchor = CharacterAnchor(
        character_id="char-001",
        display_name="Khal",
        archetype="reluctant hero",
        voice_notes="Direct, terse, avoids metaphors",
        external_goal="Survive the journey",
        internal_need="Trust others",
        core_fear="Abandonment",
    )
    assert anchor.display_name == "Khal"
    assert anchor.archetype == "reluctant hero"


def test_scene_context_dataclass():
    ctx = SceneContext(
        characters=[
            CharacterAnchor(
                character_id="c1",
                display_name="A",
                archetype="hero",
                voice_notes="",
                external_goal="",
                internal_need="",
                core_fear="",
            )
        ],
        world_facts=[],
    )
    assert len(ctx.characters) == 1


def test_world_constraint_dataclass():
    wc = WorldConstraint(
        entry_type="location",
        title="The Wastes",
        facts=["Barren landscape", "No permanent settlements"],
    )
    assert wc.entry_type == "location"
    assert len(wc.facts) == 2


def test_assemble_context_with_active_characters():
    repo = FakeRepository()
    service = SceneContextService(repository=repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001"],
    )
    assert len(ctx.characters) == 1
    assert ctx.characters[0].display_name == "Khal"


def test_assemble_context_fallback_to_all_characters():
    repo = FakeRepository()
    service = SceneContextService(repository=repo)
    ctx = service.assemble_context(project_id="proj-1")
    # Should fallback to all characters (empty in this case)
    assert isinstance(ctx.characters, list)


def test_to_prompt_string_formats_anchors():
    ctx = SceneContext(
        characters=[CharacterAnchor(
            character_id="c1", display_name="Khal",
            archetype="reluctant hero", voice_notes="Direct, terse",
            external_goal="Survive", internal_need="Trust", core_fear="Abandonment",
        )],
        world_facts=[],
    )
    prompt = ctx.to_prompt_string()
    assert "Khal" in prompt
    assert "reluctant hero" in prompt


def test_to_prompt_string_includes_world_facts():
    ctx = SceneContext(
        characters=[],
        world_facts=[WorldConstraint(
            entry_type="location", title="The Bazaar",
            facts=["crowded", "noisy", "smells of spices"],
        )],
    )
    prompt = ctx.to_prompt_string()
    assert "The Bazaar" in prompt
    assert "crowded" in prompt


class MultiCharRepository:
    """Repository that returns different characters for different IDs."""

    def list_character_profiles(self, project_id: str):
        return []  # Empty to force no fallback

    def get_character_profile(self, character_id: str):
        names = {"char-001": "Kael", "char-002": "Soraya", "char-003": "Joss"}
        if character_id not in names:
            raise KeyError(character_id)
        return CharacterProfile(
            character_id=character_id,
            project_id="proj-1",
            display_name=names[character_id],
            role_in_story="supporting",
            archetype="hero",
            external_goal="Survive",
            internal_need="Trust",
            misbelief_or_wound="Distrust",
            core_fear="Loss",
            primary_strength="Resilience",
            fatal_flaw_or_limitation="Stubbornness",
            backstory_summary="Unknown origin",
            voice_notes="Normal",
            change_axis="Learns to trust",
        )

    def list_world_bible_entries(self, project_id: str):
        return []


def test_assemble_context_respects_active_character_ids():
    """SceneContextService should filter characters by active_character_ids from ChapterPlan."""
    repo = MultiCharRepository()
    service = SceneContextService(repository=repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001", "char-002"],  # Only Kael and Soraya
    )
    assert len(ctx.characters) == 2
    names = {c.display_name for c in ctx.characters}
    assert "Kael" in names
    assert "Soraya" in names
    assert "Joss" not in names  # Not in active list


def test_assemble_context_skips_missing_character_ids():
    """Missing character IDs should be skipped gracefully."""
    repo = MultiCharRepository()
    service = SceneContextService(repository=repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001", "char-nonexistent"],
    )
    assert len(ctx.characters) == 1
    assert ctx.characters[0].display_name == "Kael"


def test_assemble_context_with_prior_chapters():
    repo = FakeRepository()
    service = SceneContextService(repository=repo)
    prior = [PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves the village"],
        character_states={"Kael": "restless"},
        unresolved_threads=["Who is waiting at the crossroads?"],
    )]
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-001"],
        prior_chapters=prior,
    )
    assert len(ctx.prior_chapters) == 1
    assert ctx.prior_chapters[0].title == "The Departure"


def test_to_prompt_string_includes_prior_chapters():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        prior_chapters=[PriorChapterSummary(
            chapter_id="ch-001",
            title="The Departure",
            key_events=["Kael leaves"],
            character_states={},
            unresolved_threads=["Where next?"],
        )],
    )
    prompt = ctx.to_prompt_string()
    assert "PRIOR CHAPTER CONTEXT:" in prompt
    assert "PRIOR CHAPTER: The Departure" in prompt
    assert "Kael leaves" in prompt


def test_to_prompt_string_caps_prior_chapters_at_3():
    """SceneContext should only include the last 3 prior chapters to avoid bloated prompts."""
    prior = [PriorChapterSummary(
        chapter_id=f"ch-{i:03d}",
        title=f"Chapter {i}",
        key_events=[f"Event in chapter {i}"],
        character_states={},
        unresolved_threads=[],
    ) for i in range(1, 6)]  # 5 chapters
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        prior_chapters=prior,
    )
    prompt = ctx.to_prompt_string()
    # Should only include last 3 (chapters 3, 4, 5)
    assert "Chapter 3" in prompt
    assert "Chapter 4" in prompt
    assert "Chapter 5" in prompt
    assert "Chapter 1" not in prompt
    assert "Chapter 2" not in prompt


def test_assemble_context_preserves_prior_chapters_with_no_characters():
    """prior_chapters should be preserved even when no characters exist (early return path)."""
    repo = FakeRepository()
    service = SceneContextService(repository=repo)
    prior = [PriorChapterSummary(
        chapter_id="ch-001",
        title="The Departure",
        key_events=["Kael leaves"],
        character_states={},
        unresolved_threads=["Where next?"],
    )]
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=[],
        prior_chapters=prior,
    )
    assert len(ctx.prior_chapters) == 1
    assert ctx.prior_chapters[0].title == "The Departure"
