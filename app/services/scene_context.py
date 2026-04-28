from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from ..persistence.story_development import StoryDevelopmentRepository

from ..schemas.pattern_extraction import VoiceProfile
from ..schemas.story_development import PriorChapterSummary

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PatternGuidance:
    voice_profile: VoiceProfile | None = None
    world_rules: list[str] = field(default_factory=list)
    thematic_constraints: list[str] = field(default_factory=list)


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
    prior_chapters: list[PriorChapterSummary] | None = None
    pattern_guidance: PatternGuidance | None = None
    author_prompt: str | None = None

    def to_prompt_string(self) -> str:
        lines = []
        if self.characters:
            lines.append("CHARACTER CONTEXT:")
            for c in self.characters:
                parts = [f"- {c.display_name} [{c.archetype}]"]
                if c.external_goal:
                    parts[-1] += f" — goal: {c.external_goal}"
                if c.internal_need:
                    parts.append(f"  internal need: {c.internal_need}")
                if c.core_fear:
                    parts.append(f"  core fear: {c.core_fear}")
                if c.voice_notes:
                    parts.append(f"  voice: {c.voice_notes}")
                lines.extend(parts)

        if self.world_facts:
            lines.append("")
            lines.append("WORLD CONSTRAINTS:")
            for w in self.world_facts:
                lines.append(f"- {w.title} ({w.entry_type}):")
                for fact in w.facts[:5]:
                    lines.append(f"  * {fact}")

        if self.prior_chapters:
            lines.append("")
            lines.append("PRIOR CHAPTER CONTEXT:")
            for ch in self.prior_chapters[-3:]:
                lines.append(ch.to_context_string())

        if self.pattern_guidance and self._has_pattern_content():
            lines.append("")
            lines.append("PATTERN GUIDANCE:")
            pg = self.pattern_guidance
            if pg.voice_profile:
                vp = pg.voice_profile
                voice_parts = [f"Voice style: {vp.narrative_voice}"]
                if vp.sentence_rhythm:
                    voice_parts.append(f"sentence rhythm: {vp.sentence_rhythm}")
                if vp.descriptive_density:
                    voice_parts.append(f"descriptive density: {vp.descriptive_density}")
                if vp.humor_level:
                    voice_parts.append(f"humor level: {vp.humor_level}")
                if vp.emotional_temperature:
                    voice_parts.append(f"emotional temperature: {vp.emotional_temperature}")
                lines.append(", ".join(voice_parts))
            if pg.world_rules:
                lines.append("World rules:")
                for rule in pg.world_rules:
                    lines.append(f"  - {rule}")
            if pg.thematic_constraints:
                lines.append("Thematic constraints:")
                for tc in pg.thematic_constraints:
                    lines.append(f"  - {tc}")

        if self.author_prompt:
            lines.append("")
            lines.append("AUTHOR DIRECTION:")
            lines.append(self.author_prompt)
            lines.append("Follow the patterns and constraints above while writing.")

        return "\n".join(lines) if lines else ""

    def _has_pattern_content(self) -> bool:
        pg = self.pattern_guidance
        return bool(pg and (pg.voice_profile or pg.world_rules or pg.thematic_constraints))


class SceneContextService:
    MAX_FALLBACK_CHARACTERS = 5

    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self._repository = repository

    def assemble_context(
        self,
        project_id: str,
        active_character_ids: Iterable[str] | None = None,
        prior_chapters: list[PriorChapterSummary] | None = None,
    ) -> SceneContext:
        target_ids = list(active_character_ids) if active_character_ids else None

        if not target_ids:
            all_chars = self._repository.list_character_profiles(project_id)
            target_ids = [c.character_id for c in all_chars[:self.MAX_FALLBACK_CHARACTERS]]
            if not target_ids:
                return SceneContext(characters=[], world_facts=[], prior_chapters=prior_chapters)

        anchors = []
        for cid in target_ids:
            try:
                profile = self._repository.get_character_profile(cid)
                anchors.append(CharacterAnchor(
                    character_id=profile.character_id,
                    display_name=profile.display_name or "",
                    archetype=profile.archetype or "",
                    voice_notes=profile.voice_notes or "",
                    external_goal=profile.external_goal or "",
                    internal_need=profile.internal_need or "",
                    core_fear=profile.core_fear or "",
                ))
            except (KeyError, AttributeError):
                logger.warning("Character profile not found: %s", cid)

        world_entries = self._repository.list_world_bible_entries(project_id)
        world_facts = []
        for entry in world_entries:
            facts = []
            if hasattr(entry, "canonical_facts") and entry.canonical_facts:
                facts = list(entry.canonical_facts)
            world_facts.append(WorldConstraint(
                entry_type=entry.entry_type or "other",
                title=entry.title or "",
                facts=facts,
            ))

        return SceneContext(characters=anchors, world_facts=world_facts, prior_chapters=prior_chapters)
