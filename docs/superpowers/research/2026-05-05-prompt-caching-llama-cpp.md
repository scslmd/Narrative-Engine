# Prompt Caching Research — llama.cpp

Date: 2026-05-05
Build under test: b8643 (Qwen3.6-27B-Q5_K_M)

## Problem

Every P-300 chapter draft re-processes the same static canon context (characters, world bible, foundation) from scratch. For a 10-chapter project with ~10K tokens of canon context, that's ~90K tokens of redundant KV computation across the batch.

## Current State

### P-300 Prompt Structure (`runtime_prompts.py:111-176`)

2 messages:
1. **System** — varies per chapter: includes `chapter_id` label and `target_word_count`. Uses `cache_control={"type": "ephemeral"}` (Fireworks-specific, silently ignored by llama.cpp).
2. **User** — `SceneContext.to_prompt_string()` + JSON prompt context. Mixes static canon (characters, world facts, patterns) with dynamic content (prior chapter summaries, author prompt, chapter plan JSON).

### SceneContext (`scene_context.py:42-117`)

`to_prompt_string()` produces a single blob mixing:
- **Static**: Character anchors, world constraints, pattern guidance
- **Dynamic**: Prior chapter summaries, author prompt, target word count

### Inference Backend (`openai_compatible.py:173-174`)

Already passes `cache_control` through to the HTTP API. Already tracks `cached_tokens` / `prompt_cache_write_tokens` in `InferenceUsage`.

## llama.cpp Caching Mechanisms

### 1. Built-in KV Cache Reuse (default, always on)

- Per-slot prefix matching within the active slot
- When a new request arrives, server finds the longest matching token prefix
- Only the non-matching suffix is re-processed
- Enabled by `--cache-prompt` (default: enabled)
- **Limitation**: cache is lost when the slot is reassigned to a different request

### 2. Host-Memory Prompt Cache (`--cache-ram`, merged PR #16391, Oct 2025)

- Stores completed prompt KV cache in host RAM as "extra slots"
- Calculates prefix similarity across all cached prompts
- Hot-swaps best-matching cached prefix into active context
- Controlled by `--cache-ram N` (N in MiB, default 8192, -1 = unlimited, 0 = disabled)
- **This is the feature we need** — designed specifically for agentic workflows with shared context

**Server log output on cache update:**
```
prompt cache: n_cached = 3, size = 128.5 MiB, limit = 8192 MiB
  [0] tokens = 12500, size = 42.3 MiB
  [1] tokens = 8200, size = 28.1 MiB
  [2] tokens = 15300, size = 58.1 MiB
```

### 3. Context Checkpoints (`--ctx-checkpoints`, `--checkpoint-every-n-tokens`)

- Creates SWA memory checkpoints during prefill
- Useful for branching/generation recovery, not prefix caching

### 4. KV Shifting (`--cache-reuse`)

- Reuses cached chunks via KV shifting
- Complementary to host-memory cache

### 5. Speculative Decoding (`--spec-type`)

- `ngram-mod` — n-gram based draft tokens
- Speeds up token generation 2-4x for predictable text
- **NOT a caching mechanism** — orthogonal speed boost
- Available in b8643, currently disabled (`"none"`)

### What Does NOT Work

| Feature | Status |
|---------|--------|
| `cache_control` on messages | Fireworks AI extension, silently ignored by llama.cpp |
| `--prompt-cache` CLI flag | Does not exist; the flag is `--cache-prompt` (default on) |
| Persistent slot assignment | llama.cpp manages slots; `--cache-ram` is the right approach |

## Benchmarks to Run

### Test 1: `--cache-ram` baseline (no prompt changes)

Send 3 identical P-300 requests (same chapter, same context) with and without `--cache-ram 8192`.

**Expected:** With cache-ram, request 2 and 3 should show `cached_tokens > 0` in response usage. Prefill time should drop significantly on subsequent requests.

**Command:**
```
# Without cache-ram (current)
llama-server -m model.gguf -c 131072

# With cache-ram
llama-server -m model.gguf -c 131072 --cache-ram 8192
```

### Test 2: Prefix match with varying suffix (simulates multi-chapter)

Send 3 requests with identical system + canon context but different chapter-specific content.

**Expected:** With `--cache-ram`, the shared prefix (system + canon) should be cached. Only the varying suffix should be re-processed.

### Test 3: `--spec-type ngram-mod` (orthogonal)

Compare token generation speed with and without speculative decoding.

**Expected:** 2-4x faster token/s for narrative prose. Does NOT affect prefill time.

## Design: Restructuring P-300 for Cache Hits

### Current (no cache benefit)

```
Message 1: System — "You are the Drafter... chapter {chapter_id}... {word_count}"  ← varies per chapter
Message 2: User — Characters + World + Prior Chapters + Pattern + JSON context     ← mixed static/dynamic
```

### Target (maximal cache benefit)

```
Message 1: System — "You are the Drafter role for Narrative-Engine. Produce the P-300 draft as deterministic markdown."  ← STATIC
Message 2: User — Characters + World + Patterns (no prior chapters, no word count)                                       ← STATIC
Message 3: User — Prior chapter summaries + target word count + author prompt                                             ← DYNAMIC (changes per chapter)
Message 4: User — Chapter plan JSON context                                                                               ← DYNAMIC (changes per chapter)
```

**Cache behavior with `--cache-ram`:**
- Messages 1-2 are identical across all chapters → cached as prefix
- Messages 3-4 vary per chapter → only these tokens are re-processed
- Estimated savings: ~80-90% of prefill tokens cached after first chapter

### Key Constraints

1. **System message must be identical** — no chapter label, no word count
2. **Static canon must be its own message** — separated from dynamic content
3. **Prior chapters must be isolated** — they change per chapter in batch mode
4. **Word count must be in dynamic message** — it varies per chapter
5. **JSON prompt context** — `prompt_context` dict includes `sequence_output` and `architect_output` which are static, but the chapter-specific instruction is dynamic; needs splitting

### Implementation Tasks

1. **Remove `cache_control` from P-300 system message** — dead code, silently ignored
2. **Split system message** — static role definition only; move chapter label/word count to user message
3. **Split SceneContext** — separate static canon (characters + world + patterns) from dynamic content (prior chapters + author prompt + word count)
4. **Split prompt_context** — static outputs (architect, sequence) go with static canon; chapter-specific instruction goes with dynamic
5. **Add `--cache-ram` to server startup** — document in AGENTS.md or launcher scripts
6. **Track cache hit rate** — log `cached_tokens` from `InferenceUsage` to verify effectiveness

## Sources

- llama.cpp server README: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Host-memory prompt cache PR: https://github.com/ggml-org/llama.cpp/pull/16391 (merged Oct 2025)
- SWA checkpoints PR: https://github.com/ggml-org/llama.cpp/pull/15293 (merged Aug 2025)
- Context caching discussion: https://github.com/ggml-org/llama.cpp/discussions/16117
- Server API changelog: https://github.com/ggml-org/llama.cpp/issues/9291
