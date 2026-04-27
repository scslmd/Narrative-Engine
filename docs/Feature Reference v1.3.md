# Narrative Engine - Feature Reference v1.3

Complete reference for every feature in Narrative Engine, with descriptions, backend APIs, and usage examples.

---

## Table of Contents

- [Project Management](#project-management)
  - [Story Import](#story-import)
- [Planning Workspace](#planning-workspace)
  - [Manifest Viewer](#manifest-viewer)
  - [Planning (Sequences, Chapters, Scenes)](#planning-sequences-chapters-scenes)
  - [Flow Editor](#flow-editor)
  - [Arcs](#arcs)
  - [Branches](#branches)
  - [Decision Tree](#decision-tree)
  - [Role Model Checker](#role-model-checker)
  - [Brainstorm Workspace](#brainstorm-workspace)
  - [Foundation Editor](#foundation-editor)
  - [Character Builder](#character-builder)
  - [World Bible](#world-bible)
- [Mythos Extraction](#mythos-extraction)
- [Pattern Extraction](#pattern-extraction)
- [Writing Workspace](#writing-workspace)
  - [Draft Management](#draft-management)
  - [Manuscript Review](#manuscript-review)
- [Storyboard Workspace](#storyboard-workspace)
- [Review Workspace](#review-workspace)
- [Inspect Mode](#inspect-mode)
- [Brain Dump Mode](#brain-dump-mode)
- [Job Management](#job-management)
- [Global Features](#global-features)

---

## Project Management

### What It Does

Project management is the entry point of Narrative Engine. Each project is an independent story workspace with its own metadata, generated artifacts, and AI execution history.

### How to Use

**Create a Project:**
```
1. Navigate to the home page (/)
2. Fill the creation form:
   - Project Name (required): "The Last Archive"
   - Genre (required): "Science Fiction"
   - Tone Profile (required): "Contemplative"
   - Story Structure (required): "Seven Point Structure"
   - POV (required): "Third Limited"
   - Primary Language (required): "English"
   - Secondary Language (optional): "" or "Spanish"
   - Premise (optional): Brief story description
3. Click Create
```

**Delete a Project:**
```
1. Find the project card on the home page
2. Click the delete action
3. Confirm deletion
```

### Backend APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects/create` | Create a new project |
| `GET` | `/projects/{project_id}` | Get project details |
| `DELETE` | `/projects/{project_id}` | Delete a project |
| `GET` | `/v1/projects/{project_id}/manifest` | Get project manifest |

### Story Import

**Import an Existing Story:**
```
1. Navigate to Project Management
2. Click "Import Story"
3. Paste the story text (or upload a file)
4. Optionally specify genre hint and tone hint for analysis
5. The LLM analyzes the story and extracts:
   - Premise, logline, thematic spine
   - Characters with goals, motivations, arcs
   - World bible entries
   - Structural breakdown (acts, sequences, chapters)
6. A new project is created with all extracted data
```

**Backend APIs**
```
POST /projects/import-story (201 Created, synchronous)
```

### Story Structures Reference

| Structure | Description | Best For |
|-----------|-------------|----------|
| `SAVE_THE_CAT` | Hero saves something/someone against odds | Action, adventure |
| `THREE_ACT` | Setup, confrontation, resolution | Classic narratives |
| `HERO_JOURNEY` | Departure, initiation, return | Epic fantasy, quest |
| `FREYTAGS_PYRAMID` | Exposition, rising action, climax, falling action, denouement | Literary fiction |
| `KISHOTENKETSU` | Introduction, development, twist, conclusion | Asian storytelling |
| `FICHTEAN_CURVE` | Equilibrium, disturbance, escalation, climax, resolution | Drama |
| `SEVEN_POINT_STRUCTURE` | Hook, plot twist 1, pin 1, midpoint, pin 2, plot twist 2, climax | Commercial fiction |
| `SEVEN_KEY_STEPS` | Seven essential story beats | Screenwriting |
| `SNOWFLAKE_METHOD` | Progressive expansion from sentence to full synopsis | Complex plotting |
| `BRAINDUMP` | Unstructured ideation, no fixed structure | Brainstorming, exploratory writing |
| `OTHER` | Custom or undefined structure | Special cases |

### POV Modes Reference

| Mode | Description |
|------|-------------|
| `First` | "I walked into the room..." |
| `Second` | "You walk into the room..." |
| `Third_Limited` | "She walked into the room" (follows one character's perspective) |
| `Third_Omni` | Omniscient narrator knowing all thoughts |
| `Third_Objective` | Fly on the wall, no internal thoughts |
| `Third_Multiple` | Third person rotating between multiple characters |
| `Other` | Custom POV |

---

## Planning Workspace

Route: `/workspace/:projectId/plan`

The Planning workspace is the central hub for story development. It contains 11 tabs covering every aspect of narrative construction.

---

### Manifest Viewer

**What It Does**

Displays the project's manifest -- the core metadata contract that guides all AI generation. The manifest defines genre, tone, structure, POV, and language settings.

**How to Use**

Navigate to Planning mode and view the Manifest tab. This is a read-only display of your project's current configuration. The manifest is set when you create the project and can be reviewed but not directly edited from the UI.

**Example Manifest**
```
Project: The Last Archive
Genre: Science Fiction
Tone Profile: Contemplative
Story Structure: Seven Point Structure
POV: Third Limited
Primary Language: English
Secondary Language: None
```

**Backend API**
```
GET /v1/projects/{project_id}/manifest
```

---

### Planning (Sequences, Chapters, Scenes)

**What It Does**

Displays the hierarchical planning artifacts generated by the P-100 Architect and P-200 Sequencer jobs:

- **Sequences:** Major story sections with beat plans (key moments within each sequence)
- **Chapters:** Individual chapters assigned to sequences, with objectives, conflict, and stakes
- **Scenes:** Scenes within chapters
- **Dependencies:** Upstream/downstream relationships between planning elements
- **Chapter Packets:** Reference bundles prepared for drafting each chapter

**How to Use**

1. After running a P-100 job, navigate to the Planning tab
2. Review the generated sequences -- these are the major act divisions
3. Click into sequences to see beat plans (key moments within each sequence)
4. Review chapters assigned to each sequence
5. Check dependencies to understand how chapters relate to each other
6. View chapter packets to see what reference materials are prepared for drafting

**Example Planning Structure**
```
Sequence 1: The Discovery
  Beats:
    - Elara finds the first altered record
    - She notices inconsistencies in the archive
  Chapter 1: The Broken Record
    Objective: Introduce Elara and the archive
    Conflict: Something is wrong with the records
    Stakes: Her career depends on accuracy
  Chapter 2: Patterns in the Noise
    Objective: Elara identifies the erasure pattern
    Conflict: She's being watched
    Stakes: Personal safety

Sequence 2: The Investigation
  ...
```

**Backend APIs**
```
GET /v1/story-development/planning/sequence-plans?project_id={id}
GET /v1/story-development/planning/chapter-plans?project_id={id}
GET /v1/story-development/planning/scene-plans?project_id={id}
GET /v1/story-development/planning/dependencies?project_id={id}
GET /v1/story-development/planning/chapter-packets?project_id={id}
```

---

### Flow Editor

**What It Does**

Configures the story development pipeline -- the ordered sequence of stages that guide your project from ideation to finished manuscript. Each stage can be customized with display name, description, dependencies, custom prompt guidance, and configuration state (enabled, disabled, archived, optional).

**How to Use**

1. Navigate to the Flow tab
2. Review the default stages: Brainstorm, Foundation, Characters, World Bible, Arc Selection, Planning, Drafting, Review
3. **Add a stage:** Click "Add Stage", fill in name, kind, and optional details
4. **Edit a stage:** Click on a stage to modify its properties
5. **Reorder:** Drag stages to change the pipeline order
6. **Rename:** Click the stage name to edit inline
7. **Disable:** Set stage configuration to "Disabled" to skip it in future jobs
8. **Archive:** Set stage configuration to "Archived" to remove it from active view
9. **Delete:** Remove a stage entirely

**Available Stage Kinds**
```
brainstorm, foundation, character, world_bible, arc_selection,
planning, drafting, review
```

**Example Custom Flow**
```
1. Brainstorm (enabled)
2. Foundation (enabled)
3. Character Development (enabled, custom prompt: "Focus on internal arcs")
4. World Bible (enabled)
5. Arc Selection (enabled)
6. Sequence Planning (enabled)
7. Chapter Drafting (enabled)
8. Beta Reader Review (enabled, custom prompt: "Check for pacing issues")
9. Final Polish (enabled)
10. Review (enabled)
```

**Backend APIs**
```
GET /v1/story-development/flow/stages?project_id={id}
POST /v1/story-development/flow/stages
PATCH /v1/story-development/flow/stages/{stage_id}?project_id={id}
DELETE /v1/story-development/flow/stages/{stage_id}?project_id={id}
POST /v1/story-development/flow/stages/reorder?project_id={id}
```

**Stage Configuration States**
| State | Meaning |
|-------|---------|
| `ENABLED` | Stage is active in the pipeline |
| `DISABLED` | Stage is skipped in the pipeline |
| `OPTIONAL` | Stage may be included but is not required |
| `ARCHIVED` | Stage is removed from active view |

---

### Arcs

**What It Does**

Manages narrative arcs -- the trajectories that connect story events to character development. Arcs are proposed as candidates, one is selected as active, and each has a stage map showing how the arc progresses through flow stages.

**How to Use**

1. Navigate to the Arcs tab
2. Review **Arc Candidates** -- AI-proposed narrative trajectories based on your foundation and characters
3. For each candidate, review:
   - **Summary:** What happens in this arc
   - **Fit Notes:** How well it matches your foundation
   - **Tags:** Classification tags for the arc
4. Review the **Arc Comparison Records** -- side-by-side comparisons of candidates
5. Review the **Arc Selections** -- which arcs have been accepted or rejected
6. Select an arc to make it active

**Example Arc Candidate**
```
Name: "The Memory Recovery Arc"
Summary: "Elara progressively recovers erased memories, each one revealing a piece of the conspiracy, until she has the complete picture needed to confront Joss."
Fit Notes: "Strong alignment with thematic spine about memory and identity. The progressive recovery structure matches the Seven Point Structure perfectly."
Tags: ["mystery", "character-driven", "revelation"]
```

**Backend APIs**
```
GET  /v1/story-development/arcs/candidates?project_id={id}
POST /v1/story-development/arcs/candidates
GET  /v1/story-development/arcs/selections?project_id={id}
POST /v1/story-development/arcs/selections
PATCH /v1/story-development/arcs/selections/{selection_id}?project_id={id}
DELETE /v1/story-development/arcs/selections/{selection_id}?project_id={id}
GET  /v1/story-development/arcs/stage-maps?project_id={id}
POST /v1/story-development/arcs/stage-maps?project_id={id}
POST /v1/story-development/arcs/comparisons
```

**How to Use Arc Selections:**

1. Navigate to the Arcs tab
2. Review **Arc Candidates** -- AI-proposed narrative trajectories based on your foundation and characters
3. Optionally **Compare** multiple candidates using the comparison endpoint (requires minimum 2 candidates)
4. **Select** an arc to make it active, optionally rejecting other candidates
5. **Update** selection notes or stage map via PATCH
6. **Delete** a selection if it was made in error
7. Review **Arc Stage Maps** -- stage-by-stage breakdown for selected arcs
8. **Create** or update stage maps for any arc candidate

---

### Branches

**What It Does**

Implements Git-like branching for narrative exploration. Create alternate versions of your story, compare them side-by-side, and merge elements from different branches.

**How to Use**

**Create a Branch:**
```
1. Navigate to the Branches tab
2. Click "Create Branch"
3. Fill in:
   - Branch Name: "Dark Ending"
   - Parent Branch: (leave empty for main, or select a parent)
   - Description: "Elara fails to stop the erasure"
4. Click Create
```

**Set Active Branch:**
```
1. Click "Set Active" on the branch you want to work on
2. All subsequent job runs and generation will apply to this branch
```

**Compare Branches:**
```
1. Select two branches
2. Click "Compare"
3. Review the comparison with review notes
```

**Merge Decision:**
```
1. After reviewing a comparison
2. Click "Record Merge Decision"
3. Fill in:
   - Selected Branch: Which branch's elements to borrow
   - Rationale: Why this choice
   - Notes: Additional context
```

**Example Branch Workflow**
```
Main Branch:
  - Elara seals the rift, saves the archive
  - Ends on hope

Branch "Dark Ending":
  - Elara fails, the Authority wins
  - Ends on ambiguity

Branch "Compromise":
  - Elara exposes the conspiracy but can't fully reverse it
  - Ends on bittersweet note

Merge Decision:
  - Take the confrontation scene from "Dark Ending"
  - Take the emotional resolution from "Main"
  - Create a new combined ending
```

**Backend APIs**
```
GET /v1/story-development/branches?project_id={id}
POST /v1/story-development/branches
GET /v1/story-development/branches/active?project_id={id}
POST /v1/story-development/branches/active
POST /v1/story-development/branches/comparisons
GET /v1/story-development/branches/comparisons?project_id={id}
POST /v1/story-development/branches/merge-decisions
GET /v1/story-development/branches/merge-decisions
GET /v1/story-development/branches/{branchId}/state-refs
```

**Branch States**
| State | Meaning |
|-------|---------|
| `ACTIVE` | This branch is currently selected for work |
| `MERGED` | Elements from this branch have been incorporated |
| `ARCHIVED` | This branch is no longer active |

---

### Decision Tree

**What It Does**

Visualizes and manages the narrative decision tree -- a graph of creative choices with labeled options, parent-child relationships, and traced paths from root to any node.

**How to Use**

1. Navigate to the Decisions tab
2. View the decision tree visualization
3. Each node represents a decision point
4. Each edge represents an option
5. Click a node to see its path from the root

**Example Decision Tree**
```
Root: "How does the story begin?"
  ├─ Option A: "In medias res - start with the discovery"
  │   └─ Sub-decision: "What is discovered?"
  │       ├─ Altered record
  │       └─ Missing record
  └─ Option B: "Establishing shot - show the archive first"
      └─ Sub-decision: "Through whose eyes?"
          ├─ Elara
          └─ A patron
```

**Backend APIs**
```
GET /v1/story-development/decisions?project_id={id}
GET /v1/story-development/decisions/{node_id}?project_id={id}
GET /v1/story-development/decisions/{node_id}/path
```

---

### Role Model Checker

**What It Does**

Runs AI analysis against your project's narrative from multiple professional perspectives. Each "role" represents a different area of narrative expertise (plottter, character analyst, consistency checker, etc.).

**How to Use**

1. Navigate to the Checker tab
2. **Select models** for each role from the model catalog (discovered via `/models`)
3. Click **"Run Checker"** to start the analysis
4. Monitor progress in real-time (status: QUEUED → RUNNING → COMPLETED/FAILED)
5. If a run fails, click **"Retry"** to re-run

**Example Configuration**
```
Role: Plottter → Model: "llama-3.1-70b"
Role: Character Analyst → Model: "llama-3.1-70b"
Role: Consistency Checker → Model: "mistral-large"
Role: Tone Monitor → Model: "llama-3.1-70b"
Role: Pacing Reviewer → Model: "gpt-4o"
```

**Backend APIs**
```
GET /models                          # Discover available models
POST /role-model-checker/run         # Start a checker run
GET /role-model-checker/{runId}/status    # Check run status
POST /role-model-checker/{runId}/retry  # Retry a failed run
GET /role-model-checker/{runId}/attempts  # View run attempts
```

**Checker Run Status Values**
| Status | Meaning |
|--------|---------|
| `QUEUED` | Run is waiting for execution |
| `RUNNING` | Run is in progress |
| `COMPLETED` | Run finished successfully |
| `FAILED` | Run failed (can be retried) |

---

### Brainstorm Workspace

**What It Does**

An interactive brainstorming board for capturing, organizing, and promoting ideas. Items can be tagged by type, clustered together, and promoted to target story elements.

**How to Use**

**Add an Idea:**
```
1. Navigate to the Brainstorm tab
2. Type your idea in the input field
3. Select the type from the dropdown
4. Click "Add"
```

**Item Types**
| Type | Description |
|------|-------------|
| `CHARACTER` | Character ideas (names, traits, arcs) |
| `LOCATION` | Place or setting ideas |
| `PLOT_POINT` | Plot event or twist ideas |
| `THEME` | Thematic concept ideas |
| `CONFLICT` | Conflict or tension ideas |
| `WORLD_BUILDING` | World lore and rules |
| `DIALOGUE` | Dialogue snippets or voice notes |
| `RELATIONSHIP` | Character relationship ideas |
| `OBJECT` | Important object or artifact |
| `RULE` | World rule or constraint |

**Cluster Items:**
```
1. Select multiple items (checkbox)
2. Click "Cluster"
3. Give the cluster a name
4. Clustered items are grouped for easier management
```

**Promote Items:**
```
1. Select an item
2. Click "Promote"
3. Choose target:
   - Foundation revision
   - Character profile
   - World Bible entry
   - Plot point
4. The item becomes part of the target artifact
```

**Example Brainstorm Session**
```
Items:
  [CHARACTER] "Elara has synesthesia - she sees memories as colors"
  [LOCATION] "The archive has a room where erased people's faces are frozen on walls"
  [PLOT_POINT] "The twist: the Archive Authority was created by the erased people themselves"
  [WORLD_BUILDING] "Memory crystals degrade after 100 years, becoming unreliable"
  [CONFLICT] "Elara's mentor is secretly part of the erasure program"

Clustering:
  Cluster "Elara's Abilities":
    - Synesthesia idea
    - Memory crystal degradation (relates to her ability to detect alterations)

Promotion:
  "Elara has synesthesia" → Character Profile (Elara Voss) → Contradictions
  "The frozen faces room" → World Bible Entry (Location: Silent Ward)
```

**Backend APIs**
```
GET /v1/story-development/brainstorm/items?project_id={id}
POST /v1/story-development/brainstorm/items
POST /v1/story-development/brainstorm/items/cluster
POST /v1/story-development/brainstorm/items/promote
GET /v1/story-development/brainstorm/promotions?project_id={id}
```

**Brainstorm Item Status**
| Status | Meaning |
|--------|---------|
| `KEEP` | This idea is valuable and should be developed |
| `DISCARD` | This idea is not useful |
| `PARK` | This idea is on hold for later consideration |

---

### Foundation Editor

**What It Does**

A form-based editor for the project's narrative foundation profile -- the detailed "north star" that guides all AI generation. Tracks revision history and surfaces review cues when foundation changes impact other artifacts.

**How to Use**

1. Navigate to the Foundation tab
2. Fill in the fields:
   - **Premise:** One-sentence core concept
   - **Logline:** Expanded premise with protagonist and stakes
   - **Thematic Spine:** Core themes the story explores
   - **Emotional Promise:** What readers should feel
   - **Tone and Voice Direction:** Writing style guidance
   - **Target Audience:** Intended readership
   - **Narrative Constraints:** Rules the story must follow
   - **Complexity Level:** How complex the narrative should be
   - **Success Definition:** What "good" looks like for this story
3. Click **"Save"** to store the foundation

**Foundation Revisions Tab:**
```
1. Click "Revisions" tab
2. View the revision history (timestamped versions)
3. Click any revision to see its contents
4. Roll back to a previous version if needed
```

**Review Cues Tab:**
```
1. Click "Review Cues" tab
2. Review items that flag when foundation changes affect other artifacts
3. Check which elements need updating after a foundation change
```

**Example Foundation**
```
Premise: In a future where human memories can be stored in crystalline archives, an archivist discovers that someone is systematically erasing entire life histories to rewrite history.

Logline: When Dr. Miren Kael, a meticulous archivist, uncovers evidence of systematic memory erasure, she must choose between reporting it through the established channels (and risking being silenced) or going underground to protect the last unaltered memories.

Thematic Spine: The weight of memory; who controls the past controls the future; the morality of forgetting; whether some truths are too dangerous to preserve.

Emotional Promise: Intellectual mystery with emotional depth. Readers should feel the thrill of discovery, the discomfort of unreliable narration, and the weight of responsibility that comes with knowledge.

Narrative Constraints:
- No deus ex machina solutions
- All character decisions must flow from established motivation
- Memory technology must have consistent rules and limitations
- No violence above blood level

Complexity Level: High (multiple plot threads, rotating POVs, non-linear elements)

Success Definition: A story that works as both a page-turning mystery and a meditation on memory and identity. Readers should finish it questioning their own relationship with their past.
```

**Backend APIs**
```
GET /v1/story-development/foundation?project_id={id}
POST /v1/story-development/foundation
PATCH /v1/story-development/foundation?project_id={id}
GET /v1/story-development/foundation/revisions?project_id={id}
GET /v1/story-development/foundation/review-cues?project_id={id}
```

---

### Character Builder

**What It Does**

A comprehensive character management system. Create, edit, and organize character profiles with detailed psychological, biographical, and relational information.

**How to Use**

**Create a Character:**
```
1. Navigate to the Characters tab
2. Click "Add Character"
3. Fill in the profile fields:
```

**Character Profile Fields:**
| Field | Description | Example |
|-------|-------------|---------|
| **Display Name** | Character's name | "Dr. Miren Kael" |
| **Role** | Narrative role | "Protagonist" |
| **Archetype** | Story archetype | "The Scholar" |
| **External Goal** | What the character wants | "Expose the conspiracy" |
| **Internal Need** | What the character needs to grow | "Trust her own judgment" |
| **Misbelief** | False belief holding them back | "Following evidence is enough" |
| **Core Fear** | Deepest fear | "Being complicit through silence" |
| **Primary Strength** | Key capability | "Pattern recognition" |
| **Fatal Flaw** | Critical weakness | "Emotional detachment" |
| **Contradictions** | Conflicting traits | "Meticulous but impulsive under stress" |
| **Backstory Summary** | Key life events before story | "Grew up in the archive..." |
| **Voice Notes** | How the character speaks | "Precise, measured, uses technical terms" |
| **Secrets** | Hidden information | "Knows more about the erasure than she admits" |
| **Values** | Core principles | "Truth, accuracy, protecting the vulnerable" |
| **Taboos** | Things they will never do | "Manipulate others' memories" |
| **Change Axis** | How they transform | "From detached observer to active participant" |
| **Arc Stage Notes** | Current position in character arc | "Just beginning to question authority" |
| **Continuity Facts** | Fixed facts that must not change | "Always wears a silver locket" |

**Manage Relationships:**
```
1. In a character's profile, scroll to Relationships
2. Click "Add Relationship"
3. Fill in:
   - Target Character: "Joss Vallen"
   - Relation Kind: "Antagonistic"
   - Summary: "Former mentor who now leads the erasure program"
   - Tension: "High"
   - Notes: "Joss believes he's doing the right thing"
4. Click "Save"
```

**Example Character Profile**
```
Name: Dr. Miren Kael
Role: Protagonist
Archetype: The Scholar
External Goal: Expose the memory erasure conspiracy and protect the last unaltered archive
Internal Need: Learn to trust her own judgment over archived records
Misbelief: If I follow the evidence logically, the truth will protect me
Core Fear: Being complicit through silence
Primary Strength: Meticulous pattern recognition and cross-reference analysis
Fatal Flaw: Emotional detachment as a coping mechanism
Contradictions: Craves connection but maintains professional distance
Backstory: Grew up in the Grand Archive; her parents were both archivists; learned to read before she could write
Voice Notes: Speaks precisely, uses technical terminology, pauses before emotional statements
Secrets: She found the first altered record but didn't report it immediately
Values: Truth, accuracy, intellectual honesty, protecting historical record
Taboos: Never alter a record, never lie about facts, never ignore evidence
Change Axis: Detached archivist → Active investigator → Courageous truth-teller
Continuity Facts: Always wears a silver locket containing her parents' combined memory crystal
```

**Backend APIs**
```
GET /v1/story-development/characters?project_id={id}
GET /v1/story-development/characters/{character_id}?project_id={id}
POST /v1/story-development/characters
PATCH /v1/story-development/characters/{character_id}?project_id={id}
GET /v1/story-development/characters/{character_id}/relationships?project_id={id}
POST /v1/story-development/relationships
```

---

### World Bible

**What It Does**

An editable encyclopedia for tracking all world-building elements: locations, organizations, technology, rules, concepts, creatures, history, and more. Supports grouping by type, canonical fact tracking, and continuity management.

**How to Use**

**Add an Entry:**
```
1. Navigate to the World Bible tab
2. Click "Add Entry"
3. Fill in:
   - Entry Type: Location, Concept, Rule, Organization, Technology, Event, etc.
   - Title: "Memory Crystals"
   - Content: Detailed description
4. Optional fields:
   - Canonical: Mark as confirmed fact
   - Related Characters: Link characters who know/about this
   - Source Artifacts: Link to documents that describe this
   - Visibility: Who in-world knows this fact
   - Continuity Warnings: Note any potential conflicts
5. Click "Save"
```

**Entry Types**
| Type | Description | Example |
|------|-------------|---------|
| `LOCATION` | Places and settings | The Grand Archive |
| `CONCEPT` | Ideas and theories | Identity Drift |
| `RULE` | Laws and constraints | The Three Laws of Memory |
| `ORGANIZATION` | Groups and institutions | The Archive Authority |
| `TECHNOLOGY` | Tools and systems | Chronos Interface |
| `EVENT` | Historical events | The Great Erasure of 2187 |
| `CREATURE` | Beings and entities | Echo Fragments |
| `ARTIFACT` | Objects and items | Memory Crystals |
| `CULTURE` | Social practices | Memory Remembrance Day |
| `HISTORY` | Historical timeline entries | Foundation Era |
| `MAGIC_SYSTEM` | Magical rules (if applicable) | N/A |
| `OTHER` | Uncategorized entries | N/A |

**Example World Bible Entries**
```
Entry 1:
  Type: Technology
  Title: Memory Crystals
  Content: Pearlescent crystalline structures that can store, retrieve, and transfer human memories. Each crystal can hold approximately 40 years of continuous memory. Crystals are created through the Extraction Process, which requires specialized equipment and a consenting subject. Crystals degrade after approximately 100 years, becoming increasingly unreliable.
  Canonical: Yes
  Related Characters: All Archivists
  Visibility: Public knowledge

Entry 2:
  Type: Rule
  Title: The Three Laws of Memory
  Content: 1) A memory cannot be created from nothing (only extracted or altered). 2) Erasure of a memory chain requires all linked memories to be removed (causality preservation). 3) No more than 30% of a population's memories can be altered in a single operation without causing systemic Identity Drift.
  Canonical: Yes
  Related Characters: All characters
  Visibility: Archive Authority internal

Entry 3:
  Type: Location
  Title: The Silent Ward
  Content: A restricted sub-level of the Grand Archive where people who have been fully erased are temporarily held before final processing. The ward is soundproofed and windowless. Erased individuals retain minimal cognitive function but have no episodic memory. Families are not notified.
  Canonical: Yes
  Related Characters: Joss Vallen (oversight), Elara Kael (discovers this location)
  Visibility: Archive Authority only
  Continuity Warning: Must be consistent with the Three Laws of Memory
```

**Backend APIs**
```
GET /v1/story-development/world-bible?project_id={id}
GET /v1/story-development/world-bible/{entry_type}/{title}?project_id={id}
POST /v1/story-development/world-bible
PATCH /v1/story-development/world-bible/{entry_type}/{title}?project_id={id}
```

---

## Mythos Extraction

Mythos Extraction analyzes mythology texts and extracts archetypal patterns, narrative structures, cosmic rules, and symbolic motifs. These extracted patterns guide original story generation — either in the same mythological world, transposed to a new setting, or as pure pattern application.

### Accessing Mythos Extraction

From the Story Import modal, toggle between "Import Story" and "Extract Mythos" modes. The Extract Mythos mode provides:
- **Source Tradition** — Optional text field to hint at the mythology (e.g., "Greek Mythology"). If omitted, the LLM identifies it from the text.
- **Generation Mode** — Three options: Same World, Transposed, or Pure Pattern (see below).
- **Mythos Text** — Paste mythology texts, mythological accounts, or source material for analysis.

### Generation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Same World | Keep the mythological setting; create original characters and plots following extracted patterns | Write new myths in an existing tradition |
| Transposed | Map archetypal patterns to a new setting | Apply Greek tragedy structure to a sci-fi world |
| Pure Pattern | Apply narrative structures and thematic constraints only; free-form world and genre | Use mythic storytelling DNA for any genre |

### What Gets Extracted

- **Archetypal Patterns** — Character archetypes and their narrative beats (e.g., hubris-fall-redemption cycle)
- **Narrative Structures** — Story phases, tension curves, and resolution types from the source tradition
- **Cosmic Rules** — Immutable rules governing the mythological world and their enforcement mechanisms
- **Symbolic Motifs** — Recurring symbols, their meanings, and narrative functions
- **Key Entities** — Deities, locations, concepts, and forces with archetypal roles (same_world mode)
- **Entity Relationships** — Power dynamics and alliances between key entities

### Persistence Mapping

Extracted data populates existing project structures:
- Foundation Profile receives thematic spine, emotional promise, tone direction, and narrative constraints (archetypal patterns + narrative structures stored as JSON)
- World Bible receives cosmic rules and symbolic motifs as "concept" entries
- Character profiles receive archetypal pattern carriers (role: archetype)
- Key entities are routed to characters (deities/forces) or world bible (locations/concepts)

### Workflow

1. Paste mythology texts in the Extract Mythos modal
2. Optionally specify source tradition and select generation mode
3. System analyzes text via LLM and extracts patterns
4. New project is created with extracted foundation, world bible entries, archetypes, and entities
5. Proceed to Planning Workspace to build sequences and chapters guided by extracted patterns
6. P-100 Architect and P-300 Drafter apply mythos context based on selected generation mode

---

## Pattern Extraction

Pattern Extraction is the generalized service that analyzes any story or mythology text and extracts its "storytelling DNA" — archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities. Extracted patterns guide original story generation through three modes: same-world (use established world/characters), new-characters (same world, original cast), or transposed (map patterns to new setting).

Pattern Extraction generalizes Mythos Extraction: when `source_type` is `"mythology"`, the service delegates to `MythosExtractionService`. When `source_type` is `"narrative"`, it uses the narrative-specific extraction pipeline with additional voice profile, narrative pattern, and thematic constraint fields.

### Accessing Pattern Extraction

From the Story Import modal, toggle between "Import Story", "Extract Mythos", and "Extract Patterns" modes. The Extract Patterns mode provides:
- **Source Type** — Select `narrative` (fiction stories) or `mythology` (mythological texts). Determines which extraction pipeline is used.
- **Generation Mode** — Three options: Same World, New Characters, or Transposed (see below).
- **Source Corpus** — Optional label for the source material (e.g., "Dune", "The Lord of the Rings").
- **Story Text** — Paste any completed story text for analysis.

### Generation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Same World | Keep the source story's world; create original characters following extracted patterns | Write new stories in an established universe |
| New Characters | Same world, original cast fulfilling extracted archetypes | Fresh characters in a familiar setting |
| Transposed | Map archetypal patterns and voice to a new setting | Apply Dune's storytelling DNA to a cyberpunk world |

### What Gets Extracted

Shared across source types:
- **Archetypal Patterns** — Character archetypes and their narrative beats
- **Narrative Structures** — Story phases, tension curves, and resolution types
- **World Rules** — Governing rules of the story world and enforcement mechanisms
- **Symbolic Motifs** — Recurring symbols, meanings, and narrative functions
- **Key Entities** — Characters, locations, organizations with archetypal roles
- **Entity Relationships** — Connections between key entities

Narrative-specific additions (source_type = "narrative"):
- **Narrative Pattern** — pacing, chapter_structure, conflict_type, dialogue_style, scene_transition
- **Voice Profile** — narrative_voice, sentence_rhythm, descriptive_density, humor_level, emotional_temperature
- **Thematic Constraints** — theme, moral_stance, recurring_questions[], forbidden_elements[]

### Persistence Mapping

Extracted data populates existing project structures:
- Foundation Profile receives thematic spine, emotional promise, tone direction, and narrative constraints (archetypal patterns + narrative structures + thematic constraints stored as JSON)
- World Bible receives world rules as "World Rule: {rule}" concept entries; symbolic motifs as "Motif: {symbol}" concept entries
- Character profiles receive archetypal pattern carriers (role: archetype) and key entities with appropriate roles
- Entity relationships are persisted as relationship edges

### SceneContext Integration

SceneContext dataclass extended for pattern-guided generation:
- `pattern_guidance` — injects voice profile, world rules, and thematic constraints into P-100/P-300 prompts
- `author_prompt` — freeform per-chapter author direction injected before character/world context
- P-100 Architect prompt adapted with `_build_pattern_context_block()` for pattern context injection across 3 generation modes
- P-300 Drafter includes pattern guidance + per-chapter author direction via SceneContext

### Backend APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects/import-patterns` | Analyze story text and extract patterns, create project (201 Created) |
| `POST` | `/projects/{project_id}/extract-patterns` | Extract patterns from existing project's manuscript documents (201 Created) |

### Request Schema (`PatternExtractionRequest`)

```json
{
  "text": "Paste story text here...",
  "source_type": "narrative",
  "generation_mode": "same_world",
  "project_id": null,
  "source_corpus": "The Shining"
}
```

### Response Schema (`PatternExtractionResponse`)

```json
{
  "status": "completed",
  "project_id": "abc-123",
  "extraction": {
    "source_corpus": "The Shining",
    "archetypal_patterns": 4,
    "narrative_structures": 2,
    "world_rules": 3,
    "symbolic_motifs": 5
  },
  "error": null
}
```

### Workflow

1. Paste story text in the Extract Patterns modal
2. Select source type (narrative or mythology) and generation mode
3. Optionally specify source corpus label
4. System analyzes text via LLM and extracts patterns
5. New project is created with extracted foundation, world bible entries, character archetypes, voice profile, narrative patterns, and thematic constraints
6. Proceed to Planning Workspace to build sequences and chapters guided by extracted patterns
7. P-100 Architect and P-300 Drafter apply pattern context based on selected generation mode

---

## Writing Workspace

Route: `/workspace/:projectId/write` and `/workspace/:projectId/write/:chapterId`

### What It Does

A three-panel workspace for reading and reviewing generated manuscript content. Left sidebar shows manuscript documents and draft artifacts. Center panel displays the full text. Right sidebar (Aids Panel) shows revision suggestions, diff comparisons, and text selection history.

### How to Use

**Read a Manuscript:**
```
1. Navigate to Writing mode
2. Select a manuscript document from the left sidebar
3. Read the full chapter text in the center panel
4. The right sidebar shows AI-generated revision suggestions
```

**View Draft Artifacts:**
```
1. In the left sidebar, under "Drafts", find draft artifacts
2. Click a draft to expand and see actions
3. Each draft shows:
   - Title
   - Status badge (DRAFT, PROPOSED, CANONICAL, etc.)
   - Truncated content preview (when expanded)
```

**Create a Draft:**
```
1. In the Drafts section, click "+ New Draft"
2. Enter a title (required) and optional content
3. Click "Create" to save the draft artifact
4. The draft appears in the list with its status
```

**Promote a Draft to Manuscript:**
```
1. In the Drafts section, click a draft to expand
2. Click "Promote" to promote the draft to a manuscript document
3. The draft becomes a new manuscript version
```

**Use Revision Suggestions:**
```
1. In the Aids Panel (right sidebar), review each suggestion
2. Each suggestion has:
   - Type: Pacing, Tone, Consistency, Clarity, etc.
   - Severity: Low, Medium, High, Critical
   - Description: What to change and why
   - Suggested Text: The recommended revision
3. Accept a suggestion to incorporate it
4. Dismiss a suggestion to ignore it
```

**View Diff Comparisons:**
```
1. Select a manuscript document
2. In the Aids Panel, switch to "Diff" tab
3. View changes between versions with highlighted additions/deletions
```

**Example Manuscript Document**
```
Document: "Chapter 1 - The Broken Record"
  Version 1: Initial draft (12,400 words)
  Version 2: Revised after P-300 suggestions (13,200 words)
  Version 3: Revised after review findings (12,800 words)

Revision Suggestions for Version 3:
  [PACING] High severity: The middle section drags. Consider combining paragraphs 4-6.
  [TONE] Medium severity: Elara's internal monologue shifts from clinical to emotional too abruptly.
  [CONSISTENCY] Low severity: Chapter mentions "seven sub-levels" but foundation says "five major divisions."
```

**Backend APIs**
```
GET /v1/story-development/drafting/manuscript-documents?project_id={id}
GET /v1/story-development/drafting/manuscript-documents/{document_id}?project_id={id}
POST /v1/story-development/drafting/manuscript-documents
GET /v1/story-development/drafting/draft-artifacts?project_id={id}
GET /v1/story-development/drafting/draft-artifacts/{artifact_id}?project_id={id}
POST /v1/story-development/drafting/promote-draft
GET /v1/story-development/drafting/revision-suggestions?project_id={id}
POST /v1/story-development/drafting/revision-suggestions
```

### Draft Management

**Continue a Draft:**
```
1. In the left sidebar, expand a draft artifact
2. Click "Continue" to extend the draft with LLM-generated content
3. The LLM appends content from the last written position
4. A new draft version is created with the extended content
```

**Create an Alternate Variant:**
```
1. In the left sidebar, expand a draft artifact
2. Click "Alternate Variant" to generate a different version
3. The LLM rewrites the draft with a different approach while preserving structure
4. The original draft remains unchanged; the variant appears as a sibling
```

### Manuscript Review

**Score and Review Manuscripts:**
```
1. Select a manuscript document in the Writing workspace
2. Trigger a manuscript review to evaluate quality
3. Review receives scores for: prose quality, pacing, consistency, voice, dialogue
4. Scores appear in the Aids Panel alongside revision suggestions
5. Use review results to guide further revisions or promotions
```

---

## Storyboard Workspace

Route: `/workspace/:projectId/storyboard`

### What It Does

Kanban-style board for organizing scenes and story beats across columns. Each card represents a scene or beat with metadata, content preview, and status tracking. Supports drag-to-reorder and column-based organization.

### How to Use

**Create Storyboard Cards:**
```
1. Navigate to the storyboard view
2. Click "Add Card" in the desired column
3. Enter a title and optional summary for the scene/beat
4. The card appears in the column with its status
```

**Reorder Cards:**
```
1. Drag cards between columns to change status/phase
2. Use the reindex endpoint to save column ordering
3. Cards maintain their identity across moves
```

**Backend APIs**
```
GET /v1/story-development/storyboard/cards?project_id={id}
GET /v1/story-development/storyboard/cards/{card_id}?project_id={id}
POST /v1/story-development/storyboard/cards
PATCH /v1/story-development/storyboard/cards/{card_id}?project_id={id}
PUT /v1/story-development/storyboard/cards/{card_id}?project_id={id}
DELETE /v1/story-development/storyboard/cards/{card_id}?project_id={id}
PUT /v1/story-development/storyboard/cards/{column_id}/reindex?project_id={id}
```

---

## Review Workspace

Route: `/workspace/:projectId/review`

### What It Does

Central hub for reviewing AI-generated findings and making decisions on each. The Review workspace has two tabs: Findings (review AI analysis) and Inspect Run Links (navigate to source jobs).

---

### Findings Tab

**What It Does**

Displays AI-generated review findings from the Role Model Checker. Each finding has a severity level, summary, details, and source context.

**How to Use**

```
1. Navigate to Review mode → Findings tab
2. Filter by:
   - Source object kind (e.g., "ManuscriptDocument", "CharacterProfile")
   - Severity (Low, Medium, High, Critical)
3. Review each finding:
   - Read the summary and details
   - Check the source context (which chapter/character/element it references)
4. Make a decision:
   - Accept: Incorporate the suggested change
   - Reject: Deliberately ignore this finding
   - Defer: Address it later
   - Refine: Request more detail
   - Escalate: Mark as requiring immediate attention
```

**Finding Severity Levels**
| Severity | Meaning |
|----------|---------|
| `LOW` | Minor suggestion, cosmetic or optional |
| `MEDIUM` | Worth addressing, may improve quality |
| `HIGH` | Should be addressed, may affect reader experience |
| `CRITICAL` | Must be addressed, likely factual or logical error |

**Example Findings**
```
Finding 1:
  Severity: HIGH
  Source: ManuscriptDocument (Chapter 3)
  Summary: "Character motivation inconsistency in Chapter 3"
  Details: "Elara's decision to confront Joss directly contradicts her established caution from Chapter 1. No intermediate scene bridges this shift."
  Suggested Action: "Add a Chapter 2.5 scene where external pressure forces Elara's hand."

Finding 2:
  Severity: MEDIUM
  Source: CharacterProfile (Tessa Rowan)
  Summary: "Mentor has unexplained access to restricted areas"
  Details: "Tessa appears in the Silent Ward (restricted) without explanation of how she gained access."
  Suggested Action: "Add a foundation fact or world bible entry explaining Tessa's authority level."
```

**Backend APIs**
```
GET /v1/story-development/review/findings?project_id={id}
GET /v1/story-development/review/findings/{finding_id}?project_id={id}
GET /v1/story-development/review/decisions?project_id={id}
POST /v1/story-development/review/decisions
```

---

### Inspect Run Links Tab

**What It Does**

Lists connections between review findings and the inspection jobs that generated them. Clicking a link navigates to the Inspect view for deep debugging. You can also create new inspect run links to connect story objects to pipeline runs.

**How to Use**

```
1. Navigate to Review mode → Inspect Run Links tab
2. Click "+ New Link" to create a new inspect run link
3. Fill in the form:
   - Link ID: Unique identifier for this link
   - Object Kind: Type of story object (e.g., "chapter-plan")
   - Object ID: ID of the story object
   - Logical Run ID: Logical run identifier
   - Run ID: Pipeline job ID
   - Run Kind: Type of run (e.g., "pipeline_job")
4. Click "Create" to save
5. Filter existing links by object kind, object ID, or run ID
6. Click a link to navigate to the Inspect view
7. The Inspect view shows:
   - Step timeline
   - Artifact lineage
   - Attempt history
```

**Backend APIs**
```
GET /v1/story-development/review/inspect-links?project_id={id}
GET /v1/story-development/review/inspect-links/{link_id}?project_id={id}
```

---

## Inspect Mode

Routes: `/workspace/:projectId/inspect` and `/workspace/:projectId/inspect/:jobId`

### What It Does

Deep inspection of AI pipeline runs (both jobs and role model checker runs). When a job ID is in the URL route, it automatically resolves the job context and displays run details.

### How to Use

**Navigate to Inspect:**
```
1. From any workspace, navigate to /workspace/:projectId/inspect/:jobId
2. Or click "Inspect Run Link" from the Review workspace
3. The Inspect view resolves the job context automatically
```

**Step Timeline Tab:**
```
1. View each step of the job execution in chronological order
2. Each step shows:
   - Step name and type
   - Start and end timestamps
   - Status (SUCCESS, FAILED, SKIPPED)
   - Output summary
   - Executor identity
3. Click a step to see detailed logs
```

**Artifact Lineage Tab:**
```
1. View all artifacts created or modified by this job
2. Each artifact shows:
   - Artifact ID
   - Kind (SequencePlan, ChapterPlan, ManuscriptDocument, etc.)
   - State (DRAFT, PROPOSED, CANONICAL, etc.)
   - Provenance (which job created it)
   - Relationships to other artifacts
3. Click an artifact to trace its creation history
```

**Attempt History Tab:**
```
1. View all attempts for this job (including retries)
2. Each attempt shows:
   - Attempt number
   - Status (PENDING, PROCESSING, COMPLETED, FAILED)
   - Phase (P-100, P-200, P-300, P-400)
   - Error message (if failed)
   - Executor name and identity
   - Queue delay
   - Finish reason
   - Lease reclaim context
```

**Logs Tab:**
```
1. Read the raw job execution logs
2. Logs are streamed in real-time for active jobs
3. Logs include timestamps, levels (INFO, WARNING, ERROR), and messages
```

**Example Inspect View**
```
Job: P-300 Drafter - Chapter 1
Status: COMPLETED

Attempt History:
  Attempt 1: COMPLETED
    Executor: local_executor
    Queue Delay: 2.3 seconds
    Finish Reason: SUCCESS
    Steps: 12 (all succeeded)

Step Timeline:
  1. Load Chapter Plan (1.2s) - SUCCESS
  2. Load World Bible (0.8s) - SUCCESS
  3. Load Character Profiles (1.1s) - SUCCESS
  4. Generate Chapter Draft (45.3s) - SUCCESS
  5. Apply Foundation Constraints (3.2s) - SUCCESS
  6. Check Consistency (5.1s) - SUCCESS
  ...

Artifact Lineage:
  - Chapter 1 Draft (DRAFT) ← Created by this job
  - Chapter 1 Manuscript (PROPOSED) ← Generated by this job
  - Chapter 1 Revision Suggestions (DRAFT) ← Generated by this job
```

**Backend APIs**
```
GET /v1/jobs/{job_id}/status
GET /v1/jobs/{job_id}/steps
GET /v1/jobs/{job_id}/lineage
GET /v1/jobs/{job_id}/attempts
GET /v1/jobs/{job_id}/logs
GET /role-model-checker/{runId}/status
GET /role-model-checker/{runId}/steps
GET /role-model-checker/{runId}/lineage
GET /role-model-checker/{runId}/attempts
```

---

## Brain Dump Mode

Route: `/workspace/:projectId/braindump`

### What It Does

A free-form text canvas for unstructured idea capture. Write raw ideas without filtering, then use AI to organize them into categorized items.

### How to Use

**Create a Session:**
```
1. Navigate to Brain Dump mode
2. If no session exists, click "Create Session"
3. Give the session a name (e.g., "Story Ideas - Week 1")
```

**Write Ideas:**
```
1. Type in the large text canvas
2. Write freely -- no structure required
3. Examples:
   "What if gravity reversed every Tuesday?"
   "A character who can taste lies"
   "The library that only appears at midnight"
4. Click "Save" to store your draft
```

**Organize Ideas:**
```
1. Click "Organize"
2. AI will categorize your text into items:
   - CHARACTER: "A character who can taste lies"
   - PLOT_POINT: "The library that only appears at midnight"
   - WORLD_BUILDING: "What if gravity reversed every Tuesday?"
3. Review the categorized grid
4. Each item can be individually:
   - Kept
   - Discarded
   - Parked for later
   - Promoted to a brainstorm item
5. Click "Promote All" to convert all kept items
```

**Archive a Session:**
```
1. Click "Archive" on a completed session
2. The session moves to the archived list
3. Archived sessions can still be viewed but not edited
```

**Example Brain Dump Session**
```
Raw Text:
"I want a story about a time traveler who keeps going back to fix mistakes
but each fix makes things worse. Main character is a woman named Sarah.
She keeps accidentally killing people when she tries to save them. The
time machine is her grandfather's old clock. She can only go back 24 hours.
Every time she changes something, she forgets the original timeline."

Organized Results:
  [PLOT_POINT] "Time traveler keeps making things worse with each fix"
  [PLOT_POINT] "Can only go back 24 hours"
  [PLOT_POINT] "Forgets original timeline after each change"
  [CHARACTER] "Sarah - female protagonist, time traveler"
  [CHARACTER] "Grandfather (deceased) - built the time machine"
  [WORLD_BUILDING] "Time machine is a clock"
  [CONFLICT] "Accidentally kills people when trying to save them"
  [CONFLICT] "Memory loss prevents learning from mistakes"
```

**Backend APIs**
```
GET /v1/story-development/braindump/sessions?project_id={id}
POST /v1/story-development/braindump/sessions
GET /v1/story-development/braindump/sessions/{session_id}?project_id={id}
PATCH /v1/story-development/braindump/sessions/{session_id}?project_id={id}
DELETE /v1/story-development/braindump/sessions/{session_id}?project_id={id}
POST /v1/story-development/braindump/sessions/{session_id}/organize
```

---

## Job Management

### What It Does

The Job Launch Panel (right sidebar, available in all workspace modes) allows launching AI pipeline jobs and monitoring their execution status. Jobs are the engine that generates all AI content.

### Job Phases

| Phase | Name | Description | When to Use |
|-------|------|-------------|-------------|
| `P-100` | Architect | Generates story architecture, sequences, beats, chapter outlines | First run for a new project, or after foundation/character changes |
| `P-200` | Sequencer | Plans detailed event sequences, assigns chapters to sequences | After P-100, or when revising the plot structure |
| `P-300` | Drafter | Writes actual manuscript prose; supports single-chapter or multi-chapter generation with cross-chapter continuity (default: 8000 tokens/~2000 words per chapter) | After planning is complete, or when rewriting chapters |
| `P-400` | Compiler | Compiles final manuscript, performs consistency checks | After all chapters are drafted |

### Multi-Chapter Generation (P-300)

P-300 supports drafting multiple chapters with automatic cross-chapter continuity:

**Single Chapter (Default):**
```
{
  "phase": "P-300",
  "payload": {
    "project_id": "your-project-id"
  }
}
```
Outputs to `chapter.md` with artifact role `chapter_1`.

**Specific Chapter:**
```
{
  "phase": "P-300",
  "payload": {
    "project_id": "your-project-id",
    "chapter_id": "ch-002"
  }
}
```
Outputs to `chapters/ch-002.md` with artifact role `chapter_ch-002`.

**What Happens:**
1. System queries ChapterPlan for `active_character_ids` (characters appearing in this chapter)
2. Scene Context Injection includes: active character profiles + world constraints + **prior chapter summaries** (last 3 chapters max)
3. Prior chapter summaries contain: key events (max 10), character states (max 10), unresolved threads (max 5)
4. Draft is written to parameterized output path

**ChapterOrchestrator:** For sequential multi-chapter generation, the orchestrator runs P-300 jobs one per chapter plan, each waiting for the prior to complete. Graceful per-chapter error handling: one failure doesn't abort the entire run.

#### Batch Multi-Chapter Mode

Draft multiple chapters sequentially within a single job using the `chapter_ids` list:

```json
{
  "phase": "P-300",
  "payload": {
    "project_id": "<your-project-id>",
    "chapter_ids": ["ch-001", "ch-002", "ch-003"]
  }
}
```

**What happens:**
1. Chapters are drafted sequentially, one at a time
2. After each chapter: ChapterSummarizerService extracts PriorChapterSummary via LLM (key events, character states, unresolved threads)
3. ManuscriptDocument record is auto-created for each completed chapter
4. Prior chapter summaries are injected into subsequent chapters' prompts (capped at last 3)
5. Per-chapter step records created: `drafter-ch-001`, `drafter-ch-002`, etc.
6. Failed chapters are logged but don't abort the job

**Outputs per chapter:**
- File: `data/projects/{project_id}/chapters/{chapter_id}.md`
- Artifact role: `chapter_{chapter_id}`
- ManuscriptDocument: `ms-{chapter_id}` (auto-created)

### How to Use

**Launch a Job:**
```
1. Ensure you're in a workspace with an active project
2. In the right sidebar, find the Job Launch Panel
3. Select a phase (P-100, P-200, P-300, P-400)
4. Optionally specify a model override (if your backend supports it)
5. Click "Launch"
6. Monitor status in the panel
```

**View Recent Jobs:**
```
1. In the Job Launch Panel, scroll down
2. See the list of recent jobs for this project
3. Each job shows:
   - Phase (P-100, etc.)
   - Status (PENDING, PROCESSING, COMPLETED, FAILED)
   - Attempt number
   - Created timestamp
```

**Retry a Failed Job:**
```
1. Find the failed job in the recent jobs list
2. Click "Retry"
3. The job will be re-executed with a new attempt number
```

**View Job Details:**
```
1. Click on a job in the recent jobs list
2. Navigate to the Inspect view for that job
3. View steps, lineage, attempts, and logs
```

**Job Creation Payload:**
```
# Basic job (any phase)
{
  "phase": "P-100",
  "payload": {
    "project_id": "your-project-id"
  },
  "idempotency_key": "optional-key-for-safe-retries"
}

# P-300 with specific chapter (multi-chapter generation)
{
  "phase": "P-300",
  "payload": {
    "project_id": "your-project-id",
    "chapter_id": "ch-002"
  }
}

# P-300 with token override (default: 8000)
{
  "phase": "P-300",
  "payload": {
    "project_id": "your-project-id",
    "chapter_id": "ch-002",
    "max_tokens": 10000
  }
}
```

**Backend APIs**
```
POST /v1/jobs/create
GET /v1/jobs/{job_id}/status
GET /v1/jobs/{job_id}/attempts
GET /v1/jobs/{job_id}/logs
GET /v1/jobs/{job_id}/steps
GET /v1/jobs/{job_id}/lineage
POST /v1/jobs/{job_id}/retry
```

### Job Status Values

| Status | Meaning |
|--------|---------|
| `PENDING` | Job is queued, not yet started |
| `PROCESSING` | Job is actively running |
| `COMPLETED` | Job finished successfully |
| `FAILED` | Job failed (can be retried) |

### Idempotency Keys

Use idempotency keys to safely retry job creation without creating duplicate jobs:

```
# First attempt
POST /v1/jobs/create
Body: {"phase": "P-100", "payload": {"project_id": "abc"}, "idempotency_key": "first-run"}
Response: 202 (created_new: true)

# Same key, same payload (safe retry)
POST /v1/jobs/create
Body: {"phase": "P-100", "payload": {"project_id": "abc"}, "idempotency_key": "first-run"}
Response: 202 (created_new: false, returns existing job status)

# Same key, different payload (rejected)
POST /v1/jobs/create
Body: {"phase": "P-200", "payload": {"project_id": "abc"}, "idempotency_key": "first-run"}
Response: 409 (idempotency conflict)
```

---

## Global Features

### Notes Panel

**What It Does**

A persistent, project-specific notes area. Notes are stored in localStorage and survive page refreshes.

**How to Use**
```
1. Available in all workspace modes (right sidebar)
2. Type notes freely
3. Notes are auto-saved with debounced localStorage persistence
4. Notes are scoped per project
```

### Job Launch Panel

**What It Does**

Persistent right sidebar panel for launching AI pipeline jobs and monitoring status. Available in all workspace modes.

**How to Use**

See [Job Management](#job-management) section above.

### Theme Toggle

**What It Does**

Switches between visual themes for the entire application.

**Available Themes**
| Theme | Description |
|-------|-------------|
| `Light` | Default light theme |
| `Dark` | Dark mode |
| `Midnight` | Deep dark with blue tint |
| `Forest` | Dark with green accents |
| `Ocean` | Dark with teal accents |

**How to Use**
```
1. Click the theme icon in the top navigation bar
2. Select a theme from the popup
3. Theme persists across sessions via localStorage
```

### Settings Panel

**What It Does**

Configures application preferences including icon mode and tooltip visibility.

**Settings**
| Setting | Options | Description |
|---------|---------|-------------|
| **Icon Mode** | `Labels`, `Icons-Large`, `Icons-Small` | How navigation items are displayed |
| **Tooltips** | `Show`, `Hide` | Whether tooltips appear on hover |

**How to Use**
```
1. Click the settings icon (gear) in the top navigation bar
2. Adjust preferences
3. Changes persist via localStorage
```

### Route Sync

**What It Does**

The URL is the source of truth for workspace state. The `useRouteSync` hook synchronizes URL route segments to the UI store, ensuring that:
- Refreshing the page restores the correct workspace mode and project
- Bookmarks work correctly
- Deep links shareable between users

**Route Structure**
```
/                                    - Project list
/workspace/:projectId/plan           - Planning mode
/workspace/:projectId/braindump      - Brain Dump mode
/workspace/:projectId/write          - Writing mode (all chapters)
/workspace/:projectId/write/:chapterId - Writing mode (specific chapter)
/workspace/:projectId/review         - Review mode
/workspace/:projectId/inspect        - Inspect mode (no specific job)
/workspace/:projectId/inspect/:jobId - Inspect mode (specific job)
```

### Toast Notifications

**What It Does**

Displays temporary notifications for success, error, warning, and info messages.

**How It Works**
```
- Success: Green toast (e.g., "Job launched successfully")
- Error: Red toast (e.g., "Failed to create project")
- Warning: Yellow toast (e.g., "Model not available, using stub")
- Info: Blue toast (e.g., "New revision available")

Toasts auto-dismiss after 5 seconds.
Multiple toasts stack vertically.
```

---

## Appendix: Quick Reference Cards

### Recommended Workflow Order

```
1. Create Project → Set manifest
2. Brain Dump → Capture raw ideas
3. Foundation → Define premise, logline, theme, constraints
4. Characters → Build full character profiles
5. World Bible → Populate world lore and rules
6. Arcs → Select narrative arc
7. Flow → Configure development pipeline
8. P-100 Architect → Generate planning artifacts
9. P-200 Sequencer → Plan detailed sequences
10. P-300 Drafter → Write manuscript chapters
11. P-400 Compiler → Finalize manuscript
12. Role Model Checker → Run analysis
13. Review → Make decisions on findings
14. Inspect → Debug any issues
15. Branch → Explore alternatives
```

### Job Phase Quick Guide

| Phase | Run When | Takes | Generates |
|-------|----------|-------|-----------|
| P-100 | New project or foundation changes | 1-5 min | Sequences, beats, chapter plans |
| P-200 | After P-100 or plot revision | 1-3 min | Detailed event sequences |
| P-300 | After planning complete | 2-10 min per chapter | Manuscript chapters (single or multi-chapter with continuity) |
| P-400 | After all chapters drafted | 1-5 min | Compiled manuscript |

### Multi-Chapter Generation Quick Reference

| Feature | Description |
|---------|-------------|
| `chapter_id` payload | Pass `"chapter_id": "ch-XXX"` to P-300 to draft a specific chapter |
| Prior Chapter Context | Last 3 completed chapters automatically injected as summaries (key events, character states, unresolved threads) |
| Active Character Filtering | ChapterPlan's `active_character_ids` determines which characters are injected into the prompt |
| Output Path | Chapters written to `chapters/{chapter_id}.md`; backward-compatible fallback to `chapter.md` |
| Token Budget | Default 8000 tokens (~2000 words per chapter), overridable via `max_tokens` in payload |
| ChapterOrchestrator | Sequential runner for multi-chapter generation; graceful per-chapter error handling |

### File/Artifact Types

| Type | Description |
|------|-------------|
| `PROJECT` | A story workspace |
| `MANUSCRIPT_DOCUMENT` | A written chapter |
| `DRAFT_ARTIFACT` | A draft version |
| `SEQUENCE_PLAN` | A story sequence with beats |
| `CHAPTER_PLAN` | A chapter outline |
| `SCENE_PLAN` | A scene outline |
| `BEAT_PLAN` | A story beat within a sequence |
| `CHARACTER_PROFILE` | A character's detailed profile |
| `RELATIONSHIP_EDGE` | A relationship between two characters |
| `WORLD_BIBLE_ENTRY` | A world-building fact |
| `FOUNDATION_PROFILE` | The narrative foundation |
| `ARC_CANDIDATE` | A proposed narrative arc |
| `ARC_SELECTION` | An accepted or rejected arc |
| `ARC_STAGE_MAP` | An arc's progression through flow stages |
| `BRANCH` | An alternate story version |
| `STORY_DECISION_NODE` | A recorded creative decision |
| `PRIOR_CHAPTER_SUMMARY` | Structured context from completed chapters for cross-chapter continuity |
