# Narrative-Engine

Narrative-Engine is a local-first narrative compilation system for long-form fiction development.

It is designed to help a writer move from premise to structured story assets, draft prose with local models, and review outputs through a deterministic multi-role workflow with durable backend progress tracking.

## Product Intent

Narrative-Engine supports:

- project-name-first story setup
- premise, tone, language, and constraint capture
- story bible and sequence generation
- role-based drafting and review workflows
- critic and checker feedback loops
- exact backend progress and status monitoring for long-running work

## Current Architecture

The current codebase includes:

- a FastAPI backend for projects, jobs, models, and role-model checking
- SQLite-backed persistence for operational state and project artifact indexing
- a frontend writer workflow prototype for setup, story workspace, drafting, and review
- accepted-and-polled job and checker APIs backed by a local lease-claim executor
- role-model checker scaffolding for model and workflow validation

## Current Status

Implemented and working now:

- project listing and artifact access
- persisted jobs and checker runs
- append-only event history and first-class attempt tables
- `202 Accepted` job and checker start flows with status polling and idempotent replay or conflict handling
- local lease-claim execution and stale-lease reclaim for accepted jobs and checker runs
- attempt-level executor telemetry for executor name, executor identity, queue delay, finish reasons, and reclaim context
- explicit operator retry flow for failed jobs and checker runs
- live SQLite persistence for step records and artifact lineage in the local executor path
- generalized inference provider configuration with a shared backend contract for `llama.cpp`, LM Studio, `vLLM`, and other OpenAI-compatible servers
- a real `P-100` `architect` execution path that builds an inference request, calls the configured inferencer, and persists canonical markdown output plus artifact lineage
- frontend workflow scaffolding and documentation

Still being built:

- runtime-backed generation for phases beyond the first `architect` slice
- full orchestrator/compiler flow
- deeper role-model checker execution against real models
- API projection for step records and artifact lineage
- richer runtime telemetry
- broader production-grade tests

## Quickstart

1. Create or use a local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q`.

Current verified baseline:

- see [docs/Validation Notes v0.1.md](F:/Dev/Narrative-Engine/docs/Validation%20Notes%20v0.1.md) for the latest checked command and scope

## Continuous Testing

- GitHub Actions runs the pytest baseline on `push`, `pull_request`, and manual dispatch.
- Matrix:
  - `ubuntu-latest` with Python `3.12`
  - `windows-latest` with Python `3.12`
- Workflow command:
  - `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`

## Core Docs

- [docs/Narrative SRS v0.1.md](F:/Dev/Narrative-Engine/docs/Narrative%20SRS%20v0.1.md)
- [docs/Frontend Design SRS v0.1.md](F:/Dev/Narrative-Engine/docs/Frontend%20Design%20SRS%20v0.1.md)
- [docs/Async Protocol Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Async%20Protocol%20Blueprint%20v0.1.md)
- [docs/Inference Runtime Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Inference%20Runtime%20Blueprint%20v0.1.md)
- [docs/Step Record Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Step%20Record%20Blueprint%20v0.1.md)
- [docs/Step and Lineage API Projection Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Step%20and%20Lineage%20API%20Projection%20Blueprint%20v0.1.md)
- [docs/Story Arc Paradigm Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Story%20Arc%20Paradigm%20Blueprint%20v0.1.md)
- [docs/Failure Mode Test Matrix v0.1.md](F:/Dev/Narrative-Engine/docs/Failure%20Mode%20Test%20Matrix%20v0.1.md)
