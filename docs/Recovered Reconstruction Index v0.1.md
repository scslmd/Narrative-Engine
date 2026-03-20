Recovered Reconstruction Index v0.2

Current recovered layers:
- docs/: recovered SRS, runtime findings, decision notes, and validation notes
- app/: recovered FastAPI shell, project APIs, model catalog, SQLite-backed persistence, hardened SQLite configuration, job flow scaffolding, and role-model checker scaffolding
- frontend/: recovered writer-workflow prototype with project creation, workspace notes, artifact preview, backend polling, and report-path display
- data/: representative test projects, generated project databases, generated checker reports, and empty models directory
- tests/: smoke coverage plus persistence coverage for the recovered baseline

What is currently reconstructed faithfully from the conversation:
- project_name as the user-facing identity
- unified workflow preferences
- role-model checker concept and workflow
- async/progress-oriented API surface shape
- recovered project artifact endpoints for manifest, sequence, and chapter 1
- local-first operational persistence using SQLite as the first rebuild layer
- explicit project reconciliation and persisted project projections instead of constructor-time registry mutation
- immutable request snapshots and append-only event history for jobs and checker runs
- deterministic transition validation for the current persisted job/checker records
- documentation map and runtime findings structure

What is currently represented as a stub and still needs deeper rebuild or true restore:
- full inference runtime integration
- full orchestrator/compiler implementation
- deeper role-model checker execution and scoring against real model output
- complete unit/integration coverage from the original repo
- exact polished frontend behavior from the lost workspace

What changed from the earliest recovered baseline:
- Operational state is no longer purely in memory; jobs and checker runs persist in SQLite.
- Project artifact registration is normalized through persistence and supports canonical lookups for `sequence` and `chapter-1`.
- Project discovery/reconciliation is now an explicit sync/repair step, and normal project reads prefer the persisted projection instead of constructor-time registry side effects plus fresh directory scans.
- The frontend now includes project creation, local story-engine workspace notes, artifact preview, backend polling, and saved checker report paths.
- Generated checker reports and generated project databases are treated as local artifacts and are ignored by git.
- SQLite now uses foreign keys, WAL mode, busy timeout, schema-version scaffolding, and indexed child/event tables.
- Executable persistence tests now cover transition rejection, explicit reconciliation behavior, pragma/index configuration, and foreign-key cascade behavior.

Recommended rebuild order from this recovered baseline:
1. extend the current SQLite persistence layer as needed for orchestration/runtime state
2. rebuild inference and model registry runtime
3. rebuild orchestrator/compiler path on top of durable state
4. rebuild full role-model checker behavior
5. expand tests before resuming production changes

Protocol hardening documents added after the first SQLite pass:
- `docs/Async Protocol Blueprint v0.1.md`: deterministic run protocol for enqueue/claim/run/validate/persist completion flow
- `docs/Failure Mode Test Matrix v0.1.md`: failure-oriented test-planning checklist for recovery/resume-safe execution
