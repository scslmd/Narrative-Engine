from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CharacterAnchor:
    character_id: str
    display_name: str
    archetype: str
    voice_notes: str
    external_goal: str
    internal_need: str
    core_fear: str


@dataclass(slots=True)
class WorldConstraint:
    entry_type: str
    title: str
    facts: list[str]


@dataclass(slots=True)
class SceneContext:
    characters: list[CharacterAnchor]
    world_facts: list[WorldConstraint]
