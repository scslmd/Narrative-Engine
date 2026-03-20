# Documentation Guide v0.1

Use these documents by purpose:

- `docs/Narrative SRS v0.1.md`: backend and product specification baseline
- `docs/Frontend Design SRS v0.1.md`: frontend workflow and interaction baseline
- `docs/Role Model Checker Decision v0.1.md`: why the checker exists and how it should be used
- `docs/Live Runtime Findings v0.1.md`: runtime lessons that inform model and workflow choices
- `docs/Async Protocol Blueprint v0.1.md`: target async execution protocol
- `docs/Inference Runtime Blueprint v0.1.md`: deterministic runtime-provider contract for backend selection, environment variables, inferencer payloads, provider defaults, and runtime error taxonomy
- `docs/Step Record Blueprint v0.1.md`: current backend contract and implementation notes for per-step records and artifact lineage; pair it with `tests/test_step_record_spec.py` and `tests/test_step_record_persistence.py`
- `docs/Step and Lineage API Projection Blueprint v0.1.md`: deterministic response contracts for future inspect endpoints over persisted steps and artifact lineage
- `docs/Story Arc Paradigm Blueprint v0.1.md`: planning taxonomy for arc-aware story guidance and next-step suggestions
- `docs/Failure Mode Test Matrix v0.1.md`: failure-oriented test planning
