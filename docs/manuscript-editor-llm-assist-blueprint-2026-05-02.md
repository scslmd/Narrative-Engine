# Manuscript Editor LLM Assist Blueprint

Date: 2026-05-02

## Implementation Progress (Current Branch)

- [x] MS-ASSIST-001: Add Manuscript Assist Schemas
- [x] MS-ASSIST-002: Add Persistence Tables
- [x] MS-ASSIST-003: Add Repository Methods
- [x] MS-ASSIST-004: Add Manuscript Assist Service
- [x] MS-ASSIST-005: Add Assist Gate Service
- [x] MS-ASSIST-006: Add Runtime Prompt Builders
- [x] MS-ASSIST-007: Add Executor Phases
- [x] MS-ASSIST-008: Add Manuscript Assist API
- [x] MS-ASSIST-009: Add Frontend Types And Service
- [x] MS-ASSIST-010: Add `useManuscriptAssist` Hook
- [x] MS-ASSIST-011: Upgrade Manuscript Editor Toolbar (Phase 1 textarea selection/actions)
- [x] MS-ASSIST-012: Add LLM Suggestions Panel Integration (merged with existing AidsPanel)
- [ ] MS-ASSIST-013: Dedicated fork-from-selection modal workflow
- [x] MS-ASSIST-014: Wire Writing View
- [x] MS-ASSIST-015: End-To-End Fake LLM Test

## Purpose

This document defines the implementation plan for a frontend manuscript “word processor” that lets an author edit generated manuscript text, fork or modify story branches from those edits, and request backend LLM assistance for story development, canon checks, revision suggestions, alternate scenes, continuations, and repair.

This is documentation only. It is designed to connect with:

- `docs/story-generation-orchestration-blueprint-2026-05-02.md`
- `docs/frontend-canon-customization-enhancement-blueprint-2026-05-02.md`

## Current Capability

Current frontend:

- `/workspace/:projectId/write` renders manuscript documents.
- `ManuscriptEditor` displays manuscript content.
- User can click `Edit`, modify content in a textarea, and save.
- Save calls `PATCH /story-development/drafting/manuscript-documents/{document_id}`.
- Save triggers `POST /story-development/drafting/manuscript-documents/{document_id}/review`.
- `AidsPanel` displays revision suggestions and a diff viewer.

Current backend:

- `DraftingService` persists manuscripts and draft artifacts.
- `DraftingService` can continue drafts and create alternate variants, but the frontend does not expose these actions.
- `ManuscriptReviewService` is rule-based. It checks repetition, blank paragraphs, and potential new character names.
- `LocalExecutor` can draft chapters in `P-300`, but it is not connected to an interactive editor assist workflow.

Current gaps:

- No rich editor model with selection/range metadata.
- No LLM-based developmental edit review.
- No LLM-based continuation from user edits.
- No “fork from selection” or “alternate version from paragraph/scene” workflow.
- No canon-aware review of user modifications.
- No persistent edit session or revision provenance.
- No UI for accepting/rejecting LLM suggestions beyond simple text replacement.
- No orchestrator phase dedicated to manuscript assists.

## Target Behavior

The author should be able to:

1. Open a generated manuscript in a word-processor-like editor.
2. Edit text directly.
3. Select a passage and ask for:
   - developmental notes
   - line edit
   - continuity/canon check
   - character voice check
   - expand scene
   - compress scene
   - rewrite in same voice
   - alternate version
   - continue from here
   - fork story from here
4. Receive LLM suggestions with diff, rationale, canon risk, and confidence.
5. Accept suggestions into the manuscript.
6. Reject or archive suggestions.
7. Create a draft artifact or story branch from a selected passage or edited manuscript.
8. Run canon gates before promotion.
9. Inspect lineage for all LLM assists and generated forks.

## UX Model

## Route

Existing:

- `/workspace/:projectId/write`
- `/workspace/:projectId/write/:chapterId`

Enhance route with optional query params:

- `/workspace/:projectId/write/:chapterId?document_id={id}&assist={assist_id}`

## Layout

Main regions:

- Left sidebar: manuscripts and draft artifacts.
- Center: rich manuscript editor.
- Right panel: LLM Assist panel.
- Bottom or modal: diff/compare and fork controls.

## Editor Modes

- `read`
- `edit`
- `suggest`
- `compare`
- `fork`

## Assist Actions

Selection-aware actions:

- `review_selection`
- `line_edit_selection`
- `expand_selection`
- `compress_selection`
- `rewrite_selection_same_voice`
- `alternate_selection`
- `continue_from_selection`
- `fork_from_selection`

Document-wide actions:

- `developmental_review`
- `canon_check`
- `character_voice_check`
- `pacing_review`
- `theme_review`
- `continuity_repair`
- `generate_next_chapter`
- `generate_alternate_chapter`

## Backend Data Contracts

Create file:

- `app/schemas/manuscript_assist.py`

## `TextRange`

Fields:

- `start_offset: int`
- `end_offset: int`
- `selected_text: str`
- `anchor_before: str`
- `anchor_after: str`

Validation:

- `start_offset >= 0`
- `end_offset >= start_offset`
- `selected_text` required for selection actions.
- Anchors max 1,000 chars each.

Purpose:

- Allows deterministic patching even if offsets drift.

## `ManuscriptAssistKind`

Allowed values:

- `developmental_review`
- `canon_check`
- `character_voice_check`
- `pacing_review`
- `theme_review`
- `line_edit_selection`
- `expand_selection`
- `compress_selection`
- `rewrite_selection_same_voice`
- `alternate_selection`
- `continue_from_selection`
- `fork_from_selection`
- `generate_next_chapter`
- `generate_alternate_chapter`
- `continuity_repair`

## `ManuscriptAssistRequest`

Fields:

- `assist_id: str | None`
- `project_id: str`
- `document_id: str`
- `assist_kind: ManuscriptAssistKind`
- `instruction: str`
- `text_range: TextRange | None`
- `canon_scope: CanonScope | None`
- `canon_policy: CanonPolicy | None`
- `target_branch_id: str | None`
- `create_branch: bool`
- `create_draft_artifact: bool`
- `model_id: str | None`
- `temperature: float | None`
- `max_tokens: int | None`
- `idempotency_key: str | None`

Validation:

- Selection actions require `text_range`.
- Fork actions require `create_branch == true` or `create_draft_artifact == true`.
- `instruction` max 5,000 chars.
- `temperature` between 0 and 1.

## `ManuscriptAssistResult`

Fields:

- `assist_id: str`
- `project_id: str`
- `document_id: str`
- `assist_kind: ManuscriptAssistKind`
- `status: "queued" | "running" | "completed" | "blocked" | "failed"`
- `summary: str`
- `suggestions: list[LLMRevisionSuggestion]`
- `created_draft_artifact_id: str | None`
- `created_branch_id: str | None`
- `created_manuscript_document_id: str | None`
- `gate_results: list[AssistGateResult]`
- `job_ids: list[str]`
- `warnings: list[str]`

## `LLMRevisionSuggestion`

Fields:

- `suggestion_id: str`
- `assist_id: str`
- `project_id: str`
- `target_document_id: str`
- `source_text: str`
- `proposed_text: str`
- `rationale: str`
- `suggestion_kind: ManuscriptAssistKind`
- `range: TextRange | None`
- `canon_risk: "none" | "low" | "medium" | "high" | "blocking"`
- `confidence_score: float`
- `status: "REQUESTED" | "PENDING" | "ACCEPTED" | "REJECTED" | "ARCHIVED"`
- `source_context: list[str]`

## `ApplyAssistSuggestionRequest`

Fields:

- `project_id: str`
- `document_id: str`
- `suggestion_id: str`
- `expected_document_version: int`
- `apply_mode: "replace_range" | "append_after_range" | "create_draft" | "create_branch"`

Validation:

- Reject if `expected_document_version` does not match current document version.
- `replace_range` requires resolvable range.

## Persistence Requirements

File:

- `app/persistence/sqlite.py`

## Table: `manuscript_assist_runs`

Columns:

- `assist_id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `document_id TEXT NOT NULL`
- `assist_kind TEXT NOT NULL`
- `request_json TEXT NOT NULL`
- `status TEXT NOT NULL`
- `summary TEXT NOT NULL DEFAULT ''`
- `created_draft_artifact_id TEXT`
- `created_branch_id TEXT`
- `created_manuscript_document_id TEXT`
- `job_ids_json TEXT NOT NULL DEFAULT '[]'`
- `warnings_json TEXT NOT NULL DEFAULT '[]'`
- `idempotency_key TEXT`
- `request_hash TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_assist_runs_project_document ON manuscript_assist_runs(project_id, document_id, updated_at)`
- `idx_assist_runs_status ON manuscript_assist_runs(status, updated_at)`
- `idx_assist_runs_idempotency ON manuscript_assist_runs(project_id, idempotency_key) WHERE idempotency_key IS NOT NULL`

## Table: `manuscript_assist_suggestions`

Columns:

- `suggestion_id TEXT PRIMARY KEY`
- `assist_id TEXT NOT NULL`
- `project_id TEXT NOT NULL`
- `target_document_id TEXT NOT NULL`
- `suggestion_kind TEXT NOT NULL`
- `source_text TEXT NOT NULL`
- `proposed_text TEXT NOT NULL`
- `rationale TEXT NOT NULL`
- `range_json TEXT`
- `canon_risk TEXT NOT NULL DEFAULT 'none'`
- `confidence_score REAL NOT NULL DEFAULT 0.0`
- `source_context_json TEXT NOT NULL DEFAULT '[]'`
- `status TEXT NOT NULL DEFAULT 'REQUESTED'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_assist_suggestions_document_status ON manuscript_assist_suggestions(project_id, target_document_id, status, updated_at)`
- `idx_assist_suggestions_assist ON manuscript_assist_suggestions(assist_id, suggestion_id)`

## Table: `manuscript_assist_gate_results`

Columns:

- `gate_result_id TEXT PRIMARY KEY`
- `assist_id TEXT NOT NULL`
- `project_id TEXT NOT NULL`
- `document_id TEXT NOT NULL`
- `gate_name TEXT NOT NULL`
- `passed INTEGER NOT NULL`
- `severity TEXT NOT NULL`
- `reasons_json TEXT NOT NULL DEFAULT '[]'`
- `created_at TEXT NOT NULL`

## Repository Requirements

File:

- `app/persistence/story_development.py`

Add dataclasses:

- `ManuscriptAssistRunRecord`
- `ManuscriptAssistSuggestionRecord`
- `ManuscriptAssistGateResultRecord`

Add methods:

- `upsert_manuscript_assist_run(...)`
- `get_manuscript_assist_run(assist_id: str)`
- `list_manuscript_assist_runs(project_id: str, document_id: str | None = None)`
- `upsert_manuscript_assist_suggestion(...)`
- `get_manuscript_assist_suggestion(suggestion_id: str)`
- `list_manuscript_assist_suggestions(project_id: str, document_id: str, status: str | None = None)`
- `update_manuscript_assist_suggestion_status(suggestion_id: str, status: str)`
- `upsert_manuscript_assist_gate_result(...)`
- `list_manuscript_assist_gate_results(assist_id: str)`

All upserts must be deterministic and idempotent.

## Backend Services

## Module: `app/services/manuscript_assist.py`

Class:

- `ManuscriptAssistService`

Responsibilities:

- Validate assist request.
- Create assist run.
- Build executor job.
- Persist suggestions.
- Apply accepted suggestions safely.
- Create draft artifacts or branches from assist results.

Dependencies:

- `StoryDevelopmentRepository`
- `DraftingService`
- `StoryBranchingService`
- `CanonPacketBuilder`
- `GenerationGateService`
- Job submission service or `JobManager`

Functions:

- `submit_assist(request: ManuscriptAssistRequest) -> ManuscriptAssistResult`
- `get_assist(assist_id: str) -> ManuscriptAssistResult`
- `list_assists(project_id: str, document_id: str | None = None) -> list[ManuscriptAssistResult]`
- `apply_suggestion(request: ApplyAssistSuggestionRequest) -> ManuscriptDocument`
- `reject_suggestion(project_id: str, suggestion_id: str) -> LLMRevisionSuggestion`
- `archive_assist(project_id: str, assist_id: str) -> ManuscriptAssistResult`
- `_resolve_document(project_id: str, document_id: str) -> ManuscriptDocumentRecord`
- `_build_assist_packet(request: ManuscriptAssistRequest) -> ManuscriptAssistPacket`
- `_queue_assist_job(run: ManuscriptAssistRunRecord, packet: ManuscriptAssistPacket) -> str`
- `_apply_text_range(content: str, range: TextRange, proposed_text: str, mode: str) -> str`
- `_create_branch_from_assist(run: ManuscriptAssistRunRecord, suggestion: LLMRevisionSuggestion) -> str`
- `_create_draft_from_assist(run: ManuscriptAssistRunRecord, suggestion: LLMRevisionSuggestion) -> str`

Apply rules:

- Require expected document version.
- Resolve exact offsets first.
- If offsets fail, resolve by `anchor_before + selected_text + anchor_after`.
- If range still cannot be resolved, return `409 Conflict`.
- Every accepted suggestion increments manuscript version through `DraftingService.save_manuscript_document`.

## Module: `app/services/manuscript_assist_gates.py`

Class:

- `ManuscriptAssistGateService`

Functions:

- `check_suggestion_against_canon(packet: ManuscriptAssistPacket, suggestion: LLMRevisionSuggestion) -> AssistGateResult`
- `check_branch_fork(packet: ManuscriptAssistPacket, draft_text: str) -> AssistGateResult`
- `check_selection_still_matches(document: ManuscriptDocumentRecord, range: TextRange) -> AssistGateResult`

Gate rules:

- Source selection must still match before applying.
- Locked canon facts must not be contradicted.
- Character voice changes must be intentional or flagged.
- New entities must be detected and either accepted or warned.
- Forks must record intentional divergence.

## Runtime Prompt Builders

File:

- `app/services/runtime_prompts.py`

Add:

- `build_m500_manuscript_assist_request(packet: ManuscriptAssistPacket, default_model: str | None) -> InferenceRequest`
- `build_m550_manuscript_repair_request(packet: ManuscriptAssistPacket, gate_reasons: list[str], default_model: str | None) -> InferenceRequest`

Prompt requirements:

- Include document title, chapter id, selected text, anchors, user instruction, relevant character bible, world bible, continuity facts, and canon policy.
- For document-wide review, include summarized manuscript chunks, not unlimited full text.
- Output strict JSON:

```json
{
  "summary": "short result summary",
  "suggestions": [
    {
      "source_text": "exact source span",
      "proposed_text": "replacement or addition",
      "rationale": "why this helps",
      "canon_risk": "none|low|medium|high|blocking",
      "confidence_score": 0.0,
      "source_context": ["character:aria", "world:capital"]
    }
  ],
  "created_branch_brief": "optional branch/fork brief",
  "warnings": []
}
```

## Executor Additions

File:

- `app/services/local_executor.py`

Add phase mapping:

- `M-500 -> manuscript_assist`
- `M-550 -> manuscript_assist_repair`

Update:

- `app/schemas/enums.py`
- `app/schemas/jobs.py`

Payload validation:

- `M-500` requires `payload.assist_id`.
- `M-550` requires `payload.assist_id` and `payload.gate_result_id`.

Executor functions:

- `_run_manuscript_assist_phase(...)`
- `_run_manuscript_assist_repair_phase(...)`

Executor behavior:

1. Load assist run.
2. Load manuscript document.
3. Build assist packet.
4. Build prompt.
5. Call LLM.
6. Parse JSON with `extract_json`.
7. Validate suggestions.
8. Run assist gates.
9. Persist suggestions and gate results.
10. Update assist run status.
11. Persist step record and lineage.

## API Requirements

Create:

- `app/api/manuscript_assist.py`

Prefix:

- `/v1/manuscript-assist`

Endpoints:

- `POST /runs`
- `GET /runs?project_id={id}&document_id={id}`
- `GET /runs/{assist_id}`
- `POST /runs/{assist_id}/retry`
- `GET /runs/{assist_id}/gates`
- `GET /suggestions?project_id={id}&document_id={id}&status={status}`
- `POST /suggestions/{suggestion_id}/apply`
- `POST /suggestions/{suggestion_id}/reject`
- `POST /suggestions/{suggestion_id}/archive`

Response semantics:

- `POST /runs` returns `202 Accepted`.
- Apply returns `200 OK` with updated manuscript document.
- Version conflict returns `409 Conflict`.
- Missing document/suggestion returns `404`.

Register in:

- `app/main.py`

## Frontend Types

Create:

- `frontend/src/types/manuscriptAssist.ts`

Types:

- `TextRange`
- `ManuscriptAssistKind`
- `ManuscriptAssistRequest`
- `ManuscriptAssistResult`
- `LLMRevisionSuggestion`
- `ApplyAssistSuggestionRequest`
- `AssistGateResult`

Keep backend field names in snake_case.

## Frontend Services

Create:

- `frontend/src/services/manuscriptAssist.ts`

Functions:

- `submitManuscriptAssist(request: ManuscriptAssistRequest): Promise<ManuscriptAssistResult>`
- `getManuscriptAssist(assistId: string): Promise<ManuscriptAssistResult>`
- `listManuscriptAssists(projectId: string, documentId?: string): Promise<ManuscriptAssistResult[]>`
- `retryManuscriptAssist(assistId: string): Promise<ManuscriptAssistResult>`
- `getManuscriptAssistGates(assistId: string): Promise<AssistGateResult[]>`
- `getLLMSuggestions(projectId: string, documentId: string, status?: string): Promise<LLMRevisionSuggestion[]>`
- `applyLLMSuggestion(request: ApplyAssistSuggestionRequest): Promise<ManuscriptDocument>`
- `rejectLLMSuggestion(projectId: string, suggestionId: string): Promise<LLMRevisionSuggestion>`
- `archiveLLMSuggestion(projectId: string, suggestionId: string): Promise<LLMRevisionSuggestion>`

Use:

- `frontend/src/lib/api.ts`

## Frontend Editor Upgrade

Current:

- `ManuscriptEditor` uses a textarea.

Phase 1 target:

- Keep textarea for lower risk.
- Add selection capture with `selectionStart`, `selectionEnd`, selected text, and anchors.
- Add assist action toolbar.

Phase 2 target:

- Replace textarea with a richer editor only if needed.
- Candidate editor must support:
  - controlled document content
  - selection ranges
  - decorations/highlights
  - inline suggestions
  - markdown/plain text compatibility

Do not add a rich editor dependency until Phase 1 proves the assist workflow.

## Frontend Components

Create directory:

- `frontend/src/components/manuscriptAssist/`

Components:

- `AssistActionToolbar.tsx`
- `AssistRequestModal.tsx`
- `AssistSuggestionCard.tsx`
- `AssistSuggestionDiff.tsx`
- `AssistGateBadge.tsx`
- `AssistRunTimeline.tsx`
- `ForkFromSelectionModal.tsx`
- `ApplySuggestionButton.tsx`

Update:

- `frontend/src/components/writing/ManuscriptEditor.tsx`
- `frontend/src/components/aids/AidsPanel.tsx`
- `frontend/src/hooks/useWritingView.ts`
- `frontend/src/views/WritingView.tsx`

## Frontend Hook Additions

Create:

- `frontend/src/hooks/useManuscriptAssist.ts`

Responsibilities:

- Track current text selection.
- Build `TextRange`.
- Submit assist requests.
- Poll assist status.
- Fetch LLM suggestions.
- Apply/reject suggestions.
- Invalidate manuscript and suggestion queries.

Return shape:

- `selectedRange`
- `assistRuns`
- `llmSuggestions`
- `isSubmittingAssist`
- `submitAssist(kind, instruction)`
- `applySuggestion(suggestionId, mode)`
- `rejectSuggestion(suggestionId)`
- `setSelectionFromEditor(start, end, content)`

## Frontend Query Keys

- `['manuscript-assist', 'runs', projectId, documentId]`
- `['manuscript-assist', 'run', assistId]`
- `['manuscript-assist', 'suggestions', projectId, documentId, status]`
- `['manuscript-assist', 'gates', assistId]`
- Existing: `['manuscript-documents', projectId]`
- Existing: `['revision-suggestions', projectId, documentId]`

## Orchestrator To Executor Markup

```yaml
orchestration_version: "manuscript-assist.v1"
assist_id: "assist_<hash>"
project_id: "project-id"
document_id: "document-id"
assist_kind: "fork_from_selection"
frontend_source:
  route: "/workspace/:projectId/write/:chapterId"
  component: "ManuscriptEditor"
  selection:
    start_offset: 1204
    end_offset: 1738
    selected_text_hash: "sha256..."
    anchor_before_hash: "sha256..."
    anchor_after_hash: "sha256..."
phases:
  - phase: "M-100"
    executor: "ManuscriptAssistService.submit_assist"
    function: "validate_and_create_run"
    inputs:
      - "ManuscriptAssistRequest"
      - "ManuscriptDocument"
      - "CanonScope"
    outputs:
      - "manuscript_assist_runs"
    gates:
      - "document_exists"
      - "selection_resolves"
      - "idempotency_ok"
  - phase: "M-500"
    executor: "LocalExecutor._run_manuscript_assist_phase"
    prompt_builder: "build_m500_manuscript_assist_request"
    job_payload:
      assist_id: "$assist_id"
    outputs:
      - "manuscript_assist_suggestions"
      - "manuscript_assist_gate_results"
    gates:
      - "llm_json_valid"
      - "suggestions_reference_source_text"
      - "canon_policy_checked"
  - phase: "M-550"
    executor: "LocalExecutor._run_manuscript_assist_repair_phase"
    prompt_builder: "build_m550_manuscript_repair_request"
    optional: true
    run_when:
      - "gate_failed"
      - "policy_allows_repair"
    outputs:
      - "repaired_suggestion"
      - "updated_gate_result"
  - phase: "M-700"
    executor: "ManuscriptAssistService.apply_suggestion"
    trigger: "user_accepts_suggestion"
    inputs:
      - "ApplyAssistSuggestionRequest"
      - "expected_document_version"
    outputs:
      - "updated ManuscriptDocument"
      - "suggestion status ACCEPTED"
    gates:
      - "version_matches"
      - "range_resolves"
      - "blocking_gates_passed_or_user_override_allowed"
  - phase: "M-800"
    executor: "ManuscriptAssistService._create_branch_from_assist"
    trigger: "user_accepts_fork"
    outputs:
      - "StoryBranch"
      - "DraftArtifact"
      - "BranchStateRef"
    gates:
      - "branch_point_recorded"
      - "intentional_divergence_recorded"
```

## Atomic Deterministic Task List

### MS-ASSIST-001: Add Manuscript Assist Schemas

Files:

- `app/schemas/manuscript_assist.py`
- `app/schemas/__init__.py`

Steps:

1. Add `TextRange`.
2. Add assist kind union.
3. Add request/result/suggestion/apply schemas.
4. Export schemas.

Acceptance:

- Selection actions reject missing text range.
- Apply request validates expected version.

Validation:

- `python -m pytest tests/test_manuscript_assist_schemas.py -q -p no:cacheprovider`

### MS-ASSIST-002: Add Persistence Tables

Files:

- `app/persistence/sqlite.py`

Steps:

1. Add `manuscript_assist_runs`.
2. Add `manuscript_assist_suggestions`.
3. Add `manuscript_assist_gate_results`.
4. Add indexes and additive migration.

Acceptance:

- Existing DB migrates.
- New DB creates tables.

Validation:

- `python -m pytest tests/test_manuscript_assist_persistence.py -q -p no:cacheprovider`

### MS-ASSIST-003: Add Repository Methods

Files:

- `app/persistence/story_development.py`
- `tests/test_manuscript_assist_persistence.py`

Steps:

1. Add record dataclasses.
2. Add upsert/get/list for assist runs.
3. Add upsert/get/list/status update for suggestions.
4. Add upsert/list for gate results.

Acceptance:

- Upserts are idempotent.
- Suggestions list by document and status.

Validation:

- `python -m pytest tests/test_manuscript_assist_persistence.py -q -p no:cacheprovider`

### MS-ASSIST-004: Add Manuscript Assist Service

Files:

- `app/services/manuscript_assist.py`
- `tests/test_manuscript_assist_service.py`

Steps:

1. Implement `submit_assist`.
2. Implement `get_assist`.
3. Implement `list_assists`.
4. Implement suggestion apply/reject/archive.
5. Implement range resolution.

Acceptance:

- Assist run can be submitted idempotently.
- Suggestion apply changes manuscript and increments version.
- Version mismatch returns service conflict error.

Validation:

- `python -m pytest tests/test_manuscript_assist_service.py -q -p no:cacheprovider`

### MS-ASSIST-005: Add Assist Gate Service

Files:

- `app/services/manuscript_assist_gates.py`
- `tests/test_manuscript_assist_gates.py`

Steps:

1. Check range still matches.
2. Check suggestion against canon packet.
3. Check fork/branch text for intentional divergence.
4. Persist deterministic gate results.

Acceptance:

- Locked canon contradiction blocks apply.
- Range drift blocks apply.

Validation:

- `python -m pytest tests/test_manuscript_assist_gates.py -q -p no:cacheprovider`

### MS-ASSIST-006: Add Runtime Prompt Builders

Files:

- `app/services/runtime_prompts.py`
- `tests/test_manuscript_assist_prompts.py`

Steps:

1. Add assist prompt builder.
2. Add repair prompt builder.
3. Require strict JSON output.
4. Add metadata phase/role fields.

Acceptance:

- Prompt includes selected text, anchors, instruction, and canon context.
- Prompt metadata includes `M-500`.

Validation:

- `python -m pytest tests/test_manuscript_assist_prompts.py -q -p no:cacheprovider`

### MS-ASSIST-007: Add Executor Phases

Files:

- `app/schemas/enums.py`
- `app/schemas/jobs.py`
- `app/services/local_executor.py`
- `tests/test_local_executor_manuscript_assist.py`

Steps:

1. Add `M-500` and `M-550` job phases.
2. Validate payloads.
3. Implement `_run_manuscript_assist_phase`.
4. Implement `_run_manuscript_assist_repair_phase`.
5. Persist step records and lineage.

Acceptance:

- Fake LLM assist creates persisted suggestions.
- Invalid JSON fails with mapped executor error.

Validation:

- `python -m pytest tests/test_local_executor_manuscript_assist.py -q -p no:cacheprovider`

### MS-ASSIST-008: Add Manuscript Assist API

Files:

- `app/api/manuscript_assist.py`
- `app/main.py`
- `tests/test_manuscript_assist_api.py`

Steps:

1. Add endpoints listed above.
2. Wire service.
3. Register router.
4. Add error mapping for 400/404/409.

Acceptance:

- Submit/list/get/apply/reject endpoints work.
- Version conflict returns 409.

Validation:

- `python -m pytest tests/test_manuscript_assist_api.py -q -p no:cacheprovider`

### MS-ASSIST-009: Add Frontend Types And Service

Files:

- `frontend/src/types/manuscriptAssist.ts`
- `frontend/src/services/manuscriptAssist.ts`
- `frontend/src/services/manuscriptAssist.test.ts`

Steps:

1. Add TS types.
2. Add service functions.
3. Add MSW tests.

Acceptance:

- Service uses shared `api`.
- Typecheck passes.

Validation:

- `cd frontend && npm run typecheck`
- `cd frontend && npm run test -- manuscriptAssist`

### MS-ASSIST-010: Add `useManuscriptAssist` Hook

Files:

- `frontend/src/hooks/useManuscriptAssist.ts`
- `frontend/src/hooks/useManuscriptAssist.test.tsx`

Steps:

1. Track selection.
2. Build `TextRange`.
3. Submit assist.
4. Poll assist.
5. Fetch suggestions.
6. Apply/reject suggestions.

Acceptance:

- Hook builds valid range from textarea offsets.
- Applying suggestion invalidates manuscript query.

Validation:

- `cd frontend && npm run test -- useManuscriptAssist`

### MS-ASSIST-011: Upgrade Manuscript Editor Toolbar

Files:

- `frontend/src/components/writing/ManuscriptEditor.tsx`
- `frontend/src/components/manuscriptAssist/AssistActionToolbar.tsx`
- `frontend/src/components/manuscriptAssist/AssistRequestModal.tsx`

Steps:

1. Capture textarea selection.
2. Show selection-aware assist actions.
3. Show document-wide assist actions.
4. Submit assist requests.

Acceptance:

- Selecting text enables selection actions.
- No selection disables selection-only actions.

Validation:

- `cd frontend && npm run test -- ManuscriptEditor`

### MS-ASSIST-012: Add LLM Suggestions Panel

Files:

- `frontend/src/components/aids/AidsPanel.tsx`
- `frontend/src/components/manuscriptAssist/AssistSuggestionCard.tsx`
- `frontend/src/components/manuscriptAssist/AssistSuggestionDiff.tsx`

Steps:

1. Merge rule-based and LLM suggestions visually.
2. Show canon risk and confidence.
3. Add accept/reject/archive actions.
4. Add diff viewer for selected suggestion.

Acceptance:

- LLM suggestions show separately from rule-based suggestions.
- Accept calls apply endpoint.

Validation:

- `cd frontend && npm run test -- AidsPanel`

### MS-ASSIST-013: Add Fork From Selection UI

Files:

- `frontend/src/components/manuscriptAssist/ForkFromSelectionModal.tsx`
- `frontend/src/components/writing/ManuscriptEditor.tsx`

Steps:

1. Add fork modal.
2. Let user choose same project branch or new draft artifact.
3. Submit `fork_from_selection`.
4. Show created branch/draft result.

Acceptance:

- Fork action requires selected text.
- Created branch/draft id is displayed.

Validation:

- `cd frontend && npm run test -- ForkFromSelectionModal`

### MS-ASSIST-014: Wire Writing View

Files:

- `frontend/src/views/WritingView.tsx`
- `frontend/src/hooks/useWritingView.ts`
- `frontend/src/hooks/useManuscriptAssist.ts`

Steps:

1. Integrate assist hook.
2. Pass assist props to editor and aids panel.
3. Invalidate manuscript/suggestion/assist queries after actions.

Acceptance:

- Author can edit, save, request assist, see suggestions, and apply one.

Validation:

- `cd frontend && npm run test -- WritingView`

### MS-ASSIST-015: End-To-End Fake LLM Test

Files:

- `tests/test_manuscript_assist_e2e.py`

Steps:

1. Create project with manuscript and canon.
2. Submit selection assist.
3. Fake LLM returns suggestion.
4. Apply suggestion.
5. Assert manuscript version increments and content changes.
6. Submit fork assist.
7. Assert draft/branch artifact created.

Acceptance:

- Mechanical end-to-end path works.

Validation:

- `python -m pytest tests/test_manuscript_assist_e2e.py -q -p no:cacheprovider`

## Production Gate

Do not claim manuscript LLM assist is production-ready until:

- User can edit manuscript text.
- User can select text and submit LLM assist.
- Backend persists assist run, suggestions, and gate results.
- Suggestions can be applied with version conflict protection.
- Fork/alternate actions create draft or branch artifacts.
- Canon gates run before applying risky suggestions.
- Frontend shows suggestions, diffs, canon risk, and apply/reject/archive controls.
- Inspect lineage exists for assist jobs.

Required validation:

- `python -m pytest tests/test_manuscript_assist_schemas.py tests/test_manuscript_assist_persistence.py tests/test_manuscript_assist_service.py tests/test_manuscript_assist_gates.py tests/test_manuscript_assist_prompts.py tests/test_local_executor_manuscript_assist.py tests/test_manuscript_assist_api.py tests/test_manuscript_assist_e2e.py -q -p no:cacheprovider`
- `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py`
- `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`
