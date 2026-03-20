# Step and Lineage API Projection Blueprint v0.1

## Purpose

This document defines deterministic read-only API projections for persisted step records and artifact lineage.

It covers:

- `GET /jobs/{job_id}/steps`
- `GET /jobs/{job_id}/lineage`
- `GET /role-model-checker/{run_id}/steps`
- `GET /role-model-checker/{run_id}/lineage`

This blueprint is intentionally limited to projection behavior. It does not redefine queue semantics, worker behavior, or write-path persistence.

## Goals

These endpoints should make it possible to:

- inspect step execution history for a single run
- inspect artifact lineage for a single run
- distinguish current-attempt views from full historical views
- support deterministic UI rendering and operator debugging
- keep response order and pagination behavior stable across runtimes

## Common Projection Rules

All four endpoints are read-only.

All four endpoints should:

- return persisted data only
- avoid deriving synthetic records that do not exist in storage
- use stable ascending sort order by default
- support deterministic pagination
- preserve attempt lineage rather than collapsing history

These endpoints should not:

- mutate state
- trigger reconciliation
- trigger execution
- hide prior attempts by default unless explicitly filtered

## Common Query Parameters

The following query parameters should be supported uniformly across all four endpoints.

- `attempt`
  - optional integer
  - if provided, return only records for that attempt number
- `cursor`
  - optional opaque cursor string
  - if omitted, begin at the first record in the endpoint's default sort order
- `limit`
  - optional integer
  - default `50`
  - minimum `1`
  - maximum `200`

Optional future filters may be added later, but this blueprint locks only `attempt`, `cursor`, and `limit`.

## Pagination Model

Pagination should be cursor-based, not offset-based.

Reason:

- step and lineage tables are append-heavy
- cursor pagination is deterministic under concurrent writes
- offset pagination becomes unstable as new rows arrive

Cursor assumptions:

- the cursor should encode the last returned stable sort key
- the cursor format is implementation-private
- clients must treat the cursor as opaque

Paging contract:

- if more rows exist after the current page, return `next_cursor`
- if no more rows exist, return `next_cursor: null`
- response rows must always be returned in the documented sort order

## Response Envelope

Each endpoint should return a projection envelope with run metadata plus paged items.

Common top-level shape:

```json
{
  "run_kind": "pipeline_job",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "current_attempt_number": 1,
  "returned_attempt_number": null,
  "items": [],
  "sort": {
    "field_order": ["attempt_number", "step_index", "step_record_id"],
    "direction": "asc"
  },
  "page": {
    "limit": 50,
    "next_cursor": null,
    "has_more": false
  }
}
```

Field rules:

- `run_kind`
  - `pipeline_job` for `/jobs/...`
  - `role_model_check` for `/role-model-checker/...`
- `run_id`
  - the concrete accepted run identifier from the route
- `logical_run_id`
  - the logical lineage identifier shared across attempts
- `current_attempt_number`
  - latest known attempt for the run
- `returned_attempt_number`
  - `null` when multiple attempts may be present
  - set to the requested attempt when `attempt` is supplied
- `items`
  - endpoint-specific array described below
- `sort`
  - explicit declaration of response ordering
- `page`
  - deterministic pagination state

## Error Contract

The four endpoints should share one error model.

- `404 Not Found`
  - run id does not exist
- `422 Unprocessable Entity`
  - invalid `attempt`, `cursor`, or `limit`

These endpoints should not use `409` because they are projections, not mutation routes.

## Step Projection Item Shape

The step endpoints should return the following item shape.

```json
{
  "step_record_id": 12,
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_kind": "pipeline_job",
  "attempt_number": 1,
  "step_name": "architect",
  "step_index": 1,
  "state": "COMPLETED",
  "project_id": "science-fantasy-test",
  "model_id": "qwen2.5-32b-instruct-q4_k_m",
  "critic_profile": null,
  "backend_name": "local_executor_stub",
  "backend_version": "v0",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "prompt_hash": "sha256:...",
  "input_artifact_refs": [],
  "output_artifact_refs": [],
  "started_at": "2026-03-20T18:15:52.000000+00:00",
  "finished_at": "2026-03-20T18:15:53.000000+00:00",
  "duration_seconds": 1.0,
  "finish_reason": "completed",
  "error_code": null,
  "error_category": null,
  "executor_id": "local-job-worker",
  "lease_owner": "job-worker-1"
}
```

Field expectations:

- the item shape should map directly to persisted step-record fields
- nullable fields should remain present with `null` values when unknown
- `input_artifact_refs` and `output_artifact_refs` should remain arrays even when empty
- no freeform projection-only fields should be added without updating this blueprint

## Lineage Projection Item Shape

The lineage endpoints should return the following item shape.

```json
{
  "artifact_lineage_id": 7,
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_kind": "pipeline_job",
  "attempt_number": 1,
  "step_name": "architect",
  "project_id": "science-fantasy-test",
  "artifact_role": "outline",
  "artifact_kind": "json",
  "path": "data/projects/science-fantasy-test/sequences.json",
  "content_hash": "sha256:...",
  "status": "CANONICAL",
  "validation_state": "PASSED",
  "produced_at": "2026-03-20T18:15:53.000000+00:00",
  "registered_at": "2026-03-20T18:15:53.200000+00:00",
  "supersedes_artifact_lineage_id": null,
  "source_artifact_refs": [],
  "source_content_hashes": [],
  "output_of_step_record_id": 12
}
```

Field expectations:

- the item shape should map directly to persisted artifact-lineage fields
- `source_artifact_refs` and `source_content_hashes` should remain arrays even when empty
- `supersedes_artifact_lineage_id` should be `null` when the artifact does not supersede a prior canonical artifact

## GET /jobs/{job_id}/steps

### Responsibility

This endpoint returns persisted step-record projections for one pipeline job run.

It should:

- expose step history across attempts for the addressed job
- support filtering to one attempt via `attempt`
- preserve step ordering within each attempt
- return enough metadata for operator inspection and UI progress history

It should not:

- infer missing steps from workflow preferences
- collapse failed and retried attempts into one synthesized record

### Sort Order

Default sort order:

1. `attempt_number ASC`
2. `step_index ASC`
3. `step_record_id ASC`

This order is the stable paging key for job step projections.

### Response Shape

```json
{
  "run_kind": "pipeline_job",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "current_attempt_number": 2,
  "returned_attempt_number": null,
  "items": [],
  "sort": {
    "field_order": ["attempt_number", "step_index", "step_record_id"],
    "direction": "asc"
  },
  "page": {
    "limit": 50,
    "next_cursor": null,
    "has_more": false
  }
}
```

`items` must contain step projection items.

## GET /jobs/{job_id}/lineage

### Responsibility

This endpoint returns persisted artifact-lineage projections for one pipeline job run.

It should:

- expose all lineage rows tied to the addressed job
- preserve canonical and superseded history
- make temporary, candidate, canonical, superseded, and rejected artifacts visible without rewriting history

It should not:

- return only the latest canonical artifact unless a future explicit filter requests that
- infer lineage links that were not persisted

### Sort Order

Default sort order:

1. `attempt_number ASC`
2. `produced_at ASC`
3. `artifact_lineage_id ASC`

This order keeps lineage deterministic even when multiple artifacts are produced by the same step.

### Response Shape

```json
{
  "run_kind": "pipeline_job",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "current_attempt_number": 2,
  "returned_attempt_number": null,
  "items": [],
  "sort": {
    "field_order": ["attempt_number", "produced_at", "artifact_lineage_id"],
    "direction": "asc"
  },
  "page": {
    "limit": 50,
    "next_cursor": null,
    "has_more": false
  }
}
```

`items` must contain lineage projection items.

## GET /role-model-checker/{run_id}/steps

### Responsibility

This endpoint returns persisted step-record projections for one role-model checker run.

It should:

- expose one row per checker step execution
- preserve multi-attempt history for the checker run
- support deterministic UI rendering of role-by-role execution history

It should not:

- collapse repeated role checks across attempts
- synthesize final role status from checker results when no step row exists

### Sort Order

Default sort order:

1. `attempt_number ASC`
2. `step_index ASC`
3. `step_record_id ASC`

The sorting contract matches the job step endpoint so clients can reuse rendering logic.

### Response Shape

```json
{
  "run_kind": "role_model_check",
  "run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "logical_run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "current_attempt_number": 1,
  "returned_attempt_number": null,
  "items": [],
  "sort": {
    "field_order": ["attempt_number", "step_index", "step_record_id"],
    "direction": "asc"
  },
  "page": {
    "limit": 50,
    "next_cursor": null,
    "has_more": false
  }
}
```

`items` must contain step projection items.

## GET /role-model-checker/{run_id}/lineage

### Responsibility

This endpoint returns persisted artifact-lineage projections for one role-model checker run.

It should:

- expose report artifacts and any future checker-produced artifacts
- preserve attempt history and supersession relationships
- allow the UI or operators to inspect canonical report registration without parsing filesystem state

It should not:

- assume only one report artifact exists
- hide rejected or superseded checker artifacts

### Sort Order

Default sort order:

1. `attempt_number ASC`
2. `produced_at ASC`
3. `artifact_lineage_id ASC`

### Response Shape

```json
{
  "run_kind": "role_model_check",
  "run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "logical_run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "current_attempt_number": 1,
  "returned_attempt_number": null,
  "items": [],
  "sort": {
    "field_order": ["attempt_number", "produced_at", "artifact_lineage_id"],
    "direction": "asc"
  },
  "page": {
    "limit": 50,
    "next_cursor": null,
    "has_more": false
  }
}
```

`items` must contain lineage projection items.

## Attempt Filtering Rules

When `attempt` is omitted:

- return records across all attempts in the endpoint's default sort order
- keep `returned_attempt_number` as `null`

When `attempt` is provided:

- return only records for that attempt
- set `returned_attempt_number` to the requested attempt number
- return `404` only if the run does not exist
- return an empty `items` array if the run exists but that attempt has no rows for the endpoint

## Empty-State Rules

If the run exists but no rows are present for the requested projection:

- return `200`
- return a valid envelope
- return `items: []`
- return `has_more: false`
- return `next_cursor: null`

This allows clients to distinguish "run exists but no persisted step or lineage rows yet" from "run does not exist".

## Projection Stability Requirements

The endpoint contract should remain stable under retries.

Specifically:

- prior-attempt rows must remain visible unless an explicit `attempt` filter narrows the response
- canonical lineage rows must not erase superseded lineage history
- sort order must not depend on transient status text
- response fields must be sourced from persisted columns, not reconstructed from logs

## Implementation Boundary

This blueprint does not require:

- nested child collections inside each item
- inline event history in the same response
- write endpoints for steps or lineage
- real-runtime telemetry beyond the persisted fields already defined by the step and lineage contracts

Those can be layered later, but these four projection endpoints should remain deterministic and minimal.
