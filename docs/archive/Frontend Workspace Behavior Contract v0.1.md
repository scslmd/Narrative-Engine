# Frontend Workspace Behavior Contract v0.1

Use this note when touching `frontend/` planning workspaces or manuscript aids. The rule is simple: if the UI exposes a story-development feature, it must speak the real backend contract and it must render real state, not a placeholder seam.

## Planning Workspace

- `frontend/src/views/PlanningView.tsx` is the router-owned workspace shell.
- `projectId` from the route stays the source of truth for workspace state.
- If a tab is shown in the planning shell, it should render an actual workspace, not a `console.log` handler or a dead stub.
- Keep loading, empty, and error states explicit. Do not hide unfinished flows behind optimistic UI.

## Contract Alignment

- `frontend/src/types/brainstorm.ts` and `frontend/src/services/brainstorm.ts` must stay aligned with the backend brainstorm schema.
- Use the real brainstorm payload shape: `item_id`, `project_id`, `content`, `status`, `tags`, and `source_notes`.
- Do not invent a parallel model such as `state`, `item_type`, `promoted_to`, or `promoted_at` unless the service layer maps it from real backend data.
- `frontend/src/types/foundation.ts` and `frontend/src/services/foundation.ts` must keep the foundation editor on the real fields: `premise`, `logline`, `thematic_spine`, `emotional_promise`, `tone_and_voice_direction`, `target_audience`, `narrative_constraints`, `complexity_level`, and `success_definition`.
- Foundation changes create revisions and downstream review cues. They do not silently overwrite downstream planning or draft output.
- `frontend/src/types/characters.ts` and `frontend/src/services/characters.ts` must use `CharacterProfile` and `RelationshipEdge` as defined by the backend.
- Do not build a new character schema with ad hoc fields like `name`, `description`, `personality`, or `arc`.
- `frontend/src/types/bible.ts` and `frontend/src/services/worldBible.ts` must use `WorldBibleEntry` and `WorldBibleEntryType`.
- Do not build new world-bible features on the legacy `BibleEntry` shape unless you are explicitly maintaining backward compatibility.

## Manuscript Aids

- `WritingView` at `/workspace/:projectId/write` reads revision suggestions through `getRevisionSuggestions(projectId, targetDocumentId?)`.
- Uses query key `['revision-suggestions', projectId, selectedDocumentId ?? 'all']`.
- Renders `AidsPanel`, `DiffViewer`, and `SuggestionHistory` as read-only review surfaces.
- `onSuggestionAccept` and `onSuggestionReject` are optional props on `AidsPanel` but are NOT provided by `WritingView`; do not document accept/reject as shipped behavior until a backend-backed mutation route exists.
- `frontend/src/components/aids/AidsPanel.tsx` should not pretend comparison works when no comparison pair exists.
- `frontend/src/components/aids/DiffViewer.tsx` must render original and modified content as distinct sides. Rendering the same combined output in both panes is wrong.
- `frontend/src/lib/diff.ts` must stay correct on manuscript-sized text without forcing a full quadratic walk over large inputs.
- If a diff target is missing, the UI should say so directly instead of showing a fake compare surface.

## Implementation Rules

- Use the shared Axios client in `frontend/src/lib/api.ts` for story-development requests.
- Keep snake_case field names at the service boundary.
- Prefer real mutations, query invalidation, and backend-backed refreshes over local-only console state.
- Do not leave user-facing prototype seams in merged flows.
- Run `cd frontend && npm run lint`, `cd frontend && npm run typecheck`, and `cd frontend && npm run build` after changing these areas.

## Quick Sanity Check

Before merging a change in this area, confirm these are true:

1. The planning shell tabs render production behavior, not placeholders.
2. New brainstorming, foundation, character, and world-bible UI uses the backend contract exactly.
3. Manuscript aids either compare real texts or clearly show why comparison is unavailable.
4. Large diff inputs do not trigger avoidable quadratic work.
