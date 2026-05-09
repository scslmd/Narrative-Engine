# API Migration Upgrade Guide

Current state (2026-05-09):
- Canonical API contract is `/v1/*`.
- Frontend production services, hooks, and tests are synchronized to canonical `/v1` routes.
- Unversioned endpoints should be treated as exceptions only where explicitly documented below.

## Canonical API Surface

Use `/v1/*` for all versioned endpoints.

Examples:

- `/v1/projects/*`
- `/v1/auth/*`
- `/v1/backup/*`
- `/v1/models`
- `/v1/jobs/*`
- `/v1/story-development/*`
- `/v1/role-model-checker/*`

## Unversioned Exceptions

Health endpoints remain unversioned by policy:

- `/health/`
- `/health/ready`
- `/health/metrics`
- `/health/llm`

## Client Migration

1. Update all API paths to `/v1/*` except `/health/*`.
2. Keep `X-API-Key` behavior unchanged for protected routes.
3. Validate integrations with the verification commands in `docs/api-migration/cutover_gate.md`.
