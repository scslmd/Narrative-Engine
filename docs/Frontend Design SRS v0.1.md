# Frontend Design SRS v0.4

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

Implemented now:

- project creation and listing
- project detail display
- local workspace notes
- artifact preview for manifest, sequence, and chapter-1
- chapter packet assembly
- backend status polling
- role-model checker model selection and result display
- inspect endpoints and lineage views for jobs and checker runs
- runtime-provenance-aware artifact review for the current implemented slices

Deferred:

- editable story-development flow editor
- brainstorm workspace
- foundation editor
- character builder
- world bible workspace
- arc comparison screen
- integrated story bible or codex rail
- dedicated planning board
- storyboard-driven write layout
- manuscript aids feature family
- manuscript-first write workspace
- inspect views for dedicated step-record and artifact-lineage endpoints
- persistent runtime-provider and model-source visibility across write and review flows
- richer drafting review surfaces
- production-grade orchestration UX
- full runtime parity with the target execution model

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
- `ArcSelection`
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

1. project shell and flow editor
2. brainstorm workspace and foundation screen
3. character builder and world bible workspace
4. arc comparison and planning board
5. drafting workspace and manuscript aids panel
6. review workspace and chapter handoff actions
7. inspect workspace and provenance badges
8. status, history, and retry polish

Each step should ship with its own acceptance criteria and should not depend on future unsupported query features.

## 19. Deterministic Orchestrator Tasks

The orchestrator should be able to assign the frontend work as deterministic, bounded tasks.

- task FE-01, Flow Editor:
  - write scope: flow editor shell, stage list, and stage detail panel only
  - expected outcome: the user can add, rename, reorder, disable, archive, mark optional, and redefine stages using the canonical editable-flow semantics
  - acceptance cue: stage edits update project configuration without mutating historical artifacts
- task FE-02, Brainstorm Workspace:
  - write scope: brainstorm capture board, keep or discard or park actions, and promote affordances
  - expected outcome: brainstorm items can be captured, clustered, and routed into structured story-development work
  - acceptance cue: brainstorm output stays distinct from promoted canonical objects
- task FE-03, Foundation Screen:
  - write scope: foundation fields, downstream-impact cues, and revision warning presentation
  - expected outcome: the writer can edit foundation data after downstream work exists and see review cues
  - acceptance cue: foundation changes never imply silent overwrite of planning or manuscript state
- task FE-04, Character Builder:
  - write scope: character editor, relationship map, contradiction cues, and arc-note surfaces
  - expected outcome: character data behaves as a structured story object rather than a flat profile card
  - acceptance cue: major character goals, flaws, relationships, and continuity facts remain visible together
- task FE-05, World Bible Workspace:
  - write scope: bible entry list, detail editor, pinned canon, and continuity warning panel
  - expected outcome: canon entries are searchable, referenceable, and visibly separate from personal notes
  - acceptance cue: extracted facts remain source-linked and continuity warnings remain readable in context
- task FE-06, Arc Comparison:
  - write scope: arc recommendation list, comparison table, and stage-map preview only
  - expected outcome: the writer can compare arcs and choose one without treating the choice as blocking
  - acceptance cue: "stay" versus "pivot" guidance is visible and advisory
- task FE-07, Planning Board:
  - write scope: board views over `BeatPlan`, `SequencePlan`, `ChapterPlan`, and `ScenePlan`
  - expected outcome: planning objects can be reordered and inspected without inventing a separate persisted card contract
  - acceptance cue: card rendering clearly maps back to canonical plan objects
- task FE-08, Drafting Workspace:
  - write scope: manuscript center pane, pinned context, chapter tabs, and draft-to-review handoff controls
  - expected outcome: `ManuscriptDocument` editing remains distinct from generated `DraftArtifact` output
  - acceptance cue: the writer can tell whether they are viewing generated output, editable manuscript state, or a proposed revision
- task FE-09, Manuscript Aids:
  - write scope: selection actions, scene actions, suggestion history, and diff review
  - expected outcome: each aid returns a `RevisionSuggestion` instead of silently mutating manuscript text
  - acceptance cue: accept, reject, and refine decisions are explicit and stateful
- task FE-10, Review Workspace:
  - write scope: checker finding list, source-text comparison, review decisions, and planning or drafting handoff actions
  - expected outcome: findings and revision suggestions become explicit decisions tied to source context
  - acceptance cue: findings can be resolved, deferred, or escalated without losing provenance
- task FE-11, Inspect Workspace:
  - write scope: step timeline, lineage chain, provenance badges, and return links to related workspace context
  - expected outcome: inspect mode renders backend-ordered items directly and stays first-class in the workspace
  - acceptance cue: the user can move from manuscript or review into inspect and back without losing selection
- task FE-12, Provenance And Status:
  - write scope: compact status, runtime-provider, model-source, and attempt-history cues across generated-output surfaces
  - expected outcome: users can tell what produced a draft, suggestion, or checker output wherever it appears
  - acceptance cue: provenance appears only when known and never invents unsupported details

These tasks are intended to be handed to agents as bounded screen-family assignments rather than broad implementation waves.

## 20. Non-Goals For The First Product Wave

- no hidden admin-only inspect surface
- no assumption of new public query filters for attempt history
- no browser-local data treated as canonical project state
- no auto-application of manuscript suggestions without explicit user action
- no hard-coded story flow that prevents stage redefinition
- no unsupported backend endpoints invented by the frontend
- no redesign that breaks the current three-pane writing direction
