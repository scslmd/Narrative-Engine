# Frontend-Backend Integration Audit & Implementation Tasks

> Audit Date: 2026-04-23
> Branch: integration-audit-fixes
> Status: 98% Complete — 1 HIGH finding (partial), 47 dead service functions

---

## Audit Summary

### Validation Baseline
- `pytest -q -p no:cacheprovider`: 802 passed, 9 skipped (0 pre-existing failures)
- `npm run lint`: passed
- `npm run typecheck`: passed
- `npm run build`: passed

### Code Quality Metrics
| Metric | Result |
|--------|--------|
| `TODO:` / `FIXME:` in non-test code | 0 |
| `console.log` statements | 0 |
| `@ts-ignore` / `@ts-expect-error` | 0 |
| `as any` casts | 0 |
| Mock/hardcoded data in service layer | 0 |
| Components making inline API calls | 0 (all go through service layer) |
| Dead service exports | 47 of 112 (42%) |

### Feature Coverage Matrix
| Feature | Backend | Frontend | Linked |
|---------|---------|----------|--------|
| Planning (seq/chap/scene/beat) | 24 endpoints | PlanningTab + inline edit | YES |
| Flow Stages | 6 endpoints | FlowEditor | YES |
| Arcs | 9 endpoints | ArcsTab + visualizations | YES |
| Branching | 13 endpoints | BranchList + Comparison | YES |
| Decisions | 4 endpoints | DecisionTree | YES |
| Characters | 9 endpoints | CharacterBuilder + Graph | YES |
| World Bible | 4 endpoints | WorldBibleWorkspace | YES |
| Foundation | 5 endpoints | FoundationEditor | YES |
| Drafting | 14 endpoints | WritingView + Editor | YES |
| Manuscript Review | 1 endpoint | WritingView integration | YES |
| Review | 7 endpoints | ReviewView | YES |
| Brainstorm | 5 endpoints | BrainstormWorkspace | YES |
| Brain Dump | 6 endpoints | BrainDumpView | YES |
| Story Import | 1 endpoint | Service done, UI pending | PARTIAL |

---

## Findings

### HIGH: Story Import Missing UI (PARTIALLY FIXED)
- Backend: `POST /projects/import-story` in `app/api/projects.py:68`
- Service: `StoryImportService` in `app/services/story_import.py`
- Frontend service: `frontend/src/services/storyImport.ts` (created — calls `POST /projects/import-story`)
- Frontend types: `frontend/src/types/storyImport.ts` (created)
- Frontend UI: No component, no modal, no route integration yet
- Impact: Users cannot trigger story import from the UI

### MEDIUM: 47 Dead Service Functions (42% of all exports)
Functions that correctly call backend APIs but are never imported by any component:

| File | Dead Functions | Type |
|------|---------------|------|
| `brainstorm.ts` | `promoteBrainstormItem`, `getBrainstormPromotions`, `getPromotionsForItem`, `isItemPromoted` | 4 |
| `worldBible.ts` | `getWorldBibleEntriesByType`, `getWorldBibleEntry`, `groupEntriesByType`, `getEntriesForCharacter`, `hasContinuityWarnings`, `getEntriesWithWarnings`, `getUniqueEntryTypes` | 7 |
| `characters.ts` | `getCharacter`, `getCharacterRelationships`, `createRelationship`, `getRelationshipsForCharacter`, `getOutgoingRelationships`, `getIncomingRelationships`, `getRelatedCharacter`, `hasRelationship` | 8 |
| `relationships.ts` | `getCharacterRelationships`, `createRelationship`, `updateRelationship`, `getRelationshipsForCharacter`, `getOutgoingRelationships`, `getIncomingRelationships`, `getRelatedCharacter`, `hasRelationship` | 8 |
| `arcs.ts` | `createArcComparison`, `updateArcSelection` | 2 |
| `foundation.ts` | `getFoundationRevisions`, `getFoundationReviewCues` | 2 |
| `branches.ts` | `createBranch` | 1 |
| `drafting.ts` | `createManuscriptDocument` | 1 |
| `flow.ts` | `updateStage` (throws error), `reorderStages`, `disableStage` | 3 |
| `checker.ts` | `AttemptHistoryItem`, `RoleModelCheckAttemptHistoryResponse` | 2 interfaces |
| `jobs.ts` | `retryJob`, `AttemptHistoryItem`, `JobAttemptHistoryResponse` | 3 items |
| `inspectLinks.ts` | `getInspectLink` | 1 |
| `review.ts` | `getFindingById` | 1 |
| `decisions.ts` | `getDecision` | 1 |
| `storyImport.ts` | `importStory` (service only, no UI yet) | 1 |

**Duplicates**: `getCharacterRelationships`, `createRelationship`, `getRelationshipsForCharacter`, `getOutgoingRelationships`, `getIncomingRelationships`, `getRelatedCharacter`, `hasRelationship` are defined identically in both `characters.ts` and `relationships.ts` — none used anywhere.

**Duplicate interfaces**: `AttemptHistoryItem` exists in `checker.ts`, `jobs.ts`, and `types/inspect.ts`. Components import from `types/inspect.ts`.

### LOW: Story Import Service Not Yet Wired
`frontend/src/services/storyImport.ts::importStory` exists but no component imports it yet.

---

## Atomic Deterministic Tasks

### T-002: Add Story Import UI (StoryImportModal)
**File**: `frontend/src/components/projects/StoryImportModal.tsx` (new)
**Scope**: Modal with form (project name, story text textarea, genre/tone optional), calls `importStory()` service, shows loading/success/error states
**Dependencies**: T-001 (service types exist)
**Acceptance**: 
- "Import Story" button appears in ProjectList alongside "Create Project"
- Modal opens with form, validates input (min 50 chars for story text)
- Service call fires, loading state shows during import
- Success redirects to `/workspace/:projectId`
- Error shows toast with backend message
- `npm run lint` + `npm run typecheck` pass

### T-003: Remove Dead Exports from brainstorm.ts
**File**: `frontend/src/services/brainstorm.ts`
**Dead**: `promoteBrainstormItem`, `getBrainstormPromotions`, `getPromotionsForItem`, `isItemPromoted`
**Also remove unused types**: `BrainstormPromotion`, `BrainstormItemPromoteRequest`, `BrainstormPromotionListResponse`
**Acceptance**: `npm run typecheck` passes, no other file imports these

### T-004: Remove Dead Exports from worldBible.ts
**File**: `frontend/src/services/worldBible.ts`
**Dead**: `getWorldBibleEntriesByType`, `getWorldBibleEntry`, `groupEntriesByType`, `getEntriesForCharacter`, `hasContinuityWarnings`, `getEntriesWithWarnings`, `getUniqueEntryTypes`
**Also remove unused types**: `WorldBibleEntryType` (if unused elsewhere in file)
**Acceptance**: `npm run typecheck` passes

### T-005: Remove Dead Exports from characters.ts
**File**: `frontend/src/services/characters.ts`
**Dead**: `getCharacter`, `getCharacterRelationships`, `createRelationship`, `getRelationshipsForCharacter`, `getOutgoingRelationships`, `getIncomingRelationships`, `getRelatedCharacter`, `hasRelationship`
**Also remove unused types**: `RelationshipEdge`, `RelationshipEdgeCreateRequest`, `RelationshipEdgeListResponse`
**Acceptance**: `npm run typecheck` passes

### T-006: Remove Dead Exports from relationships.ts
**File**: `frontend/src/services/relationships.ts`
**Dead**: `getCharacterRelationships`, `createRelationship`, `updateRelationship`, `getRelationshipsForCharacter`, `getOutgoingRelationships`, `getIncomingRelationships`, `getRelatedCharacter`, `hasRelationship`
**Also remove unused types**: `RelationshipEdge`, `RelationshipEdgeListResponse`
**Acceptance**: `npm run typecheck` passes

### T-007: Remove Dead Exports from arcs.ts
**File**: `frontend/src/services/arcs.ts`
**Dead**: `createArcComparison`, `updateArcSelection`
**Also remove unused types**: `ArcComparisonRecord`, `ArcComparisonCreateRequest`, `ArcSelectionUpdateRequest`
**Acceptance**: `npm run typecheck` passes

### T-008: Remove Dead Exports from foundation.ts
**File**: `frontend/src/services/foundation.ts`
**Dead**: `getFoundationRevisions`, `getFoundationReviewCues`
**Also remove unused types**: `FoundationRevision`, `FoundationReviewCue`
**Acceptance**: `npm run typecheck` passes

### T-009: Remove Dead Export from branches.ts
**File**: `frontend/src/services/branches.ts`
**Dead**: `createBranch`
**Acceptance**: `npm run typecheck` passes

### T-010: Remove Dead Export from drafting.ts
**File**: `frontend/src/services/drafting.ts`
**Dead**: `createManuscriptDocument`
**Acceptance**: `npm run typecheck` passes

### T-011: Remove Dead Exports from flow.ts
**File**: `frontend/src/services/flow.ts`
**Dead**: `updateStage` (deprecated, throws), `reorderStages`, `disableStage`
**Acceptance**: `npm run typecheck` passes

### T-012: Remove Dead Exports from checker.ts
**File**: `frontend/src/services/checker.ts`
**Dead**: `AttemptHistoryItem` interface, `RoleModelCheckAttemptHistoryResponse` interface
**Acceptance**: `npm run typecheck` passes (components import from `types/inspect.ts`)

### T-013: Remove Dead Exports from jobs.ts
**File**: `frontend/src/services/jobs.ts`
**Dead**: `retryJob` method, `AttemptHistoryItem` interface, `JobAttemptHistoryResponse` interface
**Acceptance**: `npm run typecheck` passes

### T-014: Remove Dead Export from inspectLinks.ts
**File**: `frontend/src/services/inspectLinks.ts`
**Dead**: `getInspectLink`
**Acceptance**: `npm run typecheck` passes

### T-015: Remove Dead Export from review.ts
**File**: `frontend/src/services/review.ts`
**Dead**: `getFindingById`
**Acceptance**: `npm run typecheck` passes

### T-016: Remove Dead Export from decisions.ts
**File**: `frontend/src/services/decisions.ts`
**Dead**: `getDecision`
**Acceptance**: `npm run typecheck` passes

### T-017: Remove Dead Export from storyImport.ts
**File**: `frontend/src/services/storyImport.ts`
**Dead**: `importStory` (only export, UI not yet wired)
**Action**: Keep the file but mark export as `@deprecated` or remove the export and re-add when T-002 UI is complete. Since T-002 will import it, we remove the function here and re-add it via T-002's component integration.
**Acceptance**: File still exists, `npm run typecheck` passes

---

## Execution Order (Parallel Groups)

| Group | Tasks | Dependencies |
|-------|-------|--------------|
| A (parallel) | T-002, T-003, T-004, T-005, T-006, T-007, T-008, T-009, T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-017 | None |

All tasks can execute in parallel since they touch distinct files.

---

## Validation Protocol

After ALL tasks complete:
1. `cd frontend && npm run lint`
2. `cd frontend && npm run typecheck`
3. `cd frontend && npm run build`
4. `python -m pytest -q -p no:cacheprovider`

All four must pass.
