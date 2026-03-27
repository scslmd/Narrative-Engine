# Frontend API Alignment Issues

This document identifies mismatches between frontend task specifications and actual backend API implementations.

## Critical Issues (Block Development)

### 1. No Manuscript Document Creation Endpoint

**Issue**: FE-013 specifies promoting drafts to manuscripts, but backend has no POST endpoint.

**Backend Reality**:
- `GET /story-development/drafting/draft-artifacts` ✅
- `GET /story-development/drafting/draft-artifacts/{artifact_id}` ✅
- `GET /story-development/drafting/manuscript-documents` ✅
- `GET /story-development/drafting/manuscript-documents/{document_id}` ✅
- `POST /story-development/drafting/manuscript-documents` ❌ **DOES NOT EXIST**

**Resolution**: FE-013 uses mock service with clear "mock mode" banner. Backend endpoint needed before production use.

---

### 2. No Review Decision Creation Endpoint

**Issue**: FE-023 specifies recording review decisions, but backend only has GET endpoints.

**Backend Reality**:
- `GET /story-development/review/decisions` ✅
- `GET /story-development/review/decisions/{decision_id}` ✅
- `POST /story-development/review/decisions` ❌ **DOES NOT EXIST**

**Resolution**: FE-023 uses mock service. Backend needs POST endpoint for decision recording.

---

### 3. No Flow Editor Endpoints

**Issue**: FE-006 specifies editing flow stages, but backend has no API endpoints for flow management.

**Backend Reality**:
- `StoryFlowStage` schema exists ✅
- `StoryFlowDefinition` schema exists ✅
- API endpoints ❌ **DOES NOT EXIST** (services only, no routes)

**Resolution**: FE-006 uses mock service. Backend needs:
- `GET /story-development/flow` - get current flow definition
- `POST /story-development/flow/stages` - add stage
- `PUT /story-development/flow/stages/{stage_id}` - update stage
- `DELETE /story-development/flow/stages/{stage_id}` - remove stage
- `PUT /story-development/flow/stages/reorder` - reorder stages

---

### 4. No Brainstorm/Foundation/Character/World Bible Endpoints

**Issue**: FE-029 through FE-032 specify these workspaces, but backend has no API endpoints.

**Backend Reality**:
- Schemas exist for all objects ✅
- Services exist (partial implementation) ✅
- API endpoints ❌ **DOES NOT EXIST**

**Resolution**: All use mock services. Backend needs full endpoint implementation.

---

### 5. No Manuscript Aids Endpoints

**Issue**: FE-025 through FE-028 specify manuscript aids, but backend has no implementation.

**Backend Reality**:
- `RevisionSuggestion` schema exists ✅
- `GET /story-development/drafting/revision-suggestions` ✅
- `GET /story-development/drafting/revision-suggestions/{suggestion_id}` ✅
- POST endpoints for creating suggestions ❌ **DOES NOT EXIST**

**Resolution**: FE-025 through FE-028 use mock services. Backend needs:
- `POST /story-development/drafting/revision-suggestions` - create suggestion request
- `PUT /story-development/drafting/revision-suggestions/{id}/decision` - record decision

---

## Schema Mismatches (Need Correction)

### 6. Project Schema Fields

**Frontend Specified**: project_id, project_name, created_at, health_status

**Backend Actual** (`ProjectSummaryResponse`):
```python
project_id: str
project_name: str
genre: str
tone_profile: str
story_structure: str
created_at: datetime
updated_at: datetime
```

**Correction**: Remove health_status, add genre, tone_profile, story_structure

---

### 7. Job Creation Schema

**Frontend Specified**: phase, model_id, payload

**Backend Actual** (`JobCreateRequest`):
```python
phase: JobPhase  # P-100, P-200, P-300, P-400
payload: dict[str, Any]
```

**Correction**: Remove model_id - models are configured in backend, not per-job

---

### 8. Chapter/Scene Plan Status Field

**Frontend Specified**: status with enum values (DRAFT, PROPOSED, CANONICAL, etc.)

**Backend Actual**:
```python
status: str = Field(default="draft", min_length=1)
```

**Correction**: Backend uses string, not enum. Frontend should map strings to UI states:
- "draft" → DRAFT
- "proposed" → PROPOSED
- "canonical" → CANONICAL
- "superseded" → SUPERSEDED
- "rejected" → REJECTED

---

### 9. Checker Finding Severity

**Frontend Specified**: severity as enum (LOW, MEDIUM, HIGH, CRITICAL)

**Backend Actual**:
```python
severity: str = Field(min_length=1)
```

**Correction**: Backend uses string. Frontend should map:
- "low" → LOW
- "medium" → MEDIUM
- "high" → HIGH
- "critical" → CRITICAL

---

### 10. Review Decision Actions

**Frontend Specified**: accept, reject, defer, escalate, refine

**Backend Actual** (`ReviewDecision`):
```python
decision_action: str  # No enum constraint
```

**Correction**: Backend uses string. Frontend should use exact strings:
- "accept"
- "reject"
- "defer"
- "escalate"
- "refine"

---

## Missing Features (Not Blockers)

### 11. No Theming Architecture

**Issue**: No support for stage-based UI themes (e.g., different colors for planning vs writing vs review).

**Recommendation**: Add FE-001A theming task with:
- CSS variables for theme colors
- Theme store in Zustand
- Stage-based theme switching
- Dark/light mode support

---

### 12. No Pagination Support

**Issue**: Backend endpoints don't support pagination, but frontend should be prepared for it.

**Backend Reality**: Most list endpoints return all items with no limit/offset parameters.

**Recommendation**: Frontend should handle large lists gracefully (virtual scrolling) but not implement pagination until backend adds it.

---

### 13. No Real-time Updates (WebSockets)

**Issue**: Frontend uses polling (600ms), but backend has no WebSocket support.

**Recommendation**: Keep polling for now. Add WebSocket support later if needed for real-time collaboration.

---

### 14. No Export/Import Endpoints

**Issue**: Frontend may need to export manuscripts or import from other formats.

**Backend Reality**: No export/import endpoints exist.

**Recommendation**: Frontend can implement client-side export (Markdown, PDF) without backend. Import needs backend support.

---

## Architecture Recommendations

### 15. Add Theming Support (FE-001A)

**Write scope**: `frontend/src/theme/`, `frontend/src/stores/themeStore.ts`

**Expected outcome**: Stage-based theming with dark/light mode

**Acceptance criteria**:
- CSS variables defined in `:root` and `[data-theme="dark"]`
- ThemeStore manages current theme (light/dark) and stage theme (planning/writing/review)
- Stage themes have distinct color palettes:
  - Planning: Blue/indigo tones
  - Writing: Green/teal tones
  - Review: Orange/amber tones
  - Inspect: Purple/violet tones
- Toggle button in header for light/dark mode
- Auto-switch stage theme based on current mode
- Theme persists in localStorage

---

### 16. Add Error Boundary Components

**Write scope**: `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/components/Fallback.tsx`

**Expected outcome**: Graceful error handling without full page crashes

**Acceptance criteria**:
- ErrorBoundary wraps all major component trees
- Fallback shows user-friendly error message with retry button
- Errors logged to console with component stack
- Network errors show "Check connection" message
- API errors show status code and message

---

### 17. Add Loading Skeleton Components

**Write scope**: `frontend/src/components/skeleton/`

**Expected outcome**: Consistent loading states across all components

**Acceptance criteria**:
- Skeleton variants: text, card, list, editor
- Animated pulse effect
- Used in all list/detail views during API fetch
- Fallback to skeleton on error retry

---

### 18. Add Toast Notification System

**Write scope**: `frontend/src/components/toast/`, `frontend/src/lib/toast.ts`

**Expected outcome**: Consistent user feedback for actions

**Acceptance criteria**:
- Toast types: success, error, warning, info
- Auto-dismiss after 5 seconds
- Manual dismiss button
- Queue multiple toasts (max 3 visible)
- Accessible (ARIA live region)

---

## Mock Service Contracts

All mock services must follow these contracts:

### Mock Service Interface

```typescript
interface MockService<T> {
  list(projectId: string): Promise<T[]>;
  get(projectId: string, id: string): Promise<T>;
  create(projectId: string, data: Partial<T>): Promise<T>;
  update(projectId: string, id: string, data: Partial<T>): Promise<T>;
  delete(projectId: string, id: string): Promise<void>;
}
```

### Mock Service Behavior

1. **Delay**: 2000ms delay on all operations (simulates network)
2. **Storage**: In-memory storage per project (clears on reload)
3. **Validation**: Same validation as backend schema
4. **Errors**: Return appropriate error codes (400, 404, 500)
5. **Banner**: UI shows "Mock Mode" banner when mock service active

### Mock Service Files

```
frontend/src/services/mocks/
  ├── flowMock.ts
  ├── brainstormMock.ts
  ├── foundationMock.ts
  ├── characterMock.ts
  ├── worldBibleMock.ts
  ├── arcComparisonMock.ts
  ├── draftingMock.ts
  └── manuscriptAidsMock.ts
```

---

## Environment Variables

```bash
# .env.local (frontend)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCKS=true
VITE_THEME=light
VITE_STAGE_THEME=writing
```

---

## Summary

| Issue | Severity | Resolution |
|-------|----------|------------|
| No manuscript creation endpoint | Critical | Mock service + banner |
| No review decision endpoint | Critical | Mock service + banner |
| No flow editor endpoints | High | Mock service |
| No brainstorm/foundation/character/world bible endpoints | High | Mock services |
| No manuscript aids endpoints | Medium | Mock service |
| Project schema mismatch | Medium | Update frontend types |
| Job creation schema mismatch | Medium | Remove model_id |
| Status/severity as strings not enums | Low | Map in frontend |
| No theming | Low | Add FE-001A |
| No error boundaries | Medium | Add components |
| No loading skeletons | Low | Add components |
| No toast system | Low | Add components |

---

## Next Steps

1. ✅ Update TODO.md with corrected API schemas
2. ✅ Add FE-001A theming task
3. ✅ Add error boundary, skeleton, toast tasks
4. ✅ Document mock service contracts
5. ⏳ Implement backend endpoints (separate effort)
6. ⏳ Replace mock services with real APIs when available
