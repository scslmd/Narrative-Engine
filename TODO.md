# TODO

## CRITICAL

- [x] Remove reconstruction or recreation framing from the story-development docs package and rewrite it as an aspirational writing-product specification, especially anywhere the docs describe story-development features as "reconstruction" requirements instead of target product contracts.
- [x] Add one canonical docs contract table for story-development objects, with one approved name per object, a short definition, owning layer, and explicit aliases or replacements for terms that should no longer be used across the SRS, product spec, frontend SRS, and orchestrator spec.
- [x] Add one canonical docs contract table for stage states, artifact lifecycle states, suggestion lifecycle states, and execution states, then update all story-development docs to use the same enum names and explain any UI-only display mapping separately.
- [x] Resolve the current docs contradiction about what is already implemented versus still aspirational in the checker and inspect surfaces so agents can tell whether future tasks are extension work or net-new work.
- [x] Define the editable-flow removal contract precisely so "remove", "disable", "archive", "optional", and "delete custom stage" are no longer interchangeable in the docs.
- [x] Split the drafting contract into distinct canonical concepts for generated draft artifacts, user-authored manuscript state, proposed revisions, and promoted canonical outputs so provenance rules stay deterministic.
- [x] Replace broad frontend implementation waves with real deterministic task cards that each have one bounded screen family, one write scope, explicit dependencies, expected outputs, acceptance criteria, and verification.
- [x] Convert abstract feature verbs in the story-development docs into concrete orchestrator-callable operations with defined inputs, outputs, side effects, and done conditions.
- [x] Define the difference between stage type, project stage instance, and stage status so rename, redefine, reorder, and revisit behavior can be persisted without ambiguity.
- [x] Canonicalize planning terminology so the docs explicitly state whether cards are persisted planning objects, UI views over plan objects, or both, and remove conflicting plan versus card naming.
- [x] Implement `app/services/runtime_prompts.py` with a deterministic `architect` prompt builder that uses the accepted job payload plus project manifest context.
- [x] Generalize the inference adapter so `llama.cpp`, LM Studio, `vLLM`, and other OpenAI-compatible backends can be selected without orchestration changes.
- [x] Update `app/services/local_executor.py` so phase `P-100` calls `inferencer.generate_text()` instead of unconditional stub completion.
- [x] Implement the first real `architect` call in `app/services/local_executor.py` for phase `P-100`, using `app/services/runtime_prompts.py`, the generalized inferencer, and persisted step or lineage output.
- [x] Promote the first real `architect` runtime output from candidate lineage to canonical lineage using an explicit artifact registration policy.
- [x] Update `app/services/role_model_checker.py` so runtime-backed checking can be enabled per role while preserving stub fallback.
- [x] Map timeout, HTTP-status, and invalid-JSON failures in `app/inference/openai_compatible.py` to structured runtime error categories.
- [x] Persist runtime telemetry for provider name, provider version when available, prompt hash, input hash, output hash, token usage, and finish reason on runtime-backed steps.
- [x] Make project artifact endpoints for generated runtime outputs lineage-aware so failed `P-200`/`P-300` runs do not return placeholder `sequence` or `chapter-1` files as if they were successful canonical artifacts.
- [x] Ignore bootstrapped empty upstream artifacts in downstream runtime phases so `P-300` does not record empty `sequence` context as a real dependency.
- [x] Add explicit supersession behavior for rerun canonical job artifacts so repeated `P-200`/`P-300` successes do not leave multiple unsuperseded `CANONICAL` lineage rows.
- [ ] Rebuild `LocalExecutor` job processing so phases after the current `P-100`, `P-200`, and `P-300` slices run through explicit runtime-backed step handlers instead of one-step stub completion.
- [x] Add read-only API endpoints for step records and artifact lineage on both jobs and checker runs.
- [x] Implement `GET /jobs/{job_id}/steps` backed only by persisted step-record rows and the step projection contract.
- [x] Implement `GET /jobs/{job_id}/lineage` backed only by persisted artifact-lineage rows and the lineage projection contract.
- [x] Implement `GET /role-model-checker/{run_id}/steps` backed only by persisted step-record rows and the step projection contract.
- [x] Implement `GET /role-model-checker/{run_id}/lineage` backed only by persisted artifact-lineage rows and the lineage projection contract.
- [x] Update `.github/workflows/tests.yml` so CI runs `tests/test_inference_runtime.py` in addition to the existing pytest baseline.

## Core Runtime

- [x] Add a prompt-builder service that turns project context into provider-ready `architect` requests.
- [x] Execute one real provider-backed `architect` step through the existing job queue and attempt pipeline.
- [x] Execute one real provider-backed `sequencer` step through the existing job queue and attempt pipeline.
- [x] Execute one real provider-backed `drafter` step through the existing job queue and attempt pipeline.
- [x] Register `architect` runtime output through canonical artifact-lineage persistence.
- [x] Register `sequence` runtime output through canonical artifact-lineage persistence.
- [x] Register `chapter_1` runtime output through canonical artifact-lineage persistence.
- [ ] Rebuild remaining job phases on top of explicit runtime-backed step handlers.
- [ ] Rebuild the orchestrator/compiler path on top of durable step and artifact state.
- [x] Expand the role-model checker beyond stub execution with provider-backed per-role evaluation.
- [x] Add a concrete runtime adapter interface that supports multiple providers and a reusable OpenAI-compatible HTTP transport.
- [x] Wire the generalized inferencer into one real provider-backed `architect` execution path.
- [x] Persist runtime telemetry and hashes for each runtime-backed step.
- [x] Replace stub checker role execution with runtime-backed per-role evaluation while preserving current run and attempt semantics.

## Protocol Hardening

- [x] Persist immutable request snapshots and append-only event history for jobs and checker runs.
- [x] Add baseline attempt-lineage fields for jobs and checker runs.
- [x] Define the planning contract for per-step records and artifact lineage before runtime wiring.
- [x] Enforce the current run-state transition rules in services.
- [x] Return `202 Accepted` from job and checker start endpoints with status polling targets.
- [x] Introduce first-class attempt records instead of relying on a single mutable run row plus event stream.
- [x] Add queue idempotency keys and deterministic duplicate-submission handling.
- [x] Add worker claim or lease semantics for accepted jobs and checker runs in the local executor path.
- [x] Make status endpoints pure persisted projections over worker-managed state.
- [x] Add explicit retry metadata and operator retry flow on top of attempt lineage.
- [x] Add stale-lease reclaim semantics and reclaim events.
- [x] Add attempt-level executor telemetry for queue delay, executor identity, and finish reasons.
- [x] Add structured runtime telemetry for backend identity, hashes, token usage, and finish reasons.
- [x] Add `GET /jobs/{job_id}/steps` and `GET /role-model-checker/{run_id}/steps`.
- [x] Add `GET /jobs/{job_id}/lineage` and `GET /role-model-checker/{run_id}/lineage`.
- [ ] Add stable response schemas for attempt history, step history, and lineage history suitable for inspect views.

## Persistence

- [x] Add SQLite-backed operational persistence.
- [x] Harden SQLite with foreign keys, WAL mode, busy timeout, indexes, and schema versioning.
- [x] Move project reconciliation into an explicit sync or repair flow.
- [x] Add step-record and artifact-lineage persistence for the local executor path.
- [ ] Extend persistence to support orchestration attempts, richer artifact lineage, and projection endpoints.
- [x] Add artifact lineage supersession behavior for canonical project artifacts rather than checker-report-only lineage.
- [ ] Persist chapter-packet, sequence, and future story-bible artifacts through lineage-aware registration instead of flat file assumptions.
- [ ] Add persistence helpers for scene or chapter storyboard cards once frontend-backed planning state becomes canonical.

## Backend Engine Completion

- [x] BE-01 Canonical story-development enums and schema models:
  define the canonical backend enums and schema models for story-development state, flow, foundation, character, world bible, arc, planning, drafting, review, and inspect links in `app/schemas/`.
  Expected result: one importable schema contract aligned with `docs/Story Development Canonical Contract v0.1.md`.
  Verification: targeted schema tests cover enum values, object shape validation, and canonical aliases that should not be accepted as primary field names.
- [x] BE-02 Story-development SQLite persistence scaffolding:
  add operational SQLite tables and repository helpers for editable flow, brainstorm items, foundation revisions, character profiles, world bible entries, arc selection, planning objects, manuscript documents, revision suggestions, and review decisions.
  Expected result: durable persistence exists for canonical story-development objects without breaking existing jobs/checker/inspect tables.
  Note: this is the first backend stage for story-development persistence; we will need to return at the required later stages to finish the remaining service-layer build-out and the still-pending object families.
  Verification: targeted persistence tests cover table creation, round-trip CRUD for representative objects, and foreign-key behavior.
- [x] BE-02A Story-development persistence contract alignment:
  align the current persistence scaffold with the canonical schema layer by using canonical enum values, separating custom-stage identity from stage kind, and tightening record shapes around the accepted story-development contract.
  Expected result: persistence is safe for service-layer integration and no longer bakes in conflicting state or stage semantics.
  Verification: focused persistence tests cover canonical enum round-trips, custom-stage deletion eligibility metadata, and schema-aligned record boundaries.
- [x] BE-03 Editable flow service and repository slice:
  implement the first backend service slice for `StoryFlowDefinition`, `StoryFlowStage`, `StoryFlowEdge`, and editable-flow transitions using the canonical disable/archive/delete-custom semantics.
  Expected result: a backend service can create a default flow, add custom stages, rename/redefine stages, reorder stages, disable/archive stages, and reject invalid custom-stage deletion.
  Verification: focused service tests cover add, rename, redefine, reorder, disable, archive, delete-eligible-custom, and blocked deletion cases.
- [x] BE-03A Editable flow integration cleanup:
  rework the current editable-flow prototype to import canonical story-development schemas, prevent stage-id reuse after deletion, and validate dependency references before saving.
  Expected result: the editable-flow service is safe to build on for persistence and API wiring.
  Verification: focused service tests cover non-reused ids, invalid dependency rejection, and shared schema-type usage.
- [ ] BE-04 Brainstorm and promotion service slice:
  implement bounded backend operations for `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item`.
  Expected result: brainstorm items can be stored, grouped, and promoted into downstream story-development objects with provenance links.
  Verification: service and persistence tests cover keep/discard/park states and promotion recording.
- [ ] BE-05 Foundation profile and downstream-impact slice:
  implement `FoundationProfile` and `FoundationRevision` services plus downstream review-cue generation for foundation changes.
  Expected result: foundation updates remain editable after downstream work exists and create explicit review cues instead of silent overwrites.
  Verification: service tests cover revision history, active-profile reads, and downstream impact records.
- [ ] BE-06 Character, world bible, and arc-selection slice:
  implement bounded services for `CharacterProfile`, `RelationshipEdge`, `WorldBibleEntry`, `ArcCandidate`, `ArcSelection`, and `ArcStageMap`.
  Expected result: canonical story knowledge can be stored and compared independently of manuscript generation.
  Verification: persistence and service tests cover source-linked world facts, relationship updates, and advisory arc selection.
- [ ] BE-07 Planning objects and chapter-packet slice:
  implement `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket` services.
  Expected result: planning objects persist as canonical records and can be rendered later as UI card views without introducing a competing persisted card contract.
  Verification: service tests cover parent-child relationships, reorder behavior, and dependency preservation.
- [ ] BE-08 Draft artifact versus manuscript document separation:
  implement the backend state split between generated `DraftArtifact`, author-owned `ManuscriptDocument`, and non-destructive `RevisionSuggestion`.
  Expected result: generated prose, editable manuscript state, and proposed revisions remain distinct in persistence and service behavior.
  Verification: tests cover promotion into manuscript state without erasing source artifacts and suggestion acceptance via explicit decisions.
- [ ] BE-09 Review decisions and inspect links:
  implement `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` support so findings and suggestions can route back into planning, drafting, and inspect surfaces.
  Expected result: review outcomes become first-class backend records tied to source artifacts and runs.
  Verification: service tests cover accept/reject/defer/escalate decisions and inspect-link creation.
- [ ] BE-10 Story-development API surface:
  expose bounded API routes for the completed story-development slices only after their schema, persistence, and service contracts are stable.
  Expected result: API routes are thin projections over accepted backend contracts rather than speculative endpoints.
  Verification: route tests cover happy path, validation errors, and 404 behavior for the first shipped slices.

## Frontend

- [x] Build the current writer workflow prototype.
- [x] Add status polling and role-model checker result display.
- [x] Replace placeholder runtime messaging with production workflow copy.
- [ ] Add storyboard-driven three-column write layout with left storyboard rail, center manuscript, and right manuscript-aids rail.
- [ ] Add manuscript aids feature family with proposed-revision diff review, including sensory enrichment and perspective shift.
- [ ] Expand authoring, review, and artifact workflows to match the target product experience.
- [ ] Implement a left-rail storyboard that supports manual cards plus AI-generated scene summaries from current draft context.
- [ ] Implement manuscript aids right-rail sections for selection actions, scene actions, continuity actions, and revision actions.
- [ ] Add selection-based diff review UX with accept, reject, and refine controls for manuscript aids.
- [ ] Add storyboard jump-to-manuscript linking so each storyboard card opens the related draft location.
- [ ] Add chapter and scene status chips plus arc-stage labels to the storyboard and planning views.
- [ ] Add manuscript version-history UI with clear separation between local editing revisions and backend-generated artifacts.
- [ ] Add integrated checker-review workspace that can open findings beside the active manuscript selection.
- [ ] Add story arc selection and arc-stage display in the planning UI using `docs/Story Arc Paradigm Blueprint v0.1.md`.
- [ ] Add a story bible or codex side rail with pinned characters, locations, rules, promises, and continuity warnings.
- [ ] Add chapter packet builder UI that shows included references, constraints, and targeted scene goals before job launch.

## Docs Contract Hardening

- [x] Write a single "Story Development Canonical Contract" doc section or appendix that all other story-development docs reference for object names, lifecycle enums, and term mappings.
- [x] Update `docs/Story Development Product Spec v0.1.md` so editable-flow rules explicitly distinguish stage deletion from disabling, optionality, and archival behavior.
- [x] Update `docs/Narrative SRS v0.1.md` so story-development sections describe an aspirational writing product and stop using reconstruction-grade language for these features.
- [x] Update `docs/Narrative SRS v0.1.md` so story-development workflow states describe actual states rather than mixing stage categories with state enums.
- [x] Update `docs/Narrative SRS v0.1.md` and `docs/Frontend Design SRS v0.1.md` so implemented-now versus target-state language is internally consistent for checker runtime behavior and inspect surfaces.
- [x] Update `docs/Frontend Design SRS v0.1.md` so backend-object names match the canonical product and backend contract instead of introducing competing object labels without mappings.
- [x] Update `docs/Frontend Design SRS v0.1.md` section 19 so each frontend TODO becomes an agent-sized deterministic task card instead of a multi-surface implementation wave.
- [x] Update `docs/Orchestrator Deterministic Task Spec v0.1.md` with concrete callable operation templates for capture, promote, compare, detect, rewrite, review, and route task families.
- [x] Add a canonical drafting/provenance contract section that explains how generated artifacts, author-edited manuscript buffers, suggestion diffs, and promoted canonical outputs relate to each other.
- [x] Add a canonical planning contract section that states whether beat, sequence, chapter, and scene "cards" are persistence objects, presentation objects, or projections over plan records.

## Testing

- [x] Add smoke coverage for the current API surface.
- [x] Add persistence coverage for jobs, checker runs, and project projections.
- [x] Add contract coverage for planned step-record and artifact-lineage expectations.
- [x] Add live persistence coverage for step records and artifact lineage.
- [x] Add failure-mode coverage for duplicate submission, accepted-start polling, and terminal transition protection.
- [x] Add failure-mode coverage for idempotent replay and idempotency conflicts.
- [x] Add failure-mode tests for stale lease handling.
- [x] Add retry-lineage coverage for explicit operator requeue of failed jobs and checker runs.
- [x] Add failure-mode tests for partial persistence failure and lock contention.
- [ ] Add broader integration coverage for orchestration and runtime behavior.
- [x] Add regression coverage proving failed runtime jobs do not expose placeholder-generated project artifacts through `GET /projects/{project_id}/sequence` or `GET /projects/{project_id}/chapter-1`.
- [x] Add regression coverage proving rerun canonical job artifacts supersede prior lineage rows instead of accumulating multiple active `CANONICAL` entries.
- [x] Add API tests for `GET /jobs/{job_id}/steps`, `GET /jobs/{job_id}/lineage`, `GET /role-model-checker/{run_id}/steps`, and `GET /role-model-checker/{run_id}/lineage`.
- [ ] Add pagination and future attempt-filter tests for `GET /jobs/{job_id}/steps` and `GET /jobs/{job_id}/lineage`.
- [ ] Add pagination and future attempt-filter tests for `GET /role-model-checker/{run_id}/steps` and `GET /role-model-checker/{run_id}/lineage`.
- [ ] Add runtime integration tests for one real provider-backed `architect` step through the executor path.
- [ ] Add tests for manuscript-aid request contracts and diff-style response payloads once the backend surface is defined.
- [x] Update CI to run `tests/test_inference_runtime.py` and current projection-endpoint tests on push and pull request.

## Subagent Queue

- [x] `Curie`: implement BE-01 by owning `app/schemas/story_development.py`, `app/schemas/enums.py`, `app/schemas/__init__.py`, and a new targeted schema test file. Do not edit persistence or service files. You are not alone in the codebase; accommodate others' changes and do not revert them.
- [x] `Kepler`: implement BE-02 by owning `app/persistence/sqlite.py`, a new `app/persistence/story_development.py`, `app/persistence/__init__.py`, and a new targeted persistence test file. Do not edit schema or service files unless a minimal import/export adjustment is required. You are not alone in the codebase; accommodate others' changes and do not revert them.
- [x] `Pasteur`: implement BE-03 by owning a new editable-flow service module plus focused service tests, using the canonical docs contract and existing persistence/service patterns. Do not edit schema files and do not replace others' work; adjust to their changes instead.
- [ ] `Ada`: implement BE-04 by owning the brainstorm and promotion service slice with bounded `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item` operations. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Lovelace`: implement BE-05 by owning the foundation profile and downstream-impact service slice with bounded revision history behavior and review-cue generation. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Euler`: implement BE-06 by owning the character, world bible, and arc-selection service slice with bounded compare, upsert, select, and stage-map operations. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Noether-2`: implement BE-07 by owning the planning objects and chapter-packet service slice with bounded plan creation, reorder, and dependency-preservation operations. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Curie-2`: implement BE-08 by owning the draft artifact versus manuscript document separation slice with bounded generate, revise, and promote operations. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Feynman`: implement BE-09 by owning the review decision and inspect-link slice with bounded finding routing, decision recording, and inspect linkage operations. Keep the write scope limited to the new service module and a focused test file.
- [ ] `Hopper`: implement BE-10 by owning the first story-development API surface slice once the preceding schemas, persistence, and service contracts are stable. Keep the write scope limited to thin route wiring and focused route tests.
- [ ] `Volta`: update `docs/Narrative SRS v0.1.md` so the story-development sections describe an aspirational writing product, remove reconstruction-specific framing for those features, resolve implemented-versus-target-state contradictions, and align workflow-state terminology with the canonical enum set once defined.
- [ ] `Kant`: update `docs/Frontend Design SRS v0.1.md` so object names, workflow states, and deterministic frontend task cards match the canonical contract and no longer bundle multiple screen families into one agent task.
- [ ] `Archimedes`: update `docs/Orchestrator Deterministic Task Spec v0.1.md` so each story-development feature area includes callable operation shapes with expected inputs, outputs, side effects, and verification, and so the safe-assignment guidance matches the new narrower task cards.
- [ ] `Hypatia`: update `docs/Story Development Product Spec v0.1.md` with the canonical editable-flow semantics, stage type versus stage instance versus stage status split, and explicit planning versus card terminology.
- [ ] `Maxwell`: author a canonical docs appendix or companion contract section that lists approved object names, lifecycle enums, forbidden aliases, and cross-doc mappings for all story-development features.
- [x] `Kuhn`: create `docs/Inference Runtime Blueprint v0.1.md` that documents provider selection, environment variables, request/response contract, and runtime error taxonomy for `llama.cpp`, LM Studio, and `vLLM`.
- [x] `Beauvoir`: add deterministic inference-backend failure tests in `tests/test_inference_backend_failures.py` covering timeout, HTTP error, and invalid-JSON cases for the OpenAI-compatible adapter.
- [x] `Newton`: update `docs/Frontend Design SRS v0.1.md` so the UI explicitly supports runtime-provider visibility, model-source visibility, and inspect views for step and lineage endpoints.
- [x] `Planck`: update `.github/workflows/tests.yml` so CI includes `tests/test_inference_runtime.py` and document the exact CI command in `docs/Validation Notes v0.1.md`.
- [x] `Cicero`: create `docs/Step and Lineage API Projection Blueprint v0.1.md` defining deterministic response shapes for the planned step and lineage inspect endpoints.
- [x] `Maxwell`: create `docs/Runtime Telemetry Contract v0.1.md` defining required persisted telemetry fields, hash inputs, finish reasons, and error categories for provider-backed runs.
- [x] `Worker`: implement the first real `architect` call for job phase `P-100` in `app/services/local_executor.py`, including prompt building, inferencer call, persisted output, and tests.
- [x] `Beauvoir`: add deterministic API tests for the four step/lineage projection endpoints, including empty-state and 404 behavior.
- [x] `Cicero`: update `docs/Step and Lineage API Projection Blueprint v0.1.md` if needed so it exactly matches the endpoint response contract implemented in code.
- [x] `Newton`: update `docs/Frontend Design SRS v0.1.md` with explicit inspect-view expectations for the four public step/lineage endpoints once their contract is locked.
- [x] `Planck`: add CI coverage for the new projection-endpoint tests after they land.
- [x] `Kuhn`: review the repo for encoding or BOM issues that could break parsing, packaging, or test execution, and fix only concrete safe issues.
  Residual low-risk note: no UTF-8/BOM/control-character blockers were found in tracked source, docs, tests, or config files; a small set of files still mixes mostly-LF text with a single CRLF line ending, but nothing currently appears parser-breaking.
- [x] `Maxwell`: create `docs/Runtime Error Mapping Blueprint v0.1.md` that turns current inferencer failures into deterministic runtime error categories suitable for persistence.
- [x] `Cicero`: create `docs/Step and Lineage API Test Matrix v0.1.md` that enumerates required endpoint cases for happy path, empty state, 404, ordering, and future attempt filtering.
- [x] `Newton`: draft inspect-mode component inventory in `docs/Frontend Design SRS v0.1.md` for step timeline, lineage list, and provenance badges using the current minimal endpoint envelopes.
- [x] `Planck`: prepare the exact CI command expansion for projection-endpoint tests and report the final workflow command expected once the test file names are locked.
- [x] `Maxwell`: implement structured runtime error mapping in `app/inference/openai_compatible.py` and the runtime-backed `P-100` executor path so failures persist stable `error_category`, `error_code`, `finish_reason`, and `retryable` behavior.
- [x] `Beauvoir`: add deterministic tests for structured runtime error mapping and persisted failure behavior on the `P-100` architect path.
- [x] `Cicero`: implement runtime telemetry persistence for the real `P-100` step, including prompt/input/output hashes and provider token usage when present.
- [x] `Planck`: add deterministic tests for runtime telemetry fields persisted on `P-100` step records and artifact lineage.
- [x] `Newton`: implement the first runtime-backed checker role slice in `app/services/role_model_checker.py` for `architect`, preserving stub fallback for the other roles.
- [x] `Kuhn`: review and sync the backend docs after these runtime/error/telemetry changes land so the SRS and runtime blueprints remain reconstruction-grade.
- [x] `Hypatia`: make project artifact reads lineage-aware for generated runtime outputs so failed `P-200`/`P-300` runs do not return placeholder `sequence` or `chapter-1` files through existing project endpoints.
- [x] `Faraday`: update downstream runtime phases to ignore empty bootstrapped upstream artifacts and only record real dependency provenance in step input refs and source hashes.
- [x] `Copernicus`: implement canonical lineage supersession for rerun `sequence` and `chapter_1` artifacts and add deterministic regression tests for repeated successful runs.
