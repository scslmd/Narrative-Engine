# Build Notes v0.1

Current implementation notes:

- Operational state is backed by SQLite instead of process-local memory.
- Project artifact lookup is normalized through persistence for `manifest`, `sequence`, and `chapter-1`.
- Jobs and checker runs persist immutable request snapshots, append-only event history, and baseline attempt-lineage fields.
- The frontend polls backend status endpoints and surfaces saved checker report paths.
- Job creation and checker start endpoints now return `202 Accepted` and complete the current stub flow in background execution.

Next build priorities:

1. replace background stubs with a real worker or lease-based runner
2. add first-class attempt or step records
3. rebuild inference/runtime integration
4. rebuild orchestrator/compiler execution
5. deepen checker evaluation and test coverage
