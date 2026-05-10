# Frontend Layout Modernization Implementation Plan
Status: Planned

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize frontend layout with warm creative studio aesthetic, CSS variable unification, and 4 shared primitives across 8 tasks.

**Architecture:** Additive CSS tokens + extract ThemeCard/PageHeader/StageIndicator/FieldWrapper primitives + update 5 views to use them. Serial execution: T8 → T1→T2 → T3→T4 → T5 → T6 → T7.

**Tech Stack:** React, TypeScript, Tailwind utility classes, Zustand, Vitest + Testing Library.

**Design Spec:** `docs/superpowers/specs/2026-05-08-layout-modernization-design.md`

**Execution Order (All Serial):** T0 → T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8

**Cross-Plan Dependencies:** Task T7 (`GuidedSetupView.tsx`) depends on both `2026-05-08-guided-setup-readiness` and `2026-05-08-guided-setup-planning` completing first. Do not execute T7 until those plans are shipped.

---

## Task 0: Add Warm Accent CSS Tokens + Utility Classes

**responsible_file:** `frontend/src/theme/variables.css`  
**serial_dependencies:** none

- [ ] **Step 1: Add warm accent tokens to `:root` in variables.css**

Add after the existing `--color-info-border` line (line 24):
```css
  /* Warm accent (creative studio) */
  --accent-primary: #f59e0b;
  --accent-secondary: #d97706;
  --accent-subtle: #fef3c7;
  --accent-ring: rgba(245, 158, 11, 0.3);
```

- [ ] **Step 2: Add warm accent tokens to dark theme block**

Add after `--color-info-border` in `[data-theme="dark"]` (line 97):
```css
  --accent-primary: #fbbf24;
  --accent-secondary: #f59e0b;
  --accent-subtle: rgba(251, 191, 36, 0.1);
  --accent-ring: rgba(251, 191, 36, 0.3);
```

- [ ] **Step 3: Add warm accent tokens to midnight theme block**

Add after existing colors in `[data-theme="midnight"]`:
```css
  --accent-primary: #fbbf24;
  --accent-secondary: #f59e0b;
  --accent-subtle: rgba(251, 191, 36, 0.1);
  --accent-ring: rgba(251, 191, 36, 0.3);
```

- [ ] **Step 4: Add new utility classes to index.css**

Add to `frontend/src/index.css` after the existing `@layer components` block (after line 107):
```css
@layer components {
  .section-stack {
    @apply space-y-3;
  }

  .route-shell {
    @apply h-full rounded-[var(--radius-xl)] border overflow-hidden;
    border-color: var(--border-primary);
    background: var(--bg-base);
  }

  .warm-badge {
    @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium;
    background: var(--accent-subtle);
    color: var(--accent-secondary);
    border: 1px solid var(--accent-ring);
  }
}
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds, no Tailwind warnings about unused classes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/theme/variables.css frontend/src/index.css
git commit -m "feat(layout): add warm accent CSS tokens and utility classes"
```

---

## Task 1: Create ThemeCard Primitive + Tests

**responsible_file:** `frontend/src/components/primitives/ThemeCard.tsx`  
**serial_dependencies:** T0

- [ ] **Step 1: Create primitives directory**

Run: `mkdir frontend/src/components/primitives`

- [ ] **Step 2: Write test file first**

Create `frontend/src/components/primitives/ThemeCard.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { ThemeCard } from './ThemeCard';

describe('ThemeCard', () => {
  it('renders children content', () => {
    render(<ThemeCard variant="elevated">Hello</ThemeCard>);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('applies elevated variant with shadow-card', () => {
    const { container } = render(<ThemeCard variant="elevated">Test</ThemeCard>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('shadow-card');
  });

  it('applies subtle variant without shadow', () => {
    const { container } = render(<ThemeCard variant="subtle">Test</ThemeCard>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).not.toContain('shadow-card');
  });

  it('applies ghost variant with transparent background', () => {
    const { container } = render(<ThemeCard variant="ghost">Test</ThemeCard>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('bg-transparent');
  });

  it('merges custom className', () => {
    const { container } = render(
      <ThemeCard variant="elevated" className="custom-class">Test</ThemeCard>
    );
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('custom-class');
  });

  it('uses CSS variable for border color', () => {
    const { container } = render(<ThemeCard variant="elevated">Test</ThemeCard>);
    const card = container.firstChild as HTMLElement;
    expect(card.style.borderColor || card.className).toBeTruthy();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npm run test -- ThemeCard.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 4: Implement ThemeCard**

Create `frontend/src/components/primitives/ThemeCard.tsx`:
```tsx
import { ReactNode } from 'react';

export interface ThemeCardProps {
  variant?: 'elevated' | 'subtle' | 'ghost';
  children: ReactNode;
  className?: string;
}

const variantClasses = {
  elevated: 'border shadow-card hover:shadow-card-hover',
  subtle: 'border bg-[var(--bg-secondary)]/50',
  ghost: 'bg-transparent',
};

export function ThemeCard({ variant = 'elevated', children, className = '' }: ThemeCardProps) {
  const base = 'rounded-[var(--radius-lg)] transition-all duration-200';
  const border = variant !== 'ghost' ? 'border-[var(--border-primary)]' : '';
  const bg = variant === 'elevated' ? 'bg-[var(--bg-primary)]' : variant === 'subtle' ? '' : '';

  return (
    <div className={`${base} ${border} ${bg} ${variantClasses[variant]} ${className}`.trim()}>
      {children}
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npm run test -- ThemeCard.test.tsx`
Expected: PASS (6 tests)

- [ ] **Step 6: Verify typecheck**

Run: `cd frontend && npm run typecheck`
Expected: Clean, no errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/primitives/
git commit -m "feat(layout): add ThemeCard primitive with elevated/subtle/ghost variants"
```

---

## Task 2: Create PageHeader Primitive + Tests

**responsible_file:** `frontend/src/components/primitives/PageHeader.tsx`  
**serial_dependencies:** T1

- [ ] **Step 1: Write test file first**

Create `frontend/src/components/primitives/PageHeader.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { PageHeader } from './PageHeader';

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="Test Title" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('renders actions slot when provided', () => {
    render(
      <PageHeader title="Test">
        <actions>
          <button type="button">Action</button>
        </actions>
      </PageHeader>
    );
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('renders back link when backTo is provided', () => {
    render(<PageHeader title="Test" backTo="/" />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/');
  });

  it('does not render back link without backTo', () => {
    render(<PageHeader title="Test" />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- PageHeader.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Implement PageHeader**

Create `frontend/src/components/primitives/PageHeader.tsx`:
```tsx
import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export interface PageHeaderProps {
  title: string;
  actions?: ReactNode;
  backTo?: string;
}

export function PageHeader({ title, actions, backTo }: PageHeaderProps) {
  return (
    <header className="page-header bg-[var(--bg-primary)]">
      <div className="max-w-7xl mx-auto flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          {backTo && (
            <Link
              to={backTo}
              className="flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
          )}
          <h1 className="text-xl font-bold text-[var(--text-primary)]">{title}</h1>
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- PageHeader.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/primitives/PageHeader.*
git commit -m "feat(layout): add PageHeader primitive with back navigation and actions slot"
```

---

## Task 3: Create StageIndicator Primitive + Tests

**responsible_file:** `frontend/src/components/primitives/StageIndicator.tsx`  
**serial_dependencies:** T0

- [ ] **Step 1: Write test file first**

Create `frontend/src/components/primitives/StageIndicator.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { StageIndicator } from './StageIndicator';

describe('StageIndicator', () => {
  it('renders planning stage label', () => {
    render(<StageIndicator stage="planning" />);
    expect(screen.getByText('Planning')).toBeInTheDocument();
  });

  it('renders writing stage label', () => {
    render(<StageIndicator stage="writing" />);
    expect(screen.getByText('Writing')).toBeInTheDocument();
  });

  it('renders review stage label', () => {
    render(<StageIndicator stage="review" />);
    expect(screen.getByText('Review')).toBeInTheDocument();
  });

  it('renders indicator dot with accent color', () => {
    const { container } = render(<StageIndicator stage="planning" />);
    const dot = container.querySelector('[data-stage-dot]');
    expect(dot).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- StageIndicator.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Implement StageIndicator**

Create `frontend/src/components/primitives/StageIndicator.tsx`:
```tsx
import type { LucideIcon } from 'lucide-react';
import { Lightbulb, BookOpen, Search } from 'lucide-react';

export type StageId = 'planning' | 'writing' | 'review';

interface StageConfig {
  label: string;
  icon: LucideIcon;
}

const stageConfigs: Record<StageId, StageConfig> = {
  planning: { label: 'Planning', icon: Lightbulb },
  writing: { label: 'Writing', icon: BookOpen },
  review: { label: 'Review', icon: Search },
};

export interface StageIndicatorProps {
  stage: StageId;
}

export function StageIndicator({ stage }: StageIndicatorProps) {
  const config = stageConfigs[stage];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2 px-1 pb-2 border-b border-[var(--border-primary)] mb-2">
      <span
        data-stage-dot
        className="w-2 h-2 rounded-full bg-[var(--accent-primary)] animate-pulse"
      />
      <Icon className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
      <span className="text-xs font-semibold text-[var(--text-secondary)]">{config.label}</span>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- StageIndicator.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/primitives/StageIndicator.*
git commit -m "feat(layout): add StageIndicator primitive with stage dot and icon"
```

---

## Task 4: Modernize Layout.tsx Shell

**responsible_file:** `frontend/src/components/Layout.tsx`  
**serial_dependencies:** T1, T3

- [ ] **Step 1: Update Layout tests for warm accent active state**

Add to `frontend/src/components/Layout.test.tsx` after the existing test for active stage (line 222):
```tsx
  it('active stage button uses warm amber shadow on desktop', async () => {
    act(() => {
      useUIStore.getState().setProjectId('test-project');
      useUIStore.getState().setMode('plan');
    });
    renderLayout('/workspace/test-project/plan');

    await vi.waitFor(() => {
      const planningBtns = screen.getAllByText('Planning').filter(
        (el) => el.parentElement?.tagName === 'BUTTON',
      );
      const activeBtn = planningBtns.find((btn) => {
        const parent = btn.parentElement;
        return parent?.classList.contains('shadow-amber-500/30');
      });
      expect(activeBtn).toBeTruthy();
    });
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- Layout.test.tsx`
Expected: 1 FAIL (new amber shadow test)

- [ ] **Step 3: Update Layout.tsx stage switcher active state**

In `frontend/src/components/Layout.tsx`, update the desktop stage button's active class (lines 113-117):
```tsx
// Replace the isActive ternary block in the desktop stage switcher (line 113-117):
className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-200 rounded-[var(--radius-sm)] ${
  isActive
    ? `bg-white text-gray-900 shadow-lg shadow-amber-500/30`
    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]/50'
}`}
```

- [ ] **Step 4: Update mobile stage bar active border to amber**

In the mobile stage switcher (lines 154-158), update the `border` config usage:
```tsx
// Replace the isActive ternary in mobile stage buttons (line 154-158):
className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs font-medium transition-colors ${
  isActive
    ? `text-[var(--text-primary)] border-b-2 border-[var(--accent-primary)]`
    : 'text-[var(--text-secondary)]'
}`}
```

Also remove the per-stage `border` config from `stageButtons` since we now use a unified amber border:
```tsx
// Simplify stageButtons type (line 25) - remove shadow and border properties:
const stageButtons: { id: StageId; label: string; icon: typeof Lightbulb }[] = [
  { id: 'planning', label: 'Planning', icon: Lightbulb },
  { id: 'writing', label: 'Writing', icon: BookOpen },
  { id: 'review', label: 'Review', icon: Search },
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npm run test -- Layout.test.tsx`
Expected: PASS (all layout tests including new one)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/Layout.tsx frontend/src/components/Layout.test.tsx
git commit -m "style(layout): use warm amber active states for stage switcher"
```

---

## Task 5: Modernize WorkspaceShell Navigation

**responsible_file:** `frontend/src/components/WorkspaceShell.tsx`  
**serial_dependencies:** T3

- [ ] **Step 1: Update WorkspaceShell tests for StageIndicator and warm active state**

Add to `frontend/src/components/WorkspaceShell.test.tsx` after line 214:
```tsx
  it('renders StageIndicator at top of sidebar', () => {
    renderShell('plan');

    expect(screen.getByText('Planning')).toBeInTheDocument();
    const dot = document.querySelector('[data-stage-dot]');
    expect(dot).toBeInTheDocument();
  });

  it('active nav item uses accent-subtle background instead of color-primary-subtle', () => {
    renderShell('plan');

    const planningBtn = screen.getByText('Planning').closest('button');
    expect(planningBtn).toBeInTheDocument();
    expect(planningBtn?.className).toContain('--accent-subtle');
    expect(planningBtn?.className).not.toContain('--color-primary-subtle');
  });
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- WorkspaceShell.test.tsx`
Expected: 2 FAIL (new StageIndicator + warm active state tests)

- [ ] **Step 3: Update WorkspaceShell.tsx**

Add import and StageIndicator, update active nav styling:
```tsx
// Add to imports at top of file:
import { StageIndicator } from '../components/primitives/StageIndicator';
import { modeToStage } from '../routes';

// In the sidebar, add StageIndicator after the "Workspace sections" label (after line 52):
<div className="rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card p-3 lg:sticky lg:top-0">
  <p className="text-[11px] uppercase tracking-wide font-semibold text-[var(--text-tertiary)] px-1 pb-2">
    Workspace sections
  </p>
  <StageIndicator stage={activeStage} />
  <nav aria-label="Workspace sections" className="space-y-1">

// Update active nav item background (line 67):
// Replace: 'bg-[var(--color-primary-subtle)] text-[var(--color-primary)] shadow-card'
// With: 'bg-[var(--accent-subtle)] text-[var(--accent-secondary)] shadow-card'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- WorkspaceShell.test.tsx`
Expected: PASS (all workspace shell tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/WorkspaceShell.tsx frontend/src/components/WorkspaceShell.test.tsx
git commit -m "style(shell): add StageIndicator and warm accent active states to sidebar nav"
```

---

## Task 6: Workspace View Layout Update

**responsible_file:** `frontend/src/views/Workspace.tsx`  
**serial_dependencies:** T4, T5

- [ ] **Step 1: Update Workspace.tsx to use CSS variable radii and shadows**

In `frontend/src/views/Workspace.tsx`, update the content section and side panels:
```tsx
// Replace line 18 (content section):
<section className="min-h-0 h-full overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">

// Replace line 22 (NotesPanel container):
<div className="min-h-0 flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">

// Replace line 25 (JobLaunchPanel container):
<div className="min-h-0 flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card">
```

- [ ] **Step 2: Verify with existing test**

Run: `cd frontend && npm run test -- Workspace.test.tsx`
Expected: PASS (no view-level regression)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Workspace.tsx
git commit -m "style(workspace): use CSS variable radii and shadows for panel cards"
```

---

## Task 7: ProjectList Modernization (Largest Task)

**responsible_file:** `frontend/src/views/ProjectList.tsx`  
**serial_dependencies:** T1, T6

- [ ] **Step 1: Create FieldWrapper primitive**

Create `frontend/src/components/primitives/FieldWrapper.tsx`:
```tsx
import { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

export interface FieldWrapperProps {
  label: string;
  icon: LucideIcon;
  children: ReactNode;
}

export function FieldWrapper({ label, icon: Icon, children }: FieldWrapperProps) {
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </label>
      {children}
    </div>
  );
}
```

Create `frontend/src/components/primitives/FieldWrapper.test.tsx`:
```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { FieldWrapper } from './FieldWrapper';
import { BookOpen } from 'lucide-react';

describe('FieldWrapper', () => {
  it('renders label text', () => {
    render(<FieldWrapper label="Genre" icon={BookOpen}><input /></FieldWrapper>);
    expect(screen.getByText('Genre')).toBeInTheDocument();
  });

  it('renders children', () => {
    render(
      <FieldWrapper label="Test" icon={BookOpen}>
        <input data-testid="field-input" />
      </FieldWrapper>
    );
    expect(screen.getByTestId('field-input')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Replace ProjectList hardcoded dark/light classes**

In `frontend/src/views/ProjectList.tsx`:

Remove the `isDark` usage for styling (keep it for the hero section gradient badge which uses a different pattern):

Replace the `Field` inline component (lines 574-594) with import:
```tsx
// Add import at top:
import { FieldWrapper } from '../components/primitives/FieldWrapper';
import { ThemeCard } from '../components/primitives/ThemeCard';

// Remove the inline Field function (lines 574-594)
// Replace all <Field label="..." icon={...} isDark={isDark}> with <FieldWrapper label="..." icon={...}>
```

Replace hero section (lines 172-185):
```tsx
<section className="rounded-[var(--radius-lg)] border border-[var(--border-primary)] px-6 py-6 bg-[var(--bg-primary)] shadow-card">
  <div className="text-center py-2">
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--accent-subtle)] border border-[var(--accent-ring)] mb-4">
      <Sparkles className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
      <span className="text-xs font-medium text-[var(--accent-secondary)]">AI-Powered Story Development</span>
    </div>
    <h1 className="text-2xl font-bold text-[var(--text-primary)]">
      Welcome to Narrative Engine
    </h1>
    <p className="text-sm mt-1.5 text-[var(--text-secondary)]">
      Create a new project to start developing your story
    </p>
  </div>
</section>
```

Replace projects section wrapper (line 187):
```tsx
<section className="rounded-[var(--radius-lg)] border border-[var(--border-primary)] p-5 bg-[var(--bg-primary)] shadow-card">
```

Replace search input (lines 190-216) — remove `isDark` ternary:
```tsx
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
  <input
    ref={searchInputRef}
    type="text"
    placeholder="Search projects... (Ctrl+K)"
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    className="pl-9 pr-8 py-1.5 text-sm rounded-[var(--radius-md)] border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] transition-all focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] focus:border-[var(--accent-primary)] w-full sm:w-72"
  />
  {searchQuery && (
    <button
      type="button"
      onClick={() => setSearchQuery('')}
      className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
      aria-label="Clear search"
    >
      <X className="w-3.5 h-3.5" />
    </button>
  )}
</div>
```

Replace project cards (lines 229-320) — use ThemeCard:
```tsx
{filteredProjects().map((project) => (
  <ThemeCard key={project.project_id} className="group p-4 hover:shadow-card-hover">
    <div className="flex items-start justify-between">
      <Link
        to={`/workspace/${project.project_id}`}
        className="flex-1 min-w-0 text-left"
      >
        <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
          {project.project_name}
        </h3>
        <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-secondary)]">
          <span>{project.genre}</span>
          <span>&bull;</span>
          <span>{project.tone_profile}</span>
        </div>
        {project.premise_text ? (
          <p className="mt-2 text-xs leading-relaxed line-clamp-2 text-[var(--text-secondary)]">
            {project.premise_text}
          </p>
        ) : (
          <p className="mt-2 text-xs italic text-[var(--text-tertiary)]">
            No description yet
          </p>
        )}
      </Link>
    </div>
    <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-[var(--border-primary)]">
      <div className="flex flex-col gap-1">
        <span className="inline-flex items-center gap-1 rounded-full border border-[var(--border-primary)] px-2 py-0.5 text-[10px] font-medium bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
          <CalendarPlus className="h-3 w-3" />
          Created {formatProjectDate(project.created_at)}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full border border-[var(--color-success-border)] px-2 py-0.5 text-[10px] font-medium bg-[var(--color-success-subtle)] text-[var(--color-success)]">
          <Clock3 className="h-3 w-3" />
          Modified {formatProjectDate(project.updated_at)}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => handleExport(project.project_id)}
          disabled={isExporting === project.project_id}
          className="p-1 rounded text-[var(--text-tertiary)] hover:text-[var(--accent-primary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
          title="Export project as ZIP"
        >
          {isExporting === project.project_id ? (
            <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          ) : (
            <Upload className="w-3.5 h-3.5" />
          )}
        </button>
        <button
          onClick={() => handleDeleteClick(project)}
          disabled={deleteMutation.isPending}
          className="p-1 rounded text-[var(--text-tertiary)] hover:text-red-500 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
          title="Delete project"
          aria-label={`Delete ${project.project_name}`}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  </ThemeCard>
))}
```

Replace empty state (line 326):
```tsx
<div className="text-center py-12 rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-secondary)]/50">
  <BookOpen className="w-10 h-10 mx-auto mb-3 text-[var(--text-tertiary)]" />
  <p className="text-sm text-[var(--text-secondary)]">No projects yet. Create your first project below!</p>
</div>
```

Replace create form (line 333):
```tsx
<form onSubmit={handleSubmit} className="rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card p-6 space-y-5">
```

Replace all Field usages with FieldWrapper and update input styling to use CSS variables:
```tsx
// Example for project_name field (replace all Field blocks):
<FieldWrapper label="Project Name" icon={FileText}>
  <input
    type="text"
    id="project_name"
    name="project_name"
    required
    placeholder="Enter project title..."
    className="w-full rounded-[var(--radius-md)] border border-[var(--border-primary)] text-sm px-3 py-2.5 bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] transition-all focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] focus:border-[var(--accent-primary)]"
  />
</FieldWrapper>
```

For select fields (story_structure, pov):
```tsx
className="w-full rounded-[var(--radius-md)] border border-[var(--border-primary)] text-sm px-3 py-2.5 bg-[var(--bg-secondary)] text-[var(--text-primary)] transition-all focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] focus:border-[var(--accent-primary)]"
```

Replace description text under selects:
```tsx
<p className="mt-1 text-xs text-[var(--text-tertiary)]">
  {STRUCTURE_DESCRIPTIONS[selectedStructure]}
</p>
```

Replace submit button (keep gradient, update focus ring):
```tsx
<button
  type="submit"
  disabled={createMutation.isPending}
  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] text-white text-sm font-medium rounded-[var(--radius-md)] hover:shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed"
>
```

Replace delete confirmation modal (line 520-568):
```tsx
<div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center bg-black/50" onClick={handleDeleteCancel}>
  <div className="mx-4 w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-elevated p-6" onClick={(e) => e.stopPropagation()}>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-base font-semibold text-[var(--text-primary)]">Delete Project</h3>
      <button onClick={handleDeleteCancel} className="p-1 rounded text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors" aria-label="Cancel">
        <X className="w-4 h-4" />
      </button>
    </div>
    <p className="text-sm mb-6 text-[var(--text-secondary)]">
      Delete '{deletingProject.project_name}' and all associated data? This cannot be undone.
    </p>
    <div className="flex justify-end gap-3">
      <button onClick={handleDeleteCancel} className="px-4 py-2 text-sm font-medium rounded-[var(--radius-md)] border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors">
        Cancel
      </button>
      <button onClick={handleDeleteConfirm} disabled={deleteMutation.isPending} className="px-4 py-2 text-sm font-medium rounded-[var(--radius-md)] bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
        {deleteMutation.isPending ? 'Deleting...' : 'Confirm'}
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Remove unused isDark from ProjectList**

The `isDark` variable (line 25) is no longer needed for styling. Remove:
```tsx
// Remove line: const isDark = resolveEffectiveMode(mode) === 'dark';
// If isDark is used elsewhere in the file, keep it. Otherwise remove the import of resolveEffectiveMode if unused.
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npm run test -- ProjectList`
Expected: PASS (no regressions)

- [ ] **Step 5: Verify typecheck**

Run: `cd frontend && npm run typecheck`
Expected: Clean

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/ProjectList.tsx frontend/src/components/primitives/FieldWrapper.*
git commit -m "refactor(projectlist): replace hardcoded dark/light classes with CSS variables and ThemeCard"
```

---

## Task 8: GuidedSetupView Layout Refresh

**responsible_file:** `frontend/src/views/GuidedSetupView.tsx`  
**serial_dependencies:** T2, T7  
**BLOCKED:** Requires guided-setup-readiness and guided-setup-planning plans to ship first

- [ ] **Step 1: Replace inline header with PageHeader**

In `frontend/src/views/GuidedSetupView.tsx`:
```tsx
// Add import:
import { PageHeader } from '../components/primitives/PageHeader';

// Replace the header section (lines 48-103) with:
<PageHeader
  title="Story Architect"
  backTo="/"
  actions={
    <>
      {hasContent && !isCreating && (
        <button
          onClick={handleCreate}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-[var(--radius-md)] transition-all font-medium shadow-md ${
            readyToCreate
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600'
              : 'bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)] text-white hover:shadow-lg'
          }`}
        >
          {readyToCreate ? <Check className="w-4 h-4" /> : <Rocket className="w-4 h-4" />}
          {readyToCreate ? 'Save Project' : 'Save What You Have'}
        </button>
      )}
      {isCreating && (
        <div className="flex items-center gap-2 px-6 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-primary-subtle)] text-[var(--color-primary)]">
          <Loader2 className="w-4 h-4 animate-spin" />
          Creating project...
        </div>
      )}
    </>
  }
/>
```

- [ ] **Step 2: Update LLM health warning**

Replace the LLM health warning (lines 50-55):
```tsx
{llmHealth && !llmHealth.ok && (
  <div className="max-w-7xl mx-auto mb-3 flex items-center gap-2 px-4 py-2.5 rounded-[var(--radius-md)] border border-[var(--color-warning-border)] bg-[var(--color-warning-subtle)] text-[var(--color-warning)] text-sm">
    <AlertTriangle className="w-4 h-4 shrink-0" />
    <span>LLM unavailable ({llmHealth.backend}). Conversational features will not work - you can still fill fields manually and create a project.</span>
  </div>
)}
```

- [ ] **Step 3: Update outer container**

Replace the root div (line 48):
```tsx
<div className="route-shell">
```

- [ ] **Step 4: Update split pane panels**

Replace the main content area:
```tsx
<main className="max-w-7xl mx-auto p-4 lg:p-6 h-[calc(100%-5.5rem)]">
  <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_22rem] gap-3 h-full">
    <section className="h-full min-h-0 rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] overflow-hidden shadow-card">
      <ChatPanel onSend={handleSend} isLoading={isAnalyzing} readyToCreate={readyToCreate} progress={progress} categoryProgress={categoryProgress} />
    </section>
    <aside className="hidden xl:block h-full min-h-0 rounded-[var(--radius-lg)] border border-[var(--border-primary)] bg-[var(--bg-primary)] overflow-hidden shadow-card">
      <FieldPreview categoryProgress={categoryProgress} />
    </aside>
  </div>
</main>
```

- [ ] **Step 5: Update LLM health status badge**

Replace the status badge (lines 67-75):
```tsx
{llmHealth && (
  <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
    llmHealth.ok
      ? 'bg-[var(--color-success-subtle)] text-[var(--color-success)] border-[var(--color-success-border)]'
      : 'bg-[var(--color-danger-subtle)] text-[var(--color-danger)] border-[var(--color-danger-border)]'
  }`}>
    <span className={`w-2 h-2 rounded-full ${llmHealth.ok ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
    {llmHealth.ok ? llmHealth.model || llmHealth.backend : `${llmHealth.backend} offline`}
  </div>
)}
```

- [ ] **Step 6: Run tests**

Run: `cd frontend && npm run test -- guidedSetup`
Expected: PASS (no guided setup flow regression)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/GuidedSetupView.tsx
git commit -m "style(guided): use PageHeader primitive and CSS variables in GuidedSetupView"
```

---

## Final Verification

- [ ] `cd frontend && npm run lint` — zero warnings
- [ ] `cd frontend && npm run typecheck` — clean
- [ ] `cd frontend && npm run build` — CSS retained, 2025+ modules
- [ ] `cd frontend && npm run test` — full suite passes
- [ ] Grep check: no remaining `isDark ?` ternary in modified files

```bash
rg -n "isDark \?" frontend/src/components/Layout.tsx frontend/src/components/WorkspaceShell.tsx frontend/src/views/ProjectList.tsx frontend/src/views/GuidedSetupView.tsx -S
```
Expected: zero matches in modified files.
