# Frontend Quality Check

Use this file as the local acceptance rubric before marking frontend work complete. The goal is to push the frontend as close to a `10/10` quality score as possible for this repo, not merely to make it compile.

## Goal

A `10/10` frontend change in this repository is:

- correct against the current backend contract
- internally consistent with the existing frontend architecture
- free of placeholder or prototype behavior
- resilient in loading, empty, and error states
- clean under `lint`, `typecheck`, and `build`
- readable enough that the next agent does not need to reverse-engineer intent

## Current Baseline

The current merged frontend is roughly:

- Architecture: `7.5/10`
- State/routing correctness: `7/10`
- API/service layer consistency: `5.5/10`
- UX polish: `5.5/10`
- Merge readiness: `8/10`

Primary gaps still lowering quality:

- duplicated service-layer API configuration (`fetch` + file-local `API_BASE` vs shared Axios client)
- prototype behaviors (`console.log`, dead buttons, placeholder assumptions like `nodes[0]` root selection)
- UI polish debt (mojibake, awkward route handling, inconsistent navigation behavior)
- mock/live inconsistency in some feature flows

## Hard Gate

Do not call the work high quality unless all of these are true:

```bash
cd F:\Dev\Narrative-Engine\frontend
npm run lint
npm run typecheck
npm run build
```

Required result:

- all three commands pass
- no newly introduced warnings that point to actual code debt
- no broken imports
- no dead code left behind

## Scoring Rubric

Score each changed area from `0` to `2`. A strong change should reach at least `17/20`.

### 1. Backend Contract Accuracy

`0`:
- wrong endpoint
- wrong payload keys
- wrong response assumptions

`1`:
- mostly correct, but still manually adapts around uncertain contract details

`2`:
- uses the exact existing endpoint, payload field names, and response shape already defined by the repo

Check:

- use `/v1/...` frontend contract where the current backend expects it
- preserve exact keys like `project_id`, `branch_a_id`, `source_branch_id`, `finding_id`, `run_id`
- do not invent new query params or rename backend fields in the service layer

Relevant files:

- [api.ts](/F:/Dev/Narrative-Engine/frontend/src/lib/api.ts)
- [branches.ts](/F:/Dev/Narrative-Engine/frontend/src/services/branches.ts)
- [decisions.ts](/F:/Dev/Narrative-Engine/frontend/src/services/decisions.ts)
- [inspectLinks.ts](/F:/Dev/Narrative-Engine/frontend/src/services/inspectLinks.ts)
- [drafting.ts](/F:/Dev/Narrative-Engine/frontend/src/services/drafting.ts)

### 2. Service-Layer Consistency

`0`:
- every file invents its own HTTP pattern

`1`:
- some consistency, but still mixed conventions

`2`:
- services use one clear pattern for host/base path, error shaping, and response mapping

Check:

- prefer the shared client in [api.ts](/F:/Dev/Narrative-Engine/frontend/src/lib/api.ts)
- avoid file-local `const API_BASE = ...` unless there is a real repo-wide exception
- normalize list-envelope handling consistently
- keep response mapping minimal and predictable

Red flags:

- `fetch(...)` with duplicated host strings
- duplicate `VITE_API_URL || 'http://localhost:8000'` fallback logic
- per-file reinvention of error messages for the same backend failure mode

### 3. Routing and State Correctness

`0`:
- routing depends on fragile string splitting or stale store state

`1`:
- works for common paths but is brittle for deep links

`2`:
- route-derived state and store state remain synchronized across reloads and direct navigation

Check:

- no brittle `pathname.split('/')[N]` logic when route helpers or params can express intent more clearly
- workspace mode must stay correct for:
  - `/workspace/:projectId/plan`
  - `/workspace/:projectId/write`
  - `/workspace/:projectId/write/:chapterId`
  - `/workspace/:projectId/review`
  - `/workspace/:projectId/inspect`
  - `/workspace/:projectId/inspect/:jobId`
- inspect/review navigation should use existing route/store mechanisms instead of ad hoc query hacks unless the route system explicitly supports them

Relevant files:

- [App.tsx](/F:/Dev/Narrative-Engine/frontend/src/App.tsx)
- [Workspace.tsx](/F:/Dev/Narrative-Engine/frontend/src/views/Workspace.tsx)
- [Layout.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/Layout.tsx)
- [routes.ts](/F:/Dev/Narrative-Engine/frontend/src/routes.ts)
- [uiStore.ts](/F:/Dev/Narrative-Engine/frontend/src/stores/uiStore.ts)

### 4. No Prototype Behavior

`0`:
- contains console logging, dead buttons, fake data, or obvious placeholders

`1`:
- placeholders mostly removed, but one or two remain in user-visible paths

`2`:
- no user-facing prototype seams remain in the changed surface

Always remove:

- `console.log(...)` in UI interaction handlers
- dead CTA buttons
- hard-coded demo results where a real service already exists
- assumptions like “first item is root for now”

Examples already seen in this repo:

- logging in [DecisionTree.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/decisions/DecisionTree.tsx)
- dead CTA in [InspectRunLinkCard.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/inspectLinks/InspectRunLinkCard.tsx)
- mock success logging in [drafting.ts](/F:/Dev/Narrative-Engine/frontend/src/services/drafting.ts)

### 5. Error Handling Quality

`0`:
- network failures collapse into generic breakage

`1`:
- some errors handled, but not consistently

`2`:
- loading, error, and empty states are explicit and appropriate for the feature

Check:

- service layer throws readable errors with stable meaning
- component layer renders:
  - loading state
  - empty state
  - recoverable error state
- do not silently swallow 404 vs 409 vs 500 distinctions when those distinctions matter

Good pattern:

- keep detailed HTTP handling in services
- keep display decisions in components

### 6. UX Polish

`0`:
- visible encoding artifacts, broken labels, or awkward interaction flow

`1`:
- functionally usable, but rough around the edges

`2`:
- labels, actions, and state transitions feel intentional and production-ready

Check:

- no mojibake like `â˜€ï¸`, `â†’`, or similar artifacts
- buttons do what they claim
- empty states suggest a real next step
- disabled states are used when an action is not actually available
- avoid user flows that intentionally trigger a warning toast for a condition the UI could prevent

Example:

- if compare requires `parent_branch_id`, do not call `onCompare(branchId, '')`

### 7. Type Quality

`0`:
- works by fighting the type system

`1`:
- type-safe enough, but awkward or lossy in places

`2`:
- types express the real backend/frontend contract cleanly with minimal casting

Check:

- avoid `as` casts unless unavoidable
- do not collapse rich response shapes into lossy local substitutes without a reason
- service functions should return existing repo types whenever possible
- component props should stay explicit and narrow

### 8. Tailwind and Styling Safety

`0`:
- dynamic classes that Tailwind cannot reliably see

`1`:
- styling works, but some classes are brittle

`2`:
- explicit class names and consistent utility usage

Check:

- avoid patterns like:

```tsx
`bg-${mode === 'dark' ? 'gray-900' : 'gray-100'}`
```

- prefer explicit conditional branches or utility helpers that preserve static class strings
- keep styling aligned with current [tailwind.config.js](/F:/Dev/Narrative-Engine/frontend/tailwind.config.js)

### 9. Mock/Live Boundary Discipline

`0`:
- mock behavior leaks into live flows unpredictably

`1`:
- boundaries exist, but are noisy or inconsistent

`2`:
- mock mode is explicit, contained, and returns repo-aligned types

Check:

- use `VITE_USE_MOCKS` only where the backend surface genuinely does not exist
- mock responses should match existing types
- live mode should never keep mock-only logging or banners unless intentional

### 10. Change Locality and Maintainability

`0`:
- the change works but makes the code harder to extend

`1`:
- acceptable, but leaves new duplication or unclear intent

`2`:
- the change reduces duplication and makes future work easier

Check:

- if the same logic appears in 3 files, centralize it
- if a component needs interaction behavior, use a callback prop instead of hard-coding navigation inside a leaf when a parent should own it
- prefer extending existing stores, services, and route helpers rather than creating parallel abstractions

## File-by-File Review Questions

Use these questions before approving work in common frontend file types.

### Service File Checklist

Applies to files like:

- [branches.ts](/F:/Dev/Narrative-Engine/frontend/src/services/branches.ts)
- [decisions.ts](/F:/Dev/Narrative-Engine/frontend/src/services/decisions.ts)
- [inspectLinks.ts](/F:/Dev/Narrative-Engine/frontend/src/services/inspectLinks.ts)
- [drafting.ts](/F:/Dev/Narrative-Engine/frontend/src/services/drafting.ts)
- [jobs.ts](/F:/Dev/Narrative-Engine/frontend/src/services/jobs.ts)

Questions:

- Does this file use the shared API configuration?
- Are payload keys exactly backend-aligned?
- Are list envelopes mapped consistently?
- Are 404, 409, and 500 treated meaningfully where needed?
- Is there any duplicated host/base path logic?
- Is there any mock-only logging or placeholder branching left behind?

### Component File Checklist

Applies to files like:

- [Layout.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/Layout.tsx)
- [DecisionTree.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/decisions/DecisionTree.tsx)
- [BranchCard.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/branches/BranchCard.tsx)
- [InspectRunLinkCard.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/inspectLinks/InspectRunLinkCard.tsx)
- [FindingCard.tsx](/F:/Dev/Narrative-Engine/frontend/src/components/review/FindingCard.tsx)

Questions:

- Is every button actionable?
- Are invalid actions prevented in the UI instead of passed down as empty strings or placeholders?
- Are loading and empty states explicit?
- Is there any console logging?
- Is there any sample/demo behavior still present?
- Are labels readable and free of encoding issues?

### Routing/Store File Checklist

Applies to files like:

- [App.tsx](/F:/Dev/Narrative-Engine/frontend/src/App.tsx)
- [Workspace.tsx](/F:/Dev/Narrative-Engine/frontend/src/views/Workspace.tsx)
- [routes.ts](/F:/Dev/Narrative-Engine/frontend/src/routes.ts)
- [uiStore.ts](/F:/Dev/Narrative-Engine/frontend/src/stores/uiStore.ts)

Questions:

- Does the route define the source of truth clearly?
- Can the page be refreshed on a deep route without losing mode/state correctness?
- Is navigation using the route helpers or equivalent stable logic?
- Is state duplicated unnecessarily between router and store?

## Automatic Failure Conditions

If any of these are true, the change is not high quality:

- `lint`, `typecheck`, or `build` fails
- user-visible `console.log` remains in the changed surface
- a button or CTA has no real action path
- a service duplicates API host/base configuration already available elsewhere
- a component relies on placeholder assumptions like “first node is root”
- a visible encoding artifact remains
- a changed flow uses mock behavior even though a live backend route already exists

## Target State for 10/10

The frontend is close to `10/10` when:

- all services share one clean API access pattern
- all route/state synchronization is explicit and robust
- all visible actions are real
- no placeholder logic remains in merged user flows
- empty/loading/error states are deliberate everywhere
- styling is static-safe and free of encoding noise
- the code is easier to extend after the change than before it

## Final Self-Check Prompt

Before declaring the frontend work complete, answer these with `yes`:

1. Does every changed component action have a real behavior?
2. Does every changed service use the correct backend contract?
3. Did I remove prototype logging and placeholder assumptions?
4. Did I avoid duplicating API configuration?
5. Can the route/state flow survive direct navigation and refresh?
6. Are loading, empty, and error states explicit?
7. Is the changed surface free of mojibake and brittle Tailwind patterns?
8. Did `npm run lint`, `npm run typecheck`, and `npm run build` pass?

If any answer is `no`, the work is not yet `10/10`.
