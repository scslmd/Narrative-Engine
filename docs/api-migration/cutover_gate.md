# API Migration Cutover Gate

All criteria must pass before legacy route removal:

1. Parity tests green:
   - `python -m pytest -q -p no:cacheprovider tests/test_api_route_parity.py`
2. Error semantics tests green:
   - `python -m pytest -q -p no:cacheprovider tests/test_api_error_semantics.py`
3. Frontend canonical-only checks green:
   - `rg -n "api\.(get|post|patch|put|delete)\((`|'|\")/(?!v1)" frontend/src/services frontend/src/lib -S`
4. Legacy hits = 0 for 14 days:
   - `python scripts/check_legacy_usage.py --days 14`
5. Full verification suite green:
   - `python scripts/api_migration_verify.py`

If any criterion fails, remediation is required before removal.
