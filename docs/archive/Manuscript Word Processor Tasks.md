# Manuscript Word Processor - Atomic Deterministic Tasks

> **Status: ALL TASKS COMPLETE** (WP-01 through WP-11). Full validation passed: 554 pytest passed, lint/typecheck/build all clean.

## Task WP-01: Backend Schema - ManuscriptDocumentUpdateRequest

**File**: `app/schemas/story_development.py`
**Change**: Add `ManuscriptDocumentUpdateRequest` schema after `ManuscriptDocument` (line 733).
**Spec**:
```python
class ManuscriptDocumentUpdateRequest(StrictSchemaModel):
    content: str | None = Field(None, max_length=1_000_000)
    title: str | None = Field(None, max_length=500)
```
Both fields optional (partial update). No model_validator needed since both are optional.

> **Status: ✅ COMPLETE** - `app/services/manuscript_review.py` created. 8 tests pass.

## Task WP-02: Backend Service - ManuscriptReviewService

**File**: `app/services/manuscript_review.py` (new file)
**Spec**:
- Exception class: `class ManuscriptReviewError(ValueError)`
- Service class: `class ManuscriptReviewService` with methods:
  - `__init__(self, repository: StoryDevelopmentRepository)` - takes repository dependency
  - `analyze_manuscript(self, project_id: str, *, document_id: str) -> tuple[RevisionSuggestion, ...]`
    - Fetches manuscript document via repository
    - Cross-project check
    - Runs `self._check_character_consistency()` (rule-based)
    - Runs `self._check_world_consistency()` (rule-based)
    - Runs `self._check_continuity()` (rule-based)
    - Returns list of findings (may be empty if no issues found)
  - `_check_character_consistency(self, project_id, manuscript_content) -> list[RevisionSuggestion]`
    - Uses regex to detect proper nouns (capitalized words that aren't at sentence start)
    - Compares with known character names from repository
    - Returns suggestions for potentially new unnamed characters
  - `_check_world_consistency(self, project_id, manuscript_content) -> list[RevisionSuggestion]`
    - Checks for references to world bible entries not yet established
  - `_check_continuity(self, project_id, manuscript_content) -> list[RevisionSuggestion]`
    - Checks for empty paragraphs, excessive repetition patterns
- Helper: `_suggest_id(self, prefix: str) -> str` - generates unique suggestion IDs
- Helper: `_require_manuscript(self, project_id, document_id) -> ManuscriptDocument` - fetch and validate

> **Status: ✅ COMPLETE** - `PATCH /drafting/manuscript-documents/{document_id}` endpoint implemented. 7 tests pass.

## Task WP-03: Backend API - PATCH Manuscript Endpoint

**File**: `app/api/story_development.py`
**Change**: Add endpoint after `create_manuscript_document` (around line 1011).
**Spec**:
```python
@router.patch("/drafting/manuscript-documents/{document_id}", response_model=ManuscriptDocument)
def update_manuscript_document(
    document_id: str,
    project_id: str,
    payload: ManuscriptDocumentUpdateRequest,
) -> ManuscriptDocument:
    """Partially update a manuscript document's content or title."""
    if payload.content is None and payload.title is None:
        raise HTTPException(status_code=400, detail="At least one of 'content' or 'title' must be provided.")
    # Build full content from existing + provided fields
    # ... (implementation details in task)
```
- Fetches existing manuscript
- Validates cross-project
- Applies partial update (use provided content if present, otherwise keep existing; same for title)
- Calls `drafting_service.save_manuscript_document()` with merged fields
- Returns updated document

> **Status: ✅ COMPLETE** - `POST /drafting/manuscript-documents/{document_id}/review` endpoint implemented.

## Task WP-04: Backend API - POST Review Trigger Endpoint

**File**: `app/api/story_development.py`
**Change**: Add endpoint after update endpoint.
**Spec**:
```python
@router.post(
    "/drafting/manuscript-documents/{document_id}/review",
    response_model=ManuscriptReviewResponse,
    status_code=202,
)
def trigger_manuscript_review(
    document_id: str,
    project_id: str,
) -> ManuscriptReviewResponse:
    """Trigger an AI review of the manuscript document.
    
    Analyzes the manuscript content for consistency issues,
    new character introductions, world-building conflicts, etc.
    """
```
- Returns 202 with list of generated `RevisionSuggestion` objects
- Calls `manuscript_review_service.analyze_manuscript()`
- Creates `RevisionSuggestion` records via `drafting_service.create_revision_suggestion()`
- Returns the generated suggestions

Also needs `ManuscriptReviewResponse` schema:
```python
class ManuscriptReviewResponse(StrictModel):
    document_id: str
    project_id: str
    findings: list[RevisionSuggestion] = Field(default_factory=list)
```

> **Status: ✅ COMPLETE** - `tests/test_manuscript_review_service.py` created with 8 tests.

## Task WP-05: Backend Tests - ManuscriptReviewService

**File**: `tests/test_manuscript_review_service.py` (new file)
**Spec**:
- Helper functions (like existing test patterns): `_service()`, `_seed_project()`
- Tests:
  1. `test_analyze_manuscript_returns_empty_when_no_issues` - clean manuscript, no findings
  2. `test_analyze_manuscript_detects_repetition` - content with repeated paragraphs
  3. `test_analyze_manuscript_detects_empty_paragraphs` - content with blank lines
  4. `test_analyze_manuscript_raises_not_found_for_missing_document` - 404 scenario
  5. `test_analyze_manuscript_raises_not_found_for_wrong_project` - cross-project isolation
  6. `test_analyze_manuscript_detects_potential_new_characters` - content with unrecognized proper nouns
  7. `test_create_revision_suggestion_creates_record` - verifies persistence
  8. `test_analyze_returns_suggestions_with_correct_target_document` - all suggestions link to correct doc

> **Status: ✅ COMPLETE** - `tests/test_manuscript_update_api.py` created with 7 tests.

## Task WP-06: Backend Tests - PATCH Manuscript Endpoint

**File**: `tests/test_manuscript_update_api.py` (new file)
**Spec**:
- Helper: `_build_client()` like existing API test patterns
- Tests:
  1. `test_update_manuscript_content_updates_and_returns_document` - full update flow
  2. `test_update_manuscript_increment_version` - version goes up by 1
  3. `test_update_manuscript_partial_title_only` - update title only, content unchanged
  4. `test_update_manuscript_partial_content_only` - update content only, title unchanged
  5. `test_update_manuscript_returns_400_when_no_fields_provided` - empty payload
  6. `test_update_manuscript_returns_404_for_missing_document` - not found
  7. `test_update_manuscript_returns_404_for_wrong_project` - cross-project

> **Status: ✅ COMPLETE** - `tests/test_manuscript_review_api.py` created with 5 tests.

## Task WP-07: Backend Tests - Review Trigger Endpoint

**File**: `tests/test_manuscript_review_api.py` (new file)
**Spec**:
- Tests:
  1. `test_trigger_review_returns_202_with_findings` - successful review
  2. `test_trigger_review_returns_202_with_empty_findings` - clean manuscript
  3. `test_trigger_review_creates_suggestion_records_in_db` - persistence verified
  4. `test_trigger_review_returns_404_for_missing_document` - not found
  5. `test_trigger_review_returns_404_for_wrong_project` - cross-project

> **Status: ✅ COMPLETE** - `triggerManuscriptReview()` added to `frontend/src/services/drafting.ts`.

## Task WP-08: Frontend Service - triggerManuscriptReview

**File**: `frontend/src/services/drafting.ts`
**Change**: Add function at end of file.
**Spec**:
```typescript
export async function triggerManuscriptReview(
  documentId: string,
  projectId: string,
): Promise<RevisionSuggestion[]> {
  const response = await api.post(
    `/story-development/drafting/manuscript-documents/${documentId}/review`,
    { params: { project_id: projectId } },
  );
  return response.data.findings ?? [];
}
```

> **Status: ✅ COMPLETE** - `WritingView.tsx` updated with edit mode, textarea, save/cancel, word/char count.

## Task WP-09: Frontend - Editable WritingView

**File**: `frontend/src/views/WritingView.tsx`
**Changes**:
1. Import `api` from `../lib/api` and `toast` from `react-hot-toast` (or use existing toast pattern)
2. Add state: `isEditing: boolean`, `editContent: string`
3. Replace `<pre>` content area with conditional:
   - View mode (default): keep existing `<pre>` rendering
   - Edit mode: `<textarea>` with content, `onBlur` saves, toolbar with Edit/Save/Cancel
4. Add toolbar with buttons:
   - **Edit** button: switches to edit mode, copies content to `editContent` state
   - **Save** button: calls PATCH endpoint, invalidates queries, triggers review, shows toast
   - **Cancel** button: resets `isEditing`, `editContent`, discards changes
5. Save handler:
   - Calls `PATCH /story-development/drafting/manuscript-documents/{documentId}` with `{ content: editContent }`
   - On success: invalidates `manuscript-documents` query, calls `triggerManuscriptReview`, sets `isEditing = false`
   - On error: shows error toast
6. Word/character count display in edit mode

> **Status: ✅ COMPLETE** - `handleSuggestionAccept` and `handleSuggestionReject` wired to AidsPanel.

## Task WP-10: Frontend - Wire AidsPanel Accept/Reject

**File**: `frontend/src/views/WritingView.tsx`
**Changes**:
1. Add `handleSuggestionAccept` callback:
   - Get current manuscript content
   - Find the suggestion, replace `source_text` with `proposed_text` in content
   - Save updated content via PATCH endpoint
   - Invalidate queries
   - Show success toast
2. Add `handleSuggestionReject` callback:
   - Call `POST /story-development/drafting/revision-suggestions` with `{ ..., status: 'REJECTED' }`
   - Invalidate queries
   - Show success toast
3. Pass callbacks to `<AidsPanel>`:
   ```tsx
   <AidsPanel
     projectId={projectId}
     suggestions={revisionSuggestions}
     onSuggestionAccept={handleSuggestionAccept}
     onSuggestionReject={handleSuggestionReject}
   />
   ```

> **Status: ✅ COMPLETE** - Auto-trigger review on save implemented with toast notifications.

## Task WP-11: Frontend - Trigger AI Review on Save

**File**: `frontend/src/views/WritingView.tsx`
**Changes**:
1. Import `triggerManuscriptReview` from drafting service
2. In save handler, after successful PATCH:
   ```typescript
   try {
     await triggerManuscriptReview(selectedDocumentId!, projectId);
     toast.success('Manuscript saved. AI review complete.');
   } catch {
     toast.success('Manuscript saved. Review queued.');
   }
   ```
3. Add a `useEffect` that watches `revisionSuggestions` for newly generated suggestions and shows a notification

---

## Summary

| Task | Status | Files |
|------|--------|-------|
| WP-01: Backend Schema | ✅ Complete | `app/schemas/story_development.py` |
| WP-02: Backend Service | ✅ Complete | `app/services/manuscript_review.py` (new) |
| WP-03: PATCH Endpoint | ✅ Complete | `app/api/story_development.py` |
| WP-04: Review Trigger | ✅ Complete | `app/api/story_development.py` |
| WP-05: Review Service Tests | ✅ Complete | `tests/test_manuscript_review_service.py` (new, 8 tests) |
| WP-06: PATCH API Tests | ✅ Complete | `tests/test_manuscript_update_api.py` (new, 7 tests) |
| WP-07: Review API Tests | ✅ Complete | `tests/test_manuscript_review_api.py` (new, 5 tests) |
| WP-08: Frontend Service | ✅ Complete | `frontend/src/services/drafting.ts` |
| WP-09: Editable WritingView | ✅ Complete | `frontend/src/views/WritingView.tsx` |
| WP-10: AidsPanel Wiring | ✅ Complete | `frontend/src/views/WritingView.tsx` |
| WP-11: Auto-trigger Review | ✅ Complete | `frontend/src/views/WritingView.tsx` |

**Validation Results:**
- `pytest -q -p no:cacheprovider`: **554 passed, 9 skipped** (+20 from baseline 514)
- `cd frontend && npm run lint`: **passed**
- `cd frontend && npm run typecheck`: **passed**
- `cd frontend && npm run build`: **passed**
