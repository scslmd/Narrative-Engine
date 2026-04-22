# PlanningView Refactor Plan

**Date:** 2026-04-21
**Goal:** Refactor 653-line `PlanningView.tsx` into smaller sub-components using callback-based pattern.
**Target architecture:** PlanningView = controller, PlanningTab = composition layer, sub-components = display with callbacks.

## Background

PlanningView.tsx was previously reduced from 1643 lines to 653 lines via a partial refactor that created:
- `usePlanningTab.ts` hook (898 lines) — owns all planning state, queries, mutations, form state
- `PlanningTab.tsx` (467 lines) — renders all sections INLINE, imports 8 sub-components but never uses them
- 8 sub-components in `frontend/src/components/planning/` (~1.1K lines) — callback-based, ready to use
- `ui.tsx` (59 lines) — shared Section, EmptyState, WorkspaceStatus

The partial refactor left stale mutations in PlanningView, unused sub-component imports in PlanningTab, and the sub-components are never wired up.

## Architecture

```
PlanningView.tsx (~370 lines after refactor)
  ├── Manages tab state, character/editor state
  ├── Owns queries/mutations for: brainstorm, foundation, characters, world-bible, relationships
  ├── Calls usePlanningTab(activeTab) hook
  └── Renders <PlanningTab state={...} callbacks={...} /> for planning + arcs tabs

usePlanningTab.ts (~920 lines)
  ├── 12 queries (sequence, chapter, scene, beat, dependencies, packets, cards,
  │    candidates, selections, stageMaps, comparisons)
  ├── 15 mutations (create/update/reorder for each entity)
  ├── ~40 useState form variables
  ├── callbacks object with all form handlers
  └── state object with all data, loading flags, form state

PlanningTab.tsx (~110 lines after refactor)
  ├── Receives state + callbacks from usePlanningTab
  ├── Composes 8 sub-components with mapped props
  └── No inline rendering logic

Sub-components (8 files, ~750 lines total)
  ├── SequencePlanSection.tsx (161) — callback-based, has reorder
  ├── ChapterPlanSection.tsx (169) — callback-based, has reorder
  ├── ScenePlanSection.tsx (167) — callback-based, has reorder
  ├── BeatPlanSection.tsx (133) — callback-based, no reorder
  ├── DependenciesSection.tsx (37) — read-only list
  ├── ChapterPacketsSection.tsx (86) — simple create form
  ├── StoryboardCardsSection.tsx (129) — create form with type select
  └── ArcsTab.tsx (261) — arc candidates, selections, stage maps, comparisons

ui.tsx (~95 lines after refactor)
  ├── Section — section wrapper with title, count, actions, children
  ├── EmptyState — empty state message
  ├── WorkspaceStatus — loading/error status card
  └── getErrorMessage — error message extraction utility
```

## Pre-existing TypeScript Errors (43 total)

| File | Errors | Category |
|------|--------|----------|
| PlanningView.tsx | 33 | Stale planning mutations (12) + unused imports (2) + unused local components (1) + missing function refs (12) |
| usePlanningTab.ts | 1 | `arcStageMaps` undefined at line 830 |
| PlanningTab.tsx | 4 | Unused imports for sub-components never used (inline rendering instead) |
| Sub-components | 10 | Unused params (`onCreateLoading`, `useState`, `smallInputClass`) |

## Plan: 3 Stages, Validate After Each

### Stage 1: Fix `usePlanningTab.ts` (2 changes)

**1.1: Define `arcStageMaps` variable (after line 527)**
```ts
const arcStageMaps = arcStageMapsQuery.data ?? [];
```

**1.2: Accept `activeTab` parameter**
- Change `export function usePlanningTab()` → `export function usePlanningTab(tab: string)`
- Remove internal `const [activeTab] = useState<...>('planning')` (line 223)
- Replace all `activeTab` references in query `enabled` props with the parameter `tab`

### Stage 2: Fix `PlanningView.tsx` (5 changes)

**2.1: Remove stale planning mutation imports**
- `createSequencePlan`, `updateSequencePlan`, `createChapterPlan`, `updateChapterPlan`
- `createScenePlan`, `updateScenePlan`, `createBeatPlan`, `updateBeatPlan`
- `createChapterPacket`, `createStoryboardCard`

**2.2: Remove unused arc visualization imports**
- `ArcComparisonGraph`, `ArcStageMapFlow`

**2.3: Remove stale mutations (lines 243-321)**
All 9 mutations: sequencePlanCreate/Update, chapterPacketCreate, storyboardCardCreate, chapterPlanCreate/Update, scenePlanCreate/Update, beatPlanCreate/Update.

**2.4: Update PlanningTab call to pass `activeTab`**
```tsx
<PlanningTab isDark={isDark} activeTab={activeTab} state={planning.state} callbacks={planning.callbacks} />
```

**2.5: Move local helpers to ui.tsx (NOT `omitKeys`)**
Move to `frontend/src/components/planning/ui.tsx`:
- `Section` (line 595-608)
- `EmptyState` (line 610-615)
- `WorkspaceStatus` (line 617-640)
- `getErrorMessage` (line 642-647)

Keep in PlanningView: `omitKeys` (utility function, not UI component).

Import in PlanningView:
```tsx
import { Section, EmptyState, WorkspaceStatus, getErrorMessage } from '../components/planning/ui';
```

### Stage 3: Wire sub-components into `PlanningTab.tsx` (5 changes)

**3.1: Add `openEdit*` callbacks to `PlanningTabCallbacks` in `usePlanningTab.ts`**

Add to interface:
```ts
openEditSequence: (plan: SequencePlan) => void;
openEditChapter: (plan: ChapterPlan) => void;
openEditScene: (plan: ScenePlan) => void;
openEditBeat: (plan: BeatPlan) => void;
```

Implement in callbacks object:
```ts
openEditSequence: (plan) => {
  setSequenceEditOpenId(plan.sequence_id);
  setSequenceEditTitle(plan.title);
  setSequenceEditSummary(plan.summary || '');
},
openEditChapter: (plan) => {
  setChapterEditOpenId(plan.chapter_id);
  setChapterEditTitle(plan.title);
  setChapterEditObjective(plan.objective);
  setChapterEditConflict(plan.conflict || '');
  setChapterEditStakes(plan.stakes || '');
},
openEditScene: (plan) => {
  setSceneEditOpenId(plan.scene_id);
  setSceneEditTitle(plan.title);
  setSceneEditObjective(plan.objective);
  setSceneEditConflict(plan.conflict || '');
  setSceneEditStakes(plan.stakes || '');
},
openEditBeat: (plan) => {
  setBeatEditOpenId(plan.beat_id);
  setBeatEditObjective(plan.objective);
  setBeatEditConflict(plan.conflict || '');
  setBeatEditStakes(plan.stakes || '');
  setBeatEditArcStage(plan.arc_stage || '');
},
```

**3.2: Remove unused props from sub-component interfaces**

Delete `onCreateLoading` and `onUpdateLoading` from all 8 sub-component interfaces.
Remove corresponding destructured parameters and unused variable declarations from all component bodies.
For ChapterPlanSection: also remove `smallInputClass` (unused).
For SequencePlanSection and ChapterPlanSection: remove unused `useState` import.

**3.3: Remove PlanningTab local definitions**
- Remove `Section`, `EmptyState`, `WorkspaceStatus` definitions (lines 407-465)
- Remove `import { ChevronUp, ChevronDown }` at line 467 (used only by inline rendering)

**3.4: Replace inline rendering with sub-components**

Replace inline section rendering (lines 28-321) with sub-component calls, passing state and callback props. Each sub-component receives:
- Data props from `state.*` (plans, isLoading, form state)
- Callback props from `callbacks.*` (setters, submit handlers, reordering)
- Derived props for button disabled states

Reorder callbacks use wrapper pattern:
```tsx
onReorderUp={(index) => callbacks.sequenceReorder('up', index)}
onReorderDown={(index) => callbacks.sequenceReorder('down', index)}
```

**3.5: Update `PlanningTabProps` interface**
```ts
export interface PlanningTabProps {
  isDark: boolean;
  activeTab: string;
  state: PlanningTabState;
  callbacks: PlanningTabCallbacks;
}
```

## Expected Results

### Line counts

| File | Before | After | Change |
|------|--------|-------|--------|
| PlanningView.tsx | 653 | ~370 | -283 |
| usePlanningTab.ts | 898 | ~920 | +22 |
| PlanningTab.tsx | 467 | ~110 | -357 |
| ui.tsx | 59 | ~95 | +36 |
| Sub-components (6 files) | ~850 | ~750 | -100 |

### Architecture improvement

- PlanningView drops 43% in size — manages routing/editor state, delegates planning to hook
- PlanningTab drops 76% in size — simple composition layer, no inline rendering
- Each sub-component is independently readable and testable
- Sub-components receive only callback functions (not raw React Query mutations)
- PlanningView remains the "controller" layer per AGENTS.md convention

## Known Debt (Not Addressed)

- `isDark` prop drilling through PlanningView → PlanningTab → sub-components — should migrate to React Context theme store
- `Section`/`EmptyState`/`WorkspaceStatus` call `document.documentElement.getAttribute('data-theme')` on every render — should use context
- `omitKeys` uses `as Partial<T>` cast — functional but type-unsafe

## Validation

After each stage, run:
```
cd frontend; npx tsc --noEmit
```

Only proceed when typecheck passes.

Full validation after all stages:
```
python -m pytest -q -p no:cacheprovider
cd frontend; npx tsc --noEmit
cd frontend; npm run lint
cd frontend; npm run build
```
