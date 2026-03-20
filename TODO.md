# TODO

## Core Runtime

- [ ] Build the real inference and model runtime layer.
- [ ] Replace in-process background stubs with a true worker or lease-based executor.
- [ ] Rebuild the orchestrator/compiler path on top of durable state.
- [ ] Expand the role-model checker beyond stub execution.

## Protocol Hardening

- [x] Persist immutable request snapshots and append-only event history for jobs and checker runs.
- [x] Add baseline attempt-lineage fields for jobs and checker runs.
- [x] Enforce the current run-state transition rules in services.
- [x] Return `202 Accepted` from job and checker start endpoints with status polling targets.
- [ ] Introduce first-class attempt or step records instead of relying on a single mutable run row plus event stream.
- [ ] Add queue idempotency keys, retry metadata, and duplicate-submission handling.
- [ ] Add worker claim or lease semantics with stale-lease handling.
- [ ] Make status endpoints pure persisted projections over worker-managed state.
- [ ] Add structured runtime telemetry for backend identity, hashes, token usage, and finish reasons.

## Persistence

- [x] Add SQLite-backed operational persistence.
- [x] Harden SQLite with foreign keys, WAL mode, busy timeout, indexes, and schema versioning.
- [x] Move project reconciliation into an explicit sync or repair flow.
- [ ] Extend persistence to support orchestration attempts, retries, and richer artifact lineage.

## Frontend

- [x] Build the current writer workflow prototype.
- [x] Add status polling and role-model checker result display.
- [ ] Replace placeholder runtime messaging with production workflow copy.
- [ ] Expand authoring, review, and artifact workflows to match the target product experience.

## Testing

- [x] Add smoke coverage for the current API surface.
- [x] Add persistence coverage for jobs, checker runs, and project projections.
- [ ] Add failure-mode tests for duplicate submission, stale lease handling, partial persistence failure, and lock contention.
- [ ] Add broader integration coverage for orchestration and runtime behavior.
