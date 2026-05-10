# Project Maintenance Design

Date: 2026-05-04  
Status: Draft  
Type: Maintenance feature — orphan detection, history cleanup, audit log rotation, database compaction, and project deletion repair

---

## 1) Goals

1. Detect orphaned project artifacts: empty shells (no manifest), DB entries without disk directories, disk directories without DB entries.
2. Provide a safe preview-then-confirm cleanup flow via the Settings panel.
3. Fix the broken `DELETE /projects/{project_id}` contract (frontend calls it, backend doesn't have it).
4. Full project deletion removes everything: DB entries (CASCADE), disk directory, execution history, checker reports.
5. Truncate unbounded audit log (`telemetry.jsonl`) to a configurable retention limit.
6. Compact the operations database (VACUUM + ANALYZE) to reclaim fragmented space.
7. Clean up orphaned checker report files.

## 2) Non-Goals

1. Soft-delete / trash / undo mechanism.
2. Automatic periodic cleanup (e.g., cron job).
3. Bulk operations beyond what the user explicitly selects.
4. Cleaning up test runtime directories (`.tmp_test_projects/`) — handled by pytest hooks.
5. Per-project `bible.db` vacuum — those files are small and project-scoped.

---

## 3) Hard Product Decisions

1. Cleanup is explicit — user must scan, review, then confirm.
2. Cleanup is best-effort per-item — one failure doesn't abort the entire batch.
3. `DELETE /projects/{project_id}` removes everything: project DB rows, execution history, disk directory, checker reports.
4. Audit log retains last 10000 lines (configurable via `AUDIT_LOG_RETAIN_LINES` env var).
5. SQLite VACUUM is manual, triggered by user action.
6. Maintenance endpoints are guarded by the existing API key middleware.

---

## 4) API Contract (Concrete Endpoints)

### 4.1 Scan for Orphans and Accumulation

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
  ],
  "summary": {
    "audit_log_lines": 52340,
    "audit_log_retain_lines": 10000,
    "database_size_bytes": 15728640,
    "checker_report_files": 47,
    "total_jobs": 234,
    "total_checker_runs": 89
  }
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

### 4.3 Truncate Audit Log

- Method: `POST`
- Path: `/projects/maintenance/audit-log/truncate`
- Auth: API-key gate
- Request (optional):
```json
{
  "retain_lines": 10000
}
```
- Success: `200 OK`
- Body:
```json
{
  "truncated": 42340,
  "retained": 10000
}
```
- Errors:
  - `500` truncation failure (e.g., file locked)

### 4.4 Compact Database

- Method: `POST`
- Path: `/projects/maintenance/database/compact`
- Auth: API-key gate
- Success: `200 OK`
- Body:
```json
{
  "before_bytes": 15728640,
  "after_bytes": 8388608
}
```
- Errors:
  - `500` compaction failure (e.g., DB locked by another connection)

### 4.5 Delete Project (Contract Repair)

- Method: `DELETE`
- Path: `/projects/{project_id}`
- Auth: API-key gate
- Success: `200 OK`
- Body:
```json
{
  "deleted": true,
  "project_id": "3b43ee1a-541d-4a62-ba96-da1151c82f68",
  "history_removed": {
    "jobs": 12,
    "checker_runs": 3,
    "step_records": 45,
    "lineage_records": 67,
    "checker_reports": 3
  }
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
- `settings.projects_dir` — path to `data/projects/`
- `settings.operations_db_path` — operations DB path
- `settings.structured_log_filename` — audit log path
- `settings.role_model_reports_dir` — checker reports directory
- `ProjectRepository` — DB access for project queries and deletion

**Methods:**

```python
class ProjectMaintenanceError(ServiceError):
    pass

class MaintenanceScanResult(NamedTuple):
    orphaned_dirs: list[OrphanInfo]
    db_only: list[OrphanInfo]
    disk_only: list[OrphanInfo]
    summary: MaintenanceSummary

class MaintenanceSummary(NamedTuple):
    audit_log_lines: int
    audit_log_retain_lines: int
    database_size_bytes: int
    checker_report_files: int
    total_jobs: int
    total_checker_runs: int

class OrphanInfo(NamedTuple):
    project_id: str
    project_name: str | None
    kind: str  # "orphaned_dir" | "db_only" | "disk_only"
    size_bytes: int

class ProjectMaintenanceService:
    _lock = threading.Lock()

    def __init__(self, settings: Settings, repository: ProjectRepository):
        ...

    def scan_orphans(self) -> MaintenanceScanResult:
        """Scan disk and DB for orphaned artifacts and accumulation stats."""
        ...

    def cleanup(self, project_ids: list[str]) -> MaintenanceCleanupResult:
        """Remove specified orphaned projects from disk and/or DB.
        Best-effort per-item: continues on individual failures.
        """
        ...

    def delete_project(self, project_id: str) -> ProjectDeletionResult:
        """Full project deletion with cascading history cleanup:
        1. Delete project row (CASCADE to project-scoped tables)
        2. Delete jobs + children (job_logs, job_attempts, job_events)
        3. Delete checker runs + children (checker_results, etc.)
        4. Delete step records and artifact lineage for deleted runs
        5. Delete canon generation runs (source or target)
        6. Delete checker report files
        7. Remove disk directory
        """
        ...

    def truncate_audit_log(self, retain_lines: int = 10000) -> AuditLogTruncationResult:
        """Keep last N lines of telemetry.jsonl. Atomic write via temp file + os.replace()."""
        ...

    def compact_database(self) -> DatabaseCompactionResult:
        """Run VACUUM; ANALYZE; on the operations database.
        Returns before/after file size.
        """
        ...

    def cleanup_checker_reports(self, keep_run_ids: set[str] | None = None) -> CleanupResult:
        """Remove checker report files for run IDs no longer in the DB.
        If keep_run_ids is provided, only remove files NOT in that set.
        """
        ...
```

**Thread safety:** All mutation operations use `_lock` to prevent concurrent modifications.

### 5.2 Backend Schemas

**File:** `app/schemas/projects.py` (extend existing)

```python
class OrphanInfo(StrictModel):
    project_id: str
    project_name: str | None
    kind: Literal["orphaned_dir", "db_only", "disk_only"]
    size_bytes: int

class MaintenanceSummary(StrictModel):
    audit_log_lines: int
    audit_log_retain_lines: int
    database_size_bytes: int
    checker_report_files: int
    total_jobs: int
    total_checker_runs: int

class MaintenanceScanResponse(StrictModel):
    orphaned_dirs: list[OrphanInfo]
    db_only: list[OrphanInfo]
    disk_only: list[OrphanInfo]
    summary: MaintenanceSummary

class MaintenanceCleanupResponse(StrictModel):
    removed: int
    errors: list[dict[str, str]]

class AuditLogTruncationResponse(StrictModel):
    truncated: int
    retained: int

class DatabaseCompactionResponse(StrictModel):
    before_bytes: int
    after_bytes: int

class ProjectDeletionResponse(StrictModel):
    deleted: bool
    project_id: str
    history_removed: dict[str, int]
```

### 5.3 Backend API Routes

**File:** `app/api/projects.py` (extend existing router)

Five new routes added to the existing projects router. Route ordering is critical — parameterized routes must come AFTER specific paths:

```python
# Maintenance routes (before parameterized routes to avoid conflicts)
@router.get("/maintenance/scan")
async def maintenance_scan(...):
    ...

@router.post("/maintenance/cleanup")
async def maintenance_cleanup(...):
    ...

@router.post("/maintenance/audit-log/truncate")
async def truncate_audit_log(...):
    ...

@router.post("/maintenance/database/compact")
async def compact_database(...):
    ...

# Project-specific routes (after maintenance routes)
@router.delete("/{project_id}")
async def delete_project(project_id: str, ...):
    ...
```

### 5.4 Persistence Layer Changes

**File:** `app/persistence/projects.py`

New method for history cleanup:

```python
def delete_project_history(self, project_id: str) -> dict[str, int]:
    """Delete all execution history for a project.
    Returns dict of table_name -> rows_deleted counts.
    """
    with connect(self.db_path) as conn:
        # Delete jobs for this project (CASCADE to job_logs, job_attempts, job_events)
        conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
        
        # Delete checker runs (CASCADE to checker_results, checker_run_attempts, checker_run_events)
        conn.execute("DELETE FROM checker_runs WHERE project_id = ?", (project_id,))
        
        # Delete step records and lineage for orphaned run IDs
        # (run_ids that were in deleted jobs/checker_runs)
        conn.execute("DELETE FROM step_records WHERE run_id IN (...)")
        conn.execute("DELETE FROM artifact_lineage WHERE run_id IN (...)")
        
        # Delete canon generation runs (source or target)
        conn.execute("DELETE FROM canon_generation_runs WHERE source_project_id = ? OR target_project_id = ?", (project_id, project_id))
        # CASCADE to canon_generation_packets, generation_gate_results
        
        conn.commit()
        return counts
```

Note: The existing `delete_project()` method stays DB-only (project row + CASCADE). History cleanup is a separate operation in the service layer.

### 5.5 Frontend Service

**File:** `frontend/src/services/maintenance.ts`

```typescript
import api from '../lib/api';
import type {
  MaintenanceScanResult,
  MaintenanceCleanupResult,
  AuditLogTruncationResult,
  DatabaseCompactionResult,
} from '../types/maintenance';

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

export async function truncateAuditLog(
  retainLines?: number,
): Promise<AuditLogTruncationResult> {
  const body = retainLines ? { retain_lines: retainLines } : {};
  const response = await api.post('/projects/maintenance/audit-log/truncate', body);
  return response.data;
}

export async function compactDatabase(): Promise<DatabaseCompactionResult> {
  const response = await api.post('/projects/maintenance/database/compact');
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

export interface MaintenanceSummary {
  audit_log_lines: number;
  audit_log_retain_lines: number;
  database_size_bytes: number;
  checker_report_files: number;
  total_jobs: number;
  total_checker_runs: number;
}

export interface MaintenanceScanResult {
  orphaned_dirs: OrphanInfo[];
  db_only: OrphanInfo[];
  disk_only: OrphanInfo[];
  summary: MaintenanceSummary;
}

export interface MaintenanceCleanupResult {
  removed: number;
  errors: Array<{ project_id: string; error: string }>;
}

export interface AuditLogTruncationResult {
  truncated: number;
  retained: number;
}

export interface DatabaseCompactionResult {
  before_bytes: number;
  after_bytes: number;
}
```

### 5.7 Frontend UI

**File:** `frontend/src/components/SettingsPanel.tsx`

New "Maintenance" section added to the existing modal, after the "Show Tooltips" section:

**Scan & Orphan Cleanup:**
1. "Scan" button — triggers `scanOrphans()`
2. Loading state during scan
3. Results panel grouped by kind:
   - "Empty shells (N)" — orphaned_dirs
   - "DB entries without files (N)" — db_only
   - "Files without DB entries (N)" — disk_only
4. Item display: truncated project_id, project_name (or "Unknown"), size
5. Checkbox per item, "Select All" / "Deselect All"
6. "Clean Selected (N)" button — disabled until items selected
7. Confirmation dialog before cleanup
8. Result toast, cache invalidation

**System Summary** (from scan `summary`):
9. Audit log: "52,340 lines (retain: 10,000)" + "Truncate" button
10. Database: "15.0 MB" + "Compact" button
11. Checker reports: "47 files"
12. Jobs: "234 total" | Checker runs: "89 total"

**Actions:**
13. "Truncate Audit Log" — confirmation dialog, calls `truncateAuditLog()`
14. "Compact Database" — confirmation dialog, calls `compactDatabase()`
15. Loading spinners during long operations (VACUUM can take seconds on large DBs)

---

## 6) Data Flow

### 6.1 Scan Flow

```
User clicks "Scan"
  → Frontend calls GET /projects/maintenance/scan
    → ProjectMaintenanceService.scan_orphans()
      → Walk data/projects/ for directories
      → For each dir: check manifest.json exists
      → Query DB for all project_ids in `projects` table
      → Compare disk vs DB sets → orphaned_dirs, db_only, disk_only
      → Count audit log lines (wc -l equivalent)
      → Get DB file size (os.path.getsize)
      → Count checker report files
      → Count total jobs, checker runs
      → Return categorized results + summary
  → Frontend renders grouped results and summary
```

### 6.2 Orphan Cleanup Flow

```
User selects items, clicks "Clean Selected"
  → Confirmation dialog
  → Frontend calls POST /projects/maintenance/cleanup { project_ids }
    → ProjectMaintenanceService.cleanup(project_ids) [locked]
      → For each project_id:
        - If db_only: repository.delete_project()
        - If disk_only / orphaned_dir: shutil.rmtree()
        - Catch per-item errors, continue
      → Return { removed, errors }
  → Frontend shows toast, invalidates project list cache, re-scans
```

### 6.3 Full Project Delete Flow

```
User calls DELETE /projects/{project_id}
  → ProjectMaintenanceService.delete_project(project_id) [locked]
    → Phase 1: Collect run IDs for this project
      → SELECT job_id FROM jobs WHERE project_id = ?
      → SELECT run_id FROM checker_runs WHERE project_id = ?
    → Phase 2: Delete execution history
      → DELETE FROM jobs WHERE project_id = ? (CASCADE)
      → DELETE FROM checker_runs WHERE project_id = ? (CASCADE)
      → DELETE FROM step_records WHERE run_id IN (collected IDs)
      → DELETE FROM artifact_lineage WHERE run_id IN (collected IDs)
      → DELETE FROM canon_generation_runs WHERE source_project_id = ? OR target_project_id = ? (CASCADE)
    → Phase 3: Delete checker report files
      → For each checker run ID: remove data/role_model_checker_runs/{id}.json
    → Phase 4: Delete project row (CASCADE to project-scoped tables)
      → DELETE FROM projects WHERE project_id = ?
    → Phase 5: Remove disk directory
      → shutil.rmtree(data/projects/{project_id}/)
    → Return { deleted, project_id, history_removed }
  → 404 if neither DB nor disk entry exists
```

### 6.4 Audit Log Truncation Flow

```
User clicks "Truncate Audit Log"
  → Confirmation dialog: "Remove 42,340 lines? Keep last 10,000."
  → Frontend calls POST /projects/maintenance/audit-log/truncate
    → ProjectMaintenanceService.truncate_audit_log(10000) [locked]
      → Read all lines from telemetry.jsonl
      → Keep last 10000 lines
      → Write to telemetry.jsonl.tmp
      → os.replace(tmp, original) — atomic on POSIX, close-enough on Windows
      → Return { truncated: 42340, retained: 10000 }
  → Frontend shows toast, re-scans for updated summary
```

### 6.5 Database Compaction Flow

```
User clicks "Compact Database"
  → Confirmation dialog: "Compact 15.0 MB database? May take several seconds."
  → Frontend calls POST /projects/maintenance/database/compact
    → ProjectMaintenanceService.compact_database() [locked]
      → Get DB file size before
      → VACUUM; ANALYZE;
      → Get DB file size after
      → Return { before_bytes, after_bytes }
  → Frontend shows toast with size reduction, re-scans
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
| Audit log file not found | Return `{ truncated: 0, retained: 0 }` — no error |
| Audit log file locked | 500 with error detail |
| VACUUM fails (DB locked by executor threads) | 500 with error detail; frontend shows error toast |
| Frontend network error | Error toast, no state change |
| Checker report file not found during cleanup | Silently skipped (file already gone) |

---

## 8) Testing Strategy

### 8.1 Backend Tests

**File:** `tests/test_project_maintenance.py`

**Orphan detection:**
- `test_scan_detects_orphaned_dirs` — creates empty dir, verifies scan finds it
- `test_scan_detects_db_only_entries` — creates DB entry without disk dir
- `test_scan_detects_disk_only_entries` — creates dir with manifest but no DB entry
- `test_scan_empty_projects_dir` — no orphans when everything is consistent
- `test_scan_summary_counts` — verifies audit log lines, DB size, checker report count

**Cleanup:**
- `test_cleanup_removes_orphaned_dirs` — verifies disk removal
- `test_cleanup_removes_db_only` — verifies DB row removal
- `test_cleanup_handles_permission_error` — mock permission denied, verifies error reporting

**Project deletion:**
- `test_delete_project_full_removal` — verifies DB + disk + history cleanup
- `test_delete_project_removes_jobs` — verifies job table cleanup
- `test_delete_project_removes_checker_runs` — verifies checker run cleanup
- `test_delete_project_removes_step_records` — verifies step record cleanup
- `test_delete_project_removes_canon_generation` — verifies canon generation cleanup
- `test_delete_project_removes_checker_reports` — verifies report file removal
- `test_delete_project_404_on_missing` — verifies 404 response

**Audit log:**
- `test_truncate_audit_log_keeps_last_n_lines` — writes 15000 lines, truncates to 10000
- `test_truncate_audit_log_empty_file` — handles empty file gracefully
- `test_truncate_audit_log_missing_file` — handles missing file gracefully
- `test_truncate_audit_log_atomic_write` — verifies temp file + replace pattern

**Database compaction:**
- `test_compact_database_reduces_size` — creates fragments, verifies VACUUM reduces size
- `test_compact_database_returns_sizes` — verifies before/after bytes

**Checker reports:**
- `test_cleanup_checker_reports_removes_orphans` — creates orphaned files, verifies cleanup

All tests use `tmp_path` for isolated project directories and temp databases.

### 8.2 Frontend Tests

**File:** `frontend/src/services/maintenance.test.ts`

- `scanOrphans returns scan result with summary` — MSW mock, verifies API call
- `cleanupOrphans sends project_ids` — MSW mock, verifies request body
- `truncateAuditLog sends retain_lines` — MSW mock, verifies optional parameter
- `compactDatabase sends empty body` — MSW mock, verifies POST
- `scanOrphans handles 500 error` — verifies error propagation

---

## 9) File Inventory

| File | Action | Description |
|------|--------|-------------|
| `app/services/project_maintenance.py` | **New** | `ProjectMaintenanceService` — scan, cleanup, delete, truncate, compact |
| `app/schemas/projects.py` | **Extend** | 7 new Pydantic models for maintenance responses |
| `app/api/projects.py` | **Extend** | 5 new routes: scan, cleanup, truncate, compact, delete |
| `app/persistence/projects.py` | **Extend** | `delete_project_history()` method |
| `app/settings.py` | **Extend** | `audit_log_retain_lines` setting (default 10000) |
| `frontend/src/types/maintenance.ts` | **New** | TypeScript interfaces for all maintenance types |
| `frontend/src/services/maintenance.ts` | **New** | 4 exported functions |
| `frontend/src/components/SettingsPanel.tsx` | **Modify** | Add Maintenance section with scan, cleanup, truncate, compact |
| `tests/test_project_maintenance.py` | **New** | ~25 backend tests |
| `frontend/src/services/maintenance.test.ts` | **New** | 5 frontend MSW tests |
| `app/main.py` | **Extend** | Add `/projects/maintenance/*` and `DELETE /projects/*` to API key gate |

---

## 10) Settings

**File:** `app/settings.py`

New setting:
```python
audit_log_retain_lines: int = 10000
```

Read from env var `AUDIT_LOG_RETAIN_LINES` with fallback to 10000.

---

## 11) Migration Path

No migration needed. This is a purely additive feature:
- New service, new endpoints, new UI section
- Existing `reconcile_projects()` at startup remains unchanged
- Existing `delete_project()` in persistence layer remains unchanged (DB-only)
- New `delete_project_history()` is called by the service layer, not by existing code
