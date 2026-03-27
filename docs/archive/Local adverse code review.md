# Local Adversarial Code Review - Recommendations

**Generated**: 2026-03-24  
**Scope**: Security and reliability improvements for local-first Narrative-Engine  
**Priority**: Immediate (security) → Short-term (reliability) → Medium-term (production)

---

## Immediate Priority - Security

### Task 1: Add Authentication Middleware

**Problem**: All API endpoints are completely open with no authentication. Anyone who can reach the API can create/delete projects, execute arbitrary jobs, read/write all project data, and trigger inference requests.

**Solution**:
1. Create `app/middleware/auth.py` with API key validation
2. Add `API_KEY` environment variable requirement
3. Apply middleware to all routers except `/health`
4. Store API key in `.env` file (not in code)

**Expected Outcome**:
- All API requests require valid `X-API-Key` header
- Unauthorized requests return 401
- Local development can use a simple static key
- API key can be rotated via environment variable

---

### Task 2: Add CORS Middleware

**Problem**: No CORS configuration means if the API is exposed to a network, browsers can make cross-origin requests without restriction.

**Solution**:
1. Install `fastapi-cors` or use `CORSMiddleware` from `starlette.middleware.cors`
2. Configure allowed origins to `["http://localhost:8000", "http://127.0.0.1:8000"]`
3. Set `allow_credentials=True` for API key header support
4. Add middleware in `app/main.py` before router inclusion

**Expected Outcome**:
- Cross-origin requests from non-localhost domains are blocked
- Browser-based frontend on localhost works correctly
- CSRF attacks via web browsers are prevented

---

### Task 3: Add Request Size Limits

**Problem**: FastAPI has no default body size limit. Large payloads could exhaust memory or be used for DoS attacks.

**Solution**:
1. Set `max_body_size=10_485_760` (10 MB) on FastAPI app in `app/main.py`
2. Add validation in `JobCreateRequest` schema to reject payloads > 5 MB
3. Add error response with clear message when limit exceeded

**Expected Outcome**:
- Requests > 10 MB are rejected with 413 Payload Too Large
- Memory exhaustion attacks are prevented
- Clear error messages guide users to reduce payload size

---

### Task 4: Validate File Paths Against Traversal

**Problem**: `read_artifact()` and file operations don't validate that paths stay within expected project directories, enabling path traversal attacks.

**Solution**:
1. Create `app/utils/path_validation.py` with `validate_path_within()` function
2. Use `path.resolve().startswith(expected_root)` to validate
3. Apply validation in:
   - `ProjectService.read_artifact()`
   - `LocalExecutor._write_staged_output()`
   - All file read/write operations
4. Return 400 Bad Request if path validation fails

**Expected Outcome**:
- Path traversal attempts (e.g., `../../../etc/passwd`) are blocked
- All file operations stay within designated directories
- Clear error messages for invalid paths

---

### Task 5: Add Rate Limiting

**Problem**: No rate limiting allows unlimited job creation, checker runs, and API calls, enabling resource exhaustion or cost attacks.

**Solution**:
1. Install `slowapi` or implement token bucket rate limiter
2. Configure limits:
   - Job creation: 10 per minute per API key
   - Checker runs: 5 per minute per API key
   - Status checks: 60 per minute per API key
3. Add `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers
4. Return 429 Too Many Requests when exceeded

**Expected Outcome**:
- Burst attacks are throttled
- Resource exhaustion is prevented
- Users get clear feedback on rate limits

---

## Short-Term Priority - Reliability

### Task 6: Add Circuit Breaker for Inference Backend

**Problem**: If inference backend is down or slow, jobs keep failing without backoff, wasting resources and providing poor UX.

**Solution**:
1. Create `app/services/circuit_breaker.py` with circuit breaker pattern
2. Configure:
   - Failure threshold: 5 consecutive failures
   - Recovery timeout: 60 seconds
   - Half-open requests: 1
3. Wrap all inference calls in `app/inference/openai_compatible.py`
4. Return circuit breaker error state in job failures

**Expected Outcome**:
- Failed inference backends are temporarily bypassed
- Automatic recovery after timeout
- Jobs fail fast with clear "circuit open" error
- Reduced load on failing backends

---

### Task 7: Add Idempotency to All Write Operations

**Problem**: Only jobs have idempotency keys. Project creation and story development operations lack idempotency, causing duplicate data on retries.

**Solution**:
1. Add `idempotency_key` parameter to:
   - `ProjectService.create_project()`
   - All story development write operations
2. Store idempotency keys in `project_operations` table
3. Return existing result if key already processed
4. Set TTL of 24 hours on idempotency keys

**Expected Outcome**:
- Retry-safe project creation
- Duplicate prevention for all write operations
- Clear errors for conflicting idempotency keys

---

### Task 8: Fix Thread Safety in LocalExecutor

**Problem**: `LocalExecutor.start()` has a race condition where concurrent calls could create duplicate threads.

**Solution**:
1. Add `threading.Lock()` to `LocalExecutor`
2. Wrap `start()` method with lock acquisition
3. Use atomic flag check inside lock:
   ```python
   with self._start_lock:
       if self._threads:
           return
       self._threads = [...]
   ```
4. Add similar protection to `stop()` method

**Expected Outcome**:
- Only one set of worker threads created
- No race conditions on start/stop
- Thread-safe lifecycle management

---

### Task 9: Add Backup Strategy for SQLite Database

**Problem**: Single SQLite file with no backup strategy. Database corruption or disk failure results in complete data loss.

**Solution**:
1. Create `app/services/backup.py` with backup functionality
2. Implement:
   - Daily automated backup to `data/backups/`
   - WAL checkpoint before backup
   - Retention policy: keep 7 days of backups
3. Add `/backup/create` and `/backup/restore` endpoints
4. Document manual backup procedure

**Expected Outcome**:
- Daily backups created automatically
- Point-in-time recovery possible
- Data loss limited to 24 hours maximum

---

## Medium-Term Priority - Production Readiness

### Task 10: Add Monitoring and Telemetry

**Problem**: No monitoring of job failures, inference latency, or system health makes debugging difficult.

**Solution**:
1. Add structured logging with correlation IDs
2. Track metrics:
   - Job success/failure rates
   - Inference latency percentiles
   - Database query times
   - Active connections
3. Export to Prometheus format at `/metrics`
4. Add alerting thresholds (e.g., >10% failure rate)

**Expected Outcome**:
- Visibility into system health
- Fast debugging with correlation IDs
- Proactive alerting on anomalies
- Performance optimization data

---

### Task 11: Add Deep Health Checks

**Problem**: `/health` endpoint only returns static "ok". No validation of database connectivity or inference backend availability.

**Solution**:
1. Create `/health/ready` endpoint with deep checks:
   - SQLite database connectivity test
   - Inference backend ping (if configured)
   - Disk space check (>1GB free)
   - Memory usage check
2. Return detailed status with component health
3. Return 503 if any critical component unhealthy

**Expected Outcome**:
- Accurate system health reporting
- Load balancers can route based on readiness
- Early detection of component failures

---

### Task 12: Add Configuration Validation

**Problem**: Invalid configuration (e.g., bad inference URL, missing directories) may not be detected until runtime, causing confusing errors.

**Solution**:
1. Create `app/services/config_validator.py`
2. Validate at startup:
   - Inference backend URL is reachable
   - Required directories exist and are writable
   - SQLite database is accessible
   - API key is set (if required)
3. Fail fast with clear error messages
4. Add `/config/validate` endpoint for manual checks

**Expected Outcome**:
- Configuration errors detected at startup
- Clear error messages guide fixes
- No silent failures from bad config

---

### Task 13: Add Input Validation for Job Payloads

**Problem**: `JobCreateRequest.payload` accepts arbitrary dict with no size or structure validation, enabling malformed payloads to crash the executor.

**Solution**:
1. Add payload size validation (< 5 MB)
2. Add per-phase payload schema validation:
   - P-100: Validate `project_id`, `premise` fields
   - P-200: Validate `project_id`, `architect_output` fields
   - P-300: Validate `project_id`, `sequence_output` fields
   - P-400: Validate `project_id` field
3. Return 400 Bad Request with field-level errors

**Expected Outcome**:
- Malformed payloads rejected early
- Clear error messages for invalid fields
- Executor crashes from bad payloads prevented

---

### Task 14: Add File Permission Validation

**Problem**: File operations don't validate ownership or permissions, potentially overwriting files in world-writable directories.

**Solution**:
1. Create `app/utils/file_permissions.py`
2. Before write operations:
   - Verify parent directory is owned by current user
   - Verify file (if exists) is writable
   - Reject if permissions are too open (world-writable)
3. Log permission warnings

**Expected Outcome**:
- Accidental overwrites prevented
- Security warnings for misconfigured directories
- Clear errors for permission issues

---

### Task 15: Add Audit Logging

**Problem**: No audit trail of who did what. Difficult to trace data changes or investigate incidents.

**Solution**:
1. Create `audit_log` table in SQLite
2. Log all write operations:
   - Timestamp
   - API key (hashed)
   - Operation type
   - Target resource
   - Before/after state (for critical changes)
3. Add `/audit/query` endpoint with filtering
4. Retain audit logs for 90 days

**Expected Outcome**:
- Complete audit trail of all changes
- Incident investigation capability
- Compliance with data governance requirements

---

## Implementation Priority Matrix

| Task | Effort | Risk Reduction | Priority |
|------|--------|----------------|----------|
| 1. Authentication | Medium | Critical | P0 |
| 2. CORS | Low | High | P0 |
| 3. Request Size Limits | Low | High | P0 |
| 4. Path Validation | Medium | Critical | P0 |
| 5. Rate Limiting | Medium | High | P0 |
| 6. Circuit Breaker | Medium | Medium | P1 |
| 7. Idempotency | Medium | Medium | P1 |
| 8. Thread Safety | Low | Medium | P1 |
| 9. Backup Strategy | Medium | Critical | P1 |
| 10. Monitoring | High | Low | P2 |
| 11. Health Checks | Medium | Medium | P2 |
| 12. Config Validation | Medium | Medium | P2 |
| 13. Input Validation | Medium | High | P2 |
| 14. Permission Validation | Low | Medium | P2 |
| 15. Audit Logging | High | Low | P2 |

---

## Testing Requirements

For each task, implement:

1. **Unit Tests**: Test the new functionality in isolation
2. **Integration Tests**: Test end-to-end with real API calls
3. **Security Tests**: Attempt to exploit the vulnerability (e.g., path traversal attempts)
4. **Load Tests**: Verify rate limiting and size limits work under load

---

## Success Criteria

**Security (P0 tasks)**:
- All API endpoints require authentication
- Path traversal attempts are blocked
- Rate limits are enforced
- Request size limits prevent DoS

**Reliability (P1 tasks)**:
- No race conditions in executor
- Idempotent operations prevent duplicates
- Circuit breaker protects against backend failures
- Backups can be restored successfully

**Production (P2 tasks)**:
- Health checks accurately report system state
- Configuration errors fail fast
- Audit logs capture all changes
- Monitoring provides actionable insights

---

## Notes

- This tool is designed for **local-first** use. Security measures should balance protection with usability.
- For local development, a simple API key is sufficient. For multi-user deployment, consider OAuth or JWT.
- All changes should maintain backward compatibility where possible.
- Document all security decisions in `SECURITY.md`.
