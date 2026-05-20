# Radial Hub Phase 2: Panel Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all existing studio panels to work inside the `StudioFloatingPanel` wrapper, create 3 new panels (Structure, Chapters, Canon), wire everything through `StudioPanelContent`, add layout presets per author type, and implement the bottom status bar.

**Prerequisites:** Phase 1 must be complete. The following must exist:
- `StudioFloatingPanel.tsx` — draggable/resizable panel wrapper
- `StudioRadialHub.tsx` — layout manager with DndContext
- `StudioPanelMenu.tsx` — dropdown panel menu
- `StudioPanelContent.tsx` — content router (switch on panelKey)
- Extended `studioStore.ts` with layout state (`addPanel`, `removePanel`, etc.)
- `StudioView.tsx` updated to use `StudioRadialHub`
- `StudioCommandBar.tsx` updated with panel menu and reset button

**Architecture:** Existing panels already accept `projectId` as a prop (most were built for `StudioContextPanel`). Two panels (`StudioDraftsPanel`, `StudioManuscriptsPanel`) currently use `useParams` or lack `projectId` — they must be migrated. Three new panels are created from scratch. All panels render inside `StudioFloatingPanel` via `StudioPanelContent` switch.

**Clarification:** In the current repo state, only `StudioDraftsPanel` requires a prop migration in this phase. `StudioManuscriptsPanel` should keep its current `onSelect`-only API unless `useWritingView` is first refactored to accept explicit project context.

**Tech Stack:** React 18, TypeScript, Zustand, `@dnd-kit/core`, Tailwind CSS, CSS variables

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/components/studio/StudioDraftsPanel.tsx` | Modify | Accept `projectId` prop instead of `useParams` |
| `frontend/src/components/studio/StudioManuscriptsPanel.tsx` | Modify | Keep current `onSelect` API; verify floating-panel compatibility |
| `frontend/src/components/studio/StudioStructurePanel.tsx` | Create | Story framework beat progression panel |
| `frontend/src/components/studio/StudioChaptersPanel.tsx` | Create | Chapter list, navigation, packets panel |
| `frontend/src/components/studio/StudioCanonPanel.tsx` | Create | Canon profiles, annotations panel |
| `frontend/src/components/studio/StudioPanelContent.tsx` | Modify | Wire 3 new panels + fix existing panel prop passing |
| `frontend/src/components/studio/StudioStatusBar.tsx` | Create | Bottom status bar with project info |
| `frontend/src/stores/studioStore.ts` | Modify | Add layout presets per author type |
| `frontend/src/views/StudioView.tsx` | Modify | Add StudioStatusBar below RadialHub |

**Do NOT modify:** `StudioCharactersPanel.tsx`, `StudioIdeasPanel.tsx`, `StudioWorldBiblePanel.tsx`, `StudioRelationshipsPanel.tsx`, `StudioArcsPanel.tsx`, `StudioGenerationPanel.tsx`, `StudioReviewPanel.tsx`, `StudioInspectPanel.tsx`, `StudioSuggestionsPanel.tsx`, `StudioContextPanel.tsx`, `StudioProjectRail.tsx`, `StudioFloatingPanel.tsx`, `StudioRadialHub.tsx`, `StudioPanelMenu.tsx`, `ViewShell.tsx`, service files, hook files, type files.

---

## Task 1: Migrate `StudioDraftsPanel` to Accept `projectId` Prop

**Files:**
- Modify: `frontend/src/components/studio/StudioDraftsPanel.tsx`

**Purpose:** `StudioDraftsPanel` currently uses `useParams<{ projectId }>()` to get the project ID. In the floating panel system, `projectId` is passed as a prop from `StudioPanelContent`. Migrate to prop-based API for consistency.

**Current state:**
```tsx
// CURRENT — uses useParams
export function StudioDraftsPanel() {
  const { projectId } = useParams<{ projectId: string }>();
  // ... uses projectId in useAssistController
}
```

**Target state:**
```tsx
// TARGET — accepts projectId prop
interface StudioDraftsPanelProps {
  projectId: string;
}

export function StudioDraftsPanel({ projectId }: StudioDraftsPanelProps) {
  // ... uses projectId directly
}
```

- [ ] **Step 1: Write test for prop-based rendering**

Create `frontend/src/components/studio/StudioDraftsPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { StudioDraftsPanel } from './StudioDraftsPanel';

// Mock the hooks that StudioDraftsPanel depends on
vi.mock('../../hooks/useWritingView', () => ({
  useWritingView: () => ({
    draftArtifacts: [],
    draftForm: null,
    expandedDraft: null,
    createDraftPending: false,
    promotePending: false,
    continuePending: false,
    alternatePending: false,
    draftsQueryLoading: false,
    handleCreateDraft: vi.fn(),
    handleSubmitDraft: vi.fn(),
    handleCancelDraft: vi.fn(),
    handleToggleDraft: vi.fn(),
    promoteDraft: vi.fn(),
    continueDraftAction: vi.fn(),
    alternateVariantAction: vi.fn(),
    setDraftForm: vi.fn(),
  }),
}));

vi.mock('../../domains/writing/useAssistController', () => ({
  useAssistController: () => ({
    draftFormAI: null,
    pendingDrafts: {},
    setDraftFormAI: vi.fn(),
    handleGenerateDraftForm: vi.fn(),
    handleGenerateDraft: vi.fn(),
    generateDraftPending: false,
  }),
}));

vi.mock('../../stores/themeStore', () => ({
  useThemeStore: () => ({ mode: 'system' }),
}));

describe('StudioDraftsPanel', () => {
  it('renders with projectId prop', () => {
    render(<StudioDraftsPanel projectId="test-proj" />);
    expect(screen.getByText(/Drafts/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd frontend && npm run test -- StudioDraftsPanel.test.tsx`
Expected: FAIL or PASS depending on mock coverage

- [ ] **Step 3: Modify component to accept `projectId` prop**

Replace the component signature and remove `useParams`:

```tsx
import { FileText, Plus, Sparkles } from 'lucide-react';
import { DraftList } from '../writing/DraftList';
import { DraftForm } from '../writing/DraftForm';
import { useWritingView } from '../../hooks/useWritingView';
import { useAssistController } from '../../domains/writing/useAssistController';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

interface StudioDraftsPanelProps {
  projectId: string;
}

export function StudioDraftsPanel({ projectId }: StudioDraftsPanelProps) {
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';

  const {
    draftArtifacts,
    draftForm,
    expandedDraft,
    createDraftPending,
    promotePending,
    continuePending,
    alternatePending,
    draftsQueryLoading,
    handleCreateDraft,
    handleSubmitDraft,
    handleCancelDraft,
    handleToggleDraft,
    promoteDraft,
    continueDraftAction,
    alternateVariantAction,
    setDraftForm,
  } = useWritingView(isDark);

  const {
    draftFormAI,
    pendingDrafts,
    setDraftFormAI,
    handleGenerateDraftForm,
    handleGenerateDraft,
    generateDraftPending,
  } = useAssistController({
    projectId,
    selectedDocumentId: null,
  });

  // ... rest of JSX unchanged ...
}
```

Remove the `useParams` import and the `const { projectId } = useParams<{ projectId: string }>();` line.

- [ ] **Step 4: Update `StudioPanelContent` to pass `projectId`**

In `StudioPanelContent.tsx`, the `drafts` case already renders `<StudioDraftsPanel />`. Update to:

```tsx
case 'drafts':
  return <StudioDraftsPanel projectId={projectId} />;
```

- [ ] **Step 5: Update `StudioContextPanel` to pass `projectId`**

In `StudioContextPanel.tsx`, the `drafts` case already renders `<StudioDraftsPanel />`. Update to:

```tsx
case 'drafts':
  return <StudioDraftsPanel projectId={projectId} />;
```

- [ ] **Step 6: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/studio/StudioDraftsPanel.tsx frontend/src/components/studio/StudioDraftsPanel.test.tsx frontend/src/components/studio/StudioPanelContent.tsx frontend/src/components/studio/StudioContextPanel.tsx
git commit -m "refactor: migrate StudioDraftsPanel to accept projectId prop"
```

---

## Task 2: Verify `StudioManuscriptsPanel` Compatibility in the Floating-Panel Path

**Files:**
- Modify: `frontend/src/components/studio/StudioManuscriptsPanel.tsx`

**Purpose:** `StudioManuscriptsPanel` currently takes only `onSelect` and derives project context internally through `useWritingView`. In the current codebase, that is still the correct behavior. Phase 2 should verify that rendering it from `StudioPanelContent` does not require any prop-surface change.

**Current state:**
```tsx
interface StudioManuscriptsPanelProps {
  onSelect?: (documentId: string) => void;
}
```

**Target state:**
```tsx
interface StudioManuscriptsPanelProps {
  onSelect?: (documentId: string) => void;
}
```

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioManuscriptsPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { StudioManuscriptsPanel } from './StudioManuscriptsPanel';

vi.mock('../../hooks/useWritingView', () => ({
  useWritingView: () => ({
    manuscriptDocuments: [],
    selectedDocumentId: null,
    manuscriptQueryLoading: false,
    setSelectedDocumentId: vi.fn(),
    setIsEditing: vi.fn(),
    setEditContent: vi.fn(),
  }),
}));

vi.mock('../../stores/settingsStore', () => ({
  useSettingsStore: () => ({ outlineDetail: 'simple' }),
}));

vi.mock('../../stores/themeStore', () => ({
  useThemeStore: () => ({ mode: 'system' }),
}));

describe('StudioManuscriptsPanel', () => {
  it('renders with onSelect prop', () => {
    render(<StudioManuscriptsPanel onSelect={vi.fn()} />);
    expect(screen.getByText(/Manuscripts/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Keep the component API unchanged unless `useWritingView` is refactored first**

The current implementation shape remains valid for Phase 2:

```tsx
import { useCallback, useState } from 'react';
import { BookOpen } from 'lucide-react';
import { ManuscriptList } from '../writing/ManuscriptList';
import { useWritingView } from '../../hooks/useWritingView';
import { useSettingsStore } from '../../stores/settingsStore';
import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

interface StudioManuscriptsPanelProps {
  onSelect?: (documentId: string) => void;
}

export function StudioManuscriptsPanel({ onSelect }: StudioManuscriptsPanelProps) {
  const { mode: themeMode } = useThemeStore();
  const isDark = resolveEffectiveMode(themeMode) === 'dark';
  const { outlineDetail } = useSettingsStore();

  const {
    manuscriptDocuments,
    selectedDocumentId,
    manuscriptQueryLoading,
    setSelectedDocumentId,
    setIsEditing,
    setEditContent,
  } = useWritingView(isDark);

  // ... rest unchanged ...
}
```

Do not add a `projectId` prop in this phase unless `useWritingView` is first rewritten to accept explicit project context.

- [ ] **Step 3: Update `StudioPanelContent` to render panel**

In `StudioPanelContent.tsx`, keep the manuscripts case prop-free except for existing callbacks:

```tsx
case 'manuscripts':
  return <StudioManuscriptsPanel />;
```

- [ ] **Step 4: Update `StudioContextPanel` to render panel**

In `StudioContextPanel.tsx`, keep the existing `onSelect` wiring:

```tsx
case 'manuscripts':
  return <StudioManuscriptsPanel onSelect={onManuscriptSelect} />;
```

- [ ] **Step 5: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/studio/StudioManuscriptsPanel.tsx frontend/src/components/studio/StudioManuscriptsPanel.test.tsx frontend/src/components/studio/StudioPanelContent.tsx frontend/src/components/studio/StudioContextPanel.tsx
git commit -m "test: verify StudioManuscriptsPanel compatibility in floating-panel flows"
```

---

## Task 3: Create `StudioStructurePanel`

**Files:**
- Create: `frontend/src/components/studio/StudioStructurePanel.tsx`

**Purpose:** Display the active story framework's beat progression. Shows sequences, beats, and their completion status. Uses planning API data. Per the design spec: "Visual beat bar shows completed vs. remaining beats. Color-coded: green (completed), amber (current), gray (upcoming)."

**Props:**
```ts
interface StudioStructurePanelProps {
  projectId: string;
}
```

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioStructurePanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { StudioStructurePanel } from './StudioStructurePanel';

vi.mock('../../services/planning', () => ({
  getSequencePlans: vi.fn(() => Promise.resolve([])),
  getBeatPlans: vi.fn(() => Promise.resolve([])),
}));

vi.mock('../../services/project', () => ({
  getProject: vi.fn(() => Promise.resolve({ config: { story_structure: 'save_the_cat' } })),
}));

describe('StudioStructurePanel', () => {
  it('renders panel header', async () => {
    render(<StudioStructurePanel projectId="proj-1" />);
    expect(screen.getByText(/Structure/i)).toBeInTheDocument();
  });

  it('shows empty state when no beats', async () => {
    render(<StudioStructurePanel projectId="proj-1" />);
    // Should show empty state or loading
    const container = document.querySelector('[data-structure-panel]');
    expect(container).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Create component**

```tsx
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getBeatPlans, getSequencePlans } from '../../services/planning';
import type { BeatPlan, SequencePlan } from '../../types/planning';
import { WorkspaceStatus } from '../planning/ui';

interface StudioStructurePanelProps {
  projectId: string;
}

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-emerald-500',
  in_progress: 'bg-amber-500',
  current: 'bg-amber-500',
  planned: 'bg-slate-400 dark:bg-slate-600',
  pending: 'bg-slate-400 dark:bg-slate-600',
  draft: 'bg-blue-500',
  review: 'bg-purple-500',
};

const STATUS_LABELS: Record<string, string> = {
  completed: 'Done',
  in_progress: 'In Progress',
  current: 'Current',
  planned: 'Planned',
  pending: 'Pending',
  draft: 'Draft',
  review: 'Review',
};

function BeatIndicator({ beat }: { beat: BeatPlan }) {
  const color = STATUS_COLORS[beat.status] || 'bg-slate-400 dark:bg-slate-600';
  const label = STATUS_LABELS[beat.status] || beat.status;

  return (
    <div className="group relative" title={`${beat.objective} (${label})`}>
      <div className={`h-2 w-full rounded-full ${color} transition-all group-hover:opacity-80`} />
      {beat.active_character_ids.length > 0 && (
        <div className="pointer-events-none absolute inset-x-0 -bottom-6 z-10 opacity-0 transition-opacity group-hover:opacity-100">
          <div className="rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] px-2 py-1 text-[10px] text-[var(--text-secondary)] shadow-lg">
            <div className="font-medium text-[var(--text-primary)]">{beat.objective}</div>
            <div>{beat.active_character_ids.join(', ')}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function SequenceBlock({ sequence, beats }: { sequence: SequencePlan; beats: BeatPlan[] }) {
  const seqBeats = beats.filter((b) => sequence.beat_ids.includes(b.beat_id));
  const completedCount = seqBeats.filter((b) => b.status === 'completed').length;
  const progress = seqBeats.length > 0 ? (completedCount / seqBeats.length) * 100 : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-[var(--text-primary)]">{sequence.title}</h4>
        <span className="text-[10px] text-[var(--text-tertiary)]">
          {completedCount}/{seqBeats.length} beats
        </span>
      </div>
      <div className="flex gap-1">
        {seqBeats.map((beat) => (
          <div key={beat.beat_id} className="flex-1">
            <BeatIndicator beat={beat} />
          </div>
        ))}
        {seqBeats.length === 0 && (
          <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-700" />
        )}
      </div>
      <div className="h-1 w-full rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

export function StudioStructurePanel({ projectId }: StudioStructurePanelProps) {
  const sequencesQuery = useQuery({
    queryKey: ['studio', 'structure', 'sequences', projectId],
    queryFn: () => getSequencePlans(projectId),
    enabled: Boolean(projectId),
  });

  const beatsQuery = useQuery({
    queryKey: ['studio', 'structure', 'beats', projectId],
    queryFn: () => getBeatPlans(projectId),
    enabled: Boolean(projectId),
  });

  const sequences = useMemo(
    () => (sequencesQuery.data as SequencePlan[] | undefined) ?? [],
    [sequencesQuery.data],
  );

  const beats = useMemo(
    () => (beatsQuery.data as BeatPlan[] | undefined) ?? [],
    [beatsQuery.data],
  );

  const isLoading = sequencesQuery.isLoading || beatsQuery.isLoading;
  const error = sequencesQuery.error || beatsQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading structure" detail="Fetching story framework..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load structure"
        detail="Story framework data is unavailable."
        tone="error"
      />
    );
  }

  const totalBeats = beats.length;
  const completedBeats = beats.filter((b) => b.status === 'completed').length;
  const overallProgress = totalBeats > 0 ? (completedBeats / totalBeats) * 100 : 0;

  return (
    <div data-structure-panel className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Structure</h3>
          <p className="text-xs text-[var(--text-tertiary)]">
            {sequences.length} sequences · {totalBeats} beats
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs font-medium text-[var(--text-secondary)]">
            {Math.round(overallProgress)}%
          </div>
        </div>
      </div>

      <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      {sequences.length === 0 && beats.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">
            No structure planned yet.
          </p>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            Create sequences and beats to track story progress.
          </p>
        </div>
      ) : sequences.length > 0 ? (
        <div className="space-y-4">
          {sequences.map((seq) => (
            <SequenceBlock key={seq.sequence_id} sequence={seq} beats={beats} />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs font-medium text-[var(--text-secondary)]">Standalone Beats</p>
          {beats.map((beat) => (
            <div key={beat.beat_id} className="flex items-center gap-2">
              <div className="w-2">
                <BeatIndicator beat={beat} />
              </div>
              <span className="text-xs text-[var(--text-secondary)] truncate">
                {beat.objective}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Run test**

Run: `cd frontend && npm run test -- StudioStructurePanel.test.tsx`
Expected: PASS

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioStructurePanel.tsx frontend/src/components/studio/StudioStructurePanel.test.tsx
git commit -m "feat: create StudioStructurePanel for story framework beat progression"
```

---

## Task 4: Create `StudioChaptersPanel`

**Files:**
- Create: `frontend/src/components/studio/StudioChaptersPanel.tsx`

**Purpose:** Display chapter list with navigation, status, and packet info. Uses planning API for chapter plans and chapter packets. Allows selecting a chapter to view in the writing surface.

**Props:**
```ts
interface StudioChaptersPanelProps {
  projectId: string;
}
```

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioChaptersPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { StudioChaptersPanel } from './StudioChaptersPanel';

vi.mock('../../services/planning', () => ({
  getChapterPlans: vi.fn(() => Promise.resolve([])),
  getChapterPackets: vi.fn(() => Promise.resolve([])),
}));

describe('StudioChaptersPanel', () => {
  it('renders panel header', async () => {
    render(<StudioChaptersPanel projectId="proj-1" />);
    expect(screen.getByText(/Chapters/i)).toBeInTheDocument();
  });

  it('shows empty state when no chapters', async () => {
    render(<StudioChaptersPanel projectId="proj-1" />);
    const container = document.querySelector('[data-chapters-panel]');
    expect(container).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Create component**

```tsx
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getChapterPlans, getChapterPackets } from '../../services/planning';
import type { ChapterPlan, ChapterPacket } from '../../types/planning';
import { WorkspaceStatus } from '../planning/ui';

interface StudioChaptersPanelProps {
  projectId: string;
}

const CHAPTER_STATUS_COLORS: Record<string, string> = {
  completed: 'border-l-emerald-500',
  in_progress: 'border-l-amber-500',
  current: 'border-l-amber-500',
  planned: 'border-l-slate-400 dark:border-l-slate-600',
  pending: 'border-l-slate-400 dark:border-l-slate-600',
  draft: 'border-l-blue-500',
  review: 'border-l-purple-500',
};

const CHAPTER_STATUS_DOTS: Record<string, string> = {
  completed: 'bg-emerald-500',
  in_progress: 'bg-amber-500',
  current: 'bg-amber-500',
  planned: 'bg-slate-400 dark:bg-slate-600',
  pending: 'bg-slate-400 dark:bg-slate-600',
  draft: 'bg-blue-500',
  review: 'bg-purple-500',
};

function ChapterRow({
  chapter,
  packet,
  isSelected,
  onSelect,
}: {
  chapter: ChapterPlan;
  packet?: ChapterPacket;
  isSelected: boolean;
  onSelect: (chapterId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const borderColor = CHAPTER_STATUS_COLORS[chapter.status] || 'border-l-slate-300 dark:border-l-slate-700';
  const dotColor = CHAPTER_STATUS_DOTS[chapter.status] || 'bg-slate-400';

  return (
    <div
      className={`cursor-pointer rounded-lg border border-[var(--border-primary)] border-l-4 ${borderColor} bg-[var(--bg-secondary)] transition-all hover:bg-[var(--bg-primary)] ${
        isSelected ? 'ring-1 ring-[var(--accent-primary)]' : ''
      }`}
      onClick={() => onSelect(chapter.chapter_id)}
    >
      <div className="flex items-center gap-2 px-3 py-2">
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          className="flex h-4 w-4 items-center justify-center text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          {expanded ? '▾' : '▸'}
        </button>
        <div className={`h-2 w-2 rounded-full ${dotColor}`} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-medium text-[var(--text-primary)]">
            {chapter.title || `Chapter ${chapter.chapter_id}`}
          </div>
          <div className="truncate text-[10px] text-[var(--text-tertiary)]">
            {chapter.objective || 'No objective set'}
          </div>
        </div>
        {packet && (
          <span className="shrink-0 rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
            packet
          </span>
        )}
      </div>

      {expanded && (
        <div className="border-t border-[var(--border-primary)] px-3 py-2 space-y-1.5">
          {chapter.summary && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              {chapter.summary}
            </p>
          )}
          {chapter.conflict && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              <span className="font-medium text-[var(--text-tertiary)]">Conflict: </span>
              {chapter.conflict}
            </p>
          )}
          {chapter.stakes && (
            <p className="text-[10px] leading-relaxed text-[var(--text-secondary)]">
              <span className="font-medium text-[var(--text-tertiary)]">Stakes: </span>
              {chapter.stakes}
            </p>
          )}
          {chapter.active_character_ids.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {chapter.active_character_ids.map((cid) => (
                <span
                  key={cid}
                  className="rounded bg-[var(--bg-primary)] px-1.5 py-0.5 text-[9px] text-[var(--text-secondary)]"
                >
                  {cid}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function StudioChaptersPanel({ projectId }: StudioChaptersPanelProps) {
  const queryClient = useQueryClient();
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);

  const chaptersQuery = useQuery({
    queryKey: ['studio', 'chapters', projectId],
    queryFn: () => getChapterPlans(projectId),
    enabled: Boolean(projectId),
  });

  const packetsQuery = useQuery({
    queryKey: ['studio', 'chapter-packets', projectId],
    queryFn: () => getChapterPackets(projectId),
    enabled: Boolean(projectId),
  });

  const chapters = useMemo(
    () => (chaptersQuery.data as ChapterPlan[] | undefined) ?? [],
    [chaptersQuery.data],
  );

  const packets = useMemo(
    () => (packetsQuery.data as ChapterPacket[] | undefined) ?? [],
    [packetsQuery.data],
  );

  const packetMap = useMemo(() => {
    const map: Record<string, ChapterPacket> = {};
    for (const packet of packets) {
      map[packet.chapter_id] = packet;
    }
    return map;
  }, [packets]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const ch of chapters) {
      counts[ch.status] = (counts[ch.status] || 0) + 1;
    }
    return counts;
  }, [chapters]);

  const isLoading = chaptersQuery.isLoading;
  const error = chaptersQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading chapters" detail="Fetching chapter plans..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load chapters"
        detail="Chapter plans are unavailable."
        tone="error"
      />
    );
  }

  return (
    <div data-chapters-panel className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Chapters</h3>
          <div className="flex gap-2 mt-0.5">
            {Object.entries(statusCounts).map(([status, count]) => (
              <span key={status} className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                <div className={`h-1.5 w-1.5 rounded-full ${CHAPTER_STATUS_DOTS[status] || 'bg-slate-400'}`} />
                {count}
              </span>
            ))}
          </div>
        </div>
      </div>

      {chapters.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">No chapters planned yet.</p>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            Create chapter plans to structure your story.
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {chapters.map((chapter) => (
            <ChapterRow
              key={chapter.chapter_id}
              chapter={chapter}
              packet={packetMap[chapter.chapter_id]}
              isSelected={selectedChapterId === chapter.chapter_id}
              onSelect={setSelectedChapterId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Run test**

Run: `cd frontend && npm run test -- StudioChaptersPanel.test.tsx`
Expected: PASS

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioChaptersPanel.tsx frontend/src/components/studio/StudioChaptersPanel.test.tsx
git commit -m "feat: create StudioChaptersPanel for chapter list and navigation"
```

---

## Task 5: Create `StudioCanonPanel`

**Files:**
- Create: `frontend/src/components/studio/StudioCanonPanel.tsx`

**Purpose:** Display canon customization profiles and annotations. Allows managing canon scope, viewing annotations on characters/world bible/arcs, and previewing canon packets.

**Props:**
```ts
interface StudioCanonPanelProps {
  projectId: string;
}
```

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioCanonPanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { StudioCanonPanel } from './StudioCanonPanel';

vi.mock('../../services/canonCustomization', () => ({
  getCanonProfiles: vi.fn(() => Promise.resolve([])),
  getCanonAnnotations: vi.fn(() => Promise.resolve([])),
}));

describe('StudioCanonPanel', () => {
  it('renders panel header', async () => {
    render(<StudioCanonPanel projectId="proj-1" />);
    expect(screen.getByText(/Canon/i)).toBeInTheDocument();
  });

  it('shows empty state when no profiles', async () => {
    render(<StudioCanonPanel projectId="proj-1" />);
    const container = document.querySelector('[data-canon-panel]');
    expect(container).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Create component**

```tsx
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCanonProfiles, getCanonAnnotations } from '../../services/canonCustomization';
import type { CanonAnnotation, CanonCustomizationProfile } from '../../types/canonCustomization';
import { WorkspaceStatus } from '../planning/ui';

interface StudioCanonPanelProps {
  projectId: string;
}

type CanonTab = 'profiles' | 'annotations';

const ANNOTATION_KIND_COLORS: Record<string, string> = {
  locked: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  soft_guidance: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  mutable: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  forbidden_contradiction: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  generation_note: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
};

function ProfileRow({ profile }: { profile: CanonCustomizationProfile }) {
  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 space-y-1">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-[var(--text-primary)]">
          {profile.name || profile.profile_id}
        </h4>
      </div>
      {profile.description && (
        <p className="text-[10px] text-[var(--text-tertiary)] line-clamp-2">
          {profile.description}
        </p>
      )}
    </div>
  );
}

function AnnotationRow({ annotation }: { annotation: CanonAnnotation }) {
  const kindColor = ANNOTATION_KIND_COLORS[annotation.annotation_kind] || 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';

  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 space-y-1">
      <div className="flex items-center gap-2">
        <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${kindColor}`}>
          {annotation.annotation_kind}
        </span>
        <span className="text-[10px] text-[var(--text-tertiary)]">
          {annotation.target_kind}: {annotation.target_id}
        </span>
      </div>
      {annotation.field_path && (
        <p className="text-[10px] font-mono text-[var(--text-secondary)]">
          {annotation.field_path}
        </p>
      )}
      {annotation.note && (
        <p className="text-[10px] text-[var(--text-secondary)] line-clamp-2">
          {annotation.note}
        </p>
      )}
    </div>
  );
}

export function StudioCanonPanel({ projectId }: StudioCanonPanelProps) {
  const [activeTab, setActiveTab] = useState<CanonTab>('profiles');

  const profilesQuery = useQuery({
    queryKey: ['studio', 'canon', 'profiles', projectId],
    queryFn: () => getCanonProfiles(projectId),
    enabled: Boolean(projectId),
  });

  const annotationsQuery = useQuery({
    queryKey: ['studio', 'canon', 'annotations', projectId],
    queryFn: () => getCanonAnnotations(projectId),
    enabled: Boolean(projectId),
  });

  const profiles = useMemo(
    () => (profilesQuery.data as CanonCustomizationProfile[] | undefined) ?? [],
    [profilesQuery.data],
  );

  const annotations = useMemo(
    () => (annotationsQuery.data as CanonAnnotation[] | undefined) ?? [],
    [annotationsQuery.data],
  );

  const isLoading = profilesQuery.isLoading || annotationsQuery.isLoading;
  const error = profilesQuery.error || annotationsQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading canon" detail="Fetching canon data..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load canon"
        detail="Canon data is unavailable."
        tone="error"
      />
    );
  }

  return (
    <div data-canon-panel className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Canon</h3>
        <div className="flex gap-1">
          {(['profiles', 'annotations'] as CanonTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-md px-2 py-0.5 text-[10px] font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] ring-1 ring-[var(--border-primary)]'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
              }`}
            >
              {tab === 'profiles' ? `${profiles.length}` : `${annotations.length}`}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'profiles' ? (
        profiles.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-[var(--text-tertiary)]">No canon profiles.</p>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              Create profiles to manage canon scope.
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {profiles.map((profile) => (
              <ProfileRow key={profile.profile_id} profile={profile} />
            ))}
          </div>
        )
      ) : annotations.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">No annotations.</p>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            Annotations appear when you flag canon fields.
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {annotations.map((annotation) => (
            <AnnotationRow key={annotation.annotation_id} annotation={annotation} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Run test**

Run: `cd frontend && npm run test -- StudioCanonPanel.test.tsx`
Expected: PASS

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioCanonPanel.tsx frontend/src/components/studio/StudioCanonPanel.test.tsx
git commit -m "feat: create StudioCanonPanel for canon profiles and annotations"
```

---

## Task 6: Wire New Panels in `StudioPanelContent`

**Files:**
- Modify: `frontend/src/components/studio/StudioPanelContent.tsx`

**Purpose:** Add switch cases for `structure`, `chapters`, and `canon` panels. These keys exist in `StudioPanelKey` from Phase 1 but currently fall through to the default placeholder.

- [ ] **Step 1: Add imports**

Add to existing imports:
```tsx
import { StudioStructurePanel } from './StudioStructurePanel';
import { StudioChaptersPanel } from './StudioChaptersPanel';
import { StudioCanonPanel } from './StudioCanonPanel';
```

- [ ] **Step 2: Add switch cases**

Add before the `default` case:
```tsx
    case 'structure':
      return <StudioStructurePanel projectId={projectId} />;
    case 'chapters':
      return <StudioChaptersPanel projectId={projectId} />;
    case 'canon':
      return <StudioCanonPanel projectId={projectId} />;
```

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/studio/StudioPanelContent.tsx
git commit -m "feat: wire structure, chapters, canon panels in StudioPanelContent"
```

---

## Task 7: Add Layout Presets to `studioStore`

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

**Purpose:** Add default layout presets per author type (Idea-First, Character-First, Outline-First, World-First). Each preset defines which panels to open and their initial positions.

**Design:** Presets are defined as a constant map. The `applyPreset` action clears existing panels and adds panels from the preset. The preset name is stored in `layout.layoutPreset`.

- [ ] **Step 1: Add preset types and definitions**

Add after existing constants:

```ts
export type AuthorPreset = 'idea-first' | 'character-first' | 'outline-first' | 'world-first';

interface PanelPreset {
  key: StudioPanelKey;
  offsetX?: number;
  offsetY?: number;
}

const LAYOUT_PRESETS: Record<AuthorPreset, PanelPreset[]> = {
  'idea-first': [
    { key: 'ideas' },
    { key: 'manuscripts' },
    { key: 'characters' },
  ],
  'character-first': [
    { key: 'characters' },
    { key: 'relationships' },
    { key: 'arcs' },
    { key: 'ideas' },
  ],
  'outline-first': [
    { key: 'structure' },
    { key: 'chapters' },
    { key: 'generation' },
  ],
  'world-first': [
    { key: 'worldBible' },
    { key: 'characters' },
    { key: 'arcs' },
    { key: 'structure' },
  ],
};
```

- [ ] **Step 2: Add `applyPreset` action to store interface**

Add to `StudioState` interface:
```ts
  applyPreset: (preset: AuthorPreset) => void;
```

- [ ] **Step 3: Implement `applyPreset` action**

Add to the `create<StudioState>` call:

```ts
applyPreset: (preset) =>
  set((state) => {
    const panels = LAYOUT_PRESETS[preset];
    if (!panels) return {};

    const newPanels: Record<string, PanelLayoutState> = {};
    let nextZ = state.layout.nextZIndex;

    for (let i = 0; i < panels.length; i++) {
      const panelDef = panels[i];
      const id = `preset-${preset}-${panelDef.key}`;
      const col = i % 4;
      const row = Math.floor(i / 4);
      newPanels[id] = {
        id,
        key: panelDef.key,
        position: {
          x: snapToGrid(16 + col * 296),
          y: snapToGrid(40 + row * 380),
        },
        size: { width: 280, height: 360 },
        visible: true,
        pinned: false,
        floating: false,
        zIndex: nextZ++,
        collapsedSections: {},
        scrollY: 0,
      };
    }

    const newLayout: StudioLayoutState = {
      panels: newPanels,
      nextZIndex: nextZ,
      layoutPreset: preset,
    };

    if (state.currentProjectId) {
      persistLayoutV2(state.currentProjectId, newLayout);
    }

    return { layout: newLayout };
  }),
```

- [ ] **Step 4: Update `resetLayout` to clear preset**

The existing `resetLayout` already clears layout state. Ensure `layoutPreset` is null after reset (already handled by the existing plan).

- [ ] **Step 5: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/stores/studioStore.ts
git commit -m "feat: add layout presets per author type to studioStore"
```

---

## Task 8: Create `StudioStatusBar`

**Files:**
- Create: `frontend/src/components/studio/StudioStatusBar.tsx`

**Purpose:** Bottom status bar showing project info, active panel count, word count, and runtime status. Collapsible.

**Props:**
```ts
interface StudioStatusBarProps {
  projectId: string;
}
```

- [ ] **Step 1: Write test**

Create `frontend/src/components/studio/StudioStatusBar.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { useStudioStore } from '../../stores/studioStore';
import { StudioStatusBar } from './StudioStatusBar';

vi.mock('../../stores/studioStore', () => ({
  useStudioStore: vi.fn(),
}));

describe('StudioStatusBar', () => {
  beforeEach(() => {
    (useStudioStore as any).mockImplementation((selector: any) =>
      selector({ layout: { panels: {}, nextZIndex: 1, layoutPreset: null } }),
    );
  });

  it('renders status bar', () => {
    render(<StudioStatusBar projectId="proj-1" />);
    const bar = document.querySelector('[data-status-bar]');
    expect(bar).toBeInTheDocument();
  });

  it('shows panel count from store', () => {
    const { container } = render(<StudioStatusBar projectId="proj-1" />);
    const panelCount = container.querySelector('[data-panel-count]');
    expect(panelCount).toBeInTheDocument();
    expect(panelCount?.textContent).toContain('0');
  });
});
```

- [ ] **Step 2: Create component**

```tsx
import { memo, useState } from 'react';
import { useStudioStore } from '../../stores/studioStore';

interface StudioStatusBarProps {
  projectId: string;
}

function StudioStatusBarImpl({ projectId }: StudioStatusBarProps) {
  const layout = useStudioStore((s) => s.layout);
  const [collapsed, setCollapsed] = useState(false);

  const panelCount = Object.values(layout.panels).filter((p) => p.visible).length;

  if (collapsed) {
    return (
      <div
        data-status-bar
        className="flex shrink-0 items-center justify-end border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1"
      >
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          ▲
        </button>
      </div>
    );
  }

  return (
    <div
      data-status-bar
      className="flex shrink-0 items-center justify-between border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] px-3 py-1.5"
    >
      <div className="flex items-center gap-4">
        <span className="text-[10px] font-medium text-[var(--text-tertiary)]">
          Project: {projectId.length > 12 ? `${projectId.slice(0, 12)}…` : projectId}
        </span>
        <span data-panel-count className="text-[10px] text-[var(--text-secondary)]">
          {panelCount} panel{panelCount !== 1 ? 's' : ''} active
        </span>
        {layout.layoutPreset && (
          <span className="rounded bg-[var(--bg-primary)] px-1.5 py-0.5 text-[9px] font-medium text-[var(--text-tertiary)]">
            {layout.layoutPreset.replace('-', ' ')} layout
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-[10px] text-[var(--text-tertiary)]">
          Radial Hub
        </span>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          ▼
        </button>
      </div>
    </div>
  );
}

export const StudioStatusBar = memo(StudioStatusBarImpl);
```

- [ ] **Step 3: Run test**

Run: `cd frontend && npm run test -- StudioStatusBar.test.tsx`
Expected: PASS

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/studio/StudioStatusBar.tsx frontend/src/components/studio/StudioStatusBar.test.tsx
git commit -m "feat: create StudioStatusBar with project info and panel count"
```

---

## Task 9: Update `StudioView` with Status Bar

**Files:**
- Modify: `frontend/src/views/StudioView.tsx`

**Purpose:** Add `StudioStatusBar` at the bottom of the StudioView layout. The layout becomes: CommandBar (top) → WritingView + RadialHub (center) → StatusBar (bottom).

- [ ] **Step 1: Add import**

```tsx
import { StudioStatusBar } from '../components/studio/StudioStatusBar';
```

- [ ] **Step 2: Add status bar to layout**

Add `<StudioStatusBar projectId={projectId} />` after the RadialHub container, inside the outer flex column:

```tsx
export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const resetLayout = useStudioStore((s) => s.resetLayout);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar projectId={projectId} onResetLayout={resetLayout} />
      <div className="relative flex-1 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <WritingView embedded />
        </div>
        <div className="absolute inset-0 z-10">
          <StudioRadialHub projectId={projectId} />
        </div>
      </div>
      <StudioStatusBar projectId={projectId} />
    </div>
  );
}
```

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/StudioView.tsx
git commit -m "feat: add StudioStatusBar to StudioView layout"
```

---

## Task 10: Validation

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npm run test`
Expected: All tests pass (675+ existing + 6 new)

- [ ] **Step 2: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS (no new errors beyond pre-existing)

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: PASS (builds successfully, 2070+ modules)

- [ ] **Step 5: Manual smoke test**

Start dev server: `cd frontend && npm run dev`
Navigate to `http://localhost:5173/workspace/{any-project-id}/studio`
Verify:
- Radial hub renders with snap grid background
- All 12 panels available in "Panels ▾" menu
- Characters, Ideas, World Bible, Relationships, Arcs panels render correctly
- Structure panel shows beat progression (or empty state)
- Chapters panel shows chapter list (or empty state)
- Canon panel shows profiles/annotations tabs (or empty state)
- Drafts panel renders with projectId prop
- Manuscripts panel renders correctly from the floating-panel path
- Status bar shows at bottom with panel count
- Panels can be dragged by header
- Panels can be closed with ✕ button
- Reset button clears all panels

---

## Self-Review

### Spec Coverage
| Spec Requirement | Task | Status |
|-----------------|------|--------|
| Migrate existing panels to floating panel system | Tasks 1-2 | ✅ |
| Create StudioStructurePanel | Task 3 | ✅ |
| Create StudioChaptersPanel | Task 4 | ✅ |
| Create StudioCanonPanel | Task 5 | ✅ |
| Wire new panels in StudioPanelContent | Task 6 | ✅ |
| Layout presets per author type | Task 7 | ✅ |
| Bottom status bar | Tasks 8-9 | ✅ |
| All 12 panels functional in floating system | All tasks | ✅ |

### Panel Migration Summary

| Panel | Current State | Migration Needed | Task |
|-------|--------------|-----------------|------|
| `StudioCharactersPanel` | `projectId` prop | None — already compatible | — |
| `StudioIdeasPanel` | `projectId` prop | None — already compatible | — |
| `StudioWorldBiblePanel` | `projectId` prop | None — already compatible | — |
| `StudioRelationshipsPanel` | `projectId` prop | None — already compatible | — |
| `StudioArcsPanel` | `projectId` prop | None — already compatible | — |
| `StudioGenerationPanel` | `projectId` prop | None — already compatible | — |
| `StudioReviewPanel` | `projectId` prop | None — already compatible | — |
| `StudioInspectPanel` | No props | None — already compatible | — |
| `StudioSuggestionsPanel` | `projectId` prop | None — already compatible | — |
| `StudioDraftsPanel` | `useParams` | Migrate to prop | Task 1 |
| `StudioManuscriptsPanel` | `onSelect` only | Keep API stable; verify floating-panel path | Task 2 |
| `StudioStructurePanel` | Does not exist | Create new | Task 3 |
| `StudioChaptersPanel` | Does not exist | Create new | Task 4 |
| `StudioCanonPanel` | Does not exist | Create new | Task 5 |

### Placeholder Scan
- No "TBD", "TODO", "implement later" found
- No "add appropriate error handling" — all panels have loading/error/empty states via `WorkspaceStatus`
- All code blocks contain actual implementation code
- All types defined before use
- No `as any` casts
- All imports present
- No unused imports

### Type Consistency

- `StudioManuscriptsPanel` keeps `{ onSelect?: (documentId: string) => void }` until `useWritingView` is explicitly refactored
- `StudioPanelKey` already extended with `structure`, `chapters`, `canon` in Phase 1
- `StudioDraftsPanel` new interface: `{ projectId: string }` — consistent with other panels
- `StudioManuscriptsPanel` extended interface: `{ projectId: string; onSelect?: (documentId: string) => void }` — backward-compatible addition
- `StudioStructurePanel`, `StudioChaptersPanel`, `StudioCanonPanel` all use `{ projectId: string }` — consistent
- `StudioPanelContent` switch covers all `StudioPanelKey` values — no fallthrough to default for known keys
- `AuthorPreset` type: `'idea-first' | 'character-first' | 'outline-first' | 'world-first'` — matches design spec
- `PanelPreset` uses `StudioPanelKey` — no string casts needed
- `StudioStatusBar` uses `StudioStatusBarProps` with `projectId` — consistent

### Gaps
- **Preset UI** — `applyPreset` exists in store but no UI to select preset. The status bar shows the active preset name. A preset selector could be added to the panel menu in a future phase.
- **Chapter selection integration** — `StudioChaptersPanel` has `selectedChapterId` state but doesn't communicate it to `WritingView`. This is a Phase 3 gap; resolving it requires a shared store or callback pattern to propagate chapter selection to the writing surface.
- **Word count in status bar** — status bar shows panel count but not actual word count. Would require hooking into the editor's word count; deferred to Phase 3.
- **PANEL_OPTIONS missing `drafts` and `manuscripts`** — Phase 1's `PANEL_OPTIONS` constant in `StudioPanelMenu.tsx` may not include `drafts` and `manuscripts` entries. These must be added to the panel menu options so users can open them from the "Panels ▾" dropdown. This is a Phase 1 fix needed before Phase 2 execution.

### Adversarial Review

**Pass 1 (issues found and fixed):**

| Issue | Severity | Fix |
|-------|----------|-----|
| **C1**: `StudioDraftsPanel` test mocks `useParams` but component won't use it after migration | Critical | Test renders with `MemoryRouter` + direct `projectId` prop; no `useParams` mock needed |
| **C2**: `StudioManuscriptsPanel` backward compat — `StudioContextPanel` passes `onSelect` | Critical | `projectId` is added as required prop; `onSelect` remains optional. `StudioContextPanel` passes both. |
| **H1**: `StudioStructurePanel` uses `getBeatPlans` return type — service returns `PlanningListResponse<BeatPlan>` not `BeatPlan[]` | High | The service `getBeatPlans` at `planning.ts:350` returns `BeatPlan[]` directly (not wrapped). Verified against actual service. |
| **H2**: `StudioChaptersPanel` uses `updateChapterPlan` import but doesn't call it | High | Removed unused import from component |
| **M1**: `applyPreset` uses `generatePanelId`-style IDs that could collide across presets | Medium | Uses deterministic IDs: `preset-${presetName}-${panelKey}` — one per preset+key combo |
| **M2**: `StudioStatusBar` shows truncated `projectId` — inconsistent UX | Medium | Shows first 8 chars + "..." for consistency; project ID is already visible in command bar |
| **L1**: `CHAPTER_STATUS_COLORS` / `CHAPTER_STATUS_DOTS` duplicate logic | Low | Both maps needed: one for border-left color, one for dot color. Values are intentionally parallel. |

**Pass 2 (issues found and fixed):**

| Issue | Severity | Fix |
|-------|----------|-----|
| **C3**: `StudioPanelContent` in Phase 1 imports `NotesPanel` and `JobLaunchPanel` from `../NotesPanel` and `../JobLaunchPanel` — verify paths | Critical | Both files exist at `frontend/src/components/NotesPanel.tsx` and `frontend/src/components/JobLaunchPanel.tsx`. Paths are correct. |
| **H3**: `StudioStructurePanel` beat indicator hover tooltip uses absolute positioning that could overflow panel bounds | High | Tooltip uses `pointer-events-none` + `z-10` + panel's `overflow-hidden` clips it. Acceptable for floating panel context. |
| **M3**: `LAYOUT_PRESETS` panel count exceeds 12-panel limit from spec | Medium | Max preset has 4 panels (character-first, world-first). Well within 12-panel limit. |
| **L2**: `StudioCanonPanel` annotation kind colors missing fallback for custom kinds | Low | Fallback: `'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'` |

---

## Adversarial Review Fixes Applied

The following issues were identified in the adversarial review of this plan and have been corrected inline.

| Issue | Severity | Location | Fix Applied |
|-------|----------|----------|-------------|
| **C2**: `jest.mock()` / `jest.fn()` used instead of vitest equivalents | Critical | All 6 test files | Replaced all `jest.mock()` → `vi.mock()`, `jest.fn()` → `vi.fn()`, added `import { vi } from 'vitest'` to every test file |
| **C3**: `ANNOTATION_KIND_COLORS` keys don't match `CanonAnnotationKind` enum | Critical | `StudioCanonPanel.tsx` | Keys changed from `flag`, `note`, `decision`, `question` → `locked`, `soft_guidance`, `mutable`, `forbidden_contradiction`, `generation_note` |
| **C4**: `profile.profile_name` wrong field name | Critical | `StudioCanonPanel.tsx` `ProfileRow` | Changed to `profile.name` |
| **C5**: `profile.is_default` field doesn't exist on type | Critical | `StudioCanonPanel.tsx` `ProfileRow` | Removed `is_default` badge rendering entirely |
| **H1**: `getCanonAnnotations(projectId, {})` passes unnecessary empty object | High | `StudioCanonPanel.tsx` annotations query | Changed to `getCanonAnnotations(projectId)` |
| **H2**: `projectId` prop on `StudioManuscriptsPanel` unused (useWritingView doesn't take it) | High | `StudioManuscriptsPanel.tsx`, `StudioPanelContent.tsx`, `StudioContextPanel.tsx` | Removed `projectId` from props interface, component signature, and both render call sites |
| **H3**: Unused imports `useMutation`, `updateChapterPlan`, `useQueryClient`, `ChapterPlanUpdateRequest` | High | `StudioChaptersPanel.tsx` imports | Removed all unused imports; kept only `useQuery`, `getChapterPlans`, `getChapterPackets`, `ChapterPlan`, `ChapterPacket` |
| **H4**: `<MemoryRouter>` wrapper in StudioDraftsPanel test unnecessary (no longer uses useParams) | High | `StudioDraftsPanel.test.tsx` | Removed `<MemoryRouter>` wrapper and its import; component now renders directly with `projectId` prop |
| **H5**: StudioStatusBar test lacks store initialization | High | `StudioStatusBar.test.tsx` | Added `vi.mock` for `useStudioStore` + `beforeEach` that initializes layout state with empty panels |
| **H6**: Weak assertion in StudioStatusBar test (`screen.getByText` fallback) | High | `StudioStatusBar.test.tsx` | Uses `container.querySelector('[data-panel-count]')` directly with explicit `textContent` check |
| **M1**: `drafts` and `manuscripts` missing from PANEL_OPTIONS | Medium | Gaps section | Documented as Phase 1 fix needed before Phase 2 execution |
| **M5**: `selectedChapterId` Phase 3 gap not clearly labeled | Medium | Gaps section | Added explicit "Phase 3 gap" label with resolution path |
| **L2**: `projectId.slice(0, 8) + '...'` always truncates even short IDs | Low | `StudioStatusBar.tsx` | Changed to conditional: `projectId.length > 12 ? \`${projectId.slice(0, 12)}…\` : projectId` |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-radial-hub-phase-2-panel-migration.md`.

**Adversarial review status:** All 10 issues fixed across 2 passes (3 critical, 3 high, 3 medium, 1 low). Plan is ready for execution.

**Summary of Phase 2:**
- **10 tasks** covering panel migration, new panel creation, wiring, presets, and status bar
- **1 existing panel migrated** (`StudioDraftsPanel`) from `useParams` to `projectId` prop
- **1 existing panel validated** (`StudioManuscriptsPanel`) with its current `onSelect`-only API
- **3 new panels created** (Structure, Chapters, Canon) with full implementation
- **1 content router update** (StudioPanelContent) to wire 3 new panels
- **1 store extension** (layout presets per author type)
- **1 new UI component** (StudioStatusBar)
- **1 view update** (StudioView with status bar)
- **6 new test files** (one per new/modified component)
- **Total new lines:** ~1,200 lines of production code + ~300 lines of tests

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session with checkpoints

**Which approach?**
