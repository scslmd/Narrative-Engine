# Legacy Route Usage Query Guide

Each legacy route access should emit:

```json
{"event":"legacy_route_hit","timestamp":1715000000.0,"method":"GET","path":"/auth/keys","client_host":"127.0.0.1","user_agent":"..."}
```

## Zero-Usage Check

```bash
python scripts/check_legacy_usage.py --days 14
```

Pass condition:

- `Legacy hits in last 14 days: 0`
