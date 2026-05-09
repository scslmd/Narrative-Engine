# Architecture Consolidation (Next Iteration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce frontend orchestration complexity and stabilize domain boundaries without changing external API behavior.

**Architecture:** Consolidate by moving orchestration out of large views/hooks into domain controllers and reusable query/mutation wrappers. Keep route-driven navigation as source of truth, keep `services/*` as HTTP boundary, and make UI components consume typed domain-state hooks instead of ad hoc per-view query bundles.

**Tech Stack:** React, TypeScript, React Query, Zustand, FastAPI backend (unchanged), Vitest, ESLint.

---

## 1. Architecture Assessment (Current)

### What already works well
- Layering is clear: `services` (transport) -> hooks/views (orchestration) -> components (presentation).
- Route-driven workspace state is consistent and supports deep-link UX.
- API export coverage is complete and validated.

### Consolidation hotspots
- `frontend/src/views/PlanningView.tsx` combines tab routing, domain orchestration, mutation policy, and UI composition.
- `frontend/src/hooks/usePlanningTab.ts` is a mega-hook mixing 10+ subdomains and extensive form-state logic.
- `frontend/src/views/CanonView.tsx` and `frontend/src/components/canon/CanonWorkshop.tsx` split orchestration in a way that leaks domain concerns into presentation.
- `frontend/src/views/GenerationView.tsx` mixes run list UX with packet/run hydration and fork mutation orchestration.
- `frontend/src/hooks/useWritingView.ts` carries document selection, drafting, revision, assist polling, and optimistic state in one module.

### Consolidation objective
Create domain controllers with narrow responsibilities and explicit ownership:
- Planning domain
- Canon domain
- Generation domain
- Writing/assist domain

---

## 2. Target Structure (End State)

### New architecture rules
- Views own route selection and layout only.
- Domain hooks own query/mutation orchestration and cache invalidation policy.
- Components own rendering and user event callbacks only.
- Service files remain pure HTTP clients (no UI state, no view coupling).

### Proposed file structure additions
- `frontend/src/domains/planning/*`
- `frontend/src/domains/canon/*`
- `frontend/src/domains/generation/*`
- `frontend/src/domains/writing/*`

Each domain folder should include:
- `queries.ts` (query key builders + queryFns)
- `mutations.ts` (mutationFns + invalidation helpers)
- `use<Domain>Controller.ts` (orchestration hook consumed by views)
- `types.ts` (domain-local UI state types only)

---

## 3. Execution Plan (Next Iteration)

### Task A: Planning Domain Split
**Files:**
- Create: `frontend/src/domains/planning/queries.ts`
- Create: `frontend/src/domains/planning/mutations.ts`
- Create: `frontend/src/domains/planning/usePlanningController.ts`
- Modify: `frontend/src/hooks/usePlanningTab.ts`
- Modify: `frontend/src/views/PlanningView.tsx`

- [ ] Move sequence/chapter/scene/beat query wiring from `usePlanningTab` into `domains/planning/queries.ts`.
- [ ] Move planning mutations and invalidation policy into `domains/planning/mutations.ts`.
- [ ] Keep `usePlanningTab` as compatibility facade that delegates to `usePlanningController`.
- [ ] Remove direct service imports from `PlanningView` except domain controller and route helpers.
- [ ] Preserve existing query keys to avoid cache bust behavior changes.

Acceptance:
- `PlanningView.tsx` no longer imports planning/character/world-bible services directly.
- `usePlanningTab.ts` line count reduced by at least 30% with identical behavior.

---

### Task B: Canon Orchestration Cleanup
**Files:**
- Create: `frontend/src/domains/canon/useCanonController.ts`
- Modify: `frontend/src/views/CanonView.tsx`
- Modify: `frontend/src/components/canon/CanonWorkshop.tsx`

- [ ] Centralize profile/annotation/materialization/generation orchestration in `useCanonController`.
- [ ] Convert `CanonWorkshop` to presentation-first callbacks with narrow prop surface.
- [ ] Remove duplicate mutation ownership between view and component.

Acceptance:
- `CanonView.tsx` owns route + controller only.
- `CanonWorkshop.tsx` has no direct domain policy branching (only UI event emission).

---

### Task C: Generation Run/Packet/Fork Controller
**Files:**
- Create: `frontend/src/domains/generation/useGenerationController.ts`
- Modify: `frontend/src/views/GenerationView.tsx`
- Modify: `frontend/src/components/generation/GeneratedStoryReview.tsx` (if needed for narrowed props)

- [ ] Move run selection, gates, packet hydration, and fork orchestration into controller.
- [ ] Keep wizard and run-card rendering in view/components.
- [ ] Standardize retry/fork toast and error mapping in one place.

Acceptance:
- `GenerationView.tsx` no longer directly owns query/mutation policy logic.
- Retry/fork behavior remains unchanged from user perspective.

---

### Task D: Writing + Assist Split
**Files:**
- Create: `frontend/src/domains/writing/useWritingDocumentController.ts`
- Create: `frontend/src/domains/writing/useAssistController.ts`
- Modify: `frontend/src/hooks/useWritingView.ts`
- Modify: `frontend/src/hooks/useManuscriptAssist.ts`

- [ ] Split manuscript/draft lifecycle from assist polling and suggestion actions.
- [ ] Replace inline polling loop ownership with dedicated assist controller.
- [ ] Keep existing public hook return contracts stable for current components.

Acceptance:
- `useWritingView.ts` reduced to composition of smaller controllers.
- Assist retry/gates/suggestions are owned by one controller module.

---

### Task E: Shared Query/Mutation Utilities
**Files:**
- Create: `frontend/src/domains/shared/invalidation.ts`
- Create: `frontend/src/domains/shared/queryKeys.ts`
- Modify: domain controllers created above

- [ ] Extract repeated invalidation patterns into helper utilities.
- [ ] Extract query key builders for planning/canon/generation/writing domains.
- [ ] Remove ad hoc string array query keys scattered across views.

Acceptance:
- Domain controllers use shared key builders.
- Invalidation behavior is explicit and consistent.

---

### Task F: Validation + Documentation
**Files:**
- Modify: `docs/Codebase Map.md`
- Modify: `AGENTS.md` (only if new architectural rule needs codifying)
- Modify: relevant test files under `frontend/src/**/*.test.tsx`

- [ ] Add targeted unit tests for each domain controller.
- [ ] Verify existing integration tests still pass.
- [ ] Update architecture docs to reflect new domain controller layout.

Acceptance:
- `cd frontend && npm run lint` passes.
- `cd frontend && npm run typecheck` passes.
- `cd frontend && npm run test -- --run` passes.
- Codebase map reflects consolidated structure.

---

## 4. Risk Controls

- Do not change backend contract shapes during this consolidation.
- Do not rewrite UI layout or styling during this iteration.
- Keep current route paths and query keys stable unless explicitly migrated with tests.
- Land in small commits per task to isolate regressions.

---

## 5. Suggested Iteration Order

1. Task A (Planning split)
2. Task C (Generation controller)
3. Task B (Canon cleanup)
4. Task D (Writing/assist split)
5. Task E (shared utilities)
6. Task F (validation/docs)

This order de-risks the largest orchestration hotspot first and reuses patterns across later domains.
