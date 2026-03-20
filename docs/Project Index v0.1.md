# Project Index v0.1

Current project layers:

- `docs/`: product, frontend, protocol, and validation documents
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
- role-model checker scaffolding

Major work still ahead:

- real inference/runtime integration
- orchestrator/compiler flow
- production-grade checker execution
- projection endpoints for step records and artifact lineage
- richer runtime telemetry
- broader integration and failure-mode testing
