# Narrative Engine - User Guide v1.6.0

This guide walks you through using Narrative Engine from first project to a fully-developed complex story, following the natural creative lifecycle: seed your project, ideate and plan, write and draft, polish manuscripts, and generate new stories from existing canon.

---

## Table of Contents

### Getting Started

1. [Getting Started](#getting-started) (includes Authentication setup)
2. [Sample Stories](#sample-stories)

### Seeding Your Project

3. [Creating a Project from Scratch](#creating-a-project-from-scratch)
4. [Importing an Existing Story](#importing-an-existing-story)
5. [Extracting Patterns for Story Generation](#extracting-patterns-for-story-generation)

### Planning and Ideation

6. [Brain Dump: Freeform Ideation](#brain-dump-freeform-ideation)
7. [Foundation, Characters, and World Bible](#foundation-characters-and-world-bible)

### Writing and Drafting

8. [The Generation Pipeline: P-100 through P-400](#the-generation-pipeline-p-100-through-p-400)
9. [Multi-Chapter Generation](#multi-chapter-generation)

### Polishing Manuscripts

10. [Manuscript LLM Assist: Interactive Editing with AI](#manuscript-llm-assist-interactive-editing-with-ai)
11. [Review and Quality Checks](#review-and-quality-checks)

### Advanced Generation

12. [Canon Workshop: Customizing Source Material Before Generation](#canon-workshop-customizing-source-material-before-generation)
13. [Story Generation Orchestration](#story-generation-orchestration)

### Project Lifecycle

14. [Exporting and Importing Projects](#exporting-and-importing-projects)
15. [Story Branching](#story-branching)

### Learning Paths (Levels 1–3)

16. [Level 1: Your First Simple Story](#level-1-your-first-simple-story)
17. [Level 2: Medium Complexity with Branching and Review](#level-2-medium-complexity-with-branching-and-review)
18. [Level 3: Complex Story with Full Pipeline](#level-3-complex-story-with-full-pipeline)

### Reference

19. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### Prerequisites

- Python 3.12+ for the backend
- Node.js 18+ for the frontend

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
```
.\start_narrative_core.ps1        # production
.\start_narrative_core.ps1 -Dev   # development
```

The backend starts on `http://127.0.0.1:8000`.

**Modes:**
- **Production (default)** — builds the frontend once, runs uvicorn in a single terminal window. The backend serves the built frontend as static files. Use this for day-to-day work.
- **Development (`--dev`)** — spawns two terminal windows: one for uvicorn (with `--reload`) and one for the Vite dev server (hot-reload). Use this when actively developing the frontend.

### Frontend-Only Development

If you need to develop the frontend in isolation:

```
cd frontend
npm install
npm run dev
```

The frontend dev server opens at `http://localhost:5173` and proxies API calls to the backend.

### Configure Your Model

Narrative Engine works with any OpenAI-compatible model server — local (llama.cpp, LM Studio, vLLM) or cloud (OpenAI, Anthropic via vertex, Google Gemini, etc.). Configure your model in the `.env` file:

```
NARRATIVE_INFERENCE_BACKEND=llama.cpp
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:8080
```

**Common local configurations:**
```
# llama.cpp
NARRATIVE_INFERENCE_BACKEND=llama.cpp
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:8080

# LM Studio
NARRATIVE_INFERENCE_BACKEND=lmstudio
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:1234

# vLLM
NARRATIVE_INFERENCE_BACKEND=vllm
NARRATIVE_INFERENCE_BASE_URL=http://127.0.0.1:8000
```

**Cloud provider configurations:**
For cloud providers (OpenAI, Anthropic, Google Gemini, etc.), use the `openai_compatible` backend with their API endpoint and your API key:

```
# OpenAI
NARRATIVE_INFERENCE_BACKEND=openai_compatible
NARRATIVE_INFERENCE_BASE_URL=https://api.openai.com/v1
NARRATIVE_INFERENCE_API_KEY=sk-proj-...
NARRATIVE_INFERENCE_MODEL=gpt-4o

# Anthropic (via Google Vertex AI)
NARRATIVE_INFERENCE_BACKEND=openai_compatible
NARRATIVE_INFERENCE_BASE_URL=https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/endpoints/ENDPOINT
NARRATIVE_INFERENCE_API_KEY=your-api-key
NARRATIVE_INFERENCE_MODEL=claude-sonnet-4@20250514

# Google Gemini (via AI Studio)
NARRATIVE_INFERENCE_BACKEND=openai_compatible
NARRATIVE_INFERENCE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
NARRATIVE_INFERENCE_API_KEY=your-gemini-api-key
NARRATIVE_INFERENCE_MODEL=gemini-2.0-flash
```

**Environment variables reference:**

| Variable | Required? | Description |
|----------|-----------|-------------|
| `NARRATIVE_INFERENCE_BACKEND` | Yes (for real inference) | One of: `llama.cpp`, `lmstudio`, `vllm`, `openai_compatible`, `stub` |
| `NARRATIVE_INFERENCE_BASE_URL` | Yes | Base URL of the model server. Trailing `/v1` is auto-appended if missing. |
| `NARRATIVE_INFERENCE_API_KEY` | Only for cloud providers | API key sent as `Authorization: Bearer {key}` to the provider. Leave blank or omit for local servers that don't require auth. |
| `NARRATIVE_INFERENCE_MODEL` | Recommended | Default model ID to use (e.g., `gpt-4o`, `llama-3.1-8b`). Can be overridden per job. |
| `NARRATIVE_INFERENCE_TIMEOUT_SECONDS` | No (default: 300) | Request timeout in seconds. Use higher values for large prompts or slow models. |

If no inference backend is set, the app uses a **stub backend** for testing (jobs complete with placeholder content). Local servers typically don't need an API key — omit `NARRATIVE_INFERENCE_API_KEY` or leave it blank. Cloud providers require a valid key.

### Authentication

Some features require API key authentication; others do not. Whether a feature needs an API key depends on its backend endpoint — the `/v1/*` endpoints are gated when `NARRATIVE_API_KEY` is set on the server, while unversioned endpoints (projects, health, backups) are always open. **Check your local service's documentation or configuration to determine if auth is required in your setup.** By default, no API key is required.

**Features that require an API key** (when `NARRATIVE_API_KEY` is set):
- Story Generation Orchestration (`/v1/story-generation/*`)
- Canon Workshop: Mythos Library, Pattern Library, Profiles, Annotations (`/v1/canon/*`, `/v1/mythos/*`, `/v1/patterns/*`)
- Brain Dump (`/v1/story-development/braindump/*`)
- Manuscript Assist (`/v1/manuscript-assist/*`)
- Jobs & Role Model Checker (`/v1/jobs/*`, `/v1/role-model-checker/*`)

**Features that do NOT require an API key** (always accessible):
- Project management: list, create, get details, manifest, sequence, chapters (`/projects/*`)
- Health checks (`/health/*`)
- Backup management (`/backup/*`)
- API key management itself (`/auth/keys*`)

To enable authentication for the gated features:

**Step 1: Create an API key in the UI**

1. Open the app and click the **Settings** button (gear icon) in the top-right corner
2. Scroll to the **API Keys** section at the bottom
3. Enter a name for your key (e.g., "local-dev") and click **Create**
4. The server will generate a key and display its prefix (first 4 characters) and permissions

**Step 2: Configure the server**

Set the `NARRATIVE_API_KEY` environment variable to the full key value. On Windows:

```powershell
# PowerShell (current session)
$env:NARRATIVE_API_KEY = "your-full-api-key-here"

# Or add to your .env file for persistence
echo "NARRATIVE_API_KEY=your-full-api-key-here" >> .env
```

On macOS/Linux:

```bash
export NARRATIVE_API_KEY="your-full-api-key-here"
# Or add to ~/.bashrc, ~/.zshrc, or your .env file
```

**Step 3: Restart the server**

Restart Narrative Core so the new environment variable takes effect.

**How it works**

Authentication is **opt-in**: the server only enforces API key checks when `NARRATIVE_API_KEY` is set in the environment. Without it, all endpoints — including `/v1/*` — are accessible without a key. This means local development and testing work out of the box. When you do set `NARRATIVE_API_KEY`, the server's middleware intercepts requests to `/v1/*` and other protected paths, rejecting any that lack a matching `X-API-Key` header. The frontend's development proxy can be configured to forward this header automatically (see `frontend/vite.config.ts`).

**Troubleshooting**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `[401] API key required` toast | Server has `NARRATIVE_API_KEY` set, but request lacks the `X-API-Key` header | Configure the key in your environment or disable auth by unsetting `NARRATIVE_API_KEY` |
| Canon Workshop shows "API key required" banner | Same as above — `/v1/*` endpoints are gated | Follow Steps 1–3 above |
| Brain Dump stuck on "Loading..." | API call returned 401; check browser console for details | Create an API key and configure it, or temporarily disable auth |
| "Invalid or missing API key" | Key doesn't match the server's `NARRATIVE_API_KEY` value | Verify the exact key string; watch for extra spaces or quotes |

**Disabling authentication**

To run without API key requirements (e.g., for local development), simply unset or remove the `NARRATIVE_API_KEY` environment variable and restart the server. All endpoints will be accessible without authentication.

---

## Sample Stories

Four sample stories are available in `docs/sample-stories/` for testing and learning:

| Story | Author | Genre | Size |
|-------|--------|-------|------|
| The Time Machine | H.G. Wells | Classic Sci-Fi | ~200 KB |
| The Picture of Dorian Gray | Oscar Wilde | Gothic Fiction | ~455 KB |
| The Last Archive | Original | Science Fiction | ~28 KB |
| Crossing Limits | Original | Pop-Romance | ~30 KB |

Three of the four stories exceed the 30,000-character threshold and exercise the **multi-pass import pipeline**; The Last Archive exercises single-pass. See `docs/sample-stories/README.md` for detailed extraction expectations per story.

To use a sample story: open the file, copy its contents, paste into the Import Story dialog on the home page, and click Import.

---

## Creating a Project from Scratch

> **Route**: `/` (home page) → "Create New Project"

If you're starting from a blank slate:

1. Navigate to the home page (`/`)
2. Click **"Create New Project"**
3. Fill in the fields:
   - **Project Name:** required, e.g., "The Last Watch"
   - **Genre:** required, e.g., "Science Fiction"
   - **Tone Profile:** required, e.g., "Dark and Atmospheric"
   - **Story Structure:** select from dropdown (Three Act, Hero's Journey, Save the Cat, etc.)
   - **POV:** select point of view (First Person, Third Limited, Third Omni, etc.)
   - **Primary Language:** defaults to "English"
   - **Secondary Language:** optional
   - **Premise:** optional short description
4. Click **"Create"**

You'll be taken to the project's Planning workspace, where you can define your foundation, create characters, build your world bible, and plan your story structure.

---

## Importing an Existing Story

> **Route**: `/` (home page) → "Import Story"

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

Stories under 30,000 characters are processed in a single pass. Larger stories use the **multi-pass pipeline**: structure detection, per-chapter analysis, character/world/arc consolidation. Multi-pass import may take several minutes.

---

## Extracting Patterns for Story Generation

> **Route**: `/` (home page) → "Import Existing Story" modal → toggle to "Extract Patterns"

Pattern Extraction lets you paste any completed story or mythology text and have the system extract its storytelling DNA — archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities — then use those patterns to guide original story generation.

### When to Use Pattern Extraction

Use this when you want to write stories that follow the narrative DNA of an existing story, without retelling it. For example:
- Write a new mystery in the same world as Sherlock Holmes with original characters
- Apply Dune's voice profile and thematic constraints to a completely different sci-fi setting
- Extract the storytelling patterns from mythology texts and apply them to your own ideas

### Step-by-Step Guide

1. **Open the Story Import modal** from your project dashboard
2. **Toggle to "Extract Patterns"** mode
3. **Enter a project name** for the new project
4. **Select Source Type:**
   - **Narrative** — for fiction stories; includes voice profile, narrative pattern, and thematic constraints in extraction
   - **Mythology** — for mythological texts; uses the Mythos Extraction pipeline (extracts archetypal patterns, cosmic rules, symbolic motifs)
5. **Select Generation Mode:**
   - **Same World** — Your story will be set in the source story's world with original characters following extracted patterns
   - **New Characters** — Same world, but original cast fulfilling extracted archetypes (narrative source only)
   - **Transposed** — Map archetypal patterns and voice to a new setting (e.g., Dune storytelling DNA → cyberpunk)
6. **(Optional) Specify Source Corpus** — e.g., "The Shining", "Dune", "Greek Mythology". Helps the LLM contextualize the extraction.
7. **Paste story or mythology text** — The system analyzes up to 24,000 characters in a single pass.
8. **Click "Extract Patterns"** — The system analyzes your text and creates a project with:
   - Foundation profile (thematic spine, emotional promise, tone direction)
   - World Bible entries for world rules and symbolic motifs
   - Character archetypes as pattern carriers
   - Voice profile and narrative patterns (narrative source type only)
   - Thematic constraints (narrative source type only)
9. **Proceed to the Planning Workspace** to build your story guided by the extracted patterns

### Mythos Extraction (Mythology Source Type)

When you select **Source Type: Mythology**, Pattern Extraction delegates to the Mythos Extraction pipeline. This is specialized for mythological texts and extracts:
- Archetypal patterns (hero, trickster, mentor, etc.)
- Narrative structures (hubris-fall-redemption, cyclical tragedy, etc.)
- Cosmic rules and symbolic motifs
- Key entities (deities, locations, concepts)

**Generation modes for mythology:** Same World, Transposed, Pure Pattern.

### Example: Applying Dune's Storytelling DNA to a New Setting

1. Toggle to Extract Patterns mode
2. Source Type: Narrative
3. Generation Mode: Transposed
4. Source Corpus: "Dune"
5. Paste key passages from Dune
6. Click Extract Patterns
7. System extracts: political intrigue patterns, ecological world-building voice, thematic constraints about power and environment
8. Navigate to Planning Workspace and create a cyberpunk story following these patterns

### Tips

- For narrative extraction, include diverse scenes from the source story for richer pattern extraction
- The system works best with 2,000+ characters of source material
- In Same World mode, you create original characters that follow the extracted archetypes within the source story's world
- Transposed mode gives maximum creative freedom while maintaining the source story's narrative DNA
- Voice profile extraction is most accurate when the source text has a distinctive narrative voice

---

## Brain Dump: Freeform Ideation

> **Route**: `/workspace/:projectId/braindump`

Brain Dump is a free-form text canvas for unstructured idea capture. Use it early in your project to capture raw thoughts before organizing them into structured elements.

### Step-by-Step Guide

1. Navigate to the Brain Dump workspace: `/workspace/:projectId/braindump`
2. In the canvas, free-write your story ideas — characters, plot points, settings, themes, conflicts
3. No structure needed — just write freely
4. Click **"Organize"** to let the LLM categorize your ideas into characters, plot points, conflicts, etc.
5. Review the organized items in the grid
6. From organized results, you can:
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

## Foundation, Characters, and World Bible

> **Route**: `/workspace/:projectId/plan` (Planning workspace)

After seeding your project (import, extraction, or from scratch), the next step is to build the core reference data that guides all AI generation downstream.

### Foundation

The Foundation is your story's north star — a detailed narrative profile that all subsequent AI generation references.

1. Go to **Planning** mode, click the **Foundation** tab
2. Fill in:
   - **Premise** — the core story premise (1-2 sentences)
   - **Logline** — a single-sentence summary
   - **Thematic Spine** — the central theme and how it develops
   - **Emotional Promise** — what emotional experience the reader should have
   - **Tone and Voice Direction** — narrative style guidance
   - **Target Audience** — intended readership
   - **Narrative Constraints** — boundaries or rules for the story
   - **Complexity Level** — simple, moderate, complex, or intricate
   - **Success Definition** — what "success" looks like for this story
3. Click **"Save"**

The foundation is used as input by the P-100 Architect job phase. Foundation revisions are tracked — you can roll back to any previous version.

### Characters

Character profiles provide the AI with structured context about who your characters are, how they speak, and what drives them.

1. Click the **Characters** tab
2. Click **"Add Character"**
3. Fill in the character profile:
   - **Display Name** — the character's name
   - **Role in Story** — protagonist, antagonist, mentor, etc.
   - **Archetype** — the hero's journey archetype
   - **External Goal** — what the character wants to achieve
   - **Internal Need** — what the character needs to grow
   - **Misbelief or Wound** — the false belief or past trauma driving behavior
   - **Core Fear** — what the character fears most
   - **Primary Strength** — the character's key advantage
   - **Fatal Flaw or Limitation** — the character's critical weakness
   - **Voice Notes** — how the character speaks/thinks (critical for consistency checking)
   - **Backstory Summary** — key events that shaped the character
   - **Secrets, Values, Taboos** — deeper character dimensions
   - **Change Axis** — how the character evolves
   - **Continuity Facts** — immutable facts for consistency
4. Click **"Save"**
5. Use the **Relationships** section to define connections between characters

### World Bible

The World Bible is an encyclopedic reference for your story world — locations, rules, concepts, organizations, and lore.

1. Click the **World Bible** tab
2. Click **"Add Entry"**
3. Select entry type: Location, Concept, Rule, Technology, Organization, History, Culture, etc.
4. Fill in:
   - **Title** — the entry title (unique per type)
   - **Summary** — a brief description
   - **Canonical Facts** — bullet points of immutable truths
   - **Related Character IDs** — characters associated with this entry
   - **Visibility Scope** — who knows this fact (public, internal, private)
   - **Continuity Warnings** — potential conflicts or red flags
5. Click **"Save"**

Entries can be **pinned** to the World Bible Rail for quick reference while writing.

### Planning Hierarchy

The Planning workspace also provides hierarchical story planning:

```
Sequence > Chapter > Scene > Beat
```

- **Sequence Plans** — high-level story structure (Acts, movements)
- **Chapter Plans** — chapters within sequences, with word count targets and active character IDs
- **Scene Plans** — scenes within chapters, with POV character assignment
- **Beat Plans** — beats within scenes, with emotional shifts

Additional planning tools:
- **Dependencies** — view cross-entity dependency conflicts
- **Chapter Packets** — bundle planning data for AI generation
- **Storyboard Cards** — Kanban-style view for story elements
- **Flow Editor** — customize the story development pipeline stages

---

## The Generation Pipeline: P-100 through P-400

> **Route**: `/workspace/:projectId/plan` → Job Launch Panel (right sidebar)

Once your foundation, characters, and world bible are in place, you can launch AI jobs to generate your story. The pipeline has four phases:

### P-100: Architect

Generates the overall story architecture from your foundation and brain dump:
- Project architecture document
- Story sequences with beats
- Chapter outlines

**To launch:** Select phase **P-100 (Architect)** in the Job Launch Panel, click **"Launch"**.

### P-200: Sequencer

Plans the detailed sequence of events:
- Assigns chapters to sequences
- Maps character arcs to specific scenes
- Creates the dependency graph

**To launch:** Select phase **P-200 (Sequencer)**, click **"Launch"**.

### P-300: Drafter

Writes actual manuscript prose. Before drafting, the **State-Aware Narrative Controller** runs three automatic quality checks:

1. **Scene Context Injection** — queries character profiles and world bible entries, injects them into the LLM prompt as structured constraints (archetypes, voice notes, goals, canonical facts). If the project was seeded via Pattern Extraction, pattern guidance (voice profile, world rules, thematic constraints) is also injected.

2. **Consistency Critic** — after the draft is generated, a separate LLM pass checks whether each character's dialogue and actions match their profile. If violations are found, triggers an automatic rewrite.

3. **Entity Intake** — detects new characters appearing in the draft prose that aren't yet in your character profiles. Extracts skeletal profiles (name, inferred archetype, inferred goal) and saves them for review.

These checks never block or fail the pipeline — if any check encounters an error, the system logs a warning and proceeds with the original draft.

**To launch:** Select phase **P-300 (Drafter)**, click **"Launch"**.

### P-400: Compiler

Compiles the final manuscript:
- Performs cross-chapter consistency checks
- Creates the polished manuscript document
- Generates review findings

**To launch:** Select phase **P-400 (Compiler)**, click **"Launch"**.

### Monitoring Progress

Monitor job progress in the Job Launch Panel. When complete:
1. Switch to **Writing** mode
2. Select a manuscript document from the left sidebar
3. Read the generated chapter in the center panel
4. Check the right sidebar (Aids Panel) for AI-generated revision suggestions

---

## Multi-Chapter Generation

When your story has multiple chapters, you can draft them sequentially with cross-chapter continuity.

### How It Works

Each chapter draft benefits from what happened in previous chapters:
- **Prior chapter context**: The last 3 completed chapters are summarized and included in the LLM prompt
- **Active character filtering**: If you have a ChapterPlan with `active_character_ids`, only those characters are injected into the prompt
- **Continuity tracking**: Key events, character states, and unresolved threads from prior chapters guide new drafts

### Batch Mode

For drafting multiple chapters in a single job, use the `chapter_ids` list in the job payload. This triggers sequential drafting with automatic context propagation:

1. **Draft chapter** — P-300 generates the chapter using architect output, character profiles, world constraints, and prior chapter summaries
2. **Summarize** — ChapterSummarizerService extracts key events, character states, and unresolved threads
3. **Create ManuscriptDocument** — Auto-persisted for Writing workspace integration
4. **Propagate context** — Summary injected into next chapter (last 3 chapters max)

Each chapter produces: output file (`chapters/{chapter_id}.md`), step record, and ManuscriptDocument. Failed chapters are logged but don't abort the job.

### Checking Results

After a batch job completes:
- **Job status**: `GET /v1/jobs/{job_id}/status` — shows completion count
- **Step records**: `GET /v1/jobs/{job_id}/steps` — one step per chapter
- **ManuscriptDocuments**: List from the Writing workspace sidebar
- **Inspect view**: Navigate to `/workspace/{projectId}/inspect/{jobId}`

---

## Manuscript LLM Assist: Interactive Editing with AI

> **Route**: `/workspace/:projectId/write` (Writing workspace)

Manuscript LLM Assist lets you select text in the manuscript editor and request AI-powered assistance: developmental reviews, line edits, canon checks, continuations, alternate versions, and story forks — all with version conflict protection and canon risk assessment.

### When to Use Manuscript Assist

Use this when you want to:
- Get developmental feedback on a specific passage or the whole manuscript
- Request a line edit, expansion, compression, or rewrite of selected text
- Check whether edited content contradicts locked canon facts
- Generate a continuation from your current cursor position
- Fork an alternate story branch from a selected passage

### Step-by-Step Guide

1. **Navigate to the Writing workspace**: `/workspace/:projectId/write`
2. **Open a manuscript document** from the left sidebar
3. **Select text** by clicking and dragging in the editor
4. **Assist toolbar appears** with two categories of actions:

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

5. **Submit the assist request** — optionally add a custom instruction (max 5,000 characters)
6. **Review suggestions** in the right panel (Aids Panel):
   - Each suggestion shows: source text, proposed text, rationale, canon risk level, and confidence score
   - Canon risk ranges from `none` → `low` → `medium` → `high` → `blocking`
7. **Apply** a suggestion — replaces the target range, increments document version
8. **Reject or archive** suggestions you don't want

### Version Conflict Protection

Every manuscript has a version number. When you apply a suggestion, the system checks that the current version matches the expected version. If another edit happened between requesting and applying, you'll get a conflict error (HTTP 409) and need to re-request the assist.

### Tips

- **Select meaningful passages.** Line edits on single sentences produce better results than whole-chapter selections.
- **Check canon risk before applying.** Suggestions marked `high` or `blocking` contradict locked canon — review carefully.
- **Developmental review first.** Run a document-wide developmental review before doing line edits.
- **Fork early, merge late.** Use "Fork from Selection" to explore alternate directions without losing your main manuscript.

---

## Review and Quality Checks

> **Routes**: `/workspace/:projectId/review`, `/workspace/:projectId/inspect`

### Role Model Checker

The Role Model Checker analyzes your generated content against multiple narrative roles:
- **Planner** — does the plot make logical sense?
- **Character Analyst** — are characters consistent and well-developed?
- **Consistency Checker** — do facts align across chapters?
- **Tone Monitor** — is the tone consistent?
- **Pacing Reviewer** — is the pacing appropriate?

1. Go to the **Checker** tab in the Planning workspace
2. Select roles to check
3. Click **"Run Checker"**
4. Review findings in the **Review** workspace

### Review Workspace

1. Navigate to `/workspace/:projectId/review`
2. **Findings tab** — browse findings filtered by severity (ERROR, WARNING, SUGGESTION)
3. Make a decision on each finding:
   - **Accept** — acknowledge and address
   - **Reject** — dismiss the finding
   - **Defer** — postpone for later consideration
   - **Escalate** — mark for priority review
   - **Refine** — request a revised check
4. **Inspect Run Links tab** — trace findings back to their source jobs

### Inspect Workspace

1. Navigate to `/workspace/:projectId/inspect/:jobId`, or click "Jump to Source" from a review finding
2. The Inspect View shows:
   - **Step Timeline** — each step of job execution with timing
   - **Artifact Lineage** — how artifacts were created and modified
   - **Attempt History** — all retry attempts for failed jobs
   - **Logs** — raw job logs

---

## Canon Workshop: Customizing Source Material Before Generation

> **Route**: `/workspace/:projectId/canon`

> **Why before generating?** Always visit the Canon Workshop *before* launching a generation run. Lock critical facts, set your policy, and preview your packet — this prevents wasted runs on contradictory content.

The Canon Workshop gives you fine-grained control over what canon material gets used during story generation, how it's classified (locked, mutable, forbidden), and which reusable patterns should guide the output.

### When to Use the Canon Workshop

Use this when you want to:
- Edit extracted characters, world entries, mythos motifs, or patterns before generation
- Mark specific facts as **locked canon** (must not be contradicted) or **mutable** (allowed to change)
- Create reusable generation profiles that save your scope, policy, and brief template
- Preview exactly what canon will be sent to the executor before launching a run
- Manage mythos entries from mythology extraction or pattern entries from pattern extraction as editable records

### Step-by-Step Guide

1. **Navigate to the Canon workspace**: `/workspace/:projectId/canon`
2. **Overview tab** — see summary counts for characters, world entries, mythos, patterns, annotations, and profiles
3. **Characters tab** — browse character profiles with annotation controls:
   - Click a character to open the editor
   - Use the **Canon Annotation Toolbar** on any field to mark it as: `locked`, `soft_guidance`, `mutable`, or `forbidden_contradiction`
   - Locked fields appear with a lock badge; they become hard constraints during generation
4. **World tab** — browse world bible entries with the same annotation controls
5. **Mythos tab** — edit mythos entries extracted from mythology texts:
   - Entry types: archetype, motif, cosmic_rule, symbol, ritual, deity, cycle, theme
   - Filter by entry type using the type filter chips
6. **Patterns tab** — edit reusable narrative patterns extracted from stories:
   - Pattern types: plot, character, relationship, world, theme, scene, structure
7. **Generation Rules tab** — configure canon policy rules:
   - Locked character/world fields
   - Allowed changes
   - Forbidden contradictions
   - Continuity strictness level
8. **Packet Preview tab** — see exactly what the executor will receive:
   - Selected characters, world entries, mythos, and patterns
   - Derived canon policy from annotations
   - Prompt budget summary
   - Source hashes for idempotency verification

### Canon Customization Profiles

Profiles let you save reusable generation configurations:

1. Click **"New Profile"** in the Overview tab
2. Fill in:
   - **Name** — e.g., "Sequel with Locked Characters"
   - **Description** — what this profile is for
   - **Default Generation Mode** — sequel, prequel, side_story, etc.
   - **Canon Scope** — which characters, world entries, mythos, and patterns to include
   - **Canon Policy** — locked fields, allowed changes, forbidden contradictions, strictness
   - **Generation Brief Template** — reusable brief text
3. Click **"Save"**
4. Later, select a saved profile and click **"Preview Packet"** → **"Submit Generation"**

### Field-Level Annotations

Annotations are the core mechanism for controlling generation behavior:

- **Locked** (`locked`) — this field must not be contradicted in generated content. Violations are blocking.
- **Soft Guidance** (`soft_guidance`) — the generator should respect this but minor deviations are acceptable.
- **Mutable** (`mutable`) — the generator is explicitly allowed to change this field.
- **Forbidden Contradiction** (`forbidden_contradiction`) — this specific text must not appear in generated content.

Annotations can be scoped to specific generation modes (e.g., lock backstory for sequels but allow mutation for alternate routes).

---

## Story Generation Orchestration

> **Route**: `/workspace/:projectId/generate`

> **Why canon matters here:** The Story Generation pipeline builds a **Canon Packet** — a snapshot of your characters, world entries, arcs, and continuity threads. This packet is the LLM's entire memory of your story for this run. If it's too large (over 120K characters), the system truncates lower-priority entries first. That's why visiting the Canon Workshop *before* generating is critical.

Story Generation lets you take an existing project's canon and generate a new canon-congruent story — either within the same project or forked into a brand-new project. The system builds a deterministic canon packet, runs a 4-phase generation pipeline (plan → draft → gate → compile), and enforces consistency gates.

### When to Use Story Generation

Use this when you want to:
- Write a sequel, prequel, or side story using characters and world from an existing project
- Fork selected characters into a completely new setting
- Generate an alternate route where key decisions played out differently
- Create a new arc within the same project without manually rebuilding context

### Step-by-Step Guide

1. **Navigate to the Generate workspace**: `/workspace/:projectId/generate`
2. **Open the Generation Wizard** — it loads your project's characters and world bible entries automatically
3. **Select Generation Mode:**
   - **Same Project — New Arc** — adds a new narrative arc within the existing project
   - **Same Project — Sequel** — continues the story after the current ending
   - **Same Project — Prequel** — generates events that happened before the current story
   - **Same Project — Side Story** — explores a parallel storyline with shared canon
   - **Same Project — Alternate Route** — reimagines key decisions from the existing story
   - **New Project — Character Fork** — copies selected characters into a new project
   - **New Project — World Fork** — copies the world bible into a new project
   - **New Project — Hybrid Fork** — copies both characters and world elements
4. **Select Destination:**
   - **Same Project** — specify the target project ID
   - **New Project** — enter a name for the new project
5. **Select Canon Scope** — choose what source material the generator should respect:
   - Characters, World Bible Entries, Arcs, Continuity Threads
6. **Enter a Generation Brief** — describe what you want the new story to accomplish (required, max 10,000 characters)
7. **Configure Canon Policy:**
   - **Locked Character Fields** — cannot be changed (default: display_name, role_in_story, backstory, voice_notes, continuity_facts, relationships)
   - **Locked World Fields** — immutable world facts (default: entry_type, title, summary, canonical_facts)
   - **Allowed Changes** — explicitly permitted modifications
   - **Forbidden Contradictions** — specific phrases that must not appear
   - **Continuity Strictness** — `warn`, `block`, `repair_once`, or `repair_twice`
8. **Set Chapter Count** — target number of chapters (1–100)
9. **Submit the Run** — the system creates a generation run and queues 4 phases:
   - **G-200 Plan** — generates a new story architecture from the canon packet
   - **G-300 Draft** — drafts each chapter with canon context and prior summaries
   - **G-350 Gate** — checks every artifact against locked canon facts
   - **G-400 Compile** — assembles the final manuscript (only if blocking gates pass)
10. **Monitor Progress** — run cards show status, job IDs, and warnings
11. **Review Gate Results** — click a run to see which gates passed or failed
12. **Inspect or Repair** — failed gates link to the Inspect view

### Fork Preview

Before committing to a fork, use the **Fork Preview** button to see exactly what would be copied:
- Selected characters and their remapped target IDs
- Selected world bible entries
- Arcs and continuity threads
- Foundation profile that will be created in the target project

### Tips

- **Visit Canon Workshop first.** Lock critical facts and set policy before submitting.
- **Start with a small scope.** Select only the characters and world entries most relevant to the new story.
- **Use forbidden contradictions wisely.** List specific terms or facts that must not appear.
- **Prefer `warn` over `block` for exploration.** Blocking stops generation entirely.
- **Review gate results before promoting.** Even passing gates may have warnings worth checking.

---

## Exporting and Importing Projects

> **Route**: `/` (home page) — Project List actions

Project Export and Import let you create complete ZIP archive backups of any project and restore them as new projects elsewhere. This supports moving work between machines, archiving completed stories, or sharing project templates.

### When to Use Export/Import

Use this when you want to:
- Create a portable backup of a completed project
- Move a project from one machine or installation to another
- Share a project setup with another user
- Archive a finished story for safekeeping

### Exporting a Project

Export creates a synchronous ZIP archive download containing:
- **Project directory** — manifest.json, bible.db, sequences.json, chapters/, exports/, .telemetry, .structured_log
- **Operations DB dump** — all 49 tables scoped to the project_id
- **Metadata** — export_version, project name, project ID, export timestamp

**Step-by-step:**

1. Navigate to the home page (`/`) — the Project List view
2. Find the project you want to export in the grid
3. Click the **Export** button (archive icon) on the project row
4. The browser will download a ZIP file named `{project_name}_export.zip` immediately

### Importing an Exported Project

Import takes a previously exported ZIP file and creates a **brand new project** from it. The original source project is never modified.

> **Important**: Import always creates a brand-new project with a fresh UUID. It does NOT overwrite or merge with any existing project.

**Step-by-step:**

1. Navigate to the home page (`/`)
2. Click **"Import Project"** (button above the project list)
3. The import wizard opens:
   - **Drag & drop** your exported ZIP file, or click to browse
   - Enter a **new project name**
4. Click **"Import Project"**
5. The system validates the ZIP and runs the import asynchronously:
   - Extracts to an isolated temp directory with path traversal protection
   - Runs schema version migration if needed
   - Creates a new project with restored files and database records
6. A progress indicator shows: pending → processing → completed (or failed)
7. On success, you're redirected to the imported project's workspace

### Schema Versioning and Migration

Every export includes an `export_version` field. Importing an older export into a newer installation applies a forward migration pass. The system never downgrades your schema.

### Troubleshooting Export/Import

| Issue | Solution |
|-------|----------|
| Export button does nothing | Ensure your project has a valid manifest and database; check browser console |
| ZIP download is very large (500+ MB) | Operations DB grows over time with job records. Expected for projects with extensive history |
| Import fails with "invalid export" | Ensure the ZIP was created by Narrative Engine and contains `metadata.json` |
| Import shows "processing" indefinitely | Large DB dumps take time. Check server logs; typical import is 15-30 seconds |
| Missing data after import | Verify the ZIP contains both `metadata.json` and the project directory |

---

## Story Branching

> **Route**: `/workspace/:projectId/plan` → Branches tab

Branches work like Git branches for your story — you can explore multiple versions, compare them, and merge the best elements.

### Creating Branches

1. Click the **Branches** tab in the Planning workspace
2. Click **"Create Branch"**
3. Name it (e.g., "Alternative Ending") with a description
4. Click **"Set Active"** to switch to this branch
5. Draft this alternate version by launching P-300

### Branch Comparisons

1. Select two branches from the comparison form
2. Click **"Compare"** to generate a comparison analysis
3. Review differences in draft content, planning entities, character development, and world bible entries

### Merge Decisions

1. Select source and target branches
2. Enter a **merge rationale** explaining why you're merging
3. Click **"Create Merge Decision"**
4. The merge decision is recorded and the source branch state can be updated

### Tips

- Only one branch is active at a time — set the active branch explicitly before launching jobs
- Use branches for endings — explore multiple endings in parallel, then merge the best elements
- MERGED branches are read-only; ARCHIVED branches are preserved for reference

---

## Level 1: Your First Simple Story

> **Integrated workflow** — creates a simple short story from scratch using basic features.
> For detailed feature explanations, see the sections above.

### Step 1: Create a Project

Navigate to `/`, click **"Create New Project"**, fill in name, genre, tone, structure, POV, and language. Click **"Create"**.

### Step 2: Brain Dump Your Ideas

Switch to **Brain Dump** mode. Free-write your story ideas. Click **"Organize"** to let AI categorize them.

### Step 3: Build Foundation and Characters

Go to **Planning** mode:
- **Foundation tab** — fill in premise, logline, thematic spine
- **Characters tab** — create at least 2-3 characters with voice notes
- **World Bible tab** — add 2-3 key entries

### Step 4: Run the Pipeline

From the Job Launch Panel (right sidebar):
1. Launch **P-100 (Architect)** — generates story architecture
2. Launch **P-200 (Sequencer)** — plans detailed sequences
3. Launch **P-300 (Drafter)** — writes prose with automatic quality checks
4. Launch **P-400 (Compiler)** — compiles the final manuscript

### Step 5: Review and Polish

1. Switch to **Writing** mode — read the generated chapter
2. Use **Manuscript Assist** to line-edit, expand, or rewrite passages
3. Run the **Role Model Checker** for consistency analysis
4. Review findings in the **Review** workspace

---

## Level 2: Medium Complexity with Branching and Review

> **Integrated workflow** — builds on Level 1, adds branching, review decisions, and inspect.
> For detailed feature explanations, see the sections above.

### Step 1: Detailed Setup

Create a project with a detailed foundation (premise, logline, thematic spine, emotional promise, narrative constraints). Build 4-6 characters with full profiles. Create 8-10 world bible entries.

### Step 2: Run the Full Pipeline

Execute P-100 through P-400. Review auto-detected characters from Entity Intake.

### Step 3: Explore Story Branches

1. Go to **Branches** tab
2. Create branches for alternate directions (e.g., "Alternative Ending")
3. Set each branch active and run P-300 for each
4. Use **Branch Comparisons** to side-by-side compare chapters
5. Use **Merge Decisions** to consolidate the best elements

### Step 4: Deep Review

1. Run the **Role Model Checker** for all roles
2. Review findings in the **Review** workspace — accept, reject, or defer each finding
3. Use **Inspect** to trace any problematic job runs
4. Iterate: update foundation or characters, re-run phases as needed

---

## Level 3: Complex Story with Full Pipeline

> **Integrated workflow** — professional workflow using all features together.
> For detailed feature explanations, see the sections above.

### Step 1: Comprehensive Setup

Create a project with:
- Detailed foundation (all fields, including complexity level and success definition)
- 5-6 characters with full profiles (backstory, voice notes, secrets, values, taboos, change axis)
- 15-20 world bible entries across multiple types
- Relationships between characters

### Step 2: Arc Management

1. Go to **Arcs** tab
2. Create arc candidates for each major character
3. Define stage maps with narrative progression
4. Select the arcs that best serve your story

### Step 3: Full Pipeline with Multi-Chapter Generation

1. Run P-100 through P-400
2. Use batch multi-chapter mode for P-300 (drafts all chapters sequentially with prior context propagation)
3. Review auto-detected characters from Entity Intake

### Step 4: Multiple Branches and Decisions

1. Create 3+ branches for different endings
2. Run the full pipeline for each branch
3. Use Branch Comparisons and Merge Decisions
4. Record key creative decisions in the **Decisions** tab

### Step 5: Canon Workshop and Story Generation

1. Visit **Canon Workshop** — lock critical facts, set policy
2. Navigate to **Generate** workspace
3. Configure a generation run (sequel, side story, or fork)
4. Submit and monitor the G-200 through G-400 pipeline
5. Review gate results, repair if needed

### Step 6: Manuscript Polish

1. Use **Manuscript Assist** for developmental review, line edits, canon checks
2. Run the **Role Model Checker** for final consistency pass
3. Inspect any remaining issues
4. Export the completed project for archiving

---

## Tips and Best Practices

### Workflow Recommendations

1. **Start with Foundation, not Drafting.** A well-defined foundation makes every subsequent AI generation coherent.
2. **Use Brain Dump liberally.** Capture raw ideas first, organize them later. Don't self-censor at the ideation stage.
3. **Build characters before sequences.** Character-driven stories need character depth before plot planning.
4. **Run the Checker early.** Don't wait until the end — run checks after each major milestone.
5. **Use branches for endings.** Explore multiple endings in parallel, then merge the best elements.
6. **Review findings actively.** Don't just auto-accept. Each finding represents a creative decision.
7. **Inspect when confused.** If AI output seems off, use Inspect to trace the execution path.

### Narrative Controller Tips

The State-Aware Narrative Controller (Scene Context, Consistency Critic, Entity Intake) runs automatically on every P-300 draft:

1. **Fill out voice notes for your characters.** The Consistency Critic uses voice notes to detect when dialogue doesn't match established speech patterns.
2. **Set canonical facts in your world bible.** Scene Context injection pulls canonical facts from world bible entries.
3. **Review auto-detected characters after drafting.** Entity Intake creates skeletal profiles for new characters in draft prose.
4. **Don't worry about critic rewrites adding latency.** The consistency critic adds one extra LLM call per draft. Intentional for quality.

### Canon Workshop Tips

1. **Lock before generating.** Visit the Canon Workshop *before* submitting a generation run.
2. **Use profiles for repeatability.** Save a customization profile if you generate multiple sequels or alternate routes.
3. **Preview your packet.** The Packet Preview tab shows exactly what the executor will receive.

### Manuscript Assist Tips

1. **Select meaningful passages.** Line edits on single sentences produce better results than whole-chapter selections.
2. **Check canon risk before applying.** Suggestions marked `high` or `blocking` contradict locked canon.
3. **Developmental review first.** Structural feedback often changes what you'd edit at the line level.
4. **Fork early, merge late.** Use "Fork from Selection" to explore alternate directions.

### Common Pitfalls

- **Don't skip the manifest.** The AI uses manifest settings to guide generation. Wrong settings = wrong tone.
- **Don't mix branches carelessly.** Only one branch is active at a time. Set explicitly before launching jobs.
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
| **Scene Context Injection** | Automatic injection of character profiles, world bible constraints, and prior chapter context into the P-300 drafter prompt |
| **Consistency Critic** | Post-draft LLM check that verifies character dialogue and actions match their profiles; triggers automatic rewrite on violations |
| **Entity Intake** | Automatic detection of new characters in draft prose; extracts skeletal profiles and persists them for review |
| **Prior Chapter Summary** | LLM-extracted context from completed chapters: key events, character states, unresolved threads. Injected into subsequent chapters for continuity. |
| **Canon Generation Packet** | Deterministic artifact that packages snapshots of selected canon from a source project for generation. Budget-aware: truncates to 120K character cap. |
| **Generation Run** | A single invocation of the story generation pipeline (G-200 through G-400). Idempotent via request hash. |
| **Generation Mode** | How the new story relates to the source: sequel, prequel, side_story, alternate_route, character_fork, world_fork, hybrid_fork |
| **Canon Policy** | Rules governing what the generator may or may not change: locked fields, allowed changes, forbidden contradictions, continuity strictness |
| **Continuity Strictness** | How gate violations are handled: `warn`, `block`, `repair_once`, `repair_twice` |
| **G-200 Plan Phase** | Loads the canon packet and generates a new story plan: premise, arcs, chapter plans, canon obligations |
| **G-300 Draft Phase** | Iterates over planned chapters, drafting prose with full canon context and prior chapter summaries |
| **G-350 Gate Phase** | Checks every generated artifact against locked canon facts and forbidden contradictions |
| **G-400 Compile Phase** | Assembles the final manuscript from chapter drafts. Only runs if no blocking gates failed. |
| **Story Forking** | Creates a target project and copies selected canon into it with deterministic ID remapping and provenance tracking |
| **Pattern Extraction** | Analyzes any story or mythology text and extracts storytelling DNA — patterns, structure, voice, constraints, entities. Supports narrative and mythology source types. |
| **Voice Profile** | Extracted narrative characteristics: voice, rhythm, density, humor, emotional temperature. Injected into P-300 via SceneContext. |
| **Canon Workshop** | Dedicated workspace at `/workspace/:projectId/canon` for editing canon, marking annotations, managing entries, creating profiles, previewing packets |
| **Canon Annotation** | Field-level classification: `locked`, `soft_guidance`, `mutable`, `forbidden_contradiction` |
| **Canon Customization Profile** | Saved reusable generation configuration: name, scope, policy, brief template |
| **Manuscript LLM Assist** | Interactive editing: select text and request AI assistance. Suggestions include canon risk ratings and confidence scores. |
| **Version Conflict Protection** | Manuscript assist applies suggestions against an expected document version. HTTP 409 on mismatch. |
| **Project Export** | Creates a complete ZIP archive of a project (directory + operations DB). Synchronous download. |
| **Project Import** | Restores an exported ZIP as a brand-new project with a fresh UUID. Asynchronous with progress tracking. |
