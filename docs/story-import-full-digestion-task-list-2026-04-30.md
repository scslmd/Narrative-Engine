# Story Import Full Digestion Task List

Date: 2026-04-30

## Completed Tasks

- [x] Inspect current story-import schemas, prompts, persistence tables, and planning services.
- [x] Identify where single-pass import was overclaiming planning coverage.
- [x] Narrow the single-pass prompt contract to high-level import only.
- [x] Prevent single-pass imports from fabricating chapter/scene/beat scaffolding from coarse sequence labels.
- [x] Add an explicit planning-synthesis schema for multi-pass import.
- [x] Add a dedicated planning-synthesis runtime prompt builder.
- [x] Run multi-pass planning synthesis after chapter analysis, character consolidation, world consolidation, and arc detection.
- [x] Normalize synthesized planning output against deterministic fallback structure.
- [x] Add semantic validation so sequence chapter assignments cannot contain unknown or duplicate chapter IDs.
- [x] Preserve `analysis_failed` and `partial_import` states through planning persistence.
- [x] Add provenance and confidence fields to story-import sequence and chapter schema objects.
- [x] Add provenance and confidence columns to persisted planning tables.
- [x] Add additive SQLite migration coverage for the new planning metadata columns.
- [x] Update repository row mappers and planning service projections to preserve the new metadata.
- [x] Update import-path tests to reflect the new single-pass and multi-pass contracts.
- [x] Validate story-import, planning, persistence, and supporting import subsets.

## Deterministic Follow-Up Tasks

- [x] Verify single-pass imports persist high-level sequences only when present.
- [x] Verify multi-pass imports persist planning artifacts with provenance metadata.
- [x] Verify degraded chapters do not emit fabricated downstream planning artifacts.
- [x] Verify repository round trips still work after planning metadata schema expansion.

## Remaining Strategic Work

- [ ] Add long-range cross-chapter continuity evaluation beyond chapter-local planning synthesis.
- [ ] Add a drafting-specific consolidation phase if manuscript-grade artifact creation is required from imports.
- [ ] Replace in-memory import job state with durable persistence if restart-safe import tracking is required.
