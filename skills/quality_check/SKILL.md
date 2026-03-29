---
name: quality_check
description: Automated code quality assessment tool that analyzes source files against 10 quality dimensions and provides actionable feedback with automatic scoring.
---

# Quality Check Skill

An automated code quality assessment tool that analyzes source files against universal quality dimensions and provides detailed feedback with automatic scoring.

## When to Use

Use this skill when:
- You want to assess code quality before merging
- You need automated feedback on coding standards
- You want to identify potential issues in the current branch diff, latest commit, or explicit target files
- You need a structured quality review checklist

## Commands

### Slash Command

```bash
/quality-check              # General quality check using the skill's context mode
/quality-check frontend     # Frontend-specific quality check
/quality-check backend      # Backend-specific quality check
/quality-check merge        # Pre-merge quality validation
```

### CLI Tool

```bash
python scripts/qc.py                    # Check branch diff vs codex/main
python scripts/qc.py --branch-diff      # Check branch diff vs codex/main
python scripts/qc.py --latest-commit    # Check files changed in HEAD
python scripts/qc.py --recent-fallback  # Check recently modified coding files
python scripts/qc.py app/main.py        # Check one specific file
python scripts/qc.py file1.py file2.ts  # Check multiple specific files
python scripts/qc.py --verbose          # Show review steps and analyzer results
python scripts/qc.py --allow-directories frontend/src  # Expand coding files under a directory target
python scripts/qc.py --files f1 f2      # Check specific files
python scripts/qc.py --adverse-only     # Only run adverse review
```

Primary implementation path: `scripts/qc.py`

- The repo root `qc.py` file is now a thin compatibility shim that forwards to `scripts/qc.py`.

## `scripts/qc.py` Target Selection

- Default behavior reviews coding files changed on the current branch relative to `codex/main`.
- If branch diff detection finds nothing, `scripts/qc.py` falls back to files changed in `HEAD`.
- If both git-derived modes find nothing, `scripts/qc.py` falls back to recently modified coding files.
- Direct positional targets such as `python scripts/qc.py app/main.py` override auto-detection and review only those files.
- Directory targets are rejected unless `--allow-directories` is provided.
- Missing or unsupported explicit targets now fail clearly instead of silently falling back to a general run.
- `--git` remains supported as a legacy alias for `--branch-diff`.
- `--verbose` prints the target-selection path, review steps, and per-file analyzer results before the final report.
- The adverse review now includes concrete file-aware findings from the analyzed files in addition to the generic checklist.

## Known Limitations / Future Improvements

- `scripts/qc.py` performs heuristic file analysis, not full semantic code review.
- It does not yet reason across multiple files to detect end-to-end contract drift such as component -> service -> router mismatches.
- It does not run repo validation commands itself; lint, typecheck, build, and pytest results still need to be gathered separately.
- It reviews full selected files, not exact changed hunks, so findings are not diff-scoped yet.
- The adverse review now produces concrete findings, but those findings are still pattern-based rather than architecture-aware.
- Framework-specific correctness is still shallow; React state flow, routing behavior, persistence ordering, and API integration bugs can still slip through.
- Test adequacy is not measured directly; the tool can point out likely gaps, but it does not prove that behavior is covered.
- Future upgrade targets:
  - run validation commands and include pass/fail output
  - add diff-hunk-aware review mode
  - add repo-specific contract checks
  - add cross-file analysis for call-chain drift
  - emit stricter findings-first merge-review output with severity and file/line emphasis

## Quality Dimensions Assessed

| Dimension | Description |
|-----------|-------------|
| Contract Adherence | Interface and endpoint compliance |
| Architectural Consistency | Pattern and utility usage |
| State Correctness | State management and persistence |
| Production Readiness | Console logs, TODOs, placeholders |
| Error Resilience | Error handling patterns |
| UX Polish | Readability and user experience |
| Type Safety | Type annotations and safety |
| Static Analyzability | Code analyzability patterns |
| Boundary Discipline | Mock/test boundaries |
| Maintainability | Code organization and clarity |

## Scoring

- Each dimension is scored 0-2
- Target: 80% (16/20 points)
- Automatic failure conditions checked
- Adverse code review included

## Automated Checks

The tool automatically detects:
- Console.log statements
- TODO/FIXME comments
- 'any' type usage (TypeScript)
- Long lines (>120 chars)
- Long functions (>50 lines)
- Magic numbers
- Bare except clauses
- Silent failures

## Example Output

```
# Quality Check Assessment

**Context:** general

## Files Analyzed

- `src/component.tsx`
- `src/service.ts`

## Dimension Assessment

### Production Readiness

[ ] No console logs in user-facing code paths
...

**Score (0-2):** `1`
**Notes:** Found 2 console.log statement(s)

## Overall Score

**Total:** 18/20 (90%) [PASS]
```

## Example Workflows

**Pre-merge Quality Check:**

```bash
# Check current branch changes against codex/main
python scripts/qc.py

# Run frontend build checks
cd frontend && npm run build
```

**Targeted File Review:**

```bash
# Check specific files
python scripts/qc.py --files src/new-feature.tsx src/utils.ts

# Check specific files without --files
python scripts/qc.py src/new-feature.tsx src/utils.ts

# Check review steps and analyzer counts
python scripts/qc.py --verbose

# Check all coding files under a directory
python scripts/qc.py --allow-directories frontend/src
```

**Adverse Review Only:**

```bash
# Quick adverse review
python scripts/qc.py --adverse-only
```
