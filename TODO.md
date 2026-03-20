# TODO

## Restore Readiness

- [ ] Perform a full restore-readiness review of the recovered `F:\Dev\Narrative-Recover` workspace.
- [ ] Audit the reconstructed code and docs for gaps between the recovered baseline and the lost implementation.
- [ ] Record a prioritized list of resume blockers, behavioral gaps, and missing rebuild slices.

## Core Rebuild

- [ ] Rebuild the persistence/database layer beyond the current stubbed baseline.
- [ ] Rebuild the inference/model runtime layer.
- [ ] Rebuild the orchestrator/compiler path.
- [ ] Expand the role-model checker beyond stub behavior.
- [ ] Add broader automated tests beyond `tests/test_recovered_smoke.py`.

## Protocol Hardening

- [x] Write the deterministic async protocol blueprint covering acceptance semantics, strict state machine, append-only events, idempotency, retries, lease rules, telemetry, and artifact-lineage rules.
- [x] Write the async failure-mode test matrix for acceptance, recovery/resume, state integrity, retry behavior, telemetry completeness, and SQLite failure cases.
- [x] Serial Step 1: persist immutable request snapshots and append-only event history for jobs and checker runs.
- [ ] Serial Step 2: introduce explicit attempt records, run/step state validation, and strict transition rules in persistence and services.
- [ ] Serial Step 3: convert create/start endpoints to acceptance semantics and add read-only status projections over persisted state.
- [ ] Serial Step 4: add worker claim/lease semantics plus stale-lease recovery.
- [ ] Serial Step 5: add structured runtime telemetry, artifact lineage, idempotency, and retry metadata.
- [ ] Serial Step 6: add failure-mode tests for restart, duplicate submission, stale lease recovery, and storage contention.
- [ ] Convert `POST /jobs/create` into a true enqueue endpoint that persists an immutable request snapshot and returns `202 Accepted`.
- [ ] Convert role-model check start/run into a true enqueue endpoint that persists the full request payload in the primary database before execution.
- [x] Introduce a strict run state machine for jobs and checker runs in the service layer and reject illegal transitions for the current persisted run records.
- [ ] Extend the strict run state machine into persistence-level attempt/step records instead of a single mutable run row.
- [ ] Add append-only phase/event history for jobs and checker runs instead of relying only on mutable latest-state rows.
- [ ] Add worker-claim or lease semantics for runnable jobs/checker runs so execution can resume after interruption.
- [ ] Add attempt counts, retry metadata, and idempotency keys for jobs and checker runs.
- [ ] Persist full checker-run provenance in the database, including request payload, selected model, critic profile, and execution metadata.
- [ ] Add per-step execution records for each role or pipeline phase with timing, finish reason, and error code.
- [ ] Unify telemetry into structured event records instead of plain text log rows only.
- [ ] Add prompt/input hashes, output hashes, artifact lineage, backend identity, token usage, and timeout/error categories to runtime telemetry.
- [x] Harden SQLite configuration with foreign keys, WAL mode, busy timeout, indexes, and schema versioning/migration support.
- [x] Add foreign-key constraints and supporting indexes for persisted jobs, logs, checker runs, checker results, and project artifacts.
- [x] Stop mutating project registry state as a side effect of `ProjectService` construction; move project sync into an explicit reconciliation/repair operation.
- [x] Establish a single authoritative source of truth for project metadata and artifact lookup instead of mixed filesystem scans and DB reads.
- [ ] Make status endpoints read-only projections over persisted state rather than reflections of inline request execution.
- [x] Convert recovered job creation and checker start/run endpoints to `202 Accepted` responses with persisted `Location` polling targets and post-response background stub execution.
- [ ] Remove the remaining in-process background stub executor and replace it with a real worker/lease runner so status endpoints become pure persisted projections.
- [ ] Implement the failure-mode matrix incrementally as persistence and worker/runtime wiring become real.

## Adversarial Follow-up

- [ ] Replace synchronous inline stub execution in `POST /jobs/create` with acceptance-only behavior and deferred execution semantics.
- [ ] Replace synchronous inline stub execution in role-model checker start/run with acceptance-only behavior and deferred execution semantics.
- [x] Add attempt lineage fields for jobs and checker runs plus append-only run events carrying `logical_run_id` and `attempt_number`.
- [ ] Split attempt lineage into first-class attempt or step records instead of relying on a single mutable run row plus event stream.
- [ ] Add retry metadata and idempotency keys for queue-facing jobs and checker runs.
- [x] Enforce the documented run state machine in code and reject illegal transitions for the current synchronous stub flow.
- [ ] Persist idempotency keys for queue-facing endpoints and define duplicate-submission behavior in code.
- [ ] Persist backend/runtime provenance fields beyond request payloads, including finish reason, backend identity, and structured error category.
- [ ] Add structured step telemetry fields for prompt/input hash, output hash, artifact lineage, token counts, and timeout classification.
- [x] Enable SQLite foreign keys, WAL mode, busy timeout, and schema version/migration tracking in the shared connection layer.
- [x] Add indexes and relational constraints for event tables, logs, results, and artifact tables.
- [x] Remove `ProjectService` constructor side effects that mutate persisted registry state during ordinary reads.
- [x] Move project reconciliation into an explicit sync/repair path and make normal project reads use a single authoritative projection.
- [ ] Add executable tests for duplicate submission handling, illegal transition rejection, stale lease recovery, partial persistence failure, and storage lock contention.

## Frontend And Parity

- [x] Review frontend parity beyond the current recovered UI shell in `frontend/index.html`.
- [x] Verify docs, SRS notes, and implementation are synchronized.

## Repo Cleanup

- [x] Decide whether generated role-model checker run reports under `data/role_model_checker_runs` should remain tracked or be ignored going forward.
