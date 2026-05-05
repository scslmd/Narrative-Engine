# Project Maintenance Design

Date: 2026-05-04  
Status: Draft  
Type: Maintenance feature — orphan detection, cleanup, and project deletion repair

---

## 1) Goals

1. Detect orphaned project artifacts: empty shells (no manifest), DB entries without disk directories, disk directories without DB entries.
2. Provide a safe preview-then-confirm cleanup flow via the Settings panel.
3. Fix the broken `DELETE /projects/{project_id}` contract (frontend calls it, backend doesn't have it).
4. Full project deletion removes both DB entries (CASCADE) and disk directory.

## 2) Non-Goals

1. Soft-delete / trash / undo mechanism.
2. Automatic periodic cleanup (e.g., cron job).
3. Bulk operations beyond what the user explicitly selects.
4. Cleaning up test runtime directories (`.tmp_test_projects/`) — handled by pytest hooks.

---

## 3) Hard Product Decisions

1. Cleanup is explicit — user must scan, review, then confirm.
2. Cleanup is best-effort per-item — one failure doesn't abort the entire batch.
3. `DELETE /projects/{project_id}` removes everything: DB rows + disk directory.
4. Maintenance endpoints are guarded by the existing API key middleware.

---

## 4) API Contract (Concrete Endpoints)

### 4.1 Scan for Orphans

- Method: `GET`
- Path: `/projects/maintenance/scan`
- Auth: API-key gate
- Success: `200 OK`
- Body:
```json
{
  "orphaned_dirs": [
    {
      "project_id": "091a511d-04de-4391-86a3-b37de692ebbf",
      "project_name": null,
      "kind": "orphaned_dir",
      "size_bytes": 12288
    }
  ],
  "db_only": [
    {
      "project_id": "abc-123",
      "project_name": "Deleted Project",
      "kind": "db_only",
      "size_bytes": 0
    }
  ],
  "disk_only": [
    {
      "project_id": "def-456",
      "project_name": "Orphaned Files",
      "kind": "disk_only",
      "size_bytes": 4096
    }
  ]
}
```
- Errors:
  - `500` scan failure (e.g., unreadable projects directory)

### 4.2 Cleanup Selected Items

- Method: `POST`
- Path: `/projects/maintenance/cleanup`
- Auth: API-key gate
- Request:
```json
{
  "project_ids": ["091a511d-...", "abc-123", "def-456"]
}
```
- Success: `200 OK`
- Body:
```json
{
  "removed": 3,
  "errors": [
    {
      "project_id": "abc-123",
      "error": "Permission denied"
    }
  ]
}
```
- Errors:
  - `422` empty or missing `project_ids`
  - `500` cleanup failure

### 4.3 Delete Project (Contract Repair)

- Method: `DELETE`
- Path: `/projects/{project_id}`
- Auth: API-key gate
- Success: `200 OK`
- Body:
```json
{
  "deleted": true,
  "project_id": "3b43ee1a-541d-4a62-ba96-da1151c82f68"
}
```
- Errors:
  - `404` project not found (no DB entry, no disk directory)
  - `500` deletion failure

---

## 5) Architecture

### 5.1 Backend Service

**File:** `app/services/project_maintenance.py`

**Class:** `ProjectMaintenanceService`

**Dependencies:**
- `ProjectService.projects_dir` — path to `data/projects/`
- `ProjectRepository` — DB access for project queries and deletion
- `settings.operations_db_path` — operations DB path

**Methods:**

```python
class ProjectMaintenanceError(ServiceError):
    pass

class ProjectMaintenanceService:
    def __init__(self, projects_dir: Path, repository: ProjectRepository):
        ...

    def scan_orphans(self) -> MaintenanceScanResult:
        """Scan disk and DB for orphaned artifacts.
        
        Returns three categories:
        - orphaned_dirs: dirs on disk with no manifest.json (empty shells)
        - db_only: DB entries with no matching disk directory
        - disk_only: dirs with manifest.json but no DB entry
        """
        ...

    def cleanup(self, project_ids: list[str]) -> MaintenanceCleanupResult:
        """Remove specified projects from disk and/or DB.
        
        Best-effort per-item: continues on individual failures.
        Returns count of successful removals and list of errors.
        """
        ...

    def delete_project(self, project_id: str) -> None:
        """Full project deletion: DB rows (CASCADE) + disk directory."""
        ...
```

**Thread safety:** Cleanup operations use a `threading.Lock()` to prevent concurrent modifications.

### 5.2 Backend Schemas

**File:** `app/schemas/projects.py` (extend existing)

```python
class OrphanInfo(StrictModel):
    project_id: str
    project_name: str | None
    kind: Literal["orphaned_dir", "db_only", "disk_only"]
    size_bytes: int

class MaintenanceScanResponse(StrictModel):
    orphaned_dirs: list[OrphanInfo]
    db_only: list[OrphanInfo]
    disk_only: list[OrphanInfo]

class MaintenanceCleanupResponse(StrictModel):
    removed: int
    errors: list[dict[str, str]]
```

### 5.3 Backend API Routes

**File:** `app/api/projects.py` (extend existing router)

Three new routes added to the existing projects router:

```python
@router.get("/maintenance/scan")
async def maintenance_scan(maintenance_service: ProjectMaintenanceService = Depends(...)):
    ...

@router.post("/maintenance/cleanup")
async def maintenance_cleanup(
    request: MaintenanceCleanupRequest,
    maintenance_service: ProjectMaintenanceService = Depends(...),
):
    ...

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    maintenance_service: ProjectMaintenanceService = Depends(...),
):
    ...
```

### 5.4 Persistence Layer Changes

**File:** `app/persistence/projects.py`

The existing `delete_project()` method (line 417-435) only removes DB rows. It will be enhanced to also accept an optional `projects_dir` parameter for filesystem cleanup:

```python
def delete_project(self, project_id: str, projects_dir: Path | None = None) -> None:
    """Delete project from DB (CASCADE). Optionally remove disk directory."""
    projection = self.get_project_projection(project_id)
    if projection is None:
        raise KeyError(project_id)
    with connect(self.db_path) as connection:
        connection.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        connection.commit()
```

Note: Disk cleanup is handled by the service layer, not persistence. The persistence method stays DB-only.

### 5.5 Frontend Service

**File:** `frontend/src/services/maintenance.ts`

```typescript
import api from '../lib/api';
import type { MaintenanceScanResult, MaintenanceCleanupResult } from '../types/maintenance';

export async function scanOrphans(): Promise<MaintenanceScanResult> {
  const response = await api.get('/projects/maintenance/scan');
  return response.data;
}

export async function cleanupOrphans(
  projectIds: string[],
): Promise<MaintenanceCleanupResult> {
  const response = await api.post('/projects/maintenance/cleanup', { project_ids: projectIds });
  return response.data;
}
```

### 5.6 Frontend Types

**File:** `frontend/src/types/maintenance.ts`

```typescript
export interface OrphanInfo {
  project_id: string;
  project_name: string | null;
  kind: 'orphaned_dir' | 'db_only' | 'disk_only';
  size_bytes: number;
}

export interface MaintenanceScanResult {
  orphaned_dirs: OrphanInfo[];
  db_only: OrphanInfo[];
  disk_only: OrphanInfo[];
}

export interface MaintenanceCleanupResult {
  removed: number;
  errors: Array<{ project_id: string; error: string }>;
}
```

### 5.7 Frontend UI

**File:** `frontend/src/components/SettingsPanel.tsx`

New "Maintenance" section added to the existing modal, after the "Show Tooltips" section:

1. **Scan button** — "Scan for Orphans" triggers `scanOrphans()`
2. **Loading state** — spinner during scan
3. **Results panel** — grouped by kind:
   - "Empty shells (N)" — orphaned_dirs
   - "DB entries without files (N)" — db_only
   - "Files without DB entries (N)" — disk_only
4. **Item display** — truncated project_id, project_name (or "Unknown"), size
5. **Selection** — checkbox per item, "Select All" / "Deselect All"
6. **Clean button** — "Clean Selected (N)" — disabled until items selected
7. **Confirmation** — modal confirmation dialog before cleanup
8. **Result toast** — success with count, or warning with error count
9. **Cache invalidation** — invalidate project list query after cleanup

---

## 6) Data Flow

### 6.1 Scan Flow

```
User clicks "Scan for Orphans"
  → Frontend calls GET /projects/maintenance/scan
    → ProjectMaintenanceService.scan_orphans()
      → Walk data/projects/ for directories
      → For each dir: check manifest.json exists
      → Query DB for all project_ids in `projects` table
      → Compare disk vs DB sets
      → Return categorized results
  → Frontend renders grouped results with checkboxes
```

### 6.2 Cleanup Flow

```
User selects items, clicks "Clean Selected"
  → Confirmation dialog
  → Frontend calls POST /projects/maintenance/cleanup { project_ids }
    → ProjectMaintenanceService.cleanup(project_ids)
      → For each project_id:
        - If db_only: call repository.delete_project()
        - If disk_only / orphaned_dir: shutil.rmtree()
        - Catch per-item errors, continue
      → Return { removed, errors }
  → Frontend shows toast, invalidates project list cache
```

### 6.3 Delete Project Flow

```
User calls DELETE /projects/{project_id}
  → ProjectMaintenanceService.delete_project(project_id)
    → Check if project exists in DB or on disk
    → If DB entry: repository.delete_project() (CASCADE)
    → If disk directory: shutil.rmtree()
    → Return { deleted: true, project_id }
  → 404 if neither DB nor disk entry exists
```

---

## 7) Error Handling

| Scenario | Behavior |
|----------|----------|
| Projects directory unreadable | 500, scan fails with error message |
| Individual cleanup item fails (permissions, in-use) | Per-item error in `errors` list, cleanup continues |
| DB connection error during delete | Wrapped as `ProjectMaintenanceError`, returned as 500 |
| DELETE on non-existent project | 404 with detail message |
| Empty `project_ids` in cleanup request | 422 validation error |
| Frontend network error | Error toast, no state change |

---

## 8) Testing Strategy

### 8.1 Backend Tests

**File:** `tests/test_project_maintenance.py`

- `test_scan_detects_orphaned_dirs` — creates empty dir, verifies scan finds it
- `test_scan_detects_db_only_entries` — creates DB entry without disk dir
- `test_scan_detects_disk_only_entries` — creates dir with manifest but no DB entry
- `test_cleanup_removes_orphaned_dirs` — verifies disk removal
- `test_cleanup_removes_db_only` — verifies DB row removal
- `test_cleanup_handles_permission_error` — mock permission denied, verifies error reporting
- `test_delete_project_full_removal` — verifies DB + disk cleanup
- `test_delete_project_404_on_missing` — verifies 404 response
- `test_scan_empty_projects_dir` — no orphans when everything is consistent

All tests use `tmp_path` for isolated project directories.

### 8.2 Frontend Tests

**File:** `frontend/src/services/maintenance.test.ts`

- `scanOrphans returns scan result` — MSW mock, verifies API call
- `cleanupOrphans sends project_ids` — MSW mock, verifies request body
- `scanOrphans handles 500 error` — verifies error propagation

---

## 9) File Inventory

| File | Action | Description |
|------|--------|-------------|
| `app/services/project_maintenance.py` | **New** | `ProjectMaintenanceService` class |
| `app/schemas/projects.py` | **Extend** | `OrphanInfo`, `MaintenanceScanResponse`, `MaintenanceCleanupResponse` |
| `app/api/projects.py` | **Extend** | 3 new routes: scan, cleanup, delete |
| `frontend/src/types/maintenance.ts` | **New** | TypeScript interfaces |
| `frontend/src/services/maintenance.ts` | **New** | `scanOrphans`, `cleanupOrphans` |
| `frontend/src/components/SettingsPanel.tsx` | **Modify** | Add Maintenance section |
| `tests/test_project_maintenance.py` | **New** | Backend tests |
| `frontend/src/services/maintenance.test.ts` | **New** | Frontend tests |
| `app/main.py` | **Extend** | Add maintenance endpoints to API key gate (if needed) |

---

## 10) Migration Path

No migration needed. This is a purely additive feature:
- New service, new endpoints, new UI section
- Existing `reconcile_projects()` at startup remains unchanged
- Existing `delete_project()` in persistence layer remains unchanged (DB-only)
