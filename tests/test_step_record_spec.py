from __future__ import annotations

import json
from pathlib import Path


def _load_contract() -> dict:
    contract_path = Path(__file__).parent / "fixtures" / "step_record_contract_v0_1.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))


def test_step_record_examples_cover_all_required_fields() -> None:
    contract = _load_contract()
    required_fields = set(contract["step_record_required_fields"])

    for example_name in ("pipeline_step_record", "checker_step_record"):
        example = contract["examples"][example_name]
        assert required_fields.issubset(example.keys())


def test_artifact_lineage_example_covers_all_required_fields() -> None:
    contract = _load_contract()
    required_fields = set(contract["artifact_lineage_required_fields"])
    example = contract["examples"]["artifact_lineage_record"]

    assert required_fields.issubset(example.keys())
    assert example["status"] == "CANONICAL"
    assert example["validation_state"] == "PASSED"
    assert example["output_of_step_record_id"] == contract["examples"]["pipeline_step_record"]["step_record_id"]


def test_lineage_rules_capture_non_overwrite_expectations() -> None:
    contract = _load_contract()
    rules = set(contract["lineage_rules"])

    assert "temporary_writes_are_not_canonical" in rules
    assert "validation_required_before_canonical_registration" in rules
    assert "failed_attempt_cannot_replace_canonical" in rules
    assert "canonical_replacement_must_supersede_explicitly" in rules
    assert "step_record_links_to_lineage_output" in rules
