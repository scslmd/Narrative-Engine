# Frontend Completeness: Shared Primitives + Full CRUD Coverage

> Date: 2026-05-03
> Status: Approved
> Approach: Hybrid (Phase 0 infrastructure, Phases 1-3 vertical slices)
> Testing: TDD for all new code

## Problem Statement

The frontend has complete read/create happy paths for all 17 feature areas but is missing:
- 9 critical backend endpoints with no frontend service function (project delete, draft continue/variant, generation/assist retry, brainstorm promote, storyboard CRUD, relationships update, arcs update)
- Loading/error/empty states in PlanningView, GenerationView, and ReviewView (silent failures)
- 23 detail endpoints without frontend services (list-only UI for branches, characters, drafts, planning items, review findings, world bible entries, foundation revisions)
- Service pattern inconsistency (jobsService and flowService use object export vs. named function exports)

## Architecture: Hybrid Approach

Phase 0 builds shared UX primitives used by all subsequent phases. Phases 1-3 deliver vertical slices pairing feature gaps with UX hardening.

---

## Phase 0: Shared UX Primitives

Five shared components/hooks that standardize loading, error, and empty states across the app.

### A) `useApiQuery` Hook

Wraps React Query with standardized error handling and toast integration.

**File**: `frontend/src/hooks/useApiQuery.ts`

**Interface**:
```typescript
interface UseApiQueryOptions<T> {
  queryKey: string[];
  serviceFn: () => Promise<T>;
  deps?: unknown[];
  onErrorToast?: boolean; // default: true
  onSuccessToast?: string | null; // optional success message
}

interface UseApiQueryReturn<T> {
  data: T | undefined;
  isLoading: boolean;
  error: ApiError | null;
  retry: () => Promise<void>;
  refetch: () => Promise<void>;
}
```

**Behavior**:
- Calls `serviceFn()` via React Query with configured staleTime and retry
- On `ApiError`: shows toast via `useToast()` with status-appropriate message (401→auth, 403→access denied, 404→not found, 409→conflict, 5xx→server error)
- Returns structured error state for inline UI rendering via `ErrorBanner`
- `onErrorToast: false` suppresses toast for silent error handling (used in Phase 3 detail panels)

**Tests**:
- Service function success returns data
- ApiError with each status code shows correct toast message
- `onErrorToast: false` suppresses toast
- `retry()` re-executes service function
- Dependency array triggers refetch on change

### B) `useApiMutation` Hook

Wraps React Query mutation with standardized error handling and query invalidation.

**File**: `frontend/src/hooks/useApiMutation.ts`

**Interface**:
```typescript
interface UseApiMutationOptions<TVariables, TData> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  invalidateKeys?: string[][]; // query keys to invalidate on success
  onSuccessToast?: string | null;
  onErrorToast?: boolean; // default: true
}

interface UseApiMutationReturn<TVariables, TData> {
  mutate: (variables: TVariables) => void;
  mutateAsync: (variables: TVariables) => Promise<TData>;
  isPending: boolean;
  error: ApiError | null;
  resetError: () => void;
}
```

**Behavior**:
- On success: invalidates queries via `queryClient.invalidateQueries()` for each key in `invalidateKeys`, shows success toast if `onSuccessToast` is set
- On error: shows error toast, returns structured error for inline display

**Tests**:
- Success triggers query invalidation for all keys
- Success toast displays configured message
- Error toast displays status-appropriate message
- `isPending` true during execution
- `resetError()` clears error state

### C) `LoadingState` Component

Consistent loading placeholder with skeleton UI.

**File**: `frontend/src/components/ui/LoadingState.tsx`

**Interface**:
```typescript
interface LoadingStateProps {
  isLoading: boolean;
  fallback?: React.ReactNode; // optional custom loading UI
  children: React.ReactNode;
}
```

**Behavior**:
- When `isLoading` is true: shows skeleton UI (animated placeholder bars) or `fallback` if provided
- When `isLoading` is false: renders `children`
- Skeleton defaults to 3 lines of varying width for generic content

**Tests**:
- Renders children when not loading
- Renders skeleton when loading
- Renders custom fallback when provided

### D) `EmptyState` Component

Consistent empty data display with optional CTA.

**File**: `frontend/src/components/ui/EmptyState.tsx`

**Interface**:
```typescript
interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}
```

**Behavior**:
- Shows centered message with title and optional description
- If `actionLabel` and `onAction` provided: renders button below message
- Uses existing design system classes for consistent styling

**Tests**:
- Renders title
- Renders description when provided
- Renders button with actionLabel and onAction
- Button click triggers onAction callback

### E) `ErrorBanner` Component

Inline error display with optional retry.

**File**: `frontend/src/components/ui/ErrorBanner.tsx`

**Interface**:
```typescript
interface ErrorBannerProps {
  error: ApiError | null;
  onRetry?: () => void;
}
```

**Behavior**:
- When `error` is null: renders nothing
- When `error` is set: shows dismissible banner with error message
- If `onRetry` provided: shows retry button in banner
- Banner auto-hides after 30 seconds; manual dismiss via X button

**Tests**:
- Renders nothing when error is null
- Renders error message when error is set
- Renders retry button when onRetry provided
- Retry button click triggers callback
- Dismiss button hides banner

---

## Phase 1: Project Delete + Draft Continue/Variant + PlanningView Error States

### A) Project Delete

**Service**: `frontend/src/services/projects.ts` — add `deleteProject(projectId: string): Promise<void>`
- Calls `DELETE /projects/{project_id}`
- Returns void on success (200/204)

**UI**: `frontend/src/views/ProjectList.tsx`
- Delete button on each project card (icon button, positioned top-right)
- Click opens confirmation dialog: "Delete '{projectName}' and all associated data? This cannot be undone."
- On confirm: call mutation with `useApiMutation`, invalidate projects query, navigate to `/`, show success toast
- On 409 (active jobs): show error toast "Cannot delete project with active jobs. Complete or cancel jobs first."
- On 404: show error toast "Project not found"
- On 403: show error toast "Access denied"

**Tests** (TDD):
- `deleteProject` calls correct endpoint with projectId in path
- Confirmation dialog renders with project name
- Confirm triggers mutation
- Success invalidates projects query and navigates to `/`
- 409 shows specific active jobs message
- 404/403 show appropriate error messages

### B) Draft Continue + Alternate Variant

**Services**: `frontend/src/services/drafting.ts` — add two functions:
- `continueDraft(artifactId: string, projectId?: string): Promise<{ run_id: string; status: string }>` → `POST /drafting/draft-artifacts/continue`
- `createAlternateVariant(artifactId: string, projectId?: string): Promise<{ run_id: string; status: string }>` → `POST /drafting/draft-artifacts/alternate-variant`

**UI**: `frontend/src/views/WritingView.tsx`
- "Continue" and "Alternate Variant" action buttons on each draft artifact card in the drafts panel
- Buttons disabled when: no prior draft content, active generation in progress, chapter already promoted to manuscript
- Click creates new job via mutation; show pending state; poll for completion; display result inline or navigate to new draft
- On 404 (no prior draft): disable button with tooltip "No prior content to continue from"
- On 409 (active generation): disable button with tooltip "Generation in progress"

**Tests** (TDD):
- `continueDraft` calls correct endpoint with artifactId and projectId
- `createAlternateVariant` calls correct endpoint with artifactId and projectId
- Buttons disabled when no prior content
- Buttons disabled when generation active
- Success returns run_id and triggers polling
- 404/409 show appropriate error messages

### C) PlanningView Error States

**Changes**: `frontend/src/views/PlanningView.tsx`

Apply Phase 0 primitives to all tabs:
- Wrap each tab's data query with `useApiQuery`. All tabs use the same hook; no exceptions.
- Add `ErrorBanner` above content area for each tab
- Add `LoadingState` for initial load on each tab: sequence plans, chapter plans, scene plans, beat plans, dependencies, chapter packets, storyboard cards, flow stages
- Add `EmptyState` for empty data sets per tab with contextual CTAs:
  - "No sequences yet" → CTA: "Create Plan" (opens sequence plan form)
  - "No chapters yet" → CTA: "Add Chapter"
  - "No scenes yet" → CTA: "Add Scene"
  - "No beats yet" → CTA: "Add Beat"
  - "No dependencies" → no CTA (informational)
  - "No chapter packets" → CTA: "Create Packet"
  - "No storyboard cards" → CTA: "Add Card"

**Tests** (TDD):
- Error banner renders when query returns error
- Loading state shows skeleton during initial load
- Empty state renders with correct message and CTA per tab
- CTA button triggers correct action (opens form, scrolls to form, etc.)
- Partial failure: one tab fails, others render normally

---

## Phase 2: Retry Paths + Generation/Review States + Storyboard CRUD

### A) Generation + Assist Retry

**Services**:
- `frontend/src/services/storyGeneration.ts` — add `retryGeneration(generationId: string): Promise<{ run_id: string; status: string }>` → `POST /v1/story-generation/runs/{generation_id}/retry`
- `frontend/src/services/manuscriptAssist.ts` — add `retryAssist(assistId: string): Promise<{ run_id: string; status: string }>` → `POST /v1/manuscript-assist/runs/{assist_id}/retry`

**UI**:
- `GenerationView.tsx`: "Retry" button on failed generation run cards (visible when status is `failed` or `completed_with_errors`)
- Manuscript assist suggestions panel: "Retry" button on failed assist runs
- Retry creates new attempt with same packet/config; poll for completion; replace status in UI atomically
- On 409 (retry on non-failed run): disable button with tooltip
- On 404 (expired packet): show error toast "Generation packet expired. Re-submit from wizard."
- On concurrent retry: show conflict message, refresh to latest state

**Tests** (TDD):
- `retryGeneration` calls correct endpoint with generationId in path
- `retryAssist` calls correct endpoint with assistId in path
- Retry button visible only on failed/completed_with_errors runs
- Success returns new run_id and triggers polling
- 409 disables button with tooltip
- 404 shows expired packet message

### B) Storyboard Full CRUD + Reindex

**Services**: `frontend/src/services/storyboard.ts` — add three functions:
- `updateStoryboardCard(cardId: string, data: StoryboardCardUpdate, projectId?: string): Promise<StoryboardCard>` → `PATCH /storyboard/cards/{card_id}`
- `deleteStoryboardCard(cardId: string, projectId?: string): Promise<void>` → `DELETE /storyboard/cards/{card_id}`
- `reindexColumn(columnId: string, orderedIds: string[], projectId?: string): Promise<void>` → `PUT /storyboard/cards/{column_id}/reindex`

**UI**: `frontend/src/views/PlanningView.tsx` storyboard tab
- Inline edit form on card click (matching existing planning inline edit pattern): title, description, status fields
- Delete button on each card with confirmation dialog ("Delete this card?")
- Drag-drop reindex in columns: on drop, call `reindexColumn` with new ordered array; optimistic update with rollback on failure
- On 409 (concurrent edit): show conflict toast, refresh from server
- On delete last card in column: allow deletion, show empty state for column

**Tests** (TDD):
- `updateStoryboardCard` calls PATCH with cardId and update data
- `deleteStoryboardCard` calls DELETE with cardId
- `reindexColumn` calls PUT with columnId and ordered array
- Inline edit form pre-populates with current values
- Delete confirmation dialog renders
- Drag-drop reindex calls service with correct order
- Optimistic update rolls back on failure
- 409 shows conflict toast and refreshes

### C) Brainstorm Promote

**Service**: `frontend/src/services/brainstorm.ts` — add `promoteBrainstormItem(itemId: string, projectId?: string): Promise<{ promoted_to: string; target_id: string }>` → `POST /brainstorm/items/promote`

**UI**: `frontend/src/views/` (brainstorm section, likely in PlanningView or dedicated view)
- "Promote" button on brainstorm items
- Click opens promotion dialog: select target type (character, world bible entry, arc) + preview field mapping
- On confirm: call mutation, invalidate brainstorm items query, show success toast with target type
- On 409 (already promoted): disable button with tooltip "Already promoted to {target_type}"
- On 400 (invalid target type): show validation error in dialog

**Tests** (TDD):
- `promoteBrainstormItem` calls correct endpoint with itemId
- Promotion dialog renders with target type options
- Field mapping preview shows source→target field pairs
- Success invalidates brainstorm query and shows toast
- 409 disables button with tooltip
- 400 shows validation error

### D) GenerationView + ReviewView Error States

**GenerationView**: `frontend/src/views/GenerationView.tsx`
- Wrap runs query with `useApiQuery`
- Add `LoadingState` for initial load
- Add `EmptyState`: "No generation runs yet" with CTA "Start Generation Wizard" (navigates to wizard)
- Add `ErrorBanner` for query failures

**ReviewView**: `frontend/src/views/ReviewView.tsx`
- Wrap findings and decisions queries with `useApiQuery`
- Add `LoadingState` for initial load on each list
- Add `EmptyState`: "No review findings yet" / "No decisions recorded"
- Add `ErrorBanner` for query failures

**Tests** (TDD):
- GenerationView loading state shows skeleton during initial load
- GenerationView empty state shows "No generation runs yet" with CTA
- GenerationView error banner renders on query failure
- ReviewView loading/error/empty states render correctly
- CTA navigation works for empty states

---

## Phase 3: All 23 Detail Endpoints + Remaining Cleanup

### Pattern for All Detail Endpoints

Each detail endpoint follows the same implementation pattern:
1. Service function in existing service file (or new file if domain-specific)
2. `useApiQuery` hook wrapper for data fetching
3. Detail panel or modal component with loading/error/empty states from Phase 0
4. TDD tests for: service function calls correct endpoint, 404 handling, 409 handling, data integrity

### A) Branch Detail (4 endpoints)

**Services**: `frontend/src/services/branches.ts` — add:
- `getBranch(branchId: string, projectId?: string): Promise<BranchRecord>` → `GET /branches/{branch_id}`
- `getBranchComparison(comparisonId: string, projectId?: string): Promise<BranchComparisonRecord>` → `GET /branches/comparisons/{comparison_id}`
- `getMergeDecision(decisionId: string, projectId?: string): Promise<MergeDecisionRecord>` → `GET /branches/merge-decisions/{merge_decision_id}`
- `getBranchStateRefs(branchId: string, projectId?: string): Promise<StateRef[]>` → `GET /branches/{branch_id}/state-refs`

**UI**: Detail panel in branching view triggered by clicking branch/comparison/decision card. Shows full record with all fields. State refs show as linked list of referenced states.
**Edge cases**: Branch deleted (404), comparison with no base branch, merge decision on archived branch

### B) Character + Relationship Detail (2 endpoints)

**Services**: `frontend/src/services/characters.ts` — add:
- `getCharacter(characterId: string, projectId: string): Promise<CharacterProfile>` → `GET /characters/{character_id}`
- `getCharacterRelationships(characterId: string, projectId: string): Promise<RelationshipEdge[]>` → `GET /characters/{character_id}/relationships`

**UI**: Character detail panel with full profile (all fields from CharacterProfile schema), continuity facts, writer notes. Relationship sub-panel showing edges filtered to this character with visual graph.
**Edge cases**: Character deleted (404), circular relationships, self-referential edges

### C) Drafting Detail (3 endpoints)

**Services**: `frontend/src/services/drafting.ts` — add:
- `getDraftArtifact(artifactId: string, projectId: string): Promise<DraftArtifact>` → `GET /drafting/draft-artifacts/{artifact_id}`
- `getManuscriptDocument(documentId: string, projectId: string): Promise<ManuscriptDocument>` → `GET /drafting/manuscript-documents/{document_id}`
- `getRevisionSuggestion(suggestionId: string, projectId: string): Promise<RevisionSuggestion>` → `GET /drafting/revision-suggestions/{suggestion_id}`

**UI**: Draft detail modal with full content, version history, canon risk rating. Manuscript document viewer with edit capability. Suggestion detail with diff preview and apply/reject buttons.
**Edge cases**: Artifact superseded (404), document locked (409), suggestion already applied/rejected/archived (409)

### D) Planning Detail (5 endpoints)

**Services**: `frontend/src/services/planning.ts` — add:
- `getSequencePlan(sequenceId: string, projectId: string): Promise<SequencePlan>` → `GET /planning/sequence-plans/{sequence_id}`
- `getChapterPlan(chapterId: string, projectId: string): Promise<ChapterPlan>` → `GET /planning/chapter-plans/{chapter_id}`
- `getScenePlan(sceneId: string, projectId: string): Promise<ScenePlan>` → `GET /planning/scene-plans/{scene_id}`
- `getBeatPlan(beatId: string, projectId: string): Promise<BeatPlan>` → `GET /planning/beat-plans/{beat_id}`
- `getChapterPacket(packetId: string, projectId: string): Promise<ChapterPacket>` → `GET /planning/chapter-packets/{packet_id}`

**UI**: Detail panel for each plan type showing full record with dependencies, active characters, chapter packet context. Hierarchical drill-down: sequence → chapter → scene → beat via linked navigation.
**Edge cases**: Plan with missing parent reference (404), circular dependencies, packet with no chapter plan

### E) Review + Foundation Detail (4 endpoints)

**Services**:
- `frontend/src/services/review.ts` — add: `getFinding(findingId: string, projectId: string): Promise<ReviewFinding>`, `getDecision(decisionId: string, projectId: string): Promise<ReviewDecision>`
- `frontend/src/services/foundation.ts` — add: `getReviewCues(projectId: string): Promise<ReviewCue[]>`, `getFoundationRevisions(projectId: string): Promise<FoundationRevision[]>`

**UI**: Finding detail with evidence, severity, and resolution status. Decision detail with rationale and timestamp. Review cues list with actionable items. Foundation revision timeline with diff view between revisions.
**Edge cases**: Finding for deleted artifact (404), decision on resolved finding, no foundation revisions yet (empty state)

### F) World Bible Detail (1 endpoint)

**Service**: `frontend/src/services/worldBible.ts` — add: `getWorldBibleEntry(entryType: string, title: string, projectId: string): Promise<WorldBibleEntry>` → `GET /world-bible/{entry_type}/{title}`

**UI**: Entry detail panel with full content, canonical facts, related characters (linked to character detail), continuity warnings.
**Edge cases**: Entry with special chars in title (URL encoding), entry type not found (404), concurrent edit conflict (409)

### G) Arcs Update + Relationships Update + Flow Init/Reorder (3 endpoints)

**Services**:
- `frontend/src/services/arcs.ts` — add: `updateArcSelection(selectionId: string, data: ArcSelectionUpdate, projectId: string): Promise<ArcSelection>` → `PATCH /arcs/selections/{selection_id}`
- `frontend/src/services/relationships.ts` — add: `updateRelationship(edgeId: string, data: RelationshipUpdate, projectId: string): Promise<RelationshipEdge>` → `PATCH /relationships/{edge_id}`
- `frontend/src/services/flow.ts` — add: `initFlow(projectId: string): Promise<FlowStage[]>`, `reorderFlowStages(orderedIds: string[], projectId: string): Promise<void>`

**UI**: Inline edit on arc selections (matching existing planning inline edit pattern). Inline edit on relationships. Flow init button in FlowEditor for new projects ("Initialize Default Flow"). Drag-drop reorder in FlowEditor with save-on-drop calling `reorderFlowStages`.
**Edge cases**: Update to archived selection (409), relationship between deleted characters (404), flow already initialized (409), reorder with duplicate IDs (400)

### H) Jobs Inspect Detail (3 endpoints)

**Services**: `frontend/src/services/jobs.ts` — add:
- `getJobSteps(jobId: string): Promise<StepRecord[]>` → `GET /jobs/{job_id}/steps`
- `getJobLineage(jobId: string): Promise<LineageRecord[]>` → `GET /jobs/{job_id}/lineage`
- `retryJob(jobId: string): Promise<{ run_id: string; status: string }>` → `POST /jobs/{job_id}/retry`

**UI**: Steps table in InspectView (enhance existing view). Lineage graph visualization showing artifact relationships. Retry button on failed jobs with confirmation dialog.
**Edge cases**: Job with no steps yet (empty state), lineage with circular references (render as DAG with cycle detection), retry on non-terminal job (409)

### I) Service Pattern Cleanup

- Convert `jobsService` (object export) to named async function exports consistent with other 21 services
- Convert `flowService` (object export) to named async function exports
- Update all import sites to use named imports

---

## Testing Strategy

All new code follows TDD:
1. Write failing test for service function (verify endpoint, params, response shape)
2. Implement service function to pass test
3. Write failing test for hook/component (verify rendering, error handling, user interactions)
4. Implement hook/component to pass test
5. Write integration test for end-to-end flow (service → hook → component → query invalidation)

Test coverage targets:
- Service functions: 100% of new exports tested
- Hooks: all state transitions and error paths tested
- Components: loading/error/empty states tested; user interactions tested with React Testing Library
- Edge cases: 404, 409, and data integrity scenarios tested per endpoint

## File Structure Impact

```
frontend/src/
  hooks/
    useApiQuery.ts (new)
    useApiMutation.ts (new)
  components/ui/
    LoadingState.tsx (new)
    EmptyState.tsx (new)
    ErrorBanner.tsx (new)
  services/
    projects.ts (add: deleteProject)
    drafting.ts (add: continueDraft, createAlternateVariant, getDraftArtifact, getManuscriptDocument, getRevisionSuggestion)
    storyGeneration.ts (add: retryGeneration)
    manuscriptAssist.ts (add: retryAssist)
    storyboard.ts (add: updateStoryboardCard, deleteStoryboardCard, reindexColumn)
    brainstorm.ts (add: promoteBrainstormItem)
    branches.ts (add: getBranch, getBranchComparison, getMergeDecision, getBranchStateRefs)
    characters.ts (add: getCharacter, getCharacterRelationships)
    planning.ts (add: getSequencePlan, getChapterPlan, getScenePlan, getBeatPlan, getChapterPacket)
    review.ts (add: getFinding, getDecision)
    foundation.ts (add: getReviewCues, getFoundationRevisions)
    worldBible.ts (add: getWorldBibleEntry)
    arcs.ts (add: updateArcSelection)
    relationships.ts (add: updateRelationship)
    flow.ts (add: initFlow, reorderFlowStages; refactor: named exports)
    jobs.ts (add: getJobSteps, getJobLineage, retryJob; refactor: named exports)
  views/
    ProjectList.tsx (add: delete with confirmation)
    WritingView.tsx (add: continue/variant buttons)
    PlanningView.tsx (add: error/loading/empty states, storyboard CRUD, detail drill-down)
    GenerationView.tsx (add: retry, error/loading/empty states)
    ReviewView.tsx (add: error/loading/empty states, detail views)
    InspectView.tsx (add: steps table, lineage graph, retry button)
```

## Estimated Scope

| Phase | New Service Functions | New Components/Hooks | Test Files | Estimated Tasks |
|-------|----------------------|---------------------|------------|-----------------|
| 0 | 0 | 5 (2 hooks + 3 components) | 5 | ~8 |
| 1 | 3 | 0 (reuses Phase 0) | 3 | ~10 |
| 2 | 6 | 0 (reuses Phase 0) | 6 | ~14 |
| 3 | 26 | 0 (reuses Phase 0) | 10+ | ~45 |
| **Total** | **35** | **5** | **24+** | **~77** |
