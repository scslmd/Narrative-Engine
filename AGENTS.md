# Narrative Engine - Development Guidelines

## Quick Start Commands

### Frontend (TypeScript/React)
```bash
cd frontend
npm run dev        # Start Vite dev server on port 5173
npm run build      # Production build with typecheck
npm run typecheck  # TypeScript check only (no emit)
npm run lint       # ESLint check
```

### Backend (Python/FastAPI)
```bash
# From project root
pytest             # Run all tests
pytest tests/test_smoke.py        # Run specific test file
pytest -k test_name              # Run tests matching pattern
pytest tests/test_story_branching_service.py::test_create_branch  # Single test
python -m app.main                # Start FastAPI server (via uvicorn)

# Security & Reliability Tests
pytest tests/test_input_validation.py   # SEC-01: Input validation (39 tests)
pytest tests/test_authentication.py     # SEC-02: API key auth (13 tests)
pytest tests/test_authorization.py      # SEC-03: Authorization (13 tests)
pytest tests/test_circuit_breaker.py    # REL-01: Circuit breaker (17 tests)
pytest tests/test_idempotency.py        # REL-02: Idempotency keys (14 tests)
pytest tests/test_backup.py             # REL-04: Backup/restore (12 tests)

# API Key Management
curl -X POST http://localhost:8000/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "test-key", "permissions": ["read", "write"]}'
# Response includes full_key (save this! only shown once)

curl -X GET http://localhost:8000/v1/auth/keys \
  -H "Authorization: Bearer {prefix}.{secret}"

curl -X DELETE http://localhost:8000/v1/auth/keys/{prefix} \
  -H "Authorization: Bearer {admin_key}"

# Backup Operations
curl -X POST http://localhost:8000/v1/backup/create \
  -H "Content-Type: application/json" \
  -d '{"description": "pre-deployment backup"}'

curl -X GET http://localhost:8000/v1/backup/list

curl -X POST http://localhost:8000/v1/backup/{backup_id}/restore
```

## Project Structure

```
narrative-engine/
├── app/                    # Backend Python code
│   ├── api/               # FastAPI routers
│   ├── services/          # Business logic
│   ├── persistence/       # Database access
│   ├── schemas/           # Pydantic models
│   └── main.py           # App entry point
├── frontend/              # Frontend Vite + React app (root level)
│   ├── package.json       # NPM dependencies and scripts
│   ├── vite.config.ts     # Vite configuration
│   ├── tsconfig.json      # TypeScript configuration
│   ├── tailwind.config.js # Tailwind CSS configuration
│   ├── index.html         # HTML entry point
│   └── src/               # Frontend React source code
│       ├── components/    # React components (grouped by domain)
│       ├── services/      # API client functions
│       ├── types/         # TypeScript interfaces
│       ├── views/         # Page-level components
│       ├── stores/        # Zustand state management
│       ├── hooks/         # Custom React hooks
│       └── lib/           # Utility libraries
├── tests/                 # Python pytest suite
└── data/                  # Runtime data (gitignored)
```

**Frontend Quick Start:**
```bash
cd frontend
npm run dev        # Start Vite dev server on port 5173
npm run build      # Production build with TypeScript check
npm run lint       # ESLint check
```

## Code Style Guidelines

### Frontend (TypeScript/React)

**Imports:** Use relative paths, group in order: React → external libs → types → services → components
```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { getBranches } from '../../services/branches';
import { BranchCard } from './BranchCard';
```

**Types:** Prefer `interface` for component props, `type` for unions/tuples. Use snake_case to match backend API:
```tsx
export interface StoryBranch {
  branch_id: string;
  state: 'active' | 'merged' | 'archived';
}
```

**Components:** Functional components with explicit typing. Export named functions:
```tsx
interface BranchListProps {
  projectId: string;
}

export function BranchList({ projectId }: BranchListProps) {
  // implementation
}
```

**State Management:** Use React Query for server state, Zustand for client state. Always invalidate queries on mutations:
```tsx
const mutation = useMutation({
  mutationFn: (id: string) => updateBranch(id),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['branches'] }),
});
```

**Error Handling:** Use try/catch for local operations, let React Query handle API errors. Show user-friendly messages:
```tsx
try {
  await mutation.mutateAsync(data);
} catch (error) {
  toast.error('Failed to save branch');
}
```

### Backend (Python/FastAPI)

**Imports:** Follow standard order: future → stdlib → third-party → local. Always use `from __future__ import annotations`:
```python
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import httpx

from app.schemas import StoryBranch
from app.persistence import Repository
```

**Type Hints:** Use modern syntax (`list[str]` not `List[str]`). Be explicit with return types:
```python
def list_branches(self, project_id: str) -> tuple[StoryBranch, ...]:
    pass
```

**Error Handling:** Create specific exception classes per service. Wrap lower-level exceptions:
```python
class StoryBranchingNotFoundError(StoryBranchingServiceError):
    pass

try:
    record = self.repository.get_branch(branch_id)
except KeyError as exc:
    raise StoryBranchingNotFoundError(branch_id) from exc
```

**Pydantic Models:** Inherit from `StrictModel` for API schemas (forbids extra fields):
```python
class BranchCreateRequest(StrictModel):
    project_id: str
    branch_name: str
```

**Naming Conventions:**
- Services: `*Service` class, `*NotFoundError`, `*ValidationError` exceptions
- Routers: `build_*_router()` factory functions
- Variables: snake_case for Python, match API field names exactly

## Testing Patterns

### Backend Tests
- Use `tmp_path` fixture for isolated test directories
- Use `TestClient(build_app())` for integration tests
- Poll async operations with terminal status checks
- Name tests: `test_<component>_<action>_<expected_result>`

```python
def test_create_branch(tmp_path):
    client = TestClient(build_app())
    response = client.post('/branches', json={...})
    assert response.status_code == 201
```

### Frontend Testing
- Mock API calls with React Query's queryClient
- Test component rendering and user interactions
- Use TypeScript for type-safe test code

## Build Verification

**Always run after changes:**
1. Frontend: `npm run build` (catches TS errors, unused vars)
2. Backend: `pytest -x` (stop on first failure)
3. Security & Reliability: `pytest tests/test_input_validation.py tests/test_authentication.py tests/test_authorization.py tests/test_circuit_breaker.py tests/test_idempotency.py tests/test_backup.py -v`

**Before committing:** Ensure both frontend and backend pass their respective checks.

**Full test suite status (as of March 26, 2026):**
- Security features: 65 tests passing (SEC-01: 39, SEC-02: 13, SEC-03: 13)
- Reliability features: 46 tests passing (REL-01: 17, REL-02: 14, REL-03: 2, REL-04: 12, REL-06: 8)
- Total new tests: 111 passing in 5.32s

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Frontend import errors | Check actual folder structure; use relative paths from file location |
| TypeScript "int not assignable to str" | Backend returns int, frontend expects string - add type conversion |
| Pydantic validation errors | Use `StrictModel` for request schemas, regular `BaseModel` for responses |
| Test temp directory conflicts | Use `tmp_path` fixture, never hardcode paths |
| node_modules in git | Add to `.gitignore`, run `git reset HEAD node_modules/` |
| API key not working | Check format: `{prefix}.{secret}` with dot separator, no spaces |
| Authorization denied error | Verify user_owner_id matches resource owner OR has admin permission |
| Circuit breaker open | Wait for recovery timeout (60s) or fix underlying backend issue |
| Idempotency key conflict | Ensure payload is identical; different payloads require new keys |
| Backup restore fails | Check disk space (>10% free required), verify backup file exists |

## API Patterns

**Versioning Convention:**
All APIs use `/v1` prefix for version management:
- Base URL: `http://localhost:8000/v1/{service}/{resource}`
- Frontend env var: `VITE_API_URL=http://localhost:8000`
- All service files use: `const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'`

**RESTful endpoints:**
- GET `/v1/projects` - List projects
- POST `/v1/branches` - Create branch
- GET `/v1/story-development/drafting/draft-artifacts?project_id={id}` - List drafts
- PATCH `/v1/story-development/branches/{branch_id}` - Update branch

**Authentication:**
- Header: `Authorization: Bearer {prefix}.{secret}`
- Create key: POST `/v1/auth/keys` with `{name, permissions[], expires_in_days?}`
- Full key only returned once at creation - store securely!
- List keys: GET `/v1/auth/keys` (requires auth)
- Revoke key: DELETE `/v1/auth/keys/{prefix}` (requires admin permission)

**Authorization:**
- Permission hierarchy: `admin` > `write` > `read`
- Write includes read access automatically
- Admin bypasses all ownership checks
- Non-admin users can only access resources they own (owner_id match required)

**Idempotency:**
- Header: `Idempotency-Key: {unique-key}`
- TTL: 24 hours
- Same key + same payload = cached response returned
- Same key + different payload = 409 Conflict error

**Response format:** Always return structured JSON with consistent field names matching TypeScript interfaces.

## Security & Reliability Features

### SEC-01: Input Validation (`app/utils/input_validation.py`)
```python
from app.utils.input_validation import sanitize_string, validate_filename, limit_size

# Sanitize user input (XSS prevention)
safe_text = sanitize_string(user_input)  # Escapes HTML entities

# Validate filenames (path traversal protection)
validate_filename(filename, max_length=255)  # Raises ValidationError if invalid

# Limit payload size (DoS protection)
limit_size(payload_dict, max_bytes=5_242_880)  # 5 MB limit
```

### SEC-02: Authentication (`app/services/authentication.py`)
```python
from app.services.authentication import get_auth_service

auth = get_auth_service()

# Create API key
api_key, full_key = auth.create_key(
    name="My App",
    permissions=["read", "write"],
    expires_in_days=365,
)
# IMPORTANT: Save full_key immediately - it's only returned once!

# Validate key from request header
validated_key = auth.validate_key("abcd.xYz123...")  # Returns APIKey or None

# Revoke key
auth.revoke_key("abcd")  # True if revoked, False if not found
```

### SEC-03: Authorization (`app/services/authorization.py`)
```python
from app.services.authorization import get_authorization_service, PERMISSION_READ

authz = get_authorization_service()

# Check permission level
if authz.check_permission(["read"], PERMISSION_READ):
    print("Access granted")

# Require permission (raises AuthorizationError if denied)
authz.require_permission(user_permissions, "write")

# Resource-level authorization
if authz.check_resource_access(
    user_permissions=["read"],
    user_owner_id="user123",
    resource_owner_id="user123",  # Same owner = access granted
    required_permission="read",
):
    print("Can access this project")
```

### REL-01: Circuit Breaker (`app/services/circuit_breaker.py`)
```python
from app.services.circuit_breaker import get_circuit_breaker

circuit = get_circuit_breaker("llama.cpp")

try:
    with circuit:
        result = call_inference_backend()
except CircuitOpenError as e:
    print(f"Backend unavailable, retry in {e.recovery_time_seconds}s")
```

### REL-02: Idempotency (`app/services/idempotency.py`)
```python
from app.services.idempotency import check_idempotency, store_response

# At start of operation
should_proceed, cached_response = check_idempotency(
    idempotency_key="client-generated-uuid",
    payload_hash=hash_payload(request_data),
)

if not should_proceed:
    if cached_response is not None:
        return cached_response  # Return cached result
    else:
        raise IdempotencyError("Payload mismatch for idempotency key")

# Execute operation...
result = do_expensive_operation()

# Store response for future retries
store_response(idempotency_key, result)
```

### REL-04: Backup (`app/services/backup.py`)
```python
from app.services.backup import get_backup_service

backup = get_backup_service()

# Create backup (auto checkpoints WAL first)
backup_path = backup.create_backup(description="pre-migration")

# List backups
backups = backup.list_backups()  # Most recent first

# Restore backup (creates pre-restore backup automatically)
backup.restore_backup(backup_id)

# Delete old backup
backup.delete_backup(backup_id)
```

---

## TypeScript Build Errors - Resolution Log

### Summary
Fixed 20+ TypeScript compilation errors during frontend build on March 26, 2026. All issues related to type mismatches between API contracts and component expectations.

**Latest Build (March 26, 2026):** Fixed 19 merge-blocking tasks including routing fixes, service implementations, and type corrections. Build output: 312KB JS + 55KB CSS (gzipped: ~96KB + 10KB).

### March 26, 2026 - Merge-Blocking Fixes

#### Batch 1: Core Infrastructure
1. **jobsApi.ts** - Added `project_id` field to `JobCreateRequest` interface
2. **useJobs hook** - Fixed mutationFn signature for create job to accept phase parameter only
3. **Layout.tsx** - Changed `themeStore.setMode()` to `uiStore.add('mode', ...)` 
4. **App.tsx** - Converted workspace modes to nested routes (`/workspace/:projectId/*`)
5. **Workspace.tsx** - Removed redundant mode rendering (now handled by router)

#### Batch 2: Backend Fixes
6. **main.py** - Added `/health` to CORS exposed headers
7. **health.py** - Fixed readiness check to use `settings.operations_db_path`
8. **main.py** - Added authentication service initialization in app builder

#### Batch 3: Service Implementations
9. **RoleModelChecker.tsx** - Swapped mock for real checker service, fixed field name (`models` vs `selected_models`)
10. **flowService.ts** - Implemented real story-development endpoints with proper error handling
11. **BranchComparison.tsx** - Connected to real branch comparison API

#### Batch 4: Component Fixes
12. **StageList.tsx** - Wired up add stage callback in empty state, fixed StageKind type ('brainstorm' vs 'PLOT_OUTLINE')
13. **FindingCard.tsx** - Implemented "Jump to Source" navigation action with projectId prop
14. **ProjectList.tsx** - Added `secondary_language` form field
15. **FlowEditor.tsx** - Passed `onAddStage` prop to StageList

#### Batch 5: Cleanup
16. **DraftPromotion.tsx** - Removed unused import stub for promoteDraftToManuscript
17. **JobLaunchPanel.tsx** - Fixed hook signature to pass projectId, simplified mutate call
18. **JobLogsViewer.tsx** - Fixed to handle JobLogsResponse type properly (entries array)
19. **FindingsList.tsx** - Added required projectId prop to FindingCard

### Detailed Error Log (Previous Fixes)

#### 1. Job Status Hook Type Narrowing Issue
**File:** `src/hooks/useJobStatus.ts:45`  
**Error:** `Property 'status' does not exist on type 'never'`  
**Cause:** TypeScript couldn't narrow the type when accessing `data?.status` in the ternary condition for `isPolling`. The `isTerminal()` helper was defined but the inline check created a type narrowing issue.  
**Fix:** Extracted `status` into a const variable before using it in the return object:
```typescript
const status = data?.status || null;
// ... then use 'status' instead of 'data?.status' in isPolling calculation
```

#### 2. DraftArtifact Type Mismatch
**File:** `src/services/mocks/draftingMock.ts`  
**Error:** Multiple errors - `Property 'id' does not exist`, `Module has no exported member 'PromotedManuscript'`  
**Cause:** Mock data used `id` field but actual type definition uses `artifact_id`. Also, `PromotedManuscript` wasn't exported from types.  
**Fix:** 
- Updated mock data to use correct field names (`artifact_id`, `project_id`, etc.)
- Added local `PromotedManuscript` interface in the mock file since it's not part of core types yet

#### 3. Scene Type Property Mismatch
**File:** `src/components/storyboard/SceneCardList.tsx:13,35`  
**Error:** `Property 'scene_id' does not exist on type 'Scene'`, `Property 'chapter_number' does not exist`  
**Cause:** Component used `scene.scene_id` and `scene.chapter_number` but Scene interface only has `id`.  
**Fix:** Changed to use `scene.id` and simplified navigation path:
```typescript
navigate(`/project/scene/${scene.id}`);
```

#### 4. Sequence Data Type Definition Missing
**File:** `src/components/SequenceViewer.tsx`, `src/lib/projectsApi.ts`  
**Error:** `Property 'beats' does not exist on type 'ProjectArtifact'`  
**Cause:** `getSequence()` returned `ProjectArtifact` but component expected a structure with `beats[]`.  
**Fix:** Created new `SequenceData` interface and updated return type:
```typescript
export interface SequenceData {
  beats: Array<{ beat_id?: string; beat_number: number; title: string; description: string; purpose?: string; emotional_tone?: string }>;
  updated_at: string;
}
```

#### 5. Manifest Data Type Definition Missing  
**File:** `src/components/ManifestViewer.tsx`, `src/lib/projectsApi.ts`  
**Error:** `Property 'constraints' does not exist on type 'ProjectArtifact'`  
**Cause:** Similar to SequenceData - manifest endpoint returns different structure than generic ProjectArtifact.  
**Fix:** Created `ManifestData` interface with proper fields including `config`, `constraints[]`, and `premise_text`.

#### 6. ReviewDecision Interface Missing Fields
**File:** `src/components/review/DecisionHistory.tsx`, `src/types/review.ts`  
**Error:** Properties `decision_action`, `rationale`, `routed_to_stage` don't exist on type 'ReviewDecision'  
**Cause:** Type definition was incomplete compared to actual API response.  
**Fix:** Updated interface:
```typescript
export interface ReviewDecision {
  decision_id: string;
  // ... other fields
  decision_action: DecisionAction;  // Changed from 'decision'
  rationale?: string;               // Added
  routed_to_stage?: string;         // Added
}
```

#### 7. Error Handling Utility Missing Functions
**File:** `src/components/Fallback.tsx`, `src/lib/errorHandling.ts`  
**Error:** Cannot find module imports, missing function exports  
**Cause:** Fallback component imported functions that didn't exist in errorHandling.ts  
**Fix:** Added missing utility functions:
```typescript
export function isNetworkError(error: unknown): boolean { ... }
export function getErrorTitle(error: unknown, statusCode?: number): string { ... }
export function getErrorMessage(error: unknown): string { ... }
```

#### 8. Import Path Errors in Fallback Component
**File:** `src/components/Fallback.tsx`  
**Error:** Cannot find module '../../types/error' (wrong relative path)  
**Cause:** Used ../../ but component is directly in components/ folder, not in a subfolder  
**Fix:** Changed to '../types/error' and '../lib/errorHandling'

#### 9. Unused Variable Warnings
**Files:** Multiple files including `FlowEditor.tsx`, `BranchList.tsx`, `DraftPromotion.tsx`  
**Error:** Variables declared but never read (TS6133)  
**Cause:** Future functionality stubs, unused imports for planned features  
**Fixes Applied:**
- Commented out unused mutation in FlowEditor with TODO note
- Used `void variableName;` pattern for intentionally unused props
- Renamed parameters with underscore prefix where appropriate

#### 10. Return Type Mismatch
**File:** `src/components/BottomUtilityLayer.tsx:43`  
**Error:** Type 'null' is not assignable to type 'ReactElement'  
**Cause:** Component declared return type as `React.ReactElement` but returns null in early exit  
**Fix:** Changed return type to `React.ReactElement | null`

#### 11. ErrorBoundary logError Call Signature
**File:** `src/components/ErrorBoundary.tsx:36`  
**Error:** Argument of type 'Error' is not assignable to parameter of type 'string'  
**Cause:** logError expects `(component: string, error: unknown, info?)` but was called with `(error, info)`  
**Fix:** Added component name as first argument: `logError('ErrorBoundary', error, errorInfo)`

#### 12. Toast Import Error
**File:** `src/components/projects/ProjectCreateForm.tsx:4`  
**Error:** Module has no default export  
**Cause:** Used `import toast from` but toast module only exports named object  
**Fix:** Changed to `import { toast } from '../../lib/toast'`

#### 13. Toast Type Definition Mismatch
**File:** `src/types/toast.ts`, `src/lib/toast.ts`  
**Error:** Property 'duration' is optional in interface but required in implementation  
**Cause:** Interface had `duration?: number` but implementation always sets it  
**Fix:** Made duration required in interface: `duration: number;`

#### 14. LogEntry fractionalSecondDigits Not Supported
**File:** `src/components/jobs/LogEntry.tsx:27`  
**Error:** Property 'fractionalSecondDigits' does not exist on type 'DateTimeFormatOptions'  
**Cause:** TypeScript lib definitions don't include this newer Intl feature  
**Fix:** Removed the option (milliseconds not critical for log display)

#### 15. JobMonitor Hook Return Type Mismatch
**File:** `src/components/jobs/JobMonitor.tsx`, `src/hooks/useJobStatus.ts`  
**Error:** Properties 'currentPhase', 'currentStep' don't exist on hook return type  
**Cause:** Hook returned camelCase properties but interface used snake_case names  
**Fix:** Updated UseJobStatusResult interface to use consistent camelCase:
```typescript
interface UseJobStatusResult {
  // ... other fields
  currentStep: string | null;    // Changed from current_step
  currentPhase: string | null;   // Changed from current_phase
  attemptNumber: number | null;  // Changed from attempt_number
}
```

#### 16. Vite Build Path Resolution Error
**File:** `index.html`, `vite.config.ts`  
**Error:** Rollup failed to resolve import "/main.tsx"  
**Cause:** index.html used absolute path `/main.tsx` which doesn't work in build mode  
**Fixes Applied:**
- Changed index.html script src from `/main.tsx` to `./src/main.tsx`
- Added path alias configuration in vite.config.ts for '@' imports

### Build Verification Command
```bash
cd frontend && npm run build
# Output: ✓ built in ~42s (312KB JS + 54KB CSS, gzipped: ~96KB + 10KB)
```

### Lessons Learned
1. **Type definitions must match API contracts exactly** - snake_case from backend should be preserved in TypeScript interfaces
2. **Mock data must use correct field names** - Don't assume `id` when the type uses `artifact_id` or similar
3. **Create specific types for different endpoints** - Not all project artifacts have the same structure
4. **Test builds catch issues linting misses** - Always run `npm run build` after changes, not just `npm run lint`
5. **Vite path resolution differs between dev and prod** - Use relative paths in index.html, configure aliases properly
