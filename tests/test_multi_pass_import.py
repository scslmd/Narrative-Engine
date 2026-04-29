from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.inference import (
    InferenceMessage,
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from app.schemas.projects import ProjectCreateRequest
from app.schemas.story_import import StoryImportRequest, StoryImportResponse
from app.services.multi_pass_import import (
    CHUNK_OVERLAP,
    MAX_CHUNK_SIZE,
    MULTI_PASS_THRESHOLD,
    PRIOR_CHAR_CONTEXT_CAP,
    CharacterAccumulator,
    MultiPassImportService,
)
from app.services.projects import ProjectService
from app.services.story_import import StoryImportService


class MultiPhaseInferenceBackend(InferenceBackend):
    """Returns predetermined responses based on call sequence."""

    def __init__(self, *, responses: list[str], model: str = "multi-phase-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._responses = responses
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Multi-Phase Backend",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["multi-phase"],
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        idx = len(self.requests) - 1
        content = self._responses[idx] if idx < len(self._responses) else "{}"
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
            raw_response={"backend": "fake"},
        )


# --- Helper JSON builders ---

def _make_structure_response(
    chapters: list[dict] | None = None,
    project_name: str = "Test Novel",
) -> str:
    if chapters is None:
        chapters = [
            {
                "id": "prologue",
                "title": "Prologue",
                "section_type": "prologue",
                "start_line": 1,
                "end_line": 50,
                "start_pos": 0,
                "end_pos": 2000,
                "estimated_word_count": 400,
            },
            {
                "id": "chapter-1",
                "title": "The Beginning",
                "section_type": "chapter",
                "start_line": 51,
                "end_line": 200,
                "start_pos": 2000,
                "end_pos": 10000,
                "estimated_word_count": 1500,
            },
        ]
    return json.dumps({
        "project_name": project_name,
        "total_estimated_words": sum(c.get("estimated_word_count", 0) for c in chapters),
        "structure_type": "traditional_novel",
        "chapters": chapters,
        "hints": {
            "character_names": ["Kvothe"],
            "location_names": ["University"],
            "pov_hints": [],
            "thematic_keywords": ["power", "knowledge"],
        },
        "narrative_voice": "First-person retrospective",
    })


def _make_chunk_analysis_response(
    chapter_id: str = "chapter-1",
    chapter_title: str = "The Beginning",
    characters: list[dict] | None = None,
) -> str:
    if characters is None:
        characters = [
            {
                "name": "Kvothe",
                "aliases": [],
                "role": "protagonist",
                "is_first_introduction": True,
                "physical_description": "Red-haired, lean youth",
                "personality_traits": ["proud", "intelligent"],
                "actions_in_chunk": ["arrives at the University"],
                "dialogue_samples": ["I am Kvothe"],
                "relationships_mentioned": [],
                "emotional_state": "Eager, ambitious",
                "motives_observed": "Wants to become famous",
                "development_notes": None,
            }
        ]
    return json.dumps({
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "section_type": "chapter",
        "summary": f"Summary of {chapter_title}",
        "key_events": ["Event 1"],
        "characters": characters,
        "world_details": [
            {
                "entry_type": "location",
                "title": "University",
                "description": "A place of learning",
                "canonical_facts": ["has three colleges"],
            }
        ],
        "plot_events": [
            {
                "summary": "Protagonist arrives",
                "characters_involved": ["Kvothe"],
                "significance": "inciting_incident",
                "unresolved_threads": [],
            }
        ],
        "thematic_elements": ["ambition"],
        "tone_shifts": None,
        "narrative_perspective": None,
    })


def _make_character_consolidation_response(
    characters: list[dict] | None = None,
) -> str:
    if characters is None:
        characters = [
            {
                "name": "Kvothe",
                "aliases": [],
                "role": "protagonist",
                "archetype": "hero",
                "external_goal": "Become famous",
                "internal_need": "Find belonging",
                "core_fear": "Being forgotten",
                "primary_strength": "Intelligence",
                "fatal_flaw": "Pride",
                "backstory": "Orphaned child prodigy",
                "voice_notes": "Poetic, confident",
                "change_axis": "From naive to experienced",
                "contradictions": [],
                "secrets": [],
                "values": ["honor"],
                "taboos": [],
                "continuity_facts": [],
                "physical_description": "Red-haired, lean",
                "personality_traits": ["proud", "intelligent"],
                "motives": "Desire for fame and recognition",
                "relationships": [],
                "character_arc": "Grows from naive youth to seasoned survivor",
                "symbolic_role": "The prodigy",
                "dialogue_patterns": "Poetic and confident speech",
                "psychological_depth": "Driven by need for recognition",
                "narrative_purpose": "Central protagonist",
                "thematic_significance": "Represents ambition vs. humility",
                "impact_on_others": "Inspires and intimidates peers",
                "first_appearance_chapter": "prologue",
                "chapter_appearances": ["prologue", "chapter-1"],
            }
        ]
    return json.dumps(characters)


def _make_arc_detection_response() -> str:
    return json.dumps({
        "premise": "A young prodigy seeks fame and power",
        "logline": "One boy's journey to legend",
        "thematic_spine": "Power, knowledge, and their costs",
        "emotional_promise": "Satisfying character growth",
        "target_audience": "Young adults",
        "complexity_level": "HIGH",
        "story_structure": "HERO_JOURNEY",
        "genre": "Fantasy",
        "tone": "Epic and introspective",
        "pov": "FIRST",
        "story_arcs": [
            {
                "name": "The Prodigy's Journey",
                "summary": "From orphan to legend",
                "stage_map": [
                    "status_quo", "inciting_incident", "rising_action",
                    "crisis", "climax", "resolution",
                ],
                "tags": ["character", "coming_of_age"],
            }
        ],
        "sequences": [],
        "narrative_constraints": [],
        "success_definition": "Satisfying character arc",
    })


# --- Phase 1: Structure Detection Tests ---

class TestStructureDetection:
    """Test Phase 1: story structure detection."""

    def test_detect_structure_parses_llm_response(self) -> None:
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[_make_structure_response()])
        )
        result = service._detect_structure("Chapter 1: The Beginning\n\nSome text...")
        assert result.project_name == "Test Novel"
        assert result.structure_type == "traditional_novel"
        assert len(result.chapters) == 2
        assert result.chapters[0].id == "prologue"
        assert result.chapters[1].id == "chapter-1"
        assert result.hints.character_names == ["Kvothe"]

    def test_detect_structure_calls_llm_with_correct_params(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[_make_structure_response()])
        service = MultiPassImportService(backend)
        service._detect_structure("Some story text...")
        assert len(backend.requests) == 1
        req = backend.requests[0]
        assert req.temperature == 0.1
        assert req.max_tokens == 8000
        assert req.metadata["phase"] == "structure_detection"

    def test_detect_structure_truncates_long_text(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[_make_structure_response()])
        service = MultiPassImportService(backend)
        long_text = "A" * 100_000
        service._detect_structure(long_text)
        req = backend.requests[0]
        user_content = req.messages[1].content
        # Structure scan limit is 40,000 chars
        assert len(user_content) < 50_000

    def test_detect_structure_invalid_json_falls_back(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=["not valid json"])
        service = MultiPassImportService(backend)
        result = service._detect_structure("Some text...")
        # Should fall back to chunk-based structure, not raise
        assert result is not None
        assert len(result.chapters) >= 1


class TestFallbackStructure:
    """Test fallback structure generation when detection fails."""

    def test_fallback_creates_fixed_size_chunks(self) -> None:
        story_text = "A" * 50_000
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        result = service._fallback_structure(story_text)
        assert result.structure_type == "short_story"
        assert len(result.chapters) >= 2  # 50k chars > MAX_CHUNK_SIZE
        total_covered = sum(
            ch.end_pos - ch.start_pos for ch in result.chapters
        )
        assert total_covered >= len(story_text)

    def test_fallback_single_chunk_for_short_text(self) -> None:
        short_text = "A short story."
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        result = service._fallback_structure(short_text)
        assert len(result.chapters) == 1
        assert result.chapters[0].start_pos == 0
        assert result.chapters[0].end_pos == len(short_text)

    def test_fallback_chapters_have_valid_bounds(self) -> None:
        story_text = "A" * 60_000
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        result = service._fallback_structure(story_text)
        for ch in result.chapters:
            assert ch.end_pos > ch.start_pos
            assert ch.start_line >= 1
            assert ch.end_line >= ch.start_line


# --- Phase 2: Chunk Analysis Tests ---

class TestChunkSplitting:
    """Test _split_into_chunks for large text."""

    def test_small_text_returns_single_chunk(self) -> None:
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        small = "A" * 10_000
        chunks = service._split_into_chunks(small)
        assert len(chunks) == 1
        assert chunks[0] == small

    def test_large_text_splits_with_overlap(self) -> None:
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        large = "A" * (MAX_CHUNK_SIZE + 5_000)
        chunks = service._split_into_chunks(large)
        assert len(chunks) >= 2

    def test_chunk_overlap_preserved(self) -> None:
        service = MultiPassImportService(
            MultiPhaseInferenceBackend(responses=[])
        )
        large = "A" * (MAX_CHUNK_SIZE + 10_000)
        chunks = service._split_into_chunks(large)
        if len(chunks) >= 2:
            # Overlap should be present between consecutive chunks
            overlap_start = len(chunks[0]) - CHUNK_OVERLAP
            assert overlap_start >= 0


class TestChunkAnalysis:
    """Test Phase 2: per-chapter analysis."""

    def test_analyze_chunk_parses_response(self) -> None:
        backend = MultiPhaseInferenceBackend(
            responses=[_make_chunk_analysis_response()]
        )
        service = MultiPassImportService(backend)
        result = service._analyze_chunk(
            "Chapter text here...",
            chapter_id="chapter-1",
            chapter_title="The Beginning",
            known_characters_json=None,
        )
        assert result.chapter_id == "chapter-1"
        assert len(result.characters) == 1
        assert result.characters[0].name == "Kvothe"

    def test_analyze_chunk_includes_prior_context(self) -> None:
        backend = MultiPhaseInferenceBackend(
            responses=[_make_chunk_analysis_response()]
        )
        service = MultiPassImportService(backend)
        prior = json.dumps([{"name": "Kvothe", "role": "protagonist"}])
        service._analyze_chunk(
            "Chapter text...",
            chapter_id="chapter-2",
            chapter_title="Continuation",
            known_characters_json=prior,
        )
        req = backend.requests[0]
        user_content = req.messages[1].content
        assert "KNOWN CHARACTERS" in user_content


# --- Character Accumulator Tests ---

class TestCharacterAccumulator:
    """Test CharacterAccumulator dataclass and merge logic."""

    def test_accumulator_default_values(self) -> None:
        acc = CharacterAccumulator(name="Test")
        assert acc.role == "supporting"
        assert acc.aliases == []
        assert acc.chapter_appearances == []
        assert acc.physical_descriptions == []

    def test_update_map_merges_aliases(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import ChapterAnalysisResult, CharacterMention

        mention1 = CharacterMention(
            name="Kvothe",
            aliases=["The Crimson Fair"],
            role="protagonist",
        )
        result1 = ChapterAnalysisResult(
            chapter_id="ch1",
            characters=[mention1],
        )
        service._update_character_map(char_map, result1, "ch1")

        assert "Kvothe" in char_map
        assert char_map["Kvothe"].role == "protagonist"
        assert "The Crimson Fair" in char_map["Kvothe"].aliases

    def test_update_map_promotes_role(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import ChapterAnalysisResult, CharacterMention

        # First mention as minor
        result1 = ChapterAnalysisResult(
            chapter_id="ch1",
            characters=[CharacterMention(name="Syldra", role="minor")],
        )
        service._update_character_map(char_map, result1, "ch1")
        assert char_map["Syldra"].role == "minor"

        # Second mention as antagonist — should promote
        result2 = ChapterAnalysisResult(
            chapter_id="ch2",
            characters=[CharacterMention(name="Syldra", role="antagonist")],
        )
        service._update_character_map(char_map, result2, "ch2")
        assert char_map["Syldra"].role == "antagonist"

    def test_update_map_tracks_appearances(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import ChapterAnalysisResult, CharacterMention

        for ch_id in ["ch1", "ch2", "ch3"]:
            result = ChapterAnalysisResult(
                chapter_id=ch_id,
                characters=[CharacterMention(name="Kvothe", role="protagonist")],
            )
            service._update_character_map(char_map, result, ch_id)

        assert char_map["Kvothe"].chapter_appearances == ["ch1", "ch2", "ch3"]

    def test_update_map_accumulates_traits(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import ChapterAnalysisResult, CharacterMention

        result1 = ChapterAnalysisResult(
            chapter_id="ch1",
            characters=[CharacterMention(
                name="Kvothe",
                personality_traits=["proud", "intelligent"],
            )],
        )
        service._update_character_map(char_map, result1, "ch1")

        result2 = ChapterAnalysisResult(
            chapter_id="ch2",
            characters=[CharacterMention(
                name="Kvothe",
                personality_traits=["intelligent", "resourceful"],
            )],
        )
        service._update_character_map(char_map, result2, "ch2")

        acc = char_map["Kvothe"]
        assert "proud" in acc.personality_traits
        assert "intelligent" in acc.personality_traits
        assert "resourceful" in acc.personality_traits
        # "intelligent" should appear only once (dedup)
        assert acc.personality_traits.count("intelligent") == 1

    def test_find_or_create_matches_by_alias(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import CharacterMention

        # First mention with alias
        mention1 = CharacterMention(
            name="Kvothe",
            aliases=["The Crimson Fair"],
            role="protagonist",
        )
        canonical = service._find_or_create_name(char_map, mention1)
        assert canonical == "Kvothe"

        # Second mention by alias — should match existing
        mention2 = CharacterMention(
            name="The Crimson Fair",
            role="protagonist",
        )
        canonical2 = service._find_or_create_name(char_map, mention2)
        assert canonical2 == "Kvothe"
        # Should have added "The Crimson Fair" as an alias
        assert "The Crimson Fair" in char_map["Kvothe"].aliases

    def test_find_or_create_case_insensitive(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map: dict[str, CharacterAccumulator] = {}

        from app.schemas.story_import import CharacterMention

        mention1 = CharacterMention(name="Kvothe", role="protagonist")
        service._find_or_create_name(char_map, mention1)

        mention2 = CharacterMention(name="kvothe", role="protagonist")
        canonical = service._find_or_create_name(char_map, mention2)
        assert canonical == "Kvothe"


# --- Prior Character Context Tests ---

class TestPriorCharacterContext:
    """Test _build_prior_character_context."""

    def test_empty_map_returns_none(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        assert service._build_prior_character_context({}) is None

    def test_builds_json_summary(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        char_map = {
            "Kvothe": CharacterAccumulator(
                name="Kvothe",
                aliases=["The Crimson Fair"],
                role="protagonist",
                first_introduction_chapter="prologue",
                personality_traits=["proud", "intelligent"],
            ),
        }
        result = service._build_prior_character_context(char_map)
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Kvothe"
        assert parsed[0]["role"] == "protagonist"

    def test_truncates_to_cap(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        # Create many characters to exceed cap
        char_map = {
            f"Char{i}": CharacterAccumulator(
                name=f"Character Number {i}",
                role="supporting",
                personality_traits=[f"trait{j}" for j in range(10)],
            )
            for i in range(50)
        }
        result = service._build_prior_character_context(char_map)
        assert result is not None
        assert len(result) <= PRIOR_CHAR_CONTEXT_CAP + 500  # small tolerance


# --- Consolidation Tests ---

class TestConsolidation:
    """Test Phase 3 consolidation methods."""

    def test_consolidate_characters_calls_llm(self) -> None:
        backend = MultiPhaseInferenceBackend(
            responses=[_make_character_consolidation_response()]
        )
        service = MultiPassImportService(backend)
        char_map = {
            "Kvothe": CharacterAccumulator(
                name="Kvothe",
                role="protagonist",
                first_introduction_chapter="prologue",
                chapter_appearances=["prologue", "chapter-1"],
                physical_descriptions=["Red-haired, lean"],
                personality_traits=["proud"],
                motives=["Desire for fame"],
                development_notes=["Grows from naive to experienced"],
            ),
        }
        result = service._consolidate_characters(char_map, None, None)
        assert len(result) == 1
        assert result[0].name == "Kvothe"
        assert len(backend.requests) == 1

    def test_consolidate_characters_fallback_on_failure(self) -> None:
        class FailingBackend(InferenceBackend):
            @property
            def descriptor(self) -> InferenceProviderDescriptor:
                return InferenceProviderDescriptor(
                    backend="stub", display_name="Failing", transport="stub",
                    default_model="fail", timeout_seconds=30.0,
                )

            def generate_text(self, request: InferenceRequest) -> InferenceResponse:
                raise InferenceBackendError(
                    "fail", category="error", code="ERR",
                    finish_reason="error", retryable=False,
                )

        service = MultiPassImportService(FailingBackend())
        char_map = {
            "Kvothe": CharacterAccumulator(
                name="Kvothe",
                role="protagonist",
                physical_descriptions=["Red-haired"],
                personality_traits=["proud"],
                motives=["Fame"],
                development_notes=["Growth arc"],
            ),
        }
        result = service._consolidate_characters(char_map, None, None)
        assert len(result) == 1
        assert result[0].name == "Kvothe"

    def test_consolidate_empty_characters(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        result = service._consolidate_characters({}, None, None)
        assert result == []
        assert len(backend.requests) == 0

    def test_consolidate_world_bible_calls_llm(self) -> None:
        from app.schemas.story_import import WorldDetail

        backend = MultiPhaseInferenceBackend(
            responses=[json.dumps([
                {
                    "entry_type": "location",
                    "title": "University",
                    "summary": "A place of learning with three colleges",
                    "canonical_facts": ["has three colleges"],
                    "related_character_ids": [],
                }
            ])]
        )
        service = MultiPassImportService(backend)
        details = [
            WorldDetail(
                entry_type="location",
                title="University",
                description="A place of learning",
                canonical_facts=["has three colleges"],
            ),
        ]
        result = service._consolidate_world_bible(details)
        assert len(result) == 1
        assert result[0].title == "University"

    def test_consolidate_world_bible_fallback_dedup(self) -> None:
        from app.schemas.story_import import WorldDetail

        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        details = [
            WorldDetail(entry_type="location", title="University", description="First mention"),
            WorldDetail(entry_type="location", title="university", description="Second mention"),  # same, lowercase
        ]
        result = service._consolidate_world_bible(details)
        # Should deduplicate by (type, title) case-insensitively
        assert len(result) == 1

    def test_consolidate_empty_world_bible(self) -> None:
        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        result = service._consolidate_world_bible([])
        assert result == []


class TestArcDetection:
    """Test Phase 3c: arc detection and fallback."""

    def test_detect_arcs_calls_llm(self) -> None:
        from app.schemas.story_import import PlotEvent, StoryStructureDetection, StructureHint

        backend = MultiPhaseInferenceBackend(
            responses=[_make_arc_detection_response()]
        )
        service = MultiPassImportService(backend)
        events = [PlotEvent(summary="Protagonist arrives", characters_involved=["Kvothe"])]
        structure = StoryStructureDetection(
            project_name="Test Novel",
            structure_type="traditional_novel",
            hints=StructureHint(thematic_keywords=["power"]),
        )
        result = service._detect_arcs(events, [], structure, None, None)
        assert "premise" in result
        assert len(backend.requests) == 1

    def test_fallback_arcs_from_events(self) -> None:
        from app.schemas.story_import import PlotEvent, StoryImportCharacterRequest, StoryStructureDetection, StructureHint

        backend = MultiPhaseInferenceBackend(responses=[])
        service = MultiPassImportService(backend)
        events = [PlotEvent(summary="Event 1")]
        characters = [
            StoryImportCharacterRequest(name="Kvothe", role="protagonist"),
        ]
        structure = StoryStructureDetection(
            project_name="Test Novel",
            structure_type="traditional_novel",
            hints=StructureHint(thematic_keywords=["power"]),
        )
        result = service._build_fallback_arcs(events, characters, structure)
        assert "premise" in result
        assert "story_arcs" in result
        # Should have at least one arc for protagonist
        assert len(result["story_arcs"]) >= 1


# --- Full Multi-Pass Integration Tests ---

@pytest.mark.integration
class TestMultiPassIntegration:
    """Test the full multi-pass analysis flow."""

    def _make_story(self, size: int) -> str:
        """Create a story text of approximately `size` characters."""
        chapters = []
        pos = 0
        for i in range(1, 6):
            ch_text = f"Chapter {i}\n\n" + "A" * (size // 5)
            chapters.append(ch_text)
            pos += len(ch_text)
        return "\n\n".join(chapters)

    def _make_full_responses(self, story_text: str) -> list[str]:
        """Build responses for: structure detection, 5 chapter analyses, character consolidation, world consolidation, arc detection."""
        # Calculate chapter boundaries from text
        lines = story_text.split("\n")
        chapters_data = []
        start_pos = 0
        chunk_size = len(story_text) // 5
        for i in range(5):
            end_pos = min(start_pos + chunk_size, len(story_text))
            line_start = story_text[:start_pos].count("\n") + 1
            line_end = story_text[:end_pos].count("\n") + 1
            chapters_data.append({
                "id": f"chapter-{i+1}",
                "title": f"Chapter {i+1}",
                "section_type": "chapter",
                "start_line": line_start,
                "end_line": line_end,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "estimated_word_count": chunk_size // 5,
            })
            start_pos = end_pos

        structure_resp = _make_structure_response(chapters=chapters_data)
        responses = [structure_resp]

        # One response per chapter analysis
        for i in range(5):
            responses.append(_make_chunk_analysis_response(
                chapter_id=f"chapter-{i+1}",
                chapter_title=f"Chapter {i+1}",
            ))

        # Character consolidation + world consolidation + arc detection
        responses.append(_make_character_consolidation_response())
        responses.append(json.dumps([
            {"entry_type": "location", "title": "University", "summary": "A place of learning",
             "canonical_facts": ["has three colleges"], "related_character_ids": []}
        ]))
        responses.append(_make_arc_detection_response())

        return responses

    def test_analyze_large_story_full_flow(self) -> None:
        story_text = self._make_story(40_000)  # Above MULTI_PASS_THRESHOLD
        responses = self._make_full_responses(story_text)
        backend = MultiPhaseInferenceBackend(responses=responses)
        service = MultiPassImportService(backend)

        analysis = service.analyze_large_story(story_text)

        assert analysis.project_name == "Test Novel"
        assert len(analysis.characters) >= 1
        assert analysis.characters[0].name == "Kvothe"
        assert analysis.genre == "Fantasy"
        # Should have made multiple LLM calls
        assert len(backend.requests) >= 5

    def test_analyze_large_story_handles_chunk_failure(self) -> None:
        """A failed chunk analysis should not stop the full flow."""
        story_text = self._make_story(40_000)
        responses = self._make_full_responses(story_text)

        # Make chapter 3's response invalid to simulate failure
        responses[3] = "invalid json"  # index 1=structure, 2-6=chapters

        backend = MultiPhaseInferenceBackend(responses=responses)
        service = MultiPassImportService(backend)

        analysis = service.analyze_large_story(story_text)
        assert analysis.project_name == "Test Novel"
        # Should still complete despite one failed chunk


# --- Size-Based Routing Tests ---

@pytest.mark.integration
class TestSizeBasedRouting:
    """Test that StoryImportService routes to multi-pass for large stories."""

    def test_small_story_uses_single_pass(self, tmp_path: Path) -> None:
        """Stories below threshold use single-pass analysis."""
        json_content = json.dumps({
            "project_name": "Small Story",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A story",
            "logline": "A logline",
            "thematic_spine": "Theme",
            "emotional_promise": "Promise",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
        })
        inferencer = MultiPhaseInferenceBackend(responses=[json_content])
        project_service = ProjectService(tmp_path)
        db_path = tmp_path / "data" / "state" / "narrative_ops.db"
        repository = StoryDevelopmentRepository(db_path)
        import_service = StoryImportService(
            project_service=project_service,
            repository=repository,
            inferencer=inferencer,
        )

        small_story = "A" * 10_000  # Below MULTI_PASS_THRESHOLD (30k)
        request = StoryImportRequest(project_name="Small", story_text=small_story)
        response = import_service.import_story(request)

        assert response.status == "completed"
        assert response.analysis_mode == "single_pass"

    def test_large_story_routes_to_multi_pass(self, tmp_path: Path) -> None:
        """Stories above threshold use multi-pass analysis."""
        story_text = "B" * 50_000  # Above MULTI_PASS_THRESHOLD (30k)

        # Build responses for multi-pass flow
        lines = story_text.split("\n")
        chunk_size = len(story_text) // 3
        chapters_data = []
        start_pos = 0
        for i in range(3):
            end_pos = min(start_pos + chunk_size, len(story_text))
            line_start = story_text[:start_pos].count("\n") + 1
            line_end = story_text[:end_pos].count("\n") + 1
            chapters_data.append({
                "id": f"chapter-{i+1}",
                "title": f"Chapter {i+1}",
                "section_type": "chapter",
                "start_line": line_start,
                "end_line": line_end,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "estimated_word_count": chunk_size // 5,
            })
            start_pos = end_pos

        structure_resp = _make_structure_response(chapters=chapters_data)
        responses = [structure_resp]
        for i in range(3):
            responses.append(_make_chunk_analysis_response(
                chapter_id=f"chapter-{i+1}",
                chapter_title=f"Chapter {i+1}",
            ))
        responses.append(_make_character_consolidation_response())
        responses.append(json.dumps([
            {"entry_type": "location", "title": "Setting", "summary": "A place",
             "canonical_facts": [], "related_character_ids": []}
        ]))
        responses.append(_make_arc_detection_response())

        backend = MultiPhaseInferenceBackend(responses=responses)
        project_service = ProjectService(tmp_path)
        db_path = tmp_path / "data" / "state" / "narrative_ops.db"
        repository = StoryDevelopmentRepository(db_path)
        import_service = StoryImportService(
            project_service=project_service,
            repository=repository,
            inferencer=backend,
        )

        request = StoryImportRequest(project_name="Large", story_text=story_text)
        response = import_service.import_story(request)

        assert response.status == "completed"
        assert response.analysis_mode == "multi_pass"
        # Verify entities were persisted
        characters = repository.list_character_profiles(response.project_id)
        assert len(characters) >= 1


class ErrorInferenceBackend(InferenceBackend):
    """Always raises InferenceBackendError."""

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return InferenceProviderDescriptor(
            backend="stub",
            display_name="Error Backend",
            transport="stub",
            base_url="http://localhost:9000/v1",
            default_model="error-model",
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["error"],
        )

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        raise InferenceBackendError(
            "Connection refused",
            category="transport_failure",
            code="connection_error",
            finish_reason="error",
            retryable=True,
        )


def test_detect_structure_falls_back_on_llm_error():
    """Phase 1 should fall back to _fallback_structure on LLM failure, not crash."""
    error_backend = ErrorInferenceBackend()
    service = MultiPassImportService(error_backend)

    story_text = "A" * 50_000  # large enough to need structure detection
    result = service._detect_structure(story_text)

    # Should return fallback, not raise
    assert result is not None
    assert len(result.chapters) >= 1


# --- Constants Tests ---

class TestConstants:
    """Verify chunking parameters are sensible."""

    def test_multi_pass_threshold(self) -> None:
        assert MULTI_PASS_THRESHOLD == 30_000

    def test_max_chunk_size(self) -> None:
        assert MAX_CHUNK_SIZE == 20_000

    def test_chunk_overlap(self) -> None:
        assert CHUNK_OVERLAP == 1_000

    def test_prior_char_context_cap(self) -> None:
        assert PRIOR_CHAR_CONTEXT_CAP == 5_000


# --- Retry with Backoff Tests ---

class TestRetryWithBackoff:
    """Test _retry_with_backoff helper method."""

    def test_retry_with_backoff_succeeds_after_failures(self) -> None:
        service = MultiPassImportService(MultiPhaseInferenceBackend(responses=["{}"]))

        call_count = [0]
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise InferenceBackendError("timeout", category="timeout", code="timeout", finish_reason="error", retryable=True)
            return "success"

        result = service._retry_with_backoff(flaky_func, (), {}, max_retries=3)
        assert result == "success"
        assert call_count[0] == 3

    def test_retry_with_backoff_raises_after_max_retries(self) -> None:
        service = MultiPassImportService(MultiPhaseInferenceBackend(responses=["{}"]))

        def always_fails():
            raise InferenceBackendError("error", category="transport_failure", code="error", finish_reason="error", retryable=True)

        with pytest.raises(InferenceBackendError):
            service._retry_with_backoff(always_fails, (), {}, max_retries=2)

    def test_retry_with_backoff_no_retry_on_first_success(self) -> None:
        call_count = [0]
        def succeeds_immediately():
            call_count[0] += 1
            return "ok"

        service = MultiPassImportService(MultiPhaseInferenceBackend(responses=["{}"]))
        result = service._retry_with_backoff(succeeds_immediately, (), {}, max_retries=3)
        assert result == "ok"
        assert call_count[0] == 1


def test_analyze_large_story_calls_progress_callback():
    """Progress callback should be invoked at each phase."""
    from unittest.mock import patch

    progress_log: list[tuple[str, dict]] = []

    def on_progress(phase: str, data: dict):
        progress_log.append((phase, data))

    responses = [
        json.dumps({
            "project_name": "Test",
            "total_estimated_words": 50000,
            "structure_type": "traditional_novel",
            "chapters": [
                {"id": "chapter-1", "title": "Chapter 1", "section_type": "chapter",
                 "start_line": 1, "end_line": 50, "start_pos": 0, "end_pos": 5000},
                {"id": "chapter-2", "title": "Chapter 2", "section_type": "chapter",
                 "start_line": 51, "end_line": 100, "start_pos": 5000, "end_pos": 10000},
            ],
            "hints": {},
        }),
        json.dumps({
            "chapter_id": "chapter-1",
            "characters": [{"name": "Hero", "role": "protagonist", "is_first_introduction": True}],
            "world_details": [],
            "plot_events": [{"summary": "Event 1", "significance": "development"}],
        }),
        json.dumps({
            "chapter_id": "chapter-2", "characters": [], "world_details": [],
            "plot_events": [{"summary": "Event 2", "significance": "development"}],
        }),
    ]

    backend = MultiPhaseInferenceBackend(responses=responses)
    service = MultiPassImportService(backend)

    story_text = "A" * 35_000

    # Patch consolidation methods to avoid LLM calls and extract_json list handling
    from app.schemas.story_import import StoryImportCharacterRequest

    mock_characters = [StoryImportCharacterRequest(name="Hero", role="protagonist")]

    with patch.object(service, "_consolidate_characters", return_value=mock_characters), \
         patch.object(service, "_consolidate_world_bible", return_value=[]), \
         patch.object(service, "_detect_arcs", return_value={
             "premise": "Test story", "logline": "A test logline", "thematic_spine": "theme",
             "emotional_promise": "promise", "target_audience": "adults",
             "complexity_level": "MEDIUM", "story_structure": "THREE_ACT",
             "genre": "fantasy", "tone": "dark", "pov": "THIRD_LIMITED",
             "story_arcs": [], "sequences": [],
             "narrative_constraints": [], "success_definition": "sd",
         }):
        service.analyze_large_story(story_text, on_progress=on_progress)

    phases = [p for p, _ in progress_log]
    assert "structure_detection" in phases
    assert "chapter_analysis" in phases
    assert any("consolidation" in p for p in phases)

    # Verify chapter count was reported
    chapter_data = [d for _, d in progress_log if d.get("total_estimated_chapters") > 0]
    assert len(chapter_data) > 0
