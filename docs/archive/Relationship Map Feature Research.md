# Relationship Map Feature Research

## Architecture Overview

### Graph Visualization
- **Component**: `frontend/src/components/characters/RelationshipMapGraph.tsx` (510 lines)
- **Render engine**: Pure SVG (NOT Cytoscape.js). Custom layout + Bezier curves.
- **Layout**: Circular arrangement sorted by connection count, trigonometric positioning.
- **Edges**: Quadratic Bezier curves (`Q` path), perpendicular control points for curvature.
- **Styling**: `RELATION_KIND_STYLES` map (30+ kinds → colors + Lucide icons). Fallback substring matching for unknown kinds.
- **Node radius**: 28px, stroke 2px. Edge width: 1.5px normal, 2.5px hover.
- **Sub-graph filtering**: Only characters with ≥1 relationship are rendered. Amber banner warns if subset.

### Props Interface
```typescript
interface RelationshipMapGraphProps {
  characters: CharacterProfile[];
  relationships: RelationshipEdge[];
  projectId?: string;
  onDeleteRelationship?: (edgeId: string) => void;
  className?: string;
}
```

### Character "Opening" Mechanism
- **NOT a modal or route navigation** — in-place mode switching within PlanningView.
- `CharacterEditorMode = 'list' | 'create' | 'edit'`
- Clicking a character card → sets `selectedCharacterId` + switches to `'edit'` mode → renders `<CharacterBuilder>` with pre-populated data.
- CharacterBuilder: full-page form, all character fields, uses `useEffect` to sync state on prop change.

### Relationship CRUD Operations

#### Frontend Hook (`frontend/src/hooks/useRelationships.ts`)
| Operation | Function | Backend Endpoint | Status |
|-----------|----------|-----------------|--------|
| Create | `createRelationship(data)` | POST `/v1/story-development/relationships` | 201, wired |
| Update | `updateRelationship(edgeId, data)` | PATCH `/v1/story-development/relationships/{edge_id}` | 200, **NOT wired** |
| Delete | `deleteRelationship(edgeId)` | DELETE `/v1/story-development/relationships/{edge_id}` | 200, wired |
| Extract | `extractRelationships(data)` | POST `/v1/story-development/relationships/extract` | 200, wired |

All mutations invalidate `['relationships', projectId]` query key.

#### Backend Schemas (`app/schemas/story_development.py`)
```python
class RelationshipEdge(StrictSchemaModel):
    edge_id: str
    source_character_id: str
    target_character_id: str
    relation_kind: str
    summary: str
    tension: str | None = None
    notes: str | None = None

class RelationshipEdgeUpdateRequest(StrictModel):
    source_character_id: str | None = None
    target_character_id: str | None = None
    relation_kind: str | None = None
    summary: str | None
    tension: str | None
    notes: str | None
```

### Components Hierarchy
```
PlanningView (tab = 'relationships')
  ├── charactersQuery → getCharacters(projectId)
  ├── relationshipsQuery → getRelationships(projectId)
  │
  ├── RelationshipMapGraph (SVG graph)
  │     └── onDeleteRelationship callback prop
  ├── RelationshipList (scrollable cards)
  │     └── onUpdateRelationship prop exists but NOT wired
  └── RelationshipForm (toggled via showCreateRelationship)
        └── Calls relationshipHook.createRelationship(data)
```

### Key Implementation Details

1. **Node rendering** (lines 260-310): Each node is a `<g>` group with circle, icon text, and label. Nodes accept `onDoubleClick` via React event on the `<g>` element.
2. **Edge rendering** (lines 311-440): Edges are `<path>` elements with arrow markers. Edge hover shows tooltip with kind/summary/tension + delete button at control point.
3. **Character names**: `characterNameMap` computed via `useMemo` from characters list, maps `character_id → display_name`.
4. **Tab structure**: Relationships tab header has count badge, "AI Extract" button, and "+ Add" button that toggles RelationshipForm.

### Files to Modify

| File | Purpose |
|------|---------|
| `RelationshipMapGraph.tsx` | Add `onOpenCharacter`, `onEditRelationship` callbacks; wire double-click handlers |
| `PlanningView.tsx` | Wire new callbacks; add relationship edit mode; connect `updateRelationship` hook |
| `RelationshipList.tsx` | Wire `onUpdateRelationship` prop; add "Edit" button to each card |
| `useRelationships.ts` | Already has `updateRelationship` — no changes needed |
| `relationships.ts` (service) | Already has `updateRelationship` — no changes needed |

### Design Decisions for Implementation

1. **Double-click character → switch to characters tab + open edit mode**: Since character editing already exists as in-place mode switching, double-click should navigate the PlanningView to the characters tab with the selected character in edit mode. This avoids duplicating the CharacterBuilder form.

2. **Double-click relationship → inline modal editor**: Use a centered modal overlay on the graph (not a full-page form swap) for editing an existing relationship. Reuse RelationshipForm fields pre-populated with edge data, calling `updateRelationship` on save.

3. **Edit button on relationship cards**: Add a pencil icon button to each card in RelationshipList that triggers the same edit modal.

4. **Edit button on graph edges**: Small edit icon near the delete button on edge hover, for direct graph interaction.

