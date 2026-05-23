# God Files Architecture Refactor Design

**Date:** 2026-05-22

**Goal**

Refactor the current backend and frontend "god files" into a package structure built around stable domain ownership, narrow interfaces, and explicit composition seams so future feature work extends focused modules instead of re-centralizing logic.

## Scope

This design covers the following files and their immediate replacements:

- `app/persistence/story_development.py`
- `app/api/story_development.py`
- `app/services/local_executor.py`
- `app/services/runtime_prompts.py`
- `frontend/src/domains/planning/usePlanningController.ts`
- `frontend/src/views/PlanningView.tsx`

This design does not change the public API surface, runtime behavior, route paths, or user-facing workflows as part of the architectural target. The purpose is structural maintainability and safer future extension.

## Problem Statement

The current codebase already contains reasonable domain-level services and feature folders, but several top-level files still aggregate too many unrelated responsibilities:

- `app/persistence/story_development.py` mixes records, serializers, and CRUD for many story-development domains in one repository.
- `app/api/story_development.py` mixes route families, inline request/response models, and route-level transformation logic.
- `app/services/local_executor.py` mixes worker lifecycle, artifact staging/publishing, runtime input resolution, phase execution, and checker execution.
- `app/services/runtime_prompts.py` mixes prompt builders and long prompt bodies for unrelated phases.
- `frontend/src/domains/planning/usePlanningController.ts` centralizes many slices of query, mutation, modal, and form state into one hook contract.
- `frontend/src/views/PlanningView.tsx` acts as both route shell and multi-domain orchestration container.

These files are difficult to reason about, hard to extend safely, and likely to attract unrelated edits because they sit at major integration points.

## Design Principles

### 1. Stable Ownership Boundaries

Modules should be grouped by domain or runtime phase, not by generic CRUD similarity or "all things related to story development."

### 2. Narrow Public Interfaces

Services should depend on focused repository or coordinator interfaces rather than one giant repository or controller.

### 3. Thin Composition Layers

Top-level facades may remain during migration, but the target architecture keeps them thin. Composition modules should wire objects together, not absorb behavior.

### 4. Shared Code Must Be Deliberately Shared

Prompt fragments, row mappers, helper types, and query invalidation utilities should live in clearly named shared modules with explicit consumers.

### 5. Behavioral Compatibility First, Structural Clarity Second

The migration path may temporarily preserve compatibility shims, but the desired end state is not a new generation of facades that permanently hide god-object internals.

### 6. Coordination-Only Shared Layers

Shared backend and frontend coordination modules may compose owned capabilities, but they must not become alternate homes for domain logic, persistence logic, or direct API business rules.

### 7. Enforceable Architectural Budgets

The target architecture is governed by explicit module budgets. Review heuristics are not enough.

## Recommended Architecture

## Architecture Budgets

These budgets are part of the target architecture:

- Backend route module target: less than 300 lines, hard review threshold at 400.
- Backend persistence domain module target: less than 500 lines, hard review threshold at 650.
- Backend executor or prompt phase module target: less than 350 lines, hard review threshold at 450.
- Frontend hook or tab container target: less than 250 lines, hard review threshold at 350.
- Shared helper module target: less than 200 lines, hard review threshold at 275.
- One route family per API module.
- One primary table family per persistence module.
- One workflow family per frontend shared hook.
- No public composition module may expose more than 12 top-level exports.

Crossing a hard threshold requires either a split or an explicit documented exception.

## Backend Persistence Target

Replace `app/persistence/story_development.py` with a package:

```text
app/persistence/story_development/
  __init__.py
  contracts.py
  records.py
  serialization.py
  flow.py
  brainstorm.py
  braindump.py
  foundation.py
  characters.py
  world_bible.py
  arcs.py
  branching.py
  review.py
  planning.py
  continuity.py
  drafting.py
  generation.py
  manuscript_assist.py
  canon.py
  libraries.py
  storyboard.py
```

### Persistence Rules

- `records.py` owns dataclass-style persistence records only.
- `serialization.py` owns row-to-record and record-to-storage conversion helpers.
- Each domain file owns one table family and the queries that naturally evolve with that family.
- `contracts.py` defines focused repository protocols or abstract interfaces such as `PlanningRepository`, `BranchingRepository`, `DraftingRepository`, and `CanonRepository`.
- `__init__.py` may export a temporary compatibility layer during migration, but the target state is for services to depend on narrow contracts instead of one monolithic repository type.

### Persistence Ownership Matrix

The end state is defined by these ownership rules:

- `flow.py`: `story_flow_definitions`, `story_flow_stages`
- `brainstorm.py`: `brainstorm_items`, brainstorm promotion persistence helpers only
- `braindump.py`: `brain_dump_sessions`
- `foundation.py`: `foundation_profiles`, `foundation_revisions`
- `characters.py`: `character_profiles`, `relationship_edges`
- `world_bible.py`: `world_bible_entries`
- `arcs.py`: `arc_candidates`, `arc_stage_maps`, `arc_selections`, `arc_comparisons`
- `branching.py`: `story_decision_nodes`, `branch_points`, `story_branches`, `branch_state_refs`, `branch_comparisons`, `branch_merge_decisions`
- `review.py`: `checker_findings`, `review_decisions`, `inspect_run_links`
- `planning.py`: `sequence_plans`, `chapter_plans`, `scene_plans`, `beat_plans`, `planning_dependencies`, `chapter_packets`
- `continuity.py`: `continuity_threads`, `continuity_states`, `continuity_findings`, `draft_briefs`, `drafting_context_packets`
- `drafting.py`: `draft_artifacts`, `manuscript_documents`, `revision_suggestions`
- `generation.py`: `canon_generation_runs`, `canon_generation_packets`, `generation_gate_results`
- `manuscript_assist.py`: `manuscript_assist_runs`, `manuscript_assist_suggestions`, `manuscript_assist_gate_results`
- `canon.py`: `canon_annotations`, `canon_customization_profiles`
- `libraries.py`: `mythos_entries`, `pattern_entries`
- `storyboard.py`: `storyboard_cards`

Ownership means:

- The owning module defines persistence records, row mappers, and CRUD/query methods for those tables.
- Other modules may read through its contract, but may not duplicate table-specific queries.
- Cross-domain joins or multi-table workflows must live in an owning service or a dedicated read-model helper, not by bypassing ownership.

### End-State Service To Repository Contract Matrix

The target state is for services to depend on narrow repository contracts:

- `EditableFlowService` -> `FlowRepository`
- `BrainstormService` -> `BrainstormRepository`
- `BrainDumpService` -> `BrainDumpRepository`
- `FoundationService` -> `FoundationRepository`
- `StoryKnowledgeService` -> `CharacterRepository`, `WorldBibleRepository`, `ArcRepository`
- `PlanningService`, `SequencePlansService`, `ChapterPacketsService` -> `PlanningRepository`
- `DraftingService` -> `DraftingRepository`, `ContinuityRepository`
- `StoryDecisionReviewService`, `ReviewRoutingService` -> `ReviewRepository`, `BranchingRepository`
- `StoryBranchingService` -> `BranchingRepository`
- `StoryboardCardService` -> `StoryboardRepository`
- `CanonCustomizationService` -> `CanonRepository`
- `MythosLibraryService`, `PatternLibraryService` -> `LibraryRepository`
- `ManuscriptAssistService` -> `ManuscriptAssistRepository`, `DraftingRepository`
- `StoryGenerationOrchestrator`, `GenerationGateService` -> `GenerationRepository`, `CanonRepository`, `PlanningRepository`

Temporary compatibility exports are allowed during migration, but the end state above is the standard to implement toward.

### Why This Is Better

- Planning changes stay within planning persistence.
- Canon and library work stop colliding with drafting or branching edits.
- Future domains can be added as new modules rather than appended to a central file.

## Backend API Target

Replace `app/api/story_development.py` with a package:

```text
app/api/story_development/
  __init__.py
  router.py
  dependencies.py
  flow.py
  brainstorm.py
  braindump.py
  foundation.py
  characters.py
  world_bible.py
  arcs.py
  branches.py
  review.py
  planning.py
  drafting.py
  storyboard.py
```

Move inline request and response models into:

```text
app/schemas/story_development_api/
  __init__.py
  common.py
  flow.py
  brainstorm.py
  braindump.py
  foundation.py
  characters.py
  world_bible.py
  arcs.py
  branches.py
  review.py
  planning.py
  drafting.py
  storyboard.py
```

### API Rules

- Route files own HTTP parsing, response codes, and response shaping only.
- `dependencies.py` owns service accessors and shared dependency helpers.
- `router.py` only registers sub-routers and shared tags or prefixes.
- PATCH merge logic and nontrivial transformations should live in service-layer helpers, not route files.
- Shared API models should not live inline in router modules.

### API Dependency Rules

- `dependencies.py` may provide dependency factories and auth/context extraction only.
- `dependencies.py` may not contain response projection, payload normalization, PATCH merge policy, or route-family business rules.
- If two route families share nontrivial behavior, that behavior belongs in a service helper or an explicit schema translator, not in router registration code.
- A route file may depend only on:
  - its schema module
  - shared auth or dependency helpers
  - the service or services that own its route family
- Cross-family route access should be treated as a design smell and requires an explicit rationale.

### API End-State Namespace Rule

The final architecture keeps the unified `/v1/story-development/*` namespace for external compatibility, but internal registration is domain-first. The namespace is a transport concern, not a module ownership rule.

### Why This Is Better

- Route families become independently readable and testable.
- Adding a new story-development endpoint family becomes additive instead of centralizing.
- Request and response contracts become reusable and discoverable.

## Executor Target

Replace `app/services/local_executor.py` with a package:

```text
app/services/local_executor/
  __init__.py
  executor.py
  context.py
  worker_lifecycle.py
  artifact_io.py
  runtime_inputs.py
  phase_protocol.py
  planning_phases.py
  drafting_phases.py
  generation_phases.py
  manuscript_assist_phases.py
  checker_runtime.py
  errors.py
  types.py
```

### Executor Rules

- `context.py` defines the stable execution context object shared by all phases.
- `worker_lifecycle.py` owns thread startup, shutdown, and polling loops.
- `artifact_io.py` owns staging, publish, restore, and finalize behavior.
- `runtime_inputs.py` owns upstream artifact resolution and selection persistence.
- Phase modules own phase execution only.
- `checker_runtime.py` owns checker-specific execution and should not share ad hoc helpers via executor internals.
- `executor.py` owns top-level dispatch and dependency composition, not phase bodies.

### Executor Phase Contract

Each runtime phase must implement a shared protocol defined in `phase_protocol.py`:

- Input: immutable execution context plus phase request payload
- Output: explicit phase result object containing status, generated artifact refs, lineage refs, and optional follow-up metadata
- Side effects allowed only through:
  - artifact I/O helpers
  - runtime input resolution helpers
  - step-record and lineage helper interfaces exposed on the execution context
  - owned service dependencies passed through the execution context

Phase modules may not:

- manipulate thread lifecycle
- write files directly outside artifact I/O helpers
- persist lineage or runtime selections directly without going through context-owned helpers
- reach into other phase modules

### Executor Mutation Boundary

The execution context is the only shared mutation boundary. If a phase needs new shared behavior, that behavior must be added to a named context helper interface instead of importing unrelated executor internals.

### Why This Is Better

- Shared execution semantics become explicit instead of implicit.
- New phases can be added by extending phase modules plus dispatch, not by extending a single 2,500-line class.
- Cross-phase behavior such as artifact publication and step recording can be tested separately.

## Runtime Prompt Target

Replace `app/services/runtime_prompts.py` with a package:

```text
app/services/runtime_prompts/
  __init__.py
  types.py
  shared_fragments.py
  formatting.py
  output_paths.py
  planning.py
  drafting.py
  generation.py
  manuscript_assist.py
  checker.py
```

### Prompt Rules

- Phase-specific builders live in the matching phase module.
- Reused prompt fragments such as formatting rules, canon instructions, and output constraints live in `shared_fragments.py`.
- Output path helpers are separate from prompt content.
- Shared fragments should be named and versioned through constants or helper builders so drift is visible in code review.

### Prompt Sharing Rules

- `shared_fragments.py` may contain only fragments reused by at least three builders or by multiple phase families.
- Fragments reused only within one phase family stay in that phase module.
- `shared_fragments.py` may not contain complete prompt builders.
- If a fragment changes semantics for only one phase, it must be forked back into that phase module instead of expanding conditionals in the shared layer.

### Why This Is Better

- Prompt drift is easier to detect.
- Runtime phase and prompt ownership match each other.
- Changes to one phase do not require scanning every other phase prompt.

## Frontend Planning Controller Target

Refactor `frontend/src/domains/planning/usePlanningController.ts` into a composition hook over smaller slices:

```text
frontend/src/domains/planning/
  usePlanningController.ts
  controllerTypes.ts
  usePlanningRetries.ts
  useSequencePlanning.ts
  useChapterPlanning.ts
  useScenePlanning.ts
  useBeatPlanning.ts
  useChapterPackets.ts
  useStoryboardPlanning.ts
  useArcPlanning.ts
  forms/
    useSequenceForm.ts
    useChapterForm.ts
    useSceneForm.ts
    useBeatForm.ts
    usePacketForm.ts
    useStoryboardForm.ts
    useArcCandidateForm.ts
    useStageMapForm.ts
```

### Frontend Hook Rules

- Each slice hook owns one feature area and its query or mutation coordination.
- Form state should live with the feature that submits it.
- Derived state should remain derived, not copied into new local state containers.
- `usePlanningController.ts` may compose the slices for compatibility, but the target end state is that consumers can adopt slices directly where appropriate.

### Frontend Slice Source-Of-Truth Matrix

- `useSequencePlanning.ts`: sequence list state, sequence mutations, sequence reorder policy
- `useChapterPlanning.ts`: chapter list state, chapter mutations, chapter reorder policy
- `useScenePlanning.ts`: scene list state, scene mutations, scene reorder policy
- `useBeatPlanning.ts`: beat list state, beat mutations
- `useChapterPackets.ts`: packet list state, packet creation and update behavior
- `useStoryboardPlanning.ts`: storyboard card state, reorder and edit behavior
- `useArcPlanning.ts`: arc candidates, selections, stage maps, comparisons, selected arc UI state
- `forms/*`: modal open state and local draft field state for the owning feature only
- `usePlanningRetries.ts`: retry callbacks only, no data ownership

### Planning Controller End-State Rule

`usePlanningController.ts` is transitional composition, not the long-term primary API.

End state:

- `PlanningTab` and related consumers should read directly from focused slice hooks where practical.
- `usePlanningController.ts` may remain only as a thin compatibility adapter.
- The compatibility adapter may compose slice outputs, but may not introduce new business logic, new duplicated state, or cross-slice mutation policy.

### Why This Is Better

- Adding new planning capability means extending one slice rather than widening a mega-hook.
- Query invalidation logic stays close to the mutation that owns it.
- Hook count and cognitive load per module remain bounded.

## Frontend Planning View Target

Refactor `frontend/src/views/PlanningView.tsx` into a shell plus tab containers:

```text
frontend/src/views/
  PlanningView.tsx
  planning/
    PlanningTabShell.tsx
    PlanningCoreTab.tsx
    FlowTab.tsx
    ArcsTab.tsx
    BranchesTab.tsx
    DecisionsTab.tsx
    CheckerTab.tsx
    BrainstormTab.tsx
    FoundationTab.tsx
    CharactersTab.tsx
    WorldBibleTab.tsx
    RelationshipsTab.tsx
    shared/
      usePlanningTabNavigation.ts
      useCharacterSelection.ts
      useRelationshipEditing.ts
      useDiscoveryScanWorkflow.ts
```

### Frontend View Rules

- `PlanningView.tsx` owns route-level setup, high-level tab selection, and shell composition only.
- Each tab container owns the composition for its visible workflow.
- Cross-tab workflows must move into named shared hooks under `shared/`, not remain hidden in the shell.
- Prop drilling should be minimized by colocating hook usage in the tab or workflow that needs it.

### Shared Frontend Workflow Rules

Shared hooks under `views/planning/shared/` are coordination-only:

- they may orchestrate already-owned hooks
- they may derive transient UI coordination state
- they may not become new data ownership layers
- they may not define direct API service calls if an owned domain hook already exists for that concern
- they may not absorb unrelated workflows for convenience

If a shared hook starts owning durable data, mutation rules, or domain validation, it should be promoted into a domain slice instead.

### Why This Is Better

- Each tab becomes independently readable.
- Shared workflows become explicit.
- New planning tabs or interactions become additive.

## Extension Model

The architecture should make future work additive:

- New story-development backend domain: add a new persistence module, service contract, API route family, and schema file.
- New runtime phase: add a phase module and prompt module, then register dispatch.
- New planning tab or feature: add a new slice hook and tab container instead of extending a central mega-view or mega-hook.

If future changes require touching several unrelated packages for one small domain addition, the boundaries are wrong.

### Extension Locality Examples

Representative target extensions:

- Adding a new planning object type should usually touch:
  - one planning persistence module
  - one planning service or contract
  - one planning API route family
  - one planning frontend slice and tab surface if exposed
  - tests

- Adding a new manuscript assist gate result field should usually touch:
  - `manuscript_assist.py` persistence ownership
  - manuscript assist schemas or service contract
  - manuscript assist runtime or API projection
  - tests

If either example requires edits across unrelated branching, storyboard, arc, or foundation modules, the architecture has regressed.

## Guardrails

The target architecture needs explicit guardrails to prevent regression:

- No single implementation file should be allowed to regrow into a central integration dump.
- Prefer one route family per API module.
- Prefer one repository contract per persistence domain.
- Keep shared modules intentionally small and named by purpose.
- Treat compatibility facades as migration scaffolding, not as the desired steady state.
- Shared coordination modules may orchestrate but may not own domain logic.
- Service constructor dependencies should move toward narrow contracts, not centralized facades.

Recommended review heuristics:

- A feature change should usually touch one domain package plus tests.
- A new domain should usually require adding files, not widening central ones.
- A reader should be able to understand a module's purpose without scanning unrelated domains.

## Migration Strategy Summary

The target end state should be approached in this order:

1. Define ownership matrices, narrow contracts, and shared types.
2. Update service dependency boundaries so target services can consume narrow repository contracts.
3. Extract persistence by domain behind those contracts.
4. Extract API route families and move inline API models into schema files, keeping dependency helpers coordination-only.
5. Extract executor phase protocol, execution context, and mutation boundaries.
6. Extract prompt fragments and phase-specific prompt builders using the phase contract.
7. Split frontend planning slices and form hooks with explicit source-of-truth ownership.
8. Split `PlanningView` into shell plus tab containers and shared coordination-only workflow hooks.

This ordering prioritizes stable boundaries first instead of merely distributing code into smaller files.

## Risks

### Risk: Compatibility Facades Become Permanent

Mitigation:

- Treat facades as transitional only.
- Track direct consumers and replace monolithic dependencies with narrow ones.

### Risk: Circular Imports In Executor Split

Mitigation:

- Extract `context.py`, `types.py`, and `errors.py` before phase modules.
- Keep phase modules stateless relative to executor wiring.

### Risk: Prompt Fragment Drift

Mitigation:

- Centralize reused prompt fragments.
- Keep shared fragments named and reviewed as explicit primitives.

### Risk: Frontend Slice Fragmentation

Mitigation:

- Define source-of-truth ownership for each slice.
- Keep derived state derived.
- Avoid duplicating mutation or invalidation policies across hooks.

### Risk: Shared Coordination Layers Re-Centralize Logic

Mitigation:

- Keep `dependencies.py`, `shared_fragments.py`, and frontend `shared/` hooks coordination-only.
- Reject additions that introduce domain ownership into coordination layers.
- Apply budget thresholds aggressively to shared modules.

## Testing Expectations

Architecture changes should be protected by tests in addition to existing behavioral tests:

- Backward-compatibility tests for current route behavior.
- Repository contract tests for domain-owned persistence modules.
- Executor phase contract tests for shared execution context and artifact finalization behavior.
- Prompt builder tests for shared fragment usage where behavior is contractually important.
- Frontend slice tests for focused hooks and tab container rendering.
- Dependency-boundary tests where useful to prove services consume narrow contracts instead of monolithic repository surfaces.
- Import-surface tests or review checks for compatibility adapters so they remain thin.

## Success Criteria

The refactor is successful when:

- No targeted god file remains the sole owner of multiple unrelated domains.
- Service and UI composition depends on narrower interfaces than today.
- New feature work can be added by extending focused modules rather than broad entrypoints.
- Existing route behavior and runtime behavior remain unchanged.
- The resulting package tree makes domain ownership obvious to a new contributor.
- Shared coordination modules remain thin and do not become alternate god files.
- The representative extension examples in this spec can be implemented without touching unrelated domain packages.
