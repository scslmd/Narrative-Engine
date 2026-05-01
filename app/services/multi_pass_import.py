from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
import time
from typing import Any, Callable

from pydantic import ValidationError

from ..inference.base import InferenceBackend, InferenceBackendError
from ..schemas.inference import InferenceRequest
from ..schemas.story_import import (
    ChapterAnalysisResult,
    ChapterBoundary,
    CharacterMention,
    PlotEvent,
    StoryImportAnalysis,
    StoryImportArc,
    StoryImportChapterSummary,
    StoryImportCharacterRequest,
    StoryImportPlanningSynthesis,
    StoryImportSequence,
    StoryImportWorldEntry,
    StoryStructureDetection,
    StructureHint,
    WorldDetail,
)
from ..utils.json_extract import extract_json

logger = logging.getLogger(__name__)

# Chunking parameters
MAX_CHUNK_SIZE = 20_000
CHUNK_OVERLAP = 1_000
STRUCTURE_SCAN_LIMIT = 40_000
PRIOR_CHAR_CONTEXT_CAP = 5_000
MULTI_PASS_THRESHOLD = 30_000


@dataclass
class CharacterAccumulator:
    """In-memory accumulator for character data across chapters."""
    name: str
    aliases: list[str] = field(default_factory=list)
    role: str = "supporting"
    first_introduction_chapter: str = ""
    chapter_appearances: list[str] = field(default_factory=list)

    # Accumulated data (deduplicated during consolidation)
    physical_descriptions: list[str] = field(default_factory=list)
    personality_traits: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    dialogue_samples: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    emotional_states: list[str] = field(default_factory=list)
    motives: list[str] = field(default_factory=list)
    development_notes: list[str] = field(default_factory=list)

    # From single-pass fields
    archetype: str = "unknown"
    external_goal: str = ""
    internal_need: str = ""
    core_fear: str = ""
    primary_strength: str = ""
    fatal_flaw: str = ""
    backstory: str = ""
    voice_notes: str = ""
    change_axis: str = ""
    contradictions: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    taboos: list[str] = field(default_factory=list)
    continuity_facts: list[str] = field(default_factory=list)


class MultiPassImportService:
    """Multi-pass story analysis for stories larger than MULTI_PASS_THRESHOLD chars.

    Phase 1: Detect story structure (TOC, chapters, sections)
    Phase 2: Process each chapter/chunk with incremental character tracking
    Phase 3a: Consolidate characters into comprehensive profiles
    Phase 3b: Consolidate world bible entries
    Phase 3c: Detect and classify overall narrative arcs
    """

    def __init__(
        self,
        inferencer: InferenceBackend,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self._inferencer = inferencer
        self._sleep = sleep_fn or time.sleep

    def _retry_with_backoff(
        self,
        func: Callable[..., Any],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> Any:
        """Call func with exponential backoff on LLM/transient errors."""
        if kwargs is None:
            kwargs = {}
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (InferenceBackendError, ValueError, ValidationError) as exc:
                if attempt == max_retries:
                    raise
                wait = min(0.5 * (2 ** attempt), 5.0)
                logger.warning(
                    "Retry %d/%d after %.1fs: %s",
                    attempt + 1, max_retries, wait, exc,
                )
                self._sleep(wait)
        raise RuntimeError("Retry loop exited unexpectedly")

    def analyze_large_story(
        self,
        story_text: str,
        genre_hint: str | None = None,
        tone_hint: str | None = None,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> StoryImportAnalysis:
        """Multi-pass analysis for stories of any size.

        Returns a consolidated StoryImportAnalysis with comprehensive
        character data, world bible, arcs, and sequences.
        """
        # Phase 1: Detect structure
        structure = self._detect_structure(story_text)
        total_chapters = len(structure.chapters) if structure.chapters else 1
        if on_progress:
            on_progress("structure_detection", {
                "chapters_processed": 0,
                "total_estimated_chapters": total_chapters,
            })

        if not structure.chapters:
            # Fallback: single chunk covering full text
            structure = self._fallback_structure(story_text)
            total_chapters = 1

        # Phase 2: Pre-split chapters into chunks (once, not twice)
        character_map: dict[str, CharacterAccumulator] = {}
        all_world_details: list[WorldDetail] = []
        all_plot_events: list[PlotEvent] = []
        chapter_summaries: list[StoryImportChapterSummary] = []
        chapters_processed = 0
        chunks_processed = 0

        chapter_chunks: list[tuple[ChapterBoundary, list[str]]] = []
        for chapter in structure.chapters:
            text_chunk = story_text[chapter.start_pos:chapter.end_pos]
            if not text_chunk.strip():
                continue
            chapter_chunks.append((chapter, self._split_into_chunks(text_chunk)))

        total_chunks = sum(len(chunks) for _, chunks in chapter_chunks)

        for chapter, chunks in chapter_chunks:
            known_chars_json = self._build_prior_character_context(character_map)
            chapter_results: list[ChapterAnalysisResult] = []

            for chunk_text in chunks:
                try:
                    result = self._analyze_chunk(
                        chunk_text,
                        chapter.id,
                        chapter.title,
                        known_chars_json,
                    )
                    self._update_character_map(character_map, result, chapter.id)
                    all_world_details.extend(result.world_details or [])
                    all_plot_events.extend(result.plot_events or [])
                    chapter_results.append(result)
                except (InferenceBackendError, ValueError, ValidationError) as exc:
                    logger.warning(
                        "Failed to analyze chunk %s: %s. Skipping.",
                        chapter.id,
                        exc,
                    )
                finally:
                    chunks_processed += 1
                    if on_progress:
                        on_progress("chapter_analysis", {
                            "chapters_processed": chapters_processed,
                            "total_estimated_chapters": total_chapters,
                            "chunks_processed": chunks_processed,
                            "total_estimated_chunks": total_chunks,
                        })

                # Refresh prior context after each successful chunk
                known_chars_json = self._build_prior_character_context(character_map)

            chapters_processed += 1
            chapter_summaries.append(self._build_chapter_summary(chapter, chapter_results, len(chunks)))
            if on_progress:
                on_progress("chapter_complete", {
                    "chapters_processed": chapters_processed,
                    "total_estimated_chapters": total_chapters,
                    "chunks_processed": chunks_processed,
                    "total_estimated_chunks": total_chunks,
                })

        # Phase 3a: Consolidate characters
        consolidated_characters = self._consolidate_characters(
            character_map,
            genre_hint,
            tone_hint,
        )
        if on_progress:
            on_progress("consolidation_characters", {
                "chapters_processed": chapters_processed,
                "total_estimated_chapters": total_chapters,
                "chunks_processed": chunks_processed,
                "total_estimated_chunks": total_chunks,
            })

        # Phase 3b: Consolidate world bible
        consolidated_world = self._consolidate_world_bible(all_world_details)
        if on_progress:
            on_progress("consolidation_world", {
                "chapters_processed": chapters_processed,
                "total_estimated_chapters": total_chapters,
                "chunks_processed": chunks_processed,
                "total_estimated_chunks": total_chunks,
            })

        # Phase 3c: Detect arcs
        arc_analysis = self._detect_arcs(
            all_plot_events,
            consolidated_characters,
            structure,
            genre_hint,
            tone_hint,
        )
        if on_progress:
            on_progress("consolidation_arcs", {
                "chapters_processed": chapters_processed,
                "total_estimated_chapters": total_chapters,
                "chunks_processed": chunks_processed,
                "total_estimated_chunks": total_chunks,
            })

        planning_synthesis = self._synthesize_planning(
            structure=structure,
            chapter_summaries=chapter_summaries,
            story_arcs=arc_analysis.get("story_arcs", []),
            characters=consolidated_characters,
        )
        if on_progress:
            on_progress("consolidation_planning", {
                "chapters_processed": chapters_processed,
                "total_estimated_chapters": total_chapters,
                "chunks_processed": chunks_processed,
                "total_estimated_chunks": total_chunks,
            })

        # Build final StoryImportAnalysis
        return self._build_analysis(
            characters=consolidated_characters,
            world_bible=consolidated_world,
            arc_analysis=arc_analysis,
            planning_synthesis=planning_synthesis,
            structure=structure,
            genre_hint=genre_hint,
            tone_hint=tone_hint,
            completed_chunk_count=chunks_processed,
            total_estimated_chunks=total_chunks,
        )

    def _detect_structure(self, story_text: str) -> StoryStructureDetection:
        """Phase 1: Detect story structure from text."""
        try:
            from .runtime_prompts import build_structure_detection_request

            inference_request = build_structure_detection_request(
                story_text=story_text,
                default_model=self._inferencer.descriptor.default_model,
            )

            response = self._inferencer.generate_text(inference_request)
            parsed = extract_json(response.content)
            if parsed is None:
                raise ValueError("Failed to parse structure detection response")

            return StoryStructureDetection.model_validate(parsed)
        except (InferenceBackendError, ValueError, ValidationError) as exc:
            logger.warning("Structure detection failed, using fallback: %s", exc)
            return self._fallback_structure(story_text)

    def _fallback_structure(self, story_text: str) -> StoryStructureDetection:
        """Fallback when structure detection fails: fixed-size chunks."""
        total_chars = len(story_text)
        word_count = len(story_text.split())
        chapters: list[ChapterBoundary] = []

        chunk_idx = 0
        pos = 0
        while pos < total_chars:
            end = min(pos + MAX_CHUNK_SIZE, total_chars)
            # Try to break at chapter/paragraph boundary
            if end < total_chars:
                next_break = story_text.find("\n\n", pos + 2000)
                if next_break > pos + 2000 and next_break < end:
                    end = next_break

            line_start = story_text[:pos].count("\n") + 1
            line_end = story_text[:end].count("\n") + 1

            chapters.append(ChapterBoundary(
                id=f"chunk-{chunk_idx + 1}",
                title=f"Chunk {chunk_idx + 1}",
                section_type="chapter",
                start_line=line_start,
                end_line=line_end,
                start_pos=pos,
                end_pos=end,
                estimated_word_count=len(story_text[pos:end].split()),
            ))

            # Move forward with overlap
            if end >= total_chars:
                break  # Reached end of text
            pos = max(end - CHUNK_OVERLAP, pos + 1)
            chunk_idx += 1

        if not chapters:
            chapters.append(ChapterBoundary(
                id="chunk-1",
                title="Full Text",
                section_type="chapter",
                start_line=1,
                end_line=story_text.count("\n") + 1,
                start_pos=0,
                end_pos=total_chars,
                estimated_word_count=word_count,
            ))

        return StoryStructureDetection(
            project_name="Untitled Story",
            total_estimated_words=word_count,
            structure_type="short_story",
            chapters=chapters,
            hints=StructureHint(),
        )

    def _analyze_chunk(
        self,
        chunk_text: str,
        chapter_id: str,
        chapter_title: str,
        known_characters_json: str | None,
    ) -> ChapterAnalysisResult:
        """Phase 2: Analyze a single chapter/chunk."""
        from .runtime_prompts import build_chunk_analysis_request

        inference_request = build_chunk_analysis_request(
            chapter_text=chunk_text,
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            known_characters_json=known_characters_json,
            default_model=self._inferencer.descriptor.default_model,
        )

        response = self._inferencer.generate_text(inference_request)
        parsed = extract_json(response.content)
        if parsed is None:
            raise ValueError("Failed to parse chapter analysis response")

        return ChapterAnalysisResult.model_validate(parsed)

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split large text into manageable chunks with overlap."""
        if len(text) <= MAX_CHUNK_SIZE:
            return [text]

        chunks: list[str] = []
        pos = 0
        while pos < len(text):
            end = min(pos + MAX_CHUNK_SIZE, len(text))

            # Try to break at paragraph boundary
            if end < len(text):
                next_break = text.rfind("\n\n", pos + 1000, end)
                if next_break > pos + 1000:
                    end = next_break

            chunks.append(text[pos:end])
            pos = max(end - CHUNK_OVERLAP, pos + 1)

        return chunks

    def _build_prior_character_context(
        self,
        character_map: dict[str, CharacterAccumulator],
    ) -> str | None:
        """Build JSON summary of known characters for prior context."""
        if not character_map:
            return None

        chars_summary: list[dict[str, Any]] = []
        for key, acc in sorted(character_map.items()):
            chars_summary.append({
                "name": acc.name,
                "aliases": acc.aliases,
                "role": acc.role,
                "first_appearance": acc.first_introduction_chapter,
                "traits": acc.personality_traits[:5],
            })

        result = json.dumps(chars_summary, ensure_ascii=True, indent=2)

        # Truncate if too long
        if len(result) > PRIOR_CHAR_CONTEXT_CAP:
            # Keep most recent/fewest characters
            while len(result) > PRIOR_CHAR_CONTEXT_CAP and len(chars_summary) > 3:
                chars_summary.pop(0)
                result = json.dumps(chars_summary, ensure_ascii=True, indent=2)

        return result

    def _update_character_map(
        self,
        character_map: dict[str, CharacterAccumulator],
        result: ChapterAnalysisResult,
        chapter_id: str,
    ) -> None:
        """Merge chapter analysis results into the character accumulator map."""
        for mention in result.characters or []:
            canonical_name = self._find_or_create_name(character_map, mention)

            acc = character_map[canonical_name]

            # Update role if this is a more significant role
            role_priority = {
                "protagonist": 6, "antagonist": 5, "mentor": 4,
                "deuteragonist": 3, "foil": 2, "supporting": 1, "minor": 0,
            }
            if role_priority.get(mention.role, 0) > role_priority.get(acc.role, 0):
                acc.role = mention.role

            # Track first introduction
            if mention.is_first_introduction and not acc.first_introduction_chapter:
                acc.first_introduction_chapter = chapter_id

            # Track appearances
            if chapter_id not in acc.chapter_appearances:
                acc.chapter_appearances.append(chapter_id)

            # Merge aliases
            for alias in mention.aliases or []:
                existing_aliases = {a.lower() for a in acc.aliases}
                if alias.lower() not in existing_aliases:
                    if alias.lower() != canonical_name.lower():
                        acc.aliases.append(alias)

            # Accumulate data
            if mention.physical_description and mention.physical_description.strip():
                desc = mention.physical_description.strip()
                if desc not in acc.physical_descriptions:
                    acc.physical_descriptions.append(desc)

            for trait in mention.personality_traits or []:
                if trait.lower() not in {t.lower() for t in acc.personality_traits}:
                    acc.personality_traits.append(trait)

            for action in mention.actions_in_chunk or []:
                acc.actions.append(action)

            for sample in mention.dialogue_samples or []:
                if len(acc.dialogue_samples) < 6:
                    acc.dialogue_samples.append(sample)

            for rel in mention.relationships_mentioned or []:
                if rel not in acc.relationships:
                    acc.relationships.append(rel)

            if mention.emotional_state and mention.emotional_state.strip():
                acc.emotional_states.append(mention.emotional_state.strip())

            if mention.motives_observed and mention.motives_observed.strip():
                motive = mention.motives_observed.strip()
                if motive not in acc.motives:
                    acc.motives.append(motive)

            if mention.development_notes and mention.development_notes.strip():
                note = mention.development_notes.strip()
                if note not in acc.development_notes:
                    acc.development_notes.append(note)

    def _find_or_create_name(
        self,
        character_map: dict[str, CharacterAccumulator],
        mention: CharacterMention,
    ) -> str:
        """Find existing character by name/alias, or create new entry."""
        mention_lower = mention.name.lower()

        # Check if this name already exists (case-insensitive)
        for key, acc in character_map.items():
            if key.lower() == mention_lower:
                return key
            if mention_lower in {a.lower() for a in acc.aliases}:
                return key

        # Check if any alias matches an existing character
        for alias in mention.aliases or []:
            alias_lower = alias.lower()
            for key, acc in character_map.items():
                if key.lower() == alias_lower:
                    # Add new name as alias to existing entry
                    if mention.name.lower() not in {a.lower() for a in acc.aliases}:
                        acc.aliases.append(mention.name)
                    return key
                if alias_lower in {a.lower() for a in acc.aliases}:
                    return key

        # New character — create entry
        canonical = mention.name
        character_map[canonical] = CharacterAccumulator(
            name=canonical,
            aliases=[a for a in (mention.aliases or []) if a.lower() != canonical.lower()],
            role=mention.role,
        )
        return canonical

    def _consolidate_characters(
        self,
        character_map: dict[str, CharacterAccumulator],
        genre_hint: str | None,
        tone_hint: str | None,
    ) -> list[StoryImportCharacterRequest]:
        """Phase 3a: LLM consolidation of character data into comprehensive profiles."""
        if not character_map:
            return []

        from .runtime_prompts import build_character_consolidation_request

        # Build JSON input for consolidation
        char_data_list: list[dict[str, Any]] = []
        for acc in sorted(character_map.values(), key=lambda a: a.name):
            char_data_list.append({
                "name": acc.name,
                "aliases": acc.aliases,
                "role": acc.role,
                "first_introduction_chapter": acc.first_introduction_chapter,
                "chapter_appearances": acc.chapter_appearances,
                "physical_descriptions": acc.physical_descriptions,
                "personality_traits": acc.personality_traits,
                "actions": acc.actions,
                "dialogue_samples": acc.dialogue_samples,
                "relationships": acc.relationships,
                "emotional_states": acc.emotional_states,
                "motives": acc.motives,
                "development_notes": acc.development_notes,
            })

        char_data_json = json.dumps(char_data_list, ensure_ascii=True, indent=2)

        try:
            inference_request = build_character_consolidation_request(
                character_data_json=char_data_json,
                story_premise=None,
                thematic_spine=None,
                genre_hint=genre_hint,
                tone_hint=tone_hint,
                default_model=self._inferencer.descriptor.default_model,
            )

            response = self._retry_with_backoff(
                self._inferencer.generate_text, (inference_request,), {}, max_retries=2
            )
            parsed = extract_json(response.content)

            if parsed and isinstance(parsed, list):
                return [
                    StoryImportCharacterRequest.model_validate(c)
                    for c in parsed if isinstance(c, dict)
                ]
        except (InferenceBackendError, ValidationError) as exc:
            logger.warning("Character consolidation failed: %s. Using raw data.", exc)

        # Fallback: build profiles from raw accumulator data
        return self._build_fallback_characters(character_map)

    def _build_fallback_characters(
        self,
        character_map: dict[str, CharacterAccumulator],
    ) -> list[StoryImportCharacterRequest]:
        """Fallback character profiles when LLM consolidation fails."""
        result: list[StoryImportCharacterRequest] = []
        for acc in sorted(character_map.values(), key=lambda a: a.name):
            result.append(StoryImportCharacterRequest(
                name=acc.name,
                role=acc.role,
                archetype=acc.archetype,
                aliases=acc.aliases,
                physical_description="; ".join(acc.physical_descriptions[:3]),
                personality_traits=acc.personality_traits,
                motives=". ".join(acc.motives),
                relationships=acc.relationships,
                character_arc=". ".join(acc.development_notes),
                first_appearance_chapter=acc.first_introduction_chapter,
                chapter_appearances=acc.chapter_appearances,
            ))
        return result

    def _consolidate_world_bible(
        self,
        world_details: list[WorldDetail],
    ) -> list[StoryImportWorldEntry]:
        """Phase 3b: LLM consolidation of world details."""
        if not world_details:
            return []

        from .runtime_prompts import build_world_bible_consolidation_request

        world_json = json.dumps([
            w.model_dump(mode="json", exclude_defaults=True)
            for w in world_details
        ], ensure_ascii=True, indent=2)

        try:
            inference_request = build_world_bible_consolidation_request(
                world_details_json=world_json,
                default_model=self._inferencer.descriptor.default_model,
            )

            response = self._retry_with_backoff(
                self._inferencer.generate_text, (inference_request,), {}, max_retries=2
            )
            parsed = extract_json(response.content)

            if parsed and isinstance(parsed, list):
                return [
                    StoryImportWorldEntry.model_validate(e)
                    for e in parsed if isinstance(e, dict)
                ]
        except (InferenceBackendError, ValidationError) as exc:
            logger.warning("World bible consolidation failed: %s. Using raw data.", exc)

        # Fallback: deduplicate by (type, title) and merge
        return self._build_fallback_world_bible(world_details)

    def _build_fallback_world_bible(
        self,
        world_details: list[WorldDetail],
    ) -> list[StoryImportWorldEntry]:
        """Fallback world bible when LLM consolidation fails."""
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for detail in world_details:
            key = (detail.entry_type.lower(), detail.title.lower())
            if key in merged:
                entry = merged[key]
                desc = detail.description or ""
                if desc and desc not in entry["summary"]:
                    entry["summary"] = f"{entry['summary']} {desc}".strip()
                for fact in detail.canonical_facts or []:
                    if fact not in entry["canonical_facts"]:
                        entry["canonical_facts"].append(fact)
            else:
                merged[key] = {
                    "entry_type": detail.entry_type,
                    "title": detail.title,
                    "summary": detail.description or "",
                    "canonical_facts": list(detail.canonical_facts or []),
                    "related_character_ids": [],
                }
        return [
            StoryImportWorldEntry.model_validate(d) for d in merged.values()
        ]

    def _detect_arcs(
        self,
        plot_events: list[PlotEvent],
        characters: list[StoryImportCharacterRequest],
        structure: StoryStructureDetection,
        genre_hint: str | None,
        tone_hint: str | None,
    ) -> dict[str, Any]:
        """Phase 3c: LLM arc detection and classification."""
        from .runtime_prompts import build_arc_detection_request

        events_json = json.dumps([
            e.model_dump(mode="json", exclude_defaults=True)
            for e in plot_events
        ], ensure_ascii=True, indent=2)

        char_arcs_json = None
        if characters:
            arcs_data = [
                {
                    "name": c.name,
                    "role": c.role,
                    "character_arc": c.character_arc or "",
                    "development": c.change_axis or "",
                }
                for c in characters
            ]
            char_arcs_json = json.dumps(arcs_data, ensure_ascii=True, indent=2)

        # Build premise from structure hints
        premise = None
        if structure.hints and structure.hints.thematic_keywords:
            premise = f"Story with themes: {', '.join(structure.hints.thematic_keywords[:5])}"

        try:
            inference_request = build_arc_detection_request(
                plot_events_json=events_json,
                character_arcs_json=char_arcs_json,
                story_premise=premise,
                default_model=self._inferencer.descriptor.default_model,
            )

            response = self._retry_with_backoff(
                self._inferencer.generate_text, (inference_request,), {}, max_retries=2
            )
            parsed = extract_json(response.content)

            if parsed and isinstance(parsed, dict):
                return parsed
        except (InferenceBackendError, ValidationError) as exc:
            logger.warning("Arc detection failed: %s. Using fallback.", exc)

        # Fallback: build basic arcs from plot events
        return self._build_fallback_arcs(plot_events, characters, structure)

    def _build_fallback_arcs(
        self,
        plot_events: list[PlotEvent],
        characters: list[StoryImportCharacterRequest],
        structure: StoryStructureDetection,
    ) -> dict[str, Any]:
        """Fallback arc data when LLM detection fails."""
        main_chars = [c for c in characters if c.role in ("protagonist", "antagonist")]

        arcs: list[dict] = []
        if main_chars:
            for char in main_chars[:3]:
                arcs.append({
                    "name": f"{char.name}'s Journey",
                    "summary": char.character_arc or f"The story of {char.name}.",
                    "stage_map": [
                        "status_quo", "inciting_incident", "rising_action",
                        "crisis", "climax", "resolution",
                    ],
                    "tags": [char.role],
                })

        return {
            "project_name": structure.project_name,
            "premise": "Story imported via multi-pass analysis",
            "logline": "",
            "thematic_spine": ", ".join(structure.hints.thematic_keywords) if structure.hints.thematic_keywords else "",
            "emotional_promise": "",
            "target_audience": "",
            "complexity_level": "MEDIUM",
            "story_structure": "THREE_ACT",
            "genre": "Fiction",
            "tone": "Dramatic",
            "pov": "THIRD_LIMITED",
            "story_arcs": arcs,
            "sequences": [],
            "narrative_constraints": [],
            "success_definition": "",
        }

    def _build_analysis(
        self,
        characters: list[StoryImportCharacterRequest],
        world_bible: list[StoryImportWorldEntry],
        arc_analysis: dict[str, Any],
        planning_synthesis: StoryImportPlanningSynthesis,
        structure: StoryStructureDetection,
        genre_hint: str | None,
        tone_hint: str | None,
        completed_chunk_count: int = 0,
        total_estimated_chunks: int = 0,
    ) -> StoryImportAnalysis:
        """Assemble final StoryImportAnalysis from all phases."""
        # Map story arcs
        story_arcs: list[StoryImportArc] = []
        for arc_data in arc_analysis.get("story_arcs", []):
            try:
                story_arcs.append(StoryImportArc.model_validate(arc_data))
            except ValidationError:
                continue

        sequences = planning_synthesis.sequences or self._build_sequences_from_structure(
            structure,
            planning_synthesis.chapter_summaries,
        )
        chapter_summaries = planning_synthesis.chapter_summaries

        return StoryImportAnalysis(
            project_name=structure.project_name or "Untitled Story",
            genre=arc_analysis.get("genre", genre_hint or "Fiction"),
            tone=arc_analysis.get("tone", tone_hint or "Dramatic"),
            pov=arc_analysis.get("pov", "THIRD_LIMITED"),
            story_structure=arc_analysis.get("story_structure", "THREE_ACT"),
            premise=arc_analysis.get("premise", "Story imported via multi-pass analysis"),
            logline=arc_analysis.get("logline", ""),
            thematic_spine=arc_analysis.get("thematic_spine", ""),
            emotional_promise=arc_analysis.get("emotional_promise", ""),
            target_audience=arc_analysis.get("target_audience", ""),
            complexity_level=arc_analysis.get("complexity_level", "MEDIUM"),
            characters=characters,
            world_bible=world_bible,
            story_arcs=story_arcs,
            sequences=sequences,
            chapter_summaries=chapter_summaries,
            narrative_constraints=arc_analysis.get("narrative_constraints", []),
            success_definition=arc_analysis.get("success_definition", ""),
            completed_chunk_count=completed_chunk_count,
            total_estimated_chunks=total_estimated_chunks,
        )

    def _synthesize_planning(
        self,
        *,
        structure: StoryStructureDetection,
        chapter_summaries: list[StoryImportChapterSummary],
        story_arcs: list[dict[str, Any]],
        characters: list[StoryImportCharacterRequest],
    ) -> StoryImportPlanningSynthesis:
        """Phase 3d: synthesize planning-grade sequences and chapter summaries from analyzed chapters."""
        if not chapter_summaries:
            return StoryImportPlanningSynthesis(sequences=[], chapter_summaries=[])

        from .runtime_prompts import build_planning_consolidation_request

        fallback = StoryImportPlanningSynthesis(
            sequences=self._build_sequences_from_structure(structure, chapter_summaries),
            chapter_summaries=[self._with_planning_metadata(chapter) for chapter in chapter_summaries],
        )

        structure_json = json.dumps(
            structure.model_dump(mode="json", exclude_defaults=True),
            ensure_ascii=True,
            indent=2,
        )
        chapter_summaries_json = json.dumps(
            [chapter.model_dump(mode="json", exclude_defaults=True) for chapter in chapter_summaries],
            ensure_ascii=True,
            indent=2,
        )
        story_arcs_json = json.dumps(story_arcs, ensure_ascii=True, indent=2)
        character_roster_json = json.dumps(
            [
                {
                    "name": character.name,
                    "role": character.role,
                    "character_arc": character.character_arc,
                    "relationships": character.relationships,
                }
                for character in characters
            ],
            ensure_ascii=True,
            indent=2,
        )

        try:
            inference_request = build_planning_consolidation_request(
                structure_json=structure_json,
                chapter_summaries_json=chapter_summaries_json,
                story_arcs_json=story_arcs_json,
                character_roster_json=character_roster_json,
                default_model=self._inferencer.descriptor.default_model,
            )
            response = self._retry_with_backoff(
                self._inferencer.generate_text,
                (inference_request,),
                {},
                max_retries=2,
            )
            parsed = extract_json(response.content)
            if isinstance(parsed, dict):
                synthesized = StoryImportPlanningSynthesis.model_validate(parsed)
                return self._normalize_planning_synthesis(
                    fallback=fallback,
                    synthesized=synthesized,
                )
        except (InferenceBackendError, ValueError, ValidationError) as exc:
            logger.warning("Planning synthesis failed: %s. Using deterministic fallback.", exc)

        return self._normalize_planning_synthesis(fallback=fallback, synthesized=fallback)

    def _normalize_planning_synthesis(
        self,
        *,
        fallback: StoryImportPlanningSynthesis,
        synthesized: StoryImportPlanningSynthesis,
    ) -> StoryImportPlanningSynthesis:
        """Validate and repair synthesized planning before persistence."""
        fallback_by_id = {
            chapter.chapter_id: self._with_planning_metadata(chapter)
            for chapter in fallback.chapter_summaries
        }
        normalized_chapters: list[StoryImportChapterSummary] = []
        seen_ids: set[str] = set()

        for chapter in synthesized.chapter_summaries:
            base = fallback_by_id.get(chapter.chapter_id)
            if base is None or chapter.chapter_id in seen_ids:
                continue
            seen_ids.add(chapter.chapter_id)
            normalized_chapters.append(self._merge_chapter_summary(base, chapter))

        for chapter_id, base in fallback_by_id.items():
            if chapter_id not in seen_ids:
                normalized_chapters.append(base)

        normalized_sequences = self._normalize_sequences(
            synthesized.sequences,
            fallback_sequences=fallback.sequences,
            chapter_summaries=normalized_chapters,
        )
        return StoryImportPlanningSynthesis(
            sequences=normalized_sequences,
            chapter_summaries=normalized_chapters,
        )

    def _merge_chapter_summary(
        self,
        base: StoryImportChapterSummary,
        candidate: StoryImportChapterSummary,
    ) -> StoryImportChapterSummary:
        plot_events = candidate.plot_events or base.plot_events
        merged = StoryImportChapterSummary(
            chapter_id=base.chapter_id,
            title=candidate.title or base.title,
            summary=candidate.summary or base.summary,
            section_type=candidate.section_type or base.section_type,
            analysis_status=base.analysis_status,
            objective=candidate.objective or base.objective,
            conflict=candidate.conflict or base.conflict,
            stakes=candidate.stakes or base.stakes,
            active_character_names=list(dict.fromkeys(candidate.active_character_names or base.active_character_names)),
            continuity_requirements=list(dict.fromkeys(candidate.continuity_requirements or base.continuity_requirements)),
            unresolved_questions=list(dict.fromkeys(candidate.unresolved_questions or base.unresolved_questions)),
            plot_events=plot_events,
            estimated_word_count=candidate.estimated_word_count if candidate.estimated_word_count is not None else base.estimated_word_count,
            provenance_note=candidate.provenance_note or base.provenance_note,
            confidence_score=max(0.0, min(1.0, candidate.confidence_score or base.confidence_score)),
        )
        return self._with_planning_metadata(merged)

    def _normalize_sequences(
        self,
        sequences: list[StoryImportSequence],
        *,
        fallback_sequences: list[StoryImportSequence],
        chapter_summaries: list[StoryImportChapterSummary],
    ) -> list[StoryImportSequence]:
        known_chapter_ids = [chapter.chapter_id for chapter in chapter_summaries]
        remaining = list(known_chapter_ids)
        normalized: list[StoryImportSequence] = []

        for sequence in sequences:
            chapter_ids: list[str] = []
            for chapter_id in sequence.chapters:
                if chapter_id in remaining and chapter_id not in chapter_ids:
                    chapter_ids.append(chapter_id)
                    remaining.remove(chapter_id)
            if not chapter_ids:
                continue
            normalized.append(StoryImportSequence(
                title=sequence.title.strip() or f"Sequence {len(normalized) + 1}",
                summary=sequence.summary.strip() or f"Covers {len(chapter_ids)} chapters",
                chapters=chapter_ids,
                provenance_note=sequence.provenance_note.strip() or "planning synthesis from chapter evidence",
                confidence_score=max(0.0, min(1.0, sequence.confidence_score or 0.7)),
            ))

        if remaining:
            fallback_map = {
                sequence.title: sequence
                for sequence in fallback_sequences
            }
            if normalized:
                normalized.append(StoryImportSequence(
                    title="Unassigned Narrative",
                    summary=f"Covers {len(remaining)} chapters not confidently grouped by planning synthesis",
                    chapters=remaining,
                    provenance_note="deterministic fallback for unassigned chapters",
                    confidence_score=0.4,
                ))
            else:
                return [
                    StoryImportSequence(
                        title=sequence.title,
                        summary=sequence.summary,
                        chapters=[chapter_id for chapter_id in sequence.chapters if chapter_id in known_chapter_ids],
                        provenance_note=sequence.provenance_note or fallback_map.get(sequence.title, sequence).provenance_note,
                        confidence_score=sequence.confidence_score or fallback_map.get(sequence.title, sequence).confidence_score,
                    )
                    for sequence in fallback_sequences
                ]

        return normalized

    def _with_planning_metadata(self, chapter: StoryImportChapterSummary) -> StoryImportChapterSummary:
        """Attach deterministic provenance and confidence based on evidence quality."""
        if chapter.analysis_status == "analysis_failed":
            provenance_note = "no direct chapter evidence; imported as degraded shell"
            confidence_score = 0.0
        elif chapter.analysis_status == "partial_import":
            provenance_note = "partial chapter evidence synthesized across incomplete chunk analysis"
            confidence_score = 0.45 if chapter.plot_events else 0.35
        else:
            evidence_units = len(chapter.plot_events) + len(chapter.active_character_names)
            confidence_score = 0.65 if evidence_units <= 2 else 0.8
            provenance_note = "direct chapter evidence synthesized from multi-pass analysis"

        if chapter.provenance_note.strip():
            provenance_note = chapter.provenance_note.strip()
        if chapter.confidence_score > 0:
            confidence_score = chapter.confidence_score

        return StoryImportChapterSummary(
            chapter_id=chapter.chapter_id,
            title=chapter.title,
            summary=chapter.summary,
            section_type=chapter.section_type,
            analysis_status=chapter.analysis_status,
            objective=chapter.objective,
            conflict=chapter.conflict,
            stakes=chapter.stakes,
            active_character_names=list(chapter.active_character_names),
            continuity_requirements=list(chapter.continuity_requirements),
            unresolved_questions=list(chapter.unresolved_questions),
            plot_events=list(chapter.plot_events),
            estimated_word_count=chapter.estimated_word_count,
            provenance_note=provenance_note,
            confidence_score=max(0.0, min(1.0, confidence_score)),
        )

    def _build_chapter_summary(
        self,
        chapter: ChapterBoundary,
        chapter_results: list[ChapterAnalysisResult],
        expected_chunks: int,
    ) -> StoryImportChapterSummary:
        """Collapse one or more chunk analyses into a chapter-level planning summary."""
        summaries = [result.summary.strip() for result in chapter_results if result.summary.strip()]
        summary = " ".join(dict.fromkeys(summaries))

        key_events: list[str] = []
        unresolved_questions: list[str] = []
        active_character_names: list[str] = []
        thematic_elements: list[str] = []
        significance_labels: list[str] = []
        plot_events: list[PlotEvent] = []

        for result in chapter_results:
            for event in result.key_events or []:
                normalized = event.strip()
                if normalized and normalized not in key_events:
                    key_events.append(normalized)

            for plot_event in result.plot_events or []:
                plot_events.append(plot_event)
                significance = plot_event.significance.strip()
                if significance and significance not in significance_labels:
                    significance_labels.append(significance)
                for thread in plot_event.unresolved_threads or []:
                    normalized = thread.strip()
                    if normalized and normalized not in unresolved_questions:
                        unresolved_questions.append(normalized)

            for mention in result.characters or []:
                normalized = mention.name.strip()
                if normalized and normalized not in active_character_names:
                    active_character_names.append(normalized)

            for theme in result.thematic_elements or []:
                normalized = theme.strip()
                if normalized and normalized not in thematic_elements:
                    thematic_elements.append(normalized)

        successful_results = [
            result
            for result in chapter_results
            if result.summary.strip() or result.key_events or result.characters or result.plot_events
        ]

        if not successful_results:
            analysis_status = "analysis_failed"
        elif len(successful_results) < expected_chunks:
            analysis_status = "partial_import"
        else:
            analysis_status = "complete"

        objective = summary or (key_events[0] if key_events else f"Advance {chapter.title}.")
        conflict = (
            unresolved_questions[0]
            if unresolved_questions
            else (significance_labels[0].replace("_", " ") if significance_labels else "Conflict to refine from imported narrative.")
        )
        stakes = (
            f"Preserve continuity around {', '.join(thematic_elements[:2])}."
            if thematic_elements
            else "Carry forward the imported narrative consequences."
        )

        return StoryImportChapterSummary(
            chapter_id=chapter.id,
            title=chapter.title,
            summary=summary,
            section_type=chapter.section_type,
            analysis_status=analysis_status,
            objective=objective,
            conflict=conflict,
            stakes=stakes,
            active_character_names=active_character_names,
            continuity_requirements=key_events[:8],
            unresolved_questions=unresolved_questions[:8],
            plot_events=plot_events,
            estimated_word_count=chapter.estimated_word_count or None,
            provenance_note="direct chapter evidence synthesized from chunk analysis" if successful_results else "no direct chapter evidence",
            confidence_score=0.75 if analysis_status == "complete" else (0.4 if analysis_status == "partial_import" else 0.0),
        )

    def _build_sequences_from_structure(
        self,
        structure: StoryStructureDetection,
        chapter_summaries: list[StoryImportChapterSummary],
    ) -> list[StoryImportSequence]:
        """Build sequence groupings from detected structure instead of a placeholder shell."""
        if not chapter_summaries:
            return []

        chapter_ids = {chapter.chapter_id for chapter in chapter_summaries}
        sequences: list[StoryImportSequence] = []
        current_title = "Main Narrative"
        current_ids: list[str] = []
        current_titles: list[str] = []

        def flush_current() -> None:
            if not current_ids:
                return
            sequences.append(StoryImportSequence(
                title=current_title,
                summary=f"Covers {', '.join(current_titles[:3])}" if current_titles else f"Story with {len(current_ids)} chapters",
                chapters=list(current_ids),
                provenance_note="detected structure grouping",
                confidence_score=0.55,
            ))

        for chapter in structure.chapters:
            if chapter.section_type == "part":
                flush_current()
                current_title = chapter.title
                current_ids = []
                current_titles = []
                continue

            if chapter.id not in chapter_ids:
                continue

            current_ids.append(chapter.id)
            current_titles.append(chapter.title)

        flush_current()

        if not sequences:
            sequences.append(StoryImportSequence(
                title="Main Narrative",
                summary=f"Story with {len(chapter_summaries)} chapters",
                chapters=[chapter.chapter_id for chapter in chapter_summaries],
                provenance_note="deterministic fallback sequence grouping",
                confidence_score=0.35,
            ))

        return sequences
