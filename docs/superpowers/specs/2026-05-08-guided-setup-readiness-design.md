# Guided Setup Readiness Detection — Design Spec

**Date:** 2026-05-08
**Status:** Approved

## Problem

The Story Architect (`/setup-wizard`) collects project data through conversational Q&A. The LLM already tracks per-category completeness and returns a `ready_to_create` signal when all five core categories (config, foundation, characters, world_bible, arcs) reach ≥ 0.7 completeness. But this signal is invisible to the user — the "Create Project" button appears based on arbitrary content thresholds (`hasContent`), not the LLM's readiness assessment. The user has no way to know when the system believes they have enough information to proceed.

## Goal

Surface the LLM's `ready_to_create` determination as a prominent visual state, and give the user a clear "Save Project" action when ready — while still allowing partial saves for early exit.

## Architecture

No backend changes. The existing `GuidedSetupService.analyze_turn()` already returns:
- `ready_to_create: bool` — true when all 5 core categories ≥ 0.7 and sequences/chapters are present
- `category_progress: list[CategoryProgress]` — per-category completeness, confidence, collected/missing fields
- `progress: float` — overall 0–100 progress

Changes are entirely frontend: 4 files across components, view, and store.

## Design

### 1. Chat Header Readiness Indicator

**File:** `ChatPanel.tsx`

Accept a `readyToCreate` prop (derived from store). When true:
- Chat panel header gets a green border pulse animation (CSS keyframe, single fire via state flag)
- Progress bar gradient shifts from violet→purple to emerald→teal
- "% complete" label replaced by "Ready to Save" badge with checkmark icon
- Badge uses `bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400` styling

When not ready but progress > 0:
- Show category readiness count: "3/5 categories ready" (computed from `categoryProgress` where completeness ≥ 0.7)
- Progress bar stays violet gradient

### 2. Dual-State Action Button

**File:** `GuidedSetupView.tsx`

Replace single `hasContent` button with two states:

| Condition | Label | Icon | Style |
|-----------|-------|------|-------|
| `readyToCreate && hasContent` | "Save Project" | Check | Primary gradient (violet→purple), shadow-md |
| `!readyToCreate && hasContent` | "Save What You Have" | Save | Secondary (outline), muted text |

Both states call the same `handleSubmitCreate()` mutation. The visual distinction communicates confidence, not capability.

### 3. Per-Category Completeness in FieldPreview

**File:** `FieldPreview.tsx`

Each collapsible section header gains:
- Mini completeness bar (width proportional to `completeness * 100%`)
- Color: green if ≥ 0.7, amber if 0.3–0.7, gray if < 0.3
- When category has missing fields and completeness < 0.7: inline tags showing missing field names

Map categories to sections: config → "Project Config", foundation → "Foundation", characters → "Characters", world_bible → "World", arcs → "Arcs". Sequences and chapters sections don't have category_progress entries, so they show no bar.

New prop: `categoryProgress: CategoryProgress[]` passed from store to FieldPreview.

### 4. Readiness Achievement Notification

**File:** `guidedSetupStore.ts`

Track `wasReadyBefore: boolean` (default false). In `handleAnalyze`, after receiving the LLM response:
- If `response.ready_to_create === true && wasReadyBefore === false`:
  - Inject a system message: "I think we have enough to create your project. You can review the fields on the right and save whenever you're ready."
  - Set `wasReadyBefore = true`

This fires only once per session, on the turn where readiness flips from false to true.

## Data Flow

```
User answer → handleAnalyze() → analyzeTurn API → LLM response
  → setProgress(progress, confidence, ready_to_create, category_progress)
  → if readyToCreate flipped: inject system message
  → ChatPanel re-renders with readiness indicator
  → FieldPreview re-renders with completeness bars
  → GuidedSetupView button switches to "Save Project" state
```

## Component Prop Changes

| Component | New Props | Source |
|-----------|-----------|--------|
| `ChatPanel` | `readyToCreate: boolean`, `categoryProgress: CategoryProgress[]` | store |
| `FieldPreview` | `categoryProgress: CategoryProgress[]` | store |
| `GuidedSetupView` | No new props — reads `readyToCreate` from hook/store | store |

## Edge Cases

- **LLM unavailable**: User can still fill fields manually and click "Save What You Have". The readiness indicator stays hidden (no category progress available).
- **Ready flips back to false**: If the user edits fields downward (unlikely but possible), `readyToCreate` reflects current state. The "Save Project" button reverts to "Save What You Have". No re-notification.
- **Empty categoryProgress**: Before any LLM analysis, `categoryProgress` is empty. Category count shows "0/5" and completeness bars are hidden.

## Testing

- Unit test: `setProgress` correctly sets `readyToCreate` and `wasReadyBefore` flags
- Unit test: readiness notification fires exactly once when flipping false → true
- Integration: verify button label/icon/style transitions at ready boundary
- Integration: verify category completeness bars render correct colors for threshold values

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/guided-setup/ChatPanel.tsx` | Readiness badge, progress bar color, category count |
| `frontend/src/views/GuidedSetupView.tsx` | Dual-state button, readiness header styling |
| `frontend/src/components/guided-setup/FieldPreview.tsx` | Per-category completeness bars, missing field tags |
| `frontend/src/stores/guidedSetupStore.ts` | `wasReadyBefore` tracking, readiness notification injection |

## Out of Scope

- Backend changes to readiness thresholds (existing 0.7 per-category is the contract)
- Mobile-specific layout for readiness indicator
- Persistence of guided setup session across page reloads
