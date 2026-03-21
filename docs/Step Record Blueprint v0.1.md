# Step Record Blueprint v0.1

## Purpose

This document defines the current backend contract for per-step execution records and artifact lineage.

Current implementation status:

- implemented now: field requirements, example records, lineage rules, fixture-backed spec coverage, live SQLite tables, repository methods, and local-executor writes for step records and artifact lineage
- not yet implemented: full orchestrator step emission beyond the current executor-backed phase set
- no queue or worker redesign is implied by this contract layer

## Scope

This blueprint applies to:

- pipeline job steps such as `architect`, `sequencer`, `drafter`, `compiler`, and future validation stages
- checker steps for role or model evaluations
- future artifact registration produced by a specific step attempt

## Step Record Goals

Each step record should answer:

- which logical run and attempt produced this step
- what step was executing
- what model/profile/backend context was used
- what inputs were consumed
- what outputs were produced
- why the step finished
- which artifacts became canonical and which did not

## Required Step Record Fields

Each persisted step record should include:

- `step_record_id`
- `logical_run_id`
- `run_id`
- `run_kind`
- `attempt_number`
- `step_name`
- `step_index`
- `state`
- `project_id`
- `model_id`
- `critic_profile`
- `backend_name`
- `backend_version`
- `input_hash`
- `output_hash`
- `prompt_hash`
- `input_artifact_refs`
- `output_artifact_refs`
- `started_at`
- `finished_at`
- `duration_seconds`
- `finish_reason`
- `error_code`
- `error_category`
- `executor_id`
- `lease_owner`

## Step State Expectations

Step states should remain compatible with the top-level async protocol:

`PENDING -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED | FAILED | CANCELLED`

Rules:

- step records are append-only or versioned by attempt; they must not be overwritten in place to erase prior outcomes
- a failed step record must still preserve hashes, finish reason, and any temporary artifact refs that were produced
- step projection rows may exist, but event history plus step records must remain sufficient to reconstruct what happened

## Artifact Lineage Goals

Artifact lineage should answer:

- which step and attempt produced an artifact
- whether that artifact was temporary, candidate, canonical, superseded, or rejected
- which prior artifact version it superseded
- which source artifacts or prompts it depended on
- whether validation succeeded before canonical registration

## Required Artifact Lineage Fields

Each artifact lineage record should include:

- `artifact_lineage_id`
- `logical_run_id`
- `run_id`
- `run_kind`
- `attempt_number`
- `step_name`
- `project_id`
- `artifact_role`
- `artifact_kind`
- `path`
- `content_hash`
- `status`
- `validation_state`
- `produced_at`
- `registered_at`
- `supersedes_artifact_lineage_id`
- `source_artifact_refs`
- `source_content_hashes`
- `output_of_step_record_id`

## Artifact Lineage Statuses

The minimum lineage statuses should be:

- `TEMPORARY`
- `CANDIDATE`
- `CANONICAL`
- `SUPERSEDED`
- `REJECTED`

Rules:

- temporary writes are not canonical lineage
- failed validation must produce `REJECTED` or leave artifacts `TEMPORARY`, but must not silently promote them
- only `PERSISTING` may promote a candidate artifact to `CANONICAL`
- a new canonical artifact should supersede a prior canonical artifact explicitly rather than replacing history in place
- failed attempts must never replace canonical artifact pointers

## Current Implementation Boundary

The current slice now includes:

- step record tables and repositories
- artifact lineage tables and repositories
- service-level helpers for step and lineage writes
- local-executor emission for pipeline steps, checker role steps, and checker report lineage
- tests that validate field presence, lineage expectations, and FK behavior

This blueprint still does not require:

- runtime token telemetry integration
- full orchestrator wiring
- dedicated API read models for step and lineage browsing

## Companion Contract Test

The fixture and test pair in:

- `tests/fixtures/step_record_contract_v0_1.json`
- `tests/test_step_record_spec.py`

exist to keep this contract stable until the real persistence/runtime slice is implemented.

Additional persistence tests now live in:

- `tests/test_step_record_persistence.py`
