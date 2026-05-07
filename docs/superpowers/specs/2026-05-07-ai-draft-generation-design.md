# AI Draft Generation — Design Spec

> Date: 2026-05-07
> Status: Approved
> Scope: Connect manuscript-assist AI generation to "+ New Draft" button in Writing workspace
> Delivery: Single feature, backend + frontend changes

---

## Overview

Extend the M-500 manuscript-assist executor to fulfill the existing `create_draft_artifact` contract. When a user chooses "Generate with AI" from the draft creation flow, the system generates a complete draft via LLM and persists it as a draft artifact — instead of only creating revision suggestions.

**Approach:** Extend M-500 executor (Approach 1). Reuses existing job infrastructure, polling, and error handling. Activates the `create_draft_artifact` flag already defined in the schema but never acted upon by the executor.

---

## Architecture

```
Split button "Generate with AI"
  │
  ▼
DraftForm (AI mode) — title + brief textarea + "Generate" button
  │
  ▼
submitAssist(kind, instruction, { create_draft_artifact: true })
  │
  POST /v1/manuscript-assist/runs
  { project_id, document_id, assist_kind, instruction,
    create_draft_artifact: true, ... }
  │
  ▼
ManuscriptAssistService.submit_assist()
  → creates M-500 job, persists run record (QUEUED)
  │
  ▼
LocalExecutor._run_manuscript_assist_phase()
  ├─ if create_draft_artifact:
  │    → build FULL-CONTENT prompt (new builder)
  │    → LLM generates complete draft text
  │    → DraftingService.register_draft_artifact(content)
  │    → set created_draft_artifact_id on run record
  └─ else:
       → existing suggestions prompt (unchanged)
  │
  ▼
Frontend polls → pending card updates to DRAFT with content
```

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Extend M-500 executor (not new endpoint) | Reuses job queue, polling, circuit breaker, error handling. `create_draft_artifact` flag already in schema. |
| Split button (manual / AI) | Clear mode separation without cluttering UI. Manual form unchanged. |
| Chapter plan first, brief fallback | Structured context when available; flexible when not. Covers all project states. |
| Pending card with in-place update | User sees immediate feedback. No blocking modal. Non-disruptive to workflow. |
| Error degradation to manual form | Resilient — user can always fall back to typing content manually. Retry preserves brief. |

---

## Backend Changes

### 1. New Assist Kind (`app/schemas/manuscript_assist.py`)

Add `ai_generate_draft` to the `ManuscriptAssistKind` enum. This kind does **not** require `text_range` (same as `generate_next_chapter`).

```python
class ManuscriptAssistKind(LiteralString):
    # ... existing kinds ...
    ai_generate_draft = "ai_generate_draft"
```

Update validation: `ai_generate_draft` joins `generate_next_chapter`, `generate_alternate_chapter`, and the review kinds in the non-selection-required group.

### 2. New Prompt Builder (`app/services/runtime_prompts.py`)

Add `build_m500_draft_generation_request()` — produces a full-content generation prompt:

- **System prompt:** "You are a draft generator for narrative fiction. Return strict JSON only: `{ full_content, summary, warnings }`. Generate complete prose content matching the brief and canon context provided."
- **User message:** JSON packet containing:
  - `instruction` — user's brief or chapter plan summary
  - `chapter_plan` — from `chapter_plans` table (if available)
  - `characters` — active character profiles from project canon
  - `world_context` — relevant world bible entries
  - `prior_chapters` — last 3 manuscript summaries (for continuity)
- **Model params:** `temperature=0.7` (creative), `max_tokens=8000` (full chapter)

### 3. Executor Extension (`app/services/local_executor.py`)

In `_run_manuscript_assist_phase()`, after the LLM response is received and before the existing suggestions-parsing logic, add a conditional branch:

```python
if run_record.create_draft_artifact:
    # Draft generation path (NEW)
    parsed = extract_json(response.content)
    content = parsed["full_content"]
    summary = parsed.get("summary", "")
    
    draft_id = hash_id("draft", f"{project_id}:{title}")
    self.drafting_service.register_draft_artifact(
        artifact_id=draft_id,
        project_id=project_id,
        title=title,
        content=content,
        status="DRAFT",
        provenance_note=f"AI-generated via assist {assist_id}"
    )
    
    self.manuscript_assist_repo.update_run(
        assist_id,
        created_draft_artifact_id=draft_id,
        status="completed",
        summary=summary
    )
else:
    # Existing suggestions path (UNCHANGED)
    ...
```

**Title resolution:** If a chapter plan exists for this generation, use `chapter_plans.title`. Otherwise, extract the title from the `instruction` field (first line of the brief, truncated to 255 chars).

### 4. No Changes Required

- `ManuscriptAssistService.submit_assist()` — already passes `create_draft_artifact` through
- `ManuscriptAssistRunRecord` — already has `created_draft_artifact_id` field
- Database schema — no new tables or columns needed
- Existing M-500 suggestion path — untouched

---

## Frontend Changes

### 1. Split Button (`DraftList.tsx`)

Replace the single "+ New Draft" button in the empty state with a button group:

```
┌─────────────────┬──┐
│  + New Draft    │ ▼│
└─────────────────┴──┘
                    └─→ ⚡ Generate with AI
```

- Main button area: opens manual form (unchanged behavior)
- Chevron dropdown: single menu item "⚡ Generate with AI" → opens AI mode form
- Uses existing Tailwind dropdown pattern (no new dependencies)

When drafts exist, the bottom "+ New Draft" button similarly becomes a split button.

### 2. DraftForm AI Mode (`DraftForm.tsx`)

Add `mode: 'manual' | 'ai'` prop to `DraftForm`:

**Manual mode (unchanged):**
- Title input + content textarea + "Create" button

**AI mode:**
- Title input (auto-filled from chapter plan if detected, editable)
- Brief textarea (placeholder: "Describe what this draft should cover...")
- If chapter plan available: show plan summary as hint text above brief
- "Generate" button (shows spinner during submission via `isPending` prop)

### 3. Pending Draft Card (`DraftArtifactCard.tsx`)

New visual state for `PENDING` status:

```
┌─────────────────────────────────┐
│ [spinner] Chapter 2             │
│           Generating...         │
└─────────────────────────────────┘
```

- Created optimistically on form submission (before backend responds)
- React Query polls `GET /v1/manuscript-assist/runs/{assist_id}` every 3s
- On completion: invalidates `draft-artifacts` query → card refetches as `DRAFT` with content
- On failure: transitions to error state (see Error Handling)

### 4. useWritingView Hook (`useWritingView.ts`)

New handler: `handleGenerateDraft(brief: string, title?: string)`

1. Calls `assist.submitAssist('ai_generate_draft', brief, { create_draft_artifact: true })`
2. Creates optimistic draft artifact with `status: 'PENDING'` and the returned `assist_id`
3. Adds optimistic draft to local draft list
4. Tracks `pendingDraftMap: Record<assistId, DraftArtifact>` for polling correlation

New polling effect: watches pending assist runs → on completion, removes from pending map, invalidates draft-artifacts query.

### 5. Chapter Plan Detection

When entering AI mode, check if unplanned chapters exist in the project's `chapter_plans` table. If so:
- Pre-fill title with the next unplanned chapter's title
- Show plan summary as hint text above the brief field
- Use `generate_next_chapter` assist kind instead of `ai_generate_draft`

If no plans exist, use `ai_generate_draft` kind and require user brief.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| LLM timeout (>60s) | M-500 job fails → run status `FAILED` → polling detects failure → pending card shows error banner + "Retry" / "Enter manually" buttons |
| No model available (circuit breaker open) | Same as timeout — card degrades to manual form with error message |
| LLM returns invalid JSON | Executor catches `extract_json()` failure → job fails → same degradation path. No partial content shown. |
| Chapter plan exists but is empty | Treated as "no plan" → falls back to user brief mode |
| Second generation while first is pending | Second PENDING card created. Both poll independently. No blocking. |
| Page refresh during generation | Optimistic PENDING state lost. Backend job completes normally, creates draft artifact. Draft appears on refetch as `DRAFT`. No orphaned state. |
| Title too long (>255 chars) | Form-level validation disables Generate button. Inline error message. |

**Stale pending cards:** Polling timeout after 120s triggers automatic failure → card degrades to manual form with "Generation timed out" banner. User can retry or enter content manually.

---

## Files Changed

| File | Change | Est. Lines |
|------|--------|------------|
| `app/schemas/manuscript_assist.py` | Add `ai_generate_draft` kind, update validation | ~5 |
| `app/services/runtime_prompts.py` | New `build_m500_draft_generation_request()` | ~60 |
| `app/services/local_executor.py` | Draft artifact creation in M-500 phase | ~40 |
| `frontend/src/components/writing/DraftList.tsx` | Split button, AI mode form trigger | ~30 |
| `frontend/src/components/writing/DraftForm.tsx` | AI mode fields, Generate button | ~25 |
| `frontend/src/components/writing/DraftArtifactCard.tsx` | PENDING status rendering, error state | ~35 |
| `frontend/src/hooks/useWritingView.ts` | `handleGenerateDraft`, polling, optimistic state | ~50 |
| **Tests** | | |
| `tests/test_draft_generation.py` | New test file (executor, prompt, schema) | ~120 |
| `frontend/src/components/writing/DraftList.test.tsx` | Split button, AI mode tests | ~60 |

**Total:** ~425 lines new code

---

## Testing Strategy

### Backend Tests (`tests/test_draft_generation.py`)

- `test_ai_generate_draft_kind_no_text_range_required` — schema validation accepts kind without text_range
- `test_executor_creates_draft_artifact_on_flag` — stub inferencer returns valid JSON → verify draft artifact persisted with correct content and `created_draft_artifact_id` set on run record
- `test_executor_invalid_json_fails_gracefully` — stub returns garbage → job fails, no draft created, run status `FAILED`
- `test_executor_chapter_plan_context_injected` — chapter plan exists → verify plan appears in prompt packet
- `test_executor_no_plan_uses_brief` — no chapter plan → verify brief is used as instruction
- `test_prompt_builder_default_params` — verify temperature=0.7, max_tokens=8000

### Frontend Tests (`frontend/src/components/writing/DraftList.test.tsx`)

- Split button renders manual and AI options
- AI mode form shows brief field instead of content textarea
- PENDING card shows spinner, transitions to DRAFT on query invalidation
- Error banner + retry button appear on polling failure
- Optimistic draft created immediately on submit

### Integration Test

Full flow: submit assist with `create_draft_artifact=true` → M-500 runs → draft artifact exists in DB → frontend polls and updates card from PENDING to DRAFT.

### Existing Tests Unchanged

All current M-500 suggestion-path tests remain untouched. New code is entirely behind the `create_draft_artifact` flag.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM generates low-quality content | User can edit draft after generation, or reject and retry with refined brief |
| Large drafts exceed token limits | `max_tokens=8000` caps output. Truncated content still persists as DRAFT for editing |
| Executor crash during draft creation | Draft artifact may not be created even if job shows "completed". User retries. Idempotent by design. |
| Chapter plan context too large for prompt | Canon context truncated to budget-aware limits (reuses existing truncation from CanonPacketBuilder) |
