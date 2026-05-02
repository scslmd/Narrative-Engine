# Narrative Engine - Complete User Walkthrough v1.5.1

> Purpose: Step-by-step guide to using all features of the Narrative Engine application, starting simple and incrementally building to advanced workflows.
>
> Prerequisites: A working Narrative Engine installation with backend and frontend running. Inference backend (llama.cpp, LM Studio, vLLM, or stub) configured and accessible.
>
> Recommended reading order: Follow the phases sequentially. Use the **User Guide** (`User Guide v1.5.1.md`) for feature reference and detailed explanations.

---

## Overview

The Narrative Engine is a narrative compilation system for long-form fiction development. It provides:

- **Mythos Extraction** -- paste mythology texts and extract narrative patterns to seed a new project
- **Pattern Extraction** -- paste any story or mythology text and extract storytelling DNA including voice profile, narrative structure, thematic constraints, and entities to seed a new project
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
- **Story Generation Orchestration** -- generate new canon-congruent stories from existing projects; fork characters/world into new projects; 4-phase pipeline (G-200 plan, G-300 draft, G-350 gate, G-400 compile) with consistency gates
- **Canon Workshop** -- edit extracted canon material, mark fields as locked/mutable/forbidden, manage mythos and pattern entries, create reusable generation profiles, preview canon packets before submission
- **Manuscript LLM Assist** -- select text in the manuscript editor and request AI assistance: line edits, expansions, rewrites, continuations, canon checks, forks; suggestions include canon risk ratings and confidence scores

---

## How to Use This Walkthrough

This walkthrough follows the **creative lifecycle**: seed your project, plan and refine, generate stories, then polish manuscripts. Follow the phases in order for the best learning experience. Each phase includes:

- **Route** — the URL path in the frontend
- **Step-by-step instructions** — what to click and fill in
- **"What you see"** — what the UI shows after each action
- **Troubleshooting** — common issues and fixes (at the end)

For deeper feature explanations, cross-reference the **User Guide** (`User Guide v1.5.1.md`).

---

## Table of Contents

### Getting Started

- [Phase 0: Getting Sample Stories](#phase-0-getting-sample-stories)
- [Phase 1: Project Setup](#phase-1-project-setup)
  - [Option A: Create Project (Manual)](#option-a-create-project-manual)
  - [Option B: Import Story (LLM-Assisted)](#option-b-import-story-llm-assisted)
  - [Option C: Extract Mythos (Pattern-Based Seed)](#option-c-extract-mythos-pattern-based-seed)
  - [Option D: Extract Patterns (Generalized Pattern-Based Seed)](#option-d-extract-patterns-generalized-pattern-based-seed)
- [Phase 1b: Mythos Extraction Results](#phase-1b-mythos-extraction-results-optional)
- [Phase 1c: Pattern Extraction Results](#phase-1c-pattern-extraction-results-optional)

### Planning and Setup

- [Phase 2: Planning Workspace](#phase-2-planning-workspace)
  - [Manifest, Foundation, Characters, World Bible](#step-2a-manifest-view)
  - [Sequence, Chapter, Scene, Beat Plans](#step-2e-planning---sequence-plans)
  - [Dependencies, Chapter Packets, Storyboard Cards](#step-2i-planning---dependencies)
  - [Flow Editor](#step-2l-flow-editor)
- [Phase 3: Arc Management](#phase-3-arc-management)
- [Phase 4: Story Branching](#phase-4-story-branching)

### Writing and AI Assistance

- [Phase 5: Writing Workspace](#phase-5-writing-workspace)
  - [Manuscript Editing, Draft Management, Promotion](#step-5-manuscript-editing)
  - [Draft Continuation, Alternate Variants, Revision Suggestions](#step-5d-draft-continuation)
- [Phase 5g: State-Aware Narrative Controller](#phase-5g-state-aware-narrative-controller-automatic)
- [Phase 5h: Multi-Chapter Generation](#phase-5h-multi-chapter-generation)
- [Phase 5i: Manuscript LLM Assist](#phase-5i-manuscript-llm-assist)

### Quality and Review

- [Phase 6: Role Model Checker](#phase-6-role-model-checker)
- [Phase 7: Review Workspace](#phase-7-review-workspace)
- [Phase 8: Inspect Workspace](#phase-8-inspect-workspace)

### Ideation and Decisions

- [Phase 9: Brain Dump](#phase-9-brain-dump)
- [Phase 10: Brainstorm](#phase-10-brainstorm)
- [Phase 11: Decisions](#phase-11-decisions)

### Advanced Generation

- [Phase 12: Story Generation Orchestration](#phase-12-story-generation-orchestration)
- [Phase 13: Canon Workshop](#phase-13-canon-workshop)

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

Three of the four stories exceed the 30,000-character threshold for single-pass import, which exercises the **multi-pass import pipeline** -- the system that handles large stories by chunking, per-chapter analysis, and consolidation. The Last Archive (~28K chars) exercises single-pass import instead. Together they test both code paths thoroughly.

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
   - Detect that the story exceeds the single-pass threshold
   - Route to multi-pass import: structure detection, per-chapter analysis, character/world/arc consolidation
   - Create a new project with all extracted data populated
   - Return a success response when complete
8. On success, you'll be redirected to the project workspace

**Note**: Import requires a configured inference backend (llama.cpp, LM Studio, vLLM, or stub). Large stories may take several minutes to process through multi-pass import.

### Expected Extraction Results

Each sample story is designed to produce clean extraction results across all categories. Here's what to expect:

#### The Time Machine
- **Characters**: 6+ (Time Traveller, Weena, Eloi collective, Morlocks, Filby, frame narrator)
- **World Bible**: 8+ entries (Year 802,701 AD, Time Machine technology, Eloi/Morlock societies, class evolution theme, Victorian London frame)
- **Arcs**: 3 (class divergence, exploration/discovery, survival/rescue)
- **Notable**: Tests extraction from classic prose with frame narrative structure and sparse character development

#### The Picture of Dorian Gray
- **Characters**: 8+ (Dorian Gray, Lord Henry Wotton, Basil Hallward, Sibyl Vane, Allan Chambers, James Vane)
- **World Bible**: 10+ entries (Victorian London high society, aestheticism philosophy, portrait's magical properties, opium dens, moral decay theme)
- **Arcs**: 4 (corruption, consequence, pursuit, redemption/despair)
- **Notable**: Tests large-story multi-pass import and philosophical dialogue extraction

#### The Last Archive
- **Characters**: 6 (Miren Kael, Joss Vallen, Tessa Rowan, Ravi Chen, Director Hale, Echo/collective consciousness)
- **World Bible**: 10+ entries (memory crystals, extraction process, Chronos interface, Grand Archive, Understack, Three Laws of Memory, Identity Drift, Erasure Protocol, Echo Fragments, New Geneva)
- **Arcs**: 3 (discovery, conflict with Council, Chronos resolution)
- **Notable**: Tests technology/world-bible extraction with many named concepts and clear arc structure

#### Crossing Limits
- **Characters**: 7 (Elara Voss, Kai Mercer, Dr. Nadia Chen, Mira Voss, The Keeper, Prof. Ashworth, The Guide)
- **World Bible**: 8+ entries (book-worlds concept, Crossing Limit Rule, Athenaeum, reality degradation, anchor points, Sealed Collection, book-world ethics, merge threat)
- **Arcs**: 3 (romance, mystery of destabilization, rescue/stabilization)
- **Notable**: Tests romance genre handling, dual-world settings, and relationship-driven plot extraction

### Bridge to Phase 1

After importing a sample story, you'll be in the project workspace. Proceed to [Phase 1](#phase-1-project-setup) to explore the imported data, or skip directly to [Phase 2](#phase-2-planning-workspace) to review the extracted planning structure.

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

#### Option C: Extract Mythos (Pattern-Based Seed)

1. Click the "Import Existing Story" button to open the modal, then toggle to "Extract Mythos" mode
2. Fill in:
   - **Project Name** -- required, name for the new project
   - **Source Tradition** -- optional, e.g., "Greek Mythology", "Norse Sagas". Omit to let AI identify.
   - **Generation Mode** -- select one:
     - **Same World** -- keep mythological setting, create original characters following extracted patterns
     - **Transposed** -- map archetypes to a new setting (e.g., Greek tragedy → corporate drama)
     - **Pure Pattern** -- apply narrative structures only; free-form world and genre
   - **Mythology Texts** -- paste mythology texts, sagas, or source material (up to 24,000 characters). Include diverse myths for richer pattern extraction.
3. Click "Extract Mythos"
4. The system:
   - Analyzes your text via LLM
   - Extracts archetypal patterns, narrative structures, cosmic rules, symbolic motifs
   - Creates a project with foundation profile, world bible entries, character archetypes, and key entities
   - Returns a success/failure response
5. On success, you are redirected to the project workspace

**Note**: Mythos Extraction requires a configured inference backend. Generation modes determine how extracted patterns are applied: Same World for in-universe stories, Transposed for adapted settings, Pure Pattern for maximum creative freedom.

#### Option D: Extract Patterns (Generalized Pattern-Based Seed)

1. Click the "Import Existing Story" button to open the modal, then toggle to "Extract Patterns" mode
2. Fill in:
   - **Project Name** -- required, name for the new project
   - **Source Type** -- select one:
     - **Narrative** — fiction stories; includes voice profile, narrative pattern, and thematic constraints in extraction
     - **Mythology** — mythological texts; delegates to Mythos Extraction pipeline
   - **Generation Mode** -- select one:
     - **Same World** — keep the source story's world, create original characters following extracted patterns
     - **New Characters** — same world, original cast fulfilling extracted archetypes
     - **Transposed** — map patterns and voice to a new setting; maximum creative freedom with narrative DNA preserved
   - **Source Corpus** -- optional label (e.g., "Dune", "The Shining")
   - **Story Text** -- paste any completed story text for analysis (up to 24,000 characters)
3. Click "Extract Patterns"
4. The system:
   - Analyzes your text via LLM
   - Extracts archetypal patterns, narrative structures, voice profile, thematic constraints, world rules, symbolic motifs, and entities
   - Creates a project with foundation profile, world bible entries, character archetypes, and narrative-specific fields (voice profile, thematic constraints)
   - Returns a success/failure response
5. On success, you are redirected to the project workspace

**Note**: Pattern Extraction requires a configured inference backend. Source type determines which extraction pipeline is used: Narrative for fiction stories with voice profile extraction, Mythology for mythological texts (delegates to MythosExtractionService). Generation modes determine how extracted patterns guide downstream generation.

---

## Phase 1b: Mythos Extraction Results (Optional)

If you used Mythos Extraction as your project seed, the following will be pre-populated when you enter the workspace:

- **Foundation Editor** -- thematic spine, emotional promise, tone direction derived from source material
- **World Bible** -- cosmic rules and symbolic motifs as concept entries
- **Character Builder** -- archetypal pattern carriers available as templates
- **P-100 Architect** -- applies mythos context based on your generation mode
- **P-300 Drafter** -- enforces cosmic rules as hard constraints during drafting

### Troubleshooting Mythos Extraction

| Issue | Solution |
|-------|----------|
| Extraction returns no patterns | Ensure text is 2,000+ characters and includes multiple mythological accounts |
| Wrong source tradition detected | Specify source_corpus manually and retry |
| Partial results | Retry — the LLM may extract more patterns on a second pass |
| Generation mode unclear | Same World for in-universe stories, Transposed for adapted settings, Pure Pattern for maximum freedom |

---

## Phase 1c: Pattern Extraction Results (Optional)

If you used Pattern Extraction as your project seed, the following will be pre-populated when you enter the workspace:

- **Foundation Editor** -- thematic spine, emotional promise, tone direction derived from source material; narrative constraints include archetypal patterns + narrative structures + thematic constraints
- **World Bible** -- world rules and symbolic motifs as concept entries
- **Character Builder** -- archetypal pattern carriers available as templates; key entities with appropriate roles
- **Voice Profile** -- extracted narrative voice, sentence rhythm, descriptive density, humor level, emotional temperature (narrative source type only)
- **Narrative Pattern** -- pacing, chapter structure, conflict type, dialogue style, scene transition (narrative source type only)
- **Thematic Constraints** -- themes with moral stances, recurring questions, forbidden elements (narrative source type only)
- **P-100 Architect** -- applies pattern context via `_build_pattern_context_block()` based on generation mode
- **P-300 Drafter** -- uses SceneContext's `pattern_guidance` and `author_prompt` for pattern-informed drafting

### Troubleshooting Pattern Extraction

| Issue | Solution |
|-------|----------|
| Extraction returns no patterns | Ensure text is 2,000+ characters and includes diverse scenes from the source story |
| Voice profile not extracted | Use source_type = "narrative" for fiction stories; mythology source type does not extract voice profiles |
| Wrong generation mode | Same World for in-universe stories, New Characters for same world with original cast, Transposed for adapted settings |
| Partial results | Retry — the LLM may extract more patterns on a second pass |

From here, proceed to Phase 2 (Planning Workspace).

---

## Phase 2: Planning Workspace

> **Bridge from Phase 1:** After creating or importing your project, the next step is to plan your story structure. If you imported a story or used Pattern/Mythos Extraction, many of these fields are pre-populated — review and refine them before launching AI jobs.

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

> **Bridge from Phase 4 (Branching):** After exploring story branches, move to the Writing workspace to edit your manuscript. Launch P-300 Drafter jobs from the Job Launch panel to generate chapter drafts, then use Manuscript Assist (Phase 5i) to polish them.

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
- Pattern guidance: voice profile, world rules, and thematic constraints from extracted patterns (if project was seeded via Pattern Extraction)
- Author prompt: per-chapter author direction (if provided)

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

## Phase 5h: Multi-Chapter Generation

When your story has multiple chapters, you can draft them sequentially with cross-chapter continuity. Each chapter build on what came before.

### Drafting Chapter by Chapter

**What it does:** When you launch a P-300 job with a `chapter_id` (e.g., `"ch-002"`), the system writes that chapter to a separate file (`chapters/ch-002.md`) and injects context from prior chapters into the LLM prompt.

**What you see:** Each chapter is saved independently, making it easy to review, edit, or regenerate individual chapters without affecting others.

**How it works:**
1. You launch P-300 with `chapter_id: "ch-002"` in the job payload
2. The system queries your ChapterPlan for `active_character_ids` (characters who appear in this chapter)
3. Scene Context Injection includes: active character profiles + world constraints + **prior chapter summaries** (last 3 chapters max)
4. Prior chapter summaries include: key events (max 10), character states at chapter end (max 10), unresolved threads (max 5)
5. The draft is written to `chapters/{chapter_id}.md`

**How to prepare:**
- Create ChapterPlan entries with `active_character_ids` for each chapter (keeps prompts focused and reduces token usage)
- Fill in character voice notes and world bible facts — the richer your reference data, the better the cross-chapter continuity
- For sequential drafting, run chapters in order (ch-001, then ch-002, etc.) so prior context is available

### ChapterOrchestrator (Sequential Multi-Chapter)

**What it does:** Runs P-300 jobs sequentially for all chapters in your project. Each chapter waits for the prior to complete before starting.

**What you see:** A series of P-300 jobs, one per chapter, each producing a completed chapter file. Failed chapters are logged but don't stop subsequent chapters from running.

**How it works:**
1. Orchestrator receives a list of chapter IDs (e.g., `["ch-001", "ch-002", "ch-003"]`)
2. For each chapter, it creates a P-300 job with the chapter_id in the payload
3. The job runs through the full pipeline (context injection → draft → critic → entity intake)
4. When complete, the next chapter begins — now with access to the prior chapter's context

**How to use:** Currently available as a programmatic service. Launch individual P-300 jobs with `chapter_id` in the payload for now. Future UI integration will expose orchestrator controls.

#### Batch Mode Alternative

Instead of creating separate jobs per chapter, you can draft multiple chapters in a single job using the `chapter_ids` list:

```bash
curl -X POST http://localhost:8000/v1/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "phase": "P-300",
    "payload": {
      "project_id": "<your-project-id>",
      "chapter_ids": ["ch-001", "ch-002", "ch-003"]
    }
  }'
```

This runs chapters sequentially within one job, with automatic LLM-based summarization between chapters. Each chapter's summary (key events, character states, unresolved threads) is injected into the next chapter's prompt for continuity. ManuscriptDocument records are auto-created for each completed chapter.

#### Checking Results

After the job completes, verify outputs:

1. **Job status**: `GET /v1/jobs/{job_id}/status` — shows completion count
2. **Step records**: `GET /v1/jobs/{job_id}/steps` — one step per chapter (`drafter-ch-XXX`)
3. **ManuscriptDocuments**: `GET /v1/story-development/drafting/manuscript-documents?project_id={id}` — auto-created for each completed chapter
4. **Chapter files**: Check `data/projects/{project_id}/chapters/` directory
5. **Inspect view**: Navigate to `/workspace/{projectId}/inspect/{jobId}` in the frontend

> **Note:** In batch mode, you do NOT need to manually promote drafts (Phase 5c). ManuscriptDocument records are created automatically for each completed chapter.

#### Failed Chapters

If a chapter fails mid-batch, subsequent chapters continue running (without the failed chapter's summary). To retry:
```json
{
  "phase": "P-300",
  "payload": {
    "project_id": "<your-project-id>",
    "chapter_ids": ["ch-002"]
  }
}
```
Check step records or the Inspect view to identify which chapter failed and why.

---

## Phase 5i: Manuscript LLM Assist

> **Route**: `/workspace/:projectId/write` (Writing workspace)

> **Bridge from Phase 5h:** After drafting chapters, use Manuscript Assist to polish the output — check canon consistency, refine voice, fix continuity errors, and explore alternate directions before promoting drafts.

The Writing workspace supports interactive AI assistance through text selection and assist actions. Use this after any P-300 draft or manual edit to get AI-powered feedback and suggestions.

### Step 5i: Select Text and Request Assist

1. Navigate to `/workspace/:projectId/write`
2. Open a manuscript document from the left sidebar
3. Click **"Edit"** to enter edit mode
4. **Select text** by clicking and dragging in the editor
5. The **Assist Toolbar** appears above the selection with two categories:

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

### Step 5j: Review LLM Suggestions

1. After submission, suggestions appear in the right panel (Aids Panel)
2. Each suggestion shows:
    - **Source text** — what was analyzed
    - **Proposed text** — the suggested replacement or addition
    - **Rationale** — why this change helps
    - **Canon risk** — none, low, medium, high, or blocking
    - **Confidence score** — 0.0 to 1.0
    - **Source context** — which canon entries were referenced
3. Suggestions have statuses: REQUESTED → PENDING → ACCEPTED/REJECTED/ARCHIVED

### Step 5k: Apply a Suggestion

1. Find the suggestion you want to apply
2. Click **"Apply"** on the suggestion card
3. The system:
    - Resolves the exact location using offsets, then anchors if offsets drifted
    - Checks version conflict protection (current version must match expected)
    - Runs canon gate checks before applying
    - Replaces the target range and increments the document version
4. If canon gates fail with blocking severity, you'll see a warning before applying

### Step 5l: Reject or Archive Suggestions

- **Reject** — dismisses the suggestion; it won't appear again for this assist run
- **Archive** — keeps the suggestion for reference but marks it as not applicable now

### Step 5m: Fork from Selection

1. Select text in the editor
2. Click **"Fork from Selection"** in the Assist Toolbar
3. Choose destination:
    - **Same Project Branch** — creates a story branch with the alternate content
    - **New Draft Artifact** — creates a separate draft for exploration
4. The system:
    - Records intentional divergence from the source manuscript
    - Creates the branch or draft artifact
    - Shows the created ID for navigation

### Step 5n: Monitor Assist Runs

1. In the Aids Panel, switch to the **Assist Runs** tab
2. View past assist requests with their status (queued, running, completed, blocked, failed)
3. Click a run to see:
    - Suggestions generated
    - Gate results with reasons and severity
    - Created draft artifacts or branches
    - Job IDs for inspection

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

## Phase 12: Story Generation Orchestration

> **Bridge from Phase 11 (Decisions):** After recording your creative decisions, use Story Generation to produce new canon-congruent stories — sequels, prequels, side stories, or forks into new projects. For best results, visit the Canon Workshop (Phase 13) first to lock critical facts and set your policy.

### Step 12: Open the Generate Workspace

**Route**: `/workspace/:projectId/generate`

The Generate workspace is where you create new stories from existing canon. It loads your project's characters and world bible entries automatically, making them available for selection in the wizard.

### Step 12a: Launch the Generation Wizard

1. Navigate to `/workspace/:projectId/generate`
2. The **Story Generation Wizard** appears with several configuration steps
3. The wizard loads:
   - Character profiles (for canon scope selection)
   - World Bible entries (for canon scope selection)
   - Existing generation runs (to monitor or retry)

### Step 12b: Select Generation Mode

The wizard's first step asks how the new story relates to the source:

- **Same Project — New Arc** (`same_project_new_arc`) — adds a fresh narrative arc within the existing project, reusing all canon
- **Same Project — Sequel** (`same_project_sequel`) — continues the story after its current ending
- **Same Project — Prequel** (`same_project_prequel`) — generates events that happened before the current story
- **Same Project — Side Story** (`same_project_side_story`) — explores a parallel storyline sharing the same world
- **Same Project — Alternate Route** (`same_project_alternate_route`) — reimagines key decisions from the existing story
- **New Project — Character Fork** (`new_project_character_fork`) — copies selected characters into a new project with a fresh world
- **New Project — World Fork** (`new_project_world_fork`) — copies the world bible into a new project with new characters
- **New Project — Hybrid Fork** (`new_project_hybrid_fork`) — copies both characters and world elements into a new project

### Step 12c: Select Destination

- **Same Project** — the target project ID defaults to the current project. You can override it to generate into a different existing project.
- **New Project** — enter a name for the new project. The system creates it automatically, copies selected canon with remapped IDs, and records provenance linking back to the source project.

### Step 12d: Configure Canon Scope

Select which source material the generator should respect:

1. **Characters** — check boxes next to characters you want included. Leave all unchecked for full-project scope.
2. **World Bible Entries** — select locations, rules, concepts, organizations, etc. that should be preserved.
3. **Arcs** — select narrative arcs to carry forward into the new story.
4. **Continuity Threads** — select unresolved threads the generator should address.

At least one category must have selections unless you're using full-project scope.

### Step 12e: Enter Generation Brief

The brief is a required text field (max 10,000 characters) describing what you want the new story to accomplish. Examples:

- "Write a sequel where the protagonist returns 5 years later to discover the antagonist has resurfaced in a new form."
- "Create a side story told from the mentor's perspective, covering events that happened during the main story but were never shown."
- "Fork these three characters into a cyberpunk setting. Keep their core personalities and relationships but adapt goals and conflicts to a corporate dystopia."

### Step 12f: Configure Canon Policy

The policy controls what the generator may or may not change:

1. **Locked Character Fields** — fields that cannot be contradicted in generated content. Defaults: `display_name`, `role_in_story`, `backstory`, `voice_notes`, `continuity_facts`, `relationships`
2. **Locked World Fields** — immutable world facts. Defaults: `entry_type`, `title`, `summary`, `canonical_facts`
3. **Allowed Character Changes** — explicitly permitted modifications (e.g., "new_goal", "changed_relationship")
4. **Allowed World Changes** — permitted world modifications (e.g., "new_location", "technology_evolution")
5. **Forbidden Contradictions** — specific phrases or facts that must not appear in generated content. Example: "the dragon was slain" (if you want the dragon alive)
6. **Continuity Strictness** — how to handle gate violations:
   - `warn` — record a warning, allow generation to proceed
   - `block` — stop generation immediately if a contradiction is detected
   - `repair_once` — attempt one automatic LLM repair, then block if still failing
   - `repair_twice` — attempt two repairs before blocking

### Step 12g: Set Chapter Count and Submit

1. Enter the target number of chapters (1–100)
2. Optionally set words per chapter (250–10,000), model ID, temperature, and max tokens
3. Click **"Submit Run"**

The system:
1. Validates the request (scope, destination, idempotency)
2. Creates a generation run with a unique `generation_id`
3. Builds a deterministic **Canon Generation Packet** from selected source material
4. Queues 4 executor jobs: G-200 (plan), G-300 (draft), G-350 (gate), G-400 (compile)
5. Returns a `GenerationRunResponse` with the run ID, job IDs, and status

### Step 12h: Monitor the Run

After submission, the **Generation Run Card** appears showing:
- Generation ID
- Source and target project IDs
- Job IDs for each phase
- Status (queued → running → completed/blocked/failed)
- Warnings generated during execution
- Created artifacts (plans, drafts, manuscripts)

Click a run card to expand details. Use the **Gate Results** panel to see which consistency checks passed or failed.

### Step 12i: Review Gate Results

The **Generation Gate Panel** shows gate results for each artifact:

- **Gate Name** — e.g., `plan_references_known_canon`, `chapter_canon_congruence`, `manuscript_canon_congruence`
- **Passed** — true/false
- **Severity** — info, warning, or blocking
- **Reasons** — specific contradictions or violations detected
- **Repair Attempted** — whether the system tried to fix violations (per policy)

Failed gates link to the Inspect view for deep debugging. Repair actions are available when your continuity strictness policy allows them.

### Step 12j: Fork Preview (Optional)

Before committing to a fork, click **"Preview Fork"** to see exactly what would be copied:
- Selected character IDs and their remapped target IDs
- Selected world Bible entries
- Arcs and continuity threads
- Foundation profile that will be created in the target project

This is read-only — no projects or data are modified.

### Step 12k: Fork Project Only (Without Generation)

If you want to fork canon into a new project without immediately running generation:

1. Configure mode, destination, and scope in the wizard
2. Click **"Fork Project Only"** instead of "Submit Run"
3. The system creates the target project with copied canon but no generation jobs
4. Navigate to the new project's workspace and run P-100 through P-400 manually

### Step 12l: Inspect a Generation Run

Generation runs produce inspectable artifacts:

1. From the Generate workspace, click **"Jump to Inspect"** on a run card
2. Or navigate directly to `/workspace/:projectId/inspect/:jobId`
3. The Inspect view shows:
   - Step timeline for each generation phase (G-200 through G-400)
   - Artifact lineage (packet → plan → drafts → manuscript)
   - Gate results with reasons and repair metadata
   - Execution logs

### What Happens Behind the Scenes (Generation Pipeline)

**G-200: Generation Plan**
The executor loads the canon packet and calls the LLM to generate a new story architecture. Output includes: premise, logline, story arcs, chapter plans, canon obligations (citing source canon IDs), and intentional differences from the source.

**G-300: Chapter Drafting Loop**
For each planned chapter, the executor drafts prose with full context: character profiles (active characters only), world constraints, prior chapter summaries (last 3 max), and the generation brief. Each chapter produces a draft artifact and an auto-created ManuscriptDocument.

**G-350: Gate Checks**
The executor runs consistency checks on every generated artifact:
- Locked character facts are not contradicted
- Locked world facts are not contradicted
- Forbidden contradictions are absent from the text
If your policy allows repair, failed artifacts are sent to an LLM repair pass. The number of repair attempts is governed by continuity strictness.

**G-400: Manuscript Assembly**
The executor assembles the final manuscript from all chapter drafts. This phase only runs if no blocking gates failed. If blocking gates failed, the run status becomes `blocked`.

### Troubleshooting Story Generation

| Issue | Solution |
|-------|----------|
| Run fails with "source project not found" | Verify the source project ID is correct and exists |
| Gate results show many contradictions | Relax locked fields or add allowed changes to the canon policy |
| Generation is too slow | Reduce canon scope (fewer characters/world entries) or chapter count |
| Forked project has missing relationships | Relationships are only copied if both endpoint characters are selected |
| Idempotency conflict (409) | Same idempotency key with different payload. Use a new key or match the original payload exactly |
| Run is "blocked" after G-350 | Blocking gate failed and repair policy was exhausted. Review gate results, fix policy, and retry |
| Packet exceeds budget warning | The system auto-truncates to 120K chars. Reduce scope for full fidelity |

---

## Phase 13: Canon Workshop

> **Bridge from Story Generation:** While you can visit the Canon Workshop at any time, the most impactful time to use it is *before* launching a generation run (Phase 12). Lock critical facts, set your policy, and preview your packet — this prevents wasted runs on contradictory content.

### Step 13: Open the Canon Workspace

**Route**: `/workspace/:projectId/canon`

The Canon Workspace is where you edit extracted canon material, classify fields for generation control, manage mythos and pattern entries, and create reusable generation profiles.

### Step 13a: Overview Tab

1. Navigate to `/workspace/:projectId/canon`
2. The **Overview** tab shows summary counts:
   - Characters, world bible entries, mythos entries, pattern entries
   - Canon annotations (locked, soft guidance, mutable, forbidden)
   - Saved customization profiles
3. Click **"New Profile"** to create a reusable generation configuration

### Step 13b: Characters Tab with Annotations

1. Click the **Characters** tab
2. Browse character profiles in card view
3. Click a character to open the editor
4. Use the **Canon Annotation Toolbar** on any field:
   - Click the annotation icon next to a field
   - Select classification: `locked`, `soft_guidance`, `mutable`, or `forbidden_contradiction`
   - Optionally add a note explaining why
   - Optionally scope to specific generation modes (e.g., lock backstory for sequels only)
5. Locked fields display a lock badge; they become hard constraints during generation

### Step 13c: World Bible Tab with Annotations

1. Click the **World** tab
2. Browse world bible entries by type
3. Edit any entry and use annotation controls on: title, summary, canonical facts, continuity warnings
4. Mark critical facts as `locked` or specific phrases as `forbidden_contradiction`

### Step 13d: Mythos Library Tab

1. Click the **Mythos** tab (or navigate to `?tab=mythos`)
2. Browse mythos entries by type: archetype, motif, cosmic_rule, symbol, ritual, deity, cycle, theme
3. Edit any entry: add canonical facts, refine pattern notes, set generation guidance
4. Use **"Use in Generation"** checkbox to include entries in canon scope
5. Filter by type using the filter chips at the top

### Step 13e: Pattern Library Tab

1. Click the **Patterns** tab (or navigate to `?tab=patterns`)
2. Browse pattern entries by type: plot, character, relationship, world, theme, scene, structure
3. Edit any pattern: add beats, constraints, transposition notes
4. Set which generation modes the pattern applies to
5. Use **"Use in Generation"** checkbox to include patterns in canon scope

### Step 13f: Generation Rules Tab

1. Click the **Generation Rules** tab
2. Configure canon policy rules:
   - **Locked Character Fields** — fields that cannot be contradicted (default: display_name, role_in_story, backstory, voice_notes, continuity_facts, relationships)
   - **Locked World Fields** — immutable world facts (default: entry_type, title, summary, canonical_facts)
   - **Allowed Changes** — explicitly permitted modifications
   - **Forbidden Contradictions** — specific phrases that must not appear
   - **Continuity Strictness** — warn, block, repair_once, or repair_twice

### Step 13g: Canon Customization Profiles

1. Click **"New Profile"** in the Overview tab
2. Fill in:
   - **Name** — e.g., "Sequel with Locked Characters"
   - **Description** — what this profile is for
   - **Default Generation Mode** — sequel, prequel, side_story, etc.
   - **Canon Scope** — select characters, world entries, mythos, and patterns
   - **Canon Policy** — locked fields, allowed changes, forbidden contradictions, strictness
   - **Generation Brief Template** — reusable brief text
3. Click **"Save"**
4. Later, select a saved profile and click **"Preview Packet"** → **"Submit Generation"**

### Step 13h: Packet Preview Tab

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

### Workflow F: Import Source Story, Generate Sequel, Fork to New Project

This workflow demonstrates the full story generation pipeline from import through forking:

1. **Import a source story** — paste an existing completed story via `POST /projects/import-story` or the frontend import modal
2. **Review the imported project** — verify characters, world bible, arcs, and foundation are correctly extracted
3. **Navigate to Generate workspace** — `/workspace/:projectId/generate`
4. **Configure the wizard:**
   - Mode: `new_project_character_fork`
   - Destination: New Project named "Sequel: [Name]"
   - Canon Scope: select all major characters and key world entries
   - Brief: "Write a sequel set 5 years after the original story. The protagonist has retired but is drawn back when new threats emerge."
   - Policy: continuity strictness = `warn`, forbidden contradictions listing resolved plot points from the original
   - Chapter count: 8
5. **Preview the fork** — verify selected characters, world entries, and arcs will be copied correctly
6. **Submit the run** — the system creates the target project, copies canon, and queues G-200 through G-400
7. **Monitor progress** — watch run status transition from queued → running → completed (or blocked)
8. **Review gate results** — check for any warnings about canon contradictions
9. **Navigate to the new project** — explore the generated sequel in its own workspace
10. **Iterate** — adjust policy, retry failed runs, or run manual P-phases for refinement

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

### Story Generation Issues

- **Run status stays "queued".** The LocalExecutor may not be running or the inference backend is unavailable. Check `GET /health/ready` and verify your model server is accessible.
- **Gate results show contradictions for accurate content.** The gate checks are text-based substring matches. If a locked fact contains a phrase that legitimately appears in context (e.g., "the king died" as historical background vs. as a current event), add that phrase to `allowed_character_changes` or relax the locked field.
- **Forked project has fewer characters than selected.** Character copy only includes characters whose IDs match exactly. Check that your canon scope character IDs match the IDs in your Characters tab.
- **Idempotency conflict (HTTP 409).** You re-submitted a generation request with the same idempotency key but different payload. The system uses SHA-256 hashing to detect this. Either omit the idempotency key for a new run, or match the original payload exactly.
- **Generation takes too long.** Large canon packets (many characters, world entries) increase prompt size and LLM latency. Reduce scope to only essential elements. Also check that your inference backend has sufficient VRAM and isn't throttled.

### Canon Workshop Issues

- **Annotations don't persist after reload.** Check that the annotation was saved (toolbar shows a checkmark). Unsaved annotations are lost on navigation. Verify `GET /v1/canon/annotations?project_id={id}` returns the expected data.
- **Packet preview doesn't include selected entries.** Ensure "Use in Generation" is checked for each entry. Unchecked entries are excluded from the packet regardless of profile settings.
- **Profile can't be saved.** Verify that at least one canon scope category has selections (characters, world, mythos, or patterns). Empty profiles are rejected.
- **Mythos/pattern entries don't appear after extraction.** Extraction creates project-level data but may not auto-materialize editable records. Call `POST /v1/mythos/materialize-extraction` or `POST /v1/patterns/materialize-extraction` to create editable entries from extraction results.

### Manuscript Assist Issues

- **Assist request fails with "selection not found".** The selected text no longer matches the document (you edited it after requesting). Re-select the text and re-submit the assist.
- **Apply suggestion returns 409 Conflict.** Document version mismatch — another edit happened between requesting and applying. Refresh the editor, re-request the assist, and try again.
- **Suggestion shows "blocking" canon risk.** The proposed text contradicts a locked canon fact. Either relax the locked field in Canon Workshop, or reject the suggestion and edit manually.
- **Fork from Selection creates empty branch.** Ensure the selected text is meaningful (at least a paragraph). Very short selections may not produce useful fork content.
- **Assist runs stay "queued".** Same as generation — check `GET /health/ready` and verify your inference backend is running. M-500 jobs require a configured inference URL.

### Branch State Management

- ACTIVE branches can be edited
- MERGED branches are read-only (consolidated into target)
- ARCHIVED branches are preserved for reference but not editable
