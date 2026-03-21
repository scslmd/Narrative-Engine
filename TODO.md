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
- [x] Rebuild `LocalExecutor` job processing so the current phase set `P-100`, `P-200`, `P-300`, and `P-400` runs through explicit runtime-backed step handlers instead of one-step stub completion.
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
- [x] Rebuild the current job-phase set on top of explicit runtime-backed step handlers.
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
- [x] BE-04 Brainstorm and promotion service slice:
  implement bounded backend operations for `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item`.
  Expected result: brainstorm items can be stored, grouped, and promoted into downstream story-development objects with provenance links.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/brainstorm/*` routes.
  Verification: service and persistence tests cover keep/discard/park states and promotion recording.
- [x] BE-05 Foundation profile and downstream-impact slice:
  implement `FoundationProfile` and `FoundationRevision` services plus downstream review-cue generation for foundation changes.
  Expected result: foundation updates remain editable after downstream work exists and create explicit review cues instead of silent overwrites.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/foundation/*` routes.
  Verification: service tests cover revision history, active-profile reads, and downstream impact records.
- [x] BE-06A Story-knowledge persistence completion:
  add canonical persistence tables and repository helpers for `RelationshipEdge`, `ArcCandidate`, `ArcSelection`, and `ArcStageMap`, and confirm `CharacterProfile` and `WorldBibleEntry` persistence remain aligned to the same contract.
  Expected result: all BE-06 canonical objects have durable backend storage and repository operations instead of mixed persistence-plus-service-local state.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, and `/story-development/arcs/*` routes.
  Verification: targeted persistence tests cover relationship-edge round trips, active arc selection storage, arc-stage-map persistence, and repository-backed candidate comparison inputs.
- [x] BE-06B Arc comparison persistence and review contract:
  add canonical persistence tables and repository helpers for `ArcComparisonRecord`, and update arc-selection storage so selections can link to the comparison records that informed the decision.
  Expected result: arc comparison history becomes a first-class persisted object the user can review later instead of advisory service-local memory.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/arcs/*` routes.
  Verification: targeted persistence tests cover ranked comparison record round trips, candidate-set storage, selection-to-comparison links, and multi-comparison history retrieval in deterministic order.
- [x] BE-06C Story decision node persistence contract:
  add canonical persistence tables and repository helpers for `StoryDecisionNode` so user-made story-shaping decisions such as arc pivots, flow changes, and future comparable direction changes remain reviewable over time as a typed timeline and tree.
  Expected result: story-shaping user decisions become first-class persisted nodes rather than only implicit changes to current state.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/decisions/*`, `/story-development/arcs/*`, and future flow-history routes.
  Verification: targeted persistence tests cover decision-subject links, decision type storage, prior-state and new-state summaries or refs, rationale or notes storage, actor identity, chronological retrieval, and links to affected canonical objects.
- [x] BE-06D Arc comparison and decision-node schema alignment:
  add canonical schema support for `ArcComparisonRecord`, selection-to-comparison links, and `StoryDecisionNode` enum-driven timeline and tree fields in `app/schemas/story_development.py`.
  Expected result: the schema layer matches the updated docs contract so persistence and services can exchange typed reviewable decision objects without ad hoc dict payloads.
  Expected endpoints: none in this slice; schema-only foundation for later `/story-development/arcs/comparisons/*`, `/story-development/decisions/*`, and related routes.
  Verification: targeted schema tests cover object validation, required timeline fields, selection link fields, and canonical naming.
- [x] BE-06 Character, world bible, and arc-selection slice:
  implement bounded services for `CharacterProfile`, `RelationshipEdge`, `WorldBibleEntry`, `ArcCandidate`, `ArcComparisonRecord`, `ArcSelection`, `ArcStageMap`, and related `StoryDecisionNode` creation for user choices.
  Expected result: canonical story knowledge can be stored and compared independently of manuscript generation.
  Note: accept this slice only after `BE-06A`, `BE-06B`, `BE-06C`, and `BE-06D` land, because the docs require these objects to be canonical persisted records rather than service-local state.
  Verification: persistence and service tests cover source-linked world facts, relationship updates, persisted arc comparison review, advisory arc selection, and reviewable user decision history.
- [x] BE-07A Planning persistence scaffold:
  add canonical persistence tables and repository helpers for `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket`.
  Expected result: planning objects exist as durable backend records before the planning service slice is implemented.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/planning/*` routes.
  Verification: targeted persistence tests cover parent-child relationships, ordering fields, dependency rows, and chapter-packet round trips.
- [x] BE-07 Planning objects and chapter-packet slice:
  implement `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket` services.
  Expected result: planning objects persist as canonical records and can be rendered later as UI card views without introducing a competing persisted card contract.
  Note: this slice depends on `BE-07A`; do not implement it as an in-memory or service-local workaround.
  Verification: service tests cover parent-child relationships, reorder behavior, and dependency preservation.
- [x] BE-08A Drafting persistence scaffold:
  add canonical persistence tables and repository helpers for `DraftArtifact`, `ManuscriptDocument`, and `RevisionSuggestion` before implementing manuscript-state services.
  Expected result: generated prose, author-owned manuscript state, and non-destructive revision suggestions all have durable backend storage with no service-local placeholders.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/drafting/*`, `/story-development/manuscript/*`, and `/story-development/revisions/*` routes.
  Verification: targeted persistence tests cover draft-artifact round trips, manuscript-document version storage, and revision-suggestion persistence without overwriting source text.
- [x] BE-08 Draft artifact versus manuscript document separation:
  implement the backend state split between generated `DraftArtifact`, author-owned `ManuscriptDocument`, and non-destructive `RevisionSuggestion`, including continuation, constrained rewrite, alternate-variant, and provenance-preserving promotion behavior.
  Expected result: generated prose, editable manuscript state, and proposed revisions remain distinct in persistence and service behavior, and accepted manuscript changes do not erase originating draft artifacts or their lineage.
  Note: this slice depends on `BE-08A`; do not implement it against process-local or browser-local placeholder state.
  Verification: tests cover promotion into manuscript state without erasing source artifacts, continuation and rewrite flows that preserve provenance, alternate-variant storage, and suggestion acceptance via explicit decisions.
- [x] BE-09B Review and inspect persistence scaffold:
  add canonical persistence tables and repository helpers for `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` before implementing review-routing services.
  Expected result: review findings, review decisions, and inspect links become durable backend records tied to source objects and runs.
  Expected endpoints: none in this slice; persistence-only foundation for later `/story-development/review/*` and inspect-linked workflow routes.
  Verification: targeted persistence tests cover finding storage, decision storage, inspect-link round trips, and stable source-object linkage.
- [x] BE-09 Review decisions and inspect links:
  implement `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` support so findings and suggestions can route back into planning, drafting, and inspect surfaces.
  Expected result: review outcomes become first-class backend records tied to source artifacts and runs.
  Note: this slice depends on `BE-09B` and `BE-08`; do not implement it against process-local review state or against placeholder manuscript or suggestion targets.
  Verification: service tests cover accept/reject/defer/escalate/refine decisions, inspect-link creation, and routing findings back into planning or drafting using canonical service boundaries rather than direct state mutation.
- [x] BE-09A Story decision review surface:
  implement bounded backend support so `StoryDecisionNode` objects can be listed and linked from the related story-development objects they affected.
  Expected result: the user can return later and review why a story direction changed without inferring history from current state alone.
  Expected endpoints: none in this slice; backend foundation for later `/story-development/decisions/*` routes and related object detail screens.
  Verification: service tests cover deterministic ordering, affected-object links, retrieval of prior superseded decisions, and timeline-ready output fields for what changed from what to what and why.
- [x] BE-11 Story branching canonical contract and persistence scaffold:
  add canonical backend schemas and persistence support for `StoryBranch`, `BranchPoint`, `BranchStateRef`, `BranchComparisonRecord`, and `BranchMergeDecision`, explicitly modeled as structured application objects rather than Git commits or branches.
  Expected result: storyline forking becomes a first-class backend capability with durable branch identity, branch origin, branch comparisons, and merge decisions.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` and related branching routes.
  Verification: targeted schema and persistence tests cover branch creation metadata, branch-point links, active-branch selection, branch comparison history, and explicit merge-decision storage.
- [x] BE-11A Story branch identity and branch-point persistence:
  add canonical schema and persistence support for `StoryBranch` and `BranchPoint`, including branch origin, branch name, source node, and active or archived branch state.
  Expected result: branch identity and the decision-node fork point become durable backend objects without compare or merge logic yet.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` routes.
  Verification: targeted schema and persistence tests cover branch creation metadata, branch-point links to `StoryDecisionNode`, and deterministic branch listing order.
- [x] BE-11B Branch state reference and active-branch persistence:
  add canonical schema and persistence support for `BranchStateRef` and active-branch selection per project.
  Expected result: the backend can persist which canonical objects and decision-node path a branch points at, and which branch is currently active.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/*` routes.
  Verification: targeted schema and persistence tests cover active-branch changes, stable state references, and branch-local decision-node lineage lookup.
- [x] BE-11C Branch comparison persistence:
  add canonical schema and persistence support for `BranchComparisonRecord` so two branches can be compared without mutating branch state.
  Expected result: branch-to-branch comparisons become reviewable first-class backend objects.
  Expected endpoints: none in this slice; foundation for later `/story-development/branches/comparisons*` routes.
  Verification: targeted schema and persistence tests cover comparison record storage, branch pair linkage, deterministic ordering, and review-note retrieval.
- [x] BE-11D Branch merge decision persistence:
  add canonical schema and persistence support for `BranchMergeDecision`, including source branch, target branch, merge rationale, and resulting node links.
  Expected result: merge intent and accepted merge outcomes become durable backend records instead of implicit state changes.
  Expected endpoints: none in this slice; foundation for later `/story-development/branch-merges*` routes.
  Verification: targeted schema and persistence tests cover merge-decision storage, source-target linkage, rationale fields, and resulting decision-node references.
- [x] BE-11E Story branching service slice:
  implement bounded services for `create_story_branch`, `list_story_branches`, `compare_story_branches`, `select_active_branch`, and `record_branch_merge_decision`.
  Expected result: the user can fork the storyline from a decision point and later review or merge branches without overwriting the active path.
  Expected endpoints: none in this slice; service-only foundation for later `/story-development/branches/*` routes.
  Verification: service tests cover branching from a decision point, deterministic branch listing, branch comparison, active-branch changes, and explicit merge decisions.
- [x] BE-10A Story-development API surface for stable non-branching slices:
  expose bounded API routes for `decisions`, `review`, `planning`, and `drafting` only after their schema, persistence, and service contracts are stable.
  Expected result: the first story-development API routes are thin projections over accepted backend contracts rather than speculative endpoints.
  Formalization rule: do not use frontend implementation pressure as the trigger for these routes. Formalize the backend API only after the underlying slice is stable, and treat the API layer as a backend contract milestone in its own right.
  Out of scope for this slice: branch routes, frontend wiring, frontend state management, or UI-driven route shape changes before the backend contract is accepted.
  Verification: route tests cover happy path, validation errors, 404 behavior, and projection-only behavior for the first shipped slices.
- [x] BE-10B Story-development branching API surface:
  expose bounded API routes for branch identity, branch comparisons, branch-local state refs, active-branch selection, and merge decisions only after `BE-11E` is complete.
  Expected result: branch routes remain thin projections over accepted branching contracts instead of inventing new branch semantics in the route layer.
  Implemented route families: `/story-development/branches`, `/story-development/branches/active`, `/story-development/branches/comparisons`, `/story-development/branches/{branch_id}/state-refs`, and `/story-development/branch-merges`.
  Verification: route tests cover branch creation, listing, active-branch changes, comparison retrieval, branch-state-ref reads, merge-decision projection, validation errors, and 404 behavior.

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
- [x] Update `docs/Narrative SRS v0.3.md` so story-development sections describe an aspirational writing product and stop using reconstruction-grade language for these features.
- [x] Update `docs/Narrative SRS v0.3.md` so story-development workflow states describe actual states rather than mixing stage categories with state enums.
- [x] Update `docs/Narrative SRS v0.3.md` and `docs/Frontend Design SRS v0.4.md` so implemented-now versus target-state language is internally consistent for checker runtime behavior and inspect surfaces.
- [x] Update `docs/Frontend Design SRS v0.4.md` so backend-object names match the canonical product and backend contract instead of introducing competing object labels without mappings.
- [x] Update `docs/Frontend Design SRS v0.4.md` section 19 so each frontend TODO becomes an agent-sized deterministic task card instead of a multi-surface implementation wave.
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
- [x] `Lagrange`: implement BE-04 by owning the brainstorm and promotion service slice with bounded `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item` operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/brainstorm/*` routes. Expected outcome: brainstorm items can be persisted, clustered, and promoted with source links and no API wiring yet. Keep the write scope limited to the new service module and a focused test file.
- [x] `Descartes`: implement BE-05 by owning the foundation profile and downstream-impact service slice with bounded revision history behavior and review-cue generation. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/foundation/*` routes. Expected outcome: active foundation reads, revision history, and downstream review cues work without API wiring yet. Keep the write scope limited to the new service module and a focused test file.
- [x] `Gauss`: implement BE-06A by owning canonical persistence for `RelationshipEdge`, `ArcCandidate`, `ArcSelection`, and `ArcStageMap` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, and `/story-development/arcs/*` routes. Expected outcome: BE-06 services can rely on durable repository-backed state for all canonical story-knowledge objects.
- [x] `Laplace`: implement BE-06B by owning canonical persistence for `ArcComparisonRecord` and selection-to-comparison links in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/arcs/*` routes. Expected outcome: arc comparison history becomes a first-class persisted reviewable object rather than advisory service-local memory.
- [x] `Nozick`: implement BE-06C by owning canonical persistence for `StoryDecisionNode` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/decisions/*`, `/story-development/arcs/*`, and future flow-history routes. Expected outcome: user-made story-shaping decisions become first-class persisted reviewable nodes rather than being inferred from current state alone.
- [x] `Bohr`: implement BE-06D by owning schema support for `ArcComparisonRecord`, selection-to-comparison links, and `StoryDecisionNode` enum-driven timeline and tree fields in `app/schemas/story_development.py`, `app/schemas/__init__.py`, and a focused schema test file. Expected endpoints for this slice: none yet; schema-only foundation for later `/story-development/arcs/comparisons/*` and `/story-development/decisions/*` routes. Expected outcome: typed schema contracts match the persisted reviewable decision objects now required by the docs.
- [x] `Euler`: retry BE-06 only after `BE-06A`, `BE-06B`, `BE-06C`, and `BE-06D` land, by owning the character, world bible, and arc-selection service slice with bounded compare, upsert, select, stage-map, and decision-node recording operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, `/story-development/arcs/*`, and `/story-development/decisions/*` routes. Expected outcome: canonical story knowledge can be stored, related, and selected without manuscript generation or API wiring, using durable repository-backed state only. Arc comparison history and user decision history must both be reviewable through persisted objects. Keep the write scope limited to a new service module and a focused test file.
- [x] `Turing`: implement BE-07A by owning canonical persistence for `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/planning/*` routes. Expected outcome: planning services can be built on durable canonical records instead of service-local state.
- [x] `Noether-2`: BE-07 remains blocked pending `BE-07A` and should not be implemented as a service-local workaround.
- [x] `Rawls`: retry BE-07 only after `BE-07A` lands, by owning the planning objects and chapter-packet service slice with bounded plan creation, reorder, and dependency-preservation operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/planning/*` routes. Expected outcome: plan objects persist as canonical records and can later be projected into UI cards without introducing a competing card persistence model. Prior blocked attempt correctly refused an in-memory workaround; retry now that canonical planning persistence exists. Keep the write scope limited to a new service module and a focused test file.
- [x] `Curie-2`: implement BE-08A by owning the drafting persistence scaffold for `DraftArtifact`, `ManuscriptDocument`, and `RevisionSuggestion` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/drafting/*`, `/story-development/manuscript/*`, and `/story-development/revisions/*` routes. Expected outcome: drafting and manuscript state gain durable storage before service logic lands.
- [x] `Feynman`: implement BE-09B by owning the review and inspect persistence scaffold for `CheckerFinding`, `ReviewDecision`, and `InspectRunLink` in `app/persistence/story_development.py`, `app/persistence/sqlite.py`, and a focused persistence test file. Expected endpoints for this slice: none yet; persistence-only foundation for later `/story-development/review/*` routes. Expected outcome: review and inspect linkage gain durable storage before service logic lands.
- [x] `Curie-3`: implement BE-08 only after `BE-08A` lands, by owning the draft artifact versus manuscript document separation service slice with bounded generate, revise, and promote operations. Keep the write scope limited to the new service module and a focused test file.
- [x] `Huygens`: implement BE-09 only after `BE-09B` lands, by owning the review decision and inspect-link service slice with bounded finding routing, decision recording, inspect linkage operations, and canonical routing back into planning or drafting. Keep the write scope limited to the new service module and a focused test file.
- [x] `Leibniz`: implement BE-09A by owning the story decision review surface slice with bounded listing, ordering, parent-path reconstruction, and affected-object linkage for `StoryDecisionNode`. Keep the write scope limited to a new service module and a focused test file.
- [x] `Gibbs`: implement BE-06 in `app/services/story_knowledge.py` and `tests/test_story_knowledge_service.py` only. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/characters/*`, `/story-development/world-bible/*`, `/story-development/arcs/*`, and `/story-development/decisions/*` routes. Expected outcome: arc comparison history and user decision history are both reviewable through persisted objects, with story-knowledge services using repository-backed state only.
- [x] `Bernoulli`: implement BE-09A in a bounded decision-review service module and focused test file only. Expected endpoints for this slice: none yet; backend foundation for later `/story-development/decisions/*` routes and related object detail screens. Expected outcome: a user can review decision-node history, affected-object links, and parent-path context without inferring direction changes from current state alone.
- [x] `Faraday-2`: implement BE-11A by owning story branch identity and branch-point schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/*` routes. Expected outcome: branch identity and branch-point linkage become first-class structured backend objects without using Git as the canonical backend.
- [x] `Spinoza`: implement BE-11B only after BE-11A lands, by owning branch state references and active-branch persistence. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/*` routes. Expected outcome: the backend can persist branch-local state refs and the current active branch without branch comparison or merge behavior yet.
- [x] `Anaximander`: implement BE-11C only after BE-11A and BE-11B land, by owning `BranchComparisonRecord` schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branches/comparisons*` routes. Expected outcome: branch comparisons become reviewable first-class backend records.
- [x] `Democritus`: implement BE-11D only after BE-11A and BE-11B land, by owning `BranchMergeDecision` schema or persistence support. Expected endpoints for this slice: none yet; foundation for later `/story-development/branch-merges*` routes. Expected outcome: merge decisions become durable backend records instead of implicit state changes.
- [x] `Goodall`: implement BE-11E only after BE-11A through BE-11D land, by owning the story-branching service slice with bounded create, list, compare, select-active, and merge-decision operations. Expected endpoints for this slice: none yet; service-only foundation for later `/story-development/branches/*` routes. Expected outcome: users can fork the storyline from a decision point and later review or merge branches without overwriting the active path.
- [x] `Dewey`: implement BE-10A by owning the first story-development API surface slice for stable non-branching contracts only. Keep the write scope limited to thin route wiring and focused route tests.
- [x] `Hopper-2`: implement BE-10B only after `BE-11E` lands, by owning the branching API surface slice with thin route wiring and focused route tests only.
- [x] `Volta`: update `docs/Narrative SRS v0.3.md` so the story-development sections describe an aspirational writing product, remove reconstruction-specific framing for those features, resolve implemented-versus-target-state contradictions, and align workflow-state terminology with the canonical enum set once defined.
- [x] `Kant`: update `docs/Frontend Design SRS v0.4.md` so object names, workflow states, and deterministic frontend task cards match the canonical contract and no longer bundle multiple screen families into one agent task.
- [x] `Archimedes`: update `docs/Orchestrator Deterministic Task Spec v0.1.md` so each story-development feature area includes callable operation shapes with expected inputs, outputs, side effects, and verification, and so the safe-assignment guidance matches the new narrower task cards.
- [x] `Hypatia`: update `docs/Story Development Product Spec v0.1.md` with the canonical editable-flow semantics, stage type versus stage instance versus stage status split, and explicit planning versus card terminology.
- [x] `Maxwell`: author a canonical docs appendix or companion contract section that lists approved object names, lifecycle enums, forbidden aliases, and cross-doc mappings for all story-development features.
- [x] `Kuhn`: create `docs/Inference Runtime Blueprint v0.1.md` that documents provider selection, environment variables, request/response contract, and runtime error taxonomy for `llama.cpp`, LM Studio, and `vLLM`.
- [x] `Beauvoir`: add deterministic inference-backend failure tests in `tests/test_inference_backend_failures.py` covering timeout, HTTP error, and invalid-JSON cases for the OpenAI-compatible adapter.
- [x] `Newton`: update `docs/Frontend Design SRS v0.4.md` so the UI explicitly supports runtime-provider visibility, model-source visibility, and inspect views for step and lineage endpoints.
- [x] `Planck`: update `.github/workflows/tests.yml` so CI includes `tests/test_inference_runtime.py` and document the exact CI command in `docs/Validation Notes v0.1.md`.
- [x] `Cicero`: create `docs/Step and Lineage API Projection Blueprint v0.1.md` defining deterministic response shapes for the planned step and lineage inspect endpoints.
- [x] `Maxwell`: create `docs/Runtime Telemetry Contract v0.1.md` defining required persisted telemetry fields, hash inputs, finish reasons, and error categories for provider-backed runs.
- [x] `Worker`: implement the first real `architect` call for job phase `P-100` in `app/services/local_executor.py`, including prompt building, inferencer call, persisted output, and tests.
- [x] `Beauvoir`: add deterministic API tests for the four step/lineage projection endpoints, including empty-state and 404 behavior.
- [x] `Cicero`: update `docs/Step and Lineage API Projection Blueprint v0.1.md` if needed so it exactly matches the endpoint response contract implemented in code.
- [x] `Newton`: update `docs/Frontend Design SRS v0.4.md` with explicit inspect-view expectations for the four public step/lineage endpoints once their contract is locked.
- [x] `Planck`: add CI coverage for the new projection-endpoint tests after they land.
- [x] `Kuhn`: review the repo for encoding or BOM issues that could break parsing, packaging, or test execution, and fix only concrete safe issues.
  Residual low-risk note: no UTF-8/BOM/control-character blockers were found in tracked source, docs, tests, or config files; a small set of files still mixes mostly-LF text with a single CRLF line ending, but nothing currently appears parser-breaking.
- [x] `Maxwell`: create `docs/Runtime Error Mapping Blueprint v0.1.md` that turns current inferencer failures into deterministic runtime error categories suitable for persistence.
- [x] `Cicero`: create `docs/Step and Lineage API Test Matrix v0.1.md` that enumerates required endpoint cases for happy path, empty state, 404, ordering, and future attempt filtering.
- [x] `Newton`: draft inspect-mode component inventory in `docs/Frontend Design SRS v0.4.md` for step timeline, lineage list, and provenance badges using the current minimal endpoint envelopes.
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
