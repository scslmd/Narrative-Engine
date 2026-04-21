# TODO

## Current Truth

- The active documentation surface is `README.md`, `AGENTS.md`, `docs/BACKEND_API_REFERENCE.md`, and the current docs under `docs/`.
- Latest verified validation baseline:
  - `python -m pytest -q -p no:cacheprovider` -> `801 passed, 9 skipped` (0 pre-existing failures. Remaining 9 skips are platform-specific.)
  - `cd frontend && npm run lint` -> passed
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run build` -> passed
- The React frontend is merged and is now the default shipped frontend surface.
- Inspect deep links and review-driven "Jump to Source" navigation are route-based and renderable through the existing inspect screen.
- Temporary review notes, executor task dumps, and stale readiness checklists belong under `docs/archive/`, not in the active docs surface.

## Active Backlog

### Pending Work

#### Persistence and Runtime Expansion

- [x] Persist chapter-packet, sequence, and storyboard cards through lineage-aware registration.
  - Completed: `ChapterPacketService.register_packet_as_lineage()`, `SequencePlanService.register_plan_as_lineage()`, `StoryboardCardService.register_card_as_lineage()` now tested with 12 integration tests in `tests/test_lineage_aware_artifacts.py`. Bugfixes: added missing `StoryArtifactLifecycleState` import to `storyboard_cards.py`, moved `get_packet` call inside try block in `chapter_packets.py`.
- [x] Expand manuscript-aid integration tests.
  - Completed: 15 integration tests in `tests/test_manuscript_aid_integration.py` covering manuscript document CRUD, revision suggestion CRUD, cross-project isolation, and document filtering.
- [x] Add broader integration coverage for orchestration and runtime behavior.
   - Completed: 14 new E2E tests across `tests/test_executor_e2e_runtime.py` and `tests/test_story_bible_lineage.py` covering: checker report persistence, deterministic critic, P-400 missing upstream artifacts, staged/backup file cleanup, project isolation, job status transitions, job retry attempts, P-400 empty output, full pipeline order guarantee, story-bible content hash stability, fallback file read, and supersession chain verification.

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
- 801 tests passing across the full suite (22 new: 12 lineage-aware artifact tests + 15 manuscript aid integration tests + 14 executor/story-bible E2E tests - 19 original + 22 fixed = 801 total. Bugfix: `create_inspect_link` incorrectly normalized `object_kind` to `StoryObjectType`, rejecting free-form strings like "job", "checker", "manuscript". Rewrote `test_review_routing_post.py` with proper `tmp_path` DB isolation.)

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
