# Narrative Engine - User Guide v1.7.0

This guide walks you through generating a short story from scratch and then iterating on it. Follow **Chapter 1** (Steps 1-7) to go from zero to a generated chapter in about 15 minutes. **Chapter 2** (Steps 8-11) shows how to modify characters, edit the story, and regenerate with updated canon. The remaining sections cover advanced features and reference material.

**Version 1.7.0 changes:** Added "Iterate and Refine" chapter (Steps 8-11): modify existing characters, add new characters after initial setup, manually edit generated manuscripts, and re-run the generation pipeline with updated canon. Added AI Draft Generation: generate full chapter drafts from a brief description via the "⚡ AI" button in the Writing workspace's draft list, without running the P-300 pipeline. Added Guided Setup Wizard at `/setup-wizard`: conversational project creation that extracts config, foundation, characters, world bible, arcs, sequences, and chapters through natural dialogue with the LLM. Fixed character PATCH 422 bug where optional fields with empty values blocked saving edits to minimally-created characters.

---

## Table of Contents

1. [Quick Start: Generate Your First Short Story](#quick-start-generate-your-first-short-story)
   - [Guided Setup Wizard (Conversational)](#alternative-guided-setup-wizard-conversational)
   - [Step 1: Create Your Project (Manual Form)](#step-1-create-your-project-manual-form)
2. [Quick Start Chapter 2: Iterate and Refine](#quick-start-chapter-2-iterate-and-refine)
3. [Setup and Configuration](#setup-and-configuration)
4. [Workspace Tour](#workspace-tour)
5. [Detailed Guides](#detailed-guides)
6. [Troubleshooting](#troubleshooting)
7. [Glossary](#glossary)

---

## Quick Start: Generate Your First Short Story

This chapter walks you through creating a project, defining your story's foundation and characters, then launching the AI generation pipeline to produce a drafted chapter. Follow each step in order.

### Prerequisites

- **Model server running**: You need an OpenAI-compatible model server (llama.cpp, LM Studio, vLLM, or cloud provider). See [Setup and Configuration](#setup-and-configuration) if you haven't configured one yet.
- **Narrative Engine running**: Start with `start_narrative_core.cmd` (production) or `start_narrative_core.cmd --dev` (development). The app opens at `http://localhost:5173` (dev) or `http://127.0.0.1:8000` (production).

---

### Alternative: Guided Setup Wizard (Conversational)

If you'd rather describe your story in plain language than fill out forms, use the **Guided Setup Wizard** at `/setup-wizard`. The wizard converses with you through an LLM to extract all project data — config, foundation, characters, world bible, arcs, sequences, and chapters — then creates the project in one step.

**How it works:**

1. Navigate to `/setup-wizard`
2. You'll see a **chat panel** (left) and a **field preview panel** (right)
3. Start describing your story idea in natural language — e.g., "I want to write a dark sci-fi story about a lone sentinel on a dying space station"
4. The LLM asks follow-up questions one at a time, building up your project data:
   - **Config**: project name, genre, tone, POV, story structure
   - **Foundation**: premise, logline, thematic spine, emotional promise
   - **Characters**: names, roles, archetypes, goals, fears, voice notes
   - **World Bible**: locations, technology, organizations, rules
   - **Arcs**: character arcs with stages and transformation types
   - **Sequences**: story structure divided into acts/sections (NEW in v1.7.0)
   - **Chapters**: chapter plans with objectives, conflicts, stakes, active characters (NEW in v1.7.0)
5. As data is extracted, the **field preview panel** updates in real time with collapsible sections for each category
6. The Sequences and Chapters panels **auto-open** when the LLM first generates planning data, so you can review the proposed outline
7. You can adjust anything naturally — say "make it three acts instead of two" or "add a character who is the colony ship's engineer"
8. When the wizard shows **"Ready to Create"** (progress bar reaches 100%), click the button to create your project
9. You'll be redirected to the new project's workspace with all data populated

**Tips:**
- Be specific in your descriptions — "dark sci-fi about isolation and moral dilemmas" produces better results than "a space story"
- Review the field preview panel as you go — you can see exactly what data has been extracted
- The Sequences and Chapters panels give you a complete narrative outline before you create the project, so you can adjust structure early
- You can always go back and refine any field after creation in the Planning workspace

---

### Step 1: Create Your Project (Manual Form)

1. Open the app — you'll see the **Project List** page with a "New Project" form at the top
2. Fill in the form:

| Field | Example Value | Notes |
|-------|---------------|-------|
| **Project Name** | `The Last Watch` | Required — this is how your project will appear in the list |
| **Genre** | `Science Fiction` | Required — guides the AI's tone and style |
| **Tone Profile** | `Dark and Atmospheric` | Required — sets the emotional register |
| **Story Structure** | `Three Act Structure` | Dropdown: Three Act Structure, Save the Cat, Hero's Journey, Freytag's Pyramid, Kishōtenketsu, Fichtean Curve, Seven-Point Structure, Seven Key Steps, Snowflake Method, Other |
| **Point of View** | `Third Person Limited` | Dropdown: First Person, Second Person, Third Person Limited, Third Person Omniscient, Third Person Objective, Third Person Multiple, Other |
| **Primary Language** | `English` | Defaults to English |
| **Secondary Language** | (leave empty) | Optional — for bilingual or code-switching stories |
| **Premise** | `A lone sentinel on a dying space station must decide whether to save the last colony ship or preserve the station's ancient AI.` | Optional — helps guide generation |

3. Click **"Create Project"**

You'll be taken to your project's workspace. The top navigation bar shows your project name and genre badge.

**What just happened**: A new project directory was created at `data/projects/{project-id}/` with a manifest, database, and empty chapter files. You're now in the **Planning** workspace.

---

### Step 2: Write Your Foundation

The Foundation is your story's north star — the AI references it during every generation phase. A well-defined foundation produces coherent output; a sparse one produces generic results.

1. In the left sidebar, click **Planning** mode
2. Click the **Foundation** tab (in the content tabs below the main tab bar)
3. Fill in the fields:

**Required fields** (marked with `*` — Save is disabled until these are filled):

| Field | Example Value | Why It Matters |
|-------|---------------|----------------|
| **Premise \*** | `A lone sentinel on a dying space station must decide whether to save the last colony ship or preserve the station's ancient AI.` | The core conflict — everything else flows from here |
| **Logline \*** | `When the last colony ship arrives at a failing deep-space station, its guard must choose between humanity's future and an AI that holds the key to understanding alien contact.` | One-sentence pitch — sets scope and stakes |

**Optional fields** (fill what you can now; you can save early and come back later):

| Field | Example Value | Why It Matters |
|-------|---------------|----------------|
| **Thematic Spine** | `The tension between duty and compassion. The story explores whether preserving knowledge (the AI) is more valuable than preserving lives (the colonists), and how isolation warps moral reasoning.` | Central theme — guides character decisions and plot resolution |
| **Emotional Promise** | `The reader should feel the weight of impossible choices, the loneliness of deep space, and ultimately a bittersweet hope. The ending should leave them questioning what they would have done.` | Target emotional experience |
| **Tone and Voice Direction** | `Claustrophobic and contemplative. Prose should emphasize sensory details of the station — the hum of failing systems, the cold, the silence between radio checks. Dialogue is sparse; most of the story is internal monologue and action.` | Narrative style guidance |
| **Target Audience** | `Adult sci-fi readers who enjoy hard SF with philosophical undertones (e.g., Ted Chiang, Andy Weir)` | Context for complexity level |
| **Narrative Constraints** | `No time travel`, `No alien appearance`, `Station decay is irreversible` | Click **+ Add Constraint** for each constraint — they're stored as individual tags |
| **Complexity Level** | `Moderate` | Dropdown: Simple, Moderate, Complex, Very Complex |
| **Success Definition** | `A compelling short story (3-5 chapters) with a clear moral dilemma, consistent tone, and a resolution that respects both sides of the conflict without being preachy.` | What "good" looks like |

A field completion counter above the Save button shows your progress: `2/2 required · X/6 optional`.

4. Click **"Save"** — you'll see a confirmation. Foundation revisions are tracked; you can roll back later using the **History** tab. You can save with just Premise and Logline filled, then return to complete the optional fields at any time.

---

### Step 3: Create Characters

Characters need at minimum an ID, name, and role. All other fields are optional — save early and flesh out details as your story develops.

1. Click the **Characters** tab (in the content tabs below the main tab bar)
2. Click **"+ New Character"**
3. Fill in the profile:

**Required fields** (marked with `*`):

| Field | Example Value | Notes |
|-------|---------------|-------|
| **Character ID \*** | `elena-voss` | Stable identifier — use lowercase, hyphens for spaces. Cannot be changed after save. |
| **Display Name \*** | `Elena Voss` | How the character appears in the UI and generated text |
| **Role in Story \*** | `Protagonist` | e.g., Protagonist, Antagonist, Mentor, Off-screen Presence |

**Optional fields** (fill what you know; save and return later):

| Field | Example Value | Why It Helps |
|-------|---------------|--------------|
| **Archetype** | `The Guardian` | Guides AI portrayal of character behavior |
| **External Goal** | `Maintain the station's systems long enough to either guide the colony ship to safety or extract the AI's core data` | What the character wants to achieve |
| **Internal Need** | `To trust her own judgment after years of following orders from a command center that abandoned her` | What the character needs for growth |
| **Misbelief or Wound** | `Believes she must follow protocol perfectly, even when protocol fails. Haunted by a past mission where breaking rules caused casualties.` | The false belief holding them back |
| **Core Fear** | `Making the wrong choice and being solely responsible for the deaths of 2,000 colonists` | Deepest fear — drives decisions |
| **Primary Strength** | `Exceptional systems knowledge and calm under pressure` | Greatest asset |
| **Fatal Flaw** | `Paralysis by analysis — she overthinks decisions until time runs out` | Limiting weakness |
| **Backstory Summary** | `Former military communications officer. Assigned to Station Meridian 8 years ago for a 2-year tour. Her tour was extended when funding cuts reduced rotations. She has not heard from Command in 14 months.` | Past events shaping the character |
| **Voice Notes** | `Speaks in measured, technical language. Uses precise numbers and system names. Rarely uses contractions when stressed. When alone, her internal monologue is more emotional and fragmented.` | How the character speaks — critical for dialogue consistency |
| **Change Axis** | `From obedient follower to moral actor who takes ownership of impossible choices.` | Character arc trajectory |
| **Contradictions / Secrets / Values / Taboos** | Click **+ Add** for each | Layered personality details |
| **Continuity Facts** | `Left-handed. Has a scar on her right forearm from a plasma leak incident.` | Details to track across chapters |

A field completion counter shows progress: `3/3 required · X/10 optional`.

**Character 1 — Protagonist (complete example):**

Fill all fields for Elena Voss as shown above, then click **"Save"**.

**Character 2 — The AI (minimal save, fill later):**

| Field | Value |
|-------|-------|
| **Character ID \*** | `ceres-ai` |
| **Display Name \*** | `CERES (Station AI)` |
| **Role in Story \*** | `Antagonist / Ally` |

Save now, then return to add Archetype (`The Mentor with a Secret`), External Goal, Voice Notes, etc. as your story develops.

**Character 3 — Colony Ship Commander (minimal, off-screen):**

| Field | Value |
|-------|-------|
| **Character ID \*** | `cmdr-hassan` |
| **Display Name \*** | `Commander Tariq Hassan` |
| **Role in Story \*** | `Secondary / Off-screen Pressure` |
| **Voice Notes** | `Speaks via radio. Direct, urgent, paternal. Carries the weight of 2,000 souls.` |

This character only appears via radio, so Voice Notes is the most important optional field.

---

### Step 4: Add World Bible Entries

The World Bible provides encyclopedic reference data. For a short story, 2-3 entries are enough.

1. Click the **World Bible** tab (in the content tabs below the main tab bar)
2. Use the inline form at the top to add each entry:

**Entry 1 — The Station:**

| Field | Value |
|-------|-------|
| **Entry Title** | `Station Meridian` |
| **Brief Summary** | `Deep-space relay station, 40 light-years from nearest colony. Originally designed for 12 crew; currently staffed by one.` |
| **Entry Type** | `Location` | (Options: Concept, Location, Organization, Artifact, Event, Creature, Magic System, Technology, Culture, History) |
3. Click **"Add"**

**Entry 2 — The AI System:**

| Field | Value |
|-------|-------|
| **Entry Title** | `CERES AI Core` |
| **Brief Summary** | `Fourth-generation autonomous intelligence. Controls all station systems. Contains classified data from an unknown alien signal.` |
| **Entry Type** | `Technology` |
4. Click **"Add"**

**Entry 3 — The Colony Ship:**

| Field | Value |
|-------|-------|
| **Entry Title** | `USC Aegis` |
| **Brief Summary** | `Generation ship carrying 2,004 colonists to an uncharted system. Departed Earth 3 years ago.` |
| **Entry Type** | `Technology` |
5. Click **"Add"**

After adding entries, click on each entry to expand it and add detailed canonical facts, related characters, and continuity warnings.

---

### Step 5: Launch the Generation Pipeline

The pipeline has four phases. For a first short story, you can run P-100 (Architect) followed by P-300 (Drafter). P-200 and P-400 are optional for simple stories.

**Launch Architect:**

1. In the Planning workspace, look for the **Launch Job** panel in the right sidebar
2. Click the **Architect** phase button to select it
3. Click the **play icon** button to launch

The Architect generates story architecture from your foundation: sequences, chapter outlines, and beat structure. Watch the job status change from `PENDING` → `PROCESSING` → `COMPLETED`. For a simple story, this takes 30-90 seconds depending on your model speed.

**Launch Drafter:**

1. Click the **Drafter** phase button to select it
2. Click the **play icon** button to launch

The Drafter writes actual prose. During drafting, three quality checks run automatically:
- **Scene Context Injection**: Character profiles and world bible entries are injected into the LLM prompt as constraints
- **Consistency Critic**: After the draft, a separate pass checks character dialogue against voice notes — triggers automatic rewrite on violations
- **Entity Intake**: Detects new characters in the prose and extracts skeletal profiles for review

Drafting takes 1-5 minutes per chapter depending on your model.

**Optional Phases:**
- **P-200 (Sequencer)**: Plans detailed event sequences and maps character arcs to scenes. Useful for longer stories with multiple plot threads.
- **P-400 (Compiler)**: Compiles the final manuscript with cross-chapter consistency checks. Recommended for multi-chapter stories.

---

### Step 6: Read Your Generated Chapter

1. In the left sidebar, click **Writing** mode
2. The Manuscripts section lists your manuscripts — click the generated chapter
3. The center panel displays your drafted chapter
4. The right panel (Manuscript Aids) shows Suggestions, Diff Viewer, and History tabs

**If you see "Select a manuscript from the sidebar"**: The draft may still be processing, or P-400 hasn't compiled it yet. Wait a moment and check again, or launch P-400 to compile the final manuscript.

---

### Step 7: Polish with Manuscript Assist (Optional)

1. Select a passage in the editor by clicking and dragging
2. An assist toolbar appears — choose an action:
   - **Line Edit Selection** — polish prose, fix grammar, improve flow
   - **Expand Selection** — add detail, description, or dialogue
   - **Compress Selection** — tighten while preserving meaning
   - **Rewrite in Same Voice** — rephrase while maintaining character voice
3. Review suggestions in the right panel (Aids Panel)
4. Click **Accept** to apply, **Reject** to dismiss, or **Archive** to save for later

You can also run document-wide actions without selecting text:
- **Developmental Review** — high-level feedback on plot, pacing, character arcs
- **Canon Check** — verify against your world bible and character profiles
- **Character Voice Check** — flag dialogue not matching voice notes

---

### You're Done! — Part 1

You now have a generated short story chapter. But stories are iterative. The next four steps show you how to **modify your canon, edit the output, and regenerate** — the core refinement loop of the Narrative Engine.

---

## Quick Start Chapter 2: Iterate and Refine

This chapter continues from where Chapter 1 left off, using the same "The Last Watch" project. Each step builds on the previous one.

### Step 8: Modify an Existing Character

Characters evolve as your story develops. Let's change Elena Voss's fatal flaw to better fit a new direction.

1. In the left sidebar, click **Planning** mode
2. Click the **Characters** tab
3. Find **Elena Voss** in the character list and click her card to open the editor
4. Locate the **Fatal Flaw** field — it currently reads: `Paralysis by analysis — she overthinks decisions until time runs out`
5. Replace it with: `She trusts machines over people. After Command abandoned her, human judgment feels unreliable. She defers to CERES's calculations even when her gut says otherwise.`
6. Click **"Save"** — you'll see a confirmation toast

**Partial updates:** You only need to change the fields you want to modify. Leaving optional fields blank won't block the save — empty values are treated as "no change" and the existing data is preserved. This means you can edit a single field (like Fatal Flaw) without having to fill out all 10 optional fields.

**What changed:** The next P-300 draft will incorporate this updated flaw into Elena's behavior and decision-making. The Consistency Critic will also use the new profile to check dialogue.

**Verify:** Scroll through Elena's card to confirm the change persisted. Foundation revisions are tracked; you can roll back later using the **History** tab in the Foundation section.

---

### Step 9: Add Another Character

Your story's cast can grow at any time. Let's add a fourth character — an engineer from the colony ship who contacts Elena via radio.

1. Still in the **Characters** tab, click **"+ New Character"**
2. Fill in the required fields:

| Field | Value |
|-------|-------|
| **Character ID \*** | `lena-park` |
| **Display Name \*** | `Engineer Lena Park` |
| **Role in Story \*** | `Secondary — Colony Ship Liaison` |

3. Fill in key optional fields:

| Field | Value | Why It Matters |
|-------|-------|----------------|
| **Archetype** | `The Pragmatist` | Grounds the story in practical stakes |
| **External Goal** | `Keep the USC Aegis's systems functional during approach; buy Elena time to decide` | Gives her agency beyond being a voice on the radio |
| **Voice Notes** | `Direct, no-nonsense. Uses engineering shorthand ("delta-v," "thermal load"). Impatient with philosophy but respects competence. Voice cracks when she talks about the colonists waking up.` | Critical for dialogue consistency in generated scenes |
| **Backstory Summary** | `Former orbital station mechanic. Recruited for the Aegis mission because she can fix anything with limited parts. Has a daughter in cryo-sleep on board.` | Adds emotional weight to her urgency |

4. Click **"Save"**

**What changed:** Lena Park is now part of your character roster. When you regenerate, the P-300 Drafter will include her profile in the Scene Context Injection (if she's marked as active for a chapter). The Consistency Critic will check any dialogue attributed to her against her voice notes.

---

### Step 10: Edit the Generated Chapter

You don't have to accept the AI's output as-is. Let's manually edit the generated chapter to reflect Elena's updated flaw.

1. In the left sidebar, click **Writing** mode
2. In the manuscript list (left panel), click your generated chapter to open it
3. Click **"Edit"** to enter edit mode (if not already editable)
4. Find a passage where Elena makes a decision. Look for text showing her hesitation or overthinking — this is what you want to change to reflect her new flaw (trusting machines over people)
5. **Select the passage** by clicking and dragging
6. **Replace it** with new prose that reflects the updated character. For example, change:

   > *Elena ran through the scenarios again, each calculation branching into more variables. She needed one more simulation, just to be sure—*

   To:

   > *CERES had already run the numbers — 73 percent chance of colony ship survival if she opened the channel now. Elena didn't need another simulation. She trusted the machine's math more than her own instinct telling her to wait. "Open it," she said.*

7. Your changes **auto-save** as you type (via the PATCH endpoint). A save indicator confirms persistence.

**Why edit before regenerating:** Manual edits let you establish the tone and direction you want. When you re-run P-300, the updated character profiles guide the AI toward your preferred direction, while your manual edits serve as a reference point for comparison.

---

### Step 11: Regenerate with Updated Canon

Now that you've modified Elena's profile, added Lena Park, and edited the chapter, re-run the generation pipeline to see how the updated canon changes the output.

**Relaunch the Drafter:**

1. In the left sidebar, click **Planning** mode
2. Look for the **Launch Job** panel in the right sidebar
3. Click the **Drafter** phase button to select it
4. Click the **play icon** button to launch

The Drafter runs with your updated canon:
- Elena's revised fatal flaw influences her decision-making in the prose
- Lena Park's profile is available for Scene Context Injection (if marked active)
- The Consistency Critic checks dialogue against the updated voice notes

**Compare Results:**

1. Wait for the job status to reach `COMPLETED` (1-5 minutes)
2. Switch back to **Writing** mode
3. Open the regenerated chapter from the manuscript list
4. Compare the new draft against your manual edits from Step 10:
   - Does Elena's behavior reflect her updated flaw?
   - Is the tone consistent with your manual edits?
   - Are there new passages you prefer over your manual version?

**Iterate Further:**
- If the output isn't quite right, go back and refine more character profiles or world bible entries, then regenerate again
- Each regeneration uses the current state of your canon — there's no "lock" that prevents mid-course corrections
- You can also launch P-100 Architect before P-300 to regenerate the story structure along with the prose

---

### You're Done!

You've completed the full iteration cycle: **create → generate → modify → edit → regenerate**. From here you can:

- Launch P-300 again for additional chapters (the AI will carry forward context from previous chapters)
- Run the Role Model Checker for a detailed quality review
- Use Manuscript Assist for AI-powered line edits and expansions
- Explore the Canon Workshop to lock critical facts before generating sequels or side stories
- Export the project as a ZIP archive for backup

---

## Setup and Configuration

### Start the Server

**Windows (production, single window):**
```
start_narrative_core.cmd
```

**Windows (development, 2 windows with hot-reload):**
```
start_narrative_core.cmd --dev
```

**PowerShell:**
```powershell
.\start_narrative_core.ps1        # production
.\start_narrative_core.ps1 -Dev   # development
```

- **Production**: builds the frontend once, serves everything from one window. Use for day-to-day writing.
- **Development**: spawns separate windows for uvicorn (`--reload`) and Vite dev server (hot-reload). Use when modifying the app itself.

### Configure Your Model

Narrative Engine works with any OpenAI-compatible model server. Configure in your `.env` file:

**Local servers:**
```
# llama.cpp (default port 8080)
NARRATIVE_INFERENCE_BACKEND=llama.cpp
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:8080

# LM Studio (default port 1234)
NARRATIVE_INFERENCE_BACKEND=lmstudio
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:1234

# vLLM (default port 8000)
NARRATIVE_INFERENCE_BACKEND=vllm
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:8000
```

**Cloud providers:**
```
# OpenAI
NARRATIVE_INFERENCE_BACKEND=openai_compatible
NARRATIVE_INFERENCE_BASE_URL=https://api.openai.com/v1
NARRATIVE_INFERENCE_API_KEY=sk-proj-...
NARRATIVE_INFERENCE_MODEL=gpt-4o

# Google Gemini
NARRATIVE_INFERENCE_BACKEND=openai_compatible
NARRATIVE_INFERENCE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
NARRATIVE_INFERENCE_API_KEY=your-gemini-api-key
NARRATIVE_INFERENCE_MODEL=gemini-2.0-flash
```

**Environment variables:**

| Variable | Required? | Description |
|----------|-----------|-------------|
| `NARRATIVE_INFERENCE_BACKEND` | Yes (for real inference) | `llama.cpp`, `lmstudio`, `vllm`, `openai_compatible`, or `stub` |
| `NARRATIVE_INFERENCE_BASE_URL` | Yes | Base URL of the model server. Trailing `/v1` is auto-appended if missing. |
| `NARRATIVE_INFERENCE_API_KEY` | Only for cloud providers | API key for `Authorization: Bearer {key}`. Omit for local servers. |
| `NARRATIVE_INFERENCE_MODEL` | Yes (for real inference) | Model ID matching what your server has loaded (e.g., `gpt-4o`, `llama-3.1-8b`). Without it, jobs fail with `RUNTIME_CONFIGURATION_ERROR`. Can be overridden per job. |
| `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` | No (default: 300) | Request timeout in seconds. Increase for large prompts or slow models. |

Without a backend configured, the app uses a **stub** that produces placeholder content. Good for testing the UI, not for writing stories.

### Authentication

Most features work without authentication. Some advanced features (Brain Dump, Canon Workshop, Manuscript Assist) require an API key when your server has `NARRATIVE_API_KEY` set.

**To enable auth:**
1. Click **Settings** (gear icon, top-right) → scroll to **API Keys** → create a key
2. Set `NARRATIVE_API_KEY=your-full-key` in your `.env` file
3. Restart the server

**If you see "API key required" errors**: Either configure the key (steps above) or unset `NARRATIVE_API_KEY` to disable auth. Local development works fine without it.

---

## Workspace Tour

### Navigation Modes (Left Sidebar)

The left sidebar shows 5 navigation modes. Additional modes are accessible through buttons or deep links:

| Mode | How to Access | Purpose |
|------|---------------|---------|
| **Guided Setup** | `/setup-wizard` (before project creation) | Conversational project setup — LLM extracts all project data through dialogue |
| **Planning** | Sidebar button | Foundation, Characters, World Bible, story structure, job launching |
| **Brain Dump** | Sidebar button | Free-form idea capture with AI organization |
| **Writing** | Sidebar button | Read and edit manuscripts, use Manuscript Assist |
| **Review** | Sidebar button | Quality findings from Role Model Checker |
| **Inspect** | Sidebar button | Debug view for job execution: steps, artifacts, attempts |
| **Canon** | Deep link: `/workspace/{project-id}/canon` | Canon Workshop — edit canon, set annotations, manage generation rules |
| **Generate** | "Generate Story" button (Planning page) or deep link: `/workspace/{project-id}/generate` | Story Generation Orchestration — create sequels, side stories, forks |

### Planning Workspace Tabs

**Core tabs**: Manifest, Planning, Flow, Arcs, Branches, Decisions, Checker
**Content tabs**: Brainstorm, Foundation, Characters, World Bible, Relationships

### Writing Workspace Layout

Three panels:
- **Left sidebar**: Manuscript list and draft list. Each manuscript card shows its title, extracted chapter heading from the content (e.g., "CHAPTER 1: THERMAL BLEED"), and version number. Click to load a document. The lower section shows draft artifacts with status indicators and a "+ New Draft" button.
- **Center**: Manuscript editor. Read mode renders markdown headings as styled text and backtick-wrapped content as inline code blocks. Click **Edit** for a plain-text editing textarea with live word/character count. Text selection enables AI-assisted actions (Line Edit, Expand, Compress, Rewrite). Click **Save** to persist changes or **Cancel** to discard.
- **Right (Aids Panel)**: Three tabs — Suggestions, Diff Viewer, History — for managing revision suggestions from Manuscript Assist.

#### Using the Diff Viewer

The Diff Viewer shows a side-by-side comparison of source text versus proposed text from a selected suggestion.

1. Open the **Suggestions** tab in the Aids Panel
2. Click any suggestion card — this automatically switches to the **Diff Viewer** tab
3. The diff displays two columns: **Source** (original text, left) and **Proposed** (suggested replacement, right)
4. Changes are color-coded:
   - **Red background + strikethrough**: text that would be deleted
   - **Green background**: text that would be added
   - **Yellow background**: text that would be replaced

The diff header shows a summary count of additions, deletions, and replacements. If no suggestion is selected, the viewer shows "Select a suggestion to compare."

**Example:** A Line Edit Selection suggestion proposes tightening a passage. Clicking the suggestion shows the original sentence in the left column and the revised version in the right, with deleted words crossed out in red and new words highlighted in green.

#### Using the History Tab

The History tab shows all revision suggestions across every status, grouped by manuscript document.

1. Click the **History** tab in the Aids Panel
2. Suggestions are grouped by their target document ID, with a count per group
3. Use the filter bar to narrow by status: **All**, **Requested**, **Pending**, **Accepted**, **Rejected**, or **Superseded**
4. Each suggestion card shows:
   - Status badge (color-coded by state)
   - Source text (red, strikethrough) → Proposed text (green)
   - Rationale (italicized explanation)
   - Source context tags (e.g., character names, world bible references that informed the suggestion)
5. Click any suggestion to open its diff in the **Diff Viewer** tab

**Example:** After running a Developmental Review, you see 4 suggestions grouped under "ms-1" (Chapter 1). Filtering by "Accepted" shows which changes you've already approved. Clicking a rejected suggestion lets you re-examine the diff to confirm your decision.

#### Using Project Notes in Writing Mode

The Notes panel appears in the right sidebar below the Aids Panel and is available across all workspace modes, including Writing.

1. In the **Notes** section, type a note in the text box (e.g., "Remember: Elena defers to CERES in Act 2")
2. Click **Add** — the note appears in the list below
3. Notes persist in your browser's local storage and survive page refreshes
4. Notes are project-specific — switching projects shows a different note set

Notes are useful for tracking writing intentions, plot reminders, or decisions made during editing sessions.

#### Draft List and New Draft Workflow

The left sidebar's lower section shows draft artifacts for the current project. Two buttons sit side by side: **+ New Draft** (manual) and **⚡ AI** (AI-generated).

**Manual Draft:**

1. Click **"+ New Draft"** to open the draft form
2. Fill in the draft title and content
3. Click **"Create"** — the draft appears in the list with status `DRAFT`

**AI-Generated Draft:**

Use this when you want the AI to write a full chapter from a brief description, without running the P-300 pipeline. Ideal for exploratory writing, alternate scenes, or quick drafts based on an idea.

1. Click **"⚡ AI"** next to the "+ New Draft" button
2. The AI draft form opens with two fields:
   - **Draft title** — required (max 255 characters), e.g., "Chapter 3: The Signal"
   - **Brief** — describe what this draft should cover (required). Be specific for better results. For example: `Elena discovers the alien signal embedded in CERES's core data. She must decide whether to broadcast it to the colony ship or keep it secret.`
3. If a chapter plan exists for the selected document, a "Plan:" hint appears above the brief field, showing the planned summary
4. Click **"Generate"** — the system submits an async job
5. While generating, the draft card shows a **PENDING** status with a pulsing amber dot and "Generating..." text
6. On success, the draft appears in the list with status `DRAFT` and the full generated content
7. On failure, an error banner appears with **Retry** and **Dismiss** buttons

**Tips for AI Draft Generation:**

- Write specific briefs — `Elena argues with CERES about the signal` produces better results than `Write a scene`
- Include character names, setting details, and the emotional beat you want
- The AI uses your project's canon (characters, world bible, foundation) as context
- Generated drafts are standalone artifacts — they don't overwrite existing manuscripts
- Promote to Manuscript when satisfied, or use Manuscript Assist for line edits

**Managing Drafts:**

1. Drafts appear in the list with status indicators (`DRAFT`, `PENDING`, `PROPOSED`, `CANONICAL`, etc.)
2. Click a draft to expand its preview
3. Use **Promote to Manuscript** to convert a finalized draft into a versioned manuscript document
4. Use **Continue Draft** or **Create Alternate Variant** for iterative refinement

---

## Detailed Guides

### Importing an Existing Story

If you have a completed story and want the AI to analyze it into a structured project:

1. On the home page, click **"Import Existing Story"**
2. Paste your story text (or upload a `.txt`/`.md` file)
3. Optionally set genre and tone hints
4. Click **"Import"**

Stories under 30,000 characters are processed in one pass. Larger stories use multi-pass analysis (structure detection → per-chapter analysis → consolidation). Multi-pass may take several minutes.

The import creates a project with extracted foundation, characters, world bible entries, and arcs — ready for you to refine and generate from.

### Brain Dump: Freeform Ideation

1. In the left sidebar, click **Brain Dump** mode
2. Name your session (e.g., "Character Ideas")
3. Free-write ideas in the canvas — no structure needed
4. Once you have 100+ characters, **"Organize with AI"** appears
5. Click it to categorize your ideas into characters, plot points, settings, themes
6. Review organized results — create character profiles or world entries from categorized items

### Story Branching

Branches work like Git branches for your story:

1. In the left sidebar, click **Planning** → click the **Branches** tab
2. Click **"Create Branch"** and name it (e.g., "Dark Ending")
3. Click **"Set Active"** to switch to that branch
4. Launch P-300 to draft an alternate version
5. Use **Branch Comparisons** to side-by-side compare chapters
6. Use **Merge Decisions** to consolidate the best elements

Only one branch is active at a time. Set it explicitly before launching jobs.

### Review and Quality Checks

**Role Model Checker** (click **Planning** in sidebar → click **Checker** tab):
- Select roles: Planner, Character Analyst, Consistency Checker, Tone Monitor, Pacing Reviewer
- Click **"Run Checker"** — the AI reviews your content from each perspective
- Findings appear in **Review** mode with severity levels (ERROR, WARNING, SUGGESTION)

**Review Workspace**:
- Accept, Reject, Defer, Escalate, or Refine each finding
- **Inspect Run Links** tab traces findings back to their source jobs

**Inspect Workspace** (`/workspace/:projectId/inspect/:jobId`):
- Step Timeline: execution steps with timing
- Artifact Lineage: how artifacts were created and modified
- Attempt History: all retry attempts for failed jobs

### Canon Workshop

The Canon Workshop is accessible at `/workspace/{project-id}/canon`. It gives you control over what canon material is used during generation:

1. **Overview tab**: See counts, select characters/world entries, configure generation rules
2. **Mythos tab**: Manage mythos entries from mythology extraction
3. **Patterns tab**: Manage narrative patterns from pattern extraction
4. **Packet Preview tab**: See exactly what the executor will receive

**Annotations** let you classify fields:
- **Locked** — must not be contradicted (blocking violation)
- **Soft Guidance** — respect this, but minor deviations OK
- **Mutable** — explicitly allowed to change
- **Forbidden Contradiction** — this text must not appear in output

### Story Generation Orchestration

Generate a new story from existing canon (sequel, prequel, side story, fork):

1. Navigate to Generate mode (click "Generate Story" button on the Planning page, or go to `/workspace/{project-id}/generate`) → **Generation Wizard**
2. Select mode: Same Project (New Arc, Sequel, Prequel, Side Story, Alternate Route) or New Project (Character Fork, World Fork, Hybrid Fork)
3. Select canon scope: which characters and world entries to include
4. Write a generation brief: what the new story should accomplish
5. Configure policy: locked fields, allowed changes, forbidden contradictions, continuity strictness
6. Set chapter count (1-100)
7. Click **"Start Generation"**

The system runs a 4-phase pipeline:
- **G-200 Plan**: Generate story architecture from canon packet
- **G-300 Draft**: Draft chapters with canon context and prior summaries
- **G-350 Gate**: Check artifacts against locked canon facts
- **G-400 Compile**: Assemble final manuscript (only if blocking gates pass)

**Tip**: Visit the Canon Workshop before generating to lock critical facts and set policy. This prevents wasted runs on contradictory content.

### Exporting and Importing Projects

**Export** (home page → project card → archive icon):
- Downloads a ZIP containing the full project directory + operations DB dump
- Synchronous — file downloads immediately

**Import** (home page → "Import Project"):
- Restores an exported ZIP as a new project with a fresh UUID
- Never overwrites existing projects
- Asynchronous with progress tracking

---

## Troubleshooting

### Generation Issues

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Jobs stuck on "PENDING" | Model server not running or unreachable | Check your model server is up; verify `NARRATIVE_INFERENCE_BASE_URL` in `.env` |
| Jobs fail with G-400 compiler error | Pre-existing flaky failure in the compiler phase | Retry the job; this is a known intermittent issue |
| Generated prose is generic or off-tone | Foundation is too sparse | Add more detail to your foundation, especially Tone and Voice Direction and Narrative Constraints |
| Character dialogue doesn't match profiles | Voice Notes field is empty or vague | Fill out Voice Notes for each character — the Consistency Critic uses these to check dialogue |
| Drafts are too short | Model token limit reached | Increase `NARRATIVE_INFERENCE_TIMEOUT_SECONDS`; check your model's max output tokens |
| Cross-chapter continuity breaks | More than 3 chapters between related events | Prior chapter context is capped at last 3 chapters. Keep related events close together. |
| AI draft stuck on "Generating..." | Model server slow or unreachable | Check model server is running; verify `NARRATIVE_INFERENCE_BASE_URL`. The system polls every 3 seconds. |
| AI draft generation fails with error banner | LLM returned invalid response or timed out | Click **Retry** — the job resubmits. If it fails repeatedly, check your model's max output tokens (needs >= 8000). |
| AI draft is generic or off-tone | Brief was too vague or foundation is sparse | Write specific briefs with character names and emotional beats. Fill out your Foundation's Tone and Voice Direction. |

### UI Issues

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Save button is grayed out (Foundation) | Required fields (Premise, Logline) are empty | Fill in at least the `*` marked fields. Optional fields can be left blank — save early, complete later. |
| Save button is grayed out (Character) | Required fields (Character ID, Display Name, Role in Story) are empty | Fill in at least the `*` marked fields. All other fields are optional. |
| Character save fails with 422 error | **Fixed in v1.7.0.** Optional fields with empty values used to trigger a validation error. Empty strings are now treated as "no change." Update your backend if you still see this. |
| "API key required" banner | Server has `NARRATIVE_API_KEY` set; request lacks matching key | Configure the key, or unset `NARRATIVE_API_KEY` to disable auth |
| Brain Dump stuck on "Loading..." | 401 from API key gate | An error banner will appear. Configure the API key (see [Authentication](#authentication)), or unset `NARRATIVE_API_KEY` to disable auth. |
| Dark theme not applying | Browser cached old styles | Hard refresh (`Ctrl+Shift+R` / `Cmd+Shift+R`) |
| Sidebar mode buttons don't switch views | Stale workspace state in store | Refresh the page or use direct URLs: `/workspace/{id}/plan`, `/write`, `/review`, `/inspect`, `/braindump`, `/canon`, `/generate` |
| Project doesn't appear in list | Missing or invalid `manifest.json` | Delete the project directory from `data/projects/` and recreate |

### Model Configuration Issues

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| "Connection refused" | Model server not running | Start your model server (llama.cpp, LM Studio, etc.) |
| "Model not found" | Model name doesn't match what the server has loaded | Check `NARRATIVE_INFERENCE_MODEL` against your server's available models |
| Timeouts on large stories | Default 300s timeout too short | Increase `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` to 600 or higher |
| Poor quality output | Model too small for the task | Use a model with at least 7B parameters for drafting (P-300). 13B+ recommended. |

---

## Glossary

| Term | Meaning |
|------|---------|
| **Project** | A complete story workspace: manifest, characters, world bible, generated artifacts |
| **Manifest** | Core metadata: genre, tone, structure, POV, language |
| **Foundation** | Detailed narrative profile: premise, logline, theme, constraints, voice direction |
| **Brain Dump** | Free-form text canvas for unstructured idea capture; AI can organize results |
| **P-100 Architect** | Generates story architecture from your foundation (sequences, chapter outlines) |
| **P-200 Sequencer** | Plans detailed event sequences and character arc mappings |
| **P-300 Drafter** | Writes actual manuscript prose with automatic quality checks |
| **P-400 Compiler** | Compiles final manuscript with cross-chapter consistency checks |
| **Scene Context Injection** | Automatic injection of character profiles, world bible entries, and prior chapter summaries into the LLM prompt |
| **Consistency Critic** | Post-draft check that verifies character dialogue/actions match profiles; triggers rewrite on violations |
| **Entity Intake** | Auto-detection of new characters in draft prose; extracts skeletal profiles for review |
| **Canon Workshop** | Workspace for editing canon, setting annotations (locked/mutable), managing generation rules |
| **Canon Annotation** | Field-level classification: `locked`, `soft_guidance`, `mutable`, `forbidden_contradiction` |
| **Generation Run** | Story Generation Orchestration: G-200 plan → G-300 draft → G-350 gate → G-400 compile |
| **Canon Packet** | Deterministic snapshot of selected canon sent to the executor. Budget-aware (120K cap). |
| **Role Model Checker** | AI review tool: Planner, Character Analyst, Consistency Checker, Tone Monitor, Pacing Reviewer |
| **Manuscript Assist** | Interactive editing: select text → request AI assistance → apply/reject suggestions |
| **Branch** | Alternate version of your story; like Git branches for narrative |
| **Inspect** | Debug view showing job execution steps, artifact lineage, and attempt history |
| **Guided Setup Wizard** | Conversational project creation at `/setup-wizard`. LLM extracts config, foundation, characters, world bible, arcs, sequences, and chapters through natural dialogue. Field preview panel updates in real time. |
