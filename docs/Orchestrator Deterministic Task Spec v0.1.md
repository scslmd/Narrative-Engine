# Orchestrator Deterministic Task Spec v0.1

## 1. Purpose

This document tells a future orchestrator how to break the story-development product into deterministic agent tasks.

It is meant to be practical, not abstract:

- use the product spec as the feature source of truth
- use `docs/Story Development Canonical Contract v0.1.md` as the authoritative source for object names, lifecycle enums, editable-flow semantics, and planning or drafting terminology
- use the narrative SRS and frontend SRS as system and UX constraints
- use the async blueprint and failure matrix as implementation guardrails
- use the documented runtime slices, inspect endpoints, failure handling, and review fixes as lessons about what can go wrong during integration

The central rule is simple:

- every agent task must have one primary purpose, one bounded write scope, one verification path, and one obvious done condition

## 2. How An Orchestrator Should Decompose Work

The orchestrator should split work by layer and by risk.

Recommended ordering:

1. spec and contract tasks
2. backend object and endpoint tasks
3. frontend screen and interaction tasks
4. tests and failure-mode tasks
5. integration and cleanup tasks

Recommended split dimensions:

- feature area
- layer: docs, backend, frontend, tests
- risk: contract change, state model change, runtime change, UI change
- dependency direction: upstream definitions before downstream consumers

Never split work in a way that causes two agents to edit the same contract surface at the same time unless one agent is explicitly the integration owner and the others are read-only reviewers.

## 3. Deterministic Task Card Template

Every agent assignment should be written as a task card with these fields:

```text
task_id:
feature_area:
purpose:
owning_area:
in_scope:
out_of_scope:
dependencies:
expected_inputs:
expected_outputs:
expected_endpoints_or_screens:
acceptance_criteria:
verification:
notes_from_prior_lessons:
```

Task cards should be narrow enough that a reviewer can answer yes or no without reading the whole repo.

## 3.1 Callable Operation Template

When a task depends on a feature operation, describe that operation with this shape:

```text
operation_name:
operation_family:
purpose:
required_inputs:
created_or_updated_objects:
side_effects:
non_destructive_guarantees:
success_result:
failure_result:
verification:
```

Use the canonical operation families from `docs/Story Development Canonical Contract v0.1.md`.

## 4. Bounded Task Rules

- one task, one primary file family, one main result
- docs tasks should define behavior before code tasks implement it
- backend tasks should own data model, API contract, and persistence together only when those changes are tightly coupled
- frontend tasks should own a coherent screen or interaction family, not the whole app
- tests tasks should be written against the accepted contract, not against speculative future behavior
- integration tasks should only join already-defined surfaces, not invent new behavior

If a feature needs more than one layer, decompose it into a vertical slice plus supporting tasks.

Good vertical slice example:

- contract doc
- backend object or endpoint
- frontend screen binding
- deterministic test coverage

Bad split example:

- one agent writes the API shape
- another agent guesses the data model
- a third agent builds the UI against an unfinished contract

## 5. Feature Areas And Task Decomposition

### 5.1 Editable Story Flow

Purpose:

- let the user add, define, rename, reorder, redefine, disable, archive, or delete eligible custom stages in the story-development workflow

Dependencies:

- Story Development Product Spec
- Narrative SRS flow/state rules
- frontend workspace layout

Expected inputs:

- project flow definition
- stage metadata
- user edits to stage order and meaning

Expected outputs:

- editable stage graph
- stage state transitions
- preserved provenance when downstream artifacts depend on revised stages

Acceptance criteria:

- the default flow exists as a scaffold, not a lock
- a custom stage can be inserted, disabled, archived, or deleted under the canonical editable-flow rules without breaking the project
- downstream artifacts remain inspectable after stage edits

Owning area:

- backend, frontend, docs, tests

Safe decomposition strategy:

- one doc task for the editable-flow contract
- one backend task for flow persistence and state transitions
- one frontend task for stage editor UI
- one tests task for reorder, add, disable, archive, delete-eligible-custom, and redefine cases
- one docs task must also lock the difference between disable, archive, optional, and delete-custom-stage behavior

### 5.2 Brainstorming

Purpose:

- convert rough ideas into concrete story directions

Dependencies:

- product spec brainstorming section
- frontend brainstorming workspace

Expected inputs:

- premise sparks
- themes
- constraints
- images or fragments

Expected outputs:

- clustered ideas
- promoted premise candidates
- loglines
- story seeds

Acceptance criteria:

- the user can keep, discard, or park ideas
- brainstorm content can be promoted into structured project artifacts

Owning area:

- frontend, backend, docs

Safe decomposition strategy:

- keep brainstorm capture separate from promotion into canonical planning data
- if suggestion logic is added, keep it advisory and non-destructive
- prefer separate callable operations such as `capture_brainstorm_item`, `cluster_brainstorm_items`, and `promote_brainstorm_item`

### 5.3 Story Foundation

Purpose:

- define the stable promise of the story before deeper planning

Dependencies:

- brainstorm outputs
- product spec foundation fields

Expected inputs:

- premise
- logline
- tone
- theme
- constraints

Expected outputs:

- foundation profile
- downstream change warnings when the foundation changes

Acceptance criteria:

- foundation fields remain editable after downstream artifacts exist
- changing the foundation does not silently overwrite draft material

Owning area:

- backend, frontend, tests

Safe decomposition strategy:

- keep foundation edits and downstream invalidation warnings separate from draft generation
- prefer separate callable operations such as `update_foundation_profile` and `detect_foundation_downstream_impact`

### 5.4 Character Background

Purpose:

- build characters as active story engines with wants, needs, flaws, and change paths

Dependencies:

- foundation profile
- brainstorm artifacts
- arc selection

Expected inputs:

- character seeds
- relationship notes
- backstory fragments

Expected outputs:

- structured character profiles
- relationship edges
- arc-stage notes

Acceptance criteria:

- major characters have explicit goals, flaws, and continuity facts
- character arcs can be compared and revised

Owning area:

- backend, frontend, docs, tests

Safe decomposition strategy:

- separate character model shape from character rendering
- keep relationship editing independent of manuscript generation
- prefer separate callable operations such as `capture_character_profile`, `update_relationship_edge`, and `compare_character_arcs`

### 5.5 World Bible

Purpose:

- maintain canonical story knowledge for locations, factions, rules, history, and continuity

Dependencies:

- story foundation
- character background
- manuscript excerpts and planning artifacts

Expected inputs:

- world facts
- continuity notes
- unresolved promises

Expected outputs:

- world-bible entries
- continuity warnings
- source-linked canonical facts

Acceptance criteria:

- bible entries can be referenced from planning and drafting surfaces
- extracted facts remain traceable to source artifacts

Owning area:

- backend, frontend, docs, tests

Safe decomposition strategy:

- keep canonical facts, extracted facts, and writer notes distinct
- do not allow a later draft to erase earlier bible provenance
- prefer separate callable operations such as `upsert_world_bible_entry`, `promote_world_fact`, and `detect_world_continuity_conflict`

### 5.6 Arc Selection And Comparison

Purpose:

- let the user choose or change an arc deliberately and receive arc-aware guidance

Dependencies:

- foundation
- characters
- world bible
- story arc paradigm guidance

Expected inputs:

- premise
- genre
- tone
- current stage

Expected outputs:

- selected arc
- comparison options
- stage-map guidance
- drift warnings

Acceptance criteria:

- romance, mystery, tragedy, heroic, and fall arcs produce different guidance
- arc selection remains advisory, not blocking

Owning area:

- docs, backend, frontend, tests

Safe decomposition strategy:

- separate arc taxonomy documentation from UI selection and suggestion behavior
- prefer separate callable operations such as `recommend_arc_candidates`, `compare_arc_candidates`, and `select_arc_candidate`

### 5.7 Planning Board

Purpose:

- turn story intent into beats, sequences, chapters, and scenes

Dependencies:

- foundation
- characters
- world bible
- selected arc

Expected inputs:

- story goals
- dependencies
- active characters
- continuity requirements

Expected outputs:

- beat plan
- sequence plan
- chapter plan
- scene cards

Acceptance criteria:

- planning objects expose objective, conflict, stakes, dependencies, and status
- reordering and revising plans preserves prior context

Owning area:

- backend, frontend, tests

Safe decomposition strategy:

- implement beat, sequence, chapter, and scene as separate objects even if they share a UI board
- prefer separate callable operations such as `create_sequence_plan`, `split_sequence_into_chapters`, `derive_scene_plan`, and `reorder_plan_objects`

### 5.8 Drafting And Revision

Purpose:

- generate and refine prose while keeping planning and continuity visible

Dependencies:

- planning board
- story bible
- runtime-backed inference

Expected inputs:

- chapter context
- scene context
- prior draft text
- author instructions

Expected outputs:

- draft artifact
- alternate version or rewrite
- provenance metadata

Acceptance criteria:

- the draft can be revised without losing source context
- selection-based aids return proposed changes instead of auto-overwriting text

Owning area:

- backend, frontend, tests

Safe decomposition strategy:

- keep generated prose, proposed revisions, and canonical manuscript state separate
- introduce one aid or one draft mode at a time
- prefer separate callable operations such as `generate_chapter_draft`, `continue_scene_draft`, and `rewrite_passage_as_revision_suggestion`

### 5.9 Suggestions And Review

Purpose:

- provide context-aware revision guidance instead of generic editing

Dependencies:

- drafts
- character context
- world bible
- arc selection

Expected inputs:

- selected text
- active scene context
- checker findings

Expected outputs:

- suggestion results
- revision diffs
- accept, reject, or refine actions

Acceptance criteria:

- suggestions preserve author control
- review surfaces explain the context used

Owning area:

- frontend, backend, tests

Safe decomposition strategy:

- split suggestion generation from result review and application
- prefer separate callable operations such as `generate_revision_suggestions`, `detect_continuity_issues`, `decide_revision_suggestion`, and `route_finding_to_planning`

### 5.10 Inspect And Provenance

Purpose:

- make every generated artifact traceable through durable steps and lineage

Dependencies:

- step-record persistence
- artifact-lineage persistence
- inspect endpoints

Expected inputs:

- job id
- checker run id
- persisted step rows
- persisted lineage rows

Expected outputs:

- ordered step timelines
- ordered lineage chains
- runtime provenance badges

Acceptance criteria:

- inspect views are deterministic and read-only
- responses preserve backend order
- canonical versus temporary lineage is visible

Owning area:

- backend, frontend, tests

Safe decomposition strategy:

- keep inspect envelope shape stable
- do not add client-side attempt guessing or filters before the backend supports them
- prefer separate callable operations such as `list_run_steps`, `list_artifact_lineage`, and `link_object_to_inspect_run`

### 5.11 Async Runtime, Retries, And Failure Handling

Purpose:

- make long-running work deterministic under acceptance, claim, retry, reclaim, and failure conditions

Dependencies:

- async protocol blueprint
- failure mode test matrix
- job and checker persistence

Expected inputs:

- enqueue requests
- idempotency keys
- retry requests
- stale lease conditions

Expected outputs:

- durable attempt rows
- append-only events
- retryable and non-retryable failure classification

Acceptance criteria:

- acceptance is separate from execution
- retries create new attempts
- stale lease reclaim is explicit
- failed runtime paths do not corrupt canonical artifacts

Owning area:

- backend, tests, docs

Safe decomposition strategy:

- treat state machine changes, persistence changes, and retry behavior as separate but coordinated tasks
- prefer separate callable operations such as `start_async_run`, `retry_async_run`, `reclaim_stale_lease`, and `classify_run_failure`

### 5.12 Frontend Workspace And Screens

Purpose:

- give the writer a three-pane workspace that matches the product workflow

Dependencies:

- frontend design SRS
- product spec screens
- inspect endpoint contracts

Expected inputs:

- project context
- selected stage
- manuscript state
- inspector data

Expected outputs:

- project setup screen
- brainstorm workspace
- character builder
- world bible rail
- planning board
- drafting workspace
- review workspace
- inspect workspace

Acceptance criteria:

- the UI keeps canonical project data and temporary workspace notes separate
- inspect mode is first-class and not buried in an admin-only drawer

Owning area:

- frontend, docs, tests

Safe decomposition strategy:

- assign one screen family at a time
- keep layout work separate from data-binding work unless the task is intentionally vertical

## 5.13 Canonical Contract Alignment

Purpose:

- keep every story-development spec and implementation task aligned to the same object names, state enums, and editable-flow semantics

Dependencies:

- story-development product spec
- narrative SRS
- frontend design SRS

Expected inputs:

- cross-doc terminology drift
- conflicting workflow-state names
- conflicting object names

Expected outputs:

- canonical object list
- canonical enum list
- explicit alias mappings

Acceptance criteria:

- one approved name exists for each story-development object
- one approved enum family exists for each state family
- planning objects versus card views are explicitly separated

Owning area:

- docs

Safe decomposition strategy:

- land the canonical contract before assigning downstream backend or frontend tasks

## 6. Lessons From Prior Work

These lessons should shape future task assignment:

- runtime-backed slices should be introduced one phase at a time, as we did with `P-100`, `P-200`, and `P-300`
- inspect endpoints should be added with a stable envelope and deterministic ordering before richer UI behavior
- failed runtime work must not expose placeholder artifacts as if they were canonical
- downstream phases must ignore empty bootstrap artifacts instead of recording false provenance
- canonical lineage should be superseded on rerun so multiple active canonicals do not accumulate
- checker roles that cannot run natively yet should have explicit fallback behavior rather than silent failure
- failure handling should be tested at the persistence boundary, not only at the happy path

## 7. Verification Expectations

Every agent task should declare how it will be verified.

Verification should usually include one of these:

- targeted pytest files
- focused doc consistency review
- endpoint contract check
- manual UI walkthrough for a single screen family
- persistence inspection for a specific artifact or lineage path

Recommended rule:

- if a task changes behavior, it must include at least one test or a precise reasoning-based verification step

Recommended verification order:

1. contract or doc validation
2. focused unit or persistence tests
3. integration or endpoint checks
4. broader baseline only when the slice is stable

## 8. Safe Assignment Strategy For Orchestrators

- assign the contract definition first, then implementation, then tests
- never let two agents write the same contract file unless one is the integration owner
- use read-only review agents for cross-cutting validation instead of having them edit code
- if a task depends on a new endpoint, define the endpoint contract before the UI task starts
- if a task depends on a new workflow state, define the state transitions before persistence or UI updates start
- if a task touches runtime behavior, require a failure-mode test task alongside the happy-path implementation task

Suggested deterministic orchestration pattern:

1. doc synthesis agent writes or updates the feature contract
2. backend agent implements the smallest vertical slice
3. frontend agent binds the screen or interaction to the contract
4. tests agent locks the expected behavior
5. integration agent reconciles names, response envelopes, and inspect or lineage details

## 9. Example Deterministic Task Sets

### 9.1 Editable Flow Slice

- doc task: define editable stage graph, lifecycle states, and user controls
- backend task: persist stage definitions and transitions
- frontend task: render stage editor and reorder controls
- tests task: verify add, rename, reorder, disable, archive, delete-eligible-custom, and redefine behavior

### 9.2 Inspect Slice

- doc task: define the inspect envelope and list ordering
- backend task: expose step and lineage projections
- frontend task: render timeline and lineage list rows
- tests task: verify deterministic ordering and empty-state behavior

### 9.3 Failure Slice

- doc task: define failure categories and retryability
- backend task: preserve durable attempt and event history
- tests task: exercise stale lease, retry, and storage failure cases
- review task: confirm canonical artifacts are not replaced by failed runs

### 9.4 Canonical Contract Slice

- docs task: define approved object names, state families, alias mappings, and editable-flow semantics
- docs task: update product spec, backend SRS, and frontend SRS to reference the canonical contract
- review task: verify that task cards no longer use conflicting plan versus card terminology

## 10. What Good Looks Like

A good orchestrator task plan should let a future agent answer these questions quickly:

- what is the feature
- what files or surfaces am I allowed to change
- what does success produce
- what must not change
- what test or review proves it worked

If a task card cannot answer those questions, it is too broad and should be split again.
