# Multi-Chapter Completion Design

Completes the multi-chapter book generation flow by filling the implementation gaps identified in 2026-04-25 gap analysis.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Summary approach | LLM-based summarizer | Consistent with critic/intake pattern; accurate semantic extraction |
| Summarizer timing | Post-P-300 hook | Immediate availability for next chapter; cached for later use |
| Chapter surfacing | Auto-create ManuscriptDocument | Leverages existing drafting service; natural Writing workspace integration |
| Orchestrator trigger | Extend job creation with `chapter_ids` | Minimal API change; executor handles sequencing inline |
| P-400 scope | Per-chapter compilation | Better quality per chapter; consistent with single-chapter model |
| Execution model | Inline executor extension | Single job, immediate continuity; no extra infrastructure |

## 1. Architecture Overview

### New Service: `ChapterSummarizerService`

LLM-based service that reads completed chapter markdown and extracts structured `PriorChapterSummary`:
- `key_events`: significant plot points from the chapter
- `character_states`: character conditions/goals at chapter end
- `unresolved_threads`: open questions, cliffhangers, pending conflicts

Follows ConsistencyCriticService pattern:
- Constructor takes inference backend reference
- Single public method: `summarize(chapter_text, character_names) -> PriorChapterSummary`
- Graceful error handling: returns empty summary on failure, never blocks pipeline

### Executor Extension

`_run_drafter_phase` detects `chapter_ids` list in payload. When present:
1. Iterate sequentially through chapter IDs
2. For each: draft → summarize → create ManuscriptDocument
3. Accumulate summaries into `prior_chapters` list (last 3 max)
4. Inject accumulated context into next chapter's SceneContext

Single job, single attempt record, per-chapter step records for lineage tracking.

### Service Wiring

New service instantiated in `build_app()` alongside existing services:
```python
summarizer = ChapterSummarizerService(inferencer=backend)
executor = LocalExecutor(
    ...,
    scene_context=context_service,
    consistency_critic=critic_service,
    entity_intake=intake_service,
    chapter_summarizer=summarizer,  # NEW
)
```

## 2. Components

### 2.1 ChapterSummarizerService

**File**: `app/services/chapter_summarizer.py`

**Constructor**:
```python
def __init__(self, *, inferencer: InferenceBackend):
    self._inferencer = inferencer
```

**Public method**:
```python
def summarize(
    self,
    chapter_id: str,
    chapter_text: str,
    character_names: list[str],
) -> PriorChapterSummary | None:
    ...
```

**Behavior**:
- Build inference request via `build_chapter_summarize_request()`
- Call LLM with temperature=0.1, max_tokens=2000
- Parse JSON response into PriorChapterSummary
- Return None on failure (never raise)
- Truncate chapter text to 16000 chars for prompt budget

### 2.2 Prompt Builder: `build_chapter_summarize_request()`

**File**: `app/services/runtime_prompts.py`

System prompt instructs LLM to extract structured JSON with fields matching PriorChapterSummary schema. User prompt includes chapter text + character names for grounding.

### 2.3 Executor Chapter Loop

**File**: `app/services/local_executor.py`

Modified `_run_drafter_phase`:
- Detect `chapter_ids` list in payload
- If present, enter sequential loop:
  - Extract single `chapter_id` from list
  - Run existing draft pipeline for that chapter
  - After success, call summarizer to build PriorChapterSummary
  - Create ManuscriptDocument record via DraftingService
  - Append summary to `prior_chapters` list (cap at 3)
  - Pass `prior_chapters` to next iteration's SceneContext assembly

### 2.4 ManuscriptDocument Auto-Creation

**File**: `app/services/local_executor.py` (executor calls)
**Integration**: `app/services/drafting.py::DraftingService.create_manuscript_document()`

After each chapter draft:
- Read generated markdown from output path
- Create ManuscriptDocument with:
  - `document_id`: `"ms-{chapter_id}"` (deterministic, stable across runs)
  - `chapter_id`: the chapter identifier
  - `title`: extracted from ChapterPlan.title if available, else "Chapter {chapter_id}"
  - `content`: chapter markdown text
  - `status`: "DRAFT"

## 3. Data Flow

```
Job payload with chapter_ids: ["ch-001", "ch-002", "ch-003"]
    |
    v
_run_drafter_phase detects list mode
    |
    v
for each chapter_id in chapter_ids:
    |
    +-> Query ChapterPlan for active_character_ids
    |
    +-> Assemble SceneContext (characters + world + prior_chapters)
    |
    +-> Build P-300 inference request
    |
    +-> Call LLM -> draft markdown
    |
    +-> Consistency critic check (if enabled)
    |
    +-> Entity intake (if enabled)
    |
    +-> Write to chapters/{chapter_id}.md
    |
    +-> NEW: ChapterSummarizerService.summarize()
    |           |
    |           +-> Build summarize request
    |           +-> Call LLM -> structured JSON
    |           +-> Parse into PriorChapterSummary
    |           +-> Append to prior_chapters list (cap 3)
    |
    +-> NEW: DraftingService.create_manuscript_document()
    |           |
    |           +-> Read chapter markdown
    |           +-> Create DB record
    |           +-> Register artifact lineage
    |
    +-> Record step for this chapter
    |
    v
Job completed with all chapters drafted
```

## 4. Error Handling

### Summarizer Failures
- LLM timeout: log warning, proceed without summary
- JSON parse failure: log warning, return None
- Empty chapter text: skip summarization
- Never blocks or fails the pipeline

### ManuscriptDocument Creation Failures
- DB write error: log warning, continue drafting
- Chapter plan not found: use default title
- Artifact lineage conflict: use ON CONFLICT DO UPDATE

### Per-Chapter Failure in Multi-Chapter Mode
- Individual chapter failure: record error, continue to next chapter
- All chapters failed: job marked FAILED
- Some succeeded, some failed: job COMPLETED with per-chapter step records showing status

## 5. Testing Strategy

### Unit Tests
- `test_chapter_summarizer.py`: summarize success/failure/empty input/LLM error
- `test_runtime_prompts.py` extension: verify summarize request structure
- Executor chapter loop: mock summarizer, verify prior_chapters accumulation

### Integration Tests
- Full multi-chapter pipeline: 3 chapters with summaries propagating
- ManuscriptDocument creation: verify DB records after drafting
- Prior chapter context injection: verify last 3 chapters in prompt
- Error tolerance: summarizer failure doesn't block drafting

## 6. File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `app/services/chapter_summarizer.py` | LLM-based chapter summarization service |
| `tests/test_chapter_summarizer.py` | Unit tests for summarizer service |

### Modified Files
| File | Change |
|------|--------|
| `app/services/runtime_prompts.py` | Add `build_chapter_summarize_request()` |
| `app/services/local_executor.py` | Chapter loop, prior_chapters wiring, ManuscriptDocument creation |
| `app/main.py` | Wire ChapterSummarizerService into LocalExecutor |
| `tests/test_local_executor_drafter_runtime.py` | Multi-chapter integration tests |

## 7. API Surface Changes

### Job Creation Payload (Extended)

Single chapter (existing):
```json
{"phase": "P-300", "payload": {"project_id": "proj-1", "chapter_id": "ch-002"}}
```

Multi-chapter (new):
```json
{"phase": "P-300", "payload": {"project_id": "proj-1", "chapter_ids": ["ch-001", "ch-002", "ch-003"]}}
```

When `chapter_ids` is present, executor enters sequential mode. When only `chapter_id` is present, existing single-chapter behavior applies. Backward compatible: no `chapter_id` or `chapter_ids` → flat `chapter.md`.
