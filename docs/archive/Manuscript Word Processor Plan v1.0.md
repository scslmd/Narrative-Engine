# Manuscript Word Processor & AI Review - Implementation Plan

## Goal

Transform the read-only Writing view into an editable word processor. When the author saves manuscript changes, the backend automatically runs an AI review and surfaces findings (new characters, arc violations, consistency issues) in the AidsPanel.

## Architecture

```
Author writes in textarea → Save (PATCH) → Backend upserts manuscript
                                      → Auto-trigger AI review job
                                      → Review generates RevisionSuggestions
                                      → Frontend polls → AidsPanel shows findings
Author clicks Accept → Replace source_text with proposed_text in content → Save
Author clicks Reject → Mark suggestion status as REJECTED
```

## Scope

### Backend
1. `ManuscriptDocumentUpdateRequest` schema (partial update, optional fields)
2. `ManuscriptReviewService` - analyze manuscript content, generate findings
3. `PATCH /drafting/manuscript-documents/{document_id}` - partial update
4. `POST /drafting/manuscript-documents/{document_id}/review` - trigger AI review

### Frontend
1. `WritingView` - edit mode (textarea), save flow, AI review trigger
2. `WritingView` - AidsPanel accept/reject callbacks
3. `drafting.ts` - `triggerManuscriptReview()` service function

## Design Decisions

1. **Plain textarea** (not rich text) - distraction-free prose writing
2. **Async review** - triggers a job, doesn't block save response
3. **Rule-based + LLM hybrid** - fast deterministic checks first, then LLM inference
4. **Use existing POST upsert** for save (version auto-increment). PATCH for partial updates.
5. **Accept suggestion** = inline edit (replace text + save), not just a status change

## Tasks

See `MANUSCRIPT_WORD_PROCESSOR_TASKS.md` for atomic task list.

## Validation

- `python -m pytest -q -p no:cacheprovider` → **554 passed, 9 skipped** (+20 new tests from baseline 514)
- `cd frontend && npm run lint` → **passed**
- `cd frontend && npm run typecheck` → **passed**
- `cd frontend && npm run build` → **passed**

## Implementation Status

> **ALL TASKS COMPLETE** (WP-01 through WP-11). See `Manuscript Word Processor Tasks.md` for per-task status.
