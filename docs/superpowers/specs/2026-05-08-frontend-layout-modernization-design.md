# Frontend Layout Modernization Design

Date: 2026-05-08
Scope: React + TypeScript frontend in `frontend/`, all user-facing views

## 1. Goals

Modernize the frontend layout across all views with one coherent system that improves:
- Information architecture and navigation clarity
- Visual hierarchy, spacing, typography, and interaction consistency
- Workflow efficiency with clearer primary actions and fewer dead-ends
- Accessibility and responsive behavior (desktop, tablet, mobile, keyboard)

Non-goals:
- No backend contract changes
- No route contract changes
- No speculative feature additions unrelated to layout/UX

## 2. Current Pain Points

- Inconsistent page scaffolding between views (`ProjectList`, workspace modes, guided setup)
- Navigation/context awareness varies by route; active location and cross-view transitions are not always clear
- Repeated ad hoc section/action layouts create uneven hierarchy and CTA placement
- Empty/loading/error states differ by view in tone, actionability, and density
- Responsive behavior is uneven, with some panels and content blocks not degrading cleanly

## 3. Recommended Approach

Adopt a foundation-first redesign:
1. Define shared shell and layout primitives first.
2. Apply the same structure and interaction rules across all views.
3. Validate with focused UI tests and full frontend checks.

Why:
- Minimizes pattern drift.
- Reduces rework versus isolated view-by-view changes.
- Produces a predictable UX system for future feature additions.

## 4. Target UX Architecture

### 4.1 Global App Shell

Introduce/standardize a route-aware shell pattern:
- Top app bar: project context, primary workspace location, global utilities
- Context nav rail/tabs: stable mode navigation for workspace routes
- Main content column: single clear page title and primary task area
- Optional secondary panel: contextual details/actions only where needed

Rules:
- Exactly one primary CTA area per view (usually in page action bar)
- Consistent breadcrumbs/title/meta placement
- Active route always visibly indicated

### 4.2 View Composition Rules

Each view follows this structure:
1. Page header (title + concise supporting text)
2. Action bar (primary CTA + secondary actions)
3. Content sections (cards/panels with consistent spacing rhythm)
4. Status zones (inline errors, empty states, loading skeletons)

Spacing and density:
- Shared container widths and gutters
- Standardized vertical rhythm for section boundaries
- Predictable card padding and heading scale

### 4.3 Navigation and Route Logic

Keep route-driven state as source of truth and clarify transitions:
- Preserve project context across mode switches
- Ensure deep links render complete, non-dead-end states
- Keep inspect/review/write transitions explicit and reversible

### 4.4 Accessibility and Responsiveness

Accessibility baseline:
- Semantic landmarks for shell regions
- Keyboard-reachable primary/secondary controls
- Visible focus styles and contrast-safe state cues
- Clear aria labeling for icon-only actions

Responsive baseline:
- Desktop: full shell with contextual side content when useful
- Tablet: condensed nav, preserved action bar priority
- Mobile: stacked sections, sticky primary CTA zone where appropriate

## 5. Component System Changes

Standardize or introduce shared UI primitives:
- Page container/layout wrapper
- Page header block
- Action bar
- Section panel/card shell
- Empty state block
- Error/retry block
- Loading skeleton patterns

Apply these primitives across:
- `ProjectList`
- Workspace modes (`plan`, `write`, `review`, `inspect`, `braindump`, `generate`, `canon`)
- `GuidedSetupView`

## 6. Workflow Efficiency Improvements

- Promote one clear next-step CTA per view
- Reduce scattered action placement; align actions in predictable bars
- Surface status/progress closer to task area
- Avoid navigation branches that land in low-context screens

## 7. Error and State Strategy

Unify state presentation contract:
- Loading: skeleton or progressive placeholders aligned to final layout
- Empty: explain why empty + actionable next step
- Error: concise failure reason + retry/recovery action

No silent failures in primary surfaces; user-visible actions must always resolve to clear feedback.

## 8. Testing and Validation

Frontend validation required after implementation:
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`

Targeted test updates/additions:
- Shell/navigation active state assertions
- Route-to-layout rendering consistency checks
- Responsive behavior snapshots/assertions for core shell
- Primary CTA placement/presence checks in key views

## 9. Implementation Boundaries

- Preserve existing API/service contracts and route paths.
- Keep Zustand/React Query usage patterns intact.
- Avoid unrelated refactors unless required by the new shared layout primitives.
- Prefer minimal logical changes when visual/structural updates are sufficient.

## 10. Success Criteria

The modernization is successful when:
- All major views share one coherent shell and section rhythm.
- Users can identify current location, next action, and navigation options immediately.
- Primary workflows require fewer ambiguous transitions.
- Keyboard navigation and small-screen usage remain practical and clear.
- Frontend checks pass with no new errors and tests cover key layout behavior.
