# Story Import Battle Hardening - 2026-04-30

## Problems

1. The import transaction bypasses normal SQLite connection configuration.
   - `StoryImportService._transactional_import()` opens a raw `sqlite3.connect(...)` connection and does not enable `PRAGMA foreign_keys = ON`.
   - This masks invalid parent/child insert ordering in the new planning persistence path.

2. Planning inserts are not parent-first.
   - `chapter_plans.sequence_id` references `sequence_plans.sequence_id`.
   - The current code inserts `chapter_plans` before `sequence_plans`, which is only succeeding because FK enforcement is currently off on that connection.

3. Partial multi-pass failures are being converted into plausible-looking fabricated planning artifacts.
   - If a chapter has no successful chunk analyses, the code still synthesizes a chapter summary shell and then fabricates a fallback plot event.
   - This produces scenes, beats, packets, and dependencies for chapters that were never actually analyzed.

4. Progress accounting mixes chapter progress with chunk progress.
   - Multi-pass import increments `chapters_processed` for each successful chunk while `total_estimated_chapters` is still chapter-based.
   - The UI can therefore exceed 100% progress when chapters are sub-chunked.

5. Final multi-pass chapter counts are derived from the first sequence only.
   - After sequence grouping became multi-sequence aware, `len(analysis.sequences[0].chapters)` undercounts total processed chapters for stories with more than one sequence.

## Recommendations

1. Enforce the same DB integrity rules in import that the rest of the repository uses.
   - Enable foreign keys explicitly on the raw import connection.
   - Keep raw-SQL atomic import if desired, but do not allow it to run in a weaker integrity mode.

2. Insert planning artifacts in parent-first order.
   - Create or upsert `sequence_plans` before any `chapter_plans` that reference them.
   - Then insert `chapter_plans`, `scene_plans`, `beat_plans`, `chapter_packets`, and dependencies.
   - Update aggregate JSON fields such as `beat_ids_json` and `chapter_ids_json` after child IDs are known.

3. Represent uncertainty explicitly instead of fabricating full structure.
   - Chapters with zero successful chunk analyses should not emit downstream planning artifacts.
   - Persist a chapter shell only if useful, and mark it with an explicit degraded status such as `analysis_failed`.
   - Chapters with some but not all chunk analyses should be marked `partial_import`.

4. Separate chapter progress from chunk progress.
   - Keep `chapters_processed` bounded by `total_estimated_chapters`.
   - Add chunk-level counters for internal visibility and diagnostics.
   - Base the final completed chapter count on chapter summaries or detected structure, not the first sequence.

5. Add regression tests for integrity and degraded import paths.
   - Validate parent-first planning persistence under FK enforcement.
   - Validate that failed chapter analysis does not create fabricated scenes/beats/packets.
   - Validate bounded chapter progress and accurate final totals.

## Fixes In This Pass

This hardening pass implements:

1. Enable FK enforcement on the raw import transaction.
2. Reorder planning persistence so sequence rows exist before chapter rows reference them.
3. Add explicit chapter analysis status to the internal import contract.
4. Prevent downstream scene/beat/packet fabrication for unanalyzed chapters.
5. Report chapter progress by chapter and chunk progress by chunk.
6. Correct final multi-pass chapter totals to reflect all chapters, not only the first sequence.

## Validation

1. Backend: `python -m pytest tests/test_json_extract.py tests/test_import_jobs.py tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider`
   - Result: `131 passed`

2. Frontend: `cd frontend && npm run typecheck`
   - Result: passed

3. Frontend: `cd frontend && npm run test`
   - Result: `35` files passed, `286` tests passed

4. Frontend: `cd frontend && npm run build`
   - Result: passed
