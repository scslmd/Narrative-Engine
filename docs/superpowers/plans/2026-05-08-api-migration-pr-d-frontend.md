# API Migration PR-D: Frontend Endpoint Migration to /v1 Implementation Plan
Status: Completed (2026-05-09)

Completion notes:
- Frontend service layer is canonical `/v1` for migrated families.
- `/story-development/*` and `/role-model-checker/*` frontend references were synchronized to `/v1/story-development/*` and `/v1/role-model-checker/*`.
- Service test mocks were updated accordingly.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all frontend service calls from legacy unversioned endpoints (`/projects`, `/auth`, `/backup`, `/health`) to canonical `/v1` paths, update test mocks, and verify zero legacy references remain in the production service layer.

**Architecture:** Scan all files under `frontend/src/services/` and `frontend/src/lib/` for endpoint strings. Replace legacy paths with their `/v1` counterparts. Update MSW handlers in test setup to match canonical routes. Verify with regex grep commands that no legacy patterns remain.

**Tech Stack:** TypeScript, Vite, React, Axios, MSW (Mock Service Worker), Vitest.

**Cross-plan dependencies:** Depends on PR-B completing (needs `/v1` routes to exist on the backend). Can run parallel with PR-C.

---

## Task 014: Frontend Endpoint Inventory Script

**Purpose:** Determine all frontend route references across service files and test mocks.

**Write scope:**
- `scripts/frontend_endpoint_inventory.py` (new)
- `docs/api-migration/frontend_endpoint_inventory.csv` (generated output)

**Steps:**

- [ ] Create `scripts/frontend_endpoint_inventory.py`:

```python
"""Scan frontend service files for API endpoint references."""
from __future__ import annotations

import csv
import re
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
frontend_services = project_root / "frontend" / "src" / "services"
frontend_lib = project_root / "frontend" / "src" / "lib"
output_path = project_root / "docs" / "api-migration" / "frontend_endpoint_inventory.csv"

# Pattern to match API calls: api.get('/path'), api.post("/path"), etc.
endpoint_pattern = re.compile(
    r"""api\.(?:get|post|patch|put|delete|head)\(\s*['"`]([^'`"\s]+)['"`]""",
)

# Also match template literal endpoints: api.get(`...`)
template_pattern = re.compile(
    r"""api\.(?:get|post|patch|put|delete|head)\(\s*`([^`]+)`""",
)


def scan_file(file_path: Path) -> list[dict]:
    """Extract endpoint references from a TypeScript file."""
    entries = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return entries

    # Find the function context for each match
    lines = content.split("\n")
    current_function = None

    for i, line in enumerate(lines, 1):
        # Track function declarations
        func_match = re.search(r"export\s+async\s+function\s+(\w+)", line)
        if not func_match:
            func_match = re.search(r"(const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(", line)
        if func_match:
            current_function = func_match.group(2)

        # Match string-based endpoints
        for m in endpoint_pattern.finditer(line):
            path_template = m.group(1)
            entries.append({
                "file": str(file_path.relative_to(project_root)),
                "line": i,
                "function": current_function or "(module-level)",
                "endpoint": path_template,
                "is_v1": path_template.startswith("/v1"),
            })

        # Match template literal endpoints
        for m in template_pattern.finditer(line):
            path_template = m.group(1)
            entries.append({
                "file": str(file_path.relative_to(project_root)),
                "line": i,
                "function": current_function or "(module-level)",
                "endpoint": path_template,
                "is_v1": "/v1" in path_template,
            })

    return entries


def main() -> None:
    all_entries = []

    # Scan service files
    for pattern in ("*.ts", "*.tsx"):
        for file_path in sorted(frontend_services.glob(pattern)):
            if file_path.suffix == ".test.ts" or file_path.suffix == ".test.tsx":
                continue  # Skip test files — inventory production code only
            all_entries.extend(scan_file(file_path))

    # Scan lib files
    for file_path in sorted(frontend_lib.glob("*.ts")):
        all_entries.extend(scan_file(file_path))

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "line", "function", "endpoint", "is_v1"])
        writer.writeheader()
        writer.writerows(all_entries)

    v1_count = sum(1 for e in all_entries if e["is_v1"])
    legacy_count = sum(1 for e in all_entries if not e["is_v1"])
    print(f"Total endpoints: {len(all_entries)}")
    print(f"  /v1 canonical: {v1_count}")
    print(f"  Legacy (unversioned): {legacy_count}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] Run the inventory script: `python scripts/frontend_endpoint_inventory.py`
- [ ] Verify output:

```powershell
$csv = Import-Csv docs/api-migration/frontend_endpoint_inventory.csv; Write-Host "Total entries: $($csv.Count)"; $legacy = ($csv | Where-Object { $_.is_v1 -eq 'False' }).Count; Write-Host "Legacy endpoints to migrate: $legacy"
```

**Acceptance criteria:**
- `docs/api-migration/frontend_endpoint_inventory.csv` exists with >= 50 entries.
- CSV has columns: `file`, `line`, `function`, `endpoint`, `is_v1`.
- Legacy endpoint count is accurately reported.
- Test files are excluded from the production inventory.

---

## Task 015: Frontend Service Migration to Canonical /v1

**Purpose:** Eliminate legacy endpoint usage from all production service files.

**Write scope:**
- `frontend/src/services/projects.ts` (modify)
- `frontend/src/services/health.ts` (modify — if it calls unversioned /health, leave as-is per policy)
- `frontend/src/services/storyImport.ts` (modify)
- `frontend/src/services/patternExtraction.ts` (modify)
- All other service files under `frontend/src/services/` that reference legacy paths

**Steps:**

- [ ] For each legacy endpoint identified in the inventory, update the path to its `/v1` counterpart. The migration map:

| Legacy Path | New /v1 Path |
|---|---|
| `/projects` | `/v1/projects` |
| `/projects/create` | `/v1/projects/create` |
| `/projects/{id}` | `/v1/projects/{id}` |
| `/projects/{id}/manifest` | `/v1/projects/{id}/manifest` |
| `/projects/{id}/sequence` | `/v1/projects/{id}/sequence` |
| `/projects/{id}/chapter-1` | `/v1/projects/{id}/chapter-1` |
| `/projects/import-story` | `/v1/projects/import-story` |
| `/projects/import/{id}` | `/v1/projects/import/{id}` |
| `/projects/import-patterns` | `/v1/projects/import-patterns` |
| `/projects/{id}/extract-patterns` | `/v1/projects/{id}/extract-patterns` |
| `/projects/maintenance/*` | `/v1/projects/maintenance/*` |
| `/auth/keys` | `/v1/auth/keys` |
| `/auth/keys/{prefix}` | `/v1/auth/keys/{prefix}` |
| `/backup/create` | `/v1/backup/create` |
| `/backup/restore/{id}` | `/v1/backup/restore/{id}` |
| `/backup/list` | `/v1/backup/list` |
| `/backup/latest` | `/v1/backup/latest` |
| `/backup/{id}` | `/v1/backup/{id}` |
| `/models` | `/v1/models` |

- [ ] Example migration for `frontend/src/services/projects.ts`:

```typescript
// Before:
const response = await api.get('/projects');
// After:
const response = await api.get('/v1/projects');

// Before:
const response = await api.post('/projects/create', data);
// After:
const response = await api.post('/v1/projects/create', data);

// Before:
await api.delete(`/projects/${projectId}`);
// After:
await api.delete(`/v1/projects/${projectId}`);
```

- [ ] Apply the same pattern to all service files. Use find-and-replace with care:
  - `/projects` -> `/v1/projects` (in `api.get/post/put/delete/patch` calls only)
  - `/auth` -> `/v1/auth`
  - `/backup` -> `/v1/backup`
  - `/models` -> `/v1/models`

- [ ] Health endpoints (`/health/*`) are explicitly exempted — do NOT change them to `/v1/health`.

- [ ] Verify no legacy endpoint strings remain in production service layer:

```powershell
# Check for non-/v1 paths in api.*() calls within services and lib
$pattern = 'api\.(get|post|patch|put|delete)\(\s*[`'"'"'"]/(?!v1)(projects|auth|backup|models)'; $results = rg -n "$pattern" frontend/src/services frontend/src/lib --type ts --type tsx; if ($results) { Write-Host "FAIL: Legacy endpoints found:"; Write-Host $results; exit 1 } else { Write-Host "No legacy api.*() calls in services/lib - PASS" }

# Check for raw API_BASE, fetch(), or bare axios() usage
$pattern2 = '(API_BASE|fetch\(|axios\.(get|post|patch|put|delete)\(\s*[`'"'"'"]/(?!v1)(projects|auth|backup|models))'; $results2 = rg -n "$pattern2" frontend/src/services frontend/src/lib --type ts --type tsx; if ($results2) { Write-Host "FAIL: Raw API patterns found:"; Write-Host $results2; exit 1 } else { Write-Host "No raw API_BASE/fetch/axios patterns - PASS" }
```

- [ ] Run frontend typecheck and tests:

```powershell
cd frontend; npm run typecheck; npm run test
```

**Acceptance criteria:**
- Zero matches from the verification grep commands (exit code 1 = no matches).
- All `api.get/post/put/delete/patch` calls in `frontend/src/services/` and `frontend/src/lib/` use `/v1` paths for projects, auth, backup, and models endpoints.
- Health service files still call `/health/*` (exempted).
- `npm run typecheck` passes with 0 errors.
- `npm run test` passes with 0 new failures.

---

## Task 016: Frontend Tests & Mocks Migration

**Purpose:** Align all test fixtures, MSW handlers, and mock data with canonical `/v1` API routes.

**Write scope:**
- `frontend/src/**/*.test.ts*` (modify — update mocked endpoint paths)
- Any MSW handler files or test setup files that define route mocks

**Steps:**

- [ ] Find all test files that mock API endpoints:

```powershell
rg -n "http\.(get|post|put|patch|delete)\(" frontend/src --type ts --type tsx | Select-String "/(projects|auth|backup|models)" | ForEach-Object { $_.Filename } | Sort-Object -Unique
```

- [ ] For each test file, update MSW handler paths from legacy to `/v1`:

```typescript
// Before:
http.get('/projects', ({ request }) => {
  return HttpResponse.json(mockProjects);
});

// After:
http.get('/v1/projects', ({ request }) => {
  return HttpResponse.json(mockProjects);
});
```

- [ ] Update `vi.mock` or `jest.mock` stubs that reference legacy paths:

```typescript
// Before:
const mockApi = { get: vi.fn().mockResolvedValue({ data: mockData, status: 200 }) };
// Verify the mocked URL in assertions:
expect(mockApi.get).toHaveBeenCalledWith('/projects');

// After:
expect(mockApi.get).toHaveBeenCalledWith('/v1/projects');
```

- [ ] Run the full frontend test suite:

```powershell
cd frontend; npm run test
```

- [ ] Verify all tests pass with canonical routes:

```powershell
cd frontend; npm run test 2>&1 | Select-String "Test Files|Tests|pass|fail"
```

**Acceptance criteria:**
- `npm run test` passes with 0 failures (baseline: 554 passed per AGENTS.md).
- No MSW handler references legacy `/projects`, `/auth`, `/backup`, or `/models` paths.
- All URL assertions in tests expect `/v1` prefixed paths.
- Health-related mocks still use `/health/*` (exempted).
