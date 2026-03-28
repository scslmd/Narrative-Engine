# API Implementation Summary

## API Versioning

All API endpoints are now versioned with `/v1` prefix:
- Base URL: `http://localhost:8000/v1/...`
- Frontend config: Set `VITE_API_BASE_URL=http://localhost:8000/v1`

### Router Prefixes
| Service | Prefix | Example Endpoint |
|---------|--------|------------------|
| Story Development | `/v1/story-development` | `GET /v1/story-development/drafting/draft-artifacts` |
| Jobs | `/v1/jobs` | `POST /v1/jobs/create` |
| Projects | `/v1/projects` | `GET /v1/projects/{project_id}` |
| Role Model Checker | `/v1/role-model-checker` | `POST /v1/role-model-checker/run` |

---

## Completed Backend Endpoints

### 1. Manuscript Document Creation

**Endpoint**: `POST /v1/story-development/drafting/manuscript-documents`

**Request Schema** (`ManuscriptDocumentCreateRequest`):
```python
{
    "document_id": str,        # Required, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "project_id": str,         # Required, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "title": str,              # Required, max_length=500
    "content": str,            # Required, max_length=1_000_000
    "chapter_id": str | None,  # Optional, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "scene_id": str | None,    # Optional, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "current_draft_artifact_id": str | None,  # Optional, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "version": int | None,     # Optional, ge=1
}
```

**Success Response** (201 Created): `ManuscriptDocument`

**Error Responses**:
| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 400 | Invalid input | Field validation failed (e.g., ID format, length exceeded) |
| 404 | Draft not found | `current_draft_artifact_id` references non-existent draft |

**Service Method**: `DraftingService.save_manuscript_document()`

---

### 2. Draft Promotion to Manuscript

**Endpoint**: `POST /v1/story-development/drafting/promote-draft`

**Request Schema** (`PromoteDraftToManuscriptRequest`):
```python
{
    "project_id": str,         # Required
    "document_id": str,        # Required
    "draft_artifact_id": str,  # Required
    "title": str | None,       # Optional - overrides draft title if provided
    "chapter_id": str | None,  # Optional
    "scene_id": str | None,    # Optional
    "version": int | None,     # Optional, defaults to 1
}
```

**Success Response** (201 Created): `ManuscriptDocument`

**Error Responses**:
| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 400 | Invalid input | Field validation failed or invalid version number |
| 404 | Draft not found | `draft_artifact_id` does not exist in project |
| 409 | Conflict | Document with same `document_id` already exists for project |

**Service Method**: `DraftingService.promote_draft_to_manuscript()`

---

### 3. Review Decision Recording

**Endpoint**: `POST /v1/story-development/review/decisions`

**Request Schema** (`ReviewDecisionCreateRequest`):
```python
{
    "decision_id": str,        # Required, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "project_id": str,         # Required, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "target_kind": str,        # Required, max_length=100 (e.g., 'checker_finding', 'artifact')
    "target_id": str,          # Required, max_length=255, pattern: ^[a-zA-Z0-9_-]+$
    "decision": str,           # Required, max_length=50 ('accept' | 'reject' | 'defer' | 'escalate' | 'refine')
    "notes": str | None,       # Optional, max_length=5000
    "source_context": list[str],  # Optional, default=[]
}
```

**Success Response** (201 Created): `ReviewDecision`

**Error Responses**:
| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 400 | Invalid input | Field validation failed or invalid decision value |
| 409 | Conflict | Decision with same `decision_id` already exists for target |

**Service Method**: `ReviewRoutingService.record_review_decision()`

---

### 4. Revision Suggestion Creation

**Endpoint**: `POST /v1/story-development/drafting/revision-suggestions`

**Request Schema** (`RevisionSuggestionCreateRequest`):
```python
{
    "suggestion_id": str,      # Required
    "project_id": str,         # Required
    "target_document_id": str, # Required - manuscript document to revise
    "source_text": str,        # Required - original text being replaced
    "proposed_text": str,      # Required - new suggested text
    "rationale": str,          # Required - explanation for the suggestion
    "source_context": list[str],  # Optional, default=[]
    "status": str,             # Optional, default='REQUESTED'
}
```

**Success Response** (201 Created): `RevisionSuggestion`

**Error Responses**:
| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 400 | Invalid input | Field validation failed or empty text fields |
| 404 | Document not found | `target_document_id` does not exist in project |
| 409 | Conflict | Suggestion with same `suggestion_id` already exists |

**Service Method**: `DraftingService.create_revision_suggestion()`

---

## Frontend Updates

### Type Definitions Updated

1. **`frontend/src/types/drafting.ts`**:
   - `DraftArtifact`: Now uses backend schema fields (`artifact_id`, `status`, etc.)
   - Added `ManuscriptDocument` interface
   - Added `PromoteDraftToManuscriptRequest` interface

2. **`frontend/src/types/review.ts`**:
   - `ReviewDecision`: Updated to match backend schema
   - Added `ReviewDecisionCreateRequest` interface

### Services Updated

1. **`frontend/src/services/drafting.ts`**:
   - `getDraftArtifacts()`: Now parses response with `.items` array
   - `promoteDraftToManuscript()`: Replaces old `promoteDraft()` with real API call
   - Maintains mock mode support via `VITE_USE_MOCKS`

2. **`frontend/src/services/review.ts`**:
   - Updated paths from `/api/story-development/...` to `/story-development/...`
   - `createDecision()`: Now uses correct request schema
   - Fixed parameter name: `finding_id` → `target_id` for GET requests

### Components Updated

1. **`DraftPromotion.tsx`**:
   - Removed mock-only restriction (now works with real API)
   - Passes `projectId` to `PromotionModal`
   - Uses new `promoteDraftToManuscript()` service method

2. **`PromotionModal.tsx`**:
   - Accepts `projectId` prop
   - Calls real API via `promoteDraftToManuscript()`
   - Updated field references to match new schema

3. **`DraftPreview.tsx`**:
   - Updated field names: `state` → `status`, `id` → `artifact_id`
   - Removed provider/model fields (not in backend schema)
   - Shows source plan count instead

4. **`DecisionForm.tsx`**:
   - Uses real `createDecision()` service method
   - Updated field names: `decision_action` → `decision`, `rationale` → `notes`
   - Removed mock mode banner
   - Added toast notifications for success/error

---

## Testing Instructions

### Start Backend Server

```bash
cd f:/dev/narrative-engine
python -m uvicorn app.main:app --reload --port 8000
```

### Test Endpoints with curl

#### 1. Create a Draft Artifact (prerequisite)

```bash
curl -X POST http://localhost:8000/v1/story-development/drafting/draft-artifacts \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "draft-001",
    "project_id": "project-1",
    "title": "Test Chapter",
    "content": "This is test content...",
    "status": "DRAFT"
  }'
```

#### 2. Promote Draft to Manuscript

```bash
curl -X POST http://localhost:8000/v1/story-development/drafting/promote-draft \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "project-1",
    "document_id": "doc-001",
    "draft_artifact_id": "draft-001",
    "title": "Chapter 1 (Promoted)"
  }'
```

#### 3. Create Review Decision

```bash
curl -X POST http://localhost:8000/v1/story-development/review/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "decision-001",
    "project_id": "project-1",
    "target_kind": "checker_finding",
    "target_id": "finding-001",
    "decision": "accept",
    "notes": "This finding is valid"
  }'
```

#### 4. Create Revision Suggestion

```bash
curl -X POST http://localhost:8000/v1/story-development/drafting/revision-suggestions \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": "suggestion-001",
    "project_id": "project-1",
    "target_document_id": "doc-001",
    "source_text": "Original text",
    "proposed_text": "Improved text",
    "rationale": "Better clarity"
  }'
```

---

## Remaining Work

### Backend (Not Implemented)

1. **Flow Editor Endpoints**:
   - `GET /v1/story-development/flow` - get current flow definition
   - `POST /v1/story-development/flow/stages` - add stage
   - `PUT /story-development/flow/stages/{stage_id}` - update stage
   - `DELETE /story-development/flow/stages/{stage_id}` - remove stage
   - `PUT /story-development/flow/stages/reorder` - reorder stages

2. **Brainstorm/Foundation/Character/World Bible Endpoints**:
   - Services exist but no API routes implemented

3. **Flow Service Implementation**:
   - No service layer for flow management yet

### Frontend (Mock Mode Still Active)

1. Flow editor components use mock services
2. Brainstorm workspace uses mock data
3. Foundation profile uses mock data
4. Character manager uses mock data
5. World bible uses mock data

---

## Environment Variables

Frontend `.env.local`:
```bash
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_USE_MOCKS=false  # Set to true for mock mode
```

---

## Notes

- All new endpoints follow existing patterns in `app/api/story_development.py`
- Error handling returns appropriate HTTP status codes (400, 404)
- Frontend maintains backward compatibility with mock mode via `VITE_USE_MOCKS` flag
- Toast notifications added for user feedback on success/error
