# Frontend Design SRS Recovered v0.3

## 1. Intent

The frontend should now be treated as a writer-workflow prototype, not only a backend console.

The interaction model is designed around four stages:

1. project setup
2. story engine context
3. chapter drafting
4. review and continuity checks

The implementation in this repo should stay original and fit the recovered Narrative-Core architecture.

## 2. Primary User Flow

### Stage 1: Project Setup

The user must be able to:

- create a project by `project_name`
- define genre, tone profile, POV, story structure, and language settings
- enter a premise or synopsis seed
- enter continuity constraints up front
- select an existing recovered project and resume work

### Stage 2: Story Engine Context

After a project is selected, the UI should expose a project workspace that keeps context visible:

- synopsis / story-bible seed
- character import notes
- worldbuilding rules
- continuity watchlist
- visible project constraints and continuity guardrails
- a compact story-bible map showing which sections are already populated

These fields may begin as frontend-local workspace notes, but the interaction model should assume they are meaningful authoring context for later runtime roles.

### Stage 3: Chapter Drafting

The drafting stage should focus on one chapter brief at a time.

The user must be able to:

- stage a chapter brief
- stage chapter-specific continuity risks
- assemble a reusable chapter packet / handoff view
- inspect recovered artifacts such as manifest, sequence, and chapter draft
- launch a backend job using the current project and chapter context
- monitor exact backend job status instead of fake timers

### Stage 4: Review And Model Validation

The review stage should combine:

- role-model selection
- critic profile selection
- per-role pass/fail visibility
- saved checker report visibility
- continuity-aware review context carried forward from the active chapter packet

The checker should be presented as part of the writing workflow, not as an isolated diagnostics page.

## 3. Layout Model

The recommended page structure is:

- left rail for project library and project creation
- main stage for active project workflow
- explicit stage strip showing Setup / Story Engine / Draft / Review
- a story-bible map that shows synopsis, characters, world, and continuity readiness
- a chapter packet area that acts as the current handoff for the next run

The user should always be able to answer:

- which project is active
- which stage they are in
- what context is currently loaded
- what artifacts already exist
- whether the system is ready to draft or review

## 4. Required Frontend Behaviors

### Project Library

The project list must show:

- `project_name`
- a lightweight metadata summary
- active selection state

Selecting a project must refresh:

- project detail
- artifact availability
- story engine workspace notes
- stage readiness display
- continuity lens / continuity guardrail list

### Project Creation

The project creation form should map directly to the backend contract for `POST /projects/create`.

Required fields:

- `project_name`
- `genre`
- `tone_profile`
- `pov`
- `primary_language`
- `secondary_language`
- `story_structure`
- `premise_text`
- `constraints`

### Story Engine Workspace

The frontend should preserve a writer-facing workspace per project with:

- cast notes
- world notes
- continuity notes
- chapter brief
- chapter-specific continuity risks

For the current recovered prototype, local browser storage is acceptable for this layer as long as the UI clearly treats it as workspace context rather than canonical backend state.

### Artifact Review

The frontend should support direct review of:

- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`

Artifact review is important because the user should be able to inspect recovered state before launching downstream steps.

### Chapter Packet

The frontend should assemble a visible chapter packet from:

- synopsis seed
- character notes
- world notes
- chapter brief
- continuity notes
- chapter-specific continuity risks
- project constraints

The chapter packet can remain frontend-generated in the current prototype, but it should model the exact context a future sequencer/drafter pipeline would need.

### Async Job Monitoring

The frontend must use backend polling for:

- `POST /jobs/create`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/logs`

The contract is backend-driven progress. Even if the recovered implementation completes immediately today, the UI must be built to poll and render exact status.

### Role-Model Checker

The frontend must use:

- `POST /role-model-checker/start`
- `GET /role-model-checker/{run_id}/status`

The checker view must display:

- recommended model choices
- selected overrides
- critic profile
- per-role result cards
- warnings and findings
- saved `report_path` when reports are enabled

The checker stage should read as a review gate on the same writing desk, not a separate admin surface.

## 5. Recovery-Safe Constraints

This recovered frontend should not pretend backend parity exists where it does not.

The UI may be stronger than the current runtime, but it must be honest about the recovered state:

- project workspace notes can be local-first
- recovered artifacts are authoritative only where they already exist
- status polling should use real backend endpoints
- missing runtime depth should be treated as deferred, not hidden

## 6. Design Direction

The visual direction should feel like a writer's operations desk:

- warm editorial palette
- high information density without looking like admin software
- explicit separation between planning context and execution state
- strong emphasis on continuity and reusable story context
- a sense of progressive assembly, where story-bible sections and chapter packets accumulate toward draft readiness

The interface should avoid copying any external product branding or literal layouts.

## 7. Immediate Prototype Scope

The current prototype should include:

- project library
- project creation form
- active project summary
- story engine workspace
- story-bible readiness map
- chapter workspace
- continuity risk capture
- chapter packet / handoff preview
- recovered artifact preview
- role-model checker with saved report path
- backend polling for job and checker runs

Current recovered implementation status:

- project selection by `project_name` is implemented
- project creation is implemented
- local browser-backed workspace notes for story engine context are implemented
- recovered artifact preview for manifest, sequence, and chapter-1 is implemented
- backend polling for job and checker status is implemented
- saved checker report-path visibility is implemented
- broader writer-facing runtime depth is still pending

## 8. Deferred Until Deeper Backend Rebuild

These remain explicitly deferred:

- true long-running orchestration progress
- canonical backend persistence for all story-engine notes
- real drafting/runtime inference
- real continuity scoring and chapter-level review loops
