"""Tests for health and metrics endpoints (REL-05, REL-06)."""

from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = pytest.mark.integration


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
