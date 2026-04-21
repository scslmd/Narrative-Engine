# TODO

## Current Truth

- The active documentation surface is `README.md`, `AGENTS.md`, `docs/BACKEND_API_REFERENCE.md`, and the current docs under `docs/`.
- Latest verified validation baseline:
  - `python -m pytest -q -p no:cacheprovider` -> `738 passed, 9 skipped` (0 pre-existing failures. Remaining 9 skips are platform-specific.)
  - `cd frontend && npm run lint` -> passed
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run build` -> passed
- The React frontend is merged and is now the default shipped frontend surface.
- Inspect deep links and review-driven "Jump to Source" navigation are route-based and renderable through the existing inspect screen.
- The remaining work is primarily backend expansion, deeper persistence hardening, and frontend features that still depend on backend APIs not yet implemented.
- Temporary review notes, executor task dumps, and stale readiness checklists belong under `docs/archive/`, not in the active docs surface.

## Active Backlog

### Pending Work

#### Persistence and Runtime Expansion

- [ ] Persist chapter-packet, sequence, and future story-bible artifacts through lineage-aware registration instead of flat file assumptions.
  - Partial: `ChapterPacketService` and `SequencePlanService` created in `app/services/` with repository-level CRUD and lineage-aware registration helpers.
  - Pending: API endpoints, frontend services, and integration tests for chapter-packet and sequence-plan persistence.
- [ ] Add persistence helpers for scene or chapter storyboard cards once frontend-backed planning state becomes canonical.
  - Partial: `StoryboardCardService` created in `app/services/storyboard_cards.py` with persistence helpers.
  - Pending: API endpoints and frontend integration once storyboard cards become a canonical planning object.
- [ ] Add broader integration coverage for orchestration and runtime behavior.
  - Partial: `tests/test_orchestration_integration.py` (7 integration tests) created covering job creation, checker runs, step record persistence, and artifact lineage.
  - Pending: Full end-to-end executor-based integration tests that exercise the local executor daemon threads.
- [ ] Add tests for manuscript-aid request contracts and diff-style response payloads once the backend surface is defined.
  - Partial: `tests/test_manuscript_aid_contracts.py` (10 tests) created covering `DraftingService` request/response contracts, diff payloads, and revision suggestion workflows.
  - Pending: Integration coverage that exercises the actual API endpoints producing these payloads.

## Completed Milestones (Summary)

Full details archived in `docs/archive/TODO_Completed_Milestones_Archive.md`.

### v1.0 Release -- All Complete
All 14 v1.0 release items (V1-001 through V1-015) completed and scope-verified.
The product surface includes routed planning, writing, review, and inspect workspaces
with real API backing.

### Backend Security & Reliability -- All Complete
- SEC-01 through SEC-05: Input validation, CORS, request size limits, path traversal, rate limiting
- REL-01 through REL-10: Circuit breaker, idempotency, thread safety, backup, health checks,
  API key auth, authorization, telemetry, file permissions, audit logging
- All 319 security/reliability tests pass

### Core Runtime & Protocol -- All Complete
- Deterministic job orchestration with P-100 through P-400 phases
- Role-model checker with runtime-backed per-role evaluation
- Attempt lineage, step records, artifact lineage, supersession behavior
- Projection endpoints: GET /jobs/{id}/steps, /lineage, /attempts and /role-model-checker equivalents

### Story Development Backend -- All Complete
- BE-01 through BE-11E: Schemas, persistence, services, and API surface for branching,
  decisions, review, planning, drafting, characters, world bible, arcs, and brainstorm
- 738 tests passing across the full suite

### Frontend -- All Complete
- React + TypeScript frontend (FE-001 through FE-032)
- Routed workspace: Plan, Write, Review, Inspect
- Real API backing for all shipped surfaces
- Manuscript editor with aids, diff viewer, selection lifecycle
- Branch UI, decision tree, inspect run links

### Deferred Mutations -- All Complete
- Arc selection mutations: POST /arcs/candidates, POST /arcs/comparisons, POST /arcs/selections, PATCH /arcs/selections/{id}, DELETE /arcs/selections/{id}, POST /arcs/stage-maps
- Character relationship mutations: GET /relationships (list-all), PATCH /relationships/{id}, DELETE /relationships/{id}
- Planning board reorder: POST /planning/reorder (supports sequence, chapter, scene plan kinds)
- 23 new integration tests across test_deferred_mutations.py

### Testing
- Smoke coverage, persistence coverage, contract coverage, failure-mode coverage
- CI runs full suite on push and pull request
