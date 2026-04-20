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
        "raw_story_text": "",
    })


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

    # 9. Assert LLM was called with correct params
    assert len(inferencer.requests) == 1
    req = inferencer.requests[0]
    assert req.temperature == 0.1
    assert req.max_tokens == 16000
    assert req.messages[0].role == "system"
    assert req.messages[1].role == "user"


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
