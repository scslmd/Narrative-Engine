# Studio Desk Stage 2 Suggestions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the Stage 1 empty Studio suggestions panel with real project-level manuscript suggestions from existing writing and manuscript-assist frontend controllers.

**Architecture:** Extract the suggestion merge and accept/reject/archive behavior currently embedded in `WritingView` into a reusable hook. Studio uses that hook to drive `AidsPanel`; `WritingView` continues to render the same behavior.

**Tech Stack:** React 18, TypeScript, React Query, existing writing domain controllers, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S2-T001 | `frontend/src/hooks/useMergedSuggestions.ts` | New reusable merge/action hook |
| S2-T002 | `frontend/src/views/WritingView.tsx` | Replace local merge/handlers with hook |
| S2-T003 | `frontend/src/components/studio/StudioSuggestionsPanel.tsx` | Create real Studio suggestions panel |
| S2-T004 | `frontend/src/components/studio/StudioContextPanel.tsx` | Use real suggestions panel in Studio |
| S2-T005 | `frontend/src/hooks/useMergedSuggestions.test.tsx` | Verify merge and action routing |

## Guardrails

- Do not change backend endpoints.
- Do not change `AidsPanel` props in this stage.
- Do not change manuscript assist service contracts.
- Do not change `useWritingDocumentController` or `useAssistController`.

## Tasks

### S2-T001: Create Reusable Merge Hook

**Responsible file:** `frontend/src/hooks/useMergedSuggestions.ts`

- [x] Create a hook with this exact public interface:

```ts
import { useCallback, useMemo } from 'react';
import type { RevisionSuggestion } from '../types/aids';
import type { LLMRevisionSuggestion } from '../types/manuscriptAssist';

export interface UseMergedSuggestionsArgs {
  revisionSuggestions: RevisionSuggestion[];
  llmSuggestions: LLMRevisionSuggestion[];
  onRevisionAccept: (suggestionId: string) => Promise<void>;
  onRevisionReject: (suggestionId: string) => Promise<void>;
  onLlmAccept: (suggestionId: string) => Promise<void>;
  onLlmReject: (suggestionId: string) => Promise<void>;
  onLlmArchive: (suggestionId: string) => Promise<void>;
}
```

- [x] The hook must not call API hooks, React Query hooks, or route hooks. It only merges provided arrays and routes actions.
- [x] The hook must export:

```ts
export function useMergedSuggestions(args: UseMergedSuggestionsArgs): {
  suggestions: RevisionSuggestion[];
  openSuggestions: RevisionSuggestion[];
  handleSuggestionAccept: (suggestionId: string) => Promise<void>;
  handleSuggestionReject: (suggestionId: string) => Promise<void>;
  handleSuggestionArchive: (suggestionId: string) => Promise<void>;
}
```

- [x] Convert every `llmSuggestions` item to `RevisionSuggestion` with these exact fields:

```ts
{
  suggestion_id: item.suggestion_id,
  project_id: item.project_id,
  target_document_id: item.target_document_id,
  source_text: item.source_text,
  proposed_text: item.proposed_text,
  rationale: item.rationale,
  source_context: item.source_context,
  status: item.status === 'ARCHIVED' ? 'REJECTED' : item.status,
}
```

- [x] Accept/reject/archive logic:
  - If `suggestionId` exists in `llmSuggestions`, accept calls `onLlmAccept(suggestionId)`.
  - If `suggestionId` exists in `llmSuggestions`, reject calls `onLlmReject(suggestionId)`.
  - If `suggestionId` exists in `llmSuggestions`, archive calls `onLlmArchive(suggestionId)`.
  - If `suggestionId` does not exist in `llmSuggestions`, accept calls `onRevisionAccept(suggestionId)`.
  - If `suggestionId` does not exist in `llmSuggestions`, reject calls `onRevisionReject(suggestionId)`.
  - Archive for non-LLM suggestions is a no-op because no existing archive handler exists.

- [x] Verify:

```powershell
cd frontend; cmd /c npm.cmd run typecheck
```

Expected: exits 0.

### S2-T002: Use Hook In WritingView

**Responsible file:** `frontend/src/views/WritingView.tsx`

- [x] Remove the local `mergedSuggestions` construction.
- [x] Import `useMergedSuggestions`.
- [x] Call the hook after `assist` is created:

```ts
const mergedSuggestions = useMergedSuggestions({
  revisionSuggestions,
  llmSuggestions: assist.llmSuggestions,
  onRevisionAccept: handleSuggestionAccept,
  onRevisionReject: handleSuggestionReject,
  onLlmAccept: assist.applySuggestion,
  onLlmReject: assist.rejectSuggestion,
  onLlmArchive: assist.archiveSuggestion,
});
```

- [x] Pass these exact props to `AidsPanel`:

```tsx
suggestions={mergedSuggestions.suggestions}
onSuggestionAccept={(suggestionId) => void mergedSuggestions.handleSuggestionAccept(suggestionId)}
onSuggestionReject={(suggestionId) => void mergedSuggestions.handleSuggestionReject(suggestionId)}
onSuggestionArchive={(suggestionId) => void mergedSuggestions.handleSuggestionArchive(suggestionId)}
```

- [x] Keep `useManuscriptAssist` in `WritingView` for selection toolbar behavior.
- [x] Do not call `useWritingDocumentController` directly from `WritingView`; continue using `useWritingView`.

### S2-T003: Create Studio Suggestions Panel

**Responsible file:** `frontend/src/components/studio/StudioSuggestionsPanel.tsx`

- [x] Create a component with this exact public contract:

```tsx
interface StudioSuggestionsPanelProps {
  projectId: string;
}

export function StudioSuggestionsPanel({ projectId }: StudioSuggestionsPanelProps) {
  // implementation
}
```

- [x] Inside the component, call `useWritingDocumentController({ projectId, chapterId: undefined })`.
- [x] Determine `selectedDocument` from `writingController.selectedDocument`.
- [x] The Studio suggestions panel is project-level in Stage 2. It may use the selected/default document returned by `useWritingDocumentController`; it is not required to synchronize selected-document state with the center `WritingView` until a later shared-workspace-state stage.
- [x] Call `useManuscriptAssist` with:

```ts
{
  projectId,
  documentId: selectedDocument?.document_id ?? null,
  documentVersion: selectedDocument?.version,
  content: writingController.isEditing ? writingController.editContent : selectedDocument?.content,
}
```

- [x] Call `useMergedSuggestions` with the writing controller handlers and assist handlers.
- [x] Render `AidsPanel` with the merged suggestions and merged handlers.

### S2-T004: Use Real Suggestions In StudioContextPanel

**Responsible file:** `frontend/src/components/studio/StudioContextPanel.tsx`

- [x] Import `StudioSuggestionsPanel`.
- [x] Replace the Stage 1 `AidsPanel suggestions={[]}` branch with:

```tsx
<StudioSuggestionsPanel projectId={projectId} />
```

- [x] Remove now-unused `AidsPanel` import from this file.

### S2-T005: Add Hook Tests

**Responsible file:** `frontend/src/hooks/useMergedSuggestions.test.tsx`

- [x] Test that backend revision suggestions and LLM suggestions are returned as one array.
- [x] Test that LLM `ARCHIVED` maps to `REJECTED`.
- [x] Test that accepting an LLM suggestion calls `onLlmAccept`.
- [x] Test that accepting a non-LLM suggestion calls `onRevisionAccept`.
- [x] Use `renderHook` from Testing Library; do not use MSW because this hook has no network calls.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- useMergedSuggestions
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all exit 0.

## Stage 2 Pass Criteria

Stage 2 is complete only when all of these are true:

- Studio suggestions panel renders real project-level suggestions, not the Stage 1 empty placeholder.
- Existing backend revision suggestions and manuscript-assist suggestions are merged into one `AidsPanel` list.
- LLM `ARCHIVED` suggestions map to `REJECTED`.
- Accept/reject/archive actions call existing handlers without adding new service contracts.
- `WritingView` preserves its current suggestion behavior.
- Studio suggestions are explicitly project-level in this stage; active-document synchronization with center `WritingView` is out of scope and must not be implied by tests.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- useMergedSuggestions
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Do not proceed to Stage 3 until these pass and the final verification commands above exit 0.
