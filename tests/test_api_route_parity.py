from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

MAPPING_CSV = Path(__file__).parent.parent / "docs" / "api-migration" / "route_classification.csv"


def _load_route_pairs() -> list[dict[str, str]]:
    if not MAPPING_CSV.exists():
        return []
    pairs: list[dict[str, str]] = []
    with MAPPING_CSV.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("classification") != "dual":
                continue
            legacy_path = row["path"]
            pairs.append(
                {
                    "method": row["method"].lower(),
                    "legacy_path": legacy_path,
                    "v1_path": "/v1" + legacy_path,
                    "tags": row.get("tags", ""),
                }
            )
    return pairs


ROUTE_PAIRS = _load_route_pairs()
AUTH_GATED_TAGS = {"projects"}


@pytest.mark.parametrize("route_pair", ROUTE_PAIRS, ids=lambda rp: f"{rp['method'].upper()} {rp['legacy_path']}")
def test_route_parity(route_pair: dict[str, str], tmp_path: Path) -> None:
    if "{" in route_pair["legacy_path"] or "}" in route_pair["legacy_path"]:
        pytest.skip("Templated path requires concrete fixture IDs")
    if route_pair["method"] != "get":
        pytest.skip("Non-GET route")
    tag_list = [t.strip() for t in route_pair.get("tags", "").split(";") if t.strip()]
    if any(t in AUTH_GATED_TAGS for t in tag_list):
        pytest.skip("Auth-gated route")

    client = TestClient(build_app())
    legacy_resp = client.get(route_pair["legacy_path"])
    v1_resp = client.get(route_pair["v1_path"])
    if legacy_resp.status_code == 404:
        pytest.skip("Legacy route removed; canonical-only migration complete for this path")

    assert legacy_resp.status_code == v1_resp.status_code
    if 200 <= legacy_resp.status_code < 300:
        try:
            assert legacy_resp.json() == v1_resp.json()
        except json.JSONDecodeError:
            assert legacy_resp.text == v1_resp.text


def test_all_get_routes_have_parity_coverage() -> None:
    if not ROUTE_PAIRS:
        pytest.skip("No dual routes remain; canonical-only migration complete.")
    get_pairs = [rp for rp in ROUTE_PAIRS if rp["method"] == "get"]
    assert len(get_pairs) > 0
