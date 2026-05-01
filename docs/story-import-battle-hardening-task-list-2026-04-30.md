# Story Import Battle Hardening Task List - 2026-04-30

## Execution Checklist

- [x] Document the hardening problems, recommendations, and intended fixes.
- [x] Enable FK enforcement on the raw import transaction.
- [x] Reorder planning persistence to insert `sequence_plans` before dependent `chapter_plans`.
- [x] Add explicit internal chapter analysis status for `complete`, `partial_import`, and `analysis_failed`.
- [x] Prevent unanalyzed chapters from emitting fabricated scenes, beats, chapter packets, and dependencies.
- [x] Keep chapter progress bounded by total chapters and add chunk-level counters for diagnostics.
- [x] Correct final multi-pass chapter totals to count all imported chapters.
- [x] Extend backend tests for FK-safe planning persistence, degraded chapter analysis, and progress accounting.
- [x] Run focused backend validation.

## Notes

- This file is the interruption-safe checklist for the battle-hardening pass.
- Checkboxes should be marked only after code and focused validation both pass.
- Validation completed with:
  - `python -m pytest tests/test_json_extract.py tests/test_import_jobs.py tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider` -> `131 passed`
  - `cd frontend && npm run typecheck` -> passed
  - `cd frontend && npm run test` -> `286 passed`
  - `cd frontend && npm run build` -> passed
