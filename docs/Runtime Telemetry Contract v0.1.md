# Runtime Telemetry Contract v0.1

## Purpose

This document defines the required persisted telemetry fields for provider-backed runs and steps.

It exists to standardize what the runtime must persist for:

- attempt rows
- step records
- future structured logs
- inspect views
- retry and failure analysis

This is a persistence contract, not a logging format specification.

## Goals

- make runtime-backed execution inspectable after the fact
- preserve enough detail to debug provider, prompt, and artifact behavior
- make retry decisions rely on persisted structured fields instead of free-form strings
- keep hashes deterministic across adapters and executor paths
- align step and attempt storage with the runtime error normalization contract

## Scope

This contract applies to:

- runtime-backed pipeline phases such as `P-100` `architect`
- future runtime-backed `sequencer`, `drafter`, and `critic` phases
- future runtime-backed checker execution
- provider adapters behind the generalized inferencer

This contract does not require:

- full orchestrator implementation
- a specific structured log transport
- pagination or query APIs beyond persisted field availability

## Relationship To Runtime Error Mapping

This contract is paired with:

- [docs/Runtime Error Mapping Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Runtime%20Error%20Mapping%20Blueprint%20v0.1.md)

Rules:

- `finish_reason`, `error_code`, `error_category`, and `retryable` must follow the error-mapping blueprint
- telemetry should preserve provider and hash context around those normalized error fields
- diagnostic provider text may exist in logs or run detail fields, but it is not the primary telemetry contract

## Telemetry Layers

Runtime telemetry is split into two layers.

### Attempt-Row Telemetry

Attempt rows answer:

- when a run was claimed
- which executor handled it
- whether it succeeded or failed
- whether the failure is retryable
- the normalized failure classification

### Step-Record Telemetry

Step records answer:

- what exact runtime step executed
- what prompt and inputs were used
- what backend and model produced the output
- what output and artifacts resulted
- how long the step took

Attempt rows are the run-level control-plane view.
Step records are the execution-data view.

## Attempt-Row Telemetry Fields

Provider-backed attempts should persist these fields.

### Implemented Now

The repo already persists these baseline attempt-row fields:

- `logical_run_id`
- `attempt_number`
- `status`
- `executor_name`
- `executor_instance_id`
- `queue_delay_ms`
- `lease_owner`
- `lease_expires_at`
- `claimed_at`
- `started_at`
- `finished_at`
- `last_heartbeat_at`
- `finish_reason`
- `failure_stage`
- `retryable`
- `retry_reason`
- `error_code`
- `error_category`

### Required Next For Runtime-Backed Attempts

Provider-backed attempts should additionally persist:

- `run_kind`
- `project_id`
- `backend_name`
- `backend_version`
- `provider_base_url` when applicable
- `model_id`
- `critic_profile` when relevant
- `prompt_hash`
- `input_hash`
- `output_hash` when a final output exists
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `timeout_seconds`

Rules:

- attempt-row hashes should summarize the primary runtime call for the active attempt
- if an attempt contains multiple provider-backed steps, attempt-row hashes may reflect the dominant or last runtime step, but step records remain the detailed source of truth
- missing token counts are allowed when the provider does not return usage

## Step-Record Telemetry Fields

Provider-backed step records should persist these fields.

### Implemented Now

The repo already persists these step-record fields:

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

### Required Next For Runtime-Backed Steps

Provider-backed step records should additionally persist:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `timeout_seconds`
- `provider_request_id` when available
- `provider_finish_reason` when the provider exposes a native finish reason distinct from the normalized one

Rules:

- step records are the preferred storage location for provider-usage details
- if provider-native finish reason is stored, the normalized `finish_reason` remains the contract field for workflow logic
- token counts should remain nullable rather than inferred

## Hash Contract

Hashes must be deterministic and computed from normalized content.

### General Rules

- hashing algorithm: `SHA-256`
- text encoding: UTF-8
- JSON serialization for payload-style hashes:
  - `ensure_ascii=True`
  - `sort_keys=True`
  - separators `(",", ":")`
- the same semantic payload must produce the same hash regardless of dictionary insertion order

This matches the existing hashing helpers used in persistence and step-record services.

## `prompt_hash`

`prompt_hash` represents the exact provider-facing request content that shaped the generation.

Minimum inputs:

- system messages
- user messages
- assistant messages if present
- model selection
- temperature when specified
- max token limit when specified
- runtime metadata sent with the request

Recommended contract:

- hash the normalized `InferenceRequest` payload that is sent to the adapter
- do not hash local Python object identity or transient executor fields

If the runtime call never reaches request construction:

- `prompt_hash = null`

## `input_hash`

`input_hash` represents the normalized semantic input to the step before generation.

Minimum inputs:

- accepted job or run request payload relevant to the step
- resolved manifest or project context relevant to the step
- referenced prior artifact content or normalized artifact references when used as direct inputs

Recommended contract:

- hash the normalized step input payload passed into step-record creation
- if a step consumes canonical artifacts, those artifacts should be represented deterministically in the hashed payload

## `output_hash`

`output_hash` represents the normalized step output payload.

Minimum inputs:

- primary generated content
- structured runtime response fields retained for the step
- generated artifact pointer or path if that pointer is part of the step output payload

Rules:

- if a step fails before any usable output exists, `output_hash = null`
- if partial usable output is intentionally persisted, hash the persisted partial output payload
- artifact lineage `content_hash` remains separate from step-record `output_hash`

## Artifact Hash Relationship

Step hashes and artifact hashes serve different purposes.

- `output_hash` answers: what structured step output was persisted
- artifact lineage `content_hash` answers: what exact artifact bytes or text were written

These values may differ and should not be forced to match.

## Token Usage Contract

When the provider returns usage, the runtime should persist:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`

Rules:

- use provider-reported values directly when available
- do not estimate counts unless a later explicit estimation policy is adopted
- keep missing values as `null`
- store token usage at the step-record layer first
- attempt rows may also carry summary usage for the dominant runtime call of the attempt

## Provider / Backend Identity Contract

Provider-backed telemetry should preserve:

- `backend_name`
- `backend_version`
- `model_id`
- `critic_profile` when relevant
- `provider_base_url` at attempt level when applicable

Definitions:

- `backend_name`: stable display or canonical provider name used by the adapter
- `backend_version`: adapter-known provider version if exposed; otherwise `null`
- `model_id`: exact model used for the runtime call, not just the default model candidate
- `critic_profile`: only populated for critic-oriented steps

Rules:

- step records must carry the precise model used by that step
- attempt rows may summarize the primary model for the attempt
- if the provider cannot expose a version, store `null` rather than synthetic placeholders

## Finish Reasons

Telemetry persistence should use normalized `finish_reason` values as the contract field.

Expected success-oriented values include:

- `completed`
- `stop`
- `passed`
- `report_saved`

Expected failure-oriented normalized values are defined in:

- [docs/Runtime Error Mapping Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Runtime%20Error%20Mapping%20Blueprint%20v0.1.md)

Rules:

- provider-native finish reasons may be preserved separately if needed later
- normalized `finish_reason` is the workflow-contract field for attempts and steps
- failure telemetry must not rely on raw exception text in place of `finish_reason`

## What Is Implemented Now

Currently implemented in the repo:

- attempt-row executor claim telemetry
- attempt-row finish and error fields
- step-record persistence for:
  - `backend_name`
  - `backend_version`
  - `model_id`
  - `critic_profile`
  - `prompt_hash`
  - `input_hash`
  - `output_hash`
  - `finish_reason`
  - `error_code`
  - `error_category`
- artifact-lineage content hashing
- one real provider-backed path:
  - `P-100` `architect`

Current limitations:

- token usage is returned by `InferenceResponse.usage` but not yet persisted into step or attempt storage
- attempt rows do not yet persist runtime-grade provider identity and hash fields
- backend version is often `null`
- provider-native request IDs are not persisted

## What Is Required Next

The next runtime telemetry implementation slice should:

1. extend persistence for step-record token usage fields
2. extend attempt rows with runtime-grade provider and hash summary fields
3. map normalized runtime errors from the inferencer into persisted attempt and step telemetry
4. ensure every provider-backed executor path persists:
   - `backend_name`
   - `model_id`
   - `prompt_hash`
   - `input_hash`
   - `output_hash` when available
   - `finish_reason`
   - `error_category`
   - `error_code`
5. add provider usage persistence when available

## Minimal Required Persistence Matrix

| Field | Attempt row | Step record |
| --- | --- | --- |
| `logical_run_id` | required | required |
| `attempt_number` | required | required |
| `project_id` | required next | required |
| `backend_name` | required next | required |
| `backend_version` | required next | required |
| `model_id` | required next | required |
| `critic_profile` | required next | required when relevant |
| `prompt_hash` | required next | required |
| `input_hash` | required next | required |
| `output_hash` | required next | required when output exists |
| `prompt_tokens` | recommended summary | required when available |
| `completion_tokens` | recommended summary | required when available |
| `total_tokens` | recommended summary | required when available |
| `finish_reason` | required | required |
| `error_code` | required | required |
| `error_category` | required | required |
| `retryable` | required | n/a |
| `timeout_seconds` | required next | required next |

## Deliberate Boundary

This document defines the persistence contract only.

It does not require in this turn:

- schema migrations
- adapter refactors
- API changes
- logging-pipeline implementation

It exists so those later changes can converge on one deterministic telemetry contract rather than inventing per-adapter or per-executor variations.
