# Frontend Canon Customization Enhancement Blueprint

Date: 2026-05-02

## Purpose

This document defines the frontend and backend integration work needed to let users edit ingested character/world/mythos/pattern material and use those edits to customize new story generation or character/world forks.

This is documentation only. It extends `docs/story-generation-orchestration-blueprint-2026-05-02.md` and uses the same orchestrator-to-executor implementation style.

## Current Frontend State

Current exposed editing:

- `/workspace/:projectId/plan` has a `Characters` tab.
- `CharacterBuilder` can create/edit character profile fields such as goals, needs, backstory, voice notes, contradictions, values, taboos, arc notes, continuity facts, and writer notes.
- `/workspace/:projectId/plan` has a `World Bible` tab.
- `WorldBibleWorkspace` can create/edit title, summary, canonical facts, continuity warnings, and writer notes.
- `/workspace/:projectId/plan` has a `Foundation` tab.
- Relationship surfaces can view/delete relationships and backend supports relationship create/update/delete.
- `StoryImportModal` supports story import, mythos extraction, and pattern extraction.

Current gaps:

- No dedicated editable canon customization workspace.
- No generation wizard connected to edited character/world selections.
- No first-class mythos editor after extraction.
- No first-class pattern editor after extraction.
- No way to classify selected fields as locked canon, soft guidance, or intentionally mutable for generation.
- No frontend view of generation packets, canon scope, canon policy, or gate status.
- No “fork selected characters/world/mythos into new project” wizard.
- No UI for previewing exactly what canon will be copied or sent to the executor.

## Target Frontend Behavior

The user should be able to:

1. Import story/mythos/pattern source material.
2. Open an editable Canon Workshop for the project.
3. Review and edit extracted characters, relationships, world bible, mythos motifs, reusable patterns, continuity findings, and generation notes.
4. Mark specific facts as:
   - locked canon
   - soft guidance
   - allowed to mutate
   - forbidden contradiction
5. Select canon scope for generation:
   - full project
   - selected characters
   - selected world entries
   - selected mythos/patterns
   - selected continuity threads
6. Preview the generated `CanonGenerationPacket`.
7. Submit generation/fork run.
8. Monitor run status, gate results, generated drafts/manuscripts, and inspect lineage.
9. Repair or revise generated output when gates fail.

## Information Architecture

Add a new workspace route:

- `/workspace/:projectId/canon`

Add a new generation route if not already implemented from the generation blueprint:

- `/workspace/:projectId/generate`

Navigation labels:

- `Canon`
- `Generate`

Recommended tab structure for Canon route:

- `Overview`
- `Characters`
- `Relationships`
- `World`
- `Mythos`
- `Patterns`
- `Continuity`
- `Generation Rules`
- `Packet Preview`

## Backend Model Requirements

Some current data already exists as characters/world/foundation/relationships. To support the frontend enhancement cleanly, add these canonical customization models.

## Schema: `CanonAnnotation`

File:

- `app/schemas/canon_customization.py`

Fields:

- `annotation_id: str`
- `project_id: str`
- `target_kind: "character" | "relationship" | "world_bible" | "mythos" | "pattern" | "continuity" | "foundation"`
- `target_id: str`
- `field_path: str`
- `annotation_kind: "locked" | "soft_guidance" | "mutable" | "forbidden_contradiction" | "generation_note"`
- `note: str`
- `applies_to_modes: list[str]`
- `created_at: str | None`
- `updated_at: str | None`

Deterministic id:

- `annotation_id = hash_id("canon-annotation", f"{project_id}:{target_kind}:{target_id}:{field_path}:{annotation_kind}")`

## Schema: `CanonCustomizationProfile`

Fields:

- `profile_id: str`
- `project_id: str`
- `name: str`
- `description: str`
- `default_generation_mode: str`
- `canon_scope: CanonScope`
- `canon_policy: CanonPolicy`
- `generation_brief_template: str`
- `selected_annotation_ids: list[str]`
- `status: "draft" | "active" | "archived"`

Purpose:

- Lets users save reusable generation/fork configurations.

## Schema: `MythosEntry`

Fields:

- `mythos_id: str`
- `project_id: str`
- `entry_type: "archetype" | "motif" | "cosmic_rule" | "symbol" | "ritual" | "deity" | "cycle" | "theme"`
- `name: str`
- `summary: str`
- `canonical_facts: list[str]`
- `pattern_notes: list[str]`
- `source_corpus: str | None`
- `generation_guidance: str`
- `visibility_scope: "project" | "forkable" | "private"`
- `writer_notes: str | None`

## Schema: `PatternEntry`

Fields:

- `pattern_id: str`
- `project_id: str`
- `pattern_type: "plot" | "character" | "relationship" | "world" | "theme" | "scene" | "structure"`
- `name: str`
- `summary: str`
- `source_type: "narrative" | "mythology" | "manual"`
- `generation_modes: list[str]`
- `beats: list[str]`
- `constraints: list[str]`
- `transposition_notes: str`
- `writer_notes: str | None`

## Persistence Requirements

File:

- `app/persistence/sqlite.py`

Add tables:

### `canon_annotations`

Columns:

- `annotation_id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `target_kind TEXT NOT NULL`
- `target_id TEXT NOT NULL`
- `field_path TEXT NOT NULL`
- `annotation_kind TEXT NOT NULL`
- `note TEXT NOT NULL DEFAULT ''`
- `applies_to_modes_json TEXT NOT NULL DEFAULT '[]'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_canon_annotations_project_target ON canon_annotations(project_id, target_kind, target_id)`
- `idx_canon_annotations_project_kind ON canon_annotations(project_id, annotation_kind)`

### `canon_customization_profiles`

Columns:

- `profile_id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `name TEXT NOT NULL`
- `description TEXT NOT NULL DEFAULT ''`
- `default_generation_mode TEXT NOT NULL`
- `canon_scope_json TEXT NOT NULL`
- `canon_policy_json TEXT NOT NULL`
- `generation_brief_template TEXT NOT NULL DEFAULT ''`
- `selected_annotation_ids_json TEXT NOT NULL DEFAULT '[]'`
- `status TEXT NOT NULL DEFAULT 'draft'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_canon_profiles_project_status ON canon_customization_profiles(project_id, status, updated_at)`

### `mythos_entries`

Columns:

- `mythos_id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `entry_type TEXT NOT NULL`
- `name TEXT NOT NULL`
- `summary TEXT NOT NULL DEFAULT ''`
- `canonical_facts_json TEXT NOT NULL DEFAULT '[]'`
- `pattern_notes_json TEXT NOT NULL DEFAULT '[]'`
- `source_corpus TEXT`
- `generation_guidance TEXT NOT NULL DEFAULT ''`
- `visibility_scope TEXT NOT NULL DEFAULT 'project'`
- `writer_notes TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_mythos_entries_project_type ON mythos_entries(project_id, entry_type, name)`

### `pattern_entries`

Columns:

- `pattern_id TEXT PRIMARY KEY`
- `project_id TEXT NOT NULL`
- `pattern_type TEXT NOT NULL`
- `name TEXT NOT NULL`
- `summary TEXT NOT NULL DEFAULT ''`
- `source_type TEXT NOT NULL DEFAULT 'manual'`
- `generation_modes_json TEXT NOT NULL DEFAULT '[]'`
- `beats_json TEXT NOT NULL DEFAULT '[]'`
- `constraints_json TEXT NOT NULL DEFAULT '[]'`
- `transposition_notes TEXT NOT NULL DEFAULT ''`
- `writer_notes TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes:

- `idx_pattern_entries_project_type ON pattern_entries(project_id, pattern_type, name)`

## Repository Requirements

File:

- `app/persistence/story_development.py`

Add dataclasses:

- `CanonAnnotationRecord`
- `CanonCustomizationProfileRecord`
- `MythosEntryRecord`
- `PatternEntryRecord`

Add methods:

- `upsert_canon_annotation(...)`
- `delete_canon_annotation(annotation_id: str)`
- `list_canon_annotations(project_id: str, target_kind: str | None = None, target_id: str | None = None)`
- `upsert_canon_customization_profile(...)`
- `get_canon_customization_profile(profile_id: str)`
- `list_canon_customization_profiles(project_id: str)`
- `delete_canon_customization_profile(profile_id: str)`
- `upsert_mythos_entry(...)`
- `get_mythos_entry(mythos_id: str)`
- `list_mythos_entries(project_id: str, entry_type: str | None = None)`
- `delete_mythos_entry(mythos_id: str)`
- `upsert_pattern_entry(...)`
- `get_pattern_entry(pattern_id: str)`
- `list_pattern_entries(project_id: str, pattern_type: str | None = None)`
- `delete_pattern_entry(pattern_id: str)`

All upserts must be deterministic and idempotent.

## Backend Service Requirements

## Module: `app/services/canon_customization.py`

Class:

- `CanonCustomizationService`

Responsibilities:

- Manage annotations and customization profiles.
- Convert frontend user selections into `CanonScope` and `CanonPolicy`.
- Provide packet preview inputs to the generation orchestrator.

Functions:

- `list_annotations(project_id: str, target_kind: str | None = None, target_id: str | None = None) -> list[CanonAnnotation]`
- `save_annotation(payload: CanonAnnotationCreateRequest) -> CanonAnnotation`
- `delete_annotation(project_id: str, annotation_id: str) -> None`
- `create_profile(payload: CanonCustomizationProfileCreateRequest) -> CanonCustomizationProfile`
- `update_profile(profile_id: str, payload: CanonCustomizationProfileUpdateRequest) -> CanonCustomizationProfile`
- `list_profiles(project_id: str) -> list[CanonCustomizationProfile]`
- `build_scope_from_profile(profile_id: str) -> CanonScope`
- `build_policy_from_annotations(project_id: str, annotation_ids: list[str]) -> CanonPolicy`

## Module: `app/services/mythos_library.py`

Class:

- `MythosLibraryService`

Responsibilities:

- Provide CRUD for mythos entries.
- Normalize mythos extraction outputs into editable mythos records.
- Feed mythos entries into canon generation packets.

Functions:

- `list_entries(project_id: str, entry_type: str | None = None) -> list[MythosEntry]`
- `create_entry(payload: MythosEntryCreateRequest) -> MythosEntry`
- `update_entry(mythos_id: str, payload: MythosEntryUpdateRequest) -> MythosEntry`
- `delete_entry(project_id: str, mythos_id: str) -> None`
- `materialize_extraction(project_id: str, extraction_id: str) -> list[MythosEntry]`

## Module: `app/services/pattern_library.py`

Class:

- `PatternLibraryService`

Responsibilities:

- Provide CRUD for reusable generation patterns.
- Normalize pattern extraction outputs into editable pattern records.
- Feed selected patterns into canon generation packets.

Functions:

- `list_entries(project_id: str, pattern_type: str | None = None) -> list[PatternEntry]`
- `create_entry(payload: PatternEntryCreateRequest) -> PatternEntry`
- `update_entry(pattern_id: str, payload: PatternEntryUpdateRequest) -> PatternEntry`
- `delete_entry(project_id: str, pattern_id: str) -> None`
- `materialize_extraction(project_id: str, extraction_id: str) -> list[PatternEntry]`

## Integration With Canon Packet Builder

Update:

- `app/services/canon_packet_builder.py`

Add functions:

- `_load_mythos_snapshots(scope: CanonScope) -> list[CanonicalMythosSnapshot]`
- `_load_pattern_snapshots(scope: CanonScope) -> list[CanonicalPatternSnapshot]`
- `_load_annotation_policy(project_id: str, annotation_ids: list[str]) -> CanonPolicy`

Packet changes:

- Add `mythos_entries`.
- Add `pattern_entries`.
- Add `canon_annotations`.
- Add `customization_profile_id`.

Ordering:

- Mythos entries by `(entry_type, name)`.
- Pattern entries by `(pattern_type, name)`.
- Annotations by `(target_kind, target_id, field_path, annotation_kind)`.

## API Requirements

Add router:

- `app/api/canon_customization.py`

Prefix:

- `/v1/canon`

Endpoints:

- `GET /annotations?project_id={id}&target_kind={kind}&target_id={id}`
- `POST /annotations`
- `DELETE /annotations/{annotation_id}?project_id={id}`
- `GET /profiles?project_id={id}`
- `POST /profiles`
- `PATCH /profiles/{profile_id}?project_id={id}`
- `DELETE /profiles/{profile_id}?project_id={id}`
- `POST /profiles/{profile_id}/packet-preview?project_id={id}`

Add router:

- `app/api/mythos_library.py`

Prefix:

- `/v1/mythos`

Endpoints:

- `GET /entries?project_id={id}&entry_type={type}`
- `POST /entries`
- `PATCH /entries/{mythos_id}?project_id={id}`
- `DELETE /entries/{mythos_id}?project_id={id}`
- `POST /materialize-extraction`

Add router:

- `app/api/pattern_library.py`

Prefix:

- `/v1/patterns`

Endpoints:

- `GET /entries?project_id={id}&pattern_type={type}`
- `POST /entries`
- `PATCH /entries/{pattern_id}?project_id={id}`
- `DELETE /entries/{pattern_id}?project_id={id}`
- `POST /materialize-extraction`

Register routers in:

- `app/main.py`

## Frontend Types

Create:

- `frontend/src/types/canonCustomization.ts`
- `frontend/src/types/mythos.ts`
- `frontend/src/types/patterns.ts`

Types:

- `CanonAnnotation`
- `CanonAnnotationCreateRequest`
- `CanonCustomizationProfile`
- `CanonCustomizationProfileCreateRequest`
- `CanonCustomizationProfileUpdateRequest`
- `MythosEntry`
- `MythosEntryCreateRequest`
- `MythosEntryUpdateRequest`
- `PatternEntry`
- `PatternEntryCreateRequest`
- `PatternEntryUpdateRequest`

Rules:

- Keep backend snake_case fields.
- Use `interface` for object-shaped API contracts.
- Use `type` for unions.

## Frontend Services

Create:

- `frontend/src/services/canonCustomization.ts`
- `frontend/src/services/mythosLibrary.ts`
- `frontend/src/services/patternLibrary.ts`

Functions:

### `canonCustomization.ts`

- `getCanonAnnotations(projectId: string, filters?: CanonAnnotationFilters): Promise<CanonAnnotation[]>`
- `createCanonAnnotation(request: CanonAnnotationCreateRequest): Promise<CanonAnnotation>`
- `deleteCanonAnnotation(projectId: string, annotationId: string): Promise<void>`
- `getCanonProfiles(projectId: string): Promise<CanonCustomizationProfile[]>`
- `createCanonProfile(request: CanonCustomizationProfileCreateRequest): Promise<CanonCustomizationProfile>`
- `updateCanonProfile(profileId: string, projectId: string, updates: CanonCustomizationProfileUpdateRequest): Promise<CanonCustomizationProfile>`
- `deleteCanonProfile(projectId: string, profileId: string): Promise<void>`
- `previewCanonProfilePacket(projectId: string, profileId: string): Promise<CanonGenerationPacket>`

### `mythosLibrary.ts`

- `getMythosEntries(projectId: string, entryType?: MythosEntryType): Promise<MythosEntry[]>`
- `createMythosEntry(request: MythosEntryCreateRequest): Promise<MythosEntry>`
- `updateMythosEntry(mythosId: string, projectId: string, updates: MythosEntryUpdateRequest): Promise<MythosEntry>`
- `deleteMythosEntry(projectId: string, mythosId: string): Promise<void>`
- `materializeMythosExtraction(projectId: string, extractionId: string): Promise<MythosEntry[]>`

### `patternLibrary.ts`

- `getPatternEntries(projectId: string, patternType?: PatternEntryType): Promise<PatternEntry[]>`
- `createPatternEntry(request: PatternEntryCreateRequest): Promise<PatternEntry>`
- `updatePatternEntry(patternId: string, projectId: string, updates: PatternEntryUpdateRequest): Promise<PatternEntry>`
- `deletePatternEntry(projectId: string, patternId: string): Promise<void>`
- `materializePatternExtraction(projectId: string, extractionId: string): Promise<PatternEntry[]>`

All services must use:

- `frontend/src/lib/api.ts`

## Frontend Components

Create directory:

- `frontend/src/components/canon/`

Components:

- `CanonWorkshop.tsx`
- `CanonOverviewPanel.tsx`
- `CanonAnnotationToolbar.tsx`
- `CanonLockBadge.tsx`
- `CanonScopeSummary.tsx`
- `CanonProfileList.tsx`
- `CanonProfileEditor.tsx`
- `CanonPacketPreview.tsx`
- `CanonGenerationRulesEditor.tsx`
- `CanonSelectionDrawer.tsx`

Create directory:

- `frontend/src/components/mythos/`

Components:

- `MythosLibraryWorkspace.tsx`
- `MythosEntryCard.tsx`
- `MythosEntryEditor.tsx`
- `MythosTypeFilter.tsx`

Create directory:

- `frontend/src/components/patterns/`

Components:

- `PatternLibraryWorkspace.tsx`
- `PatternEntryCard.tsx`
- `PatternEntryEditor.tsx`
- `PatternModeSelector.tsx`

Update existing components:

- `frontend/src/components/characters/CharacterBuilder.tsx`
- `frontend/src/components/bible/WorldBibleWorkspace.tsx`
- `frontend/src/views/PlanningView.tsx`

Required UI additions:

- Add field-level annotation controls in character editor and world bible editor.
- Add `locked`, `soft guidance`, `mutable`, and `forbidden contradiction` badges.
- Add “Use in Generation” checkboxes for characters/world/mythos/patterns.
- Add “Generate with Selected” action.
- Add “Fork Selected to New Story” action.

## Frontend Views And Routes

Create:

- `frontend/src/views/CanonView.tsx`

Update:

- `frontend/src/App.tsx`

Route:

- `/workspace/:projectId/canon`

CanonView responsibilities:

- Load characters.
- Load relationships.
- Load world bible.
- Load mythos entries.
- Load pattern entries.
- Load canon annotations.
- Load customization profiles.
- Render `CanonWorkshop`.
- Provide create/update/delete mutations.
- Invalidate all affected React Query keys after mutations.

Update:

- route navigation/workspace tabs to include Canon.

## Frontend State Model

Use React Query for server state:

Query keys:

- `['canon', 'annotations', projectId, filters]`
- `['canon', 'profiles', projectId]`
- `['canon', 'mythos', projectId, entryType]`
- `['canon', 'patterns', projectId, patternType]`
- `['planning', 'characters', projectId]`
- `['planning', 'world-bible', projectId]`

Use local component state for:

- selected canon scope
- active tab
- unsaved profile draft
- packet preview visibility

Do not use global Zustand unless generation wizard state must survive route changes.

## Interconnection With Story Generation

The Canon route must produce a `CanonGenerationRequest` compatible with `docs/story-generation-orchestration-blueprint-2026-05-02.md`.

Mapping:

- selected characters -> `canon_scope.character_ids`
- selected world entries -> `canon_scope.world_bible_refs`
- selected mythos entries -> `canon_scope.mythos_ids`
- selected pattern entries -> `canon_scope.pattern_ids`
- locked annotations -> `canon_policy.locked_character_fields` or `locked_world_fields`
- forbidden annotations -> `canon_policy.forbidden_contradictions`
- mutable annotations -> `canon_policy.allowed_character_changes` or `allowed_world_changes`
- profile generation brief -> `generation_brief`

Submit path:

1. User saves or selects a `CanonCustomizationProfile`.
2. Frontend calls `previewCanonProfilePacket`.
3. User confirms.
4. Frontend calls `createGenerationRun` from `storyGeneration.ts`.
5. Frontend navigates to `/workspace/:projectId/generate?generation_id={id}`.

## Orchestrator To Executor Markup

The frontend Canon Workshop does not execute LLM work directly. It produces deterministic profile and scope data consumed by the story generation orchestrator.

```yaml
frontend_flow_version: "canon-customization.v1"
route: "/workspace/:projectId/canon"
inputs:
  project_id: "$route.projectId"
  server_state:
    characters: "GET /v1/story-development/characters"
    relationships: "GET /v1/story-development/relationships"
    world_bible: "GET /v1/story-development/world-bible"
    mythos: "GET /v1/mythos/entries"
    patterns: "GET /v1/patterns/entries"
    annotations: "GET /v1/canon/annotations"
    profiles: "GET /v1/canon/profiles"
user_actions:
  annotate_field:
    endpoint: "POST /v1/canon/annotations"
    invalidates:
      - "canon.annotations"
      - "canon.profiles"
  save_profile:
    endpoint: "POST/PATCH /v1/canon/profiles"
    invalidates:
      - "canon.profiles"
  preview_packet:
    endpoint: "POST /v1/canon/profiles/{profile_id}/packet-preview"
    output: "CanonGenerationPacket"
  submit_generation:
    endpoint: "POST /v1/story-generation/runs"
    payload_source:
      - "CanonCustomizationProfile"
      - "CanonGenerationPacket.preview"
    output: "GenerationRunResponse"
    navigate_to: "/workspace/:projectId/generate?generation_id=$generation_id"
backend_orchestration:
  G-100:
    service: "CanonPacketBuilder"
    input: "CanonCustomizationProfile + CanonGenerationRequest"
    output: "CanonGenerationPacket"
  G-200:
    executor: "LocalExecutor._run_generation_planner_phase"
    input: "CanonGenerationPacket"
    output: "GenerationPlan"
  G-300:
    executor: "LocalExecutor._run_generation_drafter_phase"
    input: "GenerationPlan + CanonGenerationPacket"
    output: "DraftArtifact + ManuscriptDocument"
  G-350:
    service: "GenerationGateService"
    input: "Generated artifacts + CanonGenerationPacket"
    output: "GenerationGateResult"
  G-400:
    executor: "LocalExecutor._run_generation_compiler_phase"
    input: "Passing gated artifacts"
    output: "Final manuscript"
```

## Atomic Deterministic Task List

### FE-CANON-001: Add Canon Customization Schemas

Files:

- `app/schemas/canon_customization.py`
- `app/schemas/__init__.py`

Steps:

1. Add `CanonAnnotation`.
2. Add `CanonCustomizationProfile`.
3. Add create/update request schemas.
4. Export schemas.

Acceptance:

- Empty target ids are rejected.
- Invalid annotation kinds are rejected.
- Valid profile with canon scope validates.

Validation:

- `python -m pytest tests/test_canon_customization_schemas.py -q -p no:cacheprovider`

### FE-CANON-002: Add Mythos And Pattern Library Schemas

Files:

- `app/schemas/mythos_library.py`
- `app/schemas/pattern_library.py`
- `app/schemas/__init__.py`

Steps:

1. Add `MythosEntry` schemas.
2. Add `PatternEntry` schemas.
3. Add create/update request schemas.
4. Export schemas.

Acceptance:

- Invalid entry types are rejected.
- Valid manual entries validate.

Validation:

- `python -m pytest tests/test_mythos_pattern_library_schemas.py -q -p no:cacheprovider`

### FE-CANON-003: Add Persistence Tables

Files:

- `app/persistence/sqlite.py`

Steps:

1. Add `canon_annotations`.
2. Add `canon_customization_profiles`.
3. Add `mythos_entries`.
4. Add `pattern_entries`.
5. Add indexes and additive migrations.

Acceptance:

- New DB creates tables.
- Existing DB migrates.

Validation:

- `python -m pytest tests/test_canon_customization_persistence.py -q -p no:cacheprovider`

### FE-CANON-004: Add Repository Methods

Files:

- `app/persistence/story_development.py`
- `tests/test_canon_customization_persistence.py`

Steps:

1. Add record dataclasses.
2. Add upsert/list/get/delete for annotations.
3. Add upsert/list/get/delete for profiles.
4. Add CRUD for mythos entries.
5. Add CRUD for pattern entries.

Acceptance:

- Upserts are idempotent.
- Deletes are scoped by project where applicable.
- List methods preserve stable ordering.

Validation:

- `python -m pytest tests/test_canon_customization_persistence.py -q -p no:cacheprovider`

### FE-CANON-005: Add Backend Services

Files:

- `app/services/canon_customization.py`
- `app/services/mythos_library.py`
- `app/services/pattern_library.py`

Steps:

1. Implement service methods listed above.
2. Validate target ownership.
3. Convert annotations to canon policy fragments.
4. Materialize extraction outputs into editable entries.

Acceptance:

- Cannot annotate an object from another project.
- Annotation policy output is deterministic.
- Materialization is idempotent.

Validation:

- `python -m pytest tests/test_canon_customization_service.py tests/test_mythos_pattern_library_service.py -q -p no:cacheprovider`

### FE-CANON-006: Add API Routers

Files:

- `app/api/canon_customization.py`
- `app/api/mythos_library.py`
- `app/api/pattern_library.py`
- `app/main.py`

Steps:

1. Add endpoints listed in API Requirements.
2. Map service errors to precise HTTP statuses.
3. Register routers.

Acceptance:

- CRUD endpoints work through `TestClient`.
- Packet preview endpoint returns generation packet preview.

Validation:

- `python -m pytest tests/test_canon_customization_api.py tests/test_mythos_pattern_library_api.py -q -p no:cacheprovider`

### FE-CANON-007: Extend Canon Packet Builder

Files:

- `app/services/canon_packet_builder.py`
- `tests/test_canon_packet_builder.py`

Steps:

1. Add mythos snapshots.
2. Add pattern snapshots.
3. Add annotations.
4. Add customization profile id.
5. Update source hashes.

Acceptance:

- Packet preview includes selected mythos/pattern entries.
- Annotation-derived policies appear in packet.

Validation:

- `python -m pytest tests/test_canon_packet_builder.py -q -p no:cacheprovider`

### FE-CANON-008: Add Frontend Types

Files:

- `frontend/src/types/canonCustomization.ts`
- `frontend/src/types/mythos.ts`
- `frontend/src/types/patterns.ts`
- `frontend/src/types/index.ts`

Steps:

1. Add types listed above.
2. Export from index.
3. Keep snake_case fields.

Acceptance:

- `tsc --noEmit` passes.

Validation:

- `cd frontend && npm run typecheck`

### FE-CANON-009: Add Frontend Services

Files:

- `frontend/src/services/canonCustomization.ts`
- `frontend/src/services/mythosLibrary.ts`
- `frontend/src/services/patternLibrary.ts`
- `frontend/src/services/*.test.ts`

Steps:

1. Add services using shared `api`.
2. Add MSW tests for success and failure paths.
3. Do not add file-local `API_BASE`.

Acceptance:

- Services call expected endpoints.
- Error responses throw meaningful errors.

Validation:

- `cd frontend && npm run test -- canonCustomization mythosLibrary patternLibrary`

### FE-CANON-010: Add Canon Workshop View

Files:

- `frontend/src/views/CanonView.tsx`
- `frontend/src/App.tsx`

Steps:

1. Add route `/workspace/:projectId/canon`.
2. Load canon data with React Query.
3. Render `CanonWorkshop`.
4. Add loading/empty/error states.

Acceptance:

- Route deep-link renders directly.
- Missing project id shows safe empty/error state.

Validation:

- `cd frontend && npm run test -- CanonView`

### FE-CANON-011: Add Canon Workshop Components

Files:

- `frontend/src/components/canon/*.tsx`

Steps:

1. Add overview.
2. Add profile list/editor.
3. Add annotation toolbar.
4. Add packet preview.
5. Add selection drawer.

Acceptance:

- User can create profile from selected canon.
- User can preview packet.
- Invalid profile cannot submit.

Validation:

- `cd frontend && npm run test -- CanonWorkshop`

### FE-CANON-012: Add Mythos Library UI

Files:

- `frontend/src/components/mythos/*.tsx`

Steps:

1. Add list/filter view.
2. Add entry editor.
3. Add create/update/delete UI.
4. Add “Use in Generation” selection.

Acceptance:

- Mythos entries are editable after materialization.
- Selected mythos entries flow into canon profile.

Validation:

- `cd frontend && npm run test -- MythosLibraryWorkspace`

### FE-CANON-013: Add Pattern Library UI

Files:

- `frontend/src/components/patterns/*.tsx`

Steps:

1. Add list/filter view.
2. Add pattern editor.
3. Add generation mode tags.
4. Add “Use in Generation” selection.

Acceptance:

- Pattern entries are editable.
- Selected patterns flow into canon profile.

Validation:

- `cd frontend && npm run test -- PatternLibraryWorkspace`

### FE-CANON-014: Add Field-Level Annotations To Character Editor

Files:

- `frontend/src/components/characters/CharacterBuilder.tsx`
- `frontend/src/components/canon/CanonAnnotationToolbar.tsx`

Steps:

1. Add annotation controls for key fields.
2. Support locked/soft/mutable/forbidden notes.
3. Persist annotations through `canonCustomization` service.
4. Refresh annotation query after save.

Acceptance:

- Character field can be marked locked.
- Locked badge persists after reload.

Validation:

- `cd frontend && npm run test -- CharacterBuilder`

### FE-CANON-015: Add Field-Level Annotations To World Bible Editor

Files:

- `frontend/src/components/bible/WorldBibleWorkspace.tsx`
- `frontend/src/components/canon/CanonAnnotationToolbar.tsx`

Steps:

1. Add annotation controls for title, summary, canonical facts, continuity warnings.
2. Persist annotations.
3. Display badges on cards and editor fields.

Acceptance:

- World fact can be marked forbidden contradiction.
- Badge persists after reload.

Validation:

- `cd frontend && npm run test -- WorldBibleWorkspace`

### FE-CANON-016: Connect Canon Profiles To Generation Runs

Files:

- `frontend/src/components/canon/CanonProfileEditor.tsx`
- `frontend/src/services/storyGeneration.ts`
- `frontend/src/views/CanonView.tsx`

Steps:

1. Build `CanonGenerationRequest` from profile.
2. Preview packet.
3. Submit generation run.
4. Navigate to generation route.

Acceptance:

- Same-project generation can be submitted from Canon route.
- New-project fork can be submitted from Canon route.

Validation:

- `cd frontend && npm run test -- CanonProfileEditor`

### FE-CANON-017: Add Import Modal Post-Extraction Materialization

Files:

- `frontend/src/components/projects/StoryImportModal.tsx`
- `frontend/src/services/mythosLibrary.ts`
- `frontend/src/services/patternLibrary.ts`

Steps:

1. After mythos extraction success, offer “Open Mythos Library”.
2. After pattern extraction success, offer “Open Pattern Library”.
3. Optionally call materialize endpoint if extraction did not already persist editable records.
4. Navigate to `/workspace/:projectId/canon?tab=mythos` or `?tab=patterns`.

Acceptance:

- Extraction flows lead to editable library surfaces.

Validation:

- `cd frontend && npm run test -- StoryImportModal`

### FE-CANON-018: Full Frontend Integration Test

Files:

- `frontend/src/views/CanonView.test.tsx`
- `frontend/src/components/canon/CanonWorkshop.test.tsx`

Steps:

1. Mock characters/world/mythos/patterns.
2. Select character and world entry.
3. Mark one field locked.
4. Save profile.
5. Preview packet.
6. Submit generation.

Acceptance:

- Test proves user can customize canon and launch generation from frontend.

Validation:

- `cd frontend && npm run test`

## Production Gate

Do not claim the frontend supports canon-customized story generation until:

- Canon route exists and deep-links.
- Characters, world, mythos, and patterns can be edited.
- Field annotations persist and reload.
- Canon profiles can be saved.
- Packet preview works.
- Generation run submission works from saved profile.
- Import mythos/pattern flows lead to editable library surfaces.
- Backend tests for canon customization APIs pass.
- Frontend service/component/view tests pass.

Required validation:

- `python -m pytest tests/test_canon_customization_schemas.py tests/test_canon_customization_persistence.py tests/test_canon_customization_service.py tests/test_canon_customization_api.py tests/test_mythos_pattern_library_schemas.py tests/test_mythos_pattern_library_service.py tests/test_mythos_pattern_library_api.py tests/test_canon_packet_builder.py -q -p no:cacheprovider`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`

## Implementation Status (2026-05-02)

Completed:
- FE-CANON-001 to FE-CANON-018 implemented in production code and tests.
- Canon schemas, persistence, repository methods, services, and APIs are wired and validated.
- `CanonPacketBuilder` includes mythos, patterns, annotations, and updated source hashes.
- Frontend canon/mythos/pattern types and services are implemented with Vitest coverage.
- `/workspace/:projectId/canon` route is implemented with deep-link tab handling (`?tab=mythos|patterns|packet`).
- Canon component suite is implemented under `frontend/src/components/canon/`, including profile, rules, scope summary, and packet preview controls.
- Mythos and pattern workspaces are implemented under `frontend/src/components/mythos/` and `frontend/src/components/patterns/`.
- Field-level annotation controls are integrated into `CharacterBuilder` and `WorldBibleWorkspace`.
- Import modal post-extraction flows now route to canon customization tabs.
- Canon profile workflow can preview packet and launch generation directly.

Validation completed:
- `python -m pytest tests/test_canon_packet_builder.py -q -p no:cacheprovider`
- `python -m pytest tests/test_canon_customization_api.py tests/test_mythos_pattern_library_api.py -q -p no:cacheprovider`
- `cd frontend && npm run test -- canonCustomization mythosLibrary patternLibrary storyGeneration`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run lint` (warnings only, no errors)
