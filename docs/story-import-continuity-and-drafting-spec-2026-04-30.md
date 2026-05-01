# Story Import Continuity and Drafting Spec

Date: 2026-04-30

## Purpose

This document defines the remaining work needed to turn story import into a full-story digestion pipeline instead of a chapter-local planning importer.

The current importer now does the following correctly:

- high-level single-pass import only
- multi-pass chapter analysis
- character and world consolidation
- arc detection
- planning synthesis with provenance and confidence
- degraded-state persistence for failed or partial chapters

Two capabilities are still missing:

1. long-range continuity evaluation across the whole story
2. drafting-specific consolidation for manuscript-ready chapter packets and draft briefs

## Long-Range Continuity

### Problem

The current pipeline reasons locally at chapter scope. It can synthesize chapter planning, but it does not yet prove that the whole story remains coherent when viewed as a complete timeline.

What is missing:

- character state progression across chapter boundaries
- unresolved-thread lifecycle tracking
- continuity drift detection for characters, locations, objects, and chronology
- global contradiction reporting
- chapter-order validation against narrative dependencies

### Required Outcome

After import, the system should be able to answer:

- which character state changed, where, and why
- which unresolved threads were introduced, carried, or closed
- whether any chapter introduces a contradiction with earlier evidence
- whether sequence and chapter ordering preserve continuity assumptions
- whether a chapter should be marked `continuity_warning`, `partial_import`, or `analysis_failed`

### Recommended Data Model

Add continuity-oriented artifacts that are separate from planning artifacts:

- `chapter_continuity_snapshots`
- `continuity_threads`
- `continuity_findings`
- `character_state_timelines`

Each record should store:

- `project_id`
- source chapter or chapter packet reference
- entity or thread identifier
- `summary`
- `status`
- `provenance_note`
- `confidence_score`
- timestamps

### Required Pipeline Stage

Add a new import phase after planning synthesis:

1. structure detection
2. chapter analysis
3. character consolidation
4. world consolidation
5. arc detection
6. planning synthesis
7. continuity consolidation

This new phase should consume the full ordered chapter set and emit continuity findings and state snapshots.

### Continuity Gates

The pipeline should warn or degrade when:

- a character changes state without supporting evidence
- an unresolved thread disappears without closure or explicit abandonment
- a location or object changes in a way that conflicts with earlier chapters
- chronology breaks the sequence inferred from structure detection
- a chapter only contains weak or partial evidence but is treated as fully continuous

## Drafting Consolidation

### Problem

Planning synthesis still stops short of manuscript-readiness. The importer can create planning scaffolding, but not reliable writing briefs for chapter drafting.

### Required Outcome

After import, the system should be able to produce drafting-ready artifacts that answer:

- what each chapter must achieve emotionally and structurally
- which continuity obligations the writer must respect
- which callbacks or payoffs must be preserved
- what voice, POV, and tone guidance should carry forward
- what content should not be contradicted during drafting

### Recommended Data Model

Add drafting-oriented artifacts separate from planning artifacts:

- `draft_briefs`
- `drafting_context_packets`
- `imported_draft_readiness_reports`

Each record should store:

- `project_id`
- `chapter_id`
- `sequence_id`
- `summary`
- `objective`
- `emotional_turn`
- `continuity_obligations`
- `required_callbacks`
- `forbidden_contradictions`
- `voice_guidance`
- `provenance_note`
- `confidence_score`
- timestamps

### Required Pipeline Stage

Add a drafting-specific consolidation phase after continuity consolidation:

1. structure detection
2. chapter analysis
3. character consolidation
4. world consolidation
5. arc detection
6. planning synthesis
7. continuity consolidation
8. drafting consolidation

This phase should create writer-facing chapter briefs and only then allow draft artifact creation.

### Drafting Gates

The pipeline should refuse or downgrade draft artifacts when:

- continuity confidence is below threshold
- chapter evidence is incomplete
- a chapter has unresolved contradictions
- POV or voice is not stable enough to carry into drafting
- chapter-level planning is missing or degraded beyond a safe threshold

## Implementation Principles

1. Keep the phases deterministic.
The model may synthesize structure, but the importer should normalize and validate output before persistence.

2. Preserve uncertainty.
Use explicit degraded statuses rather than pretending weak evidence is trustworthy.

3. Separate planning from drafting.
Planning artifacts are not draft artifacts. Drafting requires a stricter contract.

4. Track provenance everywhere.
Every imported artifact should be attributable to direct evidence, partial evidence, or fallback synthesis.

5. Fail at the gate that owns the invariant.
If continuity is broken, stop at continuity consolidation. Do not bury the issue in drafting.

## Files Likely to Change

- [app/services/multi_pass_import.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/services/multi_pass_import.py)
- [app/services/story_import.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/services/story_import.py)
- [app/services/runtime_prompts.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/services/runtime_prompts.py)
- [app/schemas/story_import.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/schemas/story_import.py)
- [app/schemas/story_development.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/schemas/story_development.py)
- [app/persistence/sqlite.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/persistence/sqlite.py)
- [app/persistence/story_development.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/persistence/story_development.py)
- [app/services/planning.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/services/planning.py)
- [app/services/chapter_packets.py](/C:/Users/SLuh/Documents/Dev/Narrative-Engine/app/services/chapter_packets.py)
- frontend planning/review views if continuity findings or draft briefs are surfaced in the UI

## Validation Targets

Use targeted tests that prove each new phase owns its invariant:

- continuity snapshot persistence
- continuity warning generation
- continuity failure does not create draft briefs
- draft brief creation from continuity-approved input
- idempotent retries for continuity and drafting artifacts
- repository round-trip coverage for any new persistence rows

## Scope Boundary

This spec does not change the current import contract.
It only defines the remaining work needed to extend the import pipeline from planning-grade digestion to continuity-verified and drafting-ready digestion.
