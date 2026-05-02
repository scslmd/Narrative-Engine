# Story Import Continuity and Drafting Task List

Date: 2026-04-30

## Task Format

Each task below is atomic, deterministic, and ordered so a future offline implementation pass can execute it without guessing at the intended contract.

## Continuity Tasks

- [ ] Task 1: Define continuity schema models in `app/schemas/story_import.py`.
  Add models for chapter continuity snapshots, continuity threads, continuity findings, and character state timelines. Include `project_id`, chapter or thread identifiers, `summary`, `status`, `provenance_note`, `confidence_score`, and timestamps.

- [ ] Task 2: Add continuity tables and migrations in `app/persistence/sqlite.py`.
  Create additive SQLite columns or tables for the continuity artifacts defined in Task 1. Keep migrations additive and idempotent.

- [ ] Task 3: Add continuity persistence records in `app/persistence/story_development.py`.
  Add dataclasses and row-mapper functions for continuity artifacts. Ensure repository round-trips preserve provenance and confidence.

- [ ] Task 4: Add continuity prompt builder(s) in `app/services/runtime_prompts.py`.
  Create a prompt builder that accepts ordered chapter summaries, planning output, arcs, and character roster, and returns continuity findings plus state deltas in a deterministic JSON contract.

- [ ] Task 5: Add a continuity consolidation phase in `app/services/multi_pass_import.py`.
  Insert the phase after planning synthesis. The phase should compare chapter summaries against earlier state and emit continuity findings and state snapshots.

- [ ] Task 6: Add continuity normalization and gating helpers in `app/services/multi_pass_import.py`.
  Repair or drop unknown continuity references, preserve degraded chapters, and ensure the output cannot silently upgrade weak evidence into clean continuity.

- [ ] Task 7: Persist continuity artifacts in `app/services/story_import.py`.
  Wire continuity outputs into the import transaction. Write continuity findings before any drafting-related work begins.

- [ ] Task 8: Add continuity projection support in `app/services/planning.py` or a new continuity service.
  Expose list/get helpers for continuity findings and snapshots so downstream review or drafting code can consume them deterministically.

- [ ] Task 9: Add backend tests for continuity persistence and gating.
  Include cases for continuity snapshot round-trip, contradiction detection, unresolved-thread carryover, and degraded output suppression.

## Drafting Tasks

- [ ] Task 10: Define drafting schema models in `app/schemas/story_import.py` or `app/schemas/story_development.py`.
  Add draft brief and drafting context packet models with `objective`, `emotional_turn`, `continuity_obligations`, `required_callbacks`, `forbidden_contradictions`, `voice_guidance`, `provenance_note`, and `confidence_score`.

- [ ] Task 11: Add drafting persistence tables and migrations in `app/persistence/sqlite.py`.
  Keep the design additive and separate from planning tables unless a proven existing table can safely store the new contract.

- [ ] Task 12: Add drafting repository support in `app/persistence/story_development.py`.
  Add dataclasses and repository methods for draft briefs and drafting context packets.

- [ ] Task 13: Add drafting prompt builder(s) in `app/services/runtime_prompts.py`.
  Create prompts for chapter brief synthesis and scene intent synthesis. Do not reuse the analysis prompts.

- [ ] Task 14: Add a drafting consolidation phase in `app/services/multi_pass_import.py`.
  Run this phase only after continuity consolidation succeeds or degrades within an allowed threshold.

- [ ] Task 15: Add readiness gates before drafting persistence in `app/services/story_import.py`.
  Refuse draft artifact creation if continuity confidence or planning completeness falls below the defined threshold.

- [ ] Task 16: Add drafting service projection support in `app/services/planning.py` or a new drafting service.
  Expose list/get helpers for draft briefs and drafting context packets.

- [ ] Task 17: Add backend tests for drafting readiness and refusal paths.
  Verify draft briefs are produced only from continuity-approved input and are refused when continuity gates fail.

## Integration Tasks

- [ ] Task 18: Update import response or progress contracts only if the new phases need user-visible state.
  If no UI change is required, keep the API contract stable and store the new phase outputs internally.

- [ ] Task 19: Update frontend review or planning views only if continuity findings or draft briefs are surfaced.
  Do not add UI work unless the backend output is consumable by the user.

- [ ] Task 20: Add an end-to-end regression test for the full import-to-continuity-to-drafting pipeline.
  The test should prove that continuity gates run before drafting and that degraded chapters stay degraded.

## Exit Criteria

- Continuity findings exist as persisted artifacts with provenance and confidence.
- Draft briefs exist as persisted artifacts with continuity obligations and voice guidance.
- Weak evidence cannot pass continuity gates and create draft artifacts.
- Retry behavior remains idempotent.
- New persistence rows round-trip through the repository.
