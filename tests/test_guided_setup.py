from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.guided_setup import (
    CategoryProgress,
    ChatMessage,
    ExtractedFields,
    GuidedArc,
    GuidedCharacter,
    GuidedChapter,
    GuidedConfig,
    GuidedFoundation,
    GuidedSequence,
    GuidedSetupAnalyzeRequest,
    GuidedSetupAnalyzeResponse,
    GuidedSetupCreateRequest,
    GuidedSetupCreateResponse,
    GuidedWorldEntry,
)
from app.schemas.inference import (
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from app.schemas.projects import ProjectCreateRequest
from app.services.guided_setup import GuidedSetupError, GuidedSetupLLMError, GuidedSetupService
from app.services.projects import ProjectService


class FakeGuidedBackend(InferenceBackend):
    """Returns a fixed JSON response for guided setup analysis."""

    def __init__(self, *, content: str, model: str = "guided-fake") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Guided Backend",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_chat_completions=True,
        )

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return self._descriptor

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        return InferenceResponse(
            backend="openai_compatible",
            model=request.model,
            content=self._content,
            finish_reason="stop",
            usage=InferenceUsage(prompt_tokens=50, completion_tokens=100, total_tokens=150),
        )


def _make_analyze_json(
    *,
    genre: str = "sci-fi mystery",
    tone: str = "gritty noir",
    next_question: str = "Who is the main character?",
    confidence: float = 0.7,
    progress: float = 25.0,
    ready: bool = False,
    characters: list[dict] | None = None,
    project_name: str = "",
    pov: str = "",
    story_structure: str = "",
    premise: str = "",
    logline: str = "",
) -> str:
    return json.dumps({
        "extracted_fields": {
            "config": {
                "project_name": project_name,
                "genre": genre,
                "tone_profile": tone,
                "pov": pov,
                "story_structure": story_structure,
                "primary_language": "English",
                "constraints": [],
            },
            "foundation": {
                "premise_text": premise,
                "logline": logline,
                "thematic_spine": "",
                "emotional_promise": "",
                "target_audience": "",
                "complexity_level": "",
            },
            "characters": characters or [],
            "world_bible": [],
            "arcs": [],
        },
        "next_question": next_question,
        "confidence": confidence,
        "progress": progress,
        "ready_to_create": ready,
        "category_progress": [
            {"category": "config", "completeness": 0.5, "confidence": 0.8,
             "fields_collected": ["genre", "tone_profile"], "fields_missing": ["pov", "story_structure"]},
            {"category": "foundation", "completeness": 0.0, "confidence": 0.0,
             "fields_collected": [], "fields_missing": ["premise_text"]},
            {"category": "characters", "completeness": 1.0 if characters else 0.0,
             "confidence": 0.9 if characters else 0.0,
             "fields_collected": ["protagonist"] if characters else [],
             "fields_missing": [] if characters else ["protagonist"]},
        ],
    })


@pytest.fixture
def service(tmp_path: Path):
    project_service = ProjectService(tmp_path)
    ops_db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(ops_db_path)
    return GuidedSetupService(project_service=project_service, operations_db_path=ops_db_path), repository


class TestGuidedSetupAnalyze:
    """Tests for the guided setup analyze service method."""

    def test_analyze_returns_next_question(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service
        json_content = _make_analyze_json(
            genre="sci-fi",
            next_question="What's the main conflict?",
            progress=20.0,
        )
        fake_backend = FakeGuidedBackend(content=json_content)
        svc._inferencer = fake_backend

        request = GuidedSetupAnalyzeRequest(
            conversation_history=[],
            current_answer="I want to write a sci-fi mystery set on a generation ship.",
            accumulated_fields=ExtractedFields(),
        )
        response = svc.analyze_turn(request)

        assert response.next_question == "What's the main conflict?"
        assert response.extracted_fields.config.genre == "sci-fi"
        assert response.progress == 20.0
        assert not response.ready_to_create
        assert len(fake_backend.requests) == 1

    def test_analyze_merges_with_previous_fields(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service
        json_content = _make_analyze_json(
            genre="sci-fi mystery",
            tone="gritty noir",
            next_question="Who is the protagonist?",
            progress=30.0,
            pov="Third_Limited",
        )
        fake_backend = FakeGuidedBackend(content=json_content)
        svc._inferencer = fake_backend

        request = GuidedSetupAnalyzeRequest(
            conversation_history=[
                ChatMessage(role="system", content="What kind of story?", turn=1),
                ChatMessage(role="user", content="A sci-fi mystery", turn=2),
            ],
            current_answer="Third person limited, gritty tone.",
            accumulated_fields=ExtractedFields(
                config=GuidedConfig(project_name="Ship of Shadows", genre="sci-fi", tone_profile="neutral"),
            ),
        )
        response = svc.analyze_turn(request)

        fields = response.extracted_fields.config
        # New non-empty values override
        assert fields.tone_profile == "gritty noir"
        assert fields.pov == "Third_Limited"
        # Previous non-empty values preserved
        assert fields.project_name == "Ship of Shadows"

    def test_analyze_with_characters(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service
        json_content = _make_analyze_json(
            genre="sci-fi mystery",
            next_question="Any secondary characters?",
            progress=40.0,
            characters=[
                {
                    "name": "Kael Voss",
                    "role": "protagonist",
                    "archetype": "detective",
                    "age_range": "mid-40s",
                    "external_goal": "Find the missing passengers",
                    "internal_need": "Redemption for past failure",
                    "core_fear": "Failing people again",
                    "primary_strength": "Analytical mind",
                    "fatal_flaw": "Cynicism",
                    "backstory_summary": "Former security chief who missed a previous incident",
                    "contradictions": ["Cynical but deeply caring"],
                    "change_axis": "From isolated to trusting the crew",
                }
            ],
        )
        fake_backend = FakeGuidedBackend(content=json_content)
        svc._inferencer = fake_backend

        request = GuidedSetupAnalyzeRequest(
            conversation_history=[],
            current_answer="The protagonist is Kael Voss, a mid-40s security officer.",
            accumulated_fields=ExtractedFields(config=GuidedConfig(genre="sci-fi mystery")),
        )
        response = svc.analyze_turn(request)

        chars = response.extracted_fields.characters
        assert len(chars) == 1
        assert chars[0].name == "Kael Voss"
        assert chars[0].role == "protagonist"

    def test_analyze_llm_unavailable_raises_error(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service

        class ErrorBackend(InferenceBackend):
            @property
            def descriptor(self) -> InferenceProviderDescriptor:
                return InferenceProviderDescriptor(
                    backend="openai_compatible", display_name="Error",
                    transport="openai_compatible_http", base_url="http://test",
                )

            def generate_text(self, request: InferenceRequest) -> InferenceResponse:
                raise InferenceBackendError(
                    "Connection refused",
                    category="transport_failure",
                    code="CONNECTION_ERROR",
                    finish_reason="error",
                    retryable=True,
                )

        svc._inferencer = ErrorBackend()

        request = GuidedSetupAnalyzeRequest(
            conversation_history=[],
            current_answer="A sci-fi mystery.",
            accumulated_fields=ExtractedFields(),
        )
        with pytest.raises(GuidedSetupLLMError, match="LLM service unavailable"):
            svc.analyze_turn(request)

    def test_analyze_invalid_json_response_raises_error(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service
        fake_backend = FakeGuidedBackend(content="not valid json {")
        svc._inferencer = fake_backend

        request = GuidedSetupAnalyzeRequest(
            conversation_history=[],
            current_answer="A sci-fi mystery.",
            accumulated_fields=ExtractedFields(),
        )
        with pytest.raises(GuidedSetupLLMError, match="Failed to parse"):
            svc.analyze_turn(request)


class TestGuidedSetupCreate:
    """Tests for the guided setup create service method."""

    def test_create_project_from_full_fields(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service

        request = GuidedSetupCreateRequest(accumulated_fields=ExtractedFields(
            config=GuidedConfig(
                project_name="Ship of Shadows",
                genre="Sci-Fi Mystery",
                tone_profile="Gritty Noir",
                pov="Third_Limited",
                story_structure="THREE_ACT",
                constraints=["No romance subplot"],
            ),
            foundation=GuidedFoundation(
                premise_text="A security officer investigates disappearances on a generation ship.",
                logline="When passengers vanish, a cynical officer uncovers the truth.",
                thematic_spine="Trust vs. isolation",
                target_audience="Adult sci-fi readers",
                complexity_level="medium",
            ),
            characters=[
                GuidedCharacter(
                    name="Kael Voss",
                    role="protagonist",
                    archetype="detective",
                    age_range="mid-40s",
                    external_goal="Find the missing passengers",
                    internal_need="Redemption",
                    core_fear="Failing again",
                    fatal_flaw="Cynicism",
                    backstory_summary="Former security chief",
                )
            ],
            world_bible=[
                GuidedWorldEntry(
                    entry_type="location",
                    title="The Ouroboros Generation Ship",
                    summary="A massive generation ship en route to Proxima Centauri",
                    canonical_facts=["Built in 2180", "Carries 5000 souls"],
                )
            ],
            arcs=[
                GuidedArc(
                    character_name="Kael Voss",
                    arc_type="transformation",
                    summary="From isolated cynic to trusting leader",
                )
            ],
        ))

        response = svc.create_project_from_fields(request)

        assert response.project_name == "Ship of Shadows"
        assert response.characters_created == 1
        assert response.world_entries_created == 1
        assert response.arcs_created == 1
        assert response.foundation_created is True
        assert response.project_id
        assert "Ship of Shadows" in response.message

    def test_create_project_minimal_fields(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service

        request = GuidedSetupCreateRequest(accumulated_fields=ExtractedFields(
            config=GuidedConfig(
                project_name="Quick Start",
                genre="Fantasy",
                tone_profile="Hopeful",
                pov="First",
                story_structure="HERO_JOURNEY",
            ),
        ))

        response = svc.create_project_from_fields(request)

        assert response.project_name == "Quick Start"
        assert response.characters_created == 0
        assert response.world_entries_created == 0
        assert response.arcs_created == 0
        assert response.foundation_created is True

    def test_create_project_missing_name_raises_error(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service

        with pytest.raises(ValueError, match="project_name"):
            GuidedSetupCreateRequest(accumulated_fields=ExtractedFields(
                config=GuidedConfig(project_name="", genre="Fantasy"),
            ))

    def test_create_project_missing_genre_raises_error(self, service: tuple[GuidedSetupService, StoryDevelopmentRepository]) -> None:
        svc, _ = service

        with pytest.raises(ValueError, match="genre"):
            GuidedSetupCreateRequest(accumulated_fields=ExtractedFields(
                config=GuidedConfig(project_name="Test", genre=""),
            ))


class TestGuidedSetupSchemas:
    """Tests for the guided setup schemas."""

    def test_chat_message_normalizes_role(self) -> None:
        msg = ChatMessage(role="  USER  ", content="Hello", turn=1)
        assert msg.role == "user"

    def test_chat_message_invalid_role_defaults_to_user(self) -> None:
        msg = ChatMessage(role="invalid", content="Hello", turn=1)
        assert msg.role == "user"

    def test_guided_config_normalizes_pov(self) -> None:
        config = GuidedConfig(pov="third limited")
        assert config.pov == "Third_Limited"

    def test_guided_config_normalizes_pov_first_person(self) -> None:
        config = GuidedConfig(pov="first")
        assert config.pov == "First"

    def test_guided_config_invalid_pov_defaults(self) -> None:
        config = GuidedConfig(pov="bird's eye view")
        assert config.pov == "Third_Limited"

    def test_guided_config_normalizes_structure(self) -> None:
        config = GuidedConfig(story_structure="hero journey")
        assert config.story_structure == "HERO_JOURNEY"

    def test_guided_config_invalid_structure_defaults(self) -> None:
        config = GuidedConfig(story_structure="something weird")
        assert config.story_structure == "THREE_ACT"

    def test_guided_character_normalizes_role(self) -> None:
        char = GuidedCharacter(name="Test", role="main character")
        assert char.role == "supporting"

    def test_guided_character_valid_role_preserved(self) -> None:
        char = GuidedCharacter(name="Test", role="protagonist")
        assert char.role == "protagonist"

    def test_guided_arc_ensures_default_stages(self) -> None:
        arc = GuidedArc(character_name="Hero", arc_type="transformation")
        assert len(arc.stages) == 6
        assert arc.stages[0] == "status_quo"

    def test_guided_arc_custom_stages_preserved(self) -> None:
        arc = GuidedArc(
            character_name="Hero",
            stages=["beginning", "middle", "end"],
        )
        assert arc.stages == ["beginning", "middle", "end"]

    def test_guided_arc_normalizes_arc_type(self) -> None:
        arc = GuidedArc(character_name="Hero", arc_type="hero's journey")
        assert arc.arc_type == "transformation"

    def test_extracted_fields_defaults(self) -> None:
        fields = ExtractedFields()
        assert fields.config.genre == ""
        assert fields.characters == []
        assert fields.world_bible == []
        assert fields.arcs == []

    def test_category_progress_validation(self) -> None:
        cp = CategoryProgress(
            category="config",
            completeness=0.75,
            confidence=0.9,
            fields_collected=["genre", "tone"],
            fields_missing=["pov"],
        )
        assert cp.completeness == 0.75

    def test_analyze_request_validates_current_answer(self) -> None:
        with pytest.raises(Exception):  # Pydantic validation error
            GuidedSetupAnalyzeRequest(
                conversation_history=[],
                current_answer="",
                accumulated_fields=ExtractedFields(),
            )


class TestPromptBuilder:
    """Tests for the guided setup prompt builder."""

    def test_build_guided_setup_request_structure(self) -> None:
        from app.services.runtime_prompts import build_guided_setup_request

        req = build_guided_setup_request(
            conversation_history=[
                {"role": "system", "content": "What kind of story?"},
                {"role": "user", "content": "A mystery"},
            ],
            current_answer="Set on a spaceship.",
            accumulated_fields={"config": {"genre": "sci-fi"}},
            default_model="test-model",
        )

        assert req.temperature == 0.3
        assert req.max_tokens == 4096
        assert len(req.messages) == 2
        assert req.messages[0].role == "system"
        assert req.messages[1].role == "user"
        assert "mystery" in req.messages[1].content.lower()
        assert "spaceship" in req.messages[1].content.lower()
        assert "sci-fi" in req.messages[1].content

    def test_build_guided_setup_request_empty_fields(self) -> None:
        from app.services.runtime_prompts import build_guided_setup_request

        req = build_guided_setup_request(
            conversation_history=[],
            current_answer="I want to write a story.",
            accumulated_fields={},
            default_model=None,
        )

        assert req.messages[1].role == "user"
        assert "no fields collected yet" in req.messages[1].content


def test_guided_sequence_validates_minimal_fields():
    seq = GuidedSequence(
        sequence_id="seq-001",
        title="Act One",
        summary="Setup and inciting incident",
        chapter_ids=["ch-1", "ch-2"],
        status="guided",
    )
    assert seq.sequence_id == "seq-001"
    assert seq.title == "Act One"
    assert len(seq.chapter_ids) == 2


def test_guided_sequence_requires_title():
    with pytest.raises(ValidationError):
        GuidedSequence(sequence_id="s", title="", summary="x", chapter_ids=[], status="g")


def test_guided_chapter_validates_minimal_fields():
    ch = GuidedChapter(
        chapter_id="ch-001",
        sequence_id="seq-001",
        title="Chapter One",
        summary="Introduction",
        objective="Establish setting",
        conflict="None yet",
        stakes="Low",
        active_character_ids=["char-1"],
        continuity_requirements=[],
        unresolved_questions=[],
        position=0,
        status="guided",
    )
    assert ch.chapter_id == "ch-001"
    assert ch.position == 0
    assert len(ch.active_character_ids) == 1


def test_guided_chapter_requires_title():
    with pytest.raises(ValidationError):
        GuidedChapter(
            chapter_id="c", sequence_id=None, title="", summary="x",
            objective="x", conflict="x", stakes="x",
            active_character_ids=[], continuity_requirements=[],
            unresolved_questions=[], position=0, status="g"
        )


def test_extracted_fields_includes_sequences_and_chapters():
    fields = ExtractedFields(
        sequences=[GuidedSequence(sequence_id="s1", title="Act 1", summary="Setup", chapter_ids=[], status="guided")],
        chapters=[GuidedChapter(
            chapter_id="c1", sequence_id="s1", title="Ch1", summary="Intro",
            objective="Setup", conflict="None", stakes="Low",
            active_character_ids=[], continuity_requirements=[],
            unresolved_questions=[], position=0, status="guided"
        )],
    )
    assert len(fields.sequences) == 1
    assert len(fields.chapters) == 1


def test_extracted_fields_defaults_sequences_and_chapters_to_empty():
    fields = ExtractedFields()
    assert fields.sequences == []
    assert fields.chapters == []


def test_guided_setup_create_response_includes_planning_counts():
    resp = GuidedSetupCreateResponse(
        project_id="p1", project_name="Test",
        characters_created=2, world_entries_created=1, arcs_created=1,
        foundation_created=True,
        sequences_created=2, chapters_created=5,
    )
    assert resp.sequences_created == 2
    assert resp.chapters_created == 5


def test_parse_analyze_response_merges_sequences_and_chapters():
    svc = GuidedSetupService.__new__(GuidedSetupService)

    raw_data = {
        "extracted_fields": {
            "config": {"project_name": "Test", "genre": "Sci-Fi"},
            "foundation": {},
            "characters": [],
            "world_bible": [],
            "arcs": [],
            "sequences": [
                {
                    "sequence_id": "seq-1",
                    "title": "Act One",
                    "summary": "Setup and inciting incident",
                    "chapter_ids": [],
                    "status": "guided",
                }
            ],
            "chapters": [
                {
                    "chapter_id": "ch-1",
                    "sequence_id": "seq-1",
                    "title": "Chapter One",
                    "summary": "Introduction to the world",
                    "objective": "Establish setting",
                    "conflict": "None yet",
                    "stakes": "Low",
                    "active_character_ids": ["Alice"],
                    "continuity_requirements": [],
                    "unresolved_questions": ["Who is Alice?"],
                    "position": 0,
                    "status": "guided",
                }
            ],
        },
        "next_question": "Does this outline work?",
        "confidence": 0.8,
        "progress": 70,
        "ready_to_create": False,
    }

    previous = {
        "config": {"project_name": "Test", "genre": "Sci-Fi"},
        "foundation": {},
        "characters": [],
        "world_bible": [],
        "arcs": [],
        "sequences": [],
        "chapters": [],
    }

    response = svc._parse_analyze_response(raw_data, previous)
    assert len(response.extracted_fields.sequences) == 1
    assert response.extracted_fields.sequences[0].title == "Act One"
    assert len(response.extracted_fields.chapters) == 1
    assert response.extracted_fields.chapters[0].title == "Chapter One"
    assert response.extracted_fields.chapters[0].active_character_ids == ["Alice"]


def test_parse_analyze_response_preserves_previous_sequences_when_empty():
    svc = GuidedSetupService.__new__(GuidedSetupService)

    raw_data = {
        "extracted_fields": {
            "config": {"project_name": "Test", "genre": "Sci-Fi"},
            "foundation": {},
            "characters": [],
            "world_bible": [],
            "arcs": [],
            "sequences": [],
            "chapters": [],
        },
        "next_question": "Continue?",
        "confidence": 0.5,
        "progress": 30,
        "ready_to_create": False,
    }

    previous = {
        "config": {"project_name": "Test", "genre": "Sci-Fi"},
        "foundation": {},
        "characters": [],
        "world_bible": [],
        "arcs": [],
        "sequences": [
            {
                "sequence_id": "seq-old",
                "title": "Existing Act",
                "summary": "Previously collected",
                "chapter_ids": [],
                "status": "guided",
            }
        ],
        "chapters": [],
    }

    response = svc._parse_analyze_response(raw_data, previous)
    assert len(response.extracted_fields.sequences) == 1
    assert response.extracted_fields.sequences[0].title == "Existing Act"


def test_create_project_persists_sequences(service):
    svc, _ = service

    fields = ExtractedFields(
        config=GuidedConfig(project_name="Test Project", genre="Sci-Fi"),
        foundation=GuidedFoundation(premise_text="A test story"),
        characters=[],
        world_bible=[],
        arcs=[],
        sequences=[
            GuidedSequence(sequence_id="seq-1", title="Act One", summary="Setup", chapter_ids=[], status="guided"),
            GuidedSequence(sequence_id="seq-2", title="Act Two", summary="Conflict", chapter_ids=[], status="guided"),
        ],
        chapters=[],
    )

    svc.create_project_from_fields(GuidedSetupCreateRequest(accumulated_fields=fields))

    conn = sqlite3.connect(str(svc._get_operations_db_path()))
    rows = conn.execute("SELECT sequence_id, title FROM sequence_plans ORDER BY sequence_id").fetchall()
    conn.close()

    assert len(rows) == 2
    titles = {r[1] for r in rows}
    assert "Act One" in titles
    assert "Act Two" in titles


def test_create_project_persists_chapters_with_sequence_link(service):
    svc, _ = service

    fields = ExtractedFields(
        config=GuidedConfig(project_name="Test Project", genre="Sci-Fi"),
        foundation=GuidedFoundation(premise_text="A test story"),
        characters=[GuidedCharacter(name="Alice", role="protagonist")],
        world_bible=[],
        arcs=[],
        sequences=[
            GuidedSequence(sequence_id="seq-1", title="Act One", summary="Setup", chapter_ids=[], status="guided"),
        ],
        chapters=[
            GuidedChapter(
                chapter_id="ch-1", sequence_id="seq-1", title="Chapter One",
                summary="Introduction", objective="Establish setting",
                conflict="None", stakes="Low",
                active_character_ids=["Alice"], continuity_requirements=[],
                unresolved_questions=[], position=0, status="guided",
            ),
            GuidedChapter(
                chapter_id="ch-2", sequence_id="seq-1", title="Chapter Two",
                summary="Inciting incident", objective="Disrupt status quo",
                conflict="External threat", stakes="Medium",
                active_character_ids=["Alice"], continuity_requirements=[],
                unresolved_questions=[], position=1, status="guided",
            ),
        ],
    )

    svc.create_project_from_fields(GuidedSetupCreateRequest(accumulated_fields=fields))

    conn = sqlite3.connect(str(svc._get_operations_db_path()))
    rows = conn.execute("SELECT chapter_id, sequence_id, title FROM chapter_plans ORDER BY position").fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0][0] is not None
    assert rows[0][1] is not None  # sequence_id linked
    assert rows[0][2] == "Chapter One"
    assert rows[1][2] == "Chapter Two"


def test_create_project_resolves_character_names_to_ids_in_chapters(service):
    svc, _ = service

    fields = ExtractedFields(
        config=GuidedConfig(project_name="Test Project", genre="Sci-Fi"),
        foundation=GuidedFoundation(premise_text="A test story"),
        characters=[
            GuidedCharacter(name="Alice", role="protagonist"),
            GuidedCharacter(name="Bob", role="antagonist"),
        ],
        world_bible=[],
        arcs=[],
        sequences=[
            GuidedSequence(sequence_id="seq-1", title="Act One", summary="Setup", chapter_ids=[], status="guided"),
        ],
        chapters=[
            GuidedChapter(
                chapter_id="ch-1", sequence_id="seq-1", title="Chapter One",
                summary="Intro", objective="Setup", conflict="None", stakes="Low",
                active_character_ids=["Alice", "Bob"], continuity_requirements=[],
                unresolved_questions=[], position=0, status="guided",
            ),
        ],
    )

    svc.create_project_from_fields(GuidedSetupCreateRequest(accumulated_fields=fields))

    conn = sqlite3.connect(str(svc._get_operations_db_path()))

    char_ids = conn.execute(
        "SELECT character_id FROM character_profiles WHERE display_name IN ('Alice', 'Bob')"
    ).fetchall()
    expected_ids = {r[0] for r in char_ids}

    row = conn.execute(
        "SELECT active_character_ids_json FROM chapter_plans WHERE title = 'Chapter One'"
    ).fetchone()
    conn.close()

    assert row is not None
    stored_ids = json.loads(row[0])
    assert len(stored_ids) == 2
    for sid in stored_ids:
        assert sid in expected_ids


def test_create_project_response_includes_planning_counts(service):
    svc, _ = service

    fields = ExtractedFields(
        config=GuidedConfig(project_name="Test Project", genre="Sci-Fi"),
        foundation=GuidedFoundation(premise_text="A test story"),
        characters=[],
        world_bible=[],
        arcs=[],
        sequences=[
            GuidedSequence(sequence_id="seq-1", title="Act One", summary="Setup", chapter_ids=[], status="guided"),
        ],
        chapters=[
            GuidedChapter(
                chapter_id="ch-1", sequence_id="seq-1", title="Ch1",
                summary="Intro", objective="Setup", conflict="None", stakes="Low",
                active_character_ids=[], continuity_requirements=[],
                unresolved_questions=[], position=0, status="guided",
            ),
        ],
    )

    response = svc.create_project_from_fields(GuidedSetupCreateRequest(accumulated_fields=fields))
    assert response.sequences_created == 1
    assert response.chapters_created == 1


def test_create_project_updates_sequence_chapter_ids_json(service):
    svc, _ = service

    fields = ExtractedFields(
        config=GuidedConfig(project_name="Test Project", genre="Sci-Fi"),
        foundation=GuidedFoundation(premise_text="A test story"),
        characters=[],
        world_bible=[],
        arcs=[],
        sequences=[
            GuidedSequence(sequence_id="seq-1", title="Act One", summary="Setup", chapter_ids=[], status="guided"),
        ],
        chapters=[
            GuidedChapter(
                chapter_id="ch-1", sequence_id="seq-1", title="Ch1",
                summary="Intro", objective="Setup", conflict="None", stakes="Low",
                active_character_ids=[], continuity_requirements=[],
                unresolved_questions=[], position=0, status="guided",
            ),
            GuidedChapter(
                chapter_id="ch-2", sequence_id="seq-1", title="Ch2",
                summary="Inciting", objective="Disrupt", conflict="Threat", stakes="Medium",
                active_character_ids=[], continuity_requirements=[],
                unresolved_questions=[], position=1, status="guided",
            ),
        ],
    )

    svc.create_project_from_fields(GuidedSetupCreateRequest(accumulated_fields=fields))

    conn = sqlite3.connect(str(svc._get_operations_db_path()))
    row = conn.execute(
        "SELECT chapter_ids_json FROM sequence_plans WHERE title = 'Act One'"
    ).fetchone()
    conn.close()

    assert row is not None
    chapter_ids = json.loads(row[0])
    assert len(chapter_ids) == 2
