# Service Responsibility Matrix

This document clarifies the boundaries and responsibilities of services in `app/services/`.

## Overview

| Service | File | Primary Domain | Key Responsibilities |
|---------|------|----------------|---------------------|
| `DraftingService` | `drafting.py` | Manuscript & Draft Management | Create/edit manuscript documents, draft artifacts, revision suggestions |
| `PlanningService` | `planning.py` | Story Planning | Scene/chapter/sequence plans, dependencies, chapter packets |
| `ReviewRoutingService` | `review_routing.py` | Review Workflow | Checker findings, review decisions, inspect links |
| `StoryDecisionReviewService` | `story_decision_review.py` | Decision Tracking | Story decision nodes, branching paths, narrative forks |
| `StoryBranchingService` | `story_branching.py` | Branch Management | Story branches, comparisons, merge decisions |

---

## Detailed Service Boundaries

### DraftingService (`drafting.py`)

**Domain**: Manuscript document lifecycle and draft artifact management.

**Responsibilities**:
- Create/update manuscript documents with content
- Manage draft artifacts (uncommitted work)
- Promote drafts to manuscripts
- Handle revision suggestions for existing documents

**Key Methods**:
- `save_manuscript_document()` - Persist manuscript content
- `promote_draft_to_manuscript()` - Convert draft to official document
- `create_revision_suggestion()` - Propose text changes
- `list_draft_artifacts()` / `get_draft_artifact()` - Query drafts

**Schemas**: `ManuscriptDocument`, `DraftArtifact`, `RevisionSuggestion`

---

### PlanningService (`planning.py`)

**Domain**: Pre-writing story structure and organization.

**Responsibilities**:
- Manage hierarchical planning (sequences → chapters → scenes)
- Track dependencies between planning elements
- Generate chapter packets for writing sessions

**Key Methods**:
- `list_scene_plans()` / `get_scene_plan()` - Scene-level planning
- `list_chapter_plans()` / `get_chapter_plan()` - Chapter organization
- `list_sequence_plans()` - High-level story arcs
- `list_planning_dependencies()` - Track relationships

**Schemas**: `ScenePlan`, `ChapterPlan`, `SequencePlan`, `PlanningDependency`, `ChapterPacket`

---

### ReviewRoutingService (`review_routing.py`)

**Domain**: Quality assurance and review workflow.

**Responsibilities**:
- Record decisions on checker findings (accept/reject/defer/etc.)
- Create inspect links for traceability
- Route review items to appropriate handlers

**Key Methods**:
- `record_review_decision()` - Log decision on a target object
- `create_inspect_link()` - Link inspection runs to objects
- `list_checker_findings()` - Query quality issues

**Schemas**: `ReviewDecision`, `CheckerFinding`, `InspectRunLink`

**Target Kinds**: Can review any `StoryObjectType`:
- `checker_finding` - Quality assurance findings
- `artifact` - Draft or manuscript artifacts  
- `scene_plan`, `chapter_plan`, etc. - Planning elements

---

### StoryDecisionReviewService (`story_decision_review.py`)

**Domain**: Narrative branching and decision tracking.

**Responsibilities**:
- Track story decision nodes (narrative forks)
- Maintain parent paths for decision trees
- Query decisions by subject type/id

**Key Methods**:
- `list_story_decision_nodes()` - All decisions in project
- `get_story_decision_node()` - Single decision details
- `inspect_story_decision_node()` - Decision with ancestor path
- `list_story_decision_path()` - Full path to a decision

**Schemas**: `StoryDecisionNode`, `StoryDecisionNodeLink`

**Key Distinction from ReviewRoutingService**:
- **ReviewRoutingService**: Records *reviewer decisions* (accept/reject findings)
- **StoryDecisionReviewService**: Tracks *narrative decisions* (story branching points, creative choices)

---

### StoryBranchingService (`story_branching.py`)

**Domain**: Parallel story development branches.

**Responsibilities**:
- Create/manage alternative story branches
- Compare branches for merge analysis
- Record merge decisions between branches

**Key Methods**:
- `create_story_branch()` - Start new branch
- `get_active_story_branch()` / `select_active_branch()` - Branch switching
- `compare_story_branches()` - Analyze differences
- `record_branch_merge_decision()` - Document merge rationale

**Schemas**: `StoryBranch`, `BranchStateRef`, `BranchComparisonRecord`, `BranchMergeDecision`

---

## Service Interaction Patterns

### Drafting → Review Workflow

```
DraftingService.create_draft() 
  → Checker runs analysis
  → ReviewRoutingService.list_checker_findings()
  → ReviewRoutingService.record_review_decision(decision="accept")
  → DraftingService.promote_draft_to_manuscript()
```

### Planning → Drafting Pipeline

```
PlanningService.get_chapter_packet(chapter_id)
  → Provides scene plans, dependencies, context
  → DraftingService.save_manuscript_document(content=...)
```

### Branch Management with Decisions

```
StoryBranchingService.create_story_branch()
  → StoryDecisionReviewService.list_story_decision_nodes()
  → Compare branches via StoryBranchingService.compare_story_branches()
  → Record merge decision via StoryBranchingService.record_branch_merge_decision()
```

---

## Unimplemented Services (Frontend Components Exist)

| Component | Missing Service | Required Endpoints |
|-----------|-----------------|--------------------|
| Flow Editor | `FlowConfigurationService` | GET/POST/PUT flow stages, reorder |
| Brainstorm Workspace | `BrainstormService` | Create/list sparks, generate premises |
| Foundation Profile | `FoundationService` | Get/update foundation profile |
| Character Manager | `CharacterService` | CRUD character profiles, relationships |
| World Bible | `WorldBibleService` | CRUD world entries |

---

## Notes

- All services depend on `StoryDevelopmentRepository` for persistence
- Services are designed to be swappable (dependency injection pattern)
- No service should directly access database; all through repository layer
- Service errors raise specific exception types (`*NotFoundError`, `*ValidationError`)
