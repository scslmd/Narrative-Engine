# Story Development Canonical Contract v0.1

## 1. Purpose

This document is the canonical contract for story-development terminology across the product spec, backend SRS, frontend SRS, and orchestrator task spec.

Use it to keep the story-development feature set deterministic for planning and implementation.

## 2. Canonical Naming Rules

- one concept should have one approved canonical name
- UI labels may differ from backend object names, but the mapping must be explicit
- if a legacy or shorthand term is still useful, treat it as an alias only and do not use it as the primary contract term
- when this document conflicts with a story-development term elsewhere, this document wins

## 3. Flow Model

Three different things must stay distinct:

- `stage_kind`: the story-development category such as `brainstorm`, `foundation`, `character`, `world_bible`, `arc_selection`, `planning`, `drafting`, `review`, or a custom kind
- `StoryFlowStage`: the project-local configured stage node in the editable flow graph
- `stage_progress_state`: the current progress status of that stage in the active project

The default flow is a scaffold, not a locked sequence.

## 4. Editable-Flow Semantics

Canonical edit actions:

- `add_stage`: insert a new `StoryFlowStage` into the project flow
- `rename_stage`: change the display label of a stage without changing its identity
- `redefine_stage`: change the stage purpose, notes, guidance, or instructions for future work without rewriting historical artifacts
- `reorder_stage`: change stage position or dependency edges
- `disable_stage`: keep the stage record and history but remove it from active future guidance
- `mark_stage_optional`: keep the stage available but not required
- `archive_stage`: hide the stage from the active flow while preserving history and provenance
- `delete_custom_stage`: permanently remove a custom stage only when it has no dependent active stages and no required retained history is being orphaned

Rules:

- "remove" is not a canonical contract term because it is ambiguous
- default stages should be disabled or archived, not deleted
- custom stages may be deleted only when the product explicitly chooses deletion and the preconditions above are met
- historical artifacts stay linked to the stage identity that existed when they were created

## 5. Canonical Objects

### 5.1 Flow And Foundation

| Canonical name | Definition | Owning layer | Allowed alias notes |
| --- | --- | --- | --- |
| `StoryFlowDefinition` | Project-local editable flow graph | backend, docs | none |
| `StoryFlowStage` | Project-local stage node with order, guidance, and dependencies | backend, frontend, docs | "stage instance" in prose only |
| `StoryFlowEdge` | Dependency or ordering edge between stages | backend, docs | none |
| `StoryFlowRule` | Rule that constrains stage behavior or transitions | backend, docs | none |
| `BrainstormItem` | Raw or clustered idea entry with keep, discard, park, and promotion state | backend, frontend, docs | none |
| `BrainstormPromotion` | Record that maps brainstorm material into structured downstream artifacts | backend, docs | none |
| `FoundationProfile` | Stable story promise and constraint set for the project | backend, frontend, docs | none |
| `FoundationRevision` | Historical revision of the foundation profile | backend, docs | none |

### 5.2 Character, World, And Arc

| Canonical name | Definition | Owning layer | Allowed alias notes |
| --- | --- | --- | --- |
| `CharacterProfile` | Structured character object with goals, needs, flaws, and continuity facts | backend, frontend, docs | none |
| `RelationshipEdge` | Explicit relationship record between characters | backend, frontend, docs | none |
| `WorldBibleEntry` | Canonical setting or continuity record | backend, frontend, docs | "codex entry" as UI label only |
| `ArcCandidate` | Candidate story arc option under comparison | backend, frontend, docs | none |
| `ArcComparisonRecord` | Persisted comparison result over two or more arc candidates, including ranked outcomes and reviewable reasoning | backend, frontend, docs | "arc comparison" in prose only |
| `ArcSelection` | Chosen arc plus explicit links to the comparison records that informed the choice | backend, frontend, docs | none |
| `ArcStageMap` | Stage-map projection implied by the chosen arc | backend, docs | "arc-stage preview" in UI only |
| `StoryDecisionNode` | Persisted typed decision-tree node for story-shaping choices such as arc selection, pivots, stage changes, deviations, branch points, and merges | backend, frontend, docs | "decision history node" in prose only |

Rules:

- `ArcComparisonRecord` is a canonical persisted object, not transient service memory
- `ArcSelection` should reference the comparison records that informed the choice rather than absorbing comparison history into one opaque field
- if the user revisits arc choice later, prior comparison records must remain inspectable
- user-made story-shaping changes should be persisted as `StoryDecisionNode` objects so they can be reviewed later
- if a user changes direction, the prior node must remain inspectable rather than being overwritten by the newer node
- `StoryDecisionNode` must be specific enough to reconstruct a timeline and tree of arc decisions, pivots, deviations from prior direction, stage changes, branch points, and merges
- a decision node should identify at minimum: `node_type`, `change_type`, `subject_type`, `subject_id`, `parent_node_id`, `branch_id`, `summary`, `prior_state_ref` or prior state summary, `new_state_ref` or new state summary, `decision_made_at`, `made_by`, and typed links to any related or informing object
- typed node fields must use canonical enums rather than free-form labels to prevent spelling drift and query ambiguity
- child nodes are reconstructed by querying `parent_node_id`; they should not be stored as a mutable embedded child list

Implemented canonical schema shape:

`StoryDecisionNode`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `node_id` | `str` | yes | non-blank stable node identifier |
| `project_id` | `str` | yes | non-blank project identifier |
| `node_type` | `StoryDecisionNodeType` | yes | enum-backed node category |
| `change_type` | `StoryDecisionChangeType` | yes | enum-backed story change classification |
| `subject_type` | `StoryObjectType` | yes | enum-backed canonical object type |
| `subject_id` | `str` | yes | non-blank subject object identifier |
| `parent_node_id` | `str \| None` | no | nullable parent link for timeline or tree reconstruction |
| `branch_id` | `str \| None` | no | nullable branch membership identifier |
| `summary` | `str` | yes | short human-readable summary for timeline and tree views |
| `prior_state_ref` | `str \| None` | no | nullable machine-readable prior-state reference |
| `prior_state_summary` | `str \| None` | no | nullable human-readable prior-state summary |
| `new_state_ref` | `str \| None` | no | nullable machine-readable new-state reference |
| `new_state_summary` | `str \| None` | no | nullable human-readable new-state summary |
| `reason_or_note` | `str \| None` | no | nullable rationale or note |
| `decision_made_at` | `datetime` | yes | decision timestamp |
| `made_by` | `str` | yes | non-blank actor identifier |
| `related_object_links` | `list[StoryDecisionNodeLink]` | yes | defaults to empty list |
| `informing_object_links` | `list[StoryDecisionNodeLink]` | yes | defaults to empty list |

`StoryDecisionNodeLink`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `object_type` | `StoryObjectType` | yes | enum-backed canonical linked-object type |
| `object_id` | `str` | yes | non-blank linked object identifier |
| `relation_kind` | `str` | yes | non-blank relationship label such as `primary`, `selected_arc`, or `informed_by` |

Validation rule:

- at least one of `prior_state_ref`, `prior_state_summary`, `new_state_ref`, or `new_state_summary` must be present

Required node enum families:

- `StoryDecisionNodeType`
  - `DECISION`
  - `BRANCH_POINT`
  - `MERGE`
- `StoryDecisionChangeType`
  - `ARC_SELECTION`
  - `ARC_PIVOT`
  - `STORY_DEVIATION`
  - `STAGE_RENAME`
  - `STAGE_REDEFINE`
  - `STAGE_REORDER`
  - `STAGE_CONFIGURATION`
  - `FOUNDATION_REVISION`
  - `CHARACTER_REVISION`
  - `WORLD_BIBLE_REVISION`
  - `PLANNING_PIVOT`
  - `BRANCH_CREATED`
  - `BRANCH_ACTIVATED`
  - `BRANCH_MERGED`
- `StoryObjectType`
  - `STORY_FLOW_DEFINITION`
  - `STORY_FLOW_STAGE`
  - `FOUNDATION_PROFILE`
  - `FOUNDATION_REVISION`
  - `CHARACTER_PROFILE`
  - `RELATIONSHIP_EDGE`
  - `WORLD_BIBLE_ENTRY`
  - `ARC_CANDIDATE`
  - `ARC_COMPARISON_RECORD`
  - `ARC_SELECTION`
  - `ARC_STAGE_MAP`
  - `BEAT_PLAN`
  - `SEQUENCE_PLAN`
  - `CHAPTER_PLAN`
  - `SCENE_PLAN`
  - `CHAPTER_PACKET`
  - `STORY_BRANCH`
  - `BRANCH_POINT`
  - `DRAFT_ARTIFACT`
  - `MANUSCRIPT_DOCUMENT`
  - `REVISION_SUGGESTION`
  - `REVIEW_DECISION`
  - `CHECKER_FINDING`

### 5.3 Planning

| Canonical name | Definition | Owning layer | Allowed alias notes |
| --- | --- | --- | --- |
| `BeatPlan` | Lowest-level planning beat object | backend, docs | none |
| `SequencePlan` | Sequence-level planning object | backend, frontend, docs | none |
| `ChapterPlan` | Chapter-level planning object | backend, frontend, docs | none |
| `ScenePlan` | Scene-level planning object | backend, frontend, docs | UI may still render as a scene card |
| `ChapterPacket` | Structured drafting packet built from planning context | backend, frontend, docs | none |
| `PlanningDependency` | Explicit planning dependency between plan objects | backend, docs | none |
| `PlanningCardView` | UI projection of a planning object for board or rail rendering | frontend, docs | replaces ambiguous `PlanningCard`, `SequenceCard`, and `ChapterCard` as persisted names |

Rules:

- `BeatPlan`, `SequencePlan`, `ChapterPlan`, and `ScenePlan` are canonical persisted planning objects
- cards are presentation views over those plan objects unless a future spec explicitly promotes a card to a persisted object

### 5.3A Branching

| Canonical name | Definition | Owning layer | Allowed alias notes |
| --- | --- | --- | --- |
| `StoryBranch` | Durable branch identity for a forked storyline path | backend, frontend, docs | "branch" in prose only |
| `BranchPoint` | The persisted decision-node fork point that a branch originates from | backend, docs | none |
| `BranchStateRef` | Project-scoped record that links a branch to a canonical object state or decision-node path | backend, docs | none |
| `BranchComparisonRecord` | Persisted comparison between two branches with reviewable notes | backend, frontend, docs | "branch comparison" in prose only |
| `BranchMergeDecision` | Persisted merge-intent or merge-outcome record between two branches | backend, docs | none |

Rules:

- `StoryBranch`, `BranchPoint`, `BranchStateRef`, `BranchComparisonRecord`, and `BranchMergeDecision` are now part of the implemented canonical backend baseline
- only one active branch should exist per project in persisted branch state
- branch comparisons must remain reviewable records and must not mutate branch state implicitly
- branching services and branching API routes are now part of the implemented backend baseline

### 5.4 Drafting, Review, And Inspect

| Canonical name | Definition | Owning layer | Allowed alias notes |
| --- | --- | --- | --- |
| `DraftArtifact` | Generated prose artifact produced by a draft task with provenance | backend, docs | none |
| `ManuscriptDocument` | Author-maintained editable manuscript state for a chapter or scene | frontend, backend, docs | replaces ambiguous "draft version" as the primary authoring object |
| `RevisionSuggestion` | Non-destructive proposed diff, rewrite, or guidance result | backend, frontend, docs | replaces ambiguous `SuggestionResult` where the output is specifically a proposed change |
| `ReviewDecision` | Accept, reject, defer, escalate, or refine decision tied to a suggestion or finding | backend, frontend, docs | none |
| `StoryDecisionNode` | Persisted typed decision-tree node for story-shaping choices outside suggestion review | backend, frontend, docs | distinct from `ReviewDecision` |
| `CheckerFinding` | Review or checker issue linked to source text or artifacts | backend, frontend, docs | `CriticFinding` may still exist as an internal checker subtype |
| `StepRecord` | Persisted execution step row | backend, frontend, docs | none |
| `ArtifactLineage` | Persisted artifact provenance row | backend, frontend, docs | replaces `ArtifactLineageRecord` as the canonical name |
| `InspectRunLink` | Pointer from a user-facing object to related inspectable run identifiers | backend, frontend, docs | none |
| `WorkspaceNote` | Browser-local or user-local working note that is non-canonical | frontend, docs | none |

Drafting rules:

- generated prose belongs in `DraftArtifact`
- author-edited text belongs in `ManuscriptDocument`
- proposed changes belong in `RevisionSuggestion`
- a review or author action is captured in `ReviewDecision`
- accepting a suggestion updates manuscript state through an explicit decision and must not erase the originating `DraftArtifact`
- broader story-shaping user choices are captured in `StoryDecisionNode`
- those nodes must support timeline views, branch reconstruction, and "why did this change?" review flows without inference from current state alone

## 6. Canonical State Families

### 6.1 Stage Configuration State

- `ENABLED`
- `DISABLED`
- `OPTIONAL`
- `ARCHIVED`

### 6.2 Stage Progress State

- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `NEEDS_REVIEW`
- `COMPLETE`
- `SUPERSEDED`

### 6.3 Artifact Lifecycle State

- `DRAFT`
- `PROPOSED`
- `CANONICAL`
- `SUPERSEDED`
- `REJECTED`
- `ARCHIVED`

### 6.4 Suggestion Lifecycle State

- `REQUESTED`
- `READY`
- `ACCEPTED`
- `REJECTED`
- `REFINE_REQUESTED`
- `EXPIRED`

### 6.5 Execution State

- `ACCEPTED`
- `PENDING`
- `CLAIMED`
- `RUNNING`
- `VALIDATING`
- `PERSISTING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

### 6.6 UI Display Mapping Rule

- frontend display labels may use friendlier words such as "active", "complete", or "ready for review"
- those labels must map back to the canonical enum names above
- the docs should not define a second competing enum family just for UI wording

## 7. Operation Families

| Operation family | Expected input shape | Expected output shape | Side effect |
| --- | --- | --- | --- |
| `capture_*` | source text, scope, actor, context | stored object id plus normalized record | create or update one bounded record |
| `promote_*` | source object ids plus target object kind | target object id plus source links | create structured downstream object with provenance |
| `compare_*` | two or more candidate ids | comparison record or ranked result | no destructive mutation |
| `detect_*` | active object ids plus validation context | finding list or warning list | create findings, not content rewrites |
| `generate_*` | target scope plus author or project context | generated artifact id plus provenance | create new generated artifact |
| `rewrite_*` | source text plus explicit rewrite instruction | revision suggestion id plus diff | create non-destructive suggestion only |
| `route_*` | source finding or artifact id plus destination area | handoff link or task id | create a review or planning handoff record |
| `decide_*` | suggestion or finding id plus decision | review decision id plus resulting state | apply explicit decision without silent mutation |
| `record_decision_*` | decision subject ids plus chosen action and rationale | story decision node id plus affected object links | persist a reviewable user decision without erasing prior decisions |

## 8. Deterministic Naming Guidance

- use `plan` for persisted planning records
- use `card` only for UI renderings of plan records
- use `artifact` for generated content with provenance
- use `document` for author-maintained manuscript state
- use `suggestion` for non-destructive proposed changes
- use `finding` for review or validation output
- use `decision node` for durable user-made story-shaping choices that must remain reviewable
