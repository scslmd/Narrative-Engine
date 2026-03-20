# Narrative-Core Recovered

Recovered reconstruction of the Narrative-Core project based on the conversation record after the original workspace contents were lost.

This recovery folder is intentionally separate from the damaged workspace and from the active recovery source drive.

## Recovery Goals

This reconstruction focuses on:

- restoring the project structure
- preserving the latest known architecture and workflow decisions
- rebuilding the core backend contracts first
- restoring the frontend writer workflow next

## Recovered Scope

This recovered working state includes:

- core project documentation
- backend settings and schema contracts
- project lifecycle service contracts
- a FastAPI app shell with project, job, model, and role-model checker routes
- SQLite-backed persistence for project artifact registration, jobs, and checker runs
- a recovered frontend writer-workflow prototype with setup, story engine, draft, and review stages

## Current Recovery Status

This is a reconstructed working tree, not a byte-for-byte restore of the lost repository.

Recovered with highest confidence:

- project purpose and architecture
- API boundaries
- manifest and project identity contracts
- project-name requirement
- async job/checker monitoring intent
- role-model checker workflow
- frontend writer-workflow prototype direction
- project artifact endpoint surface for manifest, sequence, and chapter 1
- first-pass SQLite persistence for operational state and project artifact indexing
- SQLite hardening for local durability, schema migration, foreign keys, and indexed event history
- explicit project reconciliation instead of constructor-time registry mutation
- deterministic transition validation for the current persisted job/checker records

Still to be rebuilt in later passes:

- full inference layer
- sequencer, saliency, drafting, critic, and compiler runtime code
- vector store integration
- broader unit and integration coverage beyond the current recovered test set
- final frontend behavior and styling parity
- full writer-facing project authoring workflow parity

Current UI note
- The current frontend is a recovered writer-workflow prototype, not full parity with the original application.
- It now supports project setup, story engine workspace notes, story-bible readiness cues, chapter packet assembly, recovered artifact inspection, backend status polling, and saved checker report visibility.
- Canonical backend persistence for all story-engine notes, richer drafting runtime behavior, and final UX parity are still pending.

Current persistence note
- Operational state is backed by SQLite under `data/state/narrative_ops.db`.
- Each project also gets a local `bible.db` used for project metadata and artifact registration.
- SQLite connections now enable foreign keys, WAL mode, busy timeout, schema-version scaffolding, and indexed event tables as part of the recovered hardening pass.
- Jobs and checker runs now persist immutable request snapshots plus append-only event history.
- Jobs and checker runs now also persist baseline attempt-lineage fields (`logical_run_id`, `attempt_number`) across run rows and event rows.
- Generated checker reports and generated project databases are treated as local artifacts and are ignored by git.

Current protocol note
- The recovered code now persists request snapshots, event history, baseline attempt-lineage fields, and enforces basic transition rules for the current synchronous stub workflow.
- Job creation and role-model checker start/run now return `202 Accepted` plus a status `Location`, then finish their recovered stub work in a post-response background task.
- The API still has not crossed into true queue/worker semantics yet; the accepted work is still executed in-process rather than by a lease-claiming worker.
- The next serial rebuild step is first-class attempt/step records plus a real worker/lease runner behind those accepted endpoints.

Recovered quickstart
- This project is a safe reconstruction baseline created on F: while D: remained under live recovery.
- Start here with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
- Open `http://127.0.0.1:8000/role-model-checker-ui` after launch.
- Run `python -m pytest tests/test_recovered_smoke.py tests/test_persistence.py -q` to validate the current recovered baseline.
- Current verified baseline: `17 passed` for the recovered smoke and persistence suite.
- Read `docs/Recovered Reconstruction Index v0.1.md` before deeper rebuild work.
- Read `docs/Frontend Design SRS Recovered v0.1.md` for the current writer-workflow interaction model.
