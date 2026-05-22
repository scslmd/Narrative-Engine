# Studio Desk Stage 1 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Stage 1 adds an opt-in `/workspace/:projectId/studio` frontend workspace that keeps writing central while exposing existing Narrative Engine tools through project and context panels.

**Architecture:** This is an additive frontend-only migration. Existing backend endpoints, services, hooks, and legacy workspace routes remain unchanged. Studio composes existing capabilities into a command-bar + project-rail + center-editor + sliding-context-panel layout.

**Tech Stack:** React 18, TypeScript, React Router, Zustand, React Query, Tailwind CSS, Vitest, Testing Library.

---

## Source Design

Design spec: `docs/superpowers/specs/2026-05-16-studio-desk-redesign-design.md`

## Deterministic Task Contract

Validation summary:

- Every task has exactly one `responsible_file`.
- Same-file reuse is serial only.
- No task adds backend routes, schemas, database fields, or LLM prompt contracts.
- Existing routes remain available.
- Existing frontend services/hooks/components are reused.

Task ownership:

| Task | Responsible file | Purpose |
| --- | --- | --- |
| T001 | `frontend/src/routes.ts` | Add `studio` mode and route helper |
| T002 | `frontend/src/stores/studioStore.ts` | Add panel state |
| T003 | `frontend/src/components/studio/StudioCommandBar.tsx` | Add command bar |
| T004 | `frontend/src/components/studio/StudioProjectRail.tsx` | Add project rail |
| T005 | `frontend/src/components/studio/StudioIdeasPanel.tsx` | Reuse brainstorm surface |
| T006 | `frontend/src/components/studio/StudioCharactersPanel.tsx` | Reuse character services and builder |
| T007 | `frontend/src/components/studio/StudioWorldBiblePanel.tsx` | Reuse world bible workspace |
| T008 | `frontend/src/components/studio/StudioRelationshipsPanel.tsx` | Reuse relationship graph/list/forms |
| T009 | `frontend/src/components/studio/StudioContextPanel.tsx` | Switch panels |
| T010 | `frontend/src/views/StudioView.tsx` | Compose Studio layout |
| T011 | `frontend/src/views/Workspace.tsx` | Treat Studio as single-column workspace |
| T012 | `frontend/src/App.tsx` | Register route |
| T013 | `frontend/src/components/WorkspaceShell.tsx` | Expose Studio nav |
| T014 | `frontend/src/components/WorkspaceShell.test.tsx` | Update nav tests |
| T015 | `frontend/src/views/StudioView.test.tsx` | Add Studio route tests |

## Guardrails

- Do not remove `/plan`, `/write`, `/review`, `/inspect`, `/braindump`, `/canon`, or `/generate`.
- Do not create backend APIs.
- Do not change existing service contracts.
- Do not add mock production data.
- Do not use `fetch`; keep existing shared service patterns.
- Keep Studio additive until all tests pass.

---

## Tasks

### Task T001: Add Studio Workspace Mode And Route Helper

**Responsible file:** `frontend/src/routes.ts`

**Dependencies:** none

- [x] Add `studio` to `WorkspaceMode`.

```ts
export type WorkspaceMode = 'studio' | 'plan' | 'write' | 'review' | 'inspect' | 'braindump' | 'generate' | 'canon'
```

- [x] Add `studio` to `modeToStage`.

```ts
export const modeToStage: Record<WorkspaceMode, 'planning' | 'writing' | 'review'> = {
  studio: 'writing',
  braindump: 'planning',
  plan: 'planning',
  canon: 'planning',
  generate: 'planning',
  write: 'writing',
  review: 'review',
  inspect: 'review',
}
```

- [x] Add the helper inside `routes`.

```ts
studio: (projectId: string) => `/workspace/${projectId}/studio`,
```

- [x] Verify.

```powershell
cd frontend; cmd /c npm.cmd run typecheck
```

Expected: exits 0.

### Task T002: Create Studio Panel State Store

**Responsible file:** `frontend/src/stores/studioStore.ts`

**Dependencies:** T001

- [x] Create the file.

```ts
import { create } from 'zustand';

export type StudioPanelKey =
  | 'suggestions'
  | 'ideas'
  | 'characters'
  | 'worldBible'
  | 'relationships'
  | 'generation'
  | 'review'
  | 'inspect'
  | 'notes'
  | 'jobs';

interface StudioState {
  activePanel: StudioPanelKey;
  leftRailOpen: boolean;
  contextPanelOpen: boolean;
  setActivePanel: (panel: StudioPanelKey) => void;
  setLeftRailOpen: (open: boolean) => void;
  setContextPanelOpen: (open: boolean) => void;
  openPanel: (panel: StudioPanelKey) => void;
}

export const useStudioStore = create<StudioState>((set) => ({
  activePanel: 'suggestions',
  leftRailOpen: true,
  contextPanelOpen: true,
  setActivePanel: (activePanel) => set({ activePanel }),
  setLeftRailOpen: (leftRailOpen) => set({ leftRailOpen }),
  setContextPanelOpen: (contextPanelOpen) => set({ contextPanelOpen }),
  openPanel: (activePanel) => set({ activePanel, contextPanelOpen: true }),
}));
```

- [x] Verify typecheck.

### Task T003: Create Studio Command Bar

**Responsible file:** `frontend/src/components/studio/StudioCommandBar.tsx`

**Dependencies:** T002

- [x] Create `frontend/src/components/studio`.

- [x] Create the command bar.

```tsx
import { BookOpen, GitPullRequestArrow, Lightbulb, Search, Wand2 } from 'lucide-react';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';

const commands: Array<{ label: string; panel: StudioPanelKey; icon: typeof Lightbulb }> = [
  { label: 'Capture', panel: 'ideas', icon: Lightbulb },
  { label: 'Write', panel: 'suggestions', icon: BookOpen },
  { label: 'Generate', panel: 'generation', icon: Wand2 },
  { label: 'Review', panel: 'review', icon: GitPullRequestArrow },
  { label: 'Inspect', panel: 'inspect', icon: Search },
];

interface StudioCommandBarProps {
  projectName?: string;
}

export function StudioCommandBar({ projectName = 'Current Project' }: StudioCommandBarProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);

  return (
    <header className="flex items-center justify-between gap-3 border-b border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3">
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--text-tertiary)]">Studio Desk</p>
        <h1 className="truncate text-sm font-semibold text-[var(--text-primary)]">{projectName}</h1>
      </div>
      <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Studio commands">
        {commands.map((command) => {
          const Icon = command.icon;
          const active = activePanel === command.panel;
          return (
            <button
              key={command.panel}
              type="button"
              onClick={() => openPanel(command.panel)}
              aria-pressed={active}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {command.label}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
```

- [x] Verify typecheck.

### Task T004: Create Studio Project Rail

**Responsible file:** `frontend/src/components/studio/StudioProjectRail.tsx`

**Dependencies:** T002

- [x] Create the rail.

```tsx
import { Link } from 'react-router-dom';
import { BookOpen, Brain, GitBranch, Network, Scroll, StickyNote, Users } from 'lucide-react';
import { useStudioStore, type StudioPanelKey } from '../../stores/studioStore';

const railItems: Array<{ label: string; panel: StudioPanelKey; icon: typeof Brain }> = [
  { label: 'Ideas', panel: 'ideas', icon: Brain },
  { label: 'Characters', panel: 'characters', icon: Users },
  { label: 'World Bible', panel: 'worldBible', icon: BookOpen },
  { label: 'Relationships', panel: 'relationships', icon: Network },
  { label: 'Canon', panel: 'generation', icon: Scroll },
  { label: 'Jobs', panel: 'jobs', icon: GitBranch },
  { label: 'Notes', panel: 'notes', icon: StickyNote },
];

interface StudioProjectRailProps {
  projectId: string;
}

export function StudioProjectRail({ projectId }: StudioProjectRailProps) {
  const activePanel = useStudioStore((state) => state.activePanel);
  const openPanel = useStudioStore((state) => state.openPanel);

  return (
    <aside className="flex h-full flex-col border-r border-[var(--border-primary)] bg-[var(--bg-secondary)]">
      <div className="border-b border-[var(--border-primary)] px-3 py-2">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-tertiary)]">Project Map</p>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-2" aria-label="Studio project map">
        {railItems.map((item) => {
          const Icon = item.icon;
          const active = activePanel === item.panel;
          return (
            <button
              key={item.panel}
              type="button"
              onClick={() => openPanel(item.panel)}
              aria-pressed={active}
              className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs font-medium transition-colors ${
                active
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="space-y-1 border-t border-[var(--border-primary)] p-2 text-[11px] text-[var(--text-tertiary)]">
        <Link className="block rounded px-2 py-1 hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]" to={`/workspace/${projectId}/plan`}>Open full Planning</Link>
        <Link className="block rounded px-2 py-1 hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]" to={`/workspace/${projectId}/canon`}>Open full Canon</Link>
      </div>
    </aside>
  );
}
```

- [x] Verify typecheck.

### Task T005: Create Studio Ideas Panel

**Responsible file:** `frontend/src/components/studio/StudioIdeasPanel.tsx`

**Dependencies:** T002

- [x] Create the panel.

```tsx
import { BrainstormWorkspace } from '../brainstorm/BrainstormWorkspace';
import { useBrainstorm } from '../../hooks/useBrainstorm';
import { WorkspaceStatus } from '../planning/ui';

interface StudioIdeasPanelProps {
  projectId: string;
}

export function StudioIdeasPanel({ projectId }: StudioIdeasPanelProps) {
  const { items, isLoading, addItem, clusterItems, promoteItem } = useBrainstorm(projectId);

  if (isLoading) {
    return <WorkspaceStatus title="Loading ideas" detail="Fetching brainstorm items." />;
  }

  return (
    <BrainstormWorkspace
      projectId={projectId}
      items={items}
      onItemAdd={(request) => void addItem(request)}
      onClusterCreate={(itemIds) => void clusterItems(itemIds)}
      onPromote={async ({ item_id, target_object_kind, target_object_id }) => {
        await promoteItem(item_id, target_object_kind, target_object_id);
      }}
    />
  );
}
```

- [x] Verify typecheck.

### Task T006: Create Studio Characters Panel

**Responsible file:** `frontend/src/components/studio/StudioCharactersPanel.tsx`

**Dependencies:** T002

- [x] Create a panel that uses existing services and `CharacterBuilder`.

Required imports:

```tsx
import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CharacterBuilder } from '../characters/CharacterBuilder';
import { WorkspaceStatus } from '../planning/ui';
import { createCharacter, getCharacter, getCharacters, updateCharacter } from '../../services/characters';
import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../../types/characters';
```

Exact acceptance requirements:

- Query key for list: `['studio', 'characters', projectId]`.
- Query key for selected character: `['studio', 'character', projectId, selectedCharacterId]`.
- Local editor mode type is exactly `type CharacterEditorMode = 'list' | 'create' | 'edit';`.
- Local state names are exactly `mode` and `selectedCharacterId`.
- List mode shows heading `Characters`, count text `${characters.length} profiles`, and button `New Character`.
- Create mode renders `CharacterBuilder` without `character`.
- Edit mode renders `CharacterBuilder` with selected character.
- Save create calls `createCharacter`.
- Save edit calls `updateCharacter`.
- Payload creation must omit `project_id`, `character_id`, and `relationship_edges` before create/update using a local `omitKeys` helper copied from `PlanningView`.
- On successful save invalidate `['studio', 'characters', projectId]` and return to list.
- `canonAnnotations` is `[]` and `onAnnotateField` is `async () => undefined` in this first pass.
- If character list query errors, render `<WorkspaceStatus title="Could not load characters" detail="Character profiles are unavailable." tone="error" />`.
- If selected character cannot be found in edit mode, render `<WorkspaceStatus title="Character not found" detail="Return to the list and choose another profile." tone="error" />`.

- [x] Verify typecheck.

### Task T007: Create Studio World Bible Panel

**Responsible file:** `frontend/src/components/studio/StudioWorldBiblePanel.tsx`

**Dependencies:** T002

- [x] Create a panel that uses existing `WorldBibleWorkspace`.

Required imports:

```tsx
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { WorldBibleWorkspace } from '../bible/WorldBibleWorkspace';
import { WorkspaceStatus } from '../planning/ui';
import { createWorldBibleEntry, getWorldBibleEntries, updateWorldBibleEntry } from '../../services/worldBible';
import type { WorldBibleEntry, WorldBibleEntryUpdateRequest } from '../../types/bible';
```

Exact acceptance requirements:

- Query key: `['studio', 'world-bible', projectId]`.
- Add calls `createWorldBibleEntry`.
- Update calls `updateWorldBibleEntry(entry.entry_type, originalTitle, projectId, updates)`.
- `updates` omits `entry_id`, `project_id`, and `entry_type` using a local `omitKeys` helper copied from `PlanningView`.
- `canonAnnotations` is `[]` and `onAnnotateField` is `async () => undefined` in this first pass.
- Loading state renders `<WorkspaceStatus title="Loading world bible" detail="Fetching world bible entries." />`.
- Error state renders `<WorkspaceStatus title="Could not load world bible" detail="World bible entries are unavailable." tone="error" />`.

- [x] Verify typecheck.

### Task T008: Create Studio Relationships Panel

**Responsible file:** `frontend/src/components/studio/StudioRelationshipsPanel.tsx`

**Dependencies:** T002

- [x] Create a panel using only existing relationship services/components.

Required imports:

```tsx
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RelationshipEditModal } from '../characters/RelationshipEditModal';
import { RelationshipForm } from '../characters/RelationshipForm';
import { RelationshipList } from '../characters/RelationshipList';
import { RelationshipMapGraph } from '../characters/RelationshipMapGraph';
import { WorkspaceStatus } from '../planning/ui';
import { getCharacters } from '../../services/characters';
import { getRelationships } from '../../services/relationships';
import { useRelationships } from '../../hooks/useRelationships';
import type { RelationshipEdge } from '../../types/characters';
```

Exact acceptance requirements:

- Characters query key: `['studio', 'relationship-characters', projectId]`.
- Relationships query key: `['studio', 'relationships', projectId]`.
- Local state names are exactly `showCreateRelationship` and `editingRelationship`.
- `editingRelationship` type is `RelationshipEdge | null`.
- Loading state title: `Loading relationships`.
- Error state title: `Could not load relationships`.
- Button label: `Add Relationship`.
- Create form uses `RelationshipForm` with `characters={characters}`, `isSubmitting={relationshipHook.isCreating}`, `onSubmit={async (data) => { await relationshipHook.createRelationship(data); setShowCreateRelationship(false); }}`, and `onCancel={() => setShowCreateRelationship(false)}`.
- Graph uses `RelationshipMapGraph` with `characters={characters}`, `relationships={relationships}`, `onDeleteRelationship={(edgeId) => void relationshipHook.deleteRelationship(edgeId)}`, and `onEditRelationship={(edgeId) => setEditingRelationship(relationships.find((r) => r.edge_id === edgeId) ?? null)}`.
- List uses `RelationshipList` with `relationships={relationships}`, `characterNames={characterNameMap}`, `onDeleteRelationship={(edgeId) => void relationshipHook.deleteRelationship(edgeId)}`, and `onUpdateRelationship={(edgeId) => setEditingRelationship(relationships.find((r) => r.edge_id === edgeId) ?? null)}`.
- Edit modal must render only inside `{editingRelationship && (...)}` so TypeScript narrows `editingRelationship` to `RelationshipEdge`.
- Inside that guarded block, use `RelationshipEditModal` with `isOpen={!!editingRelationship}`, `relationship={editingRelationship}`, `characters={characters}`, `isSaving={relationshipHook.isUpdating}`, `isDeleting={relationshipHook.isDeleting}`, `onClose={() => setEditingRelationship(null)}`, `onSave={async (edgeId, data) => { await relationshipHook.updateRelationship(edgeId, data); }}`, and `onDelete={async (edgeId) => { await relationshipHook.deleteRelationship(edgeId); }}`.
- `characterNameMap` is built with `useMemo` from `characters`, mapping `character.character_id` to `character.display_name`.
- Do not include AI extract or scan manuscript buttons in this first pass.

- [x] Verify typecheck.

### Task T009: Create Studio Context Panel Shell

**Responsible file:** `frontend/src/components/studio/StudioContextPanel.tsx`

**Dependencies:** T003, T005, T006, T007, T008

- [x] Create a shell that switches by `activePanel`.

Required mapping:

```ts
const panelLabels = {
  suggestions: 'Suggestions',
  ideas: 'Ideas',
  characters: 'Characters',
  worldBible: 'World Bible',
  relationships: 'Relationships',
  generation: 'Generation',
  review: 'Review',
  inspect: 'Inspect',
  notes: 'Notes',
  jobs: 'Jobs',
} as const;
```

Render requirements:

- `ideas`: `<StudioIdeasPanel projectId={projectId} />`
- `characters`: `<StudioCharactersPanel projectId={projectId} />`
- `worldBible`: `<StudioWorldBiblePanel projectId={projectId} />`
- `relationships`: `<StudioRelationshipsPanel projectId={projectId} />`
- `generation`: `<GenerationView />`
- `review`: `<ReviewView />`
- `inspect`: `<InspectView />`
- `notes`: `<NotesPanel projectId={projectId} />`
- `jobs`: `<JobLaunchPanel projectId={projectId} />`
- `suggestions`: render `AidsPanel` with `suggestions={[]}` and no-op handlers.

Acceptance notes:

- Empty suggestions are allowed because merged suggestion state currently lives inside `WritingView`.
- The panel must include a close button that calls `setContextPanelOpen(false)`.

- [x] Verify typecheck.

### Task T010: Create Studio View Composition

**Responsible file:** `frontend/src/views/StudioView.tsx`

**Dependencies:** T003, T004, T009

- [x] Create the view.

```tsx
import { useParams } from 'react-router-dom';
import { StudioCommandBar } from '../components/studio/StudioCommandBar';
import { StudioContextPanel } from '../components/studio/StudioContextPanel';
import { StudioProjectRail } from '../components/studio/StudioProjectRail';
import { WritingView } from './WritingView';
import { useStudioStore } from '../stores/studioStore';

export function StudioView() {
  const { projectId } = useParams<{ projectId: string }>();
  const leftRailOpen = useStudioStore((state) => state.leftRailOpen);
  const contextPanelOpen = useStudioStore((state) => state.contextPanelOpen);

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
      <StudioCommandBar />
      <div
        className="grid min-h-0 flex-1"
        style={{ gridTemplateColumns: `${leftRailOpen ? '13rem' : '0rem'} minmax(0,1fr) ${contextPanelOpen ? '26rem' : '0rem'}` }}
      >
        <div className="min-h-0 overflow-hidden">
          {leftRailOpen ? <StudioProjectRail projectId={projectId} /> : null}
        </div>
        <main className="min-h-0 overflow-hidden bg-[var(--bg-primary)]">
          <WritingView />
        </main>
        <div className="min-h-0 overflow-hidden border-l border-[var(--border-primary)]">
          {contextPanelOpen ? <StudioContextPanel projectId={projectId} /> : null}
        </div>
      </div>
    </div>
  );
}
```

- [x] Verify typecheck.

### Task T011: Treat Studio As Single-Column Workspace

**Responsible file:** `frontend/src/views/Workspace.tsx`

**Dependencies:** T010

- [x] Update mode detection so Studio receives the same no-right-rail layout as Writing.

Replace:

```ts
const isWriting = mode === 'write';
```

With:

```ts
const isFocusedWorkspace = mode === 'write' || mode === 'studio';
```

- [x] Replace both uses of `isWriting` in the JSX with `isFocusedWorkspace`.
- [x] Do not remove `BottomUtilityLayer` from `Workspace.tsx`; it remains the single workspace-level bottom tray.
- [x] Verify typecheck.

### Task T012: Register Studio Route

**Responsible file:** `frontend/src/App.tsx`

**Dependencies:** T011

- [x] Import `StudioView`.

```ts
import { StudioView } from './views/StudioView'
```

- [x] Change workspace index redirect.

```tsx
<Route index element={<Navigate to="studio" replace />} />
```

- [x] Add route before `plan`.

```tsx
<Route path="studio" element={<StudioView />} />
```

- [x] Verify typecheck.

### Task T013: Expose Studio In Workspace Shell Navigation

**Responsible file:** `frontend/src/components/WorkspaceShell.tsx`

**Dependencies:** T001, T012

- [x] Add `MonitorUp` to the lucide import.

```ts
import { LayoutList, BookOpen, Search, Sparkles, Lightbulb, Scroll, Zap, MonitorUp } from 'lucide-react'
```

- [x] Add nav item before Writing.

```ts
{ key: 'studio', label: 'Studio', icon: MonitorUp, gradient: 'from-slate-700 to-slate-900', glow: 'glow-studio', stage: 'writing' },
```

- [x] Do not change `handleNavClick`.

- [x] Verify typecheck.

### Task T014: Update WorkspaceShell Tests For Studio Nav

**Responsible file:** `frontend/src/components/WorkspaceShell.test.tsx`

**Dependencies:** T013

- [x] Update the writing-stage test to expect two nav buttons.

```ts
expect(buttons).toHaveLength(2);
expect(screen.getByText('Studio')).toBeInTheDocument();
expect(screen.getByText('Writing')).toBeInTheDocument();
```

- [x] Add this test.

```ts
it('renders Studio and Writing when mode is studio', () => {
  renderShell('studio');

  const buttons = screen.getAllByRole('button', { hidden: false }).filter(
    (btn) => btn.classList.contains('nav-item'),
  );
  expect(buttons).toHaveLength(2);
  expect(screen.getByText('Studio')).toBeInTheDocument();
  expect(screen.getByText('Writing')).toBeInTheDocument();
});
```

- [x] Run focused test.

```powershell
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
```

Expected: pass.

### Task T015: Add StudioView Integration Test

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

**Dependencies:** T012

- [x] Create route test using existing test utilities and MSW.

Minimum assertions:

- Rendering `/workspace/proj-1/studio` shows `Studio Desk`.
- Studio commands navigation exists.
- Studio project map navigation exists.
- Clicking `Generate` opens the generation panel.
- Clicking `Characters` opens the characters panel and shows `0 profiles` when `/v1/story-development/characters` returns no items.

- [x] Use only existing API endpoint mocks:

```ts
http.get('/v1/story-development/drafting/manuscript-documents', () => HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }))
http.get('/v1/story-development/drafting/draft-artifacts', () => HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }))
http.get('/v1/story-development/drafting/revision-suggestions', () => HttpResponse.json({ project_id: 'proj-1', items: [], meta: {} }))
http.get('/v1/story-development/characters', () => HttpResponse.json({ items: [] }))
http.get('/v1/story-development/world-bible', () => HttpResponse.json({ items: [] }))
http.get('/v1/story-generation/runs', () => HttpResponse.json([]))
http.get('/v1/jobs', () => HttpResponse.json([]))
```

- [x] Run focused test.

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: pass.

## Final Verification

Run after all tasks:

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test
```

Expected:

- lint exits 0
- typecheck exits 0
- build exits 0
- test exits 0

## Stage 1 Pass Criteria

Stage 1 is complete only when all of these are true:

- `/workspace/:projectId/studio` renders the Studio shell.
- Workspace index redirects to Studio.
- Existing workspace routes remain available and unchanged.
- Studio command bar opens Ideas, Generation, Review, Inspect, Notes, and Jobs panels.
- Studio project rail opens Characters, World Bible, Relationships, Canon/Generation, Jobs, and Notes panels.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- WorkspaceShell
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Do not proceed to Stage 2 until these pass and the final verification commands above exit 0.

## Serial Follow-Up Stages

Implement these only after Stage 1 passes final verification:

1. Stage 2: `docs/superpowers/plans/2026-05-16-studio-desk-stage-2-suggestions.md`
2. Stage 3: `docs/superpowers/plans/2026-05-16-studio-desk-stage-3-compact-panels.md`
3. Stage 4: `docs/superpowers/plans/2026-05-16-studio-desk-stage-4-canon-annotations.md`
4. Stage 5: `docs/superpowers/plans/2026-05-16-studio-desk-stage-5-responsive-drawers.md`
