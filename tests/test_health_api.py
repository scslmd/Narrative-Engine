"""Tests for health and metrics endpoints (REL-05, REL-06)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import build_app


def test_health_endpoint_returns_ok() -> None:
    """Test that the basic health endpoint returns 200 with status ok."""
    client = TestClient(build_app())
    response = client.get('/health/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'


def test_health_ready_endpoint_returns_ready() -> None:
    """Test that the readiness endpoint returns 200 with status ready."""
    client = TestClient(build_app())
    response = client.get('/health/ready')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ready'
    assert 'components' in data


def test_health_metrics_endpoint_returns_required_sections() -> None:
    """Test that the metrics endpoint returns all required sections (REL-05).
    
    Verifies that /health/metrics returns:
    - timestamp
    - circuit_breakers
    - jobs (with status buckets)
    - role_model_checker (with status buckets)
    """
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    # Check required top-level keys
    assert 'timestamp' in data
    assert 'circuit_breakers' in data
    assert 'jobs' in data
    assert 'role_model_checker' in data
    
    # Check that timestamp is a number
    assert isinstance(data['timestamp'], (int, float))
    
    # Check that circuit_breakers is a dict
    assert isinstance(data['circuit_breakers'], dict)


def test_health_metrics_jobs_section_has_status_buckets() -> None:
    """Test that the jobs section contains all expected status buckets."""
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    jobs = data['jobs']
    
    # Check that all job statuses are present
    assert 'PENDING' in jobs
    assert 'PROCESSING' in jobs
    assert 'COMPLETED' in jobs
    assert 'FAILED' in jobs
    
    # Check that status counts are non-negative integers
    for status in ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']:
        count = jobs[status]
        assert isinstance(count, int)
        assert count >= 0
    
    # Check that rate fields exist and are floats between 0 and 1
    assert 'success_rate' in jobs
    assert 'failure_rate' in jobs
    assert isinstance(jobs['success_rate'], float)
    assert isinstance(jobs['failure_rate'], float)
    assert 0.0 <= jobs['success_rate'] <= 1.0
    assert 0.0 <= jobs['failure_rate'] <= 1.0


def test_health_metrics_role_model_checker_section_has_status_buckets() -> None:
    """Test that the role_model_checker section contains all expected status buckets."""
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    checker = data['role_model_checker']
    
    # Check that all checker statuses are present
    assert 'PENDING' in checker
    assert 'RUNNING' in checker
    assert 'COMPLETED' in checker
    assert 'FAILED' in checker
    
    # Check that status counts are non-negative integers
    for status in ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED']:
        count = checker[status]
        assert isinstance(count, int)
        assert count >= 0
    
    # Check that rate fields exist and are floats between 0 and 1
    assert 'success_rate' in checker
    assert 'failure_rate' in checker
    assert isinstance(checker['success_rate'], float)
    assert isinstance(checker['failure_rate'], float)
    assert 0.0 <= checker['success_rate'] <= 1.0
    assert 0.0 <= checker['failure_rate'] <= 1.0


def test_health_metrics_endpoint_no_auth_required() -> None:
    """Test that the metrics endpoint does not require authentication."""
    client = TestClient(build_app())
    
    # Call without any auth headers
    response = client.get('/health/metrics')
    assert response.status_code == 200
    
    # Verify we get actual data
    data = response.json()
    assert 'timestamp' in data
    assert 'jobs' in data
    assert 'role_model_checker' in data


def test_health_metrics_circuit_breaker_format() -> None:
    """Test that circuit breaker entries have the expected format."""
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    circuit_breakers = data['circuit_breakers']
    
    # Each circuit breaker should have these fields
    for backend_name, cb_data in circuit_breakers.items():
        assert 'state' in cb_data
        assert 'failure_count' in cb_data
        assert 'last_failure_time' in cb_data
        assert 'last_success_time' in cb_data
        assert 'recovery_available_at' in cb_data


def test_health_metrics_jobs_latency_fields_present() -> None:
    """Test that the jobs section contains latency telemetry fields (REL-05)."""
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    jobs = data['jobs']
    
    # Check that latency fields are present
    assert 'average_latency_ms' in jobs
    assert 'min_latency_ms' in jobs
    assert 'max_latency_ms' in jobs
    
    # Check that latency fields are floats >= 0
    assert isinstance(jobs['average_latency_ms'], float)
    assert isinstance(jobs['min_latency_ms'], float)
    assert isinstance(jobs['max_latency_ms'], float)
    assert jobs['average_latency_ms'] >= 0.0
    assert jobs['min_latency_ms'] >= 0.0
    assert jobs['max_latency_ms'] >= 0.0
    
    # Check logical consistency: min <= average <= max
    assert jobs['min_latency_ms'] <= jobs['average_latency_ms'] <= jobs['max_latency_ms']


def test_health_metrics_checker_latency_fields_present() -> None:
    """Test that the role_model_checker section contains latency telemetry fields (REL-05)."""
    client = TestClient(build_app())
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    checker = data['role_model_checker']
    
    # Check that latency fields are present
    assert 'average_latency_ms' in checker
    assert 'min_latency_ms' in checker
    assert 'max_latency_ms' in checker
    
    # Check that latency fields are floats >= 0
    assert isinstance(checker['average_latency_ms'], float)
    assert isinstance(checker['min_latency_ms'], float)
    assert isinstance(checker['max_latency_ms'], float)
    assert checker['average_latency_ms'] >= 0.0
    assert checker['min_latency_ms'] >= 0.0
    assert checker['max_latency_ms'] >= 0.0
    
    # Check logical consistency: min <= average <= max
    assert checker['min_latency_ms'] <= checker['average_latency_ms'] <= checker['max_latency_ms']


def test_health_metrics_jobs_latency_computation_deterministic() -> None:
    """Test that job latency fields are computed correctly from seeded timestamps (REL-05)."""
    from app.persistence.sqlite import connect
    from app.settings import settings
    from datetime import datetime, timedelta, timezone
    
    client = TestClient(build_app())
    
    # Seed known job attempt records with deterministic timestamps
    db_path = settings.operations_db_path
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    with connect(db_path) as conn:
        # Cleanup any existing test data
        conn.execute("DELETE FROM job_attempts WHERE job_id LIKE 'test-job-latency-%'")
        conn.execute("DELETE FROM jobs WHERE job_id LIKE 'test-job-latency-%'")
        
        # Insert 3 completed job attempts with known latencies: 1000ms, 2000ms, 3000ms
        now = datetime.now(timezone.utc).isoformat()
        
        # First create parent jobs records
        for i in range(1, 4):
            conn.execute(
                """INSERT INTO jobs (job_id, logical_run_id, attempt_number, phase, status, payload_json, request_json, request_hash, request_scope, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'test-job-latency-{i}', f'logical-run-{i}', 1, 'P-100', 'COMPLETED', '{}', '{}', '', '', now, now)
            )
        
        # Attempt 1: 1000ms latency
        conn.execute(
            """INSERT INTO job_attempts (job_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-job-latency-1', 'logical-run-1', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=1000)).isoformat(), now, now)
        )
        # Attempt 2: 2000ms latency
        conn.execute(
            """INSERT INTO job_attempts (job_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-job-latency-2', 'logical-run-2', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=2000)).isoformat(), now, now)
        )
        # Attempt 3: 3000ms latency
        conn.execute(
            """INSERT INTO job_attempts (job_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-job-latency-3', 'logical-run-3', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=3000)).isoformat(), now, now)
        )
    
    # Query metrics and verify latency computation
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    jobs = data['jobs']
    
    # Expected: average = (1000 + 2000 + 3000) / 3 = 2000ms
    #           min = 1000ms, max = 3000ms
    assert jobs['average_latency_ms'] == 2000.0
    assert jobs['min_latency_ms'] == 1000.0
    assert jobs['max_latency_ms'] == 3000.0
    
    # Cleanup: delete test job attempts
    with connect(db_path) as conn:
        conn.execute("DELETE FROM job_attempts WHERE job_id IN (?, ?, ?)",
                    ('test-job-latency-1', 'test-job-latency-2', 'test-job-latency-3'))


def test_health_metrics_checker_latency_computation_deterministic() -> None:
    """Test that checker latency fields are computed correctly from seeded timestamps (REL-05)."""
    from app.persistence.sqlite import connect
    from app.settings import settings
    from datetime import datetime, timedelta, timezone
    
    client = TestClient(build_app())
    
    # Seed known checker run attempt records with deterministic timestamps
    db_path = settings.operations_db_path
    base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    with connect(db_path) as conn:
        # Cleanup any existing test data
        conn.execute("DELETE FROM checker_run_attempts WHERE run_id LIKE 'test-checker-latency-%'")
        conn.execute("DELETE FROM checker_runs WHERE run_id LIKE 'test-checker-latency-%'")
        
        # Insert 3 completed checker run attempts with known latencies: 500ms, 1500ms, 2500ms
        now = datetime.now(timezone.utc).isoformat()
        
        # First create parent checker_runs records
        for i in range(1, 4):
            conn.execute(
                """INSERT INTO checker_runs (run_id, logical_run_id, attempt_number, status, request_json, request_hash, request_scope, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'test-checker-latency-{i}', f'logical-run-{i}', 1, 'COMPLETED', '{}', '', '', now, now)
            )
        
        # Attempt 1: 500ms latency
        conn.execute(
            """INSERT INTO checker_run_attempts (run_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-checker-latency-1', 'logical-run-1', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=500)).isoformat(), now, now)
        )
        # Attempt 2: 1500ms latency
        conn.execute(
            """INSERT INTO checker_run_attempts (run_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-checker-latency-2', 'logical-run-2', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=1500)).isoformat(), now, now)
        )
        # Attempt 3: 2500ms latency
        conn.execute(
            """INSERT INTO checker_run_attempts (run_id, logical_run_id, attempt_number, status, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('test-checker-latency-3', 'logical-run-3', 1, 'COMPLETED',
             base_time.isoformat(), (base_time + timedelta(milliseconds=2500)).isoformat(), now, now)
        )
    
    # Query metrics and verify latency computation
    response = client.get('/health/metrics')
    assert response.status_code == 200
    data = response.json()
    
    checker = data['role_model_checker']
    
    # Expected: average = (500 + 1500 + 2500) / 3 = 1500ms
    #           min = 500ms, max = 2500ms
    assert checker['average_latency_ms'] == 1500.0
    assert checker['min_latency_ms'] == 500.0
    assert checker['max_latency_ms'] == 2500.0
    
    # Cleanup: delete test checker run attempts
    with connect(db_path) as conn:
        conn.execute("DELETE FROM checker_run_attempts WHERE run_id IN (?, ?, ?)",
                    ('test-checker-latency-1', 'test-checker-latency-2', 'test-checker-latency-3'))


def test_health_metrics_latency_zero_when_no_completed_jobs() -> None:
    """Test that latency fields are 0.0 when no jobs/checkers have completed timestamps (REL-05)."""
    from app.persistence.sqlite import connect
    from app.settings import settings
    
    client = TestClient(build_app())
    
    # Temporarily hide all completed job attempts and checker run attempts by deleting them
    db_path = settings.operations_db_path
    with connect(db_path) as conn:
        # Backup and clear completed job attempts
        completed_attempts = conn.execute(
            "SELECT * FROM job_attempts WHERE started_at IS NOT NULL AND finished_at IS NOT NULL"
        ).fetchall()
        conn.execute("DELETE FROM job_attempts WHERE started_at IS NOT NULL AND finished_at IS NOT NULL")
        
        # Backup and clear completed checker run attempts
        completed_checker_attempts = conn.execute(
            "SELECT * FROM checker_run_attempts WHERE started_at IS NOT NULL AND finished_at IS NOT NULL"
        ).fetchall()
        conn.execute("DELETE FROM checker_run_attempts WHERE started_at IS NOT NULL AND finished_at IS NOT NULL")
    
    try:
        # Query metrics and verify latency fields are 0.0
        response = client.get('/health/metrics')
        assert response.status_code == 200
        data = response.json()
        
        assert data['jobs']['average_latency_ms'] == 0.0
        assert data['jobs']['min_latency_ms'] == 0.0
        assert data['jobs']['max_latency_ms'] == 0.0
        
        assert data['role_model_checker']['average_latency_ms'] == 0.0
        assert data['role_model_checker']['min_latency_ms'] == 0.0
        assert data['role_model_checker']['max_latency_ms'] == 0.0
    finally:
        # Restore completed job attempts and checker run attempts
        with connect(db_path) as conn:
            for attempt in completed_attempts:
                conn.execute(
                    """INSERT INTO job_attempts (attempt_id, job_id, logical_run_id, attempt_number, status, 
                       executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at,
                       claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage,
                       retryable, retry_reason, error_code, error_category, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (attempt['attempt_id'], attempt['job_id'], attempt['logical_run_id'], attempt['attempt_number'],
                     attempt['status'], attempt.get('executor_name'), attempt.get('executor_instance_id'),
                     attempt.get('queue_delay_ms'), attempt.get('lease_owner'), attempt.get('lease_expires_at'),
                     attempt.get('claimed_at'), attempt['started_at'], attempt['finished_at'],
                     attempt.get('last_heartbeat_at'), attempt.get('finish_reason'), attempt.get('failure_stage'),
                     attempt.get('retryable'), attempt.get('retry_reason'), attempt.get('error_code'),
                     attempt.get('error_category'), attempt['created_at'], attempt['updated_at'])
                )
            
            for attempt in completed_checker_attempts:
                conn.execute(
                    """INSERT INTO checker_run_attempts (attempt_id, run_id, logical_run_id, attempt_number, status, 
                       executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at,
                       claimed_at, started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage,
                       retryable, retry_reason, error_code, error_category, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (attempt['attempt_id'], attempt['run_id'], attempt['logical_run_id'], attempt['attempt_number'],
                     attempt['status'], attempt.get('executor_name'), attempt.get('executor_instance_id'),
                     attempt.get('queue_delay_ms'), attempt.get('lease_owner'), attempt.get('lease_expires_at'),
                     attempt.get('claimed_at'), attempt['started_at'], attempt['finished_at'],
                     attempt.get('last_heartbeat_at'), attempt.get('finish_reason'), attempt.get('failure_stage'),
                     attempt.get('retryable'), attempt.get('retry_reason'), attempt.get('error_code'),
                     attempt.get('error_category'), attempt['created_at'], attempt['updated_at'])
                )
