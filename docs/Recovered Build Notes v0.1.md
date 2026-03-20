Recovered Build Notes v0.2

This F: reconstruction was created because the original D: workspace became unavailable during active recovery.

Rules followed during reconstruction:
- No writes were made back into D:.
- Recovered files were rebuilt only into F:\Dev\Narrative-Recover.
- The rebuilt tree prefers safe stubs over pretending runtime-complete behavior exists.
- Documentation records what is reconstructed versus what remains approximate.

Current recovered implementation notes:
- The recovered workspace now includes a practical first persistence layer instead of purely in-memory operational state.
- Jobs and role-model checker runs are stored in SQLite under `data\state\narrative_ops.db`.
- The shared SQLite layer now enables foreign keys, WAL mode, busy timeout, schema-version scaffolding, and indexed event/result/log tables.
- Project registration creates and synchronizes per-project `bible.db` files for project metadata and artifact indexing.
- Project reconciliation no longer happens implicitly during `ProjectService` construction. It now runs through an explicit sync/repair call during app bootstrap or when invoked directly for repair flows.
- Normal project reads now prefer the persisted project projection and artifact registry instead of mixing constructor-time DB mutation with fresh filesystem scans on each read.
- Project artifact lookups are normalized through persistence so `manifest`, `sequence`, and `chapter-1` resolve consistently even across recovered filename differences such as `chapter.md` versus `chapter_001.md`.
- The frontend recovered console now polls backend status endpoints and surfaces saved checker report paths.
- Jobs and checker runs now persist immutable request snapshots plus append-only event history.
- The current recovered synchronous stub flow now rejects illegal state transitions for jobs and checker runs.

Git recovery note:
- A new git repository was initialized in F:\Dev\Narrative-Recover after reconstruction work began on the safe copy.
- The recovered workspace is now the active source-control root for rebuild work until any original repository data can be safely recovered from D:.
- Local-only artifacts are ignored through the repository `.gitignore`, including `.venv`, `.pytest_cache`, `__pycache__`, editable-build egg-info output, generated `data\projects\*\bible.db`, `data\state\`, and generated `data\role_model_checker_runs\`.

If the original repository is later recovered:
- Compare docs first.
- Preserve any true source recovered from the original repo over conversational reconstructions.
- Merge by module, not by blind folder overwrite.
