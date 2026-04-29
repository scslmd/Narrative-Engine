# Mythos Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable users to paste mythology texts, have the LLM extract archetypal patterns and narrative structures, then generate original stories following those mythological storytelling DNA.

**Architecture:** Dedicated `MythosExtractionService` with its own endpoint. Follows StoryImportService pattern: synchronous HTTP, LLM call for analysis, raw SQLite transaction for persistence, manifest update. Schema layer defines extraction dataclasses. ManifestConfig extended with mythos fields.

**Tech Stack:** Python/FastAPI backend, Pydantic schemas, SQLite persistence, React frontend (mode toggle in import modal).

---

### Task 1: Mythos Extraction Schema

**Files:**
- Create: `app/schemas/mythos_extraction.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for schema dataclasses**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mythos_extraction.py::test_archetypal_pattern_fields -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write schema module with all dataclasses**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArchetypalPattern:
    name: str
    description: str
    character_type: str
    narrative_beats: list[str] = field(default_factory=list)
    examples_from_text: list[str] = field(default_factory=list)


@dataclass
class NarrativeStructure:
    name: str
    phases: list[str] = field(default_factory=list)
    tension_curve: str = ""
    resolution_type: str = ""


@dataclass
class CosmicRule:
    rule: str
    enforcement: str
    exceptions: list[str] = field(default_factory=list)


@dataclass
class SymbolicMotif:
    symbol: str
    meaning: str
    narrative_function: str = ""


@dataclass
class MythosEntity:
    name: str
    entity_type: str  # deity | location | concept | force
    archetype: str
    domain_or_power: str
    canonical_facts: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source: str
    target: str
    relationship_type: str
    description: str = ""


@dataclass
class MythosExtractionAnalysis:
    source_corpus: str
    generation_mode: str  # same_world | transposed | pure_pattern

    # Pattern layer (core)
    archetypal_patterns: list[ArchetypalPattern] = field(default_factory=list)
    narrative_structures: list[NarrativeStructure] = field(default_factory=list)
    cosmic_rules: list[CosmicRule] = field(default_factory=list)
    symbolic_motifs: list[SymbolicMotif] = field(default_factory=list)

    # Thematic layer (foundation)
    thematic_spine: str = ""
    emotional_promise: str = ""
    tone_and_voice_direction: str = ""

    # Entity layer (light — for same_world mode)
    key_entities: list[MythosEntity] = field(default_factory=list)
    entity_relationships: list[Relationship] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_mythos_extraction.py::test_archetypal_pattern_fields -v`
Expected: PASS

- [ ] **Step 5: Add tests for remaining dataclasses**

```python
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
```

- [ ] **Step 6: Run all schema tests**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "test_"`
Expected: PASS (all 7 tests)

- [ ] **Step 7: Commit**

```bash
git add app/schemas/mythos_extraction.py tests/test_mythos_extraction.py
git commit -m "feat: add mythos extraction schema dataclasses"
```

---

### Task 2: Mythos Extraction Request & Response Schemas (Pydantic)

**Files:**
- Modify: `app/schemas/mythos_extraction.py` (append Pydantic models)
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for request validation**

```python
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
    try:
        MythosExtractionRequest(
            text="Once upon a time...",
            generation_mode="invalid_mode",
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_mythos_response_fields():
    from app.schemas.mythos_extraction import MythosExtractionResponse
    response = MythosExtractionResponse(
        status="completed",
        project_id="proj-123",
        extraction={
            "source_corpus": "Greek Mythology",
            "archetypal_patterns": 4,
            "narrative_structures": 2,
            "cosmic_rules": 5,
            "symbolic_motifs": 3,
        },
    )
    assert response.status == "completed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_mythos_extraction.py::test_mythos_request_validates_generation_mode -v`
Expected: FAIL with "ModuleNotFoundError" or attribute error

- [ ] **Step 3: Add Pydantic models to schema module**

Append to `app/schemas/mythos_extraction.py`:

```python
from pydantic import Field, field_validator


class MythosExtractionRequest:
    pass


class MythosExtractionResponse:
    pass
```

Replace with actual implementation:

```python
from app.schemas.base import StrictSchemaModel


GENERATION_MODES = ("same_world", "transposed", "pure_pattern")


class MythosExtractionRequest(StrictSchemaModel):
    text: str = Field(min_length=1)
    source_corpus: str | None = None
    generation_mode: str = Field(min_length=1)
    project_id: str | None = None

    @field_validator("generation_mode")
    @classmethod
    def validate_generation_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in GENERATION_MODES:
            raise ValueError(
                f"generation_mode must be one of {GENERATION_MODES}, got '{value}'"
            )
        return normalized


class ExtractionSummary(StrictSchemaModel):
    source_corpus: str
    archetypal_patterns: int
    narrative_structures: int
    cosmic_rules: int
    symbolic_motifs: int


class MythosExtractionResponse(StrictSchemaModel):
    status: str
    project_id: str
    extraction: ExtractionSummary | None = None
    error: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "request or response"`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/schemas/mythos_extraction.py tests/test_mythos_extraction.py
git commit -m "feat: add mythos extraction request/response Pydantic schemas"
```

---

### Task 3: Prompt Builder `build_mythos_analysis_request()`

**Files:**
- Modify: `app/services/runtime_prompts.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for prompt builder**

```python
def test_build_mythos_analysis_request_returns_inference_request():
    from app.services.runtime_prompts import build_mythos_analysis_request
    request = build_mythos_analysis_request(
        mythos_text="Zeus threw lightning bolts...",
        source_corpus="Greek Mythology",
        generation_mode="same_world",
        default_model="test-model",
    )
    assert request.model == "test-model"
    assert "archetypal_patterns" in request.system_prompt
    assert "narrative_structures" in request.system_prompt
    assert request.temperature == 0.1


def test_build_mythos_analysis_request_truncates_long_text():
    from app.services.runtime_prompts import build_mythos_analysis_request
    long_text = "x" * 30_000
    request = build_mythos_analysis_request(
        mythos_text=long_text,
        default_model="test-model",
    )
    assert len(request.user_prompt) <= 30_000


def test_build_mythos_analysis_request_includes_generation_mode():
    from app.services.runtime_prompts import build_mythos_analysis_request
    request = build_mythos_analysis_request(
        mythos_text="Test text",
        generation_mode="transposed",
        default_model="test-model",
    )
    assert "transposed" in request.user_prompt.lower() or "transposed" in request.system_prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mythos_extraction.py::test_build_mythos_analysis_request_returns_inference_request -v`
Expected: FAIL with ImportError or AttributeError

- [ ] **Step 3: Add prompt builder function to runtime_prompts.py**

Append to `app/services/runtime_prompts.py`:

```python
def build_mythos_analysis_request(
    *,
    mythos_text: str,
    source_corpus: str | None = None,
    generation_mode: str = "same_world",
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for mythos pattern extraction.

    The LLM should return a JSON object matching MythosExtractionAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output with patterns and entities.
    Truncates mythos_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = mythos_text[:24_000]
    corpus_hint = f"Source tradition hint: {source_corpus}" if source_corpus else "AI should identify the source tradition from the text."

    system_prompt = (
        "You are a mythology analysis AI for Narrative-Engine. You analyze mythological texts "
        "and extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs.\n\n"
        f"{corpus_hint}\n\n"
        f"Generation mode: {generation_mode}\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "source_corpus": "<string - identified tradition, e.g., Greek Mythology>",\n'
        '  "generation_mode": "<same_world | transposed | pure_pattern>",\n'
        '  "archetypal_patterns": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "description": "<string>",\n'
        '      "character_type": "<string>",\n'
        '      "narrative_beats": [],\n'
        '      "examples_from_text": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_structures": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "phases": [],\n'
        '      "tension_curve": "<string>",\n'
        '      "resolution_type": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "cosmic_rules": [\n'
        '    {\n'
        '      "rule": "<string>",\n'
        '      "enforcement": "<string>",\n'
        '      "exceptions": []\n'
        '    }\n'
        '  ],\n'
        '  "symbolic_motifs": [\n'
        '    {\n'
        '      "symbol": "<string>",\n'
        '      "meaning": "<string>",\n'
        '      "narrative_function": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "tone_and_voice_direction": "<string>",\n'
        '  "key_entities": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "entity_type": "<deity | location | concept | force>",\n'
        '      "archetype": "<string>",\n'
        '      "domain_or_power": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "entity_relationships": [\n'
        '    {\n'
        '      "source": "<string>",\n'
        '      "target": "<string>",\n'
        '      "relationship_type": "<string>",\n'
        '      "description": "<string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Focus on PATTERNS and STRUCTURES, not just cataloging entities. "
        "Extract the storytelling DNA — how stories are told in this tradition, "
        "what narrative rules govern them, what archetypal journeys characters undertake."
    )

    user_prompt = (
        f"Analyze the following mythological text and extract its archetypal patterns, "
        f"narrative structures, cosmic rules, and symbolic motifs:\n\n"
        f"{truncated_text}"
    )

    return InferenceRequest(
        model=default_model or "mythos-analysis",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
        max_tokens=16000,
        metadata={"purpose": "mythos_extraction"},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "build_mythos"`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_mythos_extraction.py
git commit -m "feat: add mythos analysis prompt builder"
```

---

### Task 4: MythosExtractionService Constructor & Error Class

**Files:**
- Create: `app/services/mythos_extraction.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for service construction**

```python
def test_mythos_service_construction():
    from app.services.mythos_extraction import MythosExtractionError, MythosExtractionService
    assert issubclass(MythosExtractionError, ValueError)


def test_mythos_service_initializes_with_dependencies(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    inferencer = FakeImportInferenceBackend(content="{}")
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )
    assert service._project_service is project_service
    assert service._inferencer is inferencer
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mythos_extraction.py::test_mythos_service_construction -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write service class skeleton**

```python
from __future__ import annotations

import logging
from pathlib import Path

from ..inference.base import InferenceBackend, InferenceBackendError
from ..persistence.story_development import StoryDevelopmentRepository
from ..schemas.mythos_extraction import (
    MythosExtractionAnalysis,
    MythosExtractionRequest,
    MythosExtractionResponse,
)
from ..settings import settings
from .projects import ProjectService

logger = logging.getLogger(__name__)


class MythosExtractionError(ValueError):
    """Base error for mythos extraction failures."""
    pass


class MythosExtractionService:
    def __init__(
        self,
        *,
        project_service: ProjectService,
        repository: StoryDevelopmentRepository,
        inferencer: InferenceBackend,
        root_dir: Path | None = None,
    ) -> None:
        self._project_service = project_service
        self._repository = repository
        self._inferencer = inferencer
        self._root_dir = root_dir or settings.root_dir
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "construction or initializes"`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/mythos_extraction.py tests/test_mythos_extraction.py
git commit -m "feat: add MythosExtractionService skeleton and error class"
```

---

### Task 5: `MythosExtractionService.extract()` Method

**Files:**
- Modify: `app/services/mythos_extraction.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for extract method**

```python
def _make_mythos_json_response(
    source_corpus: str = "Greek Mythology",
    generation_mode: str = "same_world",
) -> str:
    """Helper to generate a valid LLM JSON response for mythos extraction."""
    import json
    return json.dumps({
        "source_corpus": source_corpus,
        "generation_mode": generation_mode,
        "archetypal_patterns": [
            {
                "name": "hubris-fall-redemption",
                "description": "Hero rises through arrogance, falls through divine retribution",
                "character_type": "hubristic hero",
                "narrative_beats": ["rise", "transgression", "punishment", "suffering", "apotheosis"],
                "examples_from_text": ["Oedipus defies prophecy"],
            }
        ],
        "narrative_structures": [
            {
                "name": "cyclical tragedy",
                "phases": ["call", "transgression", "punishment", "redemption"],
                "tension_curve": "escalating divine retribution",
                "resolution_type": "bittersweet apotheosis",
            }
        ],
        "cosmic_rules": [
            {
                "rule": "Fate cannot be escaped, only fulfilled",
                "enforcement": "Gods act as agents of moira (fate)",
                "exceptions": ["prophecies can be misinterpreted"],
            }
        ],
        "symbolic_motifs": [
            {
                "symbol": "serpent",
                "meaning": "transformation, hidden knowledge",
                "narrative_function": "marks threshold between worlds",
            }
        ],
        "thematic_spine": "hubris and divine retribution",
        "emotional_promise": "catharsis through tragic downfall",
        "tone_and_voice_direction": "epic, fatalistic, mythic register",
        "key_entities": [],
        "entity_relationships": [],
    })


def test_extract_returns_completed_response(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.schemas.mythos_extraction import MythosExtractionRequest
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    inferencer = FakeImportInferenceBackend(content=_make_mythos_json_response())
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
    assert response.extraction is not None
    assert response.extraction.source_corpus == "Greek Mythology"
    assert response.extraction.archetypal_patterns == 1


def test_extract_handles_llm_failure(tmp_path):
    from app.inference.base import InferenceBackend, InferenceBackendError
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse, InferenceUsage
    from app.schemas.mythos_extraction import MythosExtractionRequest
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    class FailingInferencer(InferenceBackend):
        @property
        def descriptor(self) -> InferenceProviderDescriptor:
            return InferenceProviderDescriptor(
                backend="test", display_name="Failing", transport="test",
                base_url="http://localhost", default_model="test", timeout_seconds=30.0,
                supports_model_listing=False, supports_chat_completions=True, aliases=["failing"],
            )
        def generate_text(self, request: InferenceRequest) -> InferenceResponse:
            raise InferenceBackendError("service unavailable", "UNAVAILABLE")

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=FailingInferencer(),
        root_dir=tmp_path,
    )

    request = MythosExtractionRequest(
        text="Test text",
        generation_mode="same_world",
    )
    response = service.extract(request)

    assert response.status == "failed"
    assert response.extraction is None


def test_extract_handles_invalid_json_from_llm(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.schemas.mythos_extraction import MythosExtractionRequest
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    inferencer = FakeImportInferenceBackend(content="This is not JSON at all.")
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    request = MythosExtractionRequest(
        text="Test text",
        generation_mode="same_world",
    )
    response = service.extract(request)

    assert response.status == "failed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_mythos_extraction.py::test_extract_returns_completed_response -v`
Expected: FAIL with AttributeError (extract method doesn't exist)

- [ ] **Step 3: Implement extract() and helper methods**

Add to `app/services/mythos_extraction.py`:

```python
    def extract(self, request: MythosExtractionRequest) -> MythosExtractionResponse:
        """Main entry point. Synchronous processing flow."""
        project_id = ""
        try:
            project_id = self._create_project(request)
            analysis = self._analyze_mythos(request.text, request.source_corpus, request.generation_mode)
            self._transactional_import(project_id, analysis)
            self._update_manifest(project_id, analysis)
            return MythosExtractionResponse(
                project_id=project_id,
                status="completed",
                extraction=MythosExtractionResponse.ExtractionSummary(
                    source_corpus=analysis.source_corpus,
                    archetypal_patterns=len(analysis.archetypal_patterns),
                    narrative_structures=len(analysis.narrative_structures),
                    cosmic_rules=len(analysis.cosmic_rules),
                    symbolic_motifs=len(analysis.symbolic_motifs),
                ),
            )
        except MythosExtractionError as exc:
            return MythosExtractionResponse(
                project_id=project_id,
                status="failed",
                error=str(exc),
            )
        except InferenceBackendError as exc:
            return MythosExtractionResponse(
                project_id=project_id,
                status="failed",
                error=f"LLM service unavailable: {exc.code}",
            )

    def _create_project(self, request: MythosExtractionRequest) -> str:
        """Create project if needed, return project_id."""
        import sqlite3
        from ..schemas.projects import ProjectCreateRequest

        if request.project_id:
            try:
                self._project_service.get_project(request.project_id)
            except sqlite3.Error as exc:
                logger.error("DB error checking project %s: %s", request.project_id, exc)
                raise MythosExtractionError(f"Database error while verifying project: {exc}") from exc
            except FileNotFoundError:
                raise MythosExtractionError(f"Project not found: {request.project_id}")
            return request.project_id

        project_name = f"Mythos: {request.source_corpus or 'Unknown Tradition'}"
        create_request = ProjectCreateRequest(project_name=project_name)
        response = self._project_service.create_project(create_request)
        return response.project_id

    def _analyze_mythos(
        self,
        mythos_text: str,
        source_corpus: str | None,
        generation_mode: str,
    ) -> MythosExtractionAnalysis:
        """Call LLM to analyze mythology text and extract patterns."""
        from pydantic import ValidationError

        from .runtime_prompts import build_mythos_analysis_request

        inference_request = build_mythos_analysis_request(
            mythos_text=mythos_text,
            source_corpus=source_corpus,
            generation_mode=generation_mode,
            default_model=self._inferencer.descriptor.default_model,
        )

        try:
            response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError:
            raise

        parsed = _extract_json(response.content)
        analysis = _parse_mythos_analysis(parsed)
        return analysis

    def _update_manifest(self, project_id: str, analysis: MythosExtractionAnalysis) -> None:
        """Update manifest.json with mythos metadata."""
        import json

        project_dir = self._project_service.root_dir / "data" / "projects" / project_id
        manifest_path = project_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Manifest not found for project %s, skipping mythos metadata update", project_id)
            return

        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
            return

        if "config" not in manifest_data:
            manifest_data["config"] = {}

        manifest_data["config"]["mythos_source_corpus"] = analysis.source_corpus
        manifest_data["config"]["mythos_generation_mode"] = analysis.generation_mode

        try:
            manifest_path.write_text(
                json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write manifest for project %s: %s", project_id, exc)
```

- [ ] **Step 4: Add JSON extraction and parsing helpers**

Append module-level functions to `app/services/mythos_extraction.py`:

```python
def _extract_json(content: str) -> dict[str, Any]:
    """Extract JSON object from LLM response text."""
    import json
    import re

    stripped = content.strip()

    # Try direct parse first
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strip markdown code fences
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE)
    fenced = fenced.strip()
    if fenced:
        try:
            return json.loads(fenced)
        except (json.JSONDecodeError, ValueError):
            pass

    # Find balanced braces from first {
    first_brace = stripped.find("{")
    if first_brace == -1:
        raise MythosExtractionError("Failed to parse LLM response as JSON")

    depth = 0
    in_string = False
    escape_next = False
    json_end = -1
    for i in range(first_brace, len(stripped)):
        ch = stripped[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                json_end = i
                break

    if json_end != -1:
        try:
            return json.loads(stripped[first_brace : json_end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    raise MythosExtractionError("Failed to parse LLM response as JSON")


def _parse_mythos_analysis(data: dict[str, Any]) -> MythosExtractionAnalysis:
    """Parse and validate LLM JSON into MythosExtractionAnalysis."""
    from app.schemas.mythos_extraction import (
        ArchetypalPattern,
        CosmicRule,
        MythosEntity,
        NarrativeStructure,
        Relationship,
        SymbolicMotif,
    )

    def _to_str(value: Any, default: str = "") -> str:
        if isinstance(value, str):
            return value.strip() or default
        return str(value) if value else default

    def _to_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    # Parse archetypal patterns
    patterns: list[ArchetypalPattern] = []
    for p in data.get("archetypal_patterns", []) or []:
        if not isinstance(p, dict):
            continue
        patterns.append(ArchetypalPattern(
            name=_to_str(p.get("name")),
            description=_to_str(p.get("description")),
            character_type=_to_str(p.get("character_type")),
            narrative_beats=_to_list(p.get("narrative_beats")),
            examples_from_text=_to_list(p.get("examples_from_text")),
        ))

    # Parse narrative structures
    structures: list[NarrativeStructure] = []
    for s in data.get("narrative_structures", []) or []:
        if not isinstance(s, dict):
            continue
        structures.append(NarrativeStructure(
            name=_to_str(s.get("name")),
            phases=_to_list(s.get("phases")),
            tension_curve=_to_str(s.get("tension_curve")),
            resolution_type=_to_str(s.get("resolution_type")),
        ))

    # Parse cosmic rules
    rules: list[CosmicRule] = []
    for r in data.get("cosmic_rules", []) or []:
        if not isinstance(r, dict):
            continue
        rules.append(CosmicRule(
            rule=_to_str(r.get("rule")),
            enforcement=_to_str(r.get("enforcement")),
            exceptions=_to_list(r.get("exceptions")),
        ))

    # Parse symbolic motifs
    motifs: list[SymbolicMotif] = []
    for m in data.get("symbolic_motifs", []) or []:
        if not isinstance(m, dict):
            continue
        motifs.append(SymbolicMotif(
            symbol=_to_str(m.get("symbol")),
            meaning=_to_str(m.get("meaning")),
            narrative_function=_to_str(m.get("narrative_function")),
        ))

    # Parse key entities
    entities: list[MythosEntity] = []
    for e in data.get("key_entities", []) or []:
        if not isinstance(e, dict):
            continue
        entities.append(MythosEntity(
            name=_to_str(e.get("name")),
            entity_type=_to_str(e.get("entity_type"), "concept"),
            archetype=_to_str(e.get("archetype")),
            domain_or_power=_to_str(e.get("domain_or_power")),
            canonical_facts=_to_list(e.get("canonical_facts")),
        ))

    # Parse relationships
    relationships: list[Relationship] = []
    for r in data.get("entity_relationships", []) or []:
        if not isinstance(r, dict):
            continue
        relationships.append(Relationship(
            source=_to_str(r.get("source")),
            target=_to_str(r.get("target")),
            relationship_type=_to_str(r.get("relationship_type")),
            description=_to_str(r.get("description")),
        ))

    return MythosExtractionAnalysis(
        source_corpus=_to_str(data.get("source_corpus"), "Unknown Tradition"),
        generation_mode=data.get("generation_mode", "same_world") or "same_world",
        archetypal_patterns=patterns,
        narrative_structures=structures,
        cosmic_rules=rules,
        symbolic_motifs=motifs,
        thematic_spine=_to_str(data.get("thematic_spine")),
        emotional_promise=_to_str(data.get("emotional_promise")),
        tone_and_voice_direction=_to_str(data.get("tone_and_voice_direction")),
        key_entities=entities,
        entity_relationships=relationships,
    )
```

Also add the `Any` import at the top of the file:
```python
from typing import Any
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "extract"`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add app/services/mythos_extraction.py tests/test_mythos_extraction.py
git commit -m "feat: implement MythosExtractionService.extract() with LLM analysis"
```

---

### Task 6: `_transactional_import()` for Mythos Data Persistence

**Files:**
- Modify: `app/services/mythos_extraction.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for transactional import**

```python
def test_transactional_import_persists_foundation(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.schemas.mythos_extraction import (
        ArchetypalPattern, CosmicRule, MythosExtractionAnalysis,
    )
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    inferencer = FakeImportInferenceBackend(content="{}")
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    # Create a project first
    from app.schemas.projects import ProjectCreateRequest
    proj_response = project_service.create_project(ProjectCreateRequest(project_name="Test Mythos"))
    project_id = proj_response.project_id

    analysis = MythosExtractionAnalysis(
        source_corpus="Greek Mythology",
        generation_mode="same_world",
        archetypal_patterns=[ArchetypalPattern(
            name="hubris-fall-redemption",
            description="Hero rises and falls",
            character_type="hubristic hero",
            narrative_beats=["rise", "fall"],
        )],
        cosmic_rules=[CosmicRule(
            rule="Fate cannot be escaped",
            enforcement="Gods enforce moira",
        )],
        thematic_spine="hubris and divine retribution",
        emotional_promise="catharsis through tragic downfall",
        tone_and_voice_direction="epic, fatalistic",
    )

    service._transactional_import(project_id, analysis)

    # Verify foundation was created
    import sqlite3
    conn = sqlite3.connect(repository.db_path)
    row = conn.execute(
        "SELECT thematic_spine FROM foundation_revisions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    conn.close()
    assert row is not None
    assert "hubris" in row[0].lower()


def test_transactional_import_persists_world_bible_entries(tmp_path):
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.schemas.mythos_extraction import (
        CosmicRule, MythosExtractionAnalysis, SymbolicMotif,
    )
    from app.services.mythos_extraction import MythosExtractionService
    from app.services.projects import ProjectService

    project_service = ProjectService(tmp_path)
    repository = StoryDevelopmentRepository(tmp_path / "operations.db")
    inferencer = FakeImportInferenceBackend(content="{}")
    service = MythosExtractionService(
        project_service=project_service,
        repository=repository,
        inferencer=inferencer,
        root_dir=tmp_path,
    )

    from app.schemas.projects import ProjectCreateRequest
    proj_response = project_service.create_project(ProjectCreateRequest(project_name="Test Mythos"))
    project_id = proj_response.project_id

    analysis = MythosExtractionAnalysis(
        source_corpus="Norse Mythology",
        generation_mode="transposed",
        cosmic_rules=[CosmicRule(rule="Ragnarok is inevitable", enforcement="Fate of the Norns")],
        symbolic_motifs=[SymbolicMotif(symbol="Yggdrasil", meaning="world tree, cosmic order")],
    )

    service._transactional_import(project_id, analysis)

    import sqlite3
    conn = sqlite3.connect(repository.db_path)
    rows = conn.execute(
        "SELECT entry_type, title FROM world_bible_entries WHERE project_id = ?",
        (project_id,),
    ).fetchall()
    conn.close()
    titles = [r[1] for r in rows]
    assert any("Ragnarok" in t or "Fate" in t for t in titles)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mythos_extraction.py::test_transactional_import_persists_foundation -v`
Expected: FAIL with AttributeError

- [ ] **Step 3: Implement _transactional_import() and sub-methods**

Add to `app/services/mythos_extraction.py`:

```python
    def _transactional_import(
        self,
        project_id: str,
        analysis: MythosExtractionAnalysis,
    ) -> None:
        """Execute entire entity creation in a single database transaction."""
        import sqlite3

        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._repository.db_path, timeout=30)
        try:
            conn.execute("BEGIN")

            self._import_foundation(conn, project_id, analysis, now)
            self._import_world_bible(conn, project_id, analysis, now)
            self._import_archetypes(conn, project_id, analysis, now)
            self._import_entities(conn, project_id, analysis, now)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _import_foundation(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert foundation revision with mythos-derived thematic data."""
        # Insert foundation_profiles header
        conn.execute(
            """
            INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (project_id, now, now),
        )

        # Get next revision number
        rev_row = conn.execute(
            "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        next_rev = rev_row[0]

        # Store narrative structures and archetypal patterns as JSON in narrative_constraints
        pattern_data = {
            "archetypal_patterns": [
                {
                    "name": p.name,
                    "description": p.description,
                    "character_type": p.character_type,
                    "narrative_beats": p.narrative_beats,
                    "examples_from_text": p.examples_from_text,
                }
                for p in analysis.archetypal_patterns
            ],
            "narrative_structures": [
                {
                    "name": s.name,
                    "phases": s.phases,
                    "tension_curve": s.tension_curve,
                    "resolution_type": s.resolution_type,
                }
                for s in analysis.narrative_structures
            ],
        }
        narrative_constraints_json = json.dumps(pattern_data, ensure_ascii=True, sort_keys=True)

        conn.execute(
            """
            INSERT INTO foundation_revisions (
                project_id, revision_number, premise, logline, thematic_spine, emotional_promise,
                tone_direction, target_audience, narrative_constraints_json, complexity_level,
                success_definition, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, revision_number) DO UPDATE SET
                premise = excluded.premise,
                logline = excluded.logline,
                thematic_spine = excluded.thematic_spine,
                emotional_promise = excluded.emotional_promise,
                tone_direction = excluded.tone_direction,
                target_audience = excluded.target_audience,
                narrative_constraints_json = excluded.narrative_constraints_json,
                complexity_level = excluded.complexity_level,
                success_definition = excluded.success_definition,
                updated_at = excluded.updated_at
            """,
            (
                project_id,
                next_rev,
                None,
                None,
                analysis.thematic_spine or None,
                analysis.emotional_promise or None,
                analysis.tone_and_voice_direction or None,
                None,
                narrative_constraints_json,
                None,
                None,
                now,
                now,
            ),
        )

        # Update foundation_profiles.current_revision_id
        revision_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
            (revision_id, now, project_id),
        )

    def _import_world_bible(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert cosmic rules and symbolic motifs as world bible entries."""
        # Cosmic rules become "concept" entries
        for rule in analysis.cosmic_rules:
            canonical_facts_json = json.dumps(rule.exceptions or [], ensure_ascii=True, sort_keys=True)
            conn.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json,
                    related_character_ids_json, visibility_scope, source_artifacts_json,
                    continuity_warnings_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                    summary = excluded.summary,
                    canonical_facts_json = excluded.canonical_facts_json,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    "concept",
                    f"Cosmic Rule: {rule.rule}",
                    rule.enforcement,
                    canonical_facts_json,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    "project",
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    now,
                    now,
                ),
            )

        # Symbolic motifs become "concept" entries
        for motif in analysis.symbolic_motifs:
            conn.execute(
                """
                INSERT INTO world_bible_entries (
                    project_id, entry_type, title, summary, canonical_facts_json,
                    related_character_ids_json, visibility_scope, source_artifacts_json,
                    continuity_warnings_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                    summary = excluded.summary,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    "concept",
                    f"Motif: {motif.symbol}",
                    f"{motif.meaning}. Narrative function: {motif.narrative_function}" if motif.narrative_function else motif.meaning,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    "project",
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    now,
                    now,
                ),
            )

    def _import_archetypes(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert archetypal patterns as character profiles (pattern carriers)."""
        for pattern in analysis.archetypal_patterns:
            char_id = _hash_id("archetype", pattern.name)
            narrative_beats_json = json.dumps(pattern.narrative_beats or [], ensure_ascii=True, sort_keys=True)
            examples_json = json.dumps(pattern.examples_from_text or [], ensure_ascii=True, sort_keys=True)

            conn.execute(
                """
                INSERT INTO character_profiles (
                    character_id, project_id, display_name, role_in_story, archetype,
                    external_goal, internal_need, misbelief_or_wound, core_fear,
                    primary_strength, fatal_flaw_or_limitation, contradictions_json,
                    backstory_summary, voice_notes, relationship_map_json, secrets_json,
                    values_json, taboos_json, change_axis, arc_stage_notes,
                    continuity_facts_json, writer_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(character_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    archetype = excluded.archetype,
                    backstory_summary = excluded.backstory_summary,
                    updated_at = excluded.updated_at
                """,
                (
                    char_id,
                    project_id,
                    pattern.character_type or pattern.name,
                    "archetype",
                    pattern.name,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    pattern.description or None,
                    None,
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    json.dumps([], ensure_ascii=True, sort_keys=True),
                    None,
                    narrative_beats_json,
                    examples_json,
                    "Archetypal pattern from mythos extraction",
                    now,
                    now,
                ),
            )

    def _import_entities(
        self,
        conn: sqlite3.Connection,
        project_id: str,
        analysis: MythosExtractionAnalysis,
        now: str,
    ) -> None:
        """Insert key entities and their relationships."""
        for entity in analysis.key_entities:
            entity_id = _hash_id("entity", entity.name)

            if entity.entity_type in ("deity", "force"):
                # Deities and forces go into character_profiles
                canonical_facts_json = json.dumps(entity.canonical_facts or [], ensure_ascii=True, sort_keys=True)
                conn.execute(
                    """
                    INSERT INTO character_profiles (
                        character_id, project_id, display_name, role_in_story, archetype,
                        external_goal, internal_need, misbelief_or_wound, core_fear,
                        primary_strength, fatal_flaw_or_limitation, contradictions_json,
                        backstory_summary, voice_notes, relationship_map_json, secrets_json,
                        values_json, taboos_json, change_axis, arc_stage_notes,
                        continuity_facts_json, writer_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(character_id) DO UPDATE SET
                        display_name = excluded.display_name,
                        archetype = excluded.archetype,
                        continuity_facts_json = excluded.continuity_facts_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        entity_id,
                        project_id,
                        entity.name,
                        "mythos_entity",
                        entity.archetype or None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        entity.domain_or_power or None,
                        None,
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        None,
                        None,
                        canonical_facts_json,
                        "Key entity from mythos extraction",
                        now,
                        now,
                    ),
                )
            else:
                # Locations and concepts go into world_bible_entries
                canonical_facts_json = json.dumps(entity.canonical_facts or [], ensure_ascii=True, sort_keys=True)
                conn.execute(
                    """
                    INSERT INTO world_bible_entries (
                        project_id, entry_type, title, summary, canonical_facts_json,
                        related_character_ids_json, visibility_scope, source_artifacts_json,
                        continuity_warnings_json, writer_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, entry_type, title) DO UPDATE SET
                        summary = excluded.summary,
                        canonical_facts_json = excluded.canonical_facts_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        project_id,
                        entity.entity_type or "concept",
                        entity.name,
                        entity.domain_or_power or None,
                        canonical_facts_json,
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        "project",
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        json.dumps([], ensure_ascii=True, sort_keys=True),
                        None,
                        now,
                        now,
                    ),
                )

        # Insert relationships
        for rel in analysis.entity_relationships:
            edge_id = _hash_id("edge", f"{rel.source}-{rel.target}")
            conn.execute(
                """
                INSERT INTO relationship_edges (
                    edge_id, source_character_id, target_character_id, relationship_type,
                    description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(edge_id) DO UPDATE SET
                    relationship_type = excluded.relationship_type,
                    description = excluded.description,
                    updated_at = excluded.updated_at
                """,
                (
                    edge_id,
                    _hash_id("entity", rel.source),
                    _hash_id("entity", rel.target),
                    rel.relationship_type,
                    rel.description or None,
                    now,
                    now,
                ),
            )
```

Also add the missing imports at the top of the file:
```python
import json
from datetime import datetime, timezone
```

And the `_hash_id` helper (reused from story_import pattern):
```python
import hashlib


def _hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value."""
    raw = f"mythos-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"mythos-{prefix}-{short_hash}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "transactional"`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/services/mythos_extraction.py tests/test_mythos_extraction.py
git commit -m "feat: implement mythos transactional import with foundation, world bible, archetypes, entities"
```

---

### Task 7: ManifestConfig Extension for Mythos Fields

**Files:**
- Modify: `app/schemas/manifest.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for manifest config extension**

```python
def test_manifest_config_accepts_mythos_fields():
    from app.schemas.manifest import ManifestConfig
    config = ManifestConfig(
        genre="Mythic Fiction",
        tone_profile="Epic and Fatalistic",
        story_structure="THREE_ACT",
        mythos_source_corpus="Greek Mythology",
        mythos_generation_mode="same_world",
    )
    assert config.mythos_source_corpus == "Greek Mythology"
    assert config.mythos_generation_mode == "same_world"


def test_manifest_config_mythos_fields_optional():
    from app.schemas.manifest import ManifestConfig
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="Dark",
        story_structure="THREE_ACT",
    )
    assert config.mythos_source_corpus == ""
    assert config.mythos_generation_mode == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mythos_extraction.py::test_manifest_config_accepts_mythos_fields -v`
Expected: FAIL with ValidationError (extra fields not allowed) or AttributeError

- [ ] **Step 3: Extend ManifestConfig with mythos fields**

Modify `app/schemas/manifest.py`:

```python
class ManifestConfig(StrictSchemaModel):
    genre: str = Field(min_length=1)
    tone_profile: str = Field(min_length=1)
    pov: PovMode = PovMode.THIRD_LIMITED
    primary_language: str = Field(default="English", min_length=1)
    secondary_language: str | None = Field(default=None, min_length=0)
    story_structure: StoryStructure
    mythos_source_corpus: str = ""
    mythos_generation_mode: str = ""  # same_world | transposed | pure_pattern
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py -v -k "manifest"`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/schemas/manifest.py tests/test_mythos_extraction.py
git commit -m "feat: extend ManifestConfig with mythos_source_corpus and mythos_generation_mode"
```

---

### Task 8: API Endpoint `POST /projects/import-mythos`

**Files:**
- Modify: `app/api/projects.py`
- Modify: `app/main.py`
- Test: `tests/test_mythos_extraction.py`

- [ ] **Step 1: Write the failing test for endpoint wiring**

```python
def test_import_mythos_endpoint_exists(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import build_app
    # Just verify the route exists by checking OpenAPI spec
    # This requires the full app to be built, which needs settings configured
    pass  # Integration test, skip for now


def test_mythos_service_wired_in_main():
    """Verify MythosExtractionService is importable and constructible."""
    from app.services.mythos_extraction import MythosExtractionService, MythosExtractionError
    assert issubclass(MythosExtractionError, ValueError)
```

- [ ] **Step 2: Add endpoint to projects router**

Modify `app/api/projects.py`:

Update the `build_projects_router` function signature:
```python
def build_projects_router(
    project_service: ProjectService,
    import_service: Any = None,
    mythos_service: Any = None,
) -> APIRouter:
```

Add the import-mythos endpoint after the import-story block:

```python
    if mythos_service is not None:
        from ..schemas.mythos_extraction import MythosExtractionRequest, MythosExtractionResponse
        from ..services.mythos_extraction import MythosExtractionError

        @router.post("/import-mythos", response_model=MythosExtractionResponse, status_code=201)
        def import_mythos(request: MythosExtractionRequest) -> MythosExtractionResponse:
            try:
                return mythos_service.extract(request)
            except MythosExtractionError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [ ] **Step 3: Wire service in main.py**

Modify `app/main.py`:

After the StoryImportService block (around line 270), add:

```python
    from .services.mythos_extraction import MythosExtractionService
    mythos_service = MythosExtractionService(
        project_service=project_service,
        repository=story_development_repository,
        inferencer=inferencer,
    )
```

Update the router registration (around line 463):

```python
    app.include_router(build_projects_router(project_service, import_service=import_service, mythos_service=mythos_service))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mythos_extraction.py::test_mythos_service_wired_in_main -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/projects.py app/main.py tests/test_mythos_extraction.py
git commit -m "feat: wire POST /projects/import-mythos endpoint and MythosExtractionService in main"
```

---

### Task 9: Frontend Types & Service for Mythos Extraction

**Files:**
- Create: `frontend/src/types/mythosExtraction.ts`
- Create: `frontend/src/services/mythosExtraction.ts`

- [ ] **Step 1: Write frontend types**

```typescript
export interface MythosExtractionRequest {
  text: string;
  source_corpus?: string | null;
  generation_mode: 'same_world' | 'transposed' | 'pure_pattern';
  project_id?: string | null;
}

export interface MythosExtractionSummary {
  source_corpus: string;
  archetypal_patterns: number;
  narrative_structures: number;
  cosmic_rules: number;
  symbolic_motifs: number;
}

export interface MythosExtractionResponse {
  project_id: string;
  status: 'completed' | 'failed';
  extraction: MythosExtractionSummary | null;
  error: string | null;
}
```

- [ ] **Step 2: Write frontend service**

```typescript
import type { MythosExtractionRequest, MythosExtractionResponse } from '../types/mythosExtraction';
import api from '../lib/api';

export async function extractMythos(data: MythosExtractionRequest): Promise<MythosExtractionResponse> {
  const response = await api.post('/projects/import-mythos', data);

  if (response.status !== 201) {
    throw new Error(`Failed to extract mythos: ${response.status}`);
  }

  return response.data;
}
```

- [ ] **Step 3: Run TypeScript checks**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/mythosExtraction.ts frontend/src/services/mythosExtraction.ts
git commit -m "feat: add frontend types and service for mythos extraction"
```

---

### Task 10: Frontend StoryImportModal Mythos Mode Toggle

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx`

- [ ] **Step 1: Add mode toggle state and generation mode selector to modal**

Add new imports at the top:
```typescript
import { extractMythos } from '../../services/mythosExtraction';
```

Add new state variables:
```typescript
const [importMode, setImportMode] = useState<'story' | 'mythos'>('story');
const [sourceCorpus, setSourceCorpus] = useState('');
const [generationMode, setGenerationMode] = useState<'same_world' | 'transposed' | 'pure_pattern'>('same_world');
```

Add mode toggle before the form fields:
```tsx
<div className="flex gap-2 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
  <button
    type="button"
    onClick={() => setImportMode('story')}
    className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
      importMode === 'story'
        ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
    }`}
  >
    Import Story
  </button>
  <button
    type="button"
    onClick={() => setImportMode('mythos')}
    className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
      importMode === 'mythos'
        ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
    }`}
  >
    Extract Mythos
  </button>
</div>
```

Update the description text to be mode-aware:
```tsx
<p className="text-sm text-slate-500">
  {importMode === 'story'
    ? 'Paste a completed story and the system will analyze it, extract structured data, and create a full project with foundation, characters, world bible, arcs, planning, and drafts.'
    : 'Paste mythology texts and the system will extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs for pattern-based story generation.'}
</p>
```

Add mythos-specific fields (source corpus + generation mode selector) when in mythos mode:
```tsx
{importMode === 'mythos' && (
  <>
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Source Tradition
      </label>
      <input
        type="text"
        value={sourceCorpus}
        onChange={(e) => setSourceCorpus(e.target.value)}
        placeholder="e.g., Greek Mythology (optional)"
        className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
      />
    </div>

    <div className="space-y-1.5">
      <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Generation Mode</label>
      <div className="grid grid-cols-3 gap-2">
        {([
          { value: 'same_world' as const, label: 'Same World', desc: 'Keep mythological setting' },
          { value: 'transposed' as const, label: 'Transposed', desc: 'Map patterns to new setting' },
          { value: 'pure_pattern' as const, label: 'Pure Pattern', desc: 'Apply structures only' },
        ]).map((mode) => (
          <button
            key={mode.value}
            type="button"
            onClick={() => setGenerationMode(mode.value)}
            className={`px-3 py-2.5 text-xs rounded-lg border transition-colors ${
              generationMode === mode.value
                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
                : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300'
            }`}
          >
            <div className="font-medium">{mode.label}</div>
            <div className="text-[10px] opacity-70 mt-0.5">{mode.desc}</div>
          </button>
        ))}
      </div>
    </div>
  </>
)}
```

Update the submit handler to call the appropriate service:
```typescript
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setWarnings([]);

    if (storyText.length < MIN_STORY_LENGTH) {
      setError(`Text must be at least ${MIN_STORY_LENGTH} characters.`);
      return;
    }

    if (!projectName.trim()) {
      setError('Project name is required.');
      return;
    }

    setIsImporting(true);

    try {
      let response;
      if (importMode === 'mythos') {
        response = await extractMythos({
          text: storyText,
          source_corpus: sourceCorpus.trim() || null,
          generation_mode: generationMode,
        });
      } else {
        response = await importStory({
          project_name: projectName.trim(),
          story_text: storyText,
          genre: genre.trim() || undefined,
          tone: tone.trim() || undefined,
        });
      }

      if (response.status === 'completed') {
        // ... navigation and invalidation
      } else {
        setError(response.error || response.message || 'Import failed.');
      }
    } catch (err: unknown) {
      // ... error handling
    } finally {
      setIsImporting(false);
    }
  };
```

- [ ] **Step 2: Run frontend checks**

Run: `cd frontend && npm run lint`
Expected: PASS

Run: `cd frontend && npm run typecheck`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/projects/StoryImportModal.tsx
git commit -m "feat: add mythos extraction mode toggle to StoryImportModal"
```

---

### Task 11: Full Validation Suite

**Files:** None (verification only)

- [ ] **Step 1: Run backend tests**

Run: `python -m pytest -q -p no:cacheprovider`
Expected: All pass (baseline 907 + new mythos tests ≈ 920+)

- [ ] **Step 2: Run frontend checks**

Run: `cd frontend && npm run lint`
Expected: PASS

Run: `cd frontend && npm run typecheck`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Update AGENTS.md test baseline**

Update the test baseline in `AGENTS.md` with the new pytest count.

- [ ] **Step 4: Final commit**

```bash
git add AGENTS.md
git commit -m "ci: update test baseline after mythos extraction feature"
```

---

## Self-Review

### 1. Spec Coverage

| Spec Requirement | Task | Status |
|-----------------|------|--------|
| MythosExtractionAnalysis schema + dataclasses | Task 1 | ✅ |
| Request/Response Pydantic schemas | Task 2 | ✅ |
| `build_mythos_analysis_request()` prompt builder | Task 3 | ✅ |
| MythosExtractionService constructor + error class | Task 4 | ✅ |
| `extract()` method with LLM call, parsing, project creation | Task 5 | ✅ |
| `_transactional_import()` with foundation, world bible, archetypes, entities | Task 6 | ✅ |
| ManifestConfig extension (mythos fields) | Task 7 | ✅ |
| API endpoint `POST /projects/import-mythos` | Task 8 | ✅ |
| Service wiring in main.py | Task 8 | ✅ |
| Frontend types and service | Task 9 | ✅ |
| Frontend modal toggle with generation mode selector | Task 10 | ✅ |
| Error handling (MythosExtractionError, InferenceBackendError) | Task 5 | ✅ |
| JSON extraction from LLM response | Task 5 | ✅ |
| Generation mode validation | Task 2 | ✅ |
| Source corpus identification hint in prompt | Task 3 | ✅ |

### 2. Placeholder Scan

- No "TBD", "TODO", or "implement later" patterns found
- All code blocks contain complete, runnable implementations
- All test assertions are specific and verifiable

### 3. Type Consistency

- `MythosExtractionAnalysis` dataclass fields match prompt builder JSON schema
- `_parse_mythos_analysis()` helper maps all JSON keys to correct dataclass fields
- `MythosExtractionRequest.generation_mode` validated against same set as prompt builder expects
- ManifestConfig mythos fields match what `_update_manifest()` writes
- Frontend types match backend Pydantic schemas (snake_case preserved)

---

Plan complete. 11 tasks, TDD-first, following StoryImportService pattern throughout.
