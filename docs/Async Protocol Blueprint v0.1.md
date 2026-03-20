# Async Protocol Blueprint v0.1

## Purpose

This document defines the hardened async protocol for work that can be completed before the full queue/worker runtime is integrated.

It exists to remove ambiguity from the current implementation state and to establish one deterministic protocol for:

- pipeline jobs
- role-model checker runs
- future per-role execution steps

This is a design/specification document only. It does not imply that the current implementation already satisfies the protocol.

## Protocol Goals

- separate request acceptance from execution
- make status transitions explicit and finite
- make restart/resume behavior deterministic
- make duplicate submission behavior deterministic
- make telemetry and provenance durable enough for rebuild-time debugging
- make future worker integration a matter of wiring, not redesign

## Canonical Async Model

The system should treat both pipeline jobs and role-model checks as `runs`.

Each run has:

- a stable `run_id`
- a `run_kind`: `pipeline_job` or `role_model_check`
- an immutable request snapshot
- a strict lifecycle state
- append-only event history
- optional child step records
- final artifacts and/or report pointers

## Acceptance Contract

Queue-facing endpoints should follow the same contract:

- validate request
- persist immutable request snapshot
- assign `run_id`
- assign initial state `ACCEPTED`
- emit `RUN_ACCEPTED` event
- return `202 Accepted`

Endpoints covered by this contract:

- `POST /jobs/create`
- `POST /role-model-checker/start`

Compatibility note:

- `POST /role-model-checker/run` may temporarily remain as a compatibility alias, but it should be treated as the same enqueue contract and not as a synchronous execute-now path.

## Strict State Machine

All runs must use the same top-level state machine:

`ACCEPTED -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED | FAILED | CANCELLED`

Rules:

- `ACCEPTED`: request persisted, not yet leased by a worker
- `CLAIMED`: a worker/runner has an active lease and intends to execute
- `RUNNING`: role or phase work is actively executing
- `VALIDATING`: outputs exist and are undergoing deterministic checks
- `PERSISTING`: validated outputs are being committed to durable storage/artifact registry
- `COMPLETED`: terminal success
- `FAILED`: terminal failure after retry policy is exhausted or failure is non-retryable
- `CANCELLED`: terminal operator/user cancellation

Forbidden transitions:

- terminal states must not transition back to active states
- `ACCEPTED` must not jump directly to `COMPLETED`
- `RUNNING` must not bypass `VALIDATING` or `PERSISTING` for artifact-producing work

Allowed retry transition:

- `FAILED -> ACCEPTED` is not allowed in-place
- retries must create a new attempt record under the same logical run identity

## Step Model

Runs may contain step executions.

Pipeline job steps should eventually include:

- `architect`
- `sequencer`
- `drafter`
- `critic`

Role-model checker steps should include one step per tested role/model combination.

Each step record should include:

- `run_id`
- `attempt_number`
- `step_name`
- `step_index`
- `state`
- `model_id`
- `critic_profile` when relevant
- `input_hash`
- `output_hash`
- `started_at`
- `finished_at`
- `finish_reason`
- `error_code`
- `artifact_refs`

## Append-Only Event Model

Mutable latest-state rows are allowed as projections, but they are not sufficient as the protocol source of truth.

Each run should have append-only events with:

- `event_id`
- `run_id`
- `attempt_number`
- `step_name` nullable
- `event_type`
- `from_state` nullable
- `to_state` nullable
- `occurred_at`
- `actor_type`: `api`, `worker`, `system`, `user`
- `actor_id`
- `payload_json`

Minimum event types:

- `RUN_ACCEPTED`
- `RUN_CLAIMED`
- `RUN_STARTED`
- `STEP_STARTED`
- `STEP_PROGRESS`
- `STEP_OUTPUT_WRITTEN`
- `STEP_VALIDATION_FAILED`
- `STEP_COMPLETED`
- `RUN_VALIDATING`
- `RUN_PERSISTING`
- `RUN_COMPLETED`
- `RUN_FAILED`
- `RUN_CANCELLED`
- `LEASE_EXPIRED`
- `RUN_REQUEUED`

Projection rule:

- status endpoints should read from a projection derived from events plus current run/step materialized views
- tooling should be able to reconstruct the last known state from the event stream alone

## Idempotency Semantics

All enqueue endpoints must support idempotency keys.

Recommended key shape:

- client-supplied `Idempotency-Key` header preferred
- if absent, derive a deterministic request hash from canonicalized request payload plus route identity

Run creation semantics:

- if a matching idempotency key exists for a non-terminal run, return the existing `run_id`
- if a matching idempotency key exists for a terminal successful run, return the existing `run_id` unless the caller explicitly requests a rerun
- reruns must create a new attempt lineage and must not overwrite the original request snapshot

Idempotency scope:

- keys should be scoped by `run_kind`
- keys should include `project_id` when applicable
- checker runs should include requested roles, selected models, and critic profile in the canonical payload

## Retry Semantics

Retries must be explicit and bounded.

Required fields:

- `attempt_number`
- `parent_run_id` or `logical_run_id`
- `retry_reason`
- `retryable` boolean
- `max_attempts`

Rules:

- retryable failures include lease expiry, transient backend timeout, temporary DB lock, and retryable model backend errors
- non-retryable failures include invalid request schema, deterministic validation failure when policy says fail-fast, and operator cancellation
- a retry must emit `RUN_REQUEUED` and start a new attempt record
- attempts must not overwrite prior attempt telemetry or artifacts

## Lease / Claim Semantics

This document does not implement the worker, but the protocol must reserve for it now.

Required lease fields:

- `lease_owner`
- `lease_expires_at`
- `claimed_at`

Rules:

- only `ACCEPTED` runs may be claimed
- claim must be atomic
- expired leases may be reclaimed by another worker
- reclaiming must emit `LEASE_EXPIRED` and `RUN_REQUEUED` events before a new claim

## Telemetry Contract

Plain text logs are insufficient for the rebuild path.

Minimum telemetry fields per attempt/step:

- `run_id`
- `attempt_number`
- `step_name`
- `run_kind`
- `project_id`
- `model_id`
- `critic_profile`
- `backend_name`
- `backend_version`
- `prompt_hash`
- `input_artifact_hashes`
- `output_hash`
- `token_counts` if available
- `duration_seconds`
- `finish_reason`
- `error_code`
- `error_category`
- `timeout_seconds`
- `report_path` or artifact refs

Structured telemetry should be durable even when text logs are also emitted.

## Artifact Lineage Rules

Artifacts produced by a run should be registered only after validation succeeds.

Rules:

- writes in `RUNNING` are temporary
- validation occurs before canonical artifact registration
- canonical artifact pointers update only during `PERSISTING`
- failed attempts must not silently replace canonical artifact pointers

## Status Endpoint Projection Rules

`GET /jobs/{job_id}/status` and `GET /role-model-checker/{run_id}/status` should eventually expose read-only projections with:

- current top-level state
- current step name
- current attempt number
- exact progress counters
- last heartbeat
- terminal error code/message when applicable
- stable report/artifact pointers only after successful persistence

`detail` should be treated as diagnostic text, not as a protocol field.

## Failure-Mode Test Matrix

The following matrix should drive implementation-time tests before serial runtime integration is considered complete.

### Acceptance And Idempotency

- duplicate submission with same idempotency key returns same `run_id`
- duplicate submission without idempotency key creates distinct runs
- rerun request after terminal completion creates new attempt lineage only when explicitly requested
- malformed payload fails before run creation

### State Machine Integrity

- forbidden state transitions are rejected
- terminal states cannot be mutated back to active states
- run cannot skip required intermediate states
- projection remains consistent with event history

### Lease / Reclaim

- runner crash after `CLAIMED` but before `RUNNING` leaves reclaimable lease
- runner crash during `RUNNING` leads to expired lease and requeue behavior
- stale lease is reclaimed exactly once
- double claim is impossible under contention

### Persistence And Atomicity

- partial failure during `PERSISTING` does not mark run `COMPLETED`
- artifact pointer update is atomic with persisted success transition
- request snapshot is durable before any active execution state
- checker request provenance is still available even if report-file write fails

### Retry Behavior

- retryable timeout creates a new attempt without overwriting prior telemetry
- non-retryable validation failure ends terminally without requeue
- max-attempt policy stops infinite retry loops

### Telemetry Completeness

- each attempt records model/backend identity
- each attempt records prompt/input/output hashes
- each terminal failure records error category and finish reason
- projection can be rebuilt from events plus materialized state

### SQLite / Storage Failure Cases

- busy database returns retryable storage failure and does not corrupt state
- schema upgrade preserves prior runs and events
- foreign-key enforcement rejects orphaned logs/results

## Recommended Pre-Integration Deliverables

Before serial worker/runtime integration starts, the repo should contain:

- a protocol state machine spec
- an event taxonomy
- idempotency and retry rules
- a lease semantics spec
- a failure-mode test plan

This document is intended to satisfy those design prerequisites before worker/runtime integration.
