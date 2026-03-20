# Failure Mode Test Matrix v0.1

This document extracts the async protocol failure cases into a test-planning checklist.

It is intentionally implementation-neutral so it can guide:

- unit tests
- persistence tests
- integration tests
- future queue/worker runtime tests

## Priority 0

- [x] request snapshot is durable before a run leaves `ACCEPTED`
- [x] duplicate submission with same idempotency key returns the same logical run
- [x] forbidden state transitions are rejected
- [x] terminal states cannot be reactivated in place
- [x] a failed checker persistence step after a result insert does not erase checker-run provenance in the primary database

## Priority 1

- [ ] lease claim is atomic under concurrent claim attempts
- [x] stale lease handling emits deterministic requeue events
- [x] claim and reclaim events persist structured executor or stale-lease context
- [x] partial persistence failure cannot silently erase already-committed checker results
- [ ] canonical artifact pointers update only after validation succeeds
- [x] retryable failures create new attempts instead of mutating prior attempts

## Priority 2

- [x] enqueue-time database busy/lock contention fails without partial rows for jobs and checker runs
- [ ] database busy/lock contention is classified as retryable storage failure
- [ ] event stream and materialized projection agree after restart
- [ ] orphaned logs/results are rejected by foreign-key enforcement
- [ ] schema upgrade preserves historical runs, events, and attempts

## Coverage Groups

### API Contract

- [x] enqueue endpoints return acceptance semantics rather than inline completion semantics
- [x] status endpoints are projection-only and do not trigger mutation
- [x] rerun semantics are explicit rather than implicit duplicate submission

### Run State Machine

- [ ] `ACCEPTED -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED`
- [ ] failure path from each active state is deterministic
- [ ] cancellation path is deterministic

### Resume / Requeue

- [ ] crash before lease claim
- [ ] crash after lease claim
- [ ] crash during step execution
- [ ] crash during validation
- [x] failure during checker-result follow-up persistence preserves accepted run plus inserted result rows

### Telemetry / Provenance

- [x] executor-name and queue-delay claim telemetry captured
- [x] reclaim events preserve stale-lease context and retry reason
- [x] step-record and artifact-lineage required fields are locked by fixture coverage
- [x] live report/artifact lineage is persisted according to `docs/Step Record Blueprint v0.1.md`
- [ ] model/backend identity captured
- [ ] prompt/input/output hashes captured
- [ ] finish reason captured
- [ ] error category captured

## Notes

- This matrix should be implemented incrementally as the serial queue/worker runtime is introduced.
- Items above are intentionally written so they can be turned into tests without redesigning the protocol first.
- Current executable coverage is intentionally scoped to deterministic cases the present architecture can support:
  - checker result insertion followed by a forced heartbeat-update failure
  - enqueue-time SQLite exclusive-lock failures for jobs and checker runs with zero residual rows
