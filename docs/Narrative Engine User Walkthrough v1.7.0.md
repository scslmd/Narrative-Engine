# Narrative Engine - Complete User Walkthrough v1.8.0

Last updated: 2026-05-10

## Goal
This walkthrough is the full frontend operating manual. It explains every workspace interface and gives a comprehensive, practical workflow from first launch to advanced generation and iteration.

## Preconditions
- Backend is running.
- Frontend is running.
- Inference backend is configured for LLM-dependent features.
- If `NARRATIVE_API_KEY` is enabled on the server, configure API key usage for protected flows.

## Frontend Map
- `/` Project list and creation
- `/setup-wizard` Conversational setup
- `/workspace/:projectId/plan` Planning
- `/workspace/:projectId/braindump` Brain dump
- `/workspace/:projectId/write` Writing
- `/workspace/:projectId/review` Review
- `/workspace/:projectId/inspect` Inspect
- `/workspace/:projectId/canon` Canon
- `/workspace/:projectId/generate` Generate

## Phase 1: Start a Project
Route: `/`

You have four start paths.

### Path A: Manual project creation
1. Fill `Project Name`, `Genre`, `Tone Profile`, `Story Structure`, `Point of View`, `Primary Language`.
2. Optionally add `Secondary Language` and `Premise`.
3. Click `Create Project`.
4. Open the new project card.

### Path B: Guided setup
1. Click `Walk Me Through It` or open `/setup-wizard`.
2. Chat your story concept and answer follow-up prompts.
3. Watch field extraction in the preview panel.
4. Click `Save What You Have` (partial) or `Save Project` (ready state).

### Path C: Story import
1. Click `Import Existing Story`.
2. Supply source text and metadata hints.
3. Submit import and open created project.

### Path D: Project ZIP import
1. Click `Import Project`.
2. Upload exported archive.
3. Complete import and open restored project.

## Phase 2: Understand Workspace Layout
Route: `/workspace/:projectId/*`

The workspace has fixed structure:
- Main content area for active mode.
- Right rail: Notes panel and Job Launch panel.
- Bottom utility layer for runtime/status.

### Job Launch Panel
The Job Launch panel lets you trigger pipeline phases without leaving the current workspace view. Select a phase (P-100 through P-400), click to launch, and monitor recent jobs below. Failed jobs show expandable error details with fix guidance. Completed jobs display processing time. Running jobs show step progress.

Navigation in left rail is stage-aware:
- Planning stage: Brain Dump, Planning, Canon, Generate
- Writing stage: Writing
- Review stage: Review, Inspect

## Phase 3: Planning Workspace Deep Tour
Route: `/workspace/:projectId/plan`

Top tab row exposes all planning surfaces.

### Manifest
- Validate core project metadata.

### Planning
- Operate sequence/chapter/scene/beat structures.
- Use reordering and dependency-aware edits where available.

### Flow
- Customize development stages and order.

### Arcs
- Manage arc candidates, selections, and stage maps.

### Branches
- Create alternate story branches.
- Activate branch context for iterative drafting.

### Decisions
- Track decision trees and decision records.

### Checker
- Run role-model checker workflows.

### Brainstorm
- Add brainstorm items.
- Cluster items.
- Promote selected items into downstream planning objects.

### Foundation
- Maintain premise, logline, themes, constraints, voice direction.
- Use revision and review-cue context to refine consistency.

### Characters
- List, create, and edit character profiles.
- Annotate character fields for canon behavior.

### World Bible
- Create and edit world entries.
- Annotate fields and maintain canonical details.

### Relationships
The Relationships tab provides an interactive graph visualization with full relationship management:

**Create:** Click "Add Relationship" to open the creation form. Select From/To characters, relationship type, summary, optional tension and notes.

**Edit:** Three interaction paths to modify an existing relationship:
- Double-click a relationship edge in the graph — opens a centered modal pre-populated with current data. Save sends PATCH, Delete removes with confirmation.
- Click the pencil icon on any relationship card in the list view below the graph.
- Hover over an edge in the graph to reveal edit (blue pencil) and delete (red X) buttons at the edge midpoint.

**Open character profiles:** Double-click a character node to jump to the Characters tab with that character's profile editor open.

**AI Extract:** Click "AI Extract" to analyze your manuscript text via LLM and auto-create relationship edges between characters based on detected interactions and narrative connections. Requires at least 2 characters and generated chapter content.

### Planning workspace action
- `Generate Story` sends you directly to generation mode.

## Phase 4: Brain Dump Workflow
Route: `/workspace/:projectId/braindump`

1. Open brain dump mode.
2. Confirm active session or let auto-session creation occur.
3. Capture freeform text in canvas.
4. Trigger `Organize` when ready.
5. Review categorized output summary.
6. Return to editing for additional passes.

Use this mode early for ideation spikes and mid-project for problem solving.

## Phase 5: Writing Workspace Deep Tour
Route: `/workspace/:projectId/write`

Three columns define the writing experience.

### Left column: Manuscripts + Drafts
- Choose manuscript documents.
- View and manage draft artifacts.
- Create manual draft.
- Continue draft.
- Create alternate variant.
- Promote draft to manuscript.
- Generate AI draft from title+brief.
- Monitor pending draft generation entries.

### Center column: Manuscript Editor
- Read mode and edit mode.
- Save or cancel edits.
- Word/character counters.
- Selection-aware assist actions.

### Right column: Aids panel
- Unified suggestions list (standard revisions + assist suggestions).
- Accept/reject/archive actions.
- Diff/history support via aids components.

### Assist action flow
1. Select text.
2. Trigger assist action (`line_edit`, `expand`, `compress`, `rewrite`, `fork_from_selection`).
3. Review suggestion output.
4. Apply or reject.

## Phase 6: Review Workspace
Route: `/workspace/:projectId/review`

Tabs:
- Findings
- Inspect Run Links

Findings usage:
1. Review checker findings.
2. Resolve high-priority issues first.
3. Feed decisions back into planning/writing.

Inspect link usage:
1. Create links from objects to run ids.
2. Maintain traceability from finding to runtime evidence.

## Phase 7: Inspect Workspace
Routes:
- `/workspace/:projectId/inspect`
- `/workspace/:projectId/inspect/:jobId`

Deep-link behavior:
- Job id is resolved against checker and jobs services.
- Context initializes run kind automatically.

Tabs:
- Steps: execution timeline
- Lineage: artifact ancestry and transitions
- Attempts: run attempts and retry controls

Retry flow:
1. Open Attempts tab.
2. Trigger `Retry Job` for pipeline runs.
3. Re-check attempts list and status transitions.

## Phase 8: Canon Workshop
Route: `/workspace/:projectId/canon`
Deep-link tab query:
- `?tab=overview`
- `?tab=mythos`
- `?tab=patterns`
- `?tab=packet`

Primary use:
- Tune canon interpretation and packet composition before generation.
- Manage annotations and customization profiles.
- Materialize and curate mythos/pattern libraries.
- Validate packet scope for generation quality and guardrails.

Auth note:
- If API auth is required, this screen provides explicit setup guidance.

## Phase 9: Story Generation Workspace
Route: `/workspace/:projectId/generate`

Main elements:
- Story Generation Wizard
- Generation run cards
- Gate panel
- Generated story review

Workflow:
1. Configure and submit run in wizard.
2. Monitor run list and statuses.
3. Select run to inspect latest status and packet entity count.
4. Use retry where needed.
5. Use `Fork Project from Run` for branch-to-project expansion.
6. Review gate output and generated story summary.

## Phase 10: Full Production Workflow
Use this order for complete project execution.

1. Create/import project.
2. Build foundation, characters, world bible.
3. Build relationships (graph + list) and arcs.
4. Structure narrative in planning tabs.
5. Capture side ideas in brain dump/brainstorm.
6. Draft and revise in writing workspace.
7. Run checker and resolve findings.
8. Inspect problematic runs.
9. Harden canon in canon workshop.
10. Execute generation runs.
11. Fork successful runs into new projects where needed.
12. Export final project snapshots.

## Phase 11: Advanced Iteration Patterns
### Pattern A: Canon-tight revision loop
1. Write draft.
2. Checker review.
3. Inspect root causes.
4. Annotate canon fields.
5. Re-run generation.

### Pattern B: Alternate story exploration
1. Create branch.
2. Draft alternate variants.
3. Compare and decide.
4. Merge preferred direction.

### Pattern C: Forked sequel workflow
1. Select successful generation run.
2. Fork to new project.
3. Re-open planning and writing in fork.
4. Repeat quality loop.

## Interface Reference By Surface
### Project List
- Search bar with keyboard focus shortcut (`Ctrl/Cmd+K`).
- Project cards include metadata, export, delete.
- Creation and import actions.

### Guided Setup
- LLM status badge.
- Chat history + progressive extraction.
- Field preview completeness.
- Dual save states.

### Planning
- 12 tabs.
- Mixed strategic and entity-level planning.
- Direct route to generation.

### Brain Dump
- Session-based free writing.
- Organize summary cards.

### Writing
- Manuscript selection.
- Draft lifecycle controls.
- Assist integration.
- Suggestions control center.

### Review
- Findings triage.
- Inspect-link authoring.

### Inspect
- Steps, lineage, attempts.
- Retry entry point.

### Canon
- Overview + mythos + patterns + packet.

### Generate
- Run setup, status tracking, gates, fork.

## Common Failure Cases and Fixes
- Missing project context: verify `:projectId` route and selected project.
- Auth-gated features blocked: configure API key path and server variable.
- Generation/checker failures: validate inference backend and model readiness.
- Empty inspect context: use a valid run/job id or navigate from review/job workflows.
- No writing outputs: ensure upstream planning and draft generation steps completed.
- **Truncated LLM output** (`INFERENCE_TRUNCATED`): The LLM hit its token budget mid-response. The Job Launch panel displays an expandable error with fix guidance. Resolution: add `NARRATIVE_MAX_TOKENS_DEFAULT=8192` (or higher) to your `.env`, or set per-phase overrides such as `NARRATIVE_MAX_TOKENS_DRAFTER=8000`. Restart the server after changes.
- **Cannot reach LLM server** (`INFERENCE_TRANSPORT_FAILURE`): Verify llama.cpp is running and `NARRATIVE_INFERENCE_BASE_URL` in `.env` is correct. Default: `http://127.0.0.1:8080`.
- **LLM circuit breaker open**: The backend has failed repeatedly. Fix the underlying connectivity or configuration issue, then wait for the circuit to reset or restart the server.

## Completion Checklist
A project is operationally complete when:
- Foundation, characters, world bible, and relationships are populated.
- At least one manuscript exists and has been revised.
- Checker findings have been reviewed.
- At least one inspectable run is present.
- Canon profile/packet has been reviewed.
- At least one generation run completed (and optionally forked).
- Export archive captured.
