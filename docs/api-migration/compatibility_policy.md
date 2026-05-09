# API Compatibility & Sunset Policy

## Deprecation Headers

All legacy wrapper endpoints must include:

| Header | Value | Purpose |
|---|---|---|
| `Deprecation` | `true` | Signals endpoint deprecation |
| `Sunset` | `<HTTP-date>` | Target removal date |
| `Link` | `</v1/...>; rel="successor-version"` | Canonical replacement |

## Removal Gate

Legacy routes may be removed only when all conditions pass:

1. Zero hits for 14 consecutive days, measured via `legacy_route_hit`.
2. Parity tests pass with no failures.
3. Frontend production services use canonical `/v1` routes only.

## Compatibility Window

- Default window: 30 days from legacy-wrapper deployment.
- Extensions require documented justification and approval.
- Health endpoints (`/health/*`) are explicitly exempt from versioning.

## Change Control

- No business-logic changes during migration.
- Legacy and canonical routes must remain behaviorally equivalent.
- Contract/schema changes require simultaneous updates across route variants.
