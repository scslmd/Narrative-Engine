# Project Export/Import Executor Checklist

Date: 2026-05-04  
Scope: Offline/local-LLM deterministic execution tracker  
References:
- `docs/superpowers/specs/2026-05-04-project-export-import-design.md`
- `docs/superpowers/plans/2026-05-04-project-export-import.md`

---

## How to use

1. Execute one task at a time.
2. Run the task verify command.
3. Mark checkbox only when verify passes.
4. Record commit SHA for each completed task.

---

## Task Tracker

- [ ] EXPIMP-001 Schemas complete
  - Verify: `python -m pytest tests/test_project_export_import_schemas.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-002 Export service complete
  - Verify: `python -m pytest tests/test_project_export_service.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-003 Import service complete
  - Verify: `python -m pytest tests/test_project_import_service.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-004 Async job integration complete
  - Verify: `python -m pytest tests/test_project_export_import_jobs.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-005 API routes complete
  - Verify: `python -m pytest tests/test_project_export_import_api.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-006 Auth gate complete
  - Verify: `python -m pytest tests/test_project_export_import_auth.py -q -p no:cacheprovider`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-007 Frontend types/services complete
  - Verify:
    - `cd frontend && npm run test -- projectExportImport`
    - `cd frontend && npm run typecheck`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-008 Frontend export UX complete
  - Verify: `cd frontend && npm run test -- ProjectList`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-009 Frontend import UX complete
  - Verify: `cd frontend && npm run test -- ProjectImport`
  - Commit SHA:
  - Notes:

- [ ] EXPIMP-010 End-to-end complete
  - Verify:
    - `python -m pytest tests/test_project_export_import_e2e.py -q -p no:cacheprovider`
    - `cd frontend && npm run test -- ProjectImport ProjectList`
  - Commit SHA:
  - Notes:

---

## Final Gate

- [ ] Backend export/import full test set passed
  - `python -m pytest tests/test_project_export_import_schemas.py tests/test_project_export_service.py tests/test_project_import_service.py tests/test_project_export_import_jobs.py tests/test_project_export_import_api.py tests/test_project_export_import_auth.py tests/test_project_export_import_e2e.py -q -p no:cacheprovider`

- [ ] Frontend lint passed
  - `cd frontend && npm run lint`

- [ ] Frontend typecheck passed
  - `cd frontend && npm run typecheck`

- [ ] Frontend build passed
  - `cd frontend && npm run build`

- [ ] Frontend full tests passed
  - `cd frontend && npm run test`

Release-ready commit SHA:
Release notes summary:
