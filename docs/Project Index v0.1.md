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
- append-only event history and baseline attempt-lineage fields
- status polling for jobs and checker runs
- role-model checker scaffolding

Major work still ahead:

- real inference/runtime integration
- worker-managed async execution
- orchestrator/compiler flow
- production-grade checker execution
- broader integration and failure-mode testing
