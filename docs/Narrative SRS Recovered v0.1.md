# Narrative SRS Recovered v0.1

## 1. Purpose

Narrative-Core is a deterministic local narrative compilation pipeline for novel development.

The system is intended to help a writer:

- define a project by name
- enter premise, tone, language, and constraints
- generate a story bible
- generate beats
- draft prose with local models
- verify outputs with a critic/linter loop
- monitor long-running jobs with exact backend progress

## 2. Recovery Context

This recovered SRS is derived from the conversation record after the original workspace contents were lost.

It captures the latest known design direction, including:

- project-name-first identity
- async backend job progress
- role-model checker workflow
- unified workflow preferences
- role-based model selection

## 3. Core Principles

- deterministic pipeline behavior where possible
- local-first execution
- explicit phase boundaries
- human-readable project identity
- backend-driven progress reporting

## 4. Project Identity

Projects must be identified to the user by `project_name`, not by UUID alone.

Rules:

- `project_id` remains the internal stable identifier and storage key
- `project_name` is the primary user-facing label in the UI and API responses
- all new project creation flows must require `project_name`
- legacy manifests without `project_name` may be backfilled with a compatibility fallback

## 5. Directory Structure

```text
/Narrative-Recover
├── /app
│   ├── /api
│   ├── /schemas
│   └── /services
├── /data
│   ├── /projects
│   └── /models
├── /docs
└── /frontend
```

## 6. Required Project APIs

- `POST /projects/create`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`

All project responses must expose:

- `project_id`
- `project_name`

## 7. Manifest Schema

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

## 8. Async Progress

Long-running jobs and model checks must report exact backend progress.

Required endpoints:

- `POST /jobs/create`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/logs`
- `POST /role-model-checker/start`
- `GET /role-model-checker/{run_id}/status`

## 9. Role-Model Checker

The system must support a role-model checker that validates candidate local GGUF models against the roles:

- architect
- sequencer
- drafter
- critic

The checker exists so future users can test model substitutions without repeating manual troubleshooting.
