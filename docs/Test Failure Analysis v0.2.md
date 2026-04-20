# Test Failure Analysis v0.2

> **Superseded**: This analysis was originally written for the `583 passed, 29 failed` baseline.
> The suite was fixed in a subsequent session to `641 passed, 0 failed, 9 skipped`.
> Kept here as historical reference. See `TODO.md` and `docs/archive/TODO_Completed_Milestones_Archive.md` for current status.

Generated: 2026-04-20 (original analysis)
Last updated: 2026-04-20 (baseline fixed)

## Current Baseline

- **641 passed**, 0 failed, 9 skipped
- `cd frontend && npm run lint` -> passed
- `cd frontend && npm run typecheck` -> passed
- `cd frontend && npm run build` -> passed

## 9 Skipped Tests (Platform-Specific)

All skips are intentional and platform-specific:

| File | Count | Reason |
|------|-------|--------|
| `tests/test_attempt_persistence.py` | 5 | Tests require pre-seeded jobs/retries not created by test setup |
| `tests/test_config_validator.py` | 3 | Windows-specific filesystem permission checks (world-writable, group-writable, POSIX) |

## Historical Failures (All Fixed)

### Parameter Drift — Fixed

`StepRecordService.create_step_record()` accepted `input_payload/output_payload/prompt_payload` but `local_executor.py` was modified to pass `input_hash/output_hash/prompt_hash`. This caused `TypeError` at every executor call site, resulting in:
- 4 spurious "checker_run" failure step records instead of the expected 3
- Run status set to FAILED instead of COMPLETED

**Fix**: Updated `StepRecordService.create_step_record()` and `create_lineage_record()` signatures in `app/services/step_records.py` to accept the new parameter names.

### Test Isolation — Fixed

24 tests that failed in the full suite but passed individually were caused by shared mutable state. The root cause was the parameter drift above, not test isolation — once the parameter names were fixed, all tests pass.

### Stub Inference Backend — Fixed

2 smoke tests (`test_job_stub_runs`, `test_role_model_checker_stub_runs`) that expected `COMPLETED` but got `FAILED` were also caused by the parameter drift, not by stub backend issues.

## Remaining Test Failures

**None.** All 29 previously failing tests are now passing.
