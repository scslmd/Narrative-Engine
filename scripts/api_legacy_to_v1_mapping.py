"""Generate legacy-to-v1 endpoint mapping from classification data."""
from __future__ import annotations

import csv
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
csv_path = project_root / "docs" / "api-migration" / "route_classification.csv"
output_path = project_root / "docs" / "api-migration" / "legacy_to_v1_mapping.md"


def main() -> None:
    with csv_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    lookup = {(r["method"], r["path"]): r["classification"] for r in rows}
    out: list[str] = [
        "# Legacy-to-v1 Endpoint Mapping Spec",
        "",
        "Generated from `route_classification.csv`.",
        "",
        "| legacy_method | legacy_path | v1_method | v1_path | status_parity | schema_parity_notes |",
        "|---|---|---|---|---|---|",
    ]

    count = 0
    for row in rows:
        method = row["method"]
        path = row["path"]
        cls = row["classification"]
        if cls not in {"dual", "legacy_unversioned"}:
            continue

        v1_path = "/v1" + path
        has_v1 = (method, v1_path) in lookup
        if cls == "dual":
            out.append(
                f"| {method} | `{path}` | {method} | `{v1_path}` | exact | "
                "Identical handler or equivalent canonical route exists |"
            )
        elif has_v1:
            out.append(
                f"| {method} | `{path}` | {method} | `{v1_path}` | exact | "
                "Canonical route exists |"
            )
        else:
            out.append(
                f"| {method} | `{path}` | {method} | `{v1_path}` | missing | "
                "No /v1 counterpart exists; see `v1_gap_checklist.md` |"
            )
        count += 1

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")

    print(f"Wrote mapping for {count} route pairs to {output_path}")


if __name__ == "__main__":
    main()
