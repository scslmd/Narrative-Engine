# Narrative Engine - Complete User Walkthrough v1.9.0

Last updated: 2026-05-19 (form entry optimization: required/optional field fix, progressive disclosure, Arcs panel, canon context badges)

## Goal
This walkthrough is the full frontend operating manual. It explains every workspace interface and gives a comprehensive, practical workflow from first launch to advanced generation and iteration.

## Preconditions
- Backend is running.
- Frontend is running.
- Inference backend is configured for LLM-dependent features.
- If `NARRATIVE_API_KEY` is enabled on the server, configure API key usage for protected flows.

## Quick Start: Your First Project in 10 Minutes

1. Open `/` → fill New Project form (name, genre, tone, structure, POV, language) → click **Create Project**
2. Navigate to **Foundation** tab → fill Premise and Logline → click **Save Foundation**
3. Navigate to **Characters** tab → click **Add Character** → create one protagonist → click **Save Character**
4. Navigate to **Studio Desk** → click **Jobs** in left rail → select **P-100 Architect** → click **Launch** → wait for completion
5. Select **P-300 Drafter** → click **Launch** → wait for completion → view generated chapter in Studio Desk manuscript editor

For a complete walkthrough with 12 chapters, 7 characters, and branching, see Phase 11.

## Frontend Map
- `/` Project list and creation
- `/setup-wizard` Conversational setup
- `/workspace/:projectId/plan` Planning
- `/workspace/:projectId/braindump` Brain dump
- `/workspace/:projectId/write` → redirects to `/studio` (deprecated)
- `/workspace/:projectId/review` Review
- `/workspace/:projectId/inspect` Inspect
- `/workspace/:projectId/canon` Canon
- `/workspace/:projectId/generate` Generate
- `/workspace/:projectId/studio` Studio Desk (primary writing workspace)

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

The workspace has the following structure:
- **Left panel (Workspace sections):** 160px navigation rail with stage-specific items and a "Studio Desk" quick link. Hidden in Studio mode (StudioView has its own left rail).
- **Main content area:** Current mode view.
- **Bottom utility layer:** Runtime/status bar for job progress.

**Note:** In Studio mode, the WorkspaceShell left panel is hidden. StudioView uses its own left rail (Project Map) and right context panel via the ViewShell component.

### Left Panel Navigation
The left panel displays stage-aware navigation items plus a permanent "Studio Desk" link. The active item is highlighted with a gradient icon background and a dot indicator.
- **Planning stage:** Brain Dump, Planning, Canon, Generate
- **Writing stage:** Studio (redirects to Studio Desk)
- **Review stage:** Review, Inspect
- **Studio Desk link:** Appears below stage-specific items, separated by a divider. Always accessible from any workspace view.

### Job Launch Panel
The Job Launch panel lets you trigger pipeline phases without leaving the current workspace view. Select a phase (P-100 through P-400), click to launch, and monitor recent jobs below. Failed jobs show expandable error details with fix guidance. Completed jobs display processing time. Running jobs show step progress.

**Access:** In Studio mode, access job launch via the Jobs button in StudioView's left rail. In other workspace modes, the Job Launch panel is embedded within the view.

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
- ArcBuilder provides progressive disclosure: Core (Arc ID, Name, Summary — required), Structure (stage map notes — recommended), Metadata (fit notes, tags — optional).
- Visual indicators: `*` for required, `⚡` for fields used by story generation.

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
- List, create, and edit character profiles with progressive disclosure.
- Required fields (marked `*`): Character ID, Display Name, Role in Story.
- Recommended fields (marked `⚡`): Archetype, External Goal, Internal Need, Change Axis — used by story generation.
- Optional fields in collapsible sections: Psychological Depth, Context, Tracking.
- Annotate character fields for canon behavior.

### World Bible
- Create and edit world entries with grouped fields: Core (title, summary, type), Canon (canonical facts, continuity warnings), Notes.
- Fields marked `📖` are consumed by story generation (summary, canonical facts, continuity warnings).
- Annotate fields and maintain canonical details.

### Relationships
The Relationships tab provides an interactive graph visualization with full relationship management:

**Create:** Click "Add Relationship" to open the creation form. Select From/To characters (required, marked `*`), relationship type (required, marked `*`), summary (required, marked `*`), optional tension and notes.

**Edit:** Three interaction paths to modify an existing relationship:
- Double-click a relationship edge in the graph — opens a centered modal pre-populated with current data. Save sends PATCH, Delete removes with confirmation.
- Click the pencil icon on any relationship card in the list view below the graph.
- Hover over an edge in the graph to reveal edit (blue pencil) and delete (red X) buttons at the edge midpoint.

**Open character profiles:** Double-click a character node to jump to the Characters tab with that character's profile editor open.

**AI Extract:** Click "AI Extract" to analyze your manuscript text via LLM and auto-create relationship edges between characters based on detected interactions and narrative connections. Requires at least 2 characters and generated chapter content.

**Cascade Discovery (Scan Manuscript):**
1. Click "Scan Manuscript" in the Relationships toolbar to open the scan dialog.
2. Paste your manuscript or chapter text into the text area (minimum 50 characters).
3. Adjust chunk size if needed (default: 8000 words; increase for high-context models).
4. Click "Start Scan" — the engine submits an async job for LLM processing.
5. A loading overlay shows progress during extraction.
6. When complete, the review dialog opens with three tabs: Characters, Relationships, World Bible.
7. Review each entity: check confidence badges (High/Medium/Low), source excerpts, and fuzzy-match indicators.
8. Approve or reject entities individually, or use "Approve All" / "Reject All" per tab.
9. Click "Apply X changes" to commit approved entities to the project database.
10. Review the summary: new characters added, existing profiles enriched, relationships created, world entries discovered.
11. Click "Undo" in the summary to revert any batch if needed.

### Planning workspace action
- `Generate Story` sends you directly to generation mode.

## Phase 4: Brain Dump Workflow
Route: `/workspace/:projectId/braindump`

Session-based free writing canvas with AI-powered organization. Use this mode early for ideation spikes and mid-project for problem solving.

### Session Setup
1. Open brain dump mode. The view auto-selects the active session.
2. To create a new session, click `+ New Session`. An inline title input and writing canvas appear. Enter a session name and start typing.
3. Sessions are project-scoped and persist across visits.

### Writing
1. Write freely in the full-height canvas textarea.
2. Text auto-saves with a 2-second debounce after typing stops. An "editing..." indicator appears while unsaved changes exist, then clears when saved.
3. Word count updates in real-time in the bottom bar. A "blank session" indicator appears when no text has been entered.
4. Hover-reveal controls appear at the bottom of the canvas for quick access to actions.

### Organize with AI
1. Write at least 100 characters — the "Organize with AI" button appears once this threshold is met and a session is active.
2. Click "Organize with AI" to submit your text to the LLM for categorization.
3. The organized result display shows:
   - Total item count.
   - Category breakdown (e.g., "3 plot_points, 5 character_ideas").
   - Category cards in a grid layout, each showing line-clamped excerpts of categorized items.
4. Click "Continue editing" to return to the canvas for additional passes, or review the organized items for promotion into downstream planning entities.

### Auth Behavior
- If API key auth is enforced and missing, an API key guidance banner appears at the top of the view.

## Phase 5: Writing Workspace Deep Tour
Routes: `/workspace/:projectId/write` and `/workspace/:projectId/write/:chapterId` (both redirect to `/studio`)

The Writing workspace routes now redirect to Studio Desk. The WritingView component is embedded within StudioView, providing all writing functionality in a unified workspace.

**Accessing writing features:** Navigate to Studio Desk from the left panel's "Studio Desk" link, or use the top banner's stage selector (Planning / Studio / Review).

**Studio Desk provides the same writing capabilities in a 2-column layout:**
- Left rail: Project Map with Drafts, Manuscripts, Ideas, Suggestions, Review, Characters, World Bible, Relationships, Arcs, Canon, Notes, Jobs
- Center: Full-width manuscript editor with manuscript navigation, draft management, and revision suggestions

**To access writing features:** Navigate to Studio Desk from the left panel's "Studio Desk" link, or use the top banner's stage selector (Planning / Studio / Review).

### Manuscript Editor (Center)
1. Toggle between read mode (formatted markdown rendering) and edit mode (textarea).
2. Word count and character count display update in real-time.
3. Select text by clicking and dragging to access assist actions via the floating toolbar or Assist dropdown.

### Assist action flow (Floating Toolbar)
When you select text in the manuscript editor, a floating toolbar appears near the selection with categorized actions:

**Sensory detail** (collapsible submenu — inspired by Sudowrite Describe):
- `Sight & color` — add visual detail, lighting, color, spatial awareness
- `Sound & rhythm` — add auditory detail, ambient noise, silence, cadence
- `Smell & atmosphere` — add olfactory detail, scent memory, environmental mood
- `Touch & texture` — add tactile detail, temperature, physical sensation
- `Taste & flavor` — add gustatory detail, flavor memory, palate
- `Metaphor & simile` — add figurative language and symbolic imagery
- `Show don't tell` — convert abstract statements into concrete action and observation

**Rewrite actions:**
- `Tighten & polish` — remove redundancy, improve flow and clarity
- `Compress` — reduce word count while preserving meaning
- `Rewrite in different voice` — match a specified tone or style
- `Alternate version` — generate a different take on the same idea

**Continue actions:**
- `Continue from here` — generate next passage in current voice
- `Fork as draft` — create a new branch or alternate draft artifact

**Assist Dropdown (fallback):** Click the Assist button in the editor toolbar for the same action menu. Requires explicit click; does not auto-open on selection.

Each action sends a parameterized instruction to the Manuscript Assist backend with the selected text range, surrounding anchor context (~120 characters before/after), and kind-specific LLM prompt. The result appears as suggestions in the Suggestions panel for review, accept, or reject.

### Step-by-step assist workflow
1. Select text in the manuscript editor by clicking and dragging.
2. The floating toolbar appears near your selection.
3. Click an action (e.g., "Sight & color" under Sensory detail).
4. A toast confirms submission; the request processes via Manuscript Assist.
5. Review the suggestion output in the Suggestions panel (accessed via the left rail).
6. Accept to apply, reject to dismiss, or archive for later reference.

## Phase 6: Review Workspace
Route: `/workspace/:projectId/review`

Two-tab interface for reviewing checker findings and maintaining run traceability.

### Findings Tab — Triage Workflow
1. Open the Findings tab to see a list of checker findings for the project, sorted by priority.
2. Each finding displays severity level, description, and affected entity (character, world entry, arc, etc.).
3. Resolve high-priority findings first: navigate to Planning or Writing tabs to make corrections, then re-run the Checker to verify fixes.
4. Findings persist until the underlying issue is resolved by upstream corrections.

### Inspect Run Links Tab — Traceability Workflow
Maintain mappings from review objects to inspectable runs so you can trace any finding back to runtime evidence.

1. Click `+ New Link` to open an inline form with six fields:
   - **Link ID** — unique identifier for this link (e.g., `finding-ch1-arc`)
   - **Object Kind** — type of the source object (e.g., `chapter-plan`, `draft-artifact`, `manuscript-document`)
   - **Object ID** — identifier of the source object (e.g., `ch-001`)
   - **Logical Run ID** — human-readable run reference (e.g., `run-001`)
   - **Run ID** — actual job or checker run ID to inspect (e.g., `job-abc123`)
   - **Run Kind** — `pipeline_job` or `checker_run`
2. Fill all fields — each is required. Click "Create" to save the link.
3. Saved links appear in the list and enable navigation from review objects directly to the Inspect workspace (`/workspace/:projectId/inspect/:jobId`).
4. Use "Cancel" to discard a form without saving.

## Phase 7: Inspect Workspace
Routes:
- `/workspace/:projectId/inspect` — empty state with guidance to navigate from Review or Job Launch panel.
- `/workspace/:projectId/inspect/:jobId` — deep link that auto-resolves the job ID against both checker and jobs services.

### Deep-Link Resolution
1. Navigate to `/workspace/:projectId/inspect/:jobId` (or follow an inspect link from Review).
2. The view displays a loading state while resolving the run.
3. If the ID is found, the header shows Run ID and Run Kind. "Back to Manuscript" button navigates to Writing workspace.
4. If the ID is not found in either service, an error message displays with the run ID for verification.

### Steps Tab — Execution Timeline
1. Switch to the Steps tab to view the execution timeline.
2. Each step displays: step name, status (PENDING, PROCESSING, COMPLETED, FAILED), start time, duration, and output summary.
3. Use this tab to trace where a job succeeded or failed during execution. Failed steps highlight the point of failure for diagnosis.

### Lineage Tab — Artifact Ancestry
1. Switch to the Lineage tab to view artifact ancestry.
2. The view displays how output artifacts relate to input artifacts across pipeline phases: which draft produced which manuscript, which plan generated which sequence.
3. Use this tab to trace the provenance of any generated content back to its source inputs.

### Attempts Tab — History and Retry
1. Switch to the Attempts tab to view attempt history for the selected run.
2. Each attempt shows: attempt number, status (color-coded: green = COMPLETED, red = FAILED, yellow = other), started_at timestamp, finished_at timestamp, finish_reason, and error_code (if failed).
3. For pipeline jobs, click "Retry Job" to submit a new execution attempt with the same configuration.
4. The new attempt appears in the list with an incremented attempt number. Use this to diagnose repeated failures or compare outputs across attempts.

## Phase 8: Canon Workshop
Route: `/workspace/:projectId/canon`
Deep-link tab query: `?tab=overview|mythos|patterns|packet`

Four-tab workspace for managing canon scope, profiles, mythos/pattern libraries, and generation packets.

### Overview Tab — Profile Management and Scope Selection
1. Enter a **Profile Name** to create a new canon profile, or select an existing profile from the **Active Profile** dropdown.
2. Fill the **Generation Brief** textarea with creative instructions for generation context.
3. Use the four selection panels (checkbox lists) to choose entities:
   - **Characters** — toggle individual characters for inclusion in the canon packet.
   - **World Entries** — toggle world bible entries.
   - **Mythos** — toggle mythos library entries.
   - **Patterns** — toggle pattern library entries.
4. The **Canon Scope Summary** displays counts of selected entities per category.
5. Configure generation constraints in the **Generation Rules Editor** (continuity strictness, locked fields, allowed changes).
6. Click "Save Profile" to persist the current selection as a reusable profile.
7. Click "Preview Packet" to validate packet scope before generation (disabled unless a profile is selected).
8. Click "Generate with Selected" for a direct generation submission shortcut — bypasses the wizard and submits immediately.
9. Manage profiles with "Rename Selected Profile" or "Delete Selected Profile".

### Mythos Tab — Library Management
1. **Materialize extraction:** Paste an extraction ID into the text input and click "Materialize" to convert it into editable mythos entries. This creates project-scoped entries from LLM-extracted content.
2. Browse the Mythos Library Workspace — a grid of entry cards filtered by type (use the dropdown).
3. Each entry shows a "Use in Generation" checkbox (controls inclusion in canon packets) and a Delete action.
4. Entries persist across sessions and are available in the Overview tab's selection panel.

### Patterns Tab — Library Management
1. **Materialize extraction:** Paste an extraction ID into the text input and click "Materialize" to convert it into editable pattern entries.
2. Browse the Pattern Library Workspace — a grid of entry cards showing generation modes and a "Use in Generation" checkbox per entry.
3. Delete unwanted entries. Patterns capture archetypal structures, narrative patterns, and voice profiles extracted from source text.

### Packet Preview Tab — Scope Validation
1. Select a canon profile in the Overview tab, then switch to Packet Preview.
2. The view displays the packet structure with entity counts for Characters, World Bible, Mythos, and Patterns.
3. Use this tab to validate packet scope size and composition before submitting a generation run. Oversized packets may exceed LLM context limits; undersized packets may lack sufficient canon grounding.

### Auth Behavior
- If API key auth is enforced and missing, an API key guidance banner appears with setup instructions.

## Phase 9: Story Generation Workspace
Route: `/workspace/:projectId/generate`

Full generation lifecycle: wizard configuration, run monitoring, gate review, and project forking.

### Step-by-Step: Configure a Generation Run
1. Open the Story Generation Wizard. The form presents multiple configuration sections.

**Select a mode** — choose from 8 generation modes displayed as a grid of buttons:
- `New Arc` — generate a new story arc from existing canon
- `Sequel` — continue the narrative forward in time
- `Prequel` — generate backstory events before the current timeline
- `Side Story` — create a parallel narrative branch
- `Alternate Route` — explore a different path from the current point
- `Character Fork` — follow a different character's perspective
- `World Fork` — explore an alternate world state or setting change
- `Hybrid Fork` — combine multiple forking strategies

**Select destination** — toggle between:
- `Same Project` — generates into the current project (target project ID is auto-populated)
- `New Project` — creates a new project; an input field appears for `target_project_name`. Enter a name for the new project.

**Configure canon scope** — choose which canon entities to include in the generation context:
- Characters section: toggle buttons to select/deselect individual characters.
- World Bible section: toggle buttons to select/deselect world entries.
- You can select `full_project` mode to include everything, or pick specific entities for a focused packet.

**Set continuity policy** — use the Canon Policy Editor to control generation constraints:
- Continuity Strictness dropdown: `Warn` (non-blocking warnings), `Block` (stop on contradiction), `Repair Once` (auto-repair one pass), `Repair Twice` (two repair attempts).
- Locked fields, allowed changes, and forbidden contradictions arrays are pre-populated with sensible defaults. Adjust as needed for your project.

**Write a generation brief** — enter freeform creative instructions in the textarea. This guides the LLM's output direction. The brief is required to enable submission.

**Set chapter count** — number input (1-100, default 3). Controls how many chapters the drafter generates in batch mode. Higher counts produce longer narratives but consume more LLM tokens.

2. Click "Preview Fork" to see entity counts before submitting — validates scope size and composition.
3. Click "Start Generation" to submit the run. Both buttons are disabled until the brief is non-empty AND the scope has at least one entity or full_project mode is active.

### Monitor Runs
1. Run cards appear in a 2-column grid below the wizard. Each card shows: generation_id, status, job count, and warning count.
2. Click a run card to select it — a detail panel reveals latest status, packet entity count, and action buttons.
3. Failed runs display a "Retry" button (with loading state indicator). Click to resubmit with the same configuration.

### Review Gate Results
1. Select a completed or in-progress run to view its gate results.
2. Each gate displays: gate name, pass/fail status (color-coded), severity level, and reasons list.
3. Gates verify canon consistency — checking for forbidden contradictions, character obligation violations, and continuity errors. Failed gates may trigger auto-repair depending on your policy setting.

### Fork a Project from a Run
1. Select a completed generation run.
2. Click "Fork Project from Run" to create a new project with the generated content.
3. The fork remaps canon IDs, records provenance linking back to the source run, and creates a standalone project you can continue developing independently.

### Review Generated Story
1. Select a completed run to view the generated story summary.
2. The review displays the run ID and manuscript artifact ID (if available).
3. Use this output to evaluate quality before forking or iterating.

## Phase 10: Studio Desk Workspace
Route: `/workspace/:projectId/studio`

The Studio Desk provides a compact, single-screen workspace for focused writing with immediate access to all planning, generation, and review surfaces. Use it when you want a unified desk rather than navigating between separate workspace modes. All layout preferences persist across sessions.

### Layout
The desk has a three-column layout (left rail + manuscript editor + context panel). The context panel is hidden by default for full-width editing.
- **Command bar:** Top header with "Studio Desk" label, project name, and toggle buttons (rail expand/collapse, context panel show/hide).
- **Left rail (Project Map):** Quick navigation between all panels. Click a button to open that panel in the context panel. Collapsible to compact mode (80px icon-only) or expanded (192-320px).
- **Center (Main Content):** Full writing editor with manuscript navigation, draft management, and revision suggestions. Expands to fill available width.
- **Right context panel (320px):** Opens when a rail button is clicked or the panel toggle is pressed. Contains tabbed navigation (Suggestions, Drafts, Manuscripts, Ideas, Characters, World, Review) and the active panel's content. Note: Arcs, Relationships, Canon, Notes, and Jobs panels are accessible via the left rail but do not appear as tabs in the context panel header — they open directly when selected from the rail. Close button hides the panel.

**Accessing Studio:** Navigate to Studio Desk from the left panel's "Studio Desk" link (available on all workspace views), or use the top banner's stage selector (Planning / Studio / Review).

### Project Map Panels (Left Rail)
The left rail provides quick access to 12 panels. Clicking a button opens the context panel with that panel active:

**Develop section:**
- **Drafts:** Draft artifact lifecycle management
- **Manuscripts:** Manuscript document selection and editing. Selecting a manuscript loads it in the center editor.
- **Ideas:** Brainstorm-style idea capture and clustering
- **Suggestions:** Revision suggestions from Manuscript Assist. Accept/reject/archive flows with diff viewer.
- **Review:** Checker findings and inspect links

**Reference section:**
- **Characters:** Character CRUD with progressive disclosure sections (Core, Motivation, Psychological Depth, Context, Tracking) and canon annotations
- **World Bible:** World entry CRUD with canon annotations
- **Relationships:** Relationship graph and list views with CRUD operations. All required fields marked with `*`.
- **Arcs:** Arc candidate management with list/create modes, progressive disclosure sections
- **Canon:** Canon profile management and packet preview

**Utilities section:**
- **Notes:** Project-level notes with add/delete functionality
- **Jobs:** Job launch panel with phase selection and recent job monitoring

### Using the Desk
1. Open a project and navigate to Studio Desk from the left panel's "Studio Desk" link.
2. The editor opens in full-width mode by default.
3. Click a rail button (e.g., "Characters") to open the context panel with that panel active.
4. Write and revise in the center editor.
5. Select text to access the floating toolbar for assist actions.
6. Review suggestions in the Suggestions panel (context panel).
7. Launch jobs from the Jobs panel (context panel).
8. Use the command bar toggles to show/hide the context panel or expand/collapse the rail.
9. Click "Close" in the context panel header to hide it and return to full-width editing.

### Example Workflow: Writing with Context

1. Open Studio Desk for your project.
2. In the Project Map (left rail), select **Characters** — the context panel opens with the character list.
3. Click **Suggestions** — revision suggestions panel becomes active in the context panel.
4. In the center editor, select a paragraph and use the floating toolbar → `Sight & color`.
5. Review the suggestion in the Suggestions panel. Accept to apply, or reject.
6. Mid-chapter, click **Ideas** to capture a new plot idea.
7. Click **Suggestions** again to return to revision suggestions. Continue editing.
8. When done, click **Jobs** to launch a new generation run.
9. Click "Close" in the context panel to return to full-width editing.

### Example Workflow: Full-Width Writing Session

1. Open Studio Desk.
2. The editor starts in full-width mode (context panel hidden).
3. Use the command bar toggle to collapse the left rail to compact mode (80px icon-only) for maximum editor space.
4. Write freely with the manuscript editor filling the full viewport.
5. Expand the left rail from the command bar when you need to access other panels.

### Responsive Behavior
On smaller screens, the left rail becomes an overlay drawer. A "Project" button in the command bar toggles the drawer.

## Radial Hub Workspace Redesign (Design Approved — Future Release)

A Photoshop-style radial hub workspace is approved for implementation. Design replaces route-based navigation with a single central writing surface surrounded by draggable, resizable, tear-off panels. User chooses which panels to show. No forced navigation. Supports multi-monitor floating panels.

**Design spec:** `docs/superpowers/specs/2026-05-19-radial-hub-workspace-design.md`
**Implementation plan:** `docs/superpowers/plans/2026-05-19-radial-hub-phase-1-core-infrastructure.md`

## Phase 11: End-to-End Novel Walkthrough
This phase walks through generating a complete novel from scratch using multi-arc planning, branching, canon management, and iterative generation.

### Overview
We'll build a 12-chapter science fiction novel titled *The Last Lighthouse* with 3 character arcs, 2 sequences (Acts I-II), branching for Act III exploration, and a full canon management workflow. This demonstrates the complete toolchain: foundation → characters → world bible → arcs → planning → generation → revision → checking → canon tightening → re-generation → export.

### Part 1: Project Foundation

#### Step 1: Create the Project
1. Open the home page (`/`).
2. Fill the **New Project** form:
   - **Project Name:** `The Last Lighthouse`
   - **Genre:** `Science Fiction`
   - **Tone Profile:** `Somber, reflective, atmospheric`
   - **Story Structure:** `Three Act`
   - **Point of View:** `Third Limited`
   - **Primary Language:** `English`
   - **Premise:** `In a dying coastal world, the last lighthouse keeper must decide whether to maintain the beacon for ships that may no longer exist.`
3. Click **Create Project**.

#### Step 2: Build the Foundation
1. Navigate to the **Foundation** tab.
2. Fill in:
   - **Premise:** `In a dying coastal world, the last lighthouse keeper must decide whether to maintain the beacon for ships that may no longer exist.`
   - **Logline:** `A lone keeper battles isolation and doubt to keep a lighthouse burning at the end of the world.`
   - **Thematic Spine:** `Duty vs. futility; hope without evidence; the meaning of service when no one is watching; the weight of inherited purpose.`
   - **Tone and Voice Direction:** `Sparse, atmospheric prose. Long descriptive passages alternating with sharp internal monologue. Inspired by Cormac McCarthy and Jeff VanderMeer. No dialogue tags beyond "said". Show the world through sensory experience — salt, light, sound, texture.`
   - **Target Audience:** `Adult literary science fiction readers`
   - **Narrative Constraints:** `No exposition dumps. No omniscient narration. World revealed through keeper's direct experience only. Each chapter ends on an image, not an explanation.`
   - **Complexity Level:** `High`
   - **Success Definition:** `A novel that makes the reader feel the weight of isolation and the quiet dignity of purposeful action.`
3. Click **Save Foundation**.

### Part 2: Character Architecture

#### Step 3: Create Characters (7 total)
Navigate to the **Characters** tab. Create each character with full profiles:

**Act I Characters (3):**
- **Elara Voss** — Protagonist, The Reluctant Guardian. Former navigation officer. 14 months of isolation. Core arc: rigid duty → purposeful choice.
- **The Storm** — Antagonist, Nature as Adversary. Environmental force with increasing personification. Mechanism of the world's decline.
- **Captain Reyes** — Catalyst, The Absent Mentor. Exists only in memory and 47 audio logs. Final message: "Someone has to keep the light."

**Act II Characters (2):**
- **Dr. Ilya Moreau** — Ally/Complication, The Reluctant Truth-Teller. Inland settlement scientist. Arrives via drone with data about the world's state. Challenges Elara's isolation.
- **The Drone (AURA-7)** — Instrument/Character Hybrid. Autonomous delivery system with degraded AI. Serves as the novel's only "conversation" partner. Carries Moreau's messages.

**Act III Characters (2):**
- **Kai Voss** — Revelation, The Lost Connection. Elara's nephew, presumed dead. Signal detected on long-range radio in Act III. Forces Elara to reconsider her isolation.
- **The Fleet Remnant** — Collective Character. Ghost ships detected on radar. May or may not be real. Represents hope vs. delusion.

For each character, fill the required fields first (Character ID, Display Name, Role in Story), then expand optional sections as needed:
- **Core Identity** (required): Character ID, Display Name, Role in Story
- **Motivation** (recommended, ⚡): Archetype, External Goal, Internal Need, Change Axis — used by story generation
- **Psychological Depth** (optional, collapsible): Misbelief, Core Fear, Strengths, Flaw, Contradictions
- **Context** (optional, collapsible): Backstory, Voice Notes, Secrets, Values, Taboos
- **Tracking** (optional, collapsible): Arc Stage Notes, Continuity Facts, Writer Notes

The form uses progressive disclosure — only Core Identity and Motivation are visible by default. Expand sections as you develop character depth.

#### Step 4: Map Relationships
Navigate to the **Relationships** tab. Create relationship edges:
- Elara ↔ Captain Reyes: `Mentorship / Loyalty` — "Unbroken chain of duty"
- Elara ↔ The Storm: `Adversarial / Obsessive` — "The only companion that won't leave"
- Elara ↔ Dr. Moreau: `Tension / Respect` — "Truth she doesn't want to hear"
- Elara ↔ Kai Voss: `Grief / Denial` — "The ghost she stopped expecting"
- Dr. Moreau ↔ Captain Reyes: `Professional Rivalry` — "Disagreed on fleet strategy"

### Part 3: World Bible

#### Step 5: Build World Bible (8 entries)
Navigate to the **World Bible** tab. Create entries:

**Locations (3):**
- **The Beacon** — Last lighthouse, granite outcrop, 200m above sea. Fresnel lens, geothermal generator at 23%. Three rooms: sleeping chamber, log room, lantern gallery.
- **The Drowning** — World state. Coastal cities abandoned. Sea level +40m. Atmosphere thick with salt and storm. Civilization clusters inland.
- **The Inland Settlement (Echo Point)** — Dr. Moreau's base. 400km inland. Population unknown. Maintains radio silence except for drone drops.

**Artifacts (2):**
- **The Logs** — Three sets: official beacon log (511 entries), Reyes's tapes (47), private journal (289 entries). Structural backbone of the novel.
- **The Geothermal Generator** — Failing power source. Core of Act II crisis. Repair attempted in Act III.

**Concepts (3):**
- **The Silence** — 8 months of radio silence from inland. 11 months without ship sightings. The silence is a character — it presses on Elara.
- **The Beacon Protocol** — Military protocol requiring continuous operation. The legal/moral framework for Elara's duty. What happens when the protocol's purpose is gone?
- **The Last Fleet** — Dissolved 3 years before story begins. Reyes chose to stay on the last ship rather than return. Why?

### Part 4: Arc Planning

#### Step 6: Define Character Arcs (3 arcs)
Navigate to the **Arcs** tab. Create candidate arcs and stage maps:

**Arc 1 — The Keeper's Choice (Elara)**
- Stage 1: Routine — maintains beacon through worsening storms
- Stage 2: Crisis — generator at 8%, discovers Reyes's final tape
- Stage 3: Decision — attempts repair, fails, beacon flickers but holds
- Stage 4: Revelation — Kai's signal forces confrontation with isolation
- Stage 5: Resolution — chooses to keep the light burning for its own meaning

**Arc 2 — The Truth Arrives (Elara + Moreau)**
- Stage 1: Isolation — Elara believes she is alone
- Stage 2: Contact — drone arrives with Moreau's data
- Stage 3: Conflict — data reveals the world is worse than she thought
- Stage 4: Negotiation — Moreau offers her a way out; she refuses
- Stage 5: Acceptance — Moreau's data confirms the beacon is the last signal

**Arc 3 — The Ghost Fleet (Elara + Kai)**
- Stage 1: Denial — Kai presumed dead, Elara has accepted this
- Stage 2: Signal — long-range radio picks up Kai's voice
- Stage 3: Doubt — is it real or a ghost signal? radar shows contacts
- Stage 4: Confrontation — Elara must choose: stay at beacon or respond
- Stage 5: Synthesis — the beacon IS the response; she keeps it lit for Kai

### Part 5: Structure Planning

#### Step 7: Plan Sequences and Chapters
Navigate to the **Planning** tab.

**Sequence 1 — Act I: The Watch (Chapters 1-4)**
- Ch 1: The Watch — Elara's nightly routine. Worst storm in months. Generator abnormal. Reyes's tape #12.
- Ch 2: The Decline — Morning inspection: 8%. Log review shows 6-week acceleration. Private journal reopened.
- Ch 3: The Tape — Tape #47 discovered. Reyes knew about decline. Left repair instructions. Chose to stay on last ship.
- Ch 4: The First Crack — Elara attempts minor repair. Storm returns. She realizes the generator won't last the season.

**Sequence 2 — Act II: The Signal (Chapters 5-8)**
- Ch 5: The Drone — AURA-7 arrives. Degrading AI. Carries Moreau's data package.
- Ch 6: The Data — Moreau's findings: sea level rising faster than predicted. Inland settlements failing. Elara is truly last.
- Ch 7: The Conversation — Elara speaks to AURA-7. The drone's degraded AI creates an uncanny companionship. Moreau offers extraction.
- Ch 8: The Refusal — Elara rejects Moreau's offer. Storm intensifies. Generator drops to 4%.

**Sequence 3 — Act III: The Light (Chapters 9-12)**
- Ch 9: The Signal — Long-range radio picks up Kai's voice. Elara's world fractures.
- Ch 10: The Attempt — Elara enters geothermal chamber. Dangerous repair. Storm returns mid-work. Stabilizes at 12%.
- Ch 11: The Ghost Fleet — Radar shows contacts. Kai's signal repeats. Are they real? Moreau's data says no.
- Ch 12: The Light — Dawn breaks. Beacon still burns. Final journal entry: "The ships don't matter. The light does."

For each chapter, set **Active Characters** and write detailed summaries.

### Part 6: Canon Management

#### Step 8: Build Canon Profiles
Navigate to Canon Workshop (`/workspace/:projectId/canon`).

1. **Overview Tab**: Create canon profile `Act I Profile`:
   - Select: Elara, The Storm, Captain Reyes
   - World entries: The Beacon, The Drowning, The Logs
   - Generation brief: `Generate Act I chapters 1-4. Focus on establishing isolation, routine, and the first signs of crisis. Atmospheric prose. No dialogue beyond Reyes's tapes.`
   - Click **Save Profile**

2. Create canon profile `Act II Profile`:
   - Select: All 7 characters
   - World entries: All 8 entries
   - Generation brief: `Generate Act II chapters 5-8. Introduce Moreau and AURA-7. The conversation chapter should feel uncanny — the drone's degraded AI creates strange, fragmented exchanges. Moreau's data should feel like a world shrinking.`
   - Click **Save Profile**

3. Create canon profile `Act III Profile`:
   - Select: All 7 characters
   - World entries: All 8 entries
   - Generation brief: `Generate Act III chapters 9-12. Kai's signal is the emotional climax. The ghost fleet is ambiguous — never confirm or deny. The ending is quiet, not triumphant. Elara's choice is about meaning, not hope.`
   - Click **Save Profile**

4. **Packet Preview Tab**: Verify each profile's packet size. Adjust if exceeding context limits.

### Part 7: Multi-Run Generation

#### Step 9: Generate Act I
1. Navigate to Generation (`/workspace/:projectId/generate`).
2. Configure:
   - **Mode:** `New Arc`
   - **Destination:** `Same Project`
   - **Canon Scope:** Use `Act I Profile` (3 characters, 3 world entries)
   - **Continuity Strictness:** `Block`
   - **Generation Brief:** (from Act I Profile)
   - **Chapter Count:** `4`
3. Click **Start Generation**.
4. Monitor run. Review output in Writing workspace.
5. Revise with Floating Toolbar:
    - `Sight & color` on storm descriptions
    - `Show don't tell` on emotional passages
    - `Tighten & polish` on repetitive routine descriptions

#### If Act I generation fails:
- **INFERENCE_TRUNCATED:** Reduce Chapter Count to 2, generate Ch 1-2, then Ch 3-4 in a second run. Increase `NARRATIVE_MAX_TOKENS_DRAFTER=16000` in `.env`.
- **Canon contradiction (gate failure):** Check gate results panel. Relax continuity strictness to `Warn` or fix the conflicting canon entry.
- **Generic/flat output:** Improve generation brief with specific voice instructions. Add more world bible entries for richer context.

#### Step 10: Generate Act II
1. Repeat generation with `Act II Profile`.
2. **Key difference:** 7 characters, 8 world entries — larger canon packet.
3. Monitor for:
   - Moreau's voice consistency (scientific, direct, urgent)
   - AURA-7's degraded AI dialogue (fragmented, uncanny)
   - Canon consistency with Act I (generator readings, log references)
4. Run checker after generation. Resolve any canon contradictions.

#### If Act II generation fails:
- **Packet too large:** Split Act II into two runs (Ch 5-6, Ch 7-8). Use prior chapter summaries for context continuity.
- **Character voice drift:** Check Moreau's Voice Notes field. Annotate it in Characters tab for strict enforcement. Re-run with `Block` continuity.
- **AURA-7 dialogue not uncanny enough:** Add specific instruction to generation brief: "AURA-7's speech is fragmented, with random pauses and occasional garbled words. It should feel like talking to a broken radio."

#### Step 11: Generate Act III (with branching)
1. **Main branch:** Generate Act III with `Act III Profile`.
2. **Alternative branch:** Create a branch for Act III with different Kai resolution:
   - Navigate to **Branches** tab → Create branch `Act III - Kai Confirmed`
   - In branch: Kai's signal is confirmed real. Ghost fleet is real. Ending is hopeful.
   - Generate this branch.
3. **Compare:** Use branch comparison to evaluate both endings.
4. **Decide:** Merge preferred branch or keep both as alternate versions.

#### If Act III generation fails:
- **Ambiguity lost in ghost fleet:** Add to generation brief: "Do NOT confirm or deny whether the ghost fleet is real. End on ambiguity."
- **Kai's emotional impact weak:** Add Kai's relationship edge to canon scope. Increase Kai's presence in generation brief.
- **Branch comparison takes too long:** Generate main branch first. Only create alternate branch if the ending feels unsatisfactory.

### Part 8: Review and Polish

#### Step 12: Full Novel Review
1. Navigate to **Review** (`/workspace/:projectId/review`).
2. Run the Role Model Checker on the full novel.
3. Review findings:
   - Character voice drift across 12 chapters
   - Canon contradictions (generator readings, timeline consistency)
   - Structural pacing (Act II middle sag, Act III climax)
4. Resolve findings by returning to Writing and making corrections.
5. Use **Inspect** to trace problematic runs to their root causes.

#### Step 13: Canon-Tight Revision Loop
1. Review checker findings.
2. Annotate canon fields in Characters/World Bible tabs for fields that need strict enforcement.
3. Re-run generation for chapters with contradictions.
4. Repeat until checker is clean.

### Part 9: Export and Archive

#### Step 14: Export the Novel
1. Return to home page (`/`).
2. Find project card → Click **Export**.
3. ZIP archive contains:
   - Project manifest with full metadata
   - Bible database (7 characters, 8 world entries, 3 arcs, relationships)
   - 12 manuscript documents (one per chapter)
   - Generation run records (3 runs + branch runs)
   - Canon profiles (3 profiles)
   - Checker findings and resolution history
4. Store archive. Create a backup.

### Expected Outcome
A complete 12-chapter novel with:
- 7 character profiles with 3 interwoven arcs
- 8 world bible entries (3 locations, 2 artifacts, 3 concepts)
- 5 relationship edges with tension notes
- 3 sequences (Acts I-III) with 12 planned chapters
- 3 canon profiles for act-scoped generation
- Branch comparison for Act III resolution
- Full checker review with canon-tight revision loop
- Exported project archive with complete provenance

### Novel-Specific Troubleshooting
- **Character voice drift across chapters:** Use canon annotations on Voice Notes fields. Set continuity strictness to `Block` for voice-related contradictions.
- **Act II pacing sag:** Add more world bible entries for Act II (Moreau's lab, Echo Point interior). Increase AURA-7's presence in generation brief.
- **Canon packet too large for Act III:** Split Act III into two generation runs (Ch 9-10, Ch 11-12). Use prior chapter summaries for context continuity.
- **Branch comparison unclear:** Generate both branches, then use branch comparison tool. Focus on emotional resonance of endings, not just canon consistency.
- **Truncated output on 12-chapter novel:** Increase `NARRATIVE_MAX_TOKENS_DRAFTER=16000` and `NARRATIVE_MAX_TOKENS_DEFAULT=16000`. Generate in act-sized batches (4 chapters per run).

### See Also
- **Branching workflow:** Phase 3 (Branches tab) — create, compare, merge branches
- **Canon management:** Phase 8 (Canon Workshop) — profiles, scope selection, packet preview
- **Cascade Discovery:** Phase 3 (Relationships tab) — auto-extract entities from existing manuscript text

## Phase 12: Full Production Workflow

For the complete production workflow order, see **End-to-End Recommended Workflow** in the [User Guide v1.9.0](User%20Guide%20v1.8.0.md). The walkthrough's Phase 11 demonstrates this workflow across a full 12-chapter novel with multi-arc planning, branching, and canon management.

## Common Mistakes and Fixes

- **"I clicked Generate but nothing happened"** — The generation brief is empty or no canon entities are selected. Both are required to enable "Start Generation".
- **"My characters don't appear in the generated output"** — Characters must be selected in the canon scope (Canon Workshop Overview tab or Generation wizard). Being created in the project is not enough.
- **"Suggestions panel is empty"** — You must select text in the editor and trigger an assist action (floating toolbar or Assist dropdown). Then click "Suggestions" in the left rail to view results. The panel doesn't auto-populate.
- **"Project won't export"** — The project needs at least 1 manuscript or draft artifact. Run P-300 Drafter or promote a draft to manuscript first.
- **"Cascade scan returns no entities"** — Manuscript text must be at least 50 characters and contain character names, interactions, or descriptive details. Very short or sparse text yields no results.
- **"Inspect shows 'run not found'"** — The job ID in the URL must match an existing checker run or pipeline job. Navigate from Review → Inspect Run Links or the Job Launch panel to get valid IDs.
- **"Checker finds no findings"** — The checker needs completed runs to analyze. Run at least one pipeline job (P-100 through P-400) before expecting findings.

## Phase 13: Advanced Iteration Patterns

### Pattern A: Canon-tight revision loop
1. Write draft.
2. Checker review.
3. Inspect root causes.
4. Annotate canon fields.
5. Re-run generation.

**Example:** You wrote Ch 5. Checker finds Elara's voice drifted in paragraph 3 (too casual for the established sparse, atmospheric tone). Navigate to Characters → Elara Voss → annotate Voice Notes field for strict enforcement. Re-run P-300 for Ch 5 with `Block` continuity strictness. Checker passes on re-run.

### Pattern B: Alternate story exploration
1. Create branch.
2. Draft alternate variants.
3. Compare and decide.
4. Merge preferred direction.

**Example:** Act III ending feels rushed. Create branch `Act III - Extended`. Generate Ch 11-12 with additional world bible entries (Echo Point interior, Reyes's ship log). Compare branch output against main branch using branch comparison tool. Extended version has better pacing. Merge `Act III - Extended` into main.

### Pattern C: Forked sequel workflow
1. Select successful generation run.
2. Fork to new project.
3. Re-open planning and writing in fork.
4. Repeat quality loop.

**Example:** Act I-III of *The Last Lighthouse* is complete. Select the final generation run → click "Fork Project from Run" → name new project *The Last Lighthouse: Sequel*. Open fork → update Foundation with sequel premise → add new characters (Kai Voss arrives at the beacon) → generate sequel chapters with Act III canon as grounding context.

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

### Studio Desk
- Three-column layout: Command Bar (top), Project Map (left rail, 80-320px), Manuscript Editor (center, full width), Context Panel (right, 320px, toggleable).
- Context panel hidden by default for full-width editing. Opens on rail button click or panel toggle.
- Context panel tabs: Suggestions, Drafts, Manuscripts, Ideas, Characters, World, Review.
- Layout preferences persist across sessions (rail mode, widths, panel visibility).
- Project Map: 12 panels — Drafts, Manuscripts, Ideas, Suggestions, Review, Characters, World Bible, Relationships, Arcs, Canon, Notes, Jobs.
- Left rail collapses to compact icon-only mode (80px) or expands (192-320px).
- Command bar toggles: rail expand/collapse, context panel show/hide.
- Responsive: overlay drawer below `xl:` breakpoint.
- **Future:** Radial Hub Workspace redesign (design approved) will replace this layout with draggable, resizable, tear-off panels around a central writing surface.

## Common Failure Cases and Fixes
- Missing project context: verify `:projectId` route and selected project.
- Auth-gated features blocked: configure API key path and server variable.
- Generation/checker failures: validate inference backend and model readiness.
- Empty inspect context: use a valid run/job id or navigate from review/job workflows.
- No writing outputs: ensure upstream planning and draft generation steps completed.
- **Truncated LLM output** (`INFERENCE_TRUNCATED`): The LLM hit its token budget mid-response. The Job Launch panel displays an expandable error with fix guidance. Resolution: add `NARRATIVE_MAX_TOKENS_DEFAULT=8192` (or higher) to your `.env`, or set per-phase overrides such as `NARRATIVE_MAX_TOKENS_DRAFTER=8000`. Restart the server after changes.
- **Cannot reach LLM server** (`INFERENCE_TRANSPORT_FAILURE`): Verify llama.cpp is running and `NARRATIVE_INFERENCE_BASE_URL` in `.env` is correct. Default: `http://127.0.0.1:8080`.
- **LLM circuit breaker open**: The backend has failed repeatedly. Fix the underlying connectivity or configuration issue, then wait for the circuit to reset or restart the server.
- **Cascade scan returns no entities**: Ensure manuscript text is at least 50 characters and contains character names, interactions, or descriptive details. Very short or sparse text may yield no discoverable entities. Adjust chunk size upward if using a high-context model.

## Completion Checklist
A project is operationally complete when:
- Foundation, characters, world bible, and relationships are populated (manually or via Cascade Discovery).
- At least one manuscript exists and has been revised.
- Checker findings have been reviewed.
- At least one inspectable run is present.
- Canon profile/packet has been reviewed.
- At least one generation run completed (and optionally forked).
- Export archive captured.
- (Optional) Studio Desk workspace is configured with preferred rail width and active panel.

**Phase 11 (End-to-End Novel Walkthrough)** demonstrates all checklist items across a full novel workflow with multi-arc planning, branching, and canon management.
