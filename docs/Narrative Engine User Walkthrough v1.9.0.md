# Narrative Engine - Complete User Walkthrough v1.9.1

Last updated: 2026-05-30 (Compact rail mode, entity count badges, tray launcher, typed rail icons)

## Goal
This walkthrough is the full frontend operating manual. It explains every workspace interface and gives a comprehensive, practical workflow from first launch to advanced generation and iteration.

## Preconditions
- Backend is running.
- Frontend is running.
- Inference backend is configured for LLM-dependent features.
- If `NARRATIVE_API_KEY` is enabled on the server, configure API key usage for protected flows.

**Starting the application:**
- **Tray Launcher (recommended):** Run `narrative-launcher\narrative-launcher.exe` — starts backend + frontend automatically, system tray icon with status indicator, no console window.
- **Development mode:** Run `start_narrative_core.cmd --dev` — spawns separate windows for uvicorn (with `--reload`) and Vite dev server (hot-reload).
- **Production mode:** Run `start_narrative_core.cmd` — builds frontend once, runs uvicorn in current terminal.

## Quick Start: Your First Project in 10 Minutes

1. Open `/` → fill New Project form (name, genre, tone, structure, POV, language) → click **Create Project**
2. Navigate to **Foundation** tab → fill Premise and Logline → click **Save Foundation**
3. Navigate to **Characters** tab → click **Add Character** → create one protagonist → click **Save Character**
4. Navigate to **Studio Desk** → open the **Jobs** panel → select **P-100 Architect** → click **Launch** → wait for completion
5. Select **P-300 Drafter** → click **Launch** → wait for completion → view generated chapter in the Manuscripts panel

For a complete walkthrough with 12 chapters, 7 characters, and branching, see Phase 13.

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

**Note:** In Studio mode, the WorkspaceShell left panel is hidden. StudioView uses its own left rail (Project Map) and embeds WritingView directly in a two-column layout. The legacy right context panel is removed.

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

## Phase 4b: Ideation Workspace
Route: Studio Desk (`/workspace/:projectId/studio`) → Ideas and Notes panels

Ideation is the first stage of the writing process. The Ideas panel captures structured brainstorm items that can be promoted into planning objects. The Notes panel provides freeform scratch space for reminders, prompts, and mid-session thoughts. Use both during any stage — they survive the entire project lifecycle.

### Ideas Panel — Structured Brainstorm Capture
1. Open Studio Desk → click **Ideas** in the left rail (Ideation section).
2. Click **Add Idea** to create a new brainstorm item.
3. Fill in the idea content — a plot concept, character idea, world detail, or "what if?" scenario.
4. Ideas appear in a list with timestamps and status indicators.
5. **Cluster ideas:** Select multiple related ideas and click "Cluster" to group them. The LLM categorizes the cluster (e.g., "character arcs", "world rules").
6. **Promote ideas:** Select ideas that are ready for downstream use and click "Promote". The system creates planning entities from the selected ideas:
   - Character ideas → Character profiles in the Characters panel
   - World ideas → World Bible entries
   - Plot ideas → Scene or chapter plans
7. Promoted ideas are marked with a status badge and remain in the Ideas list for reference.

### Notes Panel — Freeform Scratch Space
1. Open Studio Desk → click **Notes** in the left rail (Ideation section).
2. Click **Add Note** to create a new note.
3. Enter title and content — a reminder, writing prompt, or mid-session thought.
4. Notes appear in a list. Click a note to edit its content.
5. **Delete notes:** Click the delete action on any note to remove it permanently.
6. Notes persist across sessions and survive project exports.

### When to Use Ideas vs. Notes
| Use Ideas when | Use Notes when |
|---|---|
| The item might become a character, world entry, or plot point | It's a reminder or scratch thought |
| You want to cluster related concepts | You don't need categorization |
| You plan to promote it into planning objects | It's temporary or personal |

### Example Workflow: Mid-Draft Ideation
1. You're drafting Ch 5 and realize you need a new character for the drone scene.
2. Open the **Ideas** panel → add idea: `"AURA-7 drone with degraded AI — speaks in fragments, carries Moreau's data."`
3. Promote the idea → a Character profile is created for AURA-7 in the Characters panel.
4. Open the **Notes** panel → add note: `"Remember: AURA-7's voice should feel like a broken radio. Check voice consistency in Ch 7."`
5. Return to drafting. The idea is captured, promoted, and the reminder is tracked.

## Phase 5: Research Workflow
Route: Studio Desk (`/workspace/:projectId/studio`) → Research panel

Research is woven throughout the writing process — pre-writing research informs concept development, just-in-time research supports active drafting, and revision research fills discovered gaps. The Research panel manages all three phases in one repository.

### Pre-Writing Research
1. Open Studio Desk → click **Research** in the left rail (Research section).
2. Click **Add Research Item** to create a new entry.
3. Fill in:
   - **Title** — descriptive name for the source (e.g., "Geothermal Energy Primer")
   - **Type** — select from Books, Articles, Papers, Reference Notes
   - **Source URL** — link to the source material (optional but recommended)
   - **Genre Tags** — tag for genre-specific organization (e.g., "science-fiction", "historical")
   - **Notes** — key findings, quotes, or summaries relevant to your project
   - **Citations** — proper citation for nonfiction or academic sources
4. Click **Save**. The item appears in the research list.

### Just-in-Time Research During Drafting
1. While writing in the center editor, open the **Research** panel alongside your manuscript.
2. As you encounter details that need verification (e.g., geothermal generator specifications), create a new research item with your findings.
3. Use the research list as a reference sidebar while drafting — no need to switch contexts.
4. Items can be updated with new findings as your research evolves.

### Revision Research
1. After completing a draft pass, review the **Revision** panel for discovered gaps.
2. For each gap, create a targeted research item to fill the hole.
3. Use the research item's notes field to record the specific detail you looked up.
4. Link research items to scenes/chapters by referencing chapter IDs in notes.

### Managing Research Items
- **Update:** Click an existing item to edit its content. Research evolves as your project does.
- **Archive:** Click the archive action to hide completed research items. Archived items are hidden by default but can be restored by changing status to "active".
- **Browse:** The research list displays all items with type badges, status indicators, and source URLs.

### Genre-Specific Research Patterns
| Genre | Research Focus | Panel Tips |
|-------|---------------|------------|
| **Science Fiction** | Scientific principles, technology, world consistency | Tag items with specific science domains. Cross-reference with World Bible entries. |
| **Fantasy** | Mythology, magic systems, cultural development | Create reference notes for magic rules. Link to world bible entries. |
| **Historical Fiction** | Period details, clothing, speech, technology | Use citations field for source tracking. Tag by time period. |
| **Mystery/Thriller** | Procedures, forensics, investigation methods | Create items for each clue mechanism. Cross-reference with plot beats. |
| **Romance** | Relationship dynamics, emotional authenticity | Tag items by emotional beat or trope. |
| **Nonfiction** | Subject expertise, fact verification | Use citations rigorously. Archive completed fact-checks. |

## Phase 6: Writing Workspace Deep Tour
Routes: `/workspace/:projectId/write` and `/workspace/:projectId/write/:chapterId` (both redirect to `/studio`)

The Writing workspace routes now redirect to Studio Desk. The WritingView component is embedded within StudioView, providing all writing functionality in a unified workspace.

**Accessing writing features:** Navigate to Studio Desk from the left panel's "Studio Desk" link, or use the top banner's stage selector (Planning / Studio / Review).

**Studio Desk provides the same writing capabilities in a floating-panel workspace:**
- Open panels as needed: Drafts, Manuscripts, Ideas, Suggestions, Review, Characters, World Bible, Relationships, Arcs, Canon, Notes, Jobs, and more
- Center: Full-width manuscript editor with manuscript navigation, draft management, and revision suggestions
- Panels can be dragged, resized, snapped together, and pinned to survive layout changes

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

## Phase 8: Revision Workflow
Route: Studio Desk (`/workspace/:projectId/studio`) → Revision panel

Revision is iterative and multi-layered. Authors do not revise once — they revise in passes, each with a different focus. The Revision panel manages structured revision passes with default checklists aligned to the proven revision methodology.

### Creating a Revision Pass
1. Open Studio Desk → click **Revision** in the left rail (Revision section).
2. Click **Create Pass** to start a new revision pass.
3. Select a checklist type:
   - **Structural** — big picture: timeline, pacing, plot holes, character arcs, worldbuilding consistency
   - **Character** — development: motivations, voice consistency, arc progression, flat character rounding
   - **Scene** — pacing: scene-by-scene flow, dialogue, transitions, sensory detail, scene necessity
   - **Line Edit** — prose: word choice, repetitive phrases, sentence variety, cliches, purple prose
   - **Copy Edit** — mechanics: grammar, spelling, punctuation, consistency (eye color, timeline details)
4. The pass appears in the list with status `pending` and a checklist of items.

### Structural Revision (Layer 1 — Big Picture)
1. Read through the entire manuscript with fresh eyes.
2. In the Revision panel, open the **Structural** pass checklist.
3. Work through each item:
   - **Map timeline** — check for contradictions across chapters
   - **Assess pacing** — does the story flow? Identify sags and rushes
   - **Identify plot holes** — logical gaps that break immersion
   - **Evaluate character arcs** — do characters change meaningfully?
   - **Check worldbuilding consistency** — rules established in the world bible
4. Check off items as you complete them. Navigate to the Writing view to make corrections.
5. Use the **Suggestions** panel to get LLM-assisted structural feedback on specific passages.

### Character Revision (Layer 2)
1. Open the **Character** pass checklist.
2. For each character:
   - Verify motivations are clear and consistent
   - Check voice is distinct from other characters
   - Add depth through backstory references and internal conflict
   - Round out flat characters with unique speech patterns, habits, quirks
3. Cross-reference with the **Characters** panel to update profiles based on what you discover during revision.
4. Use canon annotations on Voice Notes fields to enforce character voice in re-generation.

### Scene Revision (Layer 3)
1. Open the **Scene** pass checklist.
2. Work through scenes sequentially:
   - Hone pacing — does each scene move the story forward?
   - Improve dialogue — does it advance plot or deepen character?
   - Strengthen transitions between scenes
   - Add sensory details using the floating toolbar (`Sight & color`, `Sound & rhythm`, etc.)
   - Cut unnecessary scenes or combine overlapping ones
3. Use the **Ideas** panel to capture mid-revision insights about scene reordering.

### Line Edit (Layer 4)
1. Open the **Line Edit** pass checklist.
2. Read the manuscript aloud or use text-to-speech to catch awkward phrasing.
3. Use the floating toolbar:
   - `Tighten & polish` — remove redundancy, improve flow
   - `Compress` — reduce word count while preserving meaning
   - `Rewrite in different voice` — match established tone
4. Fix repetitive phrases and bad habits.
5. Check for consistency in details (eye color, timeline, character names).

### Copy Edit (Layer 5)
1. Open the **Copy Edit** pass checklist.
2. Final grammar, spelling, punctuation pass.
3. Remove any remaining cliches.
4. Verify formatting consistency.

### Tracking Progress
- Each pass shows status: `pending`, `in_progress`, `completed`.
- A completed pass cannot be modified (409 conflict). Create a new pass for additional revisions.
- Use the checklist to track which layers are done and which remain.
- Wait at least a few weeks between finishing the draft and beginning revision when possible — this puts you in a "reader" mindset.

### Revision Loop
1. Complete one layer of revision.
2. Run the checker to find remaining issues.
3. Use **Inspect** to trace problems to their root causes.
4. Annotate canon fields for strict enforcement.
5. Re-run generation for chapters with issues.
6. Repeat until the checker is clean and you've gone from making your writing *better* to merely making it *different*.

## Phase 7: Review Workspace
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

## Phase 8: Inspect Workspace
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

## Phase 9: Canon Workshop
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

## Phase 10: Story Generation Workspace
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

## Phase 11: Studio Desk Workspace
Route: `/workspace/:projectId/studio`

The Studio Desk is a floating-panel workspace for focused writing with immediate access to all planning, generation, and review surfaces. Panels can be dragged, resized, snapped together, and pinned to survive layout changes. Each panel type can only be opened once — clicking again brings the existing panel to front.

### Left Rail (Project Map)
The left rail provides quick access to all panels, organized by workflow stage. Entity count badges display live counts on rail buttons for queryable panels (Characters, World Bible, Relationships, Arcs, etc.), helping you see at a glance how many entities exist in each area.

**Rail Modes:**
- **Expanded (default):** Full-width rail with panel names, section headers, and entity count badges.
- **Compact (icon-only):** Collapses to 64px width, showing only icons with small count overlays. Activates automatically below the `xl:` breakpoint or via the rail toggle button. Frees maximum screen space for writing.
- **Overlay:** Rail overlays the writing area instead of pushing content. Useful for temporary panel access without layout disruption.

Rail mode persists to localStorage and survives page refresh.

### Panel Operations
- **Open a panel:** Click a panel name in the command bar dropdown or left rail.
- **Drag:** Click and drag the panel header to reposition.
- **Resize:** Drag panel edges or corners (240–800px width, 180–600px height).
- **Snap to panel:** Drag a panel near another panel to snap edges together (side-by-side, stacked). Snap threshold is 64px.
- **Snap to edge:** Drag a panel to the workspace edge to snap it flush.
- **Pin:** Click the pin button (📌) to prevent removal. Pinned panels survive layout reset and preset changes.
- **Close:** Click the close button (✕) to remove a panel. Pinned panels cannot be closed.

### Panels (19 types)
- **Suggestions:** Revision suggestions from Manuscript Assist. Accept/reject/archive flows with diff viewer.
- **Ideas:** Brainstorm-style idea capture and clustering.
- **Drafts:** Draft artifact lifecycle management.
- **Manuscripts:** Manuscript document selection and editing.
- **Characters:** Character CRUD with progressive disclosure sections and canon annotations.
- **World Bible:** World entry CRUD with canon annotations.
- **Relationships:** Relationship graph and list views with CRUD operations.
- **Arcs:** Arc candidate management with list/create modes and progressive disclosure sections.
- **Structure:** Sequence, chapter, scene, and beat planning.
- **Chapters:** Chapter plan management and status tracking.
- **Canon:** Canon profile management and packet preview.
- **Generation:** Story generation wizard, run monitoring, gate review.
- **Review:** Checker findings and inspect links.
- **Inspect:** Runtime inspection of pipeline jobs and checker runs.
- **Notes:** Project-level notes with add/delete functionality.
- **Jobs:** Job launch panel with phase selection and recent job monitoring.
- **Research:** Research item management for books, articles, papers, and reference notes. Create, update, and archive research items with source URLs, genre tags, and citations.
- **Revision:** Revision pass lifecycle management. Create structured revision passes with default checklists (structural, character, scene, line_edit, copy_edit). Track pass status from pending to completed.
- **Polish:** Document analysis and export. Analyze manuscripts for readability, passive voice, repetitive words, and style issues. Export in multiple formats with async status polling.

### Rail Sections (6 workflow stages)
- **Ideation:** Ideas, Notes
- **Planning:** Characters, World Bible, Relationships, Arcs, Structure, Chapters
- **Research:** Research
- **Drafting:** Manuscripts, Drafts, Generation
- **Revision:** Revision, Suggestions, Review, Inspect
- **Polish:** Polish, Canon, Jobs

### Layout Presets
Predefined panel layouts accessible via the Layout dropdown in the command bar. Applying a preset preserves pinned panels.

### Keyboard Shortcuts
- `Ctrl+1` through `Ctrl+9`: Switch focus to the 1st through 9th open panel
- `Ctrl+0`: Reset layout (removes all unpinned panels)
- `Escape`: Close all floating panels

### URL Sync
The active panel is reflected in the URL as `?tab=panelKey` (e.g., `?tab=characters`). Deep links work on first load and after refresh.

### Example Workflow: Writing with Context

1. Open Studio Desk from the left panel's "Studio Desk" link.
2. Check entity count badges on the rail — see how many characters, world entries, and arcs you have at a glance.
3. Open the **Characters** panel from the command bar — a floating panel appears with the character list.
4. Open the **Suggestions** panel — position it beside the Characters panel by dragging near its edge.
5. In the center editor, select a paragraph and use the floating toolbar → `Sight & color`.
6. Review the suggestion in the Suggestions panel. Accept to apply, or reject.
7. Mid-chapter, open the **Ideas** panel to capture a new plot idea.
8. Pin the Suggestions panel so it survives layout changes.
9. When done, open the **Jobs** panel to launch a new generation run.
10. Press `Ctrl+0` to reset the layout, keeping pinned panels.

### Example Workflow: Full-Width Writing Session

1. Open Studio Desk — the writing surface fills the viewport.
2. Toggle the rail to **compact mode** (icon-only, 64px) to maximize writing space. Entity count badges remain visible on icons.
3. Open only the panels you need, positioning them around the writing area.
4. Close panels you no longer need by clicking ✕.
5. Use the Layout dropdown to restore a preset arrangement.
6. Toggle the rail back to expanded mode when you need full panel names.

### Example Workflow: Compact Rail for Maximum Writing Space

1. Open Studio Desk.
2. Click the rail toggle button (or resize window below `xl:` breakpoint) to enter compact mode.
3. The rail collapses to 64px, showing only icons with entity count badges.
4. Write with maximum horizontal space. Click any icon to open its panel.
5. Panels open as floating panels; the rail stays compact until you toggle it back.

## Phase 12: Polish and Preparation
Route: Studio Desk (`/workspace/:projectId/studio`) → Polish panel

The final stage transforms a revised manuscript into a polished, submission-ready document. The Polish panel provides automated analysis and multi-format export.

### Document Analysis
1. Open Studio Desk → click **Polish** in the left rail (Polish section).
2. Select a manuscript from the dropdown.
3. Click **Analyze** to run automated checks:
   - **Readability score** — Flesch-Kincaid grade level and readability metrics
   - **Passive voice** — percentage of passive constructions with examples
   - **Repetitive words** — most frequent words beyond acceptable thresholds
   - **Style issues** — sentence length variation, paragraph balance, dialogue tags
4. Review the analysis report. Use the suggestions to target final edits.
5. Return to the Writing view to make corrections flagged by the analysis.
6. Re-run analysis after edits to verify improvements.

### Manuscript Formatting
1. In the Polish panel, select your final manuscript.
2. Choose export format:
   - **Markdown** — for further editing or version control
   - **PDF** — for sharing with beta readers or agents
   - **DOCX** — for traditional publishing submission
   - **Plain Text** — for minimal formatting needs
3. Configure formatting options:
   - Font (serif for print, sans-serif for digital)
   - Line spacing (double-spaced for submission, single for final)
   - Margins and page layout
4. Click **Export** to generate the formatted file.
5. The export runs asynchronously — status polling shows progress.

### Final Checklist
Before submission, verify:
- Readability score matches target audience level
- Passive voice is within acceptable range (<15% for fiction)
- No repetitive word patterns remain
- Manuscript follows industry formatting standards
- Beta reader feedback has been incorporated
- All revision passes are completed

### Export and Archive
1. Return to the home page (`/`).
2. Find your project card → click **Export**.
3. The ZIP archive contains:
   - Project manifest with full metadata
   - Bible database (characters, world entries, arcs, relationships)
   - All manuscript documents
   - Generation run records
   - Canon profiles
   - Checker findings and resolution history
   - Research items and revision pass records
4. Store the archive. Create a backup for version history.

## Phase 13: End-to-End Novel Walkthrough
This phase walks through generating a complete novel from scratch using multi-arc planning, branching, canon management, and iterative generation.

### Overview
We'll build a 12-chapter science fiction novel titled *The Last Lighthouse* with 3 character arcs, 2 sequences (Acts I-II), branching for Act III exploration, and a full canon management workflow. This demonstrates the complete writing process: ideation → planning → research → drafting → revision → polish → export.

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

### Part 1b: Ideation Capture

#### Step 2b: Capture Ideas and Notes
Navigate to Studio Desk → open the **Ideas** and **Notes** panels.

**Ideas panel — capture core concepts:**
1. Add idea: `"Lighthouse keeper in a dying coastal world. Last beacon. Ships that may no longer exist."`
2. Add idea: `"Geothermal generator failing — creates ticking clock."`
3. Add idea: `"Ghost fleet at the end — ambiguous. Never confirm or deny."`
4. Cluster ideas: select all three → cluster creates "core premise" group.
5. Promote the generator idea → creates a World Bible entry for "The Geothermal Generator".

**Notes panel — track writing reminders:**
1. Add note: `"Voice: sparse, atmospheric. No dialogue tags beyond 'said'. Each chapter ends on an image."`
2. Add note: `"Act structure: 3 acts, 12 chapters. Acts I-III = Watch/Signal/Light."`
3. Add note: `"End tone: quiet, not triumphant. Meaning over hope."`

These ideas and notes serve as reference throughout the project. The promoted generator idea is now in the World Bible for formal development.

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

### Part 3: Research

#### Step 5: Build Research Repository
Navigate to Studio Desk → open the **Research** panel.

For a science fiction novel, pre-writing research establishes the factual foundation:

1. **Create research items** for key scientific concepts:
   - **Geothermal Energy Primer** — Type: Reference Notes. Notes: "Geothermal generators use temperature differentials. Fresnel lens design: 1822, Augustin-Jean Fresnel. Typical coastal lighthouse height: 20-100m."
   - **Climate Science Reference** — Type: Articles. Source URL: link to IPCC report. Notes: "Sea level rise: 3.3mm/year average. Coastal cities at risk: NYC, Tokyo, Mumbai."
   - **Radio Communication** — Type: Reference Notes. Notes: "Long-range radio: HF band 3-30 MHz. Signal degradation over 400km. Static patterns from solar activity."
2. Tag items with `science-fiction` genre tag for organization.
3. Use research items as reference during drafting — open the Research panel alongside the manuscript editor.
4. As you discover gaps during drafting, create just-in-time research items to fill holes.

### Part 4: World Bible

#### Step 6: Build World Bible (8 entries)
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

### Part 5: Arc Planning

#### Step 7: Define Character Arcs (3 arcs)
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

### Part 6: Structure Planning

#### Step 8: Plan Sequences and Chapters
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

### Part 7: Canon Management

#### Step 9: Build Canon Profiles
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

### Part 8: Multi-Run Generation

#### Step 10: Generate Act I
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

#### Step 11: Generate Act II
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

#### Step 12: Generate Act III (with branching)
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

### Part 9: Revision

#### Step 13: Multi-Layer Revision
Navigate to Studio Desk → open the **Revision** panel.

**Layer 1 — Structural Revision:**
1. Create a **Structural** revision pass.
2. Read through all 12 chapters. Check:
   - Timeline consistency (generator readings: 23% → 8% → 4% → 12%)
   - Pacing (Act II middle sag between Ch 6-7)
   - Character arc progression (Elara's isolation → choice)
3. Check off structural items as you verify them.

**Layer 2 — Character Revision:**
1. Create a **Character** revision pass.
2. Verify Elara's voice is consistent across all 12 chapters (sparse, atmospheric).
3. Check Moreau's voice is distinct from Elara's (scientific, direct, urgent).
4. Verify AURA-7's dialogue feels fragmented and uncanny.
5. Update character profiles in the **Characters** panel based on discoveries.

**Layer 3 — Scene Revision:**
1. Create a **Scene** revision pass.
2. Work through each chapter:
   - Use `Sight & color` on storm descriptions
   - Use `Show don't tell` on emotional passages
   - Use `Tighten & polish` on repetitive routine descriptions
3. Strengthen transitions between chapters.

**Layer 4 — Line Edit:**
1. Create a **Line Edit** revision pass.
2. Read chapters aloud to catch awkward phrasing.
3. Fix repetitive phrases (e.g., overuse of "silence", "dark", "alone").
4. Improve sentence variety.

**Layer 5 — Copy Edit:**
1. Create a **Copy Edit** revision pass.
2. Final grammar, spelling, punctuation pass.
3. Verify consistency in details (generator percentages, log numbers, timeline).

### Part 10: Polish

#### Step 14: Final Polish
Navigate to Studio Desk → open the **Polish** panel.

1. Select the complete manuscript.
2. Click **Analyze** to run automated checks:
   - Readability score: verify matches adult literary fiction level
   - Passive voice: check percentage is below 15%
   - Repetitive words: identify overused terms
   - Style issues: review sentence length variation
3. Make final corrections flagged by analysis.
4. Re-run analysis to verify improvements.
5. Export in desired format (Markdown, PDF, DOCX).
6. Create project archive for version history.

#### Step 15: Full Novel Review
1. Navigate to **Review** (`/workspace/:projectId/review`).
2. Run the Role Model Checker on the full novel.
3. Review findings:
   - Character voice drift across 12 chapters
   - Canon contradictions (generator readings, timeline consistency)
   - Structural pacing (Act II middle sag, Act III climax)
4. Resolve findings by returning to Writing and making corrections.
5. Use **Inspect** to trace problematic runs to their root causes.

#### Step 16: Canon-Tight Revision Loop
1. Review checker findings.
2. Annotate canon fields in Characters/World Bible tabs for fields that need strict enforcement.
3. Re-run generation for chapters with contradictions.
4. Repeat until checker is clean.

**Concrete example — Generate, change, regenerate:**
1. **Generate:** You generated Ch 7 (The Conversation). Elara speaks to AURA-7.
2. **Discover issue:** Reading the output, AURA-7 sounds too coherent — full sentences, no fragmentation. The conversation reads like two humans talking.
3. **Change the canon:** Navigate to Characters → The Drone (AURA-7). Edit Voice Notes: `"Speech is fragmented. Random pauses. Occasional garbled words. No sentences longer than 8 words. Example: 'The data... says you are last. But the last... is not alone.'"` Save.
4. **Update the generation brief:** Navigate to Generation. Edit the Act III Profile brief to include: `"AURA-7's speech is fragmented, with random pauses and occasional garbled words. It should feel like talking to a broken radio."`
5. **Regenerate:** Re-run generation for Ch 7 with `Block` continuity strictness. The new output has AURA-7 speaking in fragments: `"The sea... rises. 40 meters. You are... the last light."`
6. **Verify:** Read the revised chapter. AURA-7 now sounds like a degrading AI. The conversation feels uncanny.
7. **Continue:** Move to Ch 8. The pattern carries forward — each chapter builds on the corrected voice.

### Part 11: Export and Archive

#### Step 17: Export the Novel
1. Return to home page (`/`).
2. Find project card → Click **Export**.
3. ZIP archive contains:
   - Project manifest with full metadata
   - Bible database (7 characters, 8 world entries, 3 arcs, relationships)
   - 12 manuscript documents (one per chapter)
   - Generation run records (3 runs + branch runs)
   - Canon profiles (3 profiles)
   - Checker findings and resolution history
   - Research items and revision pass records
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
- **Canon management:** Phase 9 (Canon Workshop) — profiles, scope selection, packet preview
- **Cascade Discovery:** Phase 3 (Relationships tab) — auto-extract entities from existing manuscript text
- **Research workflow:** Phase 5 — pre-writing, just-in-time, and revision research
- **Revision workflow:** Phase 8 — multi-layered revision (structural, character, scene, line edit, copy edit)
- **Polish workflow:** Phase 12 — document analysis, formatting, export

## Phase 14: Full Production Workflow

For the complete production workflow order, see **End-to-End Recommended Workflow** in the [User Guide v1.9.0](User%20Guide%20v1.9.0.md). The walkthrough's Phase 13 demonstrates this workflow across a full 12-chapter novel with multi-arc planning, branching, and canon management.

## Common Mistakes and Fixes

- **"I clicked Generate but nothing happened"** — The generation brief is empty or no canon entities are selected. Both are required to enable "Start Generation".
- **"My characters don't appear in the generated output"** — Characters must be selected in the canon scope (Canon Workshop Overview tab or Generation wizard). Being created in the project is not enough.
- **"Suggestions panel is empty"** — You must select text in the editor and trigger an assist action (floating toolbar or Assist dropdown). Then click "Suggestions" in the left rail to view results. The panel doesn't auto-populate.
- **"Project won't export"** — The project needs at least 1 manuscript or draft artifact. Run P-300 Drafter or promote a draft to manuscript first.
- **"Cascade scan returns no entities"** — Manuscript text must be at least 50 characters and contain character names, interactions, or descriptive details. Very short or sparse text yields no results.
- **"Inspect shows 'run not found'"** — The job ID in the URL must match an existing checker run or pipeline job. Navigate from Review → Inspect Run Links or the Job Launch panel to get valid IDs.
- **"Checker finds no findings"** — The checker needs completed runs to analyze. Run at least one pipeline job (P-100 through P-400) before expecting findings.
- **"Research items not appearing"** — Verify the project ID matches. Archived items are hidden by default; change status to "active" to restore visibility.
- **"Revision pass won't update"** — A completed pass cannot be modified (409 conflict). Create a new pass for additional revisions.
- **"Polish analysis shows zero score"** — Ensure manuscript text is at least 10 words for meaningful readability metrics.

## Phase 15: Advanced Iteration Patterns

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
- Floating-panel workspace with command bar + adaptive project rail + embedded WritingView in a two-column composition.
- Panel state is persisted per project (`studio-layout-v1`) and rail width is bounded (80-320px).
- Rail modes: `expanded`, `collapsed`, `overlay` (used for smaller breakpoints).
- Right context panel is removed; review/suggestions/generation/inspect are available as Studio panels.
- Project panels include Suggestions, Ideas, Drafts, Manuscripts, Characters, World Bible, Relationships, Arcs, Structure, Chapters, Canon, Generation, Review, Inspect, Notes, Jobs.
- `?tab=` deep links open/focus panels, and `/workspace/:projectId/write` routes redirect to `/workspace/:projectId/studio`.

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
- Ideas captured and promoted to downstream planning objects (or intentionally skipped).
- Notes used for project reminders and mid-session thoughts.
- At least one manuscript exists and has been revised.
- Research items cataloged (books, articles, references) with citations tracked.
- Revision passes completed (structural, character, scene, line_edit, copy_edit) with checklists checked off.
- Polish analysis run: readability score, passive voice, and style issues reviewed.
- Checker findings have been reviewed.
- At least one inspectable run is present.
- Canon profile/packet has been reviewed.
- At least one generation run completed (and optionally forked).
- Manuscript exported in desired format or project archive captured.
- (Optional) Studio Desk workspace is configured with preferred rail width and active panel.

**Phase 13 (End-to-End Novel Walkthrough)** demonstrates all checklist items across a full novel workflow with multi-arc planning, branching, and canon management.
