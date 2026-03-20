# Narrative SRS v0.2

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

## 7. Async Progress

Long-running jobs and model checks must report exact backend progress.

Required endpoints:

- `POST /jobs/create`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/logs`
- `POST /role-model-checker/start`
- `GET /role-model-checker/{run_id}/status`

Implementation note:

- The frontend polls these status endpoints rather than assuming immediate completion.
- Job and checker status are durably stored in SQLite instead of process-local memory.
- The current execution path uses a local lease-claim executor stub until the real worker/runtime layer is in place.
- Step records and artifact lineage are now durably persisted in SQLite for the local executor path, but they are not yet exposed through dedicated public APIs.

## 7.1 Target Async Protocol

The target protocol for long-running jobs and checker runs is:

- enqueue request
- durable acceptance record
- worker claim or lease
- execution
- validation
- persistence
- terminal completion or failure

Target lifecycle:

`ACCEPTED -> CLAIMED -> RUNNING -> VALIDATING -> PERSISTING -> COMPLETED | FAILED | CANCELLED`

Target rules:

- acceptance and execution must be separated
- status endpoints are read-only projections over durable state
- request payloads must be durably stored before active execution begins
- retries must create explicit attempts rather than mutating prior attempts in place
- event history must be append-only even if latest-state projections are materialized separately

Reference:

- see `docs/Async Protocol Blueprint v0.1.md`
- see `docs/Step Record Blueprint v0.1.md` for the current step-record and artifact-lineage contract

## 8. Role-Model Checker

The system must support a role-model checker that validates candidate local GGUF models against the roles:

- architect
- sequencer
- drafter
- critic

The checker exists so users can test model substitutions without repeating manual troubleshooting.

Implementation note:

- The checker currently persists run metadata, results, and an optional saved report path.
- The checker still uses stub execution rather than real model evaluation.
