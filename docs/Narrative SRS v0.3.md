# Narrative SRS v0.3

Document version: `v0.3`

## 1. Purpose

Narrative-Engine is a local-first narrative development system for novel and story creation.

The system is intended to help a writer:

- define a project by name
- enter premise, tone, language, and constraints
- generate a story bible
- generate beats
- draft prose with local models
- revise selected manuscript text with context-aware writing aids
- verify outputs with a critic or linter loop
- monitor long-running jobs with exact backend progress

Product-planning reference:

- the detailed story-development feature contract now lives in `docs/Story Development Product Spec v0.1.md`
- `docs/Story Development Canonical Contract v0.1.md` defines the approved object names, lifecycle enums, editable-flow semantics, and planning or drafting terminology for those features
- this SRS carries the backend-facing contract for story-development services, inspect state, lineage, and retry behavior

## 2. Core Principles

- deterministic pipeline behavior where possible
- local-first execution
- explicit phase boundaries
- human-readable project identity
- backend-driven progress reporting
- provider-agnostic inference integration
- durable persistence and inspectability across runs and generated artifacts

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

Required runtime directories for current backend operation:

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

Current implementation note:

- manifests are validated and re-read from disk when listing or opening projects
- project creation writes project artifacts on disk first and then registers the project directory into SQLite-backed projections

## 7. Public Backend Surface

**Change log (Mixed HTTP Surface Correction - March 29, 2026)**:
- Updated API Versioning Convention to document the mixed surface: versioned `/v1/...` routes for jobs, models, story-development, and checker flows; unversioned routes for projects, auth, backup, and health
- Corrected Projects Service section to use unversioned paths (`/projects`, not `/v1/projects`)
- Added Health endpoints section with `GET /health/`, `GET /health/ready`, and `GET /health/metrics`

### API Versioning Convention

The backend uses a **mixed HTTP surface** with both versioned and unversioned routes:

- **Versioned routes (`/v1`)**: Jobs, models, story-development, and role-model-checker services
- **Unversioned routes**: Projects, authentication, backup, and health endpoints

Base URL patterns:
- Versioned: `{host}/v1/{service}/{resource}`
- Unversioned: `{host}/{service}/{resource}`
- Environment variable: `VITE_API_URL=http://localhost:8000` (frontend)

### Router Prefixes by Service

| Service | Backend Router Prefix | Example Endpoint |
|---------|----------------------|------------------|
| Health | `/health` | `GET /health/ready` |
| Projects | `/projects` | `POST /projects/create` |
| Models | `/v1` | `GET /v1/models` |
| Jobs | `/v1/jobs` | `POST /v1/jobs/create` |
| Role Model Checker | `/v1/role-model-checker` | `POST /v1/role-model-checker/run` |
| Story Development | `/v1/story-development` | `GET /v1/story-development/drafting/draft-artifacts` |

### Complete API Surface

**Health & Static:**
- `GET /health/` - Health check endpoint
- `GET /health/ready` - Readiness check endpoint
- `GET /health/metrics` - Metrics endpoint with latency telemetry
- `GET /` - Serve frontend index.html
- `GET /role-model-checker-ui` - Serve role model checker UI

**Projects Service (`/projects`):**
- `POST /projects/create` - Create new project
- `GET /projects` - List all projects
- `GET /projects/{project_id}` - Get project details
- `GET /projects/{project_id}/manifest` - Get project manifest
- `GET /projects/{project_id}/sequence` - Get sequence artifact
- `GET /projects/{project_id}/chapter-1` - Get chapter-1 artifact

**Models Service (`/v1/models`):**
- `GET /v1/models` - Get model catalog with discovered local and runtime models

**Jobs Service (`/v1/jobs`):**
- `POST /v1/jobs/create` - Create and enqueue job (202 Accepted)
- `GET /v1/jobs/{job_id}/status` - Get job status
- `GET /v1/jobs/{job_id}/logs` - Get job logs
- `GET /v1/jobs/{job_id}/steps` - Get job step records
- `GET /v1/jobs/{job_id}/lineage` - Get attempt lineage
- `POST /v1/jobs/{job_id}/retry` - Retry failed job

**Role Model Checker Service (`/v1/role-model-checker`):**
- `POST /v1/role-model-checker/run` - Start checker run (202 Accepted)
- `POST /v1/role-model-checker/start` - Alternative start endpoint (compatibility alias)
- `GET /v1/role-model-checker/{run_id}/status` - Get checker run status
- `GET /v1/role-model-checker/{run_id}/steps` - Get checker step records
- `GET /v1/role-model-checker/{run_id}/lineage` - Get checker attempt lineage
- `POST /v1/role-model-checker/{run_id}/retry` - Retry failed checker run

**Story Development Service (`/v1/story-development`):**

*Drafting Subservice:*
- `GET /v1/story-development/drafting/draft-artifacts?project_id={id}` - List draft artifacts
- `POST /v1/story-development/drafting/promote-draft` - Promote draft to manuscript

*Review Subservice:*
- `GET /v1/story-development/review/findings` - List checker findings
- `GET /v1/story-development/review/findings/{finding_id}` - Get finding details
- `GET /v1/story-development/review/decisions?target_id={id}` - List review decisions
- `POST /v1/story-development/review/decisions` - Create review decision
- `GET /v1/story-development/review/inspect-links` - List inspect run links
- `GET /v1/story-development/review/inspect-links/{link_id}` - Get inspect link details

*Decisions Subservice:*
- `GET /v1/story-development/decisions?project_id={id}` - List story decision nodes
- `GET /v1/story-development/decisions/{node_id}` - Get decision node
- `GET /v1/story-development/decisions/{node_id}/path` - Get decision path with ancestors

*Branching Subservice:*
- `GET /v1/story-development/branches?project_id={id}` - List story branches
- `POST /v1/story-development/branches` - Create new branch
- `GET /v1/story-development/branches/active?project_id={id}` - Get active branch
- `POST /v1/story-development/branches/active` - Set active branch
- `GET /v1/story-development/branches/{branch_id}/state-refs` - List branch state refs
- `POST /v1/story-development/branches/comparisons` - Create branch comparison
- `GET /v1/story-development/branches/comparisons?project_id={id}` - List comparisons
- `GET /v1/story-development/branches/comparisons/{comparison_id}` - Get comparison
- `POST /v1/story-development/branches/merge-decisions` - Create merge decision
- `GET /v1/story-development/branches/merge-decisions?project_id={id}` - List merge decisions

Implemented now:

- the API surface above is live with `/v1` versioning prefix
- `/v1/jobs/create` and `/v1/role-model-checker/start` are accepted-and-polled enqueue endpoints
- `/v1/role-model-checker/run` is a compatibility alias that follows the same accepted-and-polled contract

Intentionally not yet implemented:

- public inspect views over attempt history beyond current status responses
- public project endpoint for reading `architect_p100`

## 8. Async Progress

Long-running jobs and model checks must report exact backend progress.

Required endpoints:

- `POST /v1/jobs/create` - Create and enqueue job (returns 202 Accepted)
- `GET /v1/jobs/{job_id}/status` - Get job status
- `GET /v1/jobs/{job_id}/logs` - Get job logs
- `GET /v1/jobs/{job_id}/steps` - Get job step records
- `GET /v1/jobs/{job_id}/lineage` - Get attempt lineage
- `POST /v1/jobs/{job_id}/retry` - Retry failed job
- `POST /v1/role-model-checker/start` - Start checker run (returns 202 Accepted)
- `GET /v1/role-model-checker/{run_id}/status` - Get checker run status
- `GET /v1/role-model-checker/{run_id}/steps` - Get checker step records
- `GET /v1/role-model-checker/{run_id}/lineage` - Get checker attempt lineage
- `POST /v1/role-model-checker/{run_id}/retry` - Retry failed checker run

Implementation note:

- The frontend polls these status endpoints rather than assuming immediate completion.
- Job and checker status are durably stored in SQLite instead of process-local memory.
- The current execution path uses a local lease-claim executor.
- The local executor now has explicit runtime-backed handlers for `P-100`, `P-200`, `P-300`, and `P-400`, while checker role execution supports runtime-backed roles with deterministic fallback.
- `P-100` through `P-400` are the current real provider-backed pipeline phases and remain the reference slices for any future runtime-backed phase expansion.
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

Required protocol rules:

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

The current async model depends on first-class attempt lineage for both jobs and checker runs.

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

The current backend uses a provider-agnostic inference layer.

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

Required runtime-integration rule:

- all provider-backed orchestration code must call the generalized inferencer and must not construct provider-specific HTTP payloads outside the inference package

Reference:

- see `docs/Inference Runtime Blueprint v0.1.md`

## 10. Step Records And Artifact Lineage

The current backend uses durable SQLite persistence for per-step execution records and artifact lineage.

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

Implemented now for inspect views:

- public projection endpoints return persisted step rows and lineage rows in deterministic ascending order
- runtime-backed `P-100` `architect` steps already expose:
  - `backend_name`
  - `backend_version`
  - `model_id`
  - `prompt_hash`
  - `input_hash`
  - `output_hash`
  - `finish_reason`
  - `error_code`
  - `error_category`

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

## 11. Runtime-Backed Pipeline Paths

The current runtime-backed baseline includes four real provider-backed pipeline phases: `P-100`, `P-200`, `P-300`, and `P-400`.

Implemented now:

- `P-100` builds an architect inference request from project manifest context plus job payload overrides
- `P-100` calls `inferencer.generate_text()`
- `P-100` writes the resulting markdown to `data/projects/{project_id}/exports/p100_architect_output.md`
- `P-100` persists a completed step record with role-like step name `architect`
- `P-100` persists a canonical artifact-lineage row for the generated output
- `P-100` registers the generated artifact as canonical project artifact `architect_p100`
- `P-200` builds a sequencer inference request from manifest plus upstream architect context and registers canonical `sequence`
- `P-300` builds a drafter inference request from manifest plus upstream architect and sequence context and registers canonical `chapter_1`
- `P-400` builds a compiler inference request from manifest plus architect, sequence, and chapter context and registers canonical `story_bible`

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

Current artifact rules for later implemented phases:

- `P-200`
  - artifact role: `sequence`
  - artifact kind: `json`
  - canonical project artifact registration name: `sequence`
- `P-300`
  - artifact role: `chapter_1`
  - artifact kind: `markdown`
  - canonical project artifact registration name: `chapter_1`
- `P-400`
  - artifact role: `story_bible`
  - artifact kind: `json`
  - canonical project artifact registration name: `story_bible`

Intentionally not yet implemented:

- equivalent real-runtime execution for phases beyond `P-400`

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
- The checker inspect endpoints are public and return persisted checker step and lineage projections.
- The current checker path emits inspectable runtime-backed step records for `architect`, `sequencer`, `drafter`, and `critic`.
- Checker roles still fall back deterministically when runtime is unavailable, fails, or `critic_profile` is `deterministic_only`.

## 13. Persistence Contract

The operational SQLite database is a required system component.

At contract level, the current backend depends on:

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

`GET /v1/models` must expose a deterministic catalog that merges:

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

### Request Parameters

No query parameters required.

### Response Schema (`ModelCatalogResponse`)

```json
{
  "discovered_models": [...],
  "local_discovered_models": [...],
  "runtime_discovered_models": [...],
  "default_selection": {...},
  "recommended_selection": {...},
  "workflow_order": [...],
  "workflow_guidance": "...",
  "critic_profiles": {...},
  "default_critic_profile": "...",
  "override_warning": "...",
  "inference_provider": {...}
}
```

### Error Responses

| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 500 | Server error | Model discovery or catalog generation failed |

## 15. Continuous Testing Baseline

The current backend baseline includes the GitHub Actions pytest suite.

Implemented now:

- GitHub Actions workflow on `push`, `pull_request`, and `workflow_dispatch`
- matrix:
  - `ubuntu-latest` with Python `3.12`
- `windows-latest` with Python `3.12`

Required pytest command:

- `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_local_executor_sequencer_runtime.py tests/test_local_executor_drafter_runtime.py tests/test_local_executor_compiler_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_projection_endpoints.py tests/test_projection_endpoints_impl.py tests/test_projection_runtime_failure_modes.py tests/test_runtime_error_mapping_failures.py tests/test_role_model_checker_runtime.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`

## 16. Implemented Now vs Not Yet Implemented

Implemented now:

- provider-agnostic inference layer with shared OpenAI-compatible transport
- accepted-and-polled jobs and checker runs
- idempotency and retry semantics
- first-class attempt lineage
- live step records and artifact lineage in SQLite
- real provider-backed `P-100` through `P-400` execution paths
- canonical `architect_p100` artifact registration
- public projection endpoints for step records and artifact lineage
- GitHub Actions pytest baseline

Required for the current baseline:

- exact public endpoint surface in this document
- SQLite-backed operational persistence including steps and lineage
- generalized inferencer and environment-variable configuration
- local executor with explicit runtime-backed handlers for `P-100`, `P-200`, `P-300`, and `P-400`
- canonical runtime artifact registration rules for `architect_p100`, `sequence`, `chapter_1`, and `story_bible`
- current pytest and CI command baseline

Intentionally not yet implemented:

- real-runtime execution for job phases beyond `P-400`
- public project endpoint for `architect_p100`
- richer runtime telemetry persistence beyond the current contracts

## 17. Story-Development Feature Contract

This section defines the product features that sit on top of the narrative backend. The intent is to make the story-development flow explicit enough that each feature can be implemented, inspected, retried, and evolved independently.

The core rule is unchanged:

- the story-development flow is editable, not fixed
- the user may add, remove, reorder, redefine, or skip stages at any time
- downstream outputs must preserve provenance when upstream inputs change

Current backend milestone now implemented:

- editable flow, brainstorm, foundation, story knowledge, planning, drafting, and decision-review service foundations exist in backend code
- canonical persistence now exists for planning objects, drafting objects, story decision nodes, checker findings, review decisions, and inspect run links
- public API wiring for story-development routes is still intentionally not implemented
- branch identity, branch state, branch comparison, merge behavior, and story-development route surfaces remain separate upcoming slices

**v1.0 scope clarification**: The current routed app provides read-only arc projections via `getArcCandidates`, `getArcSelections`, and `getArcStageMaps`; character profile editing via CharacterBuilder; and planning reads where API endpoints exist. Interactive decision workflows (arc selection mutations, relationship mapping) are deferred to future releases while remaining supported backend concepts.

### 17.1 Editable Core Flow

The editable core flow is the project-local workflow graph that replaces a rigid wizard.

What it solves:

- it lets exploratory writers move freely without losing structure
- it lets process-driven writers keep a repeatable planning path
- it lets the system adapt to genre-specific or project-specific stages without code changes

Backend responsibilities:

- persist a project-specific flow definition
- store stage metadata, display order, dependency edges, and stage enablement
- allow user-defined stage names and descriptions
- keep stage definitions distinct from generated artifacts
- recompute downstream guidance when a stage is inserted, removed, or renamed

Required backend objects:

- `StoryFlowDefinition`
- `StoryFlowStage`
- `StoryFlowEdge`
- `StoryFlowRule`

Required service responsibilities:

- create the default flow scaffold for a new project
- update the flow graph without destroying existing generated artifacts
- expose the current flow state to the workspace and inspect views
- mark downstream work as potentially stale when the flow changes

### 17.2 Brainstorming

Brainstorming is the freeform idea-capture layer that turns fragments into candidate story material.

What it solves:

- it gives the user a low-friction place to start
- it preserves raw ideas before they are prematurely collapsed into structure
- it supports concept discovery when the writer does not yet know the story shape

Expected behaviors:

- capture premise sparks, themes, images, questions, constraints, and scene fragments
- cluster related ideas into concept groups
- promote ideas into structured foundation fields, character seeds, or world seeds
- keep discarded or parked ideas available for later reuse

Backend responsibilities:

- persist brainstorm entries as first-class project data
- record which brainstorm items were promoted into which structured artifacts
- keep raw brainstorming text available for provenance and review
- support grouping or tagging without mutating the original source note

Required backend objects:

- `BrainstormItem`
- `BrainstormCluster`
- `BrainstormPromotion`

Required task functions:

- capture idea
- cluster related notes
- generate alternate concept branches
- promote brainstorm output into foundation or character material
- reopen a parked idea without losing its history

### 17.3 Story Foundation

The story foundation is the stable project intent that downstream planning and drafting should obey unless the user intentionally changes it.

What it solves:

- it defines what story the project is trying to tell
- it prevents planning and drafting from drifting away from the core promise
- it gives the orchestrator a reference point for suggestions and validation

Required foundation fields:

- premise
- logline
- thematic spine
- emotional promise
- tone and voice direction
- target audience
- narrative constraints
- complexity or pacing preference
- success definition for the draft

Backend responsibilities:

- store foundation data as project-level structured state
- track changes to foundation fields over time
- identify downstream artifacts that may need review after a foundation change
- preserve the previous foundation state for provenance

Required backend objects:

- `FoundationProfile`
- `FoundationRevision`
- `FoundationChangeEvent`

Required task functions:

- summarize brainstorm material into a foundation draft
- refine or rewrite foundation fields
- compare the current foundation to a prior revision
- flag downstream artifacts that should be rechecked after a change

### 17.4 Character Background

Character background is the engine that turns people in the story into structured narrative agents rather than static bios.

What it solves:

- it supports consistent character motivation across planning and drafting
- it helps the system generate dialogue, conflict, and growth that fit the character
- it keeps relationship dynamics and secrets visible to the backend

Required character data:

- role in story
- archetype or function
- external goal
- internal need
- wound, misbelief, or core contradiction
- fear
- strength
- flaw or limitation
- relationship map (deferred to future release; current v1.0 provides profile fields only)
- secrets
- continuity facts
- change axis
- arc-stage notes

Backend responsibilities:

- store character profiles as structured project objects
- store relationships as explicit graph edges
- keep character continuity facts distinct from speculative notes
- surface which characters are affected when a story foundation or arc changes

Required backend objects:

- `CharacterProfile`
- `RelationshipEdge`
- `CharacterArcNote`
- `CharacterContinuityFact`

Required task functions:

- create a character profile
- refine backstory or voice
- update a relationship edge
- compare two character arcs
- extract a character fact from a draft or scene

### 17.5 World Bible

The world bible is the canonical repository for setting facts, rules, and continuity anchors.

What it solves:

- it keeps the story world coherent across long-form drafting
- it gives the orchestrator and critic concrete facts to validate against
- it prevents repeated invention of the same setting details

World bible content should include:

- locations
- factions
- institutions
- history
- timeline anchors
- rules of magic, technology, or power systems
- cultural norms
- terminology
- unresolved promises
- continuity constraints

Backend responsibilities:

- persist world entries as addressable records
- link each entry to the source artifact that established it
- mark entries as canonical, provisional, or disputed
- raise continuity warnings when a draft conflicts with established world facts

Required backend objects:

- `WorldBibleEntry`
- `WorldBibleCategory`
- `WorldBibleRevision`
- `ContinuityWarning`

Required task functions:

- upsert a world entry
- extract a world fact from planning or draft text
- detect a setting contradiction
- promote a repeated detail into canon

### 17.6 Story Arc Selection

Story arc selection is the planning layer that lets the user choose a story shape, compare alternatives, and change course without losing prior work.

**v1.0 scope clarification**: Current routed app provides read-only arc projections (`getArcCandidates`, `getArcSelections`, `getArcStageMaps`); interactive arc-decision workflows (comparison mutations, selection changes) are deferred to future releases.

What it solves:

- it gives the project a structural lens for suggestions and pacing
- it supports multiple story families without hardcoding one narrative template
- it helps the system flag missing beats, drift, or mismatch between intent and execution

Required arc behavior (target product requirements):

- recommend arcs from premise, genre, and tone
- compare multiple arc candidates
- show stage maps or beat maps
- provide arc drift warnings
- provide arc recovery suggestions
- keep arc choice advisory rather than blocking

Arc families should be treated as planning lenses, not rigid schemas. Examples include:

- romance
- mystery or thriller
- tragedy
- heroic or quest arc
- corruption or fall arc
- ensemble or braided arc

Backend responsibilities:

- store the selected arc and any rejected alternatives
- store the stage map that the arc implies for this project
- persist arc comparisons as reviewable first-class records
- keep arc selection revision history
- link arc guidance to planning and review output
- persist user story-direction nodes with enough structured detail to generate a timeline and tree of choices, pivots, and deviations later

Required backend objects:

- `ArcSelection`
- `ArcCandidate`
- `ArcComparisonRecord`
- `ArcStageMap`
- `StoryDecisionNode`
- `ArcDriftWarning`

Required task functions:

- recommend an arc
- compare arc options
- persist the comparison result for later review
- assign a stage map to the current project
- persist the resulting user decision node so later pivots remain reviewable
- detect drift from the selected arc
- recover from an arc mismatch by suggesting a revised path

Required decision-node fields:

- node type enum
- change type enum
- affected object type enum and object id
- parent node id when this node extends an earlier decision path
- branch id when the node belongs to a forked storyline path
- human-readable summary for timeline and tree rendering
- prior state reference or prior state summary when applicable
- new state reference or new state summary when applicable
- reason, note, or explicit user rationale when present
- decision timestamp
- actor identity
- typed links to related objects and informing objects when present

Decision-node permutations must be enum-driven rather than free-form text so the backend can query deterministic subsets such as:

- all `ARC_SELECTION` nodes
- all `STAGE_REDEFINE` nodes
- all nodes whose `subject_type` is `ARC_SELECTION`
- all children of a given `parent_node_id`
- all nodes on a given `branch_id`

Implemented node-schema contract:

| Field | Expected type | Required | Notes |
| --- | --- | --- | --- |
| `node_id` | `str` | yes | non-blank stable identifier |
| `project_id` | `str` | yes | non-blank project identifier |
| `node_type` | `StoryDecisionNodeType` | yes | enum-backed node category |
| `change_type` | `StoryDecisionChangeType` | yes | enum-backed change classification |
| `subject_type` | `StoryObjectType` | yes | enum-backed canonical object type |
| `subject_id` | `str` | yes | non-blank subject identifier |
| `parent_node_id` | `str \| None` | no | nullable parent node link |
| `branch_id` | `str \| None` | no | nullable branch membership |
| `summary` | `str` | yes | timeline and tree label |
| `prior_state_ref` | `str \| None` | no | nullable machine-readable prior-state ref |
| `prior_state_summary` | `str \| None` | no | nullable human-readable prior-state summary |
| `new_state_ref` | `str \| None` | no | nullable machine-readable new-state ref |
| `new_state_summary` | `str \| None` | no | nullable human-readable new-state summary |
| `reason_or_note` | `str \| None` | no | nullable rationale |
| `decision_made_at` | `datetime` | yes | event timestamp |
| `made_by` | `str` | yes | non-blank actor identifier |
| `related_object_links` | `list[StoryDecisionNodeLink]` | yes | defaults to empty list |
| `informing_object_links` | `list[StoryDecisionNodeLink]` | yes | defaults to empty list |

`StoryDecisionNodeLink` fields:

- `object_type`: `StoryObjectType`
- `object_id`: `str`
- `relation_kind`: `str`

Validation rule:

- at least one of `prior_state_ref`, `prior_state_summary`, `new_state_ref`, or `new_state_summary` must be present

### 17.6A Story Branching And Forks

Story branching is the feature that lets the user fork the storyline at a meaningful decision point and explore alternate directions without overwriting the active path.

What it solves:

- it lets the user try multiple arc or planning directions from the same decision point
- it preserves alternate story paths as reviewable branches instead of disposable scratch state
- it makes pivots, merges, and abandoned directions inspectable later

Backend responsibilities:

- persist branch identity, branch origin, and branch-point references as first-class records
- allow a branch to reference canonical foundation, arc, planning, manuscript, and decision-history state without copying unrelated data blindly
- preserve timeline-grade and tree-grade decision history per branch
- support later comparison and selective merge behavior between branches
- keep branching semantics in structured backend storage rather than relying on Git commits or filesystem branching as the canonical product backend

Implemented now:

- canonical schema and persistence exist for `StoryBranch`, `BranchPoint`, and branch state at the branch-identity layer
- canonical schema and persistence now exist for `BranchStateRef` and active-branch selection per project
- canonical schema and persistence now exist for `BranchComparisonRecord` so alternate paths can be compared without mutating branch state
- project scoping is enforced between branch records and their originating branch points
- only one active branch is allowed per project in persisted branch state
- merge decisions and branch services are still separate upcoming slices

Explicit non-goal:

- Git should not be used as the canonical backend for story branching
- Git-like concepts such as fork, branch, compare, and merge are useful product metaphors, but the source of truth must remain structured application objects and persistence

Required backend objects:

- `StoryBranch`
- `BranchPoint`
- `BranchStateRef`
- `BranchComparisonRecord`
- `BranchMergeDecision`
- `StoryDecisionNode`

Required task functions:

- create a branch from a decision point
- list branches for a project
- compare one branch to another
- select the active branch
- merge selected branch outcomes back into another branch through explicit decisions

### 17.7 Planning Objects

Planning objects are the structured intermediates that turn abstract intent into executable writing work.

What they solve:

- they bridge the gap between high-level story design and draftable units
- they let the system reason about dependencies, escalation, and continuity before prose is generated
- they provide a stable target for inspect and revision workflows

Planning layers:

- beats
- sequences
- chapters
- scenes
- optional chapter packets

Required planning fields:

- objective
- conflict
- stakes
- dependency
- arc stage
- active characters
- continuity requirements
- unresolved questions
- status
- writer notes

Backend responsibilities:

- store planning objects as first-class records
- preserve parent-child relationships between beats, chapters, and scenes
- allow planning artifacts to be regenerated without erasing prior versions
- keep planning objects linkable to their source foundation, arc, and character data

Implementation lesson:

- do not implement planning services against process-local or in-memory plan state when the canonical planning records do not exist yet
- if a feature family introduces new canonical backend objects, the persistence tables and repository helpers for those objects must land before or with the service layer
- UI card or board views must stay projections over persisted plan records rather than becoming a second competing storage model

Implemented now:

- canonical persistence exists for `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, and `ChapterPacket`
- backend planning services can create, reorder, and packetize canonical planning records without introducing a competing persisted card model

Required backend objects:

- `BeatPlan`
- `SequencePlan`
- `ChapterPlan`
- `ScenePlan`
- `ChapterPacket`
- `PlanningDependency`

Required task functions:

- create a sequence plan from project context
- split a sequence into chapters
- derive scenes from a chapter packet
- reorder planning objects while preserving lineage
- attach unresolved questions to the next planning step

### 17.8 Drafting

Drafting is the prose-generation and prose-revision layer that consumes planning state and produces manuscript text.

What it solves:

- it turns planning into readable prose
- it lets the user iterate without losing the planning context that produced the draft
- it supports continuation drafting and controlled rewrites instead of one-shot overwrite behavior

Drafting behaviors:

- chapter drafting from planning context
- scene drafting from chapter context
- continuation drafting from prior prose
- alternate version generation
- redraft support
- visible provenance for generated text

Backend responsibilities:

- build draft prompts from manifest, foundation, arc, character, world, and planning context
- persist draft outputs as artifacts with step records and lineage
- keep the generated draft separate from the user-edited manuscript buffer
- preserve the original prompt and model metadata for later inspection

Implemented now:

- canonical persistence exists for `DraftArtifact`, `ManuscriptDocument`, and `RevisionSuggestion`
- backend drafting services support continuation drafting, alternate variants, manuscript promotion, and non-destructive revision suggestions
- accepted manuscript state does not erase the originating draft artifact or its provenance links

Required backend objects:

- `DraftArtifact`
- `DraftRequest`
- `DraftRevision`
- `DraftContinuation`
- `ManuscriptDocument`

Required task functions:

- generate a chapter draft
- continue a draft from the prior scene
- rewrite a chapter with constrained instructions
- create alternate prose variants
- register the resulting draft artifact and its lineage
- promote accepted draft content into explicit manuscript state without erasing the originating draft artifact

### 17.9 Suggestions And Revision

Suggestions are the guided-assistance layer that improves the manuscript without silently replacing author text.

What it solves:

- it provides context-aware writing help
- it keeps the user in control of final editorial choices
- it makes review actionable by translating critique into concrete options

Suggestion families should include:

- conflict boost
- emotional clarity
- continuity correction
- arc alignment
- pacing adjustment
- sensory enrichment
- point-of-view correction
- dialogue polish
- ending beat options
- alternate next-scene options

Backend responsibilities:

- generate suggestions from the current manuscript and project context
- store suggestions separately from canonical prose
- explain which context sources informed each suggestion
- allow the user to accept, reject, or park a suggestion

Required backend objects:

- `SuggestionRequest`
- `RevisionSuggestion`
- `SuggestionOption`
- `SuggestionDecision`

Required task functions:

- generate revision suggestions
- rank suggestions by relevance
- explain the context used for a suggestion
- convert a suggestion into a user-applied edit without mutating history

### 17.10 Continuity And Review

Continuity and review are the validation layers that keep generated prose aligned with canon, arc intent, and user-defined constraints.

What it solves:

- it catches contradictions before they spread through the manuscript
- it gives the user a structured critic loop rather than vague feedback
- it creates explicit repair work when a story departs from canon or from the selected arc

Review outputs should include:

- continuity issues
- arc drift warnings
- character consistency issues
- missing beats
- unresolved dependencies
- critic notes

Backend responsibilities:

- support runtime-backed checker roles where available
- preserve deterministic fallback when runtime is unavailable or rejected
- persist review findings as first-class records with source step references
- keep review output distinct from draft output

Implemented now:

- canonical persistence exists for `CheckerFinding`, `ReviewDecision`, and `InspectRunLink`
- decision-review services exist for `StoryDecisionNode` history
- review-routing services over findings, review decisions, and inspect links now exist in backend code
- public story-development review routes are still intentionally not implemented

Required backend objects:

- `CheckerFinding`
- `ReviewDecision`
- `InspectRunLink`

Required task functions:

- run a continuity check
- compare a draft against canon
- produce a review summary
- persist the resulting finding and any related inspect link
- record the resulting accept, reject, defer, escalate, or refine decision
- route a finding back into planning or drafting

### 17.11 Inspect And Provenance

Inspect and provenance are core product features, not developer conveniences.

What they solve:

- they let the user see how a result was produced
- they make retries and failures understandable
- they make it possible to trust generated material because the source chain is visible

Required inspect behavior:

- show step timelines
- show lineage chains
- show artifact ancestry
- show runtime metadata where available
- distinguish successful canonical artifacts from failed or superseded attempts

Backend responsibilities:

- expose job and checker step projections
- expose lineage projections in deterministic order
- keep prompt, input, output, and model metadata available for persisted steps
- avoid overwriting history when a later attempt supersedes an earlier one

Required backend objects:

- `InspectRunLink`
- `StepRecord`
- `ArtifactLineage`

Required task functions:

- list the steps for a job or checker run
- list lineage for a generated artifact
- link a generated artifact back to the step that produced it
- show which artifact version is canonical

### 17.12 Orchestrator Expectations

The orchestrator is the coordination layer that turns user actions into durable backend work.

It must treat every long-running action as an accepted-and-polled workflow.

Required orchestrator behavior:

- create a durable request snapshot before execution starts
- claim work through a lease rather than relying on process-local state
- support retries by creating new attempts
- keep events append-only
- surface job status through read-only projections
- avoid assuming that execution will complete in the same process or the same runtime

Backend responsibilities:

- route the selected feature task to the correct service
- choose runtime-backed execution when available and appropriate
- preserve exact payloads for inspection, retry, and auditability
- keep stage transitions and terminal outcomes explicit

Task routing expectations:

- brainstorm requests should map to capture and promotion tasks
- foundation changes should map to revision and downstream invalidation tasks
- character and world updates should map to upsert and extraction tasks
- arc selection should map to recommendation and comparison tasks
- planning changes should map to dependency-aware plan updates
- drafting should map to generation and continuation tasks
- suggestions and review should map to scoring, critique, and continuity tasks

Persistence-first routing rule:

- if a task depends on a canonical object family that is not yet durably stored, the orchestrator should assign a persistence task before assigning the dependent service task
- do not route a service implementation task that would require process-local placeholder state for canonical objects such as `RelationshipEdge`, `ArcSelection`, `ArcStageMap`, `BeatPlan`, `SequencePlan`, `ChapterPlan`, `ScenePlan`, `PlanningDependency`, or `ChapterPacket`
- when persistence is the blocker, the next deterministic task should name the missing tables, repository methods, verification path, and later endpoint family that the persistence slice unlocks

### 17.13 Failure And Retry Expectations

Failure handling must preserve both user trust and data integrity.

Required failure rules:

- runtime errors must be mapped into durable failure categories
- failed attempts must persist step records and event history
- retries must create explicit new attempts instead of mutating the old attempt in place
- canonical artifacts must not be replaced by failed outputs
- placeholder bootstrap artifacts must not be exposed as successful generated content
- downstream provenance must not treat empty or missing upstream content as a real source artifact

Required retry rules:

- a retry should preserve the original run identity and create a new attempt number
- retryable failures should remain visible in inspect views
- non-retryable failures should remain terminal but still inspectable
- lineage must continue to point to the actual producing attempt

The current backend lessons that must remain true are:

- step records are durable
- artifact lineage is append-only
- inspect views are public and deterministic
- runtime-backed checker execution may fall back deterministically when runtime execution is not possible
- canonical output should survive retries, while failed attempts remain visible for diagnosis
- canonical story-development objects must not live only in service-local memory once the docs define them as persisted records
- the correct fix for a missing object family is to add persistence and repository support first, then retry the blocked service slice on top of that storage

### 17.14 Workflow States

The story-development feature set should use the canonical state families in `docs/Story Development Canonical Contract v0.1.md`.

Core stage kinds may include:

- brainstorm
- foundation
- character
- world bible
- arc selection
- planning
- drafting
- review
- inspect

Required state-family split:

- stage configuration state: `ENABLED`, `DISABLED`, `OPTIONAL`, `ARCHIVED`
- stage progress state: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `NEEDS_REVIEW`, `COMPLETE`, `SUPERSEDED`
- artifact lifecycle state: `DRAFT`, `PROPOSED`, `CANONICAL`, `SUPERSEDED`, `REJECTED`, `ARCHIVED`
- suggestion lifecycle state: `REQUESTED`, `READY`, `ACCEPTED`, `REJECTED`, `REFINE_REQUESTED`, `EXPIRED`
- backend execution state: `ACCEPTED`, `PENDING`, `CLAIMED`, `RUNNING`, `VALIDATING`, `PERSISTING`, `COMPLETED`, `FAILED`, `CANCELLED`

### 17.15 Implementation Order

The recommended build order for the story-development layer is:

1. editable core flow
2. brainstorming capture and promotion
3. foundation profile
4. character background and relationship graph
5. world bible
6. arc recommendation and stage mapping
7. planning objects
8. drafting generation and continuation
9. suggestions and revision
10. continuity and review
11. inspect and provenance polish
12. orchestrator hardening and retry coverage

This order is advisory. The project may interleave implementation as long as step records, lineage, and retry behavior stay correct.

Additional ordering rule:

- for character, world, arc, planning, drafting, review, and inspect slices, introduce missing canonical persistence before accepting a service implementation that would otherwise invent temporary state
