# Story Import Capability Hardening v0.1

## Current Findings

The current story import pipeline is sufficient for coarse metadata extraction, but not for the "full breakdown to components" implied by the product language.

Observed limits in the current code path:

1. Single-pass import is inherently partial.
   - `build_import_analysis_request()` truncates to the first 24k characters.
   - This is enough for short stories, not for novel-scale whole-story extraction.

2. Single-pass output burden is too large for one structured response.
   - The prompt asks for foundation, all characters, world bible, arcs, sequences, constraints, and validation-grade JSON in one pass.
   - This produces useful summaries, but not reliable exhaustive decomposition.

3. Multi-pass import originally had chapter-level understanding but discarded most of it at the final contract boundary.
   - Per-chunk analysis captured chapter summaries, plot events, and character appearances.
   - The hardening work in this pass now preserves chapter summaries and builds deterministic planning artifacts from them.

4. Story import still stops short of true draft-ready decomposition.
   - Story import wrote foundation, characters, world bible, and arcs.
   - This pass now writes deterministic `sequence_plans`, `chapter_plans`, `scene_plans`, `beat_plans`, `chapter_packets`, and planning dependencies.
   - It still does not create draft artifacts or manuscript documents.

5. The UI copy overstates current capability.
   - The app claims import creates a full project with planning and drafts.
   - The backend now persists planning artifacts, but draft generation still belongs to the drafting workflow.

## Recommendations

1. Treat story import as a staged extraction pipeline, not a one-shot full decomposition.
2. Preserve chapter-level intermediate outputs as first-class internal contracts.
3. Persist deterministic planning artifacts when the extraction confidence is high enough.
4. Keep imported scene/beat synthesis explicitly marked as imported scaffolding, not authored draft output.
5. Update product copy and backend docs so "full breakdown" means:
   - imported foundation
   - imported characters
   - imported world bible
   - imported arcs
   - imported sequence plans
   - imported chapter plans
   - imported scene plans
   - imported beat plans
   - imported chapter packets and planning dependencies
   - not yet imported draft artifacts or manuscript documents

## This Implementation Pass

This pass hardens the backend in the smallest high-leverage way:

1. Add `chapter_summaries` to the internal `StoryImportAnalysis` contract.
2. Preserve multi-pass chapter summaries, active characters, unresolved questions, and estimated word counts.
3. Build real sequence groupings from detected structure instead of always emitting one synthetic shell.
4. Persist `sequence_plans`, `chapter_plans`, `scene_plans`, `beat_plans`, `chapter_packets`, and planning dependencies transactionally during story import.
5. Keep IDs deterministic and project-scoped.
6. Synthesize chapter summaries from single-pass sequence output when multi-pass chapter summaries are unavailable.

## Deferred Work

1. Single-pass chapter decomposition still remains shallow.
2. Imported scene and beat artifacts are deterministic scaffolding, not evidence of full narrative understanding.
3. The prompts still need compression and redistribution across more specialized passes.
4. Long-range continuity for very large casts still needs stronger carry-forward context than the current 5k prior-character cap.
5. Draft artifact and manuscript creation are still outside the import pipeline.

## Atomic Next Tasks

1. Add a dedicated planning-consolidation pass that can refine imported scene/beat scaffolding before drafting begins.
2. Improve multi-pass carry-forward context for large casts, recurring locations, and unresolved threads.
3. Split the single-pass prompt into narrower extraction contracts or retire single-pass for long-form prose entirely.
4. Decide whether import should ever create draft artifacts automatically, or whether drafting must remain an explicit downstream step.
5. Keep frontend copy aligned with the backend contract as import capabilities expand.
