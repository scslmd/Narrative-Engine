"""Classify routes from the inventory into migration categories."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
inventory_path = project_root / "docs" / "api-migration" / "route_inventory.json"
output_path = project_root / "docs" / "api-migration" / "route_classification.csv"


def classify_route(path: str, method: str, routes: list[dict[str, object]]) -> str:
    if path.startswith("/v1/"):
        return "canonical_v1"
    if path.startswith("/health"):
        return "internal"
    if path in {"/", "/role-model-checker-ui", "/vite.svg"}:
        return "internal"
    if path.startswith("/assets/") or path.startswith("/static/"):
        return "internal"
    if path == "/projects/create/debug":
        return "internal"
    if path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json":
        return "internal"

    v1_path = "/v1" + path
    has_v1_counterpart = any(
        r.get("path") == v1_path and r.get("method") == method for r in routes
    )
    return "dual" if has_v1_counterpart else "legacy_unversioned"


def main() -> None:
    with inventory_path.open("r", encoding="utf-8") as handle:
        routes = json.load(handle)

    rows: list[dict[str, str]] = []
    for route in routes:
        path = str(route["path"])
        method = str(route["method"])
        name = str(route.get("name", ""))
        tags = route.get("tags", [])
        cls = classify_route(path, method, routes)
        rows.append(
            {
                "method": method,
                "path": path,
                "name": name,
                "tags": ";".join([str(t) for t in tags]),
                "classification": cls,
            }
        )

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["method", "path", "name", "tags", "classification"]
        )
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(r["classification"] for r in rows)
    print("Classification summary:")
    for cls, count in sorted(counts.items()):
        print(f"  {cls}: {count}")
    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
