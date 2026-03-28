# Backend Features Not Yet Implemented

**Last Updated**: March 24, 2026  
**Status**: Services exist with persistence, but API routes not wired

---

## Summary

| Category | Service File | Methods Available | API Routes Missing | Frontend Impact |
|----------|--------------|-------------------|-------------------|-----------------|
| Brainstorm | `app/services/brainstorm.py` | 4 methods | All endpoints | FE-029 blocked |
| Foundation | `app/services/foundation.py` | 6 methods | All endpoints | FE-030 blocked |
| Editable Flow | `app/services/editable_flow.py` | 5 methods | All endpoints | FE-006 blocked |
| Story Knowledge | `app/services/story_knowledge.py` | 12 methods | All endpoints | FE-031, FE-032 blocked |
| Drafting (Write) | `app/services/drafting.py` | 2 write methods | POST endpoints only | FE-013, FE-025, FE-028 blocked |
| Review Routing (Write) | `app/services/review_routing.py` | 2 write methods | POST endpoints only | FE-023 blocked |

---

## 1. Brainstorm Service

**Service**: `app/services/brainstorm.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)

### Available Methods
```python
def capture_brainstorm_item(
    project_id: str,
    content: str,
    tags: list[str] | None = None,
    source_notes: str | None = None
) -> BrainstormItem

def cluster_brainstorm_items(
    project_id: str,
    item_ids: list[int],
    cluster_key: str | None = None
) -> tuple[BrainstormItem, ...]

def promote_brainstorm_item(
    project_id: str,
    item_id: int,
    target_kind: StoryObjectType,
    target_id: str,
    promotion_notes: str | None = None
) -> BrainstormPromotion

def list_promotions(project_id: str) -> tuple[BrainstormPromotion, ...]
```

### Missing API Routes
- `GET /story-development/brainstorm/items?project_id={id}` - List brainstorm items
- `POST /story-development/brainstorm/items` - Create/capture item
- `POST /story-development/brainstorm/items/{item_id}/cluster` - Cluster items
- `POST /story-development/brainstorm/promotions` - Promote to canonical object
- `GET /story-development/brainstorm/promotions?project_id={id}` - List promotions

### Frontend Impact
- **FE-029**: Brainstorm workspace requires mock service until routes added

---

## 2. Foundation Service

**Service**: `app/services/foundation.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)

### Available Methods
```python
def get_foundation_profile(project_id: str | UUID) -> FoundationReadResult

def list_foundation_revisions(
    project_id: str | UUID
) -> tuple[FoundationRevision, ...]

def create_foundation_revision(
    project_id: str | UUID,
    premise_text: str | None = None,
    logline: str | None = None,
    themes: list[str] | None = None,
    constraints: list[str] | None = None,
    revision_notes: str | None = None
) -> FoundationWriteResult

def update_foundation_revision(
    project_id: str | UUID,
    revision_id: str,
    premise_text: str | None = None,
    logline: str | None = None,
    themes: list[str] | None = None,
    constraints: list[str] | None = None,
    revision_notes: str | None = None
) -> FoundationWriteResult

def list_downstream_review_cues(
    project_id: str | UUID
) -> tuple[FoundationDownstreamReviewCue, ...]
```

### Missing API Routes
- `GET /story-development/foundation/profile?project_id={id}` - Get active foundation
- `GET /story-development/foundation/revisions?project_id={id}` - List revision history
- `POST /story-development/foundation/revisions` - Create new revision
- `PUT /story-development/foundation/revisions/{revision_id}` - Update revision
- `GET /story-development/foundation/downstream-cues?project_id={id}` - Get impact cues

### Frontend Impact
- **FE-030**: Foundation screen requires mock service until routes added

---

## 3. Editable Flow Service

**Service**: `app/services/editable_flow.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)

### Available Methods
```python
def create_default_flow(
    *, project_id: str, project_name: str
) -> StoryFlowDefinition

def get_flow(project_id: str) -> StoryFlowDefinition

def list_stages(project_id: str) -> list[StoryFlowStage]

def delete_custom_stage(
    *, project_id: str, stage_id: str
) -> StoryFlowStage
```

### Missing API Routes
- `GET /story-development/flow?project_id={id}` - Get flow definition
- `POST /story-development/flow` - Create default flow for project
- `GET /story-development/stages?project_id={id}` - List stages
- `DELETE /story-development/stages/{stage_id}?project_id={id}` - Delete custom stage

### Frontend Impact
- **FE-006**: Flow editor requires mock service until routes added

---

## 4. Story Knowledge Service (Characters, World Bible, Arcs)

**Service**: `app/services/story_knowledge.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)

### Available Methods
```python
# Character Profiles
def upsert_character_profile(
    project_id: str,
    character_id: str,
    name: str,
    description: str | None = None,
    goals: list[str] | None = None,
    flaws: list[str] | None = None
) -> CharacterProfile

def get_character_profile(project_id: str, character_id: str) -> CharacterProfile

def list_character_profiles(project_id: str) -> tuple[CharacterProfile, ...]

# Relationships
def upsert_relationship_edge(
    project_id: str,
    source_character_id: str,
    target_character_id: str,
    relationship_type: str,
    description: str | None = None
) -> RelationshipEdge

# World Bible
def upsert_world_bible_entry(
    project_id: str,
    entry_type: str,  # "location", "object", "rule", "event", "concept"
    title: str,
    content: str,
    source_refs: list[dict] | None = None
) -> WorldBibleEntry

def get_world_bible_entry(
    project_id: str, *, entry_type: str, title: str
) -> WorldBibleEntry

def list_world_bible_entries(project_id: str) -> tuple[WorldBibleEntry, ...]

# Arc Comparisons & Selections
def list_arc_comparisons(
    project_id: str
) -> tuple[tuple[ArcCandidateComparison, ...], ...]

def list_arc_selections(project_id: str) -> tuple[ArcSelection, ...]

def get_arc_stage_map(
    project_id: str, *, arc_id: str
) -> ArcStageMap | None

def update_arc_stage_map(
    project_id: str,
    arc_id: str,
    stage_mappings: dict[str, str]
) -> ArcStageMap
```

### Missing API Routes
- `GET /story-development/characters?project_id={id}` - List characters
- `POST /story-development/characters` - Create/update character
- `GET /story-development/characters/{character_id}?project_id={id}` - Get character
- `DELETE /story-development/characters/{character_id}?project_id={id}` - Delete character
- `POST /story-development/relationships` - Create relationship edge
- `GET /story-development/world-bible?project_id={id}` - List bible entries
- `POST /story-development/world-bible` - Create/update entry
- `GET /story-development/world-bible/{entry_type}/{title}?project_id={id}` - Get entry
- `GET /story-development/arcs/comparisons?project_id={id}` - List arc comparisons
- `GET /story-development/arcs/selections?project_id={id}` - List selections
- `POST /story-development/arcs/stage-map` - Update stage mapping

### Frontend Impact
- **FE-031**: Character builder requires mock service until routes added
- **FE-032**: World bible workspace requires mock service until routes added

---

## 5. Drafting Service (Write Operations)

**Service**: `app/services/drafting.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)  
**Status**: GET endpoints exist, POST/PUT missing

### Available Write Methods
```python
def create_alternate_variant(
    project_id: str,
    source_document_id: str,
    variant_notes: str | None = None
) -> ManuscriptDocument

def create_revision_suggestion(
    project_id: str,
    target_kind: StoryObjectType,  # "manuscript", "scene_plan", etc.
    target_id: str,
    anchor_text: str,
    proposed_revision: str,
    suggestion_notes: str | None = None
) -> RevisionSuggestion
```

### Existing GET Routes (Working)
- ✅ `GET /story-development/drafting/manuscript-documents?project_id={id}`
- ✅ `GET /story-development/drafting/manuscript-documents/{document_id}?project_id={id}`
- ✅ `GET /story-development/drafting/revision-suggestions?project_id={id}`
- ✅ `GET /story-development/drafting/revision-suggestions/{suggestion_id}?project_id={id}`

### Missing POST Routes
- `POST /story-development/drafting/manuscript-documents` - Create manuscript document
- `POST /story-development/drafting/manuscript-documents/{document_id}/variants` - Create variant
- `POST /story-development/drafting/revision-suggestions` - Create suggestion

### Frontend Impact
- **FE-013**: Draft artifact promotion requires mock until POST available
- **FE-025**: Manuscript aids panel requires mock until POST available
- **FE-028**: Suggestion history requires mock until POST available

---

## 6. Review Routing Service (Write Operations)

**Service**: `app/services/review_routing.py`  
**Repository**: `StoryDevelopmentRepository` (persistence ready)  
**Status**: GET endpoints exist, POST/PUT missing

### Available Write Methods
```python
def record_review_decision(
    project_id: str,
    finding_id: str,
    decision_action: str,  # "accept", "reject", "defer", "escalate", "refine"
    routing_target_kind: StoryObjectType | None = None,
    routing_target_id: str | None = None,
    operator_notes: str | None = None
) -> ReviewDecision

def create_inspect_link(
    project_id: str,
    finding_id: str,
    run_id: str,
    run_kind: str  # "job", "checker"
) -> InspectRunLink
```

### Existing GET Routes (Working)
- ✅ `GET /story-development/review/findings?project_id={id}`
- ✅ `GET /story-development/review/findings/{finding_id}?project_id={id}`
- ✅ `GET /story-development/review/decisions?project_id={id}`
- ✅ `GET /story-development/review/decisions/{decision_id}?project_id={id}`
- ✅ `GET /story-development/review/inspect-links?project_id={id}`
- ✅ `GET /story-development/review/inspect-links/{link_id}?project_id={id}`

### Missing POST Routes
- `POST /story-development/review/decisions` - Record review decision
- `POST /story-development/review/inspect-links` - Create inspect link

### Frontend Impact
- **FE-023**: Review decision interface requires mock until POST available

---

## Implementation Priority

Based on frontend task dependencies:

| Priority | Feature | Reason |
|----------|---------|--------|
| **P1** | Drafting POST endpoints | Blocks FE-013, FE-025, FE-028 (manuscript workflow) |
| **P1** | Review decisions POST | Blocks FE-023 (review workflow completion) |
| **P2** | Brainstorm endpoints | Blocks FE-029 (story development capture) |
| **P2** | Foundation endpoints | Blocks FE-030 (project setup) |
| **P3** | Story knowledge endpoints | Blocks FE-031, FE-032 (characters/world bible) |
| **P4** | Flow editor endpoints | Blocks FE-006 (advanced workflow customization) |

---

## Notes

1. **All services have persistence**: The `StoryDevelopmentRepository` in `app/persistence/story_development.py` has all CRUD operations implemented for these features.

2. **No new backend work needed**: Only API route wiring required - service logic is complete and tested.

3. **Mock services recommended**: Frontend can proceed with mock implementations (see `TODO.md` Phase 9-10) while backend routes are added.

4. **Testing coverage**: Service-level tests exist in `tests/test_*_service.py` files for all features listed above.

---

## Related Documentation

- [Frontend API Alignment Issues](./Frontend API Alignment Issues.md) - Complete endpoint inventory
- [TODO.md](../TODO.md) - Frontend task specifications with mock service contracts
- [Frontend Design SRS v0.5](./Frontend Design SRS v0.5.md) - UI requirements and implementation order
