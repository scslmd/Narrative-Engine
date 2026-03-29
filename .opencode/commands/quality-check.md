---
description: Run qc.py with pass-through arguments for branch diff, commit, file, or directory review
agent: build
---

Run the quality check assessment tool and forward any supplied arguments directly to `scripts/qc.py`.

Required folder structure in the target repo:

```text
<repo-root>/
|-- .opencode/
|   `-- commands/
|       `-- quality-check.md
`-- scripts/
    |-- __init__.py
    |-- qc.py
    `-- quality_check_engine.py
```

Notes:
- `quality-check.md` must stay under `.opencode/commands/`.
- `qc.py` and `quality_check_engine.py` must stay together under `scripts/`.
- Run the command from the repo root so relative file and directory targets resolve correctly.
- The root-level `qc.py` shim from this repo is not required for portability.

Execute the following command and show me the complete output:

```bash
python scripts/qc.py $ARGUMENTS
```

Examples:
1. `/quality-check` -> `python scripts/qc.py`
2. `/quality-check --verbose` -> `python scripts/qc.py --verbose`
3. `/quality-check --latest-commit` -> `python scripts/qc.py --latest-commit`
4. `/quality-check app/services/config_validator.py` -> `python scripts/qc.py app/services/config_validator.py`
5. `/quality-check --allow-directories frontend/src` -> `python scripts/qc.py --allow-directories frontend/src`

If no arguments are supplied, `qc.py` defaults to reviewing the current branch diff against `codex/main`, then falls back to `HEAD`, then to recent modified coding files.

The command should preserve all passed flags and targets exactly, including:
- `--branch-diff`
- `--latest-commit`
- `--recent-fallback`
- `--files ...`
- direct file paths
- `--allow-directories`
- `--adverse-only`
- `--verbose`

Known limitations to revisit later:
- `qc.py` is still a heuristic analyzer, not a full semantic merge reviewer.
- It does not yet run lint/typecheck/build/pytest itself.
- It does not yet analyze exact changed hunks.
- It does not yet perform cross-file contract verification.
- Its adverse review is now file-aware, but still pattern-based rather than architecture-aware.

Please display the complete output so I can review all sections.
