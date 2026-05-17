# Studio Desk Stage 3 Compact Panels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace route-sized Generation, Review, and Inspect views inside Studio with compact panel components that fit the right context rail.

**Architecture:** Keep existing full views and routes unchanged. Extract or compose smaller panel components that reuse existing controllers and present the same existing data/actions in a narrower layout.

**Tech Stack:** React 18, TypeScript, existing domain controllers, existing review/inspect/generation components, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S3-T001 | `frontend/src/components/studio/StudioGenerationPanel.tsx` | Compact generation panel |
| S3-T002 | `frontend/src/components/studio/StudioReviewPanel.tsx` | Compact review panel |
| S3-T003 | `frontend/src/components/studio/StudioInspectPanel.tsx` | Compact inspect panel |
| S3-T004 | `frontend/src/components/studio/StudioContextPanel.tsx` | Swap route views for compact panels |
| S3-T005 | `frontend/src/views/StudioView.test.tsx` | Update assertions |

## Guardrails

- Do not edit backend or services.
- Do not remove `GenerationView`, `ReviewView`, or `InspectView`.
- Do not change full route behavior.
- Do not add new generation modes or review object types.

## Tasks

### S3-T001: StudioGenerationPanel

**Responsible file:** `frontend/src/components/studio/StudioGenerationPanel.tsx`

- [ ] Create a component with this exact public contract:

```tsx
interface StudioGenerationPanelProps {
  projectId: string;
}

export function StudioGenerationPanel({ projectId }: StudioGenerationPanelProps) {
  // implementation
}
```

- [ ] Use existing `useGenerationController(projectId)`.
- [ ] Render a header with exact text `Generation`.
- [ ] Render existing `StoryGenerationWizard` with:
  - `projectId={projectId}`
  - `characters={characters}`
  - `worldEntries={worldEntries}`
  - `onPreview={previewForkRun}`
  - `onSubmit={submitGenerationRun}`
  - `onSubmitted={handleRunSubmitted}`
- [ ] Render `ErrorBanner error={runsError} onRetry={retryRuns}`.
- [ ] Render at most the first five runs from `runs.slice(0, 5)`.
- [ ] Each run must render existing `GenerationRunCard` and call `handleRunSelected(run)` when clicked.
- [ ] Render existing `GenerationGatePanel` with `gates={gates}`.
- [ ] If `selectedRun` is non-null, render exact text `Latest status:` and a button that calls `handleForkSelectedRun`.
- [ ] Do not render `GeneratedStoryReview` in the compact panel; full generated story review remains available in `/generate`.
- [ ] Do not call `useParams`; the parent passes `projectId`.

### S3-T002: StudioReviewPanel

**Responsible file:** `frontend/src/components/studio/StudioReviewPanel.tsx`

- [ ] Create a component with this exact public contract:

```tsx
interface StudioReviewPanelProps {
  projectId: string;
}

export function StudioReviewPanel({ projectId }: StudioReviewPanelProps) {
  // implementation
}
```

- [ ] Use existing `FindingsList` and `InspectRunLinksList`.
- [ ] Use local tab state initialized to `'findings'`.
- [ ] Render two buttons with exact labels `Findings` and `Inspect Links`.
- [ ] When active tab is `findings`, render `<FindingsList projectId={projectId} />`.
- [ ] When active tab is `links`, render `<InspectRunLinksList projectId={projectId} />`.
- [ ] Do not include the inspect-link create form in the compact panel; full authoring remains available in `/review`.
- [ ] Do not call `useParams`; the parent passes `projectId`.

### S3-T003: StudioInspectPanel

**Responsible file:** `frontend/src/components/studio/StudioInspectPanel.tsx`

- [ ] Create a component with this exact public contract:

```tsx
export function StudioInspectPanel() {
  // implementation
}
```

- [ ] Render exact guidance text `Open a run from Review or the job tray to inspect steps, lineage, and attempts.`
- [ ] Render existing `InspectMode` below that guidance text.
- [ ] Because the Studio route has no `:jobId`, this compact panel is allowed to show InspectMode's empty/default state until the user navigates to a concrete inspect route from Review or the job tray. Do not invent a new job-selection mechanism in this stage.
- [ ] Do not change `InspectMode`.

### S3-T004: Swap Context Panel Renderers

**Responsible file:** `frontend/src/components/studio/StudioContextPanel.tsx`

- [ ] Replace `GenerationView` import with `StudioGenerationPanel`.
- [ ] Replace `ReviewView` import with `StudioReviewPanel`.
- [ ] Replace `InspectView` import with `StudioInspectPanel`.
- [ ] Render compact panels exactly as:

```tsx
generation: <StudioGenerationPanel projectId={projectId} />
review: <StudioReviewPanel projectId={projectId} />
inspect: <StudioInspectPanel />
```

### S3-T005: Update StudioView Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

- [ ] Update generation panel assertion to target compact panel text.
- [ ] Add assertion that clicking `Review` shows `Findings`.
- [ ] Add assertion that clicking `Inspect` shows the compact inspect guidance text. Do not assert that run details appear inside Studio.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all exit 0.

## Stage 3 Pass Criteria

Stage 3 is complete only when all of these are true:

- Studio uses `StudioGenerationPanel`, `StudioReviewPanel`, and `StudioInspectPanel` in the context rail.
- Studio no longer imports route-sized `GenerationView`, `ReviewView`, or `InspectView` in `StudioContextPanel`.
- `/workspace/:projectId/generate`, `/review`, and `/inspect` still render their original full views.
- Compact panels use existing controllers/components only.
- No new backend behavior or frontend service contract is introduced.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- GenerationView
```

Do not proceed to Stage 4 until these pass and the final verification commands above exit 0.
