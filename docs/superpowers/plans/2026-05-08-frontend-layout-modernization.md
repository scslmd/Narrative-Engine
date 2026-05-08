# Frontend Layout Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a coherent modern shell/layout across home, guided setup, and workspace routes with clearer hierarchy, navigation, responsive behavior, and accessibility cues.

**Architecture:** Standardize shared shell primitives first (`Layout`, `WorkspaceShell`, global utility classes), then align route views (`Workspace`, `ProjectList`, `GuidedSetupView`) to that shell. Keep route/state contracts intact while improving structure, CTA placement, and status surfaces.

**Tech Stack:** React, TypeScript, React Router, Tailwind utility classes, Zustand, Vitest + Testing Library.

---

## Canonical Task Contract JSON

```json
{
  "contract_id": "frontend-layout-modernization-2026-05-08",
  "tasks": [
    {
      "task_id": "T1-layout-test-updates",
      "responsible_file": "frontend/src/components/Layout.test.tsx",
      "same_file_serial_group": "layout-tests",
      "serial_dependencies": [],
      "guardrails": [
        "Do not modify runtime behavior in this task",
        "Do not modify files outside frontend/src/components/Layout.test.tsx"
      ]
    },
    {
      "task_id": "T2-layout-shell-modernization",
      "responsible_file": "frontend/src/components/Layout.tsx",
      "same_file_serial_group": "layout-runtime",
      "serial_dependencies": ["T1-layout-test-updates"],
      "guardrails": [
        "Preserve existing routes and modeToStage behavior",
        "Do not change backend/API integration"
      ]
    },
    {
      "task_id": "T3-workspace-shell-test-updates",
      "responsible_file": "frontend/src/components/WorkspaceShell.test.tsx",
      "same_file_serial_group": "workspace-shell-tests",
      "serial_dependencies": [],
      "guardrails": [
        "Do not modify runtime behavior in this task",
        "Do not modify files outside frontend/src/components/WorkspaceShell.test.tsx"
      ]
    },
    {
      "task_id": "T4-workspace-shell-modernization",
      "responsible_file": "frontend/src/components/WorkspaceShell.tsx",
      "same_file_serial_group": "workspace-shell-runtime",
      "serial_dependencies": ["T3-workspace-shell-test-updates"],
      "guardrails": [
        "Keep mode-based filtering semantics intact",
        "Do not alter route path builders"
      ]
    },
    {
      "task_id": "T5-workspace-view-layout",
      "responsible_file": "frontend/src/views/Workspace.tsx",
      "serial_dependencies": ["T4-workspace-shell-modernization"],
      "guardrails": [
        "Do not alter NotesPanel/JobLaunchPanel APIs",
        "Do not change workspace route contracts"
      ]
    },
    {
      "task_id": "T6-project-list-layout",
      "responsible_file": "frontend/src/views/ProjectList.tsx",
      "serial_dependencies": ["T2-layout-shell-modernization"],
      "guardrails": [
        "Do not alter create/delete/export service behavior",
        "Keep existing fields and submission payload structure"
      ]
    },
    {
      "task_id": "T7-guided-setup-layout",
      "responsible_file": "frontend/src/views/GuidedSetupView.tsx",
      "serial_dependencies": ["T2-layout-shell-modernization"],
      "guardrails": [
        "Do not alter guided setup API calls/mutations",
        "Keep create-project action semantics"
      ]
    },
    {
      "task_id": "T8-global-layout-utilities",
      "responsible_file": "frontend/src/index.css",
      "serial_dependencies": ["T2-layout-shell-modernization", "T4-workspace-shell-modernization"],
      "guardrails": [
        "Do not remove existing theme variables usage",
        "Keep icon-mode behavior working"
      ]
    }
  ]
}
```

Validation summary:
- Schema valid: yes
- One task/one responsible file: yes
- Same-file serial grouping used only where relevant: yes
- Dependency graph acyclic: yes
- Deterministic instructions and explicit boundaries: yes

## Tasks

### Task 1: Update Layout Tests
**task_id:** `T1-layout-test-updates`  
**responsible_file:** `frontend/src/components/Layout.test.tsx`
- [ ] Add assertions for new header semantics and breadcrumb/context labeling.
- [ ] Add assertions for modern stage switcher container role/label.
- [ ] Run: `cd frontend && npm run test -- Layout.test.tsx`
- [ ] Expected: all layout tests pass.

### Task 2: Modernize Global Layout Shell
**task_id:** `T2-layout-shell-modernization`  
**responsible_file:** `frontend/src/components/Layout.tsx`  
**serial_dependencies:** `T1-layout-test-updates`
- [ ] Refine header composition: stronger app identity + explicit workspace context block.
- [ ] Standardize stage switcher visuals and active states for desktop/mobile.
- [ ] Improve accessibility labels and focus affordances for top-level controls.
- [ ] Run: `cd frontend && npm run test -- Layout.test.tsx`
- [ ] Expected: tests green with updated UX structure.

### Task 3: Update WorkspaceShell Tests
**task_id:** `T3-workspace-shell-test-updates`  
**responsible_file:** `frontend/src/components/WorkspaceShell.test.tsx`
- [ ] Add coverage for responsive shell containers and nav labeling.
- [ ] Add coverage for active-state marker semantics.
- [ ] Run: `cd frontend && npm run test -- WorkspaceShell.test.tsx`
- [ ] Expected: tests fail first for new expectations, then pass after Task 4.

### Task 4: Modernize WorkspaceShell Navigation Layout
**task_id:** `T4-workspace-shell-modernization`  
**responsible_file:** `frontend/src/components/WorkspaceShell.tsx`  
**serial_dependencies:** `T3-workspace-shell-test-updates`
- [ ] Convert nav area into modern sticky panel with clear section heading.
- [ ] Preserve mode-based item filtering and navigation behavior.
- [ ] Align active/inactive states with improved contrast and density.
- [ ] Run: `cd frontend && npm run test -- WorkspaceShell.test.tsx`
- [ ] Expected: tests pass with unchanged nav logic.

### Task 5: Workspace View Structural Layout Update
**task_id:** `T5-workspace-view-layout`  
**responsible_file:** `frontend/src/views/Workspace.tsx`  
**serial_dependencies:** `T4-workspace-shell-modernization`
- [ ] Rework content + utility panel composition for better desktop/tablet/mobile behavior.
- [ ] Keep notes/launch panels visible but non-obstructive in smaller widths.
- [ ] Maintain BottomUtilityLayer behavior.
- [ ] Run: `cd frontend && npm run test -- WorkspaceShell.test.tsx`
- [ ] Expected: no navigation regression.

### Task 6: Project List Information Architecture Refresh
**task_id:** `T6-project-list-layout`  
**responsible_file:** `frontend/src/views/ProjectList.tsx`  
**serial_dependencies:** `T2-layout-shell-modernization`
- [ ] Reorder sections to prioritize clear entry actions and project discovery.
- [ ] Improve search/action bar clarity and project card readability.
- [ ] Keep create/import/delete/export flows and payloads unchanged.
- [ ] Run: `cd frontend && npm run test -- ProjectList.test.tsx`
- [ ] Expected: project list tests pass.

### Task 7: Guided Setup Layout Refresh
**task_id:** `T7-guided-setup-layout`  
**responsible_file:** `frontend/src/views/GuidedSetupView.tsx`  
**serial_dependencies:** `T2-layout-shell-modernization`
- [ ] Improve guided setup page shell consistency with global layout language.
- [ ] Clarify status, primary CTA placement, and responsive split-pane behavior.
- [ ] Preserve LLM health + create flow semantics.
- [ ] Run: `cd frontend && npm run test -- guidedSetup`
- [ ] Expected: no guided setup flow regression.

### Task 8: Global Layout Utility Styles
**task_id:** `T8-global-layout-utilities`  
**responsible_file:** `frontend/src/index.css`  
**serial_dependencies:** `T2-layout-shell-modernization`, `T4-workspace-shell-modernization`
- [ ] Add shared utility classes for page headers/action bars/section spacing.
- [ ] Keep theme and icon-mode selectors compatible with current behavior.
- [ ] Run: `cd frontend && npm run lint`
- [ ] Expected: no CSS/class-usage lint errors.

## Final Verification

- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npm run typecheck`
- [ ] `cd frontend && npm run build`
- [ ] `cd frontend && npm run test`
- [ ] Report changed files + UX deltas by route.
