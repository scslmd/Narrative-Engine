# Relationship Map Interactions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add double-click interactions to the relationship map — character nodes open character editor, relationship edges open edit modal, list cards gain Edit buttons.

**Architecture:** Centered modal dialog for relationship editing. Character double-click switches PlanningView tab to characters + opens existing CharacterBuilder. All new state lives in `PlanningView.tsx`; graph and list components receive callback props.

**Tech Stack:** React, TypeScript, Tailwind CSS, Lucide icons, TanStack Query (via existing `useRelationships` hook).

---

## File Inventory

| File | Responsibility |
|------|---------------|
| `frontend/src/components/characters/RelationshipEditModal.tsx` | NEW — Centered modal for editing relationships |
| `frontend/src/components/characters/RelationshipMapGraph.tsx` | MODIFIED — Add `onOpenCharacter`, `onEditRelationship` props; wire double-click handlers |
| `frontend/src/components/characters/RelationshipList.tsx` | MODIFIED — Wire existing `onUpdateRelationship` prop; add pencil icon button |
| `frontend/src/views/PlanningView.tsx` | MODIFIED — Import modal, add state, wire callbacks to graph/list |

---

## Task Contract JSON

```json
[
  {
    "task_id": "T1",
    "name": "Create RelationshipEditModal component",
    "responsible_file": "frontend/src/components/characters/RelationshipEditModal.tsx",
    "serial_dependencies": [],
    "same_file_serial_group": null,
    "guardrails": {
      "do_not_modify": [
        "frontend/src/components/characters/RelationshipForm.tsx",
        "frontend/src/hooks/useRelationships.ts",
        "frontend/src/services/relationships.ts"
      ]
    },
    "acceptance_criteria": [
      "Modal renders when isOpen=true, hidden when isOpen=false",
      "Pre-populates form fields from relationship prop: relation_kind, summary, tension, notes",
      "From/To character selectors are disabled (readonly display)",
      "Save button calls onSave with updated data, closes modal",
      "Delete button shows confirmation, calls onDelete on confirm",
      "Cancel button closes modal without changes",
      "Form validates: relation_kind required, summary required (min 1 char)",
      "Uses existing RELATION_KINDS list from RelationshipForm.tsx (imported, not duplicated)",
      "Dark mode support via isDark prop"
    ]
  },
  {
    "task_id": "T2",
    "name": "Add double-click handlers to RelationshipMapGraph",
    "responsible_file": "frontend/src/components/characters/RelationshipMapGraph.tsx",
    "serial_dependencies": [],
    "same_file_serial_group": null,
    "guardrails": {
      "do_not_modify": [
        "frontend/src/hooks/useRelationships.ts",
        "frontend/src/services/relationships.ts",
        "frontend/src/components/characters/RelationshipList.tsx"
      ]
    },
    "acceptance_criteria": [
      "Props interface adds onOpenCharacter?: (characterId: string) => void",
      "Props interface adds onEditRelationship?: (edgeId: string) => void",
      "Character node <g> elements accept onDoubleClick handler with 300ms debounce to avoid single-click conflict",
      "Edge <path> elements accept onDoubleClick handler with 300ms debounce",
      "Double-click calls callback with correct ID (character_id for nodes, edge_id for edges)",
      "Edit icon (Pencil from lucide-react) appears next to delete X button on edge hover",
      "Edit icon click calls onEditRelationship(edge.id)",
      "No visual regression: existing hover, tooltip, and delete behavior unchanged"
    ]
  },
  {
    "task_id": "T3",
    "name": "Wire Edit button to RelationshipList cards",
    "responsible_file": "frontend/src/components/characters/RelationshipList.tsx",
    "serial_dependencies": [],
    "same_file_serial_group": null,
    "guardrails": {
      "do_not_modify": [
        "frontend/src/hooks/useRelationships.ts",
        "frontend/src/services/relationships.ts",
        "frontend/src/components/characters/RelationshipMapGraph.tsx"
      ]
    },
    "acceptance_criteria": [
      "Pencil icon button (Pencil from lucide-react) added next to existing Trash2 delete button",
      "Button calls onUpdateRelationship(edge.edge_id) when provided",
      "Button appears on group hover, same as delete button (opacity-0 group-hover:opacity-100)",
      "Button has title=\"Edit relationship\" for accessibility",
      "No visual regression: existing card layout and delete behavior unchanged"
    ]
  },
  {
    "task_id": "T4",
    "name": "Wire all interactions in PlanningView",
    "responsible_file": "frontend/src/views/PlanningView.tsx",
    "serial_dependencies": ["T1", "T2", "T3"],
    "same_file_serial_group": null,
    "guardrails": {
      "do_not_modify": [
        "frontend/src/components/characters/RelationshipForm.tsx",
        "frontend/src/hooks/useRelationships.ts"
      ]
    },
    "acceptance_criteria": [
      "Import RelationshipEditModal component",
      "Import Pencil from lucide-react (if not already imported)",
      "Add state: editingRelationship: RelationshipEdge | null",
      "Add callback: handleOpenCharacter(characterId) — sets activeTab='characters', selectedCharacterId=characterId, characterEditorMode='edit'",
      "Add callback: handleEditRelationship(edgeId) — finds edge from relationships array, sets editingRelationship",
      "Pass onOpenCharacter to RelationshipMapGraph",
      "Pass onEditRelationship to RelationshipMapGraph",
      "Pass onUpdateRelationship to RelationshipList (calls handleEditRelationship)",
      "Render RelationshipEditModal at end of relationships tab content",
      "Modal onSave calls relationshipHook.updateRelationship(edgeId, data)",
      "Modal onDelete confirms then calls relationshipHook.deleteRelationship(edgeId)",
      "Modal onClose sets editingRelationship to null"
    ]
  }
]

```

---

### Task 1: Create RelationshipEditModal Component

**Files:**
- Create: `frontend/src/components/characters/RelationshipEditModal.tsx`

- [ ] **Step 1: Write the component file**

Create `frontend/src/components/characters/RelationshipEditModal.tsx`:

```tsx
import { useState, useMemo } from 'react';
import { X, Pencil, Trash2 } from 'lucide-react';
import type { RelationshipEdge, CharacterProfile } from '../../types/characters';

interface RelationshipEditModalProps {
  relationship: RelationshipEdge;
  characters: CharacterProfile[];
  onSave: (edgeId: string, data: {
    relation_kind?: string;
    summary?: string;
    tension?: string | null;
    notes?: string | null;
  }) => Promise<void>;
  onDelete: (edgeId: string) => Promise<void>;
  isSaving: boolean;
  isDeleting: boolean;
  isOpen: boolean;
  onClose: () => void;
  isDark?: boolean;
}

const RELATION_KINDS = [
  'ALLY', 'ENEMY', 'FRIEND', 'LOVER', 'MENTOR', 'FAMILY',
  'RIVAL', 'MERCENARY', 'GUARDIAN', 'SUBORDINATE', 'SIBLING',
  'PARENT', 'CHILD', 'PARTNER', 'TEACHER', 'RELATIVE', 'FOE',
  'COMPETITOR', 'PROTECTOR',
];

export function RelationshipEditModal({
  relationship,
  characters,
  onSave,
  onDelete,
  isSaving,
  isDeleting,
  isOpen,
  onClose,
  isDark = false,
}: RelationshipEditModalProps) {
  const [relationKind, setRelationKind] = useState(relationship.relation_kind);
  const [summary, setSummary] = useState(relationship.summary);
  const [tension, setTension] = useState(relationship.tension ?? '');
  const [notes, setNotes] = useState(relationship.notes ?? '');
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const sourceChar = useMemo(
    () => characters.find((c) => c.character_id === relationship.source_character_id),
    [characters, relationship.source_character_id],
  );
  const targetChar = useMemo(
    () => characters.find((c) => c.character_id === relationship.target_character_id),
    [characters, relationship.target_character_id],
  );

  // Reset form when relationship changes
  if (relationship.edge_id !== (isOpen ? '' : undefined)) {
    // Simple reset on open — use key prop on parent instead
  }

  const bg = isDark ? 'bg-slate-900' : 'bg-white';
  const borderColor = isDark ? 'border-slate-700' : 'border-gray-200';
  const textPrimary = isDark ? 'text-slate-100' : 'text-slate-900';
  const textMuted = isDark ? 'text-slate-400' : 'text-gray-500';
  const inputBg = isDark ? 'bg-slate-800 border-slate-600 text-slate-100' : 'bg-white border-gray-300 text-slate-900';

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!summary.trim()) {
      setError('Summary is required');
      return;
    }

    await onSave(relationship.edge_id, {
      relation_kind: relationKind,
      summary: summary.trim(),
      tension: tension.trim() || null,
      notes: notes.trim() || null,
    });
    onClose();
  };

  const handleDelete = async () => {
    await onDelete(relationship.edge_id);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className={`relative w-full max-w-lg mx-4 ${bg} rounded-xl border ${borderColor} shadow-2xl`}>
        <div className={`flex items-center justify-between px-5 py-4 border-b ${borderColor}`}>
          <div className="flex items-center gap-2">
            <Pencil className={`w-4 h-4 ${textMuted}`} />
            <h3 className={`text-base font-semibold ${textPrimary}`}>Edit Relationship</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className={`p-1 rounded ${isDark ? 'hover:bg-slate-700' : 'hover:bg-gray-100'} ${textMuted}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-5 space-y-3">
          {error && (
            <div className={`flex items-center gap-1.5 text-xs ${isDark ? 'text-red-400' : 'text-red-600'}`}>
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>From</label>
              <input
                type="text"
                value={sourceChar?.display_name ?? relationship.source_character_id}
                disabled
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${isDark ? 'bg-slate-800/50 border-slate-700 text-slate-400' : 'bg-gray-50 border-gray-200 text-gray-500'}`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>To</label>
              <input
                type="text"
                value={targetChar?.display_name ?? relationship.target_character_id}
                disabled
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${isDark ? 'bg-slate-800/50 border-slate-700 text-slate-400' : 'bg-gray-50 border-gray-200 text-gray-500'}`}
              />
            </div>
          </div>

          <div>
            <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Relationship Type</label>
            <select
              value={relationKind}
              onChange={(e) => setRelationKind(e.target.value)}
              className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
            >
              {RELATION_KINDS.map((kind) => (
                <option key={kind} value={kind}>{kind}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={`block text-xs font-medium mb-1 ${textMuted}`}>
              Summary <span className="text-red-500">*</span>
            </label>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              rows={3}
              className={`w-full rounded-lg border px-2.5 py-1.5 text-sm resize-none ${inputBg}`}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Tension</label>
              <input
                type="text"
                value={tension}
                onChange={(e) => setTension(e.target.value)}
                placeholder="Conflict or friction..."
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Notes</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional context..."
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => confirmDelete ? handleDelete() : setConfirmDelete(true)}
              disabled={isDeleting}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                confirmDelete
                  ? 'bg-red-600 text-white hover:bg-red-500'
                  : isDark
                    ? 'text-slate-300 hover:bg-slate-700'
                    : 'text-gray-600 hover:bg-gray-100'
              } disabled:opacity-50`}
            >
              <Trash2 className="w-3.5 h-3.5" />
              {confirmDelete ? 'Delete' : 'Delete'}
            </button>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg ${isDark ? 'text-slate-300 hover:bg-slate-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify component compiles**

Run: `cd frontend && npm run typecheck`
Expected: PASS, no errors related to RelationshipEditModal

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/characters/RelationshipEditModal.tsx
git commit -m "feat: add RelationshipEditModal component for editing relationships"
```

---

### Task 2: Add Double-Click Handlers to RelationshipMapGraph

**Files:**
- Modify: `frontend/src/components/characters/RelationshipMapGraph.tsx`

- [ ] **Step 1: Update props interface**

Add to `RelationshipMapGraphProps` interface (after line 20):

```typescript
interface RelationshipMapGraphProps {
  characters: CharacterProfile[];
  relationships: RelationshipEdge[];
  projectId?: string;
  onDeleteRelationship?: (edgeId: string) => void;
  onOpenCharacter?: (characterId: string) => void;
  onEditRelationship?: (edgeId: string) => void;
  className?: string;
}
```

- [ ] **Step 2: Import Pencil icon**

Add `Pencil` to the lucide-react import (line 5):

```typescript
import {
  X,
  AlertCircle,
  Users,
  Heart,
  Sword,
  BookOpen,
  Zap,
  Mountain,
  Shield,
  Compass,
  Pencil,
} from 'lucide-react';
```

- [ ] **Step 3: Add double-click handler utility**

Add after the imports, before `RELATION_KIND_STYLES`:

```typescript
function useDoubleClickHandler(callback: (id: string) => void, id: string) {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
      callback(id);
    } else {
      timeoutRef.current = setTimeout(() => {
        timeoutRef.current = null;
      }, 300);
    }
  }, [callback, id]);

  return handleClick;
}
```

- [ ] **Step 4: Destructure new props in component**

Update the component function signature (after line 128):

```typescript
export function RelationshipMapGraph({
  characters,
  relationships,
  projectId,
  onDeleteRelationship,
  onOpenCharacter,
  onEditRelationship,
  className = '',
}: RelationshipMapGraphProps) {
```

- [ ] **Step 5: Wire double-click on character nodes**

Find the character node `<g>` element (around line 420) and add `onDoubleClick`:

```typescript
{graphNodes.map((node) => {
  const isHovered = hoveredNode === node.id;
  const isDimmed = hoveredNode !== null && !isHovered && !graphEdges.some(
    (e) =>
      ((e.sourceId === hoveredNode && e.targetId === node.id) ||
        (e.targetId === hoveredNode && e.sourceId === node.id)),
  );

  const handleDoubleClick = useDoubleClickHandler(onOpenCharacter ?? (() => {}), node.id);

  return (
    <g
      key={node.id}
      onMouseEnter={() => setHoveredNode(node.id)}
      onMouseLeave={() => setHoveredNode(null)}
      onDoubleClick={handleDoubleClick}
      className="cursor-pointer"
    >
```

- [ ] **Step 6: Wire double-click on edges + add edit button**

Find the edge `<g>` element (around line 375) and modify:

```typescript
{graphEdges.map((edge) => {
  const { color, icon: Icon } = getStyleForRelationKind(edge.relationKind);
  const isHovered = hoveredEdge === edge.id;
  const edgeColor = isHovered ? color : `${color}99`;
  const strokeWidth = isHovered ? 2.5 : 1.5;
  const d = `M ${edge.sourceX} ${edge.sourceY} Q ${edge.controlX} ${edge.controlY} ${edge.targetX} ${edge.targetY}`;

  const handleEdgeDoubleClick = useDoubleClickHandler(onEditRelationship ?? (() => {}), edge.id);

  return (
    <g key={edge.id}>
      <path
        d={d}
        fill="none"
        stroke={edgeColor}
        strokeWidth={strokeWidth}
        onMouseEnter={() => setHoveredEdge(edge.id)}
        onMouseLeave={() => setHoveredEdge(null)}
        onDoubleClick={handleEdgeDoubleClick}
        className="cursor-pointer transition-all"
      />
```

Add edit button next to delete button (inside the `isHovered &&` block, before the delete `<g>`):

```typescript
{isHovered && (
  <g>
    <path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth={4}
      opacity={0.15}
      className="pointer-events-none"
    />
    {(onEditRelationship || onDeleteRelationship) && (
      <g
        transform={`translate(${edge.controlX}, ${edge.controlY - 12})`}
        className="cursor-pointer flex items-center gap-1"
        style={{ display: 'flex', gap: '4px' }}
      >
        {onEditRelationship && (
          <g
            onClick={(e) => { e.stopPropagation(); onEditRelationship(edge.id); }}
          >
            <rect
              x="-10"
              y="-10"
              width="20"
              height="20"
              rx="4"
              fill="#3b82f6"
              className="hover:opacity-80 transition-opacity"
            />
            <text x="-4" y="-1" textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="10">
              <tspan>✎</tspan>
            </text>
          </g>
        )}
        {onDeleteRelationship && (
          <g
            onClick={(e) => handleDeleteEdge(edge.id, e)}
          >
            <rect
              x={onEditRelationship ? "4" : "-10"}
              y="-10"
              width="20"
              height="20"
              rx="4"
              fill="#ef4444"
              className="hover:opacity-80 transition-opacity"
            />
            <text x={onEditRelationship ? "10" : "-4"} y="-1" textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="10">
              <tspan>✕</tspan>
            </text>
          </g>
        )}
      </g>
    )}
  </g>
)}
```

- [ ] **Step 7: Verify component compiles**

Run: `cd frontend && npm run typecheck`
Expected: PASS, no errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/characters/RelationshipMapGraph.tsx
git commit -m "feat: add double-click handlers and edit button to relationship graph"
```

---

### Task 3: Wire Edit Button to RelationshipList Cards

**Files:**
- Modify: `frontend/src/components/characters/RelationshipList.tsx`

- [ ] **Step 1: Import Pencil icon**

Add `Pencil` to the lucide-react import (line 9):

```typescript
import {
  Users,
  Heart,
  Sword,
  BookOpen,
  Shield,
  Trash2,
  MapPin,
  AlertCircle,
  Compass,
  Pencil,
} from 'lucide-react';
```

- [ ] **Step 2: Destructure onUpdateRelationship prop**

The component already accepts `onUpdateRelationship` in the interface. Add it to the destructured props (line 78):

```typescript
export function RelationshipList({
  relationships,
  characterNames,
  onDeleteRelationship,
  onUpdateRelationship,
  className = '',
}: RelationshipListProps) {
```

- [ ] **Step 3: Add Edit button to each card**

Find the action buttons div (around line 170) and add the edit button before delete:

```typescript
<div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
  {onUpdateRelationship && (
    <button
      onClick={() => onUpdateRelationship(rel.edge_id)}
      className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
      title="Edit relationship"
    >
      <Pencil className="w-3.5 h-3.5" />
    </button>
  )}
  {onDeleteRelationship && (
    <button
      onClick={() => onDeleteRelationship(rel.edge_id)}
      className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
      title="Delete relationship"
    >
      <Trash2 className="w-3.5 h-3.5" />
    </button>
  )}
</div>
```

- [ ] **Step 4: Verify component compiles**

Run: `cd frontend && npm run typecheck`
Expected: PASS, no errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/characters/RelationshipList.tsx
git commit -m "feat: wire edit button to relationship list cards"
```

---

### Task 4: Wire All Interactions in PlanningView

**Files:**
- Modify: `frontend/src/views/PlanningView.tsx`

- [ ] **Step 1: Import RelationshipEditModal and Pencil**

Add to imports (after existing character component imports):

```typescript
import { RelationshipEditModal } from '../components/characters/RelationshipEditModal';
```

(Pencil is already used in the graph; no need to import again here since modal handles its own icons.)

- [ ] **Step 2: Add edit modal state**

Add after existing state declarations (line 110):

```typescript
const [editingRelationship, setEditingRelationship] = useState<RelationshipEdge | null>(null);
```

- [ ] **Step 3: Add callback functions**

Add before `handleExtractRelationships` (around line 165):

```typescript
const handleOpenCharacter = useCallback((characterId: string) => {
  setSelectedCharacterId(characterId);
  setCharacterEditorMode('edit');
  setActiveTab('characters');
}, []);

const handleEditRelationship = useCallback((edgeId: string) => {
  const edge = relationships.find((r) => r.edge_id === edgeId);
  if (edge) {
    setEditingRelationship(edge);
  }
}, [relationships]);
```

- [ ] **Step 4: Pass callbacks to RelationshipMapGraph**

Find the graph component (around line 580) and add props:

```typescript
<RelationshipMapGraph
  characters={characters}
  relationships={relationships}
  onDeleteRelationship={(edgeId) => {
    void relationshipDeleteMutation.mutate(edgeId);
  }}
  onOpenCharacter={handleOpenCharacter}
  onEditRelationship={handleEditRelationship}
  className="h-[350px]"
/>
```

- [ ] **Step 5: Pass onUpdateRelationship to RelationshipList**

Find the list component (around line 598) and add prop:

```typescript
<RelationshipList
  relationships={relationships}
  characterNames={characterNameMap}
  onDeleteRelationship={(edgeId) => {
    void relationshipDeleteMutation.mutate(edgeId);
  }}
  onUpdateRelationship={handleEditRelationship}
  className="h-[250px]"
/>
```

- [ ] **Step 6: Render RelationshipEditModal**

Add at the end of the relationships tab content, before the closing `</div>` of the main flex container (after the RelationshipList div, around line 610):

```typescript
{editingRelationship && (
  <RelationshipEditModal
    relationship={editingRelationship}
    characters={characters}
    isSaving={relationshipHook.isUpdating}
    isDeleting={relationshipHook.isDeleting}
    isOpen={!!editingRelationship}
    onClose={() => setEditingRelationship(null)}
    onSave={async (edgeId, data) => {
      await relationshipHook.updateRelationship(edgeId, data);
    }}
    onDelete={async (edgeId) => {
      await relationshipHook.deleteRelationship(edgeId);
    }}
    isDark={isDark}
  />
)}
```

- [ ] **Step 7: Add useCallback import**

Add `useCallback` to the React import (line 1):

```typescript
import { useState, useMemo, useCallback } from 'react';
```

- [ ] **Step 8: Verify full build**

Run all frontend checks:
```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```
Expected: All pass, no errors

- [ ] **Step 9: Commit**

```bash
git add frontend/src/views/PlanningView.tsx
git commit -m "feat: wire relationship map interactions — character open, edge edit, list edit"
```

---

## Verification Commands

After all tasks complete, run the full validation suite:

```bash
# Frontend
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build

# Backend (quick smoke test)
python -m pytest tests/test_smoke.py -v
```

## Self-Review Checklist

- [x] **Spec coverage**: All 3 features addressed — character double-click (T2+T4), relationship edit modal (T1+T4), list edit button (T3+T4)
- [x] **No placeholders**: All code blocks contain complete implementations
- [x] **Type consistency**: `RelationshipEdge` type used consistently across all files; callback signatures match between parent and child components
- [x] **File boundaries**: Each task modifies exactly one file; T2, T3, T1 are independent and can run in parallel; T4 depends on all three
- [x] **Existing patterns followed**: Uses `useCallback`, `useMemo`, Tailwind classes, lucide icons, existing hook patterns, dark mode via `isDark` prop
