from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.persistence.sqlite import connect, ensure_operations_db


def _load_contract() -> dict[str, object]:
    contract_path = Path(__file__).parent / "fixtures" / "step_record_contract_v0_1.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))


def _table_exists(connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _require_slice_tables(connection) -> None:
    missing = [
        table_name
        for table_name in ("step_records", "artifact_lineage", "runtime_artifact_selections")
        if not _table_exists(connection, table_name)
    ]
    if missing:
        pytest.skip(
            "step-record/artifact-lineage persistence tables are not present in the current workspace: "
            + ", ".join(missing)
        )


def _column_names(connection, table_name: str) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    }


def _foreign_key_edges(connection, table_name: str) -> set[tuple[str, str, str]]:
    return {
        (row["from"], row["table"], row["to"])
        for row in connection.execute(f"PRAGMA foreign_key_list('{table_name}')").fetchall()
    }


def _db_field_name(contract_field: str) -> str:
    json_backed_fields = {
        "input_artifact_refs": "input_artifact_refs_json",
        "output_artifact_refs": "output_artifact_refs_json",
        "source_artifact_refs": "source_artifact_refs_json",
        "source_content_hashes": "source_content_hashes_json",
    }
    return json_backed_fields.get(contract_field, contract_field)


def _step_record_row(contract: dict[str, object]) -> dict[str, object]:
    example = dict(contract["examples"]["pipeline_step_record"])
    return {
        **{
            _db_field_name(key): value
            for key, value in example.items()
            if key != "step_record_id"
        },
        "input_artifact_refs_json": json.dumps(example["input_artifact_refs"], ensure_ascii=True, sort_keys=True),
        "output_artifact_refs_json": json.dumps(example["output_artifact_refs"], ensure_ascii=True, sort_keys=True),
        "created_at": example["started_at"],
        "updated_at": example["finished_at"],
    }


def _artifact_lineage_row(contract: dict[str, object], **overrides: object) -> dict[str, object]:
    example = dict(contract["examples"]["artifact_lineage_record"])
    example.update(overrides)
    return {
        **{
            _db_field_name(key): value
            for key, value in example.items()
            if key != "artifact_lineage_id"
        },
        "source_artifact_refs_json": json.dumps(example["source_artifact_refs"], ensure_ascii=True, sort_keys=True),
        "source_content_hashes_json": json.dumps(example["source_content_hashes"], ensure_ascii=True, sort_keys=True),
    }


def _insert_row(connection, table_name: str, row: dict[str, object]) -> None:
    columns = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    connection.execute(
        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
        tuple(row.values()),
    )


def _insert_step_record(connection, contract: dict[str, object]) -> int:
    _insert_row(connection, "step_records", _step_record_row(contract))
    row = connection.execute("SELECT last_insert_rowid()").fetchone()
    assert row is not None
    return int(row[0])


def test_step_record_and_artifact_lineage_tables_cover_contract_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    contract = _load_contract()

    with connect(db_path) as connection:
        _require_slice_tables(connection)
        step_columns = _column_names(connection, "step_records")
        lineage_columns = _column_names(connection, "artifact_lineage")

    assert {_db_field_name(name) for name in contract["step_record_required_fields"]}.issubset(step_columns)
    assert {_db_field_name(name) for name in contract["artifact_lineage_required_fields"]}.issubset(lineage_columns)


def test_artifact_lineage_links_outputs_back_to_step_records(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)

    with connect(db_path) as connection:
        _require_slice_tables(connection)
        lineage_foreign_keys = _foreign_key_edges(connection, "artifact_lineage")

    assert ("output_of_step_record_id", "step_records", "step_record_id") in lineage_foreign_keys


def test_runtime_artifact_selection_links_back_to_artifact_lineage(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)

    with connect(db_path) as connection:
        _require_slice_tables(connection)
        selection_foreign_keys = _foreign_key_edges(connection, "runtime_artifact_selections")

    assert ("selected_artifact_lineage_id", "artifact_lineage", "artifact_lineage_id") in selection_foreign_keys


def test_artifact_lineage_supports_explicit_supersession_history(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    contract = _load_contract()

    with connect(db_path) as connection:
        _require_slice_tables(connection)
        step_record_id = _insert_step_record(connection, contract)
        _insert_row(
            connection,
            "artifact_lineage",
            _artifact_lineage_row(contract, output_of_step_record_id=step_record_id),
        )
        first_lineage_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        _insert_row(
            connection,
            "artifact_lineage",
            _artifact_lineage_row(
                contract,
                path="data/projects/science-fantasy-test/story_bible_v2.json",
                content_hash="artifact-hash-002",
                produced_at="2026-03-19T10:20:04+00:00",
                registered_at="2026-03-19T10:20:05+00:00",
                supersedes_artifact_lineage_id=first_lineage_id,
                output_of_step_record_id=step_record_id,
            ),
        )
        second_lineage_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
        connection.execute(
            "DELETE FROM artifact_lineage WHERE artifact_lineage_id = ?",
            (first_lineage_id,),
        )
        successor = connection.execute(
            "SELECT supersedes_artifact_lineage_id FROM artifact_lineage WHERE artifact_lineage_id = ?",
            (second_lineage_id,),
        ).fetchone()

    assert successor is not None
    assert successor["supersedes_artifact_lineage_id"] is None


def test_deleting_step_record_cascades_its_lineage_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    contract = _load_contract()

    with connect(db_path) as connection:
        _require_slice_tables(connection)
        step_record_id = _insert_step_record(connection, contract)
        _insert_row(
            connection,
            "artifact_lineage",
            _artifact_lineage_row(contract, output_of_step_record_id=step_record_id),
        )
        connection.execute(
            "DELETE FROM step_records WHERE step_record_id = ?",
            (step_record_id,),
        )
        remaining = connection.execute(
            "SELECT COUNT(*) FROM artifact_lineage",
        ).fetchone()[0]

    assert remaining == 0
