# Story Development Product Spec v1.3

**Change log from v1.1 (v1.3 Pattern Extraction - April 27, 2026)**:
- Added Section 9B: Pattern Extraction — generalized service that analyzes any story or mythology text and extracts storytelling DNA including archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities; supports narrative and mythology source types with three generation modes (same_world, new_characters, transposed); extends SceneContext with pattern_guidance and author_prompt for P-100/P-300 integration

**Change log from v1.0 (v1.1 Mythos Extraction - April 26, 2026)**:
- Added Section 9A: Mythos Extraction — analyzes mythology texts and extracts archetypal patterns, narrative structures, cosmic rules, and symbolic motifs to guide original story generation via same-world, transposed, or pure-pattern modes

**Change log from v0.1 (v1.0 Scope Clarification - March 29, 2026)**:
- Updated Section 4.1 to clarify that current v1.0 provides read projections of flow stages; full mutation support for adding, reordering, and deleting stages is deferred to a future release wave
- Updated Section 8.3 to document that current v1.0 provides character profile editing via CharacterBuilder routed state; relationship-map workflows are deferred to a future release wave
- Updated Section 10.2 to clarify that current v1.0 provides read-only arc projections via getArcCandidates, getArcSelections, and getArcStageMaps; arc selection mutations and comparison mutations are deferred to a future release wave
- Updated Section 14.2 screens list to note v1.0 scope for Character Builder (profile editing only) and Arc Selection (read-only projections)
- Added explicit documentation that planning is read-heavy for v1.0 via existing GET planning endpoints; create, update, reorder, and packet-edit mutations are deferred
- Updated April 2026: Deferred mutations are now implemented. Section 4.1 flow mutations (add, rename, redefine, reorder, disable, archive, delete stages) are available via `POST /v1/story-development/flow/stages/init` and `PATCH /v1/story-development/flow/stages/{stage_id}`. Section 10.2 arc mutations (POST/PUT/DELETE on candidates, selections, stage-maps, and comparisons) are now available. Section 11.3 planning mutations (POST/GET/PUT/PATCH on sequence, chapter, scene plans; POST on chapter packets; POST /planning/reorder) are available. Character relationship mutations (GET /relationships, PATCH /relationships/{id}, DELETE /relationships/{id}) are available.

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

- `docs/Story Development Canonical Contract v1.0.md` defines the approved object names, lifecycle enums, editable-flow semantics, and planning or drafting terminology for this feature family

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

Optional pre-steps:
- Mythos Extraction (Section 9A) can seed the entire flow from mythology texts, producing foundation, world bible, archetypes, and entities before entering the core flow above.
- Pattern Extraction (Section 9B) can seed the entire flow from any story or mythology text, extracting storytelling DNA including voice profile, narrative structure, thematic constraints, and entities, then guiding generation through same-world, new-characters, or transposed modes.

This flow should be project-configurable.

### 4.1 Editable Flow Requirements (Target Product Requirement)

This section describes the target product requirement for editable flow management.

**Current v1.0 scope**: The routed PlanningView provides read projections of flow stages via existing backend services. Full mutation support is now implemented via `POST /v1/story-development/flow/stages/init` (initialize or restore flow from counter table), `PATCH /v1/story-development/flow/stages/{stage_id}` (rename, redefine, update display_name/description/notes/depends_on/stage_configuration_state), `POST /v1/story-development/flow/stages` (create initial stages), `POST /v1/story-development/flow/stages/reorder` (reorder stages), and `DELETE /v1/story-development/flow/stages/{stage_id}` (delete custom stages when no dependent stages exist).

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

### 8.3 Character Tools (Target Product Requirement)

**Current v1.0 scope**: The CharacterBuilder component in PlanningView provides character profile editing via GET|POST|PATCH /v1/story-development/characters endpoints. Character relationship mutations (GET /v1/story-development/relationships, PATCH /v1/story-development/relationships/{edge_id}, DELETE /v1/story-development/relationships/{edge_id}) are now implemented. Relationship-map graph UI and advanced analysis tools described below are deferred to a future release wave.

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

## 9A. Mythos Extraction

Mythos Extraction analyzes mythology texts and extracts archetypal patterns, narrative structures, cosmic rules, and symbolic motifs. These patterns guide original story generation through three modes: same-world (mythological setting), transposed (new setting with mythic patterns), or pure-pattern (structures only, free-form world).

### 9A.1 User Workflow

1. User pastes mythology texts in the Extract Mythos modal
2. User optionally specifies source tradition and selects generation mode
3. System analyzes text via LLM and extracts structured patterns
4. New project is created with extracted foundation, world bible, archetypes, and entities
5. User proceeds to Planning Workspace guided by extracted patterns

### 9A.2 Extraction Schema

- **Archetypal Pattern**: name, description, character_type, narrative_beats[], examples_from_text[]
- **Narrative Structure**: name, phases[], tension_curve, resolution_type
- **Cosmic Rule**: rule, enforcement, exceptions[]
- **Symbolic Motif**: symbol, meaning, narrative_function
- **Mythos Entity**: name, entity_type (deity|location|concept|force), archetype, domain_or_power, canonical_facts[]
- **Relationship**: source, target, relationship_type, description

### 9A.3 Generation Modes

| Mode | Constraint Level | Setting | Characters | Patterns |
|------|-----------------|---------|------------|----------|
| Same World | High | Mythological world as-is | Original characters following archetypes | All extracted patterns applied |
| Transposed | Medium | New setting | Archetypes mapped to new roles | Structural rules adapted |
| Pure Pattern | Low | Free-form | Free-form | Narrative structures and themes only |

### 9A.4 Persistence Mapping

- Foundation Profile: thematic_spine, emotional_promise, tone_direction from analysis; narrative_constraints stores archetypal patterns + narrative structures as JSON
- World Bible: cosmic rules and symbolic motifs as "concept" entries
- Character Profiles: archetypal pattern carriers (role_in_story = "archetype"); deities/forces as mythos entities
- Relationships: entity relationship edges

### 9A.5 Integration with Generation Pipeline

- P-100 Architect receives mythos_context block based on generation mode
- P-300 Drafter enforces cosmic rules as hard constraints during drafting
- Consistency Critic verifies story obeys extracted cosmic rules (future: dedicated mythos_consistency check)

### 9A.6 Backend Objects Needed

- `MythosExtractionService` — extraction orchestration, LLM call, transactional persistence
- `build_mythos_analysis_request()` — prompt builder for pattern extraction
- `_parse_mythos_analysis()` — JSON-to-dataclass parser with type coercion

## 9B. Pattern Extraction

Pattern Extraction is the generalized service that analyzes any story or mythology text and extracts its "storytelling DNA" — archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities. Extracted patterns guide original story generation through three modes: same-world (use established world/characters), new-characters (same world, original cast), or transposed (map patterns to new setting).

Pattern Extraction generalizes Mythos Extraction: when `source_type` is `"mythology"`, the service delegates to `MythosExtractionService`. When `source_type` is `"narrative"`, it uses the narrative-specific extraction pipeline with additional voice profile, narrative pattern, and thematic constraint fields.

### 9B.1 User Workflow

1. User pastes any story or mythology text in the Extract Patterns modal
2. User selects source type (narrative or mythology) and generation mode
3. System analyzes text via LLM and extracts structured patterns
4. New project is created with extracted foundation, world bible, character archetypes, voice profile, narrative patterns, and thematic constraints
5. User proceeds to Planning Workspace guided by extracted patterns

### 9B.2 Extraction Schema

Shared across source types:
- **Archetypal Pattern**: name, description, character_type, narrative_beats[], examples_from_text[]
- **Narrative Structure**: name, phases[], tension_curve, resolution_type
- **World Rule**: rule, enforcement, exceptions[]
- **Symbolic Motif**: symbol, meaning, narrative_function
- **Story Entity**: name, entity_type, archetype, domain_or_power, canonical_facts[]
- **Relationship**: source, target, relationship_type, description

Narrative-specific additions:
- **Narrative Pattern**: pacing, chapter_structure, conflict_type, dialogue_style, scene_transition
- **Voice Profile**: narrative_voice, sentence_rhythm, descriptive_density, humor_level, emotional_temperature
- **Thematic Constraint**: theme, moral_stance, recurring_questions[], forbidden_elements[]

### 9B.3 Generation Modes

| Mode | Constraint Level | Setting | Characters | Patterns |
|------|-----------------|---------|------------|----------|
| Same World | High | Source story's world as-is | Original characters following extracted patterns | All extracted patterns applied |
| New Characters | Medium | Source story's world | Original cast fulfilling extracted archetypes | Structural rules and voice profile adapted |
| Transposed | Low | New setting | Archetypes mapped to new roles | Narrative structures, themes, and voice adapted |

### 9B.4 Persistence Mapping

- Foundation Profile: thematic_spine, emotional_promise, tone_direction from analysis; narrative_constraints stores archetypal patterns + narrative structures + thematic constraints as JSON
- World Bible: world rules → "concept" entries titled "World Rule: {rule}"; symbolic motifs → "concept" entries titled "Motif: {symbol}"
- Character Profiles: narrative archetypes stored with role_in_story="archetype"; key entities stored with appropriate role
- Relationships: entity relationship edges with hash-based edge IDs

### 9B.5 Integration with Generation Pipeline

- P-100 Architect prompt adapted with `_build_pattern_context_block()` for pattern context injection across 3 generation modes
- SceneContext extended with `pattern_guidance` (voice profile, world rules, thematic constraints) and `author_prompt` fields
- P-300 Drafter includes pattern guidance + per-chapter author direction via SceneContext
- Pattern guidance influences tone, structure, and character voice during drafting

### 9B.6 Backend Objects Needed

- `PatternExtractionService` — generalized service that dispatches to narrative or mythology extraction
- `build_narrative_analysis_request()` — prompt builder for LLM-based narrative analysis
- `_parse_llm_json()` — robust JSON extraction: direct JSON, markdown fences, trailing/leading text
- `_transactional_import()` — single raw SQLite connection with `BEGIN`, direct parameterized SQL

### 9B.7 API Endpoints

- `POST /projects/import-patterns` (201 Created) — standalone: provides text, extracts patterns, creates or updates project with results
- `POST /projects/{project_id}/extract-patterns` (201 Created) — targeted: extracts patterns from an existing project's manuscript documents

## 10. Story Arc Selection

### 10.1 User Outcome

The user should be able to choose an arc deliberately, compare alternatives, and change the chosen arc without losing project knowledge.

### 10.2 Arc Support Requirements (Target Product Requirement)

**Current v1.0 scope**: The PlanningView arcs tab provides arc projections via `getArcCandidates`, `getArcSelections`, and `getArcStageMaps` which consume GET /v1/story-development/arcs/candidates, GET /v1/story-development/arcs/selections, and GET /v1/story-development/arcs/stage-maps. Arc selection mutations and comparison mutations are now implemented via POST /v1/story-development/arcs/candidates, POST /v1/story-development/arcs/comparisons, POST /v1/story-development/arcs/selections, PATCH /v1/story-development/arcs/selections/{selection_id}, DELETE /v1/story-development/arcs/selections/{selection_id}, and POST /v1/story-development/arcs/stage-maps. Arc-driven guidance features described below remain deferred.

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

### 10.5 Forked Storyline Requirement

At any meaningful decision point, the user should be able to fork the storyline and explore an alternate branch.

The fork should:

- preserve the branch point and the state it forked from
- keep arc comparisons, selections, and decision history reviewable per branch
- allow the user to compare branches later
- allow the user to keep one branch active while preserving alternates
- support later selective merge behavior through explicit decisions rather than silent overwrite

Backend note:

- do not use Git as the canonical backend for this feature
- branching should be modeled in structured backend objects so branch state, decision history, planning objects, and lineage remain queryable and inspectable

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

**Current v1.0 scope**: The PlanningView planning tab provides read-heavy planning visibility via `getSequencePlans`, `getChapterPlans`, `getScenePlans`, `getPlanningDependencies`, and `getChapterPackets` which consume GET /v1/story-development/planning/sequence-plans, GET /v1/story-development/planning/chapter-plans, GET /v1/story-development/planning/scene-plans, GET /v1/story-development/planning/dependencies, and GET /v1/story-development/planning/chapter-packets. Create and update mutations for sequence plans (`POST /v1/story-development/planning/sequence-plans`, `PATCH /v1/story-development/planning/sequence-plans/{sequence_id}`), chapter plans (`GET /v1/story-development/planning/chapter-plans`, `GET /v1/story-development/planning/chapter-plans/{chapter_id}`), and chapter packets (`POST /v1/story-development/planning/chapter-packets`, `PATCH /v1/story-development/planning/chapter-packets/{packet_id}`) are now available. Planning reorder is available via `POST /v1/story-development/planning/reorder`.

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
- character backgrounds (filtered by ChapterPlan.active_character_ids when chapter_id is provided)
- world bible entries
- sequence or chapter plan
- prior draft text
- **prior chapter summaries** (last 3 completed chapters: key events, character states, unresolved threads)
- **pattern guidance** (voice profile, world rules, thematic constraints from PatternExtractionAnalysis)
- **author prompt** (per-chapter author direction)
- user instructions

### 12.4 Multi-Chapter Generation

P-300 supports multi-chapter drafting with cross-chapter continuity:

- `chapter_id` in job payload triggers parameterized output path (`chapters/{chapter_id}.md`)
- Prior chapter context injection: last 3 completed chapters summarized and included in LLM prompt
- Active character filtering: only characters marked as active in ChapterPlan are injected into prompt
- Pattern guidance injection: voice profile, world rules, thematic constraints from extracted patterns
- Default token budget: 8000 tokens (~2000 words per chapter), overridable via payload
- ChapterOrchestrator: sequential runner for multi-chapter generation with graceful per-chapter error handling

#### 12.4.1 Batch Multi-Chapter Mode

P-300 accepts `chapter_ids` list in job payload for sequential drafting within a single job:
- Chapters drafted one at a time, each with own output file and step record
- ChapterSummarizerService extracts PriorChapterSummary after each draft (key events, character states, unresolved threads)
- Summaries injected into subsequent chapters via SceneContextService (capped at last 3)
- ManuscriptDocument records auto-created for Writing workspace integration

#### 12.4.2 ChapterSummarizerService

LLM-based service that reads completed chapter markdown and extracts structured context:
- key_events: significant plot points (max 10)
- character_states: character conditions/goals at chapter end (max 10)
- unresolved_threads: open questions, cliffhangers (max 5)
- Error-tolerant: returns None on failure, never blocks pipeline

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

4. Character Builder (Current v1.0: character profile editing via routed state using GET|POST|PATCH /v1/story-development/characters; relationship CRUD via GET|PATCH|DELETE /v1/story-development/relationships)
- character cards
- relationship map (graph UI deferred to future release; CRUD mutations available via API)
- arc-change fields
- contradictions and secrets panel

5. World Bible Workspace
- codex entries
- locations, factions, rules, history
- continuity warning panel

6. Arc Selection and Comparison (Current v1.0: projections via getArcCandidates, getArcSelections, getArcStageMaps consuming GET /v1/story-development/arcs/*; mutations via POST/DELETE /v1/story-development/arcs/candidates, POST /v1/story-development/arcs/comparisons, POST/DELETE /v1/story-development/arcs/selections, PATCH /v1/story-development/arcs/selections/{id}, POST /v1/story-development/arcs/stage-maps)
- recommended arcs
- arc comparison table (mutations available; graph UI for comparison deferred to future release)
- stage-map preview
- "stay" versus "pivot" suggestion panel (deferred to future release)

7. Planning Board (Current v1.0: read projections via GET /v1/story-development/planning/*; mutations via POST/PATCH /v1/story-development/planning/sequence-plans, GET /v1/story-development/planning/chapter-plans, POST/PATCH /v1/story-development/planning/chapter-packets, POST /v1/story-development/planning/reorder)
- sequence view
- chapter cards
- scene cards
- drag reorder (mutations available via POST /v1/story-development/planning/reorder)
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

The eventual backend model should use the canonical names in `docs/Story Development Canonical Contract v1.0.md`.

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
- `ArcComparisonRecord`
- `ArcSelection`
- `ArcStageMap`
- `StoryDecisionNode`
- `StoryBranch`
- `BranchPoint`
- `BranchStateRef`
- `BranchComparisonRecord`
- `BranchMergeDecision`
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
- `CheckerFinding`
- `ReviewDecision`
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

`ArcComparisonRecord`

- persisted ranked comparison between two or more arc candidates
- includes the candidate set, ranking, comparison notes, and durable review context for later revisit

`ArcSelection`

- active arc plus explicit links to the comparison records that informed the decision

`StoryDecisionNode`

- persisted typed decision-tree object for story-shaping choices such as arc pivots, stage changes, deviations, branch points, and future comparable planning decisions
- must remain reviewable when the user returns later to understand why a story direction changed and from which parent path it diverged
- must be detailed enough to generate a decision timeline or tree showing what changed, what it changed from, what it changed to, why the user changed it, and what comparison or review context informed the choice

`StoryBranch`, `BranchPoint`, `BranchStateRef`, `BranchComparisonRecord`

- these are the current canonical branching objects for forked storyline identity, fork origin, branch-local state references, and branch-to-branch comparison history
- they should be treated as structured backend records, not Git branches or file-level snapshots
- only one active branch should exist per project at a time in persisted branch state

`BranchMergeDecision`

- records intended or accepted merge outcomes between branches
- remains distinct from branch comparison and from branch state selection

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

The canonical state families for story-development features live in `docs/Story Development Canonical Contract v1.0.md`.

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
3. brain dump capture flow
4. character builder
5. world bible or codex workspace
6. arc selection and comparison
7. planning board
8. drafting workspace
9. suggestion and revision workflow
10. continuity and review integration
11. richer inspect and provenance integration across all story-development artifacts

## 19. Brain Dump Workflow

The Brain Dump project type provides a distraction-free capture mode for authors who want to brainstorm without structural constraints.

### 19.1 User Flow

1. **Create Brain Dump project** — user selects "Brain Dump" as the project type during creation. The form shows only the project name field.
2. **Free-text capture** — user is taken directly to a distraction-free canvas with a large textarea. No cards, no status dropdowns, no categorization.
3. **Auto-save** — text is auto-saved with a 2-second debounce. Word count is displayed subtly in the bottom-right corner.
4. **Organize with AI** — when the user has written more than 100 characters, a floating "Organize with AI" button appears. Clicking it triggers mock AI categorization.
5. **Categorization** — the raw text is split into paragraphs and distributed across 10 categories: Character, Location, Plot Point, Theme, Conflict, World Building, Dialogue, Relationship, Object, Rule. Each category receives items displayed as cards with colored badges.
6. **Review and edit** — organized items appear in the standard Brainstorm Workspace where the user can continue managing them (keep/park/discard, clustering, promotion).

### 19.2 Session State Machine

- `active` — new or editing session. Can transition to `organized` or `archived`.
- `organized` — AI categorization has been applied. Can transition to `archived`.
- `archived` — session is final and immutable.

Invalid transitions (e.g., `organized` -> `active`, `archived` -> `organized`) raise `BrainDumpValidationError`.

### 19.3 Mock AI Categorization

The organize endpoint uses a placeholder implementation:
- Splits raw text by double-newlines into blocks
- Round-robin assigns each block to one of the 10 categories
- Creates `BrainstormItem` records with the appropriate `item_type`

This is clearly marked with a TODO for future LLM-based NLP integration.

### 19.4 API Endpoints

- `POST /v1/story-development/braindump/sessions` — create session (201)
- `GET /v1/story-development/braindump/sessions` — list sessions (200)
- `GET /v1/story-development/braindump/sessions/{id}` — get session (200)
- `PATCH /v1/story-development/braindump/sessions/{id}` — update session (200)
- `DELETE /v1/story-development/braindump/sessions/{id}` — delete session (204)
- `POST /v1/story-development/braindump/sessions/{id}/organize` — organize and categorize (201)

### 19.5 Frontend Routes

- `/workspace/:projectId/braindump` — BrainDumpView renders the canvas and organize flow
- Brain Dump projects default to the braindump route when opened

## 20. Non-Goals For The First Product Wave

This spec does not require immediate implementation of:

- full multiplayer collaboration
- final publishing workflow
- cloud sync
- automatic resolution of conflicting story facts without user review

The first wave should focus on a strong local single-writer story-development loop with durable backend provenance.
