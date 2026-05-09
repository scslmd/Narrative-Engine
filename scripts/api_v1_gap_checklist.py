"""Generate v1 gap checklist from legacy-to-v1 mapping."""
from __future__ import annotations

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
mapping_path = project_root / "docs" / "api-migration" / "legacy_to_v1_mapping.md"
output_path = project_root / "docs" / "api-migration" / "v1_gap_checklist.md"


def parse_row(line: str) -> list[str]:
    parts = [p.strip() for p in line.split("|")]
    return parts


def main() -> None:
    content = mapping_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    existing: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []

    for line in lines:
        if not line.startswith("| "):
            continue
        if "legacy_method" in line or line.startswith("|---|"):
            continue
        parts = parse_row(line)
        if len(parts) < 7:
            continue
        item = {
            "legacy_method": parts[1],
            "legacy_path": parts[2].strip("`"),
            "v1_method": parts[3],
            "v1_path": parts[4].strip("`"),
        }
        status = parts[5].lower()
        if "missing" in status:
            missing.append(item)
        else:
            existing.append(item)

    out: list[str] = [
        "# v1 Gap Checklist",
        "",
        "## Existing Canonical Routes (verified)",
        "",
        "| # | legacy_method | legacy_path | v1_method | v1_path | status |",
        "|---|---|---|---|---|---|",
    ]
    for idx, row in enumerate(existing, 1):
        out.append(
            f"| {idx} | {row['legacy_method']} | `{row['legacy_path']}` | {row['v1_method']} | "
            f"`{row['v1_path']}` | exists |"
        )

    out.extend(
        [
            "",
            "## Missing Canonical Routes (implementation required)",
            "",
            "| # | legacy_method | legacy_path | required_v1_method | required_v1_path | status |",
            "|---|---|---|---|---|---|",
        ]
    )
    for idx, row in enumerate(missing, 1):
        out.append(
            f"| {idx} | {row['legacy_method']} | `{row['legacy_path']}` | {row['v1_method']} | "
            f"`{row['v1_path']}` | missing - requires implementation |"
        )

    out.extend(
        [
            "",
            f"**Summary:** {len(existing)} existing, {len(missing)} missing. Total: {len(existing) + len(missing)}.",
            "",
            "## Action Items",
            "",
        ]
    )
    if missing:
        out.append("The following routes require `/v1` implementation (assign to PR-B):")
        for row in missing:
            out.append(
                f"- `{row['legacy_method']} {row['legacy_path']}` -> `{row['v1_method']} {row['v1_path']}`"
            )
    else:
        out.append("All legacy routes have a `/v1` counterpart. No new implementation required for PR-B.")

    output_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {len(existing)} existing + {len(missing)} missing routes to {output_path}")


if __name__ == "__main__":
    main()
