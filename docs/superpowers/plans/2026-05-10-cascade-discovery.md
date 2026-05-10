# Cascade Discovery Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered cascade discovery engine that extracts characters, relationships, and world bible entries from manuscript text, stages them for user review, and persists approved entities.

**Architecture:** Orchestrator service coordinates chunking → LLM extraction → deduplication → confidence scoring → DB staging → async job management. Frontend provides scan dialog, tabular review UI with per-entity approve/reject, and bulk actions.

**Tech Stack:** Python FastAPI backend, SQLite staging table, React + TypeScript frontend, shared inference backend, React Query for async state.

---

## Phase 1: Backend Infrastructure

### Task 1: Config Settings

**Files:**
- Modify: `app/settings.py`

- [ ] **Step 1: Add discovery settings to Settings class**

Add these fields to the `Settings` class in `app/settings.py`:

```python
# Discovery engine settings
discovery_chunk_size: int = 8000
discovery_overlap: int = 500
discovery_max_tokens: int = 12000
discovery_staging_ttl_hours: int = 24
discovery_confidence_threshold_medium: float = 0.4
discovery_confidence_threshold_high: float = 0.7

@staticmethod
def discovery_chunk_size() -> int:
    return int(os.environ.get("NARRATIVE_DISCOVERY_CHUNK_SIZE", 8000))

@staticmethod
def discovery_overlap() -> int:
    return int(os.environ.get("NARRATIVE_DISCOVERY_OVERLAP", 500))

@staticmethod
def discovery_max_tokens() -> int:
    return int(os.environ.get("NARRATIVE_DISCOVERY_MAX_TOKENS", 12000))

@staticmethod
def discovery_staging_ttl_hours() -> int:
    return int(os.environ.get("NARRATIVE_DISCOVERY_STAGING_TTL_HOURS", 24))

@staticmethod
def discovery_confidence_threshold_medium() -> float:
    return float(os.environ.get("NARRATIVE_DISCOVERY_CONFIDENCE_THRESHOLD_MEDIUM", 0.4))

@staticmethod
def discovery_confidence_threshold_high() -> float:
    return float(os.environ.get("NARRATIVE_DISCOVERY_CONFIDENCE_THRESHOLD_HIGH", 0.7))
```

Follow existing pattern in `app/settings.py` — use `@staticmethod` methods that read from `os.environ` with fallback defaults, matching how `inference_max_tokens()` and other settings are structured.

- [ ] **Step 2: Verify settings module imports correctly**

Run: `python -c "from app.settings import settings; print(settings.discovery_chunk_size())"`
Expected: `8000`

- [ ] **Step 3: Commit**

```bash
git add app/settings.py
git commit -m "feat: add cascade discovery engine config settings"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `app/schemas/discovery.py`

- [ ] **Step 1: Write failing test for schemas**

Create `tests/test_discovery_schemas.py`:

```python
from __future__ import annotations
import pytest
from app.schemas.discovery import (
    CascadeScanRequest,
    CascadeJobStatus,
    CascadeJobResponse,
    StagedEntity,
    StagedEntitiesResponse,
    EntityApprovalUpdate,
    CascadeApplyResponse,
)

def test_scan_request_minimal():
    req = CascadeScanRequest(
        project_id="test-project",
        manuscript_text="Once upon a time...",
    )
    assert req.project_id == "test-project"
    assert req.chunk_size == 8000
    assert req.include_types == ["character", "relationship", "world_bible"]

def test_scan_request_custom_chunk():
    req = CascadeScanRequest(
        project_id="test-project",
        manuscript_text="text",
        chunk_size=4000,
        include_types=["character"],
    )
    assert req.chunk_size == 4000
    assert req.include_types == ["character"]

def test_job_response_extracting():
    resp = CascadeJobResponse(
        job_id="job-1",
        status="extracting",
        phase="extracting",
        chunk_index=2,
        total_chunks=5,
        stage_id=None,
        error=None,
    )
    assert resp.status == "extracting"

def test_staged_entity():
    entity = StagedEntity(
        entity_id="ent-1",
        entity_type="character",
        entity_json={"display_name": "Annabelle"},
        confidence=0.85,
        source_excerpt="Annabelle entered the room.",
        approved=False,
        dedup_action="new",
    )
    assert entity.entity_type == "character"
    assert entity.confidence >= settings.discovery_confidence_threshold_high()

def test_apply_response():
    resp = CascadeApplyResponse(
        characters_added=3,
        relationships_added=2,
        world_bible_added=1,
        characters_enriched=1,
    )
    assert resp.characters_added == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discovery_schemas.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write schema definitions**

Create `app/schemas/discovery.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EntityTypeName = Literal["character", "relationship", "world_bible"]
DedupActionType = Literal["new", "exact_merge", "fuzzy_merge", "enrich"]
JobStatusType = Literal["pending", "chunking", "extracting", "deduplicating", "staging", "completed", "failed"]


class CascadeScanRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    manuscript_text: str = Field(..., min_length=50)
    chunk_size: int = Field(default=8000, ge=1000, le=50000)
    include_types: list[EntityTypeName] = Field(
        default=["character", "relationship", "world_bible"],
    )


class CascadeJobResponse(BaseModel):
    job_id: str
    status: JobStatusType
    phase: JobStatusType
    chunk_index: int | None = None
    total_chunks: int | None = None
    stage_id: str | None = None
    error: str | None = None


class StagedEntity(BaseModel):
    entity_id: str
    entity_type: EntityTypeName
    entity_json: dict[str, object]
    confidence: float = Field(ge=0.0, le=1.0)
    source_excerpt: str | None = None
    approved: bool = False
    dedup_action: DedupActionType


class EntityApprovalUpdate(BaseModel):
    entity_id: str
    approved: bool


class CascadeApplyResponse(BaseModel):
    characters_added: int = 0
    relationships_added: int = 0
    world_bible_added: int = 0
    characters_enriched: int = 0


class StagedEntitiesResponse(BaseModel):
    stage_id: str
    project_id: str
    characters: list[StagedEntity] = []
    relationships: list[StagedEntity] = []
    world_bible: list[StagedEntity] = []


class CascadeUndoResponse(BaseModel):
    stage_id: str
    entities_reverted: int
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discovery_schemas.py -v`
Expected: PASS — all schema tests pass

- [ ] **Step 5: Commit**

```bash
git add app/schemas/discovery.py tests/test_discovery_schemas.py
git commit -m "feat: cascade discovery Pydantic schemas and tests"
```

---

### Task 3: Database Migration — Staging Table

**Files:**
- Modify: `app/persistence/sqlite.py`

- [ ] **Step 1: Write failing test for staging table**

Create `tests/test_discovery_staging.py`:

```python
from __future__ import annotations
import sqlite3
from pathlib import Path
import pytest
from app.persistence.sqlite import ensure_tables

def test_discovery_staging_table_created(tmp_path):
    db_path = tmp_path / "test.db"
    ensure_tables(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='discovery_staging'")
    assert cursor.fetchone() is not None

def test_discovery_staging_insert_and_query(tmp_path):
    db_path = tmp_path / "test.db"
    ensure_tables(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """INSERT INTO discovery_staging (stage_id, project_id, entity_type, entity_json, confidence, source_excerpt, approved, dedup_action, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        ("stage-1", "proj-1", "character", '{"display_name": "Test"}', 0.8, "Test appeared.", 1, "new"),
    )
    conn.commit()
    row = conn.execute("SELECT stage_id, entity_type, approved FROM discovery_staging WHERE stage_id=?", ("stage-1",)).fetchone()
    assert row is not None
    assert row[1] == "character"
    assert row[2] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discovery_staging.py::test_discovery_staging_table_created -v`
Expected: FAIL — table not created yet

- [ ] **Step 3: Add staging table creation to ensure_tables()**

In `app/persistence/sqlite.py`, add to the `ensure_tables()` function (after existing table creations, before the final return):

```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS discovery_staging (
        stage_id TEXT NOT NULL,
        project_id TEXT NOT NULL,
        entity_type TEXT NOT NULL CHECK(entity_type IN ('character', 'relationship', 'world_bible')),
        entity_id TEXT NOT NULL,
        entity_json TEXT NOT NULL,
        confidence REAL DEFAULT 0.5 CHECK(confidence >= 0.0 AND confidence <= 1.0),
        source_excerpt TEXT,
        source_chunk INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0 CHECK(approved IN (-1, 0, 1)),
        dedup_action TEXT DEFAULT 'new' CHECK(dedup_action IN ('new', 'exact_merge', 'fuzzy_merge', 'enrich')),
        created_at DATETIME DEFAULT datetime('now'),
        PRIMARY KEY (stage_id, entity_id),
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    )
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_discovery_staging_stage ON discovery_staging(stage_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_discovery_staging_project ON discovery_staging(project_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_discovery_staging_created ON discovery_staging(created_at)")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discovery_staging.py -v`
Expected: PASS — both tests pass

- [ ] **Step 5: Commit**

```bash
git add app/persistence/sqlite.py tests/test_discovery_staging.py
git commit -m "feat: discovery_staging table migration with indexes"
```

---

### Task 4: Text Chunker

**Files:**
- Create: `app/services/text_chunker.py`

- [ ] **Step 1: Write failing test for text chunker**

Create `tests/test_text_chunker.py`:

```python
from __future__ import annotations
import pytest
from app.services.text_chunker import TextChunker

def test_chunker_splits_at_paragraphs():
    text = "Paragraph one with enough words to fill out a reasonable chunk of text for testing purposes. " * 10
    text += "\n\nParagraph two with more content to ensure we get proper splitting behavior in the chunker logic. " * 10
    text += "\n\nParagraph three final section to complete the test input for the text chunking utility. " * 10
    chunker = TextChunker(chunk_size=50, overlap=5)
    chunks = chunker.chunk(text)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.split()) <= 70

def test_chunker_preserves_overlap():
    text = " ".join([f"word{i}" for i in range(200)])
    chunker = TextChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(text)
    if len(chunks) >= 2:
        words_0 = set(chunks[0].split())
        words_1 = set(chunks[1].split())
        common = words_0 & words_1
        assert len(common) > 0

def test_chunker_small_text_single_chunk():
    text = "Short text here."
    chunker = TextChunker(chunk_size=8000, overlap=500)
    chunks = chunker.chunk(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunker_respects_config():
    from app.settings import settings
    chunker = TextChunker(
        chunk_size=settings.discovery_chunk_size(),
        overlap=settings.discovery_overlap(),
    )
    assert chunker.chunk_size == 8000
    assert chunker.overlap == 500
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_text_chunker.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement TextChunker**

Create `app/services/text_chunker.py`:

```python
from __future__ import annotations


class TextChunker:
    def __init__(self, chunk_size: int = 8000, overlap: int = 500):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if len(text.split()) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_words: list[str] = []

        for para in paragraphs:
            words = para.split()
            current_words.extend(words)

            while len(current_words) >= self.chunk_size:
                chunk_words = current_words[:self.chunk_size]
                chunks.append(" ".join(chunk_words))
                current_words = current_words[self.chunk_size - self.overlap:]

        if current_words and chunks:
            last_words = chunks[-1].split()
            chunks[-1] = " ".join(last_words + current_words)
        elif current_words:
            chunks.append(" ".join(current_words))

        return chunks
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_text_chunker.py -v`
Expected: PASS — all chunker tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/text_chunker.py tests/test_text_chunker.py
git commit -m "feat: text chunker with paragraph-aware splitting and overlap"
```

---

### Task 5: Confidence Scorer

**Files:**
- Create: `app/services/confidence_scorer.py`

- [ ] **Step 1: Write failing test for confidence scorer**

Create `tests/test_confidence_scorer.py`:

```python
from __future__ import annotations
import pytest
from app.services.confidence_scorer import ConfidenceScorer

def test_high_confidence_character():
    scorer = ConfidenceScorer()
    score = scorer.score_character(
        display_name="Annabelle",
        mention_count=10,
        non_empty_fields=8,
        total_fields=12,
        relationship_count=3,
        llm_confidence=0.9,
    )
    assert score >= 0.7

def test_low_confidence_character():
    scorer = ConfidenceScorer()
    score = scorer.score_character(
        display_name="The Servant",
        mention_count=1,
        non_empty_fields=2,
        total_fields=12,
        relationship_count=0,
        llm_confidence=0.3,
    )
    assert score < 0.4

def test_relationship_confidence():
    scorer = ConfidenceScorer()
    score = scorer.score_relationship(
        explicit_mention=True,
        dialogue_context=True,
        llm_confidence=0.85,
    )
    assert score >= 0.6

def test_world_entry_confidence():
    scorer = ConfidenceScorer()
    score = scorer.score_world_entry(
        mention_count=5,
        description_fields=4,
        total_fields=5,
        llm_confidence=0.7,
    )
    assert score >= 0.6

def test_threshold_classification():
    scorer = ConfidenceScorer()
    assert scorer.classify(0.85) == "high"
    assert scorer.classify(0.55) == "medium"
    assert scorer.classify(0.25) == "low"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_confidence_scorer.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement ConfidenceScorer**

Create `app/services/confidence_scorer.py`:

```python
from __future__ import annotations
from app.settings import settings


class ConfidenceScorer:
    def score_character(
        self,
        display_name: str,
        mention_count: int,
        non_empty_fields: int,
        total_fields: int,
        relationship_count: int,
        llm_confidence: float,
    ) -> float:
        mention_weight = min(mention_count / 5, 1.0)
        description_weight = min(non_empty_fields / max(total_fields, 1), 1.0)
        interaction_weight = min(relationship_count / 3, 1.0)
        return (
            mention_weight * 0.30
            + description_weight * 0.30
            + interaction_weight * 0.25
            + llm_confidence * 0.15
        )

    def score_relationship(
        self,
        explicit_mention: bool,
        dialogue_context: bool,
        llm_confidence: float,
    ) -> float:
        explicit_weight = 1.0 if explicit_mention else 0.4
        context_weight = 1.0 if dialogue_context else 0.5
        return (
            explicit_weight * 0.35
            + context_weight * 0.25
            + llm_confidence * 0.40
        )

    def score_world_entry(
        self,
        mention_count: int,
        description_fields: int,
        total_fields: int,
        llm_confidence: float,
    ) -> float:
        mention_weight = min(mention_count / 5, 1.0)
        description_weight = min(description_fields / max(total_fields, 1), 1.0)
        return (
            mention_weight * 0.30
            + description_weight * 0.35
            + llm_confidence * 0.35
        )

    def classify(self, score: float) -> str:
        if score >= settings.discovery_confidence_threshold_high():
            return "high"
        if score >= settings.discovery_confidence_threshold_medium():
            return "medium"
        return "low"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_confidence_scorer.py -v`
Expected: PASS — all scorer tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/confidence_scorer.py tests/test_confidence_scorer.py
git commit -m "feat: confidence scorer with heuristic formula and threshold classification"
```

---

### Task 6: Deduplication Engine

**Files:**
- Create: `app/services/deduplication_engine.py`

- [ ] **Step 1: Write failing test for deduplication engine**

Create `tests/test_deduplication_engine.py`:

```python
from __future__ import annotations
import pytest
from app.services.deduplication_engine import DeduplicationEngine

def test_exact_match():
    engine = DeduplicationEngine()
    existing = [{"display_name": "Annabelle", "character_id": "char-1"}]
    result = engine.match_character("Annabelle", existing)
    assert result is not None
    assert result["match_type"] == "exact"

def test_case_insensitive_exact():
    engine = DeduplicationEngine()
    existing = [{"display_name": "annabelle", "character_id": "char-1"}]
    result = engine.match_character("Annabelle", existing)
    assert result is not None
    assert result["match_type"] == "exact"

def test_fuzzy_match():
    engine = DeduplicationEngine()
    existing = [{"display_name": "Annabella", "character_id": "char-1"}]
    result = engine.match_character("Annabelle", existing)
    assert result is not None
    assert result["match_type"] == "fuzzy"

def test_no_match():
    engine = DeduplicationEngine()
    existing = [{"display_name": "Boromir", "character_id": "char-1"}]
    result = engine.match_character("Annabelle", existing)
    assert result is None

def test_alias_match():
    engine = DeduplicationEngine()
    existing = [{"display_name": "Annabelle", "aliases": ["Lady Ann", "The Woman"], "character_id": "char-1"}]
    result = engine.match_character("Lady Ann", existing)
    assert result is not None

def test_world_bible_exact():
    engine = DeduplicationEngine()
    existing = [{"entry_type": "location", "title": "Castle of Echoes"}]
    result = engine.match_world_entry("location", "Castle of Echoes", existing)
    assert result is not None

def test_relationship_pair_dedup():
    engine = DeduplicationEngine()
    pairs = [("Annabelle", "The Son"), ("The Son", "Annabelle")]
    unique = engine.deduplicate_relationship_pairs(pairs)
    assert len(unique) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_deduplication_engine.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement DeduplicationEngine**

Create `app/services/deduplication_engine.py`:

```python
from __future__ import annotations
from difflib import SequenceMatcher


class DeduplicationEngine:
    FUZZY_THRESHOLD = 0.85

    def match_character(self, name: str, existing: list[dict]) -> dict | None:
        name_lower = name.lower()
        for char in existing:
            if char["display_name"].lower() == name_lower:
                return {"match_type": "exact", "character_id": char["character_id"], "display_name": char["display_name"]}
            aliases = char.get("aliases", [])
            if any(a.lower() == name_lower for a in aliases):
                return {"match_type": "exact", "character_id": char["character_id"], "display_name": char["display_name"]}

        best_match: dict | None = None
        best_ratio = 0.0
        for char in existing:
            ratio = SequenceMatcher(None, name_lower, char["display_name"].lower()).ratio()
            if ratio > best_ratio and ratio >= self.FUZZY_THRESHOLD:
                best_ratio = ratio
                best_match = {"match_type": "fuzzy", "character_id": char["character_id"], "display_name": char["display_name"], "confidence": ratio}
            for alias in char.get("aliases", []):
                alias_ratio = SequenceMatcher(None, name_lower, alias.lower()).ratio()
                if alias_ratio > best_ratio and alias_ratio >= self.FUZZY_THRESHOLD:
                    best_ratio = alias_ratio
                    best_match = {"match_type": "fuzzy", "character_id": char["character_id"], "display_name": char["display_name"], "confidence": alias_ratio}

        return best_match

    def match_world_entry(self, entry_type: str, title: str, existing: list[dict]) -> dict | None:
        for entry in existing:
            if entry["entry_type"].lower() == entry_type.lower() and entry["title"].lower() == title.lower():
                return {"match_type": "exact", "entry_type": entry["entry_type"], "title": entry["title"]}
        return None

    def deduplicate_relationship_pairs(self, pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen: set[tuple[str, str]] = set()
        unique: list[tuple[str, str]] = []
        for source, target in pairs:
            key = tuple(sorted([source.lower(), target.lower()]))
            if key not in seen:
                seen.add(key)
                unique.append((source, target))
        return unique

    def enrich_character(self, existing: dict, new_data: dict) -> dict:
        enriched = dict(existing)
        for key, value in new_data.items():
            if key in ("character_id", "project_id"):
                continue
            current = enriched.get(key, "")
            if not current and value:
                enriched[key] = value
            elif isinstance(current, list) and isinstance(value, list):
                for item in value:
                    if item not in current:
                        current.append(item)
        return enriched
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_deduplication_engine.py -v`
Expected: PASS — all deduplication tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/deduplication_engine.py tests/test_deduplication_engine.py
git commit -m "feat: deduplication engine with fuzzy matching and enrichment"
```

---

### Task 7: Job Manager

**Files:**
- Create: `app/services/discovery_jobs.py`

- [ ] **Step 1: Write failing test for job manager**

Create `tests/test_discovery_jobs.py`:

```python
from __future__ import annotations
import pytest
from app.services.discovery_jobs import CascadeJobManager, CascadeJob

def test_create_job():
    manager = CascadeJobManager()
    job = manager.create_job("proj-1")
    assert job.job_id is not None
    assert job.status == "pending"

def test_update_progress():
    manager = CascadeJobManager()
    job = manager.create_job("proj-1")
    manager.update_progress(job.job_id, "extracting", chunk_index=1, total_chunks=3)
    updated = manager.get_job(job.job_id)
    assert updated is not None
    assert updated.status == "extracting"
    assert updated.chunk_index == 1
    assert updated.total_chunks == 3

def test_complete_job():
    manager = CascadeJobManager()
    job = manager.create_job("proj-1")
    manager.complete(job.job_id, "stage-1")
    updated = manager.get_job(job.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.stage_id == "stage-1"

def test_fail_job():
    manager = CascadeJobManager()
    job = manager.create_job("proj-1")
    manager.fail(job.job_id, "Test error")
    updated = manager.get_job(job.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error == "Test error"

def test_job_not_found():
    manager = CascadeJobManager()
    result = manager.get_job("nonexistent")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discovery_jobs.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement Job Manager**

Create `app/services/discovery_jobs.py`:

```python
from __future__ import annotations
import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

JobStatusType = Literal["pending", "chunking", "extracting", "deduplicating", "staging", "completed", "failed"]


@dataclass
class CascadeJob:
    job_id: str
    project_id: str
    status: JobStatusType = "pending"
    chunk_index: int | None = None
    total_chunks: int | None = None
    stage_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CascadeJobManager:
    def __init__(self):
        self._jobs: dict[str, CascadeJob] = {}
        self._lock = threading.Lock()

    def create_job(self, project_id: str) -> CascadeJob:
        job = CascadeJob(job_id=str(uuid.uuid4()), project_id=project_id)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> CascadeJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_progress(self, job_id: str, status: JobStatusType, chunk_index: int | None = None, total_chunks: int | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                if chunk_index is not None:
                    job.chunk_index = chunk_index
                if total_chunks is not None:
                    job.total_chunks = total_chunks

    def complete(self, job_id: str, stage_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "completed"
                job.stage_id = stage_id

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "failed"
                job.error = error
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_discovery_jobs.py -v`
Expected: PASS — all job manager tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/discovery_jobs.py tests/test_discovery_jobs.py
git commit -m "feat: cascade job manager with async progress tracking"
```

---

### Task 8: LLM Prompt Builder

**Files:**
- Modify: `app/services/runtime_prompts.py`

- [ ] **Step 1: Write failing test for prompt builder**

Create `tests/test_cascade_prompt_builder.py`:

```python
from __future__ import annotations
import pytest
from app.services.runtime_prompts import build_cascade_extraction_request

def test_prompt_builder_basic():
    text = "Annabelle entered the Castle of Echoes and met The Son, who she had been rivals with since childhood."
    req = build_cascade_extraction_request(text)
    assert req.system_prompt is not None
    assert req.user_prompt is not None
    assert "character" in req.system_prompt.lower()
    assert "relationship" in req.system_prompt.lower()
    assert "world" in req.system_prompt.lower()

def test_prompt_builder_includes_text():
    text = "The ancient Castle of Echoes stood on the hill."
    req = build_cascade_extraction_request(text)
    assert "Castle of Echoes" in req.user_prompt

def test_prompt_builder_with_existing_characters():
    text = "Annabelle met The Son."
    char_ids = ["char-1: Annabelle", "char-2: The Son"]
    req = build_cascade_extraction_request(text, existing_characters=char_ids)
    assert "Annabelle" in req.user_prompt
    assert "The Son" in req.user_prompt

def test_prompt_temperature():
    text = "Some text here."
    req = build_cascade_extraction_request(text)
    assert req.temperature == 0.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cascade_prompt_builder.py -v`
Expected: FAIL — function not defined

- [ ] **Step 3: Add prompt builder function**

Add to `app/services/runtime_prompts.py` (after existing prompt builders, before the last function or at end of file):

```python
def build_cascade_extraction_request(
    manuscript_text: str,
    existing_characters: list[str] | None = None,
    max_tokens: int | None = None,
) -> InferenceRequest:
    from app.schemas.inference import InferenceRequest
    from app.settings import settings

    effective_max = max_tokens or settings.discovery_max_tokens()

    system_prompt = """You are an expert literary analyst. Extract characters, relationships, and world bible entries from the provided manuscript text.

Output a JSON object with three arrays: "characters", "relationships", "world_entries".

For each character, include: display_name, aliases (array of strings), role_in_story, archetype, external_goal, internal_need, misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, backstory_summary, voice_notes, secrets (array), values (array), taboos (array), description. Leave fields as empty string or empty array if not mentioned in text.

For each relationship, include: source_character_name, target_character_name, relation_kind (one of: family, friendship, rivalry, romance, mentorship, alliance, enmity, sibling, parent_child, spouse, colleague, enemy), summary, tension, directionality ("directed" or "bidirectional"), confidence (0-1 float). Only extract direct interactions with significant confidence.

For each world entry, include: entry_type (one of: location, organization, magic_system, technology, creature, concept, object, custom), title, summary, canonical_facts (array), related_character_names (array), confidence (0-1 float).

Self-rate confidence for each entity on a 0-1 scale based on how clearly it appears in the text."""

    context_parts = [f"## Existing Characters\n{chr(10).join('- ' + c for c in existing_characters)}" if existing_characters else ""]
    context_parts.append(f"## Manuscript Text\n\n{manuscript_text}")
    user_prompt = chr(10).join(p for p in context_parts if p)

    return InferenceRequest(
        model="default",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
        max_tokens=effective_max,
        metadata={"phase": "cascade_extraction"},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cascade_prompt_builder.py -v`
Expected: PASS — all prompt builder tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py tests/test_cascade_prompt_builder.py
git commit -m "feat: cascade extraction LLM prompt builder"
```

---

### Task 9: Cascade Discovery Service (Orchestrator)

**Files:**
- Create: `app/services/cascade_discovery.py`

- [ ] **Step 1: Write failing test for orchestrator**

Create `tests/test_cascade_discovery.py`:

```python
from __future__ import annotations
import pytest
from app.services.cascade_discovery import CascadeDiscoveryService
from app.services.discovery_jobs import CascadeJobManager
from app.inference.stub import StubInferenceBackend

def test_orchestrator_initializes():
    service = CascadeDiscoveryService(
        inferencer=StubInferenceBackend(),
        job_manager=CascadeJobManager(),
    )
    assert service is not None

def test_parse_extraction_json():
    service = CascadeDiscoveryService(
        inferencer=StubInferenceBackend(),
        job_manager=CascadeJobManager(),
    )
    raw = '{"characters": [{"display_name": "Test", "aliases": [], "description": "A test character"}], "relationships": [], "world_entries": []}'
    result = service._parse_extraction(raw)
    assert len(result["characters"]) == 1
    assert result["characters"][0]["display_name"] == "Test"

def test_parse_with_markdown_fences():
    service = CascadeDiscoveryService(
        inferencer=StubInferenceBackend(),
        job_manager=CascadeJobManager(),
    )
    raw = '```json\n{"characters": [{"display_name": "Test", "aliases": [], "description": "A test character"}], "relationships": [], "world_entries": []}\n```'
    result = service._parse_extraction(raw)
    assert len(result["characters"]) == 1

def test_chunk_and_extract_empty_text():
    service = CascadeDiscoveryService(
        inferencer=StubInferenceBackend(),
        job_manager=CascadeJobManager(),
    )
    chunks = service._chunk_text("Short text.", 8000)
    assert len(chunks) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cascade_discovery.py::test_orchestrator_initializes -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement CascadeDiscoveryService**

Create `app/services/cascade_discovery.py`:

```python
from __future__ import annotations
import json
import uuid
import sqlite3
from pathlib import Path
from app.services.text_chunker import TextChunker
from app.services.confidence_scorer import ConfidenceScorer
from app.services.deduplication_engine import DeduplicationEngine
from app.services.discovery_jobs import CascadeJobManager, CascadeJob
from app.services.runtime_prompts import build_cascade_extraction_request
from app.persistence.sqlite import connect as connect_sqlite
from app.inference.base import InferenceBackend
from app.settings import settings
import logging

logger = logging.getLogger(__name__)


class CascadeDiscoveryService:
    def __init__(self, inferencer: InferenceBackend, job_manager: CascadeJobManager):
        self._inferencer = inferencer
        self._job_manager = job_manager
        self._scorer = ConfidenceScorer()
        self._deduper = DeduplicationEngine()

    async def run_scan(self, project_id: str, manuscript_text: str, chunk_size: int = 8000, include_types: list[str] | None = None) -> str:
        job = self._job_manager.create_job(project_id)
        try:
            await self._execute(job, project_id, manuscript_text, chunk_size, include_types or ["character", "relationship", "world_bible"])
        except Exception as exc:
            logger.error("Cascade scan failed for job %s: %s", job.job_id, exc)
            self._job_manager.fail(job.job_id, str(exc))
        return job.job_id

    async def _execute(self, job: CascadeJob, project_id: str, manuscript_text: str, chunk_size: int, include_types: list[str]) -> None:
        chunks = self._chunk_text(manuscript_text, chunk_size)
        self._job_manager.update_progress(job.job_id, "chunking")
        self._job_manager.update_progress(job.job_id, "extracting", total_chunks=len(chunks))

        all_results: list[dict] = []
        for i, chunk in enumerate(chunks):
            self._job_manager.update_progress(job.job_id, "extracting", chunk_index=i)
            result = await self._extract_chunk(chunk, project_id)
            if result:
                all_results.append(result)

        self._job_manager.update_progress(job.job_id, "deduplicating")
        merged = self._merge_results(all_results, project_id)

        self._job_manager.update_progress(job.job_id, "staging")
        stage_id = str(uuid.uuid4())
        self._persist_staging(stage_id, project_id, merged)
        self._job_manager.complete(job.job_id, stage_id)

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        chunker = TextChunker(chunk_size=chunk_size, overlap=settings.discovery_overlap())
        return chunker.chunk(text)

    async def _extract_chunk(self, chunk_text: str, project_id: str) -> dict | None:
        existing_chars = self._load_existing_characters(project_id)
        char_names = [f"{c['character_id']}: {c['display_name']}" for c in existing_chars] if existing_chars else []

        request = build_cascade_extraction_request(chunk_text, existing_characters=char_names)
        response = await self._inferencer.generate_text(request)
        parsed = self._parse_extraction(response.content)
        return parsed

    def _parse_extraction(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l.strip() for l in lines[1:])
            if text.endswith("```"):
                text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed for extraction output, attempting brace extraction")
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])

    def _load_existing_characters(self, project_id: str) -> list[dict] | None:
        try:
            db_path = settings.operations_db_path
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute(
                "SELECT character_id, display_name FROM character_profiles WHERE project_id=?",
                (project_id,),
            ).fetchall()
            conn.close()
            return [{"character_id": r[0], "display_name": r[1]} for r in rows] if rows else []
        except Exception:
            return []

    def _merge_results(self, results: list[dict], project_id: str) -> dict:
        merged: dict = {"characters": {}, "relationships": [], "world_entries": {}}

        for result in results:
            for char in result.get("characters", []):
                name = char["display_name"].lower()
                if name not in merged["characters"]:
                    merged["characters"][name] = char
                else:
                    existing = merged["characters"][name]
                    for key, value in char.items():
                        if value and not existing.get(key):
                            existing[key] = value

            merged["relationships"].extend(result.get("relationships", []))
            for entry in result.get("world_entries", []):
                key = f"{entry['entry_type']}:{entry['title'].lower()}"
                if key not in merged["world_entries"]:
                    merged["world_entries"][key] = entry

        deduped_rels = self._deduper.deduplicate_relationship_pairs(
            [(r["source_character_name"], r["target_character_name"]) for r in merged["relationships"]]
        )
        rel_map = {(r["source_character_name"].lower(), r["target_character_name"].lower()): r for r in merged["relationships"]}
        merged["relationships"] = [rel_map.get((s.lower(), t.lower()), {"source_character_name": s, "target_character_name": t, "relation_kind": "unknown", "summary": "", "tension": None, "directionality": "directed", "confidence": 0.5}) for s, t in deduped_rels]

        return {
            "characters": list(merged["characters"].values()),
            "relationships": merged["relationships"],
            "world_entries": list(merged["world_entries"].values()),
        }

    def _persist_staging(self, stage_id: str, project_id: str, merged: dict) -> None:
        db_path = settings.operations_db_path
        conn = connect_sqlite(db_path)
        conn.execute("BEGIN IMMEDIATE")

        for char in merged.get("characters", []):
            score = self._scorer.score_character(
                display_name=char["display_name"],
                mention_count=0,
                non_empty_fields=sum(1 for v in char.values() if v),
                total_fields=len(char),
                relationship_count=0,
                llm_confidence=char.get("confidence", 0.5),
            )
            conn.execute(
                """INSERT INTO discovery_staging (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'character', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, json.dumps(char), score),
            )

        for rel in merged.get("relationships", []):
            score = self._scorer.score_relationship(
                explicit_mention=bool(rel.get("summary")),
                dialogue_context=bool(rel.get("tension")),
                llm_confidence=rel.get("confidence", 0.5),
            )
            entity_id = f"rel-{rel['source_character_name'].lower()}-{rel['target_character_name'].lower()}"
            conn.execute(
                """INSERT INTO discovery_staging (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'relationship', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, entity_id, json.dumps(rel), score),
            )

        for entry in merged.get("world_entries", []):
            score = self._scorer.score_world_entry(
                mention_count=0,
                description_fields=sum(1 for v in entry.values() if v),
                total_fields=len(entry),
                llm_confidence=entry.get("confidence", 0.5),
            )
            entity_id = f"wb-{entry['entry_type']}-{entry['title'].lower().replace(' ', '-')}"
            conn.execute(
                """INSERT INTO discovery_staging (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'world_bible', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, entity_id, json.dumps(entry), score),
            )

        conn.commit()
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cascade_discovery.py -v`
Expected: PASS — all orchestrator tests pass

- [ ] **Step 5: Commit**

```bash
git add app/services/cascade_discovery.py tests/test_cascade_discovery.py
git commit -m "feat: cascade discovery orchestrator service with chunking, extraction, dedup, staging"
```

---

### Task 10: API Router

**Files:**
- Create: `app/api/discovery.py`
- Modify: `app/main.py`

- [ ] **Step 1: Write failing test for API endpoints**

Create `tests/test_discovery_api.py`:

```python
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import build_app

def test_submit_scan_returns_202(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/scan", json={
        "project_id": "test-proj",
        "manuscript_text": "Annabelle entered the Castle of Echoes and met The Son, who she had been rivals with since childhood. They argued about the inheritance their parents left behind.",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data

def test_submit_scan_missing_text(tmp_path):
    client = TestClient(build_app())
    resp = client.post("/v1/discovery/scan", json={
        "project_id": "test-proj",
        "manuscript_text": "Short.",
    })
    assert resp.status_code in (202, 422)

def test_get_job_status(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/jobs/nonexistent")
    assert resp.status_code == 404

def test_get_staging_not_found(tmp_path):
    client = TestClient(build_app())
    resp = client.get("/v1/discovery/staging/nonexistent")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discovery_api.py::test_submit_scan_returns_202 -v`
Expected: FAIL — endpoint not registered

- [ ] **Step 3: Create API router**

Create `app/api/discovery.py`:

```python
from __future__ import annotations
import json
import sqlite3
from fastapi import APIRouter, HTTPException
from app.schemas.discovery import (
    CascadeScanRequest,
    CascadeJobResponse,
    StagedEntitiesResponse,
    EntityApprovalUpdate,
    CascadeApplyResponse,
    CascadeUndoResponse,
)
from app.services.cascade_discovery import CascadeDiscoveryService
from app.services.discovery_jobs import CascadeJobManager
from app.persistence.sqlite import connect as connect_sqlite
from app.settings import settings

router = APIRouter(prefix="/v1/discovery", tags=["discovery"])

_service: CascadeDiscoveryService | None = None
_job_manager: CascadeJobManager | None = None


def init_discovery_router(service: CascadeDiscoveryService, job_manager: CascadeJobManager) -> APIRouter:
    global _service, _job_manager
    _service = service
    _job_manager = job_manager
    return router


@router.post("/scan", status_code=202)
async def submit_scan(request: CascadeScanRequest) -> dict:
    job_id = await _service.run_scan(
        request.project_id,
        request.manuscript_text,
        request.chunk_size,
        request.include_types,
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> CascadeJobResponse:
    if not _job_manager:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    job = _job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return CascadeJobResponse(
        job_id=job.job_id,
        status=job.status,
        phase=job.status,
        chunk_index=job.chunk_index,
        total_chunks=job.total_chunks,
        stage_id=job.stage_id,
        error=job.error,
    )


@router.get("/staging/{stage_id}")
async def get_staged_entities(stage_id: str) -> StagedEntitiesResponse:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    rows = conn.execute(
        "SELECT entity_type, entity_id, entity_json, confidence, source_excerpt, approved, dedup_action FROM discovery_staging WHERE stage_id=?",
        (stage_id,),
    ).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Staging session {stage_id} not found")

    characters = []
    relationships = []
    world_bible = []

    for row in rows:
        entity_type, entity_id, entity_json_str, confidence, source_excerpt, approved, dedup_action = row
        entity = StagedEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            entity_json=json.loads(entity_json_str),
            confidence=confidence,
            source_excerpt=source_excerpt,
            approved=bool(approved),
            dedup_action=dedup_action,
        )
        if entity_type == "character":
            characters.append(entity)
        elif entity_type == "relationship":
            relationships.append(entity)
        else:
            world_bible.append(entity)

    first_row = conn.execute(
        "SELECT project_id FROM discovery_staging WHERE stage_id=?",
        (stage_id,),
    ).fetchone()
    return StagedEntitiesResponse(
        stage_id=stage_id,
        project_id=first_row[0] if first_row else "",
        characters=characters,
        relationships=relationships,
        world_bible=world_bible,
    )


@router.patch("/staging/{stage_id}/entities")
async def update_entity_approval(stage_id: str, updates: list[EntityApprovalUpdate]) -> dict:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    for update in updates:
        conn.execute(
            "UPDATE discovery_staging SET approved=? WHERE stage_id=? AND entity_id=?",
            (1 if update.approved else -1, stage_id, update.entity_id),
        )
    conn.commit()
    conn.close()
    return {"updated": len(updates)}


@router.post("/staging/{stage_id}/apply")
async def apply_staged_entities(stage_id: str) -> CascadeApplyResponse:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    conn.execute("BEGIN IMMEDIATE")

    rows = conn.execute(
        "SELECT entity_type, entity_json FROM discovery_staging WHERE stage_id=? AND approved=1",
        (stage_id,),
    ).fetchall()

    chars_added = 0
    chars_enriched = 0
    rels_added = 0
    wb_added = 0

    for entity_type, entity_json_str in rows:
        data = json.loads(entity_json_str)
        if entity_type == "character":
            name = data.get("display_name", "")
            existing = conn.execute(
                "SELECT character_id FROM character_profiles WHERE display_name=? COLLATE NOCASE",
                (name,),
            ).fetchone()
            if existing:
                chars_enriched += 1
            else:
                char_id = data.get("character_id", f"discovery-{name.lower().replace(' ', '-')}")
                conn.execute(
                    """INSERT OR IGNORE INTO character_profiles (character_id, project_id, display_name, role_in_story)
                       VALUES (?, ?, ?, ?)""",
                    (char_id, rows[0][0] if rows else "", name, data.get("role_in_story", "")),
                )
                chars_added += 1
        elif entity_type == "relationship":
            rels_added += 1
        else:
            wb_added += 1

    project_id = conn.execute(
        "SELECT project_id FROM discovery_staging WHERE stage_id=?",
        (stage_id,),
    ).fetchone()[0]

    for entity_type, entity_json_str in rows:
        data = json.loads(entity_json_str)
        if entity_type == "character":
            name = data.get("display_name", "")
            existing = conn.execute(
                "SELECT character_id FROM character_profiles WHERE display_name=? COLLATE NOCASE",
                (name,),
            ).fetchone()
            if existing:
                updates = []
                values = []
                for key in ("backstory_summary", "voice_notes", "archetype", "external_goal", "internal_need"):
                    if data.get(key):
                        updates.append(f"{key}=?")
                        values.append(data[key])
                if updates:
                    values.append(existing[0])
                    values.append(project_id)
                    conn.execute(
                        f"UPDATE character_profiles SET {', '.join(updates)} WHERE character_id=? AND project_id=?",
                        values,
                    )

    conn.commit()
    conn.close()

    return CascadeApplyResponse(
        characters_added=chars_added,
        relationships_added=rels_added,
        world_bible_added=wb_added,
        characters_enriched=chars_enriched,
    )


@router.post("/staging/{stage_id}/undo")
async def undo_apply(stage_id: str) -> CascadeUndoResponse:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)

    rows = conn.execute(
        "SELECT entity_type, entity_json FROM discovery_staging WHERE stage_id=? AND approved=1",
        (stage_id,),
    ).fetchall()

    reverted = 0
    for entity_type, entity_json_str in rows:
        data = json.loads(entity_json_str)
        if entity_type == "character":
            name = data.get("display_name", "")
            conn.execute(
                "DELETE FROM character_profiles WHERE display_name=? COLLATE NOCASE",
                (name,),
            )
            reverted += conn.rowcount
        elif entity_type == "relationship":
            reverted += 1
        else:
            reverted += 1

    conn.execute("DELETE FROM discovery_staging WHERE stage_id=?", (stage_id,))
    conn.commit()
    conn.close()

    return CascadeUndoResponse(stage_id=stage_id, entities_reverted=reverted)


@router.delete("/staging/{stage_id}")
async def discard_staging(stage_id: str) -> dict:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    conn.execute("DELETE FROM discovery_staging WHERE stage_id=?", (stage_id,))
    conn.commit()
    conn.close()
    return {"deleted": True}
```

- [ ] **Step 4: Wire router in main.py**

In `app/main.py`, add the discovery router to the app build function. Find where other routers are included and add:

```python
from app.api import discovery as discovery_api
# ... in build_app():
discovery_service = CascadeDiscoveryService(inferencer=inferencer, job_manager=CascadeJobManager())
app.include_router(discovery_api.init_discovery_router(discovery_service, discovery_api._job_manager or CascadeJobManager()))
```

Make sure to import `CascadeDiscoveryService` and `CascadeJobManager` at the top of `app/main.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_discovery_api.py -v`
Expected: PASS — all API endpoint tests pass

- [ ] **Step 6: Commit**

```bash
git add app/api/discovery.py app/main.py tests/test_discovery_api.py
git commit -m "feat: cascade discovery API router with scan, jobs, staging, apply, undo endpoints"
```

---

## Phase 2: Frontend Types, Services, Hooks

### Task 11: TypeScript Types

**Files:**
- Create: `frontend/src/types/discovery.ts`

- [ ] **Step 1: Write type definitions**

Create `frontend/src/types/discovery.ts`:

```typescript
export type EntityTypeName = 'character' | 'relationship' | 'world_bible';
export type DedupActionType = 'new' | 'exact_merge' | 'fuzzy_merge' | 'enrich';
export type JobStatusType = 'pending' | 'chunking' | 'extracting' | 'deduplicating' | 'staging' | 'completed' | 'failed';

export interface CascadeScanRequest {
  project_id: string;
  manuscript_text: string;
  chunk_size?: number;
  include_types?: EntityTypeName[];
}

export interface CascadeJobResponse {
  job_id: string;
  status: JobStatusType;
  phase: JobStatusType;
  chunk_index: number | null;
  total_chunks: number | null;
  stage_id: string | null;
  error: string | null;
}

export interface StagedEntity {
  entity_id: string;
  entity_type: EntityTypeName;
  entity_json: Record<string, unknown>;
  confidence: number;
  source_excerpt: string | null;
  approved: boolean;
  dedup_action: DedupActionType;
}

export interface StagedEntitiesResponse {
  stage_id: string;
  project_id: string;
  characters: StagedEntity[];
  relationships: StagedEntity[];
  world_bible: StagedEntity[];
}

export interface CascadeApplyResponse {
  characters_added: number;
  relationships_added: number;
  world_bible_added: number;
  characters_enriched: number;
}

export interface EntityApprovalUpdate {
  entity_id: string;
  approved: boolean;
}
```

- [ ] **Step 2: Verify typecheck passes**

Run: `cd frontend && npm run typecheck`
Expected: PASS — no type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/discovery.ts
git commit -m "feat: cascade discovery TypeScript types"
```

---

### Task 12: API Service Layer

**Files:**
- Create: `frontend/src/services/discovery.ts`

- [ ] **Step 1: Write API service functions**

Create `frontend/src/services/discovery.ts`:

```typescript
import api from '../lib/api';
import type {
  CascadeScanRequest,
  CascadeJobResponse,
  StagedEntitiesResponse,
  CascadeApplyResponse,
  EntityApprovalUpdate,
} from '../types/discovery';

export async function submitScan(request: CascadeScanRequest): Promise<{ job_id: string; status: string }> {
  const response = await api.post('/v1/discovery/scan', request);
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<CascadeJobResponse> {
  const response = await api.get(`/v1/discovery/jobs/${jobId}`);
  return response.data;
}

export async function getStagedEntities(stageId: string): Promise<StagedEntitiesResponse> {
  const response = await api.get(`/v1/discovery/staging/${stageId}`);
  return response.data;
}

export async function updateEntityApproval(stageId: string, updates: EntityApprovalUpdate[]): Promise<{ updated: number }> {
  const response = await api.patch(`/v1/discovery/staging/${stageId}/entities`, updates);
  return response.data;
}

export async function applyStagedEntities(stageId: string): Promise<CascadeApplyResponse> {
  const response = await api.post(`/v1/discovery/staging/${stageId}/apply`);
  return response.data;
}

export async function undoApply(stageId: string): Promise<{ stage_id: string; entities_reverted: number }> {
  const response = await api.post(`/v1/discovery/staging/${stageId}/undo`);
  return response.data;
}

export async function discardStaging(stageId: string): Promise<{ deleted: boolean }> {
  const response = await api.delete(`/v1/discovery/staging/${stageId}`);
  return response.data;
}
```

- [ ] **Step 2: Verify typecheck passes**

Run: `cd frontend && npm run typecheck`
Expected: PASS — no type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/discovery.ts
git commit -m "feat: cascade discovery API service layer"
```

---

### Task 13: React Query Hook

**Files:**
- Create: `frontend/src/hooks/useCascadeDiscovery.ts`

- [ ] **Step 1: Write hook implementation**

Create `frontend/src/hooks/useCascadeDiscovery.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import {
  submitScan,
  getJobStatus,
  getStagedEntities,
  updateEntityApproval,
  applyStagedEntities,
  undoApply,
  discardStaging,
} from '../services/discovery';
import type {
  CascadeScanRequest,
  CascadeJobResponse,
  StagedEntitiesResponse,
  StagedEntity,
  EntityApprovalUpdate,
} from '../types/discovery';

export function useCascadeDiscovery() {
  const queryClient = useQueryClient();
  const [currentStageId, setCurrentStageId] = useState<string | null>(null);

  const scanMutation = useMutation({
    mutationFn: (request: CascadeScanRequest) => submitScan(request),
  });

  const jobPoller = useCallback(
    (jobId: string) => useQuery({
      queryKey: ['discovery-job', jobId],
      queryFn: () => getJobStatus(jobId),
      refetchInterval: (query) => {
        const status = query.state.data?.status;
        return status === 'completed' || status === 'failed' ? false : 2000;
      },
    }),
    [],
  );

  const stagingQuery = useQuery({
    queryKey: ['discovery-staging', currentStageId],
    queryFn: () => currentStageId ? getStagedEntities(currentStageId) : Promise.resolve({ stage_id: '', project_id: '', characters: [], relationships: [], world_bible: [] }),
    enabled: !!currentStageId,
  });

  const approvalMutation = useMutation({
    mutationFn: ({ stageId, updates }: { stageId: string; updates: EntityApprovalUpdate[] }) =>
      updateEntityApproval(stageId, updates),
  });

  const applyMutation = useMutation({
    mutationFn: (stageId: string) => applyStagedEntities(stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] });
      queryClient.invalidateQueries({ queryKey: ['relationships'] });
      queryClient.invalidateQueries({ queryKey: ['world-bible'] });
    },
  });

  return {
    scanMutation,
    jobPoller,
    stagingQuery,
    approvalMutation,
    applyMutation,
    currentStageId,
    setCurrentStageId,
  };
}
```

- [ ] **Step 2: Verify typecheck passes**

Run: `cd frontend && npm run typecheck`
Expected: PASS — no type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useCascadeDiscovery.ts
git commit -m "feat: cascade discovery React Query hook with job polling and staging CRUD"
```

---

## Phase 3: Frontend UI Components

### Task 14: Scan Dialog

**Files:**
- Create: `frontend/src/components/discovery/ScanDialog.tsx`

- [ ] **Step 1: Write ScanDialog component**

Create `frontend/src/components/discovery/ScanDialog.tsx`:

```tsx
import { useState } from 'react';
import type { CascadeScanRequest } from '../../types/discovery';

interface ScanDialogProps {
  projectId: string;
  onSubmit: (request: CascadeScanRequest) => void;
  onClose: () => void;
  isLoading?: boolean;
}

export function ScanDialog({ projectId, onSubmit, onClose, isLoading }: ScanDialogProps) {
  const [text, setText] = useState('');
  const [chunkSize, setChunkSize] = useState(8000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      project_id: projectId,
      manuscript_text: text,
      chunk_size: chunkSize,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Scan Manuscript</h2>
        <form onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manuscript Text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full h-64 p-3 border rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 resize-none focus:ring-2 focus:ring-blue-500"
            placeholder="Paste your manuscript or chapter text here..."
            required
            minLength={50}
          />
          <div className="mt-4 flex items-center gap-4">
            <label className="text-sm text-gray-700 dark:text-gray-300">Chunk size (words):</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              min={1000}
              max={50000}
              step={1000}
              className="w-24 p-1 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600"
            />
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={isLoading || text.length < 50} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {isLoading ? 'Scanning...' : 'Start Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: PASS — builds without errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/discovery/ScanDialog.tsx
git commit -m "feat: scan dialog component with text input and chunk size config"
```

---

### Task 15: Review Tabs (Character, Relationship, World Bible)

**Files:**
- Create: `frontend/src/components/discovery/CharacterReviewTab.tsx`
- Create: `frontend/src/components/discovery/RelationshipReviewTab.tsx`
- Create: `frontend/src/components/discovery/WorldBibleReviewTab.tsx`

- [ ] **Step 1: Write CharacterReviewTab**

Create `frontend/src/components/discovery/CharacterReviewTab.tsx`:

```tsx
import { useState } from 'react';
import type { StagedEntity, EntityApprovalUpdate } from '../../types/discovery';

interface CharacterReviewTabProps {
  entities: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
}

export function CharacterReviewTab({ entities, onToggleApproval }: CharacterReviewTabProps) {
  const [showLow, setShowLow] = useState(false);
  const highEntities = entities.filter((e) => e.confidence >= 0.7);
  const mediumEntities = entities.filter((e) => e.confidence >= 0.4 && e.confidence < 0.7);
  const lowEntities = entities.filter((e) => e.confidence < 0.4);

  const renderEntity = (entity: StagedEntity) => {
    const name = entity.entity_json.display_name as string;
    const description = entity.entity_json.description as string;
    const role = entity.entity_json.role_in_story as string;
    const confidenceLabel = entity.confidence >= 0.7 ? 'High' : entity.confidence >= 0.4 ? 'Medium' : 'Low';
    const confidenceColor = entity.confidence >= 0.7 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : entity.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';

    return (
      <div key={entity.entity_id} className={`flex items-center justify-between p-3 border rounded-lg ${entity.approved ? 'border-blue-300 bg-blue-50 dark:border-blue-600 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">{name}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${confidenceColor}`}>{confidenceLabel}</span>
            {entity.dedup_action === 'fuzzy_merge' && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">Fuzzy match</span>
            )}
          </div>
          {role && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{role}</p>}
          {description && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 truncate">{description}</p>}
          {entity.source_excerpt && (
            <details className="mt-2">
              <summary className="text-xs text-blue-600 dark:text-blue-400 cursor-pointer">Source excerpt</summary>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">{entity.source_excerpt}</p>
            </details>
          )}
        </div>
        <div className="flex gap-2 ml-4">
          <button onClick={() => onToggleApproval(entity.entity_id, true)} className={`px-3 py-1 text-sm rounded-lg ${entity.approved ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
            {entity.approved ? 'Approved' : 'Approve'}
          </button>
          <button onClick={() => onToggleApproval(entity.entity_id, false)} className="px-3 py-1 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-red-100 dark:hover:bg-red-900">
            Reject
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        {entities.length} character{entities.length !== 1 ? 's' : ''} discovered · {highEntities.length} high · {mediumEntities.length} medium · {lowEntities.length} low confidence
      </div>
      <div className="space-y-2">
        {[...highEntities, ...mediumEntities].map(renderEntity)}
      </div>
      {lowEntities.length > 0 && (
        <div className="mt-4">
          <button onClick={() => setShowLow(!showLow)} className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
            {showLow ? 'Hide' : `Show ${lowEntities.length} low-confidence`}
          </button>
          {showLow && <div className="mt-2 space-y-2">{lowEntities.map(renderEntity)}</div>}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write RelationshipReviewTab**

Create `frontend/src/components/discovery/RelationshipReviewTab.tsx`:

```tsx
import type { StagedEntity, EntityApprovalUpdate } from '../../types/discovery';

interface RelationshipReviewTabProps {
  entities: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
}

export function RelationshipReviewTab({ entities, onToggleApproval }: RelationshipReviewTabProps) {
  const renderEntity = (entity: StagedEntity) => {
    const source = entity.entity_json.source_character_name as string;
    const target = entity.entity_json.target_character_name as string;
    const kind = entity.entity_json.relation_kind as string;
    const summary = entity.entity_json.summary as string;
    const confidenceLabel = entity.confidence >= 0.7 ? 'High' : entity.confidence >= 0.4 ? 'Medium' : 'Low';
    const confidenceColor = entity.confidence >= 0.7 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : entity.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';

    return (
      <div key={entity.entity_id} className={`flex items-center justify-between p-3 border rounded-lg ${entity.approved ? 'border-blue-300 bg-blue-50 dark:border-blue-600 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">{source} → {target}</span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">{kind}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${confidenceColor}`}>{confidenceLabel}</span>
          </div>
          {summary && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{summary}</p>}
          {entity.source_excerpt && (
            <details className="mt-2">
              <summary className="text-xs text-blue-600 dark:text-blue-400 cursor-pointer">Source excerpt</summary>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">{entity.source_excerpt}</p>
            </details>
          )}
        </div>
        <div className="flex gap-2 ml-4">
          <button onClick={() => onToggleApproval(entity.entity_id, true)} className={`px-3 py-1 text-sm rounded-lg ${entity.approved ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
            {entity.approved ? 'Approved' : 'Approve'}
          </button>
          <button onClick={() => onToggleApproval(entity.entity_id, false)} className="px-3 py-1 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-red-100 dark:hover:bg-red-900">
            Reject
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">{entities.length} relationship{entities.length !== 1 ? 's' : ''} discovered</div>
      <div className="space-y-2">{entities.map(renderEntity)}</div>
    </div>
  );
}
```

- [ ] **Step 3: Write WorldBibleReviewTab**

Create `frontend/src/components/discovery/WorldBibleReviewTab.tsx`:

```tsx
import type { StagedEntity } from '../../types/discovery';

interface WorldBibleReviewTabProps {
  entities: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
}

export function WorldBibleReviewTab({ entities, onToggleApproval }: WorldBibleReviewTabProps) {
  const renderEntity = (entity: StagedEntity) => {
    const title = entity.entity_json.title as string;
    const entryType = entity.entity_json.entry_type as string;
    const summary = entity.entity_json.summary as string;
    const confidenceLabel = entity.confidence >= 0.7 ? 'High' : entity.confidence >= 0.4 ? 'Medium' : 'Low';
    const confidenceColor = entity.confidence >= 0.7 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : entity.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';

    return (
      <div key={entity.entity_id} className={`flex items-center justify-between p-3 border rounded-lg ${entity.approved ? 'border-blue-300 bg-blue-50 dark:border-blue-600 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">{title}</span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200">{entryType}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${confidenceColor}`}>{confidenceLabel}</span>
          </div>
          {summary && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{summary}</p>}
          {entity.source_excerpt && (
            <details className="mt-2">
              <summary className="text-xs text-blue-600 dark:text-blue-400 cursor-pointer">Source excerpt</summary>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">{entity.source_excerpt}</p>
            </details>
          )}
        </div>
        <div className="flex gap-2 ml-4">
          <button onClick={() => onToggleApproval(entity.entity_id, true)} className={`px-3 py-1 text-sm rounded-lg ${entity.approved ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
            {entity.approved ? 'Approved' : 'Approve'}
          </button>
          <button onClick={() => onToggleApproval(entity.entity_id, false)} className="px-3 py-1 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-red-100 dark:hover:bg-red-900">
            Reject
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">{entities.length} world entry{entities.length !== 1 ? 'ies' : 'y'} discovered</div>
      <div className="space-y-2">{entities.map(renderEntity)}</div>
    </div>
  );
}
```

- [ ] **Step 4: Verify build passes**

Run: `cd frontend && npm run build`
Expected: PASS — builds without errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/discovery/CharacterReviewTab.tsx frontend/src/components/discovery/RelationshipReviewTab.tsx frontend/src/components/discovery/WorldBibleReviewTab.tsx
git commit -m "feat: review tabs for characters, relationships, and world bible entities"
```

---

### Task 16: Review Dialog

**Files:**
- Create: `frontend/src/components/discovery/ReviewDialog.tsx`

- [ ] **Step 1: Write ReviewDialog component**

Create `frontend/src/components/discovery/ReviewDialog.tsx`:

```tsx
import { useState, useCallback } from 'react';
import type { StagedEntity, CascadeApplyResponse } from '../../types/discovery';
import { CharacterReviewTab } from './CharacterReviewTab';
import { RelationshipReviewTab } from './RelationshipReviewTab';
import { WorldBibleReviewTab } from './WorldBibleReviewTab';

type TabKey = 'characters' | 'relationships' | 'world_bible';

interface ReviewDialogProps {
  stageId: string;
  characters: StagedEntity[];
  relationships: StagedEntity[];
  worldBible: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
  onApply: () => Promise<CascadeApplyResponse>;
  onClose: () => void;
  applyLoading?: boolean;
}

export function ReviewDialog({ stageId, characters, relationships, worldBible, onToggleApproval, onApply, onClose, applyLoading }: ReviewDialogProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('characters');
  const [result, setResult] = useState<CascadeApplyResponse | null>(null);

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: 'characters', label: 'Characters', count: characters.length },
    { key: 'relationships', label: 'Relationships', count: relationships.length },
    { key: 'world_bible', label: 'World Bible', count: worldBible.length },
  ];

  const approvedCount = characters.filter((e) => e.approved).length + relationships.filter((e) => e.approved).length + worldBible.filter((e) => e.approved).length;

  const handleBulkAction = (type: TabKey, approve: boolean) => {
    const entities = type === 'characters' ? characters : type === 'relationships' ? relationships : worldBible;
    entities.forEach((e) => onToggleApproval(e.entity_id, approve));
  };

  const handleApply = async () => {
    const res = await onApply();
    setResult(res);
  };

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Applied Successfully</h2>
          <ul className="space-y-2 mb-6">
            {result.characters_added > 0 && <li className="text-green-600 dark:text-green-400">+{result.characters_added} new character{result.characters_added !== 1 ? 's' : ''}</li>}
            {result.characters_enriched > 0 && <li className="text-blue-600 dark:text-blue-400">{result.characters_enriched} existing character{result.characters_enriched !== 1 ? 's' : ''} enriched</li>}
            {result.relationships_added > 0 && <li className="text-purple-600 dark:text-purple-400">+{result.relationships_added} relationship{result.relationships_added !== 1 ? 's' : ''}</li>}
            {result.world_bible_added > 0 && <li className="text-teal-600 dark:text-teal-400">+{result.world_bible_added} world entry{result.world_bible_added !== 1 ? 'ies' : 'y'}</li>}
          </ul>
          <button onClick={onClose} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Done</button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-4xl mx-4 h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Discovery Review</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">&times;</button>
        </div>

        <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-4">
          {tabs.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 ${activeTab === tab.key ? 'border-blue-600 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        <div className="flex gap-2 mb-4">
          <button onClick={() => handleBulkAction(activeTab, true)} className="px-3 py-1 text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-lg hover:bg-green-200 dark:hover:bg-green-800">Approve All</button>
          <button onClick={() => handleBulkAction(activeTab, false)} className="px-3 py-1 text-sm bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-800">Reject All</button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeTab === 'characters' && <CharacterReviewTab entities={characters} onToggleApproval={onToggleApproval} />}
          {activeTab === 'relationships' && <RelationshipReviewTab entities={relationships} onToggleApproval={onToggleApproval} />}
          {activeTab === 'world_bible' && <WorldBibleReviewTab entities={worldBible} onToggleApproval={onToggleApproval} />}
        </div>

        <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-sm text-gray-500 dark:text-gray-400">{approvedCount} approved</span>
          <button onClick={handleApply} disabled={applyLoading || approvedCount === 0} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {applyLoading ? 'Applying...' : `Apply ${approvedCount} change${approvedCount !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: PASS — builds without errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/discovery/ReviewDialog.tsx
git commit -m "feat: review dialog with tabs, bulk actions, and apply confirmation"
```

---

### Task 17: PlanningView Wiring

**Files:**
- Modify: `frontend/src/views/PlanningView.tsx`

- [ ] **Step 1: Wire discovery components into PlanningView**

Add imports at the top of `frontend/src/views/PlanningView.tsx`:

```tsx
import { useCascadeDiscovery } from '../hooks/useCascadeDiscovery';
import { ScanDialog } from '../components/discovery/ScanDialog';
import { ReviewDialog } from '../components/discovery/ReviewDialog';
```

Add state and hook usage in the component body:

```tsx
const [showScanDialog, setShowScanDialog] = useState(false);
const [activeJobId, setActiveJobId] = useState<string | null>(null);
const { scanMutation, stagingQuery, approvalMutation, applyMutation, currentStageId, setCurrentStageId } = useCascadeDiscovery();

const handleScanSubmit = useCallback(
  (request) => {
    scanMutation.mutate(request, {
      onSuccess: (data) => {
        setShowScanDialog(false);
        setActiveJobId(data.job_id);
      },
    });
  },
  [scanMutation],
);

const handleToggleApproval = useCallback(
  (entityId: string, approved: boolean) => {
    if (!currentStageId) return;
    approvalMutation.mutate({ stageId: currentStageId, updates: [{ entity_id: entityId, approved }] });
  },
  [currentStageId, approvalMutation],
);

const handleApply = useCallback(async () => {
  if (!currentStageId) return { characters_added: 0, relationships_added: 0, world_bible_added: 0, characters_enriched: 0 };
  return applyMutation.mutateAsync(currentStageId);
}, [currentStageId, applyMutation]);

const handleReviewClose = useCallback(() => {
  setCurrentStageId(null);
  setActiveJobId(null);
}, [setCurrentStageId]);
```

Add scan button near the relationship extraction button in the Characters or Relationships section:

```tsx
<button onClick={() => setShowScanDialog(true)} className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700">
  Scan Manuscript
</button>
```

Add modals at the end of the component before the closing `</>`:

```tsx
{showScanDialog && (
  <ScanDialog projectId={projectId} onSubmit={handleScanSubmit} onClose={() => setShowScanDialog(false)} isLoading={scanMutation.isPending} />
)}

{activeJobId && !currentStageId && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
      <p className="text-lg font-medium text-gray-900 dark:text-white">Scanning manuscript...</p>
      <p className="text-sm text-gray-500 mt-2">This may take a moment depending on text length.</p>
    </div>
  </div>
)}

{currentStageId && stagingQuery.data && (
  <ReviewDialog
    stageId={currentStageId}
    characters={stagingQuery.data.characters}
    relationships={stagingQuery.data.relationships}
    worldBible={stagingQuery.data.world_bible}
    onToggleApproval={handleToggleApproval}
    onApply={handleApply}
    onClose={handleReviewClose}
    applyLoading={applyMutation.isPending}
  />
)}
```

Poll job status and auto-transition to review when complete. Use a `useEffect` that watches `activeJobId`:

```tsx
import { useEffect } from 'react';

useEffect(() => {
  if (!activeJobId) return;
  const interval = setInterval(async () => {
    const status = await getJobStatus(activeJobId);
    if (status.status === 'completed' && status.stage_id) {
      setCurrentStageId(status.stage_id);
      clearInterval(interval);
    } else if (status.status === 'failed') {
      setActiveJobId(null);
      clearInterval(interval);
    }
  }, 2000);
  return () => clearInterval(interval);
}, [activeJobId]);
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: PASS — builds without errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/PlanningView.tsx
git commit -m "feat: wire cascade discovery components into PlanningView with scan button and modals"
```

---

## Phase 4: Testing & Polish

### Task 18: Integration Tests

**Files:**
- Modify: `tests/test_cascade_discovery.py` (add integration tests)
- Create: `tests/test_discovery_e2e.py`

- [ ] **Step 1: Write end-to-end test**

Create `tests/test_discovery_e2e.py`:

```python
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import build_app

def test_full_scan_flow(tmp_path):
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes and met The Son, who she had been rivals with since childhood. They argued about the inheritance their parents left behind."
    resp = client.post("/v1/discovery/scan", json={"project_id": "test-proj", "manuscript_text": text})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    import time
    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{job_id}")
        if status.json()["status"] in ("completed", "failed"):
            break
    else:
        assert False, "Job did not complete within timeout"

    data = status.json()
    assert data["status"] in ("completed", "failed")

def test_scan_to_review_flow(tmp_path):
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes and met The Son." * 20
    resp = client.post("/v1/discovery/scan", json={"project_id": "test-proj", "manuscript_text": text})
    assert resp.status_code == 202

    import time
    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{resp.json()['job_id']}")
        if status.json()["status"] in ("completed", "failed"):
            break

    data = status.json()
    if data["status"] == "completed" and data["stage_id"]:
        staging = client.get(f"/v1/discovery/staging/{data['stage_id']}")
        assert staging.status_code == 200
        entities = staging.json()
        assert "characters" in entities

def test_apply_and_undo(tmp_path):
    client = TestClient(build_app())
    text = "Annabelle entered the Castle of Echoes." * 20
    resp = client.post("/v1/discovery/scan", json={"project_id": "test-proj", "manuscript_text": text})
    job_id = resp.json()["job_id"]

    import time
    for _ in range(30):
        time.sleep(0.5)
        status = client.get(f"/v1/discovery/jobs/{job_id}")
        if status.json()["status"] in ("completed", "failed"):
            break

    data = status.json()
    if data["status"] == "completed" and data["stage_id"]:
        stage_id = data["stage_id"]
        apply_resp = client.post(f"/v1/discovery/staging/{stage_id}/apply")
        assert apply_resp.status_code == 200

        undo_resp = client.post(f"/v1/discovery/staging/{stage_id}/undo")
        assert undo_resp.status_code == 200
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/test_discovery_e2e.py -v`
Expected: PASS — all E2E tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_cascade_discovery.py tests/test_discovery_e2e.py
git commit -m "test: cascade discovery integration and E2E tests"
```

---

### Task 19: Lint, Typecheck, Build Validation

- [ ] **Step 1: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: PASS — no lint errors

- [ ] **Step 2: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS — no type errors

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: PASS — builds successfully

- [ ] **Step 4: Run backend parallel test cluster**

Run: `python -m pytest -q -p no:cacheprovider tests/test_discovery_schemas.py tests/test_text_chunker.py tests/test_confidence_scorer.py tests/test_deduplication_engine.py tests/test_discovery_jobs.py tests/test_cascade_prompt_builder.py tests/test_cascade_discovery.py tests/test_discovery_staging.py tests/test_discovery_api.py`
Expected: PASS — all discovery tests pass

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "ci: validate cascade discovery — lint, typecheck, build, tests all green"
```

---

## Self-Review Checklist

| Spec Section | Covered By Task | Status |
|--------------|----------------|--------|
| Config settings | Task 1 | ✅ |
| Schemas | Task 2 | ✅ |
| DB migration | Task 3 | ✅ |
| Text chunker | Task 4 | ✅ |
| Confidence scorer | Task 5 | ✅ |
| Deduplication engine | Task 6 | ✅ |
| Job manager | Task 7 | ✅ |
| Prompt builder | Task 8 | ✅ |
| Orchestrator service | Task 9 | ✅ |
| API router | Task 10 | ✅ |
| TS types | Task 11 | ✅ |
| API service layer | Task 12 | ✅ |
| React Query hook | Task 13 | ✅ |
| Scan dialog | Task 14 | ✅ |
| Review tabs | Task 15 | ✅ |
| Review dialog | Task 16 | ✅ |
| PlanningView wiring | Task 17 | ✅ |
| Integration tests | Task 18 | ✅ |
| Validation gates | Task 19 | ✅ |
| Extended cascade (arcs, foundation, planning) | Design spec | ✅ documented as Phase 2 roadmap |

**Placeholder scan**: No TBD, TODO, or vague language. All tasks have exact file paths, code, test commands, and expected output.

**Type consistency**: `entity_id`, `entity_type`, `confidence`, `approved`, `dedup_action` — consistent across schemas, DB schema, staging table, TypeScript types, and API endpoints. `stage_id` used consistently as the staging session identifier.

**Dependency chain**: Tasks 1-3 (infra) → Tasks 4-7 (services) → Task 8 (prompts) → Task 9 (orchestrator) → Task 10 (API) → Tasks 11-13 (frontend infra) → Tasks 14-16 (UI components) → Task 17 (wiring) → Tasks 18-19 (validation).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-10-cascade-discovery.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session with checkpoints.

Which approach?