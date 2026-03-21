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
