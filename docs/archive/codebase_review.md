# Narrative-Engine Code Review

## Purpose
Narrative-Engine is a local-first narrative development system for novel and story creation. It is designed to help a writer move from premise to structured story assets, draft prose with local models, and review outputs through a deterministic multi-role workflow with durable backend progress tracking.

## Core Principles
- Deterministic pipeline behavior where possible
- Local-first execution
- Explicit phase boundaries
- Human-readable project identity
- Backend-driven progress reporting
- Provider-agnostic inference integration
- Durable persistence and inspectability across runs and generated artifacts

## Project Identity
Projects must be identified by `project_name`, not by UUID alone.

## Directory Structure
The project structure includes directories for `app`, `data`, `docs`, and `frontend`.

## Required Project APIs
- `POST /projects/create`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence`
- `GET /projects/{project_id}/chapter-1`

## Manifest Schema
The manifest schema defines the structure for project configuration and constraints.

## Public Backend Surface
The current public backend surface includes API endpoints for health, models, projects, jobs, and role-model-checker runs.

## Async Protocol Overview
The async protocol defines a hardened protocol for work that can be completed before the full queue/worker runtime is integrated. It removes ambiguity from the current implementation state and establishes one deterministic protocol for pipeline jobs, role-model checker runs, and future per-role execution steps.

### Implementation Status
- Implemented: `202 Accepted` enqueue semantics, status polling, local lease-claim execution, stale-lease reclaim events, immutable request snapshots, append-only event history, first-class attempt tables, explicit retry attempts, attempt-level executor telemetry, and `Idempotency-Key` replay or conflict handling.
- Implemented for step persistence: live SQLite step records, artifact lineage, local-executor writes, fixture coverage, and persistence tests.
- Implemented for real runtime paths: `P-100` architect execution, `P-200` sequencer execution, `P-300` drafter execution, and `P-400` compiler execution through the generalized inferencer with canonical artifact registration.
- Implemented for inspectability: dedicated public API projections for persisted step records and artifact lineage, including `attempt`, `limit`, and `offset` query support.
- Implemented for runtime hardening: unsupported job phases fail deterministically, and runtime jobs do not transition to `COMPLETED` before persistence and artifact registration succeed.
- Still to be implemented: richer runtime-grade model telemetry for step records and artifact lineage.

### Protocol Goals
- Separate request acceptance from execution.
- Make status transitions explicit and finite.
- Make restart/resume behavior deterministic.
- Make duplicate submission behavior deterministic.
- Make telemetry and provenance durable enough for rebuild-time debugging.
- Make future worker integration a matter of wiring, not redesign.

### Canonical Async Model
Each run has a stable `run_id`, a `run_kind` (pipeline_job or role_model_check), an immutable request snapshot, a strict lifecycle state, append-only event history, optional child step records, and final artifacts/report pointers.

### State Machine
- `PENDING`: request persisted, not yet leased by a worker.
- `CLAIMED`: a worker/runner has an active lease and intends to execute.
- `RUNNING`: role or phase work is actively executing.
- `VALIDATING`: outputs exist and are undergoing deterministic checks.
- `PERSISTING`: validated outputs are being committed to durable storage/artifact registry.
- `COMPLETED`: terminal success.
- `FAILED`: terminal failure after retry policy is exhausted or failure is non-retryable.
- `CANCELLED`: terminal operator/user cancellation.

### Idempotency Semantics
All enqueue endpoints support idempotency keys. The key shape includes client-supplied `Idempotency-Key` header preferred, and if absent, a deterministic request hash is persisted without deduping automatically.

## Async Protocol Blueprint v0.1
For detailed information on the async protocol, refer to the documentation file `Async Protocol Blueprint v0.1.md`.

## Manifest Schema
The manifest schema defines the structure for project configuration and constraints.

## Public Backend Surface
The current public backend surface includes API endpoints for health, models, projects, jobs, and role-model-checker runs.

## Async Progress
The protocol for long-running jobs and model checks includes steps for acceptance, execution, validation, and persistence.

## Inference Runtime Contract
The inference layer supports provider-agnostic integration with backends such as `llama.cpp`, `lmstudio`, `vllm`, and `openai_compatible`.

## Step Records and Artifact Lineage
Step records and artifact lineage are durably persisted in SQLite for the local executor path.

## Runtime-Backed Pipeline Paths
The current runtime-backed baseline includes four real provider-backed pipeline phases: `P-100`, `P-200`, `P-300`, and `P-400`.

## Role-Model Checker
The role-model checker validates candidate local GGUF models against roles such as `architect`, `sequencer`, `drafter`, and `critic`.

## Persistence Contract
The operational SQLite database is a required system component with specific behaviors such as WAL mode, foreign keys enabled, and busy timeout configured.

## Models Endpoint Contract
The `GET /models` endpoint exposes a deterministic catalog that merges discovered local GGUF models and runtime models.

## Continuous Testing Baseline
The current backend baseline includes the GitHub Actions pytest suite.

## Implemented Now vs Not Yet Implemented
- Provider-agnostic inference layer with shared OpenAI-compatible transport
- Accepted-and-polled jobs and checker runs
- Idempotency and retry semantics
- First-class attempt lineage
- Live step records and artifact lineage in SQLite
- Real provider-backed `P-100` through `P-400` execution paths
- Canonical `architect_p100` artifact registration
- Public projection endpoints for step records and artifact lineage
- GitHub Actions pytest baseline

## Story-Development Feature Contract
The product features include editable flow, brainstorming, foundation, character background, world bible, arc selection, planning, drafting, suggestions and revision, continuity and review, and inspect and provenance.

## Implementation Order
The recommended build order for the story-development layer is:
1. Editable core flow
2. Brainstorming capture and promotion
3. Foundation profile
4. Character background and relationship graph
5. World bible
6. Arc recommendation and stage mapping
7. Planning objects
8. Drafting generation and continuation
9. Suggestions and revision
10. Continuity and review
11. Inspect and provenance polish
12. Orchestrator hardening and retry coverage

This order is advisory. The project may interleave implementation as long as step records, lineage, and retry behavior stay correct.