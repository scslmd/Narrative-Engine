# Story Import Full Digestion Hardening

Date: 2026-04-30

## Problems

1. Single-pass import was overclaiming capability.
It accepted a short leading slice of the story and still attempted to imply planning-grade structure from that partial context.

2. Multi-pass import had no dedicated planning synthesis phase.
Chapter analysis, character/world consolidation, and arc detection existed, but sequence and chapter planning were still being derived by thin fallback logic instead of an explicit planning contract.

3. Planning artifacts had no trust metadata.
Persisted sequence, chapter, scene, beat, and packet rows carried status only, which made it impossible to distinguish direct chapter evidence from structural fallback.

4. Semantic gates were too weak.
The pipeline could accept sparse or malformed planning groupings and still persist them as if they were equally trustworthy.

5. Single-pass sequence payloads could fabricate downstream planning artifacts.
If the model returned high-level sequences without chapter evidence, the importer synthesized chapter/scene/beat scaffolding anyway.

## Recommendations

1. Split single-pass import into a high-level contract only.
Single-pass should extract foundation, characters, world, arcs, and optional coarse sequences. It should not claim chapter, scene, or beat coverage.

2. Add a dedicated planning-synthesis phase after multi-pass chapter analysis.
This phase should consume detected structure, chapter summaries, arcs, and character roster, then synthesize reliable sequence grouping and chapter planning summaries.

3. Persist provenance and confidence for imported planning artifacts.
Every imported planning artifact should carry both a provenance note and a confidence score.

4. Add deterministic semantic gates before persistence.
Planning synthesis should be normalized before persistence so every chapter is assigned at most once, no unknown chapter IDs survive, and failed evidence is not silently upgraded.

5. Preserve degraded states explicitly.
`analysis_failed` and `partial_import` chapters should remain degraded all the way into persistence and child artifact generation.

## Implemented Fixes

### Contract split

- `build_import_analysis_request()` was narrowed to a high-level single-pass contract.
- Single-pass prompt instructions now explicitly forbid fabricated chapter-level planning.
- Single-pass imports no longer synthesize chapter, scene, beat, or packet artifacts from coarse sequence labels.

### Multi-pass planning synthesis

- Added `StoryImportPlanningSynthesis` to the story-import schema layer.
- Added `build_planning_consolidation_request()` in the runtime prompt layer.
- Multi-pass import now runs a dedicated planning synthesis phase after arc detection.
- Planning synthesis output is normalized against fallback structure before persistence.

### Semantic gates

- Chapter-level success now requires usable evidence, not just parseable JSON.
- Planning synthesis now normalizes chapter assignments, removes unknown chapter IDs, fills missing chapters from deterministic fallback, and preserves degraded chapter statuses.
- Failed chapters continue to persist only as degraded shells without fabricated downstream planning artifacts.

### Provenance and confidence

- Added `provenance_note` and `confidence_score` to:
  - story-import sequence/chapter schema objects
  - `sequence_plans`
  - `chapter_plans`
  - `scene_plans`
  - `beat_plans`
  - `chapter_packets`
- Added additive SQLite migrations for those planning columns.
- Repository row mapping and planning service projections now preserve those values.

## Validation

- `python -m pytest tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`
- `python -m pytest tests/test_story_development_persistence.py tests/test_planning_service.py -q -p no:cacheprovider`
- `python -m pytest tests/test_import_jobs.py tests/test_json_extract.py -q -p no:cacheprovider`

## Current Truth

The import pipeline is now more honest and more reliable:

- single-pass import is high-level only
- multi-pass import owns planning synthesis
- planning artifacts now carry trust metadata
- degraded evidence remains degraded

This still does not mean the app can author a fully trustworthy manuscript from any arbitrary novel input. It means the import path now behaves like a staged evidence pipeline instead of a best-effort planner pretending to be exhaustive.
