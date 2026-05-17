# Narrative Engine - Complete User Walkthrough v1.8.0

Last updated: 2026-05-17

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
- `/workspace/:projectId/studio` Studio Desk

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
Route: `/workspace/:projectId/write`

Three-column layout: Manuscripts/Drafts (left), Editor (center), Aids panel (right).

**Route-aware layout:** When navigating to a specific chapter via `/workspace/:projectId/write/:chapterId`, the layout collapses to a single column showing only the Editor. The left sidebar and right aids panel are hidden for focused chapter editing. Navigate back to `/workspace/:projectId/write` to restore the full three-column view.

### Left Column: Manuscripts + Drafts
**Manuscripts section:**
- Select a manuscript document from the list to open it in the center editor.
- Click "Edit" to enter edit mode; "Save" or "Cancel" to commit/discard changes.

**Drafts section:**
- **Create manual draft** — form with title input and content textarea. Submits a new draft artifact for the selected manuscript.
- **Continue draft** — per-draft-card button that generates a continuation of the draft's content via LLM. The result appears as a new draft artifact.
- **Alternate variant** — per-draft-card button that generates an alternate version of the same narrative beat from a different angle.
- **Promote to manuscript** — per-draft-card button that promotes a finalized draft into a new manuscript document, making it editable in the main editor.
- **AI draft generation** — form with title input and brief textarea. Generates a complete draft from scratch using LLM, guided by the title and creative brief. Click submit to trigger an async job.
- **Pending state display** — in-flight AI draft jobs show an amber loading indicator with pulsing dots and the draft title. If the job fails, an error message appears inline. Completed drafts appear in the list automatically.

### Center Column: Manuscript Editor
1. Toggle between read mode (formatted markdown rendering) and edit mode (textarea).
2. Word count and character count display update in real-time.
3. Select text by clicking and dragging to access assist actions via the floating toolbar or Assist dropdown.

### Right Column: Aids Panel
- Unified suggestions list combining standard revision suggestions and LLM-powered assist suggestions.
- Each suggestion shows source text, proposed text, and rationale.
- Actions per suggestion: "Accept" (apply changes), "Reject" (dismiss), "Archive" (save for later reference).
- Diff view and history support via aids components for tracking changes over time.

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

Each action sends a parameterized instruction to the Manuscript Assist backend with the selected text range, surrounding anchor context (~120 characters before/after), and kind-specific LLM prompt. The result appears as suggestions in the Aids panel for review, accept, or reject.

### Step-by-step assist workflow
1. Select text in the manuscript editor by clicking and dragging.
2. The floating toolbar appears near your selection.
3. Click an action (e.g., "Sight & color" under Sensory detail).
4. A toast confirms submission; the request processes via Manuscript Assist.
5. Review the suggestion output in the Aids panel (right column).
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

The Studio Desk provides a compact, single-screen workspace for focused writing with immediate access to all planning, generation, and review surfaces. Use it when you want a unified desk rather than navigating between separate workspace modes.

### Layout
The desk has three columns (desktop) or overlay drawers (below `xl:` breakpoint):
- **Left rail (Project Map):** Quick navigation between Ideas, Characters, World Bible, Relationships, Canon, Jobs, and Notes panels.
- **Center (Main Content):** Full writing editor with manuscript navigation, draft management, and revision suggestions.
- **Right rail (Context Panel):** Switchable panel based on active command.

### Command Bar
Five command buttons at the top toggle the right context panel:
- `Capture` — switches to Ideas panel for brainstorm-style ideation
- `Write` — switches to Suggestions panel for revision suggestions, diff viewer, and history
- `Generate` — switches to Generation panel for compact story generation wizard
- `Review` — switches to Review panel for checker findings and inspect links
- `Inspect` — switches to Inspect panel for job inspection and lineage

### Using the Desk
1. Open a project and navigate to Studio Desk from the left rail.
2. Use the Project Map to switch between planning panels (Characters, World Bible, Relationships, etc.).
3. Click command buttons to change the right context panel.
4. Write and revise in the center editor while keeping planning context visible.
5. Launch generation runs directly from the Generation panel without leaving the desk.
6. Review checker findings and inspect problematic runs from the Review/Inspect panels.

### Responsive Behavior
On smaller screens, the left rail and right context panel become overlay drawers. Toggle buttons appear in the header. Click the close-drawer button to dismiss both drawers simultaneously.

## Phase 11: End-to-End Short Story Walkthrough
This phase walks through generating a complete short story from scratch. Follow these steps with your own story concept or use the example provided.

### Step 1: Create the Project
1. Open the home page (`/`).
2. Fill the **New Project** form:
   - **Project Name:** `The Last Lighthouse`
   - **Genre:** `Science Fiction`
   - **Tone Profile:** `Somber, reflective`
   - **Story Structure:** `Three Act`
   - **Point of View:** `Third Limited`
   - **Primary Language:** `English`
   - **Premise:** `In a dying coastal world, the last lighthouse keeper must decide whether to maintain the beacon for ships that may no longer exist.`
3. Click **Create Project**. The project opens in Planning mode.

### Step 2: Build the Foundation
1. Navigate to the **Foundation** tab.
2. Fill in the core fields:
   - **Premise:** `In a dying coastal world, the last lighthouse keeper must decide whether to maintain the beacon for ships that may no longer exist.`
   - **Logline:** `A lone keeper battles isolation and doubt to keep a lighthouse burning at the end of the world.`
   - **Thematic Spine:** `Duty vs. futility; hope without evidence; the meaning of service when no one is watching.`
   - **Tone and Voice Direction:** `Sparse, atmospheric prose. Long descriptive passages alternating with sharp internal monologue. Inspired by Cormac McCarthy and Jeff VanderMeer.`
   - **Target Audience:** `Adult literary science fiction readers`
   - **Narrative Constraints:** `No dialogue tags beyond "said". No exposition dumps. Show the world through the keeper's sensory experience.`
   - **Complexity Level:** `Medium`
3. Click **Save Foundation**. A revision is recorded.

### Step 3: Create Characters
1. Navigate to the **Characters** tab.
2. Click **Add Character** and create:

   **Character 1 — Elara Voss (The Keeper)**
   - **Role in Story:** `Protagonist`
   - **Archetype:** `The Reluctant Guardian`
   - **External Goal:** `Keep the lighthouse beacon lit through the final storm season`
   - **Internal Need:** `Accept that her duty has meaning even without witnesses`
   - **Misbelief or Wound:** `Believes she was abandoned here as punishment`
   - **Core Fear:** `That the light means nothing and she wasted her life`
   - **Primary Strength:** `Unshakable discipline; meticulous attention to detail`
   - **Fatal Flaw:** `Inability to ask for help; emotional isolation`
   - **Voice Notes:** `Speaks sparingly. When she does, sentences are short and precise. Internal monologue is richer, more poetic.`
   - **Backstory Summary:** `Former navigation officer on the last deep-sea fleet. Assigned to the lighthouse after the fleet dissolved. Has not spoken to another person in 14 months.`
   - Click **Save Character**

   **Character 2 — The Storm (Antagonistic Force)**
   - **Role in Story:** `Antagonist / Environmental Force`
   - **Archetype:** `Nature as Adversary`
   - **External Goal:** `Extinguish the beacon, reclaim the coast`
   - **Internal Need:** `N/A — elemental force`
   - **Backstory Summary:** `The storms have been growing for decades. They are the mechanism of the world's decline — salt winds, acid rain, pressure systems that shred the coastline. The keeper's logs describe them with increasing personification over time.`
   - Click **Save Character**

   **Character 3 — Captain Reyes (Memory / Ghost)**
   - **Role in Story:** `Catalyst / Memory Figure`
   - **Archetype:** `The Absent Mentor`
   - **External Goal:** `N/A — exists only in memory and recorded messages`
   - **Internal Need:** `To be remembered accurately`
   - **Backstory Summary:** `Elara's former fleet commander. Left a series of audio logs before the fleet dissolved. His final message — "Someone has to keep the light" — is the reason Elara stayed. His logs play throughout the story as structural anchors.`
   - Click **Save Character**

3. Verify all three characters appear in the character list.

### Step 4: Build the World Bible
1. Navigate to the **World Bible** tab.
2. Click **Add Entry** and create:

   **Entry 1 — The Beacon (Location)**
   - **Summary:** `The last functioning lighthouse on the eastern coast. Built on a granite outcrop 200 meters above the churning sea. The lens is a first-order Fresnel, powered by a geothermal generator that's failing. The keeper's quarters are three rooms: sleeping chamber, log room, and the lantern gallery.`
   - **Canonical Facts:** `The beacon has operated continuously for 14 years. The geothermal generator is at 23% capacity. Supply drops ceased 14 months ago.`
   - Click **Save Entry**

   **Entry 2 — The Drowning (World State)**
   - **Summary:** `The world is slowly being reclaimed by the sea. Coastal cities are abandoned. The atmosphere is thick with salt and storm. What remains of civilization clusters inland, far from the coast. No ships have been sighted in 11 months.`
   - **Canonical Facts:** `Sea level has risen 40 meters since the keeper arrived. The last supply drop was from an automated drone. Radio silence from inland settlements for 8 months.`
   - Click **Save Entry**

   **Entry 3 — The Logs (Artifact)**
   - **Summary:** `Elara maintains three sets of logs: the official beacon log (daily readings), Captain Reyes's audio logs (stored on a deteriorating tape drive), and her private journal (kept in a waterproof tin). The logs serve as the story's structural backbone.`
   - **Canonical Facts:** `The official log has 511 daily entries. Reyes's tapes number 47. The private journal has 289 entries spanning 3 years.`
   - Click **Save Entry**

### Step 5: Define the Story Arc
1. Navigate to the **Arcs** tab.
2. Click **Add Candidate Arc** and create:

   **Arc 1 — The Keeper's Choice**
   - **Summary:** `Elara discovers the geothermal generator will fail within weeks. She must choose: attempt a dangerous repair that could kill her, or let the beacon go dark and abandon her post. Her journey from rigid duty to purposeful choice forms the emotional core.`
   - **Arc Type:** `Character Arc`
   - Click **Save Arc**

3. Select the arc and create a **Stage Map**:
   - **Stage 1:** `Routine — Elara maintains the beacon through worsening storms. Generator readings decline.`
   - **Stage 2:** `Crisis — Generator drops to 8%. Elara finds Reyes's final tape revealing he knew about the decline.`
   - **Stage 3:** `Decision — Elara attempts the repair. Fails. The beacon flickers but holds.`
   - **Stage 4:** `Resolution — Elara chooses to keep the light burning not for ships, but because the act itself is meaningful.`

### Step 6: Plan the Structure
1. Navigate to the **Planning** tab.
2. Create a **Sequence Plan**:
   - **Title:** `The Last Light`
   - **Description:** `A three-act short story in 5 chapters`
   - Click **Save Sequence**

3. Create **Chapter Plans** under the sequence:

   **Chapter 1 — The Watch**
   - **Summary:** `Elara performs her nightly routine. The storm outside is the worst in months. Generator readings are abnormal. She plays Reyes's tape #12 as she climbs to the lantern gallery.`
   - **Active Characters:** `Elara Voss, Captain Reyes (memory)`
   - Click **Save Chapter**

   **Chapter 2 — The Decline**
   - **Summary:** `Morning inspection reveals the generator is at 8%. Elara reviews the official log — the decline has been accelerating for 6 weeks. She opens her private journal for the first time in months.`
   - **Active Characters:** `Elara Voss`
   - Click **Save Chapter**

   **Chapter 3 — The Tape**
   - **Summary:** `Elara discovers Reyes's tape #47 — previously unplayed. Reyes knew about the generator's decline and left repair instructions. The tape also reveals he chose to stay on the last ship rather than return inland.`
   - **Active Characters:** `Elara Voss, Captain Reyes (memory)`
   - Click **Save Chapter**

   **Chapter 4 — The Attempt**
   - **Summary:** `Elara attempts the repair during a lull in the storm. The work is dangerous — she must enter the geothermal chamber below the beacon. The storm returns mid-repair. She fails but stabilizes the generator at 12%.`
   - **Active Characters:** `Elara Voss, The Storm`
   - Click **Save Chapter**

   **Chapter 5 — The Light**
   - **Summary:** `Elara sits in the lantern gallery as dawn breaks. The beacon still burns. She writes her final journal entry: "The ships don't matter. The light does." She returns to her watch.`
   - **Active Characters:** `Elara Voss`
   - Click **Save Chapter**

### Step 7: Generate the Story
1. Click the **Generate Story** button (or navigate to `/workspace/:projectId/generate`).
2. Configure the generation wizard:
   - **Mode:** `New Arc`
   - **Destination:** `Same Project`
   - **Canon Scope:** Select all 3 characters and all 3 world bible entries
   - **Continuity Strictness:** `Block`
   - **Generation Brief:** `Write a 5-chapter short story following the planned structure. Sparse, atmospheric prose. No dialogue tags beyond "said". Show the dying world through Elara's sensory experience — the salt on her skin, the groan of the lens, the taste of old coffee. Each chapter should end on an image, not an explanation. Captain Reyes exists only in memory and recorded tapes. The storm is a living presence. The ending is quiet, not triumphant.`
   - **Chapter Count:** `5`
3. Click **Preview Fork** to verify scope: should show 3 characters, 3 world entries, 1 arc.
4. Click **Start Generation**.

### Step 8: Monitor the Run
1. A run card appears in the grid showing generation status.
2. Click the run card to view details:
   - **Status:** `Processing` → `Completed` (or `Failed` if inference issues)
   - **Job Count:** 4 (G-200 plan, G-300 draft, G-350 gate, G-400 compile)
3. If the run fails:
   - Check the error details in the run card
   - For `INFERENCE_TRUNCATED`: increase `NARRATIVE_MAX_TOKENS_DEFAULT` in `.env`
   - For `INFERENCE_TRANSPORT_FAILURE`: verify llama.cpp is running
   - Click **Retry** to resubmit

### Step 9: Review the Output
1. Once completed, the generated story appears in the **Generated Story Review** panel.
2. Navigate to **Writing** (`/workspace/:projectId/write`) to view the manuscript.
3. Review each chapter for:
   - Canon consistency (character voices match profiles)
   - Thematic alignment (tone matches Foundation direction)
   - Structural integrity (chapters follow planned sequence)

### Step 10: Revise with Assist
1. In the Writing workspace, select text you want to improve.
2. Use the **Floating Toolbar** for targeted edits:
   - `Sight & color` — enhance visual atmosphere in storm scenes
   - `Show don't tell` — convert abstract emotional statements into concrete actions
   - `Tighten & polish` — remove redundancy in repetitive passages
3. Review suggestions in the **Aids Panel** (right column).
4. **Accept** good suggestions, **Reject** ones that break voice, **Archive** ideas for later.

### Step 11: Run the Checker
1. Navigate to **Review** (`/workspace/:projectId/review`).
2. In the **Findings** tab, review any checker findings:
   - Character voice inconsistencies
   - Canon contradictions
   - Structural issues
3. Resolve findings by returning to Writing and making corrections.
4. Re-run the checker to verify fixes.

### Step 12: Export the Project
1. Return to the home page (`/`).
2. Find your project card.
3. Click **Export** to download a ZIP archive containing:
   - Project manifest
   - Bible database (characters, world bible, arcs)
   - Manuscript documents
   - Generation run records
4. Store the archive for backup or transfer.

### Expected Outcome
You should now have a complete short story with:
- 3 character profiles with arcs
- 3 world bible entries establishing setting
- 5 planned chapters with active character assignments
- Generated manuscript content
- Revision suggestions applied
- Checker findings resolved
- Exported project archive

### Troubleshooting This Walkthrough
- **Generation produces generic output:** Improve the generation brief with more specific voice and tone instructions. Add more world bible entries for richer context.
- **Characters feel flat in output:** Add more detail to character profiles — especially Voice Notes, Contradictions, and Secrets fields.
- **Storm doesn't feel like a character:** Add a world bible entry specifically for the storm's behavior patterns, or increase the Storm character's presence in the generation brief.
- **Pacing feels rushed:** Increase chapter count to 7-8 and add transitional chapters between major beats.
- **Output is truncated:** Increase `NARRATIVE_MAX_TOKENS_DRAFTER=16000` in `.env` and restart the server.

## Phase 12: Full Production Workflow
Use this order for complete project execution.

1. Create or import a project (Phase 1).
2. Build foundation, characters, world bible, and arcs in Planning tabs (Phase 3).
3. (Optional) Run Cascade Discovery to auto-extract entities from existing manuscript text — review discovered characters, relationships, and world entries before committing.
4. Structure narrative in planning and flow tabs (Phase 3).
5. Capture side ideas in brain dump and brainstorm (Phases 3-4).
6. Draft and revise in writing workspace using the floating toolbar for targeted assist actions (Phase 5).
7. Use Manuscript Assist sensory detail, rewrite, and continue actions to refine prose (Phase 5).
8. Run the Role Model Checker and resolve findings in Review workspace (Phase 6).
9. Inspect problematic runs from deep links or Inspect mode to diagnose failures (Phase 7).
10. Harden canon scope, manage profiles, and validate packet composition in Canon Workshop (Phase 8).
11. Execute generation runs: configure wizard, monitor status, review gates, fork successful runs (Phase 9).
12. Iterate via branches, decisions, and additional drafts.
13. Export final project archive for backup and transfer.
14. (Alternative) Use Studio Desk for a compact single-screen workspace that combines writing, planning, generation, and review in one view (Phase 10).

## Phase 13: Advanced Iteration Patterns
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

### Studio Desk
- Three-column layout: Project Map (left), Main Content (center), Context Panel (right).
- Command bar toggles context panel: Capture, Write, Generate, Review, Inspect.
- Project Map provides quick navigation between Ideas, Characters, World Bible, Relationships, Canon, Jobs, Notes.
- Context Panel switches between Suggestions, Generation, Review, Inspect panels.
- Responsive: overlay drawers below `xl:` breakpoint with header toggle buttons.

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
- (Optional) Studio Desk workspace is configured with preferred panels and command bar layout.

**Phase 11 (End-to-End Short Story Walkthrough)** demonstrates all checklist items in a single practical workflow.
