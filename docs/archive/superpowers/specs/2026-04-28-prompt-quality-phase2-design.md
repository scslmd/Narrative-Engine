# Prompt Quality Phase 2 — Design Spec

**Date:** 2026-04-28
**Branch:** `codex/main`
**Approach:** A — Minimal additive changes, backward-compatible optional fields

## Overview

Three independent features that improve draft output quality and prepare for vLLM inference backend migration:

1. **P-300 Chapter Length Guidance** — `target_word_count` controls draft length via manifest default with per-chapter override
2. **Critic Violation Locations** — line numbers and quoted excerpts enable precise rewrite targeting
3. **Prompt Caching Passthrough** — `cache_control` annotations activate prefix caching on vLLM, no-op on llama.cpp

All changes are additive. New fields default to `None`. Zero breaking changes to API contracts or schemas.

## Architecture

```
app/schemas/manifest.py              → +target_word_count on ManifestConfig
app/services/scene_context.py        → +target_word_count on SceneContext; rendered in to_prompt_string()
app/persistence/story_development.py → +target_word_count column on chapter_plans table
app/services/runtime_prompts.py      → P-300 length instruction; critic prompt locations; cache tagging
app/services/consistency_critic.py   → +line_start, line_end, quote on Violation
app/services/local_executor.py       → rewrite prompt uses location info
app/schemas/inference.py             → +cache_control on InferenceMessage; +cache metrics on Usage
app/inference/openai_compatible.py   → cache_control passthrough in serialization
```

Each feature is self-contained with no cross-feature dependencies.

---

## Feature 1: P-300 Chapter Length Guidance

### Problem

P-300 drafter has no length control. The only mechanism is `max_tokens=8000` (token budget), which doesn't translate to meaningful word count targets. Users cannot express "I want ~2000-word chapters" through any project configuration.

### Design

#### Schema Changes

**ManifestConfig** (`app/schemas/manifest.py`):
```python
target_word_count: int | None = Field(default=None, ge=100)
```
Minimum 100 words prevents meaningless targets. `None` means no length instruction.

**SceneContext** (`app/services/scene_context.py`):
```python
target_word_count: int | None = None
```
Rendered in `to_prompt_string()` as a new `CHAPTER LENGTH:` section.

**ChapterPlan** (database schema, `app/persistence/story_development.py`):
Add optional column `target_word_count INTEGER` to `chapter_plans` table. Migration: ALTER TABLE with nullable column — no data loss on existing rows. Corresponding schema field in `ChapterPlanCreateRequest` and `ChapterPlanUpdateRequest`.

#### Override Chain

Resolved in `build_p300_drafter_request()`:
1. `payload.get("target_word_count")` — job-level override (highest priority)
2. `scene_context.target_word_count` — per-chapter override from ChapterPlan
3. `manifest.config.target_word_count` — project default
4. No instruction if all are `None`

#### Prompt Injection

When a target is resolved, append to system prompt:
```
Target length: approximately {target_words} words.
Adjust detail and pacing to meet this target while maintaining story quality.
```

#### SceneContextService Integration

`assemble_context()` resolves `target_word_count`:
- If ChapterPlan exists and has `target_word_count`, use it
- Else fall through to manifest default
- Pass resolved value to SceneContext constructor

### Testing

5 tests in `tests/test_p300_length_guidance.py`:
1. Manifest default applied when no override
2. Payload override takes precedence over manifest
3. Scene context override takes precedence over manifest, below payload
4. No instruction emitted when all sources are None
5. System prompt content includes length instruction with correct value

---

## Feature 2: Critic Violation Locations

### Problem

Critic violations describe WHAT's wrong but not WHERE in the draft text. The rewrite LLM must search the entire draft to find problematic passages, producing imprecise rewrites that may miss the actual violation or alter unrelated content.

### Design

#### Schema Changes

**Violation** (`app/services/consistency_critic.py`):
```python
@dataclass(slots=True)
class Violation:
    character: str
    issue: str
    suggestion: str
    line_start: int | None = None
    line_end: int | None = None
    quote: str | None = None
```
All new fields optional — backward compatible with existing critic responses.

#### Prompt Changes

**System prompt** (`runtime_prompts.py`): JSON schema instruction updated:
```json
{
  "passed": true or false,
  "violations": [
    {
      "character": "<name>",
      "issue": "<what is wrong>",
      "suggestion": "<how to fix>",
      "line_start": <int or null>,
      "line_end": <int or null>,
      "quote": "<short excerpt of the offending text>"
    }
  ]
}
```

Additional instruction:
```
For each violation, include approximate line numbers (line_start, line_end)
and a short quoted excerpt (max 100 characters) of the problematic passage.
Line numbers refer to the numbered draft below.
```

**User message:** Draft text prefixed with line numbers for reliable LLM reference:
```
DRAFT TO CHECK (line numbers for reference):
1: First line of draft...
2: Second line...
...
```
Capped at 500 lines to avoid token bloat on long drafts. Lines beyond 500 are truncated with a note.

#### Rewrite Prompt Changes

**local_executor.py:** Violation summary incorporates location info when available:
```
- {character} (lines {line_start}-{line_end}): {issue}
  Quote: "{quote}"
  Fix: {suggestion}
```
When location fields are `None` (backward compat), degrade to original format:
```
- {character}: {issue} -> {suggestion}
```

### Testing

6 tests in `tests/test_critic_locations.py`:
1. Line-numbered draft input generated correctly
2. JSON schema includes line_start, line_end, quote fields
3. Rewrite prompt formats location info when present
4. Rewrite prompt degrades gracefully when locations are None
5. Long draft truncation at 500 lines with truncation note
6. Backward compatibility — old responses without locations parse correctly

---

## Feature 3: Prompt Caching Passthrough

### Problem

When switching to vLLM, prefix caching can reduce token processing costs for repeated context (system prompts, character profiles, world bible entries). Currently no infrastructure exists to signal cacheable content to the backend.

### Design

#### Schema Changes

**InferenceMessage** (`app/schemas/inference.py`):
```python
class InferenceMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str
    cache_control: dict[str, Any] | None = None
```

**InferenceUsage** (`app/schemas/inference.py`):
```python
class InferenceUsage(StrictModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_prompt_tokens: int | None = None
    prompt_cache_write_tokens: int | None = None
```

#### Backend Passthrough

**OpenAICompatibleInferenceBackend** (`app/inference/openai_compatible.py`):

Serialization includes `cache_control` when present:
```python
messages = []
for msg in request.messages:
    d = {"role": msg.role, "content": msg.content}
    if msg.cache_control is not None:
        d["cache_control"] = msg.cache_control
    messages.append(d)
payload["messages"] = messages
```

Response parser extracts cache metrics from provider response:
```python
cached_tokens = usage_payload.get("cached_prompt_tokens") or usage_payload.get("prompt_cache_read_tokens")
cache_write_tokens = usage_payload.get("prompt_cache_write_tokens")
```

#### Tagging Strategy

Tag stable prefix content in multi-chapter drafting. The tagging logic lives in `build_p300_drafter_request()`, which constructs the message list for P-300 calls:
- System prompt message → `cache_control={"type": "ephemeral"}`
- Scene context user message (characters, world, prior summaries) → `cache_control={"type": "ephemeral"}`
- Chapter-specific instruction user message → no cache_control (varies per call)

`local_executor.py` does not tag messages — it calls `build_p300_drafter_request()` which returns tagged `InferenceRequest` objects.

#### Current Behavior

- **llama.cpp:** No caching support. `cache_control` fields are sent but ignored by the server. No functional impact.
- **vLLM:** Activates prefix caching when server has chunked-prefill enabled. Stable prefixes (system prompt, context blocks) are cached across consecutive chapter calls, reducing processing time for repeated content.

### Testing

4 tests in `tests/test_prompt_caching.py`:
1. `cache_control` passthrough in message serialization when present
2. `cache_control` omitted from payload when None
3. Cache usage metrics extracted from response
4. Stable prefix tagging applied to system and context messages in multi-chapter mode

---

## Error Handling

All new fields are optional with `None` defaults:
- If LLM omits location fields (older model), critic degrades to original behavior
- If backend ignores `cache_control`, no functional impact
- If `target_word_count` is absent from manifest, P-300 operates without length instruction

No new exception types. Existing error handling paths cover all new code.

---

## Future Enhancements (Tabled — Approach B)

The following were considered but deferred to a future phase:

### B1: Two-Phase Critic

Separate violation detection from location finding into two LLM calls:
- Phase 1: Identify WHAT's wrong (current behavior, enhanced analysis)
- Phase 2: Given the violations, find WHERE they occur in the draft

**Benefit:** More accurate line numbers because each LLM call focuses on one task.
**Cost:** Additional LLM call per critic run (~2x critic latency). Schema migration for stored results.
**Trigger:** Implement when critic accuracy becomes a bottleneck.

### B2: Post-Draft Word Count Gate

After P-300 generates a draft, count actual words and compare against `target_word_count`:
- If within ±20%, accept as-is
- If outside tolerance, trigger automatic rewrite with adjusted length instruction

**Benefit:** Guaranteed length compliance rather than best-effort LLM guidance.
**Cost:** Additional LLM call for drafts that miss the target (slower pipeline).
**Trigger:** Implement when users report consistent length drift.

### B3: Caching Abstraction Layer

Replace raw `cache_control` passthrough with a `CachingStrategy` protocol:
- Backend-aware activation — automatically enable/disable based on provider capabilities
- Configurable cache granularity — control which message segments are cached
- Cache hit/miss telemetry exposed through metrics endpoint

**Benefit:** No manual tagging required when switching backends.
**Cost:** ~150 lines of protocol code. Adds abstraction layer that may not be needed for simple passthrough.
**Trigger:** Implement when managing multiple backends with different caching capabilities.

---

## Validation Criteria

After implementation:
- `python -m pytest tests/test_p300_length_guidance.py -q` → 5/5 passed
- `python -m pytest tests/test_critic_locations.py -q` → 6/6 passed
- `python -m pytest tests/test_prompt_caching.py -q` → 4/4 passed
- Full critical subset (217 existing + 15 new = 232) → all passed
- Frontend lint/typecheck/build → unchanged (no frontend changes)
