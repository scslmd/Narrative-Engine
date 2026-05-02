from __future__ import annotations

import time
from datetime import datetime

import pytest

from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository


def test_story_generation_tables_and_indexes_created(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)

    with connect(db_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        indexes = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert "canon_generation_runs" in tables
    assert "canon_generation_packets" in tables
    assert "generation_gate_results" in tables
    assert "idx_generation_runs_source_created" in indexes
    assert "idx_generation_runs_target_created" in indexes
    assert "idx_generation_runs_status" in indexes
    assert "idx_generation_runs_idempotency" in indexes
    assert "idx_generation_packets_generation" in indexes
    assert "idx_generation_gate_results_generation" in indexes


def test_story_generation_repository_upserts_and_idempotency_conflict(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    run = repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={"brief": "v1"},
        canon_scope_json={"character_ids": ["char-1"]},
        canon_policy_json={"continuity_strictness": "warn"},
        status="queued",
        idempotency_key="idem-1",
        request_hash="hash-1",
    )
    assert run.generation_id == "gen-1"
    assert run.request_json["brief"] == "v1"

    run_updated = repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={"brief": "v2"},
        canon_scope_json={"character_ids": ["char-1"]},
        canon_policy_json={"continuity_strictness": "warn"},
        status="running",
        idempotency_key="idem-1",
        request_hash="hash-1",
    )
    assert run_updated.request_json["brief"] == "v2"
    assert run_updated.status == "running"

    with pytest.raises(ValueError, match="idempotency key conflict"):
        repo.upsert_canon_generation_run(
            generation_id="gen-2",
            source_project_id="source-1",
            target_project_id="target-2",
            mode="same_project_side_story",
            request_json={"brief": "other"},
            canon_scope_json={"character_ids": ["char-1"]},
            canon_policy_json={"continuity_strictness": "warn"},
            status="queued",
            idempotency_key="idem-1",
            request_hash="hash-different",
        )

    packet = repo.upsert_canon_generation_packet(
        packet_id="packet-1",
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        packet_json={"packet_id": "packet-1"},
        source_hashes_json={"characters": "abc"},
        prompt_budget_json={"fit_to_budget": True},
    )
    assert packet.packet_id == "packet-1"

    gate = repo.upsert_generation_gate_result(
        gate_result_id="gate-1",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-1",
        gate_name="canon_congruence",
        passed=False,
        severity="blocking",
        reasons=["conflict"],
    )
    assert gate.gate_result_id == "gate-1"
    assert gate.passed is False


def test_get_canon_generation_run_returns_correct_fields(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={"brief": "test brief"},
        canon_scope_json={"character_ids": ["char-1", "char-2"]},
        canon_policy_json={"continuity_strictness": "block", "forbidden_contradictions": []},
        status="queued",
        gate_status="pending",
        idempotency_key="idem-1",
        request_hash="hash-1",
    )

    retrieved = repo.get_canon_generation_run("gen-1")
    assert retrieved.generation_id == "gen-1"
    assert retrieved.source_project_id == "source-1"
    assert retrieved.target_project_id == "target-1"
    assert retrieved.mode == "same_project_side_story"
    assert retrieved.request_json["brief"] == "test brief"
    assert retrieved.canon_scope_json["character_ids"] == ["char-1", "char-2"]
    assert retrieved.canon_policy_json["continuity_strictness"] == "block"
    assert retrieved.status == "queued"
    assert retrieved.gate_status == "pending"
    assert retrieved.idempotency_key == "idem-1"
    assert retrieved.request_hash == "hash-1"
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)


def test_get_canon_generation_run_raises_key_error_nonexistent(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    with pytest.raises(KeyError):
        repo.get_canon_generation_run("nonexistent-gen")


def test_list_canon_generation_runs_source_role_filters_correctly(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="proj-a",
        target_project_id="proj-b",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-1",
        request_hash="h1",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-2",
        source_project_id="proj-c",
        target_project_id="proj-a",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-2",
        request_hash="h2",
    )

    results = repo.list_canon_generation_runs("proj-a", role="source")
    assert len(results) == 1
    assert results[0].generation_id == "gen-1"


def test_list_canon_generation_runs_target_role_filters_correctly(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="proj-a",
        target_project_id="proj-b",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-1",
        request_hash="h1",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-2",
        source_project_id="proj-c",
        target_project_id="proj-a",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-2",
        request_hash="h2",
    )

    results = repo.list_canon_generation_runs("proj-a", role="target")
    assert len(results) == 1
    assert results[0].generation_id == "gen-2"


def test_list_canon_generation_runs_either_role_returns_both(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="proj-a",
        target_project_id="proj-b",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-1",
        request_hash="h1",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-2",
        source_project_id="proj-c",
        target_project_id="proj-a",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-2",
        request_hash="h2",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-3",
        source_project_id="proj-a",
        target_project_id="proj-a",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-3",
        request_hash="h3",
    )

    results = repo.list_canon_generation_runs("proj-a", role="either")
    assert len(results) == 3
    gen_ids = {r.generation_id for r in results}
    assert "gen-1" in gen_ids
    assert "gen-2" in gen_ids
    assert "gen-3" in gen_ids


def test_list_canon_generation_runs_rejects_invalid_role(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    with pytest.raises(ValueError, match="role must be one of"):
        repo.list_canon_generation_runs("proj-a", role="invalid_role")


def test_get_canon_generation_packet_returns_record_after_upsert(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-pkt",
        request_hash="h-pkt",
    )

    repo.upsert_canon_generation_packet(
        packet_id="packet-1",
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        packet_json={"test_key": "test_value"},
        source_hashes_json={"characters": "abc123"},
        prompt_budget_json={"total_chars": 5000, "fit_to_budget": True},
    )

    retrieved = repo.get_canon_generation_packet("packet-1")
    assert retrieved.packet_id == "packet-1"
    assert retrieved.generation_id == "gen-1"
    assert retrieved.source_project_id == "source-1"
    assert retrieved.target_project_id == "target-1"
    assert retrieved.packet_json["test_key"] == "test_value"
    assert retrieved.source_hashes_json["characters"] == "abc123"
    assert retrieved.prompt_budget_json["total_chars"] == 5000
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)


def test_get_canon_generation_packet_raises_key_error_nonexistent(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    with pytest.raises(KeyError):
        repo.get_canon_generation_packet("nonexistent-packet")


def test_list_canon_generation_packets_for_generation_returns_by_generation_id(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-pkt-list",
        request_hash="h-pkt-list",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-other",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-pkt-other",
        request_hash="h-pkt-other",
    )

    repo.upsert_canon_generation_packet(
        packet_id="packet-1",
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        packet_json={"version": 1},
        source_hashes_json={"characters": "hash-a"},
        prompt_budget_json={"fit_to_budget": True},
    )

    time.sleep(0.05)

    repo.upsert_canon_generation_packet(
        packet_id="packet-2",
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        packet_json={"version": 2},
        source_hashes_json={"characters": "hash-b"},
        prompt_budget_json={"fit_to_budget": True},
    )

    repo.upsert_canon_generation_packet(
        packet_id="packet-other",
        generation_id="gen-other",
        source_project_id="source-1",
        target_project_id="target-1",
        packet_json={"version": 1},
        source_hashes_json={"characters": "hash-c"},
        prompt_budget_json={"fit_to_budget": True},
    )

    results = repo.list_canon_generation_packets_for_generation("gen-1")
    assert len(results) == 2
    assert results[0].packet_id == "packet-2"
    assert results[1].packet_id == "packet-1"


def test_get_generation_gate_result_returns_record_after_upsert(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-gate-get",
        request_hash="h-gate-get",
    )

    repo.upsert_generation_gate_result(
        gate_result_id="gate-1",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-1",
        gate_name="canon_congruence",
        passed=False,
        severity="blocking",
        reasons=["conflict with canon"],
    )

    retrieved = repo.get_generation_gate_result("gate-1")
    assert retrieved.gate_result_id == "gate-1"
    assert retrieved.generation_id == "gen-1"
    assert retrieved.project_id == "target-1"
    assert retrieved.artifact_kind == "chapter"
    assert retrieved.artifact_id == "ch-1"
    assert retrieved.gate_name == "canon_congruence"
    assert retrieved.passed is False
    assert retrieved.severity == "blocking"
    assert retrieved.reasons == ["conflict with canon"]
    assert isinstance(retrieved.created_at, datetime)


def test_get_generation_gate_result_raises_key_error_nonexistent(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    with pytest.raises(KeyError):
        repo.get_generation_gate_result("nonexistent-gate")


def test_list_generation_gate_results_ordered_by_created_at_desc(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-gate-list",
        request_hash="h-gate-list",
    )
    repo.upsert_canon_generation_run(
        generation_id="gen-other",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-gate-other",
        request_hash="h-gate-other",
    )

    repo.upsert_generation_gate_result(
        gate_result_id="gate-1",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-1",
        gate_name="canon_congruence",
        passed=True,
        severity="info",
    )

    time.sleep(0.05)

    repo.upsert_generation_gate_result(
        gate_result_id="gate-2",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-2",
        gate_name="canon_congruence",
        passed=False,
        severity="blocking",
    )

    time.sleep(0.05)

    repo.upsert_generation_gate_result(
        gate_result_id="gate-3",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-3",
        gate_name="canon_congruence",
        passed=True,
        severity="info",
    )

    repo.upsert_generation_gate_result(
        gate_result_id="gate-other",
        generation_id="gen-other",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-4",
        gate_name="canon_congruence",
        passed=True,
        severity="info",
    )

    results = repo.list_generation_gate_results("gen-1")
    assert len(results) == 3
    assert results[0].gate_result_id == "gate-3"
    assert results[1].gate_result_id == "gate-2"
    assert results[2].gate_result_id == "gate-1"


def test_gate_result_repair_fields_round_trip(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        idempotency_key="idem-gate-repair",
        request_hash="h-gate-repair",
    )

    repo.upsert_generation_gate_result(
        gate_result_id="gate-repair",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-1",
        gate_name="canon_congruence",
        passed=False,
        severity="blocking",
        reasons=["needs repair"],
        repair_attempted=True,
        repair_job_id="repair-job-1",
    )

    retrieved = repo.get_generation_gate_result("gate-repair")
    assert retrieved.repair_attempted is True
    assert retrieved.repair_job_id == "repair-job-1"

    updated = repo.upsert_generation_gate_result(
        gate_result_id="gate-repair",
        generation_id="gen-1",
        project_id="target-1",
        artifact_kind="chapter",
        artifact_id="ch-1",
        gate_name="canon_congruence",
        passed=True,
        severity="info",
        reasons=["repaired"],
        repair_attempted=False,
        repair_job_id=None,
    )
    assert updated.repair_attempted is False
    assert updated.repair_job_id is None


def test_run_record_json_list_fields_round_trip(tmp_path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    repo = StoryDevelopmentRepository(db_path)

    repo.upsert_canon_generation_run(
        generation_id="gen-1",
        source_project_id="source-1",
        target_project_id="target-1",
        mode="same_project_side_story",
        request_json={},
        canon_scope_json={},
        canon_policy_json={},
        status="queued",
        warnings=["warning-1", "warning-2"],
        created_job_ids=["job-1", "job-2", "job-3"],
        created_artifacts=[
            {"artifact_id": "art-1", "role": "plan"},
            {"artifact_id": "art-2", "role": "draft"},
        ],
        idempotency_key="idem-1",
        request_hash="hash-1",
    )

    retrieved = repo.get_canon_generation_run("gen-1")
    assert retrieved.warnings == ["warning-1", "warning-2"]
    assert retrieved.created_job_ids == ["job-1", "job-2", "job-3"]
    assert len(retrieved.created_artifacts) == 2
    assert retrieved.created_artifacts[0]["artifact_id"] == "art-1"
    assert retrieved.created_artifacts[0]["role"] == "plan"
    assert retrieved.created_artifacts[1]["artifact_id"] == "art-2"
    assert retrieved.created_artifacts[1]["role"] == "draft"
