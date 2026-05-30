# Cross-Reference: Comprehensive Audit vs Code Review Findings

**Date:** 2026-05-29
**Documents:**
- `docs/Comprehensive-Audit-2026-05-29.md` (12-phase systematic audit)
- `docs/Code-Review-Findings-2026-05-29.md` (14 task-specific findings from branch diff)

---

## Coverage Matrix

| Area | Audit | Code Review | Status |
|------|-------|-------------|--------|
| Backend architecture (discovery.py) | H1/H2/H3 | NE-09 | **Overlapping** |
| Frontend XSS (innerHTML) | H5 | — | Audit only |
| Connection pooling | H4 | — | Audit only |
| N+1 queries | M3/M4/M5 | — | Audit only |
| Prompt injection | M2 | — | Audit only |
| Backup path traversal | M1 | — | Audit only |
| Unbounded list endpoints | M6 | — | Audit only |
| Status code / validation (API) | M7/M8 | NE-07/NE-08 | **Overlapping** |
| Idempotency / pagination | M9/M6 | — | Audit only |
| CI test coverage | M10 | — | Audit only |
| Pre-commit hooks / CHANGELOG | M11/M12 | — | Audit only |
| Launcher backend duplicate kill | — | NE-01 | Code review only |
| Launcher frontend static model | — | NE-02 | Code review only |
| Launcher frontend rebuild | — | NE-03 | Code review only |
| Launcher LLM unmanaged | — | NE-06 | Code review only |
| Studio rail compact mode | — | NE-04 | Code review only |
| Entity count badges | — | NE-05 | Code review only |
| Polish error handling | — | NE-07 | Code review only |
| Export option rejection | — | NE-08 | Code review only |
| Deleted test restoration | — | NE-09 to NE-12 | Code review only |
| Root Image/ cleanup | — | NE-13 | Code review only |
| Rail icon typing | — | NE-14 | Code review only |

---

## Overlapping Findings (Both Documents Agree)

### 1. `discovery.py` Architectural Problems

| Audit | Code Review |
|-------|-------------|
| **H1**: Layer leakage — raw sqlite3 in API handlers | **NE-09**: Discovery endpoint existence tests were deleted from branch |
| **H2**: Module-level singleton globals | — |
| **H3**: Async handlers blocking on sqlite3 | — |

**Analysis:** The audit identified `discovery.py` as the single worst architectural offender (layer leakage, DI violations, async blocking). The code review independently found that the branch deleted 7 endpoint existence tests for discovery. This is a compounding risk: the module with the most architectural debt now has reduced test coverage. Fixing NE-09 (restoring tests) is a prerequisite before refactoring per H1/H2/H3, because the restored tests will serve as regression guards.

**Recommended order:** NE-09 first (restore tests), then H1/H2/H3 (refactor).

### 2. Polish API Error Handling

| Audit | Code Review |
|-------|-------------|
| Phase 6: Error response format — consistent `{detail: str}` | **NE-07**: `analyze_document` and `export_manuscript` don't catch `PolishServiceError` |

**Analysis:** The audit found error format to be generally consistent (PASS). NE-07 identifies two specific routes in `polish.py` that bypass this pattern — service errors leak as 500 instead of 404/400. This is a localized gap in an otherwise good pattern. NE-07 fixes it.

**Resolution:** NE-07 subsumes the audit finding for these two routes.

### 3. Request Validation

| Audit | Code Review |
|-------|-------------|
| **M8**: Guided-setup accepts raw `dict` instead of Pydantic | **NE-08**: `ExportRequest` accepts options that are silently ignored |

**Analysis:** Both find the same class of problem — API endpoints silently accept inputs they don't properly handle. M8 is about missing validation (raw dict), NE-08 is about false validation (accepts but ignores). Both are Pydantic-level fixes.

**Resolution:** Address both independently. Same root cause pattern.

---

## Audit-Only Findings (Not in Code Review)

These are systemic issues the audit found that the code review did not address:

| Finding | Severity | Description | Action |
|---------|----------|-------------|--------|
| **H4** | HIGH | No connection pooling — 246 separate DB connections per request | New task needed |
| **H5** | HIGH | XSS via `dangerouslySetInnerHTML` in toast | New task needed |
| **M1** | MEDIUM | Backup path traversal in `_find_backup()` | New task needed |
| **M2** | MEDIUM | Prompt injection — user story text unfenced in LLM prompt | New task needed |
| **M3** | MEDIUM | N+1 in story_forking (loop over characters/world/arcs) | New task needed |
| **M4** | MEDIUM | N+1 in generation_phases (loop over chapters) | New task needed |
| **M5** | MEDIUM | N+1 in planning sync | New task needed |
| **M6** | MEDIUM | 44 unbounded list endpoints (no pagination) | New task needed |
| **M7** | MEDIUM | Backup create returns 200 instead of 201 | New task needed |
| **M9** | MEDIUM | Missing idempotency on backup/project create | New task needed |
| **M10** | MEDIUM | CI runs only 13 test files | New task needed |
| **M11** | MEDIUM | No pre-commit hooks | New task needed |
| **M12** | MEDIUM | No CHANGELOG.md | New task needed |

**Note:** H4 (connection pooling) and M6 (pagination) are the highest-priority audit-only findings. H4 affects every multi-entity operation; M6 affects every list endpoint as data grows.

---

## Code Review-Only Findings (Not in Audit)

These are branch-specific issues the code review found that the audit did not cover:

| Finding | Severity | Reason Not in Audit |
|---------|----------|---------------------|
| **NE-01** | P1 | Audit scope excluded `narrative-launcher/` (.NET) |
| **NE-02** | P1 | Audit scope excluded `narrative-launcher/` (.NET) |
| **NE-03** | P1 | Audit scope excluded `narrative-launcher/` (.NET) |
| **NE-04** | P1 | UI rendering bug — audit checked XSS, not render logic |
| **NE-05** | P2 | UI state bug — audit checked type safety, not count mapping |
| **NE-06** | P2 | Audit scope excluded `narrative-launcher/` (.NET) |
| **NE-07** | P2 | Overlaps with audit Phase 6 (error format) |
| **NE-08** | P2 | Overlaps with audit Phase 6 (validation) |
| **NE-09** | P2 | Branch diff finding — audit assesses current state, not deleted code |
| **NE-10** | P2 | Branch diff finding — audit assesses current state |
| **NE-11** | P2 | Branch diff finding — audit assesses current state |
| **NE-12** | P2 | Branch diff finding — audit assesses current state |
| **NE-13** | P3 | Housekeeping — audit focuses on code quality, not filesystem |
| **NE-14** | P3 | Type safety — audit checked `as any`/`@ts-ignore`, not Record keys |

**Key gap:** The audit did not cover `narrative-launcher/` (4 findings: NE-01, NE-02, NE-03, NE-06). The .NET launcher is outside the Python/TypeScript audit scope. These 4 P1/P2 findings should be treated as HIGH priority.

---

## Risk Interaction Analysis

### Compound Risks (Multiple Findings Affect Same Code)

1. **`discovery.py`** — Audit H1/H2/H3 + Code Review NE-09
   - Architectural debt + deleted tests = highest risk area
   - **Recommendation:** Restore tests (NE-09) before any refactoring

2. **`ServiceManager.cs`** — Code Review NE-01/NE-02/NE-03
   - Three P1 findings in one file
   - **Recommendation:** Execute in order: NE-01, NE-02, NE-03

3. **`polish.py` + schemas** — Audit M8 + Code Review NE-07/NE-08
   - Error handling + validation gaps in same module
   - **Recommendation:** Execute NE-07 and NE-08 together

4. **Test files** — Code Review NE-09/NE-10/NE-11/NE-12
   - 26 deleted tests across 4 files
   - **Recommendation:** Restore all before merge; they are regression guards for the audit's Phase 5 assessment

### Dependencies Between Documents

```
NE-09 (restore discovery tests)
    -> H1/H2/H3 (refactor discovery.py)  [audit findings depend on NE-09]

NE-07 (polish error handling)
    -> audit Phase 6 PASS  [NE-07 fixes audit gap]

NE-08 (export validation)
    -> audit Phase 6 M8  [same pattern, different endpoint]

NE-02 (frontend static model)
    -> NE-03 (frontend rebuild)  [explicit dependency]
```

---

## Consolidated Priority List

Combining both documents, ranked by severity and dependency:

| Priority | Item | Source | Severity | Depends On |
|----------|------|--------|----------|------------|
| 1 | NE-01: Launcher backend duplicate kill | Code Review | P1 | — |
| 2 | NE-02: Launcher frontend static model | Code Review | P1 | — |
| 3 | NE-03: Launcher frontend rebuild | Code Review | P1 | NE-02 |
| 4 | NE-04: Studio rail compact mode | Code Review | P1 | — |
| 5 | NE-09: Restore discovery tests | Code Review | P2 | — |
| 6 | H1/H2/H3: Refactor discovery.py | Audit | HIGH | NE-09 |
| 7 | H4: Connection pooling | Audit | HIGH | — |
| 8 | H5: Remove dangerouslySetInnerHTML | Audit | HIGH | — |
| 9 | NE-05: Entity count badges | Code Review | P2 | — |
| 10 | NE-06: LLM unmanaged in launcher | Code Review | P2 | — |
| 11 | NE-07: Polish error handling | Code Review | P2 | — |
| 12 | NE-08: Export option rejection | Code Review | P2 | — |
| 13 | NE-10 to NE-12: Restore deleted tests | Code Review | P2 | — |
| 14 | M1: Backup path traversal | Audit | MEDIUM | — |
| 15 | M2: Prompt injection fencing | Audit | MEDIUM | — |
| 16 | M3/M4/M5: N+1 queries | Audit | MEDIUM | — |
| 17 | M6: Pagination on list endpoints | Audit | MEDIUM | — |
| 18 | M7: Backup create 201 status | Audit | MEDIUM | — |
| 19 | M9: Idempotency on create endpoints | Audit | MEDIUM | — |
| 20 | M10: CI test coverage expansion | Audit | MEDIUM | — |
| 21 | NE-13: Remove root Image/ | Code Review | P3 | — |
| 22 | NE-14: Type rail icon map | Code Review | P3 | — |
| 23 | M11: Pre-commit hooks | Audit | MEDIUM | — |
| 24 | M12: CHANGELOG.md | Audit | MEDIUM | — |

---

## Summary

| Metric | Audit | Code Review | Overlap |
|--------|-------|-------------|---------|
| Total findings | 18 (5H, 12M, 1L) | 14 (4P1, 10P2, 3P3) | 3 areas |
| Unique to audit | 13 findings | — | — |
| Unique to code review | — | 11 findings | — |
| Scope gap | `.NET launcher` not covered | Branch diff, not full codebase | — |

**Key takeaway:** The two documents are largely complementary. The audit found systemic issues (connection pooling, N+1, pagination, prompt injection) that the code review missed. The code review found branch-specific issues (deleted tests, launcher bugs, UI rendering) that the audit missed. Together they provide a near-complete picture. The 3 overlapping areas confirm both methods are finding real problems.

**Missing from both:** No document addresses the `.playwright-mcp/` directory (200+ stale log/snapshot files). This is a housekeeping item, not a code quality issue.
