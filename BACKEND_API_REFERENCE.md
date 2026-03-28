# Backend API Reference for Frontend Integration

This document provides a comprehensive reference of all backend API endpoints available for frontend integration.

## Base URL

All endpoints are prefixed with `/v1` when accessed through the frontend.

## Authentication

### API Key Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/api-keys` | Create a new API key |
| `DELETE` | `/auth/api-keys/{key_prefix}` | Revoke an API key |

---

## Projects

### Project Management

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/projects` | List all projects | `ProjectListResponse` |
| `POST` | `/projects/create` | Create a new project | `Project` (201) |
| `GET` | `/projects/{project_id}` | Get a specific project | `Project` |
| `DELETE` | `/projects/{project_id}` | Delete a project | `204 No Content` |

---

## Story Development

### Branch Management

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/branches` | List all story branches | `StoryBranchListResponse` |
| `POST` | `/story-development/branches` | Create a new branch | `StoryBranch` (201) |
| `GET` | `/story-development/branches/{branch_id}` | Get a specific branch | `StoryBranch` |
| `GET` | `/story-development/branches/active` | Get active branch | `StoryBranch` |
| `POST` | `/story-development/branches/active` | Select active branch | `StoryBranch` |
| `GET` | `/story-development/branches/{branch_id}/state-refs` | List branch state refs | `BranchStateRefListResponse` |

### Branch Comparisons

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `POST` | `/story-development/branches/comparisons` | Create a comparison | `BranchComparisonRecord` (201) |
| `GET` | `/story-development/branches/comparisons` | List comparisons | `BranchComparisonListResponse` |
| `GET` | `/story-development/branches/comparisons/{comparison_id}` | Get a comparison | `BranchComparisonRecord` |

### Merge Decisions

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `POST` | `/story-development/branches/merge-decisions` | Record merge decision | `BranchMergeDecision` (201) |
| `GET` | `/story-development/branches/merge-decisions` | List merge decisions | `BranchMergeDecisionListResponse` |
| `GET` | `/story-development/branches/merge-decisions/{merge_decision_id}` | Get merge decision | `BranchMergeDecision` |

### Flow Stages

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/flow/stages` | List flow stages | `FlowStageListResponse` |
| `POST` | `/story-development/flow/stages` | Create a flow stage | `StoryFlowStage` (201) |
| `PATCH` | `/story-development/flow/stages/{stage_id}` | Update a flow stage | `StoryFlowStage` |
| `DELETE` | `/story-development/flow/stages/{stage_id}` | Delete a flow stage | `StoryFlowStage` |
| `POST` | `/story-development/flow/stages/reorder` | Reorder flow stages | `StoryFlowDefinition` |

### Story Decisions

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/decisions` | List decision nodes | `StoryDecisionNodeListResponse` |
| `GET` | `/story-development/decisions/{node_id}` | Get a decision node | `StoryDecisionNode` |
| `GET` | `/story-development/decisions/{node_id}/path` | Get decision path | `StoryDecisionPathResponse` |

### Review & Inspection

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/review/findings` | List checker findings | `CheckerFindingListResponse` |
| `GET` | `/story-development/review/findings/{finding_id}` | Get a finding | `CheckerFinding` |
| `GET` | `/story-development/review/decisions` | List review decisions | `ReviewDecisionListResponse` |
| `GET` | `/story-development/review/decisions/{decision_id}` | Get a decision | `ReviewDecision` |
| `POST` | `/story-development/review/decisions` | Record review decision | `ReviewDecision` (201) |
| `GET` | `/story-development/review/inspect-links` | List inspect links | `InspectRunLinkListResponse` |
| `GET` | `/story-development/review/inspect-links/{link_id}` | Get inspect link | `InspectRunLink` |

### Planning

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/planning/sequence-plans` | List sequence plans | `SequencePlanListResponse` |
| `GET` | `/story-development/planning/sequence-plans/{sequence_id}` | Get sequence plan | `SequencePlan` |
| `GET` | `/story-development/planning/chapter-plans` | List chapter plans | `ChapterPlanListResponse` |
| `GET` | `/story-development/planning/chapter-plans/{chapter_id}` | Get chapter plan | `ChapterPlan` |
| `GET` | `/story-development/planning/scene-plans` | List scene plans | `ScenePlanListResponse` |
| `GET` | `/story-development/planning/scene-plans/{scene_id}` | Get scene plan | `ScenePlan` |
| `GET` | `/story-development/planning/dependencies` | List dependencies | `PlanningDependencyListResponse` |
| `GET` | `/story-development/planning/dependencies/{dependency_id}` | Get dependency | `PlanningDependency` |
| `GET` | `/story-development/planning/chapter-packets` | List chapter packets | `ChapterPacketListResponse` |
| `GET` | `/story-development/planning/chapter-packets/{packet_id}` | Get chapter packet | `ChapterPacket` |

### Drafting & Manuscript

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/drafting/draft-artifacts` | List draft artifacts | `DraftArtifactListResponse` |
| `GET` | `/story-development/drafting/draft-artifacts/{artifact_id}` | Get draft artifact | `DraftArtifact` |
| `GET` | `/story-development/drafting/manuscript-documents` | List manuscript documents | `ManuscriptDocumentListResponse` |
| `GET` | `/story-development/drafting/manuscript-documents/{document_id}` | Get manuscript document | `ManuscriptDocument` |
| `POST` | `/story-development/drafting/manuscript-documents` | Create manuscript document | `ManuscriptDocument` (201) |
| `POST` | `/story-development/drafting/promote-draft` | Promote draft to manuscript | `ManuscriptDocument` (201) |
| `GET` | `/story-development/drafting/revision-suggestions` | List revision suggestions | `RevisionSuggestionListResponse` |
| `GET` | `/story-development/drafting/revision-suggestions/{suggestion_id}` | Get revision suggestion | `RevisionSuggestion` |
| `POST` | `/story-development/drafting/revision-suggestions` | Create revision suggestion | `RevisionSuggestion` (201) |

### Brainstorm (NEW)

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/brainstorm/items` | List brainstorm items | `BrainstormItemListResponse` |
| `POST` | `/story-development/brainstorm/items` | Create brainstorm item | `BrainstormItem` (201) |
| `POST` | `/story-development/brainstorm/items/cluster` | Cluster brainstorm items | `list[BrainstormItem]` |
| `POST` | `/story-development/brainstorm/items/promote` | Promote brainstorm item | `BrainstormPromotion` (201) |
| `GET` | `/story-development/brainstorm/promotions` | List promotions | `BrainstormPromotionListResponse` |

### Foundation (NEW)

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/foundation` | Get active foundation | `FoundationReadResponse` |
| `POST` | `/story-development/foundation` | Create foundation | `FoundationWriteResponse` (201) |
| `PATCH` | `/story-development/foundation` | Update foundation | `FoundationWriteResponse` |
| `GET` | `/story-development/foundation/revisions` | List revisions | `FoundationRevisionListResponse` |
| `GET` | `/story-development/foundation/review-cues` | List review cues | `FoundationReviewCueListResponse` |

### Characters (NEW)

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/characters` | List characters | `CharacterProfileListResponse` |
| `GET` | `/story-development/characters/{character_id}` | Get character | `CharacterProfile` |
| `POST` | `/story-development/characters` | Create character | `CharacterProfile` (201) |
| `PATCH` | `/story-development/characters/{character_id}` | Update character | `CharacterProfile` |
| `GET` | `/story-development/characters/{character_id}/relationships` | List relationships | `RelationshipEdgeListResponse` |
| `POST` | `/story-development/relationships` | Create relationship | `RelationshipEdge` (201) |

### World Bible (NEW)

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/world-bible` | List world bible entries | `WorldBibleEntryListResponse` |
| `GET` | `/story-development/world-bible/{entry_type}/{title}` | Get entry | `WorldBibleEntry` |
| `POST` | `/story-development/world-bible` | Create entry | `WorldBibleEntry` (201) |
| `PATCH` | `/story-development/world-bible/{entry_type}/{title}` | Update entry | `WorldBibleEntry` |

### Arcs (NEW)

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/story-development/arcs/candidates` | List arc candidates | `ArcCandidateListResponse` |
| `GET` | `/story-development/arcs/selections` | List arc selections | `ArcSelectionListResponse` |
| `GET` | `/story-development/arcs/stage-maps` | List arc stage maps | `ArcStageMapListResponse` |

---

## Jobs

### Job Management

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `POST` | `/jobs` | Create a new job | `JobStatusResponse` (201) |
| `GET` | `/jobs/{job_id}` | Get job status | `JobStatusResponse` |
| `GET` | `/jobs/{job_id}/events` | List job events | `list[dict]` |
| `GET` | `/jobs/{job_id}/attempts` | List job attempts | `list[dict]` |
| `GET` | `/jobs/{job_id}/logs` | Get job logs | `JobLogsResponse` |
| `POST` | `/jobs/{job_id}/claim` | Claim a job | `ClaimResult` |
| `POST` | `/jobs/{job_id}/heartbeat` | Update heartbeat | `204 No Content` |
| `POST` | `/jobs/{job_id}/complete` | Complete a job | `204 No Content` |
| `POST` | `/jobs/{job_id}/fail` | Fail a job | `204 No Content` |
| `POST` | `/jobs/{job_id}/retry` | Retry a failed job | `JobStatusResponse` |

---

## Role Model Checker

### Checker Management

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `POST` | `/role-model-checker/checks` | Create a new check | `CheckerStatusResponse` (201) |
| `GET` | `/role-model-checker/checks/{check_id}` | Get check status | `CheckerStatusResponse` |
| `GET` | `/role-model-checker/checks/{check_id}/events` | List check events | `list[dict]` |
| `GET` | `/role-model-checker/checks/{check_id}/attempts` | List check attempts | `list[dict]` |
| `GET` | `/role-model-checker/checks/{check_id}/logs` | Get check logs | `CheckerLogsResponse` |

---

## Models

### Model Registry

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/models` | List registered models | `list[ModelInfo]` |
| `GET` | `/models/{model_id}` | Get model info | `ModelInfo` |
| `POST` | `/models/register` | Register a model | `ModelInfo` (201) |
| `DELETE` | `/models/{model_id}` | Unregister a model | `204 No Content` |

---

## Health & Metrics

### Health Checks

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `GET` | `/health` | Basic health check | `HealthResponse` |
| `GET` | `/health/metrics` | Detailed metrics | `HealthMetricsResponse` |

---

## Backup

### Backup Management

| Method | Endpoint | Description | Response Model |
|--------|----------|-------------|----------------|
| `POST` | `/backup/create` | Create a backup | `BackupInfo` (201) |
| `GET` | `/backup` | List backups | `list[BackupInfo]` |
| `DELETE` | `/backup/{backup_id}` | Delete a backup | `204 No Content` |
| `POST` | `/backup/restore` | Restore from backup | `RestoreResult` |

---

## Query Parameters

Many endpoints support optional query parameters for filtering:

- `project_id` - Filter by project
- `subject_type` / `subject_id` - Filter by subject
- `target_kind` / `target_id` - Filter by target
- `object_kind` / `object_id` - Filter by object
- `run_id` / `logical_run_id` - Filter by run
- `entry_type` / `category` - Filter by type/category

---

## Error Responses

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Successful request |
| `201` | Created | Resource created successfully |
| `204` | No Content | Successful deletion |
| `400` | Bad Request | Invalid input or validation error |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists or conflict |
| `500` | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message describing the problem"
}
```

---

## Frontend Integration Notes

### Shared API Client

Use the shared Axios client from `frontend/src/lib/api.ts`:

```typescript
import api from '../lib/api';

export async function getFoundation(projectId: string) {
  const response = await api.get(`/story-development/foundation`, {
    params: { project_id: projectId },
  });
  return response.data;
}
```

### Response Models

All response models follow the pattern:
- List responses include `project_id`, `items`, and `meta` fields
- Single item responses return the item directly
- Create/update responses return the created/updated resource

### Pagination

Currently, list endpoints return all items. Pagination will be added in a future release.

---

## Testing

### Backend Tests

```bash
# Run all tests
python -m pytest -q -p no:cacheprovider

# Run specific test file
pytest tests/test_story_branching_service.py

# Run specific test
pytest tests/test_story_branching_service.py::test_create_branch
```

### Frontend Validation

```bash
# Run lint
cd frontend && npm run lint

# Run type check
cd frontend && npm run typecheck

# Run build
cd frontend && npm run build
```

---

## Recent Changes

### v1.0.0 (Current)

- Added Brainstorm endpoints
- Added Foundation endpoints
- Added Character endpoints
- Added World Bible endpoints
- Added Arc endpoints
- Enhanced Flow Stage management
- Improved error handling and validation

---

## Support

For questions or issues:
1. Check existing tests in `tests/` directory
2. Review service implementations in `app/services/`
3. Check router implementations in `app/api/`
