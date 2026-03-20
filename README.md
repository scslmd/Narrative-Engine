# Narrative-Engine

Narrative-Engine is a local-first narrative compilation system for long-form fiction development.

The project is designed to help a writer move from premise to structured story assets, draft prose with local models, and review outputs through a deterministic multi-role workflow with durable backend progress tracking.

## Product Intent

Narrative-Engine is intended to support:

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
- persisted status polling for jobs and checker runs
- role-model checker scaffolding for model and workflow validation

## Current Status

The repository is usable and actively rebuildable, but some major runtime layers are still in progress.

Implemented and working now:

- project listing and artifact access
- persisted jobs and checker runs
- append-only event history and baseline attempt-lineage fields
- `202 Accepted` job/checker start flows with status polling
- recovered frontend prototype and supporting docs

Still being rebuilt:

- real inference/runtime integration
- true worker or lease-based execution
- full orchestrator/compiler flow
- deeper role-model checker execution against real models
- broader production-grade tests

## Quickstart

1. Create or use the local Python 3.12 environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Start the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
4. Open [http://127.0.0.1:8000/role-model-checker-ui](http://127.0.0.1:8000/role-model-checker-ui).
5. Validate the current baseline with `python -m pytest tests/test_recovered_smoke.py tests/test_persistence.py -q`.

Current verified baseline:

- `17 passed`

## Core Docs

- [docs/Narrative SRS Recovered v0.1.md](F:/Dev/Narrative-Engine/docs/Narrative%20SRS%20Recovered%20v0.1.md)
- [docs/Frontend Design SRS Recovered v0.1.md](F:/Dev/Narrative-Engine/docs/Frontend%20Design%20SRS%20Recovered%20v0.1.md)
- [docs/Async Protocol Blueprint v0.1.md](F:/Dev/Narrative-Engine/docs/Async%20Protocol%20Blueprint%20v0.1.md)
- [docs/Failure Mode Test Matrix v0.1.md](F:/Dev/Narrative-Engine/docs/Failure%20Mode%20Test%20Matrix%20v0.1.md)

## Workspace Note

This repository is the safe rebuilt workspace on `F:` created while the original `D:` workspace remained under recovery. The code and docs should now be treated as the active working copy going forward.
