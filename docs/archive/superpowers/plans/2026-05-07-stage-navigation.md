# Stage-Based Navigation Implementation Plan

> Date: 2026-05-07  
> Status: Implemented  
> Evidence commits:
> - `4a271c5` (design/spec baseline)
> - `25648b9` (UI/UX modernization wave with stage navigation updates)
> - `d41ccef` (follow-up project-card/nav polish in same surface)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace duplicated header pill + sidebar navigation with stage-based header selector and context-filtered sidebar.

**Architecture:** Header shows 3 stage buttons (Planning / Writing / Review). Sidebar filters its nav items to show only modes belonging to the active stage. Stage derivation uses the existing `stageMap` from `Layout.tsx`. No new state — `activeStage` is computed from `useUIStore().mode`.

**Tech Stack:** React, TypeScript, Zustand (uiStore), Tailwind CSS, Vitest + Testing Library

---

## File Structure

| File | Change |
|------|--------|
| `frontend/src/components/WorkspaceShell.tsx` | Add `stage` property to nav items, add Canon + Generate entries, filter by active stage |
| `frontend/src/components/Layout.tsx` | Replace 7-mode pill group with 3-stage selector |
| `frontend/src/components/Layout.test.tsx` | Update mode nav test → stage nav test |
| `frontend/src/components/WorkspaceShell.test.tsx` | Create new test file for filtered sidebar |

---

### Task 1: Add stage property and missing entries to WorkspaceShell nav config

**Files:**
- Modify: `frontend/src/components/WorkspaceShell.tsx:11-25`

- [ ] **Step 1: Update the `NavItem` interface and `navItems` array**

Add a `stage` property to `NavItem`. Add `Canon` and `Generate` entries. Use `BookOpen` for Canon, `Sparkles` for Generate (matching existing icon conventions from `Layout.tsx`).

```ts
interface NavItem {
  key: string
  label: string
  icon: typeof LayoutList
  gradient: string
  glow: string
  stage: 'planning' | 'writing' | 'review'
}

const navItems: NavItem[] = [
  { key: 'braindump', label: 'Brain Dump', icon: Lightbulb, gradient: 'from-amber-500 to-amber-600', glow: 'glow-braindump', stage: 'planning' },
  { key: 'plan', label: 'Planning', icon: LayoutList, gradient: 'from-blue-500 to-blue-600', glow: 'glow-planning', stage: 'planning' },
  { key: 'canon', label: 'Canon', icon: BookOpen, gradient: 'from-indigo-500 to-indigo-600', glow: 'glow-canon', stage: 'planning' },
  { key: 'generate', label: 'Generate', icon: Sparkles, gradient: 'from-purple-500 to-purple-600', glow: 'glow-generate', stage: 'planning' },
  { key: 'write', label: 'Writing', icon: BookOpen, gradient: 'from-emerald-500 to-emerald-600', glow: 'glow-writing', stage: 'writing' },
  { key: 'review', label: 'Review', icon: Search, gradient: 'from-amber-500 to-amber-600', glow: 'glow-review', stage: 'review' },
  { key: 'inspect', label: 'Inspect', icon: Sparkles, gradient: 'from-violet-500 to-violet-600', glow: 'glow-inspect', stage: 'review' },
]
```

- [ ] **Step 2: Run typecheck to verify**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: PASS (no errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/WorkspaceShell.tsx
git commit -m "refactor: add stage property and Canon/Generate entries to sidebar nav config"
```

---

### Task 2: Filter sidebar by active stage in WorkspaceShell

**Files:**
- Modify: `frontend/src/components/WorkspaceShell.tsx:27-39`

- [ ] **Step 1: Add stage mapping and derive active stage**

Add a `modeToStage` map inside the component, compute `activeStage`, filter `navItems` before rendering.

After line 29 (`const navigate = useNavigate()`), add:

```ts
  const modeToStage: Record<string, 'planning' | 'writing' | 'review'> = {
    braindump: 'planning',
    plan: 'planning',
    canon: 'planning',
    generate: 'planning',
    write: 'writing',
    review: 'review',
    inspect: 'review',
  }

  const activeStage = modeToStage[mode] ?? 'planning'
  const visibleItems = navItems.filter(item => item.stage === activeStage)
```

- [ ] **Step 2: Change the map to iterate over `visibleItems` instead of `navItems`**

Replace line 45 (`{navItems.map((item) => {`) with:

```ts
          {visibleItems.map((item) => {
```

- [ ] **Step 3: Run typecheck and tests**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: PASS

Run: `cd frontend && cmd /c "npm run test -- --testPathPattern=Layout.test"`
Expected: PASS (existing Layout tests should still pass since they don't assert on sidebar item count)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/WorkspaceShell.tsx
git commit -m "feat: filter sidebar nav items by active stage"
```

---

### Task 3: Replace header pill group with 3-stage selector in Layout

**Files:**
- Modify: `frontend/src/components/Layout.tsx:109-131` (the `{isWorkspace && (` block that renders the mode pill group)

- [ ] **Step 1: Define stage config and replace the pill group**

The current code (lines ~109-131) renders a pill group using `modeIcons`, `modeLabels`, and `handleModeChange`. Replace it with a 3-stage selector.

Add after line 44 (after `modeLabels` definition):

```ts
const stages = [
  { key: 'planning' as const, label: 'Planning', defaultMode: 'plan' as WorkspaceMode },
  { key: 'writing' as const, label: 'Writing', defaultMode: 'write' as WorkspaceMode },
  { key: 'review' as const, label: 'Review', defaultMode: 'review' as WorkspaceMode },
]
```

Replace the header pill group (the `{isWorkspace && (` block starting around line 109) with:

```tsx
            {isWorkspace && (
              <div className="hidden sm:flex items-center rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)]/50">
                {stages.map((stage) => {
                  const isActive = stageMap[uiMode] === stage.key
                  return (
                    <button
                      key={stage.key}
                      onClick={() => handleModeChange(stage.defaultMode)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
                        isActive
                          ? 'text-[var(--text-primary)] bg-[var(--bg-elevated)] shadow-sm'
                          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                      }`}
                    >
                      {stage.label}
                    </button>
                  )
                })}
              </div>
            )}
```

- [ ] **Step 2: Remove unused imports**

The `modeIcons` object (lines 26-34) is no longer used in the header pill group. Check if it's used elsewhere in the file. It's still used in the mobile tab bar (lines 151-172), so keep it. However, remove the icon imports that are only used by `modeIcons` if any become unused — check each: `Grid3x3`, `LayoutList`, `Lightbulb`, `BookOpen`, `Sparkles`, `Search`. All are still referenced in `modeIcons`, so no import changes needed.

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && cmd /c "npm run typecheck"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat: replace mode pill group with stage selector in header"
```

---

### Task 4: Update Layout tests for stage navigation

**Files:**
- Modify: `frontend/src/components/Layout.test.tsx:100-124`

- [ ] **Step 1: Update the mode nav test to check for stage buttons**

Replace the test at line 100 (`it('renders mode navigation buttons in workspace'`) with:

```ts
  it('renders stage navigation buttons in workspace', async () => {
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useSettingsStore.getState().setIconMode('labels');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      expect(screen.getByText('Planning')).toBeInTheDocument();
      expect(screen.getByText('Writing')).toBeInTheDocument();
      expect(screen.getByText('Review')).toBeInTheDocument();
    });
  });
```

This test still checks for "Planning", "Writing", and "Review" which are the stage labels. The test should pass since those strings appear in the header stage selector.

- [ ] **Step 2: Update the active mode highlight test**

The test at line 126 (`it('highlights active mode in sidebar'`) checks for `bg-[var(--bg-elevated)]` on the "Writing" button. With stage-based nav, the header shows "Writing" as a stage label and the sidebar shows "Writing" as a mode within the Writing stage. The test should still work since both use similar active state classes. However, the test searches for buttons named "Writing" — there will be one in the header (stage) and one in the sidebar (mode). Keep the test as-is since it uses `some()` to check if any match.

- [ ] **Step 3: Run tests**

Run: `cd frontend && cmd /c "npm run test -- --testPathPattern=Layout.test"`
Expected: PASS (10/10 tests)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.test.tsx
git commit -m "test: update Layout tests for stage-based navigation"
```

---

### Task 5: Create WorkspaceShell test for filtered sidebar

**Files:**
- Create: `frontend/src/components/WorkspaceShell.test.tsx`

- [ ] **Step 1: Write the test file**

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { render, screen } from '../__tests__/test-utils';
import { WorkspaceShell } from './WorkspaceShell';
import { useUIStore } from '../stores/uiStore';
import { useSettingsStore } from '../stores/settingsStore';

vi.mock('../hooks/useRouteSync', () => ({
  useRouteSync: vi.fn(),
}));

function renderShell() {
  return render(
    <WorkspaceShell><div data-testid="main-content">Page Content</div></WorkspaceShell>,
  );
}

describe('WorkspaceShell', () => {
  beforeEach(() => {
    act(() => {
      useUIStore.setState({ mode: 'plan', projectId: 'test-project', chapterId: null, jobId: null, inspectContext: null });
      useSettingsStore.getState().setIconMode('labels');
    });
  });

  it('shows Planning stage items when mode is plan', async () => {
    act(() => {
      useUIStore.getState().setMode('plan');
    });
    renderShell();

    await vi.waitFor(() => {
      expect(screen.getByText('Brain Dump')).toBeInTheDocument();
      expect(screen.getByText('Planning')).toBeInTheDocument();
      expect(screen.getByText('Canon')).toBeInTheDocument();
      expect(screen.getByText('Generate')).toBeInTheDocument();
      expect(screen.queryByText('Writing')).not.toBeInTheDocument();
      expect(screen.queryByText('Review')).not.toBeInTheDocument();
    });
  });

  it('shows Writing stage item when mode is write', async () => {
    act(() => {
      useUIStore.getState().setMode('write');
    });
    renderShell();

    await vi.waitFor(() => {
      expect(screen.getByText('Writing')).toBeInTheDocument();
      expect(screen.queryByText('Planning')).not.toBeInTheDocument();
      expect(screen.queryByText('Brain Dump')).not.toBeInTheDocument();
    });
  });

  it('shows Review stage items when mode is review', async () => {
    act(() => {
      useUIStore.getState().setMode('review');
    });
    renderShell();

    await vi.waitFor(() => {
      expect(screen.getByText('Review')).toBeInTheDocument();
      expect(screen.getByText('Inspect')).toBeInTheDocument();
      expect(screen.queryByText('Planning')).not.toBeInTheDocument();
      expect(screen.queryByText('Writing')).not.toBeInTheDocument();
    });
  });

  it('falls back to planning stage for unknown mode', async () => {
    act(() => {
      // @ts-expect-error — testing fallback for invalid mode
      useUIStore.getState().setMode('invalid-mode');
    });
    renderShell();

    await vi.waitFor(() => {
      expect(screen.getByText('Planning')).toBeInTheDocument();
      expect(screen.getByText('Canon')).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run the test**

Run: `cd frontend && cmd /c "npm run test -- --testPathPattern=WorkspaceShell.test"`
Expected: PASS (4/4 tests)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/WorkspaceShell.test.tsx
git commit -m "test: add WorkspaceShell tests for stage-filtered sidebar"
```

---

### Task 6: Full validation

**Files:** All changed files

- [ ] **Step 1: Run full frontend validation**

Run each command and verify PASS:

```bash
cd frontend && cmd /c "npm run lint"
cd frontend && cmd /c "npm run typecheck"
cd frontend && cmd /c "npm run build"
cd frontend && cmd /c "npm run test"
```

Expected:
- Lint: 0 errors (2 pre-existing warnings acceptable)
- Typecheck: PASS
- Build: 2030+ modules, no errors
- Tests: 535+ passed (4 new from WorkspaceShell test)

- [ ] **Step 2: Commit if all pass**

```bash
git add -A
git commit -m "feat: stage-based navigation — header stage selector + filtered sidebar"
```
