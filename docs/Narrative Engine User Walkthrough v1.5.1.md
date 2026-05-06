# Narrative Engine - Complete User Walkthrough v1.6.0

> Purpose: Step-by-step guide to using all features of the Narrative Engine application, starting simple and incrementally building to advanced workflows.
>
> Prerequisites: A working Narrative Engine installation with backend and frontend running. Inference backend (llama.cpp, LM Studio, vLLM, or stub) configured in `.env` and accessible. If using a cloud provider (OpenAI, Anthropic, Gemini), set `NARRATIVE_INFERENCE_API_KEY` — see **User Guide §Configure Your Model**. If your server has `NARRATIVE_API_KEY` set for endpoint protection, create an API key in Settings for features like Brain Dump, Canon Workshop, and Story Generation (see **User Guide §Authentication**).
>
> Recommended reading order: Follow the phases sequentially. Use the **User Guide** (`User Guide v1.6.0.md`) for feature reference and detailed explanations.

---

## Overview

The Narrative Engine is a narrative compilation system for long-form fiction development. It provides:

- **Pattern Extraction** -- paste any story or mythology text and extract storytelling DNA to seed a new project
- **Story Import** -- paste an existing story and have the LLM auto-extract structured data
- **Project Export/Import** -- create ZIP archive backups and restore projects on other installations
- **Project Creation** -- manual project setup with genre, tone, POV, structure
- **Brain Dump** -- freeform ideation with AI-powered categorization
- **Planning** -- hierarchical story planning (sequences, chapters, scenes, beats)
- **Writing** -- manuscript editing with draft management and AI suggestions
- **Manuscript LLM Assist** -- interactive AI editing: line edits, expansions, canon checks, forks
- **Review** -- automated review findings and decision management
- **Inspection** -- deep-dive into AI job execution steps, artifacts, and lineage
- **Role Model Checker** -- consistency checking against narrative roles
- **Story Branching** -- alternate story paths, comparison, and merging
- **World Bible** -- canonical world entries with pinning and character cross-references
- **Character Profiles** -- detailed character management with relationship graph
- **Arc Management** -- character arc candidates, selections, and stage maps
- **Flow Editor** -- customizable story development pipeline
- **State-Aware Narrative Controller** -- automatic quality checks during P-300 drafting
- **Canon Workshop** -- edit canon material, mark fields locked/mutable/forbidden, create generation profiles
- **Story Generation Orchestration** -- generate new canon-congruent stories; fork into new projects; 4-phase pipeline with consistency gates

---

## How to Use This Walkthrough

This walkthrough follows the **creative lifecycle**: seed your project, ideate, plan, write, polish, then generate new stories. Follow the phases in order for the best learning experience. Each phase includes:

- **Route** — the URL path in the frontend
- **Step-by-step instructions** — what to click and fill in
- **"What you see"** — what the UI shows after each action
- **Troubleshooting** — common issues and fixes (at the end)

For deeper feature explanations, cross-reference the **User Guide** (`User Guide v1.6.0.md`).

---

## Table of Contents

### Getting Started

- [Phase 0: Getting Sample Stories](#phase-0-getting-sample-stories)
- [Phase 1: Project Setup](#phase-1-project-setup)
  - [Option A: Create Project (Manual)](#option-a-create-project-manual)
  - [Option B: Import Story (LLM-Assisted)](#option-b-import-story-llm-assisted)
  - [Option C: Extract Patterns (Pattern-Based Seed)](#option-c-extract-patterns-pattern-based-seed)
- [Phase 1b: Extraction Results](#phase-1b-extraction-results-optional)

### Ideation

- [Phase 2: Brain Dump](#phase-2-brain-dump)
- [Phase 3: Brainstorm](#phase-3-brainstorm)

### Planning and Setup

- [Phase 4: Planning Workspace](#phase-4-planning-workspace)
  - [Manifest, Foundation, Characters, World Bible](#step-4a-manifest-view)
  - [Sequence, Chapter, Scene, Beat Plans](#step-4e-planning---sequence-plans)
  - [Dependencies, Chapter Packets, Storyboard Cards](#step-4i-planning---dependencies)
  - [Flow Editor](#step-4l-flow-editor)
- [Phase 5: Arc Management](#phase-5-arc-management)

### Writing and AI Assistance

- [Phase 6: Writing Workspace](#phase-6-writing-workspace)
  - [Manuscript Editing, Draft Management, Promotion](#step-6-manuscript-editing)
  - [Draft Continuation, Alternate Variants, Revision Suggestions](#step-6d-draft-continuation)
- [Phase 6g: State-Aware Narrative Controller](#phase-6g-state-aware-narrative-controller-automatic)
- [Phase 6h: Multi-Chapter Generation](#phase-6h-multi-chapter-generation)
- [Phase 6i: Manuscript LLM Assist](#phase-6i-manuscript-llm-assist)

### Quality and Review

- [Phase 7: Role Model Checker and Review](#phase-7-role-model-checker-and-review)
- [Phase 8: Inspect Workspace](#phase-8-inspect-workspace)

### Advanced Generation

- [Phase 9: Canon Workshop](#phase-9-canon-workshop)
- [Phase 10: Story Generation Orchestration](#phase-10-story-generation-orchestration)

### Project Lifecycle

- [Phase 11: Story Branching](#phase-11-story-branching)
- [Phase 12: Exporting and Importing Projects](#phase-12-exporting-and-importing-projects)

### Reference

- [Advanced Workflows (A–F)](#advanced-workflows)
- [UI Features and Utilities](#ui-features-and-utilities)
- [Troubleshooting](#troubleshooting)

---

## Phase 0: Getting Sample Stories

Before you begin the walkthrough, you may want sample stories to import and test with. Four sample stories are provided in `docs/sample-stories/`:

### Available Sample Stories

| Story | Author | Genre | Size | Format | Import Mode |
|-------|--------|-------|------|--------|-------------|
| The Time Machine | H.G. Wells | Classic Sci-Fi | ~200 KB (~30K words) | Plain text (Project Gutenberg) | Multi-pass |
| The Picture of Dorian Gray | Oscar Wilde | Gothic Fiction | ~455 KB (~75K words) | Plain text (Project Gutenberg) | Multi-pass |
| The Last Archive | Original | Science Fiction | ~28 KB (~5K words) | Markdown | Single-pass |
| Crossing Limits | Original | Pop-Romance | ~30 KB (~5K words) | Markdown | Multi-pass |

Three of the four stories exceed the 30,000-character threshold for single-pass import, which exercises the **multi-pass import pipeline**. The Last Archive (~28K chars) exercises single-pass import instead.

### How to Import a Sample Story

1. Open your preferred text editor and load one of the sample story files from `docs/sample-stories/`
2. Select all text (Ctrl+A / Cmd+A) and copy it (Ctrl+C / Cmd+C)
3. In the Narrative Engine frontend, navigate to the home screen (`/`)
4. Click **"Import Existing Story"** (green/teal button)
5. Fill in:
   - **Project Name** -- e.g., "The Time Machine" or "The Last Archive"
   - **Genre** -- optional hint for the LLM (e.g., "Science Fiction", "Gothic Fiction")
   - **Tone** -- optional hint (e.g., "Classic", "Dark and Atmospheric")
   - **Story Text** -- paste the copied story text
6. Click **"Import Story"**
7. The system will:
   - Detect that the story exceeds the single-pass threshold (if applicable)
   - Route to multi-pass import: structure detection, per-chapter analysis, character/world/arc consolidation
   - Create a new project with all extracted data populated
   - Return a success response when complete
8. On success, you'll be redirected to the project workspace

**Note**: Import requires a configured inference backend (llama.cpp, LM Studio, vLLM, or stub). Large stories may take several minutes to process through multi-pass import.

### Expected Extraction Results

#### The Time Machine
- **Characters**: 6+ (Time Traveller, Weena, Eloi collective, Morlocks, Filby, frame narrator)
- **World Bible**: 8+ entries (Year 802,701 AD, Time Machine technology, Eloi/Morlock societies, class evolution theme, Victorian London frame)
- **Arcs**: 3 (class divergence, exploration/discovery, survival/rescue)

#### The Picture of Dorian Gray
- **Characters**: 8+ (Dorian Gray, Lord Henry Wotton, Basil Hallward, Sibyl Vane, Allan Chambers, James Vane)
- **World Bible**: 10+ entries (Victorian London high society, aestheticism philosophy, portrait's magical properties, opium dens, moral decay theme)
- **Arcs**: 4 (corruption, consequence, pursuit, redemption/despair)

#### The Last Archive
- **Characters**: 6 (Miren Kael, Joss Vallen, Tessa Rowan, Ravi Chen, Director Hale, Echo/collective consciousness)
- **World Bible**: 10+ entries (memory crystals, extraction process, Chronos interface, Grand Archive, Understack, Three Laws of Memory, Identity Drift, Erasure Protocol, Echo Fragments, New Geneva)
- **Arcs**: 3 (discovery, conflict with Council, Chronos resolution)

#### Crossing Limits
- **Characters**: 7 (Elara Voss, Kai Mercer, Dr. Nadia Chen, Mira Voss, The Keeper, Prof. Ashworth, The Guide)
- **World Bible**: 8+ entries (book-worlds concept, Crossing Limit Rule, Athenaeum, reality degradation, anchor points, Sealed Collection, book-world ethics, merge threat)
- **Arcs**: 3 (romance, mystery of destabilization, rescue/stabilization)

### Bridge to Phase 1

After importing a sample story, you'll be in the project workspace. Proceed to [Phase 1](#phase-1-project-setup) to explore the imported data, or skip directly to [Phase 4](#phase-4-planning-workspace) to review the extracted planning structure.

---

## Phase 1: Project Setup

### Step 1: Create or Import a Project

**Route**: `/`

The home screen shows three ways to start a project:

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

#### Option C: Extract Patterns (Pattern-Based Seed)

Pattern Extraction lets you paste any story or mythology text and extract its storytelling DNA — archetypal patterns, narrative structure, voice profile, thematic constraints, and entities — then use those patterns to guide original story generation.

1. Click the "Import Existing Story" button to open the modal, then toggle to "Extract Patterns" mode
2. Fill in:
   - **Project Name** -- required, name for the new project
   - **Source Type** -- select one:
     - **Narrative** — fiction stories; includes voice profile, narrative pattern, and thematic constraints
     - **Mythology** — mythological texts; extracts archetypal patterns, cosmic rules, symbolic motifs
   - **Generation Mode** -- select one:
     - **Same World** — keep the source story's world, create original characters following extracted patterns
     - **New Characters** — same world, original cast fulfilling extracted archetypes (narrative source only)
     - **Transposed** — map patterns and voice to a new setting (maximum creative freedom)
   - **Source Corpus** -- optional label (e.g., "Dune", "Greek Mythology")
   - **Story Text** -- paste any completed story or mythology text (up to 24,000 characters)
3. Click "Extract Patterns"
4. The system:
   - Analyzes your text via LLM
   - Extracts patterns, structure, voice, constraints, and entities
   - Creates a project with foundation profile, world bible entries, character archetypes, and narrative-specific fields
   - Returns a success/failure response
5. On success, you are redirected to the project workspace

**Note**: Pattern Extraction requires a configured inference backend. Source type determines which extraction pipeline is used: Narrative for fiction stories with voice profile extraction, Mythology for mythological texts.

---

## Phase 1b: Extraction Results (Optional)

If you used Pattern Extraction as your project seed, the following will be pre-populated when you enter the workspace:

- **Foundation Editor** -- thematic spine, emotional promise, tone direction derived from source material
- **World Bible** -- world rules and symbolic motifs as concept entries
- **Character Builder** -- archetypal pattern carriers available as templates
- **Voice Profile** -- extracted narrative voice, sentence rhythm, descriptive density, humor level, emotional temperature (narrative source type only)
- **Narrative Pattern** -- pacing, chapter structure, conflict type, dialogue style, scene transition (narrative source type only)
- **Thematic Constraints** -- themes with moral stances, recurring questions, forbidden elements (narrative source type only)
- **P-100 Architect** -- applies pattern context based on generation mode
- **P-300 Drafter** -- uses SceneContext's `pattern_guidance` and `author_prompt` for pattern-informed drafting

### Troubleshooting Extraction

| Issue | Solution |
|-------|----------|
| Extraction returns no patterns | Ensure text is 2,000+ characters and includes diverse scenes |
| Voice profile not extracted | Use source_type = "narrative" for fiction stories; mythology does not extract voice profiles |
| Wrong generation mode | Same World for in-universe stories, New Characters for original cast, Transposed for adapted settings |
| Partial results | Retry — the LLM may extract more patterns on a second pass |

From here, proceed to [Phase 2](#phase-2-brain-dump) (Brain Dump) to add your own ideas, or to [Phase 4](#phase-4-planning-workspace) (Planning) to refine the extracted data.

---

## Phase 2: Brain Dump

> **Bridge from Phase 1:** After creating or importing your project, the first step in adding your own creative input is freeform ideation. Brain Dump captures raw ideas before you organize them into structured elements.
>
> **Authentication note:** Brain Dump uses API endpoints that require an API key if your server has `NARRATIVE_API_KEY` set. If you see "API key required" or the view stays on "Loading...", follow the setup in **User Guide §Authentication**.

**Route**: `/workspace/:projectId/braindump`

Freeform ideation with AI-powered organization:

1. Start with a blank canvas (or an existing session)
2. Write raw thoughts, ideas, plot points, character notes in the canvas
3. No structure needed -- just write freely
4. When done, click **"Organize"** to have the LLM categorize the text

Organize results appear as:
- **Categorized items** grouped by type (characters, locations, plot-points, etc.)
- **Item cards** showing the extracted element with its category
- **Continue Editing** button to return to the draft canvas

From the organized results, you can:
- Create brainstorm items from categorized content
- Create world bible entries from setting entries
- Create character profiles from character entries
- Add to foundation profiles from thematic entries

### Tips

- Use Brain Dump liberally — capture raw ideas first, organize them later
- Don't self-censor at the ideation stage
- Run Organize multiple times as you add more content
- Organized items feed into the Planning workspace (Foundation, Characters, World Bible tabs)

---

## Phase 3: Brainstorm

> **Bridge from Phase 2:** After organizing your Brain Dump, convert categorized ideas into structured brainstorm items that can be clustered and promoted to planning elements.

**Tab**: Brainstorm (in PlanningView)

Manage brainstorm items and clusters:

1. Click "+ New Item" to create a brainstorm item
2. Fill in:
   - **Content** -- the brainstorm idea
   - **Kind** -- the type of idea (plot, character, setting, theme, etc.)
   - **Notes** -- additional context
3. Click "Save"

### Cluster Items

Group related brainstorm items:

1. Select multiple brainstorm items
2. Click "Cluster" to group them together
3. The cluster is created with a generated title based on the items' common themes

---

## Phase 4: Planning Workspace

> **Bridge from Phase 3:** After ideating and brainstorming, it's time to structure your story. If you imported a story or used Pattern Extraction, many of these fields are pre-populated — review and refine them before launching AI jobs.

### Step 4: Explore the Workspace Layout

**Route**: `/workspace/:projectId/plan`

The workspace has three panels:

- **Left Sidebar** -- workspace mode navigation (Plan, Write, Review, Inspect, Brain Dump)
- **Center Panel** -- active view (PlanningView with 12 tabs)
- **Right Panel** -- notes (project-specific sticky notes) and job launch panel

### Step 4a: Manifest View

**Tab**: Manifest

View the project's core configuration:
- Genre, tone profile, POV, story structure, primary language, secondary language
- Premise text
- Constraints defined by the user

This is read-only and reflects the project creation or import data.

### Step 4b: Foundation Editor

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

### Step 4c: Characters

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
   - **Voice Notes** -- how the character speaks/thinks (critical for consistency checking)
   - **Secrets** -- hidden information about the character
   - **Values** -- core principles the character holds
   - **Taboos** -- things the character will never do
   - **Change Axis** -- how the character evolves
   - **Continuity Facts** -- immutable facts for consistency
   - **Writer Notes** -- any additional guidance
3. Click "Save" to create or update the character
4. Use the **Relationships** section to define connections between characters

### Step 4d: World Bible

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

### Step 4e: Planning - Sequence Plans

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

### Step 4f: Planning - Chapter Plans

**Tab**: Planning > Chapter Plans

Create chapters within sequences:

1. Click "+ New Chapter" to create a chapter
2. Fill in:
   - **Name** -- the chapter title
   - **Description** -- what the chapter covers
   - **Sequence ID** -- assign to an existing sequence
   - **Order** -- the chapter's position within the sequence
   - **Word Count Target** -- planned word count
   - **Active Character IDs** -- characters who appear in this chapter (keeps P-300 prompts focused)
   - **Notes** -- planning notes
3. Click "Save"

### Step 4g: Planning - Scene Plans

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

### Step 4h: Planning - Beat Plans

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

### Step 4i: Planning - Dependencies

**Tab**: Planning > Dependencies

View and manage dependencies between planning entities. The dependencies view shows:
- Which chapters depend on which sequences
- Which scenes depend on which chapters
- Which beats depend on which scenes
- Cross-entity dependency conflicts

### Step 4j: Planning - Chapter Packets

**Tab**: Planning > Chapter Packets

Create chapter packets that bundle planning data for AI generation:

1. Click "+ New Packet" to create a chapter packet
2. Select:
   - **Chapter ID** -- the chapter to package
   - **Included Elements** -- sequences, characters, world bible entries to include
3. Click "Save"

Chapter packets are used as input for the P-300 Drafter phase when generating manuscript drafts.

### Step 4k: Planning - Storyboard Cards

**Tab**: Planning > Storyboard Cards

Create and manage storyboard cards in a Kanban-style view:

1. Click "+ New Card" to create a storyboard card
2. Fill in:
   - **Title** -- the card title
   - **Content** -- a description of the story element
   - **Column** -- which column to place it in (e.g., "To Do", "In Progress", "Done")
   - **Order** -- position within the column
3. Click "Save"

Cards can be reordered within columns, moved between columns, and linked to planning entities for traceability.

### Step 4l: Flow Editor

**Tab**: Flow

Manage the story development pipeline stages:

1. View existing stages (typically: Architect, Sequencer, Drafter, Compiler)
2. **Add Stage** -- click the "+" button to add a new stage
3. **Rename Stage** -- click the pencil icon on any stage
4. **Disable/Enable Stage** -- toggle the stage on/off
5. **Archive Stage** -- click the archive icon to archive (preserves history)
6. **Delete Stage** -- click the delete icon (custom stages only, default stages hidden)
7. **Reorder Stages** -- use drag handles to change execution order

---

## Phase 5: Arc Management

### Step 5: Arc Candidates

**Tab**: Arcs > Candidates

Identify character arcs to track:

1. Click "+ New Arc Candidate" to create an arc candidate
2. Fill in:
   - **Arc Name** -- a descriptive name for the arc (e.g., "Hero's Journey")
   - **Summary** -- what this arc represents
   - **Character ID** -- which character this arc tracks
   - **Stage Kind** -- the narrative stage type
   - **Notes** -- additional context
3. Click "Save"

Arc candidates are hypotheses about character development that can be:
- **Selected** -- confirmed as the active arc
- **Deselected** -- removed from active consideration
- **Compared** -- visualized against other arc candidates

### Step 5b: Arc Selections

**Tab**: Arcs > Selections

1. After creating arc candidates, click "Select" on the preferred arc
2. The selection is recorded in the Arcs Selections view
3. Deselect an arc by clicking "Deselect"

### Step 5c: Arc Stage Maps

**Tab**: Arcs > Stage Maps

Define the stage progression for an arc:

1. Click "+ New Stage Map" to create a stage map
2. Select:
   - **Arc** -- which arc candidate this stage map belongs to
   - **Stage Kinds** -- select from the chip buttons (exposition, inciting_incident, rising_action, complication, crisis, climax, falling_action, resolution, etc.)
   - **Order** -- the stage's position
   - **Notes** -- narrative notes for this stage
3. Click "Save"

Stage maps are visualized as an SVG sequential flow diagram with directional arrows, color-coded stage types, and active arc indicator badges.

### Step 5d: Arc Comparisons

**Tab**: Arcs > Comparisons

1. After having multiple arc candidates, create a comparison
2. The comparison is visualized as a graph showing arc candidates as nodes, relationships between arcs, and similarity metrics

---

## Phase 6: Writing Workspace

> **Bridge from Phase 5 (Arcs):** With your story planned, launch P-300 Drafter jobs from the Job Launch panel to generate chapter drafts. Then use the Writing workspace to edit and Manuscript Assist (Phase 6i) to polish them.

### Step 6: Manuscript Editing

**Route**: `/workspace/:projectId/write`

The Writing View has three panels:

- **Left** -- Manuscript documents list
- **Center** -- Manuscript editor (main content area)
- **Right** -- Aids panel (revision suggestions, diff viewer)

To write/edit:

1. In the left sidebar, click a manuscript document to select it
2. Edit the content in the main editor
3. The editor shows live word count and character count
4. Changes are saved automatically (via the PATCH endpoint)

To create a new manuscript document:

1. Click "Create New Manuscript" (if available)
2. Fill in the title and initial content
3. Click "Save"

### Step 6b: Draft Management

**Draft List (center panel)**:

1. View existing draft artifacts with their titles, content previews, status, and word counts
2. Click a draft to expand its preview
3. Click "+ New Draft" to create a new draft artifact
4. Fill in title, content, and status (DRAFT, REVISING, or FINAL)
5. Click "Save"

### Step 6c: Draft Promotion

Promote a draft to a manuscript:

1. Find a draft artifact in the draft list
2. Click "Promote to Manuscript" on the draft card
3. Fill in the promotion form:
   - **Target Document Title** -- what to name the resulting manuscript
   - **Content Override** -- optional content to replace the draft
4. Click "Promote"
5. The draft becomes a manuscript document in the left sidebar

### Step 6d: Draft Continuation and Alternate Variants

**Continue a draft:**
1. Select a draft artifact
2. Click "Continue Draft" to generate additional content
3. The continuation is appended to the draft content

**Create alternate variants:**
1. Select a draft artifact
2. Click "Create Alternate Variant"
3. Specify the variation (e.g., "Darker tone", "More dialogue")
4. A new draft artifact is created with the variant content

### Step 6e: Revision Suggestions

The right panel shows revision suggestions for the active manuscript:

1. After editing a manuscript, click "Trigger Review" to generate suggestions
2. Suggestions appear in the Aids panel with severity level, description, and affected text range
3. **Accept** a suggestion to apply it (in-place text replacement)
4. **Reject** a suggestion to dismiss it
5. Suggestions can be filtered by status (REQUESTED, PENDING, ACCEPTED, REJECTED)

---

## Phase 6g: State-Aware Narrative Controller (Automatic)

When you launch a **P-300 Drafter** job, the State-Aware Narrative Controller runs three automatic quality checks. These run in the background and never block or fail your pipeline.

### Scene Context Injection

**What it does:** Before the drafter sends its prompt to the LLM, the system queries your character profiles and world bible entries and injects them as structured constraints into the prompt.

**What you see:** The generated prose is more consistent with your established characters and world rules because the LLM receives explicit context about character archetypes, voice notes, goals, fears, world canonical facts, pattern guidance (if project was seeded via Pattern Extraction), and per-chapter author direction.

**How to prepare:** The more detail you fill in your character profiles (especially voice notes, goals, fears) and world bible entries (canonical facts), the better the injected context will be. Empty fields are silently skipped.

### Consistency Critic

**What it does:** After the draft is generated, a separate LLM pass checks whether each character's dialogue and actions match their profile. If violations are found, the system triggers an automatic rewrite to fix them.

**What you see:** Your final draft has fewer instances of characters speaking out of character or behaving inconsistently. The rewrite happens automatically.

**How to prepare:** Fill in voice notes for your characters. The critic relies on voice notes to detect when dialogue doesn't match established speech patterns.

### Entity Intake

**What it does:** Detects new characters that appear in the draft prose but aren't yet in your character profiles. Extracts skeletal profiles (name, inferred archetype, inferred goal) and saves them to your project.

**What you see:** After a P-300 run, check your **Characters** tab. You may find auto-generated character profiles with extracted names, inferred archetypes, and inferred goals.

**How to prepare:** No setup needed. After each P-300 run, review the Characters tab for any auto-detected profiles that need fleshing out.

### Error Handling Guarantee

All three checks follow the same rule: **never fail the pipeline**. If any check encounters an error, the system logs a warning and proceeds with the original draft.

---

## Phase 6h: Multi-Chapter Generation

When your story has multiple chapters, you can draft them sequentially with cross-chapter continuity.

### Drafting Chapter by Chapter

**What it does:** When you launch a P-300 job with a `chapter_id` in the job payload, the system writes that chapter to a separate file and injects context from prior chapters into the LLM prompt.

**How it works:**
1. You launch P-300 with `chapter_id` in the job payload
2. The system queries your ChapterPlan for `active_character_ids`
3. Scene Context Injection includes: active character profiles + world constraints + **prior chapter summaries** (last 3 chapters max)
4. Prior chapter summaries include: key events (max 10), character states (max 10), unresolved threads (max 5)
5. The draft is written to `chapters/{chapter_id}.md`

**How to prepare:**
- Create ChapterPlan entries with `active_character_ids` for each chapter
- Fill in character voice notes and world bible facts
- Run chapters in order so prior context is available

### Batch Mode

Instead of creating separate jobs per chapter, you can draft multiple chapters in a single job using the `chapter_ids` list in the job payload. This runs chapters sequentially within one job, with automatic LLM-based summarization between chapters. ManuscriptDocument records are auto-created for each completed chapter.

### Checking Results

After the job completes, verify outputs:
1. **Job status**: `GET /v1/jobs/{job_id}/status` — shows completion count
2. **Step records**: `GET /v1/jobs/{job_id}/steps` — one step per chapter
3. **ManuscriptDocuments**: Available in the Writing workspace sidebar
4. **Inspect view**: Navigate to `/workspace/{projectId}/inspect/{jobId}`

> **Note:** In batch mode, you do NOT need to manually promote drafts. ManuscriptDocument records are created automatically.

### Failed Chapters

If a chapter fails mid-batch, subsequent chapters continue running (without the failed chapter's summary). Retry the failed chapter by submitting a new job with just that chapter's ID.

---

## Phase 6i: Manuscript LLM Assist

> **Route**: `/workspace/:projectId/write` (Writing workspace)
>
> **Bridge from Phase 6h:** After drafting chapters, use Manuscript Assist to polish the output — check canon consistency, refine voice, fix continuity errors, and explore alternate directions.

### Step 6i: Select Text and Request Assist

1. Navigate to `/workspace/:projectId/write`
2. Open a manuscript document from the left sidebar
3. Click **"Edit"** to enter edit mode
4. **Select text** by clicking and dragging in the editor
5. The **Assist Toolbar** appears above the selection:

**Selection-Aware Actions** (require selected text):
- **Line Edit Selection** — polish prose, fix grammar, improve flow
- **Expand Selection** — add detail, description, or dialogue
- **Compress Selection** — tighten while preserving meaning
- **Rewrite in Same Voice** — rephrase while maintaining character voice
- **Alternate Version** — generate an alternative way to write the passage
- **Continue from Here** — generate new content following from the selection
- **Fork from Selection** — create a branch diverging from this point

**Document-Wide Actions** (no selection needed):
- **Developmental Review** — high-level feedback on plot, pacing, character arcs
- **Canon Check** — verify against locked canon facts
- **Character Voice Check** — flag dialogue not matching profiles
- **Pacing Review** — identify slow or rushed sections
- **Theme Review** — check thematic consistency
- **Continuity Repair** — find and fix continuity errors

6. Click an action button to submit the assist request
7. Optionally add a custom instruction (max 5,000 characters)

### Step 6j: Review, Apply, or Reject Suggestions

1. Suggestions appear in the right panel (Aids Panel)
2. Each suggestion shows: source text, proposed text, rationale, canon risk (none/low/medium/high/blocking), confidence score (0.0-1.0), and source context references
3. **Apply** — replaces the target range, increments document version, runs canon gate checks
4. **Reject** — dismisses the suggestion
5. **Archive** — keeps for reference but marks as not applicable now

### Step 6k: Fork from Selection

1. Select text in the editor
2. Click **"Fork from Selection"** in the Assist Toolbar
3. Choose destination: Same Project Branch or New Draft Artifact
4. The system records intentional divergence and creates the branch or draft

### Step 6l: Monitor Assist Runs

1. In the Aids Panel, switch to the **Assist Runs** tab
2. View past assist requests with their status
3. Click a run to see suggestions, gate results, created artifacts, and job IDs

---

## Phase 7: Role Model Checker and Review

> **Bridge from Phase 6 (Writing):** After drafting and polishing, run quality checks to verify consistency across your entire story.

### Step 7a: Run the Role Model Checker

**Tab**: Checker (in Planning workspace)

1. Click "Run Checker" to start a new checker run
2. Select the roles to check:
   - **Planner** — does the plot make logical sense?
   - **Character Analyst** — are characters consistent and well-developed?
   - **Consistency Checker** — do facts align across chapters?
   - **Tone Monitor** — is the tone consistent?
   - **Pacing Reviewer** — is the pacing appropriate?
3. Click "Start" to submit the check
4. The run status updates in real-time: PENDING → PROCESSING → COMPLETED or FAILED
5. Click on a completed run to view steps, attempts, lineage, and logs

### Step 7b: Review Findings

**Route**: `/workspace/:projectId/review`

1. **Findings tab** — browse findings filtered by severity:
   - ERROR -- critical issues that must be addressed
   - WARNING -- important concerns
   - SUGGESTION -- optional improvements
2. Click a finding card to expand: description, source object, related inspect run
3. Make a decision on each finding:
   - **Accept** -- acknowledge and address
   - **Reject** -- dismiss the finding
   - **Defer** -- postpone for later consideration
   - **Escalate** -- mark for priority review
   - **Refine** -- request a revised check
4. The decision is recorded and linked to the finding

### Step 7c: Decisions and Inspect Run Links

**Decisions tab** — view the story decision hierarchy:
- Decision nodes with parent-child relationships
- Decision paths (lineage of decisions leading to a point)
- Click a node to see the decision text, options considered, rationale, and related findings

**Inspect Run Links tab** — view and manage links between review objects and inspect runs:
- Browse existing inspect run links
- Create manual links between objects and runs for traceability

---

## Phase 8: Inspect Workspace

### Step 8: Inspect a Job or Checker Run

**Route**: `/workspace/:projectId/inspect/:jobId`

Deep-dive into AI job execution:

1. Navigate to a specific job/run ID, or
2. Click "Jump to Source" from a review finding
3. The Inspect View shows:
   - **Run Header** -- run ID, run kind, status
   - **Steps Tab** -- timeline of individual execution steps with executor name, timestamps, hashes, finish reason, error details
   - **Artifacts Tab** -- generated artifacts with kind, content preview, file path, timestamp
   - **Lineage Tab** -- artifact lineage graph showing input-output relationships, content hashes, supersession chains
   - **Logs Tab** -- execution log entries with timestamp, level, message

From the Inspect View, you can:
- Click "Back to Manuscript" to return to the Writing view
- Retry a failed run (via the retry endpoint)
- View the run's full attempt history

---

## Phase 9: Canon Workshop

> **Bridge from Phase 8 (Inspect):** Before launching a story generation run (Phase 10), visit the Canon Workshop to lock critical facts, set your policy, and preview your packet. This prevents wasted runs on contradictory content.

**Route**: `/workspace/:projectId/canon`

The Canon Workspace is where you edit extracted canon material, classify fields for generation control, manage mythos and pattern entries, and create reusable generation profiles.

### Step 9a: Overview Tab

1. Navigate to `/workspace/:projectId/canon`
2. The **Overview** tab shows summary counts:
   - Characters, world bible entries, mythos entries, pattern entries
   - Canon annotations (locked, soft guidance, mutable, forbidden)
   - Saved customization profiles
3. Click **"New Profile"** to create a reusable generation configuration

### Step 9b: Characters Tab with Annotations

1. Click the **Characters** tab
2. Browse character profiles in card view
3. Click a character to open the editor
4. Use the **Canon Annotation Toolbar** on any field:
   - Click the annotation icon next to a field
   - Select classification: `locked`, `soft_guidance`, `mutable`, or `forbidden_contradiction`
   - Optionally add a note explaining why
   - Optionally scope to specific generation modes
5. Locked fields display a lock badge; they become hard constraints during generation

### Step 9c: World Bible Tab with Annotations

1. Click the **World** tab
2. Browse world bible entries by type
3. Edit any entry and use annotation controls on: title, summary, canonical facts, continuity warnings
4. Mark critical facts as `locked` or specific phrases as `forbidden_contradiction`

### Step 9d: Mythos and Pattern Library Tabs

**Mythos tab** (`?tab=mythos`):
1. Browse mythos entries by type: archetype, motif, cosmic_rule, symbol, ritual, deity, cycle, theme
2. Edit any entry: add canonical facts, refine pattern notes, set generation guidance
3. Use **"Use in Generation"** checkbox to include entries in canon scope

**Patterns tab** (`?tab=patterns`):
1. Browse pattern entries by type: plot, character, relationship, world, theme, scene, structure
2. Edit any pattern: add beats, constraints, transposition notes
3. Set which generation modes the pattern applies to
4. Use **"Use in Generation"** checkbox

### Step 9e: Generation Rules and Profiles

**Generation Rules tab:**
1. Configure canon policy rules:
   - Locked Character Fields (default: display_name, role_in_story, backstory, voice_notes, continuity_facts, relationships)
   - Locked World Fields (default: entry_type, title, summary, canonical_facts)
   - Allowed Changes — explicitly permitted modifications
   - Forbidden Contradictions — specific phrases that must not appear
   - Continuity Strictness — warn, block, repair_once, or repair_twice

**Canon Customization Profiles:**
1. Click **"New Profile"** in the Overview tab
2. Fill in: Name, Description, Default Generation Mode, Canon Scope, Canon Policy, Generation Brief Template
3. Click **"Save"**
4. Later, select a saved profile and click **"Preview Packet"** → **"Submit Generation"**

### Step 9f: Packet Preview Tab

1. Click the **Packet Preview** tab (or navigate to `?tab=packet`)
2. Select a saved profile or configure scope inline
3. Click **"Preview"** to see exactly what the executor will receive:
   - Selected characters with locked/mutable annotations
   - Selected world entries with canonical facts
   - Selected mythos and pattern entries
   - Derived canon policy from annotations
   - Prompt budget summary (character count, truncation warnings)
   - Source hashes for idempotency verification
4. Click **"Submit Generation"** to launch a run from the preview

---

## Phase 10: Story Generation Orchestration

> **Bridge from Phase 9 (Canon Workshop):** With your canon locked and policy set, you're ready to generate new stories — sequels, prequels, side stories, or forks into new projects.

**Route**: `/workspace/:projectId/generate`

### Step 10a: Launch the Generation Wizard

1. Navigate to `/workspace/:projectId/generate`
2. The **Story Generation Wizard** appears with several configuration steps
3. The wizard loads character profiles, world bible entries, and existing generation runs

### Step 10b: Select Generation Mode

- **Same Project — New Arc** (`same_project_new_arc`) — adds a fresh narrative arc within the existing project
- **Same Project — Sequel** (`same_project_sequel`) — continues the story after its current ending
- **Same Project — Prequel** (`same_project_prequel`) — generates events that happened before the current story
- **Same Project — Side Story** (`same_project_side_story`) — explores a parallel storyline sharing the same world
- **Same Project — Alternate Route** (`same_project_alternate_route`) — reimagines key decisions from the existing story
- **New Project — Character Fork** (`new_project_character_fork`) — copies selected characters into a new project
- **New Project — World Fork** (`new_project_world_fork`) — copies the world bible into a new project
- **New Project — Hybrid Fork** (`new_project_hybrid_fork`) — copies both characters and world elements

### Step 10c: Select Destination

- **Same Project** — target project ID defaults to the current project
- **New Project** — enter a name; the system creates it automatically with copied canon and provenance tracking

### Step 10d: Configure Canon Scope

Select which source material the generator should respect:
1. **Characters** — check boxes next to characters. Leave all unchecked for full-project scope.
2. **World Bible Entries** — select locations, rules, concepts, etc.
3. **Arcs** — select narrative arcs to carry forward
4. **Continuity Threads** — select unresolved threads to address

### Step 10e: Enter Generation Brief and Policy

1. **Brief** (required, max 10,000 characters) — describe what you want the new story to accomplish
2. **Canon Policy:**
   - Locked Character/World Fields — defaults provided
   - Allowed Changes — explicitly permitted modifications
   - Forbidden Contradictions — specific phrases that must not appear
   - Continuity Strictness — `warn`, `block`, `repair_once`, `repair_twice`

### Step 10f: Submit and Monitor

1. Enter the target number of chapters (1–100)
2. Click **"Submit Run"**
3. The system validates, creates a generation run, builds a Canon Generation Packet, and queues 4 executor jobs: G-200 (plan), G-300 (draft), G-350 (gate), G-400 (compile)
4. **Generation Run Card** shows: generation ID, source/target project IDs, job IDs, status, warnings, created artifacts
5. Click a run card to expand details and view **Gate Results**

### Step 10g: Review Gate Results and Inspect

**Gate Results** show:
- Gate name, pass/fail, severity (info/warning/blocking), reasons, repair metadata
- Failed gates link to the Inspect view for debugging

**Fork Preview** (optional):
- Click **"Preview Fork"** to see what would be copied before committing

**Fork Project Only** (without generation):
- Click **"Fork Project Only"** to create the target project with copied canon but no generation jobs

### What Happens Behind the Scenes

- **G-200**: Loads canon packet, generates new story architecture (premise, arcs, chapter plans, canon obligations)
- **G-300**: Iterates over planned chapters, drafts prose with full canon context and prior summaries
- **G-350**: Runs consistency checks on every artifact; applies repair policy for violations
- **G-400**: Assembles final manuscript from chapter drafts; only runs if no blocking gates failed

### Troubleshooting Story Generation

| Issue | Solution |
|-------|----------|
| Run fails with "source project not found" | Verify the source project ID is correct |
| Gate results show many contradictions | Relax locked fields or add allowed changes |
| Generation is too slow | Reduce canon scope or chapter count |
| Forked project has missing relationships | Relationships only copied if both endpoint characters are selected |
| Idempotency conflict (409) | Same key with different payload. Use a new key or match original payload |
| Run is "blocked" after G-350 | Blocking gate failed, repair exhausted. Review gates, fix policy, retry |
| Packet exceeds budget warning | System auto-truncates to 120K chars. Reduce scope for full fidelity |

---

## Phase 11: Story Branching

> **Bridge from Phase 10 (Generation):** After generating stories, you may want to explore alternate directions within existing projects. Branches let you explore multiple versions without modifying your main story.

**Tab**: Branches (in Planning workspace)

### Step 11a: Create Branches

1. Click the **Branches** tab
2. Click **"Create Branch"**
3. Fill in:
   - **Branch Name** -- a descriptive name (e.g., "Alternate Ending")
   - **Branch Point** -- the ID of the branch point in the story
   - **State** -- ACTIVE (default), MERGED, or ARCHIVED
4. Click "Save"
5. Click **"Set Active"** to switch to this branch
6. Draft this alternate version by launching P-300

### Step 11b: Branch Comparisons

1. Select two branches from the comparison form
2. Click "Compare" to generate a comparison analysis
3. The comparison shows differences in draft content, planning entities, character development, and world bible entries

### Step 11c: Merge Decisions

1. Select source and target branches
2. Enter a **merge rationale** explaining why you're merging
3. Click "Create Merge Decision"
4. The merge decision is recorded and the source branch state can be updated

### Tips

- Only one branch is active at a time — set explicitly before launching jobs
- Use branches for endings — explore multiple endings in parallel, then merge the best elements
- MERGED branches are read-only; ARCHIVED branches are preserved for reference

---

## Phase 12: Exporting and Importing Projects

> **Bridge from Phase 11 (Branching):** Once your project is complete, you can export it as a portable ZIP archive for backup, transfer, or sharing.

**Route**: `/` (home page) — Project List actions

### Step 12a: Export a Project

1. Navigate to the home page (`/`) — the Project List view
2. Find the project you want to export in the grid
3. Click the **Export** button (archive icon) on the project row
4. The browser downloads a ZIP file named `{project_name}_export.zip`

The ZIP contains:
- Project directory (manifest.json, bible.db, sequences.json, chapters/, exports/, .telemetry, .structured_log)
- Operations DB dump (all 49 tables scoped to the project_id)
- Metadata (export_version, project name, project ID, timestamp)

### Step 12b: Import an Exported Project

1. Navigate to the home page (`/`)
2. Click **"Import Project"** (button above the project list)
3. The import wizard opens:
   - **Drag & drop** your exported ZIP file, or click to browse
   - Enter a **new project name** — this becomes the display name for the imported project
4. Click **"Import Project"**
5. The system validates the ZIP and runs the import asynchronously:
   - Extracts to an isolated temp directory with path traversal protection
   - Runs schema version migration if needed
   - Creates a new project with restored files and database records
6. Progress indicator shows: pending → processing → completed (or failed)
7. On success, you're redirected to the imported project's workspace

> **Important**: Import always creates a brand-new project with a fresh UUID. It does NOT overwrite or merge with any existing project.

### Troubleshooting Export/Import

| Issue | Solution |
|-------|----------|
| Export button does nothing | Ensure your project has a valid manifest; check browser console |
| ZIP is very large (500+ MB) | Operations DB grows over time with job records. Expected for extensive history |
| Import fails with "invalid export" | ZIP must be created by Narrative Engine and contain `metadata.json` |
| Import hangs at "Processing" | Large DB dumps take time. Typical import: 15-30 seconds for medium projects |
| Missing data after import | Verify ZIP contains both `metadata.json` and the project directory |

---

## Advanced Workflows

### Workflow A: Full Story Pipeline (Automated Generation)

After setting up foundation, characters, and world bible:

1. **Brain Dump** raw ideas, click Organize
2. **Run P-100 Architect** -- generates the story architecture (markdown)
3. **Run P-200 Sequencer** -- generates the sequence plan (JSON) using P-100 output
4. **Run P-300 Drafter** -- generates chapter drafts with automatic quality checks:
   - Scene Context Injection feeds character profiles and world facts into the prompt
   - Consistency Critic verifies character voice and behavior, triggers rewrite on violations
   - Entity Intake detects new characters in draft prose and auto-extracts skeletal profiles
5. **Check Characters tab** -- review any auto-detected character profiles from Entity Intake
6. **Run P-400 Compiler** -- generates the story bible snapshot (JSON) using all prior outputs
7. **Review findings** from P-400 and make decisions
8. **Iterate** -- update foundation or world bible, re-run phases as needed

### Workflow B: Brain Dump to Structured Project

1. Go to **Brain Dump**, write raw ideas freely
2. Click **Organize** to have the LLM categorize the content
3. Navigate to **Planning** workspace:
   - **Foundation** tab -- create foundation from organized themes
   - **Characters** tab -- create characters from organized character entries
   - **World Bible** tab -- create world entries from organized setting entries
   - **Arcs** tab -- create arc candidates from organized plot arc ideas
4. Run the **Full Story Pipeline** (P-100 through P-400)
5. **Review** findings and iterate

### Workflow C: Story Branching and Comparison

1. In the **Planning** workspace, establish a baseline plan
2. Go to **Branches** tab, create a branch with a descriptive name
3. Edit the manuscript in **Write** workspace for this branch
4. Create new planning entities (alternate sequences, chapters)
5. Go back to **Branches** tab and create a comparison between branches
6. If satisfied, create a **merge decision** to consolidate the branch

### Workflow D: Character Arc Development

1. Create characters in the **Characters** tab
2. In the **Arcs** tab, create arc candidates for each character
3. Define stage maps with narrative progression chips
4. Run the **Role Model Checker** to verify character consistency
5. Review findings in the **Review** workspace
6. Update character profiles based on review feedback
7. Iterate

### Workflow E: Manuscript Review Cycle

1. Write/edit manuscript content in the **Writing** workspace
2. Use **Manuscript Assist** for line edits, expansions, canon checks
3. Run the **Role Model Checker** for deeper consistency analysis
4. Review findings in the **Review** workspace
5. Inspect checker runs via the **Inspect** workspace for detailed analysis
6. Iterate until satisfied

### Workflow F: Import Source Story, Generate Sequel, Fork to New Project

1. **Import a source story** — paste an existing completed story via the frontend import modal
2. **Review the imported project** — verify characters, world bible, arcs, and foundation
3. **Visit Canon Workshop** — lock critical facts, set policy
4. **Navigate to Generate workspace** — `/workspace/:projectId/generate`
5. **Configure the wizard:**
   - Mode: `new_project_character_fork`
   - Destination: New Project named "Sequel: [Name]"
   - Canon Scope: select all major characters and key world entries
   - Brief: describe the sequel
   - Policy: continuity strictness = `warn`, forbidden contradictions listing resolved plot points
6. **Preview the fork** — verify selected characters, world entries, and arcs
7. **Submit the run** — system creates target project, copies canon, queues G-200 through G-400
8. **Monitor progress** — watch run status transition
9. **Review gate results** — check for warnings about canon contradictions
10. **Navigate to the new project** — explore the generated sequel
11. **Iterate** — adjust policy, retry failed runs, or run manual P-phases for refinement

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

### Project Export/Import Issues

- **Export button does nothing** — Ensure the project has a valid manifest and database. Check browser console for network errors.
- **ZIP file is larger than expected (500+ MB)** — The operations DB accumulates job records over time. Normal for projects with extensive AI execution history.
- **Import fails with "invalid export"** — Verify the ZIP was created by Narrative Engine and contains `metadata.json`.
- **Import shows "processing" indefinitely** — Large operations DB dumps require time to restore. Check server logs; typical import takes 15-30 seconds.
- **Imported project is missing data** — Verify the export ZIP contains both `metadata.json` and a complete project directory.
- **Schema migration fails on import** — The export version may be significantly older than your current installation. Import is rolled back on migration failure.

### Job Failure Recovery

- Failed jobs can be retried via the Inspect view's "Retry" button
- Retries use the same input but may use a different inference provider
- Step records and lineage are preserved for inspection

### Narrative Controller Issues

- **Drafts don't seem to use character context.** Check that character profiles have filled-in fields (archetype, voice notes, goals, fears). Empty fields are not injected.
- **Consistency critic isn't catching out-of-character dialogue.** Ensure voice notes are specific (e.g., "terse, avoids metaphors" rather than "normal").
- **Too many auto-detected characters.** The entity intake stop-word list filters common non-name words, but some false positives may slip through. Review the Characters tab after each P-300 run.
- **Drafts take longer to generate.** The narrative controller adds 1-5 extra LLM calls per draft. Intentional for quality. Use the stub backend for faster iteration.

### Story Generation Issues

- **Run status stays "queued".** The LocalExecutor may not be running or the inference backend is unavailable. Check `GET /health/ready`.
- **Gate results show contradictions for accurate content.** Gate checks are text-based substring matches. Add legitimate phrases to `allowed_character_changes` or relax locked fields.
- **Forked project has fewer characters than selected.** Character copy only includes characters whose IDs match exactly.
- **Idempotency conflict (HTTP 409).** Re-submitted with same key but different payload. Omit the idempotency key for a new run, or match the original payload exactly.
- **Generation takes too long.** Large canon packets increase prompt size and LLM latency. Reduce scope to only essential elements.

### Canon Workshop Issues

- **Annotations don't persist after reload.** Check that the annotation was saved (toolbar shows a checkmark). Unsaved annotations are lost on navigation.
- **Packet preview doesn't include selected entries.** Ensure "Use in Generation" is checked for each entry.
- **Profile can't be saved.** Verify that at least one canon scope category has selections. Empty profiles are rejected.
- **Mythos/pattern entries don't appear after extraction.** Call `POST /v1/mythos/materialize-extraction` or `POST /v1/patterns/materialize-extraction` to create editable entries.

### Manuscript Assist Issues

- **Assist request fails with "selection not found".** Selected text no longer matches the document. Re-select and re-submit.
- **Apply suggestion returns 409 Conflict.** Document version mismatch. Refresh the editor, re-request the assist.
- **Suggestion shows "blocking" canon risk.** Proposed text contradicts a locked canon fact. Relax the locked field or reject the suggestion.
- **Fork from Selection creates empty branch.** Ensure selected text is meaningful (at least a paragraph).
- **Assist runs stay "queued".** Check `GET /health/ready` and verify your inference backend is running.

### Branch State Management

- ACTIVE branches can be edited
- MERGED branches are read-only (consolidated into target)
- ARCHIVED branches are preserved for reference but not editable
