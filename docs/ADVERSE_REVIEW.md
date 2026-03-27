# Adverse Review: Narrative Engine Frontend/API Implementation

**Date**: 2026-03-25  
**Scope**: API endpoints, frontend integration, schema design, security, module architecture

---

## Executive Summary

The recent implementation of story development API endpoints and frontend integration contains **critical gaps** across multiple dimensions. While the basic CRUD operations for drafting and review are functional, significant architectural debt has been introduced that will compound as the system scales.

### Critical Issues Identified
1. **API Coverage Gap**: 70%+ of service layer functionality lacks API exposure
2. **Security Deficiencies**: No authentication, authorization, or input validation at API boundaries  
3. **Schema Inconsistencies**: Frontend types diverge from backend schemas in subtle but breaking ways
4. **Module Coupling**: Services leak persistence concerns; unclear ownership boundaries
5. **Documentation Debt**: Implementation summary lacks error cases, edge conditions, and versioning strategy

---

## 1. Documentation Deficiencies

### 1.1 API Implementation Summary.md - Critical Gaps

**Missing Content:**
- ❌ No error response schemas (400, 404, 500 cases)
- ❌ No rate limiting or pagination documentation  
- ❌ No versioning strategy for breaking changes
- ❌ No authentication/authorization requirements
- ❌ No idempotency guarantees for POST operations
- ❌ Missing request validation rules (max lengths, patterns)

**Example of Incomplete Documentation:**
```markdown
# Current (inadequate):
**Response**: `ManuscriptDocument`

# Should include:
**Success Response** (201 Created): ManuscriptDocument
**Error Responses**:
  - 400 Bad Request: Validation error with field-specific messages
  - 404 Not Found: Referenced draft artifact doesn't exist  
  - 409 Conflict: Document ID already exists for project
  - 500 Internal Server Error: Database operation failed
```

### 1.2 No OpenAPI/Swagger Documentation

The FastAPI routers lack proper schema descriptions, making it impossible to auto-generate client SDKs or interactive API documentation.

**Required:**
- Add `summary` and `description` to all endpoint functions
- Document query parameter constraints
- Add response examples for success/error cases

---

## 2. API Coverage Analysis

### 2.1 Services Without API Exposure (Critical Gap)

| Service | Methods Available | API Endpoints | Coverage |
|---------|------------------|---------------|----------|
| `brainstorm.py` | ~8 methods | 0 | **0%** ❌ |
| `foundation.py` | ~6 methods | 0 | **0%** ❌ |
| `editable_flow.py` | ~12 methods | 0 | **0%** ❌ |
| `story_knowledge.py` | ~5 methods | 0 | **0%** ❌ |
| `planning.py` | ~15 methods | 4 GET, 0 POST/PUT/DELETE | **27%** ⚠️ |
| `drafting.py` | ~10 methods | 4 GET, 3 POST | **70%** ⚠️ |
| `review_routing.py` | ~8 methods | 3 GET, 1 POST | **63%** ⚠️ |
| `story_branching.py` | ~6 methods | 2 GET, 1 POST | **50%** ⚠️ |

**Total API Coverage: ~35% of service layer functionality exposed**

### 2.2 Missing Critical Endpoints

#### Flow Editor (Frontend component exists but no backend)
```python
# Required endpoints for components/flow/FlowEditor.tsx:
GET    /story-development/flow                    # Get current flow definition
POST   /story-development/flow/stages             # Add new stage
PUT    /story-development/flow/stages/{id}        # Update stage config
DELETE /story-development/flow/stages/{id}        # Remove stage  
PUT    /story-development/flow/stages/reorder     # Reorder stages
GET    /story-development/flow/stage-templates    # Get available templates
```

#### Brainstorm Service (No API exposure)
```python
# Required for brainstorm workspace:
POST   /story-development/brainstorm/sparks       # Create idea spark
GET    /story-development/brainstorm/sparks       # List sparks by project
PUT    /story-development/brainstorm/sparks/{id}  # Update spark
DELETE /story-development/brainstorm/sparks/{id}  # Delete spark
POST   /story-development/brainstorm/premise      # Generate premise options
```

#### Foundation Profile (No API exposure)
```python
# Required for foundation profile editor:
GET    /story-development/foundation              # Get current foundation
PUT    /story-development/foundation              # Update foundation
POST   /story-development/foundation/revisions    # Create revision branch
```

### 2.3 Incomplete CRUD Operations

**Planning Service:**
- ✅ GET `/planning/scene-plans` - list scenes
- ✅ GET `/planning/chapter-packets` - list chapters  
- ❌ POST `/planning/scene-plans` - create scene (MISSING)
- ❌ PUT `/planning/scene-plans/{id}` - update scene (MISSING)
- ❌ DELETE `/planning/scene-plans/{id}` - delete scene (MISSING)

**Story Branching:**
- ✅ GET `/branches` - list branches
- ✅ POST `/branches` - create branch
- ❌ PUT `/branches/{id}` - update branch state (MISSING)
- ❌ DELETE `/branches/{id}` - archive/delete branch (MISSING)

---

## 3. Frontend/Backend Alignment Issues

### 3.1 Schema Divergences

#### Issue: DraftArtifact Status Enum Mismatch

**Backend (`app/schemas/enums.py`):**
```python
class StoryArtifactLifecycleState(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"           # ← Missing in frontend
    CANONICAL = "CANONICAL"         # ← Missing in frontend  
    SUPERSEDED = "SUPERSEDED"       # ← Different meaning than frontend
    REJECTED = "REJECTED"           # ← Missing in frontend
    ARCHIVED = "ARCHIVED"           # ← Missing in frontend
```

**Frontend (`types/drafting.ts`):**
```typescript
status: 'DRAFT' | 'REVIEW' | 'APPROVED';  // REVIEW/APPROVED don't exist in backend!
```

**Impact:** Frontend will break when receiving `CANONICAL`, `REJECTED`, or `ARCHIVED` statuses. Backend validation may reject frontend updates using invalid enum values.

#### Issue: ReviewDecision Field Name Inconsistency

**Backend Schema:**
```python
class ReviewDecision(StrictSchemaModel):
    decision_id: str
    target_kind: str  # ← Generic "target" naming
    target_id: str
    decision: str     # ← Just "decision", not "decision_action"
    notes: str | None
```

**Frontend Type (after update):**
```typescript
export interface ReviewDecision {
  decision_id: string;
  target_kind: string;
  target_id: string;
  decision: DecisionAction;  // ← Now matches, but was "decision_action" before
  notes: string | null;
}
```

**Historical Issue:** Previous frontend code used `decision_action` and `rationale`, creating confusion. The rename to match backend is correct but breaks any cached/old client code.

### 3.2 Missing Frontend Types

No TypeScript definitions for:
- `StoryFlowDefinition` / `StoryFlowStage` (flow editor)
- `BrainstormSpark` / `PremiseOption` (brainstorm workspace)
- `FoundationProfile` (foundation editor)
- `CharacterProfile` / `RelationshipEdge` (character manager)
- `WorldBibleEntry` (world bible)

### 3.3 Service Layer Anti-Patterns

**Problem: Services Return Raw Schema Objects Instead of DTOs**

```python
# Current (problematic):
@router.get("/drafting/draft-artifacts", response_model=DraftArtifactListResponse)
def list_draft_artifacts(project_id: str) -> DraftArtifactListResponse:
    return DraftArtifactListResponse(
        project_id=project_id,
        items=list(drafting_service.list_draft_artifacts(project_id)),  # ← Returns internal schema
        meta={"ordered_by": "title_asc"},
    )
```

**Issue:** Frontend is tightly coupled to backend schema structure. Any schema change requires frontend update. Should use API-specific DTOs that can evolve independently.

---

## 4. Security Analysis

### 4.1 Authentication/Authorization: NONE ❌

**Critical Finding:** Zero authentication or authorization checks exist on any endpoint.

```python
# All endpoints are completely open:
@router.post("/story-development/drafting/manuscript-documents")
def create_manuscript_document(payload: ManuscriptDocumentCreateRequest):
    # ← No @login_required, no JWT validation, no API key check
    return drafting_service.save_manuscript_document(...)
```

**Required:**
- Implement JWT-based authentication middleware
- Add project-level authorization (user must own/have access to project)
- Role-based access control (admin vs. contributor vs. viewer)

### 4.2 Input Validation: INCOMPLETE ⚠️

**Current State:** Pydantic models provide basic type validation but lack business logic constraints.

```python
class ManuscriptDocumentCreateRequest(StrictModel):
    document_id: str  # ← No max_length, no pattern validation
    content: str      # ← Could be 10MB of malicious text!
    title: str        # ← No sanitization for XSS if rendered unsanitized
```

**Missing Validations:**
- Maximum content length (prevent DoS via large payloads)
- Document ID format validation (alphanumeric + dash only?)
- SQL injection protection in IDs (even with ORM, be defensive)
- XSS prevention in text fields that may be rendered

### 4.3 No Rate Limiting ❌

All endpoints are vulnerable to:
- Brute force attacks on decision creation
- DoS via massive content uploads  
- API abuse through automated requests

**Required:** Add rate limiting middleware (e.g., 100 req/min per IP, 10 req/sec for write operations)

### 4.4 CORS Configuration Too Permissive ⚠️

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', ...],  # ← Hardcoded dev origins only
    allow_methods=['*'],                            # ← All methods allowed!
    allow_headers=['*'],                            # ← All headers allowed!
)
```

**Issues:**
- No production CORS configuration
- `allow_methods=['*']` is dangerous - should be explicit list
- Missing `expose_headers` for important response headers

---

## 5. Schema Design Problems

### 5.1 Inconsistent Naming Conventions

**Backend uses multiple styles:**
```python
# Snake_case (Python standard):
artifact_id, project_id, source_plan_ids

# But enums use SCREAMING_SNAKE:
STORY_FLOW_DEFINITION, FOUNDATION_PROFILE

# Frontend expects camelCase:
{ artifactId, projectId }  // ← Would need conversion layer!
```

**Current Workaround:** FastAPI auto-converts snake_case ↔ camelCase in JSON, but this is implicit and can break with custom serializers.

### 5.2 Missing Temporal Fields

**Backend Schemas Lack Audit Trail:**
```python
class ManuscriptDocument(StrictSchemaModel):
    document_id: str
    project_id: str
    title: str
    content: str
    version: int
    # ← No created_at, updated_at, created_by, updated_by!
```

**Impact:** Cannot track document history, blame analysis, or conflict resolution.

### 5.3 Version Field Ambiguity

```python
version: int = Field(default=1, ge=1)
```

**Questions Unanswered:**
- Is this optimistic locking version?
- Is this semantic versioning (major.minor.patch encoded as int)?
- What happens on concurrent updates?
- How does frontend handle version conflicts?

### 5.4 No Soft Delete Pattern

All schemas lack `is_deleted` or `deleted_at` fields, making data recovery impossible and requiring hard deletes that may violate referential integrity.

---

## 6. Module Delineation & Purpose Clarity

### 6.1 Service Layer Responsibilities Unclear

**Current Structure:**
```
app/services/
├── drafting.py          # Manuscript operations + draft artifacts
├── planning.py          # Scene/chapter planning  
├── review_routing.py    # Review decisions + checker findings
├── story_branching.py   # Branch management
├── story_decision_review.py  # Decision nodes (what's the difference from review_routing?)
└── editable_flow.py     # Flow configuration (no API exposure!)
```

**Ambiguities:**
1. **`review_routing.py` vs `story_decision_review.py`:** Both handle "decisions" - unclear separation of concerns
2. **`drafting.py` handles both drafts AND manuscripts:** Should manuscripts be separate?
3. **No service for flow configuration despite frontend component existing**

### 6.2 Persistence Layer Leaks Into Services

```python
# app/services/drafting.py:
class DraftingService:
    def __init__(self, repository: StoryDevelopmentRepository):
        self.repository = repository
    
    def save_manuscript_document(self, ...):
        # ← Service directly calls repository methods
        record = self.repository.upsert_manuscript_document(...)
```

**Issue:** Services are tightly coupled to specific repository implementation. Cannot swap persistence backend or add caching layer without modifying services.

**Recommended Pattern:**
```python
class DraftingService:
    def __init__(self, manuscript_repo: ManuscriptRepository, draft_repo: DraftArtifactRepository):
        # ← Dependency injection of specific repos only
        self._manuscripts = manuscript_repo
        self._drafts = draft_repo
```

### 6.3 Missing Domain Model Layer

No clear separation between:
- **Domain entities** (business objects with behavior)
- **Persistence models** (database records)  
- **API DTOs** (transfer objects for HTTP)

Currently all three are conflated in `app/schemas/story_development.py`.

---

## 7. Testing Gaps

### 7.1 No Integration Tests for New Endpoints

The four new POST endpoints have no test coverage:
```bash
# Missing test files:
tests/api/test_drafting_endpoints.py
tests/api/test_review_endpoints.py
```

### 7.2 Frontend Has No E2E Tests

No Playwright/Cypress tests verify the integration between frontend components and backend APIs.

---

## 8. Recommendations (Prioritized)

### P0 - Critical (Block Release)

1. **Add Authentication Middleware**  
   Implement JWT-based auth before exposing to any users
   
2. **Fix Enum Mismatches**  
   Align `StoryArtifactLifecycleState` between frontend/backend or add conversion layer

3. **Add Input Validation**  
   Max content lengths, ID format validation, sanitization

4. **Document Error Responses**  
   Add error schemas and examples to API documentation

### P1 - High (Before Production)

5. **Implement Rate Limiting**  
   Prevent DoS and abuse

6. **Add Missing CRUD Endpoints**  
   At minimum: flow editor, planning scene operations

7. **Separate DTOs from Schemas**  
   Create API-specific response types to decouple frontend/backend

8. **Add Audit Fields**  
   `created_at`, `updated_at`, `created_by` to all entities

### P2 - Medium (Technical Debt)

9. **Clarify Service Boundaries**  
   Document responsibility matrix for each service

10. **Add Integration Tests**  
    Test new endpoints with realistic payloads

11. **Implement Soft Deletes**  
    Add `deleted_at` pattern to prevent data loss

12. **Version the API**  
    Add `/api/v1/` prefix for future breaking changes

---

## 9. Conclusion

The current implementation provides a functional foundation but introduces significant architectural debt. The most critical issues are:

1. **Security**: No auth/authorization makes this unsafe for any production use
2. **Coverage Gap**: 65% of service functionality is inaccessible via API  
3. **Schema Drift**: Frontend/backend type mismatches will cause runtime errors
4. **Module Confusion**: Unclear ownership boundaries will complicate future development

**Recommendation:** Address P0 items before any external use. Create a technical debt backlog for P1/P2 items with assigned owners and target dates.

---

## Appendix: Files Reviewed

- `app/api/story_development.py` (666 lines)
- `app/schemas/story_development.py` (1143 lines)  
- `app/services/drafting.py`, `review_routing.py`, `editable_flow.py`, etc.
- `frontend/src/types/drafting.ts`, `review.ts`
- `frontend/src/services/drafting.ts`, `review.ts`
- `docs/API Implementation Summary.md`
