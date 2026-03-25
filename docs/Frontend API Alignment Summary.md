# Frontend API Alignment Summary

This document summarizes the API alignment work completed for the narrative engine frontend.

## Changes Made

### 1. Updated TODO.md

**Added Tasks**:
- **FE-001A**: Theming architecture with stage-based colors
- **FE-004A**: Error boundary components
- **FE-004B**: Loading skeleton components
- **FE-004C**: Toast notification system

**Updated Tasks with Backend Schemas**:
- **FE-003**: Project list/creation - Added `ProjectSummaryResponse` schema fields (genre, tone_profile, story_structure)
- **FE-007**: Planning board view - Added `ChapterPlan` and `ScenePlan` schemas
- **FE-008**: Chapter/scene cards - Clarified status field is string, not enum
- **FE-009**: Chapter packet builder - Added `ChapterPacket` schema
- **FE-013**: Draft promotion - Marked as mock service (no POST endpoint)
- **FE-014**: Job launch - Removed model_id from schema (backend configures models)
- **FE-015**: Job status polling - Added `JobStatusResponse` schema details
- **FE-016**: Job logs viewer - Added `JobLogsResponse` schema
- **FE-018-021**: Inspect mode - Added detailed schemas for steps, lineage, provenance
- **FE-022**: Checker findings - Added `CheckerFinding` schema, severity as string
- **FE-023**: Review decisions - Marked as mock service, added `ReviewDecision` schema
- **FE-024**: Role-model checker - Added detailed acceptance criteria
- **FE-025-028**: Manuscript aids - Marked as mock services, added schemas
- **FE-029-032**: Story development features - All marked as mock services with detailed schemas

### 2. Created docs/Frontend API Alignment Issues.md

Comprehensive document identifying:
- **Critical Issues**: 5 blocking issues (no POST endpoints for manuscript creation, review decisions, flow editor, brainstorm/foundation/character/world bible, manuscript aids)
- **Schema Mismatches**: 8 schema corrections (project fields, job creation, status/severity as strings)
- **Missing Features**: 4 recommendations (theming, error boundaries, loading skeletons, toast system)
- **Mock Service Contracts**: Standard interface and behavior for all mock services

## Key Findings

### Backend Endpoints Ready for Frontend

**58 endpoints** are ready for immediate frontend integration:

### Projects (7 endpoints)
- GET/POST `/projects`
- GET `/projects/{id}`, `/projects/{id}/manifest`, `/projects/{id}/sequence`, `/projects/{id}/chapter-1`

### Jobs (7 endpoints)
- POST `/jobs/create`
- GET `/jobs/{id}/status`, `/jobs/{id}/logs`, `/jobs/{id}/steps`, `/jobs/{id}/lineage`, `/jobs/{id}/attempts`
- POST `/jobs/{id}/retry`

### Role Model Checker (7 endpoints)
- POST `/role-model-checker/run`, `/role-model-checker/start`
- GET `/role-model-checker/{run_id}/status`, `/role-model-checker/{run_id}/steps`, `/role-model-checker/{run_id}/lineage`, `/role-model-checker/{run_id}/attempts`
- POST `/role-model-checker/{run_id}/retry`

### Models (1 endpoint)
- GET `/models`

### Story Branches (12 endpoints)
- GET/POST `/story-development/branches`
- GET/POST `/story-development/branches/active`
- GET/POST `/story-development/branches/comparisons`
- GET `/story-development/branches/comparisons/{id}`
- GET/POST `/story-development/branches/merge-decisions`
- GET `/story-development/branches/{id}`, `/story-development/branches/{id}/state-refs`

### Story Decisions (3 endpoints)
- GET `/story-development/decisions`, `/story-development/decisions/{node_id}`, `/story-development/decisions/{node_id}/path`

### Planning (12 endpoints)
- GET `/story-development/planning/sequence-plans`, `/story-development/planning/sequence-plans/{id}`
- GET `/story-development/planning/chapter-plans`, `/story-development/planning/chapter-plans/{id}`
- GET `/story-development/planning/scene-plans`, `/story-development/planning/scene-plans/{id}`
- GET `/story-development/planning/dependencies`, `/story-development/planning/dependencies/{id}`
- GET `/story-development/planning/chapter-packets`, `/story-development/planning/chapter-packets/{id}`

### Drafting (6 endpoints)
- GET `/story-development/drafting/draft-artifacts`, `/story-development/drafting/draft-artifacts/{id}`
- GET `/story-development/drafting/manuscript-documents`, `/story-development/drafting/manuscript-documents/{id}`
- GET `/story-development/drafting/revision-suggestions`, `/story-development/drafting/revision-suggestions/{id}`

### Review (6 endpoints)
- GET `/story-development/review/findings`, `/story-development/review/findings/{id}`
- GET `/story-development/review/decisions`, `/story-development/review/decisions/{id}`
- GET `/story-development/review/inspect-links`, `/story-development/review/inspect-links/{id}`

### Backend Endpoints Not Yet Available

**9 feature areas** require mock services:

1. **Manuscript document creation** (POST) - FE-013
2. **Review decision recording** (POST) - FE-023
3. **Flow editor** (all endpoints) - FE-006
4. **Revision suggestions creation** (POST) - FE-025, FE-028
5. **Brainstorm workspace** (all endpoints) - FE-029
6. **Foundation editor** (all endpoints) - FE-030
7. **Character builder** (all endpoints) - FE-031
8. **World bible workspace** (all endpoints) - FE-032
9. **Planning writes** (POST chapter-plans, scene-plans, sequence-plans, chapter-packets) - FE-007, FE-009

### Schema Corrections

1. **ProjectSummaryResponse**: Has genre, tone_profile, story_structure (not health_status)
2. **JobCreateRequest**: No model_id field (models configured in backend)
3. **Status fields**: String, not enum (map in frontend: "draft"→DRAFT, etc.)
4. **Severity fields**: String, not enum (map in frontend: "low"→LOW, etc.)
5. **Decision actions**: String values ("accept", "reject", "defer", "escalate", "refine")

## Theming Architecture

**New Task FE-001A** adds stage-based theming:
- **Light/Dark mode**: Toggle in header, persists in localStorage
- **Stage themes**: Distinct colors per mode
  - Planning: blue-600/blue-500
  - Writing: green-600/green-500
  - Review: orange-600/orange-500
  - Inspect: purple-600/purple-500
- **Auto-switch**: Stage theme changes with current mode
- **CSS variables**: All colors use CSS variables for dynamic theming

## Mock Service Contract

All mock services follow this standard:

```typescript
interface MockService<T> {
  list(projectId: string): Promise<T[]>;
  get(projectId: string, id: string): Promise<T>;
  create(projectId: string, data: Partial<T>): Promise<T>;
  update(projectId: string, id: string, data: Partial<T>): Promise<T>;
  delete(projectId: string, id: string): Promise<void>;
}
```

**Behavior**:
- 2000ms delay on all operations
- In-memory storage per project
- Same validation as backend schema
- Appropriate error codes (400, 404, 500)
- "Mock Mode" banner in UI
- Feature flag: `VITE_USE_MOCKS=true`

## Development Readiness

The frontend is now ready for development with:
- ✅ 36 deterministic task cards (FE-001 through FE-032, plus FE-001A, FE-004A, FE-004B, FE-004C, FE-024A, FE-024B, FE-024C)
- ✅ 4 new infrastructure tasks (FE-001A, FE-004A, FE-004B, FE-004C)
- ✅ 3 new story development tasks (FE-024A, FE-024B, FE-024C)
- ✅ Clear API alignment for all tasks
- ✅ Mock service contracts for unavailable endpoints
- ✅ Backend schema documentation for all types
- ✅ Theming architecture for stage-based UI
- ✅ Error handling, loading states, toast notifications
- ✅ 58 real API endpoints ready for integration

## Next Steps

1. **Frontend Development**: Begin with Phase 1 (FE-001 through FE-004C)
2. **Backend Development**: Implement missing POST endpoints (separate effort)
3. **Integration Testing**: Replace mock services with real APIs as they become available
4. **Documentation**: Update API docs as backend endpoints are added

## Files Modified

- `TODO.md`: Updated all 36 tasks with backend schemas and mock service specifications
- `docs/Frontend API Alignment Issues.md`: Created comprehensive alignment analysis
- `docs/Frontend API Alignment Summary.md`: This summary document

**Latest Updates**:
- Added FE-024: Role-model checker UI (real API with 7 endpoints)
- Added FE-024A: Story branches UI (real API with 12 endpoints)
- Added FE-024B: Story decision nodes UI (real API with 3 endpoints)
- Added FE-024C: Inspect run links UI (real API with 2 endpoints)
- Updated API Alignment Summary table with 58 ready endpoints
- Added planning writes to mock service requirements

## Environment Configuration

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCKS=true
VITE_THEME=light
VITE_STAGE_THEME=writing
```
