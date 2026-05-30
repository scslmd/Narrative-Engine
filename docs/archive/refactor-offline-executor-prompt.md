# Offline Executor Prompt: God-File Refactor (Test-Verified Slices)

You are a senior refactoring agent working in the repository root `Narrative-Engine` on branch `refactor/god-files-final-pass`.

Objective:
Refactor remaining backend god files into smaller, logical modules using slow, test-verified slices. Preserve behavior exactly. No feature additions.

Critical target files:
1. `app/persistence/story_development/__init__.py`  (~4884 lines)
2. `app/api/story_development/__init__.py`          (~3070 lines)
3. `app/services/local_executor/__init__.py`        (~2578 lines)
4. `app/services/runtime_prompts/__init__.py`       (~2016 lines)

Already extracted modules exist; extend them incrementally instead of rewriting from scratch.

Non-negotiable rules:
- Do not change public API behavior, endpoint contracts, schemas, or output formats.
- Prefer extraction + re-export pattern: move code to new module, import back into original module.
- Keep compatibility for all existing imports.
- One small slice per commit-sized change.
- Run tests after every slice before continuing.
- If tests fail, stop, fix, and re-run before any new extraction.
- No speculative cleanup. No new features.

Process for each slice:
1. Read target file and map cohesive blocks by responsibility.
2. Extract only one cohesive block (models/helpers/converters/domain routes/builders).
3. Create new module file with identical logic.
4. Replace original block with imports from the new module.
5. Ensure underscore/private symbol behavior is preserved (if using `import *`, define `__all__` as needed).
6. Run targeted tests.
7. If green, continue to next slice.

Testing protocol (must follow):
- Persistence/API slice checks:
  - `python -m pytest -n 0 tests/test_story_development_persistence.py tests/test_story_development_repository_contracts.py`
  - `python -m pytest -n 0 tests/test_story_development_api.py tests/test_discovery_api.py::test_patch_returns_updated`
- Runtime prompts slice checks:
  - `python -m pytest -n 0 tests/test_p100_prompt_content.py tests/test_critic_prompt_content.py tests/test_prompt_caching.py tests/test_runtime_error_mapping_failures.py`
- Local executor slice checks:
  - `python -m pytest -n 0 tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters`
  - plus related executor tests discovered by grep in tests/
- Final full verification at end:
  - `python -m pytest -q -p no:cacheprovider -n auto --dist=loadfile --basetemp=.tmp_xdist --ignore=tests/test_audit_logging.py --ignore=tests/test_rate_limiting.py --ignore=tests/test_smoke.py --ignore=tests/test_local_executor_manuscript_assist.py --ignore=tests/test_story_generation_e2e.py`
  - `python -m pytest -q -p no:cacheprovider -n 0 tests/test_audit_logging.py tests/test_rate_limiting.py tests/test_persistence.py::test_local_executor_persists_pipeline_step_records tests/test_smoke.py tests/test_local_executor_manuscript_assist.py tests/test_story_generation_e2e.py tests/test_local_executor_drafter_runtime.py::test_multi_chapter_pipeline_generates_sequential_chapters tests/test_discovery_api.py::test_patch_returns_updated tests/test_story_bible_lineage.py::TestStoryBibleLineageContentHash::test_story_bible_content_hash_matches_file_content`

Refactor order:
1) `app/api/story_development/__init__.py`
   - Continue extracting request/response model groups into dedicated modules (`common_models.py`, `planning_models.py`, `branch_models.py`, etc.)
   - Then extract router domain blocks to per-domain route modules while keeping `build_story_development_router` stable.
2) `app/persistence/story_development/__init__.py`
   - Continue extracting cohesive conversion/record/query helper groups into modules.
   - Preserve symbol availability and import order safety.
3) `app/services/runtime_prompts/__init__.py`
   - Extract large builder families to modules (`narrative_analysis.py`, `planning_prompts.py`, `drafting_prompts.py`, etc.).
   - Preserve exact prompt strings and metadata payloads.
4) `app/services/local_executor/__init__.py`
   - Extract phase handlers/helpers into modules (`types/helpers/phase runners/state transitions`) with no behavior drift.

Output requirements after each slice:
- List files changed.
- State what responsibility was extracted.
- Show tests run and pass/fail.
- Show current line counts for the 4 target files.

Stop condition:
All 4 target files are decomposed into logical modules, core behavior preserved, and full verification passes.

