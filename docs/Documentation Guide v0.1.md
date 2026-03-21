# Documentation Guide v0.1

Use these documents by purpose:

- `STRUCTURE.md`: practical repository map describing the purpose of the main folders and key files
- `docs/Narrative SRS v0.1.md`: backend and product specification baseline for the current system
- `docs/Frontend Design SRS v0.1.md`: frontend workflow and interaction baseline
- `docs/Story Development Product Spec v0.1.md`: comprehensive product spec for brainstorming, editable core flow, characters, world bible, arc-aware planning, drafting, screens, backend objects, and workflow states
- `docs/Story Development Canonical Contract v0.1.md`: canonical object names, lifecycle enums, editable-flow semantics, drafting/provenance rules, and planning terminology for story-development features
- `docs/Orchestrator Deterministic Task Spec v0.1.md`: deterministic task-assignment reference for future agent orchestration
- `docs/Async Protocol Blueprint v0.1.md`: target async execution protocol
- `docs/Inference Runtime Blueprint v0.1.md`: deterministic runtime-provider contract for backend selection, environment variables, inferencer payloads, provider defaults, and runtime error taxonomy
- `docs/Step Record Blueprint v0.1.md`: current backend contract and implementation notes for per-step records and artifact lineage; pair it with `tests/test_step_record_spec.py` and `tests/test_step_record_persistence.py`
- `docs/Step and Lineage API Projection Blueprint v0.1.md`: deterministic response contracts for future inspect endpoints over persisted steps and artifact lineage
- `docs/Story Arc Paradigm Blueprint v0.1.md`: planning taxonomy for arc-aware story guidance and next-step suggestions
- `docs/Failure Mode Test Matrix v0.1.md`: failure-oriented test planning

Historical notes and superseded decisions live under `docs/archive/`.

- `docs/archive/Role Model Checker Decision v0.1.md`: earlier checker rationale retained for reference
- `docs/archive/Live Runtime Findings v0.1.md`: earlier runtime observations retained for reference
- `docs/archive/Build Notes v0.1.md`: superseded scratch planning notes retained for reference
