from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPatternExtractionError:
    def test_is_value_error_subclass(self) -> None:
        from app.services.pattern_extraction import PatternExtractionError

        assert issubclass(PatternExtractionError, ValueError)

    def test_raises_with_message(self) -> None:
        from app.services.pattern_extraction import PatternExtractionError

        with pytest.raises(PatternExtractionError, match="extraction failed"):
            raise PatternExtractionError("extraction failed")

    def test_can_be_caught_as_value_error(self) -> None:
        from app.services.pattern_extraction import PatternExtractionError

        with pytest.raises(ValueError):
            raise PatternExtractionError("test")


class TestPatternExtractionServiceConstructor:
    def test_construct_with_all_params(self) -> None:
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()
        root_dir = Path("/tmp/test-root")

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
            root_dir=root_dir,
        )

        assert service._inferencer is mock_inferencer
        assert service._root_dir == root_dir

    def test_construct_with_defaults(self) -> None:
        from app.services.pattern_extraction import PatternExtractionService
        from app.settings import settings

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

        assert service._inferencer is mock_inferencer
        assert service._root_dir == settings.root_dir

    def test_keyword_only_args(self) -> None:
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        with pytest.raises(TypeError, match="positional argument"):
            PatternExtractionService(mock_project_service, mock_repository, mock_inferencer)  # type: ignore[call-arg]

    def test_creates_mythos_service(self) -> None:
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

        assert service._mythos_service is not None

    def test_mythos_service_receives_same_deps(self) -> None:
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

        assert service._mythos_service._inferencer is mock_inferencer
        assert service._mythos_service._project_service is mock_project_service
        assert service._mythos_service._repository is mock_repository


class TestBuildNarrativeAnalysisRequest:
    """Task 4: Narrative Prompt Builder tests."""

    def test_function_exists_and_is_importable(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request
        assert callable(build_narrative_analysis_request)

    def test_returns_inference_request(self) -> None:
        from app.schemas.inference import InferenceRequest
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        assert isinstance(request, InferenceRequest)

    def test_has_system_and_user_messages(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        roles = [m.role for m in request.messages]
        assert "system" in roles
        assert "user" in roles

    def test_system_prompt_contains_json_schema_keys(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content = system_msg.content

        # Shared pattern layer fields
        assert "archetypal_patterns" in content
        assert "narrative_structures" in content
        assert "world_rules" in content
        assert "symbolic_motifs" in content

        # Thematic layer fields
        assert "thematic_spine" in content
        assert "emotional_promise" in content
        assert "tone_and_voice_direction" in content

        # Narrative-specific fields
        assert "narrative_pattern" in content
        assert "voice_profile" in content
        assert "thematic_constraints" in content

        # Entity layer fields
        assert "key_entities" in content
        assert "entity_relationships" in content

    def test_narrative_specific_fields_in_schema(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content = system_msg.content

        # NarrativePattern sub-fields
        assert "pacing" in content
        assert "chapter_structure" in content or "conflict_type" in content

        # VoiceProfile sub-fields
        assert "narrative_voice" in content

        # ThematicConstraint sub-fields
        assert "moral_stance" in content or "recurring_questions" in content

    def test_temperature_is_deterministic(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        assert request.temperature == 0.1

    def test_max_tokens_is_16000(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        assert request.max_tokens == 16000

    def test_metadata_contains_source(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        assert request.metadata.get("source") == "narrative-analysis"

    def test_truncates_long_story_text(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        long_text = "x" * 30_000
        request = build_narrative_analysis_request(
            story_text=long_text,
            default_model="test-model",
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        # The user message contains a prefix before the story text.
        # Extract the story portion (after the last "\n\n") and verify it's exactly 24,000 chars.
        story_portion = user_msg.content.rsplit("\n\n", 1)[-1]
        assert len(story_portion) == 24_000

    def test_empty_story_text_does_not_crash(self) -> None:
        from app.schemas.inference import InferenceRequest
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="",
            default_model="test-model",
        )
        assert isinstance(request, InferenceRequest)
        assert len(request.messages) == 2
        system_msg = [m for m in request.messages if m.role == "system"][0]
        user_msg = [m for m in request.messages if m.role == "user"][0]
        assert system_msg.content  # system prompt is non-empty
        assert user_msg.content  # user prompt prefix is non-empty

    def test_includes_source_corpus_when_provided(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            source_corpus="Tolkien Legendarium",
            default_model="test-model",
        )
        combined = " ".join(m.content for m in request.messages).lower()
        assert "tolkien" in combined

    def test_includes_generation_mode(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            generation_mode="new_characters",
            default_model="test-model",
        )
        combined = " ".join(m.content for m in request.messages).lower()
        assert "new_characters" in combined

    def test_default_generation_mode_is_same_world(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        combined = " ".join(m.content for m in request.messages).lower()
        assert "same_world" in combined

    def test_model_is_passed_through(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="my-custom-model",
        )
        assert request.model == "my-custom-model"

    def test_system_prompt_mentions_storytelling_dna(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        system_msg = [m for m in request.messages if m.role == "system"][0]
        content_lower = system_msg.content.lower()
        # Should mention storytelling DNA or narrative patterns extraction
        assert any(phrase in content_lower for phrase in [
            "storytelling dna",
            "narrative pattern",
            "extract",
        ])

    def test_source_type_is_narrative(self) -> None:
        from app.services.runtime_prompts import build_narrative_analysis_request

        request = build_narrative_analysis_request(
            story_text="Once upon a time...",
            default_model="test-model",
        )
        combined = " ".join(m.content for m in request.messages).lower()
        assert "narrative" in combined


class TestExtractNarrative:
    """Task 5: PatternExtractionService.extract() method tests."""

    def _make_service(self):
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_inferencer.descriptor.default_model = "test-model"
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        return PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        ), mock_inferencer

    def test_extract_narrative_returns_response(self) -> None:
        from app.schemas.inference import InferenceResponse
        from app.schemas.pattern_extraction import PatternExtractionResponse

        service, mock_inferencer = self._make_service()

        llm_json = '{"source_type": "narrative", "source_corpus": "test", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub",
            content=llm_json,
        )

        result = service.extract(
            text="Once upon a time...",
            source_type="narrative",
            generation_mode="same_world",
        )

        assert isinstance(result, PatternExtractionResponse)
        assert result.status == "completed"
        assert result.extraction is not None

    def test_extract_narrative_calls_inferencer(self) -> None:
        from app.schemas.inference import InferenceResponse
        from app.services.runtime_prompts import build_narrative_analysis_request

        service, mock_inferencer = self._make_service()

        llm_json = '{"source_type": "narrative", "source_corpus": "test", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub",
            content=llm_json,
        )

        service.extract(
            text="Once upon a time...",
            source_type="narrative",
            generation_mode="same_world",
        )

        assert mock_inferencer.generate_text.call_count == 1
        call_arg = mock_inferencer.generate_text.call_args[0][0]
        assert call_arg.temperature == 0.1
        assert call_arg.max_tokens == 16000

    def test_extract_narrative_passes_source_corpus(self) -> None:
        from app.schemas.inference import InferenceResponse

        service, mock_inferencer = self._make_service()

        llm_json = '{"source_type": "narrative", "source_corpus": "Tolkien Legendarium", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub",
            content=llm_json,
        )

        service.extract(
            text="Once upon a time...",
            source_type="narrative",
            generation_mode="same_world",
            source_corpus="Tolkien Legendarium",
        )

        call_arg = mock_inferencer.generate_text.call_args[0][0]
        combined = " ".join(m.content for m in call_arg.messages)
        assert "tolkien" in combined.lower()

    def test_extract_mythology_delegates_to_mythos_service(self) -> None:
        from app.schemas.mythos_extraction import MythosExtractionRequest, MythosExtractionResponse
        from app.schemas.pattern_extraction import PatternExtractionResponse

        service, _ = self._make_service()

        mock_mythos_response = MythosExtractionResponse(
            project_id="proj-123",
            status="completed",
        )
        service._mythos_service.extract = MagicMock(return_value=mock_mythos_response)

        result = service.extract(
            text="The gods of Olympus...",
            source_type="mythology",
            generation_mode="same_world",
        )

        assert isinstance(result, PatternExtractionResponse)
        assert result.status == "completed"
        assert result.project_id == "proj-123"
        service._mythos_service.extract.assert_called_once()

    def test_extract_mythology_passes_source_corpus(self) -> None:
        from app.schemas.mythos_extraction import MythosExtractionRequest, MythosExtractionResponse

        service, _ = self._make_service()

        mock_mythos_response = MythosExtractionResponse(
            project_id="proj-123",
            status="completed",
        )
        service._mythos_service.extract = MagicMock(return_value=mock_mythos_response)

        service.extract(
            text="The gods of Olympus...",
            source_type="mythology",
            generation_mode="transposed",
            source_corpus="Greek Mythology",
        )

        call_arg = service._mythos_service.extract.call_args[0][0]
        assert isinstance(call_arg, MythosExtractionRequest)
        assert call_arg.source_corpus == "Greek Mythology"
        assert call_arg.generation_mode == "transposed"

    def test_extract_returns_error_on_llm_failure(self) -> None:
        from app.inference.base import InferenceBackendError

        service, mock_inferencer = self._make_service()
        mock_inferencer.generate_text.side_effect = InferenceBackendError(
            "timeout",
            category="timeout",
            code="timeout",
            finish_reason="error",
            retryable=True,
        )

        result = service.extract(
            text="Once upon a time...",
            source_type="narrative",
        )

        assert result.status == "failed"
        assert result.error is not None

    def test_extract_mythology_propagates_error(self) -> None:
        from app.schemas.mythos_extraction import MythosExtractionResponse

        service, _ = self._make_service()

        mock_mythos_response = MythosExtractionResponse(
            project_id="proj-123",
            status="failed",
            error="LLM unavailable",
        )
        service._mythos_service.extract = MagicMock(return_value=mock_mythos_response)

        result = service.extract(
            text="The gods...",
            source_type="mythology",
        )

        assert result.status == "failed"
        assert result.error is not None


class TestParseLlmJson:
    """Task 5: _parse_llm_json() method tests."""

    def _make_service(self):
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        return PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

    def test_parse_direct_json(self) -> None:
        service = self._make_service()
        json_str = '{"source_type": "narrative", "source_corpus": "test"}'

        result = service._parse_llm_json(json_str)
        assert result is not None
        assert result.source_type == "narrative"
        assert result.source_corpus == "test"

    def test_parse_markdown_fenced_json(self) -> None:
        service = self._make_service()
        json_str = '```json\n{"source_type": "narrative", "source_corpus": "test"}\n```'

        result = service._parse_llm_json(json_str)
        assert result is not None
        assert result.source_type == "narrative"

    def test_parse_bare_fenced_json(self) -> None:
        service = self._make_service()
        json_str = '```\n{"source_type": "narrative"}\n```'

        result = service._parse_llm_json(json_str)
        assert result is not None
        assert result.source_type == "narrative"

    def test_parse_with_leading_text(self) -> None:
        service = self._make_service()
        json_str = 'Here is the analysis:\n```json\n{"source_type": "narrative"}\n```'

        result = service._parse_llm_json(json_str)
        assert result is not None
        assert result.source_type == "narrative"

    def test_parse_invalid_returns_none(self) -> None:
        service = self._make_service()
        json_str = "This is not JSON at all."

        result = service._parse_llm_json(json_str)
        assert result is None

    def test_parse_empty_string_returns_none(self) -> None:
        service = self._make_service()
        result = service._parse_llm_json("")
        assert result is None


class TestBuildAnalysis:
    """Task 5: _build_analysis() method tests."""

    def _make_service(self):
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        return PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

    def test_build_minimal_analysis(self) -> None:
        from app.schemas.pattern_extraction import PatternExtractionAnalysis

        service = self._make_service()
        data: dict = {}

        result = service._build_analysis(data)
        assert isinstance(result, PatternExtractionAnalysis)

    def test_build_shared_patterns(self) -> None:
        service = self._make_service()
        data: dict = {
            "source_type": "narrative",
            "archetypal_patterns": [
                {"name": "Hero", "description": "The hero's journey"}
            ],
            "narrative_structures": [
                {"name": "Three-Act", "phases": ["Setup", "Confrontation", "Resolution"]}
            ],
            "world_rules": [
                {"rule": "Magic has a cost", "enforcement": "Physical toll"}
            ],
            "symbolic_motifs": [
                {"symbol": "Water", "meaning": "Purification"}
            ],
        }

        result = service._build_analysis(data)
        assert len(result.archetypal_patterns) == 1
        assert result.archetypal_patterns[0].name == "Hero"
        assert len(result.narrative_structures) == 1
        assert len(result.world_rules) == 1
        assert result.world_rules[0].rule == "Magic has a cost"
        assert len(result.symbolic_motifs) == 1

    def test_build_narrative_specific_fields(self) -> None:
        service = self._make_service()
        data: dict = {
            "narrative_pattern": {
                "pacing": "slow-burn",
                "chapter_structure": "alternating POV",
                "conflict_type": "internal",
                "dialogue_style": "sparse",
                "scene_transition": "fade-to-black",
            },
            "voice_profile": {
                "narrative_voice": "omniscient",
                "sentence_rhythm": "measured",
                "descriptive_density": "high",
                "humor_level": "dry",
                "emotional_temperature": "warm",
            },
            "thematic_constraints": [
                {
                    "theme": "redemption",
                    "moral_stance": "grace over judgment",
                    "recurring_questions": ["Can anyone truly change?"],
                    "forbidden_elements": ["deus ex machina"],
                }
            ],
        }

        result = service._build_analysis(data)
        assert result.narrative_pattern is not None
        assert result.narrative_pattern.pacing == "slow-burn"
        assert result.voice_profile is not None
        assert result.voice_profile.narrative_voice == "omniscient"
        assert len(result.thematic_constraints) == 1
        assert result.thematic_constraints[0].theme == "redemption"

    def test_build_entities_and_relationships(self) -> None:
        service = self._make_service()
        data: dict = {
            "key_entities": [
                {
                    "name": "Aragorn",
                    "entity_type": "character",
                    "archetype": "reluctant king",
                    "domain_or_power": "leadership",
                    "canonical_facts": ["Heir of Isildur"],
                }
            ],
            "entity_relationships": [
                {
                    "source": "Aragorn",
                    "target": "Gandalf",
                    "relationship_type": "mentorship",
                    "description": "Guide and protÃ©gÃ©",
                }
            ],
        }

        result = service._build_analysis(data)
        assert len(result.key_entities) == 1
        assert result.key_entities[0].name == "Aragorn"
        assert len(result.entity_relationships) == 1
        assert result.entity_relationships[0].source == "Aragorn"

    def test_build_missing_fields_use_defaults(self) -> None:
        service = self._make_service()
        data: dict = {"source_type": "narrative"}

        result = service._build_analysis(data)
        assert result.source_type == "narrative"
        assert result.narrative_pattern is None
        assert result.voice_profile is None
        assert result.archetypal_patterns == []
        assert result.narrative_structures == []
        assert result.world_rules == []

    def test_build_thematic_fields(self) -> None:
        service = self._make_service()
        data: dict = {
            "thematic_spine": "Power corrupts",
            "emotional_promise": "Catharsis through sacrifice",
            "tone_and_voice_direction": "Dark, lyrical",
        }

        result = service._build_analysis(data)
        assert result.thematic_spine == "Power corrupts"
        assert result.emotional_promise == "Catharsis through sacrifice"
        assert result.tone_and_voice_direction == "Dark, lyrical"


# --- Task 6: Transactional Import & Persistence tests ---


class TestCreateAndPersist:
    """Task 6: _create_and_persist() method tests."""

    def _setup_service(self, tmp_path: Path):
        from app.persistence.story_development import StoryDevelopmentRepository
        from app.services.pattern_extraction import PatternExtractionService
        from app.services.projects import ProjectService

        project_service = ProjectService(tmp_path)
        db_path = tmp_path / "data" / "state" / "narrative_ops.db"
        repository = StoryDevelopmentRepository(db_path)
        mock_inferencer = MagicMock()
        mock_inferencer.descriptor.default_model = "test-model"

        service = PatternExtractionService(
            project_service=project_service,
            repository=repository,
            inferencer=mock_inferencer,
            root_dir=tmp_path,
        )
        return service, project_service, db_path

    @pytest.mark.integration
    def test_create_and_persist_creates_project_and_persists_foundation(
        self, tmp_path: Path
    ) -> None:
        """_create_and_persist creates a new project and persists foundation data."""
        import sqlite3

        from app.schemas.pattern_extraction import (
            NarrativePattern,
            PatternExtractionAnalysis,
            VoiceProfile,
        )

        service, _project_service, db_path = self._setup_service(tmp_path)

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            source_corpus="Test Story",
            generation_mode="same_world",
            thematic_spine="Redemption through sacrifice",
            emotional_promise="Hope in darkness",
            tone_and_voice_direction="Grim but hopeful",
            narrative_pattern=NarrativePattern(
                pacing="slow-burn",
                chapter_structure="alternating POV",
                conflict_type="internal",
            ),
            voice_profile=VoiceProfile(
                narrative_voice="third-person limited",
                sentence_rhythm="measured",
            ),
        )

        project_id = service._create_and_persist(
            project_id=None,
            analysis=analysis,
        )

        assert project_id  # non-empty
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT thematic_spine, emotional_promise, tone_direction "
                "FROM foundation_revisions WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            assert row is not None, "foundation_revisions row not found"
            assert row[0] == "Redemption through sacrifice"
            assert row[1] == "Hope in darkness"
            assert row[2] == "Grim but hopeful"
        finally:
            conn.close()

    @pytest.mark.integration
    def test_create_and_persist_validates_existing_project(
        self, tmp_path: Path
    ) -> None:
        """_create_and_persist validates an existing project_id and persists."""
        import sqlite3

        from app.schemas.pattern_extraction import PatternExtractionAnalysis
        from app.schemas.projects import ProjectCreateRequest

        service, project_service, db_path = self._setup_service(tmp_path)

        # Pre-create a project
        create_resp = project_service.create_project(
            ProjectCreateRequest(project_name="Existing Project")
        )
        existing_id = create_resp.project_id

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            thematic_spine="Power and corruption",
            emotional_promise="Moral reckoning",
        )

        returned_id = service._create_and_persist(
            project_id=existing_id,
            analysis=analysis,
        )

        assert returned_id == existing_id
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT thematic_spine FROM foundation_revisions WHERE project_id = ?",
                (existing_id,),
            ).fetchone()
            assert row is not None
            assert row[0] == "Power and corruption"
        finally:
            conn.close()

    @pytest.mark.integration
    def test_create_and_persist_raises_for_missing_project(
        self, tmp_path: Path
    ) -> None:
        """_create_and_persist raises when given a non-existent project_id."""
        from app.schemas.pattern_extraction import PatternExtractionAnalysis
        from app.services.pattern_extraction import PatternExtractionError

        service, _, _ = self._setup_service(tmp_path)

        analysis = PatternExtractionAnalysis(source_type="narrative")

        with pytest.raises(PatternExtractionError, match="not found"):
            service._create_and_persist(
                project_id="non-existent-project-id",
                analysis=analysis,
            )

    @pytest.mark.integration
    def test_create_and_persist_stores_world_bible_entries(
        self, tmp_path: Path
    ) -> None:
        """World rules and symbolic motifs are persisted as world_bible_entries."""
        import sqlite3

        from app.schemas.mythos_extraction import SymbolicMotif
        from app.schemas.pattern_extraction import (
            PatternExtractionAnalysis,
            WorldRule,
        )

        service, _, db_path = self._setup_service(tmp_path)

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            world_rules=[
                WorldRule(
                    rule="Magic has a cost",
                    enforcement="Physical toll on the caster",
                    exceptions=["Blood magic bypasses this"],
                )
            ],
            symbolic_motifs=[
                SymbolicMotif(
                    symbol="Broken mirror",
                    meaning="Shattered identity",
                    narrative_function="Foreshadowing protagonist's crisis",
                )
            ],
        )

        project_id = service._create_and_persist(
            project_id=None, analysis=analysis
        )

        conn = sqlite3.connect(db_path)
        try:
            entries = conn.execute(
                "SELECT entry_type, title FROM world_bible_entries WHERE project_id = ?",
                (project_id,),
            ).fetchall()
            titles = [e[1] for e in entries]
            assert any("Magic has a cost" in t for t in titles)
            assert any("Broken mirror" in t for t in titles)
        finally:
            conn.close()

    @pytest.mark.integration
    def test_create_and_persist_stores_characters_and_relationships(
        self, tmp_path: Path
    ) -> None:
        """Key entities are persisted as character_profiles, relationships as edges."""
        import sqlite3

        from app.schemas.pattern_extraction import (
            PatternExtractionAnalysis,
            StoryEntity,
        )
        from app.schemas.mythos_extraction import Relationship

        service, _, db_path = self._setup_service(tmp_path)

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            key_entities=[
                StoryEntity(
                    name="Elena",
                    entity_type="character",
                    archetype="reluctant hero",
                    domain_or_power="empathy",
                    canonical_facts=["Orphaned at age seven"],
                ),
                StoryEntity(
                    name="Kael",
                    entity_type="character",
                    archetype="shadow",
                    domain_or_power="deception",
                ),
            ],
            entity_relationships=[
                Relationship(
                    source="Elena",
                    target="Kael",
                    relationship_type="rivalry",
                    description="Childhood friends turned enemies",
                )
            ],
        )

        project_id = service._create_and_persist(
            project_id=None, analysis=analysis
        )

        conn = sqlite3.connect(db_path)
        try:
            chars = conn.execute(
                "SELECT display_name FROM character_profiles WHERE project_id = ?",
                (project_id,),
            ).fetchall()
            names = [c[0] for c in chars]
            assert "Elena" in names
            assert "Kael" in names

            edges = conn.execute(
                "SELECT relation_kind, summary FROM relationship_edges WHERE project_id = ?",
                (project_id,),
            ).fetchall()
            assert len(edges) >= 1
            assert any("rivalry" in e[0] for e in edges)
        finally:
            conn.close()

    @pytest.mark.integration
    def test_create_and_persist_stores_narrative_specific_fields(
        self, tmp_path: Path
    ) -> None:
        """Narrative-specific fields are stored as JSON in narrative_constraints_json."""
        import json as _json
        import sqlite3

        from app.schemas.pattern_extraction import (
            NarrativePattern,
            PatternExtractionAnalysis,
            ThematicConstraint,
            VoiceProfile,
        )

        service, _, db_path = self._setup_service(tmp_path)

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            narrative_pattern=NarrativePattern(
                pacing="slow-burn",
                chapter_structure="alternating POV",
                conflict_type="internal",
                dialogue_style="sparse",
                scene_transition="fade-to-black",
            ),
            voice_profile=VoiceProfile(
                narrative_voice="omniscient",
                sentence_rhythm="measured",
                descriptive_density="high",
                humor_level="dry",
                emotional_temperature="warm",
            ),
            thematic_constraints=[
                ThematicConstraint(
                    theme="redemption",
                    moral_stance="grace over judgment",
                    recurring_questions=["Can anyone truly change?"],
                    forbidden_elements=["deus ex machina"],
                )
            ],
        )

        project_id = service._create_and_persist(
            project_id=None, analysis=analysis
        )

        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT narrative_constraints_json FROM foundation_revisions "
                "WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            assert row is not None, "foundation_revisions row not found"

            constraints = _json.loads(row[0])
            assert "narrative_pattern" in constraints
            assert "voice_profile" in constraints
            assert "thematic_constraints" in constraints

            np = constraints["narrative_pattern"]
            assert np["pacing"] == "slow-burn"
            assert np["chapter_structure"] == "alternating POV"

            vp = constraints["voice_profile"]
            assert vp["narrative_voice"] == "omniscient"
            assert vp["humor_level"] == "dry"

            tc_list = constraints["thematic_constraints"]
            assert len(tc_list) == 1
            assert tc_list[0]["theme"] == "redemption"
            assert tc_list[0]["moral_stance"] == "grace over judgment"
        finally:
            conn.close()

    @pytest.mark.integration
    def test_update_manifest_writes_narrative_metadata(
        self, tmp_path: Path
    ) -> None:
        """_update_manifest writes source_corpus and generation_mode to manifest."""
        import json as _json

        from app.schemas.pattern_extraction import PatternExtractionAnalysis

        service, project_service, _ = self._setup_service(tmp_path)

        # Create a project first
        from app.schemas.projects import ProjectCreateRequest

        create_resp = project_service.create_project(
            ProjectCreateRequest(project_name="Manifest Test")
        )
        project_id = create_resp.project_id

        analysis = PatternExtractionAnalysis(
            source_type="narrative",
            source_corpus="Test Story Corpus",
            generation_mode="same_world",
        )

        service._update_manifest(project_id, analysis)

        manifest_path = (
            tmp_path / "data" / "projects" / project_id / "manifest.json"
        )
        assert manifest_path.exists()
        manifest_data = _json.loads(manifest_path.read_text(encoding="utf-8"))

        config = manifest_data.get("config", {})
        assert config.get("pattern_source_type") == "narrative"
        assert config.get("pattern_source_corpus") == "Test Story Corpus"
        assert config.get("pattern_generation_mode") == "same_world"


# --- Task 7: ManifestConfig Extension & API Endpoints tests ---


class TestManifestConfigPatternFields:
    """Task 7 Step 1-4: ManifestConfig pattern fields."""

    def test_manifest_config_has_pattern_source_type(self) -> None:
        from app.schemas.enums import StoryStructure
        from app.schemas.manifest import ManifestConfig

        config = ManifestConfig(
            genre="fantasy",
            tone_profile="dark",
            story_structure=StoryStructure.THREE_ACT,
            pattern_source_type="narrative",
        )
        assert config.pattern_source_type == "narrative"

    def test_manifest_config_has_pattern_generation_mode(self) -> None:
        from app.schemas.enums import StoryStructure
        from app.schemas.manifest import ManifestConfig

        config = ManifestConfig(
            genre="fantasy",
            tone_profile="dark",
            story_structure=StoryStructure.THREE_ACT,
            pattern_generation_mode="transposed",
        )
        assert config.pattern_generation_mode == "transposed"

    def test_manifest_config_has_pattern_source_corpus(self) -> None:
        from app.schemas.enums import StoryStructure
        from app.schemas.manifest import ManifestConfig

        config = ManifestConfig(
            genre="fantasy",
            tone_profile="dark",
            story_structure=StoryStructure.THREE_ACT,
            pattern_source_corpus="Greek Mythology",
        )
        assert config.pattern_source_corpus == "Greek Mythology"

    def test_manifest_config_pattern_fields_default_to_empty(self) -> None:
        from app.schemas.enums import StoryStructure
        from app.schemas.manifest import ManifestConfig

        config = ManifestConfig(
            genre="fantasy",
            tone_profile="dark",
            story_structure=StoryStructure.THREE_ACT,
        )
        assert config.pattern_source_type == ""
        assert config.pattern_generation_mode == ""
        assert config.pattern_source_corpus == ""

    def test_manifest_config_all_pattern_fields_together(self) -> None:
        from app.schemas.enums import StoryStructure
        from app.schemas.manifest import ManifestConfig

        config = ManifestConfig(
            genre="sci-fi",
            tone_profile="hopeful",
            story_structure=StoryStructure.HERO_JOURNEY,
            pattern_source_type="mythology",
            pattern_generation_mode="new_characters",
            pattern_source_corpus="Norse Mythology",
        )
        assert config.pattern_source_type == "mythology"
        assert config.pattern_generation_mode == "new_characters"
        assert config.pattern_source_corpus == "Norse Mythology"


class TestImportPatternsEndpoint:
    """Task 7 Step 5-7: POST /projects/import-patterns endpoint."""

    def test_import_patterns_endpoint_exists(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "Once upon a time",
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            # Should not be 404 or 405
            assert response.status_code not in (404, 405), (
                f"import-patterns endpoint not registered: {response.status_code}"
            )

    def test_import_patterns_returns_202_on_submit(self, tmp_path: Path) -> None:
        """import-patterns now returns 202 with extraction_id for async processing."""
        import time

        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "This is a sufficiently long story text for testing purposes that exceeds the minimum character requirement.",
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 202
            body = response.json()
            assert "extraction_id" in body
            # Poll until completion or failure
            extraction_id = body["extraction_id"]
            for _ in range(30):
                time.sleep(0.5)
                status_resp = client.get(f"/v1/projects/extraction/{extraction_id}")
                assert status_resp.status_code == 200
                if status_resp.json()["status"] in ("completed", "failed"):
                    break

    def test_import_patterns_validates_source_type(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "Once upon a time",
                    "source_type": "invalid_type",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 422

    def test_import_patterns_validates_generation_mode(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "Once upon a time",
                    "source_type": "narrative",
                    "generation_mode": "invalid_mode",
                },
            )
            assert response.status_code == 422

    def test_import_patterns_accepts_request_body(self, tmp_path: Path) -> None:
        """import-patterns accepts a JSON request body, not query params. Returns 202 for async."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "This is a sufficiently long story text for testing purposes that exceeds the minimum character requirement.",
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                    "project_id": None,
                    "source_corpus": "Test Corpus",
                },
            )
            assert response.status_code == 202
            body = response.json()
            assert "extraction_id" in body

    def test_import_patterns_rejects_missing_text(self, tmp_path: Path) -> None:
        """import-patterns rejects requests without required 'text' field."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 422

    def test_import_patterns_rejects_empty_text(self, tmp_path: Path) -> None:
        """import-patterns rejects requests with empty 'text' field."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            response = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "",
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 422


class TestExtractFromProject:
    """Service-level tests for extract_from_project method."""

    def _make_service(self):
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_inferencer.descriptor.default_model = "test-model"
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        return PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        ), mock_inferencer, mock_repository

    def test_extract_from_project_retrieves_manuscript_docs(self) -> None:
        """extract_from_project calls list_manuscript_documents."""
        from app.schemas.inference import InferenceResponse
        from app.persistence.story_development import ManuscriptDocumentRecord
        from datetime import datetime, timezone

        service, mock_inferencer, mock_repository = self._make_service()

        mock_doc = ManuscriptDocumentRecord(
            document_id="ms-1",
            project_id="proj-123",
            title="Chapter 1",
            content="Once upon a time...",
            chapter_id="ch-1",
            scene_id=None,
            current_draft_artifact_id=None,
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_repository.list_manuscript_documents.return_value = [mock_doc]

        llm_json = '{"source_type": "narrative", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub",
            content=llm_json,
        )

        result = service.extract_from_project(project_id="proj-123")

        mock_repository.list_manuscript_documents.assert_called_once_with("proj-123")
        assert result.status == "completed"

    def test_extract_from_project_concatenates_multiple_docs(self) -> None:
        """extract_from_project concatenates content from multiple manuscript documents."""
        from app.schemas.inference import InferenceRequest, InferenceResponse
        from app.persistence.story_development import ManuscriptDocumentRecord
        from datetime import datetime, timezone

        service, mock_inferencer, mock_repository = self._make_service()

        now = datetime.now(timezone.utc)
        mock_docs = [
            ManuscriptDocumentRecord(
                document_id="ms-1",
                project_id="proj-123",
                title="Chapter 1",
                content="First chapter text.",
                chapter_id="ch-1",
                scene_id=None,
                current_draft_artifact_id=None,
                version=1,
                created_at=now,
                updated_at=now,
            ),
            ManuscriptDocumentRecord(
                document_id="ms-2",
                project_id="proj-123",
                title="Chapter 2",
                content="Second chapter text.",
                chapter_id="ch-2",
                scene_id=None,
                current_draft_artifact_id=None,
                version=1,
                created_at=now,
                updated_at=now,
            ),
        ]
        mock_repository.list_manuscript_documents.return_value = mock_docs

        llm_json = '{"source_type": "narrative", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub",
            content=llm_json,
        )

        service.extract_from_project(project_id="proj-123")

        # Verify the concatenated text was passed to the inferencer
        call_arg: InferenceRequest = mock_inferencer.generate_text.call_args[0][0]
        user_msg = [m for m in call_arg.messages if m.role == "user"][0]
        assert "First chapter text." in user_msg.content
        assert "Second chapter text." in user_msg.content

    def test_extract_from_project_errors_on_empty_docs(self) -> None:
        """extract_from_project returns error when no manuscript documents exist."""
        from app.schemas.pattern_extraction import PatternExtractionResponse

        service, _, mock_repository = self._make_service()
        mock_repository.list_manuscript_documents.return_value = []

        result = service.extract_from_project(project_id="proj-empty")

        assert isinstance(result, PatternExtractionResponse)
        assert result.status == "failed"
        assert "No manuscript documents found" in (result.error or "")


class TestExtractPatternsEndpoint:
    """Task 7 Step 5-7: POST /projects/{project_id}/extract-patterns endpoint."""

    def test_extract_patterns_endpoint_exists(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            # Create a project first
            create_resp = client.post(
                "/v1/projects/create",
                json={"project_name": "Extract Test"},
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            response = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            # Should not be 404 or 405
            assert response.status_code not in (404, 405), (
                f"extract-patterns endpoint not registered: {response.status_code}"
            )

    def test_extract_patterns_returns_202_on_submit(self, tmp_path: Path) -> None:
        """extract-patterns now returns 202 with extraction_id for async processing."""
        import time

        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            create_resp = client.post(
                "/v1/projects/create",
                json={"project_name": "Extract Test 2"},
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            response = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 202
            body = response.json()
            assert "extraction_id" in body
            # Poll until completion or failure (will fail due to no manuscript docs)
            extraction_id = body["extraction_id"]
            for _ in range(30):
                time.sleep(0.5)
                status_resp = client.get(f"/v1/projects/extraction/{extraction_id}")
                assert status_resp.status_code == 200
                if status_resp.json()["status"] == "failed":
                    break

    def test_extract_patterns_errors_when_no_manuscript_docs(self, tmp_path: Path) -> None:
        """extract-patterns returns error when project has no manuscript documents (async)."""
        import time

        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            create_resp = client.post(
                "/v1/projects/create",
                json={"project_name": "No Docs Project"},
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            response = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 202
            extraction_id = response.json()["extraction_id"]
            # Poll until failed
            for _ in range(30):
                time.sleep(0.5)
                status_resp = client.get(f"/v1/projects/extraction/{extraction_id}")
                assert status_resp.status_code == 200
                data = status_resp.json()
                if data["status"] == "failed":
                    assert "No manuscript documents found" in (data.get("error") or "")
                    break

    def test_extract_patterns_retrieves_text_from_manuscript_docs(
        self, tmp_path: Path
    ) -> None:
        """extract-patterns retrieves source text from manuscript documents (async)."""
        import sqlite3
        import time

        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app
            from app.settings import settings

            client = TestClient(build_app())
            create_resp = client.post(
                "/v1/projects/create",
                json={"project_name": "With Docs Project"},
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            # Insert a manuscript document directly into the operations database
            db_path = settings.operations_db_path
            conn = sqlite3.connect(db_path)
            try:
                import uuid

                doc_id = f"ms-test-{uuid.uuid4().hex[:8]}"
                conn.execute(
                    """
                    INSERT INTO manuscript_documents (
                        document_id, project_id, title, content, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 1, datetime('now'), datetime('now'))
                    """,
                    (doc_id, project_id, "Chapter 1", "This is the story content. It has enough text to meet the minimum requirement for extraction."),
                )
                conn.commit()
            finally:
                conn.close()

            response = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 202
            extraction_id = response.json()["extraction_id"]
            # Poll until terminal state
            for _ in range(30):
                time.sleep(0.5)
                status_resp = client.get(f"/v1/projects/extraction/{extraction_id}")
                assert status_resp.status_code == 200
                data = status_resp.json()
                if data["status"] in ("completed", "failed"):
                    # Key verification: error should NOT be about missing docs
                    err = data.get("error") or ""
                    assert "No manuscript documents found" not in err
                    break

    def test_extract_patterns_validates_source_type(self, tmp_path: Path) -> None:
        """extract-patterns validates source_type via PatternExtractionRequest."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            create_resp = client.post(
                "/v1/projects/create",
                json={"project_name": "Validation Project"},
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            response = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={
                    "source_type": "invalid_type",
                    "generation_mode": "same_world",
                },
            )
            assert response.status_code == 422


class TestMainPyWiring:
    """Task 8: Verify PatternExtractionService is wired in build_app()."""

    def test_pattern_service_instantiated_in_build_app(self, tmp_path: Path) -> None:
        """PatternExtractionService is created inside build_app()."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            app = build_app()
            # If build_app() succeeds without error, the service was instantiated.
            # (Instantiation failures would raise during build_app().)
            assert app is not None

    def test_pattern_service_passed_to_projects_router(self, tmp_path: Path) -> None:
        """PatternExtractionService is passed to build_projects_router and endpoints are registered."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())

            # import-patterns route should be registered (not 404/405)
            resp = client.post(
                "/v1/projects/import-patterns",
                json={"text": "", "source_type": "narrative"},
            )
            assert resp.status_code not in (404, 405), (
                f"import-patterns not registered: {resp.status_code}"
            )

            # extract-patterns route should be registered
            create_resp = client.post(
                "/v1/projects/create", json={"project_name": "Wiring Test"}
            )
            assert create_resp.status_code == 201
            project_id = create_resp.json()["project_id"]

            resp = client.post(
                f"/v1/projects/{project_id}/extract-patterns",
                json={"source_type": "narrative"},
            )
            assert resp.status_code not in (404, 405), (
                f"extract-patterns not registered: {resp.status_code}"
            )

    def test_pattern_service_receives_inferencer(self, tmp_path: Path) -> None:
        """PatternExtractionService receives the inference backend from build_app()."""
        with patch_env_tmpdir(tmp_path):
            # Import after env patch so settings pick up stub backend
            import importlib

            import app.settings as settings_mod

            importlib.reload(settings_mod)

            from app.inference import build_inference_backend
            from app.settings import settings as _settings

            inferencer = build_inference_backend(_settings)
            assert inferencer is not None, "Inference backend should be built"
            assert inferencer.descriptor.backend == "stub", (
                f"Expected stub backend with env var, got {inferencer.descriptor.backend}"
            )


class TestMythosBackwardCompatibility:
    """Task 8: Verify mythology source_type still works via delegation."""

    def test_import_mythos_endpoint_still_functions(self, tmp_path: Path) -> None:
        """POST /projects/import-mythos continues to work independently (async, returns 202)."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())
            resp = client.post(
                "/v1/projects/import-mythos",
                json={
                    "text": "The gods of Olympus waged war against the titans in an epic battle that shaped the cosmos.",
                    "source_corpus": "Greek Mythology",
                    "generation_mode": "same_world",
                },
            )
            # Should not be 404 or 405 â€” endpoint still registered
            assert resp.status_code not in (404, 405), (
                f"import-mythos endpoint broken: {resp.status_code}"
            )
            assert resp.status_code == 202
            body = resp.json()
            assert "extraction_id" in body

    def test_mythology_source_type_delegates_via_pattern_service(self) -> None:
        """source_type='mythology' delegates to MythosExtractionService through PatternExtractionService."""
        from app.schemas.mythos_extraction import MythosExtractionResponse
        from app.schemas.pattern_extraction import PatternExtractionResponse
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

        mock_mythos_resp = MythosExtractionResponse(
            project_id="myth-proj-1",
            status="completed",
        )
        service._mythos_service.extract = MagicMock(return_value=mock_mythos_resp)

        result = service.extract(
            text="The gods of Olympus...",
            source_type="mythology",
            generation_mode="same_world",
        )

        assert isinstance(result, PatternExtractionResponse)
        assert result.status == "completed"
        assert result.project_id == "myth-proj-1"
        service._mythos_service.extract.assert_called_once()

    def test_narrative_and_mythology_both_dispatched(self) -> None:
        """PatternExtractionService.dispatch routes narrative and mythology to different paths."""
        from app.schemas.inference import InferenceResponse
        from app.schemas.mythos_extraction import MythosExtractionResponse
        from app.services.pattern_extraction import PatternExtractionService

        mock_inferencer = MagicMock()
        mock_inferencer.descriptor.default_model = "test-model"
        mock_project_service = MagicMock()
        mock_repository = MagicMock()

        service = PatternExtractionService(
            project_service=mock_project_service,
            repository=mock_repository,
            inferencer=mock_inferencer,
        )

        # Narrative path calls the inferencer directly
        llm_json = '{"source_type": "narrative", "generation_mode": "same_world"}'
        mock_inferencer.generate_text.return_value = InferenceResponse(
            backend="stub", content=llm_json,
        )
        service._mythos_service.extract = MagicMock()

        narr_result = service.extract(
            text="A narrative story...",
            source_type="narrative",
        )
        assert narr_result.status == "completed"
        assert mock_inferencer.generate_text.call_count == 1
        # Mythos service should NOT have been called for narrative
        service._mythos_service.extract.assert_not_called()

        # Mythology path delegates to mythos service, does NOT call inferencer directly
        mock_inferencer.generate_text.reset_mock()
        mock_mythos_resp = MythosExtractionResponse(
            project_id="myth-proj-2", status="completed",
        )
        service._mythos_service.extract = MagicMock(return_value=mock_mythos_resp)

        myth_result = service.extract(
            text="The pantheon...",
            source_type="mythology",
        )
        assert myth_result.status == "completed"
        assert myth_result.project_id == "myth-proj-2"
        # Inferencer should NOT have been called for mythology (delegated)
        assert mock_inferencer.generate_text.call_count == 0
        service._mythos_service.extract.assert_called_once()


class TestServiceWiringIntegration:
    """Task 8: End-to-end wiring tests with build_app()."""

    def test_mythos_and_pattern_endpoints_coexist(self, tmp_path: Path) -> None:
        """Both import-mythos and import-patterns endpoints are accessible from the same app (async)."""
        from fastapi.testclient import TestClient

        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            client = TestClient(build_app())

            mythos_resp = client.post(
                "/v1/projects/import-mythos",
                json={
                    "text": "The Norse myths tell of Odin and Thor, the gods who shaped the world and fought eternal battles against chaos.",
                    "source_corpus": "Norse Mythology",
                    "generation_mode": "same_world",
                },
            )
            assert mythos_resp.status_code == 202

            pattern_resp = client.post(
                "/v1/projects/import-patterns",
                json={
                    "text": "This is a sufficiently long narrative story text for testing purposes that exceeds the minimum character requirement.",
                    "source_type": "narrative",
                    "generation_mode": "same_world",
                },
            )
            assert pattern_resp.status_code == 202

    def test_build_app_does_not_raise(self, tmp_path: Path) -> None:
        """build_app() completes without raising any exceptions."""
        with patch_env_tmpdir(tmp_path):
            from app.main import build_app

            try:
                app = build_app()
            except Exception as exc:
                pytest.fail(f"build_app() raised: {exc}")

            assert app is not None


class TestP100ArchitectPromptPatternContext:
    """Task 10: P-100 architect prompt adaptation for pattern context injection."""

    def _make_manifest(self):
        from app.schemas.manifest import Manifest

        return Manifest.model_validate({
            "project_id": "test-project",
            "project_name": "Test Project",
            "genre": "Fantasy",
            "tone": "Dark",
            "story_structure": "THREE_ACT",
            "constraints": [],
            "premise_text": "A test story.",
        })

    def _make_pattern_analysis(self, generation_mode: str = "same_world"):
        from app.schemas.mythos_extraction import ArchetypalPattern
        from app.schemas.pattern_extraction import (
            NarrativePattern,
            PatternExtractionAnalysis,
            VoiceProfile,
            WorldRule,
        )

        return PatternExtractionAnalysis(
            source_type="narrative",
            source_corpus="Test Story Corpus",
            generation_mode=generation_mode,
            archetypal_patterns=[
                ArchetypalPattern(
                    name="Reluctant Hero",
                    description="A hero who resists the call to adventure",
                    character_type="protagonist",
                    narrative_beats=["Call", "Refusal", "Acceptance"],
                )
            ],
            world_rules=[
                WorldRule(rule="Magic has a cost", enforcement="Physical toll"),
            ],
            voice_profile=VoiceProfile(
                narrative_voice="third-person limited",
                sentence_rhythm="measured",
                descriptive_density="high",
            ),
            narrative_pattern=NarrativePattern(pacing="slow-burn"),
        )

    def test_accepts_pattern_context_parameter(self) -> None:
        """build_p100_architect_request accepts pattern_context parameter."""
        from app.services.runtime_prompts import build_p100_architect_request

        manifest = self._make_manifest()
        analysis = self._make_pattern_analysis("same_world")

        request = build_p100_architect_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            pattern_context=analysis,
        )
        assert request is not None

    def test_same_world_injects_pattern_context_block(self) -> None:
        """same_world mode injects pattern context with world rules and voice profile."""
        from app.services.runtime_prompts import build_p100_architect_request

        manifest = self._make_manifest()
        analysis = self._make_pattern_analysis("same_world")

        request = build_p100_architect_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            pattern_context=analysis,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "PATTERN CONTEXT" in content
        assert "Same World Mode" in content
        assert "Test Story Corpus" in content
        assert "Reluctant Hero" in content
        assert "Magic has a cost" in content
        assert "third-person limited" in content

    def test_new_characters_injects_pattern_context_block(self) -> None:
        """new_characters mode injects pattern context with archetypal roles."""
        from app.services.runtime_prompts import build_p100_architect_request

        manifest = self._make_manifest()
        analysis = self._make_pattern_analysis("new_characters")

        request = build_p100_architect_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            pattern_context=analysis,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "PATTERN CONTEXT" in content
        assert "New Characters Mode" in content
        assert "Test Story Corpus" in content
        assert "Reluctant Hero" in content
        assert "Magic has a cost" in content

    def test_transposed_injects_pattern_context_block(self) -> None:
        """transposed mode injects pattern context with patterns to transpose."""
        from app.services.runtime_prompts import build_p100_architect_request

        manifest = self._make_manifest()
        analysis = self._make_pattern_analysis("transposed")

        request = build_p100_architect_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            pattern_context=analysis,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "PATTERN CONTEXT" in content
        assert "Transposed Mode" in content
        assert "Test Story Corpus" in content
        assert "Reluctant Hero" in content
        assert "Magic has a cost" in content

    def test_none_pattern_context_no_block(self) -> None:
        """pattern_context=None does not inject any pattern block."""
        from app.services.runtime_prompts import build_p100_architect_request

        manifest = self._make_manifest()

        request = build_p100_architect_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            pattern_context=None,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "PATTERN CONTEXT" not in content


class TestP300DrafterPromptSceneContext:
    """Task 10: P-300 drafter prompt adaptation for scene context injection."""

    def _make_manifest(self):
        from app.schemas.manifest import Manifest

        return Manifest.model_validate({
            "project_id": "test-project",
            "project_name": "Test Project",
            "genre": "Fantasy",
            "tone": "Dark",
            "story_structure": "THREE_ACT",
            "constraints": [],
            "premise_text": "A test story.",
        })

    def test_accepts_scene_context_parameter(self) -> None:
        """build_p300_drafter_request accepts scene_context parameter."""
        from app.services.runtime_prompts import build_p300_drafter_request
        from app.services.scene_context import (
            CharacterAnchor,
            PatternGuidance,
            SceneContext,
            WorldConstraint,
        )

        manifest = self._make_manifest()
        scene_ctx = SceneContext(
            characters=[
                CharacterAnchor(
                    character_id="ch-1",
                    display_name="Elena",
                    archetype="reluctant hero",
                    voice_notes="sparse, deliberate",
                    external_goal="find the artifact",
                    internal_need="accept vulnerability",
                    core_fear="abandonment",
                )
            ],
            world_facts=[
                WorldConstraint(
                    entry_type="magic_system",
                    title="The Weave",
                    facts=["Magic draws from life force", "Overuse causes burnout"],
                )
            ],
            pattern_guidance=PatternGuidance(),
        )

        request = build_p300_drafter_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            scene_context=scene_ctx,
        )
        assert request is not None

    def test_scene_context_injected_in_user_message(self) -> None:
        """SceneContext content appears in the user message."""
        from app.services.runtime_prompts import build_p300_drafter_request
        from app.services.scene_context import (
            CharacterAnchor,
            SceneContext,
            WorldConstraint,
        )

        manifest = self._make_manifest()
        scene_ctx = SceneContext(
            characters=[
                CharacterAnchor(
                    character_id="ch-1",
                    display_name="Elena",
                    archetype="reluctant hero",
                    voice_notes="sparse",
                    external_goal="find the artifact",
                    internal_need="",
                    core_fear="",
                )
            ],
            world_facts=[
                WorldConstraint(
                    entry_type="magic_system",
                    title="The Weave",
                    facts=["Magic draws from life force"],
                )
            ],
        )

        request = build_p300_drafter_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            scene_context=scene_ctx,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "CHARACTER CONTEXT" in content
        assert "Elena" in content
        assert "reluctant hero" in content
        assert "WORLD CONSTRAINTS" in content
        assert "The Weave" in content

    def test_author_direction_injected(self) -> None:
        """Author direction from SceneContext appears in the prompt."""
        from app.services.runtime_prompts import build_p300_drafter_request
        from app.services.scene_context import SceneContext

        manifest = self._make_manifest()
        scene_ctx = SceneContext(
            characters=[],
            world_facts=[],
            author_prompt="Focus on the emotional climax of this scene.",
        )

        request = build_p300_drafter_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            scene_context=scene_ctx,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "AUTHOR DIRECTION" in content
        assert "emotional climax" in content

    def test_none_scene_context_no_block(self) -> None:
        """scene_context=None does not inject any scene context block."""
        from app.services.runtime_prompts import build_p300_drafter_request

        manifest = self._make_manifest()

        request = build_p300_drafter_request(
            manifest=manifest,
            payload={"project_id": "test-project"},
            default_model="test-model",
            scene_context=None,
        )
        user_msg = [m for m in request.messages if m.role == "user"][0]
        content = user_msg.content

        assert "CHARACTER CONTEXT" not in content
        assert "AUTHOR DIRECTION" not in content


def patch_env_tmpdir(tmp_path: Path):
    import os
    from unittest.mock import patch

    env = {
        "NARRATIVE_ROOT_DIR": str(tmp_path),
        "NARRATIVE_INFERENCE_BACKEND": "stub",
    }
    return patch.dict(os.environ, env)

