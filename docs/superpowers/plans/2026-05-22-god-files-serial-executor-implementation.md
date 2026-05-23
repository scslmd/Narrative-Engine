# God Files Serial Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILLS: `test-driven-development`, `verification-before-completion`, and `requesting-code-review`. If review feedback arrives, use `receiving-code-review`. Execute the JSON contracts in strict serial order. Every task is one-file-per-task with exactly one `responsible_file`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the approved god files into package- and slice-based architecture with preserved behavior, narrow ownership boundaries, and deterministic serial execution instructions for a local LLM executor.

**Architecture:** The work is decomposed into four serial contracts so each executor batch stays within one architectural concern: persistence and service contracts, API packaging, executor and prompt extraction, then frontend planning decomposition. Within each contract, every task is executor-tight and one-file-per-task, with explicit serial dependencies, TDD-first execution, and a review gate before completion claims.

**Tech Stack:** Python, FastAPI, Pydantic, SQLite persistence layer, React, TypeScript, TanStack Query, Vitest, pytest

---

## Execution Order

- [ ] **Phase 1:** Execute [2026-05-22-god-files-phase-1-persistence-and-service-contracts.json](C:\Users\SLuh\Documents\Dev\Narrative-Engine\docs\superpowers\contracts\2026-05-22-god-files-phase-1-persistence-and-service-contracts.json)
- [ ] **Phase 2:** Execute [2026-05-22-god-files-phase-2-api-packaging.json](C:\Users\SLuh\Documents\Dev\Narrative-Engine\docs\superpowers\contracts\2026-05-22-god-files-phase-2-api-packaging.json)
- [ ] **Phase 3:** Execute [2026-05-22-god-files-phase-3-executor-and-prompts.json](C:\Users\SLuh\Documents\Dev\Narrative-Engine\docs\superpowers\contracts\2026-05-22-god-files-phase-3-executor-and-prompts.json)
- [ ] **Phase 4:** Execute [2026-05-22-god-files-phase-4-frontend-planning.json](C:\Users\SLuh\Documents\Dev\Narrative-Engine\docs\superpowers\contracts\2026-05-22-god-files-phase-4-frontend-planning.json)

## Global Rules For Every Subagent Task

- [ ] Read the architecture spec first: `docs/superpowers/specs/2026-05-22-god-files-architecture-refactor-design.md`
- [ ] Read the assigned JSON contract task fully before editing anything. Do not infer extra scope from neighboring tasks.
- [ ] Use TDD literally: write the failing test first, run it and confirm the expected failure, then write the minimal implementation.
- [ ] Never add a product feature, endpoint, field, phase, route, or UI behavior that does not already exist.
- [ ] Preserve current public import paths, route paths, and behavior unless the contract explicitly says a compatibility facade is transitional.
- [ ] Respect the one-file-per-task rule: if a contract task names one `responsible_file`, do not edit a second production file unless the contract is explicitly revised first.
- [ ] Before claiming a task is complete, run the task verification commands fresh and read the full output.
- [ ] Before moving to the next task, review the code changes for ownership-boundary violations and request a code review.

## Phase Notes

### Phase 1

- Focus: package conversion for `app/persistence/story_development`, persistence domain ownership extraction, and narrowing service repository dependencies.
- Granularity: package facade, protocol definitions, each persistence ownership module, and each service-contract narrowing step are separate serial tasks.
- Main risk: creating a new compatibility facade that silently becomes the next god file.

### Phase 2

- Focus: package conversion for `app/api/story_development`, schema extraction, and thin domain router modules.
- Granularity: packaging, schema extraction, dependency helper extraction, and route-family extraction remain serial and task-scoped by one responsible file each.
- Main risk: moving business logic into `dependencies.py` or router registration files.

### Phase 3

- Focus: package conversion and extraction for `LocalExecutor` and `runtime_prompts`.
- Granularity: context, protocol, shared types, shared errors, each helper module, each prompt module, and each executor phase module are separate serial tasks.
- Main risk: shared helper modules becoming implicit mutation backdoors.

### Phase 4

- Focus: decomposing `usePlanningController` and `PlanningView` into slice-owned hooks and tab-owned containers.
- Granularity: slice hooks, the compatibility controller, and view-shell decomposition remain separate serial tasks, each with one responsible file.
- Main risk: new shared frontend hooks becoming cross-domain logic sinks.

## Completion Standard

- [ ] Every completed task changed only its declared `responsible_file` plus any explicitly permitted test or compatibility files described in that task contract.
- [ ] Every contract task has passed its listed verification command.
- [ ] Every phase has passed its listed phase-completion verification commands.
- [ ] Every phase has had an explicit review before being marked complete.
- [ ] No completion claim is made without fresh command output.
