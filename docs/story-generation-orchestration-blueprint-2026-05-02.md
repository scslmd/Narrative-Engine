# Story Generation Orchestration Blueprint

Date: 2026-05-02

## Implementation Progress

- [x] SG-001 Add generation schemas (`app/schemas/generation.py`, schema exports, validation tests)
- [x] SG-002 Add generation persistence tables/indexes (`canon_generation_runs`, `canon_generation_packets`, `generation_gate_results`)
- [x] SG-003 Add repository methods
- [x] SG-004 Build canon packet builder
- [x] SG-005 Build story forking service
- [x] SG-006 Add generation gate service
- [x] SG-007 Add generation prompt builders
- [x] SG-008 Add orchestrator service
- [x] SG-009 Extend job phase enum and validation
- [x] SG-010 Extend local executor
- [x] SG-011 Add story generation API
- [x] SG-012 Add frontend types and service
- [x] SG-013 Add generation wizard UI
- [x] SG-014 Wire import CTA to generation
- [x] SG-015 Add review/inspect integration
- [x] SG-016 Add full end-to-end generation test

## Purpose

This document defines what is needed for the application to support the advertised behavior:

`ingest completed story -> extract character bible/world bible/continuity -> generate a new canon-congruent story -> optionally fork selected characters/world elements into a new story/project`

This is documentation only. It is written as an orchestrator-to-executor implementation plan with deterministic modules, functions, data contracts, endpoints, frontend hooks, gates, and tests.

## Current Capability

The application currently supports these pieces:

- `POST /projects/import-story` imports a source story and creates project foundation, characters, world bible, arcs, planning artifacts, continuity findings, draft briefs, and drafting context packets.
- `StoryImportService` persists imported artifacts atomically.
- `MultiPassImportService` can analyze large stories, consolidate continuity, gate continuity, and generate draft briefs/context packets when gates pass.
- `LocalExecutor` supports pipeline phases `P-100`, `P-200`, `P-300`, and `P-400`.
- `P-300` can draft chapters and auto-create manuscript documents.
- `DraftingService` supports registering drafts, continuing drafts, creating alternate variants, and promoting drafts to manuscripts.
- Branching APIs track story branches inside a project.
- Frontend has import, planning, writing, drafting, branch, job, and inspect surfaces.

The missing pieces are:

- No first-class “generate new story from imported canon” job type.
- No first-class “fork selected characters/world bible into a new project/story” command.
- No canonical generation packet that packages imported character/world/continuity constraints for executor use.
- No generation plan that maps imported canon into new premise/outline/chapter drafting targets.
- No frontend wizard for selecting source canon, generation mode, character/world scope, and output destination.
- No hard gates proving generated output is congruent with selected canon before promotion.

## Target Product Behavior

### Flow A: Generate New Story In Same Project

1. User imports a source story.
2. User opens a generation wizard from the imported project.
3. User selects generation mode: sequel, side story, alternate route, prequel, or new arc.
4. User selects canon scope: all characters/world bible, selected characters, selected locations/items, selected continuity threads.
5. Backend builds a `CanonGenerationPacket`.
6. Orchestrator creates a generation run.
7. Executor generates story premise, sequence plan, chapter plans, draft briefs, chapter drafts, manuscript documents.
8. Consistency gates compare generated artifacts against selected canon.
9. UI presents generated story with warnings, inspect lineage, and promote/accept actions.

### Flow B: Fork Characters To New Story Project

1. User opens “Fork to New Story” from a source project.
2. User selects characters and optional world bible constraints.
3. Backend creates a target project.
4. Backend copies or transforms selected characters/world bible entries into the target project.
5. Backend creates a generation brief for the new story.
6. Orchestrator runs generation in the target project using source canon as locked provenance.
7. UI links source project and target project.

### Flow C: Alternate Variant From Existing Draft/Manuscript

1. User selects a draft/manuscript.
2. User chooses alternate premise, branch point, or changed decision.
3. Backend creates a branch/generation packet.
4. Executor drafts alternate chapters with provenance back to the base artifact.
5. Consistency gates ensure intentional differences are recorded and accidental contradictions are flagged.

## Backend Architecture Additions

## Module: `app/schemas/generation.py`

Create strict schemas for the generation contract. These must be separate from raw import schemas because generation has destination, scope, and policy requirements.

### `CanonScope`

Fields:

- `source_project_id: str`
- `character_ids: list[str]`
- `world_bible_refs: list[WorldBibleRef]`
- `continuity_thread_ids: list[str]`
- `arc_ids: list[str]`
- `include_relationships: bool`
- `include_unresolved_questions: bool`
- `include_contradictions_as_forbidden: bool`

Validation:

- `source_project_id` required.
- At least one of `character_ids`, `world_bible_refs`, `continuity_thread_ids`, or `arc_ids` must be selected unless `scope_mode == "full_project"`.
- All ids must be non-empty stable ids.

### `WorldBibleRef`

Fields:

- `entry_type: str`
- `title: str`

Validation:

- Match existing world bible endpoint identity: `entry_type` plus `title`.

### `GenerationMode`

Allowed values:

- `same_project_new_arc`
- `same_project_sequel`
- `same_project_prequel`
- `same_project_side_story`
- `same_project_alternate_route`
- `new_project_character_fork`
- `new_project_world_fork`
- `new_project_hybrid_fork`

### `GenerationDestination`

Fields:

- `destination_kind: "same_project" | "new_project"`
- `target_project_id: str | None`
- `target_project_name: str | None`
- `source_branch_id: str | None`
- `target_branch_id: str | None`

Validation:

- `same_project` requires `target_project_id`.
- `new_project` requires `target_project_name`; backend creates `target_project_id`.

### `CanonGenerationRequest`

Fields:

- `request_id: str | None`
- `source_project_id: str`
- `mode: GenerationMode`
- `destination: GenerationDestination`
- `canon_scope: CanonScope`
- `generation_brief: str`
- `premise_override: str | None`
- `tone_override: str | None`
- `pov_override: str | None`
- `target_chapter_count: int`
- `target_words_per_chapter: int | None`
- `canon_policy: CanonPolicy`
- `review_policy: GenerationReviewPolicy`
- `model_id: str | None`
- `temperature: float | None`
- `max_tokens: int | None`
- `idempotency_key: str | None`

Validation:

- `generation_brief` required, max 10,000 chars.
- `target_chapter_count` between 1 and 100.
- `target_words_per_chapter` between 250 and 10,000 when provided.
- `temperature` between 0 and 1.

### `CanonPolicy`

Fields:

- `locked_character_fields: list[str]`
- `locked_world_fields: list[str]`
- `allowed_character_changes: list[str]`
- `allowed_world_changes: list[str]`
- `forbidden_contradictions: list[str]`
- `continuity_strictness: "warn" | "block" | "repair_once" | "repair_twice"`

Default locked character fields:

- `display_name`
- `role_in_story`
- `backstory`
- `voice_notes`
- `continuity_facts`
- `relationships_json`

Default locked world fields:

- `entry_type`
- `title`
- `summary`
- `canonical_facts`

### `CanonGenerationPacket`

This is the executor input artifact. It must be deterministic and hashable.

Fields:

- `packet_id: str`
- `source_project_id: str`
- `target_project_id: str`
- `mode: GenerationMode`
- `generation_brief: str`
- `foundation_snapshot: dict`
- `characters: list[CanonicalCharacterSnapshot]`
- `relationships: list[CanonicalRelationshipSnapshot]`
- `world_bible: list[CanonicalWorldSnapshot]`
- `arcs: list[CanonicalArcSnapshot]`
- `continuity_threads: list[CanonicalContinuityThreadSnapshot]`
- `continuity_findings: list[CanonicalContinuityFindingSnapshot]`
- `drafting_context_packets: list[CanonicalDraftingContextSnapshot]`
- `canon_policy: CanonPolicy`
- `prompt_budget_summary: PromptBudgetSummary`
- `source_hashes: dict[str, str]`

Deterministic id:

- `packet_id = hash_id("canon-generation-packet", f"{source_project_id}:{target_project_id}:{mode}:{scope_hash}:{brief_hash}")`

### `GenerationPlan`

Fields:

- `plan_id: str`
- `project_id: str`
- `packet_id: str`
- `mode: GenerationMode`
- `premise: str`
- `logline: str`
- `story_arcs: list[GeneratedArcPlan]`
- `chapter_plans: list[GeneratedChapterPlan]`
- `canon_obligations: list[str]`
- `intentional_differences: list[str]`
- `forbidden_contradictions: list[str]`
- `status: "draft" | "approved" | "blocked" | "failed"`
- `gate_reasons: list[str]`

### `GenerationRunResponse`

Fields:

- `generation_id: str`
- `source_project_id: str`
- `target_project_id: str`
- `job_ids: list[str]`
- `status: "queued" | "running" | "completed" | "blocked" | "failed"`
- `warnings: list[str]`
- `created_artifacts: list[GenerationArtifactRef]`

## Persistence Additions

## Table: `canon_generation_runs`

Columns:

- `generation_id TEXT PRIMARY KEY`
- `source_project_id TEXT NOT NULL`
- `target_project_id TEXT NOT NULL`
- `mode TEXT NOT NULL`
- `request_json TEXT NOT NULL`
- `canon_scope_json TEXT NOT NULL`
- `canon_policy_json TEXT NOT NULL`
- `status TEXT NOT NULL`
- `gate_status TEXT NOT NULL DEFAULT 'pending'`
- `warnings_json TEXT NOT NULL DEFAULT '[]'`
- `created_job_ids_json TEXT NOT NULL DEFAULT '[]'`
- `created_artifacts_json TEXT NOT NULL DEFAULT '[]'`
- `idempotency_key TEXT`
- `request_hash TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_generation_runs_source_created ON canon_generation_runs(source_project_id, created_at)`
- `idx_generation_runs_target_created ON canon_generation_runs(target_project_id, created_at)`
- `idx_generation_runs_status ON canon_generation_runs(status, updated_at)`
- `idx_generation_runs_idempotency ON canon_generation_runs(source_project_id, idempotency_key) WHERE idempotency_key IS NOT NULL`

## Table: `canon_generation_packets`

Columns:

- `packet_id TEXT PRIMARY KEY`
- `generation_id TEXT NOT NULL`
- `source_project_id TEXT NOT NULL`
- `target_project_id TEXT NOT NULL`
- `packet_json TEXT NOT NULL`
- `source_hashes_json TEXT NOT NULL`
- `prompt_budget_json TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

## Table: `generation_gate_results`

Columns:

- `gate_result_id TEXT PRIMARY KEY`
- `generation_id TEXT NOT NULL`
- `project_id TEXT NOT NULL`
- `artifact_kind TEXT NOT NULL`
- `artifact_id TEXT NOT NULL`
- `gate_name TEXT NOT NULL`
- `passed INTEGER NOT NULL`
- `severity TEXT NOT NULL`
- `reasons_json TEXT NOT NULL DEFAULT '[]'`
- `repair_attempted INTEGER NOT NULL DEFAULT 0`
- `repair_job_id TEXT`
- `created_at TEXT NOT NULL`

Deterministic id:

- `gate_result_id = hash_id("generation-gate", f"{generation_id}:{artifact_kind}:{artifact_id}:{gate_name}")`

## Repository Additions

File: `app/persistence/story_development.py`

Add record dataclasses:

- `CanonGenerationRunRecord`
- `CanonGenerationPacketRecord`
- `GenerationGateResultRecord`

Add methods:

- `upsert_canon_generation_run(...) -> CanonGenerationRunRecord`
- `get_canon_generation_run(generation_id: str) -> CanonGenerationRunRecord`
- `list_canon_generation_runs(project_id: str, *, role: "source" | "target" | "either") -> list[CanonGenerationRunRecord]`
- `upsert_canon_generation_packet(...) -> CanonGenerationPacketRecord`
- `get_canon_generation_packet(packet_id: str) -> CanonGenerationPacketRecord`
- `upsert_generation_gate_result(...) -> GenerationGateResultRecord`
- `list_generation_gate_results(generation_id: str) -> list[GenerationGateResultRecord]`

All upserts must be idempotent and must not create duplicate generation records for the same idempotency key and request hash.

## Service Additions

## Module: `app/services/canon_packet_builder.py`

Purpose:

- Build a compact, deterministic, prompt-budget-aware `CanonGenerationPacket` from source project data.

Class:

- `CanonPacketBuilder`

Dependencies:

- `StoryDevelopmentRepository`
- `ProjectService`

Functions:

- `build_packet(request: CanonGenerationRequest, target_project_id: str) -> CanonGenerationPacket`
- `_load_foundation_snapshot(project_id: str) -> dict`
- `_load_character_snapshots(scope: CanonScope) -> list[CanonicalCharacterSnapshot]`
- `_load_relationship_snapshots(scope: CanonScope) -> list[CanonicalRelationshipSnapshot]`
- `_load_world_snapshots(scope: CanonScope) -> list[CanonicalWorldSnapshot]`
- `_load_arc_snapshots(scope: CanonScope) -> list[CanonicalArcSnapshot]`
- `_load_continuity_snapshots(scope: CanonScope) -> tuple[list[...], list[...]]`
- `_load_drafting_context_snapshots(project_id: str, scope: CanonScope) -> list[CanonicalDraftingContextSnapshot]`
- `_compute_source_hashes(packet_parts: dict) -> dict[str, str]`
- `_fit_prompt_budget(packet: CanonGenerationPacket, max_chars: int) -> CanonGenerationPacket`

Rules:

- Full character profile is included for selected major characters.
- Supporting characters are summarized unless explicitly selected.
- World bible entries include `canonical_facts` first, prose summary second.
- Continuity contradictions become `canon_policy.forbidden_contradictions` when `include_contradictions_as_forbidden` is true.
- Packet ordering must be stable: characters by `display_name`, world entries by `(entry_type, title)`, arcs by `name`, threads by `title`.

## Module: `app/services/story_forking.py`

Purpose:

- Create a target project for new story generation and copy selected canon into it.

Class:

- `StoryForkingService`

Functions:

- `create_fork_project(request: CanonGenerationRequest) -> str`
- `copy_selected_characters(source_project_id: str, target_project_id: str, character_ids: list[str]) -> list[str]`
- `copy_selected_relationships(source_project_id: str, target_project_id: str, character_ids: list[str]) -> list[str]`
- `copy_selected_world_entries(source_project_id: str, target_project_id: str, refs: list[WorldBibleRef]) -> list[str]`
- `create_fork_foundation(source_project_id: str, target_project_id: str, request: CanonGenerationRequest) -> str`
- `record_source_link(source_project_id: str, target_project_id: str, generation_id: str) -> None`

Rules:

- Character ids in target project should be deterministic:
  - `hash_id("fork-character", f"{source_project_id}:{target_project_id}:{source_character_id}")`
- Relationships copied only if both endpoints are selected.
- Copied records must preserve provenance note: `forked from {source_project_id}:{source_id}`.
- New project manifest must record source project link and generation mode.

## Module: `app/services/story_generation_orchestrator.py`

Purpose:

- Convert a user generation request into a deterministic series of executor jobs and repository artifacts.

Class:

- `StoryGenerationOrchestrator`

Dependencies:

- `StoryDevelopmentRepository`
- `ProjectService`
- `CanonPacketBuilder`
- `StoryForkingService`
- `JobManager` or existing job creation service

Functions:

- `submit_generation(request: CanonGenerationRequest) -> GenerationRunResponse`
- `get_generation(generation_id: str) -> GenerationRunResponse`
- `list_generations(project_id: str) -> list[GenerationRunResponse]`
- `_resolve_destination(request: CanonGenerationRequest) -> str`
- `_create_generation_run(request: CanonGenerationRequest, target_project_id: str) -> CanonGenerationRunRecord`
- `_build_and_store_packet(run: CanonGenerationRunRecord, request: CanonGenerationRequest) -> CanonGenerationPacket`
- `_create_generation_plan_job(run: CanonGenerationRunRecord, packet: CanonGenerationPacket) -> str`
- `_create_chapter_draft_jobs(run: CanonGenerationRunRecord, plan: GenerationPlan) -> list[str]`
- `_record_artifact_refs(run: CanonGenerationRunRecord, refs: list[GenerationArtifactRef]) -> None`
- `_finalize_or_block(run: CanonGenerationRunRecord) -> GenerationRunResponse`

Minimum orchestration phases:

- `G-100`: Canon packet build and destination setup.
- `G-200`: New story architecture and generation plan.
- `G-300`: Chapter drafting loop using draft briefs/context packet and prior summaries.
- `G-350`: Canon consistency gate and repair loop.
- `G-400`: Manuscript assembly and promotion.

## Module: `app/services/generation_gates.py`

Purpose:

- Enforce canon congruence between generated outputs and selected source canon.

Class:

- `GenerationGateService`

Functions:

- `check_generation_plan(packet: CanonGenerationPacket, plan: GenerationPlan) -> GateResult`
- `check_chapter_draft(packet: CanonGenerationPacket, chapter_id: str, draft_text: str) -> GateResult`
- `check_manuscript(packet: CanonGenerationPacket, manuscript_text: str) -> GateResult`
- `build_repair_prompt(packet: CanonGenerationPacket, artifact_text: str, result: GateResult) -> InferenceRequest`
- `should_block(result: GateResult, policy: CanonPolicy) -> bool`

Gate checks:

- Locked character facts are not contradicted.
- Character voice notes are reflected or not contradicted.
- Relationship facts are not contradicted.
- World canonical facts are not contradicted.
- Forbidden contradictions are absent.
- Intentional differences are explicitly listed.
- New entities are either allowed or routed through entity intake.
- Chapter drafts satisfy assigned chapter plan and draft brief.

Gate result severities:

- `info`
- `warning`
- `blocking`

Repair policy:

- `warn`: record warning, allow progression.
- `block`: stop generation before promotion.
- `repair_once`: one repair attempt, then block if still failing.
- `repair_twice`: two repair attempts, then block if still failing.

## Runtime Prompt Additions

File: `app/services/runtime_prompts.py`

Add builders:

- `build_g200_story_generation_plan_request(packet: CanonGenerationPacket, default_model: str | None) -> InferenceRequest`
- `build_g300_chapter_generation_request(packet: CanonGenerationPacket, plan: GenerationPlan, chapter_id: str, prior_summaries: list[str], default_model: str | None) -> InferenceRequest`
- `build_g350_canon_repair_request(packet: CanonGenerationPacket, artifact_text: str, gate_reasons: list[str], default_model: str | None) -> InferenceRequest`
- `build_g400_manuscript_assembly_request(packet: CanonGenerationPacket, chapter_artifacts: list[DraftArtifact], default_model: str | None) -> InferenceRequest`

Prompt rules:

- Always include explicit selected canon, not counts.
- Separate locked canon from optional inspiration.
- Include `intentional_differences` as a required output field for planning.
- Require generated plans to cite source canon ids in `canon_obligations`.
- For chapter drafting, include only current chapter brief, active character roster, relevant world constraints, active continuity threads, and capped prior summaries.
- Never ask model to invent source ids.

## Executor Additions

File: `app/services/local_executor.py`

Add phase mapping:

- `G-200 -> generation_planner`
- `G-300 -> generation_drafter`
- `G-350 -> generation_gate`
- `G-400 -> generation_compiler`

Update job phase enum:

- File: `app/schemas/enums.py`
- Add job phases `G-200`, `G-300`, `G-350`, `G-400`.

Update job validation:

- File: `app/schemas/jobs.py`
- Generation phases require `payload.generation_id`.
- `G-300` additionally accepts `payload.chapter_ids` or `payload.chapter_id`.
- `G-350` requires `payload.artifact_refs`.
- `G-400` requires `payload.chapter_artifact_ids`.

New executor functions:

- `_run_generation_planner_phase(...)`
- `_run_generation_drafter_phase(...)`
- `_run_generation_gate_phase(...)`
- `_run_generation_compiler_phase(...)`

Executor persistence rules:

- Every phase creates `StepRecordService.create_step_record(...)`.
- Every generated artifact creates lineage through `_finalize_generated_job_phase(...)` or equivalent.
- G-300 chapter outputs create `DraftArtifact` and `ManuscriptDocument` records.
- G-350 gate outputs create `generation_gate_results`.
- G-400 creates or updates final manuscript.

## API Additions

File: `app/api/story_generation.py`

Router prefix:

- `/v1/story-generation`

Endpoints:

- `POST /runs`
- `GET /runs?project_id={id}`
- `GET /runs/{generation_id}`
- `POST /runs/{generation_id}/retry`
- `GET /runs/{generation_id}/packet`
- `GET /runs/{generation_id}/gates`
- `POST /fork-preview`
- `POST /fork-project`

Request/response models:

- `CanonGenerationRequest`
- `GenerationRunResponse`
- `CanonForkPreviewResponse`
- `CanonGenerationPacket`
- `GenerationGateResultListResponse`

Endpoint behavior:

- `POST /runs` creates or resumes an idempotent generation run.
- `POST /fork-preview` validates selected canon and returns what would be copied.
- `POST /fork-project` creates target project and returns target project id without running generation unless `start_generation` is true.
- All endpoints must return precise `400`, `404`, `409`, and `500` errors.

App registration:

- File: `app/main.py`
- Include `story_generation` router under `/v1/story-generation`.

## Frontend Additions

## Types

Create file:

- `frontend/src/types/storyGeneration.ts`

Types:

- `GenerationMode`
- `CanonScope`
- `WorldBibleRef`
- `GenerationDestination`
- `CanonPolicy`
- `CanonGenerationRequest`
- `GenerationRunResponse`
- `CanonGenerationPacket`
- `GenerationGateResult`
- `CanonForkPreviewResponse`

Keep backend field names in snake_case.

## Service

Create file:

- `frontend/src/services/storyGeneration.ts`

Functions:

- `createGenerationRun(request: CanonGenerationRequest): Promise<GenerationRunResponse>`
- `getGenerationRun(generationId: string): Promise<GenerationRunResponse>`
- `listGenerationRuns(projectId: string): Promise<GenerationRunResponse[]>`
- `retryGenerationRun(generationId: string): Promise<GenerationRunResponse>`
- `getGenerationPacket(generationId: string): Promise<CanonGenerationPacket>`
- `getGenerationGates(generationId: string): Promise<GenerationGateResult[]>`
- `previewFork(request: CanonGenerationRequest): Promise<CanonForkPreviewResponse>`
- `createForkProject(request: CanonGenerationRequest): Promise<GenerationRunResponse>`

Use:

- `frontend/src/lib/api.ts`

Do not use:

- local `fetch`
- local `API_BASE`

## UI Components

Create components:

- `frontend/src/components/generation/StoryGenerationWizard.tsx`
- `frontend/src/components/generation/CanonScopeSelector.tsx`
- `frontend/src/components/generation/GenerationModeSelector.tsx`
- `frontend/src/components/generation/GenerationDestinationSelector.tsx`
- `frontend/src/components/generation/CanonPolicyEditor.tsx`
- `frontend/src/components/generation/ForkPreviewPanel.tsx`
- `frontend/src/components/generation/GenerationRunCard.tsx`
- `frontend/src/components/generation/GenerationGatePanel.tsx`
- `frontend/src/components/generation/GeneratedStoryReview.tsx`

Wizard steps:

1. Select mode.
2. Select destination.
3. Select characters.
4. Select world bible entries.
5. Select continuity threads/arcs.
6. Enter generation brief.
7. Configure canon policy.
8. Preview fork/generation packet.
9. Submit run.
10. Monitor run and inspect gates.

## Views

Add route:

- `/workspace/:projectId/generate`

Files:

- `frontend/src/App.tsx`
- `frontend/src/views/GenerationView.tsx`
- `frontend/src/components/Layout.tsx` if navigation is centrally declared there

GenerationView responsibilities:

- Load characters with `getCharacters(projectId)`.
- Load world bible with `getWorldBibleEntries(projectId)`.
- Load arcs/chapter plans as needed.
- Load generation runs with `listGenerationRuns(projectId)`.
- Render wizard and run list.
- Navigate to write/review/inspect after generation.

## Existing Frontend Integration Points

Update:

- `frontend/src/components/projects/StoryImportModal.tsx`

Add post-import call-to-action:

- `Open Project`
- `Generate From Imported Canon`

Update:

- `frontend/src/views/PlanningView.tsx`

Add generation actions from character/world/branch tabs:

- `Generate story with selected characters`
- `Fork selected characters`
- `Generate side story from this branch`

Update:

- `frontend/src/views/WritingView.tsx`

Show generated run provenance on drafts/manuscripts:

- source generation id
- source project id when forked
- gate status
- warning count

Update:

- `frontend/src/components/writing/DraftList.tsx`

Add actions:

- `Run canon gate`
- `Repair canon issues`
- `Promote if gates pass`

## Orchestrator To Executor Markup

The orchestrator must emit a deterministic execution manifest for every generation run. Store it inside `canon_generation_runs.request_json` and expose it via `GET /runs/{generation_id}`.

```yaml
orchestration_version: "story-generation.v1"
generation_id: "gen_<hash>"
source_project_id: "source-project"
target_project_id: "target-project"
mode: "new_project_character_fork"
idempotency_key: "user-or-client-key"
phases:
  - phase: "G-100"
    executor: "orchestrator"
    function: "StoryGenerationOrchestrator._build_and_store_packet"
    inputs:
      request_ref: "canon_generation_runs.request_json"
    outputs:
      - kind: "canon_generation_packet"
        id_ref: "packet_id"
    gates:
      - "scope_resolves"
      - "prompt_budget_fits"
      - "target_project_ready"
  - phase: "G-200"
    executor: "LocalExecutor._run_generation_planner_phase"
    job_payload:
      generation_id: "$generation_id"
      packet_id: "$packet_id"
    prompt_builder: "build_g200_story_generation_plan_request"
    outputs:
      - kind: "generation_plan"
      - kind: "sequence_plans"
      - kind: "chapter_plans"
    gates:
      - "plan_references_known_canon"
      - "intentional_differences_declared"
      - "chapter_count_matches_request"
  - phase: "G-300"
    executor: "LocalExecutor._run_generation_drafter_phase"
    job_payload:
      generation_id: "$generation_id"
      packet_id: "$packet_id"
      chapter_ids: "$generation_plan.chapter_ids"
    prompt_builder: "build_g300_chapter_generation_request"
    outputs:
      - kind: "draft_artifact"
      - kind: "manuscript_document"
    gates:
      - "chapter_draft_non_empty"
      - "chapter_uses_assigned_context"
      - "prior_summary_propagated"
  - phase: "G-350"
    executor: "LocalExecutor._run_generation_gate_phase"
    job_payload:
      generation_id: "$generation_id"
      packet_id: "$packet_id"
      artifact_refs: "$G-300.outputs"
    service: "GenerationGateService"
    outputs:
      - kind: "generation_gate_result"
    gates:
      - "canon_congruence"
      - "locked_fact_no_contradiction"
      - "repair_policy_satisfied"
  - phase: "G-400"
    executor: "LocalExecutor._run_generation_compiler_phase"
    job_payload:
      generation_id: "$generation_id"
      packet_id: "$packet_id"
      chapter_artifact_ids: "$G-300.draft_artifact_ids"
    prompt_builder: "build_g400_manuscript_assembly_request"
    outputs:
      - kind: "manuscript_document"
      - kind: "generation_run_completed"
    gates:
      - "all_blocking_gates_passed"
      - "lineage_complete"
```

## Atomic Deterministic Task List

### SG-001: Add Generation Schemas

Files:

- `app/schemas/generation.py`
- `app/schemas/__init__.py`

Steps:

1. Add schemas listed in `Backend Architecture Additions`.
2. Use `StrictModel` or existing strict schema base.
3. Add validators for scope, destination, target chapter count, and model parameters.
4. Export schemas from `app/schemas/__init__.py`.

Acceptance:

- Invalid empty scope is rejected.
- Invalid destination combinations are rejected.
- Valid same-project and new-project requests validate.

Validation:

- `python -m pytest tests/test_story_generation_schemas.py -q -p no:cacheprovider`

### SG-002: Add Generation Persistence Tables

Files:

- `app/persistence/sqlite.py`

Steps:

1. Add `canon_generation_runs`.
2. Add `canon_generation_packets`.
3. Add `generation_gate_results`.
4. Add indexes.
5. Add additive migration if schema version already exists.

Acceptance:

- Existing DBs migrate without rebuild failure.
- New DBs create tables.

Validation:

- `python -m pytest tests/test_story_generation_persistence.py -q -p no:cacheprovider`

### SG-003: Add Repository Methods

Files:

- `app/persistence/story_development.py`
- `tests/test_story_generation_persistence.py`

Steps:

1. Add record dataclasses.
2. Add upsert/get/list methods.
3. Ensure idempotency by `generation_id`, `packet_id`, and `gate_result_id`.
4. Add tests for retry behavior.

Acceptance:

- Repeated upsert with same ids updates one row.
- Idempotency conflict is detectable when same idempotency key has different request hash.

Validation:

- `python -m pytest tests/test_story_generation_persistence.py -q -p no:cacheprovider`

### SG-004: Build Canon Packet Builder

Files:

- `app/services/canon_packet_builder.py`
- `tests/test_canon_packet_builder.py`

Steps:

1. Load selected source artifacts.
2. Normalize ordering.
3. Build deterministic source hashes.
4. Enforce prompt budget reduction.
5. Convert contradictions to forbidden contradictions when configured.

Acceptance:

- Same input creates byte-stable JSON packet.
- Missing selected ids fail with clear error.
- Packet contains real character/world/continuity ids, not counts.

Validation:

- `python -m pytest tests/test_canon_packet_builder.py -q -p no:cacheprovider`

### SG-005: Build Story Forking Service

Files:

- `app/services/story_forking.py`
- `tests/test_story_forking_service.py`

Steps:

1. Create target project for new-project destination.
2. Copy selected characters with deterministic target ids.
3. Copy relationships only when endpoints are selected.
4. Copy selected world bible entries.
5. Create target foundation from source plus request brief.
6. Record provenance notes.

Acceptance:

- Forked project has selected characters and world bible entries.
- Relationship copy is endpoint-safe.
- Re-running same fork request does not duplicate copied entities.

Validation:

- `python -m pytest tests/test_story_forking_service.py -q -p no:cacheprovider`

### SG-006: Add Generation Gate Service

Files:

- `app/services/generation_gates.py`
- `tests/test_generation_gates.py`

Steps:

1. Implement plan gate.
2. Implement chapter draft gate.
3. Implement manuscript gate.
4. Implement repair decision policy.
5. Add deterministic gate result ids.

Acceptance:

- Locked character contradiction is blocking.
- Locked world fact contradiction is blocking.
- Intentional differences are allowed only when declared.
- `warn`, `block`, and repair policies behave distinctly.

Validation:

- `python -m pytest tests/test_generation_gates.py -q -p no:cacheprovider`

### SG-007: Add Generation Prompt Builders

Files:

- `app/services/runtime_prompts.py`
- `tests/test_story_generation_prompts.py`

Steps:

1. Add `build_g200_story_generation_plan_request`.
2. Add `build_g300_chapter_generation_request`.
3. Add `build_g350_canon_repair_request`.
4. Add `build_g400_manuscript_assembly_request`.
5. Add metadata phase/role fields.

Acceptance:

- Prompts include selected canon ids.
- Prompts include locked vs optional canon separation.
- Prompt metadata includes generation id, phase, and role.

Validation:

- `python -m pytest tests/test_story_generation_prompts.py -q -p no:cacheprovider`

### SG-008: Add Orchestrator Service

Files:

- `app/services/story_generation_orchestrator.py`
- `tests/test_story_generation_orchestrator.py`

Steps:

1. Implement `submit_generation`.
2. Resolve destination.
3. Create generation run.
4. Build/store canon packet.
5. Queue generation jobs.
6. Persist job ids and artifact refs.
7. Return `GenerationRunResponse`.

Acceptance:

- Same idempotency key and same payload returns same generation run.
- New-project mode creates target project.
- Same-project mode uses existing project.
- Generation run exposes packet and job ids.

Validation:

- `python -m pytest tests/test_story_generation_orchestrator.py -q -p no:cacheprovider`

### SG-009: Extend Job Phase Enum And Validation

Files:

- `app/schemas/enums.py`
- `app/schemas/jobs.py`
- `tests/test_jobs.py`

Steps:

1. Add generation phases.
2. Validate generation payloads.
3. Preserve existing P-phase validation.

Acceptance:

- `G-200` without `generation_id` fails.
- Existing `P-100` to `P-400` tests still pass.

Validation:

- `python -m pytest tests/test_jobs.py -q -p no:cacheprovider`

### SG-010: Extend Local Executor

Files:

- `app/services/local_executor.py`
- `tests/test_local_executor_generation_runtime.py`

Steps:

1. Map generation phases to executor roles.
2. Implement planner phase.
3. Implement drafter phase with prior summaries and canon packet context.
4. Implement gate phase.
5. Implement compiler phase.
6. Persist lineage and manuscript/draft records.

Acceptance:

- G-200 creates generation plan and planning artifacts.
- G-300 creates draft artifacts and manuscript documents.
- G-350 records gate results.
- G-400 assembles final manuscript only when blocking gates pass.

Validation:

- `python -m pytest tests/test_local_executor_generation_runtime.py -q -p no:cacheprovider`

### SG-011: Add Story Generation API

Files:

- `app/api/story_generation.py`
- `app/main.py`
- `tests/test_story_generation_api.py`

Steps:

1. Add router.
2. Add endpoints listed above.
3. Wire orchestrator service.
4. Add error mapping.
5. Register router in app.

Acceptance:

- API can submit, list, fetch, and retry generation runs.
- API can preview and create forks.
- 400/404/409 semantics are covered.

Validation:

- `python -m pytest tests/test_story_generation_api.py -q -p no:cacheprovider`

### SG-012: Add Frontend Types And Service

Files:

- `frontend/src/types/storyGeneration.ts`
- `frontend/src/services/storyGeneration.ts`
- `frontend/src/services/storyGeneration.test.ts`

Steps:

1. Add TS types with snake_case backend fields.
2. Add service functions.
3. Add MSW tests for success and errors.

Acceptance:

- Service uses shared `api`.
- Tests cover create/list/get/packet/gates/fork-preview.

Validation:

- `cd frontend && npm run typecheck`
- `cd frontend && npm run test -- storyGeneration`

### SG-013: Add Generation Wizard UI

Files:

- `frontend/src/components/generation/*.tsx`
- `frontend/src/views/GenerationView.tsx`
- `frontend/src/App.tsx`

Steps:

1. Add route `/workspace/:projectId/generate`.
2. Build wizard with deterministic state.
3. Load characters/world bible/arcs/continuity options.
4. Submit generation request.
5. Show run status and gate results.

Acceptance:

- User can submit same-project generation.
- User can preview fork.
- User can start new-project character fork.
- UI blocks submit when scope or destination is invalid.

Validation:

- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`

### SG-014: Wire Import CTA To Generation

Files:

- `frontend/src/components/projects/StoryImportModal.tsx`
- `frontend/src/views/ProjectList.tsx`
- `frontend/src/components/projects/StoryImportModal.test.tsx`

Steps:

1. Add post-import `Generate From Imported Canon` CTA.
2. Navigate to `/workspace/:projectId/generate`.
3. Preserve existing open/close behavior.

Acceptance:

- Successful import can immediately open generation wizard.
- Existing import tests still pass.

Validation:

- `cd frontend && npm run test -- StoryImportModal`

### SG-015: Add Review/Inspect Integration

Files:

- `frontend/src/components/generation/GenerationGatePanel.tsx`
- `frontend/src/views/GenerationView.tsx`
- `frontend/src/services/inspectLinks.ts`
- `tests/test_story_generation_api.py`

Steps:

1. Link generation jobs to inspect runs.
2. Surface gate result reasons.
3. Add “Jump to Inspect” for each failed gate.
4. Add “Repair” action only when repair policy allows.

Acceptance:

- Failed gate has inspectable lineage.
- Repair action queues a repair job with idempotency key.

Validation:

- `cd frontend && npm run test`
- `python -m pytest tests/test_story_generation_api.py -q -p no:cacheprovider`

### SG-016: Full End-To-End Generation Test

Files:

- `tests/test_story_generation_e2e.py`
- `frontend/src/services/storyGeneration.test.ts`

Steps:

1. Import a fixture story.
2. Submit same-project generation.
3. Verify packet, plan, drafts, gates, and manuscript records.
4. Submit new-project character fork.
5. Verify target project and copied canon.

Acceptance:

- End-to-end fake-LLM test proves the intended behavior mechanically.
- Gate failure test proves blocked promotion.

Validation:

- `python -m pytest tests/test_story_generation_e2e.py -q -p no:cacheprovider`

## Production Gate For This Feature

Do not claim the feature works as advertised until all are true:

- Generation schemas validate all modes.
- Canon packet builder emits stable packets with real ids.
- New-project fork copies selected canon deterministically.
- Orchestrator can submit and resume generation runs idempotently.
- Executor can run planner, drafter, gate, and compiler phases.
- Generated drafts/manuscripts are persisted and lineage-linked.
- Blocking canon gates prevent promotion.
- Frontend exposes wizard, run status, gate reasons, and inspect links.
- Same-project generation and new-project character fork are covered by backend integration tests.
- Frontend service and wizard tests pass.

Required validation:

- `python -m pytest tests/test_story_generation_schemas.py tests/test_story_generation_persistence.py tests/test_canon_packet_builder.py tests/test_story_forking_service.py tests/test_generation_gates.py tests/test_story_generation_orchestrator.py tests/test_story_generation_api.py tests/test_story_generation_e2e.py -q -p no:cacheprovider`
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`
- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`
