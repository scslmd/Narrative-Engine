# Relationship Map Interactions — Design Spec

## Overview

Add interactive editing to the relationship map in `PlanningView.tsx`. Users can double-click character nodes to open character details, double-click relationship edges to edit them, and use an "Edit" button on relationship list cards.

## Features

### 1. Character Node Double-Click → Switch to Characters Tab + Edit Mode

**Trigger**: Double-click a character node in the relationship graph.

**Behavior**:
- Switches `activeTab` to `'characters'`
- Sets `selectedCharacterId` to the clicked character's ID
- Sets `characterEditorMode` to `'edit'`
- Reuses existing `<CharacterBuilder>` component — no new UI needed

**Rationale**: The CharacterBuilder already exists as the canonical character editing surface. No duplication required. Consistent with current "click card → edit" flow.

### 2. Relationship Edge Double-Click / Edit Button → Centered Modal

**Trigger**: Double-click a relationship edge in the graph, or click "Edit" (pencil icon) on a relationship list card.

**Behavior**:
- Opens a centered modal dialog with backdrop dim
- Pre-populated form with all relationship fields:
  - From character (select, disabled — cannot change endpoints mid-edit)
  - To character (select, disabled — cannot change endpoints mid-edit)
  - Relationship type (select dropdown, 19 kinds)
  - Summary (textarea, required)
  - Tension (text input, optional)
  - Notes (textarea, optional)
- Actions: Cancel, Delete (red), Save Changes (blue)
- On save → calls `updateRelationship(edgeId, data)` hook mutation
- On delete → confirms, then calls `deleteRelationship(edgeId)`
- Closes modal on success, invalidates `['relationships', projectId]` query

**Rationale**: Centered modal is the industry-standard pattern (GitHub, Figma, Notion). Full field visibility, includes Delete in same context. Graph briefly obscured is acceptable — editing doesn't require simultaneous graph navigation.

### 3. Edit Button on Relationship List Cards

**Trigger**: Click pencil icon button on any card in `RelationshipList`.

**Behavior**: Opens the same centered modal as edge double-click, pre-populated with that edge's data.

**Placement**: Pencil icon next to existing trash (delete) icon on each card.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Reuse RelationshipForm fields | Existing form component has all 19 relationship types, proper validation, dark mode support |
| Centered modal over slide-out panel | Simpler implementation, no layout reflow, familiar pattern |
| From/To characters disabled in edit | Changing endpoints would create a new relationship; editing should modify properties of the existing edge |
| Delete button in modal | Reduces one click — user can delete without going back to list |
| `updateRelationship` hook already exists | No backend or hook changes needed; just wire it up in PlanningView |

## Components to Create/Modify

### New: `RelationshipEditModal.tsx`
- Centered overlay modal component
- Props: `relationship: RelationshipEdge`, `characters: CharacterProfile[]`, `onSave`, `onDelete`, `isSaving`, `isDeleting`, `isOpen`, `onClose`
- Reuses field layout from `RelationshipForm.tsx` (type select, summary textarea, tension/notes inputs)
- Includes Delete button with confirmation dialog

### Modified: `RelationshipMapGraph.tsx`
- Add `onOpenCharacter?: (characterId: string) => void` prop
- Add `onEditRelationship?: (edgeId: string) => void` prop
- Wire `onDoubleClick` on character node `<g>` elements → debounced double-click → call `onOpenCharacter`
- Wire `onDoubleClick` on edge `<path>` elements → call `onEditRelationship`
- Add edit icon button next to delete button on edge hover tooltip

### Modified: `RelationshipList.tsx`
- Wire existing `onUpdateRelationship` prop
- Add pencil icon button next to trash icon on each card
- Button calls `onUpdateRelationship(edgeId)` if provided

### Modified: `PlanningView.tsx`
- Import `RelationshipEditModal`
- Add state: `editingRelationship: RelationshipEdge | null`, `showEditModal: boolean`
- Wire `onOpenCharacter` callback to graph → switches tab + opens character edit
- Wire `onEditRelationship` callback from graph and list → sets `editingRelationship` + opens modal
- Connect `relationshipHook.updateRelationship` for save, `relationshipHook.deleteRelationship` for delete
- Query invalidation on success

## Data Flow

```
User double-clicks edge / clicks Edit button
  → PlanningView sets editingRelationship = selected edge
  → RelationshipEditModal opens with pre-populated form
  → User modifies fields, clicks Save
  → Modal calls relationshipHook.updateRelationship(edgeId, updatedData)
  → PATCH /v1/story-development/relationships/{edge_id} (200)
  → Query invalidated, modal closes, graph/list refresh
```

## Error Handling

- Save: Show inline error toast on failure, keep modal open with current values
- Delete: Confirm before delete ("Delete this relationship?"), show toast on failure
- Character navigation: No-op if character ID not found in characters list (defensive guard)

## Testing

- Double-click character node → verifies tab switch + character editor opens
- Double-click edge → modal opens with correct pre-populated data
- Edit and save → PATCH request sent, UI updates without reload
- Delete from modal → relationship removed from graph and list
- Edit button on list card → same modal as edge double-click
- Form validation → summary required, type required
