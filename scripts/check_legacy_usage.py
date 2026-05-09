"""Check legacy route telemetry usage in structured logs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--log-path", type=str, default="")
    args = parser.parse_args()

    log_path = Path(args.log_path) if args.log_path else settings.audit_log_path
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).timestamp()

    hits = 0
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if event.get("event") != "legacy_route_hit":
                    continue
                ts = event.get("timestamp")
                if isinstance(ts, (int, float)) and ts > cutoff:
                    hits += 1
    print(f"Legacy hits in last {args.days} days: {hits}")
    if hits == 0:
        print("PASS: Safe to remove legacy routes")
    else:
        print("FAIL: Legacy hits detected")


if __name__ == "__main__":
    main()
