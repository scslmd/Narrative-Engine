# State-Aware Narrative Controller — Design Spec

**Date:** 2026-04-25
**Status:** Approved by user
**Scope:** Character consistency, world continuity, critic loop for P-300 drafter phase

## Problem

The P-300 drafter phase generates prose using only manifest config, P-100 architect markdown, and P-200 sequence JSON. It never queries the rich character profiles, world bible entries, or planning data stored in the operations database. This leads to:

1. Character voice/behavior drift — drafted characters don't match their profiles
2. World continuity breaks — drafted scenes ignore established facts and rules
3. No post-hoc consistency checking — issues are caught manually, not by the system

## Architecture

Two new services wired into the existing P-300 drafter phase:

```
Scene plan (active_character_ids)
  → SceneContextService.assemble_context()
    → [character anchors + world constraints]
      → build_p300_drafter_request()  (augmented prompt)
        → LLM generates draft
          → ConsistencyCriticService.check()
            → PASS: write chapter.md
            → FAIL: deterministic rewrite prompt → LLM → write chapter.md
```

### SceneContextService

Queries the operations database and returns a structured context object for prompt injection.

**Method:** `assemble_context(project_id, active_character_ids=None)` → `SceneContext`

1. If `active_character_ids` is None or empty: fall back to all project characters (limited to 5 by arc stage priority)
2. Query `character_profiles` where `character_id IN (active_character_ids)`
3. For each character, extract the **Anchor**: `archetype`, `voice_notes`, `external_goal`, `internal_need`, `core_fear` (~100 tokens per character)
4. Query `world_bible_entries` for project-scoped entries; filter to location-type entries matching scene context
5. Return as **Actionable Constraints** list:
   - `"Character A [archetype]: goal=X, voice=Y"`
   - `"World: it is raining; B is limping"`

**Fallback:** If no planning data exists (user drafts without scene plans), the service queries all project characters and limits to 5 by arc stage priority. This ensures context injection works even in unplanned drafting flows.

**Dependencies:** `StoryDevelopmentRepository` (existing), no new DB tables

### ConsistencyCriticService

Checks drafted prose against character profiles and returns pass/fail with violations.

**Method:** `check(draft_text, character_profiles)` → `CriticResult`

1. Build inference request: system prompt + character bios + draft text
2. Call LLM to check consistency
3. Parse JSON response: `{passed: bool, violations: [{character, issue, suggestion}]}`
4. If failed and rewrite requested: build targeted rewrite prompt, call LLM once (max 1 retry)

**Dependencies:** `InferenceBackend` (existing), no new DB tables

### EntityIntakeService

When the draft introduces characters or world elements not yet in the database, extract skeletal profiles from their behavior in the prose.

**Method:** `intake_new_entities(draft_text, known_character_ids)` → `list[NewEntity]`

1. Extract proper nouns and character-like references from draft text (rule-based: capitalized names, pronouns with context)
2. Compare against `known_character_ids` — any unknown references are candidates
3. For each candidate, build LLM extraction request: "From this draft passage, extract a character profile for [NAME]. Infer archetype, voice, apparent goal from their dialogue and actions."
4. Parse JSON response into skeletal `CharacterProfile` with `auto_generated=true`
5. Upsert into `character_profiles` table via repository

**Dependencies:** `StoryDevelopmentRepository`, `InferenceBackend`

### Integration Point

In `local_executor.py`, `_run_drafter_phase()`:

1. Attempt to resolve chapter packet → extract scene plans and `active_character_ids`
2. If no planning data exists, call `SceneContextService.assemble_context(project_id)` — it falls back to all project characters (limited to 5)
3. Call `SceneContextService.assemble_context(project_id, active_character_ids)` before building drafter request
4. Augment prompt with character anchors and world constraints
5. After LLM draft: call `ConsistencyCriticService.check()`
6. If violations: trigger rewrite pass (max 1 retry), then accept

## Data Flow

**Prompt assembly:**
- Current: manifest config + architect markdown + sequence JSON → ~3000 tokens
- With context injection: above + character anchors (~100 tokens/char) + world constraints (~50 tokens/fact) → ~4000-6000 tokens

**Critic pass:**
- Input: draft text (~2000 tokens) + full character bios for active characters (~500 tokens/char)
- Output: JSON with pass/fail and violations
- Rewrite: targeted prompt focusing only on flagged passages

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty `active_character_ids` | Proceed with no context injection — don't block drafting |
| Character profile not found in DB | Log warning, skip that character |
| Critic LLM call fails (timeout, network) | Log warning, proceed with original draft — never fail pipeline on critic error |
| Rewrite pass fails | Accept original draft, log violation count |
| Rewrite draft also fails critic | Accept original draft (max 1 retry) |

## Testing

| Test | Type | What it verifies |
|------|------|-----------------|
| `test_scene_context_assembles_character_anchors` | Unit | Correct character filtering by `active_character_ids` |
| `test_scene_context_handles_empty_active_characters` | Unit | Graceful degradation when no active characters |
| `test_critic_passes_consistent_draft` | Unit | Pass classification with matching character behavior |
| `test_critic_fails_inconsistent_draft` | Unit | Violation detection for voice/behavior mismatch |
| `test_critic_rewrite_targets_flagged_passages` | Unit | Rewrite prompt includes only flagged content |
| `test_drafter_phase_injects_context` | Integration | Full P-300 phase with fake inferencer → context in prompt |
| `test_drafter_phase_runs_critic_check` | Integration | Critic runs after draft, rewrite triggers on failure |
| `test_intake_detects_new_character_from_draft` | Unit | New character reference extracted from prose |
| `test_intake_creates_skeletal_profile` | Unit | LLM extraction creates valid CharacterProfile |
| `test_intake_skips_known_characters` | Unit | Known character IDs are excluded from intake |
| `test_intake_upserts_to_repository` | Integration | Full intake pipeline persists to DB |

## Schema Changes

None. All required data already exists:

- `character_profiles`: archetype, voice_notes, external_goal, internal_need, core_fear, secrets, misbelief_or_wound
- `world_bible_entries`: entry_type, title, summary, canonical_facts_json
- `scene_plans`: active_character_ids (already used for planning)

## New Files

| File | Purpose |
|------|---------|
| `app/services/scene_context.py` | SceneContextService class |
| `app/services/consistency_critic.py` | ConsistencyCriticService class |
| `app/services/entity_intake.py` | EntityIntakeService class |
| `tests/test_scene_context.py` | Unit tests for context assembly |
| `tests/test_consistency_critic.py` | Unit + integration tests for critic |
| `tests/test_entity_intake.py` | Unit + integration tests for intake |

## Modified Files

| File | Change |
|------|--------|
| `app/services/local_executor.py` | Wire context injection before drafting, critic check after |
| `app/services/runtime_prompts.py` | Add `build_drafter_context_request()` and `build_critic_check_request()` |
| `app/main.py` | Register new services at startup |

## Out of Scope (Future)

- Semantic search / vector embeddings for world bible retrieval (Approach 3)
- Working memory / rolling summary of last N beats
- Critic configuration via UI (enable/disable, threshold tuning)
- Multi-scene continuity tracking across chapters
