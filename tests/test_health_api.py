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
    
    # Check that all values are non-negative integers
    for status, count in jobs.items():
        assert isinstance(count, int)
        assert count >= 0


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
    
    # Check that all values are non-negative integers
    for status, count in checker.items():
        assert isinstance(count, int)
        assert count >= 0


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
