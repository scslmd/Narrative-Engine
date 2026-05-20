# Radial Hub Serial Subagent Dispatch Batches

Purpose: provide a single operator-facing batch file for strict serial subagent dispatch by stage.

Source artifacts:
- [Master contract](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/2026-05-20-radial-hub-phases-1-5-fine-grained-contract.json)
- [Stage contracts](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages)
- [Per-task prompts](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts)

Dispatch rules:
- Dispatch one prompt at a time.
- Do not dispatch the next prompt until the current prompt reports success and its task verification commands are green.
- Do not dispatch a task whose listed dependencies are incomplete.
- Do not move to the next stage until every task in the current stage is complete and the stage pass criteria are green.
- After each stage pass criteria are green, create a rollback checkpoint before dispatching the next stage.
- Use checkpoint commit message format `checkpoint(radial-hub): complete S{N} <Stage Name>` or create an equivalent stage-scoped patch snapshot if a commit is not appropriate.
- If any prompt reports `BLOCKED_MISSING_INPUT`, `BLOCKED_AMBIGUOUS_INSTRUCTION`, `BLOCKED_NONDETERMINISTIC_CHECK`, or `BLOCKED_PLAN_VIOLATION`, stop the batch and resolve the blocker before continuing.

## Stage S1: Core Infrastructure

Stage contract:
- [01-S1-core-infrastructure.json](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages/01-S1-core-infrastructure.json)

Serial dispatch order:
1. [001-extend-studiostore-for-floating-panel-layout-state-and-panel-keys.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/001-extend-studiostore-for-floating-panel-layout-state-and-panel-keys.md)
2. [002-create-initial-studiofloatingpanel-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/002-create-initial-studiofloatingpanel-tests.md)
3. [003-create-studiofloatingpanel-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/003-create-studiofloatingpanel-implementation.md)
4. [004-create-initial-studiopanelmenu-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/004-create-initial-studiopanelmenu-tests.md)
5. [005-create-studiopanelmenu-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/005-create-studiopanelmenu-implementation.md)
6. [006-create-initial-studioradialhub-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/006-create-initial-studioradialhub-tests.md)
7. [007-create-studioradialhub-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/007-create-studioradialhub-implementation.md)
8. [008-create-studiopanelcontent-router.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/008-create-studiopanelcontent-router.md)
9. [009-replace-studioview-grid-shell-with-radial-hub-composition.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/009-replace-studioview-grid-shell-with-radial-hub-composition.md)
10. [010-update-studioview-tests-for-radial-hub-rendering.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/010-update-studioview-tests-for-radial-hub-rendering.md)
11. [011-extend-studiocommandbar-with-panel-menu-and-reset-control.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/011-extend-studiocommandbar-with-panel-menu-and-reset-control.md)

Stage pass criteria before S2:
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioPanelMenu.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioRadialHub.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioView.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run build`

Checkpoint before S2:
- `checkpoint(radial-hub): complete S1 Core Infrastructure`

## Stage S2: Panel Migration

Stage contract:
- [02-S2-panel-migration.json](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages/02-S2-panel-migration.json)

Serial dispatch order:
1. [012-add-studiodraftspanel-prop-based-test-coverage.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/012-add-studiodraftspanel-prop-based-test-coverage.md)
2. [013-migrate-studiodraftspanel-from-useparams-to-projectid-prop.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/013-migrate-studiodraftspanel-from-useparams-to-projectid-prop.md)
3. [014-update-studiocontextpanel-drafts-call-site.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/014-update-studiocontextpanel-drafts-call-site.md)
Transitional note:
This task preserves `StudioContextPanel` as legacy compatibility wiring. Do not remove `StudioContextPanel` in S2.
4. [015-create-studiostructurepanel-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/015-create-studiostructurepanel-implementation.md)
5. [016-add-studiostructurepanel-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/016-add-studiostructurepanel-tests.md)
6. [017-create-studiochapterspanel-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/017-create-studiochapterspanel-implementation.md)
7. [018-add-studiochapterspanel-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/018-add-studiochapterspanel-tests.md)
8. [019-create-studiocanonpanel-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/019-create-studiocanonpanel-implementation.md)
9. [020-add-studiocanonpanel-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/020-add-studiocanonpanel-tests.md)
10. [021-wire-structure-chapters-canon-and-drafts-through-studiopanelcontent.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/021-wire-structure-chapters-canon-and-drafts-through-studiopanelcontent.md)
11. [022-add-layout-presets-to-studiostore.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/022-add-layout-presets-to-studiostore.md)
12. [023-create-studiostatusbar-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/023-create-studiostatusbar-implementation.md)
13. [024-add-studiostatusbar-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/024-add-studiostatusbar-tests.md)
14. [025-add-studiostatusbar-to-studioview.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/025-add-studiostatusbar-to-studioview.md)

Stage pass criteria before S3:
- `cd frontend; cmd /c npm.cmd run test -- StudioDraftsPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioStructurePanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioChaptersPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioCanonPanel.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioStatusBar.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`

Checkpoint before S3:
- `checkpoint(radial-hub): complete S2 Panel Migration`

## Stage S3: Interaction Polish

Stage contract:
- [03-S3-interaction-polish.json](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages/03-S3-interaction-polish.json)

Serial dispatch order:
1. [026-create-studiosnapindicator-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/026-create-studiosnapindicator-implementation.md)
2. [027-add-studiosnapindicator-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/027-add-studiosnapindicator-tests.md)
3. [028-create-studiofloatingwindow-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/028-create-studiofloatingwindow-implementation.md)
4. [028a-add-studiofloatingwindow-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/028a-add-studiofloatingwindow-tests.md)
5. [029-create-studiohoverpreview-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/029-create-studiohoverpreview-implementation.md)
6. [029a-add-studiohoverpreview-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/029a-add-studiohoverpreview-tests.md)
7. [030-create-usepanelkeyboard-hook.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/030-create-usepanelkeyboard-hook.md)
8. [030a-add-usepanelkeyboard-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/030a-add-usepanelkeyboard-tests.md)
9. [031-add-debounced-persistence-and-layout-import-export-to-studiostore.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/031-add-debounced-persistence-and-layout-import-export-to-studiostore.md)
10. [031a-add-studiostore-layout-persistence-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/031a-add-studiostore-layout-persistence-tests.md)
11. [032-create-studiolayoutpreset-implementation.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/032-create-studiolayoutpreset-implementation.md)
12. [032a-add-studiolayoutpreset-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/032a-add-studiolayoutpreset-tests.md)
13. [033-integrate-layout-preset-ui-into-studiocommandbar.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/033-integrate-layout-preset-ui-into-studiocommandbar.md)
14. [033a-add-studiocommandbar-layout-preset-integration-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/033a-add-studiocommandbar-layout-preset-integration-tests.md)
15. [034-apply-phase-3-polish-to-studiofloatingpanel.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/034-apply-phase-3-polish-to-studiofloatingpanel.md)
16. [034a-add-studiofloatingpanel-phase-3-polish-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/034a-add-studiofloatingpanel-phase-3-polish-tests.md)
17. [035-apply-phase-3-polish-to-studioradialhub.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/035-apply-phase-3-polish-to-studioradialhub.md)
18. [035a-add-studioradialhub-phase-3-polish-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/035a-add-studioradialhub-phase-3-polish-tests.md)

Stage pass criteria before S4:
- `cd frontend; cmd /c npm.cmd run test -- StudioSnapIndicator.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingWindow.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioHoverPreview.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- usePanelKeyboard.test.ts`
- `cd frontend; cmd /c npm.cmd run test -- studioStore.layoutPersistence.test.ts`
- `cd frontend; cmd /c npm.cmd run test -- StudioLayoutPreset.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioCommandBar.layoutPreset.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioFloatingPanel.phase3.test.tsx`
- `cd frontend; cmd /c npm.cmd run test -- StudioRadialHub.phase3.test.tsx`
- `cd frontend; cmd /c npm.cmd run test`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run build`

Checkpoint before S4:
- `checkpoint(radial-hub): complete S3 Interaction Polish`

## Stage S4: Route Migration

Stage contract:
- [04-S4-route-migration.json](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages/04-S4-route-migration.json)

Serial dispatch order:
1. [036-sync-activepanel-on-bringtofront-in-studiostore.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/036-sync-activepanel-on-bringtofront-in-studiostore.md)
2. [037-create-usepanelurlsync-hook.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/037-create-usepanelurlsync-hook.md)
3. [038-integrate-usepanelurlsync-into-studioview.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/038-integrate-usepanelurlsync-into-studioview.md)
4. [039-replace-app-workspace-routes-with-backward-compatible-redirects.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/039-replace-app-workspace-routes-with-backward-compatible-redirects.md)
5. [039a-add-app-redirect-tests-for-studio-route-migration.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/039a-add-app-redirect-tests-for-studio-route-migration.md)
6. [040-update-workspaceshell-navigation-to-studio-query-urls.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/040-update-workspaceshell-navigation-to-studio-query-urls.md)
7. [041-simplify-useroutesync-for-the-single-route-workspace.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/041-simplify-useroutesync-for-the-single-route-workspace.md)
8. [042-derive-layout-stage-state-from-studio-tab-query-param.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/042-derive-layout-stage-state-from-studio-tab-query-param.md)
9. [043-update-studioprojectrail-bottom-links-to-studio-urls.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/043-update-studioprojectrail-bottom-links-to-studio-urls.md)

Stage pass criteria before S5:
- `cd frontend; cmd /c npm.cmd run test -- App.redirects.test.tsx`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`
- Manual redirect checks for `/plan`, `/review`, `/inspect/:jobId`, `/braindump`, `/canon?tab=mythos`, `/generate`, `/write/:chapterId` resolve to `/studio` query URLs.

Checkpoint before S5:
- `checkpoint(radial-hub): complete S4 Route Migration`

## Stage S5: Validation, Accessibility, And Mobile Behavior

Stage contract:
- [05-S5-validation-accessibility-and-mobile-behavior.json](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-stages/05-S5-validation-accessibility-and-mobile-behavior.json)

Serial dispatch order:
1. [044-create-usemediaquery-hook.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/044-create-usemediaquery-hook.md)
2. [045-apply-final-accessibility-and-mobile-behavior-to-studiofloatingpanel.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/045-apply-final-accessibility-and-mobile-behavior-to-studiofloatingpanel.md)
3. [046-apply-final-responsive-and-accessibility-behavior-to-studioradialhub.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/046-apply-final-responsive-and-accessibility-behavior-to-studioradialhub.md)
4. [047-apply-final-responsive-and-accessibility-behavior-to-studiopanelmenu.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/047-apply-final-responsive-and-accessibility-behavior-to-studiopanelmenu.md)
5. [048-apply-final-semantics-to-studiostatusbar.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/048-apply-final-semantics-to-studiostatusbar.md)
6. [049-create-integrated-radial-hub-accessibility-tests.md](C:/Users/SLuh/Documents/Dev/Narrative-Engine/docs/superpowers/contracts/radial-hub-prompts/049-create-integrated-radial-hub-accessibility-tests.md)

Final stage pass criteria:
- `cd frontend; cmd /c npm.cmd run test`
- `cd frontend; cmd /c npm.cmd run lint`
- `cd frontend; cmd /c npm.cmd run typecheck`
- `cd frontend; cmd /c npm.cmd run build`
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters tests/test_discovery_api.py::test_patch_returns_updated tests/test_story_bible_lineage.py::TestStoryBibleLineageContentHash::test_story_bible_content_hash_matches_file_content`

Final checkpoint:
- `checkpoint(radial-hub): complete S5 Validation, Accessibility, And Mobile Behavior`

Global completion gate:
- Do not claim merge-readiness until every Stage S5 pass criterion is green.
- Use timeout >= 300000ms for the parallel pytest cluster.
- Use timeout >= 240000ms for the serial pytest command.
