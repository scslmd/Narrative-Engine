# Failure Mode Test Matrix v0.1

This document extracts the async protocol failure cases into a test-planning checklist.

It is intentionally implementation-neutral so it can guide:

- unit tests
- persistence tests
- integration tests
- future queue/worker recovery tests

## Priority 0

- [ ] request snapshot is durable before a run leaves `ACCEPTED`
- [ ] duplicate submission with same idempotency key returns the same logical run
- [ ] forbidden state transitions are rejected
- [ ] terminal states cannot be reactivated in place
- [ ] a failed report-file write does not erase checker-run provenance in the primary database

## Priority 1

- [ ] lease claim is atomic under concurrent claim attempts
- [ ] stale lease recovery emits deterministic requeue events
- [ ] partial persistence failure cannot produce `COMPLETED`
- [ ] canonical artifact pointers update only after validation succeeds
- [ ] retryable failures create new attempts instead of mutating prior attempts

## Priority 2

- [ ] database busy/lock contention is classified as retryable storage failure
- [ ] event stream and materialized projection agree after restart
- [ ] orphaned logs/results are rejected by foreign-key enforcement
- [ ] schema upgrade preserves historical runs, events, and attempts

## Coverage Groups

### API Contract

- [ ] enqueue endpoints return acceptance semantics rather than inline completion semantics
- [ ] status endpoints are projection-only and do not trigger mutation
- [ ] rerun semantics are explicit rather than implicit duplicate submission

### Run State Machine

- [ ] `ACCEPTED -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED`
- [ ] failure path from each active state is deterministic
- [ ] cancellation path is deterministic

### Recovery / Resume

- [ ] crash before lease claim
- [ ] crash after lease claim
- [ ] crash during step execution
- [ ] crash during validation
- [ ] crash during persistence

### Telemetry / Provenance

- [ ] model/backend identity captured
- [ ] prompt/input/output hashes captured
- [ ] finish reason captured
- [ ] error category captured
- [ ] report/artifact lineage captured

## Notes

- This matrix should be implemented incrementally as the serial queue/worker runtime is introduced.
- Items above are intentionally written so they can be turned into tests without redesigning the protocol first.
