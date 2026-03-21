# Step and Lineage API Projection Blueprint v0.1

## Purpose

This document defines the first implemented public projection slice for persisted step records and artifact lineage.

It covers:

- `GET /jobs/{job_id}/steps`
- `GET /jobs/{job_id}/lineage`
- `GET /role-model-checker/{run_id}/steps`
- `GET /role-model-checker/{run_id}/lineage`

This document is intentionally aligned to the current implementation only. It describes the current attempt-filter support, but not future pagination or expanded projection metadata that are not yet present in the API.

## Current Slice Summary

The first implementation slice exposes:

- read-only projections only
- exactly one top-level run identifier field
- a flat `items` array
- a minimal `meta` object with ordering information only
- optional attempt filtering only
- no pagination
- no inline event history

The current endpoints return persisted step-record and artifact-lineage rows for the addressed run id across all attempts currently stored for that run.

## Shared Endpoint Behavior

All four endpoints:

- are `GET` routes
- are read-only
- return persisted projection data only
- expose exactly three top-level keys:
  - `job_id` or `run_id`
  - `items`
  - `meta`
- return `404` if the addressed job or checker run does not exist
- return `200` with `items: []` if the run exists but there are no step or lineage rows yet
- support optional `attempt=<positive integer>` filtering
- do not support `cursor`, `limit`, or any other query parameters in this slice

These endpoints do not:

- mutate state
- trigger execution
- trigger reconciliation
- synthesize missing rows

## Error Behavior

Current error behavior is minimal and deterministic.

- `404 Not Found`
  - `GET /jobs/{job_id}/steps`
  - `GET /jobs/{job_id}/lineage`
  - response detail: `Job not found.`
- `404 Not Found`
  - `GET /role-model-checker/{run_id}/steps`
  - `GET /role-model-checker/{run_id}/lineage`
  - response detail: `Role-model check run not found.`

Projection-specific validation in this slice is limited to `422` for invalid non-positive `attempt` values.

Any supplied query string values are outside the documented first-slice contract and should not be treated as supported behavior.

## Envelope Contract

The implemented envelopes are intentionally small.

### Job Step Projection Envelope

```json
{
  "job_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "items": [],
  "meta": {
    "ordered_by": "step_index_asc"
  }
}
```

### Job Lineage Projection Envelope

```json
{
  "job_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "items": [],
  "meta": {
    "ordered_by": "artifact_lineage_id_asc"
  }
}
```

### Checker Step Projection Envelope

```json
{
  "run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "items": [],
  "meta": {
    "ordered_by": "step_index_asc"
  }
}
```

### Checker Lineage Projection Envelope

```json
{
  "run_id": "9f7f1d43-65d2-4e18-8ec4-f6bbf91111b4",
  "items": [],
  "meta": {
    "ordered_by": "artifact_lineage_id_asc"
  }
}
```

## Step Item Shape

The step endpoints return `items` shaped as persisted `StepRecordView` rows.

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
  "model_id": "architect-test-model",
  "critic_profile": null,
  "backend_name": "Fake Architect Runtime",
  "backend_version": null,
  "input_hash": "3d1b...",
  "output_hash": "e02c...",
  "prompt_hash": "f198...",
  "input_artifact_refs": ["manifest"],
  "output_artifact_refs": ["architect_output"],
  "started_at": "2026-03-20T18:15:52.000000+00:00",
  "finished_at": "2026-03-20T18:15:53.000000+00:00",
  "duration_seconds": 1.0,
  "finish_reason": "completed",
  "error_code": null,
  "error_category": null,
  "executor_id": "job-worker-local",
  "lease_owner": "job-worker-local"
}
```

Field rules:

- all fields above are part of the public response shape in this slice
- nullable fields remain present with `null` values when unknown
- `started_at` and `finished_at` are string timestamps or `null`
- `input_artifact_refs` and `output_artifact_refs` are always arrays

## Lineage Item Shape

The lineage endpoints return `items` shaped as persisted `ArtifactLineageView` rows.

```json
{
  "artifact_lineage_id": 7,
  "logical_run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_id": "8bb4c0e0-b531-433c-8f9a-f8e7b458e7de",
  "run_kind": "pipeline_job",
  "attempt_number": 1,
  "step_name": "architect",
  "project_id": "science-fantasy-test",
  "artifact_role": "architect_output",
  "artifact_kind": "markdown",
  "path": "data/projects/science-fantasy-test/exports/p100_architect_output.md",
  "content_hash": "4b22...",
  "status": "CANONICAL",
  "validation_state": "PASSED",
  "produced_at": "2026-03-20T18:15:53.000000+00:00",
  "registered_at": "2026-03-20T18:15:53.200000+00:00",
  "supersedes_artifact_lineage_id": null,
  "source_artifact_refs": ["manifest"],
  "source_content_hashes": [],
  "output_of_step_record_id": 12
}
```

Field rules:

- all fields above are part of the public response shape in this slice
- `produced_at` is required and returned as a string timestamp
- `registered_at` may be `null`
- `source_artifact_refs` and `source_content_hashes` are always arrays

## GET /jobs/{job_id}/steps

### Responsibility

Returns persisted step-record rows for the addressed pipeline job.

### Implemented Response Model

`JobStepsResponse`

Top-level fields:

- `job_id`
- `items`
- `meta`

### Implemented Ordering

Current repository ordering is:

1. `step_index ASC`
2. `step_record_id ASC`

This ordering is surfaced via:

```json
{
  "meta": {
    "ordered_by": "step_index_asc"
  }
}
```

Important limitation:

- the `meta` value does not currently mention the `step_record_id` tie-breaker even though the repository uses it
- the actual stable order is therefore `step_index ASC, step_record_id ASC`

### Empty-State Behavior

If the job exists but has no persisted step records:

- return `200`
- return the job id
- return `items: []`
- return `meta.ordered_by = "step_index_asc"`

## GET /jobs/{job_id}/lineage

### Responsibility

Returns persisted artifact-lineage rows for the addressed pipeline job.

### Implemented Response Model

`JobLineageResponse`

Top-level fields:

- `job_id`
- `items`
- `meta`

### Implemented Ordering

Current repository ordering is:

1. `artifact_lineage_id ASC`

This ordering is surfaced via:

```json
{
  "meta": {
    "ordered_by": "artifact_lineage_id_asc"
  }
}
```

### Empty-State Behavior

If the job exists but has no persisted lineage rows:

- return `200`
- return the job id
- return `items: []`
- return `meta.ordered_by = "artifact_lineage_id_asc"`

## GET /role-model-checker/{run_id}/steps

### Responsibility

Returns persisted step-record rows for the addressed role-model checker run.

### Implemented Response Model

`RoleModelCheckStepsResponse`

Top-level fields:

- `run_id`
- `items`
- `meta`

### Implemented Ordering

Current repository ordering is:

1. `step_index ASC`
2. `step_record_id ASC`

This ordering is surfaced via:

```json
{
  "meta": {
    "ordered_by": "step_index_asc"
  }
}
```

Important limitation:

- as with job steps, the `meta` value does not currently expose the `step_record_id` tie-breaker

### Empty-State Behavior

If the checker run exists but has no persisted step records:

- return `200`
- return the run id
- return `items: []`
- return `meta.ordered_by = "step_index_asc"`

## GET /role-model-checker/{run_id}/lineage

### Responsibility

Returns persisted artifact-lineage rows for the addressed role-model checker run.

### Implemented Response Model

`RoleModelCheckLineageResponse`

Top-level fields:

- `run_id`
- `items`
- `meta`

### Implemented Ordering

Current repository ordering is:

1. `artifact_lineage_id ASC`

This ordering is surfaced via:

```json
{
  "meta": {
    "ordered_by": "artifact_lineage_id_asc"
  }
}
```

### Empty-State Behavior

If the checker run exists but has no persisted lineage rows:

- return `200`
- return the run id
- return `items: []`
- return `meta.ordered_by = "artifact_lineage_id_asc"`

## Query Parameter Contract

The current implementation slice supports one query parameter:

- `attempt`

Rules:

- `attempt` is optional
- when omitted, the endpoint returns persisted rows across all stored attempts for the addressed run
- when provided, the endpoint returns only rows whose `attempt_number` matches the supplied value
- `attempt` must be a positive integer
- invalid `attempt` values return `422`

These endpoints do not currently implement:

- `cursor`
- `limit`
- filtering by step name
- filtering by artifact status

## Attempt History Behavior

The current projection endpoints now provide optional attempt filtering.

Because the underlying repositories query by `run_id`, `run_kind`, and optionally `attempt_number`:

- all stored attempts for the addressed run may appear in one `items` array when `attempt` is omitted
- only rows for that attempt appear when `attempt` is supplied
- step ordering is still controlled by `step_index`, then `step_record_id`
- lineage ordering is still controlled by `artifact_lineage_id`

When `attempt` is supplied, the response `meta` object includes:

```json
{
  "attempt_number": 2,
  "ordered_by": "step_index_asc"
}
```

or:

```json
{
  "attempt_number": 2,
  "ordered_by": "artifact_lineage_id_asc"
}
```

## Implementation Boundary

This blueprint does not claim support for:

- cursor pagination
- offset pagination
- attempt scoping
- public query parameter filtering of any kind
- richer top-level run metadata
- derived summaries
- inline event history

Those remain future enhancements. The implemented contract today is the minimal envelope and ordering documented above.
