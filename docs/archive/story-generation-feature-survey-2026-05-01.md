# Story Generation Orchestration - Feature Survey

Date: 2026-05-01
Scope: Post-implementation audit of story-generation-orchestration-blueprint-2026-05-02

## Backend Schemas (`app/schemas/generation.py`)

285 lines, 30 classes/enums. Complete.

**Enums:** GenerationMode (8 values), DestinationKind, ContinuityStrictness, GenerationRunStatus, GenerationPlanStatus
**Input Models:** CanonGenerationRequest, CanonScope, GenerationDestination, CanonPolicy, GenerationReviewPolicy
**Snapshot Models:** WorldBibleRef, CanonicalCharacter/Relationship/World/Arc/ContinuityThread/ContinuityFinding/DraftingContext Snapshot
**Core Models:** CanonGenerationPacket, PromptBudgetSummary, GenerationPlan
**Output Models:** GenerationRunResponse, GenerationArtifactRef, CanonForkPreviewResponse, GenerationGateResult, GenerationGateResultListResponse

StrictModel pattern throughout. Pydantic validators on CanonScope and GenerationDestination.

## Backend Services

| Service | Lines | Status | Notes |
|---------|-------|--------|-------|
| `canon_packet_builder.py` | 265 | Complete | Deterministic IDs, budget-aware truncation (120K cap), scope filtering |
| `story_forking.py` | 187 | Complete | Project creation, character/relationship/world/foundation copying, ID remapping |
| `story_generation_orchestrator.py` | 253 | Complete | Full 4-phase job pipeline, idempotency, same-project and new-project paths |
| `generation_gates.py` | 105 | Complete (minimal) | 2 gate types: plan_references_known_canon, canon_congruence. Repair prompt builder present. |

## Backend API (`app/api/story_generation.py`)

130 lines. Router prefix: `/v1/story-generation`. 8 endpoints:

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| POST | `/runs` | 201 | Create generation run (full orchestration) |
| GET | `/runs` | 200 | List runs by project_id |
| GET | `/runs/{generation_id}` | 200 | Get single run |
| POST | `/runs/{generation_id}/retry` | **Stub** | Returns existing run, doesn't re-submit |
| GET | `/runs/{generation_id}/packet` | 200 | Get canon packet |
| GET | `/runs/{generation_id}/gates` | 200 | Get gate results |
| POST | `/fork-preview` | 200 | Preview fork |
| POST | `/fork-project` | 201 | Fork project only |

Error handling: 404, 409 (idempotency conflict), 400.

## Persistence

**Tables** (`app/persistence/sqlite.py`):
- `canon_generation_runs` (line 872) - 4 indexes, partial unique on source+idempotency_key
- `canon_generation_packets` (line 891) - FK CASCADE to runs
- `generation_gate_results` (line 904) - FK CASCADE to runs

**Repository methods** (`app/persistence/story_development.py`):
- 9 CRUD methods + 3 frozen dataclass records
- Upsert patterns (ON CONFLICT DO UPDATE), idempotency conflict detection at DB layer

## Executor Integration (`app/services/local_executor.py`)

4 G-phases implemented:
- G-200 (line 1658): Generation plan creation
- G-300 (line 1737): Chapter drafting loop with canon context
- G-350 (line 1867): Gate checks, repair handling
- G-400 (line 1963): Final manuscript assembly

Phase enum: `app/schemas/enums.py` lines 35-38.

## Frontend

| Area | File(s) | Status | Notes |
|------|---------|--------|-------|
| Types | `types/storyGeneration.ts` | Complete | 12 exports, snake_case preserved |
| Service | `services/storyGeneration.ts` | Complete | 8 functions, shared Axios client |
| Components | `components/generation/*.tsx` (9 files) | Complete | Wizard, selectors, policy editor, panels |
| View | `views/GenerationView.tsx` | Complete | React Query, route-wired |
| Route | `App.tsx:44` | Complete | `/workspace/:projectId/generate` |

## Tests

15 tests across 7 files. **Coverage is thin** for ~1,400 lines of service code.

| File | Count | Coverage |
|------|-------|----------|
| `test_story_generation_schemas.py` | 6 | Schema validation only |
| `test_story_generation_orchestrator.py` | 1 | E2E submission only |
| `test_story_generation_api.py` | 1 | Create+fetch round-trip only |
| `test_story_generation_persistence.py` | 2 | Table creation + upsert/idempotency |
| `test_story_generation_e2e.py` | 1 | Full flow (tmp_path) |
| `test_canon_packet_builder.py` | 1 | Deterministic packet only |
| `test_story_forking_service.py` | 1 | Selected canon copy only |
| `test_generation_gates.py` | 2 | Contradiction blocking + plan validation |

## Identified Gaps

1. **Test coverage thin** - Critical paths untested: packet budget truncation, fork ID remapping, gate repair flows, same-project orchestration
2. **`/retry` endpoint is a stub** - Returns existing run instead of re-submitting
3. **No polling mechanism** - Frontend has getGenerationRun but no interval-based status refresh
4. **Gate checks are basic** - Only text matching + character obligation validation; no LLM-assisted evaluation
5. **No cancel/abort mechanism** - Cannot stop a running generation mid-flight
