# Extraction Services — Remaining Work Plan v1.0

> **Status: COMPLETE** — All 6 tasks executed and merged to `codex/main` (2026-04-28)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining findings from Code Review v1.0 and Prompt Optimization Review v1.0 that were not addressed during the consolidation pass.

**Architecture:** All changes are additive/refactoring — zero API contract changes. Forward-compatible with multi-book and future features.

## Results Summary

| Task | Tests | Lines Changed | Status |
|------|-------|---------------|--------|
| P1: Critic prompt expansion | +18 | +207, -3 | ✅ Merged |
| P2: P-100 output guardrails | +9 | +137, -4 | ✅ Merged |
| P3: Summarizer improvements | +8 | +116, -2 | ✅ Merged |
| B1: Braindump JSON consolidation | +9 | +79, -24 | ✅ Merged |
| E1: Error handling middleware | +3 | +94, -27 | ✅ Merged |
| S1: Scene context robustness | +5 | +104, -18 | ✅ Merged |

**Total:** 52 new tests, all passing. 182/182 critical subset passed. Zero regressions.

---

## Task Group P: Prompt Quality Phase 2 (Highest Priority)

### P1: Critic Prompt Expansion

**Source:** Prompt Optimization Review §4.1 — ISSUE 11
**Files:** `app/services/runtime_prompts.py`

**Scope:** Expand the consistency critic system prompt with specific violation criteria, weight guidance, and "NOT violations" section to reduce false positives/negatives.

Current prompt (~300 tokens):
```python
"You are a consistency critic for Narrative-Engine. Check whether each character's dialogue and actions match their profile."
```

Target prompt (~500 tokens):
```python
"""You are a consistency critic for Narrative-Engine.
Check whether characters' dialogue and actions align with their defined profiles.

CHECK FOR:
  1. VOICE: Does word choice, sentence length, and vocabulary match the character?
  2. BEHAVIOR: Do goals, fears, and traits drive the character's actions?
  3. KNOWLEDGE: Does the character only know what they should know?
  4. CONFLICT: Is the character's stance consistent with their values?

NOT VIOLATIONS:
  - Natural character growth or emotional shifts (these are arc progressions)
  - Understatement or subtlety (not all feelings are expressed openly)
  - Cultural or background-appropriate behavior differences

Only flag CLEAR contradictions between profile and draft. Be conservative."""
```

- [ ] Step 1: Read current critic prompt in `runtime_prompts.py`
- [ ] Step 2: Expand system prompt with CHECK FOR / NOT VIOLATIONS sections
- [ ] Step 3: Run critic-related tests
- [ ] Step 4: Commit

### P2: P-100 Output Format Guardrails

**Source:** Prompt Optimization Review §2.1 — ISSUE 5
**Files:** `app/services/runtime_prompts.py`

**Scope:** Add explicit output constraints to P-100 architect prompt: length limits per heading, no preamble/code fences, handling uncertain information.

Current system prompt:
```python
"You are the Architect role for Narrative-Engine. Produce the P-100 story architecture foundation as deterministic markdown."
```

Target: Add explicit constraints for each heading (length, scope), no extra headings, no preamble, no code fences.

- [ ] Step 1: Read current P-100 prompt builder
- [ ] Step 2: Add output format guardrails per heading
- [ ] Step 3: Run P-100 tests
- [ ] Step 4: Commit

### P3: Chapter Summarizer Improvements

**Source:** Prompt Optimization Review §6 — ISSUES 14-16
**Files:** `app/services/runtime_prompts.py`

**Scope:** Three improvements to chapter summarizer prompt:
1. Add granularity guidance for key events (major plot turns, not scene transitions)
2. Improve character state format (goal + emotional state + key change)
3. Remove redundant chapter_id from JSON output schema

- [ ] Step 1: Read current summarizer prompt builder
- [ ] Step 2: Add granularity guidance to key_events instruction
- [ ] Step 3: Update character_states format description
- [ ] Step 4: Remove chapter_id from expected JSON output
- [ ] Step 5: Run summarizer tests
- [ ] Step 6: Commit

---

## Task Group B: Braindump JSON Consolidation (Medium Priority)

### B1: Consolidate braindump.py JSON Parser

**Source:** Code Review v1.0 — 4th copy finding
**Files:** `app/services/braindump.py`, `app/utils/json_extract.py`

**Scope:** Replace braindump's `_parse_llm_json()` (~60 lines) with shared `extract_json()`.

Current: braindump has its own 3-tier JSON parser at line ~143.
Target: Import and use `from ..utils.json_extract import extract_json`.

- [ ] Step 1: Read braindump.py JSON parser location
- [ ] Step 2: Replace with shared `extract_json()` call
- [ ] Step 3: Run braindump tests
- [ ] Step 4: Commit

---

## Task Group E: Error Handling Middleware (Medium Priority)

### E1: Centralize Duplicate Error Handling in projects.py

**Source:** Code Review v1.0 §5.2
**Files:** `app/api/projects.py`

**Scope:** Create a decorator or middleware to centralize the 5× repeated try/except pattern:
```python
try:
    return service.method(...)
except SpecificError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [ ] Step 1: Read current error handling in projects.py
- [ ] Step 2: Create `@service_handler` decorator or middleware
- [ ] Step 3: Apply to all 5 endpoint handlers
- [ ] Step 4: Run project API tests
- [ ] Step 5: Commit

---

## Task Group S: Scene Context Robustness (Low Priority)

### S1: Replace Index-Based Message Access

**Source:** Prompt Optimization Review §3.2 — ISSUE 9
**Files:** `app/services/local_executor.py`

**Scope:** Replace `inference_request.messages[1]` with role-based lookup to avoid brittleness if message count changes.

Current (line ~1118):
```python
new_messages = list(inference_request.messages)
new_messages[1] = InferenceMessage(...)
```

Target:
```python
# Find the user message by role, not index
for i, msg in enumerate(new_messages):
    if msg.role == "user":
        new_messages[i] = InferenceMessage(...)
        break
```

- [ ] Step 1: Read current scene context injection in local_executor.py
- [ ] Step 2: Replace index-based access with role-based lookup
- [ ] Step 3: Run executor tests
- [ ] Step 4: Commit

---

## Execution Order

```
Group P (Prompt Quality Phase 2) → Highest priority — affects all generation quality
  P1: Critic prompt expansion
  P2: P-100 output format guardrails
  P3: Chapter summarizer improvements

Group B (Braindump Consolidation) → Quick win — eliminates last JSON parser copy
  B1: Braindump JSON consolidation

Group E (Error Handling) → Code quality — reduces maintenance burden
  E1: Centralize error handling in projects.py

Group S (Scene Context) → Low priority — current approach works, just brittle
  S1: Replace index-based message access
```

**Recommended execution order:** P1 → P2 → P3 → B1 → E1 → S1

**Estimated total:** 6 tasks, ~2 hours (subagent-driven), all atomic with clear pass/fail gates.

---

## Validation Gates

After each task:
1. Run affected test suite — must pass
2. Run `python -m pytest tests/test_runtime_prompts.py -q` for prompt changes
3. Full critical subset: 217/217 passed before branch merge

Final validation (all tasks complete):
- `python -m pytest -q -p no:cacheprovider` — full suite
- `cd frontend && npm run lint` — lint
- `cd frontend && npm run typecheck` — typecheck
- `cd frontend && npm run build` — build
