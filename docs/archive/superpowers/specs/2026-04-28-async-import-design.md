# Async Story Import — Design Spec v1.0

> **Date:** 2026-04-28
> **Status:** Design approved, awaiting implementation plan
> **Branch:** `codex/async-import`

## Problem

The current `POST /projects/import-story` endpoint blocks the HTTP request for the entire duration of LLM analysis and database persistence. For large multi-pass imports (stories ≥30k chars), this can take minutes and:
1. Hits server timeout limits (HTTP connection drops)
2. Provides no progress feedback to the user — they see a spinner with no indication of phase or chapter count
3. Phase 1 structure detection has no fallback on LLM failure — crashes entire pipeline
4. No retry logic for transient LLM errors
5. Text-only input limits usability for large novels

## Goals

- Convert import to async pattern: submit → poll for progress/result
- Fix Phase 1 crash risk with fallback and retry
- Add file upload (.txt/.md) alongside text paste
- Show phase + chapter count progress in frontend
- Maintain backward compatibility — existing JSON POST still works

## Non-Goals

- WebSocket or Server-Sent Events (polling is sufficient)
- Database persistence of import jobs (in-memory with TTL cleanup)
- Cancel server-side job (cancel only stops client polling)
- Integration with existing job executor system (kept separate)

## Architecture

### Async Flow

```
Client                              Server
  |                                   |
  | POST /projects/import-story       |
  | (JSON or multipart)               |
  |---------------------------------->|
  | 202 {import_id, status: "pending"}|
  |                                   |→ Submit to thread pool
  |                                   |→ Run import in background
  | GET /projects/import/{id}         |
  |---------------------------------->|
  | 200 {status, phase, progress...}  |
  |                                   |
  | ... poll every 2s ...             |
  |                                   |
  | GET /projects/import/{id}         |
  |---------------------------------->|
  | 200 {status: "completed", result} |
```

### Components

#### ImportJobManager (new)

Manages the lifecycle of async imports.

```python
@dataclass
class ImportJob:
    import_id: str
    status: str              # pending | running | completed | failed
    phase: str               # structure_detection | chapter_analysis | consolidation
    chapters_processed: int
    total_estimated_chapters: int
    result: StoryImportResponse | None
    error: str | None
    created_at: float

class ImportJobManager:
    _jobs: dict[str, ImportJob]       # in-memory store
    _lock: threading.Lock
    _cleanup_interval: int = 300      # TTL for completed jobs (5 min)

    def submit(self, request) -> str   # create job, return import_id
    def get_status(self, import_id) -> ImportJobResponse  # poll endpoint
    def update_progress(self, import_id, **kwargs)        # called by worker thread
    def complete(self, import_id, result)                  # mark done with result
    def fail(self, import_id, error: str)                  # mark failed
    def cleanup_expired(self)                              # remove old completed jobs
```

Thread-safety: All mutations protected by `_lock`. Background worker calls `update_progress`/`complete`/`fail` on the same manager instance. Periodic cleanup removes completed jobs older than TTL.

#### POST /projects/import-story (modified)

Accepts both content types:
- `application/json` — existing behavior, `story_text` in body
- `multipart/form-data` — new: `file` field (.txt/.md), optional `project_name`, `genre_hint`, `tone_hint`

Behavior change: Instead of blocking on `import_service.import_story()`, the endpoint:
1. Validates input (text length, file type)
2. Creates `ImportJob` via manager
3. Submits import work to thread pool: `executor.submit(worker, job_id, request)`
4. Returns `202 Accepted` with `{import_id, status: "pending"}`

#### GET /projects/import/{import_id} (new)

Returns current progress or final result:
```json
{
  "import_id": "abc-123",
  "status": "running",
  "phase": "chapter_analysis",
  "chapters_processed": 5,
  "total_estimated_chapters": 12,
  "result": null,
  "error": null
}
```

When completed:
```json
{
  "import_id": "abc-123",
  "status": "completed",
  "phase": "done",
  "chapters_processed": 12,
  "total_estimated_chapters": 12,
  "result": { /* full StoryImportResponse */ },
  "error": null
}
```

404 if import_id not found or expired.

### Error Handling Improvements

#### Phase 1 Fallback

Current: `_detect_structure()` raises on LLM failure → crashes pipeline.
Fixed: Wrap in try/except, fall back to `_fallback_structure()` on any exception.

```python
def _detect_structure(self, story_text: str) -> StoryStructureDetection:
    try:
        request = build_structure_detection_request(...)
        response = self._inferencer.generate_text(request)
        return self._parse_structure(response.content)
    except (InferenceBackendError, ValueError, ValidationError) as exc:
        logger.warning("Structure detection failed, using fallback: %s", exc)
        return self._fallback_structure(story_text)
```

#### Retry with Backoff

New helper for critical LLM calls (Phase 1, Phase 3):
```python
def _retry_with_backoff(
    self, func: Callable, args: tuple, kwargs: dict, max_retries: int = 2
) -> Any:
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (InferenceBackendError, ValueError, ValidationError) as exc:
            if attempt == max_retries:
                raise
            wait = min(0.5 * (2 ** attempt), 5.0)  # 0.5s, 1s, max 5s
            logger.warning("Retry %d/%d after %.1fs: %s", attempt+1, max_retries, wait, exc)
            time.sleep(wait)
```

Applied to: Phase 1 structure detection, Phase 3a character consolidation, Phase 3b world bible consolidation, Phase 3c arc detection.

### File Upload

`POST /projects/import-story` modified to accept `UploadFile` via FastAPI multipart:
```python
async def import_story(
    story_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    project_name: Optional[str] = Form(None),
    genre_hint: Optional[str] = Form(None),
    tone_hint: Optional[str] = Form(None),
):
```

Validation:
- Either `story_text` (JSON body) or `file` must be provided — not both, not neither
- File extension must be `.txt` or `.md`
- File read as UTF-8 text, max size enforced via existing `MAX_BODY_SIZE`
- Content validated same way as JSON `story_text` field

### Frontend Changes

#### StoryImportModal updates

1. **File drop zone** — alongside textarea, user can drag-drop or click to upload .txt/.md files
2. **Async submit flow** — POST returns 202 with import_id; begin polling
3. **Progress display** — phase text + chapter count: "Analyzing Chapter 5 of 12..."
4. **Cancel button** — stops polling, does not abort server-side job

#### Type updates

`frontend/src/types/storyImport.ts`:
```typescript
export interface StoryImportResponse {
  project_id: string;
  status: string;
  message: string;
  warnings: string[];
  chapters_processed: number;
  total_estimated_chapters: number;
  analysis_mode: string;
}

export interface ImportProgress {
  import_id: string;
  status: "pending" | "running" | "completed" | "failed";
  phase: string;
  chapters_processed: number;
  total_estimated_chapters: number;
  result: StoryImportResponse | null;
  error: string | null;
}
```

#### Service updates

`frontend/src/services/storyImport.ts`:
- `importStory(request)` — POST, returns `{import_id}`
- `getImportStatus(import_id)` — GET progress, returns `ImportProgress`
- File upload via `FormData` with multipart encoding

### Data Flow

1. User pastes text or uploads file → StoryImportModal validates (min 50 chars)
2. Frontend POSTs to `/projects/import-story` (JSON or multipart)
3. Server creates ImportJob, submits to thread pool, returns 202 with import_id
4. Frontend polls `GET /projects/import/{import_id}` every 2 seconds
5. Background worker runs import, calls `manager.update_progress()` at each phase
6. Polling returns updated status: phase, chapters_processed, total_estimated_chapters
7. When complete, poll returns full result; frontend navigates to workspace
8. Completed jobs cleaned up after 5-minute TTL

### Testing Strategy

- **ImportJobManager**: Thread safety (concurrent updates), TTL cleanup, 404 on expired ID
- **Phase 1 fallback**: LLM failure triggers `_fallback_structure()`, not crash
- **Retry logic**: Backoff timing, max retries respected, final exception propagated
- **File upload**: Valid .txt/.md accepted, invalid extension rejected, empty file rejected
- **Async endpoint**: 202 returned immediately, progress updates visible via polling
- **Frontend**: Polling starts after 202, progress display updates, completion triggers navigation

## Files Affected

| File | Change |
|------|--------|
| `app/services/import_jobs.py` | NEW — ImportJobManager, ImportJob dataclass, worker function |
| `app/services/multi_pass_import.py` | Modify — Phase 1 fallback, retry helper, progress callbacks |
| `app/services/story_import.py` | Modify — accept progress callback, wire to job manager |
| `app/api/projects.py` | Modify — async POST, new GET endpoint, file upload handling |
| `app/schemas/story_import.py` | Add — ImportProgressResponse schema |
| `frontend/src/types/storyImport.ts` | Add — ImportProgress type, extend StoryImportResponse |
| `frontend/src/services/storyImport.ts` | Add — getImportStatus, file upload support |
| `frontend/src/components/projects/StoryImportModal.tsx` | Modify — async flow, progress display, file drop zone |
| `tests/test_import_jobs.py` | NEW — ImportJobManager, retry, Phase 1 fallback, file upload |

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Thread pool exhaustion from concurrent large imports | Limit pool size to 4; reject with 503 if queue full |
| In-memory job store loses state on server restart | Acceptable — import is idempotent, user can retry |
| Polling too frequent → server load | Client polls every 2s; server-side lock protects job dict |
| File upload exceeds memory | MAX_BODY_SIZE constant already enforced; reject oversized files early |
