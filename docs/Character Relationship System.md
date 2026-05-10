# Character Relationship System

How character relationships are formed, stored, and managed in the Narrative Engine.

## Data Model

### RelationshipEdge (`app/schemas/story_development.py`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edge_id` | string | auto-generated | Unique ID; defaults to `{source}->{target}:{kind}` |
| `source_character_id` | string | yes | The "from" character |
| `target_character_id` | string | yes | The "to" character |
| `relation_kind` | string | yes | Free-text relationship type (max 100 chars) |
| `summary` | string | yes | Description of the relationship (max 2000 chars) |
| `tension` | string \| null | no | Tension or conflict descriptor (max 1000 chars) |
| `notes` | string \| null | no | Additional notes (max 2000 chars) |

### Database Table (`app/persistence/sqlite.py`, lines 383-397)

```sql
CREATE TABLE IF NOT EXISTS relationship_edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_character_id TEXT NOT NULL,
    target_character_id TEXT NOT NULL,
    relation_kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    tension TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(source_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE,
    FOREIGN KEY(target_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE
);
```

### Character Profile Linkage

The `character_profiles` table has a `relationship_map_json TEXT NOT NULL DEFAULT '[]'` column. When a relationship edge is created, `_append_relationship_edge_to_character_map()` appends the `edge_id` to **both** the source and target character's `relationship_map_json` array. This creates a bidirectional link: fetching a character profile returns their `relationship_edges` populated from this map.

## Backend API Endpoints

All endpoints in `app/api/story_development.py`:

| Method | Route | Status | Description |
|--------|-------|--------|-------------|
| `POST` | `/v1/story-development/relationships` | 201 | Create a new relationship |
| `GET` | `/v1/story-development/relationships?project_id=` | 200 | List all relationships for a project |
| `PATCH` | `/v1/story-development/relationships/{edge_id}?project_id=` | 200 | Update an existing relationship |
| `DELETE` | `/v1/story-development/relationships/{edge_id}?project_id=` | 200 | Delete a relationship |
| `GET` | `/v1/story-development/characters/{character_id}/relationships?project_id=` | 200 | List relationships for a specific character |

### Request Schemas

```python
class RelationshipEdgeCreateRequest(StrictModel):
    edge_id: str | None = None          # optional, auto-generated
    project_id: str                     # required
    source_character_id: str            # required
    target_character_id: str            # required
    relation_kind: str                  # required, max 100 chars
    summary: str                        # required, max 2000 chars
    tension: str | None                 # optional, max 1000 chars
    notes: str | None                   # optional, max 2000 chars

class RelationshipEdgeUpdateRequest(StrictModel):
    source_character_id: str | None = None
    target_character_id: str | None = None
    relation_kind: str | None = None
    summary: str | None = None
    tension: str | None = None
    notes: str | None = None
```

## Backend Service Layer

**Service**: `StoryKnowledgeService` in `app/services/story_knowledge.py`

- `upsert_relationship_edge()` — creates or updates an edge. Auto-generates `edge_id` if omitted.
- `list_all_relationship_edges()` — returns all edges for a project
- `list_relationship_edges_for_character()` — returns edges where character is source OR target
- `delete_relationship_edge()` — removes an edge by ID

**Persistence**: `StoryDevelopmentRepository` in `app/persistence/story_development.py`

- `upsert_relationship_edge()` (line 1481) — `INSERT ... ON CONFLICT(edge_id) DO UPDATE`. Calls `_append_relationship_edge_to_character_map()` to link the edge to both characters.
- `list_relationship_edges()` (line 1554) — queries by project_id
- `list_relationship_edges_for_character()` (line 1568) — queries where character is source OR target
- `delete_relationship_edge()` (line 1582) — deletes from `relationship_edges` table

## How Relationships Are Created Today

Relationships are created through **four paths**:

1. **Frontend UI** — `PlanningView.tsx` "Add Relationship" button opens `RelationshipForm`, which calls `createRelationship()` → POSTs to backend.
2. **AI Extraction** — `POST /v1/story-development/relationships/extract` endpoint analyzes manuscript text via LLM and auto-creates relationship edges between characters based on detected interactions, shared themes, and narrative connections. Frontend "AI Extract" button in the Relationships tab triggers this flow.
3. **Project forking** (`app/services/story_forking.py`, line 107) — when a project is forked, relationship edges are copied to the new project with remapped character IDs and provenance notes appended.
4. **Programmatic access** — tests call `repo.upsert_relationship_edge()` or `service.upsert_relationship_edge()` directly.

## Frontend Layer

### Service (`frontend/src/services/relationships.ts`)

| Function | Method | Endpoint |
|----------|--------|----------|
| `getRelationships(projectId)` | GET | `/v1/story-development/relationships` |
| `createRelationship(data)` | POST | `/v1/story-development/relationships` (201) |
| `deleteRelationship(edgeId, projectId)` | DELETE | `/v1/story-development/relationships/{edge_id}` |
| `updateRelationship(edgeId, data, projectId)` | PATCH | `/v1/story-development/relationships/{edge_id}` |

### Hook (`frontend/src/hooks/useRelationships.ts`)

```typescript
useRelationships(projectId) -> {
  createRelationship(data),
  updateRelationship(edgeId, data),
  deleteRelationship(edgeId),
  isCreating,
  isUpdating,
  isDeleting
}

### Types (`frontend/src/types/characters.ts`)

```typescript
interface RelationshipEdge {
  edge_id: string;
  source_character_id: string;
  target_character_id: string;
  relation_kind: string;
  summary: string;
  tension: string | null;
  notes: string | null;
}
```

## UI Layer

### Entry Point

`PlanningView.tsx` — "Relationships" tab at `/workspace/:projectId/plan`.

When a user selects the **Relationships** tab, they see:

1. **Header bar** — Title + count badge + "AI Extract" button + "Add Relationship" button (disabled if < 2 characters).
2. **Graph visualization** (`RelationshipMapGraph`) — SVG graph showing characters as circular nodes and relationships as colored curved edges with labels. Circular layout sorted by connection count. Supports:
   - Hover for edge details (tooltip with kind, summary, tension)
   - Double-click character node → navigates to Characters tab, opens CharacterBuilder for that character
   - Double-click relationship edge → opens `RelationshipEditModal` centered dialog
   - Hover reveals edit (blue pencil) and delete (red X) buttons at edge midpoint
3. **List view** (`RelationshipList`) — Below the graph, sorted alphabetically by `relation_kind`. Shows source/target names, kind badge (color-coded), summary, tension indicator, notes. Hover reveals edit (pencil) and delete (trash) buttons.

### Creating a Relationship

Clicking "Add Relationship" opens `RelationshipForm` (`components/characters/RelationshipForm.tsx`):

- **From / To** — Two dropdown selectors for characters. Selecting one disables it in the other to prevent self-relations.
- **Relationship Type** — Dropdown of predefined kinds (ALLY, ENEMY, FRIEND, LOVER, MENTOR, FAMILY, RIVAL, etc.).
- **Summary** — Required text field describing the relationship.
- **Tension** — Optional field for conflict/friction descriptor.
- **Notes** — Optional additional context.

Form validates: both characters required, must be different, summary required. On submit, calls `createRelationship()` mutation which POSTs to backend and invalidates the relationships cache. Form auto-closes on success.

### Editing a Relationship

Three interaction paths open the same `RelationshipEditModal` (`components/characters/RelationshipEditModal.tsx`):

1. **Double-click edge in graph** — Opens modal pre-populated with the edge's current data.
2. **Click pencil icon on list card** — Same modal, triggered from the relationship list view.
3. **Hover edit button on graph edge** — Blue pencil icon at edge midpoint, same modal.

The modal form includes:
- From character (disabled, read-only display)
- To character (disabled, read-only display)
- Relationship type (select dropdown, 19 kinds)
- Summary (textarea, required)
- Tension (text input, optional)
- Notes (text input, optional)
- Actions: Cancel, Delete (with confirmation), Save Changes

Save calls `updateRelationship(edgeId, data)` → PATCH endpoint. Delete calls `deleteRelationship(edgeId)` with confirmation dialog. Query cache invalidates on success, refreshing graph and list views.

### Opening Character Profiles from Graph

Double-clicking a character node in the relationship graph triggers `handleOpenCharacter(characterId)`:
- Switches active tab to "Characters"
- Sets `selectedCharacterId` to the clicked character
- Opens existing `CharacterBuilder` in edit mode with pre-populated data

### Relationship Kind Categories

The UI uses fuzzy matching for color-coding. Backend accepts any free-text string:

| Category | Recognized Kinds | Color |
|----------|-----------------|-------|
| Ally | ALLY, ALLIED | Emerald green |
| Enemy | ENEMY, FOE, ENEMIES | Red |
| Romance | LOVER, LOVED, ROMANCE, PARTNER | Pink |
| Friend | FRIEND, FRIENDS | Violet |
| Mentor | MENTOR, MENTORED, TEACHER, MASTER | Amber |
| Family | FAMILY, SIBLING, PARENT, CHILD, RELATIVE | Orange |
| Rivalry | RIVAL, COMPETITOR | Rose |
| Mercenary | MERCENARY | Cyan |
| Guardian | GUARDIAN, PROTECTOR | Teal |
| Hierarchy | SUBORDINATE, SERVANT | Purple |
| World | WORLD | Slate gray |

## Remaining Gaps

1. **Free-text relation_kind** — Backend accepts any string. No server-side validation against recognized types. Could lead to inconsistent data (`"ally"` vs `"ALLY"` vs `"Alliance"`).
2. **No relationship creation during character editing** — The character builder has no section for creating/managing relationships inline.
3. **No drag-and-drop edge creation** — Users must use the form to create relationships; the graph does not support dragging from one node to another to create an edge.

## File Map

| Layer | File | Purpose |
|-------|------|---------|
| Types | `frontend/src/types/characters.ts` | `RelationshipEdge`, `RelationshipEdgeCreateRequest` interfaces |
| Service | `frontend/src/services/relationships.ts` | API calls (get, create, delete, update) |
| Hook | `frontend/src/hooks/useRelationships.ts` | React Query mutations for create/update/delete |
| Components | `frontend/src/components/characters/RelationshipForm.tsx` | Create relationship form |
| Components | `frontend/src/components/characters/RelationshipList.tsx` | List view with color-coded badges |
| Components | `frontend/src/components/characters/RelationshipMapGraph.tsx` | SVG graph visualization |
| Components | `frontend/src/components/characters/RelationshipEditModal.tsx` | Centered edit modal dialog |
| View | `frontend/src/views/PlanningView.tsx` | "Relationships" tab container |
| API | `app/api/story_development.py` (lines 2357-2436) | 5 endpoints: create, list-all, list-by-character, update, delete |
| Schema | `app/api/story_development.py` (lines 716-739) | Request/response models |
| Service | `app/services/story_knowledge.py` | Business logic for relationships |
| Persistence | `app/persistence/story_development.py` (line 1481) | DB operations, character map updates |
| DB Schema | `app/persistence/sqlite.py` (lines 383-397) | `relationship_edges` table definition |

## User Flows

### Browse and Explore
```
Navigate to /workspace/:projectId/plan
  -> Click "Relationships" tab
    -> See graph visualization of existing relationships
    -> See list view below the graph
      -> Hover over edges for details (kind, summary, tension)
      -> Double-click character node -> jumps to Characters tab, opens profile editor
      -> Double-click edge -> opens edit modal
      -> Hover edge -> reveals edit (pencil) and delete (X) buttons
```

### Create a Relationship
```
  -> Click "Add Relationship" button in header bar
    -> Fill out form: select From/To characters, type, summary, optional tension/notes
    -> Submit -> relationship created and graph/list refresh automatically
```

### Edit a Relationship
```
  -> Double-click edge / click pencil icon on list card / hover edit button on graph
    -> Modal opens with pre-populated data
    -> Modify type, summary, tension, or notes
    -> Save Changes -> PATCH request sent, UI refreshes
    OR
    -> Click Delete -> confirm deletion -> relationship removed from graph and list
```

### AI Relationship Extraction
```
  -> Click "AI Extract" button in header bar
    -> Frontend fetches chapter-1 content from project
    -> Sends manuscript text + character IDs to backend extraction endpoint
    -> LLM analyzes text, extracts relationship edges between characters
    -> New relationships appear in graph and list on success
```

## Research Date

2026-05-10 — Updated with relationship map interactions (double-click, edit modal, list edit buttons) and AI extraction feature. Original: 2026-05-09.
