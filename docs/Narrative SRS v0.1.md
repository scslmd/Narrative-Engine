# Narrative SRS v0.3

## 1. Purpose

Narrative-Engine is a deterministic local narrative compilation pipeline for novel development.

The system is intended to help a writer:

- define a project by name
- enter premise, tone, language, and constraints
- generate a story bible
- generate beats
- draft prose with local models
- revise selected manuscript text with context-aware writing aids
- verify outputs with a critic or linter loop
- monitor long-running jobs with exact backend progress

## 2. Core Principles

- deterministic pipeline behavior where possible
- local-first execution
- explicit phase boundaries
- human-readable project identity
- backend-driven progress reporting
- provider-agnostic inference integration
- durable reconstruction from documentation plus persisted state

## 3. Project Identity

Projects must be identified to the user by `project_name`, not by UUID alone.

Rules:

- `project_id` remains the internal stable identifier and storage key
- `project_name` is the primary user-facing label in the UI and API responses
- all new project creation flows must require `project_name`
- compatibility fallbacks may exist for legacy manifests that lack `project_name`

## 4. Directory Structure

```text
/Narrative-Engine
|-- /app
|   |-- /api
|   |-- /persistence
|   |-- /schemas
|   `-- /services
|-- /data
|   |-- /models
|   |-- /projects
|   `-- /state
|-- /docs
`-- /frontend
```

Required runtime directories for deterministic recreation:

- `data/projects`
- `data/state`
- `data/models`
- `data/role_model_checker_runs`

Required backend assembly in `app/main.py`:

- `ProjectService`
- `JobManager`
- provider-selected inferencer from `build_inference_backend(settings)`
- `ModelRegistry`
- `RoleModelCheckManager`
- `RoleModelCheckerService`
- `LocalExecutor`

## 5. Required Project APIs

- `POST /projects/create`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`

All project responses must expose:

- `project_id`
- `project_name`

Implementation note:

- The current backend implements `manifest`, `sequence`, and `chapter-1` artifact endpoints.
- Artifact lookup is normalized through persistence so canonical API names remain stable even if source filenames vary.
- The frontend exposes direct artifact preview for these endpoints.
- `architect_p100` is also a canonical persisted artifact type in the current backend, but it is not yet exposed through a dedicated public project artifact endpoint.

## 6. Manifest Schema

```json
{
  "project_id": "UUID",
  "project_name": "string",
  "config": {
    "genre": "string",
    "tone_profile": "string",
    "pov": "Enum[First, Third_Limited, Third_Omni]",
    "primary_language": "string",
    "secondary_language": "string",
    "story_structure": "Enum[SAVE_THE_CAT, THREE_ACT]"
  },
  "constraints": [
    "string"
  ]
}
```

Current reconstruction note:

- manifests are validated and re-read from disk when listing or opening projects
- project creation writes project artifacts on disk first and then registers the project directory into SQLite-backed projections

## 7. Public Backend Surface

The current public backend surface that must be recreated is:

- `GET /health`
- `GET /models`
- `POST /projects/create`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`
- `POST /jobs/create`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/logs`
- `GET /jobs/{job_id}/steps`
- `GET /jobs/{job_id}/lineage`
- `POST /jobs/{job_id}/retry`
- `POST /role-model-checker/run`
- `POST /role-model-checker/start`
- `GET /role-model-checker/{run_id}/status`
- `GET /role-model-checker/{run_id}/steps`
- `GET /role-model-checker/{run_id}/lineage`
- `POST /role-model-checker/{run_id}/retry`
- `GET /`
- `GET /role-model-checker-ui`

Implemented now:

- the API surface above is live
- `/jobs/create` and `/role-model-checker/start` are accepted-and-polled enqueue endpoints
- `/role-model-checker/run` is a compatibility alias that follows the same accepted-and-polled contract

Intentionally not yet implemented:

- public inspect views over attempt history beyond current status responses
- public project endpoint for reading `architect_p100`

## 8. Async Progress

Long-running jobs and model checks must report exact backend progress.

Required endpoints:

- `POST /jobs/create`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/logs`
- `GET /jobs/{job_id}/steps`
- `GET /jobs/{job_id}/lineage`
- `POST /jobs/{job_id}/retry`
- `POST /role-model-checker/start`
- `GET /role-model-checker/{run_id}/status`
- `GET /role-model-checker/{run_id}/steps`
- `GET /role-model-checker/{run_id}/lineage`
- `POST /role-model-checker/{run_id}/retry`

Implementation note:

- The frontend polls these status endpoints rather than assuming immediate completion.
- Job and checker status are durably stored in SQLite instead of process-local memory.
- The current execution path uses a local lease-claim executor.
- The local executor still uses stub logic for most phases and for checker role execution.
- `P-100` is the first real provider-backed pipeline phase and must be treated as a reconstruction-critical special case.
- Step records and artifact lineage are durably persisted in SQLite for the local executor path and are exposed through dedicated public inspect endpoints for jobs and checker runs.

## 8.1 Async Protocol Contract

The current protocol for long-running jobs and checker runs is:

- enqueue request
- durable acceptance record
- worker claim or lease
- execution
- validation
- persistence
- terminal completion or failure

Lifecycle:

`PENDING -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED | FAILED | CANCELLED`

Required reconstruction rules:

- acceptance and execution must be separated
- status endpoints are read-only projections over durable state
- request payloads must be durably stored before active execution begins
- retries must create explicit attempts rather than mutating prior attempts in place
- event history must be append-only even if latest-state projections are materialized separately
- idempotency conflicts must return `409 Conflict`
- accepted responses must set `Location` to the corresponding status endpoint
- idempotent replay of terminal runs may return `200`

Reference:

- see `docs/Async Protocol Blueprint v0.1.md`
- see `docs/Step Record Blueprint v0.1.md` for the current step-record and artifact-lineage contract

## 8.2 Attempt Lineage Requirements

Deterministic recreation now requires first-class attempt lineage for both jobs and checker runs.

Required projection behavior:

- top-level run rows keep the latest attempt number and latest status projection
- append-only event rows retain `attempt_number`
- dedicated attempt rows persist lease and finish metadata per attempt

Required attempt metadata:

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

## 9. Inference Runtime Contract

The current backend must be reconstructed with a provider-agnostic inference layer.

Implemented now:

- `InferenceBackend` interface
- `InferenceProviderDescriptor`
- `InferenceRequest`
- `InferenceResponse`
- `build_inference_backend(settings)`
- shared OpenAI-compatible HTTP adapter for provider-backed runtimes

Supported configured backends:

- `stub`
- `llama.cpp`
- `lmstudio`
- `vllm`
- `openai_compatible`

Required environment variables:

- `NARRATIVE_INFERENCE_BACKEND`
- `NARRATIVE_INFERENCE_BASE_URL`
- `NARRATIVE_INFERENCE_API_KEY`
- `NARRATIVE_INFERENCE_MODEL`
- `NARRATIVE_INFERENCE_TIMEOUT_SECONDS`

Required deterministic recreation rule:

- all provider-backed orchestration code must call the generalized inferencer and must not construct provider-specific HTTP payloads outside the inference package

Reference:

- see `docs/Inference Runtime Blueprint v0.1.md`

## 10. Step Records And Artifact Lineage

The current backend must be reconstructed with durable SQLite persistence for per-step execution records and artifact lineage.

Implemented now:

- `step_records` table in the operational SQLite database
- `artifact_lineage` table in the operational SQLite database
- local-executor writes for pipeline and checker steps
- repository and service helpers for listing step records and lineage by run

Required step-record contract fields:

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

Required artifact-lineage contract fields:

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

Required lineage rules:

- canonical artifacts must not overwrite history in place
- failed attempts must not replace canonical artifact pointers
- lineage rows must point back to the originating step record
- deleting a step record must cascade to its lineage rows

Reference:

- see `docs/Step Record Blueprint v0.1.md`

## 11. P-100 Architect Runtime Path

Deterministic recreation now requires one real provider-backed pipeline phase: `P-100`.

Implemented now:

- `P-100` builds an architect inference request from project manifest context plus job payload overrides
- `P-100` calls `inferencer.generate_text()`
- `P-100` writes the resulting markdown to `data/projects/{project_id}/exports/p100_architect_output.md`
- `P-100` persists a completed step record with role-like step name `architect`
- `P-100` persists a canonical artifact-lineage row for the generated output
- `P-100` registers the generated artifact as canonical project artifact `architect_p100`

Required prompt-construction rules:

- system prompt must instruct deterministic markdown with fixed headings
- user prompt must serialize manifest and payload context as JSON
- request metadata must include:
  - `mode = pipeline_phase`
  - `phase = P-100`
  - `role = architect`
  - `project_id`
  - `project_name`

Required artifact rules for `P-100`:

- output path: `exports/p100_architect_output.md`
- artifact role: `architect_output`
- artifact kind: `markdown`
- lineage status: `CANONICAL`
- lineage validation state: `PASSED`
- canonical project artifact registration name: `architect_p100`

Intentionally not yet implemented:

- equivalent real-runtime execution for phases after `P-100`
- provider-backed checker role execution

## 12. Role-Model Checker

The system must support a role-model checker that validates candidate local GGUF models against the roles:

- architect
- sequencer
- drafter
- critic

The checker exists so users can test model substitutions without repeating manual troubleshooting.

Implementation note:

- The checker currently persists run metadata, results, and an optional saved report path.
- The checker persists step records and artifact lineage for its local executor path.
- The checker still uses stub execution rather than real model evaluation.

## 13. Persistence Contract

The operational SQLite database is a required reconstruction component.

At contract level, deterministic recreation must include:

- project projection tables
- job projection, attempt, log, and event tables
- checker projection, attempt, result, and event tables
- `step_records`
- `artifact_lineage`

Required persistence behaviors:

- WAL mode
- foreign keys enabled
- busy timeout configured
- schema versioning through SQLite `user_version`
- migration or rebuild behavior that preserves legacy operational rows

## 14. Models Endpoint Contract

`GET /models` must expose a deterministic catalog that merges:

- discovered local GGUF models under `data/models`
- discovered runtime models from the configured inferencer
- workflow preferences and recommended defaults
- the active `InferenceProviderDescriptor`

Required response categories:

- `discovered_models`
- `local_discovered_models`
- `runtime_discovered_models`
- `default_selection`
- `recommended_selection`
- `workflow_order`
- `workflow_guidance`
- `critic_profiles`
- `default_critic_profile`
- `override_warning`
- `inference_provider`

## 15. Continuous Testing Baseline

Deterministic recreation now requires the GitHub Actions pytest baseline.

Implemented now:

- GitHub Actions workflow on `push`, `pull_request`, and `workflow_dispatch`
- matrix:
  - `ubuntu-latest` with Python `3.12`
  - `windows-latest` with Python `3.12`

Required pytest command:

- `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`

## 16. Implemented Now vs Not Yet Implemented

Implemented now:

- provider-agnostic inference layer with shared OpenAI-compatible transport
- accepted-and-polled jobs and checker runs
- idempotency and retry semantics
- first-class attempt lineage
- live step records and artifact lineage in SQLite
- real provider-backed `P-100` architect execution path
- canonical `architect_p100` artifact registration
- GitHub Actions pytest baseline

Required for deterministic recreation now:

- exact public endpoint surface in this document
- SQLite-backed operational persistence including steps and lineage
- generalized inferencer and environment-variable configuration
- local executor with special-case runtime-backed `P-100`
- canonical `architect_p100` registration rules
- current pytest and CI command baseline

Intentionally not yet implemented:

- real-runtime execution for non-`P-100` job phases
- provider-backed checker execution
- public step and lineage inspect endpoints
- public project endpoint for `architect_p100`
- richer runtime telemetry persistence beyond the current contracts
