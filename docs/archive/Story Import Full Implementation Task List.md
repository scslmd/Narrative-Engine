# Story Import Full Implementation Task List

## Execution Checklist

- [x] Document capability gap between current prompts/context size and claimed full story decomposition.
- [x] Preserve chapter-level multi-pass import outputs in the backend contract.
- [x] Persist imported `sequence_plans`.
- [x] Persist imported `chapter_plans`.
- [x] Persist imported `scene_plans`.
- [x] Persist imported `beat_plans`.
- [x] Persist imported `chapter_packets`.
- [x] Persist deterministic planning dependencies for imported structure.
- [x] Extend tests to cover scene/beat/packet/dependency persistence.
- [x] Re-run focused backend import validation.
- [x] Re-run broader story import validation.

## Notes

- This file is intended as an interruption-safe execution log.
- Tasks should be checked only after code and focused validation both land.
- Broader validation completed with `python -m pytest tests/test_json_extract.py tests/test_import_jobs.py tests/test_story_import_service.py tests/test_multi_pass_import.py -q -p no:cacheprovider` -> `129 passed`.
