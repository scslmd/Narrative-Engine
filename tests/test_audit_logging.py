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

@pytest.mark.integration
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


class TestAuditLoggingOperationField:
    """Test REL-10: Audit operation field normalization."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        log_path = Path(settings.structured_log_filename)
        if log_path.exists():
            log_path.unlink()
        
        self.original_api_key = os.environ.get('API_KEY')
        os.environ['API_KEY'] = ''
        
        self.client = TestClient(build_app())

    def teardown_method(self) -> None:
        """Clean up after tests."""
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
        
        log_path = Path(settings.structured_log_filename)
        if log_path.exists():
            log_path.unlink()

    def test_audit_record_includes_operation_field(self) -> None:
        """Audit record should include operation field."""
        self.client.get('/v1/jobs')
        
        record = read_last_audit_record()
        assert record is not None
        assert 'operation' in record
        assert isinstance(record['operation'], str)

    def test_project_create_operation(self) -> None:
        """POST /v1/projects/create should have operation project.create."""
        self.client.post('/v1/projects/create', json={'project_name': 'test'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'project.create'

    def test_project_artifact_read_operation(self) -> None:
        """GET /v1/projects/{id}/manifest should have operation project_artifact.manifest.read."""
        self.client.get('/v1/projects/test-project-id/manifest')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'project_artifact.manifest.read'

    def test_job_status_read_operation(self) -> None:
        """GET /v1/jobs/{id}/status should have operation job.status.read."""
        self.client.get('/v1/jobs/test-job-id/status')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.status.read'

    def test_job_logs_read_operation(self) -> None:
        """GET /v1/jobs/{id}/logs should have operation job.logs.read."""
        self.client.get('/v1/jobs/test-job-id/logs')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.logs.read'

    def test_job_steps_read_operation(self) -> None:
        """GET /v1/jobs/{id}/steps should have operation job.steps.read."""
        self.client.get('/v1/jobs/test-job-id/steps')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.steps.read'

    def test_job_lineage_read_operation(self) -> None:
        """GET /v1/jobs/{id}/lineage should have operation job.lineage.read."""
        self.client.get('/v1/jobs/test-job-id/lineage')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.lineage.read'

    def test_story_development_draft_artifacts_read_operation(self) -> None:
        """GET /v1/story-development/drafting/draft-artifacts should have operation story_development.drafting.draft_artifacts.read."""
        self.client.get('/v1/story-development/drafting/draft-artifacts', 
                       params={'project_id': 'test-project-id'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.drafting.draft_artifacts.read'

    def test_story_development_branches_create_operation(self) -> None:
        """POST /v1/story-development/branches should have operation story_development.branches.create."""
        self.client.post('/v1/story-development/branches', 
                        json={'project_id': 'test-project-id', 'branch_name': 'test-branch'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.branches.create'

    def test_story_development_foundation_update_operation(self) -> None:
        """PATCH /v1/story-development/foundation should have operation story_development.foundation.update."""
        self.client.patch('/v1/story-development/foundation', 
                         params={'project_id': 'test-project-id'},
                         json={'premise': 'updated premise'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.foundation.update'

    def test_role_model_check_create_operation(self) -> None:
        """POST /v1/role-model-checker/run should have operation role_model_check.create."""
        self.client.post('/v1/role-model-checker/run', 
                        json={'project_id': 'test-project-id'})
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'role_model_check.create'

    def test_role_model_check_status_read_operation(self) -> None:
        """GET /v1/role-model-checker/{id}/status should have operation role_model_check.status.read."""
        self.client.get('/v1/role-model-checker/test-run-id/status')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'role_model_check.status.read'

    def test_operation_field_preserved_with_target_resource(self) -> None:
        """Operation field should be present alongside target_resource."""
        self.client.get('/v1/jobs/test-job-id/status')
        
        record = read_last_audit_record()
        assert record is not None
        assert 'operation' in record
        assert 'target_resource' in record
        assert record['operation'] == 'job.status.read'
        assert record['target_resource'] == 'job:test-job-id'

    def test_operation_field_preserved_with_project_id(self) -> None:
        """Operation field should be present alongside project_id."""
        self.client.get('/v1/story-development/drafting/draft-artifacts', 
                       params={'project_id': 'query-project-id'})
        
        record = read_last_audit_record()
        assert record is not None
        assert 'operation' in record
        assert 'project_id' in record
        assert record['operation'] == 'story_development.drafting.draft_artifacts.read'
        assert record['project_id'] == 'query-project-id'

    def test_story_development_characters_read_operation_stable(self) -> None:
        """GET /v1/story-development/characters/{id} should have stable operation story_development.characters.read."""
        self.client.get('/v1/story-development/characters/test-character-id')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.characters.read'
        assert 'test-character-id' not in record['operation']

    def test_story_development_characters_relationships_read_operation_stable(self) -> None:
        """GET /v1/story-development/characters/{id}/relationships should have stable operation."""
        self.client.get('/v1/story-development/characters/test-character-id/relationships')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.characters.relationships.read'
        assert 'test-character-id' not in record['operation']

    def test_story_development_findings_read_operation_stable(self) -> None:
        """GET /v1/story-development/review/findings/{id} should have stable operation story_development.review.findings.read."""
        self.client.get('/v1/story-development/review/findings/test-finding-id')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.review.findings.read'
        assert 'test-finding-id' not in record['operation']

    def test_story_development_inspect_links_read_operation_stable(self) -> None:
        """GET /v1/story-development/review/inspect-links/{id} should have stable operation."""
        self.client.get('/v1/story-development/review/inspect-links/test-link-id')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.review.inspect_links.read'
        assert 'test-link-id' not in record['operation']

    def test_story_development_world_bible_read_operation_stable(self) -> None:
        """GET /v1/story-development/world-bible/{type}/{title} should have stable operation."""
        self.client.get('/v1/story-development/world-bible/location/Test Title')
        
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'story_development.world_bible.read'
        assert 'Test Title' not in record['operation']

    def test_assembled_app_job_create_status_flow(self) -> None:
        """Assembled-app flow: POST create then GET status should log both operations."""
        # Create a job
        create_response = self.client.post(
            '/v1/jobs/create',
            json={
                'phase': 'P-100',
                'payload': {
                    'project_id': 'test-project-id',
                    'premise_text': 'Test premise'
                }
            }
        )
        
        assert create_response.status_code in (200, 202)
        job_id = create_response.json()['id']
        
        # Verify create operation logged
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.create'
        
        # Follow with status check
        status_response = self.client.get(f'/v1/jobs/{job_id}/status')
        
        assert status_response.status_code == 200
        
        # Verify status operation logged
        record = read_last_audit_record()
        assert record is not None
        assert record['operation'] == 'job.status.read'
