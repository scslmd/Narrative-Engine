# Unwired API Exposure — Design Spec

> Date: 2026-05-05
> Status: Approved
> Scope: Wire 40 unwired service functions + 35 backend endpoints to frontend UI
> Delivery: Phased A → B → C

---

## Overview

Expose all unwired API endpoints through inline actions in existing views. Build shared `<InlineActions>` component and `useConfirmation` hook once (~70 lines), reuse across all phases. Total effort: ~430 lines new code + 8 component modifications.

---

## Architecture

```
Component → Hook (useApiMutation) → Service Function → Axios Client → Backend Endpoint
     ↓                                      ↓
  React Query (invalidation)          Toast + Error Handling
```

**Reuse existing infrastructure:**
- `useApiMutation` — Mutations with toast notifications + query invalidation
- `useApiQuery` — Queries with toast + error handling
- `Button` — 6 variants (`primary`, `secondary`, `danger`, `ghost`, `outline`, `soft`), 3 sizes
- `Toast` / `toastStore` — Success/error/warning/info notifications
- `ErrorBanner`, `EmptyState`, `LoadingState` — View states
- `api.ts` — Shared Axios client with `ApiError` interceptor
- `errorHandling.ts` — Error classification, status code messaging
- `queryClient.ts` — React Query configuration

**New files:**
| File | Purpose | Lines |
|------|---------|-------|
| `frontend/src/components/ui/InlineActions.tsx` | Reusable action button group | ~40 |
| `frontend/src/hooks/useConfirmation.ts` | Confirm dialog hook for destructive actions | ~30 |

---

## Phase A — Critical Workflow Gaps

**Priority:** Highest. Breaks existing features.

### A1: Manuscript Assist Suggestions

**Endpoints:**
- `POST /v1/manuscript-assist/suggestions/{id}/apply` → `applyLLMSuggestion()`
- `POST /v1/manuscript-assist/suggestions/{id}/archive` → `archiveLLMSuggestion()`

**Changes:**
1. `useManuscriptAssist.ts` — Add `archiveMutation`, expose `archiveSuggestion()`
2. `AidsPanel.tsx` — Add Archive button alongside Accept/Reject
3. `WritingView.tsx` — Wire archive callback to hook

**UI:** Inline buttons in suggestion cards: `[Accept] [Reject] [Archive]`

### A2: Relationship Editing

**Endpoint:**
- `PATCH /v1/story-development/relationships/{edge_id}` → `updateRelationship()`

**Changes:**
1. `useRelationships.ts` — New hook with `updateMutation`
2. `RelationshipMapGraph.tsx` — Add inline action on selected edge: `[Edit] [Delete]`
3. Edit opens inline form for relationship type + strength

**UI:** Context menu on relationship edges in graph view.

### A3: Arc Selection Updates

**Endpoint:**
- `PATCH /v1/story-development/arcs/selections/{selection_id}` → `updateArcSelection()`

**Changes:**
1. `useArcs.ts` — Add `updateSelectionMutation`, expose `updateArcSelection()`
2. `ArcsTab.tsx` — Add status dropdown + update button on selection cards

**UI:** Inline status selector on arc selection cards.

---

## Phase B — Feature Completeness

**Priority:** Medium. Turns list-only views into full CRUD.

### B1: Mythos Library CRUD

**Endpoints:**
- `POST /v1/mythos/entries` → `createMythosEntry()`
- `PATCH /v1/mythos/entries/{id}` → `updateMythosEntry()`
- `DELETE /v1/mythos/entries/{id}` → `deleteMythosEntry()`
- `POST /v1/mythos/materialize-extraction` → `materializeExtraction()`

**Changes:**
1. `useMythosLibrary.ts` — New hook with CRUD mutations
2. `MythosLibraryWorkspace.tsx` — Add "New Entry" button + inline actions on cards
3. `MythosEntryCard.tsx` — Add `[Edit] [Delete]` actions

**UI:** Card grid with inline actions. Edit promotes to modal if entry has >3 fields.

### B2: Pattern Library CRUD

**Endpoints:**
- `POST /v1/patterns/entries` → `createPatternEntry()`
- `PATCH /v1/patterns/entries/{id}` → `updatePatternEntry()`
- `DELETE /v1/patterns/entries/{id}` → `deletePatternEntry()`
- `POST /v1/patterns/materialize-extraction` → `materializeExtraction()`

**Changes:**
1. `usePatternLibrary.ts` — New hook with CRUD mutations
2. `PatternLibraryWorkspace.tsx` — Same pattern as mythos
3. `PatternEntryCard.tsx` — Add `[Edit] [Delete]` actions

**UI:** Identical to mythos library (shared component patterns).

### B3: Foundation History + Review Cues

**Endpoints:**
- `GET /v1/story-development/foundation/revisions?project_id={id}` → `getFoundationRevisions()`
- `GET /v1/story-development/foundation/review-cues?project_id={id}` → `getReviewCues()`

**Changes:**
1. `useFoundation.ts` — Add revisions + review cues queries
2. `FoundationEditor.tsx` — Add "History" tab showing revision list
3. Review cues render as inline badges on editable fields

**UI:** Tabbed view: `[Editor] [History]`. History shows timestamped revision list.

### B4: Brainstorm Promote Workflow

**Endpoints:**
- `POST /v1/story-development/brainstorm/items/promote` → `promoteBrainstormItem()`
- `GET /v1/story-development/brainstorm/promotions?project_id={id}` → `getPromotions()`

**Changes:**
1. `useBrainstorm.ts` — Add promote mutation + promotions query
2. `BrainstormWorkspace.tsx` — Add "Promote" button on items
3. Promoted items show badge; promotions list in separate tab

**UI:** `[Promote to Planning]` button on brainstorm items. Success moves item to promotions tab.

---

## Phase C — Admin Features

**Priority:** Low. Operational UI, hidden from creative workflow.

### C1: Backup Management

**Endpoints:**
- `POST /backup/create` → `createBackup()`
- `GET /backup/list` → `listBackups()`
- `GET /backup/latest` → `getLatestBackup()`
- `POST /backup/restore/{id}` → `restoreBackup()`
- `DELETE /backup/{id}` → `deleteBackup()`

**Changes:**
1. `useBackups.ts` — New hook with CRUD mutations + queries
2. `SettingsPanel.tsx` — Add "Backups" section
3. Table view: `[Created] [Size] [Actions: Restore | Delete]`

**UI:** Settings > Maintenance > Backups. Create button at top. Restore requires confirmation.

### C2: API Key Management

**Endpoints:**
- `POST /auth/keys` → `createApiKey()`
- `GET /auth/keys` → `listApiKeys()`
- `DELETE /auth/keys/{prefix}` → `revokeApiKey()`

**Changes:**
1. `useAuthKeys.ts` — New hook with CRUD mutations + queries
2. `SettingsPanel.tsx` — Add "Security" section
3. Table view: `[Name] [Prefix] [Expires] [Actions: Revoke]`

**UI:** Settings > Security > API Keys. Create opens modal (name + permissions). Revoke requires confirmation.

---

## Shared Infrastructure Design

### `<InlineActions>` Component

```tsx
interface InlineAction {
  label: string;
  variant?: 'primary' | 'ghost' | 'soft' | 'danger';
  onClick?: () => void;
  onConfirm?: () => Promise<void>;  // Triggers confirmation dialog
  danger?: boolean;
  disabled?: boolean;
  isLoading?: boolean;
}

interface InlineActionsProps {
  actions: InlineAction[];
  className?: string;
}

// Renders horizontal button group (flex gap-2).
// Handles loading states (disables button, shows spinner).
// onConfirm triggers useConfirmation dialog before executing.
// Uses existing Button component with consistent variants.
```

### `useConfirmation` Hook

```tsx
interface ConfirmationResult {
  confirm: (message: string, options?: ConfirmOptions) => Promise<boolean>;
  isOpen: boolean;
  dialog: React.ReactNode;  // Render this in component tree
}

interface ConfirmOptions {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

// Returns lightweight confirm dialog component.
// Renders portal-mounted dialog when confirm() is called.
// Resolves Promise on user choice.
```

---

## Testing Strategy

### Unit Tests
- `<InlineActions>` renders correct number of buttons
- Loading state disables button, shows spinner
- Danger variant applies correct styling
- `onConfirm` triggers confirmation dialog before execution

### Integration Tests
- Hook + service wiring with mocked Axios (MSW handlers)
- React Query invalidation on mutation success
- Error toast on failed mutation
- Confirmation dialog prevents accidental deletion

### E2E Tests (Phase A only)
- Apply suggestion → document content updates
- Archive suggestion → suggestion disappears from list
- Delete mythos entry → entry removed from grid, list query invalidated

**Reuses existing test infrastructure:** MSW handlers, `@testing-library/react`, React Query test utils. No new dependencies.

---

## File Manifest

### New Files (6)
1. `frontend/src/components/ui/InlineActions.tsx`
2. `frontend/src/hooks/useConfirmation.ts`
3. `frontend/src/hooks/useRelationships.ts` (Phase A)
4. `frontend/src/hooks/useMythosLibrary.ts` (Phase B)
5. `frontend/src/hooks/usePatternLibrary.ts` (Phase B)
6. `frontend/src/hooks/useBackups.ts`, `useAuthKeys.ts` (Phase C)

### Modified Files (8)
1. `frontend/src/hooks/useManuscriptAssist.ts` — Add archive mutation
2. `frontend/src/components/aids/AidsPanel.tsx` — Add Archive button
3. `frontend/src/views/WritingView.tsx` — Wire archive callback
4. `frontend/src/components/characters/RelationshipMapGraph.tsx` — Add edge actions
5. `frontend/src/components/arcs/ArcsTab.tsx` — Add selection update UI
6. `frontend/src/components/mythos/MythosLibraryWorkspace.tsx` — Add CRUD
7. `frontend/src/components/patterns/PatternLibraryWorkspace.tsx` — Add CRUD
8. `frontend/src/components/SettingsPanel.tsx` — Add Backups + API Keys sections

---

## Success Criteria

- [ ] Phase A: 4 endpoints wired, existing features complete
- [ ] Phase B: 12 endpoints wired, library views support full CRUD
- [ ] Phase C: 8 endpoints wired, admin features accessible from Settings
- [ ] All mutations use `useApiMutation` with toast + invalidation
- [ ] All destructive actions require confirmation
- [ ] Zero `as any`, zero `@ts-ignore`, zero console.log in production code
- [ ] Frontend lint, typecheck, build pass
- [ ] Backend parallel + serial tests pass
