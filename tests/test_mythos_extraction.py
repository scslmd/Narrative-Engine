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
from app.services.projects import ProjectService


class _FakeMythosInferenceBackend(InferenceBackend):
    """Returns a fixed JSON response for mythos extraction analysis."""

    def __init__(self, *, content: str, model: str = "mythos-fake-model") -> None:
        self.requests: list[InferenceRequest] = []
        self._content = content
        self._model = model
        self._descriptor = InferenceProviderDescriptor(
            backend="openai_compatible",
            display_name="Fake Mythos Backend",
            transport="openai_compatible_http",
            base_url="http://127.0.0.1:9000/v1",
            default_model=model,
            timeout_seconds=30.0,
            supports_model_listing=False,
            supports_chat_completions=True,
            aliases=["fake-mythos"],
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
            usage=InferenceUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            raw_response={"backend": "fake"},
        )


def _make_mythos_json_response(
    source_corpus: str = "Greek Mythology",
    generation_mode: str = "same_world",
    n_patterns: int = 2,
    n_structures: int = 1,
    n_rules: int = 3,
    n_motifs: int = 2,
) -> str:
    """Helper to generate a valid LLM JSON response for mythos extraction."""
    patterns = [
        {
            "name": f"pattern-{i}",
            "description": f"Description of pattern {i}",
            "character_type": "trickster",
            "narrative_beats": ["rise", "fall"],
            "examples_from_text": [f"Example {i}"],
        }
        for i in range(n_patterns)
    ]
    structures = [
        {
            "name": f"structure-{i}",
            "phases": ["beginning", "end"],
            "tension_curve": "rising",
            "resolution_type": "tragic",
        }
        for i in range(n_structures)
    ]
    rules = [
        {
            "rule": f"Rule {i}",
            "enforcement": f"Enforced by gods {i}",
            "exceptions": [f"Exception {i}"],
        }
        for i in range(n_rules)
    ]
    motifs = [
        {
            "symbol": f"symbol-{i}",
            "meaning": f"Meaning of symbol {i}",
            "narrative_function": f"Function {i}",
        }
        for i in range(n_motifs)
    ]
    return json.dumps({
        "source_corpus": source_corpus,
        "generation_mode": generation_mode,
        "archetypal_patterns": patterns,
        "narrative_structures": structures,
        "cosmic_rules": rules,
        "symbolic_motifs": motifs,
        "thematic_spine": "Order vs chaos",
        "emotional_promise": "Awe and terror",
        "tone_and_voice_direction": "Epic, solemn",
        "key_entities": [],
        "entity_relationships": [],
    })


def test_archetypal_pattern_fields():
    from app.schemas.mythos_extraction import ArchetypalPattern
    pattern = ArchetypalPattern(
        name="hubris-fall-redemption",
        description="Hero rises through arrogance, falls through divine retribution",
        character_type="hubristic hero",
        narrative_beats=["rise", "transgression", "punishment", "suffering", "apotheosis"],
        examples_from_text=["Oedipus defies prophecy"],
    )
    assert pattern.name == "hubris-fall-redemption"
    assert len(pattern.narrative_beats) == 5


def test_narrative_structure_fields():
    from app.schemas.mythos_extraction import NarrativeStructure
    structure = NarrativeStructure(
        name="cyclical tragedy",
        phases=["call", "transgression", "punishment", "redemption"],
        tension_curve="escalating divine retribution",
        resolution_type="bittersweet apotheosis",
    )
    assert len(structure.phases) == 4


def test_cosmic_rule_fields():
    from app.schemas.mythos_extraction import CosmicRule
    rule = CosmicRule(
        rule="Fate cannot be escaped, only fulfilled",
        enforcement="Gods act as agents of moira (fate)",
        exceptions=["prophecies can be misinterpreted"],
    )
    assert len(rule.exceptions) == 1


def test_symbolic_motif_fields():
    from app.schemas.mythos_extraction import SymbolicMotif
    motif = SymbolicMotif(
        symbol="serpent",
        meaning="transformation, hidden knowledge",
        narrative_function="marks threshold between worlds",
    )
    assert motif.narrative_function


def test_mythos_entity_fields():
    from app.schemas.mythos_extraction import MythosEntity
    entity = MythosEntity(
        name="Zeus",
        entity_type="deity",
        archetype="sky father",
        domain_or_power="oaths, hospitality, strangers",
        canonical_facts=["King of the gods"],
    )
    assert entity.entity_type == "deity"


def test_relationship_fields():
    from app.schemas.mythos_extraction import Relationship
    rel = Relationship(
        source="Zeus",
        target="Hades",
        relationship_type="rivalry",
        description="Brothers who divided dominion",
    )
    assert rel.relationship_type == "rivalry"


def test_mythos_extraction_analysis_defaults():
    from app.schemas.mythos_extraction import MythosExtractionAnalysis
    analysis = MythosExtractionAnalysis(
        source_corpus="Greek Mythology",
        generation_mode="same_world",
    )
    assert analysis.archetypal_patterns == []
    assert analysis.key_entities == []
    assert analysis.thematic_spine == ""


def test_mythos_request_validates_generation_mode():
    from app.schemas.mythos_extraction import MythosExtractionRequest
    request = MythosExtractionRequest(
        text="Once upon a time...",
        source_corpus="Greek Mythology",
        generation_mode="same_world",
    )
    assert request.generation_mode == "same_world"


def test_mythos_request_rejects_invalid_mode():
    from app.schemas.mythos_extraction import MythosExtractionRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        MythosExtractionRequest(
            text="Once upon a time...",
            generation_mode="invalid_mode",
        )


def test_mythos_request_rejects_empty_text():
    from app.schemas.mythos_extraction import MythosExtractionRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        MythosExtractionRequest(
            text="",
            generation_mode="same_world",
        )


def test_mythos_response_fields():
    from app.schemas.mythos_extraction import MythosExtractionResponse, ExtractionSummary
    summary = ExtractionSummary(
        source_corpus="Greek Mythology",
        archetypal_patterns=4,
        narrative_structures=2,
        cosmic_rules=5,
        symbolic_motifs=3,
    )
    response = MythosExtractionResponse(
        status="completed",
        project_id="proj-123",
        extraction=summary,
    )
    assert response.status == "completed"
    assert response.extraction.archetypal_patterns == 4


def test_build_mythos_analysis_request_returns_inference_request():
    from app.services.runtime_prompts import build_mythos_analysis_request
    request = build_mythos_analysis_request(
        mythos_text="Zeus threw lightning bolts...",
        source_corpus="Greek Mythology",
        generation_mode="same_world",
        default_model="test-model",
    )
    assert request.model == "test-model"
    system_msg = [m for m in request.messages if m.role == "system"][0]
    assert "archetypal_patterns" in system_msg.content
    assert "narrative_structures" in system_msg.content
    assert request.temperature == 0.1


def test_build_mythos_analysis_request_truncates_long_text():
    from app.services.runtime_prompts import build_mythos_analysis_request
    long_text = "x" * 30_000
    request = build_mythos_analysis_request(
        mythos_text=long_text,
        default_model="test-model",
    )
    user_msg = [m for m in request.messages if m.role == "user"][0]
    assert len(user_msg.content) <= 30_000


def test_build_mythos_analysis_request_includes_generation_mode():
    from app.services.runtime_prompts import build_mythos_analysis_request
    request = build_mythos_analysis_request(
        mythos_text="Test text",
        generation_mode="transposed",
        default_model="test-model",
    )
    combined = " ".join(m.content for m in request.messages).lower()
    assert "transposed" in combined


# --- Task 4: Constructor & Error Class tests ---

def test_mythos_service_construction():
    """MythosExtractionError is subclass of ValueError."""
    from app.services.mythos_extraction import MythosExtractionError
    assert issubclass(MythosExtractionError, ValueError)


def test_mythos_service_initializes_with_dependencies(tmp_path: Path):
    """Constructor stores all injected dependencies."""
    from app.services.mythos_extraction import MythosExtractionService

    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    inferencer = _FakeMythosInferenceBackend(content="{}")

    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    assert service._project_service is project_service
    assert service._repository is repository
    assert service._inferencer is inferencer
    assert service._root_dir == tmp_path


# --- Task 5: extract() method tests ---

@pytest.mark.integration
def test_extract_returns_completed_response(tmp_path: Path):
    """Happy path: extract returns completed response with correct counts."""
    from app.services.mythos_extraction import MythosExtractionService, MythosExtractionRequest

    json_content = _make_mythos_json_response(
        n_patterns=3, n_structures=2, n_rules=4, n_motifs=5
    )
    inferencer = _FakeMythosInferenceBackend(content=json_content)
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)

    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    request = MythosExtractionRequest(
        text="Zeus threw lightning bolts at the Titans...",
        source_corpus="Greek Mythology",
        generation_mode="same_world",
    )
    response = service.extract(request)

    assert response.status == "completed"
    assert response.project_id is not None and len(response.project_id) > 0
    assert response.extraction is not None
    assert response.extraction.source_corpus == "Greek Mythology"
    assert response.extraction.archetypal_patterns == 3
    assert response.extraction.narrative_structures == 2
    assert response.extraction.cosmic_rules == 4
    assert response.extraction.symbolic_motifs == 5


@pytest.mark.integration
def test_extract_handles_llm_failure(tmp_path: Path):
    """InferenceBackendError should return status='failed' without raising."""
    from app.services.mythos_extraction import MythosExtractionService, MythosExtractionRequest

    class _FailingMythosBackend(InferenceBackend):
        @property
        def descriptor(self) -> InferenceProviderDescriptor:
            return InferenceProviderDescriptor(
                backend="stub",
                display_name="Failing Mythos",
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
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=_FailingMythosBackend(),
        root_dir=tmp_path,
    )

    request = MythosExtractionRequest(
        text="Some mythology text...",
        generation_mode="same_world",
    )
    response = service.extract(request)

    assert response.status == "failed"
    assert response.error is not None
    assert "SERVICE_UNAVAILABLE" in response.error


@pytest.mark.integration
def test_extract_handles_invalid_json_from_llm(tmp_path: Path):
    """Non-JSON LLM output should return status='failed'."""
    from app.services.mythos_extraction import MythosExtractionService, MythosExtractionRequest

    inferencer = _FakeMythosInferenceBackend(content="this is not json at all, just text")
    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    request = MythosExtractionRequest(
        text="Some mythology text...",
        generation_mode="transposed",
    )
    response = service.extract(request)

    assert response.status == "failed"
    assert response.error is not None


# --- Task 6: _transactional_import() tests ---

@pytest.mark.integration
def test_transactional_import_persists_foundation(tmp_path: Path):
    """_transactional_import persists foundation with thematic_spine from analysis."""
    import sqlite3
    from app.services.mythos_extraction import MythosExtractionService
    from app.schemas.mythos_extraction import (
        ArchetypalPattern,
        MythosExtractionAnalysis,
        NarrativeStructure,
    )

    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    inferencer = _FakeMythosInferenceBackend(content="{}")

    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    # Create a project first
    from app.schemas.projects import ProjectCreateRequest
    create_resp = project_service.create_project(
        ProjectCreateRequest(project_name="Test Mythos Project")
    )
    project_id = create_resp.project_id

    analysis = MythosExtractionAnalysis(
        source_corpus="Greek Mythology",
        generation_mode="same_world",
        thematic_spine="Order vs chaos",
        emotional_promise="Awe and terror",
        tone_and_voice_direction="Epic, solemn",
        archetypal_patterns=[
            ArchetypalPattern(
                name="hubris-fall",
                description="Hero rises through arrogance",
                character_type="hubristic hero",
                narrative_beats=["rise", "transgression", "punishment"],
                examples_from_text=["Oedipus defies prophecy"],
            )
        ],
        narrative_structures=[
            NarrativeStructure(
                name="cyclical tragedy",
                phases=["call", "fall", "redemption"],
                tension_curve="escalating",
                resolution_type="bittersweet",
            )
        ],
    )

    service._transactional_import(project_id, analysis)

    # Verify foundation_revisions was persisted
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT thematic_spine, emotional_promise, tone_direction FROM foundation_revisions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert row is not None, "foundation_revisions row not found"
        assert row[0] == "Order vs chaos", f"Expected 'Order vs chaos', got {row[0]}"
        assert row[1] == "Awe and terror", f"Expected 'Awe and terror', got {row[1]}"
        assert row[2] == "Epic, solemn", f"Expected 'Epic, solemn', got {row[2]}"

        # Verify narrative_constraints_json contains patterns and structures
        constraints_row = conn.execute(
            "SELECT narrative_constraints_json FROM foundation_revisions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert constraints_row is not None
        import json as _json
        constraints = _json.loads(constraints_row[0])
        assert "archetypal_patterns" in constraints or "narrative_structures" in constraints
    finally:
        conn.close()


@pytest.mark.integration
def test_transactional_import_persists_world_bible_entries(tmp_path: Path):
    """_transactional_import persists cosmic rules and symbolic motifs as world bible entries."""
    import sqlite3
    from app.services.mythos_extraction import MythosExtractionService
    from app.schemas.mythos_extraction import (
        CosmicRule,
        MythosExtractionAnalysis,
        SymbolicMotif,
    )

    project_service = ProjectService(tmp_path)
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repository = StoryDevelopmentRepository(db_path)
    inferencer = _FakeMythosInferenceBackend(content="{}")

    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    from app.schemas.projects import ProjectCreateRequest
    create_resp = project_service.create_project(
        ProjectCreateRequest(project_name="Test Mythos Project 2")
    )
    project_id = create_resp.project_id

    analysis = MythosExtractionAnalysis(
        source_corpus="Norse Mythology",
        generation_mode="same_world",
        cosmic_rules=[
            CosmicRule(
                rule="Fate cannot be escaped",
                enforcement="The Norns weave destiny",
                exceptions=["Odin can see but not change fate"],
            ),
            CosmicRule(
                rule="Ragnarok is inevitable",
                enforcement="Cosmic cycle of destruction and rebirth",
                exceptions=[],
            ),
        ],
        symbolic_motifs=[
            SymbolicMotif(
                symbol="Yggdrasil",
                meaning="World tree connecting nine realms",
                narrative_function="represents cosmic order and sacrifice",
            ),
        ],
    )

    service._transactional_import(project_id, analysis)

    # Verify world_bible_entries were persisted
    conn = sqlite3.connect(db_path)
    try:
        entries = conn.execute(
            "SELECT entry_type, title, summary FROM world_bible_entries WHERE project_id = ?",
            (project_id,),
        ).fetchall()

        titles = [e[1] for e in entries]
        # Check cosmic rules were persisted
        assert any("Fate cannot be escaped" in t for t in titles), f"Expected fate rule in titles: {titles}"
        assert any("Ragnarok is inevitable" in t for t in titles), f"Expected ragnarok rule in titles: {titles}"
        # Check symbolic motif was persisted
        assert any("Yggdrasil" in t for t in titles), f"Expected Yggdrasil motif in titles: {titles}"

        # Verify at least 3 entries exist (2 rules + 1 motif)
        assert len(entries) >= 3, f"Expected at least 3 world bible entries, got {len(entries)}"
    finally:
        conn.close()
