# Narrative Engine - User Guide v1.8.0

Last updated: 2026-05-17 (end-to-end walkthrough added)

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
- `/workspace/:projectId/studio` - Studio Desk (compact single-screen workspace)

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

### Job Launch Panel
- Select pipeline phase (P-100 Architect, P-200 Sequencer, P-300 Drafter, P-400 Compiler).
- Launch button submits a new job; disabled while another job is running.
- Recent Jobs list shows up to 4 most recent jobs for the project.
- Failed jobs show expandable error details with actionable fix guidance for inference errors (truncated responses, timeouts, transport failures, circuit breaker, invalid JSON/response shape, configuration errors).
- Completed jobs show processing time and step name.
- Processing jobs show current step, elapsed time, and progress counter.

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
- Relationships: interactive graph + list views with create, edit, and delete actions. Double-click a character node to open its profile editor. Double-click a relationship edge or click the edit button to modify an existing relationship via centered modal dialog.

### Relationship Map Interactions
The Relationships tab provides an interactive graph visualization with full CRUD operations:

**Creating relationships:** Click "Add Relationship" to open the creation form. Select From/To characters, relationship type (19 predefined kinds), summary, optional tension and notes fields.

**Editing relationships:** Three ways to edit an existing relationship:
- Double-click a relationship edge in the graph — opens a centered modal dialog pre-populated with current data.
- Click the pencil icon on a relationship card in the list view below the graph.
- Edit button appears on graph edges when hovering (blue pencil icon next to red delete X).

The edit modal supports: changing relationship type, summary, tension, and notes. From/To characters are displayed as read-only. Save sends a PATCH request; Delete removes the relationship with confirmation.

**Opening character profiles:** Double-click any character node in the graph to jump to the Characters tab with that character's profile editor open. This reuses the existing CharacterBuilder form — no separate character detail view is needed.

**AI Relationship Extraction:** The "AI Extract" button analyzes your manuscript text via LLM and auto-creates relationship edges between characters based on detected interactions, shared themes, and narrative connections. Requires at least 2 characters and generated chapter content.

### Cascade Discovery — AI-Powered Entity Extraction
The "Scan Manuscript" button (visible in the Relationships toolbar) runs a full cascade analysis of your manuscript text via LLM, discovering characters, relationships, and world bible entries in a single pass.

**How it works:**
1. Click "Scan Manuscript" to open the scan dialog.
2. Paste your manuscript or chapter text (minimum 50 characters).
3. Configure chunk size (default: 8000 words, adjustable for high-context models).
4. Click "Start Scan" — the engine processes the text asynchronously.
5. A loading overlay shows progress while the LLM extracts entities.
6. When complete, the review dialog opens with three tabs: Characters, Relationships, World Bible.

**Reviewing discovered entities:**
- Each entity shows a confidence badge (High / Medium / Low) based on mention frequency, description richness, interaction density, and LLM self-rating.
- Low-confidence entities are collapsed by default — expand to review.
- Source text excerpts are available per entity for context verification.
- Fuzzy-matched characters show an orange "Fuzzy match" indicator.

**Approving and committing:**
- Per-entity: click "Approve" or "Reject" on each row.
- Bulk actions: "Approve All" / "Reject All" per tab.
- Click "Apply X changes" to commit approved entities to the project database.
- On success, a summary shows counts of new characters added, existing characters enriched, relationships created, and world entries discovered.

**Undo:** Revert any applied batch by clicking "Undo" in the confirmation summary — all entities from that batch are removed from the database.

**Deduplication behavior:**
- Exact name matches (case-insensitive) are auto-detected; new details enrich existing profiles.
- Fuzzy matches (similar names, alias overlap) flag for user review before merge.
- World bible entries deduplicate by type + title combination.

Global action:
- `Generate Story` button routes to generation workspace.

## Brain Dump (`/workspace/:projectId/braindump`)
Session-based free writing canvas with AI-powered organization.

### Session Management
- Auto-selects the active session on load.
- `+ New Session` button opens an inline title input and writing canvas. Enter a session name and start typing.
- Sessions are project-scoped and persist across visits.

### Writing Canvas
- Full-height textarea for freeform writing.
- Auto-saves with 2-second debounce after typing stops; "editing..." indicator appears while unsaved changes exist.
- Word count display in bottom bar.
- "blank session" indicator when no text has been entered.
- Hover-reveal controls overlay at bottom of canvas.

### Organize Flow
- "Organize with AI" button appears when text exceeds 100 characters and a session is active.
- Submits text to LLM for categorization into structured items.
- Result display shows:
  - Total item count.
  - Category breakdown (e.g., "3 plot_points, 5 character_ideas").
  - Category cards in grid layout with line-clamped item excerpts.
- "Continue editing" button returns to canvas for additional passes.

### Auth Behavior
- If API key auth is enforced and missing, view shows an API key guidance banner.

## Writing Workspace (`/workspace/:projectId/write`)
Three-column layout: Manuscripts/Drafts (left), Editor (center), Aids panel (right).

**Route-aware layout:** When on `/workspace/:projectId/write/:chapterId`, the layout collapses to a single column showing only the Editor. The left sidebar and right aids panel are hidden for focused chapter editing.

### Manuscripts
- Select manuscript documents from the list.
- Enter edit mode, save/cancel edits.
- Word and character counts update in real-time.

### Drafts
Draft artifact lifecycle management in the left column:
- **Create manual draft** — form with title input and content textarea. Submits a new draft artifact for the selected manuscript.
- **Continue draft** — per-draft-card button that generates a continuation of the draft's content via LLM.
- **Alternate variant** — per-draft-card button that generates an alternate version of the same narrative beat.
- **Promote to manuscript** — per-draft-card button that promotes a finalized draft into a new manuscript document.
- **AI draft generation** — form with title input and brief textarea. Generates a complete draft from scratch using LLM, guided by the title and brief. Submit button triggers async job; result appears as a pending entry.
- **Pending state display** — in-flight AI draft jobs show an amber loading indicator with pulsing dots and title text. If the job fails, error message is displayed inline. Completed drafts appear in the list automatically.

### Editor
- Read/edit content toggle.
- Word and character counts display.

**Floating Selection Toolbar:** When you select text, a floating toolbar appears near the selection with categorized actions:
- **Sensory detail** (collapsible submenu, inspired by Sudowrite Describe):
  - `Sight & color` — add visual detail, lighting, color, spatial awareness
  - `Sound & rhythm` — add auditory detail, ambient noise, silence, cadence
  - `Smell & atmosphere` — add olfactory detail, scent memory, environmental mood
  - `Touch & texture` — add tactile detail, temperature, physical sensation
  - `Taste & flavor` — add gustatory detail, flavor memory, palate
  - `Metaphor & simile` — add figurative language and symbolic imagery
  - `Show don't tell` — convert abstract statements into concrete action and observation
- **Rewrite** actions:
  - `Tighten & polish` — remove redundancy, improve flow and clarity
  - `Compress` — reduce word count while preserving meaning
  - `Rewrite in different voice` — match a specified tone or style
  - `Alternate version` — generate a different take on the same idea
- **Continue** actions:
  - `Continue from here` — generate next passage in current voice
  - `Fork as draft` — create a new branch or alternate draft artifact

**Assist Dropdown:** Click the Assist button in the editor toolbar for the same action menu. Requires explicit click to open; does not auto-open on selection (floating toolbar handles that).

Each action sends a parameterized instruction to the Manuscript Assist backend (`POST /v1/manuscript-assist/runs`) with the selected text range, anchor context, and kind-specific LLM prompt. The result appears as suggestions in the Aids panel for review, accept, or reject.

### Aids panel
- Suggestions: actionable revision suggestions.
- Diff view and history behavior via aids components.
- Accept/reject/archive flows.

## Review Workspace (`/workspace/:projectId/review`)
Two-tab interface for reviewing checker findings and maintaining run traceability.

### Findings Tab
- Renders a list of checker findings for the project, sorted by priority.
- Each finding shows severity, description, and affected entity.
- Use findings to identify consistency issues, canon violations, or structural problems detected by the Role Model Checker.
- Resolve high-priority findings first, then feed corrections back into Planning or Writing tabs.

### Inspect Run Links Tab
Maintains mappings from review objects to inspectable runs for traceability.

**Creating an inspect link:** Click `+ New Link` to open an inline form with six fields:
- **Link ID** — unique identifier for this link
- **Object Kind** — type of the source object (e.g., `chapter-plan`, `draft-artifact`)
- **Object ID** — identifier of the source object
- **Logical Run ID** — human-readable run reference (e.g., `run-001`)
- **Run ID** — actual job or checker run ID to inspect
- **Run Kind** — `pipeline_job` or `checker_run`

All fields are required. Click "Create" to save the link; "Cancel" to discard. Links enable navigation from review objects directly to the Inspect workspace for runtime evidence.

## Inspect Workspace (`/workspace/:projectId/inspect`)
Runtime inspection interface for pipeline jobs and checker runs.

### Deep-Link Resolution
- `/workspace/:projectId/inspect` — shows empty state with guidance to navigate from Review or Job Launch panel.
- `/workspace/:projectId/inspect/:jobId` — auto-resolves the job ID against both checker and jobs services. Displays a loading state during resolution. If the ID is not found in either service, shows an error message with the run ID.
- Header displays Run ID and Run Kind. "Back to Manuscript" button navigates to Writing workspace.

### Steps Tab
- Execution timeline view showing each pipeline step in chronological order.
- Each step displays: step name, status (PENDING, PROCESSING, COMPLETED, FAILED), start time, duration, and output summary.
- Use this tab to trace where a job succeeded or failed during execution.

### Lineage Tab
- Artifact ancestry view showing how output artifacts relate to input artifacts across pipeline phases.
- Displays artifact transitions: which draft produced which manuscript, which plan generated which sequence.
- Use this tab to trace the provenance of any generated content back to its source inputs.

### Attempts Tab
- Attempt history list for the selected run.
- Each attempt shows: attempt number, status (color-coded: green = COMPLETED, red = FAILED, yellow = other), started_at timestamp, finished_at timestamp, finish_reason, and error_code (if failed).
- "Retry Job" button available for pipeline jobs — submits a new execution attempt with the same configuration.
- Use this tab to diagnose repeated failures or compare outputs across attempts.

## Canon Workshop (`/workspace/:projectId/canon`)
Four-tab workspace for managing canon scope, profiles, mythos/pattern libraries, and generation packets. Deep-link tabs via `?tab=mythos|patterns|packet`.

### Overview Tab
Central control surface for canon profiles and generation configuration:
- **Profile Name** input field — name a new canon profile.
- **Active Profile** dropdown — select an existing profile to edit or use.
- **Generation Brief** textarea — freeform instructions for generation context.
- **Selection panels** (checkbox lists): Characters, World Entries, Mythos, Patterns — choose which entities to include in the canon packet.
- **Canon Scope Summary** — displays counts of selected entities per category.
- **Generation Rules Editor** — policy editor for continuity strictness and constraints.
- **Actions**: "Save Profile" (persist current selection), "Preview Packet" (disabled unless profile selected), "Generate with Selected" (direct generation submission shortcut).
- **Profile management**: "Rename Selected Profile", "Delete Selected Profile" buttons for lifecycle management.

### Mythos Tab
Mythos library management:
- **Materialize** — text input + "Materialize" button to convert an extraction ID into editable mythos entries.
- **Mythos Library Workspace** — grid of MythosEntryCards with type filter dropdown. Each entry shows a "Use in Generation" checkbox and Delete action.
- Entries are project-scoped and persist across sessions.

### Patterns Tab
Pattern library management:
- **Materialize** — text input + "Materialize" button to convert an extraction ID into editable pattern entries.
- **Pattern Library Workspace** — grid of PatternEntryCards with "Use in Generation" checkbox, generation modes display, and Delete action.
- Entries capture archetypal patterns, narrative structures, and voice profiles extracted from source text.

### Packet Preview Tab
Deterministic canon packet preview:
- Displays the packet structure when a profile is selected and previewed.
- Shows entity counts for Characters, World Bible, Mythos, and Patterns.
- Use this tab to validate packet scope size and composition before submitting a generation run.

### Auth Behavior
- If API key auth is enforced and missing, view shows an API key guidance banner with setup instructions.

## Story Generation (`/workspace/:projectId/generate`)
Full generation lifecycle: wizard configuration, run monitoring, gate review, and project forking.

### Story Generation Wizard
Multi-step form for configuring a generation run:

**Mode Selector** — 8 generation modes displayed as a grid of buttons:
- `New Arc` — generate a new story arc from existing canon
- `Sequel` — continue the narrative forward
- `Prequel` — generate backstory events
- `Side Story` — parallel narrative branch
- `Alternate Route` — different path from current point
- `Character Fork` — follow a different character's perspective
- `World Fork` — explore an alternate world state
- `Hybrid Fork` — combine multiple forking strategies

**Destination Selector** — toggle between:
- `Same Project` — generate into the current project (requires target project ID)
- `New Project` — creates a new project; input field appears for `target_project_name`

**Canon Scope Selector** — choose which canon entities to include:
- Characters section — toggle buttons per character
- World Bible section — toggle buttons per entry
- Supports `full_project` mode (include everything) or individual selection
- Hidden scope fields available for advanced use: continuity threads, arcs, mythos IDs, pattern IDs, relationships, unresolved questions, contradictions as forbidden

**Canon Policy Editor** — controls generation constraints:
- Continuity Strictness dropdown with 4 levels: `Warn`, `Block`, `Repair Once`, `Repair Twice`
- Locked fields, allowed changes, and forbidden contradictions arrays (pre-populated defaults)

**Generation Brief** — textarea (min-height 120px) for freeform creative instructions. Required to enable submission.

**Chapter Count** — number input (1-100, default 3). Controls how many chapters the drafter generates in batch mode.

**Actions**: "Preview Fork" button shows entity counts before submission; "Start Generation" submits the run. Both disabled until brief is non-empty AND scope has at least one entity or full_project mode is active.

### Run Management
- Run cards displayed in a 2-column grid. Each card shows: generation_id, status, job count, warning count.
- Click a run card to select it — reveals detail panel with latest status, packet entity count, and "Fork Project from Run" button.
- Failed runs show a "Retry" button (with loading state indicator).

### Gate Results Panel
- Shows gate results for the selected run.
- Each gate displays: gate name, pass/fail status (color-coded), severity, and reasons list.
- Use gates to verify canon consistency and identify contradictions before accepting generated content.

### Generated Story Review
- Displays the run ID and manuscript artifact ID (if available).
- Shows the assembled output from successful generation runs.
- "Fork Project from Run" creates a new project with the generated content, remapping canon IDs and recording provenance.

### Fork Preview Panel
- "Preview Fork" button in wizard shows counts of selected characters, world entries, arcs, and continuity threads before submitting.
- Helps validate scope size and composition before committing to generation.

## Studio Desk (`/workspace/:projectId/studio`)
Compact, single-screen workspace for focused writing with immediate access to all planning, generation, and review surfaces. Designed for users who want a unified desk rather than navigating between separate workspace modes.

**Layout:** Three-column grid (desktop) or overlay drawers (below `xl:` breakpoint).
- **Left rail (Project Map):** Quick navigation between Ideas, Characters, World Bible, Relationships, Canon, Jobs, and Notes panels.
- **Center (Main Content):** Full writing editor with manuscript navigation, draft management, and revision suggestions.
- **Right rail (Context Panel):** Switchable panel based on active command: Suggestions, Generation, Review, or Inspect.

**Command Bar (top):** Five command buttons toggle the right context panel.
- `Capture` — switches to Ideas panel (brainstorm-style ideation)
- `Write` — switches to Suggestions panel (revision suggestions, diff viewer, history)
- `Generate` — switches to Generation panel (compact story generation wizard)
- `Review` — switches to Review panel (checker findings and inspect links)
- `Inspect` — switches to Inspect panel (job inspection and lineage)

**Responsive Behavior:** Below `xl:` breakpoint, the left rail and right context panel become overlay drawers. Toggle buttons appear in the header. A close-drawer button dismisses both drawers simultaneously.

**Project Rail Panels:**
- **Ideas:** Brainstorm-style idea capture and clustering
- **Characters:** Character CRUD with profile editing and canon annotations
- **World Bible:** World entry CRUD with canon annotations
- **Relationships:** Relationship graph and list views with CRUD operations
- **Canon:** Canon profile management and packet preview
- **Jobs:** Job launch panel with phase selection and recent job monitoring
- **Notes:** Project-level notes with add/delete functionality

**Context Panel Panels:**
- **Suggestions:** Merged revision suggestions from Manuscript Assist and LLM sources. Accept/reject/archive flows with diff viewer.
- **Generation:** Compact story generation wizard with mode selector, destination, canon scope, and policy configuration.
- **Review:** Tab-based interface for checker findings and inspect links.
- **Inspect:** Job inspection with guidance text when no run is selected.

## End-to-End Walkthrough
For a complete, step-by-step walkthrough of generating a novel from project creation through export, see **Phase 11: End-to-End Novel Walkthrough** in the [Narrative Engine User Walkthrough v1.8.0](Narrative%20Engine%20User%20Walkthrough%20v1.8.0.md). It walks through creating a 12-chapter novel (*The Last Lighthouse*) with 7 characters, 8 world bible entries, 3 character arcs, 3 sequences, branching for Act III exploration, and a full generation/revision/checker/export workflow.

## End-to-End Recommended Workflow
1. Create project (`/`) or use Guided Setup (`/setup-wizard`).
2. Build canon in Planning tabs: Foundation, Characters, World Bible, Relationships, Arcs.
3. (Optional) Run Cascade Discovery to auto-extract characters, relationships, and world entities from existing manuscript text — review and approve discovered entities before committing.
4. Shape structure in Planning/Flow tabs.
5. Capture optional ideation in Brain Dump and Brainstorm.
6. Draft in Writing (manual, AI, continue, alternate, promote) or use Studio Desk for a compact single-screen workspace.
7. Use Manuscript Assist for targeted edits: floating toolbar for sensory detail, rewrite, and continue actions; Aids panel for suggestion review.
8. Run Checker and review findings in Review workspace. Create inspect links for traceability.
9. Inspect problematic runs from deep links or Inspect mode to diagnose failures.
10. Use Canon Workshop to tighten packet scope, manage profiles, and validate generation context.
11. Launch Story Generation runs: configure wizard, monitor status, review gates, fork successful runs.
12. Iterate via branches, decisions, and additional drafts.
13. Export project archive for backup and transfer.

## API/Auth Notes For Users
- If backend sets `NARRATIVE_API_KEY`, protected features require matching API key usage.
- Health/auth errors are shown in-view for Brain Dump and Canon.
- Generation and assist depend on configured inference backend.

## Troubleshooting Quick Map
- Cannot access canon/brain dump: verify API key setup.
- Generation run stuck/failing: check inference backend health and model config.
- Missing inspect data on deep link: verify job id exists in checker or jobs services.
- No drafts/manuscripts visible: confirm selected project and completed upstream planning or generation steps.
- Job fails with "Response truncated" (`INFERENCE_TRUNCATED`): the LLM ran out of token budget mid-response. Fix by adding `NARRATIVE_MAX_TOKENS_DEFAULT=8192` to your `.env` file, or set per-phase overrides (e.g., `NARRATIVE_MAX_TOKENS_DRAFTER=8000`, `NARRATIVE_MAX_TOKENS_ARCHITECT=4096`). Restart the server after changing `.env`. The Job Launch panel shows expandable error details with fix guidance for all inference errors.
- Job fails with "Cannot reach LLM server" (`INFERENCE_TRANSPORT_FAILURE`): verify llama.cpp (or your configured backend) is running and that `NARRATIVE_INFERENCE_BASE_URL` in `.env` matches the server address.
- Job fails with "LLM circuit breaker open": the backend has been failing repeatedly. Fix the underlying issue and wait for the circuit to reset, or restart the server.
- Cascade scan returns no entities: ensure manuscript text is at least 50 characters and contains character names, interactions, or descriptive details. Very short or sparse text may yield no discoverable entities.

## Glossary
- Assist action: a Manuscript Assist operation triggered by text selection (sensory detail, rewrite, continue).
- Floating toolbar: MS Word-style ribbon that appears near selected text with categorized assist actions.
- Canon packet: selected canon payload passed to generation phases.
- Cascade Discovery: LLM-powered extraction of characters, relationships, and world bible entries from manuscript text, with staged approval workflow.
- Draft artifact: intermediate draft output before manuscript promotion.
- Inspect link: mapping from review object to inspectable run.
- Manuscript Assist: LLM-powered targeted editing system that processes selection context and returns revision suggestions.
- Manuscript document: editable narrative document in writing workspace.
- Run: one execution instance of checker or generation pipeline.
- Sensory detail: expand actions that add sensory-specific description (sight, sound, smell, touch, taste, metaphor, show-don't-tell).
