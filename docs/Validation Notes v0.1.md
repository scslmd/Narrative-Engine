# Validation Notes v0.1

Quick checks:

1. Create a Python 3.12 virtual environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Run `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q`.
4. Launch the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
5. Open `http://127.0.0.1:8000/role-model-checker-ui`.

Current validation covers:

- FastAPI app boot and public endpoint surface
- sample project listing and detail access
- workflow preference and model catalog responses
- job and checker contracts with `202 Accepted` plus polling
- local lease-claim execution and stale-lease reclaim coverage for accepted jobs and checker runs
- attempt-level executor telemetry for executor name, executor identity, queue delay, finish reasons, and reclaim context
- persisted checker report creation
- persistence for jobs, checker runs, and project projections
- request snapshots and append-only event history
- first-class attempt persistence on runs and events
- idempotency-key replay and conflict handling for enqueue endpoints
- explicit operator retry flow that requeues failed runs onto a new attempt number
- step-record and artifact-lineage contract fixture coverage for required fields and lineage rules
- live step-record and artifact-lineage persistence in SQLite, including executor-written rows and lineage FK behavior
- generalized inference-provider wiring for `llama.cpp`, LM Studio, `vLLM`, and other OpenAI-compatible runtimes
- the first real provider-backed `architect` execution path for phase `P-100`, including canonical markdown output, canonical artifact registration, and artifact lineage
- SQLite pragma, index, and foreign-key behavior
- explicit project reconciliation behavior
- deterministic rejection of illegal run-state transitions
- deterministic checker partial-persistence failure handling after result insertion
- deterministic enqueue-time SQLite lock-contention failures with no partial rows for jobs and checker runs

Current validation does not yet cover:

- runtime-backed execution for phases beyond `P-100`
- orchestrator/compiler behavior
- production-grade checker scoring
- broader browser workflow coverage
- storage contention classification as retryable runtime failure
- concurrent claim races under real parallel workers
- projection endpoints for step records and artifact lineage

Current verified result:

- `.\.venv\Scripts\python.exe -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q`
- Result: `67 passed`

Continuous testing:

- GitHub Actions workflow: `.github/workflows/tests.yml`
- Triggered on `push`, `pull_request`, and manual dispatch
- Matrix:
  - `ubuntu-latest` with Python `3.12`
  - `windows-latest` with Python `3.12`
- CI command:
  - `python -m pytest tests/test_inference_runtime.py tests/test_inference_backend_failures.py tests/test_smoke.py tests/test_local_executor_architect_runtime.py tests/test_persistence.py tests/test_failure_modes.py tests/test_attempt_lineage.py tests/test_step_record_spec.py tests/test_step_record_persistence.py -q -p no:cacheprovider`
