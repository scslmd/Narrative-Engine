# Guided Setup Planning Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LLM-generated sequences and chapters to the guided setup wizard so projects are created with a complete narrative structure.

**Architecture:** Extend existing guided setup flow — single extended prompt with 7 categories (config, foundation, characters, world_bible, arcs, sequences, chapters). Reuses story import's raw SQL persistence pattern with `hash_id` for deterministic IDs. Frontend adds two collapsible panels to FieldPreview.

**Tech Stack:** Python (Pydantic, SQLite), TypeScript (React, Zustand), existing guided setup infrastructure

---

### File Map

| File | Responsibility |
|------|----------------|
| `app/schemas/guided_setup.py` | Add `GuidedSequence`, `GuidedChapter` models; extend `ExtractedFields`, `GuidedSetupCreateResponse` |
| `app/services/guided_setup.py` | Extend `_parse_analyze_response` for sequences/chapters; add `_insert_sequence`, `_insert_chapter`; extend `create_project_from_fields` transaction |
| `app/services/runtime_prompts.py` | Extend `_GUIDED_SETUP_SYSTEM_PROMPT` with category 10 (story structure) and transition guidance |
| `tests/test_guided_setup.py` | Tests for parsing, persistence, character ID resolution |
| `frontend/src/services/guidedSetup.ts` | Add `GuidedSequence`, `GuidedChapter` interfaces; extend `ExtractedFields`, `emptyExtractedFields`, `GuidedSetupCreateResponse` |
| `frontend/src/components/guided-setup/FieldPreview.tsx` | Add Sequences and Chapters collapsible panels with auto-open-on-first-data behavior |

---

### Task 1: Backend Schema — GuidedSequence and GuidedChapter Models

**Files:**
- Modify: `app/schemas/guided_setup.py`
- Test: `tests/test_guided_setup.py`

- [ ] **Step 1: Write failing tests for new schema models**

Add to `tests/test_guided_setup.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_guided_setup.py::test_guided_sequence_validates_minimal_fields tests/test_guided_setup.py::test_guided_chapter_validates_minimal_fields tests/test_guided_setup.py::test_extracted_fields_includes_sequences_and_chapters tests/test_guided_setup.py::test_extracted_fields_defaults_sequences_and_chapters_to_empty tests/test_guided_setup.py::test_guided_setup_create_response_includes_planning_counts -v`
Expected: FAIL — `GuidedSequence`, `GuidedChapter` not yet imported/defined; `ExtractedFields` doesn't accept `sequences`/`chapters`; `GuidedSetupCreateResponse` missing `sequences_created`/`chapters_created`

- [ ] **Step 3: Implement GuidedSequence and GuidedChapter in app/schemas/guided_setup.py**

Add after `GuidedArc` class (around line 105):

```python
class GuidedSequence(StrictModel):
    """Sequence (act/section) extracted from conversation."""
    sequence_id: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    chapter_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="guided", max_length=50)


class GuidedChapter(StrictModel):
    """Chapter plan extracted from conversation."""
    chapter_id: str = Field(..., min_length=1, max_length=255)
    sequence_id: str | None = None
    title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(default="", max_length=5000)
    objective: str = Field(default="", max_length=2000)
    conflict: str = Field(default="", max_length=2000)
    stakes: str = Field(default="", max_length=2000)
    active_character_ids: list[str] = Field(default_factory=list)
    continuity_requirements: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    position: int = Field(default=0, ge=0)
    status: str = Field(default="guided", max_length=50)
```

Extend `ExtractedFields` (line 161-167):

```python
class ExtractedFields(StrictModel):
    """All fields extracted from the conversation so far."""
    config: GuidedConfig = Field(default_factory=GuidedConfig)
    foundation: GuidedFoundation = Field(default_factory=GuidedFoundation)
    characters: list[GuidedCharacter] = Field(default_factory=list)
    world_bible: list[GuidedWorldEntry] = Field(default_factory=list)
    arcs: list[GuidedArc] = Field(default_factory=list)
    sequences: list[GuidedSequence] = Field(default_factory=list)
    chapters: list[GuidedChapter] = Field(default_factory=list)
```

Extend `GuidedSetupCreateResponse` (line 210-218):

```python
class GuidedSetupCreateResponse(StrictModel):
    """Response after creating a project from guided setup."""
    project_id: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    characters_created: int = Field(ge=0)
    world_entries_created: int = Field(ge=0)
    arcs_created: int = Field(ge=0)
    foundation_created: bool = False
    sequences_created: int = Field(ge=0, default=0)
    chapters_created: int = Field(ge=0, default=0)
    message: str = Field(default="Project created successfully")
```

Update test imports at top of `tests/test_guided_setup.py` to include `GuidedSequence`, `GuidedChapter`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_guided_setup.py::test_guided_sequence_validates_minimal_fields tests/test_guided_setup.py::test_guided_chapter_validates_minimal_fields tests/test_guided_setup.py::test_extracted_fields_includes_sequences_and_chapters tests/test_guided_setup.py::test_extracted_fields_defaults_sequences_and_chapters_to_empty tests/test_guided_setup.py::test_guided_setup_create_response_includes_planning_counts tests/test_guided_setup.py::test_guided_sequence_requires_title tests/test_guided_setup.py::test_guided_chapter_requires_title -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add app/schemas/guided_setup.py tests/test_guided_setup.py
git commit -m "feat: add GuidedSequence and GuidedChapter schema models"
```

---

### Task 2: Backend Service — Parsing Response Extension

**Files:**
- Modify: `app/services/guided_setup.py`
- Test: `tests/test_guided_setup.py`

- [ ] **Step 1: Write failing test for parsing sequences/chapters from LLM response**

Add to `tests/test_guided_setup.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_guided_setup.py::test_parse_analyze_response_merges_sequences_and_chapters tests/test_guided_setup.py::test_parse_analyze_response_preserves_previous_sequences_when_empty -v`
Expected: FAIL — `_parse_analyze_response` doesn't handle sequences/chapters yet

- [ ] **Step 3: Implement parsing extension in app/services/guided_setup.py**

Update imports (line 27-39) to add `GuidedChapter`, `GuidedSequence`:

```python
from ..schemas.guided_setup import (
    CategoryProgress,
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
```

Extend `_parse_analyze_response` (line 246-295). After the existing merge for `merged_arcs` (around line 267), add:

```python
merged_arcs = extracted_raw.get("arcs") or previous_fields.get("arcs", [])
merged_sequences = extracted_raw.get("sequences") or previous_fields.get("sequences", [])
merged_chapters = extracted_raw.get("chapters") or previous_fields.get("chapters", [])
```

Then extend the `ExtractedFields` construction (line 269-276) to include:

```python
extracted = ExtractedFields(
    config=GuidedConfig(**merged_config),
    foundation=GuidedFoundation(**merged_foundation),
    characters=[GuidedCharacter(**c) for c in merged_characters] if merged_characters else [],
    world_bible=[GuidedWorldEntry(**w) for w in merged_world] if merged_world else [],
    arcs=[GuidedArc(**a) for a in merged_arcs] if merged_arcs else [],
    sequences=[GuidedSequence(**s) for s in merged_sequences] if merged_sequences else [],
    chapters=[GuidedChapter(**c) for c in merged_chapters] if merged_chapters else [],
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_guided_setup.py::test_parse_analyze_response_merges_sequences_and_chapters tests/test_guided_setup.py::test_parse_analyze_response_preserves_previous_sequences_when_empty -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run full existing test suite to verify no regressions**

Run: `python -m pytest tests/test_guided_setup.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add app/services/guided_setup.py tests/test_guided_setup.py
git commit -m "feat: parse sequences and chapters from guided setup LLM response"
```

---

### Task 3: Backend Service — Persistence Extension (Sequences + Chapters)

**Files:**
- Modify: `app/services/guided_setup.py`
- Test: `tests/test_guided_setup.py`

- [ ] **Step 1: Write failing tests for sequence/chapter persistence**

Add to `tests/test_guided_setup.py`:

```python
def test_create_project_persists_sequences(tmp_path):
    ops_db = tmp_path / "operations.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    svc = GuidedSetupService(
        project_service=ProjectService(projects_dir=projects_dir),
        operations_db_path=ops_db,
    )

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

    conn = sqlite3.connect(str(ops_db))
    rows = conn.execute("SELECT sequence_id, title FROM sequence_plans ORDER BY sequence_id").fetchall()
    conn.close()

    assert len(rows) == 2
    titles = {r[1] for r in rows}
    assert "Act One" in titles
    assert "Act Two" in titles


def test_create_project_persists_chapters_with_sequence_link(tmp_path):
    ops_db = tmp_path / "operations.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    svc = GuidedSetupService(
        project_service=ProjectService(projects_dir=projects_dir),
        operations_db_path=ops_db,
    )

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

    conn = sqlite3.connect(str(ops_db))
    rows = conn.execute("SELECT chapter_id, sequence_id, title FROM chapter_plans ORDER BY position").fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0][0] is not None
    assert rows[0][1] is not None  # sequence_id linked
    assert rows[0][2] == "Chapter One"
    assert rows[1][2] == "Chapter Two"


def test_create_project_resolves_character_names_to_ids_in_chapters(tmp_path):
    ops_db = tmp_path / "operations.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    svc = GuidedSetupService(
        project_service=ProjectService(projects_dir=projects_dir),
        operations_db_path=ops_db,
    )

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

    conn = sqlite3.connect(str(ops_db))

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


def test_create_project_response_includes_planning_counts(tmp_path):
    ops_db = tmp_path / "operations.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    svc = GuidedSetupService(
        project_service=ProjectService(projects_dir=projects_dir),
        operations_db_path=ops_db,
    )

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


def test_create_project_updates_sequence_chapter_ids_json(tmp_path):
    ops_db = tmp_path / "operations.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    svc = GuidedSetupService(
        project_service=ProjectService(projects_dir=projects_dir),
        operations_db_path=ops_db,
    )

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

    conn = sqlite3.connect(str(ops_db))
    row = conn.execute(
        "SELECT chapter_ids_json FROM sequence_plans WHERE sequence_id = 'seq-1'"
    ).fetchone()
    conn.close()

    assert row is not None
    chapter_ids = json.loads(row[0])
    assert len(chapter_ids) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_guided_setup.py::test_create_project_persists_sequences tests/test_guided_setup.py::test_create_project_persists_chapters_with_sequence_link tests/test_guided_setup.py::test_create_project_resolves_character_names_to_ids_in_chapters tests/test_guided_setup.py::test_create_project_response_includes_planning_counts tests/test_guided_setup.py::test_create_project_updates_sequence_chapter_ids_json -v`
Expected: FAIL — persistence methods don't exist yet

- [ ] **Step 3: Implement _insert_sequence and _insert_chapter in app/services/guided_setup.py**

Add after `_insert_arc` method (around line 390):

```python
def _insert_sequence(
    self,
    conn: sqlite3.Connection,
    project_id: str,
    sequence: GuidedSequence,
    position: int,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    seq_id = hash_id("guided-sequence", f"{project_id}:{sequence.title}")

    conn.execute(
        """
        INSERT INTO sequence_plans (
            sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json,
            status, position, provenance_note, confidence_score, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sequence_id) DO UPDATE SET
            project_id = excluded.project_id,
            title = excluded.title,
            summary = excluded.summary,
            status = excluded.status,
            position = excluded.position,
            confidence_score = excluded.confidence_score,
            updated_at = excluded.updated_at
        """,
        (
            seq_id,
            project_id,
            sequence.title,
            _to_none(sequence.summary),
            json_safe([]),
            json_safe([]),
            sequence.status or "guided",
            position,
            "guided setup wizard",
            0.75,
            now,
            now,
        ),
    )

    return seq_id


def _insert_chapter(
    self,
    conn: sqlite3.Connection,
    project_id: str,
    chapter: GuidedChapter,
    character_name_to_id: dict[str, str],
) -> str | None:
    now = datetime.now(timezone.utc).isoformat()
    ch_id = hash_id("guided-chapter", f"{project_id}:{chapter.chapter_id}")

    # Resolve character names to persisted IDs
    resolved_characters: list[str] = []
    for name in chapter.active_character_ids:
        stripped = name.strip()
        if not stripped:
            continue
        resolved = character_name_to_id.get(stripped.lower())
        if resolved:
            resolved_characters.append(resolved)

    conn.execute(
        """
        INSERT INTO chapter_plans (
            chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes,
            active_character_ids_json, continuity_requirements_json, unresolved_questions_json,
            status, position, provenance_note, confidence_score, created_at, updated_at, target_word_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chapter_id) DO UPDATE SET
            project_id = excluded.project_id,
            sequence_id = excluded.sequence_id,
            title = excluded.title,
            summary = excluded.summary,
            objective = excluded.objective,
            conflict = excluded.conflict,
            stakes = excluded.stakes,
            active_character_ids_json = excluded.active_character_ids_json,
            continuity_requirements_json = excluded.continuity_requirements_json,
            unresolved_questions_json = excluded.unresolved_questions_json,
            status = excluded.status,
            position = excluded.position,
            confidence_score = excluded.confidence_score,
            updated_at = excluded.updated_at
        """,
        (
            ch_id,
            project_id,
            chapter.sequence_id if chapter.sequence_id else None,
            chapter.title,
            _to_none(chapter.summary),
            _to_none(chapter.objective),
            _to_none(chapter.conflict),
            _to_none(chapter.stakes),
            json_safe(resolved_characters),
            json_safe(chapter.continuity_requirements or []),
            json_safe(chapter.unresolved_questions or []),
            chapter.status or "guided",
            chapter.position,
            "guided setup wizard",
            0.75,
            now,
            now,
            None,
        ),
    )

    return ch_id
```

- [ ] **Step 4: Extend create_project_from_fields transaction**

Modify `create_project_from_fields` (line 120-219). After the existing inserts (around line 195-199), add planning persistence:

Replace lines 176-218 with:

```python
characters_created = 0
world_created = 0
arcs_created = 0
foundation_created = False
sequences_created = 0
chapters_created = 0

try:
    conn.execute("BEGIN IMMEDIATE")

    self._insert_foundation(conn, project_id, fields.foundation)
    foundation_created = True

    for char_data in fields.characters:
        self._insert_character(conn, project_id, char_data)
        characters_created += 1

    for world_entry in fields.world_bible:
        self._insert_world_entry(conn, project_id, world_entry)
        world_created += 1

    for arc_data in fields.arcs:
        self._insert_arc(conn, project_id, arc_data, fields.characters)
        arcs_created += 1

    # Build character name -> ID map for chapter resolution
    character_name_to_id: dict[str, str] = {}
    for char_data in fields.characters:
        char_id = hash_id("guided-character", f"{project_id}:{char_data.name}")
        character_name_to_id[char_data.name.strip().lower()] = char_id

    # Insert sequences (first pass — chapter_ids_json is empty placeholder)
    persisted_sequence_ids: list[str | None] = []
    for position, seq in enumerate(fields.sequences):
        seq_id = self._insert_sequence(conn, project_id, seq, position)
        persisted_sequence_ids.append(seq_id)

    # Insert chapters
    persisted_chapter_ids: list[str | None] = []
    for chapter in fields.chapters:
        ch_id = self._insert_chapter(conn, project_id, chapter, character_name_to_id)
        persisted_chapter_ids.append(ch_id)

    # Second pass: update sequences with actual chapter IDs
    for seq_idx, seq in enumerate(fields.sequences):
        seq_chapter_ids = [
            cid for cid, ch in zip(persisted_chapter_ids, fields.chapters)
            if cid is not None and (ch.sequence_id == seq.sequence_id or
                (seq_idx < len(persisted_sequence_ids) and
                 persisted_sequence_ids[seq_idx] and
                 ch.sequence_id == persisted_sequence_ids[seq_idx]))
        ]
        if seq_chapter_ids:
            conn.execute(
                "UPDATE sequence_plans SET chapter_ids_json = ?, updated_at = ? WHERE sequence_id = ?",
                (json_safe(seq_chapter_ids), datetime.now(timezone.utc).isoformat(), persisted_sequence_ids[seq_idx]),
            )

    sequences_created = len(fields.sequences)
    chapters_created = len(fields.chapters)

    conn.commit()
except Exception:
    conn.rollback()
    logger.exception("Failed to populate entities for project %s", project_id)
    raise
finally:
    conn.close()

return GuidedSetupCreateResponse(
    project_id=project_id,
    project_name=config.project_name,
    characters_created=characters_created,
    world_entries_created=world_created,
    arcs_created=arcs_created,
    foundation_created=foundation_created,
    sequences_created=sequences_created,
    chapters_created=chapters_created,
    message=(
        f"Project '{config.project_name}' created with "
        f"{characters_created} characters, {world_created} world entries, "
        f"{arcs_created} arcs, {sequences_created} sequences, {chapters_created} chapters"
    ),
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_guided_setup.py::test_create_project_persists_sequences tests/test_guided_setup.py::test_create_project_persists_chapters_with_sequence_link tests/test_guided_setup.py::test_create_project_resolves_character_names_to_ids_in_chapters tests/test_guided_setup.py::test_create_project_response_includes_planning_counts tests/test_guided_setup.py::test_create_project_updates_sequence_chapter_ids_json -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Run full existing test suite to verify no regressions**

Run: `python -m pytest tests/test_guided_setup.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add app/services/guided_setup.py tests/test_guided_setup.py
git commit -m "feat: persist sequences and chapters during guided setup project creation"
```

---

### Task 4: Backend Prompt — System Prompt Extension

**Files:**
- Modify: `app/services/runtime_prompts.py`

- [ ] **Step 1: Extend _GUIDED_SETUP_SYSTEM_PROMPT**

Locate `_GUIDED_SETUP_SYSTEM_PROMPT` in `app/services/runtime_prompts.py`. Find the existing collection steps (steps 1-9). Add step 10 after the last existing step:

```
10. **Story structure**: Once core elements are collected, organize the story into
    sequences and chapters. Ask about pacing, chapter count, and major turning points.
    Propose a sequence/chapter outline for the user to confirm or adjust.
```

In the transition guidance section (where it tells the LLM when to set `ready_to_create`), add:

```
When config, foundation, characters, world_bible, and arcs all reach 0.7+ completeness,
shift focus to structuring the story into sequences and chapters. Present a proposed
outline and ask if it works or needs adjustment. Do not set ready_to_create until the
user has confirmed the story structure.
```

In the output format section, extend the JSON schema example to include:

```json
"sequences": [{"sequence_id": "", "title": "", "summary": "", "chapter_ids": [], "status": "guided"}],
"chapters": [{"chapter_id": "", "sequence_id": "", "title": "", "summary": "",
    "objective": "", "conflict": "", "stakes": "", "active_character_ids": [],
    "continuity_requirements": [], "unresolved_questions": [], "position": 0, "status": "guided"}]
```

- [ ] **Step 2: Verify existing guided setup tests still pass**

Run: `python -m pytest tests/test_guided_setup.py -v`
Expected: All pass (prompt change doesn't break parsing)

- [ ] **Step 3: Commit**

```bash
git add app/services/runtime_prompts.py
git commit -m "feat: extend guided setup system prompt with story structure category"
```

---

### Task 5: Frontend Types — Service Types Extension

**Files:**
- Modify: `frontend/src/services/guidedSetup.ts`

- [ ] **Step 1: Add GuidedSequence and GuidedChapter interfaces**

Add after `GuidedArc` interface (around line 63):

```typescript
export interface GuidedSequence {
  sequence_id: string;
  title: string;
  summary: string;
  chapter_ids: string[];
  status: string;
}

export interface GuidedChapter {
  chapter_id: string;
  sequence_id: string | null;
  title: string;
  summary: string;
  objective: string;
  conflict: string;
  stakes: string;
  active_character_ids: string[];
  continuity_requirements: string[];
  unresolved_questions: string[];
  position: number;
  status: string;
}
```

- [ ] **Step 2: Extend ExtractedFields**

Add `sequences` and `chapters` to `ExtractedFields` (line 65-71):

```typescript
export interface ExtractedFields {
  config: GuidedConfig;
  foundation: GuidedFoundation;
  characters: GuidedCharacter[];
  world_bible: GuidedWorldEntry[];
  arcs: GuidedArc[];
  sequences: GuidedSequence[];
  chapters: GuidedChapter[];
}
```

- [ ] **Step 3: Extend emptyExtractedFields**

Add to return object (line 110-136):

```typescript
export function emptyExtractedFields(): ExtractedFields {
  return {
    config: { /* ... existing ... */ },
    foundation: { /* ... existing ... */ },
    characters: [],
    world_bible: [],
    arcs: [],
    sequences: [],
    chapters: [],
  };
}
```

- [ ] **Step 4: Extend GuidedSetupCreateResponse**

Add to interface (line 100-108):

```typescript
export interface GuidedSetupCreateResponse {
  project_id: string;
  project_name: string;
  characters_created: number;
  world_entries_created: number;
  arcs_created: number;
  foundation_created: boolean;
  sequences_created: number;
  chapters_created: number;
  message: string;
}
```

- [ ] **Step 5: Verify TypeScript compiles**

Run: `cd frontend && npm run typecheck`
Expected: PASS, 0 errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/guidedSetup.ts
git commit -m "feat: add GuidedSequence and GuidedChapter frontend types"
```

---

### Task 6: Frontend UI — FieldPreview Sequences and Chapters Panels

**Files:**
- Modify: `frontend/src/components/guided-setup/FieldPreview.tsx`

- [ ] **Step 1: Add SequenceCard and ChapterCard components, extend FieldPreview**

Update imports (line 1-4):

```typescript
import { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Users, Globe, GitBranch, Settings, ListTree, FileText } from 'lucide-react';
import { useGuidedSetupStore } from '../../stores/guidedSetupStore';
import type { GuidedCharacter, GuidedWorldEntry, GuidedArc, GuidedSequence, GuidedChapter } from '../../services/guidedSetup';
```

Add new card components after `ArcCard` (around line 98):

```typescript
function SequenceCard({ seq }: { seq: GuidedSequence }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {seq.title} <span className="text-gray-400">({seq.chapter_ids.length} chapters)</span>
      </div>
      {seq.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{seq.summary}</div>
      )}
    </div>
  );
}

function ChapterCard({ ch }: { ch: GuidedChapter }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {ch.title} <span className="text-gray-400">[{ch.position}]</span>
      </div>
      {ch.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{ch.summary}</div>
      )}
      {ch.objective && (
        <div className="text-gray-600 dark:text-gray-400 text-xs">Objective: {ch.objective}</div>
      )}
      {ch.sequence_id && (
        <div className="text-gray-500 dark:text-gray-500 text-xs">{ch.sequence_id}</div>
      )}
    </div>
  );
}
```

Update `FieldPreview` component (line 100-139). Replace destructuring and add new panels:

```typescript
export function FieldPreview(): React.ReactElement {
  const { accumulatedFields, updateFields } = useGuidedSetupStore();
  const { config, foundation, characters, world_bible, arcs, sequences, chapters } = accumulatedFields;

  // Auto-open sequences/chapters panels on first data, then respect user toggle
  const [sequencesWasOpen, setSequencesWasOpen] = useState(sequences.length > 0);
  const [chaptersWasOpen, setChaptersWasOpen] = useState(chapters.length > 0);
  const [sequencesCollapsed, setSequencesCollapsed] = useState(false);
  const [chaptersCollapsed, setChaptersCollapsed] = useState(false);

  const sequencesOpen = !sequencesCollapsed && (sequencesWasOpen || sequences.length > 0);
  const chaptersOpen = !chaptersCollapsed && (chaptersWasOpen || chapters.length > 0);

  return (
    <div className="h-full overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900">
      {/* ... existing panels ... */}

      <CollapsibleSection
        title={`Sequences (${sequences.length})`}
        icon={<ListTree className="w-4 h-4" />}
        defaultOpen={sequencesOpen}
      >
        {sequences.length === 0 && <p className="text-sm text-gray-400">No sequences yet</p>}
        {sequences.map((s, i) => <SequenceCard key={i} seq={s} />)}
      </CollapsibleSection>

      <CollapsibleSection
        title={`Chapters (${chapters.length})`}
        icon={<FileText className="w-4 h-4" />}
        defaultOpen={chaptersOpen}
      >
        {chapters.length === 0 && <p className="text-sm text-gray-400">No chapters yet</p>}
        {chapters.map((c, i) => <ChapterCard key={i} ch={c} />)}
      </CollapsibleSection>
    </div>
  );
}
```

Wait — the current `CollapsibleSection` uses internal state that doesn't support external open/close tracking. Need to refactor it to accept a controlled `isOpen` prop:

Update `CollapsibleSection` (line 6-30):

```typescript
interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
  isOpen?: boolean | undefined;
  onToggle?: (isOpen: boolean) => void;
}

function CollapsibleSection({ title, icon, defaultOpen = false, children, isOpen: isOpenProp, onToggle }: CollapsibleSectionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isControlled = isOpenProp !== undefined;
  const isOpen = isControlled ? isOpenProp : internalOpen;

  const handleClick = () => {
    if (isControlled) {
      onToggle?.(!isOpenProp as boolean);
    } else {
      setInternalOpen(!internalOpen);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg mb-2">
      <button
        onClick={handleClick}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {isOpen && <div className="px-3 pb-2">{children}</div>}
    </div>
  );
}
```

Then update FieldPreview to use controlled mode for sequences/chapters:

```typescript
export function FieldPreview(): React.ReactElement {
  const { accumulatedFields, updateFields } = useGuidedSetupStore();
  const { config, foundation, characters, world_bible, arcs, sequences, chapters } = accumulatedFields;

  const [sequencesOpen, setSequencesOpen] = useState(sequences.length > 0);
  const [chaptersOpen, setChaptersOpen] = useState(chapters.length > 0);
  const [sequencesUserCollapsed, setSequencesUserCollapsed] = useState(false);
  const [chaptersUserCollapsed, setChaptersUserCollapsed] = useState(false);

  const handleSequencesToggle = (open: boolean) => {
    setSequencesOpen(open);
    if (!open) setSequencesUserCollapsed(true);
  };

  const handleChaptersToggle = (open: boolean) => {
    setChaptersOpen(open);
    if (!open) setChaptersUserCollapsed(true);
  };

  // Auto-open when data appears and user hasn't collapsed
  const finalSequencesOpen = sequencesUserCollapsed ? sequencesOpen : sequences.length > 0;
  const finalChaptersOpen = chaptersUserCollapsed ? chaptersOpen : chapters.length > 0;

  return (
    <div className="h-full overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900">
      {/* ... existing panels unchanged ... */}

      <CollapsibleSection
        title={`Sequences (${sequences.length})`}
        icon={<ListTree className="w-4 h-4" />}
        isOpen={finalSequencesOpen}
        onToggle={handleSequencesToggle}
      >
        {sequences.length === 0 && <p className="text-sm text-gray-400">No sequences yet</p>}
        {sequences.map((s, i) => <SequenceCard key={i} seq={s} />)}
      </CollapsibleSection>

      <CollapsibleSection
        title={`Chapters (${chapters.length})`}
        icon={<FileText className="w-4 h-4" />}
        isOpen={finalChaptersOpen}
        onToggle={handleChaptersToggle}
      >
        {chapters.length === 0 && <p className="text-sm text-gray-400">No chapters yet</p>}
        {chapters.map((c, i) => <ChapterCard key={i} ch={c} />)}
      </CollapsibleSection>
    </div>
  );
}
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: PASS, no errors

- [ ] **Step 3: Verify frontend lint**

Run: `cd frontend && npm run lint`
Expected: PASS, 0 errors

- [ ] **Step 4: Verify frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS, 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/guided-setup/FieldPreview.tsx
git commit -m "feat: add sequences and chapters panels to guided setup FieldPreview"
```

---

### Task 7: Integration Verification

**Files:** All modified files

- [ ] **Step 1: Run full backend test suite for guided setup**

Run: `python -m pytest tests/test_guided_setup.py -v`
Expected: All pass (existing + new tests)

- [ ] **Step 2: Run frontend validation**

Run: `cd frontend && npm run lint && npm run typecheck && npm run build && npm run test`
Expected: All pass

- [ ] **Step 3: Run backend parallel cluster**

Run: `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
Expected: All pass (no new failures)

- [ ] **Step 4: Run backend serial tests**

Run: `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters`
Expected: All pass (only pre-existing failures)

---

## Self-Review Checklist

### 1. Spec Coverage
- [x] Schema extension (GuidedSequence, GuidedChapter) → Task 1
- [x] System prompt extension → Task 4
- [x] Parsing response (_parse_analyze_response) → Task 2
- [x] Persistence (_insert_sequence, _insert_chapter) → Task 3
- [x] Frontend types → Task 5
- [x] Frontend UI (FieldPreview panels with auto-open) → Task 6
- [x] Tests for all new functionality → Tasks 1-3

### 2. Placeholder Scan
- No TBDs, no "implement later", no vague language
- All code blocks contain complete, copy-paste-ready implementations
- All test assertions are specific and deterministic

### 3. Type Consistency
- `GuidedSequence` / `GuidedChapter` — consistent naming across Python (`GuidedSequence`) and TypeScript (`GuidedSequence`)
- `sequence_id`, `chapter_id` — snake_case preserved at all boundaries
- `active_character_ids` — name → ID resolution in `_insert_chapter` matches story import pattern
- `hash_id("guided-sequence", ...)` / `hash_id("guided-chapter", ...)` — consistent with existing `guided-character`, `guided-arc` patterns

### 4. Parallel Execution Groups
- Task 1 (schema) must complete before Tasks 2, 3, 5
- Task 5 (frontend types) can run in parallel with Tasks 2, 3 (backend service)
- Task 6 depends on Task 5 (types)
- Task 4 (prompt) is independent — can run anytime after Task 1
