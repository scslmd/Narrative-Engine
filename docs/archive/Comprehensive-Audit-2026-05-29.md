# Narrative Engine — Comprehensive Audit Report

**Date:** 2026-05-29
**Strategy:** Full audit (Phases 1-12)
**Profiles:** `local-desktop-app` + `LLM-orchestration-app` + `data-sensitive-app`
**Scope:** `app/`, `frontend/`, `tests/`, `scripts/` (excludes `docs/archive/`, `data/`, `node_modules/`)

---

## Executive Summary

| Severity | Count | Key Findings |
|----------|-------|--------------|
| **BLOCKER** | **0** | — |
| **HIGH** | **5** | `discovery.py` layer leakage, module-level singletons, event-loop blocking, connection pooling, XSS via innerHTML |
| **MEDIUM** | **12** | Backup path traversal, prompt injection, N+1 queries, unbounded lists, missing pagination/idempotency, CI gap, etc. |
| **LOW** | **1** | `console.warn` in production |

**Verdict: CONDITIONAL** — No blockers. 5 HIGH findings must be addressed before merge. 12 MEDIUM findings should be tracked.

---

## Phase Results

| Phase | Result | BLOCKER | HIGH | MEDIUM | LOW |
|-------|--------|---------|------|--------|-----|
| 1. Code Quality | **PASS** | 0 | 0 | 0 | 0 |
| 2. Security | **PASS** | 0 | 0 | 2 | 0 |
| 3. Architecture | **FAIL** | 0 | 3 | 1 | 0 |
| 4. Performance | **FAIL** | 0 | 2 | 2 | 0 |
| 5. Testing | **PASS** | 0 | 0 | 1 | 0 |
| 6. API Design | **FAIL** | 0 | 0 | 3 | 0 |
| 7. Frontend | **FAIL** | 0 | 1 | 0 | 1 |
| 8. Infrastructure | **FAIL** | 0 | 0 | 2 | 0 |
| 9. Data | **PASS** | 0 | 0 | 0 | 0 |
| 10. Compliance | **PASS** | 0 | 0 | 0 | 0 |
| 11. Documentation | **FAIL** | 0 | 0 | 1 | 0 |
| 12. Operations | **PASS** | 0 | 0 | 0 | 0 |

---

## Phase 1: Code Quality — PASS

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 1.1 | Syntax compilation | PASS | BLOCKER | E2, `python -m compileall app tests` exit 0 | All files compile cleanly |
| 1.2 | `eval()` usage | PASS | HIGH | E2, grep | Zero matches |
| 1.3 | `exec()` usage | PASS | HIGH | E2, grep | Zero matches |
| 1.4 | `pickle.load` usage | PASS | HIGH | E2, grep | Zero matches |
| 1.5 | `shell=True` usage | PASS | HIGH | E2, grep | Zero matches |
| 1.6 | `assert False` | PASS | MEDIUM | E2, grep | Zero matches |
| 1.7 | TODO/FIXME/hack/XXX | PASS | LOW | E2, grep | Zero matches in production code |
| 1.8 | Bare except clauses | PASS | HIGH | E2, grep | Zero matches |
| 1.9 | Hardcoded secrets | PASS | BLOCKER | E2, grep | 8 dynamic variable assignments in `authentication.py`, no hardcoded values |
| 1.10 | Subprocess/os.system | PASS | HIGH | E2, grep | Zero matches |
| 1.11 | YAML unsafe load | PASS | HIGH | E2, grep | Zero matches |

**Summary:** 11 passed, 0 failed, 0 waived, 0 unable

---

## Phase 2: Security — PASS (2 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 2.1 | CORS configuration | PASS | MEDIUM | E1, `app/settings.py:240-249` | Origins restricted to `localhost:5173` and `localhost:3000`. No wildcard. |
| 2.2 | Rate limiting | PASS | MEDIUM | E1, `app/middleware/rate_limit.py:19-26` | 3 tiers, per-client-IP, short-circuits on 429. |
| 2.3 | Authentication | PASS | HIGH | E1, `app/services/authentication.py` | bcrypt hashing, `secrets` module, `hmac.compare_digest` for timing-safe comparison. |
| 2.4 | Authorization | PASS | HIGH | E1, `app/services/authorization.py` | 3-tier permission hierarchy (read < write < admin). |
| 2.5 | SQL injection | PASS | HIGH | E1, `app/persistence/sqlite.py` | All data queries use parameterized `?` placeholders. No user input reaches SQL execution. |
| 2.6 | Path traversal (URL) | PASS | HIGH | E1, `app/middleware/path_traversal.py` | Blocks `..`, `%2e%2e`, `%252e`, `%00`, `\\` in URL paths. |
| 2.7 | Path traversal (ZIP import) | PASS | HIGH | E1, `app/services/project_import.py:66` | Rejects ZIP entries with `/` prefix or `..` in path. |
| 2.8 | Path traversal (backup) | **FAIL** | **MEDIUM** | E1, `app/services/backup.py:334-335` | `_find_backup()` accepts absolute paths. `DELETE /backup/{backup_id}` passes `backup_id` directly. Attacker could pass absolute path to delete arbitrary files. Mitigated by API key auth. |
| 2.9 | File upload validation | PASS | HIGH | E1, `app/api/projects.py:460-475` | Extension check (`.zip` only), 500MB limit, UUID temp filename. |
| 2.10 | Error info leakage | PASS | MEDIUM | E2, grep | Zero matches for traceback/sys.exc_info/format_exc in app/. |
| 2.11 | XSS (innerHTML) | PASS | HIGH | E1, `StudioLayoutManager.tsx:352` | `dangerouslySetInnerHTML` used but only with hardcoded strings. Promoted to HIGH in Phase 7. |
| 2.12 | Prompt injection (LLM) | **FAIL** | **MEDIUM** | E1, `app/services/runtime_prompts/import_prompts.py:147` | User story text injected directly into LLM prompt without fencing. Malicious content could attempt instruction override. Mitigated by low temp (0.1) and strict JSON output. |
| 2.13 | `.env` exposure | PASS | BLOCKER | E2, git status | `.env` in `.gitignore`, not tracked. `.env.example` contains placeholder only. |
| 2.14 | Thread safety | PASS | HIGH | E2, grep `threading.Lock` | 10 lock instances across job managers, circuit breaker, idempotency, maintenance, worker lifecycle. |
| 2.15 | CSRF protection | WAIVED | HIGH | E1 | Bearer-token API. No cookies or session state. CSRF not applicable. |

**Summary:** 13 passed, 2 failed (MEDIUM), 1 waived, 0 unable

---

## Phase 3: Architecture — FAIL (3 HIGH, 1 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 3.1 | Single Responsibility | **FAIL** | HIGH | E1, file line counts | 6 files exceed 500 lines. `sqlite.py` (2725 lines) combines schema DDL, migration logic, index management, AND CRUD. `multi_pass_import.py` (1786 lines), `story_import.py` (1588 lines) each handle full multi-phase LLM workflows. |
| 3.2 | Dependency Injection | **FAIL** | HIGH | E2, `backup.py:389-402`, `authentication.py:416-430`, `authorization.py:169-179`, `discovery.py:28-38` | 5 module-level singletons use lazy init with `global` keyword. State leaks between tests. `build_*_router` pattern used elsewhere is the correct approach. |
| 3.3 | Circular imports | PASS | INFO | E3, `import app.main` succeeds | No circular import issues. |
| 3.4 | Layer Leakage (API → Persistence) | **FAIL** | HIGH | E2, `discovery.py:77-264`, `health.py:50-57,200-248`, `planning.py:212-241` | `discovery.py` performs raw `sqlite3.Connection.execute()` calls in 6 async API handlers, bypassing service and persistence layers. Contains business logic for entity deduplication, character enrichment, staging apply/undo. |
| 3.5 | Business Logic in API Handlers | **FAIL** (included in 3.4) | HIGH | E2, `discovery.py:141-225`, `planning.py:212-241` | Entity approval logic and beat position calculation in API handlers. |
| 3.6 | Configuration Management | PASS | INFO | E1, `app/constants.py`, `app/settings.py` | Magic numbers centralized. Minor: `health.py:89` has inline `1_073_741_824` (1 GB). |
| 3.7 | Error Handling Strategy | PASS | INFO | E2, grep | No bare `except: pass`. Exceptions consistently caught and re-raised as `HTTPException`. `sqlite.py:1568` has `except Exception: raise` — dead code. |
| 3.8 | Global Mutable State | **FAIL** | MEDIUM | E2, `discovery.py:28-29`, `backup.py:389`, `authentication.py:416`, `authorization.py:169` | 5 module-level mutable globals modified via `global`. Testability concern. |
| 3.9 | Async Consistency | **FAIL** | HIGH | E2, `discovery.py:76-264`, `health.py:50-57,200-248` | Async handlers perform blocking sqlite3 operations on event loop thread. |
| 3.10 | Persistence → API imports | PASS | INFO | E2, grep | No reverse dependencies. Layer boundaries respected in majority of codebase. |

**Summary:** 4 passed, 5 failed (3 HIGH, 1 MEDIUM)
**Key insight:** Refactoring `discovery.py` alone would resolve findings 3.2, 3.4, 3.5, 3.8, and 3.9.

---

## Phase 4: Performance — FAIL (2 HIGH, 2 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 4.1 | N+1 query: story_forking | **FAIL** | HIGH | E1, `story_forking.py:53-86,99-118,135-144` | Loop over character_ids calls `upsert_character_profile()` per iteration. Each opens/closes own DB connection. Same for relationships and world entries. |
| 4.2 | N+1 query: story_import | PASS | INFO | E1, `story_import.py:519-580` | Uses shared connection, single transaction with `BEGIN IMMEDIATE`. Correct pattern. |
| 4.3 | N+1 query: generation_phases | **FAIL** | HIGH | E1, `generation_phases.py:136-159` | Loop over chapter_ids calls `upsert_draft_artifact()` + `upsert_manuscript_document()` per chapter. Separate connections. |
| 4.4 | N+1 query: planning sync | **FAIL** | MEDIUM | E1, `planning.py:371-390` | `_sync_sequence_chapter_ids` calls list + upsert per sequence. 3+ connections per call. |
| 4.5 | Connection pooling | **FAIL** | HIGH | E2, `sqlite.py:1246-1251`, 246 occurrences of `with connect(self.db_path)` | **No connection pooling.** Every repo method creates new `sqlite3.connect()`. Creating N entities = 2N file opens. |
| 4.6 | Blocking I/O in async | PASS | INFO | E1, grep | All file I/O in synchronous handlers. No blocking in async context. |
| 4.7 | Unbounded response payloads | **FAIL** | MEDIUM | E2, 47 list endpoints, only 3 with limits | 44 list endpoints return all results: projects, characters, world-bible, arcs, relationships, draft-artifacts, manuscript-documents, generation runs, etc. |
| 4.8 | Thread management | PASS | INFO | E1, `worker_lifecycle.py:61-81` | 2 daemon threads, lock guard, Event-based stop, 2s join timeout. Clean lifecycle. |
| 4.9 | SQLite WAL + busy_timeout | PASS | INFO | E1, `sqlite.py:1268-1272` | WAL mode, foreign_keys ON, 5000ms busy_timeout, passive checkpoint. Correct. |
| 4.10 | No asyncio misuse | PASS | INFO | E2, grep | No `asyncio.run`, `to_thread`, or `run_in_executor` in app code. All handlers are synchronous. |

**Summary:** 6 passed, 4 failed (2 HIGH, 2 MEDIUM)

---

## Phase 5: Testing — PASS (1 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 5.1 | Test count | PASS | INFO | E2, 147 test files, 1,661 test functions | Substantial coverage. ~11 functions/file average. |
| 5.2 | Naming conventions | PASS | INFO | E2, grep | Majority follow `test_<component>_<action>_<expected_result>`. |
| 5.3 | Test isolation (tmp_path) | PASS | INFO | E2, 1,715 `tmp_path` usages | Vast majority of tests use `tmp_path`. 165 pure unit tests correctly don't need it. |
| 5.4 | Skipped/xfail tests | PASS | INFO | E2, 4 skip markers | All have documented justifications (xdist isolation, platform-specific, no stable fixtures). |
| 5.5 | Mock usage (LLM/network) | PASS | INFO | E2, 429 mock-related matches | `MagicMock`, `patch`, `StubInferenceBackend` used extensively. |
| 5.6 | Multi-thing tests | **FAIL** | MEDIUM | E1, `test_discovery_api.py:356-430` | `test_full_lifecycle*` tests have 8+ assertions each. Fragile, hard to isolate root cause. |
| 5.7 | Error path coverage | PASS | INFO | E2, 121 `pytest.raises` usages | Broad coverage: ValueError, KeyError, HTTPException, RuntimeError, idempotency conflicts, cross-project rejections. |
| 5.8 | Class-based tests | PASS | INFO | E2, 833 class-based test methods | ~50% use class organization with shared fixtures. |
| 5.9 | No destructive tests | PASS | INFO | E1 | All integration tests use `tmp_path` or `patch_env_tmpdir`. No production data touched. |
| 5.10 | Async test support | WAIVED | INFO | E1 | All FastAPI handlers are synchronous. `pytest-asyncio` not needed. |

**Summary:** 8 passed, 1 failed (MEDIUM), 1 waived

---

## Phase 6: API Design — FAIL (3 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 6.1 | HTTP method correctness | PASS | INFO | E3, all routers reviewed | GET=reads, POST=creates, PATCH=updates, DELETE=deletes. PUT used correctly for reindex. |
| 6.2 | Status codes: backup create | **FAIL** | MEDIUM | E2, `app/api/backup.py:16` | `POST /v1/backup/create` returns 200. Should return **201 Created**. |
| 6.2b | Status codes: async | PASS | INFO | E2 | Async POSTs correctly return 202: jobs, checker runs, imports, manuscript-assist. |
| 6.2c | Status codes: creates | PASS | INFO | E2 | All sync creates return 201 correctly. |
| 6.3 | Error response format | PASS | INFO | E2 | Consistent `{detail: str}` via `HTTPException`. Global 422 handler at `main.py:483`. |
| 6.4 | API versioning | PASS | INFO | E2, `main.py:455-468` | All endpoints under `/v1/`. Health unversioned (documented policy). |
| 6.5 | Request validation: guided-setup | **FAIL** | MEDIUM | E2, `projects.py:571-592,594-614` | `POST /projects/guided-setup/analyze` and `/create` accept raw `dict` instead of Pydantic model. Generic 400 errors instead of structured 422. |
| 6.5b | Request validation: constraints | PASS | INFO | E2 | Character models use `Field(..., min_length=1, max_length=255, pattern=...)`. `StrictModel` base for request schemas. |
| 6.6 | Idempotency | **FAIL** | MEDIUM | E2, `jobs.py:32-37` vs `backup.py:16-24` | Jobs/checker runs support `Idempotency-Key` header (409 on conflict). **Missing** from: `POST /backup/create`, `POST /projects/create`, `POST /projects/import-story`. |
| 6.7 | Health/readiness probes | PASS | INFO | E2, `health.py:24-161` | Three probes: liveness, readiness (DB, circuit breakers, disk, write permission), LLM connectivity. |
| 6.8 | Pagination | **FAIL** | MEDIUM | E2, grep | Only 3 endpoints support pagination (`/jobs/`, `/jobs/{id}/steps`, `/jobs/{id}/lineage`). 44 unbounded list endpoints. |

**Summary:** 7 passed, 3 failed (MEDIUM), 0 waived

---

## Phase 7: Frontend — FAIL (1 HIGH, 1 LOW)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 7.1 | XSS via innerHTML | **FAIL** | HIGH | E3, `StudioLayoutManager.tsx:352` | `dangerouslySetInnerHTML` for toast messages. Currently hardcoded strings only, but fragile against future changes. |
| 7.2 | HTTP error handling | PASS | INFO | E2, `frontend/src/lib/api.ts:25-59` | Shared Axios interceptor handles all HTTP error codes. Returns typed `ApiError`. All services use shared client. |
| 7.3 | console.log in production | **FAIL** | LOW | E3, grep | No `console.log`. 10 `console.warn/error` in production (error boundaries, localStorage failures, polling errors). Acceptable for diagnostics. |
| 7.4 | `as any` / `@ts-ignore` | PASS | INFO | E3, grep | Zero matches. No unsafe type casts or suppression comments. |
| 7.5 | Mock data / hardcoded URLs | PASS | INFO | E3, grep | All `mock*` in `.test.ts` files only. Services use shared `api` client with relative URLs. |
| 7.6 | Component error states | PASS | INFO | E2, 20+ components reviewed | Loading, error, and empty states handled consistently. Shared `ErrorBanner`, `EmptyState`, `LoadingState` components. |
| 7.7 | Dead code / unused exports | PASS | INFO | E2, grep | 157 named exports, all appear wired to imports. No obvious orphans. |
| 7.8 | Route deep links | PASS | INFO | E2, `App.tsx:72-96`, `StudioView.tsx:39-45` | `BrowserRouter` with explicit routes. URL params survive hard refresh. Backward-compatible redirects for old routes. SPA catch-all in `main.py:526-536`. |
| 7.8b | Route state persistence | PASS | INFO | E2, `StudioView.tsx:35-37`, `usePanelUrlSync` | Layout state in `studio-layout-v1` localStorage. Panel state synced with URL query params. |

**Summary:** 7 passed, 2 failed (1 HIGH, 1 LOW), 0 waived

---

## Phase 8: Infrastructure — FAIL (2 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 8.1 | CI/CD pipeline | PASS | HIGH | E2, `.github/workflows/tests.yml` | GitHub Actions on push/PR/manual. Matrix: ubuntu + windows, Python 3.12. |
| 8.1a | CI test coverage | **FAIL** | MEDIUM | E2, `tests.yml:33-49` | CI runs only 13 test files, not the full suite. Missing: parallel cluster, serial tests, story import, pattern extraction, generation orchestration, security tests. ~1,700 local tests vs. ~13 files in CI. |
| 8.2 | Pre-commit hooks | **FAIL** | MEDIUM | E2, no `.pre-commit-config.yaml` | No pre-commit hooks. Lint/typecheck/build only run manually or in CI. |
| 8.3 | Dockerfile | WAIVED | MEDIUM | E2, no Dockerfile | Local desktop app; containerization not required. |
| 8.4 | Environment variables | PASS | HIGH | E2, `.env.example:1-13` + `settings.py` | Documents key vars. Missing from `.env.example`: `CORS_ORIGINS`, per-phase temperature/tokens, discovery settings (all have defaults in settings.py). |
| 8.5 | Secrets management | PASS | BLOCKER | E2, `settings.py:97-104`, `main.py:434-453` | API key from env var, `hmac.compare_digest`. No secrets in repo. |
| 8.6 | Logging framework | PASS | MEDIUM | E2, `main.py:354-432`, `settings.py` | Structured JSONL audit logging. 30+ modules use `logging.getLogger(__name__)`. |
| 8.7 | Request ID tracing | WAIVED | LOW | E1 | No `X-Request-ID` header. Uses `request_hash` for idempotency. Acceptable for local app. |
| 8.8 | Metrics endpoint | PASS | LOW | E2, `health.py:164-325` | Circuit breaker states, job/checker counts, success rates, latency telemetry. |
| 8.9 | Alerting | WAIVED | MEDIUM | E1 | Tray launcher monitors health via 5s polling with hysteresis. |
| 8.10 | Health check | PASS | HIGH | E2, `health.py:24-132` | Liveness, readiness, LLM probe, metrics. |

**Summary:** 6 passed, 2 failed (MEDIUM), 3 waived

---

## Phase 9: Data — PASS

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 9.1 | Schema constraints | PASS | HIGH | E2, `sqlite.py:14-1221` | NOT NULL on required columns. Foreign keys with CASCADE/SET NULL. UNIQUE on natural keys. |
| 9.1a | CHECK constraints | WAIVED | MEDIUM | E2, `sqlite.py:1073-1080` | Only 4 CHECK constraints (on `discovery_staging`). Most tables lack CHECK for enum columns. Relies on app-layer validation. Acceptable. |
| 9.2 | Index coverage | PASS | HIGH | E2, `sqlite.py:1117-1221` | 107 indexes covering all FK columns, WHERE columns, composite query patterns. |
| 9.3 | Migration safety | PASS | HIGH | E2, `sqlite.py:1304-1393` | Full rebuild migration pattern. Targeted ALTER for additive changes. Stale legacy FK repair. `user_version` tracking. |
| 9.4 | WAL mode + checkpoint | PASS | HIGH | E2, `sqlite.py:1269-1272` | Every connection: WAL mode, passive checkpoint. Backup does TRUNCATE checkpoint before copy. |
| 9.5 | Busy timeout | PASS | HIGH | E2, `sqlite.py:11,1269` | 5000ms (5 seconds) applied to every connection. |
| 9.6 | Backup strategy | PASS | BLOCKER | E2, `backup.py:1-402` | WAL checkpoint, integrity validation, pre-restore backup, disk space check, 7-day retention, WAL/SHM handling. |
| 9.7 | RTO/RPO defined | WAIVED | HIGH | E1 | No formal RTO/RPO. Manual backup/restore available. 7-day retention. |
| 9.8 | Temp file cleanup | PASS | MEDIUM | E2, `project_maintenance.py:59-124` | Orphan detection, cleanup, audit log truncation, DB compaction. Import jobs expire after 300s TTL. Idempotency records expire after 24h. |
| 9.9 | Disk quota enforcement | PASS | HIGH | E2, `constants.py:11`, `main.py:332`, `health.py:74-97` | 10MB body, 5MB payload. Health warns at < 1GB free. Backup refuses if insufficient space. |
| 9.10 | Data retention | PASS | MEDIUM | E2 | Backup: 7 days. Import jobs: 300s. Idempotency: 24h. Audit log: configurable, default 10,000 lines. No automatic job history archival. |

**Summary:** 7 passed, 0 failed, 2 waived

---

## Phase 10: Compliance & Privacy — PASS (all WAIVED)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 10.1 | PII identification | WAIVED | HIGH | E2 | No PII stored. Fictional characters, story text, project metadata only. |
| 10.2 | GDPR compliance | WAIVED | BLOCKER | E1 | No EU users, no data leaves the machine. |
| 10.3 | Data minimization | PASS | HIGH | E2 | Stores only what's needed. No telemetry beyond local structured log. |
| 10.4 | Encryption at rest | WAIVED | HIGH | E1 | SQLite and project files unencrypted. Acceptable for personal writing tool. |
| 10.5 | Encryption in transit | WAIVED | HIGH | E1 | All traffic localhost loopback. No external exposure. |
| 10.6 | Third-party license audit | WAIVED | HIGH | E1 | Dependencies via `pyproject.toml`/`package.json`. No automated license check. Low risk. |
| 10.7 | Data Processing Agreement | WAIVED | HIGH | E1 | No third-party processors. LLM runs locally. |
| 10.8 | Privacy policy | WAIVED | HIGH | E1 | No external data collection. Not applicable. |

**Summary:** 1 passed, 0 failed, 7 waived

---

## Phase 11: Documentation — FAIL (1 MEDIUM)

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 11.1 | README | PASS | HIGH | E2, `README.md` | Comprehensive: product intent, requirements, inference config, architecture, quickstart, test baselines, core docs links. |
| 11.2 | API documentation | PASS | HIGH | E2 | FastAPI auto-generates `/docs` (Swagger) and `/redoc`. All 80+ endpoints documented. |
| 11.3 | Architecture diagram | WAIVED | MEDIUM | E1 | No visual diagram. Architecture described textually in README and AGENTS.md. |
| 11.4 | Runbook | PASS | HIGH | E2, `AGENTS.md` | Comprehensive: server lifecycle, startup commands, detached process management, test patterns, merge-readiness validation, security/reliability features, API patterns, common pitfalls. |
| 11.5 | Onboarding guide | PASS | MEDIUM | E2, `README.md` + `AGENTS.md` | Backend + frontend quickstart. Test baselines. Project structure, import patterns, type conventions. |
| 11.6 | Code comments | PASS | LOW | E2 | Complex logic has docstrings: migration rationale, backup steps, audit fields, health components. Module-level docstrings on services. |
| 11.7 | CHANGELOG | **FAIL** | MEDIUM | E2, no `CHANGELOG.md` | No changelog. Version history in git commits and README "Current Status". |
| 11.8 | Commit conventions | WAIVED | LOW | E1 | No enforced conventional commits. Pre-commit hooks absent. Low priority for solo/small team. |

**Summary:** 5 passed, 1 failed (MEDIUM), 2 waived

---

## Phase 12: Operations — PASS

| # | Check | Result | Severity | Evidence | Details |
|---|-------|--------|----------|----------|---------|
| 12.1 | Capacity planning | PASS | HIGH | E2, `constants.py`, `health.py`, `settings.py` | Request limits: 10MB body, 5MB payload. Rate limit: 100 req/min. Disk: 1GB warning. Audit log: 10,000 line default. Backup: 7-day retention. |
| 12.2 | Rollback strategy | PASS | HIGH | E2, `backup.py:159-256`, `sqlite.py:1304-1393` | DB rollback via backup restore with pre-restore backup. Schema rollback via full rebuild migration. Git-based code rollback. |
| 12.3 | Feature flags | WAIVED | MEDIUM | E1 | No feature flags. Acceptable for local app with direct deploy. |
| 12.4 | Incident response | PASS | MEDIUM | E2, `health.py`, `main.py`, `AGENTS.md` | Readiness probe checks all components. Structured audit log for forensics. Maintenance endpoints for orphan detection, DB compaction, audit truncation. Server management scripts. |
| 12.5 | Monitoring dashboard | PASS | MEDIUM | E2, `health.py:164-325` | `/health/metrics` provides circuit breaker states, job/checker counts, success rates, latency telemetry. Tray launcher visual status. |
| 12.6 | Alert thresholds | PASS | MEDIUM | E2, `health.py:89-95`, `constants.py:21-22` | Disk: 1GB warning. Circuit breaker: 5 failures before open, 60s reset. Rate limit: 100 req/60s. |
| 12.7 | Disaster recovery test | WAIVED | BLOCKER | E1 | Backup/restore service exists with integrity checks. Manual restore into temp location not verified during this audit. |
| 12.8 | Environment parity | PASS | HIGH | E2, `settings.py:32-51` | Single config pattern: env vars -> Settings -> all services. Pytest isolation via `PYTEST_CURRENT_TEST` hash-derived temp paths. |

**Summary:** 6 passed, 0 failed, 2 waived

---

## HIGH Findings Detail (Must Fix)

### H1: `discovery.py` — Layer Leakage + Business Logic in API + Async Blocking
- **File:** `app/api/discovery.py:77-264`
- **Issue:** 6 async API handlers perform raw `sqlite3.Connection.execute()` calls directly, bypassing service and persistence layers. Contains entity deduplication, character enrichment, and staging apply/undo business logic. Blocks event loop on sync SQLite I/O.
- **Impact:** Violates 4 architectural principles simultaneously. Hardest to test, blocks event loop.
- **Fix:** Extract to `CascadeDiscoveryService` with repository. Convert handlers to sync `def`.

### H2: Module-Level Singleton Globals
- **Files:** `app/api/discovery.py:28-29`, `app/services/backup.py:389`, `app/services/authentication.py:416`, `app/services/authorization.py:169`
- **Issue:** 5 module-level mutable globals initialized via `global` keyword. State leaks between tests, makes parallel pytest execution unsafe.
- **Fix:** Adopt `build_*_router()` factory pattern (already used for 80% of routers).

### H3: Event-Loop Blocking in Async Handlers
- **Files:** `app/api/discovery.py:76-264`, `app/api/health.py:50-57,200-248`
- **Issue:** Async handlers perform blocking sqlite3 operations. Worse than sync handlers because the block is silent.
- **Fix:** Convert to sync `def` handlers or use `run_in_executor`.

### H4: No Connection Pooling — N+1 File Opens
- **File:** `app/persistence/sqlite.py:1246-1251` (246 occurrences of `with connect(self.db_path)`)
- **Issue:** Every repository method opens/closes its own SQLite connection. Creating N entities = 2N file opens.
- **Fix:** Thread-local connection cache or shared connection per request context.

### H5: XSS via `dangerouslySetInnerHTML`
- **File:** `frontend/src/components/studio/StudioLayoutManager.tsx:352`
- **Issue:** Toast messages rendered via `innerHTML`. If toast content ever includes user-generated text, this is stored XSS.
- **Fix:** Replace with `<span>{toast.msg}</span>`. Current risk low (hardcoded strings only), but fragile.

---

## MEDIUM Findings Detail (Track & Fix)

| # | Finding | Location | Fix |
|---|---------|----------|-----|
| M1 | Backup path traversal | `app/services/backup.py:334` | Validate `backup_id` format, reject absolute paths |
| M2 | Prompt injection (import) | `app/services/runtime_prompts/import_prompts.py:147` | Fence user content with delimiters in LLM prompt |
| M3 | N+1 in story_forking | `app/services/story_forking.py:53-144` | Batch inserts with shared connection |
| M4 | N+1 in generation_phases | `app/services/local_executor/generation_phases.py:136-159` | Shared connection for chapter loop |
| M5 | N+1 in planning sync | `app/services/planning.py:371-390` | Batch sequence updates |
| M6 | Unbounded list endpoints (44) | Most API routers | Add `limit`/`offset` params |
| M7 | Backup create returns 200 | `app/api/backup.py:16` | Change to `status_code=201` |
| M8 | Guided-setup raw dict params | `app/api/projects.py:571,594` | Use Pydantic model types |
| M9 | Missing idempotency (backup/project create) | `app/api/backup.py`, `app/api/projects.py` | Add `Idempotency-Key` support |
| M10 | CI runs only 13 test files | `.github/workflows/tests.yml` | Expand to full parallel + serial clusters |
| M11 | No pre-commit hooks | Missing `.pre-commit-config.yaml` | Add ruff + mypy hooks |
| M12 | No CHANGELOG.md | Missing | Create with semantic versioning |

---

## What Went Well

- **Zero hardcoded secrets, eval/exec/pickle usage, or bare excepts** in production code
- **Strong test suite**: 1,661 tests across 147 files, `tmp_path` isolation, 429 mocks, 121 `pytest.raises`
- **Comprehensive security middleware**: CORS restricted, rate limiting, path traversal protection, API key auth with bcrypt + timing-safe comparison
- **Robust SQLite configuration**: WAL mode, 5s busy timeout, 107 indexes, full rebuild migrations, foreign key constraints
- **Clean frontend**: 0 `as any` casts, 0 `@ts-ignore`, 0 mock data, 0 TODO/FIXME in production
- **Excellent documentation**: README, AGENTS.md, structured audit logging, health probes, metrics endpoint
- **Backup service**: WAL checkpoint, integrity validation, pre-restore backup, disk space checks

---

## Top 5 Priorities

1. **Refactor `discovery.py`** into service + repository pattern (resolves H1, H2, H3)
2. **Implement connection pooling** in `app/persistence/sqlite.py` (resolves H4)
3. **Remove `dangerouslySetInnerHTML`** in `StudioLayoutManager.tsx` (resolves H5)
4. **Expand CI** to run full test clusters (M10)
5. **Add pagination** to unbounded list endpoints (M6)

---

## Residual Risk

Low. The 5 HIGH findings are architectural concerns that do not create immediate security vulnerabilities for a local desktop app. The most impactful (H1: `discovery.py`) is a single-file refactor. The XSS finding (H5) is currently low-risk since toast messages are hardcoded, but is fragile against future changes.
