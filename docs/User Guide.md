# Narrative Engine - User Guide

This guide walks you through using Narrative Engine from first project to a fully-developed complex story.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Importing an Existing Story](#importing-an-existing-story)
3. [Level 1: Your First Simple Story](#level-1-your-first-simple-story)
4. [Level 2: Medium Complexity with Branching and Review](#level-2-medium-complexity-with-branching-and-review)
5. [Level 3: Complex Story with Full Pipeline](#level-3-complex-story-with-full-pipeline)
6. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### Prerequisites

- Python 3.12+ for the backend
- Node.js 18+ for the frontend

### Start the Server

**Windows:**
```
start_narrative_core.cmd
```

**PowerShell:**
```
.\start_narrative_core.ps1
```

The backend starts on `http://127.0.0.1:8000`.

### Start the Frontend

```
cd frontend
npm install
copy .env.example .env.local   (Windows) or cp .env.example .env.local  (Unix)
npm run dev
```

The frontend opens at `http://localhost:5173`.

### Configure Your Model

Narrative Engine works with any OpenAI-compatible local model server (llama.cpp, LM Studio, vLLM). Set the `INFERENCE_URL` environment variable to point at your model server:

```
INFERENCE_URL=http://localhost:1234/v1   (LM Studio)
INFERENCE_URL=http://localhost:8081      (llama.cpp)
```

If no inference URL is set, the app uses a stub backend for testing (jobs complete with placeholder content).

### Alternative: Import an Existing Story

If you already have a completed story, you can import it and have the AI analyze and structure it automatically:

1. Navigate to the home page (`/`)
2. Click **"Import Story"**
3. Paste your story text into the editor
4. Optionally specify genre and tone hints to guide the analysis
5. Click **"Import"**

The system will:
- Analyze the story with an LLM to extract characters, world details, and structure
- Create a new project with all structured data
- Generate foundation profiles, character profiles, world bible entries, and planning artifacts

---

## Level 1: Your First Simple Story

In this section, you'll create a simple short story from scratch using just the basic features.

### Step 1: Create a Project

1. Navigate to the home page (`/`)
2. Click **"Create New Project"**
3. Fill in the fields:
   - **Project Name:** "My First Story"
   - **Genre:** Select a genre (e.g., "Science Fiction")
   - **Tone Profile:** Select a tone (e.g., "Hopeful")
   - **Story Structure:** Choose a structure (e.g., "Three Act")
   - **POV:** Choose point of view (e.g., "Third Limited")
   - **Primary Language:** "English"
4. Click **"Create"**

You'll be taken to the project's Planning workspace.

### Step 2: Review Your Manifest

The default tab shows your **Manifest** -- the core metadata for your story. This includes genre, tone, structure, POV, and language settings. These settings influence every AI-generated artifact downstream.

### Step 3: Write a Brain Dump

1. Switch to **Brain Dump** mode from the top navigation bar
2. In the canvas, free-write your story ideas:
   ```
   A young inventor discovers a broken time machine in her grandfather's
   workshop. When she fixes it, she accidentally sends her cat to last
   Tuesday. She has to convince her skeptical neighbor to help her
   retrieve him before the timeline collapses.
   ```
3. Click **"Organize"** to let AI categorize your ideas into characters, plot points, conflicts, etc.
4. Review the organized items in the grid

### Step 4: Launch the Architect (P-100)

1. Go back to **Planning** mode
2. In the right sidebar, find the **Job Launch Panel**
3. Select phase **P-100 (Architect)**
4. Click **"Launch"**

The Architect analyzes your manifest and brain dump, then generates:
- A project architecture document
- Story sequences with beats
- Chapter outlines

Monitor progress in the Job Launch Panel. When complete, switch to the **Planning** tab to see the generated sequences and chapters.

### Step 5: Draft Your First Chapter

1. In the Job Launch Panel, select phase **P-300 (Drafter)**
2. Click **"Launch"**

The Drafter writes actual prose. When complete:
1. Switch to **Writing** mode
2. Select a manuscript document from the left sidebar
3. Read the generated chapter in the center panel
4. Check the right sidebar (Aids Panel) for AI-generated revision suggestions

You now have a simple story drafted end-to-end.

---

## Level 2: Medium Complexity with Branching and Review

This section builds on Level 1 and introduces story branches, the role model checker, and the review workflow.

### Step 1: Define Your Foundation

1. Go to **Planning** mode
2. Click the **Foundation** tab
3. Fill in the foundation profile:
   - **Premise:** "What if a librarian discovered that books were actually portals to parallel worlds?"
   - **Logline:** "A reclusive librarian must navigate dangerous book-worlds to prevent a catastrophic merger of realities."
   - **Thematic Spine:** "Knowledge vs. ignorance; the courage to question authority"
   - **Emotional Promise:** "Wonder and tension; readers should feel the thrill of discovery"
   - **Narrative Constraints:** "No violence over blood level; all characters must have agency"
4. Click **"Save"**

The foundation acts as a north star -- all subsequent AI generation references it.

### Step 2: Build Your Characters

1. Click the **Characters** tab
2. Click **"Add Character"**
3. Fill in the character profile:
   - **Name:** "Elara Voss"
   - **Role:** "Protagonist"
   - **External Goal:** "Find and seal the rift between worlds"
   - **Internal Need:** "Overcome her fear of being noticed"
   - **Misbelief:** "Staying invisible keeps everyone safe"
   - **Core Fear:** "Being responsible for someone's harm"
   - **Primary Strength:** "Meticulous research skills"
   - **Fatal Flaw:** "Paralyzing indecision under pressure"
4. Click **"Save"**
5. Add more characters as needed (mentor, antagonist, ally, etc.)
6. Use the **Relationships** section to define connections between characters

### Step 3: Build Your World Bible

1. Click the **World Bible** tab
2. Click **"Add Entry"**
3. Create entries like:
   - **Type:** "Location" -- **Title:** "The Athenaeum" -- **Content:** "A vast underground library spanning seven sub-levels..."
   - **Type:** "Concept" -- **Title:** "Book-Worlds" -- **Content:** "Each book contains a fully realized alternate reality. Opening a book transports the reader..."
   - **Type:** "Rule" -- **Title:** "Crossing Limit" -- **Content:** "A person can only safely traverse 3 book-worlds before reality begins to degrade"
4. Each entry can reference related characters, mark canonical facts, and track continuity

### Step 4: Explore Story Branches

1. Click the **Branches** tab
2. Click **"Create Branch"**
3. Name it "Alternative Ending" with a description like "Elara merges the worlds instead of sealing them"
4. Click **"Set Active"** to switch to this branch
5. Now draft this alternate version by launching P-300 again

Branches work like Git branches for your story -- you can explore multiple versions, compare them, and merge the best elements.

### Step 5: Run the Role Model Checker

1. Click the **Checker** tab
2. Select your model from the catalog (if using stub mode, no selection needed)
3. Click **"Run Checker"**

The checker analyzes your generated content against multiple narrative roles (plottter, character analyst, consistency checker, tone monitor). It produces findings about potential issues.

### Step 6: Review Findings

1. Switch to **Review** mode
2. Click the **Findings** tab
3. Review each finding:
   - **Accept** the suggested change
   - **Reject** it if it doesn't fit your vision
   - **Defer** for later consideration
4. Check the **Inspect Run Links** tab to see which jobs generated each finding
5. Click a link to navigate to the Inspect view for deep debugging

---

## Level 3: Complex Story with Full Pipeline

This section demonstrates a complete professional workflow using all features together.

### Step 1: Project Setup with Detailed Manifest

Create a new project with careful attention to the manifest:

1. **Project Name:** "The Last Archive"
2. **Genre:** "Science Fiction / Literary Fiction"
3. **Tone Profile:** "Contemplative with moments of tension"
4. **Story Structure:** "Seven Point Structure"
5. **POV:** "Third Limited" (rotating between two protagonists)
6. **Primary Language:** "English"
7. **Secondary Language:** "None"

The manifest is your story's contract. Get this right and all downstream generation will be coherent.

### Step 2: Foundation with Revision Tracking

1. Go to **Foundation**
2. Fill in a detailed foundation:
   - **Premise:** "In a future where human memories can be stored in crystalline archives, a archivist discovers that someone is systematically erasing entire life histories to rewrite history."
   - **Logline:** "When an archivist uncovers a conspiracy to erase people from existence, she must protect the last surviving memories while questioning whether some truths should stay buried."
   - **Thematic Spine:** "The weight of memory; who controls the past controls the future; the morality of forgetting"
   - **Emotional Promise:** "Intellectual mystery with emotional depth; readers should question their own memories"
   - **Target Audience:** "Adult readers of speculative fiction (Le Guin, Chiang, Chiang)"
   - **Narrative Constraints:** "No deus ex machina; all solutions must come from established characters; maintain internal consistency of memory technology"
   - **Complexity Level:** "High"
   - **Success Definition:** "A story that is both a page-turning mystery and a meditation on memory and identity"
3. Click **"Save"**

Later, go to **Foundation Revisions** tab to see the revision history. You can roll back to any previous version.

### Step 3: Deep Character Development

Create 5-6 characters with full profiles:

**Character 1: Dr. Miren Kael (Protagonist)**
- Role: Protagonist
- Archetype: "The Scholar"
- External Goal: "Expose the memory erasure conspiracy"
- Internal Need: "Trust her own judgment over archived records"
- Misbelief: "If I follow the evidence logically, the truth will protect me"
- Core Fear: "Being complicit through silence"
- Primary Strength: "Meticulous pattern recognition"
- Fatal Flaw: "Emotional detachment as a coping mechanism"

**Character 2: Joss Vallen (Antagonist)**
- Role: Antagonist
- Archetype: "The Reformer"
- External Goal: "Complete the Grand Erasure to prevent future suffering"
- Internal Need: "Relief from the guilt of past failures"
- Misbelief: "Forgetting is a form of mercy"
- Core Fear: "History repeating itself"

**Character 3: Tessa Rowan (Mentor)**
- Role: Mentor
- External Goal: "Protect the last unaltered archive"
- Internal Need: "Atone for her role in creating the system"

For each character, fill in:
- Backstory summary
- Voice notes (how they speak)
- Secrets
- Values and taboos
- Change axis (how they transform)

Define relationships between characters (mentor-protagonist, antagonistic, romantic, etc.) with tension levels and notes.

### Step 4: Comprehensive World Bible

Create 15-20 world bible entries across multiple types:

**Technology:**
- "Memory Crystals" -- storage medium, capacity, limitations
- "The Extraction Process" -- how memories are removed, side effects
- "Chronos Interface" -- the software used to query and modify archives

**Locations:**
- "The Grand Archive" -- main facility, layout, security
- "The Understack" -- black market for memory trading
- "Silent Ward" -- where erased people are temporarily held

**Organizations:**
- "The Archive Authority" -- governing body
- "The Rememberers" -- underground resistance
- "The Reclamation Project" -- Joss's organization

**Rules:**
- "The Three Laws of Memory" -- fundamental constraints of the technology
- "Erasure Protocol" -- procedure for removing memories
- "Continuity Requirement" -- why complete erasure requires chain consistency

**Concepts:**
- "Identity Drift" -- what happens when memories are incomplete
- "Echo Fragments" -- residual memory traces that resist erasure

Each entry should have:
- Canonical status (confirmed fact vs. theory)
- Related characters
- Source artifacts
- Visibility scope (who knows this fact)
- Continuity warnings

### Step 5: Story Flow Configuration

1. Go to the **Flow** tab
2. Review the default flow stages:
   - Brainstorm -> Foundation -> Characters -> World Bible -> Arc Selection -> Planning -> Drafting -> Review
3. Customize if needed:
   - Add custom stages (e.g., "Beta Reader Review")
   - Reorder stages to fit your process
   - Set custom prompt guidance for each stage
   - Disable stages you don't need
4. Save the flow

### Step 6: Arc Exploration

1. Go to the **Arcs** tab
2. The system proposes arc candidates based on your foundation and characters
3. Review each candidate:
   - **Summary:** What happens in this arc
   - **Fit Notes:** How well it matches your foundation
   - **Stage Map:** How this arc progresses through flow stages
4. Select the arc that best serves your story
5. The selected arc guides all subsequent generation

### Step 7: Run the Full Pipeline

Execute jobs in sequence:

**P-100 Architect:**
- Generates the overall story architecture
- Creates sequences, chapters, and scene plans
- Builds the dependency graph

**P-200 Sequencer:**
- Plans the detailed sequence of events
- Assigns chapters to sequences
- Maps character arcs to specific scenes

**P-300 Drafter:**
- Writes actual manuscript chapters
- Creates draft artifacts
- Generates revision suggestions

**P-400 Compiler:**
- Compiles the final manuscript
- Performs cross-chapter consistency checks
- Creates the polished manuscript document

You can run these in order by clicking "Launch" for each phase in the Job Launch Panel. Monitor progress in real-time.

### Step 8: Create Narrative Branches for Plot Exploration

1. Go to the **Branches** tab
2. Create multiple branches:
   - "Dark Ending" -- Elara fails, the Archive Authority wins
   - "Compromise Ending" -- Elara exposes the conspiracy but can't reverse it
   - "Hopeful Ending" -- Elara succeeds, memories are restored
3. Set each branch active and run P-300/P-400 for each
4. Use **Branch Comparisons** to side-by-side compare key chapters across branches
5. Use **Merge Decisions** to record which elements you're borrowing from each branch

### Step 9: Decision Tree Management

1. Go to the **Decisions** tab
2. Review the decision tree that captures key creative decisions
3. Add decision points:
   - "How does Elara discover the conspiracy?" (options: accident, deliberate search, third party)
   - "What is the final confrontation?" (options: physical, intellectual, emotional)
4. Track the path from root to each node
5. Record your choices and rationale

### Step 10: Run the Role Model Checker

1. Go to the **Checker** tab
2. Run checks for all roles:
   - **Planner:** Does the plot make logical sense?
   - **Character Analyst:** Are characters consistent and well-developed?
   - **Consistency Checker:** Do facts align across chapters?
   - **Tone Monitor:** Is the tone consistent?
   - **Pacing Reviewer:** Is the pacing appropriate?
3. Review findings in the **Review** workspace
4. Accept, reject, or defer each finding
5. Track your review decisions over time

### Step 11: Deep Inspect Any Job Run

1. From the Review workspace, click an **Inspect Run Link** to jump to the source
2. Or navigate directly to `/workspace/:projectId/inspect/:jobId`
3. In the Inspect view:
   - **Step Timeline:** See each step of the job execution with timing
   - **Artifact Lineage:** Trace how artifacts were created and modified
   - **Attempt History:** See all retry attempts for failed jobs
   - **Logs:** Read the raw job logs

### Step 12: Writing and Revision

1. Go to **Writing** mode
2. Select a manuscript chapter from the left sidebar
3. Read the full text in the center panel
4. Use the Aids Panel (right sidebar) to:
   - View revision suggestions
   - Compare versions with diff viewer
   - See text selection history
5. Promote drafts to manuscript when satisfied

---

## Tips and Best Practices

### Workflow Recommendations

1. **Start with Foundation, not Drafting.** A well-defined foundation makes every subsequent AI generation coherent.
2. **Use Brain Dump liberally.** Capture raw ideas first, organize them later. Don't self-censor at the ideation stage.
3. **Build characters before sequences.** Character-driven stories need character depth before plot planning.
4. **Run the Checker early.** Don't wait until the end -- run checks after each major milestone.
5. **Use branches for endings.** Explore multiple endings in parallel, then merge the best elements.
6. **Review findings actively.** Don't just auto-accept. Each finding represents a creative decision.
7. **Inspect when confused.** If AI output seems off, use Inspect to trace the execution path.

### Common Pitfalls

- **Don't skip the manifest.** The AI uses manifest settings to guide generation. Wrong settings = wrong tone.
- **Don't mix branches carelessly.** Only one branch is active at a time. Set the active branch explicitly before launching jobs.
- **Don't ignore foundation revisions.** If later chapters contradict your foundation, check the revision cues tab.
- **Don't overwrite character profiles.** If you need variations, create additional characters rather than modifying existing ones.

### Keyboard Shortcuts and Navigation

- Top navigation bar: Switch between Planning, Brain Dump, Writing, Review, Inspect modes
- Right sidebar: Toggle Job Launch Panel and Notes Panel
- Settings (top right): Change theme, icon density, tooltip behavior
- URL deep links: Bookmark any workspace state by copying the full URL

---

## Glossary

| Term | Meaning |
|------|---------|
| **Project** | A complete story workspace with its own manifest, characters, and generated artifacts |
| **Manifest** | Core metadata defining genre, tone, structure, POV, and language |
| **Foundation** | Detailed narrative profile: premise, logline, theme, constraints |
| **Brain Dump** | Free-form text canvas for unstructured idea capture |
| **Flow Stage** | A step in the story development pipeline (brainstorm, foundation, drafting, etc.) |
| **Arc** | A narrative trajectory connecting story events to character development |
| **Branch** | An alternate version of the story, like Git branches |
| **Decision** | A recorded creative choice with options and rationale |
| **P-100 Architect** | Job phase that generates story architecture and planning |
| **P-200 Sequencer** | Job phase that plans detailed event sequences |
| **P-300 Drafter** | Job phase that writes actual manuscript prose |
| **P-400 Compiler** | Job phase that compiles and finalizes the manuscript |
| **Role Model Checker** | AI analysis tool that reviews content from multiple narrative perspectives |
| **Finding** | A review insight flagged by the checker (with severity level) |
| **Job** | An AI execution task with status, logs, and attempt history |
| **Inspect** | Deep debug view showing step execution, artifacts, and lineage |
| **World Bible** | Encyclopedic reference for story world facts, lore, and rules |
| **Chapter Packet** | A bundle of reference materials prepared for drafting a chapter |
