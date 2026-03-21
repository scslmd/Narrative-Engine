# Project Index v0.1

Current project layers:

- `STRUCTURE.md`: repository map for folders and key files
- `docs/`: product, frontend, protocol, and validation documents
- `docs/archive/`: superseded notes and historical decisions retained for reference
- `app/`: FastAPI app, persistence layer, schemas, and services
- `frontend/`: writer workflow prototype
- `data/`: sample projects, generated artifacts, and local runtime data roots
- `tests/`: smoke and persistence coverage

Implemented foundation:

- project-name-first identity
- project artifact endpoints for manifest, sequence, and chapter 1
- SQLite-backed jobs, checker runs, and project projections
- append-only event history and first-class attempt tables
- accepted-and-polled jobs and checker runs with idempotent replay support
- local lease-claim execution and stale-lease reclaim for accepted jobs and checker runs
- attempt-level executor telemetry on jobs and checker runs, including executor-name and claim or reclaim payload metadata
- explicit operator retry flow that requeues failed runs onto a new attempt number
- persisted step records and artifact lineage for the local executor path, plus contract fixtures that lock the record shape
- generalized inference provider selection plus real runtime execution paths for `P-100` `architect`, `P-200` `sequencer`, `P-300` `drafter`, and `P-400` `compiler`
- canonical `architect_p100` project artifact registration backed by artifact lineage
- canonical `sequence`, `chapter_1`, and `story_bible` artifact registration backed by artifact lineage
  `story_bible` is canonical and internally consumable today, but it is not yet exposed through a public `/projects/{project_id}` artifact route.
- public projection endpoints for step records and artifact lineage on jobs and checker runs
- public inspect projections now support optional `attempt`, `limit`, and `offset` query parameters with stable envelope metadata
- runtime phases no longer mark jobs `COMPLETED` before step persistence, lineage persistence, and project artifact registration succeed
- role-model checker scaffolding
- story-development backend foundations for editable flow, brainstorm, foundation, story knowledge, planning, drafting, story-decision review, review routing, review/inspect persistence, the first non-branching story-development API routes, and branching API routes
- story-branching persistence and service foundations for branch identity, branch-point linkage, branch state references, active-branch selection, branch comparison records, branch merge decisions, and branching service behavior

Current planning reference docs:

- `docs/Narrative SRS v0.3.md`
- `docs/Frontend Design SRS v0.4.md`
- `docs/Story Development Product Spec v0.1.md`
- `docs/Story Development Canonical Contract v0.1.md`
- `docs/Story Arc Paradigm Blueprint v0.1.md`

Major work still ahead:

- runtime phase expansion beyond the current `P-100` through `P-400` set
- orchestrator/compiler upstream artifact selection and provenance hardening
- production-grade checker execution
- richer runtime telemetry
- broader integration and failure-mode testing
