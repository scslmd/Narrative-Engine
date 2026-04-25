# Narrative Engine - Complete User Walkthrough

> Purpose: Step-by-step guide to using all features of the Narrative Engine application, starting simple and incrementally building to advanced workflows.
>
> Prerequisites: A working Narrative Engine installation with backend and frontend running. Inference backend (llama.cpp, LM Studio, vLLM, or stub) configured and accessible.

---

## Overview

The Narrative Engine is a narrative compilation system for long-form fiction development. It provides:

- **Story Import** -- paste an existing story and have the LLM auto-extract structured data
- **Project Creation** -- manual project setup with genre, tone, POV, structure
- **Planning** -- hierarchical story planning (sequences, chapters, scenes, beats)
- **Writing** -- manuscript editing with draft management and AI suggestions
- **Review** -- automated review findings and decision management
- **Inspection** -- deep-dive into AI job execution steps, artifacts, and lineage
- **Brain Dump** -- freeform ideation with AI-powered categorization
- **Role Model Checker** -- consistency checking against narrative roles
- **Story Branching** -- alternate story paths, comparison, and merging
- **World Bible** -- canonical world entries with pinning and character cross-references
- **Character Profiles** -- detailed character management with relationship graph
- **Arc Management** -- character arc candidates, selections, and stage maps
- **Flow Editor** -- customizable story development pipeline
- **State-Aware Narrative Controller** -- automatic quality checks during P-300 drafting (context injection, consistency critic, entity intake)

---

## Phase 1: Project Setup

### Step 1: Create or Import a Project

**Route**: `/`

The home screen shows two options:

#### Option A: Create Project (Manual)

1. Click the "Create Project" button to reveal the project form
2. Fill in the fields:
   - **Project Name** -- required, e.g., "The Last Watch"
   - **Genre** -- required, e.g., "Science Fiction"
   - **Tone Profile** -- required, e.g., "Dark and Atmospheric"
   - **Story Structure** -- select from dropdown (Three Act, Hero's Journey, etc.)
   - **Point of View** -- select (First Person, Third Person Limited, etc.)
   - **Primary Language** -- defaults to "English"
   - **Secondary Language** -- optional
   - **Premise** -- optional short description
3. Click "Create Project" to create the project
4. The project card appears in the "Your Projects" grid
5. Click the card to enter the workspace

#### Option B: Import Story (LLM-Assisted)

1. Click the "Import Existing Story" button (green/teal) to open the modal
2. Fill in:
   - **Project Name** -- required
   - **Genre** -- optional (hints to LLM)
   - **Tone** -- optional (hints to LLM)
   - **Story Text** -- paste a completed story (minimum 50 characters)
3. Click "Import Story"
4. The system:
   - Sends the story to the LLM for analysis
   - Extracts characters, world elements, arcs, and foundation data
   - Creates a new project with all extracted data populated
   - Returns a success/failure response with any warnings
5. On success, you are redirected to the project workspace

**Note**: Story Import requires a configured inference backend (llama.cpp, LM Studio, vLLM, etc.). If unavailable, the import will fail with an error message.

---

## Phase 2: Planning Workspace

### Step 2: Explore the Workspace Layout

**Route**: `/workspace/:projectId/plan`

The workspace has three panels:

- **Left Sidebar** -- workspace mode navigation (Plan, Write, Review, Inspect, Brain Dump)
- **Center Panel** -- active view (PlanningView with 12 tabs)
- **Right Panel** -- notes (project-specific sticky notes) and job launch panel

### Step 2a: Manifest View

**Tab**: Manifest

View the project's core configuration:
- Genre, tone profile, POV, story structure, primary language, secondary language
- Premise text
- Constraints defined by the user

This is read-only and reflects the project creation or import data.

### Step 2b: Foundation Editor

**Tab**: Foundation

Set the story's foundational elements:

1. Click "Create Foundation" if none exists
2. Fill in the fields:
   - **Premise** -- the core story premise (1-2 sentences)
   - **Logline** -- a single-sentence summary
   - **Thematic Spine** -- the central theme and how it develops
   - **Emotional Promise** -- what emotional experience the reader should have
   - **Tone and Voice Direction** -- narrative style guidance
   - **Target Audience** -- intended readership
   - **Narrative Constraints** -- any boundaries or rules for the story
   - **Complexity Level** -- simple, moderate, complex, or intricate
   - **Success Definition** -- what "success" looks like for this story
3. Click "Save" to persist the foundation profile

The foundation is used as input by the P-100 Architect job phase.

### Step 2c: Characters

**Tab**: Characters

Manage character profiles:

1. Click "+ New Character" to create a character
2. Fill in the fields:
   - **Display Name** -- the character's name
   - **Role in Story** -- protagonist, antagonist, mentor, etc.
   - **Archetype** -- the hero's journey archetype
   - **External Goal** -- what the character wants to achieve
   - **Internal Need** -- what the character needs to grow
   - **Misbelief or Wound** -- the false belief or past trauma driving behavior
   - **Core Fear** -- what the character fears most
   - **Primary Strength** -- the character's key advantage
   - **Fatal Flaw or Limitation** -- the character's critical weakness
   - **Contradictions** -- conflicting traits that add depth
   - **Backstory Summary** -- key events that shaped the character
   - **Voice Notes** -- how the character speaks/thinks
   - **Secrets** -- hidden information about the character
   - **Values** -- core principles the character holds
   - **Taboos** -- things the character will never do
   - **Change Axis** -- how the character evolves
   - **Arc Stage Notes** -- where the character is in their arc
   - **Continuity Facts** -- immutable facts for consistency
   - **Writer Notes** -- any additional guidance
3. Click "Save" to create or update the character

Characters can be referenced in:
- World Bible entries (via `related_character_ids`)
- Brain Dump sessions (via AI categorization)
- Story Import analysis (auto-extracted)

### Step 2d: World Bible

**Tab**: World Bible

Manage canonical world knowledge:

1. Click "+ New Entry" to create a world bible entry
2. Select the entry type from the dropdown:
   - Characters, Locations, Lore, Magic, Technology, History, Factions, Culture, Economy, Politics, Natural World, Organizations, Artifacts, Events, Concepts, Other
3. Fill in:
   - **Title** -- the entry title (unique per type)
   - **Summary** -- a brief description
   - **Canonical Facts** -- bullet points of immutable truths about this element
   - **Related Character IDs** -- characters associated with this entry
   - **Visibility Scope** -- who can see this (public, internal, private)
   - **Continuity Warnings** -- potential conflicts or red flags
   - **Writer Notes** -- any additional context
4. Click "Save"

Entries can be:
- **Pinned** to the World Bible Rail for quick reference while writing
- Cross-referenced with characters via `related_character_ids`
- Used as context for AI jobs (P-100 Architect references world anchors)

### Step 2e: Planning - Sequence Plans

**Tab**: Planning > Sequence Plans

Create the high-level story structure:

1. Click "+ New Sequence" to create a sequence
2. Fill in:
   - **Name** -- the sequence name (e.g., "Act I: The Call")
   - **Description** -- what happens in this sequence
   - **Kind** -- the sequence type (setup, rising_action, climax, falling_action, resolution, etc.)
   - **Order** -- the sequence's position in the story
   - **Notes** -- any additional planning notes
3. Click "Save"

Sequences form the top level of the planning hierarchy:
```
Sequence > Chapter > Scene > Beat
```

### Step 2f: Planning - Chapter Plans

**Tab**: Planning > Chapter Plans

Create chapters within sequences:

1. Click "+ New Chapter" to create a chapter
2. Fill in:
   - **Name** -- the chapter title
   - **Description** -- what the chapter covers
   - **Sequence ID** -- assign to an existing sequence
   - **Order** -- the chapter's position within the sequence
   - **Word Count Target** -- planned word count
   - **Notes** -- planning notes
3. Click "Save"

### Step 2g: Planning - Scene Plans

**Tab**: Planning > Scene Plans

Create scenes within chapters:

1. Click "+ New Scene" to create a scene
2. Fill in:
   - **Name** -- the scene title
   - **Description** -- what happens in this scene
   - **Chapter ID** -- assign to an existing chapter
   - **Order** -- the scene's position within the chapter
   - **POV Character** -- which character's perspective the scene uses
   - **Notes** -- planning notes
3. Click "Save"

### Step 2h: Planning - Beat Plans

**Tab**: Planning > Beat Plans

Create beats within scenes:

1. Click "+ New Beat" to create a beat
2. Fill in:
   - **Name** -- the beat title
   - **Description** -- the beat's content
   - **Scene ID** -- assign to an existing scene
   - **Order** -- the beat's position within the scene
   - **Emotional Beat** -- the emotional shift this beat creates
   - **Notes** -- planning notes
3. Click "Save"

### Step 2i: Planning - Dependencies

**Tab**: Planning > Dependencies

View and manage dependencies between planning entities. The dependencies view shows:
- Which chapters depend on which sequences
- Which scenes depend on which chapters
- Which beats depend on which scenes
- Cross-entity dependency conflicts

### Step 2j: Planning - Chapter Packets

**Tab**: Planning > Chapter Packets

Create chapter packets that bundle planning data for AI generation:

1. Click "+ New Packet" to create a chapter packet
2. Select:
   - **Chapter ID** -- the chapter to package
   - **Included Elements** -- sequences, characters, world bible entries to include
3. Click "Save"

Chapter packets are used as input for the P-300 Drafter phase when generating manuscript drafts.

### Step 2k: Planning - Storyboard Cards

**Tab**: Planning > Storyboard Cards

Create and manage storyboard cards in a Kanban-style view:

1. Click "+ New Card" to create a storyboard card
2. Fill in:
   - **Title** -- the card title
   - **Content** -- a description of the story element
   - **Column** -- which column to place it in (e.g., "To Do", "In Progress", "Done")
   - **Order** -- position within the column
3. Click "Save"

Cards can be:
- Reordered within columns via the reindex endpoint
- Moved between columns by updating the column field
- Linked to sequence/chapter/scene plans for traceability

### Step 2l: Flow Editor

**Tab**: Flow

Manage the story development pipeline stages:

1. View existing stages (typically: Architect, Sequencer, Drafter, Compiler)
2. **Add Stage** -- click the "+" button to add a new stage
   - Select stage kind
   - Provide a display name
   - Set description
3. **Rename Stage** -- click the pencil icon on any stage
4. **Disable/Enable Stage** -- toggle the stage on/off
5. **Archive Stage** -- click the archive icon to archive (preserves history)
6. **Delete Stage** -- click the delete icon (custom stages only, default stages hidden)
7. **Reorder Stages** -- use drag handles to change execution order

Stages define the pipeline flow for automated story generation.

---

## Phase 3: Arc Management

### Step 3: Arc Candidates

**Tab**: Arcs > Candidates

Identify character arcs to track:

1. Click "+ New Arc Candidate" to create an arc candidate
2. Fill in:
   - **Arc Name** -- a descriptive name for the arc (e.g., "Hero's Journey")
   - **Summary** -- what this arc represents
   - **Project ID** -- automatically set to current project
   - **Character ID** -- which character this arc tracks
   - **Stage Kind** -- the narrative stage type
   - **Notes** -- additional context
3. Click "Save"

Arc candidates are hypotheses about character development that can be:
- **Selected** -- confirmed as the active arc
- **Deselected** -- removed from active consideration
- **Compared** -- visualized against other arc candidates

### Step 3b: Arc Selections

**Tab**: Arcs > Selections

Manage active arc selections:

1. After creating arc candidates, click "Select" on the preferred arc
2. The selection is recorded in the Arcs Selections view
3. Deselect an arc by clicking "Deselect"

### Step 3c: Arc Stage Maps

**Tab**: Arcs > Stage Maps

Define the stage progression for an arc:

1. Click "+ New Stage Map" to create a stage map
2. Select:
   - **Arc** -- which arc candidate this stage map belongs to
   - **Stage Kinds** -- select from the chip buttons (exposition, inciting_incident, rising_action, complication, crisis, climax, falling_action, resolution, etc.)
   - **Order** -- the stage's position
   - **Notes** -- narrative notes for this stage
3. Click "Save"

Stage maps are visualized as an SVG sequential flow diagram with:
- Directional arrows between stages
- Color-coded stage types
- Multi-stage-map support with selector dropdown
- Active arc indicator badge

### Step 3d: Arc Comparisons

**Tab**: Arcs > Comparisons

Compare arc candidates visually:

1. After having multiple arc candidates, create a comparison
2. The comparison is visualized as a graph showing:
   - Arc candidates as nodes
   - Relationships between arcs
   - Similarity metrics

---

## Phase 4: Story Branching

### Step 4: Create Branches

**Tab**: Branches

Manage alternate story paths:

1. Click "Create Branch" to create a new branch
2. Fill in:
   - **Branch Name** -- a descriptive name (e.g., "Alternate Ending")
   - **Branch Point** -- the ID of the branch point in the story
   - **State** -- ACTIVE (default), MERGED, or ARCHIVED
3. Click "Save"

Branches allow you to:
- Explore alternate story directions without modifying the main story
- Compare branches side-by-side
- Make merge decisions to consolidate branches

### Step 4b: Branch Comparisons

**Tab**: Branches > Comparisons

Compare two branches:

1. Select two branches from the comparison form
2. Click "Compare" to generate a comparison analysis
3. The comparison shows differences in:
   - Draft content
   - Planning entities
   - Character development
   - World bible entries

### Step 4c: Merge Decisions

**Tab**: Branches > Merge

Decide whether to merge branches:

1. Select source and target branches
2. Enter a **merge rationale** explaining why you're merging
3. Click "Create Merge Decision"
4. The merge decision is recorded and the source branch state can be updated

---

## Phase 5: Writing Workspace

### Step 5: Manuscript Editing

**Route**: `/workspace/:projectId/write`

The Writing View has three panels:

- **Left** -- Manuscript documents list
- **Center** -- Manuscript editor (main content area)
- **Right** -- Aids panel (revision suggestions, diff viewer)

To write/edit:

1. In the left sidebar, click a manuscript document to select it
2. Edit the content in the main editor
3. The editor shows:
   - Live word count and character count
   - Character count indicator
4. Changes are saved automatically (via the PATCH endpoint)

To create a new manuscript document:

1. Click "Create New Manuscript" (if available)
2. Fill in the title and initial content
3. Click "Save"

### Step 5b: Draft Management

**Draft List (center panel)**:

1. View existing draft artifacts with their titles, content previews, status, and word counts
2. Click a draft to expand its preview
3. Click "+ New Draft" to create a new draft artifact
4. Fill in:
   - **Title** -- the draft title
   - **Content** -- the draft content
   - **Status** -- DRAFT, REVISING, or FINAL
5. Click "Save"

### Step 5c: Draft Promotion

Promote a draft to a manuscript:

1. Find a draft artifact in the draft list
2. Click "Promote to Manuscript" on the draft card
3. Fill in the promotion form:
   - **Target Document Title** -- what to name the resulting manuscript
   - **Content Override** -- optional content to replace the draft
4. Click "Promote"
5. The draft becomes a manuscript document in the left sidebar

### Step 5d: Draft Continuation

Continue an existing draft:

1. Select a draft artifact
2. Click "Continue Draft" to generate additional content
3. The system sends the draft context to the inference backend
4. The continuation is appended to the draft content

### Step 5e: Alternate Variants

Create alternate versions of a draft:

1. Select a draft artifact
2. Click "Create Alternate Variant"
3. Specify the variation (e.g., "Darker tone", "More dialogue")
4. A new draft artifact is created with the variant content

### Step 5f: Revision Suggestions

The right panel shows revision suggestions for the active manuscript:

1. After editing a manuscript, click "Trigger Review" to generate suggestions
2. Suggestions appear in the Aids panel with:
   - Severity level (error, warning, suggestion)
   - Description of the issue
   - Affected text range
3. **Accept** a suggestion to apply it (in-place text replacement)
4. **Reject** a suggestion to dismiss it
  5. Suggestions can be filtered by status (REQUESTED, PENDING, ACCEPTED, REJECTED)

---

## Phase 5g: State-Aware Narrative Controller (Automatic)

When you launch a **P-300 Drafter** job, the State-Aware Narrative Controller runs three automatic quality checks. These run in the background and never block or fail your pipeline.

### Scene Context Injection

**What it does:** Before the drafter sends its prompt to the LLM, the system queries your character profiles and world bible entries and injects them as structured constraints into the prompt.

**What you see:** The generated prose is more consistent with your established characters and world rules because the LLM receives explicit context about:
- Character archetypes (e.g., "reluctant hero")
- Voice notes (e.g., "terse, avoids metaphors")
- External goals and internal needs
- Core fears
- World canonical facts (e.g., "The Athenaeum has seven sub-levels")

**How to prepare:** The more detail you fill in your character profiles (especially voice notes, goals, fears) and world bible entries (canonical facts), the better the injected context will be. Empty fields are silently skipped.

### Consistency Critic

**What it does:** After the draft is generated, a separate LLM pass checks whether each character's dialogue and actions match their profile. If violations are found, the system triggers an automatic rewrite to fix them.

**What you see:** Your final draft has fewer instances of characters speaking out of character or behaving inconsistently with their established traits. The rewrite happens automatically — you don't need to trigger it manually.

**How it works:**
1. The critic receives the draft text and character bios (archetype + voice notes)
2. It checks: voice (word choice, sentence style), behavior (goals, fears, traits), knowledge (what characters should know)
3. If violations are found (up to 3), a rewrite prompt is sent to fix them
4. If the rewrite fails or encounters an error, the original draft is kept

**How to prepare:** Fill in voice notes for your characters. The critic relies on voice notes to detect when dialogue doesn't match established speech patterns. Characters with empty voice notes will produce fewer useful critic flags.

### Entity Intake

**What it does:** Detects new characters that appear in the draft prose but aren't yet in your character profiles. Extracts skeletal profiles (name, inferred archetype, inferred goal) from the character's behavior in the text and saves them to your project.

**What you see:** After a P-300 run, check your **Characters** tab. You may find auto-generated character profiles with:
- **Display Name** -- extracted from the prose
- **Role in Story** -- set to "supporting" (default)
- **Archetype** -- inferred from behavior (e.g., "mysterious ally")
- **External Goal** -- inferred from actions in the scene
- **Writer Notes** -- includes a snippet of the draft where the character appeared

**How it works:**
1. The system extracts proper noun candidates from the draft text
2. It filters out known characters (those already in your profiles) and common non-name words
3. For unknown names (up to 3 per draft), it sends an LLM request to extract archetype and goal from behavior
4. Detected entities are saved as new character profiles with a generated ID (`auto-{name}`)

**How to prepare:** No setup needed. After each P-300 run, review the Characters tab for any auto-detected profiles that need fleshing out (backstory, relationships, arc stages, etc.).

### Error Handling Guarantee

All three checks follow the same rule: **never fail the pipeline**. If any check encounters an error (LLM timeout, database issue, malformed response), the system logs a warning and proceeds with the original draft. Your P-300 job will always complete, even if one or more quality checks fail silently.

---

## Phase 6: Role Model Checker

### Step 6: Run a Checker

**Tab**: Checker

Use the role model checker to verify story consistency:

1. Click "Run Checker" to start a new checker run
2. Select the roles to check (Architect, Sequencer, Drafter, Critic)
3. Click "Start" to submit the check
4. The run status updates in real-time (via polling):
   - PENDING --> PROCESSING --> COMPLETED or FAILED
5. Click on a completed run to view:
   - **Steps** -- individual step records with execution details
   - **Attempts** -- retry history for each step
   - **Lineage** -- artifact lineage graph
   - **Logs** -- execution log entries

The role model checker:
- Validates story elements against defined narrative roles
- Checks consistency between foundation, characters, world bible, and planning
- Produces review findings that appear in the Review workspace

---

## Phase 7: Review Workspace

### Step 7: Review Findings

**Route**: `/workspace/:projectId/review`

The Review View has two tabs:

#### Findings Tab

Review findings generated by:
- The P-400 Compiler phase
- The Role Model Checker
- Manuscript reviews

1. Browse findings filtered by severity:
   - ERROR -- critical issues that must be addressed
   - WARNING -- important concerns
   - SUGGESTION -- optional improvements
2. Click a finding card to expand:
   - The finding description
   - Source object (which story element triggered it)
   - Related inspect run (if applicable)
3. Make a decision on each finding:
   - **Accept** -- acknowledge and address
   - **Reject** -- dismiss the finding
   - **Defer** -- postpone for later consideration
   - **Escalate** -- mark for priority review
   - **Refine** -- request a revised check
4. The decision is recorded and linked to the finding

#### Inspect Run Links Tab

View and manage links between review objects and inspect runs:

1. Browse existing inspect run links
2. Click "New Link" to create a manual link:
   - **Object Kind** -- the type of object (job, checker, manuscript, etc.)
   - **Object ID** -- the ID of the object
   - **Logical Run ID** -- the conceptual run identifier
   - **Run ID** -- the actual job/checker run ID
   - **Run Kind** -- the type of run (pipeline_job or role_model_checker)
3. Click "Save" to create the link

---

## Phase 8: Inspect Workspace

### Step 8: Inspect a Job or Checker Run

**Route**: `/workspace/:projectId/inspect/:jobId`

Deep-dive into AI job execution:

1. Navigate to a specific job/run ID, or
2. Click "Jump to Source" from a review finding
3. The Inspect View shows:
   - **Run Header** -- run ID, run kind, status
   - **Steps Tab** -- timeline of individual execution steps with:
     - Executor name and instance ID
     - Queue delay, claimed/started/finished timestamps
     - Input/output/prompt hashes
     - Finish reason and error details
   - **Artifacts Tab** -- generated artifacts with:
     - Artifact kind (manifest, architect_output, sequence, chapter_1, story_bible)
     - Content preview
     - File path
     - Creation timestamp
   - **Lineage Tab** -- artifact lineage graph showing:
     - Input-output relationships between artifacts
     - Content hashes
     - Supersession chains
   - **Logs Tab** -- execution log entries with:
     - Timestamp
     - Log level (INFO, WARNING, ERROR)
     - Message

From the Inspect View, you can:
- Click "Back to Manuscript" to return to the Writing view
- Retry a failed run (via the retry endpoint)
- View the run's full attempt history

---

## Phase 9: Brain Dump

### Step 9: Brain Dump Session

**Route**: `/workspace/:projectId/braindump`

Freeform ideation with AI-powered organization:

1. Start with a blank canvas (or an existing session)
2. Write raw thoughts, ideas, plot points, character notes in the canvas
3. No structure needed -- just write freely
4. When done, click "Organize" to have the LLM categorize the text

Organize results appear as:
- **Categorized items** grouped by type (characters, locations, plot-points, etc.)
- **Item cards** showing the extracted element with its category
- **Continue Editing** button to return to the draft canvas

From the organized results, you can:
- Create brainstorm items from categorized content
- Create world bible entries
- Create character profiles
- Add to foundation profiles

---

## Phase 10: Brainstorm

### Step 10: Brainstorm Items

**Tab**: Brainstorm (in PlanningView)

Manage brainstorm items and clusters:

1. Click "+ New Item" to create a brainstorm item
2. Fill in:
   - **Content** -- the brainstorm idea
   - **Kind** -- the type of idea (plot, character, setting, theme, etc.)
   - **Notes** -- additional context
3. Click "Save"

### Step 10b: Cluster Items

Group related brainstorm items:

1. Select multiple brainstorm items
2. Click "Cluster" to group them together
3. The cluster is created with a generated title based on the items' common themes

---

## Phase 11: Decisions

### Step 11: Decision Tree

**Tab**: Decisions

View the story decision hierarchy:

1. The Decision Tree view shows:
   - Decision nodes with their parent-child relationships
   - Decision paths (the lineage of decisions leading to a point)
   - Decision metadata (timestamps, authors, reasons)
2. Click a decision node to see:
   - The decision text
   - The options that were considered
   - The rationale for the chosen option
   - Related findings and inspect runs

---

## Advanced Workflows

### Workflow A: Full Story Pipeline (Automated Generation)

After setting up foundation, characters, and world bible:

1. **Run P-100 Architect** -- generates the story architecture foundation (markdown)
2. **Run P-200 Sequencer** -- generates the sequence plan (JSON) using P-100 output
3. **Run P-300 Drafter** -- generates chapter drafts with automatic quality checks:
   - Scene Context Injection feeds character profiles and world facts into the prompt
   - Consistency Critic verifies character voice and behavior, triggers rewrite on violations
   - Entity Intake detects new characters in draft prose and auto-extracts skeletal profiles
4. **Check Characters tab** -- review any auto-detected character profiles from Entity Intake
5. **Run P-400 Compiler** -- generates the story bible snapshot (JSON) using all prior outputs
6. **Review findings** from P-400 and make decisions
7. **Iterate** -- update foundation or world bible, re-run phases as needed

Each phase is triggered via the Job Launch panel (right sidebar) by selecting the phase and clicking "Launch".

### Workflow B: Brain Dump to Structured Project

1. Go to **Brain Dump** tab
2. Write raw ideas freely (characters, settings, plot points, themes)
3. Click **Organize** to have the LLM categorize the content
4. Review the categorized results
5. Navigate to **Planning** workspace:
   - **Foundation** tab -- create foundation from organized themes
   - **Characters** tab -- create characters from organized character entries
   - **World Bible** tab -- create world entries from organized setting entries
   - **Arcs** tab -- create arc candidates from organized plot arc ideas
6. Run the **Full Story Pipeline** (P-100 through P-400)
7. **Review** findings and iterate

### Workflow C: Story Branching and Comparison

1. In the **Planning** workspace, establish a baseline plan (sequences, chapters, scenes)
2. Go to **Branches** tab
3. Create a branch with a descriptive name (e.g., "Alternative Climax")
4. Edit the manuscript in **Write** workspace for this branch
5. Create new planning entities (alternate sequences, chapters)
6. Go back to **Branches** tab and create a comparison between branches
7. Review the comparison
8. If satisfied, create a **merge decision** to consolidate the branch

### Workflow D: Character Arc Development

1. Create characters in the **Characters** tab
2. In the **Arcs** tab, create arc candidates for each character
3. Define stage maps with narrative progression chips
4. Run the **Role Model Checker** to verify character consistency
5. Review findings in the **Review** workspace
6. Make decisions on character arc issues
7. Update character profiles based on review feedback
8. Iterate

### Workflow E: Manuscript Review Cycle

1. Write/edit manuscript content in the **Writing** workspace
2. Click **Trigger Review** to generate revision suggestions
3. Review suggestions in the **Aids** panel
4. Accept/reject individual suggestions
5. Run the **Role Model Checker** for deeper consistency analysis
6. Review findings in the **Review** workspace
7. Make decisions on each finding
8. Inspect checker runs via the **Inspect** workspace for detailed analysis
9. Iterate until satisfied

---

## UI Features and Utilities

### Theme Switching

Toggle between themes via the header:
- Light, Dark, Midnight, Forest, Ocean

### Project Notes

The right panel includes a notes area:
- Create, edit, and delete project-specific notes
- Notes are persisted in localStorage
- Notes persist across workspace mode switches

### Job Monitor

The bottom utility layer shows:
- Active job status (PENDING, RUNNING, COMPLETED, FAILED)
- Progress indicator for long-running jobs
- Toggle to show/hide the job monitor bar

### Settings

Configure user preferences via the settings menu:
- Icon mode (labels, icons-small, icons-large)
- Show tooltips (toggle)
- Theme selection

### Toast Notifications

- Success messages for create/update operations
- Error messages for failed operations
- Auto-dismiss after 5 seconds
- Manually dismissible

---

## Troubleshooting

### Inference Backend Unavailable

If the inference backend (llama.cpp, LM Studio, vLLM) is not running:
- Story Import will fail with an error
- Job creation (P-100 through P-400) will fail
- Role Model Checker runs will fail
- Brain Dump organization will fail
- The system falls back to stub mode if configured

### Project Import Issues

- Story text must be at least 50 characters
- The LLM must return valid JSON matching the import schema
- At least one character must be extracted
- Genre and tone values that don't match enum values are silently skipped (warning in response)

### Job Failure Recovery

- Failed jobs can be retried via the Inspect view's "Retry" button
- Retries use the same input but may use a different inference provider
- Step records and lineage are preserved for inspection

### Narrative Controller Issues

- **Drafts don't seem to use character context.** Check that your character profiles have filled-in fields (archetype, voice notes, goals, fears). Empty fields are not injected. The system falls back to the first 5 characters if no active character IDs are specified for a scene.
- **Consistency critic isn't catching out-of-character dialogue.** Ensure voice notes are specific (e.g., "terse, avoids metaphors" rather than "normal"). Vague voice notes produce vague critic checks.
- **Too many auto-detected characters.** The entity intake stop-word list filters common non-name words, but some false positives may slip through (e.g., "Morning", "Shadow"). Review the Characters tab after each P-300 run and delete any spurious entries.
- **Drafts take longer to generate.** The narrative controller adds 1-5 extra LLM calls per draft (critic check + optional rewrite + up to 3 entity intake calls). This is intentional for quality. Use the stub backend for faster iteration during early exploration.

### Branch State Management

- ACTIVE branches can be edited
- MERGED branches are read-only (consolidated into target)
- ARCHIVED branches are preserved for reference but not editable
