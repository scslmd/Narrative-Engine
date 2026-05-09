# 4-Phase Story Generation Pipeline

The Narrative Engine generates stories through four sequential phases (P-100 to P-400). Each phase reads upstream artifacts, calls the LLM, writes output files, and registers the result in both the lineage database and file registry.

## Phase Overview

| Phase | Name | Output File | Artifact Role | File Registry Name |
|-------|------|-------------|---------------|-------------------|
| P-100 | Architect | `exports/p100_architect_output.md` | `architect_output` | `architect_p100` |
| P-200 | Sequencer | `sequences.json` | `sequence` | `sequence` |
| P-300 | Drafter | `chapters/{id}.md` or `chapter.md` | `chapter_{id}` | `chapter_{id}` |
| P-400 | Compiler | `story_bible.json` | `story_bible` | `story_bible` |

## Artifact Data Flow

```
+------------+    architect_output.md     +-----------+    sequences.json     +----------+    chapter_{N}.md    +----------+
| P-100      | ──────────────────────────► | P-200     | ─────────────────────► | P-300    | ──────────────────────► | P-400    |
| Architect  |                             | Sequencer |                        | Drafter  |                          | Compiler |
+------------+                             +-----------+                        +----------+                          +----------+
     manifest                                   architect_output                     sequence                            story_bible.json
                                                + sequence
                                               + architect_output
```

Each phase must complete before the next starts. No parallel execution — data dependencies enforce strict sequential ordering.

## Naming Conventions

The pipeline uses two parallel naming systems. Both must be consistent or artifact resolution fails.

| Concept | Where Used | Example Values |
|---------|-----------|----------------|
| **Artifact role** | Lineage DB (`artifact_role` column), step record `input_artifact_refs` / `output_artifact_refs` | `architect_output`, `sequence`, `chapter_1`, `story_bible` |
| **Project artifact name** | File registry (`project_artifacts.name`), `_read_optional_artifact()` lookups | `architect_p100`, `sequence`, `chapter_1`, `story_bible` |

P-100 is the only phase where artifact role and file registry name differ (`architect_output` vs `architect_p100`). All other phases use the same name for both.

## Phase Details

### P-100: Architect

- **Executor method**: `_run_architect_phase` (`local_executor.py:624`)
- **Prompt builder**: `build_p100_architect_request` (`runtime_prompts.py:18`)
- **Output path helper**: `architect_output_path(project_dir)` → `exports/p100_architect_output.md`
- **Inputs**: Project manifest only
- **Output format**: Markdown with headings (Logline, Core Premise, Story Engine, World Anchors, Character Arcs, Constraints, Open Questions)
- **Artifact kind**: `markdown`
- **Step record refs**: `input_artifact_refs=["manifest"]`, `output_artifact_refs=["architect_output"]`
- **Registration**:
  - `create_lineage_record(artifact_role="architect_output", ...)`
  - `register_generated_artifact(project_id, "architect_p100", output_path)`

### P-200: Sequencer

- **Executor method**: `_run_sequencer_phase` (`local_executor.py:749`)
- **Prompt builder**: `build_p200_sequencer_request` (`runtime_prompts.py:71`)
- **Output path helper**: `sequence_output_path(project_dir)` → `sequences.json`
- **Inputs**: Project manifest + `architect_output`
- **Upstream sources**: `[("architect_output", "architect_p100")]`
- **Output format**: JSON (ordered sequence plan with dependencies)
- **Artifact kind**: `json`
- **Step record refs**: `input_artifact_refs=["manifest", "architect_output"]`, `output_artifact_refs=["sequence"]`
- **Registration**:
  - `create_lineage_record(artifact_role="sequence", ...)`
  - `register_generated_artifact(project_id, "sequence", output_path)`

### P-300: Drafter

- **Executor method**: `_run_drafter_phase` (`local_executor.py:890`)
- **Prompt builder**: `build_p300_drafter_request` (`runtime_prompts.py:113`)
- **Output path helper**: `chapter_output_path(project_dir, chapter_id)` → `chapters/{id}.md` or `chapter.md`
- **Inputs**: Project manifest + `sequence` + `architect_output`
- **Upstream sources**: `[("sequence", "sequence"), ("architect_output", "architect_p100")]`
- **Output format**: Markdown (chapter prose)
- **Artifact kind**: `markdown`
- **Step record refs**: `input_artifact_refs=["manifest", "sequence", "architect_output"]`, `output_artifact_refs=["chapter_{id}"]`
- **Registration**:
  - `create_lineage_record(artifact_role="chapter_{id}", ...)`
  - `register_generated_artifact(project_id, "chapter_{id}", output_path)`
  - `DraftingService.register_draft_artifact()` — creates `DraftArtifact` entry (visible in frontend Drafts panel)
  - `DraftingService.save_manuscript_document()` — creates `ManuscriptDocument` with content

**Post-Draft Processing** (each chapter):
1. Consistency critic check + rewrite loop
2. Entity intake (auto-persist new characters to project DB)
3. DraftArtifact creation (linked to ManuscriptDocument via `current_draft_artifact_id`)
4. Chapter summarization (for multi-chapter prior context propagation)

#### Multi-Chapter Mode

Triggered when job payload contains `chapter_ids` list. Executor method: `_run_multi_chapter_draft` (`local_executor.py:1197`).

- Iterates chapters sequentially, propagating `prior_chapters` summaries (capped at last 3)
- Each chapter gets full finalize cycle: critic check, entity intake, DraftArtifact + ManuscriptDocument creation
- Summarizes each chapter via `ChapterSummarizerService.summarize()` for next-chapter context
- Reports partial success: `"Completed N/M chapters"`

**Active Character Filtering**: When `chapter_id` is provided, P-300 queries `ChapterPlan.active_character_ids` and passes only active characters to `SceneContextService`. Falls back to all characters if no chapter plan exists.

### P-400: Compiler

- **Executor method**: `_run_compiler_phase` (`local_executor.py:1559`)
- **Prompt builder**: `build_p400_compiler_request` (`runtime_prompts.py:182`)
- **Output path helper**: `story_bible_output_path(project_dir)` → `story_bible.json`
- **Inputs**: Project manifest + `architect_output` + `sequence` + `chapter_1`
- **Upstream sources**: `[("architect_output", "architect_p100"), ("sequence", "sequence"), ("chapter_1", "chapter_1")]`
- **Output format**: JSON (keys: project, premise, world_anchors, character_threads, continuity_notes, open_questions)
- **Artifact kind**: `json`
- **Step record refs**: `input_artifact_refs=["manifest", "architect_output", "sequence", "chapter_1"]`, `output_artifact_refs=["story_bible"]`
- **Registration**:
  - `create_lineage_record(artifact_role="story_bible", ...)`
  - `register_generated_artifact(project_id, "story_bible", output_path)`

## Artifact Resolution

When a phase needs an upstream artifact, `_resolve_runtime_artifact_inputs` (`local_executor.py:1513`) performs:

1. Check for existing `runtime_artifact_selection` records (idempotency cache)
2. Fall back to `_read_optional_artifact(project_id, project_artifact_name)` → `ProjectService.read_artifact()`
3. `read_artifact` prefers lineage-based canonical artifacts, falls back to file-based reads
4. Creates `runtime_artifact_selection` records for each resolved input (with lineage ID linkage)

**Canonical type normalization** (`projects.py:243`): Normalizes variant names to canonical keys:
- `"chapter"`, `"chapter-1"`, `"chapter_1"` → `"chapter_1"`
- `"sequence"`, `"sequences"` → `"sequence"`

## Job State Machine

```
PENDING -> PROCESSING -> COMPLETED | FAILED
```

Worker: `local_executor.py` runs two daemon threads (`_job_loop`, `_checker_loop`). Only P-100 to P-400 phases exist (`app/schemas/enums.py::JobPhase`). No custom phases allowed.

## Frontend Integration

The frontend Drafts panel queries `DraftArtifact` entries via `GET /v1/story-development/drafting/draft-artifacts?project_id={id}`. The drafter phase must create both:
- A `DraftArtifact` (so the UI count is non-zero)
- A `ManuscriptDocument` (for content storage)

These are linked via `current_draft_artifact_id` on the ManuscriptDocument record.

## Key Files

| File | Purpose |
|------|---------|
| `app/schemas/enums.py:30-34` | `JobPhase` enum definition |
| `app/services/local_executor.py` | Phase executor methods, artifact resolution |
| `app/services/runtime_prompts.py` | Prompt builders, output path helpers |
| `app/services/projects.py` | Artifact discovery, canonical type normalization |
| `app/persistence/projects.py` | `_discover_artifacts`, lineage lookup |
| `app/services/drafting.py` | `DraftingService.register_draft_artifact`, `save_manuscript_document` |
| `frontend/src/views/WritingView.tsx` | Drafts panel UI, queries `draftArtifacts.length` |

## Known Issues & Fixes

### Drafter Creates No DraftArtifact (2026-05-09)

**Problem**: P-300 drafter only created `ManuscriptDocument` entries. Frontend Drafts panel showed 0 drafts because it queries `DraftArtifact`.

**Fix**: Added `register_draft_artifact()` call alongside `save_manuscript_document()` in both single-chapter and multi-chapter paths. Drafter now creates a `DraftArtifact` linked to the `ManuscriptDocument` via `current_draft_artifact_id`.

### Filesystem MCP Path Escape (2026-05-09)

**Problem**: `opencode.json` used unescaped backslashes for Windows path: `"C:\Users\SLuh"`.

**Fix**: Escaped to `"C:\\Users\\SLuh"` (proper JSON string escaping).

## Settings

Prompt builders resolve `max_tokens` via `settings.inference_max_tokens(phase)`:
- P-100: 4096
- P-200: 4096
- P-300: 8000
- P-400: 4096

Per-phase env vars override the default. Falls back to `NARRATIVE_MAX_TOKENS_DEFAULT` if no phase-specific value is set.

## References

- Prompt caching research: `docs/superpowers/research/2026-05-05-prompt-caching-llama-cpp.md`
- Inference backend architecture: `app/inference/base.py`, `app/inference/openai_compatible.py`, `app/inference/stub.py`
- Multi-chapter context: `app/services/scene_context.py`, `app/services/chapter_summarizer.py`