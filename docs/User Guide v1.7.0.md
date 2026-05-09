# Narrative Engine - User Guide v1.8.0

Last updated: 2026-05-09

## Purpose
This guide explains the current frontend interface, what each workspace mode does, and how to complete production workflows from project creation through generation, review, and iteration.

## Core Routes
- `/` - Project List, New Project, Story Import, Project Import
- `/setup-wizard` - Guided Setup (conversational project creation)
- `/workspace/:projectId/plan` - Planning workspace
- `/workspace/:projectId/write` - Writing workspace
- `/workspace/:projectId/write/:chapterId` - Writing workspace with chapter route context
- `/workspace/:projectId/review` - Review workspace
- `/workspace/:projectId/inspect` - Inspect workspace
- `/workspace/:projectId/inspect/:jobId` - Inspect workspace deep link
- `/workspace/:projectId/braindump` - Brain Dump workspace
- `/workspace/:projectId/canon` - Canon Workshop
- `/workspace/:projectId/generate` - Story Generation workspace

## Home Interface (`/`)
### Project list
- Search projects with instant filtering across name, genre, tone, structure, and premise.
- Open a project by clicking its card.
- Export a project (ZIP).
- Delete a project (with confirmation).
- Import a project (ZIP archive restore).

### New Project form
Required:
- Project Name
- Genre
- Tone Profile
- Story Structure
- Point of View
- Primary Language

Optional:
- Secondary Language
- Premise

Actions:
- `Create Project`
- `Walk Me Through It` (opens Guided Setup)
- `Import Existing Story` (opens import and pattern extraction modal)

## Guided Setup (`/setup-wizard`)
Layout:
- Left: chat-driven intake.
- Right: extracted field preview and completeness state.

Capabilities:
- Conversational extraction of config, foundation, characters, world bible, arcs, sequences, chapters.
- Save before full completion (`Save What You Have`) or after readiness (`Save Project`).
- Health indicator for LLM backend.

## Workspace Shell Behavior
The workspace shell includes:
- Main content area (current mode view).
- Right rail cards: Notes panel and Job Launch panel.
- Bottom utility layer for operational status.

Mode navigation is stage-aware and may hide some modes depending on current stage:
- Planning stage: Brain Dump, Planning, Canon, Generate
- Writing stage: Writing
- Review stage: Review, Inspect

## Planning Workspace (`/workspace/:projectId/plan`)
Top-level planning tabs:
- Manifest
- Planning
- Flow
- Arcs
- Branches
- Decisions
- Checker
- Brainstorm
- Foundation
- Characters
- World Bible
- Relationships

### What each tab is for
- Manifest: project metadata and baseline config.
- Planning: sequence, chapter, scene, beat planning surfaces.
- Flow: custom story development stage flow management.
- Arcs: arc candidates, selections, stage maps.
- Branches: branch lifecycle and comparisons.
- Decisions: decision tree and decision history.
- Checker: role model checker execution and outputs.
- Brainstorm: idea capture, clustering, promotion to downstream entities.
- Foundation: premise, logline, thematic spine, constraints, review cues.
- Characters: character CRUD, profile editing, canon annotations.
- World Bible: world entry CRUD, updates, canon annotations.
- Relationships: graph + list views with delete actions.

Global action:
- `Generate Story` button routes to generation workspace.

## Brain Dump (`/workspace/:projectId/braindump`)
- Auto-selects active session.
- Auto-creates a session when none exists.
- Save freeform text continuously.
- Organize session into categorized items.
- Shows organized result summary and category cards.

## Writing Workspace (`/workspace/:projectId/write`)
Three-column layout:
- Left: Manuscripts and Drafts
- Center: Manuscript Editor
- Right: Aids panel

### Manuscripts
- Select manuscript documents.
- Enter edit mode, save/cancel edits.

### Drafts
- Create manual drafts.
- Continue draft.
- Create alternate variant.
- Promote draft to manuscript.
- AI draft generation from title + brief.
- Pending state display for in-flight AI draft jobs.

### Editor
- Read/edit content.
- Word and character counts.
- Text selection assist actions through Manuscript Assist:
- `line_edit`
- `expand`
- `compress`
- `rewrite`
- `fork_from_selection`

### Aids panel
- Suggestions: actionable revision suggestions.
- Diff view and history behavior via aids components.
- Accept/reject/archive flows.

## Review Workspace (`/workspace/:projectId/review`)
Tabs:
- Findings
- Inspect Run Links

Capabilities:
- Findings list review and triage workflows.
- Create inspect links manually (`+ New Link`) for object/run traceability.

## Inspect Workspace (`/workspace/:projectId/inspect`)
- Supports route-driven deep link resolution by job id.
- Auto-detects whether id belongs to pipeline job or checker run.

Tabs:
- Steps
- Lineage
- Attempts

Attempt features:
- Attempt history list.
- Pipeline run retry from attempts tab.

## Canon Workshop (`/workspace/:projectId/canon`)
Tabs (including deep link via `?tab=`):
- `overview`
- `mythos`
- `patterns`
- `packet`

Features:
- Canon annotation and profile operations.
- Mythos and pattern library management.
- Packet preview and generation-context control.

Auth behavior:
- If API key auth is enforced and missing, view shows an API key guidance banner.

## Story Generation (`/workspace/:projectId/generate`)
Components:
- Story Generation Wizard
- Run list cards
- Gate panel
- Generated story review

Capabilities:
- Configure generation run and submit.
- View run history and status.
- Retry failed/blocked runs.
- Preview fork.
- Fork project from selected run.
- Review gates and packet scope size.

## End-to-End Recommended Workflow
1. Create project (`/`) or use Guided Setup (`/setup-wizard`).
2. Build canon in Planning tabs: Foundation, Characters, World Bible, Relationships, Arcs.
3. Shape structure in Planning/Flow tabs.
4. Capture optional ideation in Brain Dump and Brainstorm.
5. Draft in Writing (manual, AI, continue, alternate, promote).
6. Use Manuscript Assist for targeted edits.
7. Run Checker and review findings.
8. Inspect problematic runs from deep links or Inspect mode.
9. Use Canon Workshop to tighten packet and canon behavior.
10. Launch Story Generation runs and fork when needed.
11. Iterate via branches, decisions, and additional drafts.
12. Export project archive for backup and transfer.

## API/Auth Notes For Users
- If backend sets `NARRATIVE_API_KEY`, protected features require matching API key usage.
- Health/auth errors are shown in-view for Brain Dump and Canon.
- Generation and assist depend on configured inference backend.

## Troubleshooting Quick Map
- Cannot access canon/brain dump: verify API key setup.
- Generation run stuck/failing: check inference backend health and model config.
- Missing inspect data on deep link: verify job id exists in checker or jobs services.
- No drafts/manuscripts visible: confirm selected project and completed upstream planning or generation steps.

## Glossary
- Canon packet: selected canon payload passed to generation phases.
- Run: one execution instance of checker or generation pipeline.
- Draft artifact: intermediate draft output before manuscript promotion.
- Manuscript document: editable narrative document in writing workspace.
- Inspect link: mapping from review object to inspectable run.
