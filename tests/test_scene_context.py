from __future__ import annotations

import pytest
from app.schemas.story_development import CharacterProfile
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
