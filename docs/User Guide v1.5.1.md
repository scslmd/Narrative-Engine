# Narrative Engine - User Guide v1.6.0

This guide walks you through using Narrative Engine from first project to a fully-developed complex story, following the natural creative lifecycle: seed your project, refine canon, generate stories, and polish manuscripts.

---

## Table of Contents

### Getting Started

1. [Getting Started](#getting-started)

### Seeding Your Project

2. [Importing an Existing Story](#importing-an-existing-story)
3. [Extracting Mythos for Pattern-Based Story Generation](#extracting-mythos-for-pattern-based-story-generation)
4. [Extracting Patterns for Story Generation](#extracting-patterns-for-story-generation)

### Transferring Projects

5. [Exporting and Importing Projects](#exporting-and-importing-projects)

### Refining Canon

6. [Canon Workshop: Customizing Source Material Before Generation](#canon-workshop-customizing-source-material-before-generation)

### Generating Stories

7. [Story Generation Orchestration](#story-generation-orchestration)

### Polishing Manuscripts

8. [Manuscript LLM Assist: Interactive Editing with AI](#manuscript-llm-assist-interactive-editing-with-ai)

### Learning Paths (Levels 1–3)

9. [Level 1: Your First Simple Story](#level-1-your-first-simple-story)
10. [Level 2: Medium Complexity with Branching and Review](#level-2-medium-complexity-with-branching-and-review)
11. [Level 3: Complex Story with Full Pipeline](#level-3-complex-story-with-full-pipeline)

### Reference

12. [Tips and Best Practices](#tips-and-best-practices)

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

### Sample Stories

Four sample stories are available in `docs/sample-stories/` for testing and learning:

| Story | Author | Genre | Size |
|-------|--------|-------|------|
| The Time Machine | H.G. Wells | Classic Sci-Fi | ~200 KB |
| The Picture of Dorian Gray | Oscar Wilde | Gothic Fiction | ~455 KB |
| The Last Archive | Original | Science Fiction | ~28 KB |
| Crossing Limits | Original | Pop-Romance | ~30 KB |

Three of the four stories exceed the 30,000-character threshold and exercise the **multi-pass import pipeline**; The Last Archive exercises single-pass. See `docs/sample-stories/README.md` for detailed extraction expectations per story.

To use a sample story: open the file, copy its contents, paste into the Import Story dialog on the home page, and click Import.

### Importing an Existing Story (`/`)

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

## Extracting Mythos for Pattern-Based Story Generation

> **Route**: `/` (home page) → "Import Existing Story" modal → toggle to "Extract Mythos"

Mythos Extraction lets you paste mythology texts and have the system extract their storytelling DNA — archetypal patterns, narrative structures, cosmic rules, and symbolic motifs — then use those patterns to guide original story generation.

### When to Use Mythos Extraction

Use this when you want to write stories that follow the narrative DNA of a mythological tradition, without retelling specific myths. For example:
- Write an original tragedy following Greek hubris-fall-redemption patterns
- Create a sci-fi story using Norse cyclical tragedy structure
- Apply Egyptian cosmic order themes to a modern corporate drama

### Step-by-Step Guide

1. **Open the Story Import modal** from your project dashboard
2. **Toggle to "Extract Mythos"** mode (next to "Import Story")
3. **Enter a project name** for the new project
4. **(Optional) Specify Source Tradition** — e.g., "Greek Mythology", "Norse Sagas". If omitted, the AI identifies it from your text.
5. **Select Generation Mode:**
   - **Same World** — Your story will be set in the mythological world with original characters following extracted patterns
   - **Transposed** — Archetypal patterns map to a new setting (e.g., Greek trickster → cyberpunk hacker)
   - **Pure Pattern** — Only narrative structures and themes apply; you're free to choose any world and genre
6. **Paste mythology texts** — Include myths, sagas, or source material. The system analyzes up to 24,000 characters in a single pass.
7. **Click "Extract Mythos"** — The system analyzes your text and creates a project with:
   - Foundation profile (thematic spine, emotional promise, tone direction)
   - World Bible entries for cosmic rules and symbolic motifs
   - Character archetypes as pattern carriers
   - Key entities (deities, locations, concepts) in same_world mode
8. **Proceed to the Planning Workspace** to build your story guided by the extracted patterns

### Example: Greek Tragedy in a Modern Setting

1. Toggle to Extract Mythos mode
2. Source Tradition: "Greek Mythology"
3. Generation Mode: Transposed
4. Paste key Greek myths (Oedipus, Antigone, etc.)
5. Click Extract Mythos
6. System extracts: hubris-fall-redemption pattern, cyclical tragedy structure, cosmic rule "fate cannot be escaped"
7. Navigate to Planning Workspace and create a modern story following these patterns

### Tips

- Include diverse myths from the tradition for richer pattern extraction
- The system works best with 2,000+ characters of source material
- In Transposed mode, the extracted archetypes become templates — you create new characters that fulfill those roles
- Pure Pattern mode gives maximum creative freedom while maintaining mythic narrative structure

---

## Extracting Patterns for Story Generation

> **Route**: `/` (home page) → "Import Existing Story" modal → toggle to "Extract Patterns"

Pattern Extraction lets you paste any completed story and have the system extract its storytelling DNA — archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities — then use those patterns to guide original story generation. This generalizes Mythos Extraction: it works with both fiction stories (`source_type: narrative`) and mythology texts (`source_type: mythology`).

### When to Use Pattern Extraction

Use this when you want to write stories that follow the narrative DNA of an existing story, without retelling it. For example:
- Write a new mystery in the same world as Sherlock Holmes with original characters
- Apply Dune's voice profile and thematic constraints to a completely different sci-fi setting
- Extract the storytelling patterns from your favorite novel and apply them to your own ideas

### Step-by-Step Guide

1. **Open the Story Import modal** from your project dashboard
2. **Toggle to "Extract Patterns"** mode (next to "Import Story" and "Extract Mythos")
3. **Enter a project name** for the new project
4. **Select Source Type:**
   - **Narrative** — for fiction stories; includes voice profile, narrative pattern, and thematic constraints in extraction
   - **Mythology** — for mythological texts; delegates to Mythos Extraction pipeline
5. **Select Generation Mode:**
   - **Same World** — Your story will be set in the source story's world with original characters following extracted patterns
   - **New Characters** — Same world, but original cast fulfilling extracted archetypes
   - **Transposed** — Map archetypal patterns and voice to a new setting (e.g., Dune storytelling DNA → cyberpunk)
6. **(Optional) Specify Source Corpus** — e.g., "The Shining", "Dune". Helps the LLM contextualize the extraction.
7. **Paste story text** — Include a completed story or significant excerpt. The system analyzes up to 24,000 characters in a single pass.
8. **Click "Extract Patterns"** — The system analyzes your text and creates a project with:
   - Foundation profile (thematic spine, emotional promise, tone direction)
   - World Bible entries for world rules and symbolic motifs
   - Character archetypes as pattern carriers
   - Voice profile and narrative patterns (narrative source type only)
   - Thematic constraints (narrative source type only)
9. **Proceed to the Planning Workspace** to build your story guided by the extracted patterns

### Example: Applying Dune's Storytelling DNA to a New Setting

1. Toggle to Extract Patterns mode
2. Source Type: Narrative
3. Generation Mode: Transposed
4. Source Corpus: "Dune"
5. Paste key passages from Dune
6. Click Extract Patterns
7. System extracts: political intrigue patterns, ecological world-building voice, thematic constraints about power and environment
8. Navigate to Planning Workspace and create a cyberpunk story following these patterns

### Difference Between Mythos Extraction and Pattern Extraction

| Aspect | Mythos Extraction | Pattern Extraction |
|--------|------------------|-------------------|
| Source material | Mythology texts only | Any story or mythology text |
| Voice profile | Not extracted | Extracted (narrative source) |
| Narrative pattern | Not extracted | Extracted (narrative source) |
| Thematic constraints | Basic thematic spine | Full thematic constraints with forbidden elements |
| Generation modes | Same World, Transposed, Pure Pattern | Same World, New Characters, Transposed |

### Tips

- For narrative extraction, include diverse scenes from the source story for richer pattern extraction
- The system works best with 2,000+ characters of source material
- In Same World mode, you create original characters that follow the extracted archetypes within the source story's world
- Transposed mode gives maximum creative freedom while maintaining the source story's narrative DNA
- Voice profile extraction is most accurate when the source text has a distinctive narrative voice

---

## Exporting and Importing Projects

> **Route**: `/` (home page) — Project List actions

Project Export and Import let you create complete ZIP archive backups of any project and restore them as new projects elsewhere. This supports moving work between machines, archiving completed stories, or sharing project templates without requiring direct file access.

### When to Use Export/Import

Use this when you want to:
- Create a portable backup of a completed project (directory structure + operations DB records)
- Move a project from one machine or installation to another
- Share a project setup with another user without exposing your full data directory
- Archive a finished story for safekeeping outside the live workspace

### Exporting a Project

Export creates a synchronous ZIP archive download containing:
- **Project directory** — manifest.json, bible.db, sequences.json, chapters/, exports/, .telemetry, .structured_log
- **Operations DB dump** — all 49 tables scoped to the project_id (projects, project_artifacts, foundation_profiles, character_profiles, world_bible_entries, arc_* tables, planning tables, draft_artifacts, manuscript_documents, jobs, step_records, job_attempts, and more)
- **Metadata** — export_version field, project name, project ID, export timestamp

**Step-by-step:**

1. Navigate to the home page (`/`) — the Project List view
2. Find the project you want to export in the grid
3. Click the **Export** button (archive icon) on the project row
4. The browser will download a ZIP file named `{project_name}_export.zip` immediately
5. The file contains a `metadata.json` with export version, project ID, and timestamp

The export is synchronous — you receive the complete ZIP in one download. No polling or progress tracking needed.

### Importing an Exported Project

Import takes a previously exported ZIP file and creates a **brand new project** from it. The original source project is never modified. All data from both the project directory and operations DB is restored into a fresh project with a new project ID.

> **Important**: Import always creates a brand-new project with a fresh UUID. It does NOT overwrite or merge with any existing project, even if the names match.

**Step-by-step:**

1. Navigate to the home page (`/`)
2. Click **"Import Project"** (button above the project list)
3. The import wizard opens:
   - **Drag & drop** your exported ZIP file into the upload area, or click to browse
   - Enter a **new project name** — this becomes the display name for the imported project
4. Click **"Import Project"**
5. The system validates the ZIP (min 1 MB, max 500 MB):
   - Checks `metadata.json` exists and is valid
   - Verifies the project directory structure (`manifest.json`, `bible.db`)
   - Detects the `export_version` for forward migration compatibility
6. The import runs asynchronously on the server:
   - Extracts the ZIP to an isolated temp directory with path traversal protection
   - Runs a schema version migration pass if the export version is older than the current version (the system only applies newer versions, not older ones)
   - Creates a new project in `data/projects/{new_project_id}/` with restored files
   - Restores operations DB records into the new project scope
   - Initializes project artifacts and registers everything in the operations registry
7. A progress indicator shows status updates:
   - **pending** — queued for processing
   - **processing** — extracting and restoring data
   - **completed** — import finished successfully (redirects to new project)
   - **failed** — an error occurred (error message displayed)
8. On success, you're redirected to the imported project's workspace

### Schema Versioning and Migration

Every export includes an `export_version` field in `metadata.json`. This tracks which schema version was current when the export was created:

- **Forward migration** — if you import an older export into a newer Narrative Engine installation, the system applies a migration pass to reconcile any changes. The import process never downgrades your schema.
- **Backward compatibility** — exports always contain the full project directory structure, so even if schema versions differ significantly, the core files (manifest.json, bible.db) remain usable.

To check the version of an exported ZIP without extracting it:

```bash
unzip -p archive.zip metadata.json | python -m json.tool
```

### Troubleshooting Export/Import

| Issue | Solution |
|-------|----------|
| Export button does nothing | Ensure your project has a valid manifest and database; check browser console for errors |
| ZIP download is very large (500+ MB) | The operations DB grows over time with job records and step data. Consider archiving rather than importing if you only need reference data |
| Import fails with "invalid export" | Ensure the ZIP was created by Narrative Engine and contains `metadata.json`. Corrupted or manually re-packed ZIPs will fail |
| Import shows "project directory missing manifest" | The source project's directory was incomplete or the ZIP is corrupted. Re-export the original project |
| Export takes a long time for large projects | Large operations DB dumps can take 30+ seconds. This is expected for projects with extensive job history |
| Missing data after import | Check that both `metadata.json` and the project directory exist in the source ZIP. The operations DB dump must contain tables matching `_OPS_TABLES_WITH_PROJECT_ID` |

---

## Canon Workshop: Customizing Source Material Before Generation

> **Route**: `/workspace/:projectId/canon`

> **Why before generating?** Always visit the Canon Workshop *before* launching a generation run. Lock critical facts, set your policy, and preview your packet — this prevents wasted runs on contradictory content.

The Canon Workshop gives you fine-grained control over what canon material gets used during story generation, how it's classified (locked, mutable, forbidden), and which reusable patterns should guide the output. It lives at `/workspace/:projectId/canon`.

### When to Use the Canon Workshop

Use this when you want to:
- Edit extracted characters, world entries, mythos motifs, or patterns before generation
- Mark specific facts as **locked canon** (must not be contradicted) or **mutable** (allowed to change)
- Create reusable generation profiles that save your scope, policy, and brief template
- Preview exactly what canon will be sent to the executor before launching a run
- Manage mythos entries from Mythos Extraction or pattern entries from Pattern Extraction as editable records

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
    - Each entry has canonical facts, pattern notes, and generation guidance
    - Filter by entry type using the type filter chips
6. **Patterns tab** — edit reusable narrative patterns extracted from stories:
    - Pattern types: plot, character, relationship, world, theme, scene, structure
    - Each pattern has beats, constraints, transposition notes, and applicable generation modes
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
    - **Generation Brief Template** — reusable brief text that gets sent to the generator
3. Click **"Save"**
4. Later, select a saved profile and click **"Preview Packet"** → **"Submit Generation"** to launch a run

### Field-Level Annotations

Annotations are the core mechanism for controlling generation behavior:

- **Locked** (`locked`) — this field must not be contradicted in generated content. Violations are blocking.
- **Soft Guidance** (`soft_guidance`) — the generator should respect this but minor deviations are acceptable.
- **Mutable** (`mutable`) — the generator is explicitly allowed to change this field.
- **Forbidden Contradiction** (`forbidden_contradiction`) — this specific text must not appear in generated content.

Annotations can be scoped to specific generation modes (e.g., lock backstory for sequels but allow mutation for alternate routes).

### Mythos Library

After running Mythos Extraction, extracted entries become editable records:

1. Navigate to `/workspace/:projectId/canon?tab=mythos`
2. Review auto-extracted entries (archetypes, cosmic rules, motifs, symbols)
3. Edit any entry: add canonical facts, refine pattern notes, set generation guidance
4. Use **"Use in Generation"** checkbox to include entries in your canon scope
5. Filter by type using the filter chips at the top

### Pattern Library

After running Pattern Extraction, extracted patterns become editable records:

1. Navigate to `/workspace/:projectId/canon?tab=patterns`
2. Review auto-extracted patterns (plot structures, character archetypes, scene templates)
3. Edit any pattern: add beats, constraints, transposition notes
4. Set which generation modes the pattern applies to
5. Use **"Use in Generation"** checkbox to include patterns in your canon scope

---

## Story Generation Orchestration

> **Route**: `/workspace/:projectId/generate`

> **Why canon matters here:** The Story Generation pipeline builds a **Canon Packet** — a snapshot of your characters, world entries, arcs, and continuity threads. This packet is the LLM's entire memory of your story for this run. If it's too large (over 120K characters), the system truncates lower-priority entries first. That's why visiting the Canon Workshop *before* generating is critical: you decide what gets included and what gets locked.

Story Generation lets you take an existing project's canon (characters, world bible, arcs) and generate a new canon-congruent story — either within the same project or forked into a brand-new project. The system builds a deterministic **canon packet** from your selected source material, runs a 4-phase generation pipeline (plan → draft → gate → compile), and enforces consistency gates to ensure generated content respects locked canon facts.

### When to Use Story Generation

Use this when you want to:
- Write a sequel, prequel, or side story using characters and world from an existing project
- Fork selected characters into a completely new setting
- Generate an alternate route where key decisions played out differently
- Create a new arc within the same project without manually rebuilding context

### Step-by-Step Guide

1. **Navigate to the Generate workspace** for your source project: `/workspace/:projectId/generate`
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
   - **Same Project** — specify the target project ID (defaults to current project)
   - **New Project** — enter a name for the new project; the system creates it automatically
5. **Select Canon Scope** — choose what source material the generator should respect:
   - **Characters** — select specific characters (or leave empty for all)
   - **World Bible Entries** — select locations, rules, concepts, etc.
   - **Arcs** — select narrative arcs to carry forward
   - **Continuity Threads** — select unresolved threads to address
6. **Enter a Generation Brief** — describe what you want the new story to accomplish (required, max 10,000 characters)
7. **Configure Canon Policy:**
   - **Locked Character Fields** — fields that cannot be changed (default: display_name, role_in_story, backstory, voice_notes, continuity_facts, relationships)
   - **Locked World Fields** — immutable world facts (default: entry_type, title, summary, canonical_facts)
   - **Allowed Changes** — explicitly permitted modifications to characters or world
   - **Forbidden Contradictions** — specific phrases or facts that must not appear in generated content
   - **Continuity Strictness** — how to handle violations:
     - `warn` — record a warning, allow generation to proceed
     - `block` — stop generation if a contradiction is detected
     - `repair_once` — attempt one automatic repair, then block if still failing
     - `repair_twice` — attempt two repairs before blocking
8. **Set Chapter Count** — target number of chapters (1–100)
9. **Submit the Run** — the system creates a generation run and queues 4 phases:
   - **G-200 Plan** — generates a new story architecture from the canon packet
   - **G-300 Draft** — drafts each chapter with canon context and prior summaries
   - **G-350 Gate** — checks every artifact against locked canon facts
   - **G-400 Compile** — assembles the final manuscript (only if blocking gates pass)
10. **Monitor Progress** — run cards show status, job IDs, and warnings
11. **Review Gate Results** — click a run to see which gates passed or failed, with reasons
12. **Inspect or Repair** — failed gates link to the Inspect view for debugging; repair actions are available when your policy allows

### Fork Preview

Before committing to a fork, use the **Fork Preview** button to see exactly what would be copied:
- Selected characters and their remapped target IDs
- Selected world bible entries
- Arcs and continuity threads
- Foundation profile that will be created in the target project

### Fork Project (Without Generation)

If you want to fork canon into a new project without immediately running generation:
1. Configure mode, destination, and scope in the wizard
2. Click **"Fork Project Only"** instead of "Submit Run"
3. The system creates the target project with copied canon but no generation jobs
4. You can then run P-100 through P-400 manually against the new project

### What Happens Behind the Scenes

**Canon Packet Builder:**
The system queries your source project and builds a deterministic packet containing snapshots of every selected character, world entry, arc, and continuity thread. The packet is budget-aware — if the total exceeds 120K characters, it truncates lower-priority entries (supporting characters before major ones, prose summaries before canonical facts).

**Generation Pipeline:**
- **G-200** loads the canon packet and asks the LLM to generate a new story plan: premise, logline, story arcs, chapter plans, and canon obligations. The plan must cite source canon IDs.
- **G-300** iterates over each planned chapter, drafting prose with full canon context (character profiles, world constraints, prior chapter summaries). Each chapter produces a draft artifact and a ManuscriptDocument.
- **G-350** runs gate checks on every generated artifact. Locked character facts, locked world facts, and forbidden contradictions are verified. If your policy allows repair, the system sends a repair prompt to fix violations.
- **G-400** assembles the final manuscript from all chapter drafts. This phase only runs if no blocking gates failed.

**Idempotency:**
Re-submitting the same request (same source project, same scope, same brief) with an idempotency key returns the existing generation run instead of creating a duplicate. The system detects conflicts via SHA-256 request hashes.

### Example: Fork Characters into a New Sci-Fi Project

1. Open Generate workspace on your fantasy project
2. Mode: **New Project — Character Fork**
3. Destination: **New Project** named "Cyberpunk Chronicles"
4. Canon Scope: select 3 characters you want to transpose
5. Brief: "Reimagine these characters in a near-future cyberpunk city. Keep their core personalities and relationships, but adapt their goals and conflicts to a corporate dystopia."
6. Policy: continuity strictness = `warn`, forbidden contradictions = ["magic", "spell", "mana"]
7. Chapter count: 5
8. Submit — the system creates the new project, copies the 3 characters with remapped IDs, and runs the generation pipeline

### Tips

- **Start with a small scope.** Select only the characters and world entries most relevant to the new story. Large packets increase latency and token costs.
- **Use forbidden contradictions wisely.** List specific terms or facts that must not appear (e.g., character deaths, resolved plot points).
- **Prefer `warn` over `block` for exploration.** Blocking stops generation entirely. Warning lets you review issues afterward.
- **Review gate results before promoting.** Even passing gates may have warnings worth checking.
- **Fork preview first.** Always preview what will be copied before committing to a fork, especially with hybrid forks.

---

## Manuscript LLM Assist: Interactive Editing with AI

> **Route**: `/workspace/:projectId/write` (Writing workspace)

> **Bridge from Story Generation:** After a generation run completes, use Manuscript Assist to polish the output — check canon consistency, refine voice, and fix continuity errors before promoting drafts.

Manuscript LLM Assist lets you select text in the manuscript editor and request AI-powered assistance: developmental reviews, line edits, canon checks, continuations, alternate versions, and story forks — all with version conflict protection and canon risk assessment.

### When to Use Manuscript Assist

Use this when you want to:
- Get developmental feedback on a specific passage or the whole manuscript
- Request a line edit, expansion, compression, or rewrite of selected text
- Check whether edited content contradicts locked canon facts
- Generate a continuation from your current cursor position
- Fork an alternate story branch from a selected passage
- See canon risk ratings and confidence scores before accepting suggestions

### Step-by-Step Guide

1. **Navigate to the Writing workspace**: `/workspace/:projectId/write`
2. **Open a manuscript document** from the left sidebar
3. **Select text** by clicking and dragging in the editor
4. **Assist toolbar appears** with two categories of actions:

**Selection-Aware Actions** (require selected text):
- **Line Edit Selection** — polish prose, fix grammar, improve flow
- **Expand Selection** — add detail, description, or dialogue to the selected passage
- **Compress Selection** — tighten the passage while preserving meaning
- **Rewrite in Same Voice** — rephrase while maintaining character voice
- **Alternate Version** — generate an alternative way to write the same scene
- **Continue from Here** — generate new content following from the selection endpoint
- **Fork from Selection** — create a branch or draft artifact diverging from this point

**Document-Wide Actions** (work on the full manuscript):
- **Developmental Review** — high-level feedback on plot, pacing, character arcs
- **Canon Check** — verify the entire document against locked canon facts
- **Character Voice Check** — flag dialogue that doesn't match character profiles
- **Pacing Review** — identify slow or rushed sections
- **Theme Review** — check thematic consistency and resonance
- **Continuity Repair** — find and suggest fixes for continuity errors

5. **Submit the assist request**:
   - For selection actions: the toolbar captures selected text, anchors, and offsets automatically
   - For document-wide actions: click the action button directly
   - Optionally add a custom instruction (max 5,000 characters) to guide the AI
6. **Review suggestions** in the right panel (Aids Panel):
   - Each suggestion shows: source text, proposed text, rationale, canon risk level, and confidence score
   - Canon risk ranges from `none` → `low` → `medium` → `high` → `blocking`
7. **Accept a suggestion**:
   - Click **"Apply"** — the suggestion replaces the target range in the manuscript
   - Document version increments automatically
   - If canon gates fail, you'll see a warning before applying
8. **Reject or archive** suggestions you don't want
9. **Fork from selection**:
   - Creates a new story branch with the alternate content
   - Records intentional divergence from the source manuscript
   - Branch appears in the Branches tab for comparison

### How Assist Works Behind the Scenes

**Text Range Resolution:**
Every assist request captures: selected text, character offsets, and 1000-character anchors before/after. When you apply a suggestion, the system resolves the exact location using offsets first, then falls back to anchor matching. This prevents applying suggestions to wrong locations if the document has been edited since the assist was requested.

**Version Conflict Protection:**
Every manuscript has a version number. When you apply a suggestion, the system checks that the current version matches the expected version. If another edit happened between requesting and applying, you'll get a conflict error (HTTP 409) and need to re-request the assist.

**Canon Gate Checks:**
Before suggestions are applied, the system runs gate checks:
- Source selection must still match (range hasn't drifted)
- Locked canon facts must not be contradicted by proposed text
- Character voice changes are flagged as warnings
- New entities in proposed text trigger entity intake

**Executor Phases:**
Assist requests run through dedicated executor phases:
- **M-500**: Manuscript assist — loads document, builds assist packet, calls LLM, parses suggestions, runs gates
- **M-550**: Assist repair — triggered when gates fail and policy allows repair; sends a repair prompt to fix violations

### Tips

- **Select meaningful passages.** Line edits on single sentences produce better results than whole-chapter selections.
- **Check canon risk before applying.** Suggestions marked `high` or `blocking` contradict locked canon — review carefully.
- **Use anchors for stability.** The system captures 1000-character anchors before/after your selection, so suggestions remain valid even if you edit nearby text.
- **Fork early, merge late.** Use "Fork from Selection" to explore alternate directions without losing your main manuscript.
- **Developmental review first.** Run a document-wide developmental review before doing line edits — structural feedback often changes what you'd edit at the line level.

---

## Learning Paths: Levels 1–3

The following levels walk you through complete workflows, from simple to complex. Each level builds on the previous one and references the features documented above. Use the **User Walkthrough** (`Narrative Engine User Walkthrough v1.5.1.md`) for a detailed step-by-step version of these same workflows.

---

## Level 1: Your First Simple Story

> **Route**: `/workspace/:projectId/plan` (Planning workspace)

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

#### What Happens Behind the Scenes (Narrative Controller)

When you launch P-300, the **State-Aware Narrative Controller** runs three quality checks automatically:

1. **Scene Context Injection** — Before drafting begins, the system queries your character profiles and world bible entries, then injects them into the LLM prompt as structured constraints (character archetypes, voice notes, goals, canonical facts). If the project was seeded via Pattern Extraction, pattern guidance (voice profile, world rules, thematic constraints) and per-chapter author direction are also injected.

2. **Consistency Critic** — After the draft is generated, a separate LLM pass checks whether each character's dialogue and actions match their profile. If Khal (archetype: "reluctant hero", voice: "terse, avoids metaphors") starts speaking in flowery poetry, the critic flags it and triggers an automatic rewrite to fix the inconsistency.

3. **Entity Intake** — If a new character appears in the draft that isn't yet in your character profiles (e.g., "Soraya watched from the shadows"), the system detects the unknown name, extracts a skeletal profile (name, inferred archetype, inferred goal) from the character's behavior in the prose, and saves it to your project for review.

These checks run on every P-300 draft automatically. They never block or fail the pipeline — if any check encounters an error, the system logs a warning and proceeds with the original draft.

### Step 5 (continued): Draft Multiple Chapters

Once your first chapter is complete, you can draft additional chapters with cross-chapter continuity:

1. In the Job Launch Panel, select phase **P-300 (Drafter)** again
2. Add `chapter_id` to the job payload (e.g., `"chapter_id": "ch-002"`)
3. Click **"Launch"**

Each chapter is written to a separate file (`chapters/ch-001.md`, `chapters/ch-002.md`, etc.). The system automatically:

- **Injects prior chapter context**: The last 3 completed chapters are summarized and included in the LLM prompt, so the drafter knows what happened previously
- **Filters active characters**: If you have a ChapterPlan with `active_character_ids`, only those characters are injected into the prompt (keeps it focused)
- **Maintains continuity**: Key events, character states, and unresolved threads from prior chapters guide the new draft

For larger projects, use the **ChapterOrchestrator** to run all chapters sequentially — each chapter waits for the prior to complete before starting.

#### Batch Multi-Chapter Mode

For drafting multiple chapters in a single job, use the `chapter_ids` list:

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

This triggers sequential drafting with automatic context propagation:

1. **Draft chapter** — P-300 generates the chapter using architect output, sequence, character profiles, world constraints, and prior chapter summaries
2. **Summarize** — ChapterSummarizerService extracts key events, character states, and unresolved threads via LLM
3. **Create ManuscriptDocument** — Auto-persisted for Writing workspace integration
4. **Propagate context** — Summary injected into next chapter (last 3 chapters max)

Each chapter produces: output file (`chapters/{chapter_id}.md`), step record, and ManuscriptDocument. Failed chapters are logged but don't abort the job.

#### Checking Batch Results

After submitting a batch job, verify the results:

**1. Check job status:**
```bash
curl http://localhost:8000/v1/jobs/{job_id}/status
```
Response shows `"status": "COMPLETED"` and detail like `"Completed 3/3 chapters."` If a chapter failed, the detail reflects partial completion (e.g., `"Completed 2/3 chapters."`).

**2. Inspect per-chapter step records:**
```bash
curl http://localhost:8000/v1/jobs/{job_id}/steps
```
Each chapter produces a step record with `step_name: "drafter-ch-XXX"`. Check individual steps for failures.

**3. List auto-created ManuscriptDocuments:**
```bash
curl "http://localhost:8000/v1/story-development/drafting/manuscript-documents?project_id={your-project-id}"
```
Each completed chapter has a ManuscriptDocument with `document_id: "ms-ch-XXX"` and the chapter's content.

**4. Read chapter files directly:**
```bash
cat data/projects/{project_id}/chapters/ch-001.md
cat data/projects/{project_id}/chapters/ch-002.md
```

**5. Inspect view (frontend):** Navigate to `/workspace/{projectId}/inspect/{jobId}` to see the step timeline and artifact lineage for the batch run.

#### What Prior Context Propagation Means for You

When you use batch mode, each chapter's draft benefits from what happened in previous chapters:

- If Chapter 1 ends with your protagonist discovering a hidden letter, Chapter 2's draft will know about that discovery
- Character states carry forward (e.g., "injured", "distrustful of allies"), so subsequent drafts maintain consistency
- Unresolved threads are tracked, increasing the chance later chapters address them

This is why batch mode produces more cohesive multi-chapter stories than launching individual jobs.

#### When a Chapter Fails Mid-Batch

If chapters `[ch-001, ch-002, ch-003]` are submitted and `ch-002` fails:
- `ch-001` is already completed (file written, ManuscriptDocument created)
- `ch-002` is logged as failed, step record shows error details
- `ch-003` still runs but without `ch-002`'s summary in its prior context

To retry a failed chapter, submit a new job with just that chapter's ID:
```json
{
  "phase": "P-300",
  "payload": {
    "project_id": "<your-project-id>",
    "chapter_ids": ["ch-002"]
  }
}
```

#### Batch Mode vs. Manual Draft Promotion

In single-chapter mode (Phase 5c), you manually promote drafts to ManuscriptDocuments using the drafting API. In batch mode, this happens automatically — you do NOT need to manually promote each chapter's draft. The ManuscriptDocument records are created with:
- `document_id`: `ms-{chapter_id}`
- `title`: from your ChapterPlan (or "Chapter {id}")
- `content`: the generated chapter markdown

---

## Level 2: Medium Complexity with Branching and Review

> **Routes**: `/workspace/:projectId/plan` (Planning) → `review` (Review) → `inspect` (Inspect)

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

> **Routes**: All workspace modes — `plan`, `write`, `review`, `inspect`, `braindump`, `generate`, `canon`

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
- Injects character anchors, world constraints, prior chapter context (last 3 chapters max), and pattern guidance (voice profile, world rules, thematic constraints) into the LLM prompt via SceneContext
- Applies per-chapter author direction via SceneContext's `author_prompt` field
- Writes actual manuscript chapters using your character profiles and world bible as grounding
- Supports multi-chapter generation: pass `chapter_id` in job payload to write to `chapters/{chapter_id}.md`
- Filters active characters from ChapterPlan when `chapter_id` is provided (keeps prompt focused)
- Runs a consistency critic after generation to catch character voice drift or behavior that contradicts profiles, triggering automatic rewrites when needed
- Detects new characters appearing in the draft prose and auto-extracts skeletal profiles for your review (Entity Intake)
- Creates draft artifacts with revision suggestions
- Default output budget: 8000 tokens (~2000 words per chapter, overridable via payload)

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

### Narrative Controller Tips

The State-Aware Narrative Controller (Scene Context, Consistency Critic, Entity Intake) runs automatically on every P-300 draft. To get the most out of it:

1. **Fill out voice notes for your characters.** The Consistency Critic uses voice notes to detect when a character's dialogue doesn't match their established speech patterns. Vague or empty voice notes = fewer useful critic flags.
2. **Set canonical facts in your world bible.** Scene Context injection pulls canonical facts from world bible entries and feeds them to the drafter. The more facts you define, the more grounded your drafts will be.
3. **Review auto-detected characters after drafting.** Entity Intake creates skeletal profiles for new characters that appear in draft prose. Check the Characters tab after each P-300 run -- you may find auto-generated profiles with inferred archetypes and goals that need fleshing out.
4. **Don't worry about critic rewrites adding latency.** The consistency critic adds one extra LLM call per draft (plus a rewrite call if violations are found). This is intentional for quality. If you need faster iteration during early exploration, you can still run the stub backend.

### Common Pitfalls

- **Don't skip the manifest.** The AI uses manifest settings to guide generation. Wrong settings = wrong tone.
- **Don't mix branches carelessly.** Only one branch is active at a time. Set the active branch explicitly before launching jobs.
- **Don't ignore foundation revisions.** If later chapters contradict your foundation, check the revision cues tab.
- **Don't overwrite character profiles.** If you need variations, create additional characters rather than modifying existing ones.

### Canon Workshop Tips

1. **Lock before generating.** Visit the Canon Workshop *before* submitting a generation run. Locked fields become hard constraints during G-350 gate checks.
2. **Use profiles for repeatability.** Save a customization profile if you generate multiple sequels or alternate routes — you won't need to reconfigure scope and policy each time.
3. **Preview your packet.** The Packet Preview tab shows exactly what the executor will receive. Use it to catch missing entries or budget warnings before committing.

### Manuscript Assist Tips

1. **Select meaningful passages.** Line edits on single sentences produce better results than whole-chapter selections.
2. **Check canon risk before applying.** Suggestions marked `high` or `blocking` contradict locked canon — review carefully.
3. **Developmental review first.** Run a document-wide developmental review before doing line edits — structural feedback often changes what you'd edit at the line level.
4. **Fork early, merge late.** Use "Fork from Selection" to explore alternate directions without losing your main manuscript.

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
| **Scene Context Injection** | Automatic injection of character profiles, world bible constraints, and prior chapter context into the P-300 drafter prompt before generation begins |
| **Consistency Critic** | Post-draft LLM check that verifies character dialogue and actions match their profiles; triggers automatic rewrite on violations |
| **Entity Intake** | Automatic detection of new characters in draft prose; extracts skeletal profiles (name, archetype, goal) and persists them for review |
| **Prior Chapter Summary** | LLM-extracted context from completed chapters, including key events (max 10), character states (max 10), and unresolved threads (max 5). Automatically generated by ChapterSummarizerService after each chapter draft in batch mode. Injected into subsequent chapters for continuity. |
| **ChapterSummarizerService** | LLM-based service that reads completed chapter markdown and extracts structured PriorChapterSummary. Follows the ConsistencyCriticService pattern: error-tolerant, never blocks the pipeline. |
| **ChapterOrchestrator** | Programmatic service for running multiple P-300 jobs sequentially across chapters (one job per chapter). For batch mode within a single job, use the `chapter_ids` payload instead. |
| **Canon Generation Packet** | Deterministic artifact that packages snapshots of selected characters, world bible entries, arcs, and continuity threads from a source project for use in story generation. Budget-aware: truncates to 120K character cap by dropping lower-priority entries first. |
| **Generation Run** | A single invocation of the story generation pipeline (G-200 through G-400). Identified by `generation_id`, tracks source project, target project, mode, job IDs, status, gate results, and created artifacts. Idempotent via request hash and optional idempotency key. |
| **Generation Mode** | How the new story relates to the source: same_project_new_arc, same_project_sequel, same_project_prequel, same_project_side_story, same_project_alternate_route, new_project_character_fork, new_project_world_fork, or new_project_hybrid_fork. |
| **Canon Policy** | Rules governing what the generator may or may not change: locked character/world fields, allowed changes, forbidden contradictions, and continuity strictness (warn, block, repair_once, repair_twice). |
| **Continuity Strictness** | How gate violations are handled: `warn` records a warning and proceeds; `block` stops generation; `repair_once` attempts one automatic repair then blocks; `repair_twice` allows two repairs. |
| **G-200 Plan Phase** | First generation phase. Loads the canon packet and generates a new story plan: premise, logline, arcs, chapter plans, and canon obligations. Must cite source canon IDs. |
| **G-300 Draft Phase** | Second generation phase. Iterates over planned chapters, drafting prose with full canon context and prior chapter summaries. Produces draft artifacts and ManuscriptDocuments. |
| **G-350 Gate Phase** | Third generation phase. Checks every generated artifact against locked canon facts and forbidden contradictions. Applies repair policy for violations. |
| **G-400 Compile Phase** | Final generation phase. Assembles the final manuscript from chapter drafts. Only runs if no blocking gates failed. |
| **Gate Result** | Record of a consistency check: gate name, pass/fail status, severity (info/warning/blocking), reasons, and repair metadata. Persists in `generation_gate_results` table. |
| **Story Forking** | Creates a target project and copies selected canon (characters, world entries, arcs) into it with deterministic ID remapping and provenance tracking. Can run without generation for manual pipeline control. |
| **Fork Preview** | Validates selected canon scope and returns what would be copied in a fork — characters, world entries, arcs, threads — before committing to the operation. |
| **Pattern Extraction** | Generalized service that analyzes any story or mythology text and extracts storytelling DNA — archetypal patterns, narrative structure, voice profile, thematic constraints, world rules, and entities. Supports narrative and mythology source types with three generation modes (same_world, new_characters, transposed). |
| **Voice Profile** | Extracted narrative characteristics: narrative_voice, sentence_rhythm, descriptive_density, humor_level, emotional_temperature. Injected into P-300 drafter prompts via SceneContext's pattern_guidance field. Available for narrative source type only. |
| **Narrative Pattern** | Extracted structural characteristics: pacing, chapter_structure, conflict_type, dialogue_style, scene_transition. Guides P-100 architect and P-300 drafter in maintaining the source story's structural DNA. Available for narrative source type only. |
| **Thematic Constraint** | Extracted thematic boundaries: theme, moral_stance, recurring_questions[], forbidden_elements[]. Enforced as soft constraints during drafting to maintain thematic consistency with the source material. Available for narrative source type only. |
| **Canon Workshop** | Dedicated workspace at `/workspace/:projectId/canon` for editing extracted canon material, marking fields as locked/mutable/forbidden, managing mythos and pattern entries, creating reusable generation profiles, and previewing canon packets before submission. |
| **Canon Annotation** | Field-level classification that controls generation behavior: `locked` (must not contradict), `soft_guidance` (respect but allow minor deviation), `mutable` (explicitly allowed to change), `forbidden_contradiction` (this text must not appear). Persists in `canon_annotations` table. |
| **Canon Customization Profile** | Saved reusable generation configuration: name, description, default mode, canon scope, canon policy, generation brief template, and selected annotation IDs. Lets you re-generate with the same settings without reconfiguring. |
| **Mythos Entry** | Editable record of extracted mythological material: archetype, motif, cosmic_rule, symbol, ritual, deity, cycle, or theme. Contains canonical facts, pattern notes, generation guidance, and source corpus reference. Managed via Mythos Library at `/workspace/:projectId/canon?tab=mythos`. |
| **Pattern Entry** | Editable record of extracted narrative pattern: plot, character, relationship, world, theme, scene, or structure type. Contains beats, constraints, transposition notes, and applicable generation modes. Managed via Pattern Library at `/workspace/:projectId/canon?tab=patterns`. |
| **Manuscript LLM Assist** | Interactive editing feature that lets you select text in the manuscript editor and request AI assistance: line edits, expansions, compressions, rewrites, continuations, canon checks, voice checks, forks. Suggestions include canon risk ratings and confidence scores. |
| **TextRange** | Selection metadata captured by the editor: start_offset, end_offset, selected_text, and 1000-character anchors before/after. Used for deterministic patching even if document offsets drift after editing. |
| **Assist Kind** | Type of LLM assistance requested: developmental_review, canon_check, character_voice_check, pacing_review, theme_review, line_edit_selection, expand_selection, compress_selection, rewrite_selection_same_voice, alternate_selection, continue_from_selection, fork_from_selection, generate_next_chapter, generate_alternate_chapter, continuity_repair. |
| **LLM Revision Suggestion** | AI-generated edit proposal: source_text, proposed_text, rationale, canon_risk (none/low/medium/high/blocking), confidence_score, and source_context references to canon entries. Statuses: REQUESTED → PENDING → ACCEPTED/REJECTED/ARCHIVED. |
| **M-500 Assist Phase** | Executor phase for manuscript assist requests. Loads document, builds assist packet with canon context, calls LLM, parses JSON suggestions, runs gate checks, persists suggestions and gate results. |
| **M-550 Repair Phase** | Optional executor phase triggered when M-500 gates fail and policy allows repair. Sends a repair prompt to fix canon violations in generated suggestions. |
| **Version Conflict Protection** | Manuscript assist applies suggestions against an expected document version. If the document was edited between requesting and applying, the apply fails with HTTP 409, preventing silent overwrites. |
| **Project Export** | Creates a complete ZIP archive snapshot of a project including its directory structure (manifest.json, bible.db, chapters/, etc.) and all operations DB records scoped to the project_id. Downloaded synchronously via streaming response. Accessible from the Project List page. |
| **Project Import** | Restores a previously exported project ZIP as a brand-new project with a fresh UUID. Never overwrites or merges with existing projects. Runs asynchronously (202 Accepted + polling). Includes schema version migration for forward compatibility. Accessed via the "Import Project" button on the home page. |
| **Export ZIP** | The ZIP archive format used by project export. Contains metadata.json (with export_version, project_id, project_name, timestamp), the full project directory tree, and all operations DB tables. Minimum size 1 MB, maximum size 500 MB for imports. |
| **Export Version** | Schema versioning field in metadata.json that tracks which Narrative Engine schema version was current at export time. Used during import to apply forward migration passes when importing older exports into newer installations. |
