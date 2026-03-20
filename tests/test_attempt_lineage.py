from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.persistence.sqlite import connect
from app.schemas.jobs import JobCreateRequest
from app.schemas.role_model_checker import RoleModelCheckStartRequest
from app.services.job_manager import JobManager
from app.services.role_model_check_manager import RoleModelCheckManager


def _fetch_one(db_path: Path, sql: str, params: tuple[object, ...]) -> object | None:
    with connect(db_path) as connection:
        return connection.execute(sql, params).fetchone()


def _fetch_attempt_row(db_path: Path, table_name: str, primary_key_column: str, primary_key_value: UUID):
    return _fetch_one(
        db_path,
        f"SELECT * FROM {table_name} WHERE {primary_key_column} = ? ORDER BY attempt_number ASC, attempt_id ASC",
        (str(primary_key_value),),
    )


def _assert_initial_attempt_lineage(row: object, *, expected_id: UUID) -> None:
    assert row is not None
    assert row["attempt_number"] == 1
    assert row["logical_run_id"] == str(expected_id)
    assert row["status"] == "PENDING"
    assert row["created_at"] == row["updated_at"]


def test_job_attempt_lineage_tracks_projection_status_and_claim_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)

    job = manager.create_job(
        JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"})
    )
    job_attempt = _fetch_attempt_row(db_path, "job_attempts", "job_id", job.id)

    _assert_initial_attempt_lineage(job_attempt, expected_id=job.id)
    assert manager.list_events(job.id)[0]["attempt_number"] == 1

    manager.update_job(job.id, status="PROCESSING", current_step="outline")

    projection = manager.get_status(job.id)
    job_attempt = _fetch_attempt_row(db_path, "job_attempts", "job_id", job.id)

    assert projection.status == "PROCESSING"
    assert job_attempt["status"] == "PROCESSING"
    assert job_attempt["logical_run_id"] == str(job.id)

    claimed_job_id = manager.claim_next_pending(worker_id="worker-alpha", lease_seconds=60)
    assert claimed_job_id is None


def test_job_claim_persists_lease_metadata_on_projection_and_attempt_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = JobManager(db_path)

    job = manager.create_job(JobCreateRequest(phase="P-100", payload={"project_id": "science-fantasy-test"}))
    claimed_job_id = manager.claim_next_pending(worker_id="worker-alpha", lease_seconds=60)

    assert claimed_job_id == job.id

    with connect(db_path) as connection:
        projection = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (str(job.id),)).fetchone()
        attempt = connection.execute(
            "SELECT * FROM job_attempts WHERE job_id = ? ORDER BY attempt_number ASC, attempt_id ASC",
            (str(job.id),),
        ).fetchone()

    assert projection["lease_owner"] == "worker-alpha"
    assert projection["lease_expires_at"] is not None
    assert projection["claimed_at"] is not None
    assert attempt["lease_owner"] == "worker-alpha"
    assert attempt["lease_expires_at"] is not None
    assert attempt["claimed_at"] is not None
    assert attempt["attempt_number"] == 1


def test_checker_attempt_lineage_tracks_projection_status_and_claim_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)

    run = manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect", "critic"],
            model_selection={"architect": "qwen"},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    attempt = _fetch_attempt_row(db_path, "checker_run_attempts", "run_id", run.run_id)

    _assert_initial_attempt_lineage(attempt, expected_id=run.run_id)
    assert manager.list_events(run.run_id)[0]["attempt_number"] == 1

    manager.update_run(run.run_id, status="RUNNING", current_role="architect", detail="starting")
    manager.update_run(run.run_id, status="COMPLETED", current_role="critic", detail="finished")

    projection = manager.get_status(run.run_id)
    attempt = _fetch_attempt_row(db_path, "checker_run_attempts", "run_id", run.run_id)

    assert projection.status == "COMPLETED"
    assert attempt["status"] == "COMPLETED"
    assert attempt["logical_run_id"] == str(run.run_id)

    claimed_run_id = manager.claim_next_pending(worker_id="worker-beta", lease_seconds=60)
    assert claimed_run_id is None


def test_checker_claim_persists_lease_metadata_on_projection_and_attempt_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    manager = RoleModelCheckManager(db_path)

    run = manager.create_run(
        RoleModelCheckStartRequest(
            roles=["architect"],
            model_selection={},
            critic_profile="minimal_context",
            save_report=False,
        )
    )
    claimed_run_id = manager.claim_next_pending(worker_id="worker-beta", lease_seconds=60)

    assert claimed_run_id == run.run_id

    with connect(db_path) as connection:
        projection = connection.execute("SELECT * FROM checker_runs WHERE run_id = ?", (str(run.run_id),)).fetchone()
        attempt = connection.execute(
            "SELECT * FROM checker_run_attempts WHERE run_id = ? ORDER BY attempt_number ASC, attempt_id ASC",
            (str(run.run_id),),
        ).fetchone()

    assert projection["lease_owner"] == "worker-beta"
    assert projection["lease_expires_at"] is not None
    assert projection["claimed_at"] is not None
    assert attempt["lease_owner"] == "worker-beta"
    assert attempt["lease_expires_at"] is not None
    assert attempt["claimed_at"] is not None
    assert attempt["attempt_number"] == 1
