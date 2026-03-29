# Task List

Generated from `docs/archive/executor_atomic_staged_tasks.json`

---

## Stage 1 Tasks

### [0f3580e1] Convert `StageList` to read-only-capable presenter
- [x] Complete
**File:** `frontend/src/components/flow/StageList.tsx`  
**Dependencies:** None

Make `onEdit`, `onDelete`, and `onAddStage` optional. Render no edit/delete hover controls or empty-state add button when callbacks are absent.

**Guardrails:**
- Do not modify `StageCard.tsx` or `StageActions.tsx`
- Do not change `StoryFlowStage` type or API route contracts
- Do not add new props, stores, routes, or mutation behavior

---

### [e6bc6778] Remove interactive stage-mutation controls from `FlowEditor`
- [x] Complete
**File:** `frontend/src/components/flow/FlowEditor.tsx`  
**Dependencies:** 0f3580e1

Eliminate mutations (`addStageMutation`, `updateStageMutation`, `deleteStageMutation`), edit modal state, and top-level "Add Stage" select. Pass no mutation callbacks into `StageList`. Preserve existing query key `['flow-stages', projectId]`.

**Guardrails:**
- Do not modify `frontend/src/services/flow.ts` or backend routes
- Do not change the query key
- Do not introduce new buttons, toggles, or replacement workflows

---

### [c1da1f97] Recompose `Workspace` layout with stacked right rail
- [x] Complete
**File:** `frontend/src/views/Workspace.tsx`  
**Dependencies:** None

Move `NotesPanel` and `JobLaunchPanel` into a single stacked right rail instead of two parallel side columns. Keep `Outlet` as primary workspace pane. Preserve `WorkspaceShell` and `BottomUtilityLayer`.

**Guardrails:**
- Do not modify route paths or nested route ownership
- Do not edit `App.tsx`, `NotesPanel.tsx`, `JobLaunchPanel.tsx`, or `BottomUtilityLayer.tsx`
- Do not add new state, stores, or components

---

### [91eb7d31] Replace placeholder empty-state copy in `PlanningView`
- [x] Complete
**File:** `frontend/src/views/PlanningView.tsx`  
**Dependencies:** None

Update exact strings: "No sequence plans yet", "No chapter plans yet", "No scene plans yet", "No dependencies defined yet", "No chapter packets yet", "No arc selected yet", "No arc candidates yet", "No characters yet".

**Guardrails:**
- Do not change `PlanningTab` union or `activeTab` behavior
- Do not modify React Query keys
- Do not edit service files under `frontend/src/services/`
- Do not add new buttons, routes, or mutation behavior

---

### [418b7e40] Replace inspect attempts empty-state copy in `InspectTabs`
- [x] Complete
**File:** `frontend/src/components/inspect/InspectTabs.tsx`  
**Dependencies:** None

Replace "No attempts recorded yet" with explicit inspect wording. Keep `loadAttempts`, service calls, and rendering intact.

**Guardrails:**
- Do not modify `loadAttempts`, `useEffect`, or `TabKey` union
- Do not change calls to `jobsService.getAttempts()` or `getCheckerAttempts()`
- Do not edit `StepTimeline.tsx` or `ArtifactLineage.tsx`

---

### [27a05d44] Replace step-timeline empty-state copy in `StepTimeline`
- [x] Complete
**File:** `frontend/src/components/inspect/StepTimeline.tsx`  
**Dependencies:** None

Replace "No steps recorded yet" with explicit inspect wording. Keep `useJobSteps`, retry button, and `StepCard` rendering unchanged.

**Guardrails:**
- Do not change the `useJobSteps` hook signature or values passed from context
- Do not modify loading skeleton, error retry button, or sorting logic
- Do not edit `StepCard.tsx`

---

### [1fc9744f] Replace artifact-lineage empty-state copy in `ArtifactLineage`
- [x] Complete
**File:** `frontend/src/components/inspect/ArtifactLineage.tsx`  
**Dependencies:** None

Replace "No artifacts generated yet" with explicit persisted-lineage wording. Keep `useJobLineage`, retry behavior, and `ArtifactCard` rendering unchanged.

**Guardrails:**
- Do not change the `useJobLineage` hook signature or values passed from context
- Do not modify loading skeleton, error retry button, or populated branch
- Do not edit `ArtifactCard.tsx`

---

## Stage 2 Tasks

### [508f39db] Update README.md current status and workspace-scope language
- [x] Complete
**File:** `README.md`  
**Dependencies:** e6bc6778, c1da1f97, 91eb7d31, 418b7e40, 27a05d44, 1fc9744f

Align documentation with shipped routed product: planning is read-heavy, `FlowEditor` is stage visibility (not editable flow), `CharacterBuilder` ships profile editing only, arc support is read-only projections.

**Guardrails:**
- Do not edit any code files
- Do not change verified validation numbers or command list
- Do not invent new routes, mutation endpoints, or shipped workflows

---

### [bc449669] Correct current-state language in Frontend Design SRS v0.5.md
- [x] Complete
**File:** `docs/Frontend Design SRS v0.5.md`  
**Dependencies:** e6bc6778, 91eb7d31

Update implementation-status rows and mock-service notes to reflect shipped routed frontend after Stage 1 changes.

**Guardrails:**
- Do not edit any code files
- Do not delete historical task inventory
- Do not invent new routes, mutation flows, or helper layers

---

### [99ff6a99] Tighten Story Development Product Spec v0.1.md present-tense language
- [x] Complete
**File:** `docs/Story Development Product Spec v0.1.md`  
**Dependencies:** e6bc6778, 91eb7d31

Align product spec with current shipped route set: planning is read-heavy routed view, flow is not editable for v1.0, character profile editing ships, relationship-map workflows deferred, arc support is read-only projections.

**Guardrails:**
- Do not edit any code files
- Do not remove canonical object names (`StoryFlowStage`, `RelationshipEdge`, etc.)
- Do not invent new route paths, status codes, or release commitments

---

### [7c14dd43] Update Narrative SRS v0.3.md current-state and requirements language
- [x] Complete (already aligned)
**File:** `docs/Narrative SRS v0.3.md`  
**Dependencies:** e6bc6778, 91eb7d31

Align with shipped routed app: planning and arc views are read surfaces, `CharacterBuilder` ships profile editing only, relationship-map workflows deferred, interactive arc-decision behavior deferred.

**Guardrails:**
- Do not edit any code files
- Do not remove backend-domain terminology or canonical object references
- Do not add new UI components, routes, or endpoint claims

---

## Stage 3 Tasks

### [f3092970] Reconcile TODO.md top-level backlog after Stages 1 and 2
- [x] Complete
**File:** `TODO.md`  
**Dependencies:** c1da1f97, 91eb7d31, 418b7e40, 27a05d44, 1fc9744f, 508f39db, bc449669, 99ff6a99, 7c14dd43

Update `### v1.0 Release Checklist` and `### Backend Reliability` sections to close items satisfied by shipped code or scope-cut docs. Keep only true remaining blockers open with updated wording.

**Guardrails:**
- Do not edit any code files
- Do not add new backlog sections or delete historical implementation notes outside active top checklist sections
- Do not re-open items already verified complete
- Do not invent new product capabilities or roadmap categories
