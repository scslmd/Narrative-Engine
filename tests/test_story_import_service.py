from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.inference.base import InferenceBackend, InferenceBackendError
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.inference import (
    InferenceProviderDescriptor,
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from app.schemas.projects import ProjectCreateRequest
from app.schemas.story_import import StoryImportRequest, StoryImportResponse
from app.services.projects import ProjectService
from app.services.story_import import StoryImportError, StoryImportService


class FakeImportInferenceBackend(InferenceBackend):
    """Returns a fixed JSON response for import analysis."""

    def __init__(self, *, content: str, model: str = "import-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Import Backend",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-import"],
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
            usage=InferenceUsage(prompt_tokens=101, completion_tokens=202, total_tokens=303),
            raw_response={"backend": "fake", "backend_version": "2026.03"},
        )


def _make_json_response(
    project_name: str = "Test Story",
    genre: str = "fantasy",
    tone: str = "dark",
    pov: str = "THIRD_LIMITED",
    structure: str = "THREE_ACT",
    characters: list[dict] | None = None,
) -> str:
    """Helper to generate a valid LLM JSON response."""
    if characters is None:
        characters = [
            {
                "name": "Aria",
                "role": "protagonist",
                "archetype": "hero",
                "external_goal": "Save the kingdom",
                "internal_need": "Find belonging",
                "core_fear": "Being forgotten",
                "primary_strength": "Courage",
                "fatal_flaw": "Recklessness",
                "backstory": "A peasant raised by knights",
                "voice_notes": "Direct, earnest",
                "change_axis": "From naive to wise leader",
            }
        ]
    return json.dumps({
        "project_name": project_name,
        "genre": genre,
        "tone": tone,
        "pov": pov,
        "story_structure": structure,
        "premise": "A hero saves the world from darkness",
        "logline": "One hero against all odds",
        "thematic_spine": "Courage over fear",
        "emotional_promise": "Satisfying victory",
        "target_audience": "Young adults",
        "complexity_level": "MEDIUM",
        "characters": characters,
        "world_bible": [
            {
                "entry_type": "location",
                "title": "The Kingdom",
                "summary": "A magical kingdom in peril",
            }
        ],
        "story_arcs": [
            {"name": "Hero's Journey", "summary": "Classic hero's journey arc"}
        ],
        "sequences": [
            {"title": "Act 1", "summary": "The beginning", "chapters": ["Chapter 1"]}
        ],
        "narrative_constraints": [],
        "success_definition": "Satisfying ending",
    })

@pytest.mark.integration
def test_import_story_creates_project_and_all_entities(tmp_path: Path) -> None:
    """Happy path: full import creates project, foundation, characters, world bible, arcs."""
    # 1. Setup
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(
        project_name="Test Story",
        story_text="Once upon a time in a kingdom far away...",
    )
    response = import_service.import_story(request)

    # 3. Assert response
    assert response.status == "completed"
    assert response.project_id is not None
    assert "Successfully imported" in response.message

    # 4. Assert project exists
    project = project_service.get_project(response.project_id)
    assert project.project_name == "Test Story"

    # 5. Assert foundation created
    foundation_revisions = repository.list_foundation_revisions(response.project_id)
    assert len(foundation_revisions) == 1
    assert foundation_revisions[0].premise == "A hero saves the world from darkness"
    assert foundation_revisions[0].logline == "One hero against all odds"

    # 6. Assert character created
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) == 1
    assert characters[0].display_name == "Aria"
    assert characters[0].role_in_story == "protagonist"

    # 7. Assert world bible entry created
    bible_entries = repository.list_world_bible_entries(response.project_id)
    assert len(bible_entries) == 1
    assert bible_entries[0].title == "The Kingdom"
    assert bible_entries[0].entry_type == "location"

    # 8. Assert arc created
    arcs = repository.list_arc_candidates(response.project_id)
    assert len(arcs) == 1
    assert arcs[0].name == "Hero's Journey"

    # 8b. Assert single-pass persists only high-level sequence shells
    sequences = repository.list_sequence_plans(response.project_id)
    assert len(sequences) == 1
    assert sequences[0].title == "Act 1"
    assert sequences[0].chapter_ids == []
    assert sequences[0].beat_ids == []
    assert sequences[0].status == "imported_high_level"
    assert sequences[0].confidence_score > 0

    chapters = repository.list_chapter_plans(response.project_id)
    assert chapters == []

    scenes = repository.list_scene_plans(response.project_id)
    assert scenes == []

    beats = repository.list_beat_plans(response.project_id)
    assert beats == []

    packets = repository.list_chapter_packets(response.project_id)
    assert packets == []

    # 9. Assert LLM was called with correct params
    assert len(inferencer.requests) == 1
    req = inferencer.requests[0]
    assert req.temperature == 0.1
    assert req.max_tokens == 16000
    assert req.messages[0].role == "system"
    assert req.messages[1].role == "user"


@pytest.mark.integration
def test_import_story_persists_contradiction_only_continuity_findings_idempotently(tmp_path: Path) -> None:
    payload = json.loads(_make_json_response())
    payload["continuity_finding"] = {
        "project_id": "import-project",
        "threads": [],
        "states": [],
        "contradictions": ["Timeline contradiction: Aria leaves before she receives the map."],
        "unresolved_questions": ["Which map handoff is canonical?"],
        "overall_confidence": 0.62,
        "status": "partial",
        "provenance_note": "single-pass continuity smoke",
    }
    inferencer = FakeImportInferenceBackend(content=json.dumps(payload))
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(
        project_name="Continuity Story",
        story_text="Once upon a time in a kingdom far away...",
    )
    first_response = import_service.import_story(request)
    assert first_response.status == "completed"

    second_response = import_service.import_story(
        StoryImportRequest(
            project_name="Continuity Story",
            story_text="Once upon a time in a kingdom far away...",
            project_id=first_response.project_id,
        )
    )
    assert second_response.status == "completed"

    findings = repository.list_continuity_findings(first_response.project_id)
    assert len(findings) == 1
    assert findings[0].finding_key is not None
    assert findings[0].contradictions == [
        "Timeline contradiction: Aria leaves before she receives the map."
    ]
    assert findings[0].unresolved_questions == ["Which map handoff is canonical?"]


@pytest.mark.integration
def test_import_story_with_existing_project_id(tmp_path: Path) -> None:
    """Import into an existing project should not create a new one."""
    # 1. Setup: Create project first
    project_service = ProjectService(tmp_path)
    create_request = ProjectCreateRequest(project_name="Existing Project")
    create_resp = project_service.create_project(create_request)
    project_id = create_resp.project_id

    # 2. Setup: Create import service
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 3. Act
    request = StoryImportRequest(
        project_name="Existing Project",
        story_text="Long ago...",
        project_id=project_id,
    )
    response = import_service.import_story(request)

    # 4. Assert
    assert response.status == "completed"
    assert response.project_id == project_id

    # 5. Assert entities created in existing project
    characters = repository.list_character_profiles(project_id)
    assert len(characters) >= 1

    sequences = repository.list_sequence_plans(project_id)
    assert len(sequences) == 1

    chapters = repository.list_chapter_plans(project_id)
    assert chapters == []


@pytest.mark.integration
def test_import_story_with_existing_project_id_allows_blank_project_name(tmp_path: Path) -> None:
    """Existing-project imports should not require project_name in the request payload."""
    project_service = ProjectService(tmp_path)
    create_request = ProjectCreateRequest(project_name="Existing Project")
    create_resp = project_service.create_project(create_request)
    project_id = create_resp.project_id

    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    request = StoryImportRequest(
        project_name="",
        story_text="Long ago...",
        project_id=project_id,
    )
    response = import_service.import_story(request)

    assert response.status == "completed"
    assert response.project_id == project_id


@pytest.mark.integration
def test_import_story_skips_downstream_planning_for_analysis_failed_chapters(tmp_path: Path) -> None:
    payload = json.loads(_make_json_response())
    payload["sequences"] = [
        {"title": "Act 1", "summary": "Opening movement", "chapters": ["chapter-1", "chapter-2"]},
    ]
    payload["chapter_summaries"] = [
        {
            "chapter_id": "chapter-1",
            "title": "Chapter 1",
            "summary": "The hero answers the call.",
            "section_type": "chapter",
            "analysis_status": "complete",
            "objective": "Leave home.",
            "conflict": "Fear of the unknown.",
            "stakes": "The kingdom may fall.",
            "active_character_names": ["Aria"],
            "continuity_requirements": ["Aria still has the map."],
            "unresolved_questions": ["Who sent the summons?"],
            "plot_events": [
                {
                    "summary": "Aria receives the summons.",
                    "characters_involved": ["Aria"],
                    "significance": "inciting_incident",
                    "unresolved_threads": ["Who sent the summons?"],
                }
            ],
        },
        {
            "chapter_id": "chapter-2",
            "title": "Chapter 2",
            "summary": "",
            "section_type": "chapter",
            "analysis_status": "analysis_failed",
            "objective": "Advance Chapter 2.",
            "conflict": "Conflict unavailable because analysis failed.",
            "stakes": "The consequences remain unclear.",
            "active_character_names": ["Aria"],
            "continuity_requirements": [],
            "unresolved_questions": [],
            "plot_events": [],
        },
    ]

    inferencer = FakeImportInferenceBackend(content=json.dumps(payload))
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    response = import_service.import_story(
        StoryImportRequest(
            project_name="Degraded Story",
            story_text="A" * 500,
        )
    )

    assert response.status == "completed"

    chapters = repository.list_chapter_plans(response.project_id)
    chapter_by_title = {chapter.title: chapter for chapter in chapters}
    assert chapter_by_title["Chapter 1"].status == "imported"
    assert chapter_by_title["Chapter 2"].status == "analysis_failed"

    scenes = repository.list_scene_plans(response.project_id)
    beats = repository.list_beat_plans(response.project_id)
    packets = repository.list_chapter_packets(response.project_id)

    assert len(scenes) == 1
    assert len(beats) == 1
    assert len(packets) == 1
    assert packets[0].chapter_id == chapter_by_title["Chapter 1"].chapter_id
    assert any("could not be analyzed" in warning for warning in response.warnings)


@pytest.mark.integration
def test_import_story_rejects_invalid_project_id(tmp_path: Path) -> None:
    """Using a non-existent project_id should fail with status='failed'."""
    # 1. Setup
    inferencer = FakeImportInferenceBackend(content=_make_json_response())
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(
        project_name="Test",
        story_text="Once upon a time...",
        project_id="nonexistent-uuid-0000",
    )
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "failed"
    assert "not found" in response.message.lower() or "invalid" in response.message.lower()


@pytest.mark.integration
def test_import_story_handles_malformed_json(tmp_path: Path) -> None:
    """Malformed JSON that can't be extracted should fail gracefully."""
    # 1. Setup
    inferencer = FakeImportInferenceBackend(content="this is not json at all")
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "failed"
    assert "JSON" in response.message or "parse" in response.message.lower()


@pytest.mark.integration
def test_import_story_handles_markdown_code_fences(tmp_path: Path) -> None:
    """LLM wraps JSON in ```json fences - should extract successfully."""
    # 1. Setup
    wrapped = "```json\n" + _make_json_response() + "\n```"
    inferencer = FakeImportInferenceBackend(content=wrapped)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) >= 1


@pytest.mark.integration
def test_import_story_handles_inference_backend_error(tmp_path: Path) -> None:
    """InferenceBackendError should return status='failed' without raising."""
    # 1. Setup
    class FailingInferenceBackend(InferenceBackend):
        @property
        def descriptor(self) -> InferenceProviderDescriptor:
            return InferenceProviderDescriptor(
                backend="stub",
                display_name="Failing",
                transport="stub",
                default_model="fail-model",
                timeout_seconds=30.0,
            )

        def generate_text(self, request: InferenceRequest) -> InferenceResponse:
            raise InferenceBackendError(
                "Service unavailable",
                category="timeout",
                code="SERVICE_UNAVAILABLE",
                finish_reason="timeout",
                retryable=True,
            )

    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=FailingInferenceBackend(),
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "failed"
    assert "unavailable" in response.message.lower() or "SERVICE_UNAVAILABLE" in response.message


@pytest.mark.integration
def test_import_story_handles_trailing_text(tmp_path: Path) -> None:
    """JSON followed by explanatory text should still parse."""
    # 1. Setup
    json_content = _make_json_response()
    wrapped = json_content + "\n\nHope this helps!"
    inferencer = FakeImportInferenceBackend(content=wrapped)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"


@pytest.mark.integration
def test_import_story_is_idempotent_on_retry(tmp_path: Path) -> None:
    """Re-importing the same story should use ON CONFLICT DO UPDATE."""
    # 1. Setup
    json_content = _make_json_response(project_name="Idempotent Test")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act: First import
    request = StoryImportRequest(
        project_name="Idempotent Test",
        story_text="First import...",
    )
    first_response = import_service.import_story(request)
    assert first_response.status == "completed"

    # 3. Act: Second import of same story (same project_id)
    second_request = StoryImportRequest(
        project_name="Idempotent Test",
        story_text="Second import of same story...",
        project_id=first_response.project_id,
    )
    second_response = import_service.import_story(second_request)
    assert second_response.status == "completed"

    # 4. Assert: Characters should still be 1 (not duplicated)
    characters = repository.list_character_profiles(first_response.project_id)
    assert len(characters) == 1


@pytest.mark.integration
def test_import_story_story_text_truncation(tmp_path: Path) -> None:
    """Story text > 24K chars should be truncated before sending to LLM."""
    # 1. Setup
    long_story = "A" * 30_000
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text=long_story)
    response = import_service.import_story(request)

    # 3. Assert response
    assert response.status == "completed"

    # 4. Assert: LLM was called with truncated text
    req = inferencer.requests[0]
    user_content = req.messages[1].content
    assert len(user_content) < 30_000


@pytest.mark.integration
def test_import_story_handles_missing_fields(tmp_path: Path) -> None:
    """LLM response missing required characters field should fail."""
    # 1. Setup
    incomplete = json.dumps({
        "project_name": "Incomplete",
        "genre": "fantasy",
        "tone": "dark",
        "pov": "THIRD_LIMITED",
        "story_structure": "THREE_ACT",
        "premise": "A story",
        "logline": "A logline",
        "thematic_spine": "Theme",
        "emotional_promise": "Feeling",
        "target_audience": "Everyone",
        "complexity_level": "MEDIUM",
        "characters": [],
        "narrative_constraints": [],
    })
    inferencer = FakeImportInferenceBackend(content=incomplete)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Test", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "failed"
    assert "characters" in response.message.lower() or "list" in response.message.lower()


@pytest.mark.integration
def test_import_story_multiple_characters(tmp_path: Path) -> None:
    """Import with multiple characters should create all of them."""
    # 1. Setup
    multi_chars = [
        {"name": "Aria", "role": "protagonist", "archetype": "hero"},
        {"name": "Malachi", "role": "antagonist", "archetype": "villain"},
        {"name": "Tessa", "role": "mentor", "archetype": "sage"},
    ]
    json_content = _make_json_response(characters=multi_chars)
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Multi-char", story_text="story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"
    characters = repository.list_character_profiles(response.project_id)
    assert len(characters) == 3
    assert characters[0].display_name == "Aria"
    assert characters[1].display_name == "Malachi"
    assert characters[2].display_name == "Tessa"


@pytest.mark.integration
def test_import_story_with_genre_and_tone_hints(tmp_path: Path) -> None:
    """Genre and tone hints should be included in the LLM request context."""
    # 1. Setup
    json_content = _make_json_response()
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(
        project_name="Hinted",
        story_text="Once upon a time...",
        genre="sci-fi",
        tone="bleak",
    )
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"

    # 4. Assert: hints were included in request
    req = inferencer.requests[0]
    user_content = req.messages[1].content
    assert "Genre hint: sci-fi" in user_content
    assert "Tone hint: bleak" in user_content


@pytest.mark.integration
def test_import_story_updates_manifest_with_llm_metadata(tmp_path: Path) -> None:
    """B4/M3: LLM-extracted genre, tone, pov, story_structure should persist to manifest.json."""
    # 1. Setup
    json_content = _make_json_response(genre="science fiction", tone="hopeful", pov="FIRST", structure="HERO_JOURNEY")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Manifest Test", story_text="A story...")
    response = import_service.import_story(request)

    # 3. Assert response
    assert response.status == "completed"

    # 4. Assert manifest.json was updated
    project_dir = tmp_path / "data" / "projects" / response.project_id
    manifest_path = project_dir / "manifest.json"
    assert manifest_path.exists()

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["config"]["genre"] == "Science Fiction"
    assert manifest_data["config"]["tone_profile"] == "hopeful"
    assert manifest_data["config"]["pov"] == "First"
    assert manifest_data["config"]["story_structure"] == "HERO_JOURNEY"
    assert manifest_data["premise_text"] == "A hero saves the world from darkness"


@pytest.mark.integration
def test_import_story_stable_ids_on_retry(tmp_path: Path) -> None:
    """B2: Hash-based IDs should produce same character/arcs on every retry."""
    # 1. Setup
    json_content = _make_json_response(project_name="Stable IDs Test")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act: First import
    request = StoryImportRequest(project_name="Stable IDs Test", story_text="First...")
    first_response = import_service.import_story(request)
    assert first_response.status == "completed"

    # 3. Act: Second import into same project
    second_request = StoryImportRequest(
        project_name="Stable IDs Test",
        story_text="Second...",
        project_id=first_response.project_id,
    )
    second_response = import_service.import_story(second_request)
    assert second_response.status == "completed"

    # 4. Assert: Character count unchanged (stable hash IDs, not index-based)
    characters = repository.list_character_profiles(first_response.project_id)
    assert len(characters) == 1

    # 5. Assert: Arc count unchanged
    arcs = repository.list_arc_candidates(first_response.project_id)
    assert len(arcs) == 1


@pytest.mark.integration
def test_import_story_ids_are_scoped_per_project(tmp_path: Path) -> None:
    """Same imported names in different projects should not overwrite prior project rows."""
    json_content = _make_json_response(project_name="Scoped IDs Test")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    first_response = import_service.import_story(
        StoryImportRequest(project_name="Scoped IDs Test A", story_text="First...")
    )
    second_response = import_service.import_story(
        StoryImportRequest(project_name="Scoped IDs Test B", story_text="Second...")
    )

    assert first_response.status == "completed"
    assert second_response.status == "completed"
    assert first_response.project_id != second_response.project_id

    first_characters = repository.list_character_profiles(first_response.project_id)
    second_characters = repository.list_character_profiles(second_response.project_id)
    assert len(first_characters) == 1
    assert len(second_characters) == 1
    assert first_characters[0].character_id != second_characters[0].character_id

    first_arcs = repository.list_arc_candidates(first_response.project_id)
    second_arcs = repository.list_arc_candidates(second_response.project_id)
    assert len(first_arcs) == 1
    assert len(second_arcs) == 1
    assert first_arcs[0].arc_id != second_arcs[0].arc_id


@pytest.mark.integration
def test_import_story_duplicate_character_names_deduplicated(tmp_path: Path) -> None:
    """B2: Same character name produces same hash ID, so duplicate names are deduplicated."""
    # 1. Setup
    duplicate_chars = [
        {"name": "Aria", "role": "protagonist", "archetype": "hero"},
        {"name": "Aria", "role": "deuteragonist", "archetype": "sidekick"},  # Same name, different data
        {"name": "Borin", "role": "antagonist", "archetype": "villain"},
    ]
    json_content = _make_json_response(characters=duplicate_chars)
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Dedup Test", story_text="A story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"
    characters = repository.list_character_profiles(response.project_id)
    # Should have 2 unique characters (Aria deduplicated to 1, Borin = 1)
    assert len(characters) == 2
    names = sorted([c.display_name for c in characters])
    assert names == ["Aria", "Borin"]


@pytest.mark.integration
def test_import_story_foundation_revisions_idempotent(tmp_path: Path) -> None:
    """B3/M2: Foundation revision insert with ON CONFLICT should not duplicate on retry."""
    # 1. Setup
    json_content = _make_json_response(project_name="Foundation Dup Test")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act: First import
    request = StoryImportRequest(project_name="Foundation Dup Test", story_text="First...")
    first_response = import_service.import_story(request)
    assert first_response.status == "completed"

    # 3. Act: Second import into same project
    second_request = StoryImportRequest(
        project_name="Foundation Dup Test",
        story_text="Second...",
        project_id=first_response.project_id,
    )
    second_response = import_service.import_story(second_request)
    assert second_response.status == "completed"

    # 4. Assert: Only 2 foundation revisions (initial + retry, no duplicates of same revision number)
    revisions = repository.list_foundation_revisions(first_response.project_id)
    # First import creates revision 1, second import also calculates revision 1 (since COALESCE
    # finds MAX=1 and adds 1... but with ON CONFLICT, revision 1 gets updated instead of duplicated)
    # Actually, after first import revision=1 exists. Second import: MAX=1, next_rev=2.
    # So we get revision 1 and 2 = 2 total, not duplicated revision 1.
    assert len(revisions) == 2


@pytest.mark.integration
def test_import_story_manifest_update_invalid_pov_skipped(tmp_path: Path) -> None:
    """B4: Invalid POV value should be logged and skipped without failing import."""
    # 1. Setup
    # Use invalid POV that doesn't match any PovMode
    json_content = _make_json_response(pov="INFINITE_REALM")
    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Invalid POV Test", story_text="A story...")
    response = import_service.import_story(request)

    # 3. Assert: Import still succeeds, manifest just doesn't get invalid POV
    assert response.status == "completed"
    project_dir = tmp_path / "data" / "projects" / response.project_id
    manifest_path = project_dir / "manifest.json"
    assert manifest_path.exists()

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Invalid POV should be skipped - default or unchanged POV remains
    # Genre should still be updated
    assert manifest_data["config"]["genre"] == "Fantasy"


@pytest.mark.integration
def test_import_story_multiple_arcs_hash_ids(tmp_path: Path) -> None:
    """B2: Multiple arcs should get stable hash-based IDs."""
    # 1. Setup
    multi_arcs = [
        {"name": "Hero's Journey", "summary": "The classic arc"},
        {"name": "Redemption Arc", "summary": "A villain turns good"},
        {"name": "Hero's Journey", "summary": "Duplicate arc name"},
    ]
    json_content = _make_json_response()
    # Override story_arcs in the JSON
    parsed = json.loads(json_content)
    parsed["story_arcs"] = multi_arcs
    json_content = json.dumps(parsed)

    inferencer = FakeImportInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    import_service = StoryImportService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
    )

    # 2. Act
    request = StoryImportRequest(project_name="Multi-Arc Test", story_text="A story...")
    response = import_service.import_story(request)

    # 3. Assert
    assert response.status == "completed"
    arcs = repository.list_arc_candidates(response.project_id)
    # Hero's Journey appears twice -> same hash -> deduplicated to 1
    # Redemption Arc = 1
    # Total: 2 unique arcs
    assert len(arcs) == 2
    arc_names = sorted([a.name for a in arcs])
    assert "Hero's Journey" in arc_names
    assert "Redemption Arc" in arc_names


class TestLLMFieldMapper:
    """Test the _map_llm_fields post-processing mapper."""

    def test_mapper_fixes_world_bibble_wrong_keys(self):
        """LLM uses name/description/significance instead of entry_type/title/summary."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_bible": [
                {
                    "name": "The Kingdom",
                    "description": "A magical kingdom",
                    "significance": "It is the setting of the story",
                }
            ],
            "story_arcs": [],
            "sequences": [],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)
        wb = mapped["world_bible"][0]
        assert "title" in wb and wb["title"] == "The Kingdom"
        assert "entry_type" in wb
        assert "summary" in wb
        assert "magical kingdom" in wb["summary"].lower()
        assert "setting" in wb["summary"].lower()

    def test_mapper_fixes_world_bibble_missing_entry_type(self):
        """LLM omits entry_type entirely."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_bible": [
                {"name": "Railway System", "description": "A transport network"}
            ],
            "story_arcs": [],
            "sequences": [],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)
        wb = mapped["world_bible"][0]
        assert wb["entry_type"] == "technology"

    def test_mapper_fixes_arcs_wrong_keys(self):
        """LLM uses description/type instead of summary/stage_map/tags."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_bible": [],
            "story_arcs": [
                {"name": "Hero's Journey", "description": "Classic arc", "type": "character"}
            ],
            "sequences": [],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)
        arc = mapped["story_arcs"][0]
        assert arc["summary"] == "Classic arc"
        assert arc["tags"] == ["character"]
        assert arc["stage_map"] == []

    def test_mapper_fixes_sequences_wrong_keys(self):
        """LLM uses name/description instead of title/summary."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_bible": [],
            "story_arcs": [],
            "sequences": [
                {"name": "Act One", "description": "The beginning"}
            ],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)
        seq = mapped["sequences"][0]
        assert seq["title"] == "Act One"
        assert seq["summary"] == "The beginning"
        assert seq["chapters"] == []

    def test_mapper_fixes_character_array_fields(self):
        """LLM returns array fields as strings instead of lists."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [
                {
                    "name": "Hero",
                    "role": "protagonist",
                    "contradictions": "brave but cautious",
                    "secrets": "orphaned child",
                    "values": "honor",
                    "taboos": "betrayal",
                    "continuity_facts": "scar on left cheek",
                }
            ],
            "world_bible": [],
            "story_arcs": [],
            "sequences": [],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)
        char = mapped["characters"][0]
        assert char["contradictions"] == ["brave but cautious"]
        assert char["secrets"] == ["orphaned child"]
        assert char["values"] == ["honor"]
        assert char["taboos"] == ["betrayal"]
        assert char["continuity_facts"] == ["scar on left cheek"]

    def test_mapper_fixes_narrative_constraints_string(self):
        """LLM returns narrative_constraints as a string instead of list."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_bible": [],
            "story_arcs": [],
            "sequences": [],
            "narrative_constraints": "First-person perspective",
        }
        mapped = _map_llm_fields(llm_data)
        assert mapped["narrative_constraints"] == ["First-person perspective"]

    def test_mapper_preserves_correct_fields(self):
        """Mapper should not corrupt data that already uses correct field names."""
        from app.services.story_import import _map_llm_fields

        llm_data = {
            "project_name": "Test",
            "genre": "Fantasy",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A test",
            "logline": "A test",
            "thematic_spine": "A test",
            "emotional_promise": "A test",
            "target_audience": "Adults",
            "complexity_level": "MEDIUM",
            "characters": [
                {
                    "name": "Hero",
                    "role": "protagonist",
                    "contradictions": ["brave, cautious"],
                    "secrets": [],
                    "values": ["honor"],
                    "taboos": [],
                    "continuity_facts": ["scar"],
                }
            ],
            "world_bible": [
                {
                    "entry_type": "location",
                    "title": "The Kingdom",
                    "summary": "A magical place",
                    "canonical_facts": ["has a castle"],
                    "related_character_ids": [],
                }
            ],
            "story_arcs": [
                {
                    "name": "Hero's Journey",
                    "summary": "Classic arc",
                    "stage_map": ["start", "end"],
                    "tags": ["character"],
                }
            ],
            "sequences": [
                {"title": "Act 1", "summary": "Beginning", "chapters": ["ch1"]},
            ],
            "narrative_constraints": [],
        }
        mapped = _map_llm_fields(llm_data)

        # World bible should be unchanged
        wb = mapped["world_bible"][0]
        assert wb["entry_type"] == "location"
        assert wb["title"] == "The Kingdom"
        assert wb["summary"] == "A magical place"

        # Arcs should be unchanged
        arc = mapped["story_arcs"][0]
        assert arc["name"] == "Hero's Journey"
        assert arc["summary"] == "Classic arc"
        assert arc["stage_map"] == ["start", "end"]
        assert arc["tags"] == ["character"]

        # Sequences should be unchanged
        seq = mapped["sequences"][0]
        assert seq["title"] == "Act 1"
        assert seq["summary"] == "Beginning"
        assert seq["chapters"] == ["ch1"]

        # Characters should be unchanged
        char = mapped["characters"][0]
        assert char["contradictions"] == ["brave, cautious"]
        assert char["secrets"] == []


@pytest.mark.integration
class TestMapperIntegration:
    """Test that the mapper integrates correctly with the full import pipeline."""

    def test_import_with_llm_wrong_field_names_succeeds(self, tmp_path: Path) -> None:
        """Import with LLM output using wrong field names should succeed after mapping."""
        # This is the exact output pattern we saw from the LLM
        wrong_field_output = json.dumps({
            "project_name": "Test Story",
            "genre": "Adventure",
            "tone": "dark",
            "pov": "FIRST",
            "story_structure": "THREE_ACT",
            "premise": "A hero's journey",
            "logline": "One hero against all odds",
            "thematic_spine": "Courage over fear",
            "emotional_promise": "Satisfying victory",
            "target_audience": "Young adults",
            "complexity_level": "MEDIUM",
            "characters": [
                {
                    "name": "Aria",
                    "role": "protagonist",
                    "archetype": "hero",
                    "external_goal": "Save the kingdom",
                    "internal_need": "Find belonging",
                    "core_fear": "Being forgotten",
                    "primary_strength": "Courage",
                    "fatal_flaw": "Recklessness",
                    "backstory": "A peasant raised by knights",
                    "voice_notes": "Direct, earnest",
                    "change_axis": "From naive to wise leader",
                    "contradictions": "brave but impulsive",
                    "secrets": "royal bloodline",
                    "values": "honor, loyalty",
                    "taboos": "betrayal",
                    "continuity_facts": "scar on left cheek",
                }
            ],
            "world_bible": [
                {
                    "name": "The Kingdom",
                    "description": "A magical kingdom in peril",
                    "significance": "Central setting where the story takes place",
                }
            ],
            "story_arcs": [
                {"name": "Hero's Journey", "description": "Classic hero arc", "type": "character"},
            ],
            "sequences": [
                {"name": "Act 1", "description": "The beginning"},
            ],
            "narrative_constraints": "No magic system defined",
        })
        inferencer = FakeImportInferenceBackend(content=wrong_field_output)
        project_service = ProjectService(tmp_path)
        db_path = tmp_path / "data" / "state" / "narrative_ops.db"
        repository = StoryDevelopmentRepository(db_path)
        import_service = StoryImportService(
            project_service=project_service,
            repository=repository,
            inferencer=inferencer,
        )

        request = StoryImportRequest(project_name="Test Story", story_text="A story...")
        response = import_service.import_story(request)

        assert response.status == "completed", f"Import failed: {response.message}"

        # Verify world bible was correctly mapped
        bible_entries = repository.list_world_bible_entries(response.project_id)
        assert len(bible_entries) == 1
        assert bible_entries[0].title == "The Kingdom"
        assert bible_entries[0].entry_type == "location"  # inferred
        assert "magical kingdom" in bible_entries[0].summary.lower()
        assert "setting" in bible_entries[0].summary.lower()

        # Verify arcs were correctly mapped
        arcs = repository.list_arc_candidates(response.project_id)
        assert len(arcs) == 1
        assert arcs[0].name == "Hero's Journey"
        assert arcs[0].summary == "Classic hero arc"

        # Verify character was created with array fields
        characters = repository.list_character_profiles(response.project_id)
        assert len(characters) == 1


class TestExtractJSON:
    """Test _extract_json handles various LLM output patterns."""

    def _extract(self, content: str):
        from app.utils.json_extract import extract_json
        return extract_json(content)

    def test_direct_json(self):
        """Raw JSON object should parse directly."""
        result = self._extract('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_code_fence(self):
        """JSON inside markdown code fences should be extracted."""
        content = '```json\n{"key": "value"}\n```'
        result = self._extract(content)
        assert result == {"key": "value"}

    def test_code_fence_without_lang(self):
        """Code fence without language specifier should work."""
        content = '```\n{"key": "value"}\n```'
        result = self._extract(content)
        assert result == {"key": "value"}

    def test_trailing_text_after_json(self):
        """JSON with trailing explanatory text should extract just the JSON."""
        content = '{"key": "value"}\n\nHere is some extra explanation.'
        result = self._extract(content)
        assert result == {"key": "value"}

    def test_leading_text_before_json(self):
        """Text before JSON should be ignored."""
        content = 'Sure, here is the analysis:\n\n{"key": "value"}'
        result = self._extract(content)
        assert result == {"key": "value"}

    def test_nested_objects_with_braces_in_strings(self):
        """Braces inside string values should not confuse the parser."""
        content = '{"quote": "He said {hello} and waved", "nested": {"a": 1}}'
        result = self._extract(content)
        assert result["quote"] == "He said {hello} and waved"
        assert result["nested"] == {"a": 1}

    def test_escaped_quotes_in_strings(self):
        """Escaped quotes should not toggle string boundary tracking."""
        content = '{"dialogue": "She said \\"hello\\" to him"}'
        result = self._extract(content)
        assert result["dialogue"] == 'She said "hello" to him'

    def test_deeply_nested_structure(self):
        """Deeply nested JSON should be correctly extracted."""
        content = '{"a": {"b": {"c": {"d": [1, 2, 3]}}}}'
        result = self._extract(content)
        assert result["a"]["b"]["c"]["d"] == [1, 2, 3]

    def test_empty_object(self):
        """Empty JSON object should parse."""
        result = self._extract('{}')
        assert result == {}

    def test_no_opening_brace_returns_none(self):
        """Content with no opening brace should return None."""
        assert self._extract("This is just plain text") is None

    def test_empty_content_returns_none(self):
        """Empty content should return None."""
        assert self._extract("") is None

    def test_code_fence_with_trailing_explanation(self):
        """Code fence followed by explanatory text should extract JSON."""
        content = '```json\n{"key": "value"}\n```\n\nNote: this was the analysis.'
        result = self._extract(content)
        assert result == {"key": "value"}

    def test_truncated_json_fallback(self):
        """Truncated JSON with extra trailing content should use rfind fallback."""
        # Balanced brace parser may fail on malformed JSON, but rfind can recover.
        content = '{"key": "value"}\n\nSome explanation text follows.'
        result = self._extract(content)
        assert result["key"] == "value"

    def test_balanced_brace_with_nested_objects(self):
        """Balanced brace parser should handle nested objects correctly."""
        content = 'Here is the result: {"outer": {"inner": [1, 2]}, "done": true}\nEnd.'
        result = self._extract(content)
        assert result["outer"]["inner"] == [1, 2]
        assert result["done"] is True

    def test_whitespace_only_returns_none(self):
        """Whitespace-only content should return None."""
        assert self._extract("   \n\t  ") is None

    def test_array_fields_preserved(self):
        """JSON with array fields should preserve arrays."""
        content = '{"items": [1, 2, {"nested": true}], "empty": []}'
        result = self._extract(content)
        assert result["items"] == [1, 2, {"nested": True}]
        assert result["empty"] == []

    def test_unicode_content(self):
        """Unicode characters in JSON should be preserved."""
        content = '{"title": "Café", "emoji": "test"}'
        result = self._extract(content)
        assert result["title"] == "Café"
