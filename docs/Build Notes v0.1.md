# Build Notes v0.1

Current implementation notes:

- Operational state is backed by SQLite instead of process-local memory.
- Project artifact lookup is normalized through persistence for `manifest`, `sequence`, and `chapter-1`.
- Jobs and checker runs persist immutable request snapshots, append-only event history, and first-class attempt records.
- The frontend polls backend status endpoints and surfaces saved checker report paths.
- Job creation and checker start endpoints now return `202 Accepted`, run through a local lease-claim executor, support idempotent replay through `Idempotency-Key`, emit reclaim events for expired accepted leases, and persist attempt-level executor telemetry including executor name, executor instance, queue delay, finish reason, and reclaim context.
- Failed jobs and checker runs can now be requeued explicitly through retry endpoints that create a new attempt number without overwriting prior attempt metadata.
- Step-record and artifact-lineage contracts are now documented separately and backed by live SQLite persistence, executor writes, and deterministic persistence tests.
- Inference is now generalized behind a provider-agnostic contract with a reusable OpenAI-compatible adapter, so `llama.cpp`, LM Studio, and `vLLM` can be targeted through configuration instead of backend-specific orchestration code.
- The `P-100` pipeline phase now runs a real `architect` inference request through the generalized inferencer, writes markdown output to the project exports folder, persists canonical lineage, and registers the output as the canonical `architect_p100` project artifact.
- Current limitation: step records and lineage exist in the backend, but they are not yet exposed through dedicated API projections, and phases after `P-100` plus checker role execution still rely on stubbed runtime behavior.

Next build priorities:

1. expose step records and artifact lineage through dedicated API projections
2. wire structured runtime errors, finish reasons, and richer telemetry into the inference layer
3. extend runtime-backed execution beyond `P-100`
4. rebuild orchestrator/compiler execution
5. deepen checker evaluation and test coverage
