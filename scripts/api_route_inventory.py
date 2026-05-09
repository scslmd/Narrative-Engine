"""Capture full runtime route table from the FastAPI app."""
from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.main import build_app


def main() -> None:
    app = build_app()
    routes: list[dict[str, object]] = []

    for route in app.routes:
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue

        methods = getattr(route, "methods", None)
        path = getattr(route, "path", "")
        name = getattr(route, "name", "")
        tags = getattr(route, "tags", [])

        if not methods or not path:
            continue

        for method in sorted(methods):
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.append(
                {
                    "method": method,
                    "path": path,
                    "name": name,
                    "tags": list(tags),
                }
            )

    routes.sort(key=lambda r: (str(r["method"]), str(r["path"])))

    output_dir = project_root / "docs" / "api-migration"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "route_inventory.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(routes, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {len(routes)} routes to {output_path}")


if __name__ == "__main__":
    main()
