# Project Export/Import Implementation Plan

Date: 2026-05-04
Status: Shipped (completed)
Linked spec: `docs/superpowers/specs/2026-05-04-project-export-import-design.md`

---

## Execution Rules

1. Feature is shipped. Do not re-implement.
2. Any changes should be additive (new export versions, additional validation).
3. Keep endpoint contracts stable.
4. Every endpoint change must have API tests.

---

## Shipped Tasks

### EXPIMP-001 Schemas (done)

- Goal: add strict backend schemas for export/import responses and metadata.
- Files:
  - `app/schemas/project_io.py`
  - `app/schemas/__init__.py`
- Shipped:
  - `ExportMetadata`
  - `ProjectExportSubmitResponse`
  - `ProjectExportProgressResponse`
- Verify:
  - Tests covered by service test suites

### EXPIMP-002 Export service (done)

- Goal: produce ZIP stream payload with metadata + project files + scoped ops rows.
- Files:
  - `app/services/project_export.py`
- Shipped:
  - `ProjectExportService.create_zip_stream(project_id)`
  - `ProjectExportService.get_scoped_ops_data(project_id)`
- Verify:
  - `python -m pytest tests/test_project_export_service.py -q -p no:cacheprovider` (10 tests)

### EXPIMP-003 Import service (done)

- Goal: validate ZIP, guard traversal, migrate export version, create fresh project, restore scoped rows.
- Files:
  - `app/services/project_import.py`
- Shipped:
  - `ProjectImportService.import_from_zip(zip_path, project_name)`
  - `ProjectImportService.validate_zip(zip_path)`
  - Path traversal protection
- Verify:
  - `python -m pytest tests/test_project_import_service.py -q -p no:cacheprovider` (7 tests)

### EXPIMP-004 Async job manager (done, absorbed)

- Goal: support export-import async jobs with deterministic phases.
- Files:
  - `app/services/import_jobs.py` (existing, reused)
- Shipped:
  - Uses existing `ImportJobManager` (no separate export/import job manager created)
  - Phases: `validating_zip`, `creating_project`, `importing_ops`, `completed`, `failed`
- Verify:
  - Covered by API integration tests

### EXPIMP-005 API routes (done)

- Goal: add backend routes and wire services.
- Files:
  - `app/api/projects.py`
  - `app/main.py` (API key gate)
- Shipped:
  - `POST /projects/{project_id}/export` (200 zip)
  - `POST /projects/import-export` (202 submit)
  - `GET /projects/export/{import_id}` (200 status / 404 missing)
- Verify:
  - `python -m pytest tests/test_project_export_import_api.py -q -p no:cacheprovider` (6 tests)

### EXPIMP-006 Auth gate (done)

- Goal: ensure API-key middleware protects export/import endpoints.
- Files:
  - `app/main.py`
- Shipped:
  - `/projects/import-export` guarded
  - `/projects/export/` guarded
  - `/projects/{project_id}/export` guarded
- Verify:
  - Covered by API integration tests

### EXPIMP-007 Frontend types/services (done)

- Goal: typed frontend client support for export/import endpoints.
- Files:
  - `frontend/src/types/projectIO.ts`
  - `frontend/src/services/projectIO.ts`
- Shipped:
  - `exportProject(projectId)`
  - `submitExportImport(file, projectName?)`
  - `getExportImportStatus(importId)`
- Verify:
  - `cd frontend && npm run test -- projectIO` (6 MSW tests)
  - `cd frontend && npm run typecheck`

### EXPIMP-008 Frontend export UX (done)

- Goal: add Export action in project list.
- Files:
  - `frontend/src/views/ProjectList.tsx`
- Shipped:
  - Export button per project row
  - Triggers `POST /projects/{project_id}/export` and downloads blob
- Verify:
  - `cd frontend && npm run test -- ProjectList`

### EXPIMP-009 Frontend import wizard UX (done)

- Goal: add ZIP import flow and progress polling UI.
- Files:
  - `frontend/src/components/projects/ImportProjectModal.tsx`
- Shipped:
  - ZIP picker with drag-and-drop
  - Optional project name
  - Async polling UI with phase display
  - Success navigation to new project workspace
- Verify:
  - `cd frontend && npm run test -- ImportProject`

### EXPIMP-010 End-to-end integration (covered)

- Goal: validate export->import roundtrip and data restoration.
- Files:
  - Backend integration tests cover API roundtrip
  - Frontend tests cover service layer
- Verify:
  - `python -m pytest tests/test_project_export_import_api.py -q -p no:cacheprovider`
  - `cd frontend && npm run test -- projectIO`

---

## Final Merge Gate

1. `python -m pytest tests/test_project_export_service.py tests/test_project_import_service.py tests/test_project_export_import_api.py -q -p no:cacheprovider`
2. `cd frontend && npm run lint`
3. `cd frontend && npm run typecheck`
4. `cd frontend && npm run build`
5. `cd frontend && npm run test`
