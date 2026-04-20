# Test Failure Analysis v0.1

Generated: 2026-04-20

## Executive Summary

After implementing persistence expansion (artifact lineage project-scoped queries, step record service wrappers, chapter packet / sequence plan / storyboard card services, and manuscript-aid contract tests), the full test suite shows:

- **583 passed** (baseline: 572, +11 from current session)
- **29 failed** (pre-existing issues)
- **9 skipped**

All **17 new tests pass** with zero regressions.

---

## 1. Root Cause: StepRecordService / local_executor.py Parameter Drift

The working directory contained pending changes to `app/services/local_executor.py` that changed how step records and lineage records are created, but `StepRecordService` was never updated to match.

### 1.1 Before (old service signature)

`local_executor.py` passed:
```python
input_payload=input_payload, output_payload=output_payload, prompt_payload=prompt_payload
content_hash_source=content_hash_source
```

`StepRecordService.create_step_record()` accepted `input_payload`, `output_payload`, `prompt_payload` and internally converted them via `stable_hash_payload()`.

### 1.2 After (local_executor.py changes)

`local_executor.py` was modified to pass:
```python
input_hash=stable_hash_payload(input_payload) if input_payload else None,
output_hash=stable_hash_payload(output_payload) if output_payload else None,
prompt_hash=stable_hash_payload(prompt_payload) if prompt_payload else None,
created_at=started_at,
updated_at=finished_at,
```

And for lineage:
```python
content_hash=content_hash_source,  # was content_hash_source=...
```

### 1.3 Impact

Every call site that invoked `StepRecordService.create_step_record()` or `create_lineage_record()` from the executor failed with `TypeError: unexpected keyword argument`.

### 1.4 Fix Applied

Updated `StepRecordService.create_step_record()` in `app/services/step_records.py`:
- Changed parameter names: `input_payload` → `input_hash`, `output_payload` → `output_hash`, `prompt_payload` → `prompt_hash`
- Added `created_at: datetime | None = None`, `updated_at: datetime | None = None` parameters
- Internal hash conversion removed (executor now passes pre-computed hashes)

Updated `StepRecordService.create_lineage_record()`:
- Changed parameter name: `content_hash_source` → `content_hash`
- Internal hash conversion removed (executor now passes pre-computed hash)

---

## 2. Category: Test Isolation / Shared State Pollution

### Affected Tests (24 tests)

| File | Count | Pattern |
|------|-------|---------|
| `test_local_executor_architect_runtime.py` | 2 | `P-100` jobs expect `COMPLETED`, get `FAILED` |
| `test_local_executor_compiler_runtime.py` | 8 | `P-100`/`P-400` jobs expect `COMPLETED`, get `FAILED` |
| `test_local_executor_drafter_runtime.py` | 2 | `P-100` → `P-300` chain expects `COMPLETED`, gets `FAILED` |
| `test_local_executor_sequencer_runtime.py` | 2 | `P-100` → `P-200` chain expects `COMPLETED`, gets `FAILED` |
| `test_smoke.py` | 2 | Stub jobs expect `COMPLETED`, get `FAILED` |
| `test_runtime_error_mapping_failures.py` | 3 | Parametrized, expect `COMPLETED`, get `FAILED` |
| `test_projection_runtime_failure_modes.py` | 4 | Lineage projection tests fail |
| `test_persistence.py` | 4 | Lineage supersession tests fail |
| `test_failure_modes.py` | 1 | Job start endpoint test fails |

### Symptoms

- All 24 tests **pass when run individually** (e.g., `pytest test_file.py::test_name`)
- All 24 tests **fail when run together** in the full suite (`python -m pytest`)
- All expect `status == "COMPLETED"` but receive `status == "FAILED"`

### Diagnosis

This pattern indicates shared mutable state (likely a database file or in-memory cache) that:
1. Tests overwrite or corrupt during execution
2. Subsequent tests read corrupted state and fail

Likely culprits:
- A shared SQLite database path (`narrative_ops.db`) used across tests without proper isolation
- A shared `LocalExecutor` singleton or module-level state
- A shared inference backend or fake backend that accumulates state

### Not Yet Fixed

Requires investigation into test fixture setup and shared resource cleanup.

---

## 3. Category: Stub Inference Backend Failures

### Affected Tests (2 tests)

| Test | File |
|------|------|
| `test_job_stub_runs` | `test_smoke.py` |
| `test_role_model_checker_stub_runs` | `test_smoke.py` |

### Symptoms

- Both tests use stub inference backends (`FakeArchitectInferenceBackend`, `FakePipelineInferenceBackend`)
- Jobs complete with `FAILED` status instead of `COMPLETED`
- When run individually, `test_job_stub_runs` **passes**
- When run in the full suite, it **fails**

### Likely Cause

Part of the shared state pollution pattern (Category 2), since `test_job_stub_runs` passes individually but fails in the suite.

---

## 4. Category: Resolved Parameter Mismatch (Fixed in Session)

### Before Fix

Error:
```
StepRecordService.create_step_record() got an unexpected keyword argument 'input_hash'
```

Affected tests (no longer fail after fix):
- `test_runtime_backed_p100_lineage_failure_does_not_emit_canonical_lineage_success`
- `test_projection_endpoints_remain_read_only_when_projection_read_fails`
- `test_job_lineage_persistence_under_lock_leaves_job_state_non_corrupt`
- `test_checker_lineage_persistence_under_lock_leaves_job_state_non_corrupt`

### Fix

Updated `StepRecordService` signatures in `app/services/step_records.py` to accept the new parameter names used by `local_executor.py`.

---

## 5. Files Modified During Fix

| File | Change |
|------|--------|
| `app/services/step_records.py` | Updated `create_step_record()` and `create_lineage_record()` signatures |
| `tests/test_orchestration_integration.py` | Added `_seed_project()` with full columns, created prerequisite FK records |
| `tests/test_manuscript_aid_contracts.py` | Replaced `register_manuscript_document` with `save_manuscript_document`, added project seeding |
| `app/services/storyboard_cards.py` | Removed `column_id` from `update_card_content()` signature |

---

## 6. New Tests Added (All Pass)

| Test File | Count |
|-----------|-------|
| `tests/test_orchestration_integration.py` | 7 |
| `tests/test_manuscript_aid_contracts.py` | 10 |
| **Total** | **17** |

### Test Coverage

- Step record + artifact lineage lifecycle and project-scoped queries
- Canonical supersession behavior
- Runtime artifact selections project-scoped queries
- ChapterPacketService with repository
- SequencePlanService with repository
- StoryboardCardService with repository
- DraftingService integration
- Revision suggestion validation, storage, listing, get-by-id, idempotency
- Diff payload contract (source/proposed text, context)
- Status transitions (REQUESTED → ACCEPTED → REJECTED)

---

## 7. Verification Commands

```bash
# New tests only
python -m pytest tests/test_orchestration_integration.py tests/test_manuscript_aid_contracts.py -v

# Full suite (29 pre-existing failures expected)
python -m pytest -q -p no:cacheprovider

# Individual test (proves isolation issue)
python -m pytest tests/test_smoke.py::test_job_stub_runs -v
```
