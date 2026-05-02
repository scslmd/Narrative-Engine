# Story Import Continuity And Drafting Execution Checklist

Date: 2026-04-30

This checklist is ordered for offline completion. Each task should be completed, validated, and only then should the next dependent task begin.

## Phase 0: Baseline Assumptions

1. The current import contract is already in place.
2. Single-pass import remains high-level only.
3. Planning synthesis already exists and must not be regressed.
4. New continuity and drafting work must preserve existing degraded statuses and provenance metadata.

## Dependency Order

1. Define continuity schema models.
2. Add persistence for continuity artifacts.
3. Add repository support for continuity artifacts.
4. Add continuity prompt builder.
5. Add continuity consolidation phase.
6. Add continuity normalization and gating.
7. Persist continuity artifacts from story import.
8. Define drafting schema models.
9. Add persistence for drafting artifacts.
10. Add repository support for drafting artifacts.
11. Add drafting prompt builder.
12. Add drafting consolidation phase.
13. Add drafting readiness gates.
14. Add service projections and API exposure if needed.
15. Add integration and end-to-end tests.

## Checklist

### Task 1: Define continuity schema models

- [ ] Add continuity models to `app/schemas/story_import.py` or `app/schemas/story_development.py`.
- [ ] Include:
  - `project_id`
  - chapter or thread identifiers
  - `summary`
  - `status`
  - `provenance_note`
  - `confidence_score`
  - timestamps or import-time equivalents
- [ ] Keep the models strict and additive.

Risk:
- If continuity is modeled too loosely, downstream gates will not have stable data to validate.

Validation:
- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`

### Task 2: Add continuity persistence

- [ ] Add SQLite schema for continuity artifacts in `app/persistence/sqlite.py`.
- [ ] Keep migrations additive.
- [ ] Ensure existing databases can upgrade without data loss.

Risk:
- Rebuilding or replacing existing tables is unnecessary and increases migration risk.

Validation:
- `python -m pytest tests/test_story_development_persistence.py -q -p no:cacheprovider`

### Task 3: Add continuity repository support

- [ ] Add dataclasses in `app/persistence/story_development.py`.
- [ ] Add row mappers for continuity tables.
- [ ] Add list/get/upsert methods for continuity artifacts.
- [ ] Preserve provenance and confidence during round-trip.

Risk:
- If repository projections drop provenance fields, the rest of the pipeline cannot distinguish direct evidence from fallback synthesis.

Validation:
- `python -m pytest tests/test_story_development_persistence.py tests/test_planning_service.py -q -p no:cacheprovider`

### Task 4: Add continuity prompt builder

- [ ] Add a continuity prompt builder in `app/services/runtime_prompts.py`.
- [ ] Inputs should include:
  - ordered chapter summaries
  - planning synthesis output
  - arc analysis
  - character roster
- [ ] The prompt must return a deterministic JSON contract.
- [ ] The prompt must not invent new chapter IDs or rewrite the chapter order.

Risk:
- If the prompt is too open-ended, continuity output will be stylistic instead of structural.

Validation:
- `python -m pytest tests/test_multi_pass_import.py -q -p no:cacheprovider`

### Task 5: Add continuity consolidation phase

- [ ] Add the continuity phase in `app/services/multi_pass_import.py`.
- [ ] Place it after planning synthesis.
- [ ] Emit continuity findings and state snapshots from the full ordered chapter set.
- [ ] Track provenance and confidence.

Risk:
- This phase should not replace planning synthesis; it should validate and extend it.

Validation:
- `python -m pytest tests/test_multi_pass_import.py tests/test_story_import_service.py -q -p no:cacheprovider`

### Task 6: Add continuity normalization and gating

- [ ] Add deterministic repair or rejection for unknown continuity references.
- [ ] Preserve `analysis_failed` and `partial_import`.
- [ ] Require explicit evidence before upgrading a continuity finding to a confident state.

Risk:
- Without a gate, continuity will become another place where weak evidence is silently upgraded.

Validation:
- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`

### Task 7: Persist continuity artifacts from story import

- [ ] Wire continuity outputs into `app/services/story_import.py`.
- [ ] Write continuity findings before any drafting work.
- [ ] Keep the transaction atomic.

Risk:
- If continuity writes occur after draft generation, the draft path may consume unverified state.

Validation:
- `python -m pytest tests/test_story_import_service.py tests/test_import_jobs.py -q -p no:cacheprovider`

### Task 8: Define drafting schema models

- [ ] Add draft brief models in `app/schemas/story_import.py` or `app/schemas/story_development.py`.
- [ ] Include:
  - `objective`
  - `emotional_turn`
  - `continuity_obligations`
  - `required_callbacks`
  - `forbidden_contradictions`
  - `voice_guidance`
  - `provenance_note`
  - `confidence_score`

Risk:
- Draft briefs that omit continuity obligations will not be safe for writer-facing use.

Validation:
- `python -m pytest tests/test_story_development_persistence.py tests/test_planning_service.py -q -p no:cacheprovider`

### Task 9: Add drafting persistence

- [ ] Add drafting tables and migrations in `app/persistence/sqlite.py`.
- [ ] Keep them separate from planning tables unless the schema can safely reuse an existing table.
- [ ] Preserve provenance and confidence.

Risk:
- Mixing draft-ready artifacts with planning artifacts can blur the trust boundary and make review/UI behavior ambiguous.

Validation:
- `python -m pytest tests/test_story_development_persistence.py -q -p no:cacheprovider`

### Task 10: Add drafting repository support

- [ ] Add dataclasses and repository methods in `app/persistence/story_development.py`.
- [ ] Add round-trip tests for any new drafting records.

Risk:
- Missing repository support means the new phase can only exist in memory.

Validation:
- `python -m pytest tests/test_story_development_persistence.py tests/test_planning_service.py -q -p no:cacheprovider`

### Task 11: Add drafting prompt builder

- [ ] Add drafting prompt builder(s) in `app/services/runtime_prompts.py`.
- [ ] Use the continuity-approved planning output as input.
- [ ] Do not reuse analysis prompts.
- [ ] Output should be a writer-facing brief, not another analysis summary.

Risk:
- Reusing analysis prompts will recreate the current overbroad import contract.

Validation:
- `python -m pytest tests/test_multi_pass_import.py -q -p no:cacheprovider`

### Task 12: Add drafting consolidation phase

- [ ] Add drafting consolidation in `app/services/multi_pass_import.py`.
- [ ] Run it only after continuity consolidation succeeds or degrades within the allowed threshold.
- [ ] Emit draft briefs and drafting context packets.

Risk:
- Drafting must not be available when continuity is unresolved beyond the allowed threshold.

Validation:
- `python -m pytest tests/test_multi_pass_import.py tests/test_story_import_service.py -q -p no:cacheprovider`

### Task 13: Add drafting readiness gates

- [ ] Refuse or downgrade draft artifacts when:
  - continuity confidence is below threshold
  - planning completeness is insufficient
  - a chapter has unresolved contradictions
  - POV or voice is unstable
- [ ] Preserve explicit degraded states.

Risk:
- If the gate is too permissive, the system will create writer-facing artifacts that look trustworthy but are not.

Validation:
- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`

### Task 14: Add service projections and API exposure if needed

- [ ] Decide whether continuity and drafting need new service-facing readers.
- [ ] Add API endpoints only if the frontend must surface these artifacts.
- [ ] Do not add UI routes without persisted data and stable contracts.

Risk:
- Exposing incomplete API surfaces increases frontend drift.

Validation:
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`

### Task 15: Add integration and end-to-end tests

- [ ] Add continuity persistence tests.
- [ ] Add drafting readiness tests.
- [ ] Add refusal tests for weak continuity.
- [ ] Add idempotency tests for continuity and draft artifacts.
- [ ] Add repository round-trip coverage for new rows.

Risk:
- Without end-to-end coverage, the phases may exist but fail at the boundary between synthesis and persistence.

Validation:
- `python -m pytest tests/test_json_extract.py tests/test_import_jobs.py tests/test_story_import_service.py tests/test_multi_pass_import.py tests/test_story_development_persistence.py tests/test_planning_service.py -q -p no:cacheprovider`

## Completion Criteria

- Continuity artifacts exist, persist, and round-trip.
- Draft briefs exist, persist, and round-trip.
- Continuity gates reject weak or contradictory evidence.
- Drafting gates only allow continuity-approved imports.
- Existing planning import tests still pass.
- Single-pass import remains high-level only.

## Suggested Execution Strategy

1. Implement continuity first.
2. Validate continuity before starting drafting.
3. Only add draft-specific artifacts after continuity gates are deterministic and stable.
4. Do not widen the import contract while doing this work.
