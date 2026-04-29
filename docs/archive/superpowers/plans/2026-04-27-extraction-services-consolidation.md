# Extraction Services Consolidation & Prompt Optimization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate code duplication across three extraction services, fix race conditions, optimize efficiency, and improve LLM prompt quality — without changing any public API contracts.

**Architecture:** Introduce shared utilities for JSON parsing, database inserts, hashing, and manifest updates. Fix SQLite transaction isolation. Add prompt quality improvements to all prompt builders. All changes are additive/refactoring — zero API contract changes.

**Tech Stack:** Python 3.12, SQLite, Pydantic, FastAPI, React, TypeScript

---

## Task Group A: Shared Utilities (Foundation — Must Complete First)

### Task A1: Create `app/utils/json_extract.py` — Shared JSON Parser

**Files:**
- Create: `app/utils/json_extract.py`
- Modify: `app/services/mythos_extraction.py`
- Modify: `app/services/pattern_extraction.py`
- Modify: `app/services/story_import.py`
- Create: `tests/test_json_extract.py`

**Scope:** Replace three duplicate `_extract_json` / `_parse_llm_json` methods with a single shared function.

- [ ] **Step 1: Write the shared JSON parser module**

Create `app/utils/json_extract.py`:
```python
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json(content: str) -> dict[str, Any] | None:
    """Extract a JSON object from LLM response text.

    Tries three strategies in order:
    1. Direct JSON parse of the stripped content
    2. Markdown fence stripping (````json` ... `````)
    3. Balanced brace detection starting from first '{'

    Returns None if all strategies fail. This is preferred over raising
    because callers handle failures differently (some raise, some return None).
    """
    stripped = content.strip()
    if not stripped:
        return None

    data: dict[str, Any] | None = None

    # Strategy 1: Direct parse
    try:
        data = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: Strip markdown fences
    if data is None:
        fenced = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE
        )
        fenced = fenced.strip()
        if fenced:
            try:
                data = json.loads(fenced)
            except (json.JSONDecodeError, ValueError):
                pass

    # Strategy 3: Balanced brace detection
    if data is None:
        first_brace = stripped.find("{")
        if first_brace != -1:
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
                    data = json.loads(stripped[first_brace : json_end + 1])
                except (json.JSONDecodeError, ValueError):
                    pass

    if data is None:
        return None

    if not isinstance(data, dict):
        return None

    return data


def parse_llm_json(content: str) -> dict[str, Any] | None:
    """Alias for extract_json (backward compat with story_import naming)."""
    return extract_json(content)
```

- [ ] **Step 2: Write tests**

Create `tests/test_json_extract.py`:
```python
import pytest
from app.utils.json_extract import extract_json, parse_llm_json


class TestExtractJsonDirect:
    def test_valid_json(self):
        result = extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_nested_json(self):
        result = extract_json('{"a": {"b": [1, 2, {"c": "d"}]}}')
        assert result == {"a": {"b": [1, 2, {"c": "d"}]}}

    def test_empty_object(self):
        result = extract_json('{}')
        assert result == {}

    def test_empty_array_in_object(self):
        result = extract_json('{"items": []}')
        assert result == {"items": []}

    def test_empty_string(self):
        result = extract_json('')
        assert result is None

    def test_whitespace_only(self):
        result = extract_json('   \n  ')
        assert result is None

    def test_invalid_json(self):
        result = extract_json('{invalid json}')
        assert result is None


class TestExtractJsonFenced:
    def test_markdown_fence_with_json_lang(self):
        result = extract_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_markdown_fence_without_lang(self):
        result = extract_json('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_fenced_with_whitespace(self):
        result = extract_json('```\n\n  {"key": "value"}  \n\n```')
        assert result == {"key": "value"}


class TestExtractJsonBalancedBrace:
    def test_text_before_json(self):
        result = extract_json('Here is the JSON:\n{"key": "value"}')
        assert result == {"key": "value"}

    def test_text_after_json(self):
        result = extract_json('{"key": "value"}\nHope that helps.')
        assert result == {"key": "value"}

    def test_json_with_nested_braces_in_string(self):
        # Braces inside strings should not affect depth counting
        result = extract_json('{"note": "{braced}"}')
        assert result == {"note": "{braced}"}

    def test_escaped_quotes_in_string(self):
        result = extract_json(r'{"text": "he said \"hello\""}')
        assert result == {"text": "he said \"hello\""}

    def test_no_opening_brace(self):
        result = extract_json('no json here, just text')
        assert result is None

    def test_unclosed_brace(self):
        result = extract_json('{"incomplete": true,')
        assert result is None


class TestExtractJsonArrays:
    def test_array_at_top_level(self):
        """Arrays are not dicts, so should return None."""
        result = extract_json('[1, 2, 3]')
        assert result is None

    def test_object_with_array_values(self):
        result = extract_json('{"items": [1, 2, 3], "text": "hello"}')
        assert result == {"items": [1, 2, 3], "text": "hello"}


class TestAlias:
    def test_parse_llm_json_is_alias(self):
        result = parse_llm_json('{"a": 1}')
        assert result == {"a": 1}
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `python -m pytest tests/test_json_extract.py -v`
Expected: All tests pass

- [ ] **Step 4: Update mythos_extraction.py to use shared parser**

Replace `_extract_json()` function (lines 572-628) with:
```python
from ..utils.json_extract import extract_json
```
Replace `parsed = _extract_json(response.content)` with:
```python
parsed = extract_json(response.content)
if parsed is None:
    raise MythosExtractionError("Failed to parse LLM response as JSON")
```

- [ ] **Step 5: Run mythos tests**

Run: `python -m pytest tests/test_mythos_extraction.py -v`
Expected: All pass (same behavior, just shared implementation)

- [ ] **Step 6: Update pattern_extraction.py to use shared parser**

Replace `_parse_llm_json()` method (lines 197-268) body with:
```python
from ..utils.json_extract import extract_json
# ...
data = extract_json(content)
if data is None:
    return None
return self._build_analysis(data)
```

- [ ] **Step 7: Run pattern extraction tests**

Run: `python -m pytest tests/test_pattern_extraction.py -v`
Expected: All pass

- [ ] **Step 8: Update story_import.py to use shared parser**

Replace `_parse_llm_json()` in story_import.py with the shared `extract_json`.

- [ ] **Step 9: Run story import tests**

Run: `python -m pytest tests/test_story_import_service.py -v`
Expected: All pass

- [ ] **Step 10: Commit**

```bash
git add app/utils/json_extract.py tests/test_json_extract.py \
        app/services/mythos_extraction.py app/services/pattern_extraction.py \
        app/services/story_import.py
git commit -m "refactor: share JSON extraction logic in app/utils/json_extract.py"
```

### Task A2: Create `app/utils/db_inserts.py` — Shared SQL Insert Helpers

**Files:**
- Create: `app/utils/db_inserts.py`
- Modify: `app/services/mythos_extraction.py`
- Modify: `app/services/pattern_extraction.py`
- Create: `tests/test_db_inserts.py`

**Scope:** Consolidate the three duplicated `_hash_id`, two `_import_foundation`, two `_import_world_bible`, three character_profiles INSERTs, and two relationship_edges INSERTs.

- [ ] **Step 1: Write shared insert helpers**

Create `app/utils/db_inserts.py`:
```python
from __future__ import annotations

import hashlib
import json
from typing import Any


def hash_id(prefix: str, value: str) -> str:
    """Generate a stable, order-independent ID from a string value."""
    raw = f"{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{short_hash}"


def json_safe(obj: Any) -> str:
    """Serialize to JSON with consistent formatting for DB storage."""
    return json.dumps(obj, ensure_ascii=True, sort_keys=True)


def insert_foundation_profile(
    conn, project_id: str, now: str, next_rev: int,
    thematic_spine: str | None, emotional_promise: str | None,
    tone_direction: str | None, constraints_json: str,
) -> int:
    """Insert foundation_profiles header + foundation_revisions row.

    Returns the rowid of the inserted revision.
    """
    conn.execute(
        """
        INSERT INTO foundation_profiles (project_id, current_revision_id, created_at, updated_at)
        VALUES (?, NULL, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (project_id, now, now),
    )

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
            project_id, next_rev, "", "",
            thematic_spine, emotional_promise, tone_direction,
            None, constraints_json, None, None, now, now,
        ),
    )

    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_foundation_revision_id(
    conn, project_id: str, revision_id: int, now: str,
) -> None:
    """Set current_revision_id on foundation_profiles."""
    conn.execute(
        "UPDATE foundation_profiles SET current_revision_id = ?, updated_at = ? WHERE project_id = ?",
        (revision_id, now, project_id),
    )


def insert_world_bible_entry(
    conn, project_id: str, entry_type: str, title: str,
    summary: str | None, canonical_facts_json: str | None,
) -> None:
    """Insert a world_bible_entry row."""
    empty_list = json_safe([])
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
            related_character_ids_json = excluded.related_character_ids_json,
            visibility_scope = excluded.visibility_scope,
            source_artifacts_json = excluded.source_artifacts_json,
            continuity_warnings_json = excluded.continuity_warnings_json,
            writer_notes = excluded.writer_notes,
            updated_at = excluded.updated_at
        """,
        (
            project_id, entry_type, title, summary,
            canonical_facts_json or empty_list,
            empty_list, "project", empty_list, empty_list, None,
            _now_iso(), _now_iso(),
        ),
    )


def insert_character_profile(
    conn, character_id: str, project_id: str, display_name: str,
    role_in_story: str, archetype: str | None,
    external_goal: str | None, internal_need: str | None,
    misbelief_or_wound: str | None, core_fear: str | None,
    primary_strength: str | None, fatal_flaw: str | None,
    contradictions_json: str, backstory_summary: str | None,
    voice_notes: str | None, relationship_map_json: str,
    secrets_json: str, values_json: str, taboos_json: str,
    change_axis: str | None, arc_stage_notes: str | None,
    continuity_facts_json: str, writer_notes: str | None,
) -> None:
    """Insert a character_profiles row."""
    empty_list = json_safe([])
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
            project_id = excluded.project_id,
            display_name = excluded.display_name,
            role_in_story = excluded.role_in_story,
            archetype = excluded.archetype,
            external_goal = excluded.external_goal,
            internal_need = excluded.internal_need,
            misbelief_or_wound = excluded.misbelief_or_wound,
            core_fear = excluded.core_fear,
            primary_strength = excluded.primary_strength,
            fatal_flaw_or_limitation = excluded.fatal_flaw_or_limitation,
            contradictions_json = excluded.contradictions_json,
            backstory_summary = excluded.backstory_summary,
            voice_notes = excluded.voice_notes,
            relationship_map_json = excluded.relationship_map_json,
            secrets_json = excluded.secrets_json,
            values_json = excluded.values_json,
            taboos_json = excluded.taboos_json,
            change_axis = excluded.change_axis,
            arc_stage_notes = excluded.arc_stage_notes,
            continuity_facts_json = excluded.continuity_facts_json,
            writer_notes = excluded.writer_notes,
            updated_at = excluded.updated_at
        """,
        (
            character_id, project_id, display_name, role_in_story, archetype,
            external_goal, internal_need, misbelief_or_wound, core_fear,
            primary_strength, fatal_flaw, contradictions_json,
            backstory_summary, voice_notes, relationship_map_json,
            secrets_json, values_json, taboos_json,
            change_axis, arc_stage_notes, continuity_facts_json, writer_notes,
            _now_iso(), _now_iso(),
        ),
    )


def insert_relationship_edge(
    conn, edge_id: str, project_id: str, source_character_id: str,
    target_character_id: str, relation_kind: str, summary: str,
) -> None:
    """Insert a relationship_edges row."""
    conn.execute(
        """
        INSERT INTO relationship_edges (
            edge_id, project_id, source_character_id, target_character_id,
            relation_kind, summary, tension, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(edge_id) DO UPDATE SET
            project_id = excluded.project_id,
            source_character_id = excluded.source_character_id,
            target_character_id = excluded.target_character_id,
            relation_kind = excluded.relation_kind,
            summary = excluded.summary,
            tension = excluded.tension,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (
            edge_id, project_id, source_character_id, target_character_id,
            relation_kind, summary, None, None,
            _now_iso(), _now_iso(),
        ),
    )


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 2: Write tests for shared helpers**

Create `tests/test_db_inserts.py`:
```python
import pytest
import sqlite3
from app.utils.db_inserts import (
    hash_id,
    json_safe,
    insert_foundation_profile,
    update_foundation_revision_id,
    insert_world_bible_entry,
    insert_character_profile,
    insert_relationship_edge,
)


class TestHashId:
    def test_stable_id(self):
        id1 = hash_id("pattern", "Test Entity")
        id2 = hash_id("pattern", "test entity")
        assert id1 == id2

    def test_different_prefixes_different_ids(self):
        mythos_id = hash_id("mythos", "Zeus")
        pattern_id = hash_id("pattern", "Zeus")
        assert mythos_id != pattern_id
        assert mythos_id.startswith("mythos-")
        assert pattern_id.startswith("pattern-")

    def test_whitespace_stripping(self):
        id1 = hash_id("prefix", "  hello  ")
        id2 = hash_id("prefix", "hello")
        assert id1 == id2

    def test_consistent_length(self):
        id1 = hash_id("p", "x")
        id2 = hash_id("p", "a very long entity name for testing")
        # Both should be "prefix-<12 hex chars>" = 21 chars
        assert len(id1) == 21
        assert len(id2) == 21


class TestJsonSafe:
    def test_serializes_dict(self):
        result = json_safe({"a": 1, "b": [2, 3]})
        assert '"a": 1' in result
        assert '"b": [2, 3]' in result

    def test_ensures_ascii(self):
        result = json_safe({"text": "héllo"})
        assert "\\u00e9" in result

    def test_sort_keys(self):
        result = json_safe({"z": 1, "a": 2})
        assert result.index('"a"') < result.index('"z"')

    def test_serializes_list(self):
        result = json_safe([1, "two", True])
        assert result == '[1, "two", true]'

    def test_serializes_none(self):
        result = json_safe(None)
        assert result == "null"


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    # Create minimal schema needed for insert helpers
    conn.executescript("""
        CREATE TABLE foundation_profiles (
            project_id TEXT PRIMARY KEY,
            current_revision_id INTEGER,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE foundation_revisions (
            project_id TEXT,
            revision_number INTEGER,
            premise TEXT,
            logline TEXT,
            thematic_spine TEXT,
            emotional_promise TEXT,
            tone_direction TEXT,
            target_audience TEXT,
            narrative_constraints_json TEXT,
            complexity_level TEXT,
            success_definition TEXT,
            created_at TEXT,
            updated_at TEXT,
            PRIMARY KEY (project_id, revision_number)
        );
        CREATE TABLE world_bible_entries (
            project_id TEXT,
            entry_type TEXT,
            title TEXT,
            summary TEXT,
            canonical_facts_json TEXT,
            related_character_ids_json TEXT,
            visibility_scope TEXT,
            source_artifacts_json TEXT,
            continuity_warnings_json TEXT,
            writer_notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            PRIMARY KEY (project_id, entry_type, title)
        );
        CREATE TABLE character_profiles (
            character_id TEXT PRIMARY KEY,
            project_id TEXT,
            display_name TEXT,
            role_in_story TEXT,
            archetype TEXT,
            external_goal TEXT,
            internal_need TEXT,
            misbelief_or_wound TEXT,
            core_fear TEXT,
            primary_strength TEXT,
            fatal_flaw_or_limitation TEXT,
            contradictions_json TEXT,
            backstory_summary TEXT,
            voice_notes TEXT,
            relationship_map_json TEXT,
            secrets_json TEXT,
            values_json TEXT,
            taboos_json TEXT,
            change_axis TEXT,
            arc_stage_notes TEXT,
            continuity_facts_json TEXT,
            writer_notes TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE relationship_edges (
            edge_id TEXT PRIMARY KEY,
            project_id TEXT,
            source_character_id TEXT,
            target_character_id TEXT,
            relation_kind TEXT,
            summary TEXT,
            tension TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        );
    """)
    return conn


class TestFoundationInsert:
    def test_insert_creates_profile_and_revision(self, db_path):
        rev_id = insert_foundation_profile(
            db_path, "proj-1", "2026-01-01T00:00:00+00:00", 1,
            thematic_spine="test spine", emotional_promise="test promise",
            tone_direction="dark", constraints_json='{}',
        )
        assert rev_id > 0

        profile = db_path.execute(
            "SELECT project_id, current_revision_id FROM foundation_profiles WHERE project_id = ?",
            ("proj-1",),
        ).fetchone()
        assert profile[0] == "proj-1"
        assert profile[1] == rev_id

    def test_upsert_updates_profile(self, db_path):
        insert_foundation_profile(db_path, "proj-1", "2026-01-01T00:00:00+00:00", 1, "", "", "", '{}')

        # Re-insert with same revision (simulates conflict)
        insert_foundation_profile(db_path, "proj-1", "2026-01-02T00:00:00+00:00", 1, "updated", None, None, '{}')

        profile = db_path.execute("SELECT updated_at FROM foundation_profiles WHERE project_id = ?", ("proj-1",)).fetchone()
        assert "2026-01-02" in profile[0]


class TestWorldBibleInsert:
    def test_insert_creates_entry(self, db_path):
        insert_world_bible_entry(
            db_path, "proj-1", "concept", "Rule: Gravity", "Governs all matter", None,
        )
        row = db_path.execute(
            "SELECT entry_type, title, summary FROM world_bible_entries WHERE project_id = ? AND title = ?",
            ("proj-1", "Rule: Gravity"),
        ).fetchone()
        assert row[0] == "concept"
        assert row[2] == "Governs all matter"


class TestCharacterProfileInsert:
    def test_insert_creates_profile(self, db_path):
        insert_character_profile(
            db_path, "char-1", "proj-1", "Athena", "protagonist", "wisdom",
            None, None, None, None, None, "[]", None, None, "[]", "[]", "[]",
            None, None, "[]", None,
        )
        row = db_path.execute("SELECT display_name, role_in_story, archetype FROM character_profiles WHERE character_id = ?", ("char-1",)).fetchone()
        assert row == ("Athena", "protagonist", "wisdom")


class TestRelationshipEdgeInsert:
    def test_insert_creates_edge(self, db_path):
        insert_relationship_edge(
            db_path, "edge-1", "proj-1", "char-1", "char-2", "rival", "They compete for the throne",
        )
        row = db_path.execute("SELECT source_character_id, relation_kind FROM relationship_edges WHERE edge_id = ?", ("edge-1",)).fetchone()
        assert row[0] == "char-1"
        assert row[1] == "rival"
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_db_inserts.py -v`
Expected: All pass

- [ ] **Step 4: Update mythos_extraction.py — replace _hash_id, _import_foundation, _import_world_bible, _import_archetypes, _import_entities**

Replace all 5 methods with calls to the shared helpers. The mythos service file should shrink from ~724 lines to ~300 lines (keeping its own `_parse_mythos_analysis` and `_update_manifest`).

Key mapping:
- `_hash_id()` → `from ..utils.db_inserts import hash_id`
- `_import_foundation()` → `insert_foundation_profile()` + `update_foundation_revision_id()`
- `_import_world_bible()` → `insert_world_bible_entry()` per rule/motif
- `_import_archetypes()` → `insert_character_profile()` with archetype-specific field values
- `_import_entities()` → `insert_character_profile()` for deity/force + `insert_world_bible_entry()` for other
- `json.dumps(..., ensure_ascii=True, sort_keys=True)` → `json_safe()`

- [ ] **Step 5: Update pattern_extraction.py — same replacements**

Replace all duplicated methods with shared helpers. Pattern service should shrink from ~776 lines to ~350 lines (keeping its own `_build_analysis`, `_create_and_persist`, `_update_manifest`).

- [ ] **Step 6: Update story_import.py — replace json.dumps calls and _hash_id**

Replace `json_safe()` for all `json.dumps(..., ensure_ascii=True, sort_keys=True)` calls.

- [ ] **Step 7: Run full mythos test suite**

Run: `python -m pytest tests/test_mythos_extraction.py -v`
Expected: All pass

- [ ] **Step 8: Run full pattern extraction test suite**

Run: `python -m pytest tests/test_pattern_extraction.py -v`
Expected: All pass

- [ ] **Step 9: Run story import test suite**

Run: `python -m pytest tests/test_story_import_service.py -v`
Expected: All pass

- [ ] **Step 10: Commit**

```bash
git add app/utils/db_inserts.py tests/test_db_inserts.py \
        app/services/mythos_extraction.py app/services/pattern_extraction.py \
        app/services/story_import.py
git commit -m "refactor: share DB insert helpers, hash_id, json_safe, and SQL templates"
```

### Task A3: Create `app/utils/manifest.py` — Shared Manifest Update

**Files:**
- Create: `app/utils/manifest.py`
- Modify: `app/services/mythos_extraction.py`
- Modify: `app/services/pattern_extraction.py`

**Scope:** Consolidate `_update_manifest()` from both services.

- [ ] **Step 1: Write shared manifest helper**

Create `app/utils/manifest.py`:
```python
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def update_manifest(
    project_dir: Path,
    project_id: str,
    config_updates: dict[str, str],
) -> None:
    """Update manifest.json with config key-value pairs.

    Log-warnings on failure; never raise. The caller handles
    transaction boundaries — this function only touches the file.
    """
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("Manifest not found for project %s, skipping update", project_id)
        return

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
        return

    if "config" not in manifest_data:
        manifest_data["config"] = {}

    manifest_data["config"].update(config_updates)

    try:
        manifest_path.write_text(
            json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Failed to write manifest for project %s: %s", project_id, exc)
```

- [ ] **Step 2: Write tests**

Create `tests/test_manifest.py`:
```python
import json
import pytest
from pathlib import Path
from app.utils.manifest import update_manifest


class TestUpdateManifest:
    def test_adds_config_keys(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(json.dumps({"config": {"existing": "value"}}))

        update_manifest(project_dir, "proj-1", {"new_key": "new_value"})

        data = json.loads(manifest_path.read_text())
        assert data["config"]["existing"] == "value"
        assert data["config"]["new_key"] == "new_value"

    def test_overwrites_existing_key(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        (project_dir / "manifest.json").write_text(json.dumps({"config": {"key": "old"}}))

        update_manifest(project_dir, "proj-1", {"key": "new"})

        data = json.loads((project_dir / "manifest.json").read_text())
        assert data["config"]["key"] == "new"

    def test_creates_config_if_missing(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        (project_dir / "manifest.json").write_text(json.dumps({"other": "data"}))

        update_manifest(project_dir, "proj-1", {"key": "value"})

        data = json.loads((project_dir / "manifest.json").read_text())
        assert data["config"]["key"] == "value"

    def test_skips_if_manifest_missing(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        # No manifest.json

        update_manifest(project_dir, "proj-1", {"key": "value"})
        # Should not raise

    def test_handles_corrupt_json(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        (project_dir / "manifest.json").write_text("not json {{{")

        update_manifest(project_dir, "proj-1", {"key": "value"})
        # Should not raise, file unchanged

    def test_sorts_keys(self, tmp_path):
        project_dir = tmp_path / "projects" / "proj-1"
        project_dir.mkdir(parents=True)
        (project_dir / "manifest.json").write_text("{}")

        update_manifest(project_dir, "proj-1", {"z_key": "1", "a_key": "2"})

        content = (project_dir / "manifest.json").read_text()
        assert content.index('"a_key"') < content.index('"z_key"')
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: All pass

- [ ] **Step 4: Update mythos_extraction.py**

Replace `_update_manifest()` with:
```python
from ..utils.manifest import update_manifest

def _update_manifest(self, project_id: str, analysis) -> None:
    project_dir = self._project_service.root_dir / "data" / "projects" / project_id
    config_updates = {}
    if analysis.source_corpus:
        config_updates["mythos_source_corpus"] = analysis.source_corpus
    if analysis.generation_mode:
        config_updates["mythos_generation_mode"] = analysis.generation_mode
    update_manifest(project_dir, project_id, config_updates)
```

- [ ] **Step 5: Update pattern_extraction.py**

Replace `_update_manifest()` with:
```python
from ..utils.manifest import update_manifest

def _update_manifest(self, project_id: str, analysis) -> None:
    project_dir = self._project_service.root_dir / "data" / "projects" / project_id
    config_updates = {}
    if analysis.source_type:
        config_updates["pattern_source_type"] = analysis.source_type
    if analysis.source_corpus:
        config_updates["pattern_source_corpus"] = analysis.source_corpus
    if analysis.generation_mode:
        config_updates["pattern_generation_mode"] = analysis.generation_mode
    update_manifest(project_dir, project_id, config_updates)
```

- [ ] **Step 6: Run full test suite for affected services**

Run: `python -m pytest tests/test_mythos_extraction.py tests/test_pattern_extraction.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add app/utils/manifest.py tests/test_manifest.py \
        app/services/mythos_extraction.py app/services/pattern_extraction.py
git commit -m "refactor: share manifest update logic in app/utils/manifest.py"
```

---

## Task Group B: Race Condition Fixes

### Task B1: Fix SQLite Transaction Isolation

**Files:**
- Modify: `app/services/mythos_extraction.py`
- Modify: `app/services/pattern_extraction.py`
- Modify: `app/services/story_import.py` (existing)
- Create: `tests/test_transaction_isolation.py`

**Scope:** Replace `BEGIN` with `BEGIN IMMEDIATE` and fix non-atomic revision number increment.

- [ ] **Step 1: Write revision number helper in db_inserts.py**

Add to `app/utils/db_inserts.py`:
```python
def next_revision_number(conn, project_id: str) -> int:
    """Atomically compute the next revision number for a project.

    Uses a single SELECT on foundation_revisions. The INSERT that
    follows must be in the same IMMEDIATE transaction to be safe.
    """
    row = conn.execute(
        "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return row[0]
```

- [ ] **Step 2: Write transaction isolation tests**

Create `tests/test_transaction_isolation.py`:
```python
import pytest
import sqlite3
from app.utils.db_inserts import next_revision_number


class TestNextRevisionNumber:
    def test_first_revision(self, tmp_path):
        path = tmp_path / "test.db"
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE foundation_revisions (
                project_id TEXT,
                revision_number INTEGER,
                PRIMARY KEY (project_id, revision_number)
            )
        """)
        result = next_revision_number(conn, "proj-1")
        assert result == 1

    def test_second_revision(self, tmp_path):
        path = tmp_path / "test.db"
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE foundation_revisions (
                project_id TEXT,
                revision_number INTEGER,
                PRIMARY KEY (project_id, revision_number)
            )
        """)
        conn.execute("INSERT INTO foundation_revisions VALUES ('proj-1', 1)")
        result = next_revision_number(conn, "proj-1")
        assert result == 2

    def test_skips_gaps(self, tmp_path):
        path = tmp_path / "test.db"
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE foundation_revisions (
                project_id TEXT,
                revision_number INTEGER,
                PRIMARY KEY (project_id, revision_number)
            )
        """)
        conn.execute("INSERT INTO foundation_revisions VALUES ('proj-1', 1)")
        conn.execute("INSERT INTO foundation_revisions VALUES ('proj-1', 3)")
        result = next_revision_number(conn, "proj-1")
        assert result == 4

    def test_different_projects_independent(self, tmp_path):
        path = tmp_path / "test.db"
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE foundation_revisions (
                project_id TEXT,
                revision_number INTEGER,
                PRIMARY KEY (project_id, revision_number)
            )
        """)
        conn.execute("INSERT INTO foundation_revisions VALUES ('proj-a', 1)")
        conn.execute("INSERT INTO foundation_revisions VALUES ('proj-b', 2)")

        assert next_revision_number(conn, "proj-a") == 2
        assert next_revision_number(conn, "proj-b") == 3
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_transaction_isolation.py -v`
Expected: All pass

- [ ] **Step 4: Update mythos_extraction.py — BEGIN IMMEDIATE + use helper**

In `_transactional_import()` method, replace:
```python
conn = sqlite3.connect(self._repository.db_path, timeout=30)
try:
    conn.execute("BEGIN")
```
with:
```python
conn = sqlite3.connect(self._repository.db_path, timeout=30)
try:
    conn.execute("BEGIN IMMEDIATE")
```

Also replace the `rev_row = conn.execute(...).fetchone()` pattern in `_import_foundation` with:
```python
from ..utils.db_inserts import next_revision_number

next_rev = next_revision_number(conn, project_id)
```

- [ ] **Step 5: Update pattern_extraction.py — same changes**

Same `BEGIN` → `BEGIN IMMEDIATE` and `next_revision_number` import.

- [ ] **Step 6: Run all affected tests**

Run: `python -m pytest tests/test_mythos_extraction.py tests/test_pattern_extraction.py -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add app/utils/db_inserts.py tests/test_transaction_isolation.py \
        app/services/mythos_extraction.py app/services/pattern_extraction.py
git commit -m "fix: use BEGIN IMMEDIATE for concurrent-write safety, add next_revision_number helper"
```

---

## Task Group C: Efficiency Optimizations

### Task C1: Move Repository and Character Load Outside Chapter Loop

**Files:**
- Modify: `app/services/local_executor.py`

**Scope:** Move `_repo` and `_chars` instantiation outside the `for idx, chapter_id` loop in `_run_multi_chapter_draft`.

- [ ] **Step 1: Read current loop structure**

In `_run_multi_chapter_draft` (line 1063), move lines 1155-1156 (`_repo = StoryDevelopmentRepository(...)` and `_chars = _repo.list_character_profiles(...)`) to before the `for idx, chapter_id in enumerate(chapter_ids):` loop (line 1063).

Current code at line 1155 (inside loop):
```python
_repo = StoryDevelopmentRepository(settings.operations_db_path)
_chars = _repo.list_character_profiles(project_id)
```

Moved to line 1062 (before loop):
```python
_repo = StoryDevelopmentRepository(settings.operations_db_path)
_chars = _repo.list_character_profiles(project_id)
```

And update all references inside the loop from `_repo` → `_repo` (same variable, no code change needed).

- [ ] **Step 2: Run multi-chapter tests**

Run: `python -m pytest tests/test_chapter_summarizer.py tests/test_local_executor.py -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add app/services/local_executor.py
git commit -m "perf: move repository and character loading outside multi-chapter loop"
```

### Task C2: Document extract_from_project Truncation Limitation

**Files:**
- Modify: `app/services/pattern_extraction.py`

**Scope:** Add docstring warning about 24,000 char truncation for multi-document concatenation.

- [ ] **Step 1: Add docstring to extract_from_project**

In `pattern_extraction.py:123-151`, add to the docstring:
```python
"""Extract patterns from manuscript documents of an existing project.

Retrieves all manuscript documents for the project, concatenates their
content as source text, and delegates to extract().

NOTE: The concatenated text is truncated to 24,000 chars for single-pass
LLM analysis. For projects with many chapters, only the earliest content
may reach the LLM. Consider using the extraction endpoint per-chapter
or in batches for large projects.
"""
```

- [ ] **Step 2: Commit**

```bash
git add app/services/pattern_extraction.py
git commit -m "docs: document extract_from_project truncation limitation"
```

---

## Task Group D: Frontend Fixes

### Task D1: Fix Mythology Source Type Generation Modes

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx`

**Scope:** When `patternSourceType === "mythology"`, show `same_world/transposed/pure_pattern` modes instead of `same_world/new_characters/transposed`.

- [ ] **Step 1: Add mythology-specific generation mode state**

Add a new state variable (or refactor to use a single state with type narrowing). Replace lines 27-29:
```typescript
// Replace:
const [generationMode, setGenerationMode] = useState<'same_world' | 'transposed' | 'pure_pattern'>('same_world');
const [patternSourceType, setPatternSourceType] = useState<'narrative' | 'mythology'>('narrative');
const [patternGenMode, setPatternGenMode] = useState<'same_world' | 'new_characters' | 'transposed'>('same_world');

// With:
const [patternSourceType, setPatternSourceType] = useState<'narrative' | 'mythology'>('narrative');
const [patternGenMode, setPatternGenMode] = useState<'same_world' | 'new_characters' | 'transposed' | 'transposed' | 'pure_pattern'>('same_world');
```

Actually, simpler approach — change the patterns generation mode type to include all valid values:
```typescript
const [patternGenMode, setPatternGenMode] = useState<string>('same_world');
```

- [ ] **Step 2: Add conditional mode options**

In the "Extract Patterns" tab JSX (lines 304-322), replace the hardcoded mode list with conditional rendering:
```tsx
{patternSourceType === 'mythology' ? (
  <>
    <label className="...">Generation Mode (Mythology)</label>
    <div className="flex gap-2">
      {[
        { value: 'same_world', label: 'Same World' },
        { value: 'transposed', label: 'Transposed' },
        { value: 'pure_pattern', label: 'Pure Pattern' },
      ].map((mode) => (
        <button key={mode.value} type="button"
          onClick={() => setPatternGenMode(mode.value)}
          className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
            patternGenMode === mode.value
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
              : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'
          }`}>
          {mode.label}
        </button>
      ))}
    </div>
  </>
) : (
  <>
    <label className="...">Generation Mode</label>
    <div className="flex gap-2">
      {[
        { value: 'same_world', label: 'Same World' },
        { value: 'new_characters', label: 'New Characters' },
        { value: 'transposed', label: 'Transposed' },
      ].map((mode) => (
        <button key={mode.value} type="button"
          onClick={() => setPatternGenMode(mode.value)}
          className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
            patternGenMode === mode.value
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
              : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:hover:border-slate-600'
          }`}>
          {mode.label}
        </button>
      ))}
    </div>
  </>
)}
```

- [ ] **Step 3: Remove unused `generationMode` state**

Remove line 27 (`const [generationMode, setGenerationMode] = useState<'same_world' | 'transposed' | 'pure_pattern'>('same_world');`) since the mythos tab uses its own state from the separate block (lines 218-264).

Wait — the mythos tab's `generationMode` and the patterns tab's `patternGenMode` serve different endpoints. Keep both but clean up the type.

Actually, looking at the code more carefully: the mythos tab uses `generationMode` and sends it to `extractMythos()`. The patterns tab uses `patternSourceType` + `patternGenMode` and sends to `importPatterns()`. These are separate flows. The issue is just that `patternGenMode` type doesn't include `pure_pattern`.

- [ ] **Step 4: Run frontend validation**

Run: `cd frontend && npm run typecheck && npm run lint`
Expected: Both pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/projects/StoryImportModal.tsx
git commit -m "fix: show correct generation modes for mythology source type in patterns tab"
```

### Task D2: Fix Union Type in handleSubmit

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx`

**Scope:** Replace inline union type with `MythosExtractionResponse` type.

- [ ] **Step 1: Add import**

Add at top of file (line 5 area):
```typescript
import type { MythosExtractionResponse } from '../../types/mythosExtraction';
```

- [ ] **Step 2: Replace inline type**

Replace line 54:
```typescript
// Replace:
response: StoryImportResponse | PatternExtractionResponse | { project_id: string; status: 'completed' | 'failed'; error: string | null };

// With:
response: StoryImportResponse | PatternExtractionResponse | MythosExtractionResponse;
```

- [ ] **Step 3: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: Pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/projects/StoryImportModal.tsx
git commit -m "fix: use MythosExtractionResponse type instead of inline union"
```

---

## Task Group E: Minor Cleanups

### Task E1: Add Type Annotations to Router

**Files:**
- Modify: `app/api/projects.py`

**Scope:** Replace `Any` types with Protocol interfaces for service injection.

- [ ] **Step 1: Define Protocol interfaces**

Add to `app/api/projects.py` (after imports, before `build_projects_router`):
```python
from typing import Protocol

class _ImportServiceProtocol(Protocol):
    def import_story(self, request: Any) -> Any: ...

class _MythosServiceProtocol(Protocol):
    def extract(self, request: Any) -> Any: ...

class _PatternServiceProtocol(Protocol):
    def extract(self, text: str, source_type: str, generation_mode: str, project_id: str | None, source_corpus: str | None) -> Any: ...
    def extract_from_project(self, project_id: str, source_type: str, generation_mode: str, source_corpus: str | None) -> Any: ...
```

- [ ] **Step 2: Update function signature**

Replace line 31-36:
```python
def build_projects_router(
    project_service: ProjectService,
    import_service: _ImportServiceProtocol | None = None,
    mythos_service: _MythosServiceProtocol | None = None,
    pattern_service: _PatternServiceProtocol | None = None,
) -> APIRouter:
```

- [ ] **Step 3: Run backend tests**

Run: `python -m pytest tests/test_projects.py -v`
Expected: Pass

- [ ] **Step 4: Commit**

```bash
git add app/api/projects.py
git commit -m "refactor: add Protocol types for service injection in projects router"
```

### Task E2: Simplify _has_pattern_content

**Files:**
- Modify: `app/services/scene_context.py`

**Scope:** Replace redundant `pg and` checks.

- [ ] **Step 1: Replace method body**

Replace lines 112-118:
```python
def _has_pattern_content(self) -> bool:
    pg = self.pattern_guidance
    return bool(pg and (pg.voice_profile or pg.world_rules or pg.thematic_constraints))
```

- [ ] **Step 2: Run scene context tests**

Run: `python -m pytest tests/test_pattern_guidance_scene_context.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add app/services/scene_context.py
git commit -m "refactor: simplify _has_pattern_content redundancy"
```

### Task E3: Remove Unused Import

**Files:**
- Modify: `app/services/pattern_extraction.py`

**Scope:** Remove unused `MythosExtractionError` import.

- [ ] **Step 1: Remove import**

Replace line 32:
```python
# Replace:
from .mythos_extraction import MythosExtractionService, MythosExtractionError

# With:
from .mythos_extraction import MythosExtractionService
```

- [ ] **Step 2: Run pattern extraction tests**

Run: `python -m pytest tests/test_pattern_extraction.py -v`
Expected: Pass

- [ ] **Step 3: Commit**

```bash
git add app/services/pattern_extraction.py
git commit -m "fix: remove unused MythosExtractionError import"
```

---

## Task Group F: Prompt Quality Review

See `docs/Prompt Optimization Review - Extraction & Generation v1.0.md` for detailed analysis and specific prompt improvements. A separate task list follows below.

### Task F1: Optimize Narrative Analysis Prompt

**Files:**
- Modify: `app/services/runtime_prompts.py`

**Scope:** Add JSON structural guardrail to `build_narrative_analysis_request()` to improve parse success rate.

- [ ] **Step 1: Add JSON structural instructions**

In `build_narrative_analysis_request()` system prompt (lines 720-809), add before "CRITICAL: Return ONLY the JSON object":
```python
# Add to system_prompt, before the final "CRITICAL" line:
'JSON STRUCTURE RULES:\n'
'- All arrays must be JSON arrays [], not strings.\n'
'- Use null (not empty string) for missing optional fields where shown.\n'
'- Do not include trailing commas in JSON objects or arrays.\n'
'- All string values must be properly escaped (use \\n for newlines, \\\\ for backslashes).\n'
'- The "generation_mode" field must exactly match: "same_world", "new_characters", or "transposed".\n'
```

- [ ] **Step 2: Run prompt builder tests**

Run: `python -m pytest tests/test_runtime_prompts.py -v -k narrative`
Expected: All pass (prompts should not affect existing test behavior)

- [ ] **Step 3: Commit**

```bash
git add app/services/runtime_prompts.py
git commit -m "prompt: add JSON structural guardrails to narrative analysis prompt"
```

### Task F2: Optimize Mythos Analysis Prompt

**Files:**
- Modify: `app/services/runtime_prompts.py`

**Scope:** Same JSON guardrails for `build_mythos_analysis_request()`.

- [ ] **Step 1: Add JSON structural instructions**

In `build_mythos_analysis_request()` system prompt (lines 855-919), add before the closing section:
```python
# Add before the last paragraph in system_prompt:
'JSON STRUCTURE RULES:\n'
'- All arrays must be JSON arrays [], not strings.\n'
'- Use null (not empty string) for missing optional fields where shown.\n'
'- Do not include trailing commas in JSON objects or arrays.\n'
'- The "generation_mode" field must exactly match: "same_world", "transposed", or "pure_pattern".\n'
'- The "entity_type" field must be one of: "deity", "location", "concept", "force".\n'
```

- [ ] **Step 2: Run prompt builder tests**

Run: `python -m pytest tests/test_runtime_prompts.py -v -k mythos`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add app/services/runtime_prompts.py
git commit -m "prompt: add JSON structural guardrails to mythos analysis prompt"
```

### Task F3: Optimize Story Import Analysis Prompt

**Files:**
- Modify: `app/services/runtime_prompts.py`

**Scope:** Tighten JSON guardrails in `build_import_analysis_request()` to reduce malformed output.

- [ ] **Step 1: Add explicit key ordering instruction**

Add to system prompt (after the field value rules, before "CHARACTER EXTRACTION RULES"):
```python
# Insert before CHARACTER EXTRACTION RULES:
'JSON OUTPUT FORMAT:\n'
'- Return ONLY the raw JSON object. No markdown code fences. No explanation text.\n'
'- Use "null" for fields you cannot determine, not empty strings (except for strings that must have content — use "" only when a string is expected but empty).\n'
'- Every array field must be [] when empty, never omitted.\n'
'- Do not use "description" anywhere — use "summary" for world_bible entries and "description" is not a valid key.\n'
'- Do not use "name" for sequences — use "title" instead.\n'
```

- [ ] **Step 2: Run prompt tests**

Run: `python -m pytest tests/test_story_import_service.py -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add app/services/runtime_prompts.py
git commit -m "prompt: tighten JSON guardrails in story import analysis prompt"
```

### Task F4: Improve P-100 Pattern Context Block

**Files:**
- Modify: `app/services/runtime_prompts.py`

**Scope:** Make `_build_pattern_context_block` more structured and explicit about what the LLM should produce.

- [ ] **Step 1: Add output format instruction to each mode block**

In `_build_pattern_context_block` (line 426), after each mode section, append:
```python
# After same_world block (around line 476):
lines.append("")
lines.append("INSTRUCTION: Follow these patterns when building the P-100 architect foundation. ")
lines.append("Your output must respect these world rules, voice guidelines, and archetypal patterns.")

# After new_characters block (around line 498):
lines.append("")
lines.append("INSTRUCTION: Create new characters who fill these archetypal roles in this world. ")
lines.append("Your architect output must respect the world rules and populate the archetypal structure.")

# After transposed block (around line 528):
lines.append("")
lines.append("INSTRUCTION: Transpose these patterns and structures into a new setting. ")
lines.append("Map each archetypal pattern and narrative structure to an equivalent in your new world.")
```

- [ ] **Step 2: Update `_build_pattern_context_block` type annotation**

Replace `pc: Any` with `pc: PatternExtractionAnalysis`:
```python
from ..schemas.pattern_extraction import PatternExtractionAnalysis

def _build_pattern_context_block(pc: PatternExtractionAnalysis) -> str:
```

- [ ] **Step 3: Update all callers**

Update call sites in `runtime_prompts.py:26`:
```python
# Change:
user_parts.append(_build_pattern_context_block(pattern_context))

# pattern_context is already a PatternExtractionAnalysis or None at the call site
# Ensure type is propagated:
if pattern_context is not None:
    user_parts.append(_build_pattern_context_block(pattern_context))
```

- [ ] **Step 4: Run P-100 tests**

Run: `python -m pytest tests/test_runtime_prompts.py -v -k p100`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add app/services/runtime_prompts.py
git commit -m "prompt: improve P-100 pattern context blocks with explicit instructions and type safety"
```

---

## Task Group G: Integration Validation

### Task G1: Full Suite Validation

**Scope:** Run all four validation commands after completing Tasks A-F.

- [ ] **Step 1: Run backend tests**

Run: `python -m pytest -q -p no:cacheprovider`
Expected: Same count as baseline (1031 passed, 9 skipped). No regressions.

- [ ] **Step 2: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: Pass

- [ ] **Step 3: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: Pass

- [ ] **Step 4: Run frontend build**

Run: `cd frontend && npm run build`
Expected: 1973 modules, same count.

- [ ] **Step 5: Commit all**

```bash
git add -A
git commit -m "refactor: consolidation of extraction services — shared utils, race condition fixes, efficiency, prompt quality"
```

---

## Execution Order

```
Group A (Shared Utilities) → Foundation tasks. Must complete before B, C, G.
  A1: JSON extraction utility
  A2: DB insert helpers
  A3: Manifest utility

Group B (Race Conditions) → Depends on A2 (db_inserts.py)
  B1: BEGIN IMMEDIATE + revision number helper

Group C (Efficiency) → Independent, can run in parallel with B
  C1: Move repo load outside chapter loop
  C2: Document truncation limitation

Group D (Frontend) → Independent
  D1: Fix mythology generation modes
  D2: Fix union type

Group E (Minor Cleanups) → Independent
  E1: Protocol types for router
  E2: Simplify _has_pattern_content
  E3: Remove unused import

Group F (Prompt Quality) → Independent
  F1: Narrative analysis prompt
  F2: Mythos analysis prompt
  F3: Story import prompt
  F4: P-100 pattern context

Group G (Integration) → Depends on A-F
  G1: Full validation suite
```

**Recommended execution order:** A1 → A2 → A3 → B1 → D1 → D2 → E1 → E2 → E3 → F1 → F2 → F3 → F4 → C1 → C2 → G1

**Estimated total:** ~15 tasks, 3-4 hours (subagent-driven), all atomic with clear pass/fail gates.
