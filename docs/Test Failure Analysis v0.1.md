# Test Failure Analysis v0.1

> **Superseded**: See `docs/Test Failure Analysis v0.2.md` for the current analysis.
> This file is kept as historical reference.

## Executive Summary

After implementing persistence expansion (artifact lineage project-scoped queries, step record service wrappers, chapter packet / sequence plan / storyboard card services, and manuscript-aid contract tests), the full test suite shows:

- **583 passed** (baseline: 572, +11 from current session)
- **29 failed** (pre-existing issues — all fixed in subsequent session)
- **9 skipped**

All **17 new tests pass** with zero regressions.
