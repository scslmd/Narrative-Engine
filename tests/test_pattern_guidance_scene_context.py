from __future__ import annotations

from app.schemas.pattern_extraction import VoiceProfile
from app.services.scene_context import PatternGuidance, SceneContext, CharacterAnchor, WorldConstraint


def test_pattern_guidance_dataclass_defaults():
    pg = PatternGuidance()
    assert pg.voice_profile is None
    assert pg.world_rules == []
    assert pg.thematic_constraints == []


def test_pattern_guidance_dataclass_with_values():
    pg = PatternGuidance(
        voice_profile=VoiceProfile(narrative_voice="lyrical"),
        world_rules=["Magic has a cost", "No resurrection"],
        thematic_constraints=["Explore grief without melodrama"],
    )
    assert pg.voice_profile.narrative_voice == "lyrical"
    assert len(pg.world_rules) == 2
    assert len(pg.thematic_constraints) == 1


def test_scene_context_with_pattern_guidance():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=PatternGuidance(
            voice_profile=VoiceProfile(narrative_voice="terse"),
            world_rules=["Rule A", "Rule B"],
            thematic_constraints=["Constraint X"],
        ),
    )
    assert ctx.pattern_guidance is not None
    assert ctx.pattern_guidance.voice_profile.narrative_voice == "terse"


def test_scene_context_with_author_prompt():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        author_prompt="Emphasize the protagonist's internal conflict in this chapter.",
    )
    assert ctx.author_prompt == "Emphasize the protagonist's internal conflict in this chapter."


def test_to_prompt_string_includes_pattern_guidance():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=PatternGuidance(
            voice_profile=VoiceProfile(
                narrative_voice="terse",
                sentence_rhythm="staccato",
                descriptive_density="sparse",
            ),
            world_rules=["Magic has a cost", "No resurrection"],
            thematic_constraints=["Explore grief without melodrama"],
        ),
    )
    prompt = ctx.to_prompt_string()
    assert "PATTERN GUIDANCE:" in prompt
    assert "Voice style:" in prompt
    assert "terse" in prompt
    assert "staccato" in prompt
    assert "sparse" in prompt
    assert "World rules:" in prompt
    assert "Magic has a cost" in prompt
    assert "No resurrection" in prompt
    assert "Thematic constraints:" in prompt
    assert "Explore grief without melodrama" in prompt


def test_to_prompt_string_skips_empty_pattern_guidance():
    """Empty PatternGuidance should not render the section."""
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=PatternGuidance(),
    )
    prompt = ctx.to_prompt_string()
    assert "PATTERN GUIDANCE:" not in prompt


def test_to_prompt_string_skips_none_pattern_guidance():
    """None PatternGuidance should not render the section."""
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=None,
    )
    prompt = ctx.to_prompt_string()
    assert "PATTERN GUIDANCE:" not in prompt


def test_to_prompt_string_includes_author_direction():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        author_prompt="Focus on the betrayal scene.",
    )
    prompt = ctx.to_prompt_string()
    assert "AUTHOR DIRECTION:" in prompt
    assert "Focus on the betrayal scene." in prompt


def test_to_prompt_string_skips_none_author_prompt():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        author_prompt=None,
    )
    prompt = ctx.to_prompt_string()
    assert "AUTHOR DIRECTION:" not in prompt


def test_to_prompt_string_sections_appear_after_existing_sections():
    """Pattern guidance and author direction should appear after character/world/prior sections."""
    ctx = SceneContext(
        characters=[CharacterAnchor(
            character_id="c1", display_name="Khal",
            archetype="hero", voice_notes="",
            external_goal="Survive", internal_need="", core_fear="",
        )],
        world_facts=[WorldConstraint(
            entry_type="location", title="The Bazaar",
            facts=["crowded"],
        )],
        pattern_guidance=PatternGuidance(
            voice_profile=VoiceProfile(narrative_voice="lyrical"),
            world_rules=["Rule 1"],
            thematic_constraints=["Constraint 1"],
        ),
        author_prompt="Write with restraint.",
    )
    prompt = ctx.to_prompt_string()
    char_pos = prompt.index("CHARACTER CONTEXT:")
    world_pos = prompt.index("WORLD CONSTRAINTS:")
    pattern_pos = prompt.index("PATTERN GUIDANCE:")
    author_pos = prompt.index("AUTHOR DIRECTION:")
    assert char_pos < world_pos < pattern_pos < author_pos


def test_to_prompt_string_voice_profile_partial_fields():
    """VoiceProfile with only narrative_voice should still render."""
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=PatternGuidance(
            voice_profile=VoiceProfile(narrative_voice="minimalist"),
        ),
    )
    prompt = ctx.to_prompt_string()
    assert "PATTERN GUIDANCE:" in prompt
    assert "minimalist" in prompt


def test_to_prompt_string_pattern_guidance_with_world_rules_only():
    """PatternGuidance with only world_rules should render that section."""
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        pattern_guidance=PatternGuidance(
            world_rules=["No time travel"],
        ),
    )
    prompt = ctx.to_prompt_string()
    assert "PATTERN GUIDANCE:" in prompt
    assert "World rules:" in prompt
    assert "No time travel" in prompt


def test_pattern_guidance_slots():
    """PatternGuidance should use slots for memory efficiency."""
    pg = PatternGuidance()
    assert not hasattr(pg, "__dict__")
