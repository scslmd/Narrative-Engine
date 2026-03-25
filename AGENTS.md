# Narrative Engine - Development Guidelines

## Quick Start Commands

### Frontend (TypeScript/React)
```bash
cd frontend/src
npm run dev        # Start dev server (Vite)
npm run build      # Production build with typecheck
npm run lint       # ESLint check
npx tsc --noEmit   # Typecheck only
```

### Backend (Python/FastAPI)
```bash
# From project root
pytest             # Run all tests
pytest tests/test_smoke.py        # Run specific test file
pytest -k test_name              # Run tests matching pattern
pytest tests/test_story_branching_service.py::test_create_branch  # Single test
python -m app.main                # Start FastAPI server (via uvicorn)
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
├── frontend/src/          # Frontend React code
│   ├── components/        # React components (grouped by domain)
│   ├── services/          # API client functions
│   ├── types/             # TypeScript interfaces
│   ├── views/             # Page-level components
│   └── stores/            # Zustand state management
├── tests/                 # Python pytest suite
└── data/                  # Runtime data (gitignored)
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

**Before committing:** Ensure both frontend and backend pass their respective checks.

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Frontend import errors | Check actual folder structure; use relative paths from file location |
| TypeScript "int not assignable to str" | Backend returns int, frontend expects string - add type conversion |
| Pydantic validation errors | Use `StrictModel` for request schemas, regular `BaseModel` for responses |
| Test temp directory conflicts | Use `tmp_path` fixture, never hardcode paths |
| node_modules in git | Add to `.gitignore`, run `git reset HEAD node_modules/` |

## API Patterns

**RESTful endpoints:**
- GET `/projects` - List projects
- POST `/branches` - Create branch
- GET `/branches/{project_id}` - List branches for project
- PATCH `/branches/{branch_id}` - Update branch

**Response format:** Always return structured JSON with consistent field names matching TypeScript interfaces.
