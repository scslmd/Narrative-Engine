# Guided Setup Planning Extension — Design Spec

**Date:** 2026-05-08
**Branch:** `codex/guided-setup-planning`
**Status:** Approved

## Problem

The guided setup wizard collects config, foundation, characters, world bible, and arcs — but produces no planning-level data (sequences, chapters, scenes, beats). After project creation, the Plan view is empty. The user must either manually fill out the structure or run the full generation pipeline, which defeats the purpose of a guided conversational setup.

## Decision Record

| Question | Decision |
|----------|----------|
| When to generate planning? | During conversation, after core categories reach ≥0.7 completeness |
| How deep? | Sequences + chapters only (no scenes/beats) |
| Interaction model? | Conversational — LLM proposes outline, user adjusts naturally |
| Prompt strategy? | Single extended prompt with 7 categories (not separate phase) |

## Design

### 1. Schema Extension

**File:** `app/schemas/guided_setup.py`

Two new Pydantic models:

```python
class GuidedSequence(StrictModel):
    sequence_id: str          # deterministic hash
    title: str                # min_length=1, max_length=255
    summary: str              # max_length=5000
    chapter_ids: list[str]    # populated after chapter persistence
    status: str               # default "guided"

class GuidedChapter(StrictModel):
    chapter_id: str           # deterministic hash
    sequence_id: str | None   # FK reference to parent sequence
    title: str                # min_length=1, max_length=255
    summary: str              # max_length=5000
    objective: str            # what this chapter achieves
    conflict: str             # central tension in this chapter
    stakes: str               # what's at risk
    active_character_ids: list[str]  # character names (resolved to IDs on persist)
    continuity_requirements: list[str]
    unresolved_questions: list[str]
    position: int             # display order within sequence
    status: str               # default "guided"
```

`ExtractedFields` gains:
```python
sequences: list[GuidedSequence] = Field(default_factory=list)
chapters: list[GuidedChapter] = Field(default_factory=list)
```

`CategoryProgress` adds two new trackable categories: `"sequences"` and `"chapters"`.

`ready_to_create` requires all 7 categories (config, foundation, characters, world_bible, arcs, sequences, chapters) to reach ≥0.7 completeness. Progress is average of all 7 category completeness values × 100.

### 2. System Prompt Extension

**File:** `app/services/runtime_prompts.py`

`_GUIDED_SETUP_SYSTEM_PROMPT` extended with:

**New collection step (10):**
```
10. **Story structure**: Once core elements are collected, organize the story into
    sequences and chapters. Ask about pacing, chapter count, and major turning points.
    Propose a sequence/chapter outline for the user to confirm or adjust.
```

**Transition guidance:**
```
When config, foundation, characters, world_bible, and arcs all reach 0.7+ completeness,
shift focus to structuring the story into sequences and chapters. Present a proposed
outline and ask if it works or needs adjustment. Do not set ready_to_create until the
user has confirmed the story structure.
```

**Output format extension:**
```json
"sequences": [{"sequence_id": "", "title": "", "summary": "", "chapter_ids": []}],
"chapters": [{"chapter_id": "", "sequence_id": "", "title": "", "summary": "",
    "objective": "", "conflict": "", "stakes": "", "active_character_ids": [],
    "continuity_requirements": [], "unresolved_questions": [], "position": 0}]
```

`max_tokens` for guided setup remains at `settings.inference_max_tokens("GUIDED_SETUP")` (default 8192), sufficient for extended conversation with planning data.

### 3. Parsing Response

**File:** `app/services/guided_setup.py`

`_parse_analyze_response` extended to handle `sequences` and `chapters` from LLM JSON:

```python
merged_sequences = extracted_raw.get("sequences") or previous_fields.get("sequences", [])
merged_chapters = extracted_raw.get("chapters") or previous_fields.get("chapters", [])

extracted.sequences = [GuidedSequence(**s) for s in merged_sequences] if merged_sequences else []
extracted.chapters = [GuidedChapter(**c) for c in merged_chapters] if merged_chapters else []
```

Category progress tracking includes sequences and chapters completeness calculation.

### 4. Persistence

**File:** `app/services/guided_setup.py`

`create_project_from_fields` extends its transaction:

After existing inserts (foundation, characters, world, arcs), adds:

1. **Build character ID map**: Resolve character names from chapter `active_character_ids` to persisted IDs using existing `hash_id("guided-character", ...)` pattern.

2. **Insert sequences** (`_insert_sequence`):
   - ID: `hash_id("guided-sequence", f"{project_id}:{title}")`
   - Raw SQL INSERT into `sequence_plans` with ON CONFLICT DO UPDATE
   - Status: `"guided"`, confidence: 0.75

3. **Insert chapters** (`_insert_chapter`):
   - ID: `hash_id("guided-chapter", f"{project_id}:{chapter_id}")`
   - Raw SQL INSERT into `chapter_plans` with ON CONFLICT DO UPDATE
   - Resolve `sequence_id` FK, character name → ID mapping
   - Status: `"guided"`, confidence: 0.75

4. **Second pass on sequences**: Update `beat_ids_json` and `chapter_ids_json` with actual persisted chapter IDs (same pattern as story import `_import_planning`).

All operations within existing `BEGIN IMMEDIATE` transaction. Rollback on any failure.

### 5. Frontend

**File:** `frontend/src/components/guided-setup/FieldPreview.tsx`

Two new collapsible panels added below "Arcs":

**Sequences (N)** — shows sequence title, summary, chapter count
**Chapters (N)** — shows chapter title, summary, objective, assigned sequence

Panel open/close state:
- Auto-open when data first appears (sequences.length > 0 or chapters.length > 0)
- After user collapses, do NOT auto-reopen on subsequent updates
- Tracked via `useState` per panel with initial value derived from whether data exists at mount

**File:** `frontend/src/services/guidedSetup.ts`

`ExtractedFields` type extended with `sequences` and `chapters` arrays matching backend schema.

### 6. Testing

**File:** `tests/test_guided_setup.py`

New test areas:
- `test_analyze_turn_includes_sequences_and_chapters` — LLM produces planning data in JSON
- `test_parse_analyze_response_merges_planning` — merge logic preserves previous + new values
- `test_create_project_persists_sequences` — sequences inserted into `sequence_plans` table
- `test_create_project_persists_chapters_with_sequence_link` — chapters linked to parent sequence
- `test_create_project_resolves_character_names_to_ids` — chapter `active_character_ids` resolved from character names

## Out of Scope

- Scenes and beats (user fills in Plan view or via generation pipeline)
- Chapter packets and planning dependencies
- Real-time LLM validation of proposed outline
- Undo/redo for planning changes within wizard
