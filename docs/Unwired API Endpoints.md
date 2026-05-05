# Unwired API Endpoints & Service Functions

> Generated: 2026-05-05
> Scope: Backend endpoints and frontend service functions with no production UI caller
> Status: All endpoints are functional, tested, and documented in AGENTS.md. Awaiting UI implementation.

---

## Summary

| Category | Count |
|----------|-------|
| Unwired service functions (exist, tested, not called) | 40 |
| Backend endpoints with no frontend caller | ~35 |
| Backend route groups with zero frontend coverage | 2 (`backup`, `auth`) |

---

## 1. Service Functions Without UI Callers

### Relationships (`frontend/src/services/relationships.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `updateRelationship(edgeId, data)` | `PATCH /v1/story-development/relationships/{edge_id}` | Service exists, no component caller |

**Notes:** `deleteRelationship` is wired in `PlanningView.tsx`. Create endpoint (`POST`) has no frontend service function.

### Arcs (`frontend/src/services/arcs.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `updateArcSelection(selectionId, data)` | `PATCH /v1/story-development/arcs/selections/{selection_id}` | Service exists, no component caller |
| `createArcComparison(request)` | `POST /v1/story-development/arcs/comparisons` | No service function; backend endpoint exists |

**Notes:** `getArcComparisons` (GET) is wired. Selection CRUD is partial — only GET and DELETE are called.

### Brainstorm (`frontend/src/services/brainstorm.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `promoteBrainstormItem(itemId, data)` | `POST /v1/story-development/brainstorm/items/promote` | Service exists, no component caller |

**Notes:** List and create are wired. Promote and promotions list are unwired.

### Foundation (`frontend/src/services/foundation.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `getFoundationRevisions(projectId)` | `GET /v1/story-development/foundation/revisions?project_id={id}` | Service exists, no component caller |
| `getReviewCues(projectId)` | `GET /v1/story-development/foundation/review-cues?project_id={id}` | Service exists, no component caller |

**Notes:** Active profile GET/PATCH are wired. Revision history and review cues are unwired.

### Mythos Library (`frontend/src/services/mythosLibrary.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `createMythosEntry(data)` | `POST /v1/mythos/entries` | Service exists, no component caller |
| `updateMythosEntry(mythosId, data)` | `PATCH /v1/mythos/entries/{mythos_id}` | Service exists, no component caller |
| `deleteMythosEntry(mythosId)` | `DELETE /v1/mythos/entries/{mythos_id}` | Service exists, no component caller |
| `materializeExtraction(data)` | `POST /v1/mythos/materialize-extraction` | Service exists, no component caller |

**Notes:** Only `getMythosEntries` (list) is wired. Full CRUD + materialization unwired.

### Pattern Library (`frontend/src/services/patternLibrary.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `createPatternEntry(data)` | `POST /v1/patterns/entries` | Service exists, no component caller |
| `updatePatternEntry(patternId, data)` | `PATCH /v1/patterns/entries/{pattern_id}` | Service exists, no component caller |
| `deletePatternEntry(patternId)` | `DELETE /v1/patterns/entries/{pattern_id}` | Service exists, no component caller |
| `materializeExtraction(data)` | `POST /v1/patterns/materialize-extraction` | Service exists, no component caller |

**Notes:** Only `getPatternEntries` (list) is wired. Full CRUD + materialization unwired.

### Manuscript Assist (`frontend/src/services/manuscriptAssist.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `applySuggestion(suggestionId)` | `POST /v1/manuscript-assist/suggestions/{suggestion_id}/apply` | Service exists, no component caller |
| `archiveSuggestion(suggestionId)` | `POST /v1/manuscript-assist/suggestions/{suggestion_id}/archive` | Service exists, no component caller |

**Notes:** 7/9 exports wired. Apply and archive are unwired (reject is wired).

### Planning (`frontend/src/services/planning.ts`)

| Function | Backend Endpoint | Status |
|----------|-----------------|--------|
| `getSequencePlan(sequenceId)` | `GET /v1/story-development/planning/sequence-plans/{sequence_id}` | No single-item GET service function |
| `getChapterPacket(packetId)` | `GET /v1/story-development/planning/chapter-packets/{packet_id}` | No single-item GET service function |

**Notes:** List and bulk operations are wired. Single-entity inspection endpoints unwired.

---

## 2. Backend Endpoints With No Frontend Service Function

### Story Development Relationships (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `POST` | `/v1/story-development/relationships` | No frontend service function |
| `PATCH` | `/v1/story-development/relationships/{edge_id}` | Service exists, no UI caller |

### Story Development Arcs (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `POST` | `/v1/story-development/arcs/comparisons` | No frontend service function |
| `PATCH` | `/v1/story-development/arcs/selections/{selection_id}` | Service exists, no UI caller |

### Story Development Brainstorm (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/v1/story-development/brainstorm/promotions?project_id={id}` | No frontend service function |

### Story Development Foundation (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/v1/story-development/foundation/revisions?project_id={id}` | Service exists, no UI caller |
| `GET` | `/v1/story-development/foundation/review-cues?project_id={id}` | Service exists, no UI caller |

### Story Development Planning (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/v1/story-development/planning/sequence-plans/{sequence_id}?project_id={id}` | No frontend service function |
| `GET` | `/v1/story-development/planning/chapter-packets/{packet_id}?project_id={id}` | No frontend service function |

### Story Development Storyboard (`app/api/story_development.py`)

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/v1/story-development/storyboard/cards/{card_id}?project_id={id}` | No frontend service function |
| `PUT` | `/v1/story-development/storyboard/cards/{card_id}?project_id={id}` | No frontend service function |

### Project Artifacts (`app/api/projects.py`)

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/projects/{project_id}/manifest` | Legacy artifact endpoint, no frontend caller |
| `GET` | `/projects/{project_id}/sequence` | Legacy artifact endpoint, no frontend caller |
| `GET` | `/projects/{project_id}/chapter-1` | Legacy artifact endpoint, no frontend caller |

---

## 3. Route Groups With Zero Frontend Coverage

### Backup (`app/api/backup.py`)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/backup/create` | Create backup of project data |
| `POST` | `/backup/restore/{backup_id}` | Restore from backup |
| `GET` | `/backup/list` | List available backups |
| `GET` | `/backup/latest` | Get latest backup |
| `DELETE` | `/backup/{backup_id}` | Delete backup |

**Frontend status:** No service file. No UI. Feature is fully implemented backend-side (REL-04).

### Authentication (`app/api/auth.py`)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/keys` | Create API key |
| `GET` | `/auth/keys` | List API keys |
| `DELETE` | `/auth/keys/{prefix}` | Revoke API key |

**Frontend status:** No service file. No UI. Feature is fully implemented backend-side (SEC-02).

---

## 4. Health & Metrics (`app/api/health.py`)

| Method | Path | Purpose | Frontend Caller |
|--------|------|---------|----------------|
| `GET` | `/health/metrics` | Latency telemetry | None (monitoring endpoint) |

**Notes:** Intentionally unwired. Used for operational monitoring, not user-facing.

---

## 5. Priority Recommendations

### High Priority (core workflow gaps)

1. **Manuscript Assist: `applySuggestion`, `archiveSuggestion`** — Critical for complete assist workflow. User can generate suggestions but cannot apply or archive them from UI.
2. **Relationships: `updateRelationship`** — Partial CRUD breaks relationship editing flow.
3. **Arc selections: `updateArcSelection`** — Partial CRUD breaks arc management flow.

### Medium Priority (feature completeness)

4. **Mythos Library: full CRUD** — List-only UI is incomplete for a library feature.
5. **Pattern Library: full CRUD** — List-only UI is incomplete for a library feature.
6. **Foundation: revisions, review cues** — Missing history and review features.
7. **Brainstorm: promote, promotions** — Missing promotion workflow.

### Low Priority (admin/operational)

8. **Backup endpoints** — Admin feature, no UI needed for core users.
9. **Auth key management** — Admin feature, managed via CLI/env vars.
10. **Legacy artifact endpoints** — Superseded by newer API patterns.

---

## 6. Implementation Checklist

When building UI for these gaps, verify:

- [ ] Service function exists and is exported (or create new service file)
- [ ] Backend endpoint accepts correct request format (snake_case params)
- [ ] Component/hook calls service function with correct props
- [ ] React Query invalidation configured for mutations
- [ ] Error handling covers 400/401/403/404/409/429/5xx
- [ ] Loading, empty, and error states are explicit
- [ ] Tests cover the new call path

---

## Appendix: Service File Index

| Service File | Exports | Wired | Unwired | Coverage |
|-------------|---------|-------|---------|----------|
| `relationships.ts` | 3 | 2 | 1 | 67% |
| `arcs.ts` | 8 | 5 | 3 | 63% |
| `brainstorm.ts` | 5 | 3 | 2 | 60% |
| `foundation.ts` | 5 | 3 | 2 | 60% |
| `mythosLibrary.ts` | 5 | 1 | 4 | 20% |
| `patternLibrary.ts` | 5 | 1 | 4 | 20% |
| `manuscriptAssist.ts` | 9 | 7 | 2 | 78% |
| `planning.ts` | 14 | 12 | 2 | 86% |
| **Total** | **~135** | **~95** | **~40** | **70%** |
