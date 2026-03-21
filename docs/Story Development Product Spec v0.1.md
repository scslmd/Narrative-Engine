# Story Development Product Spec v0.1

## 1. Purpose

This document defines the target product feature set for guided story development in Narrative-Engine.

It exists to turn the current high-level product direction into a concrete, buildable specification for:

- brainstorming and early idea capture
- editable core-flow planning
- character background development
- world bible or codex management
- story arc selection and comparison
- sequence, chapter, and scene planning
- drafting and revision suggestions
- backend objects and workflow-state expectations

This spec assumes one critical product rule:

- the user must be able to add, redefine, reorder, disable, archive, or delete eligible custom parts of the story-development flow at any time

Canonical contract reference:

- `docs/Story Development Canonical Contract v0.1.md` defines the approved object names, lifecycle enums, editable-flow semantics, and planning or drafting terminology for this feature family

The system should guide strongly without behaving like a rigid template engine.

## 2. Product Goal

Narrative-Engine should help a writer move from an undeveloped idea to a structured, draftable story while preserving author control, continuity, provenance, and room for change.

The system should support both:

- exploratory writing where the writer does not know the story yet
- structured writing where the writer wants explicit arcs, planning stages, and continuity discipline

## 3. Core Principle

The story-development flow is editable, not prescribed.

Rules:

- the product may suggest a default flow
- the user may skip any stage
- the user may insert a custom stage
- the user may rename stages or redefine what a stage means in the current project
- the user may revisit earlier stages after drafting has begun
- the system must preserve provenance when a later artifact depends on an earlier artifact that has since been revised

The engine should treat the core flow as:

- a recommended scaffold
- a configurable workflow graph
- a set of reusable planning and drafting tools

not as a locked sequence.

## 4. Default Story-Development Flow

The default guided flow should be:

1. Brainstorm
2. Story Foundation
3. Character Background
4. World Bible
5. Story Arc Selection
6. Sequence and Chapter Planning
7. Drafting
8. Review and Suggestions

This flow should be project-configurable.

### 4.1 Editable Flow Requirements

Each `StoryFlowStage` should support:

- `enabled`
- `display_name`
- `description`
- `position`
- `depends_on`
- `writer_notes`
- `stage_configuration_state`
- `stage_progress_state`
- `custom_prompt_guidance`
- `stage_kind`

The UI should support:

- adding a custom stage
- deleting a custom stage only when deletion rules allow it
- reordering stages
- marking a stage optional
- attaching artifacts to a stage
- changing the working definition of a stage inside the project

The product should distinguish:

- stage kind: brainstorm, foundation, character, world bible, arc selection, planning, drafting, review, inspect, or custom
- stage instance: the project-local configured `StoryFlowStage`
- stage progress state: where that stage currently stands in the active project

Removal semantics:

- default stages should be disabled or archived rather than deleted
- custom stages may be deleted only when they are not required to preserve active dependencies or retained history
- redefining a stage updates future guidance and labels but does not rewrite historical artifacts

## 5. Feature Scope

The feature family should include:

- idea capture and brainstorming
- project foundation and promises
- character and relationship development
- world and continuity bible management
- arc-aware planning assistance
- scene and chapter planning
- manuscript drafting
- revision and suggestion tools
- inspectable provenance across all generated outputs

## 6. Brainstorming

### 6.1 User Outcome

The user should be able to take fragments such as:

- premise sparks
- themes
- images
- genre intentions
- scene fragments
- dialogue ideas
- constraints
- "what if" questions

and grow them into concrete story directions.

### 6.2 Required Capabilities

- freeform idea capture
- idea clustering
- conflict generation
- stakes generation
- theme exploration
- premise expansion
- alternative concept branches
- "keep", "discard", and "park for later" states
- promotion of brainstorm content into structured project artifacts

### 6.3 Structured Outputs

Brainstorm outputs should be promotable into:

- premise candidates
- loglines
- thematic statements
- world seeds
- character seeds
- scene seeds
- project constraints

## 7. Story Foundation

### 7.1 User Outcome

The user should be able to define the stable foundation of the project before or during planning.

### 7.2 Required Foundation Fields

- project premise
- logline
- thematic spine
- emotional promise
- tone and voice direction
- target audience
- narrative constraints
- desired complexity level
- success definition for the draft

### 7.3 Rules

- foundation fields must remain editable after downstream work exists
- the system should show downstream artifacts that may need review when foundation fields change
- foundation changes should not silently overwrite generated planning or draft artifacts

## 8. Character Background

### 8.1 User Outcome

The user should be able to build characters as story engines, not just reference cards.

### 8.2 Character Record Shape

Each major character should support:

- `character_id`
- `display_name`
- `role_in_story`
- `archetype`
- `external_goal`
- `internal_need`
- `misbelief_or_wound`
- `core_fear`
- `primary_strength`
- `fatal_flaw_or_limitation`
- `contradictions`
- `backstory_summary`
- `voice_notes`
- `relationship_map`
- `secrets`
- `values`
- `taboos`
- `change_axis`
- `arc_stage_notes`
- `continuity_facts`
- `writer_notes`

### 8.3 Character Tools

- generate or refine character backstory
- compare character arcs
- detect redundant characters
- suggest relationship tension
- suggest arc-aligned turning points
- promote manuscript excerpts into character knowledge

## 9. World Bible

### 9.1 User Outcome

The user should be able to maintain a persistent world bible or codex that supports both planning and drafting.

### 9.2 World-Bible Categories

- locations
- factions
- rules
- history
- lore
- magic or technology systems
- cultural norms
- timeline anchors
- continuity facts
- unresolved promises

### 9.3 Bible Entry Shape

Each entry should support:

- `entry_id`
- `entry_type`
- `title`
- `summary`
- `canonical_facts`
- `related_characters`
- `related_locations`
- `continuity_warnings`
- `visibility_scope`
- `source_artifacts`
- `writer_notes`

### 9.4 Rules

- bible content should be extractable from brainstorms, sequences, and manuscript drafts
- bible entries should be referenceable from planning and drafting surfaces
- continuity tools should use bible entries as canonical context

## 10. Story Arc Selection

### 10.1 User Outcome

The user should be able to choose an arc deliberately, compare alternatives, and change the chosen arc without losing project knowledge.

### 10.2 Arc Support Requirements

The system should support:

- arc recommendation from premise and genre
- arc comparison
- stage-map display
- arc adherence guidance
- arc drift warnings
- arc recovery suggestions
- arc-specific next-step recommendations

### 10.3 Arc-Aware Suggestion Rules

Suggestions should differ by arc family.

Examples:

- romance:
  - intimacy pacing
  - emotional risk
  - misunderstanding pressure
  - vulnerability beats
- mystery or thriller:
  - clue timing
  - suspicion management
  - reveal control
  - pressure escalation
- tragedy:
  - inevitability reinforcement
  - flaw activation
  - irreversible cost
  - collapse pacing
- heroic or quest arc:
  - trials
  - sacrifice
  - moral testing
  - transformed return
- corruption or fall arc:
  - rationalization ladder
  - moral compromise
  - consequence widening
  - self-deception reinforcement

### 10.4 Flexibility Rule

The selected arc should behave as:

- a planning lens
- a suggestion engine
- a diagnostic tool

not as a hard schema that blocks user choices.

## 11. Sequence and Chapter Planning

### 11.1 User Outcome

The user should be able to turn abstract story intent into concrete planning artifacts.

### 11.2 Planning Layers

- beats
- sequences
- chapters
- scenes
- optional chapter packets

### 11.3 Required Planning Fields

Planning objects should support:

- objective
- conflict
- stakes
- dependency
- arc stage
- active characters
- continuity requirements
- unresolved questions
- status
- writer notes

### 11.4 Planner Capabilities

- suggest next beats
- propose alternate sequence shapes
- detect missing escalation
- detect repeated beats
- map chapter cards to arc stages
- build chapter packets from sequence context

## 12. Drafting

### 12.1 User Outcome

The user should be able to generate and refine draft prose while keeping planning, continuity, and character intent visible.

### 12.2 Drafting Requirements

- chapter drafting from planning context
- scene drafting from chapter context
- continuation drafting
- alternate version generation
- chapter rewrite or redraft support
- provenance visibility for generated text

### 12.3 Draft Context Inputs

The drafting system should be able to consume:

- manifest and project foundation
- selected arc and stage context
- character backgrounds
- world bible entries
- sequence or chapter plan
- prior draft text
- user instructions

## 13. Suggestions and Revision Tools

### 13.1 User Outcome

The user should receive context-aware suggestions instead of generic writing assistance.

### 13.2 Suggestion Families

- conflict boost
- emotional clarity
- continuity correction
- arc alignment
- pacing adjustment
- sensory enrichment
- point-of-view correction
- dialogue polish
- ending beat options
- alternate next-scene options

### 13.3 Suggestion Rules

- suggestions must preserve author control
- suggestions must not silently overwrite canonical draft text
- suggestions should explain what context they used
- arc-aware suggestions should cite the selected arc or current arc stage when relevant

## 14. Screens

### 14.1 Project Workspace

The main workspace should stay aligned with the current three-pane direction.

- left rail:
  - story flow stages
  - storyboard
  - chapter and scene list
  - arc-stage map
- center pane:
  - brainstorm
  - plan
  - write
  - review
  - inspect
- right rail:
  - world bible
  - character context
  - continuity notes
  - manuscript aids
  - checker findings
  - workflow controls

### 14.2 Required Screens or Modes

1. Project Setup
- create project
- define premise and constraints
- choose or skip default flow stages

2. Brainstorm Workspace
- freeform idea board
- clustered concept cards
- promote-to-foundation actions

3. Story Foundation Screen
- logline
- premise
- themes
- promises
- constraints

4. Character Builder
- character cards
- relationship map
- arc-change fields
- contradictions and secrets panel

5. World Bible Workspace
- codex entries
- locations, factions, rules, history
- continuity warning panel

6. Arc Selection and Comparison
- recommended arcs
- arc comparison table
- stage-map preview
- "stay" versus "pivot" suggestion panel

7. Planning Board
- sequence view
- chapter cards
- scene cards
- drag reorder
- dependency and arc-stage badges

8. Drafting Workspace
- manuscript center pane
- scene or chapter goals
- pinned world and character context
- manuscript aids rail

9. Review Workspace
- checker findings
- continuity warnings
- suggested revisions
- handoff back to planning or drafting

10. Inspect Workspace
- step timeline
- lineage chain
- runtime provenance
- artifact ancestry

## 15. Backend Objects Needed

The eventual backend model should use the canonical names in `docs/Story Development Canonical Contract v0.1.md`.

Required canonical objects for this feature family:

- `Project`
- `StoryFlowDefinition`
- `StoryFlowStage`
- `StoryFlowEdge`
- `StoryFlowRule`
- `BrainstormItem`
- `BrainstormPromotion`
- `FoundationProfile`
- `FoundationRevision`
- `CharacterProfile`
- `RelationshipEdge`
- `WorldBibleEntry`
- `ArcCandidate`
- `ArcSelection`
- `ArcStageMap`
- `BeatPlan`
- `SequencePlan`
- `ChapterPlan`
- `ScenePlan`
- `ChapterPacket`
- `PlanningDependency`
- `DraftArtifact`
- `ManuscriptDocument`
- `RevisionSuggestion`
- `SuggestionRequest`
- `ContinuityIssue`
- `CheckerFinding`
- `ReviewDecision`
- `ReviewTask`
- `StepRecord`
- `ArtifactLineage`
- `InspectRunLink`

### 15.1 Object Notes

`StoryFlowDefinition`

- project-specific editable stage graph

`BrainstormItem`

- raw or clustered ideas with promotion state

`FoundationProfile`

- stable story premise and constraints

`CharacterProfile`

- structured narrative character background

`WorldBibleEntry`

- persistent codex or continuity object

`ArcSelection`

- active arc plus comparison history

`SequencePlan`, `ChapterPlan`, `ScenePlan`

- planning hierarchy with explicit dependencies

`DraftArtifact`

- generated prose artifact with provenance

`ManuscriptDocument`

- author-maintained editable manuscript state

`RevisionSuggestion`

- non-destructive proposed revision or guidance output

Planning note:

- plan objects are canonical persisted records
- cards are UI renderings of those plan objects rather than separate canonical backend objects unless a future spec promotes them explicitly

## 16. Workflow States

The canonical state families for story-development features live in `docs/Story Development Canonical Contract v0.1.md`.

### 16.1 Stage Configuration State

- `ENABLED`
- `DISABLED`
- `OPTIONAL`
- `ARCHIVED`

### 16.2 Stage Progress State

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `NEEDS_REVIEW`
- `COMPLETE`
- `SUPERSEDED`

### 16.3 Artifact-Lifecycle Expectations

- `DRAFT`
- `PROPOSED`
- `CANONICAL`
- `SUPERSEDED`
- `REJECTED`
- `ARCHIVED`

### 16.4 Suggestion-Lifecycle Expectations

- `REQUESTED`
- `READY`
- `ACCEPTED`
- `REJECTED`
- `REFINE_REQUESTED`
- `EXPIRED`

### 16.5 Flow Rules

- changing a foundation artifact may push downstream stage progress back to `IN_PROGRESS` or `NEEDS_REVIEW`
- accepted generated artifacts must remain inspectable after replacement
- writer-authored notes should not be silently invalidated by backend generation

## 17. Backend and UX Integration Rules

- every generated artifact should be inspectable through durable step and lineage state
- frontend surfaces should distinguish canonical project knowledge from temporary workspace notes
- user-defined flow changes should not break backend provenance
- arc-aware suggestions must remain advisory rather than mandatory
- the product should always reveal what source context was used for a suggestion or generated artifact when available

## 18. Implementation Order

Recommended build order:

1. editable story-flow definition
2. brainstorm workspace
3. character builder
4. world bible or codex workspace
5. arc selection and comparison
6. planning board
7. drafting workspace
8. suggestion and revision workflow
9. continuity and review integration
10. richer inspect and provenance integration across all story-development artifacts

## 19. Non-Goals For The First Product Wave

This spec does not require immediate implementation of:

- full multiplayer collaboration
- final publishing workflow
- cloud sync
- automatic resolution of conflicting story facts without user review

The first wave should focus on a strong local single-writer story-development loop with durable backend provenance.
