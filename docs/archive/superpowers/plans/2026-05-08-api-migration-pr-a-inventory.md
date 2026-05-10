# API Migration PR-A: Route Inventory & Classification Implementation Plan
Status: Planned

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a complete, machine-generated route inventory, classification table, legacy-to-canonical mapping spec, compatibility policy, and v1 gap checklist — the artifacts needed before any code changes.

**Architecture:** Five scripts/docs that together form the authoritative migration specification. The inventory script introspects the live FastAPI app to extract every registered route. The classification and mapping are derived from that inventory cross-referenced against `app/main.py`'s dual-registration pattern (e.g., `build_jobs_router(job_manager)` then `build_jobs_router(job_manager, prefix='/v1/jobs')`).

**Tech Stack:** Python 3.12+, FastAPI, pytest, CSV/JSON/Markdown artifacts.

**Cross-plan dependencies:** None (PR-A is the root). PR-B depends on PR-A completing.

---

## Task 001: Route Inventory Snapshot Script

**Purpose:** Capture full runtime route table from the live FastAPI app.

**Write scope:**
- `scripts/api_route_inventory.py` (new)
- `docs/api-migration/route_inventory.json` (generated output)

**Steps:**

- [ ] Create `scripts/api_route_inventory.py`:

```python
"""Capture full runtime route table from the FastAPI app."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.main import build_app


def main() -> None:
    app = build_app()
    routes = []

    for route in app.routes:
        # Skip non-APIRoute entries (mounts, WebSocket, etc.)
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue

        methods = getattr(route, "methods", None)
        path = getattr(route, "path", "")
        name = getattr(route, "name", "")
        tags = getattr(route, "tags", [])

        if methods and path:
            for method in sorted(methods):
                if method in ("HEAD", "OPTIONS"):
                    continue
                routes.append({
                    "method": method,
                    "path": path,
                    "name": name,
                    "tags": list(tags),
                })

    # Sort by method then path for stable output
    routes.sort(key=lambda r: (r["method"], r["path"]))

    output_dir = project_root / "docs" / "api-migration"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "route_inventory.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(routes)} routes to {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] Run the script: `python scripts/api_route_inventory.py`
- [ ] Verify output exists and is non-empty:

```powershell
python -c "import json; data=json.load(open('docs/api-migration/route_inventory.json','r',encoding='utf-8')); print(f'Route count: {len(data)}'); assert len(data) > 0, 'Inventory is empty'"
```

**Acceptance criteria:**
- `docs/api-migration/route_inventory.json` exists with >= 100 route entries.
- Each entry has `method`, `path`, `name`, `tags` keys.
- No `HEAD` or `OPTIONS` methods in output.

---

## Task 002: Route Classification Table

**Purpose:** Classify every route from the inventory by its contract role.

**Write scope:**
- `docs/api-migration/route_classification.csv` (new)

**Steps:**

- [ ] Create a classification script that reads `route_inventory.json` and produces the CSV:

```python
"""Classify routes into canonical_v1, legacy_unversioned, dual, or internal."""
from __future__ import annotations

import csv
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
inventory_path = project_root / "docs" / "api-migration" / "route_inventory.json"
output_path = project_root / "docs" / "api-migration" / "route_classification.csv"

with open(inventory_path, "r", encoding="utf-8") as f:
    routes = json.load(f)

classifications = []
for route in routes:
    path = route["path"]
    method = route["method"]

    if path.startswith("/v1/"):
        classification = "canonical_v1"
    elif path.startswith("/health"):
        classification = "internal"
    elif path in ("/", "/role-model-checker-ui", "/vite.svg"):
        classification = "internal"
    elif path.startswith("/assets/") or path.startswith("/static/"):
        classification = "internal"
    elif path == "/projects/create/debug":
        classification = "internal"
    elif path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json":
        classification = "internal"
    else:
        # Unversioned routes that have a /v1 counterpart are legacy_unversioned
        # Check if a /v1 version of this route exists in the inventory
        v1_path = "/v1" + path
        has_v1_counterpart = any(
            r["path"] == v1_path and r["method"] == method
            for r in routes
        )
        if has_v1_counterpart:
            classification = "dual"
        else:
            classification = "legacy_unversioned"

    classifications.append({
        "method": method,
        "path": path,
        "name": route["name"],
        "tags": ";".join(route["tags"]),
        "classification": classification,
    })

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["method", "path", "name", "tags", "classification"])
    writer.writeheader()
    writer.writerows(classifications)

# Summary
from collections import Counter
counts = Counter(c["classification"] for c in classifications)
print(f"Classification summary:")
for cls, count in sorted(counts.items()):
    print(f"  {cls}: {count}")
print(f"Wrote {len(classifications)} rows to {output_path}")
```

- [ ] Run the classification script.
- [ ] Verify row count matches inventory and all classifications are valid:

```powershell
python -c "import csv, json; inv=json.load(open('docs/api-migration/route_inventory.json','r',encoding='utf-8')); rows=list(csv.DictReader(open('docs/api-migration/route_classification.csv','r',encoding='utf-8'))); print(f'Inventory: {len(inv)}, CSV: {len(rows)}'); assert len(inv)==len(rows), 'Count mismatch'; valid={'canonical_v1','legacy_unversioned','dual','internal'}; assert all(r['classification'] in valid for r in rows), 'Invalid classification found'"
```

**Acceptance criteria:**
- Row count equals inventory count.
- Every row has one of: `canonical_v1`, `legacy_unversioned`, `dual`, `internal`.
- At least 1 route per classification category.

---

## Task 003: Legacy-to-Canonical Mapping Spec

**Purpose:** Define the authoritative endpoint mapping for every legacy route to its `/v1` counterpart.

**Write scope:**
- `docs/api-migration/legacy_to_v1_mapping.md` (new)

**Steps:**

- [ ] Generate the mapping document from the classification CSV:

```python
"""Generate legacy-to-v1 mapping spec from classification data."""
from __future__ import annotations

import csv
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
csv_path = project_root / "docs" / "api-migration" / "route_classification.csv"
output_path = project_root / "docs" / "api-migration" / "legacy_to_v1_mapping.md"

with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Build a lookup: (method, path) -> classification
lookup = {(r["method"], r["path"]): r["classification"] for r in rows}

lines = [
    "# Legacy-to-v1 Endpoint Mapping Spec",
    "",
    "Generated from `route_classification.csv`. Each legacy route maps to its canonical `/v1` counterpart.",
    "",
    "| legacy_method | legacy_path | v1_method | v1_path | status_parity | schema_parity_notes |",
    "|---|---|---|---|---|---|",
]

for row in rows:
    method = row["method"]
    path = row["path"]
    cls = row["classification"]

    if cls == "dual":
        v1_path = "/v1" + path
        lines.append(f"| {method} | `{path}` | {method} | `{v1_path}` | exact | Identical handler, dual-registered in `app/main.py` |")
    elif cls == "legacy_unversioned":
        v1_path = "/v1" + path
        # Check if the v1 path actually exists
        has_v1 = (method, v1_path) in lookup
        if has_v1:
            lines.append(f"| {method} | `{path}` | {method} | `{v1_path}` | exact | Exists as canonical route |")
        else:
            lines.append(f"| {method} | `{path}` | {method} | `{v1_path}` | missing | No /v1 counterpart exists — requires implementation (see v1_gap_checklist.md) |")
    # Skip canonical_v1 and internal routes

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Wrote mapping for {len([l for l in lines if l.startswith('|')]) - 1} route pairs to {output_path}")
```

- [ ] Verify no unresolved placeholders remain:

```powershell
rg -n "TODO|TBD|UNMAPPED" docs/api-migration/legacy_to_v1_mapping.md; if ($LASTEXITCODE -eq 0) { Write-Error "Unresolved placeholders found"; exit 1 } else { Write-Host "No unresolved placeholders - PASS" }
```

**Acceptance criteria:**
- Mapping table covers all `dual` and `legacy_unversioned` routes.
- No `TODO`, `TBD`, or `UNMAPPED` strings in the file.
- Routes marked `missing` are cross-referenced to gap checklist.

---

## Task 004: Compatibility & Sunset Policy

**Purpose:** Establish deterministic deprecation behavior for legacy routes.

**Write scope:**
- `docs/api-migration/compatibility_policy.md` (new)

**Steps:**

- [ ] Write the compatibility policy document:

```markdown
# API Compatibility & Sunset Policy

## Deprecation Headers

All legacy wrapper endpoints MUST include the following response headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `Deprecation` | `true` | Signals the endpoint is deprecated (RFC 8594) |
| `Sunset` | `<HTTP-date>` | Target removal date (ISO 822 format) |
| `Link` | `</v1/...>; rel="successor-version"` | Points clients to the canonical replacement |

## Removal Gate

Legacy routes may be removed when ALL of the following conditions are met:

1. **Zero hits for 14 consecutive days** — measured via `legacy_route_hit` telemetry events in structured logs.
2. **Parity tests green** — `tests/test_api_route_parity.py` passes with 0 failures.
3. **Frontend canonical-only** — no production service file calls a legacy path (verified by grep, see PR-D Task 015).

## Compatibility Window

- Default window: **30 days** from the date legacy wrappers are deployed.
- Extension requires documented justification and team approval.
- Health endpoints (`/health/*`) are explicitly exempted from versioning per policy decision (see API-SURFACE-009).

## Change Control

- No business logic changes during migration. Legacy and canonical routes must produce byte-identical responses for identical inputs.
- Schema changes require simultaneous update of both legacy and canonical routes, or the legacy route must return a 410 Gone with migration instructions.
```

- [ ] Verify key terms are present:

```powershell
$policy = Get-Content docs/api-migration/compatibility_policy.md -Raw; @("Deprecation", "Sunset", "zero hits", "30 days") | ForEach-Object { if ($policy -notmatch [regex]::Escape($_)) { Write-Error "Missing: $_"; exit 1 } }; Write-Host "Policy contains all required terms - PASS"
```

**Acceptance criteria:**
- Document defines `Deprecation`, `Sunset`, and `Link` header requirements.
- Removal gate is date/threshold-based (zero hits for N days, N=14).
- Default compatibility window is concrete (30 days).
- Health endpoint exemption is documented.

---

## Task 005: v1 Gap Checklist

**Purpose:** Enumerate legacy routes lacking a `/v1` canonical counterpart and mark implementation status.

**Write scope:**
- `docs/api-migration/v1_gap_checklist.md` (new)

**Steps:**

- [ ] Generate the gap checklist from the mapping spec:

```python
"""Generate v1 gap checklist from legacy-to-v1 mapping."""
from __future__ import annotations

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
mapping_path = project_root / "docs" / "api-migration" / "legacy_to_v1_mapping.md"
output_path = project_root / "docs" / "api-migration" / "v1_gap_checklist.md"

with open(mapping_path, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.strip().split("\n")
gap_items = []
missing_items = []

for line in lines:
    if not line.startswith("|"):
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 6:
        continue
    legacy_method = parts[1]
    legacy_path = parts[2]
    v1_method = parts[3]
    v1_path = parts[4]
    status_parity = parts[5]

    if "missing" in status_parity.lower():
        missing_items.append({
            "legacy_method": legacy_method,
            "legacy_path": legacy_path.strip("`"),
            "v1_method": v1_method,
            "v1_path": v1_path.strip("`"),
        })
    else:
        gap_items.append({
            "legacy_method": legacy_method,
            "legacy_path": legacy_path.strip("`"),
            "v1_method": v1_method,
            "v1_path": v1_path.strip("`"),
            "status": "exists",
        })

# Build output
out = [
    "# v1 Gap Checklist",
    "",
    "Routes that have a legacy path but need verification of `/v1` canonical counterpart.",
    "",
    "## Existing Canonical Routes (verified)",
    "",
    "| # | legacy_method | legacy_path | v1_method | v1_path | status |",
    "|---|---|---|---|---|---|",
]

for i, item in enumerate(gap_items, 1):
    out.append(f"| {i} | {item['legacy_method']} | `{item['legacy_path']}` | {item['v1_method']} | `{item['v1_path']}` | exists |")

out.extend([
    "",
    "## Missing Canonical Routes (implementation required)",
    "",
    "| # | legacy_method | legacy_path | required_v1_method | required_v1_path | status |",
    "|---|---|---|---|---|---|",
])

for i, item in enumerate(missing_items, 1):
    out.append(f"| {i} | {item['legacy_method']} | `{item['legacy_path']}` | {item['v1_method']} | `{item['v1_path']}` | missing - requires implementation |")

out.extend([
    "",
    f"**Summary:** {len(gap_items)} existing, {len(missing_items)} missing. Total: {len(gap_items) + len(missing_items)}.",
    "",
    "## Action Items",
    "",
])

if missing_items:
    out.append("The following routes require `/v1` implementation (assign to PR-B):")
    for item in missing_items:
        out.append(f"- `{item['legacy_method']} {item['legacy_path']}` -> `{item['v1_method']} {item['v1_path']}`")
else:
    out.append("All legacy routes have a `/v1` counterpart. No new implementation required for PR-B.")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")

print(f"Wrote {len(gap_items)} existing + {len(missing_items)} missing routes to {output_path}")
```

- [ ] Verify the checklist is complete and actionable:

```powershell
$checklist = Get-Content docs/api-migration/v1_gap_checklist.md -Raw; if ($checklist -match "missing.*requires implementation") { Write-Host "Missing routes identified - review required for PR-B" } else { Write-Host "All routes have v1 counterparts - PASS" }; $summaryMatch = [regex]::Match($checklist, "Summary:.*Total:"); if ($summaryMatch.Success) { Write-Host "Summary present: $($summaryMatch.Value)" } else { Write-Error "No summary found"; exit 1 }
```

**Acceptance criteria:**
- Checklist has two sections: existing canonical routes and missing canonical routes.
- Summary line shows counts for both categories.
- Action items list is populated if any routes are missing.
- File is cross-referenced from the mapping spec.
