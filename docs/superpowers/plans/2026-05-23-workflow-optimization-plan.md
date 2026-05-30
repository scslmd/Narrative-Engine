# Workflow Optimization - Executor-Ready Implementation Plan

Date: 2026-05-23
Owner: Story Development / Studio Desk
Status: Ready for execution

## 1. Scope Lock

This document replaces ambiguous wording in earlier drafts and is the implementation source of truth.

In scope:
- Add three new Studio capabilities: Research, Revision, Polish.
- Reorganize Studio rail by workflow stage.
- Add backend contracts and frontend wiring for the new capabilities.

Out of scope for this plan:
- Broad refactors outside Studio/story-development surfaces.
- Replacing existing review APIs.
- New AI model behavior changes.

## 2. Canonical Decisions (Resolved)

1. API namespace is `/v1/story-development/*` for all new routes.
2. Studio panel key count moves from 16 to 19.
3. `review` remains a supported key/API surface; `revision` is added as a separate panel.
4. New persistence is SQLite via story-development repository mixins, consistent with current architecture.
5. All new create routes return `201`. Update/select operations return `200`. Delete returns `204`.

## 3. Panel Inventory (Target)

Current keys (16):
- suggestions, ideas, drafts, manuscripts, characters, worldBible, relationships, arcs, structure, chapters, canon, generation, review, inspect, notes, jobs

Add keys (3):
- research, revision, polish

Target keys (19):
- suggestions, ideas, drafts, manuscripts, characters, worldBible, relationships, arcs, structure, chapters, canon, generation, review, inspect, notes, jobs, research, revision, polish

## 4. Backend Contracts

## 4.1 Research

File targets:
- `app/schemas/story_development.py`
- `app/services/research.py`
- `app/persistence/story_development/research.py`
- `app/api/story_development/research.py`
- `app/persistence/story_development/__init__.py`
- `app/api/story_development/__init__.py`

Routes:
- `GET /v1/story-development/research/items?project_id={id}&status={status?}&genre_tag={tag?}`
- `GET /v1/story-development/research/items/{item_id}?project_id={id}`
- `POST /v1/story-development/research/items`
- `PATCH /v1/story-development/research/items/{item_id}?project_id={id}`
- `DELETE /v1/story-development/research/items/{item_id}?project_id={id}`

Schema contract:
- `ResearchItem`
  - `item_id: str`
  - `project_id: str`
  - `title: str`
  - `content: str`
  - `source_url: str | None`
  - `source_type: Literal["book", "article", "paper", "site", "note", "other"]`
  - `genre_tags: list[str]`
  - `status: Literal["active", "archived", "cited"]`
  - `citations: list[str]`
  - `created_at: datetime`
  - `updated_at: datetime`
- `ResearchItemCreateRequest`
  - required: `project_id`, `title`, `content`
  - optional: `source_url`, `source_type`, `genre_tags`, `citations`
- `ResearchItemUpdateRequest`
  - optional mutable: `title`, `content`, `source_url`, `source_type`, `genre_tags`, `status`, `citations`

Error behavior:
- `404` if item not found in project
- `409` on conflicting updates
- `422` for invalid enum/field formats

## 4.2 Revision

File targets:
- `app/schemas/story_development.py`
- `app/services/revision.py`
- `app/persistence/story_development/revision.py`
- `app/api/story_development/revision.py`
- `app/persistence/story_development/__init__.py`
- `app/api/story_development/__init__.py`

Routes:
- `GET /v1/story-development/revision/passes?project_id={id}&pass_type={type?}&status={status?}`
- `GET /v1/story-development/revision/passes/{pass_id}?project_id={id}`
- `POST /v1/story-development/revision/passes`
- `PATCH /v1/story-development/revision/passes/{pass_id}?project_id={id}`
- `POST /v1/story-development/revision/passes/{pass_id}/complete?project_id={id}`
- `GET /v1/story-development/revision/checklists/{pass_type}`

Schema contract:
- `RevisionPassType = Literal["structural", "character", "scene", "line_edit", "copy_edit"]`
- `RevisionPassStatus = Literal["pending", "in_progress", "completed", "skipped"]`
- `RevisionPass`
  - `pass_id: str`
  - `project_id: str`
  - `pass_type: RevisionPassType`
  - `status: RevisionPassStatus`
  - `checklist: list[RevisionChecklistItem]`
  - `notes: str | None`
  - `created_at: datetime`
  - `completed_at: datetime | None`
- `RevisionChecklistItem`
  - `item_id: str`
  - `label: str`
  - `done: bool`

Business rules:
- `complete` endpoint sets status to `completed` and `completed_at` to server time.
- Completed pass may still accept notes updates, but checklist mutation is rejected with `409`.

## 4.3 Polish

File targets:
- `app/schemas/story_development.py`
- `app/services/polish.py`
- `app/persistence/story_development/polish.py`
- `app/api/story_development/polish.py`
- `app/persistence/story_development/__init__.py`
- `app/api/story_development/__init__.py`

Routes:
- `POST /v1/story-development/polish/analyze`
- `GET /v1/story-development/polish/reports?project_id={id}&document_id={id?}`
- `POST /v1/story-development/polish/export`
- `GET /v1/story-development/polish/export/{export_id}?project_id={id}`

Schema contract:
- `PolishReport`
  - `report_id: str`
  - `project_id: str`
  - `document_id: str`
  - `readability_score: float`
  - `word_count: int`
  - `sentence_count: int`
  - `avg_sentence_length: float`
  - `passive_voice_count: int`
  - `repetitive_words: list[str]`
  - `style_issues: list[str]`
  - `generated_at: datetime`
- `ExportFormat = Literal["docx", "epub", "pdf", "markdown"]`
- `ExportRequest`
  - `project_id: str`
  - `document_id: str`
  - `format: ExportFormat`
  - `include_frontmatter: bool = False`
  - `include_toc: bool = False`
  - `stylesheet: str | None = None`

Async export behavior:
- `POST /export` returns `202` with `export_id`.
- Status endpoint returns queued/running/completed/failed plus artifact metadata when completed.

## 5. Frontend Contracts

File targets:
- `frontend/src/types/research.ts`
- `frontend/src/types/revision.ts`
- `frontend/src/types/polish.ts`
- `frontend/src/services/research.ts`
- `frontend/src/services/revision.ts`
- `frontend/src/services/polish.ts`
- `frontend/src/hooks/useResearch.ts`
- `frontend/src/hooks/useRevision.ts`
- `frontend/src/hooks/usePolish.ts`
- `frontend/src/components/studio/StudioResearchPanel.tsx`
- `frontend/src/components/studio/StudioRevisionPanel.tsx`
- `frontend/src/components/studio/StudioPolishPanel.tsx`
- `frontend/src/components/studio/StudioProjectRail.tsx`
- `frontend/src/components/studio/StudioPanelContent.tsx`
- `frontend/src/components/studio/StudioContextPanel.tsx`
- `frontend/src/stores/studioStore.ts`

Rules:
- Services must use shared Axios client: `frontend/src/lib/api.ts`.
- Query keys:
  - Research: `['research-items', projectId]`
  - Revision: `['revision-passes', projectId]`
  - Polish: `['polish-reports', projectId]`
- Mutations must invalidate corresponding query keys on success.
- Preserve snake_case at service/type boundaries.

## 6. Rail Reorganization (Deterministic)

Required stage grouping:
- Ideation: ideas, research, notes
- Planning: foundation, characters, worldBible, relationships, arcs, structure, chapters
- Drafting: manuscripts, drafts, generation
- Revision: revision, suggestions, review, inspect
- Polish: polish, canon, jobs

Note: if `foundation` is not currently a `StudioPanelKey`, add it in the same phase where its panel wiring is added. Do not leave dead entries.

## 7. Execution Phases

## Phase 1 - Research
- Implement backend + frontend contracts in sections 4.1 and 5.
- Wire rail/context/content/store for `research`.
- Add API and UI tests for list/create/update/delete + filters.

## Phase 2 - Revision
- Implement backend + frontend contracts in sections 4.2 and 5.
- Wire `revision` panel and integrations with suggestions/review inputs.
- Add tests for pass lifecycle and checklist rules.

## Phase 3 - Rail Reorganization
- Update rail groups and context labels.
- Ensure all keys render valid panel content (no dead-end routes).
- Add navigation tests for any-to-any panel switching.

## Phase 4 - Polish
- Implement backend + frontend contracts in sections 4.3 and 5.
- Wire `polish` panel and export status polling.
- Add tests for analyze/export/status flow.

## 8. Acceptance Criteria (Executor Gate)

Feature gates:
- All target keys open valid panels.
- All new endpoints mounted under `/v1/story-development/*`.
- CRUD/lifecycle behavior matches schema and error contracts.
- No dead CTA buttons or placeholder actions.

Validation gates:
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`
- Parallel backend cluster (timeout >= 300000 ms)
- Serial backend suite (timeout >= 240000 ms)

Merge-readiness gate:
- Do not declare complete until all checks above are green.

## 9. Risks and Mitigations

- Risk: schema drift between backend and frontend.
  - Mitigation: define strict request/response types first, then implement services/hooks.
- Risk: panel key mismatches causing dead navigation.
  - Mitigation: add compile-time union updates + switch-case exhaustiveness.
- Risk: async export status race conditions.
  - Mitigation: stable `export_id`, idempotent polling, explicit failed state.
