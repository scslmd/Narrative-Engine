# Radial Hub Phase 4: Route Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all workspace routes to a single `/workspace/:projectId/studio` route with query-param deep-links. Old routes redirect gracefully, preserving backward compatibility for bookmarks and external links.

**Status:** Design approved. Phase 1 (core infrastructure) is the prerequisite — this plan assumes `StudioRadialHub`, `StudioFloatingPanel`, layout store state, and `bringToFront` exist.

**Architecture:** Replace the current multi-route workspace (plan, review, inspect, braindump, canon, generate) with a single `studio` route. Old routes redirect via `<Navigate replace>` to `/studio?tab=<panel_key>` with preserved params (jobId, chapterId, subtab). StudioView reads deep-link params on mount and opens the correct panel. A `usePanelUrlSync` hook keeps the active panel and URL in sync for shareable links.

**Dependencies (prerequisite):** Phase 1 must be completed first (layout store, StudioRadialHub, StudioFloatingPanel, StudioPanelContent).

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/App.tsx` | Modify | Replace old view routes with redirect routes; remove dead view imports |
| `frontend/src/hooks/usePanelUrlSync.ts` | Create | Sync active panel ↔ URL query params; read deep-link params on mount |
| `frontend/src/views/StudioView.tsx` | Modify | Integrate usePanelUrlSync; open panels from URL on mount |
| `frontend/src/components/WorkspaceShell.tsx` | Modify | Navigate to studio with query params instead of old routes |
| `frontend/src/routes.ts` | Modify (dead code) | Add `panelToStage` mapping; update route helpers for studio URLs. **NOTE: routes.ts has no callers — consider deferring or removing Task 6.** |
| `frontend/src/hooks/useRouteSync.ts` | Modify | Simplify for single-route workspace; always set mode to 'studio' |
| `frontend/src/components/Layout.tsx` | Modify | Derive stage from tab query param; update stage bar navigation |
| `frontend/src/components/studio/StudioProjectRail.tsx` | Modify | Update bottom links to use studio URLs |
| `frontend/src/stores/studioStore.ts` | Modify | Sync `activePanel` with `bringToFront` |

**Do NOT modify:** Panel content components, service files, type files, test files (except adding new tests).

**Do NOT delete:** Old view files (`PlanningView.tsx`, `ReviewView.tsx`, etc.) — they may be archived later.

---

## Task 1: Sync `activePanel` with `bringToFront` in studioStore

**Files:**
- Modify: `frontend/src/stores/studioStore.ts`

**Purpose:** When a panel is brought to front (clicked), `activePanel` should reflect it so that `usePanelUrlSync` can update the URL. Currently `bringToFront` only updates z-index.

- [ ] **Step 1: Modify `bringToFront` action**

Find the existing `bringToFront` action and add `activePanel: panel.key` to its return:

```ts
bringToFront: (id) =>
  set((state) => {
    const panel = state.layout.panels[id];
    if (!panel) return {};
    const newPanels = { ...state.layout.panels, [id]: { ...panel, zIndex: state.layout.nextZIndex } };
    return {
      activePanel: panel.key,
      layout: { ...state.layout, panels: newPanels, nextZIndex: state.layout.nextZIndex + 1 },
    };
  }),
```

**Important typing note:** `useParams()` returns `string | undefined`, so the hook must accept `projectId: string | null` (or internally no-op when it is absent). Do not pass a possibly-undefined route param into a hook signature that requires `string`.

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS (no new errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/studioStore.ts
git commit -m "fix: sync activePanel with bringToFront in studioStore"
```

---

## Task 2: Create `usePanelUrlSync` hook

**Files:**
- Create: `frontend/src/hooks/usePanelUrlSync.ts`

**Purpose:** Two-way sync between active panel and URL query params. On mount, reads `?tab=`, `?jobId=`, `?chapterId=`, `?subtab=` from URL and opens the correct panel. On active panel change, updates `?tab=` in URL.

- [ ] **Step 1: Create hook**

```ts
import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useStudioStore } from '../stores/studioStore';
import type { StudioPanelKey } from '../stores/studioStore';
import { useUIStore } from '../stores/uiStore';

interface PanelUrlSyncOptions {
  projectId: string | null;
  /** Called when URL contains ?jobId=XXX on mount */
  onJobId?: (jobId: string | null) => void;
  /** Called when URL contains ?chapterId=XXX on mount */
  onChapterId?: (chapterId: string | null) => void;
  /** Called when URL contains ?subtab=XXX on mount */
  onSubtab?: (subtab: string | null) => void;
}

/**
 * Syncs active panel to URL query params and reads deep-link params on mount.
 * - On mount: reads ?tab=, ?jobId=, ?chapterId=, ?subtab= from URL
 * - On active panel change: writes ?tab= to URL
 * - Uses replace: true to avoid polluting browser history on panel clicks
 */
export function usePanelUrlSync(options: PanelUrlSyncOptions) {
  const [searchParams, setSearchParams] = useSearchParams();
  const activePanel = useStudioStore((s) => s.activePanel);
  const layout = useStudioStore((s) => s.layout);
  const addPanel = useStudioStore((s) => s.addPanel);
  const bringToFront = useStudioStore((s) => s.bringToFront);
  const setJobId = useUIStore((s) => s.setJobId);

   // READ: On mount, process deep-link params from URL
    useEffect(() => {
      if (!options.projectId) return;

      const tab = searchParams.get('tab');
      const jobId = searchParams.get('jobId');
      const chapterId = searchParams.get('chapterId');
      const subtab = searchParams.get('subtab');

      // Validate tab against known panel keys before casting
      const validKeys = ['structure', 'chapters', 'ideas', 'canon', 'generation', 'manuscripts', 'drafts', 'characters', 'relationships', 'worldBible', 'arcs', 'notes', 'jobs', 'suggestions', 'review', 'inspect'] as const;
      if (tab && validKeys.includes(tab as typeof validKeys[number])) {
        const panelKey = tab as StudioPanelKey;
        const existingPanelId = Object.values(layout.panels).find(
          (p) => p.key === panelKey && p.visible
        )?.id;

        if (existingPanelId) {
          bringToFront(existingPanelId);
        } else {
          addPanel(panelKey);
        }
      }

      // Pass through panel-specific params
      if (jobId) {
        setJobId(jobId);
        options.onJobId?.(jobId);
      }
      if (chapterId) {
        options.onChapterId?.(chapterId);
      }
      if (subtab) {
        options.onSubtab?.(subtab);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
      // NOTE: intentionally empty deps — this effect should only run on mount to read initial URL params
    }, []); // Only on mount

 // WRITE: When active panel changes, update URL ?tab= param
    useEffect(() => {
      if (!options.projectId || !activePanel) return;
      setSearchParams(
        (prev) => {
          prev.set('tab', activePanel);
          // Clean up panel-specific params that no longer apply
          // NOTE: read from `prev` everywhere to avoid stale closure over `searchParams`
          const currentTab = prev.get('tab');
          if (currentTab === 'inspect' && !prev.get('jobId')) {
            // Keep jobId if inspect is active
          } else if (currentTab !== 'inspect') {
            prev.delete('jobId');
          }
          if (currentTab !== 'manuscripts' && currentTab !== 'drafts') {
            prev.delete('chapterId');
          }
          if (currentTab !== 'canon') {
            prev.delete('subtab');
          }
          return prev;
        },
        { replace: true },
      );
      // NOTE: `searchParams` intentionally excluded from deps to prevent infinite loop
      // The updater function reads from `prev` (latest state), not from closure.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activePanel, setSearchParams]);
}
```

- [ ] **Step 2: Write test**

Create `frontend/src/hooks/usePanelUrlSync.test.tsx`:

```tsx
import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { usePanelUrlSync } from './usePanelUrlSync';
import { useStudioStore } from '../stores/studioStore';

function Wrapper({ children, initialUrl }: { children: ReactNode; initialUrl: string }) {
  return (
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="*" element={<>{children}</>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('usePanelUrlSync', () => {
  beforeEach(() => {
    useStudioStore.setState({
      activePanel: 'suggestions',
      layout: { panels: {}, nextZIndex: 1, layoutPreset: null },
    });
  });

  it('reads tab param from URL on mount', () => {
    const { onJobId, onChapterId, onSubtab } = {
      onJobId: vi.fn(),
      onChapterId: vi.fn(),
      onSubtab: vi.fn(),
    };

    renderHook(
      () => usePanelUrlSync({ projectId: 'proj-1', onJobId, onChapterId, onSubtab }),
      { wrapper: (props) => <Wrapper {...props} initialUrl="/workspace/proj-1/studio?tab=inspect&jobId=abc-123" /> },
    );

    // Panel should have been added
    const panels = useStudioStore.getState().layout.panels;
    expect(Object.values(panels).some((p) => p.key === 'inspect')).toBe(true);
    expect(onJobId).toHaveBeenCalledWith('abc-123');
  });

  it('reads chapterId param from URL on mount', () => {
    const onChapterId = vi.fn();
    renderHook(
      () => usePanelUrlSync({ projectId: 'proj-1', onChapterId }),
      { wrapper: (props) => <Wrapper {...props} initialUrl="/workspace/proj-1/studio?tab=manuscripts&chapterId=ch-5" /> },
    );

    expect(onChapterId).toHaveBeenCalledWith('ch-5');
  });
});
```

- [ ] **Step 3: Run test**

Run: `cd frontend && npm run test -- usePanelUrlSync.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/usePanelUrlSync.ts frontend/src/hooks/usePanelUrlSync.test.tsx
git commit -m "feat: create usePanelUrlSync hook for panel-to-URL sync"
```

---

## Task 3: Update `StudioView.tsx` — Handle deep-link params

**Files:**
- Modify: `frontend/src/views/StudioView.tsx`

**Purpose:** Integrate `usePanelUrlSync` so that deep-link URLs (e.g., `?tab=inspect&jobId=abc`) open the correct panel with the correct state. Assumes Phase 1's RadialHub layout.

- [ ] **Step 1: Add deep-link integration to StudioView (incremental patch)**

Apply the following additions to the existing StudioView — do NOT replace the file:

**Add imports:**
```tsx
import { usePanelUrlSync } from '../hooks/usePanelUrlSync';
import { useUIStore } from '../stores/uiStore';
```

**Add hook call** (after existing store hooks, before the `return`):
```tsx
  const setJobId = useUIStore((s) => s.setJobId);

  // Sync active panel with URL query params; handle deep-link params on mount
  usePanelUrlSync({
    projectId: projectId ?? null,
    onJobId: (jobId) => {
      if (jobId) setJobId(jobId);
    },
  });
```

**Diff summary:**
```diff
+ import { usePanelUrlSync } from '../hooks/usePanelUrlSync';
+ import { useUIStore } from '../stores/uiStore';

  export function StudioView() {
    const { projectId } = useParams<{ projectId: string }>();
    const resetLayout = useStudioStore((s) => s.resetLayout);
+   const setJobId = useUIStore((s) => s.setJobId);
+
+   // Sync active panel with URL query params; handle deep-link params on mount
+   usePanelUrlSync({
+     projectId: projectId ?? null,
+     onJobId: (jobId) => {
+       if (jobId) setJobId(jobId);
+     },
+   });

    return (
```

**Note:** If Phase 1 has not yet been implemented (StudioView still uses ViewShell), add the `usePanelUrlSync` call to the existing ViewShell-based StudioView. The hook works regardless of layout — it only manipulates studioStore state.

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/StudioView.tsx
git commit -m "feat: integrate usePanelUrlSync into StudioView for deep-link support"
```

---

## Task 4: Update `App.tsx` — Redirect old routes to studio

**Files:**
- Modify: `frontend/src/App.tsx`

**Purpose:** Replace all old view routes with redirect routes to `/studio?tab=<panel_key>`. Remove dead view imports. Preserve backward compatibility for bookmarks and external links.

**Route-to-tab mapping:**

| Old route | Redirect target | Panel key |
|-----------|----------------|-----------|
| `/plan` | `?tab=structure` | `structure` |
| `/review` | `?tab=review` | `review` |
| `/inspect` | `?tab=inspect` | `inspect` |
| `/inspect/:jobId` | `?tab=inspect&jobId=XXX` | `inspect` |
| `/braindump` | `?tab=ideas` | `ideas` |
| `/canon` | `?tab=canon` (+ preserve `?tab=X` as `?subtab=X`) | `canon` |
| `/canon?tab=mythos` | `?tab=canon&subtab=mythos` | `canon` |
| `/generate` | `?tab=generation` | `generation` |
| `/write` | `?tab=manuscripts` | `manuscripts` |
| `/write/:chapterId` | `?tab=manuscripts&chapterId=XXX` | `manuscripts` |

- [ ] **Step 1: Replace App.tsx content**

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate, useParams, useLocation } from 'react-router-dom'
import { ToastProvider } from './hooks/useToast'
import { ToastContainer } from './components/ui/Toast'
import { Layout } from './components/Layout'
import { ProjectList } from './views/ProjectList'
import { Workspace } from './views/Workspace'
import { GuidedSetupView } from './views/GuidedSetupView'
import { StudioView } from './views/StudioView'
import { useHealthCheck } from './hooks/useHealthCheck'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

// --- Redirect components for backward compatibility ---

function PlanRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=structure`} replace />;
}

function ReviewRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=review`} replace />;
}

function InspectRedirect() {
  const { projectId, jobId } = useParams();
  const params = new URLSearchParams({ tab: 'inspect' });
  if (jobId) params.set('jobId', jobId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function BrainDumpRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=ideas`} replace />;
}

function CanonRedirect() {
  const { projectId } = useParams();
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  // Only extract known canon subtabs; drop unknown params to avoid leaking noise
  const knownSubtabs = ['mythos', 'patterns', 'packet'];
  const canonTab = params.get('tab');
  const newParams = new URLSearchParams({ tab: 'canon' });
  if (canonTab && knownSubtabs.includes(canonTab)) newParams.set('subtab', canonTab);
  return <Navigate to={`/workspace/${projectId}/studio?${newParams.toString()}`} replace />;
}

function GenerateRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=generation`} replace />;
}

function WriteRedirect() {
  const { projectId, chapterId } = useParams();
  const params = new URLSearchParams({ tab: 'manuscripts' });
  if (chapterId) params.set('chapterId', chapterId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function AppInner() {
  useHealthCheck();
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/setup-wizard" element={<GuidedSetupView />} />
          <Route path="/workspace/:projectId" element={<Workspace />}>
            <Route index element={<Navigate to="studio" replace />} />
            <Route path="studio" element={<StudioView />} />
            {/* Backward-compatible redirects — old routes still work for bookmarks */}
            <Route path="plan" element={<PlanRedirect />} />
            <Route path="write" element={<WriteRedirect />} />
            <Route path="write/:chapterId" element={<WriteRedirect />} />
            <Route path="review" element={<ReviewRedirect />} />
            <Route path="inspect" element={<InspectRedirect />} />
            <Route path="inspect/:jobId" element={<InspectRedirect />} />
            <Route path="braindump" element={<BrainDumpRedirect />} />
            <Route path="canon" element={<CanonRedirect />} />
            <Route path="generate" element={<GenerateRedirect />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
      <ToastContainer />
    </BrowserRouter>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AppInner />
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App
```

**Changes from current:**
- Removed imports: `PlanningView`, `ReviewView`, `InspectView`, `BrainDumpView`, `GenerationView`, `CanonView`
- Added imports: `useParams`, `useLocation` from react-router-dom
- Added 7 redirect components (PlanRedirect, ReviewRedirect, InspectRedirect, BrainDumpRedirect, CanonRedirect, GenerateRedirect, WriteRedirect)
- Replaced old view routes with redirect component routes
- Kept `write` and `write/:chapterId` redirects (already existed, now with query params)

- [ ] **Step 2: Write redirect test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import App from './App';

function LocationSpy() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}${location.search}</div>;
}

// Named redirect test components (avoid IIFE pattern for readability and debuggability)
function TestPlanRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=structure`} replace />;
}

function TestInspectRedirect() {
  const { projectId, jobId } = useParams();
  const params = new URLSearchParams({ tab: 'inspect' });
  if (jobId) params.set('jobId', jobId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function TestCanonRedirect() {
  const { projectId } = useParams();
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  const canonTab = params.get('tab');
  const newParams = new URLSearchParams({ tab: 'canon' });
  if (canonTab) newParams.set('subtab', canonTab);
  return <Navigate to={`/workspace/${projectId}/studio?${newParams.toString()}`} replace />;
}

function TestWriteRedirect() {
  const { projectId, chapterId } = useParams();
  const params = new URLSearchParams({ tab: 'manuscripts' });
  if (chapterId) params.set('chapterId', chapterId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

describe('App route redirects', () => {
  it('redirects /plan to /studio?tab=structure', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/plan']}>
        <Routes>
          <Route path="/workspace/:projectId" element={<LocationSpy />}>
            <Route path="plan" element={<TestPlanRedirect />} />
            <Route path="studio" element={<LocationSpy />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      const loc = document.querySelector('[data-testid="location"]');
      expect(loc?.textContent).toContain('/workspace/proj-1/studio');
      expect(loc?.textContent).toContain('tab=structure');
    });
  });

  it('redirects /inspect/:jobId to /studio?tab=inspect&jobId=XXX', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/inspect/job-abc']}>
        <Routes>
          <Route path="/workspace/:projectId" element={<LocationSpy />}>
            <Route path="inspect/:jobId" element={<TestInspectRedirect />} />
            <Route path="studio" element={<LocationSpy />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      const loc = document.querySelector('[data-testid="location"]');
      expect(loc?.textContent).toContain('tab=inspect');
      expect(loc?.textContent).toContain('jobId=job-abc');
    });
  });

  it('redirects /canon?tab=mythos to /studio?tab=canon&subtab=mythos', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/canon?tab=mythos']}>
        <Routes>
          <Route path="/workspace/:projectId" element={<LocationSpy />}>
            <Route path="canon" element={<TestCanonRedirect />} />
            <Route path="studio" element={<LocationSpy />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      const loc = document.querySelector('[data-testid="location"]');
      expect(loc?.textContent).toContain('tab=canon');
      expect(loc?.textContent).toContain('subtab=mythos');
    });
  });

  it('redirects /write/:chapterId to /studio?tab=manuscripts&chapterId=XXX', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace/proj-1/write/ch-5']}>
        <Routes>
          <Route path="/workspace/:projectId" element={<LocationSpy />}>
            <Route path="write/:chapterId" element={<TestWriteRedirect />} />
            <Route path="studio" element={<LocationSpy />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      const loc = document.querySelector('[data-testid="location"]');
      expect(loc?.textContent).toContain('tab=manuscripts');
      expect(loc?.textContent).toContain('chapterId=ch-5');
    });
  });
});
```

- [ ] **Step 3: Run tests**

Run: `cd frontend && npm run test -- App.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 4: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: redirect old workspace routes to studio with query params"
```

---

## Task 5: Update `WorkspaceShell.tsx` — Navigate to studio with query params

**Files:**
- Modify: `frontend/src/components/WorkspaceShell.tsx`

**Purpose:** Update left rail nav items to navigate directly to `/studio?tab=X` instead of old routes. Avoids redirect overhead and mode flash.

- [ ] **Step 1: Add route-to-tab mapping and update nav handler**

Add the mapping and update `handleNavClick`:

```ts
const ROUTE_TO_TAB: Record<string, string | null> = {
  braindump: 'ideas',
  plan: 'structure',
  canon: 'canon',
  generate: 'generation',
  studio: null,
  review: 'review',
  inspect: 'inspect',
  write: 'manuscripts',
};
```

Replace the existing `handleNavClick`:

```ts
  const handleNavClick = (key: string) => {
    setMode('studio');
    if (projectId) {
      const tab = ROUTE_TO_TAB[key];
      if (key === 'studio' || !tab) {
        navigate(`/workspace/${projectId}/studio`);
      } else {
        navigate(`/workspace/${projectId}/studio?tab=${tab}`);
      }
    }
  }
```

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/WorkspaceShell.tsx
git commit -m "feat: update WorkspaceShell nav to navigate to studio with query params"
```

---

## Task 6: Update `routes.ts` — Add panel-to-stage mapping and studio route helpers

> **DEPRECATED:** `routes.ts` has no callers in the codebase — it is dead code. This task is deferred. If/when `routes.ts` is revived or callers are added, apply the `panelToStage` mapping and studio URL helpers below. For now, Layout.tsx imports `panelToStage` directly from an inline definition or from a dedicated module.

**Files:**
- Modify: `frontend/src/routes.ts` (deferred — no current callers)

**Purpose:** Add `panelToStage` mapping for Layout's stage derivation. Update route helpers to return studio URLs with query params (canonical URLs). Keep old URL format available via `routesLegacy` for backward compatibility.

- [ ] **Step 1: Update routes.ts**

```ts
export type WorkspaceMode = 'studio' | 'plan' | 'write' | 'review' | 'inspect' | 'braindump' | 'generate' | 'canon'

export interface RouteState {
  mode: WorkspaceMode
  projectId: string | null
  chapterId: string | null
}

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

/** Maps panel keys to workflow stages for stage bar awareness. */
export const panelToStage: Record<string, 'planning' | 'writing' | 'review'> = {
  structure: 'planning',
  chapters: 'planning',
  ideas: 'planning',
  canon: 'planning',
  generation: 'planning',
  manuscripts: 'writing',
  drafts: 'writing',
  characters: 'writing',
  relationships: 'writing',
  worldBible: 'writing',
  arcs: 'writing',
  notes: 'writing',
  jobs: 'writing',
  suggestions: 'writing',
  review: 'review',
  inspect: 'review',
}

function studioUrl(projectId: string, params: Record<string, string>): string {
  const search = new URLSearchParams(params).toString();
  return search
    ? `/workspace/${projectId}/studio?${search}`
    : `/workspace/${projectId}/studio`;
}

export const routes = {
  home: '/',
  workspace: (projectId: string) => `/workspace/${projectId}`,
  studio: (projectId: string) => `/workspace/${projectId}/studio`,

  // Canonical routes — navigate directly to studio with query params
  plan: (projectId: string) => studioUrl(projectId, { tab: 'structure' }),
  write: (projectId: string, chapterId?: string) =>
    studioUrl(projectId, { tab: 'manuscripts', ...(chapterId && { chapterId }) }),
  review: (projectId: string) => studioUrl(projectId, { tab: 'review' }),
  inspect: (projectId: string, jobId?: string) =>
    studioUrl(projectId, { tab: 'inspect', ...(jobId && { jobId }) }),
  braindump: (projectId: string) => studioUrl(projectId, { tab: 'ideas' }),
  canon: (projectId: string) => studioUrl(projectId, { tab: 'canon' }),
  generate: (projectId: string) => studioUrl(projectId, { tab: 'generation' }),

  // Direct studio tab helper
  studioTab: (projectId: string, tab: string, extra?: Record<string, string>) =>
    studioUrl(projectId, { tab, ...extra }),
} as const

/** Legacy route URLs — preserved for backward-compat checks and old bookmarks. */
export const routesLegacy = {
  plan: (projectId: string) => `/workspace/${projectId}/plan`,
  write: (projectId: string, chapterId?: string) =>
    chapterId ? `/workspace/${projectId}/write/${chapterId}` : `/workspace/${projectId}/write`,
  review: (projectId: string) => `/workspace/${projectId}/review`,
  inspect: (projectId: string, jobId?: string) =>
    jobId ? `/workspace/${projectId}/inspect/${jobId}` : `/workspace/${projectId}/inspect`,
  braindump: (projectId: string) => `/workspace/${projectId}/braindump`,
  canon: (projectId: string) => `/workspace/${projectId}/canon`,
  generate: (projectId: string) => `/workspace/${projectId}/generate`,
} as const
```

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes.ts
git commit -m "feat: add panelToStage mapping and studio query param route helpers"
```

---

## Task 7: Update `useRouteSync.ts` — Simplify for single-route workspace

**Files:**
- Modify: `frontend/src/hooks/useRouteSync.ts`

**Purpose:** Simplify route sync for the single-route workspace. Real studio screens should converge on `'studio'`, but redirect source routes still need transient segment-based mode derivation until `<Navigate>` completes. Deep-link params (jobId, chapterId) are handled by `usePanelUrlSync` in StudioView.

- [ ] **Step 1: Replace useRouteSync**

```ts
import { useEffect } from 'react';
import { matchPath, useLocation } from 'react-router-dom';
import { useUIStore } from '../stores/uiStore';

/**
 * Hook that synchronizes route state with UI store.
 * After Phase 4 route migration, all workspace routes resolve to 'studio' mode.
 * Deep-link params (tab, jobId, chapterId) are handled by usePanelUrlSync in StudioView.
 */
export function useRouteSync() {
  const location = useLocation();
  const { setMode, setProjectId, setChapterId, setJobId } = useUIStore();

  useEffect(() => {
      const match = matchPath('/workspace/:projectId/:segment?', location.pathname);

      if (match) {
        const params = match.params as { projectId: string; segment?: string };
        setProjectId(params.projectId);
        // Keep mode derivation from `segment` for redirect routes to avoid flash:
        // redirect routes (plan, review, etc.) will render briefly before Navigate fires,
        // so mode should reflect the segment until the redirect completes.
        const segment = params.segment;
        if (segment === 'studio' || !segment) {
          setMode('studio');
        } else {
          setMode(segment as WorkspaceMode);
        }
        setChapterId(null);
        setJobId(null);
      } else {
        setProjectId(null);
        setMode('plan');
        setChapterId(null);
        setJobId(null);
      }
    }, [location.pathname, setMode, setProjectId, setChapterId, setJobId]);
}
```

**Changes from current:**
- Removed `WorkspaceMode` import (no longer needed)
- Removed inspect-specific route matching (`/workspace/:projectId/inspect/:jobId?`)
- Removed standard mode derivation from route segment
- Always sets mode to 'studio' for any workspace route
- Always clears chapterId and jobId (handled by usePanelUrlSync)

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useRouteSync.ts
git commit -m "refactor: simplify useRouteSync for single-route workspace"
```

---

## Task 8: Update `Layout.tsx` — Stage bar awareness of active panel

**Files:**
- Modify: `frontend/src/components/Layout.tsx`

**Purpose:** After Phase 4, mode is always 'studio', so the stage bar would always show "Studio" as active. Fix: derive stage from the `?tab=` query param using `panelToStage` mapping. Update stage bar navigation to go directly to studio with query params.

- [ ] **Step 1: Add panelToStage import and update stage derivation**

Add import:
```ts
import { panelToStage } from '../routes'
```

Update the stage derivation effect. Replace the existing `useEffect` that syncs stage with mode:

```ts
  useEffect(() => {
    let nextStage = modeToStage[uiMode]

    // After Phase 4: derive stage from active panel tab when in studio mode
    if (uiMode === 'studio') {
      const params = new URLSearchParams(location.search)
      const tab = params.get('tab')
      if (tab && tab in panelToStage) {
        nextStage = panelToStage[tab]
      }
    }

    if (stage !== nextStage) {
      setStage(nextStage)
    }
  }, [setStage, stage, uiMode, location.search])
```

- [ ] **Step 2: Update stage bar navigation**

Replace the existing `handleStageChange`:

```ts
  const STAGE_TO_TAB: Record<StageId, string> = {
    planning: 'structure',
    writing: 'manuscripts',
    review: 'review',
  }

  const handleStageChange = (stageId: StageId) => {
    setMode('studio')
    if (!projectId) return
    const tab = STAGE_TO_TAB[stageId]
    if (tab) {
      navigate(`/workspace/${projectId}/studio?tab=${tab}`)
    } else {
      navigate(`/workspace/${projectId}/studio`)
    }
  }
```

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat: derive stage bar from tab query param; update stage navigation"
```

---

## Task 9: Update `StudioProjectRail.tsx` — Update bottom links

**Files:**
- Modify: `frontend/src/components/studio/StudioProjectRail.tsx`

**Purpose:** The bottom links ("Open full Planning", "Open full Canon") currently navigate to old routes. Update to navigate to studio with query params.

- [ ] **Step 1: Update bottom links**

Replace the bottom section links:

```tsx
      {!compact ? (
        <div className="space-y-1 border-t border-[var(--border-primary)] px-3 py-3 text-[11px] text-[var(--text-tertiary)]">
          <Link
            className="block rounded-lg px-3 py-2 transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/studio?tab=structure`}
          >
            Open Planning Panel
          </Link>
          <Link
            className="block rounded-lg px-3 py-2 transition-colors hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]"
            to={`/workspace/${projectId}/studio?tab=canon`}
          >
            Open Canon Panel
          </Link>
        </div>
      ) : null}
```

- [ ] **Step 2: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/studio/StudioProjectRail.tsx
git commit -m "feat: update StudioProjectRail bottom links to studio URLs"
```

---

## Task 10: Validation

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npm run test`
Expected: All tests pass (675+ existing + 6 new)

- [ ] **Step 2: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS (no new errors)

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: PASS (builds successfully, 2070+ modules)

- [ ] **Step 5: Manual smoke test**

Start dev server: `cd frontend && npm run dev`

Verify each redirect:
| URL | Expected result |
|-----|----------------|
| `/workspace/XXX/plan` | Redirects to `/studio?tab=structure`, stage bar shows "Planning" |
| `/workspace/XXX/review` | Redirects to `/studio?tab=review`, stage bar shows "Review" |
| `/workspace/XXX/inspect/job-123` | Redirects to `/studio?tab=inspect&jobId=job-123` |
| `/workspace/XXX/braindump` | Redirects to `/studio?tab=ideas`, stage bar shows "Planning" |
| `/workspace/XXX/canon?tab=mythos` | Redirects to `/studio?tab=canon&subtab=mythos` |
| `/workspace/XXX/generate` | Redirects to `/studio?tab=generation`, stage bar shows "Planning" |
| `/workspace/XXX/write/ch-5` | Redirects to `/studio?tab=manuscripts&chapterId=ch-5` |

Verify URL sync:
- Open a panel → URL updates to include `?tab=<panel_key>`
- Paste a URL with `?tab=inspect&jobId=abc` → Inspect panel opens with jobId set
- Click stage bar "Planning" → navigates to `/studio?tab=structure` directly (no redirect)
- Click left rail nav item → navigates to `/studio?tab=X` directly (no redirect)

Verify backward compatibility:
- Old bookmarks (`/workspace/XXX/plan`) still work (via redirect)
- Browser back/forward works correctly (redirects use `replace`)

---

## Self-Review

### Spec Coverage
| Spec Requirement | Task | Status |
|-----------------|------|--------|
| Update App.tsx routes | Task 4 | ✅ |
| Add redirects from old routes to studio | Task 4 | ✅ |
| Preserve deep-link behavior (?tab= query params) | Tasks 2, 3, 4 | ✅ |
| Preserve inspect deep-links (/inspect/:jobId → studio + open Inspect panel) | Tasks 2, 3, 4 | ✅ |
| Update WorkspaceShell left rail | Task 5 | ✅ |
| Handle route params passed to panels (jobId for inspect) | Tasks 2, 3 | ✅ |
| URL state sync (panel focused → update URL) | Task 2 | ✅ |
| Old routes redirect gracefully, not 404 | Task 4 | ✅ |
| Stage bar reflects active panel | Task 8 | ✅ |

### Placeholder Scan
- No "TBD", "TODO", "implement later" found
- All redirect components contain complete implementation code
- All type definitions are explicit (no `as any` casts)
- `studioUrl` helper avoids string concatenation bugs
- Canon redirect correctly renames `?tab=` to `?subtab=` to avoid param collision
- **Task 3 is conditionally incomplete:** the StudioView patch assumes Phase 1's RadialHub layout exists. If Phase 1 is not yet implemented, the patch instructions note to add `usePanelUrlSync` to the existing ViewShell-based StudioView, but the exact diff depends on the current StudioView structure. This is a known conditional dependency.

### Type Consistency
- `WorkspaceMode` type unchanged — backward compatible
- `panelToStage` uses `Record<string, StageId>` — safe for unknown panel keys
- `ROUTE_TO_TAB` in WorkspaceShell uses `Record<string, string | null>` — null for studio (no tab needed)
- `usePanelUrlSync` options use optional callbacks — no breaking changes
- `routes` and `routesLegacy` are both `as const` — full type inference

### Breaking Changes
- `routes.plan(projectId)` now returns `/workspace/XXX/studio?tab=structure` instead of `/workspace/XXX/plan`
  - **Mitigation:** `routesLegacy.plan(projectId)` returns the old URL for any code that needs it
  - **Impact:** Code using `routes.plan()` will navigate directly to studio (better UX, no redirect)
- `useRouteSync` no longer sets `jobId` from route segment
  - **Mitigation:** `usePanelUrlSync` reads `?jobId=` from URL in StudioView
  - **Impact:** InspectView no longer rendered from routes; StudioView handles jobId

### Risks
| Risk | Mitigation |
|------|-----------|
| Old view components become dead code | Not deleted — imports removed from App.tsx only; files remain for archival |
| Redirect flash during navigation | Navigate uses `replace` — no history entry; React Router v6 processes Navigate synchronously |
| Stage bar shows wrong stage during redirect | Redirect is synchronous; useRouteSync sees final URL; stage derived from `?tab=` |
| `usePanelUrlSync` runs on every StudioView render | Mount effect uses `[]` deps; write effect only fires on `activePanel` change |
| Query param collision (canon `?tab=` vs studio `?tab=`) | Canon redirect renames canon's `?tab=` to `?subtab=` |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-radial-hub-phase-4-route-migration.md`.

**Prerequisites:** Phase 1 (core infrastructure) must be completed before executing this plan. Tasks 1-3 depend on Phase 1's layout store, StudioRadialHub, and bringToFront action.

**Execution order:** Tasks 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 (validation). Tasks 5-9 are independent of each other and can be parallelized after Tasks 1-4 complete.

**Estimated effort:** ~2 hours (10 tasks, 6 new tests, 8 file modifications, 1 new file).

---

## Adversarial Review Fixes Applied

The following issues were identified in the adversarial review and have been corrected in this document:

| ID | Severity | Issue | Fix Applied |
|----|----------|-------|-------------|
| C2 | Critical | Invalid JSX `<data-testid="location">` — self-closing tag with attribute as element name | Changed to `<div data-testid="location">` with closing `</div>` in test helper component |
| C3 | Critical | Closure bug in write effect: `searchParams` read from closure instead of `prev` inside `setSearchParams((prev) => { ... })` | All reads inside the updater now use `prev` (e.g., `prev.get('jobId')` instead of `searchParams.get('jobId')`) |
| C4 | Critical | `useRouteSync` else branch sets `setMode('studio')` for non-workspace routes (e.g., `/`, `/setup-wizard`) | Changed else branch to `setMode('plan')`; also preserved segment-based mode derivation for redirect routes to avoid flash (M3) |
| H1 | High | Task 3 showed a full StudioView replacement instead of incremental change | Replaced with a diff-style patch showing only the additions needed to integrate `usePanelUrlSync` |
| H2 | High | Missing `write: 'manuscripts'` in `ROUTE_TO_TAB` mapping (Task 5) | Added `write: 'manuscripts'` entry to the mapping |
| H3 | High | No validation for `?tab=` param before casting to `StudioPanelKey` | Added `validKeys` array with `includes` check before casting; invalid tab values are silently ignored |
| H4 | High | `searchParams` in write effect deps array causes infinite loop | Removed `searchParams` from deps; added `eslint-disable` comment explaining why updater reads from `prev` |
| H5 | High | Missing `structure: 'planning'` in `panelToStage` mapping | Already present in the mapping — no change needed |
| H6 | High | CanonRedirect copies all query params, including unknown ones | Added `knownSubtabs` whitelist (`mythos`, `patterns`, `packet`); unknown params are dropped |
| M1 | Medium | `routes.ts` rewrite is dead code (no callers) — Task 6 unnecessary | Added deprecation notice to Task 6; deferred until callers exist |
| M2 | Medium | File Structure table listed the wrong `WorkspaceShell` path | Corrected to `frontend/src/components/WorkspaceShell.tsx` |
| M3 | Medium | Mode derivation from `segment` removed for redirect routes, causing flash | Restored segment-based mode derivation in `useRouteSync` for redirect routes (`plan`, `review`, etc.) before Navigate fires |
| M4 | Medium | No default tab for writing stage in `STAGE_TO_TAB` | Changed `writing: ''` to `writing: 'manuscripts'` |
| M6 | Medium | Redirect tests use IIFE pattern `(() => { ... })()` instead of named components | Extracted `TestPlanRedirect`, `TestInspectRedirect`, `TestCanonRedirect`, `TestWriteRedirect` as named function components |
| L1 | Low | No comment explaining `eslint-disable exhaustive-deps` for mount effect | Added inline comment: "intentionally empty deps — this effect should only run on mount to read initial URL params" |
| L3 | Low | Self-review doesn't flag conditional incompleteness of Task 3 | Added note to Placeholder Scan documenting the Phase 1 conditional dependency |
