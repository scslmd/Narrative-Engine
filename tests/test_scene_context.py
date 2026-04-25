from __future__ import annotations

import pytest
from app.services.scene_context import SceneContext, CharacterAnchor, WorldConstraint


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
