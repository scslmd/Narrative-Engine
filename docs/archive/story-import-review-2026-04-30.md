# Story Import Review - 2026-04-30

## Findings

1. Multi-pass consolidation accepted valid top-level JSON arrays from prompts, but the shared extractor rejected any top-level value that was not an object. Character and world consolidation therefore fell back every time.
2. Import jobs could return a `StoryImportResponse(status="failed")` while the job manager still marked the overall job as `completed`.
3. Stable import IDs for characters and arcs were keyed only by entity name, so identical names in different projects could overwrite each other.
4. `StoryImportRequest` required `project_name` even when `project_id` was supplied, which blocked the existing-project import path if the caller omitted the name.
5. API-key middleware protected `POST /projects/import-story` but not `GET /projects/import/{import_id}`.
6. Manifest updates rebuilt the project path manually instead of using the project service's path abstraction.

## Atomic Deterministic Tasks

1. Update `app/utils/json_extract.py` so `extract_json()` accepts any valid top-level JSON value and can recover fenced or embedded arrays as well as objects.
2. Keep `StoryImportService._parse_llm_json()` strict by validating that single-pass analysis still receives a JSON object before schema validation.
3. Update `app/services/import_jobs.py` so a returned `StoryImportResponse(status="failed")` marks the job itself as failed and surfaces the message in `error`.
4. Scope story-import-generated character and arc IDs by `project_id` while preserving deterministic retry behavior within the same project.
5. Relax `StoryImportRequest` validation so callers may omit `project_name` when `project_id` is present, but still reject requests that provide neither.
6. Extend the API-key gate in `app/main.py` to also protect `/projects/import/{import_id}`.
7. Change `StoryImportService._update_manifest()` to resolve the project directory through `ProjectService.projects_dir`.

## Secondary Improvements

1. Remove duplicate single-pass truncation so prompt-size control lives in one layer.
2. Consider removing the unused `story_text` positional argument from `ImportJobManager.submit()` in a follow-up patch.
3. Consider consolidating manifest update behavior onto `app/utils/manifest.py` if story-import, mythos, and pattern extraction should share one write path.
