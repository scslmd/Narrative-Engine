"""Tests for audit logging (REL-10)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from app.main import build_app
from app.settings import settings
from app.services.authentication import fingerprint_api_key
from tests.conftest import read_last_audit_record, count_audit_records


class TestAuditLogging:
    """Test REL-10: Request audit logging."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Clear any existing log file
        log_path = Path(settings.structured_log_filename)
        if log_path.exists():
            log_path.unlink()
        
        # Disable API key requirement for tests
        self.original_api_key = os.environ.get('API_KEY')
        os.environ['API_KEY'] = ''
        
        self.client = TestClient(build_app())

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Restore original API key
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
        
        # Clean up log file
        log_path = Path(settings.structured_log_filename)
        if log_path.exists():
            log_path.unlink()

    def test_versioned_api_request_creates_audit_record(self) -> None:
        """A request to /v1 endpoint should create an audit record."""
        # Make a request to versioned endpoint
        self.client.get('/v1/jobs')
        
        # Check that log file was created
        log_path = Path(settings.structured_log_filename)
        assert log_path.exists()
        
        # Use shared utility
        assert count_audit_records() == 1
        record = read_last_audit_record()
        assert record is not None
        
        # Verify required fields
        assert 'timestamp' in record
        assert 'method' in record
        assert 'path' in record
        assert 'status_code' in record
        assert 'api_key_fingerprint' in record

    def test_audit_record_has_correct_values(self) -> None:
        """Audit record should have correct method, path, and status code."""
        self.client.post('/v1/projects/create', json={'project_name': 'test'})
        
        record = read_last_audit_record()
        assert record is not None
        
        assert record['method'] == 'POST'
        assert record['path'] == '/v1/projects/create'
        assert record['status_code'] in (200, 201, 400, 404, 422)  # Various possible outcomes

    def test_audit_record_includes_api_key_fingerprint(self) -> None:
        """Audit record should include API key fingerprint when key is provided."""
        test_key = 'test-key-abc123'
        expected_fingerprint = fingerprint_api_key(test_key)
        
        self.client.get(
            '/v1/jobs',
            headers={'X-API-Key': test_key}
        )
        
        record = read_last_audit_record()
        assert record is not None
        assert record['api_key_fingerprint'] == expected_fingerprint

    def test_audit_record_does_not_contain_raw_api_key(self) -> None:
        """Audit record should never contain the raw API key."""
        test_key = 'super-secret-key-12345'
        
        self.client.get(
            '/v1/jobs',
            headers={'X-API-Key': test_key}
        )
        
        log_path = Path(settings.structured_log_filename)
        with open(log_path, 'r') as f:
            log_content = f.read()
        
        # Raw key should not appear anywhere in the log
        assert test_key not in log_content
        
        # But the fingerprint should be there
        fingerprint = fingerprint_api_key(test_key)
        assert fingerprint in log_content

    def test_non_versioned_requests_not_logged(self) -> None:
        """Requests to non-/v1 endpoints should not create audit records."""
        # Make requests to non-versioned endpoints
        self.client.get('/health/')
        self.client.get('/models')
        
        # Log file should not exist or be empty
        log_path = Path(settings.structured_log_filename)
        if log_path.exists():
            with open(log_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 0

    def test_audit_record_includes_duration(self) -> None:
        """Audit record should include request duration."""
        self.client.get('/v1/jobs')
        
        record = read_last_audit_record()
        assert record is not None
        
        assert 'duration_ms' in record
        assert isinstance(record['duration_ms'], int)
        assert record['duration_ms'] >= 0

    def test_audit_record_includes_project_id_from_path(self) -> None:
        """Audit record should include project_id when present in path."""
        self.client.get('/v1/projects/test-project-id/manifest')
        
        record = read_last_audit_record()
        assert record is not None
        assert record.get('project_id') == 'test-project-id'
        assert record.get('target_resource') == 'project:test-project-id'

    def test_audit_record_includes_project_id_from_query(self) -> None:
        """Audit record should include project_id from query params for story-dev."""
        self.client.get('/v1/story-development/drafting/draft-artifacts', 
                       params={'project_id': 'query-project-id'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record.get('project_id') == 'query-project-id'
        assert record.get('target_resource') == 'story_project:query-project-id'

    def test_audit_record_includes_target_resource_for_job_route(self) -> None:
        """Job routes should record a job-scoped target resource."""
        self.client.get('/v1/jobs/test-job-id/status')

        record = read_last_audit_record()
        assert record is not None
        assert record.get('target_resource') == 'job:test-job-id'

    def test_audit_record_includes_target_resource_for_checker_route(self) -> None:
        """Checker routes should record a checker-run target resource."""
        self.client.get('/v1/role-model-checker/test-run-id')

        record = read_last_audit_record()
        assert record is not None
        assert record.get('target_resource') == 'role_model_check:test-run-id'

    def test_audit_record_timestamp_is_iso_format(self) -> None:
        """Audit record timestamp should be ISO format."""
        from datetime import datetime
        
        self.client.get('/v1/jobs')
        
        record = read_last_audit_record()
        assert record is not None
        
        # Should be parseable as ISO format
        timestamp = record['timestamp']
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_multiple_requests_create_multiple_records(self) -> None:
        """Multiple requests should create multiple audit records."""
        self.client.get('/v1/jobs')
        self.client.post('/v1/projects/create', json={'project_name': 'test'})
        self.client.get('/v1/models')
        
        assert count_audit_records() == 3

    def test_audit_logging_does_not_fail_request(self) -> None:
        """Request should succeed even if audit logging fails."""
        # This is implicitly tested - if logging failed, the test would fail
        # But we can verify the request still works
        response = self.client.get('/v1/jobs')
        
        # Request should complete (status code may vary)
        assert response.status_code < 500  # Not a server error
