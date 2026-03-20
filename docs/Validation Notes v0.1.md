# Validation Notes v0.1

Quick checks:

1. Create a Python 3.12 virtual environment in this folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Run `python -m pytest tests/test_smoke.py tests/test_persistence.py -q`.
4. Launch the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
5. Open `http://127.0.0.1:8000/role-model-checker-ui`.

Current validation covers:

- FastAPI app boot and public endpoint surface
- sample project listing and detail access
- workflow preference and model catalog responses
- job and checker contracts with `202 Accepted` plus polling
- persisted checker report creation
- persistence for jobs, checker runs, and project projections
- request snapshots and append-only event history
- baseline attempt-lineage fields on runs and events
- SQLite pragma, index, and foreign-key behavior
- explicit project reconciliation behavior
- deterministic rejection of illegal run-state transitions

Current validation does not yet cover:

- real model inference execution
- worker or lease-based async execution
- orchestrator/compiler behavior
- production-grade checker scoring
- broader browser workflow coverage
- duplicate submission and storage contention handling

Current verified result:

- `python -m pytest tests/test_smoke.py tests/test_persistence.py -q`
- Result: `17 passed`
