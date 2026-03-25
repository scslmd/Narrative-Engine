# Frontend Design SRS v0.5

Document version: `v0.5`

**Change log from v0.4**:
- Updated Section 12 (Current Implementation Status) to reflect completed backend work
- Added Section 12A (Backend API Availability) with explicit endpoint inventory
- Updated Section 18 (Implementation Order) to align with backend readiness
- Updated Section 19 (Deterministic Orchestrator Tasks) with React + Vite + Zustand tech stack
- Added Section 21 (Technology Stack Decisions) documenting framework choices
- Clarified manuscript aids mock service pattern for incomplete backend endpoints

**Change log from v0.5 (API Alignment Update - March 24, 2026)**:
- Updated Section 12A with complete 58-endpoint inventory (jobs, role-model-checker, branches, decisions, planning, drafting, review)
- Updated Section 18 with 36 frontend tasks (FE-001 through FE-032, plus FE-001A, FE-004A-C, FE-024A-C)
- Added FE-024: Role-model checker UI (7 real API endpoints)
- Added FE-024A: Story branches UI (12 real API endpoints)
- Added FE-024B: Story decision nodes UI (3 real API endpoints)
- Added FE-024C: Inspect run links UI (2 real API endpoints)
- Added FE-001A: Theming architecture with stage-based colors
- Added FE-004A-C: Error boundaries, loading skeletons, toast notifications
- Updated mock service documentation for 12 feature areas (manuscript creation, review decisions, planning writes, revision suggestions, flow editor, brainstorm, foundation, characters, world bible)
- Added reference to `docs/Frontend API Alignment Issues.md` and `docs/API Alignment Verification.md`

## 1. Purpose

The frontend should feel like a writer workspace, not a generic admin panel.

It should help the user:

- create or open a project
- shape premise and story context
- inspect generated artifacts
- launch backend work
- monitor exact progress
- review checker outcomes before changing models or workflow settings

## 2. Core UX Principles

- project-first workflow
- clear authoring context
- backend-driven status
- runtime-provider visibility
- model-source visibility
- visible artifact inspection
- practical model and checker controls
- honest representation of implemented behavior
- long-session writing comfort
- continuity visibility without modal overload
- planning and drafting in one connected workspace

## 3. Competitive UX Pattern References

Current writing software patterns worth adapting into Narrative-Engine:

- a persistent story knowledge layer, similar to a story bible or codex, that stays visible while writing
- a flexible planning surface that can represent beats, scenes, chapter packets, and alternate story paths
- a drafting workspace with live contextual sidebars instead of forcing the user to constantly switch screens
- card-based scene or chapter navigation that makes reordering, status, and gaps obvious
- continuity-aware reference access for characters, world details, rules, and unresolved threads
- chapter status markers and progress tags that keep the writing queue visible at a glance
- tabbed manuscript navigation and compare-friendly chapter switching for longer revision sessions
- version history that makes draft recovery and comparison feel native to the writing surface
- extract or promote flows that turn brainstormed or drafted material into structured story knowledge
- lightweight inline assistance actions near the manuscript instead of burying core actions in global menus
- progress and session framing that show what is done, what is blocked, and what the engine is currently processing
- explicit separation between canonical project data and temporary writer workspace notes

Narrative-Engine should adopt the following product direction from those patterns:

- a three-pane writing workspace with story storyboard on the left, manuscript focus in the center, and manuscript aids on the right
- a dedicated story bible rail that can pin characters, locations, factions, rules, promises, and continuity warnings
- a planning board that can switch between chapter cards, sequence view, and chapter packet preparation
- a write view that keeps scene goals, continuity notes, and model or checker controls within one interaction distance
- chapter status chips and revision states visible in the navigation rail and planning board
- tabbed manuscript navigation for multi-chapter revision and comparison
- version history and restore points available from the write or review context
- extract-to-bible or extract-to-packet actions that convert promising draft material into structured project knowledge
- a review mode that compares draft text, checker findings, and workflow recommendations without leaving the manuscript context
- explicit visibility into which runtime provider and model source produced a draft, checker result, or inspectable artifact

Patterns that should not be copied directly:

- opaque AI-first writing flows that hide source context from the author
- overly playful prompt surfaces that distract from drafting rhythm
- fragmented navigation where planning, writing, and review feel like separate apps
- browser-local state treated as if it were canonical project history

## 4. Primary User Flow

The intended user journey is:

1. create or open a project
2. review premise, constraints, and story context
3. shape the story bible or codex for character, world, continuity, and promises
4. inspect existing artifacts such as manifest, sequence, chapter packet, and chapter draft
5. move between planning board and manuscript without losing context
6. stage a chapter packet with scene goals, required references, and target outcomes
7. launch a backend job
8. monitor exact job status, logs, and retry state
9. review checker outcomes before adjusting workflow configuration or revising the draft

Story-development refinement:

- the default journey above is a recommended scaffold, not a locked workflow
- the writer must be able to add, rename, reorder, redefine, disable, archive, or delete eligible custom stages in the active project flow
- brainstorm, foundation, character, world-bible, arc, planning, drafting, and review surfaces should all support re-entry after downstream artifacts already exist
- the flow editor should make stage definitions visible and editable as first-class project data, including stage name, purpose, dependencies, ordering, enabled state, and stage-specific notes
- adding a custom stage should create a new flow stage that can be inserted before, between, or after existing stages without breaking the rest of the workspace
- disabling or archiving a stage should only remove it from active future guidance; it should not delete prior artifacts or erase provenance
- deleting a custom stage should be allowed only when the canonical editable-flow deletion rules are satisfied
- redefining a stage should update future suggestions and screen labels while preserving the old meaning in historical artifacts and inspect views
- when a stage changes, the UI should identify the downstream artifacts, planning cards, or draft segments that may need review
- the user should be able to pause a stage, mark it optional, or re-enable it at any point in the project
- for the detailed product contract covering editable flow, screens, backend objects, and workflow states, see `docs/Story Development Product Spec v0.1.md`

## 5. Main Surface Areas

The UI should include:

- project list and creation flow
- active project detail and health cues
- story-development flow editor for adding, removing, renaming, and redefining stages
- story bible or codex workspace for story development
- chapter and scene planning board
- storyboard rail for live chapter or scene progression
- artifact preview for manifest, sequence, and chapter
- primary write view with contextual sidebars
- manuscript aids rail
- chapter packet assembly
- job monitor and logs
- workflow guidance and role-model checker controls
- review workspace for checker findings, continuity notes, and revision actions
- inspect workspace for step records, artifact lineage, and provenance

## 6. Workspace Information Architecture

The target frontend should use a stable workspace layout:

- left rail: story-flow stages, storyboard, chapter or scene list, arc-stage progression, chapter status, and autogenerated or editable scene cards
- center pane: manuscript editor, artifact reader, packet builder, review surface, brainstorm canvas, foundation editor, or inspect view for runtime provenance
- right rail: manuscript aids, story bible context, continuity notes, scene goals, checker outcomes, workflow controls, and provider or model-source diagnostics
- bottom utility layer: job progress, logs, retry controls, version history access, and status diagnostics

Workspace behavior requirements:

- the left rail should always preserve context for the current project and selected chapter or stage, even when the center pane changes modes
- the center pane should be able to swap between plan, write, review, and inspect without losing the current selection
- the right rail should act as a working knowledge layer, not a replacement for the manuscript or plan
- local workspace notes may live in the browser, but the UI must clearly mark them as personal and non-canonical
- any screen that shows generated output should also show what project context produced it when that information is available

The center pane should be mode-based rather than route-heavy. A writer should be able to move between:

- plan
- write
- review
- inspect

without feeling like they left the project workspace.

Inspect mode expectations:

- inspect mode should be a first-class center-pane surface rather than a hidden admin drawer
- inspect mode should support the current first-slice public step-record and artifact-lineage projection endpoints:
  - `GET /jobs/{job_id}/steps`
  - `GET /jobs/{job_id}/lineage`
  - `GET /role-model-checker/{run_id}/steps`
  - `GET /role-model-checker/{run_id}/lineage`
- inspect responses should be treated as minimal envelopes containing exactly:
  - `job_id` or `run_id`
  - `items`
  - `meta`
- inspect items should be rendered in the deterministic ascending order returned by the backend
- inspect mode must not assume a public attempt filter exists yet
- inspect mode should make it obvious which attempt, step, runtime provider, model source, and artifact version produced the current output
- inspect mode should keep protocol detail expandable so manuscript focus is not overwhelmed
- inspect mode should support a clean handoff back to the related manuscript, review, planning, or artifact context
- inspect mode should not introduce attempt filters, lineage filters, or other query controls that are not publicly supported yet

Inspect mode component inventory for the current endpoint slice:

- step timeline list component:
  - reads from `GET /jobs/{job_id}/steps` or `GET /role-model-checker/{run_id}/steps`
  - uses the returned `items` array in backend order with no client-side attempt regrouping
  - shows one row per returned step item in deterministic ascending order
- artifact lineage list component:
  - reads from `GET /jobs/{job_id}/lineage` or `GET /role-model-checker/{run_id}/lineage`
  - uses the returned `items` array in backend order with no lineage filter controls beyond what the endpoint returns
  - shows one row per returned lineage item in deterministic ascending order
- provenance badges or chips:
  - should surface runtime provider, model source, attempt identifier if present, state or status, and canonical versus temporary lineage status when those fields are present in the returned item
  - should remain compact and scannable in list rows and expand into fuller detail on demand
- empty-state treatment:
  - when the inspect envelope exists but `items` is empty, the center pane should show a neutral empty state explaining that no public step or lineage records are available yet for that run
  - the empty state should preserve the current project or manuscript context rather than navigating away
- missing-run error treatment:
  - if the endpoint returns a missing-run or missing-job error, inspect mode should show an inline error state in the center pane
  - the error treatment should explain that the selected job or checker run could not be found and should offer a clear route back to the related manuscript, review, or artifact context
- immediate versus expandable fields:
  - visible immediately in list rows: step or lineage label, current state, runtime provider or model source if present, and the most important artifact or status indicator
  - expandable detail only: raw identifiers, deeper metadata, hashes, timestamps, lineage ancestry, and other protocol-level detail that would otherwise crowd the manuscript workspace
- coexistence with the three-pane workspace:
  - inspect mode remains a center-pane mode, not a separate app section
  - the left rail should continue to show storyboard or chapter navigation for context
  - the right rail should continue to show manuscript aids, story context, or checker context relevant to the selected item
  - switching into inspect mode must not discard the current chapter, packet, or review selection

Storyboard expectations:

- the left storyboard should represent what is happening in the story now, not just file navigation
- storyboard cards may be authored manually or generated by AI from the current draft and planning artifacts
- each card should be able to show scene purpose, active characters, emotional turn, conflict, and likely next beat
- storyboard cards should help the writer see gaps, repeated beats, missing escalation, and unresolved threads
- the storyboard should support quick jump from a card into the related manuscript location
- storyboard cards should also be able to carry a short provenance note when they are generated from planning or draft material
- the storyboard should remain usable as a navigation layer even when the user is in review or inspect mode

## 7. Persistence Expectations

Canonical project and runtime state must come from the backend.

Local browser storage is acceptable for temporary workspace notes as long as the UI clearly treats it as personal workspace context rather than canonical backend state.

Required separation:

- canonical: manifests, sequences, packets, chapters, checker outputs, backend state
- personal workspace: notes, pinned references, local drafting checklists, temporary layout preferences

## 8. Artifact Review

Artifact review is important because the user should be able to inspect current story state before launching downstream steps.

The frontend should support direct review of:

- manifest
- sequence
- chapter-1
- chapter packet
- checker report

Artifact review should support:

- quick switching between related artifacts
- fixed-width reading mode for generated prose
- structural reading mode for manifests, packets, and sequence outlines
- one-click promotion from inspected artifact to planning or revision context
- extract actions that can send selected artifact text into story-bible entries, packet notes, or revision tasks
- direct review of both canonical artifacts and generated planning drafts without mixing them into a single undifferentiated view
- a visible distinction between canonical project state and user-authored workspace notes
- review panels that keep the selected artifact, the current project, and the current stage or chapter visible at the same time

Planned inspect views should extend artifact review with:

- step timeline for the selected chapter, packet, or checker run
- artifact lineage chain showing temporary, candidate, canonical, and superseded outputs
- visibility into which runtime provider and model source produced each inspectable output
- clear distinction between canonical artifacts and personal workspace notes
- deterministic routing from manuscript or review context into the relevant `steps` or `lineage` projection for the active job or checker run
- no attempt-selector UI in the first slice; the frontend should present the returned ordered items as-is
- no hidden attempt regrouping in the client; the backend order is the user-facing order
- enough room for protocol detail to be expanded without taking over the manuscript experience

## 9. Authoring And Review Requirements

The frontend should treat planning, drafting, and review as one loop instead of separate utilities.

Planning requirements:

- chapter and scene cards should expose title, intent, status, dependencies, and continuity flags
- the planning board should support drag reorder and clear incomplete or blocked states
- chapter packet assembly should show which references and constraints are included
- chapter statuses should support at least draft, revise, blocked, approved, and exported
- the planning board should support inline status changes without opening a separate detail page
- planning and review surfaces should preserve runtime-provider and model-source provenance for generated cards, packets, and summaries where relevant
- planning cards should also show which flow stage they belong to and whether that stage is user-defined or default
- when a stage is redefined, planning cards should retain their original artifact history and show a review cue instead of silently changing meaning

Drafting requirements:

- the manuscript surface should prioritize legibility and low visual noise
- current scene goals and relevant story-bible entries should remain visible without replacing the manuscript
- the author should be able to pin references and continuity warnings beside the current chapter
- the right rail should support notes, goals, and comment or issue history without obscuring the draft
- the writer should be able to open multiple chapter tabs during revision-heavy sessions
- the manuscript should expose version history and restore affordances that are clearly separate from canonical backend generation
- the manuscript editor should support selection-based writing aids that operate on highlighted text
- one selection action should perform sensory enrichment by reviewing the selected text and generating a revision grounded in sight, sound, smell, taste, and touch where appropriate
- one selection action should perform perspective shift by identifying the immediate active viewpoint context and rewriting the selected text from a different chosen character's perspective
- selection-based aids must show the result as a proposed revision or diff, never silently replacing canonical text
- selection-based aids should explain which context they used, especially for viewpoint-sensitive rewrites
- the drafting workspace should keep the current chapter or scene goal visible while the writer edits prose
- the drafting workspace should make it easy to move a passage into a revision or review state without leaving the chapter context

Manuscript aids requirements:

- manuscript aids should be treated as one coherent feature family in the right rail rather than scattered buttons
- aids should work on either the current selection or the currently active scene context
- each aid should return a proposed revision, annotation, or guided next step
- aids should preserve author control by requiring accept, reject, or refine rather than auto-apply
- generation-backed aids should expose which runtime provider and model source were used
- manuscript aids should be able to cite the scene, chapter, character, or bible entry they relied on when that context is available

Manuscript aids interaction contract for the first implementation wave:

- selection lifecycle:
  - a selection-based aid begins only when the user has an active manuscript text selection
  - the selected text should remain visibly anchored in the manuscript while the aid result is being prepared or reviewed
  - if the selection is cleared before submission, the aid should return to an idle state rather than silently switching to scene context
  - once an aid result is returned, the UI should preserve both the original selected text and the proposed output until the writer chooses an explicit action
- request surface assumptions:
  - this SRS does not assume dedicated manuscript-aids endpoints already exist in the backend
  - the first implementation wave should treat manuscript aids as a frontend interaction contract that can later bind to backend generation surfaces
  - the request surface should be described in UI terms only: selected text or active scene context, chosen aid type, optional author instructions, and current project context
  - the frontend must not imply attempt filters, advanced provider selectors, or aid-specific backend query parameters unless those are later added publicly
  - **mock service pattern**: the frontend should implement a mock service layer that returns realistic suggestion payloads for manuscript aids. A feature flag (`VITE_USE_MOCKS`) should allow switching between mock and real backend services without UI changes.
- proposed diff review flow:
  - generation-backed aids should return into a review state, not directly mutate manuscript text
  - the center pane should present the original passage and the proposed revision as a readable diff or side-by-side comparison
  - the diff review should make insertions, removals, and rewritten spans obvious without forcing the writer into a raw protocol view
  - the writer must be able to move back from diff review to the manuscript without losing the proposed result
- accept or reject or refine states:
  - `accept`: apply the proposed revision into the manuscript draft in the current editing session
  - `reject`: discard the proposal and return to the manuscript with the original text intact
  - `refine`: keep the proposal visible, preserve the original selection or scene context, and allow the writer to request a revised proposal with additional guidance
  - the UI should not auto-apply results and should not collapse accepted and rejected outcomes into the same visual treatment
- selection-based versus scene-based actions:
  - selection-based by default in the first wave:
    - sensory enrichment
    - perspective shift
    - voice match
    - pacing adjust
    - subtext pass
    - dialogue polish
    - specificity boost
    - ending beat options when a paragraph or scene ending is selected
  - scene-based by default in the first wave:
    - continuity check
    - pov integrity check
    - scene goal check
    - conflict boost
    - theme or arc alignment
    - foreshadowing pass
  - scene-based aids may still highlight relevant passages in their output, but they should begin from the active scene or chapter context rather than requiring a text selection
- provider and model provenance:
  - when backend results expose runtime provider or model source, manuscript-aids review should surface that provenance near the proposed result rather than hiding it in a debug panel
  - provenance should be compact by default, using badges, chips, or a short metadata row
  - deeper provider or model detail may be expandable, but the first visible layer should make it clear whether the result came from a known backend source
  - if provider or model provenance is unavailable, the UI should omit those labels rather than inventing placeholders that imply certainty
- manuscript aids should support a suggestion history so the writer can compare earlier proposals during revision-heavy sessions

Initial manuscript aids set:

- sensory enrichment: revise highlighted text with stronger use of the five senses where appropriate
- perspective shift: rewrite highlighted text from a different chosen character's viewpoint after inferring immediate scene context
- voice match: align the selected passage to the project's intended voice and tone
- pacing adjust: tighten, expand, or slow a selected passage while preserving intent
- subtext pass: strengthen implied emotion, tension, and what remains unsaid
- continuity check: flag contradictions against story-bible facts, timeline, and recent events
- pov integrity check: detect viewpoint leakage, head-hopping, or knowledge the current viewpoint character should not have
- scene goal check: evaluate whether the selected passage is visibly serving the current scene objective
- conflict boost: suggest specific ways to intensify friction, pressure, or stakes in the current passage
- dialogue polish: improve distinction of speaker voice, rhythm, compression, and implication
- theme or arc alignment: suggest revisions that better support the selected story arc and current arc stage
- foreshadowing pass: lightly seed later payoff, dread, or setup into the selected passage
- specificity boost: replace generic phrasing with more story-specific detail
- ending beat options: propose stronger paragraph endings, scene exits, or transition lines

Review requirements:

- checker findings should appear in a revision-focused panel, not as a disconnected tool page
- workflow recommendations should explain why a model or critic profile is suggested
- revision mode should support moving from finding to source text to planned fix with minimal navigation
- review mode should support chapter status updates and explicit handoff back to planning or drafting
- review mode should expose runtime-provider and model-source details for checker output and generated manuscript suggestions
- review mode should support jumping from a finding or artifact into inspect mode for step and lineage detail
- review mode should make it possible to mark a finding resolved, deferred, or escalated without losing its source context

## 10. Async Behavior

The contract is backend-driven progress. Even if some flows currently complete quickly, the UI must be built to poll and render exact status.

Required patterns:

- job and checker starts return immediately
- status is read from polling endpoints
- terminal success and failure states are clearly visible
- logs and result details remain inspectable after completion
- retries and reclaimed work should be visible as attempt history, not hidden behind one mutable status line

Planned inspect-endpoint support:

- the frontend should be prepared to consume dedicated read models for step records and artifact lineage without changing the three-pane workspace model
- step-record inspect views should read from:
  - `GET /jobs/{job_id}/steps`
  - `GET /role-model-checker/{run_id}/steps`
- artifact-lineage inspect views should read from:
  - `GET /jobs/{job_id}/lineage`
  - `GET /role-model-checker/{run_id}/lineage`
- the current public envelope should be treated as:
  - `job_id` or `run_id`
  - `items`
  - `meta`
- the frontend should not describe or depend on unsupported query features such as public attempt filtering in this first slice
- inspect projections should be reachable from chapter cards, manuscript tabs, checker findings, and artifact previews
- runtime-provider and model-source visibility should come from these inspect projections when available, not from guessed UI labels
- the job and checker status surfaces should keep their relationship to the current project, chapter, or selected artifact visible while polling

## 11. Feature Priorities For Spec Finalization

Highest-priority frontend features to carry forward into the final spec:

- editable story-development flow editor
- brainstorm and idea capture workspace
- story foundation screen
- character builder and relationship map
- world bible or codex rail
- arc comparison and stage-map support
- chapter and scene planning board
- story bible or codex side rail
- storyboard-driven left rail for live story progression
- manuscript-centered write view with contextual right rail
- manuscript aids feature family in the right rail
- packet builder that bridges planning and execution
- integrated checker review and revision workspace
- runtime-provider and model-source visibility in write, review, and inspect contexts
- inspect views for step records and artifact lineage within the center pane
- transparent backend progress, attempt history, and retry controls
- all of the above should be designed as one connected writing system, not as isolated utilities

These should be treated as target product features even if the current implementation is still partial.

## 12. Current Implementation Status

### 12.1 Implemented Backend (Available Now)

**Projects**:
- `GET /projects` - list projects
- `POST /projects/create` - create project
- `GET /projects/{project_id}` - get project detail
- `GET /projects/{project_id}/manifest` - get manifest artifact
- `GET /projects/{project_id}/sequence` - get sequence artifact
- `GET /projects/{project_id}/chapter-1` - get chapter-1 artifact

**Jobs**:
- `GET /jobs` - list jobs
- `POST /jobs/create` - create job (returns 202)
- `GET /jobs/{job_id}/status` - poll job status
- `GET /jobs/{job_id}/logs` - get job logs
- `GET /jobs/{job_id}/steps` - get step records for inspect
- `GET /jobs/{job_id}/lineage` - get artifact lineage for inspect

**Models**:
- `GET /models` - list available models

**Role-Model Checker**:
- `POST /role-model-checker/start` - start checker run (returns 202)
- `GET /role-model-checker/{run_id}/status` - poll checker status
- `GET /role-model-checker/{run_id}/logs` - get checker logs
- `GET /role-model-checker/{run_id}/steps` - get step records for inspect
- `GET /role-model-checker/{run_id}/lineage` - get artifact lineage for inspect

**Story Development**:
- `GET /story-development/branches?project_id={id}` - list story branches
- `POST /story-development/branches` - create story branch
- `GET /story-development/branches/active?project_id={id}` - get active branch
- `POST /story-development/branches/active` - select active branch
- `GET /story-development/branches/comparisons?project_id={id}` - list branch comparisons
- `POST /story-development/branches/comparisons` - create branch comparison
- `GET /story-development/branches/comparisons/{comparison_id}?project_id={id}` - get comparison
- `GET /story-development/branches/merge-decisions?project_id={id}` - list merge decisions
- `POST /story-development/branches/merge-decisions` - record merge decision
- `GET /story-development/branches/{branch_id}?project_id={id}` - get branch
- `GET /story-development/branches/{branch_id}/state-refs?project_id={id}` - get branch state refs
- `GET /story-development/decisions?project_id={id}` - list story decision nodes
- `GET /story-development/decisions/{node_id}?project_id={id}` - get decision node
- `GET /story-development/decisions/{node_id}/path?project_id={id}` - get decision path
- `GET /story-development/review/findings?project_id={id}` - list checker findings
- `GET /story-development/review/findings/{finding_id}?project_id={id}` - get finding
- `GET /story-development/review/decisions?project_id={id}` - list review decisions
- `GET /story-development/review/decisions/{decision_id}?project_id={id}` - get decision
- `GET /story-development/review/inspect-links?project_id={id}` - list inspect links
- `GET /story-development/review/inspect-links/{link_id}?project_id={id}` - get inspect link
- `GET /story-development/planning/sequence-plans?project_id={id}` - list sequence plans
- `GET /story-development/planning/sequence-plans/{sequence_id}?project_id={id}` - get sequence plan
- `GET /story-development/planning/chapter-plans?project_id={id}` - list chapter plans
- `GET /story-development/planning/chapter-plans/{chapter_id}?project_id={id}` - get chapter plan
- `GET /story-development/planning/scene-plans?project_id={id}` - list scene plans
- `GET /story-development/planning/scene-plans/{scene_id}?project_id={id}` - get scene plan
- `GET /story-development/planning/dependencies?project_id={id}` - list planning dependencies
- `GET /story-development/planning/chapter-packets?project_id={id}` - list chapter packets
- `GET /story-development/planning/chapter-packets/{packet_id}?project_id={id}` - get chapter packet
- `GET /story-development/drafting/draft-artifacts?project_id={id}` - list draft artifacts
- `GET /story-development/drafting/draft-artifacts/{artifact_id}?project_id={id}` - get draft artifact
- `GET /story-development/drafting/manuscript-documents?project_id={id}` - list manuscript documents
- `GET /story-development/drafting/manuscript-documents/{document_id}?project_id={id}` - get manuscript document
- `GET /story-development/drafting/revision-suggestions?project_id={id}` - list revision suggestions
- `GET /story-development/drafting/revision-suggestions/{suggestion_id}?project_id={id}` - get suggestion

**Health**:
- `GET /health` - health check

### 12.2 Implemented Frontend (React + Vite)

**Completed Tasks (FE-001 through FE-012)**:
- ✅ FE-001: Vite + React + TypeScript setup with Tailwind CSS
- ✅ FE-001A: Theming architecture with stage-based colors (light/dark mode, planning/writing/review/inspect themes)
- ✅ FE-002: Zustand + TanStack Query configuration (uiStore, workspaceStore, API client)
- ✅ FE-005: Three-pane layout shell (LeftRail, CenterPane, RightRail, BottomUtility, ModeSwitcher)
- ✅ FE-007: Planning board view with real API integration
- ✅ FE-008: Chapter/scene card components (ChapterCard, SceneCard, StatusChip, CharacterChip, DependencyBadge)
- ✅ FE-009: Chapter packet builder (PacketContents, PacketReferences)
- ✅ FE-010: TipTap editor integration with auto-save and word count
- ✅ FE-011: Chapter tab management with unsaved change warnings
- ✅ FE-012: Manuscript context rail (ChapterPlanPanel, SceneGoalsPanel, PinnedReferencesPanel)

**Vanilla JS Prototype (Legacy - Being Replaced)**:
- project creation and listing
- project detail display
- local workspace notes (localStorage)
- artifact preview for manifest, sequence, and chapter-1
- chapter packet assembly
- backend status polling (600ms interval)
- role-model checker model selection and result display
- basic job monitoring with logs

**Migration Status**: React frontend is functional and running at http://localhost:5173/. Vanilla JS prototype will be decommissioned after remaining tasks complete.

### 12.3 Deferred / Incomplete Backend

The following story-development features have backend persistence and services but **no API endpoints yet**:

- Brainstorm workspace (`BrainstormItem`, `BrainstormPromotion`)
- Foundation editor (`FoundationProfile`, `FoundationRevision`)
- Character builder (`CharacterProfile`, `RelationshipEdge`) - services exist, no routes
- World bible workspace (`WorldBibleEntry`) - services exist, no routes
- Arc comparison (`ArcCandidate`, `ArcComparisonRecord`, `ArcSelection`, `ArcStageMap`) - services exist, no routes
- Editable flow editor (`StoryFlowDefinition`, `StoryFlowStage`, `StoryFlowEdge`, `StoryFlowRule`) - services exist, no routes

The following features have **no backend implementation yet**:

- Manuscript aids endpoints (sensory enrichment, perspective shift, etc.)
- Story branching UI endpoints (backend exists, frontend needs implementation)

### 12.4 Frontend Implementation Strategy

**Hybrid approach**: The frontend will use real backend APIs where available and mock services where endpoints are incomplete. This allows UI development to proceed without blocking on backend completion.

**Mock service pattern**:
- Implement mock services that return realistic payloads matching the canonical schema
- Use environment variable `VITE_USE_MOCKS=true` to toggle between mock and real APIs
- Mock services should follow the same TypeScript interfaces as real API clients
- When backend endpoints are added, flip the flag and remove mock implementations

**Priority order**:
1. Core writing workflow (project → plan → write → review) using existing APIs
2. Inspect mode using existing step/lineage endpoints
3. Story development features with mock services where needed
4. Manuscript aids with mock service (no backend exists yet)

## 12A. Backend API Availability Matrix

| Feature | Backend Status | Frontend Approach |
|---------|---------------|-------------------|
| Projects | ✅ Complete | Use real API |
| Jobs | ✅ Complete | Use real API |
| Models | ✅ Complete | Use real API |
| Role-Model Checker | ✅ Complete | Use real API |
| Inspect (steps/lineage) | ✅ Complete | Use real API |
| Planning (read) | ✅ Complete | Use real API |
| Drafting (read) | ✅ Complete | Use real API |
| Review (read) | ✅ Complete | Use real API |
| Branching | ✅ Complete | Use real API |
| Story Decisions | ✅ Complete | Use real API |
| Flow Editor | ⚠️ Services only | Mock service |
| Brainstorm | ⚠️ Services only | Mock service |
| Foundation | ⚠️ Services only | Mock service |
| Character Builder | ⚠️ Services only | Mock service |
| World Bible | ⚠️ Services only | Mock service |
| Arc Comparison | ⚠️ Services only | Mock service |
| Manuscript Aids | ❌ Not started | Mock service |

## 13. Feature Responsibilities And Task Contracts

This section makes the frontend feature set actionable for implementation.

- project shell and project switcher:
  - responsibility: open, create, and switch projects without losing the current working context
  - consumes: project list, project detail, manifest, current workspace notes
  - produces: selected project context, active shell state, and entry into the current mode
- flow editor:
  - responsibility: let the writer add, rename, reorder, redefine, disable, archive, and delete eligible custom story-development stages
  - consumes: project flow definition, foundation notes, downstream artifact status, current stage ordering
  - produces: updated stage definitions, dependency warnings, and review cues for downstream artifacts
- brainstorm workspace:
  - responsibility: capture raw ideas and turn them into candidate story material
  - consumes: user notes, story premise, current themes, stage context, existing flow labels
  - produces: brainstorm cards, clustered ideas, premise candidates, and promote-to-foundation actions
- foundation workspace:
  - responsibility: define the stable story promise and constraints for the project
  - consumes: brainstorm material, selected arc, project constraints, existing draft context
  - produces: foundation profile, logline, tone direction, and downstream change warnings
- character builder:
  - responsibility: build characters as active story forces with goals, flaws, relationships, and change arcs
  - consumes: foundation, world context, arc choice, manuscript references
  - produces: character profiles, relationship map updates, contradiction warnings, and arc notes
- world bible workspace:
  - responsibility: store canon, rules, and continuity facts for planning and drafting
  - consumes: character context, foundation, manuscript excerpts, sequence context
  - produces: bible entries, pinned references, continuity warnings, and extractable canon notes
- arc comparison view:
  - responsibility: compare story arc options and show how each one changes the planning shape
  - consumes: premise, genre, theme, character intent, selected story direction
  - produces: arc candidates, stage-map previews, drift warnings, and chosen-arc notes
- planning board:
  - responsibility: move from story intent to beat, sequence, chapter, and scene cards
  - consumes: foundation, arc selection, character and bible context, current stage ordering
  - produces: planned cards, reordered chapters, chapter packet requests, and status updates
- drafting workspace:
  - responsibility: keep manuscript writing, story context, and version history in one view
  - consumes: draft text, chapter goals, scene goals, bible references, selection context
  - produces: draft revisions, proposed diffs, version history entries, and promotion actions
- review workspace:
  - responsibility: turn checker findings and revision suggestions into decisions
  - consumes: checker outputs, draft context, inspect provenance, chapter status
  - produces: accept, reject, refine, defer, or escalate decisions; review notes; planning handoffs
- story-direction surfaces:
  - responsibility: let the user revisit prior story-shaping decisions such as arc choices or future pivots without losing the decision trail
  - consumes: arc comparisons, arc selections, stage changes, and other persisted story decision nodes
  - produces: reviewable decision history, rationale views, explicit stay or pivot actions, and timeline or tree views showing what changed from what to what
- inspect workspace:
  - responsibility: surface step records, artifact lineage, and runtime provenance in a readable form
  - consumes: public inspect projections and current project or chapter context
  - produces: step timelines, lineage chains, provenance chips, and routes back to the related artifact
- manuscript aids panel:
  - responsibility: provide selection-aware or scene-aware revision help without mutating canonical text automatically
  - consumes: selected text, active scene context, user instructions, project context, visible story bible items
  - produces: proposed revisions, annotations, diffs, and explicit accept, reject, or refine actions

## 14. Required Screens Or Modes

Each screen should be concrete about what it takes in and what it gives back.

### 14.1 Project Setup

- user can create a project, pick or skip the default flow, set the starting story context, and open an existing project
- consumes: project list, project manifest, default flow template, saved workspace notes
- produces: new project shell, selected project, initial flow configuration, and project-level notes
- implementation cue: this screen should feel like the entry point to a writing workspace, not a generic settings page

### 14.2 Brainstorm Workspace

- user can capture raw ideas, cluster them, park them, delete them, or promote them into story foundations
- consumes: user notes, themes, premises, stage context, current project constraints
- produces: brainstorm items, clustered concept groups, premise candidates, logline candidates, and promoted seeds
- implementation cue: keep the input surface fast and low friction so the writer can think aloud without pausing to structure everything

### 14.3 Story Foundation Screen

- user can define premise, logline, tone, themes, emotional promise, audience, constraints, and success criteria
- consumes: brainstorm items, arc candidates, story goals, current project context
- produces: foundation profile, revision warnings for downstream artifacts, and foundation-linked notes
- implementation cue: surface downstream impact when foundation fields change, but do not lock the writer into a rigid order

### 14.4 Character Builder

- user can add characters, edit biographies, define wants and needs, map relationships, and track arc changes
- consumes: foundation profile, world bible entries, selected arc, chapter or scene references
- produces: character profiles, relationship edges, contradiction flags, and character-specific writing notes
- implementation cue: treat each character as an evolving story object, not a static contact card

### 14.5 World Bible Workspace

- user can add canon entries, pin references, review continuity warnings, and connect facts to characters or scenes
- consumes: foundation, characters, sequence context, draft excerpts, selected references
- produces: bible entries, pinned canon, continuity warnings, and extracted reference notes
- implementation cue: the workspace should make canon easy to search and easy to trust

### 14.6 Arc Comparison

- user can compare candidate arcs, inspect the stage map for each one, and choose or replace the current arc
- consumes: premise, genre, tone, themes, character direction, current planning context
- produces: selected arc, comparison notes, arc fit rationale, and stage-map preview
- implementation cue: the screen should show how the story would feel if the writer stays in one arc versus pivots to another

### 14.6A Story Branching

- user can fork the storyline from a decision point, name the branch, review branch history, compare alternate branches, and later choose whether to keep or merge outcomes
- consumes: branch point, current arc or planning state, decision history, and related canonical objects
- produces: story branches, branch comparisons, branch activation changes, and merge decisions
- implementation cue: the branch experience may borrow the mental model of source-control branching, but it should remain a writing workflow rather than a Git UI

### 14.7 Planning Board

- user can arrange beats, sequences, chapters, and scenes; drag to reorder; mark status; and attach references
- consumes: arc choice, foundation, character context, bible entries, current stage definitions
- produces: planning cards, chapter packets, reorder actions, blocked or missing-beat cues, and draft-ready plan states
- implementation cue: the board should support both high-level structure and chapter-level execution without changing screens

### 14.8 Drafting Workspace

- user can write prose, switch chapter tabs, inspect context, pin references, and launch manuscript aids
- consumes: chapter plan, sequence context, selected manuscript text, bible references, character context
- produces: draft text, revision proposals, accepted changes, version history entries, and artifact promotion actions
- implementation cue: keep the center pane readable and keep author control visible at every step

### 14.9 Review Workspace

- user can inspect checker findings, compare source text to proposed revisions, update chapter status, and hand work back to planning or drafting
- consumes: checker findings, draft text, inspect provenance, chapter or scene status
- produces: review decisions, resolved or deferred findings, revised text proposals, and handoff actions
- implementation cue: review should feel like a continuation of writing, not a separate admin flow

### 14.10 Inspect Workspace

- user can inspect step timelines and artifact lineage for jobs and checker runs, then return to the original manuscript or review context
- consumes: step records, lineage records, current run identifiers, and the selected project or chapter context
- produces: readable provenance, artifact ancestry, runtime-provider badges, and back-links to the source workspace
- implementation cue: the screen should present ordered records as-is and avoid extra query controls that the backend does not expose yet

### 14.11 Manuscript Aids

- user can request revision help on selected text or on the active scene context
- consumes: selected manuscript text, active scene context, optional author instructions, project context, story bible context
- produces: proposed diffs, annotations, next-step suggestions, and review actions
- implementation cue: every aid result should preserve the original text until the writer explicitly accepts it

## 15. Backend Objects Needed

The frontend should be designed around the canonical story-development contract in `docs/Story Development Canonical Contract v0.1.md`.

The frontend should use these user-facing data concepts, even where some are still target-state only:

- `Project`
- `StoryFlowDefinition`
- `StoryFlowStage`
- `BrainstormItem`
- `FoundationProfile`
- `CharacterProfile`
- `RelationshipEdge`
- `WorldBibleEntry`
- `ArcCandidate`
- `ArcComparisonRecord`
- `ArcSelection`
- `StoryDecisionNode`
- `BeatPlan`
- `SequencePlan`
- `ChapterPlan`
- `ScenePlan`
- `ChapterPacket`
- `DraftArtifact`
- `ManuscriptDocument`
- `RevisionSuggestion`
- `CheckerFinding`
- `ReviewDecision`
- `StepRecord`
- `ArtifactLineage`
- `InspectRunLink`
- `WorkspaceNote`
- `ProvenanceBadge`

Object notes:

- these objects should be rendered as UI contracts first, not assumed backend implementations
- where the backend already exists, the frontend should use the canonical server shape
- where the backend does not yet exist, the frontend should still define the visible state and expected outputs
- `PlanningCardView` is a UI projection over `BeatPlan`, `SequencePlan`, `ChapterPlan`, or `ScenePlan`; "card" should not be used as the canonical persisted backend object name
- `ManuscriptDocument` is the author-maintained editing surface; `DraftArtifact` remains the generated artifact with inspectable provenance
- user-made story-shaping decisions should be visible through first-class `StoryDecisionNode` history rather than inferred only from the latest active state
- the UI should be able to render a chronological decision timeline or decision tree using node type, change type, subject, parent link, branch id, prior state, new state, rationale, actor, and timestamp fields without reverse-engineering those details from other objects

## 16. Workflow States

The UI should display the canonical state families from `docs/Story Development Canonical Contract v0.1.md`.

Friendly labels are allowed, but they must map back to the canonical enum names.

### 16.1 Stage Configuration States

- `ENABLED`
- `DISABLED`
- `OPTIONAL`
- `ARCHIVED`

### 16.2 Stage Progress States

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `NEEDS_REVIEW`
- `COMPLETE`
- `SUPERSEDED`

### 16.3 Artifact Lifecycle States

- `DRAFT`
- `PROPOSED`
- `CANONICAL`
- `SUPERSEDED`
- `REJECTED`
- `ARCHIVED`

### 16.4 Suggestion Lifecycle States

- `REQUESTED`
- `READY`
- `ACCEPTED`
- `REJECTED`
- `REFINE_REQUESTED`
- `EXPIRED`

### 16.5 Flow Rules

- changing a stage definition should not erase historical artifacts
- accepted revisions should be clearly separated from canonical source text until the user commits them
- canonical artifacts should remain distinguishable from draft, proposed, and personal workspace notes
- inspect views should reflect the latest persisted lineage while still exposing the ordered history behind it

## 17. Backend And UX Integration Rules

- the frontend must not invent public query filters or attempt selectors that are not supported by the backend
- inspect mode should use the existing public projection endpoints and render their ordered items directly
- artifact review should use current artifact endpoints for manifest, sequence, and chapter-1 without assuming extra public artifact routes
- provenance labels should only appear when the backend returns them
- browser-local state should be used only for temporary notes, layout preferences, and other clearly non-canonical workspace data
- every generated or inspected output should remain linked to the current project, chapter, stage, or checker run
- when the user edits the flow, the UI should treat that as project configuration, not as silent mutation of generated artifacts
- generated suggestions should always return into a review state before they can affect canonical text

## 18. Implementation Order

The implementation order should stay deterministic so the workspace grows in a stable sequence:

**Phase 1: Foundation (Week 1-2) - COMPLETED ✅**
- ✅ FE-001: Vite + React + TypeScript setup with Tailwind CSS
- ✅ FE-001A: Theming architecture with stage-based colors
- ✅ FE-002: Zustand + TanStack Query configuration
- ⏳ FE-003: Project list and creation (real API) - NOT YET IMPLEMENTED
- ⏳ FE-004: Workspace notes persistence (Zustand + localStorage) - NOT YET IMPLEMENTED

**Phase 2: Three-Pane Layout + Storyboard (Week 3)**
- ✅ FE-005: Three-pane layout shell (LeftRail, CenterPane, RightRail, BottomUtility)
- ⏳ FE-005A: Storyboard rail with scene cards - NOT YET IMPLEMENTED
- ⏳ FE-005B: Story bible rail section (pinned references) - NOT YET IMPLEMENTED

**Phase 3: Flow Editor (Week 4)**
- ⏳ FE-006: Editable flow editor (mock service) - BLOCKED: Backend not available

**Phase 4: Planning Board (Week 5) - COMPLETED ✅**
- ✅ FE-007: Planning board view (real API)
- ✅ FE-008: Chapter/scene card components with drag-and-drop
- ✅ FE-009: Chapter packet builder

**Phase 5: Manuscript Editor (Week 6-7) - COMPLETED ✅**
- ✅ FE-010: TipTap editor integration
- ✅ FE-011: Chapter tab management
- ✅ FE-012: Manuscript context rail
- ⏳ FE-013: Draft artifact promotion - BLOCKED: Backend POST endpoint not available

**Phase 6: Job Execution (Week 8)**
- ⏳ FE-014: Job launch interface (real API) - NOT YET IMPLEMENTED
- ⏳ FE-015: Job status polling with TanStack Query - NOT YET IMPLEMENTED
- ⏳ FE-016: Job logs viewer - NOT YET IMPLEMENTED
- ⏳ FE-017: Bottom utility layer for job monitoring - NOT YET IMPLEMENTED

**Phase 7: Inspect & Provenance (Week 9)**
- ⏳ FE-018: Inspect mode integration - NOT YET IMPLEMENTED
- ⏳ FE-019: Step timeline component (real API) - NOT YET IMPLEMENTED
- ⏳ FE-020: Artifact lineage component (real API) - NOT YET IMPLEMENTED
- ⏳ FE-021: Provenance badges - NOT YET IMPLEMENTED

**Phase 8: Review Workspace (Week 10)**
- ⏳ FE-022: Checker findings list (real API) - NOT YET IMPLEMENTED
- ⏳ FE-023: Review decision interface (mock service) - BLOCKED: Backend POST endpoint not available
- ⏳ FE-024: Role-model checker UI (real API) - NOT YET IMPLEMENTED
- ⏳ FE-024A: Story branches UI (real API) - NOT YET IMPLEMENTED
- ⏳ FE-024B: Story decision nodes UI (real API) - NOT YET IMPLEMENTED
- ⏳ FE-024C: Inspect run links UI (real API) - NOT YET IMPLEMENTED

**Phase 9: Manuscript Aids (Week 11-12)**
- ⏳ FE-025: Manuscript aids panel (mock service) - BLOCKED: Backend POST endpoint not available
- ⏳ FE-026: Selection lifecycle handling - NOT YET IMPLEMENTED
- ⏳ FE-027: Diff review interface - NOT YET IMPLEMENTED
- ⏳ FE-028: Suggestion history (mock service) - BLOCKED: Backend POST endpoint not available

**Phase 10: Story Development Features (Week 13+)**
- ⏳ FE-029: Brainstorm workspace (mock service) - BLOCKED: Backend not available
- ⏳ FE-030: Foundation screen (mock service) - BLOCKED: Backend not available
- ⏳ FE-031: Character builder (mock service) - BLOCKED: Backend not available
- ⏳ FE-032: World bible workspace (mock service) - BLOCKED: Backend not available

**Infrastructure Tasks (Throughout)**
- ✅ FE-001A: Theming architecture with stage-based colors - COMPLETED
- ⏳ FE-004A: Error boundary components - NOT YET IMPLEMENTED
- ⏳ FE-004B: Loading skeleton components - NOT YET IMPLEMENTED
- ⏳ FE-004C: Toast notification system - NOT YET IMPLEMENTED

**Summary**: 12 tasks completed (FE-001, FE-001A, FE-002, FE-005, FE-007, FE-008, FE-009, FE-010, FE-011, FE-012), 16 tasks ready to implement (real API available), 10 tasks blocked (backend not available)

Each phase should ship with its own acceptance criteria and should not depend on future unsupported query features.

**See**: `TODO.md` for complete task specifications with backend schemas and acceptance criteria.

## 19. Deterministic Orchestrator Tasks

The orchestrator should be able to assign the frontend work as deterministic, bounded tasks.

**Technology Stack**:
- Framework: React 18 + Vite (TypeScript)
- State Management: Zustand (client state) + TanStack Query (server state)
- Routing: React Router v6
- Forms: React Hook Form + Zod validation
- Styling: Tailwind CSS
- Editor: TipTap
- HTTP: Axios with interceptors
- Drag-and-Drop: dnd-kit

- task FE-001, Vite Setup:
  - write scope: `frontend/` directory, Vite config, TypeScript config, ESLint, Prettier, Tailwind
  - expected outcome: React + TypeScript development environment with hot reload, proxy to backend on port 8000
  - acceptance cue: `npm run dev` starts dev server, `npm run build` produces production bundle

- task FE-002, State Management Setup:
  - write scope: Zustand stores, TanStack Query client configuration, Axios API client
  - expected outcome: Base state management infrastructure with devtools, retry logic, error handling
  - acceptance cue: Stores persist across reloads, Query client polls with configurable intervals

- task FE-003, Project Management:
  - write scope: Project list, creation form, project detail view, project selection
  - expected outcome: Users can create, list, select, and view projects using real backend API
  - acceptance cue: Project CRUD works end-to-end, health cards display correctly

- task FE-004, Workspace Notes:
  - write scope: Workspace notes Zustand store, auto-save with debounce, per-project isolation
  - expected outcome: Local workspace notes persist without affecting canonical state
  - acceptance cue: Notes survive page reload, are isolated per project, clearly marked as non-canonical

- task FE-005, Three-Pane Layout:
  - write scope: WorkspaceShell component, LeftRail, CenterPane, RightRail, BottomUtility
  - expected outcome: Stable three-pane layout with mode-based center pane switching
  - acceptance cue: Layout is responsive, modes switch without losing context

- task FE-005A, Storyboard Rail:
  - write scope: Storyboard component with scene cards, jump-to-manuscript linking
  - expected outcome: Storyboard shows story progression with scene-level detail
  - acceptance cue: Cards display scene purpose, characters, conflict; clicking jumps to manuscript

- task FE-005B, Story Bible Rail:
  - write scope: Story bible section in RightRail with pinning functionality
  - expected outcome: Users can pin characters, locations, rules for quick reference
  - acceptance cue: Pinned items persist, are visible while writing, can be unpinned

- task FE-006, Flow Editor:
  - write scope: Flow editor shell, stage list, stage detail panel, stage actions
  - expected outcome: Users can add, rename, reorder, disable, archive, and redefine stages
  - acceptance cue: Stage edits update project configuration without mutating historical artifacts
  - note: Uses mock service until backend API endpoints are added

- task FE-007, Planning Board:
  - write scope: Board views over `ChapterPlan` and `ScenePlan` from backend
  - expected outcome: Planning objects can be viewed, reordered, and inspected
  - acceptance cue: Cards map back to canonical plan objects, drag-and-drop works

- task FE-008, Chapter/Scene Cards:
  - write scope: Card components with status chips, arc stage labels, expandable detail
  - expected outcome: Cards show title, objective, status, dependencies, continuity flags
  - acceptance cue: Inline status changes work, cards are visually scannable

- task FE-009, Chapter Packet Builder:
  - write scope: Packet assembly UI showing references, constraints, goals
  - expected outcome: Users can preview packet contents before job launch
  - acceptance cue: Packet contents are clear, job launch integrates with packet context

- task FE-010, Manuscript Editor:
  - write scope: TipTap editor integration, auto-save, markdown import/export
  - expected outcome: Rich text editing with writing-focused UX
  - acceptance cue: Editor is legible, low visual noise, supports long-form writing

- task FE-011, Chapter Tabs:
  - write scope: Tab management, unsaved change warnings, tab persistence
  - expected outcome: Multiple chapters can be open simultaneously
  - acceptance cue: Tabs survive reload, unsaved changes are warned, quick switching works

- task FE-012, Manuscript Context Rail:
  - write scope: Right rail section showing chapter plan, scene goals, pinned references
  - expected outcome: Context stays visible while writing
  - acceptance cue: Goals and references are visible without obscuring manuscript

- task FE-013, Draft Promotion:
  - write scope: Load `DraftArtifact` from backend, promote to `ManuscriptDocument`
  - expected outcome: Generated drafts can be promoted to editable manuscript state
  - acceptance cue: Provenance is preserved, promotion is explicit

- task FE-014, Job Launch:
  - write scope: Job creation form, phase selection, model selection, payload builder
  - expected outcome: Users can launch backend jobs with proper context
  - acceptance cue: Jobs return 202, status polling begins automatically

- task FE-015, Job Polling:
  - write scope: TanStack Query polling configuration, progress indicator, terminal state handling
  - expected outcome: Job status updates in real-time with 600ms polling
  - acceptance cue: COMPLETED/FAILED states are clear, retry is available for failures

- task FE-016, Job Logs:
  - write scope: Log viewer with timestamp, level, message, auto-scroll, export
  - expected outcome: Job logs are readable and exportable
  - acceptance cue: Logs update in real-time, export downloads file

- task FE-017, Bottom Utility Layer:
  - write scope: Persistent bottom panel for job progress, logs, retry controls
  - expected outcome: Job monitoring is visible across all workspace modes
  - acceptance cue: Bottom layer stays visible during mode switches, can be collapsed

- task FE-018, Inspect Mode:
  - write scope: Inspect mode integration into center pane, steps/lineage tabs
  - expected outcome: Inspect is first-class mode, not hidden admin surface
  - acceptance cue: Mode switch preserves context, can return to manuscript

- task FE-019, Step Timeline:
  - write scope: Step timeline list from `/jobs/{id}/steps` and `/role-model-checker/{id}/steps`
  - expected outcome: Steps render in backend order with provenance badges
  - acceptance cue: Items show step label, state, provider, model; expandable detail available

- task FE-020, Artifact Lineage:
  - write scope: Lineage list from `/jobs/{id}/lineage` and `/role-model-checker/{id}/lineage`
  - expected outcome: Lineage shows artifact history with state indicators
  - acceptance cue: CANONICAL/SUPERSEDED states are clear, ancestry is visible

- task FE-021, Provenance Badges:
  - write scope: Compact provenance chips for provider, model, attempt
  - expected outcome: Provenance is visible wherever generated output appears
  - acceptance cue: Badges are compact, only show when data exists, expandable for detail

- task FE-022, Checker Findings:
  - write scope: Findings list from `/story-development/review/findings`, severity indicators
  - expected outcome: Checker findings are visible with source context
  - acceptance cue: Findings can be filtered, jumped to source text

- task FE-023, Review Decisions:
  - write scope: Accept/reject/defer/escalate/refine actions, decision history
  - expected outcome: Review decisions are recorded and visible
  - acceptance cue: Decisions route to planning/drafting, history is reviewable

- task FE-024, Role-Model Checker UI:
  - write scope: Migrate existing checker interface, model selection per role
  - expected outcome: Checker runs with model selection, results display
  - acceptance cue: Pass/fail states are clear, results integrate with review

- task FE-025, Manuscript Aids Panel:
  - write scope: Right rail aids section, selection-based and scene-based actions
  - expected outcome: Aids are organized coherently, availability based on selection
  - acceptance cue: Aids are disabled when no selection, scene actions always available
  - note: Uses mock service until backend endpoints are added

- task FE-026, Selection Lifecycle:
  - write scope: Track manuscript selection, anchor selected text, preserve during review
  - expected outcome: Selection is stable through aid request/response cycle
  - acceptance cue: Selection clears properly, aids return to idle when no selection

- task FE-027, Diff Review:
  - write scope: Side-by-side or unified diff view, accept/reject/refine controls
  - expected outcome: Proposed revisions are reviewable without auto-apply
  - acceptance cue: Diffs are readable, controls are clear, original text preserved

- task FE-028, Suggestion History:
  - write scope: List prior suggestions, compare proposals, restore rejected
  - expected outcome: Suggestion history supports revision workflows
  - acceptance cue: History is scrollable, comparisons are clear, restore works
  - note: Uses mock service until backend endpoints are added

- task FE-029, Brainstorm Workspace:
  - write scope: Idea capture board, clustering, keep/discard/park, promote actions
  - expected outcome: Brainstorm items can be captured and promoted
  - acceptance cue: Items are distinct from canonical objects, promotion is explicit
  - note: Uses mock service until backend API endpoints are added

- task FE-030, Foundation Screen:
  - write scope: Foundation fields, downstream impact warnings, revision history
  - expected outcome: Foundation can be edited with impact visibility
  - acceptance cue: Warnings appear for downstream artifacts, history is reviewable
  - note: Uses mock service until backend API endpoints are added

- task FE-031, Character Builder:
  - write scope: Character profiles, relationship map, contradiction warnings
  - expected outcome: Characters are structured story objects
  - acceptance cue: Goals, flaws, relationships visible together, contradictions flagged
  - note: Uses mock service until backend API endpoints are added

- task FE-032, World Bible Workspace:
  - write scope: Bible entries, search, pinning, continuity warnings
  - expected outcome: Canon is searchable and referenceable
  - acceptance cue: Entries are source-linked, warnings are readable in context
  - note: Uses mock service until backend API endpoints are added

These tasks are intended to be handed to agents as bounded screen-family assignments rather than broad implementation waves.

## 20. Non-Goals For The First Product Wave

- no hidden admin-only inspect surface
- no assumption of new public query filters for attempt history
- no browser-local data treated as canonical project state
- no auto-application of manuscript suggestions without explicit user action
- no hard-coded story flow that prevents stage redefinition
- no unsupported backend endpoints invented by the frontend
- no redesign that breaks the current three-pane writing direction
- no blocking frontend development on incomplete backend endpoints (use mock services)

## 21. Technology Stack Decisions

**Framework**: React 18 + Vite
- Rationale: Modern DX, fast HMR, excellent TypeScript support, small bundle sizes
- Alternative considered: Vue.js (gentle learning curve), Svelte (minimal boilerplate)

**State Management**: Zustand + TanStack Query
- Zustand: Client state (workspace notes, UI state, manuscript buffers)
- TanStack Query: Server state (all backend data with caching, polling, retry)
- Rationale: Clear separation of concerns, minimal boilerplate, excellent devtools
- Alternative considered: Redux Toolkit (more boilerplate), React Context alone (no server state)

**Routing**: React Router v6
- Rationale: Industry standard, type-safe routes, lazy loading support
- Alternative considered: No routing (mode-based center pane reduces route needs)

**Forms**: React Hook Form + Zod
- Rationale: Performance, validation schema reuse, TypeScript integration
- Alternative considered: Formik (more boilerplate), controlled components (verbose)

**Styling**: Tailwind CSS
- Rationale: Fast development, consistent design, small production bundles
- Alternative considered: CSS Modules (slower iteration), styled-components (runtime overhead)

**Editor**: TipTap
- Rationale: React-friendly, extensible, good Markdown support, selection APIs
- Alternative considered: Draft.js (Facebook-maintained but aging), ProseMirror (steeper learning curve)

**HTTP Client**: Axios
- Rationale: Interceptors for error handling, request cancellation, widely adopted
- Alternative considered: fetch (no interceptors without wrappers)

**Drag-and-Drop**: dnd-kit
- Rationale: Flexible, TypeScript-friendly, accessible
- Alternative considered: react-beautiful-dnd (less flexible, maintenance mode)

**Testing**: Vitest + React Testing Library + Playwright
- Vitest: Unit tests (fast, Vite-native)
- React Testing Library: Component tests (UX-focused)
- Playwright: E2E tests (cross-browser, reliable)

**Mock Services**: Environment-flagged mock layer
- Rationale: Allows UI development without blocking on backend completion
- Implementation: `VITE_USE_MOCKS=true` toggles between mock and real APIs
- Mock services follow same TypeScript interfaces as real API clients

## 22. Migration Strategy

**Week 1-2: Parallel Development**
- Keep existing vanilla JS frontend running at `/`
- Build new React app in `frontend/` (replaces current vanilla JS)
- Configure Vite proxy to existing backend (port 8000)

**Week 3-4: Gradual Feature Migration**
- Migrate project management first (lowest risk)
- Test thoroughly before decommissioning old UI components
- Keep both frontends available during transition if needed

**Week 5+: Cutover**
- Switch default route to React app
- Keep old UI patterns as reference for 1 month
- Decommission vanilla JS after validation

**Backend API Integration**:
- Use real APIs where available (projects, jobs, models, checker, planning, drafting, review, branching)
- Use mock services where incomplete (flow editor, brainstorm, foundation, character, world bible, arc comparison, manuscript aids)
- Feature flag allows testing with mocks even when real APIs exist

## 23. Verification Criteria

**Phase 1 Complete When**:
- `npm run dev` starts React dev server
- Projects can be created, listed, selected
- Workspace notes persist across reloads

**Phase 2 Complete When**:
- Three-pane layout is responsive
- Storyboard shows scene cards
- Story bible rail supports pinning

**Phase 3 Complete When**:
- Flow editor allows stage CRUD
- Stage reordering works
- Mock service returns realistic flow data

**Phase 4 Complete When**:
- Planning board displays chapter/scene cards
- Drag-and-drop reordering works
- Chapter packet builder shows contents

**Phase 5 Complete When**:
- Manuscript editor supports rich text
- Multiple chapter tabs work
- Draft promotion preserves provenance

**Phase 6 Complete When**:
- Jobs can be launched from UI
- Status polling updates every 600ms
- Logs are viewable and exportable

**Phase 7 Complete When**:
- Inspect mode is accessible from all contexts
- Step timeline shows backend-ordered items
- Lineage shows artifact history with states

**Phase 8 Complete When**:
- Checker findings are listed with severity
- Review decisions can be recorded
- Role-model checker UI migrated

**Phase 9 Complete When**:
- Manuscript aids panel is visible
- Selection-based aids work with mock service
- Diff review supports accept/reject/refine

**Phase 10 Complete When**:
- Brainstorm, foundation, character, world bible workspaces exist
- Mock services return realistic data
- UI is ready for backend API integration
