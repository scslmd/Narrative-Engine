# Full Code Review Findings

**Date:** 2026-05-22
**Scope:** Entire codebase (`app/`, `frontend/src/`, `tests/`)
**Branch:** `codex/radial-hub` (pre-merge into `codex/main`)
**Method:** Systematic analysis of backend services, API routers, persistence layer, frontend components, hooks, stores, and test suite.

---

## Executive Summary

| Severity | Count | Top Issues |
|----------|-------|------------|
| Critical | 5 | God files (6269/3138/2564/2440 lines), duplicated import methods, router business logic, 33-param functions |
| High | 5 | Depth-8 nesting, bypassed React Query, duplicated polling, 20 useState calls, stale closure queries |
| Medium | 5 | Mixed persistence, dead schema models, 65 fire-and-forget promises, synthetic event cast, inline styles |
| Low | 4 | Empty inits, duplicate CSS, incomplete barrel, unused var suppression |

---

## CRITICAL FINDINGS

### C-1: God Files — Unmaintainable Module Sizes

Six modules exceed maintainable size thresholds. These are the highest-leverage targets for refactoring.

| File | Lines | Issue |
|------|-------|-------|
| `app/persistence/story_development.py` | **6,269** | ALL story dev CRUD in one file — branches, flows, arcs, planning (sequences/chapters/scenes/beats), drafting, brainstorm, braindump, canon annotations, customization profiles, mythos, patterns, storyboards, chapter packets, dependencies. ~100+ CRUD functions + 20+ `@dataclass` definitions. |
| `app/api/story_development.py` | **3,138** | 30+ endpoints across 15+ distinct domains + 35 inline Pydantic response models + business logic for PATCH field-level merging + conversion helpers. |
| `app/services/local_executor.py` | **2,564** | ALL job phase execution (P-100 through P-400, G-200 through G-400, M-500 through M-550), role model checker execution, thread lifecycle, inference orchestration, step record creation, lineage registration, consistency critic integration, multi-chapter drafting loop. |
| `app/services/runtime_prompts.py` | **2,440** | ALL prompt building logic for every phase. Long system prompt strings embedded inline as string literals. |
| `frontend/src/domains/planning/usePlanningController.ts` | **1,076** | Single React hook with 85-field `PlanningTabState` interface, 55+ setter functions, 10+ queries, 20+ mutations, callbacks, and error conversions. |
| `frontend/src/views/PlanningView.tsx` | **761** | 12+ tab sub-applications (manifest, planning, flow, arcs, branches, decisions, checker, brainstorm, foundation, characters, world bible, relationships) rendered in a single component with its own CRUD mutations. |

**Recommended action:**
- `story_development.py` persistence → split into `branches.py`, `planning.py`, `drafting.py`, `arcs.py`, `bible.py`, `library.py`
- `story_development.py` router → split into `story_branching.py`, `story_planning.py`, `story_drafting.py`, `story_knowledge.py`, `story_review.py`, `story_exploration.py`, `story_canvas.py`
- `local_executor.py` → extract phase handlers into `executor_phases/` directory
- `runtime_prompts.py` → split into `prompts_p100.py`, `prompts_p300.py`, etc. + extract system prompts to `prompt_templates.py`
- `usePlanningController.ts` → `useSequenceController`, `useChapterController`, `useSceneController`, `useBeatController`, `useArcController`
- `PlanningView.tsx` → move per-tab state into sub-components

---

### C-2: Massive Code Duplication — `import_story` vs `import_story_with_progress`

**File:** `app/services/story_import.py:115-290`

Two methods that are ~95% identical. The only difference: `import_story_with_progress` inserts 3 `on_progress()` callback calls. All error handling, response construction, and control flow is duplicated verbatim.

```python
def import_story(self, request) -> StoryImportResponse:         # line 115
def import_story_with_progress(self, request, on_progress) -> ... # line 196
```

**Impact:** ~80 lines of duplicated logic. Any bug fix must be applied to both methods.

**Fix:** Consolidate into one method:
```python
def import_story(self, request, on_progress=None) -> StoryImportResponse:
    # Guard callbacks with: if on_progress: on_progress("phase", data)
```

---

### C-3: PATCH Field-Merge Business Logic in Router (5+ Copies)

**File:** `app/api/story_development.py`

| Handler | Lines | Fields Merged |
|---------|-------|---------------|
| `update_chapter_plan` | 1368-1377 | 10 fields |
| `update_scene_plan` | 1433-1442 | 9 fields |
| `update_beat_plan` | 1497+ | 8 fields |
| `update_chapter_packet` | 2930+ | 8 fields |
| `update_sequence_plan` | 3001+ | 6 fields |

Each handler repeats this pattern:
```python
title = payload.title if payload.title is not None else existing.title
summary = payload.summary if payload.summary is not None else existing.summary
objective = payload.objective if payload.objective is not None else existing.objective
# ... 5-8 more fields per handler
```

Then calls `create_*` as an upsert — which is a misleading API contract (create != update).

**Why it matters:** This is business logic in the router. The router's responsibility is: validate input → call service → translate errors to HTTP codes. Field-level merging belongs in the service layer.

**Fix:** Move merge logic into service-layer `update_*` methods. Or create a utility:
```python
def merge_partial_update(existing: object, payload: object, fields: list[str]) -> dict:
    return {f: getattr(payload, f) if getattr(payload, f) is not None else getattr(existing, f)
            for f in fields}
```

---

### C-4: LLM Inference + File I/O in Router Handler

**File:** `app/api/projects.py:153-191`

The `generate_description` endpoint directly:
1. Imports inference backend and prompt builder (lines 161-163)
2. Builds inference request (lines 165-172)
3. Calls `backend.generate_text()` (line 176)
4. Writes result to `manifest.json` via raw file I/O (lines 182-189)

This is a complete business workflow (inference → persistence) in a router handler.

**Fix:** Create `ProjectDescriptionService.generate_description(project_id)` that encapsulates the full flow.

---

### C-5: Functions With 25-33 Parameters

Functions that accept more parameters than can be reasonably tracked mentally. These are error-prone at call sites (positional arg mistakes, silent `TypeError` on missing args).

| Function | Params | File |
|----------|--------|------|
| `create_step_record()` | **33** | `app/persistence/steps.py:48-81` |
| `StepRecordService.create_step_record()` | **32** | `app/services/step_records.py` |
| `_finalize_generated_job_phase()` | **31** | `app/services/local_executor.py` |
| `upsert_character_profile()` | **27** | `app/persistence/story_development.py` |
| `record_story_decision_node()` | **25** | `app/persistence/story_development.py` |

**Fix:** Use dataclasses:
```python
@dataclass
class StepRecordData:
    logical_run_id: str
    run_id: str
    run_kind: str
    attempt_number: int
    # ... remaining fields with defaults
```

---

## HIGH SEVERITY

### H-1: Deep Nesting (Depth 8)

**File:** `app/services/local_executor.py:1308-1350`

Nesting chain:
```
_process_job
  └─ _run_multi_chapter_draft
      └─ for chapter in chapter_ids
          └─ try:
              └─ if self._consistency_critic:
                  └─ try:
                      └─ for v in critic_result.violations[:3]
                          └─ if v.line_start is not None:
                              └─ violation_lines.append(...)  # DEPTH 8
```

**Fix:** Extract `_format_critic_violations(critic_result)` and `_execute_rewrite(output_text, inference_request)` methods.

---

### H-2: Mutation Objects Bypass React Query

**File:** `frontend/src/domains/planning/usePlanningController.ts:347-378`

Storyboard mutations use plain `{ mutateAsync: () => serviceCall().then(invalidate) }` objects instead of `useMutation` hooks. This means:
- No `isLoading`, `isError`, `isSuccess` state tracking
- No error handling via `onError`/`onSettled`
- No automatic retry or refetch
- Silent failures with no user feedback

**Fix:** Use proper `useMutation` hooks.

---

### H-3: Polling Logic Duplicated 3 Times

**File:** `frontend/src/components/projects/StoryImportModal.tsx:101-220`

Identical `setInterval` polling pattern copy-pasted for patterns, mythos, and story imports:
1. Start interval at 2000ms
2. Poll status endpoint
3. On completed: clear interval, navigate, invalidate, close
4. On failed: clear interval, set error, toast
5. On exception: swallow and keep polling

**Fix:** Extract `useAsyncPoll<T>({ id, fetchFn, onCompleted, onFailed })` hook.

---

### H-4: 20 `useState` Calls in CharacterBuilder

**File:** `frontend/src/components/characters/CharacterBuilder.tsx:29-48, 50-71`

20 separate `useState` calls for individual form fields. `useEffect` fires 20 state updates per character prop change, triggering 20 re-renders.

**Fix:** Consolidate into single `useState<CharacterFormState>` with `initializeFromCharacter(character)` reset function.

---

### H-5: Implicit Query Dependency in Closure

**File:** `frontend/src/views/PlanningView.tsx:130-138`

```typescript
const firstWorldEntryQuery = useQuery({
  queryFn: async () => {
    const firstEntry = (worldBibleQuery.data ?? [])[0]; // reads from another query closure
    if (!firstEntry) return null;
    return getWorldBibleEntry(...);
  },
  enabled: ... && (worldBibleQuery.data ?? []).length > 0,
});
```

`firstWorldEntryQuery`'s `queryFn` reads `worldBibleQuery.data` from a closure — capturing a stale value if the parent re-renders while the query is in-flight.

**Fix:** Use dependent query keys or derive from existing data directly.

---

## MEDIUM SEVERITY

### M-1: Mixed Persistence Strategies

| Service | Pattern |
|---------|---------|
| `app/services/story_import.py` | Uses `StoryDevelopmentRepository` AND raw `sqlite3` with `BEGIN IMMEDIATE` |
| `app/services/pattern_extraction.py` | Same — repository + raw SQL |

The raw SQL is used for atomic transactional persistence of imported/extracted entities. The code documents this choice ("NOT repo methods"), which is architecturally justified for atomicity. However, it creates a dual-strategy codebase that's difficult to maintain: changes to entity schemas must be reflected in both repository methods AND raw SQL strings.

**Recommendation:** Either add transaction support to the repository layer (batch upsert with single connection), or document the dual-strategy rationale in a design doc.

---

### M-2: Dead Code in Schemas (25+ Unused Models)

Models defined but never imported by any router, service, or persistence module:

| Model | File |
|-------|------|
| `ApplyAssistMode`, `AssistCanonRisk` | `app/schemas/manuscript_assist.py` |
| `ArtifactLineage`, `ArtifactLineageRecord`, `ArtifactLineageResponse`, `ArtifactLineageView` | `app/schemas/story_development.py`, `app/schemas/jobs.py`, `app/schemas/inspect.py` |
| `CanonAnnotationKind`, `CanonProfileStatus`, `CanonTargetKind` | `app/schemas/canon_customization.py` |
| `ContinuityStrictness`, `DestinationKind`, `GenerationDestination`, `GenerationMode`, `GenerationPlanStatus`, `GenerationReviewPolicy` | `app/schemas/generation.py` |
| `ChatMessage` | `app/schemas/guided_setup.py` |
| `InferenceResponse`, `InferenceUsage` | `app/schemas/inference.py` |
| `JobAttempt`, `JobAttemptSummaryStats`, `JobEvent` | `app/schemas/jobs.py` |
| `ModelSelectionWarning` | `app/schemas/models.py` |
| `MythosEntryType`, `MythosVisibilityScope` | `app/schemas/mythos_library.py` |
| `PatternEntryType`, `PatternSourceType` | `app/schemas/pattern_library.py` |
| `ExtractionProgressResult` | `app/schemas/extraction_progress.py` |
| `BrainstormItemTypes`, `BranchPoint` | `app/schemas/enums.py`, `app/schemas/story_development.py` |

**Recommendation:** Audit each model. Remove if truly unused. Add `# used by: ...` comment if used via `__init__.py` re-export or runtime `typing.Literal`/enum value access.

---

### M-3: `void` Fire-and-Forget Pattern (65 Occurrences)

```typescript
void queryClient.invalidateQueries({ queryKey: ['planning', 'relationships', projectId] });
void relationshipDeleteMutation.mutate(edgeId);
void assist.submitAssist(kind, instruction, { create_draft_artifact: true });
```

Errors from these calls are silently swallowed. A failed mutation is indistinguishable from success.

**Files affected:** `PlanningView.tsx`, `CanonWorkshop.tsx`, `WritingView.tsx`, `StudioSuggestionsPanel.tsx`, `StudioIdeasPanel.tsx`, and others.

**Recommendation:** For mutations, add `.catch(console.error)` at minimum. For invalidations, the pattern is acceptable (best-effort by design).

---

### M-4: Synthetic Event Cast in StoryImportModal

**File:** `frontend/src/components/projects/StoryImportModal.tsx:567-578`

```typescript
<button onClick={() => {
  setError(null);
  handleSubmit(new Event('submit') as unknown as React.FormEvent);
}}>
```

Double-cast bypasses TypeScript. The event has no `currentTarget`, so form data will be empty on retry.

**Fix:** Separate the retry logic into its own handler rather than synthesizing a form event.

---

### M-5: 69 Inline Styles Where Tailwind Suffices

Scattered across multiple files. Notable offenders:

| File | Lines | Issue |
|------|-------|-------|
| `ProjectList.tsx` | 170, 185, 224, 250, 252, 295, 302, 480 | `style={{ borderColor: 'var(--border-primary)' }}` repeated 8 times |
| `RelationshipMapGraph.tsx` | 321, 387, 405, 416, 451, 459, 469, 479, 509, 531, 534 | SVG context makes Tailwind impractical for some, but `minHeight: 800` (line 321) could be `min-h-[800px]` |
| `ManuscriptList.tsx` | 250 | Hardcodes Tailwind colors (`slate-800`/`slate-200`) instead of CSS variables |
| `StudioFloatingPanel.tsx` | 239, 290, 314, 333, 352, 371, 390, 403 | Dynamic position/size styles are necessary, but `background: 'var(--accent-primary)'` and `#ef4444` could use Tailwind classes |

---

## LOW SEVERITY

### L-1: Empty `__init__` Methods

Multiple services have no-op `__init__` methods:
```python
class AuthorizationService:
    def __init__(self):
        pass
```

**Fix:** Remove empty `__init__` methods entirely. Keep empty exception bodies — they're standard Python convention.

---

### L-2: Duplicate CSS Constants

**File:** `frontend/src/components/studio/StudioFloatingPanel.tsx:226-227`

```typescript
const resizeHandleBase = 'absolute opacity-0 hover:opacity-100 transition-opacity touch-none';
const resizeHandleVertical = 'absolute opacity-0 hover:opacity-100 transition-opacity touch-none';
```

Identical values, different names. The naming suggests they were intended to differ.

---

### L-3: Incomplete Barrel Exports

**File:** `frontend/src/hooks/index.ts`

Only 3 of 30+ hooks are re-exported, giving a misleading impression of available exports.

---

### L-4: Unused Variable Suppression (6 Occurrences)

```typescript
void _systemTick;    // Layout.tsx:27, WritingView.tsx:54
void projectId;      // BibleEntryList.tsx:19
void manuscript;     // DraftPromotion.tsx:37
void loadArtifacts(); // DraftPromotion.tsx:38
```

---

## POSITIVE OBSERVATIONS

1. **Zero `as any` casts and zero `@ts-ignore`** — strict type discipline maintained across the entire codebase.
2. **Consistent shared Axios client** — all services use `frontend/src/lib/api.ts`.
3. **Proper React Query patterns** — `useQuery` with `enabled` guards, `invalidateQueries` after mutations, `staleTime` configuration.
4. **Zustand for UI state** — clean separation between server state (React Query) and UI state (Zustand).
5. **Consolidated form state** in `usePlanningController.ts` correctly avoids React's 50-hook limit.
6. **Error boundaries** properly implemented in `main.tsx` and `ErrorBoundary.tsx`.
7. **Backward-compatible route redirects** — old routes still work for bookmarks via `Navigate` with `replace`.
8. **Polling cleanup** — `useEffect` cleanup functions properly clear intervals.
9. **Exception hierarchy** — domain-specific exceptions follow proper inheritance chains.
10. **`extract_json` utility** (`app/utils/json_extract.py`) is clean, well-documented, and handles 3 strategies with proper fallback.
