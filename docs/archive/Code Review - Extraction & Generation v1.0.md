# Code Review: Mythos + Pattern Extraction + Multi-Chapter Generation

**Date:** 2026-04-27
**Scope:** `codex/main~2..HEAD` — 26 files, +11,019 / -117 lines
**Features reviewed:** MythosExtractionService, PatternExtractionService, multi-chapter generation, SceneContext pattern guidance, StoryImportModal triple-mode UI

---

## 1. DUPLICATION

### 1.1 Three-JSON-Parse Logic (3 copies, ~120 lines total)

| File | Method | Lines |
|------|--------|-------|
| `app/services/mythos_extraction.py` | `_extract_json()` | 572-628 |
| `app/services/pattern_extraction.py` | `_parse_llm_json()` | 197-268 |
| `app/services/story_import.py` | `_parse_llm_json()` | (existing) |

All implement identical 3-tier logic: direct JSON parse → markdown fence stripping → balanced-brace fallback. Micro-variations exist (mythos raises `MythosExtractionError`, pattern returns `None`, story_import may have different error handling). Divergence risk grows over time.

**Impact:** ~120 lines of copy-paste code. Each copy must be manually updated for bug fixes or edge cases (e.g., nested JSON strings with escaped braces).

### 1.2 Foundation Import Logic (2 copies, ~80 lines each)

`_import_foundation()` is nearly identical in:
- `mythos_extraction.py:155-233`
- `pattern_extraction.py:451-549`

Both create `foundation_profiles` header row, compute `next_rev` via `COALESCE(MAX(revision_number), 0) + 1`, build `narrative_constraints_json` (differently), then INSERT into `foundation_revisions` with `ON CONFLICT`. The only structural difference is how constraints are assembled.

### 1.3 World Bible Import (2 copies, ~60 lines each)

`_import_world_bible()` in both services:
- `mythos_extraction.py:235-315`
- `pattern_extraction.py:551-631`

Identical INSERT statement for `world_bible_entries`. Only differences: `entry_type` prefix ("Cosmic Rule:" vs "Rule:"), field naming ("rule" vs "rule"), and `summary` construction for motifs.

### 1.4 Character Profile INSERT Template (3 copies, ~40 lines each)

The 25-column `INSERT INTO character_profiles` template is copy-pasted:
1. `mythos_extraction.py:329-389` — `_import_archetypes()` — archetype patterns as characters
2. `mythos_extraction.py:404-463` — `_import_entities()` — deity/force entities as characters
3. `pattern_extraction.py:645-705` — `_import_entities()` — key entities as characters

Only 2-3 field values differ per copy (role_in_story, archetype, backstory_summary, writer_notes).

### 1.5 Entity Relationship INSERT (2 copies, ~20 lines each)

`INSERT INTO relationship_edges` duplicated:
- `mythos_extraction.py:502-532`
- `pattern_extraction.py:707-737`

Identical SQL, identical `ON CONFLICT` clause. Only source/target hashing differs.

### 1.6 Hash ID Functions (2 copies, 5 lines each)

```python
# mythos_extraction.py:565-569
def _hash_id(prefix: str, value: str) -> str:
    raw = f"mythos-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"mythos-{prefix}-{short_hash}"

# pattern_extraction.py:772-776
def _hash_id(prefix: str, value: str) -> str:
    raw = f"pattern-{prefix}-{value.strip().lower()}"
    short_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"pattern-{prefix}-{short_hash}"
```

Only the prefix ("mythos-" vs "pattern-") differs.

### 1.7 Manifest Update (2 copies, ~30 lines each)

`_update_manifest()` in both services follows identical pattern:
1. Construct `project_dir / "manifest.json"` path
2. Check existence, log warning if missing
3. Read JSON, catch `JSONDecodeError` / `OSError`
4. Ensure `config` dict exists
5. Add 2-3 config keys
6. Write back with `ensure_ascii=True, indent=2, sort_keys=True`

### 1.8 JSON Serialization Pattern (40+ occurrences)

`json.dumps(..., ensure_ascii=True, sort_keys=True)` is repeated 40+ times across both files for every list/dict field. No helper function exists.

---

## 2. EFFICIENCY

### 2.1 ChapterSummarizerService Creates Per-Chapter LLM Call

In `_run_multi_chapter_draft` (line 1300-1314), after each chapter is drafted, a separate LLM call summarizes it. For a 10-chapter book: **11 LLM calls minimum** (10 chapters + summarizer per chapter).

**Impact:** Increased latency and cost. For long books, summarizer calls alone could exceed rate limits.

### 2.2 Repository Instantiation Inside Chapter Loop

`_run_multi_chapter_draft` line 1155:
```python
_repo = StoryDevelopmentRepository(settings.operations_db_path)
_chars = _repo.list_character_profiles(project_id)
```

This executes **once per chapter** inside the loop. For a 10-chapter book: 10 redundant SQLite connections.

### 2.3 extract_from_project Reads ALL Manuscript Documents

`pattern_extraction.py:136-144`:
```python
documents = self._repository.list_manuscript_documents(project_id)
text = "\n\n".join(doc.content for doc in documents)
```

Then truncated to 24,000 chars at line 713. If the project has 50 chapters averaging 3,000 chars each (150,000 total), only ~16% of the text reaches the LLM.

---

## 3. RACE CONDITIONS

### 3.1 Non-Atomic Revision Number Increment

`mythos_extraction.py:172-176` and `pattern_extraction.py:468-472`:
```sql
SELECT COALESCE(MAX(revision_number), 0) + 1 FROM foundation_revisions WHERE project_id = ?
-- ... then INSERT with that number
```

Between SELECT and INSERT, another concurrent transaction could insert a higher revision_number. The `ON CONFLICT(project_id, revision_number) DO UPDATE` prevents a crash but **silently overwrites** the first writer's data.

**Impact:** Data loss under concurrent extraction requests for the same project.

### 3.2 `BEGIN` vs `BEGIN IMMEDIATE`

Both services use `conn.execute("BEGIN")` (deferred transaction). SQLite's default opens readers first and writers second, which can cause `database is locked` errors under concurrent writes.

`BEGIN IMMEDIATE` would acquire a reserved lock immediately, causing the second writer to fail fast rather than deadlocking or silently overwriting.

### 3.3 Manifest Read-Modify-Write Without Locking

`_update_manifest()` reads `manifest.json`, modifies in memory, writes back. If two concurrent extractions target the same project, the second write may overwrite the first's changes.

**Impact:** Stale manifest.json despite successful database commit.

### 3.4 Manifest Update Outside Transaction

Both services call `_update_manifest()` AFTER `conn.close()` (outside the transaction). If manifest writing fails:
- Database is already committed
- Project has entities in DB
- Manifest.json is stale

**Impact:** Inconsistent project state — DB says entities exist, manifest doesn't reflect them.

---

## 4. FRONTEND

### 4.1 Inline Type Union

`StoryImportModal.tsx:54`:
```typescript
response: StoryImportResponse | PatternExtractionResponse | { project_id: string; status: 'completed' | 'failed'; error: string | null };
```

The third member is an ad-hoc inline type matching `MythosExtractionResponse`'s shape. Should use the actual type.

### 4.2 Unreachable Generation Mode for Mythology Source Type

The "Extract Patterns" tab has `patternSourceType` (narrative/mythology) and `patternGenMode` (same_world/new_characters/transposed). When source type is "mythology", the backend validation accepts `GENERATION_MODES = ("same_world", "new_characters", "transposed")` — but the mythos service uses different modes (`same_world/transposed/pure_pattern`).

**Impact:** User selects "Extract Patterns → Mythology" but `pure_pattern` mode is unreachable. The `new_characters` mode is invalid for mythology extraction.

### 4.3 Redundant State Variables

`generationMode` (mythos-only, lines 27) and `patternGenMode` (patterns-only, line 29) are separate state variables, only one used at a time based on `importMode`. Could be unified into a single `generationMode` state with type narrowing.

---

## 5. API / SERVER

### 5.1 `Any` Types for Service Injection

`app/api/projects.py:34-35`:
```python
mythos_service: Any = None,
pattern_service: Any = None,
```

These should be typed as the actual service classes or Protocol interfaces for better type safety and IDE support.

### 5.2 Duplicate Error Handling Pattern

All 5 endpoint handlers follow the same pattern:
```python
try:
    return service.method(...)
except SpecificError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
```

Repeated 5 times across the file. A middleware or decorator would centralize.

---

## 6. BACKWARD COMPATIBILITY

### 6.1 Empty project_id on Narrative Failure

`pattern_extraction.py:173-176` returns `project_id=""` on narrative extraction failure:
```python
return PatternExtractionResponse(status="failed", project_id="", error="...")
```

Mythos delegation returns the real `project_id`. Inconsistent — caller can't distinguish "failed before project creation" from "failed after project creation."

---

## 7. MINOR ISSUES

### 7.1 Dynamic `getattr` Usage

`runtime_prompts.py:426`:
```python
def _build_pattern_context_block(pc: Any) -> str:
    mode = getattr(pc, "generation_mode", "same_world") or "same_world"
```

Uses `getattr` everywhere instead of expecting a typed `PatternExtractionAnalysis` parameter. Loses type checking.

### 7.2 Redundant Truthiness Checks

`scene_context.py:112-118`:
```python
def _has_pattern_content(self) -> bool:
    pg = self.pattern_guidance
    return bool(
        (pg and pg.voice_profile)
        or (pg and pg.world_rules)
        or (pg and pg.thematic_constraints)
    )
```

`pg` is checked 3 times in the `or` chain. Simplifiable to:
```python
return bool(pg and (pg.voice_profile or pg.world_rules or pg.thematic_constraints))
```

### 7.3 Unused Import

`pattern_extraction.py:32`:
```python
from .mythos_extraction import MythosExtractionService, MythosExtractionError
```

`MythosExtractionError` is imported but never referenced directly.

---

## RISK ASSESSMENT

| Category | Count | Severity |
|----------|-------|----------|
| Duplication (7 areas) | 7 | Medium — maintainability debt |
| Efficiency (3 areas) | 3 | Low-Medium — performance cost |
| Race conditions (4 areas) | 4 | Medium — data integrity risk |
| Frontend issues (3 areas) | 3 | Low-Medium — UX/type safety |
| API/Server issues (2 areas) | 2 | Low — code quality |
| Minor issues (3 areas) | 3 | Low — cleanup |

**No critical bugs found.** Architecture is sound. Duplication is the highest-impact area for refactoring.
