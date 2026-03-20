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

## 5. Main Surface Areas

The UI should include:

- project list and creation flow
- active project detail and health cues
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

## 6. Workspace Information Architecture

The target frontend should use a stable workspace layout:

- left rail: storyboard, chapter or scene list, arc-stage progression, chapter status, and autogenerated or editable scene cards
- center pane: manuscript editor, artifact reader, packet builder, review surface, or inspect view for runtime provenance
- right rail: manuscript aids, story bible context, continuity notes, scene goals, checker outcomes, workflow controls, and provider or model-source diagnostics
- bottom utility layer: job progress, logs, retry controls, version history access, and status diagnostics

The center pane should be mode-based rather than route-heavy. A writer should be able to move between:

- plan
- write
- review
- inspect

without feeling like they left the project workspace.

Inspect mode expectations:

- inspect mode should be a first-class center-pane surface rather than a hidden admin drawer
- inspect mode should support planned step-record and artifact-lineage endpoints once those projections are exposed
- inspect mode should make it obvious which attempt, step, runtime provider, model source, and artifact version produced the current output
- inspect mode should keep protocol detail expandable so manuscript focus is not overwhelmed

Storyboard expectations:

- the left storyboard should represent what is happening in the story now, not just file navigation
- storyboard cards may be authored manually or generated by AI from the current draft and planning artifacts
- each card should be able to show scene purpose, active characters, emotional turn, conflict, and likely next beat
- storyboard cards should help the writer see gaps, repeated beats, missing escalation, and unresolved threads
- the storyboard should support quick jump from a card into the related manuscript location

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

Planned inspect views should extend artifact review with:

- step timeline for the selected chapter, packet, or checker run
- artifact lineage chain showing temporary, candidate, canonical, and superseded outputs
- visibility into which runtime provider and model source produced each inspectable output
- clear distinction between canonical artifacts and personal workspace notes

## 9. Authoring And Review Requirements

The frontend should treat planning, drafting, and review as one loop instead of separate utilities.

Planning requirements:

- chapter and scene cards should expose title, intent, status, dependencies, and continuity flags
- the planning board should support drag reorder and clear incomplete or blocked states
- chapter packet assembly should show which references and constraints are included
- chapter statuses should support at least draft, revise, blocked, approved, and exported
- the planning board should support inline status changes without opening a separate detail page
- planning and review surfaces should preserve runtime-provider and model-source provenance for generated cards, packets, and summaries where relevant

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

Manuscript aids requirements:

- manuscript aids should be treated as one coherent feature family in the right rail rather than scattered buttons
- aids should work on either the current selection or the currently active scene context
- each aid should return a proposed revision, annotation, or guided next step
- aids should preserve author control by requiring accept, reject, or refine rather than auto-apply
- generation-backed aids should expose which runtime provider and model source were used

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
- inspect projections should be reachable from chapter cards, manuscript tabs, checker findings, and artifact previews
- runtime-provider and model-source visibility should come from these inspect projections when available, not from guessed UI labels

## 11. Feature Priorities For Spec Finalization

Highest-priority frontend features to carry forward into the final spec:

- story bible or codex side rail
- chapter and scene planning board
- storyboard-driven left rail for live story progression
- manuscript-centered write view with contextual right rail
- manuscript aids feature family in the right rail
- packet builder that bridges planning and execution
- integrated checker review and revision workspace
- runtime-provider and model-source visibility in write, review, and inspect contexts
- inspect views for step records and artifact lineage within the center pane
- transparent backend progress, attempt history, and retry controls

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

Deferred:

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
