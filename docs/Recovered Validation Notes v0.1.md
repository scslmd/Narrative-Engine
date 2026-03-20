Recovered Validation Notes v0.2

Quick checks:
1. Create a Python 3.12 virtual environment in this recovered folder.
2. Install dependencies with `pip install -e .[dev]`.
3. Run `python -m pytest tests/test_recovered_smoke.py tests/test_persistence.py -q`.
4. Launch the app with `start_narrative_core.cmd` or `start_narrative_core.ps1`.
5. Open `http://127.0.0.1:8000/role-model-checker-ui`.

Current status:
- This recovered tree is a safe reconstruction baseline.
- It is not a byte-perfect restore of the lost D: repository.
- The backend now has SQLite-backed persistence for jobs, checker runs, and project artifact registration.
- The SQLite layer is now hardened with foreign keys, WAL mode, busy timeout, schema-version scaffolding, and indexed child/event tables.
- Project artifact endpoints for `manifest`, `sequence`, and `chapter-1` are implemented and backed by canonical artifact lookup.
- The frontend now polls backend status endpoints and exposes saved checker report paths.
- The recovered create/start endpoints now return `202 Accepted` with polling targets, while the current stub execution continues in post-response background tasks.
- The current recovered stub workflow persists immutable request snapshots, append-only event history, baseline attempt-lineage fields, and rejects illegal state transitions for jobs and checker runs.
- Runtime LLM integration is still represented as recovered stubs until the original implementation is either recovered or rebuilt.

What current validation covers:
- FastAPI app boot and recovered endpoint surface
- recovered sample project listing
- workflow preference/model catalog responses
- recovered job and checker flow contracts, including `202 Accepted` plus status polling
- persisted checker report creation
- persistence of jobs, checker runs, and project artifact registration
- persistence of request snapshots and append-only event history for jobs and checker runs
- persistence of baseline attempt-lineage fields on job/checker rows and event rows
- explicit project reconciliation behavior instead of constructor-time registry mutation
- canonical artifact lookup for recovered chapter naming differences and project database creation
- SQLite pragma/index/foreign-key behavior and deterministic state-transition rejection
- recovery-safe schema rebuilds from older operation database shapes

What current validation does not cover yet:
- real model inference execution
- orchestrator/compiler behavior
- critic scoring calibration
- end-to-end coverage for the full writer-workflow prototype in the browser
- hardened queue/lease/idempotency behavior from the async protocol blueprint
- first-class attempt records, retry metadata, and acceptance-only queue semantics
- true worker/lease execution behind the accepted endpoints

Design status:
- The deterministic async protocol/state-machine blueprint is documented in `docs/Async Protocol Blueprint v0.1.md`.
- The failure-oriented test plan for recovery/resume behavior is documented in `docs/Failure Mode Test Matrix v0.1.md`.
- These documents are design-only prerequisites for the later serial queue/worker runtime integration.

Current verified result:
- `python -m pytest tests/test_recovered_smoke.py tests/test_persistence.py -q`
- Result: `17 passed`
