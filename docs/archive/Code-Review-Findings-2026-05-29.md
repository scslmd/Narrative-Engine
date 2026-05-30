# Code Review Findings 2026-05-29

## Scope

Reviewed branch `codex/studio-workflow-progress` against `codex/main`, plus the current uncommitted working tree.

Evidence gathered:

- `git diff --stat codex/main...HEAD`
- `git diff --name-only codex/main...HEAD`
- `git diff --stat`
- `git diff --check`
- `python scripts/qc.py --verbose`
- `python -m pytest -q tests/test_story_development_research_api.py tests/test_story_development_revision_api.py tests/test_story_development_polish_api.py` -> 42 passed
- `cd frontend && npm run build` -> passed, 2049 modules
- `dotnet build narrative-launcher\NarrativeLauncher.csproj` -> passed

## Executor Contract Rules

- Treat each finding below as an independent task unless it lists an explicit dependency.
- Do not make adjacent refactors.
- Do not change files outside each task's `Allowed files`.
- If an acceptance criterion cannot be met because the current code lacks a required seam, stop with `BLOCKED_MISSING_INPUT` and document the exact missing seam.
- Validate each task with its listed commands before moving to the next task.

## Findings

### NE-2026-05-29-01 - Exclude the intentionally reused backend from duplicate-kill lists

Priority: P1

Responsible file: `narrative-launcher/ServiceManager.cs`

Allowed files:

- `narrative-launcher/ServiceManager.cs`
- `narrative-launcher/Program.cs`

Problem:

`Program.cs` skips `StartBackend()` when `IsBackendRunningAsync()` returns true. In that path `Backend.Process` remains null. `FindDuplicates()` scans listeners on port 8000 and treats every listener as killable when `Backend.Process` is null, so the already-running backend that the launcher intentionally reused can appear in the duplicate list and be killed by `Kill All`.

Required implementation:

- Add this exact external ownership property to `ServiceInfo`: `public int? ExternalPid { get; set; }`.
- Add a `ServiceManager.AttachExternalBackendAsync()` method that finds the single listening PID on `Backend.Port` after `IsBackendRunningAsync()` succeeds and stores it in `Backend.ExternalPid`.
- In `Program.cs`, when `backendRunning` is true, call `await services.AttachExternalBackendAsync()` before constructing `HealthMonitor`.
- Update `AddPortDuplicate(...)` so it skips both `service.Process?.Id` and `service.ExternalPid`.
- Keep duplicate detection for any other listener PID on the same port.

Do not:

- Do not kill or restart externally owned backend processes.
- Do not remove duplicate detection entirely.
- Do not change backend startup command arguments.

Acceptance criteria:

- Existing live backend on port 8000 is not returned by `FindDuplicates()` after `AttachExternalBackendAsync()`.
- A second different PID on a monitored port is still returned by `FindDuplicates()`.
- `Backend.ExternalPid` is cleared when `StartBackend()` starts a launcher-owned backend.

Validation:

```powershell
dotnet build narrative-launcher\NarrativeLauncher.csproj
```

Manual smoke:

1. Start the backend outside the launcher.
2. Start the launcher.
3. Open the status window.
4. Confirm duplicate list does not include the running backend PID.

### NE-2026-05-29-02 - Make production launcher frontend handling explicitly static-on-backend

Priority: P1

Responsible file: `narrative-launcher/ServiceManager.cs`

Allowed files:

- `narrative-launcher/ServiceManager.cs`
- `narrative-launcher/StatusWindow.cs`
- `narrative-launcher/HealthMonitor.cs`
- `narrative-launcher/TrayManager.cs`

Problem:

The launcher now builds static frontend assets and opens `http://127.0.0.1:8000`, but the service model still partly treats frontend as a Vite service on port 5173. This causes inconsistent health, port display, duplicate detection, and restart behavior.

Required implementation:

- Set the launcher production model explicitly: frontend is a static build artifact served by the backend on port 8000.
- Keep `TrayManager` "Open Frontend" URL as `http://127.0.0.1:8000`.
- Set `Frontend.Port` to `8000` and `Frontend.CheckUrl` to `/`.
- Remove frontend duplicate-port scanning from `FindDuplicates()` in production mode. Only backend port 8000 should be checked for duplicates.
- In `StatusWindow`, display frontend port text as `8000` and status label as `Built` when `frontend/dist/index.html` exists.
- In `HealthMonitor`, keep frontend health based on `IsFrontendReady()` because production frontend readiness means the static build exists.

Do not:

- Do not start `npm run dev`.
- Do not ping port 5173 in production launcher paths.
- Do not introduce a dev-mode toggle in this task.

Acceptance criteria:

- No production launcher code path scans port 5173 for frontend duplicates.
- Status window frontend port display matches `8000`.
- "Open Frontend" opens `http://127.0.0.1:8000`.
- `dotnet build` remains clean.

Validation:

```powershell
dotnet build narrative-launcher\NarrativeLauncher.csproj
```

Manual smoke:

1. Build frontend.
2. Start launcher.
3. Confirm status window shows frontend as `Built` on port `8000`.
4. Confirm Open Frontend opens `http://127.0.0.1:8000`.

### NE-2026-05-29-03 - Force frontend rebuild on launcher frontend restart

Priority: P1

Responsible file: `narrative-launcher/ServiceManager.cs`

Allowed files:

- `narrative-launcher/ServiceManager.cs`
- `narrative-launcher/StatusWindow.cs`
- `narrative-launcher/Program.cs`

Dependency: complete `NE-2026-05-29-02` first.

Problem:

`StartFrontendAsync()` returns early when `frontend/dist/index.html` exists. `RestartFrontendAsync()` calls `StartFrontendAsync()`, so frontend restart often does not rebuild changed source files.

Required implementation:

- Change `StartFrontendAsync` signature to `StartFrontendAsync(bool forceRebuild = false)`.
- Preserve the early return only when `forceRebuild == false` and `FrontendBuilt()` is true.
- Update `RestartFrontendAsync()` to call `StartFrontendAsync(forceRebuild: true)`.
- Update the StatusWindow "Restart All" frontend path to force rebuild through `RestartFrontendAsync()`.
- Leave initial startup behavior unchanged except for the signature update.

Do not:

- Do not delete `frontend/dist` manually.
- Do not add timestamp comparison logic.
- Do not change npm script names.

Acceptance criteria:

- Calling `RestartFrontendAsync()` runs `npm run build` even when `frontend/dist/index.html` exists.
- Calling `StartFrontendAsync()` with default arguments still skips when `FrontendBuilt()` is true.
- `Frontend.Process` is set to the completed build process after a forced rebuild.

Validation:

```powershell
dotnet build narrative-launcher\NarrativeLauncher.csproj
cd frontend
npm run build
```

Manual smoke:

1. Record the timestamp of `frontend/dist/index.html`.
2. Use launcher "Restart Frontend".
3. Confirm the timestamp changes.

### NE-2026-05-29-04 - Render Studio rail buttons in compact mode

Priority: P1

Responsible file: `frontend/src/components/studio/StudioProjectRail.tsx`

Allowed files:

- `frontend/src/components/studio/StudioProjectRail.tsx`
- `frontend/src/components/studio/__tests__/studioWorkflowRouting.test.tsx`

Problem:

The item container renders only when `!(compact || isCollapsed)`. In compact mode this is always false, so compact rail width appears but no rail buttons render.

Required implementation:

- Change the section item rendering condition so compact mode renders section items.
- Use this exact behavior: render items when `compact || !isCollapsed`.
- In compact mode, render the existing `RailButton` components directly in a vertical list without section headers.
- Add a test in `studioWorkflowRouting.test.tsx` that renders `StudioProjectRail` with `compact={true}` and asserts that buttons with accessible names `Ideas`, `Characters`, and `Polish` exist.

Do not:

- Do not change `railSections` membership.
- Do not change `RailButton` labels.
- Do not add new panels.

Acceptance criteria:

- Compact rail renders all panel buttons from `railSections`.
- Collapsed expanded-mode sections still hide their items.
- New test fails before the fix and passes after the fix.

Validation:

```powershell
cd frontend
npm run test -- studioWorkflowRouting
npm run build
```

### NE-2026-05-29-05 - Make entity count badges deterministic and hide unsupported counts

Priority: P2

Responsible file: `frontend/src/hooks/useEntityCounts.ts`

Allowed files:

- `frontend/src/hooks/useEntityCounts.ts`
- `frontend/src/hooks/__tests__/useEntityCounts.test.tsx`
- `frontend/src/components/studio/StudioProjectRail.tsx`

Problem:

`useEntityCounts()` uses positional mapping between a query array and `panelKeys`. The rail includes panels that do not have queried counts. Some panels therefore show misleading zero badges even when backed data exists or when no count source is defined.

Required implementation:

- Replace positional `panelKeys` mapping with named query definitions. Each query definition must include `panel` and `queryFn`.
- Add a real research count using existing `getResearchItems(projectId)` from the research service. If that exported function does not exist, stop with `BLOCKED_MISSING_INPUT`; do not invent a new service in this task.
- Change `getPanelCount` return type from `number` to `number | null`.
- Return `null` for these unsupported count panels: `notes`, `generation`, `review`, `inspect`, `canon`, `polish`.
- Update `RailButton` props and render logic so badges render only when `count !== null && count > 0`.
- Add a unit test that proves:
  - research count is assigned to `research`, not to another panel.
  - unsupported panels return `null`.
  - a count of zero does not render a badge.

Do not:

- Do not create new backend endpoints.
- Do not add count queries for unsupported panels.
- Do not keep positional array-to-key assignment.

Acceptance criteria:

- Reordering query definitions cannot assign counts to the wrong panel.
- Research badge can show a nonzero count when the service returns research items.
- Unsupported panels do not display a zero badge.

Validation:

```powershell
cd frontend
npm run test -- useEntityCounts
npm run typecheck
npm run build
```

### NE-2026-05-29-06 - Treat LLM as explicitly unmanaged in launcher UI and health

Priority: P2

Responsible file: `narrative-launcher/StatusWindow.cs`

Allowed files:

- `narrative-launcher/StatusWindow.cs`
- `narrative-launcher/TrayManager.cs`
- `narrative-launcher/HealthMonitor.cs`
- `narrative-launcher/ServiceManager.cs`

Problem:

`MonitorLlm` is hard-coded false and `Llm.Healthy` is forced true, but the UI still exposes LLM as if it is a managed service through tooltip status and restart controls.

Required implementation:

- Keep LLM unmanaged. Do not add LLM process startup.
- In `StatusWindow`, keep the LLM row visible but display:
  - status text `Not Managed`
  - muted status color
  - disabled restart button
- In "Restart All", restart only backend and frontend. Do not call `RestartLlm()`.
- In `TrayManager.UpdateTooltip`, omit LLM health from the tooltip when `services.IsLlmMonitored()` is false.
- In `HealthMonitor.UpdateTray`, omit LLM from unhealthy lists and overall health when monitoring is disabled.

Do not:

- Do not make `MonitorLlm` configurable.
- Do not start, kill, or restart LLM processes.
- Do not remove the LLM row entirely.

Acceptance criteria:

- LLM restart button is disabled when `IsLlmMonitored()` is false.
- Restart All does not call LLM restart code.
- Tray tooltip does not show `LLM ✓` or `LLM ✗` when LLM is unmanaged.
- Overall tray health ignores LLM when unmanaged.

Validation:

```powershell
dotnet build narrative-launcher\NarrativeLauncher.csproj
```

Manual smoke:

1. Open the status window.
2. Confirm LLM row reads `Not Managed`.
3. Confirm LLM restart control is disabled.
4. Confirm tray tooltip lists backend/frontend only.

### NE-2026-05-29-07 - Map Polish analyze/export service errors to HTTP responses

Priority: P2

Responsible file: `app/api/story_development/polish.py`

Allowed files:

- `app/api/story_development/polish.py`
- `tests/test_story_development_polish_api.py`

Problem:

`analyze_document` and `export_manuscript` return service responses directly. Unlike `list_reports`, they do not catch `PolishServiceError`, so service-level validation failures can leak as 500 errors.

Required implementation:

- Wrap `service.analyze_document(...)` in `try/except PolishServiceError`.
- Wrap `service.export_manuscript(...)` in `try/except PolishServiceError`.
- Convert `PolishNotFoundError` to HTTP 404.
- Convert other `PolishServiceError` values to HTTP 400.
- Add tests using a stub or monkeypatched service that raises:
  - `PolishNotFoundError` from analyze -> 404
  - `PolishServiceError` from analyze -> 400
  - `PolishNotFoundError` from export -> 404
  - `PolishServiceError` from export -> 400

Do not:

- Do not change successful response shape.
- Do not change route paths or status codes for successful calls.
- Do not catch broad `Exception`.

Acceptance criteria:

- Both routes map domain errors deterministically.
- Existing polish API tests still pass.

Validation:

```powershell
python -m pytest -q tests/test_story_development_polish_api.py
```

### NE-2026-05-29-08 - Reject unsupported Polish export options explicitly

Priority: P2

Responsible file: `app/schemas/story_development.py`

Allowed files:

- `app/schemas/story_development.py`
- `tests/test_story_development_polish_api.py`

Problem:

`ExportRequest` accepts `include_frontmatter`, `include_toc`, and `stylesheet`, but `PolishService.export_manuscript()` ignores those fields. Silent acceptance makes callers believe options are honored.

Required implementation:

- Keep the fields on `ExportRequest` for API compatibility.
- Add an `after` model validator on `ExportRequest`.
- Reject any request with `include_frontmatter == true`, `include_toc == true`, or `stylesheet is not None`.
- The validator error message must contain `Export options are not supported`.
- Update `test_export_with_options` to expect HTTP 422.
- Add one test for `stylesheet` alone returning HTTP 422.

Do not:

- Do not implement real export option handling.
- Do not remove fields from `ExportRequest`.
- Do not change valid formats.

Acceptance criteria:

- Unsupported export options fail at request validation with 422.
- Existing plain export requests still return 202.

Validation:

```powershell
python -m pytest -q tests/test_story_development_polish_api.py
```

### NE-2026-05-29-09 - Restore deleted discovery API endpoint existence tests

Priority: P2

Responsible file: `tests/test_discovery_api.py`

Allowed files:

- `tests/test_discovery_api.py`

Problem:

The branch deletes endpoint existence coverage for discovery scan, job status, staging get/apply/undo/discard, and entity patch endpoints.

Required implementation:

- Restore the following tests with their original assertions from `codex/main`:
  - `test_scan_endpoint_exists`
  - `test_job_status_endpoint_exists`
  - `test_staging_endpoint_exists`
  - `test_apply_endpoint_exists`
  - `test_undo_endpoint_exists`
  - `test_discard_endpoint_exists`
  - `test_patch_endpoint_exists`

Do not:

- Do not weaken expected status codes.
- Do not rename tests.
- Do not alter production discovery code in this task.

Acceptance criteria:

- The seven named tests exist in `tests/test_discovery_api.py`.
- The file passes by itself.

Validation:

```powershell
python -m pytest -q tests/test_discovery_api.py
```

### NE-2026-05-29-10 - Restore deleted manuscript assist endpoint tests

Priority: P2

Responsible file: `tests/test_manuscript_assist_integration.py`

Allowed files:

- `tests/test_manuscript_assist_integration.py`

Problem:

The branch deletes broad manuscript document and revision suggestion endpoint coverage unrelated to the studio rail or launcher work.

Required implementation:

- Restore the following tests with their original assertions from `codex/main`:
  - `TestManuscriptDocumentEndpoints.test_create_manuscript_document_returns_201`
  - `TestManuscriptDocumentEndpoints.test_list_manuscript_documents`
  - `TestManuscriptDocumentEndpoints.test_get_manuscript_document`
  - `TestManuscriptDocumentEndpoints.test_get_manuscript_document_not_found`
  - `TestManuscriptDocumentEndpoints.test_update_manuscript_document`
  - `TestRevisionSuggestionEndpoints.test_create_revision_suggestion_returns_201`
  - `TestRevisionSuggestionEndpoints.test_create_revision_suggestion_requires_target_document`
  - `TestRevisionSuggestionEndpoints.test_list_revision_suggestions_filtered_by_document`

Do not:

- Do not weaken expected status codes.
- Do not rename tests.
- Do not alter production drafting code in this task.

Acceptance criteria:

- The eight named tests exist in `tests/test_manuscript_assist_integration.py`.
- The file passes by itself.

Validation:

```powershell
python -m pytest -q tests/test_manuscript_assist_integration.py
```

### NE-2026-05-29-11 - Restore deleted pattern extraction constructor tests

Priority: P2

Responsible file: `tests/test_pattern_extraction.py`

Allowed files:

- `tests/test_pattern_extraction.py`

Problem:

The branch deletes constructor behavior tests for `PatternExtractionService`.

Required implementation:

- Restore the following tests with their original assertions from `codex/main`:
  - `TestPatternExtractionServiceConstructor.test_construct_with_defaults`
  - `TestPatternExtractionServiceConstructor.test_keyword_only_args`
  - `TestPatternExtractionServiceConstructor.test_creates_mythos_service`
  - `TestPatternExtractionServiceConstructor.test_mythos_service_receives_same_deps`
- If `test_construct_creates_mythos_service` currently combines two restored tests, split it back into the two original tests listed above.

Do not:

- Do not alter production pattern extraction code in this task.
- Do not remove existing passing tests.

Acceptance criteria:

- The four named tests exist in `tests/test_pattern_extraction.py`.
- Constructor dependency behavior is covered separately for creation and dependency wiring.

Validation:

```powershell
python -m pytest -q tests/test_pattern_extraction.py
```

### NE-2026-05-29-12 - Restore deleted storyboard endpoint tests

Priority: P2

Responsible file: `tests/test_persistence_runtime_expansion.py`

Allowed files:

- `tests/test_persistence_runtime_expansion.py`

Problem:

The branch deletes storyboard create/get/list/filter endpoint coverage.

Required implementation:

- Restore the following tests with their original assertions from `codex/main`:
  - `TestStoryboardCardEndpoints.test_create_storyboard_card`
  - `TestStoryboardCardEndpoints.test_get_storyboard_card`
  - `TestStoryboardCardEndpoints.test_get_storyboard_card_not_found`
  - `TestStoryboardCardEndpoints.test_list_storyboard_cards`
  - `TestStoryboardCardEndpoints.test_list_storyboard_cards_filtered_by_type`
  - `TestStoryboardCardEndpoints.test_list_storyboard_cards_filtered_by_column`
  - `TestStoryboardCardEndpoints.test_list_storyboard_cards_filtered_by_tag`

Do not:

- Do not weaken expected status codes.
- Do not rename tests.
- Do not alter production storyboard code in this task.

Acceptance criteria:

- The seven named tests exist in `tests/test_persistence_runtime_expansion.py`.
- The file passes by itself.

Validation:

```powershell
python -m pytest -q tests/test_persistence_runtime_expansion.py
```

### NE-2026-05-29-13 - Remove root-level generated `Image/` directory from commit scope

Priority: P3

Responsible file: `Image/`

Allowed files:

- `Image/`

Problem:

The root-level untracked `Image/` directory contains generated/source asset material that is not imported by the app. Runtime icons are already under `frontend/src/assets/icons/rail/`.

Required implementation:

- Delete the untracked root-level `Image/` directory from the working tree.
- Keep `frontend/src/assets/icons/rail/` unchanged.

Do not:

- Do not delete `frontend/src/assets/icons/rail/`.
- Do not move `Image/` contents into docs.
- Do not add new documentation references to `Image/`.

Acceptance criteria:

- `git status --short` no longer lists `?? Image/`.
- Frontend build still succeeds.

Validation:

```powershell
git status --short
cd frontend
npm run build
```

### NE-2026-05-29-14 - Type rail icon map with exact keys

Priority: P3

Responsible file: `frontend/src/assets/icons/rail/index.ts`

Allowed files:

- `frontend/src/assets/icons/rail/index.ts`
- `frontend/src/components/studio/StudioProjectRail.tsx`

Problem:

`railIcons` is typed as `Record<string, RailIconComponent>`, so missing or misspelled icon keys are not caught by TypeScript.

Required implementation:

- Export a `RailIconKey` union containing exactly these keys:
  - `ideas`
  - `notes`
  - `characters`
  - `worldBible`
  - `relationships`
  - `arcs`
  - `structure`
  - `chapters`
  - `research`
  - `manuscripts`
  - `drafts`
  - `generation`
  - `revision`
  - `suggestions`
  - `review`
  - `inspect`
  - `polish`
  - `canon`
  - `jobs`
- Type `railIcons` as `Record<RailIconKey, RailIconComponent>`.
- In `StudioProjectRail.tsx`, set `RailItem.icon` to `RailIconComponent` and keep assigning icon components from `railIcons`.

Do not:

- Do not import `StudioPanelKey` into `frontend/src/assets/icons/rail/index.ts`.
- Do not change icon file names.
- Do not change rail labels or panel keys.

Acceptance criteria:

- Misspelling a key in `railIcons` would fail TypeScript.
- Existing `railSections` compile without casts.

Validation:

```powershell
cd frontend
npm run typecheck
npm run build
```

## Suggested Serial Order

1. `NE-2026-05-29-01`
2. `NE-2026-05-29-02`
3. `NE-2026-05-29-03`
4. `NE-2026-05-29-04`
5. `NE-2026-05-29-05`
6. `NE-2026-05-29-06`
7. `NE-2026-05-29-07`
8. `NE-2026-05-29-08`
9. `NE-2026-05-29-09`
10. `NE-2026-05-29-10`
11. `NE-2026-05-29-11`
12. `NE-2026-05-29-12`
13. `NE-2026-05-29-13`
14. `NE-2026-05-29-14`

## Minimum Merge-Readiness Validation After All Fixes

Use the timeout guidance from AGENTS.md: at least 300000ms for the parallel cluster and at least 240000ms for serial tests.

```powershell
python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py
python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters tests/test_discovery_api.py::test_patch_returns_updated tests/test_story_bible_lineage.py::TestStoryBibleLineageContentHash::test_story_bible_content_hash_matches_file_content
cd frontend
npm run lint
npm run typecheck
npm run build
npm run test
cd ..
dotnet build narrative-launcher\NarrativeLauncher.csproj
```
