# Project Export/Import Design

Date: 2026-05-04  
Status: Shipped  
Type: New feature - bidirectional project export/import with export-schema versioning

---

## 1) Goals

1. Export any project as a complete ZIP snapshot (project files + project-scoped operations DB data).
2. Import a ZIP snapshot as a brand-new project (never overwrite or merge).
3. Version the export format and support deterministic forward migration.

## 2) Non-Goals

1. Partial restore (for example: only characters).
2. Differential/incremental backup.
3. Archive formats other than ZIP.
4. Whole-operations-DB backup/restore beyond project scope.

---

## 3) Hard Product Decisions

1. Import always creates a new `project_id`.
2. Export includes project directory + project-scoped operations data.
3. `export_version` is format-level, not app-release-level.
4. Export endpoint is synchronous streaming; import endpoint is async + poll.

---

## 4) API Contract (Concrete Endpoints)

### 4.1 Export

- Method: `POST`
- Path: `/projects/{project_id}/export`
- Auth: same API-key gate behavior as `/projects/import-story`
- Success: `200 OK`
- Response:
  - `Content-Type: application/zip`
  - `Content-Disposition: attachment; filename="{project_name}_export.zip"`
  - Body: ZIP stream
- Errors:
  - `404` project missing
  - `500` export failure

### 4.2 Import Submit

- Method: `POST`
- Path: `/projects/import-export`
- Auth: API-key gate
- Request: multipart form-data
  - `file` (required, `.zip`)
  - `project_name` (optional)
- Success: `202 Accepted`
- Body:
```json
{
  "import_id": "expimp-..."
}
```
- Errors:
  - `422` invalid archive, missing metadata, unsupported version
  - `413` body too large (MAX_BODY_SIZE)
  - `500` submit failure

### 4.3 Import Progress

- Method: `GET`
- Path: `/projects/export/{import_id}`
- Auth: API-key gate
- Success: `200 OK`
- Body:
```json
{
  "import_id": "expimp-...",
  "status": "pending|running|completed|failed",
  "phase": "validating_zip|migrating_schema|creating_project|importing_ops|completed|failed",
  "result": {
    "project_id": "new-project-id"
  },
  "error": null
}
```
- Errors:
  - `404` unknown/expired job

---

## 5) Export Archive Spec

### 5.1 Required ZIP Entries

1. `metadata.json` (required)
2. `manifest.json` (required if present in project)
3. `bible.db` (required if present)
4. `ops_db/` JSON payload files (required)

### 5.2 Metadata Schema

```json
{
  "export_version": 1,
  "engine_version": "x.y.z",
  "created_at": "2026-05-04T12:00:00Z",
  "original_project_id": "proj-...",
  "original_project_name": "Project Name"
}
```

### 5.3 Operations Data Shape

Each file under `ops_db/` is an array of row objects from a project-scoped query.

---

## 6) Deterministic Import Rules

1. Reject if `metadata.json` missing.
2. Reject if `export_version` unsupported.
3. Reject any ZIP member containing path traversal (`..`, absolute path, drive prefix).
4. Create new project first.
5. Rewrite all imported rows that contain `project_id` to the new `project_id`.
6. Preserve entity IDs unless they are project IDs.
7. Import operation is all-or-nothing per job; partial success must end in `failed`.

---

## 7) Shipped Implementation

### Backend Files

| File | Purpose |
|------|---------|
| `app/schemas/project_io.py` | `ExportMetadata`, `ProjectExportSubmitResponse`, `ProjectExportProgressResponse` |
| `app/services/project_export.py` | `ProjectExportService.create_zip_stream()`, ops DB dump |
| `app/services/project_import.py` | `ProjectImportService.import_from_zip()`, validation, migration |
| `app/api/projects.py` | 3 routes: `/{project_id}/export`, `/import-export`, `/export/{import_id}` |
| `app/main.py` | API key gate extended for export/import paths |

### Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/types/projectIO.ts` | TypeScript interfaces for export/import |
| `frontend/src/services/projectIO.ts` | `exportProject()`, `submitExportImport()`, `getExportImportStatus()` |
| `frontend/src/components/projects/ImportProjectModal.tsx` | Import wizard modal |
| `frontend/src/views/ProjectList.tsx` | Export button + import modal wiring |

### Test Files

| File | Coverage |
|------|----------|
| `tests/test_project_export_service.py` | 10 unit tests |
| `tests/test_project_import_service.py` | 7 unit tests |
| `tests/test_project_export_import_api.py` | 6 integration tests |
| `frontend/src/services/projectIO.test.ts` | 6 MSW-based tests |

### Notes

- Import uses existing `ImportJobManager` in `app/services/import_jobs.py` (no separate job manager created)
- Export filename format: `{project_name}_export.zip`
- Frontend uses `projectIO.ts` naming (not `projectExportImport.ts`)

---

## 8) Error Matrix

| Scenario | Endpoint | Expected |
|---|---|---|
| missing project | `POST /projects/{project_id}/export` | `404` |
| bad zip bytes | `POST /projects/import-export` | `422` |
| no metadata.json | `POST /projects/import-export` | `422` |
| unsupported export_version | `POST /projects/import-export` | `422` |
| unknown import_id | `GET /projects/export/{import_id}` | `404` |
| missing API key | all three endpoints | `401` |

---

## 9) Merge Gate

Do not mark complete until all pass:

1. `python -m pytest tests/test_project_export_service.py tests/test_project_import_service.py tests/test_project_export_import_api.py -q -p no:cacheprovider`
2. `cd frontend && npm run lint`
3. `cd frontend && npm run typecheck`
4. `cd frontend && npm run build`
5. `cd frontend && npm run test`

---

## 10) Implementation Notes for Local LLM Executor

1. Feature is shipped. Do not re-implement.
2. Any changes should be additive (new export versions, additional validation).
3. Keep endpoint contract stable; only additive changes after API tests are green.
