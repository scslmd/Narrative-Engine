# Step and Lineage API Test Matrix v0.1

## Purpose

This document defines the required endpoint test coverage for the first public projection slice covering:

- `GET /jobs/{job_id}/steps`
- `GET /jobs/{job_id}/lineage`
- `GET /role-model-checker/{run_id}/steps`
- `GET /role-model-checker/{run_id}/lineage`

It is aligned to the current implementation slice:

- minimal envelopes
- no query parameters
- deterministic ascending ordering
- `404` for missing run ids
- `200` with empty `items` for existing runs without persisted rows

Future attempt-filter tests are included separately and explicitly labeled as not yet implemented.

## Scope

This matrix covers six test categories:

- happy path
- empty existing-run state
- `404` missing-run state
- deterministic ordering expectations
- envelope stability checks
- future attempt-filter cases

## Shared Assertions

The following assertions should be applied consistently where relevant:

- response status code matches the documented contract
- response body includes the correct top-level run identifier:
  - `job_id` for job endpoints
  - `run_id` for checker endpoints
- response body includes `items`
- response body includes `meta`
- `meta` remains a stable object with the implemented `ordered_by` value
- no unexpected top-level pagination or filter fields are present in the first slice

## Current Slice Test Matrix

### 1. Happy Path

#### 1.1 `GET /jobs/{job_id}/steps`

- existing job with persisted step rows returns `200`
- response includes the requested `job_id`
- response `items` length matches the number of persisted step rows for that job
- each item matches the public `StepRecordView` shape
- `meta.ordered_by` equals `step_index_asc`

#### 1.2 `GET /jobs/{job_id}/lineage`

- existing job with persisted lineage rows returns `200`
- response includes the requested `job_id`
- response `items` length matches the number of persisted lineage rows for that job
- each item matches the public `ArtifactLineageView` shape
- `meta.ordered_by` equals `artifact_lineage_id_asc`

#### 1.3 `GET /role-model-checker/{run_id}/steps`

- existing checker run with persisted step rows returns `200`
- response includes the requested `run_id`
- response `items` length matches the number of persisted step rows for that checker run
- each item matches the public `StepRecordView` shape
- `meta.ordered_by` equals `step_index_asc`

#### 1.4 `GET /role-model-checker/{run_id}/lineage`

- existing checker run with persisted lineage rows returns `200`
- response includes the requested `run_id`
- response `items` length matches the number of persisted lineage rows for that checker run
- each item matches the public `ArtifactLineageView` shape
- `meta.ordered_by` equals `artifact_lineage_id_asc`

### 2. Empty Existing-Run State

#### 2.1 `GET /jobs/{job_id}/steps`

- existing job with no persisted step rows returns `200`
- response includes the requested `job_id`
- response `items` equals `[]`
- `meta.ordered_by` equals `step_index_asc`

#### 2.2 `GET /jobs/{job_id}/lineage`

- existing job with no persisted lineage rows returns `200`
- response includes the requested `job_id`
- response `items` equals `[]`
- `meta.ordered_by` equals `artifact_lineage_id_asc`

#### 2.3 `GET /role-model-checker/{run_id}/steps`

- existing checker run with no persisted step rows returns `200`
- response includes the requested `run_id`
- response `items` equals `[]`
- `meta.ordered_by` equals `step_index_asc`

#### 2.4 `GET /role-model-checker/{run_id}/lineage`

- existing checker run with no persisted lineage rows returns `200`
- response includes the requested `run_id`
- response `items` equals `[]`
- `meta.ordered_by` equals `artifact_lineage_id_asc`

### 3. Missing-Run `404` State

#### 3.1 `GET /jobs/{job_id}/steps`

- missing job id returns `404`
- response detail equals `Job not found.`

#### 3.2 `GET /jobs/{job_id}/lineage`

- missing job id returns `404`
- response detail equals `Job not found.`

#### 3.3 `GET /role-model-checker/{run_id}/steps`

- missing checker run id returns `404`
- response detail equals `Role-model check run not found.`

#### 3.4 `GET /role-model-checker/{run_id}/lineage`

- missing checker run id returns `404`
- response detail equals `Role-model check run not found.`

### 4. Deterministic Ordering Expectations

#### 4.1 Job Steps Ordering

- multiple job step rows are returned in ascending `step_index`
- rows with the same `step_index` are returned in ascending `step_record_id`
- ordering remains stable across repeated requests against unchanged data

#### 4.2 Job Lineage Ordering

- multiple job lineage rows are returned in ascending `artifact_lineage_id`
- ordering remains stable across repeated requests against unchanged data

#### 4.3 Checker Steps Ordering

- multiple checker step rows are returned in ascending `step_index`
- rows with the same `step_index` are returned in ascending `step_record_id`
- ordering remains stable across repeated requests against unchanged data

#### 4.4 Checker Lineage Ordering

- multiple checker lineage rows are returned in ascending `artifact_lineage_id`
- ordering remains stable across repeated requests against unchanged data

Important note:

- the current public `meta.ordered_by` value for step projections is `step_index_asc`
- tests should validate the real response order as `step_index ASC, step_record_id ASC`
- tests should not assume the tie-breaker is exposed in `meta`

### 5. Envelope Stability Checks

#### 5.1 Job Step Envelope

- top-level keys remain exactly:
  - `job_id`
  - `items`
  - `meta`
- `job_id` is a UUID string
- `items` is always a list
- `meta` is always an object
- `meta.ordered_by` equals `step_index_asc`
- no top-level `page`, `cursor`, `limit`, `attempt`, or summary fields are present

#### 5.2 Job Lineage Envelope

- top-level keys remain exactly:
  - `job_id`
  - `items`
  - `meta`
- `job_id` is a UUID string
- `items` is always a list
- `meta` is always an object
- `meta.ordered_by` equals `artifact_lineage_id_asc`
- no top-level `page`, `cursor`, `limit`, `attempt`, or summary fields are present

#### 5.3 Checker Step Envelope

- top-level keys remain exactly:
  - `run_id`
  - `items`
  - `meta`
- `run_id` is a UUID string
- `items` is always a list
- `meta` is always an object
- `meta.ordered_by` equals `step_index_asc`
- no top-level `page`, `cursor`, `limit`, `attempt`, or summary fields are present

#### 5.4 Checker Lineage Envelope

- top-level keys remain exactly:
  - `run_id`
  - `items`
  - `meta`
- `run_id` is a UUID string
- `items` is always a list
- `meta` is always an object
- `meta.ordered_by` equals `artifact_lineage_id_asc`
- no top-level `page`, `cursor`, `limit`, `attempt`, or summary fields are present

### 6. Item Shape Stability Checks

#### 6.1 Step Item Shape

- each step item includes:
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
- `input_artifact_refs` is always a list
- `output_artifact_refs` is always a list
- nullable fields remain present even when `null`

#### 6.2 Lineage Item Shape

- each lineage item includes:
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
- `source_artifact_refs` is always a list
- `source_content_hashes` is always a list
- nullable fields remain present even when `null`

## Future Cases: Attempt Filter

The following cases are intentionally future-facing and should not be treated as required for the current implementation slice because the public endpoints do not yet implement attempt filtering.

### Future Attempt Filter Cases

- `GET /jobs/{job_id}/steps?attempt=1`
  - returns only step rows for attempt `1`
- `GET /jobs/{job_id}/lineage?attempt=1`
  - returns only lineage rows for attempt `1`
- `GET /role-model-checker/{run_id}/steps?attempt=1`
  - returns only checker step rows for attempt `1`
- `GET /role-model-checker/{run_id}/lineage?attempt=1`
  - returns only checker lineage rows for attempt `1`
- invalid attempt filter value returns `422`
- valid attempt filter against an existing run with no matching rows returns `200` with empty `items`
- response envelope remains otherwise unchanged when attempt filtering is added

### Future Attempt-Aware Ordering Checks

- filtered step responses preserve ascending `step_index`, then `step_record_id`
- filtered lineage responses preserve ascending `artifact_lineage_id`
- attempts are not merged or renumbered in the projection response

## Recommended Test Grouping

The current endpoint tests should be grouped into:

- `happy path`
- `empty existing-run state`
- `missing-run 404 state`
- `deterministic ordering`
- `envelope stability`
- `item shape stability`

Future tests should be grouped separately under:

- `attempt filter`

This separation keeps the implemented first slice explicit and prevents future contract assumptions from leaking into current coverage.
