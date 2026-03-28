"""Tests for phase-specific payload validation (REL-08)."""

from __future__ import annotations

import pytest

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import build_app
from app.schemas.jobs import JobCreateRequest


class TestJobCreateRequestValidation:
    """Test schema-level validation for JobCreateRequest."""

    def test_valid_payload_accepted(self) -> None:
        """Valid payload with project_id should be accepted."""
        req = JobCreateRequest(phase='P-100', payload={'project_id': 'test-project'})
        assert req.phase == 'P-100'
        assert req.payload['project_id'] == 'test-project'

    def test_missing_project_id_rejected(self) -> None:
        """Missing project_id should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(phase='P-100', payload={})
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'value_error'
        assert 'project_id' in error['msg']
        assert 'P-100' in error['msg']

    def test_empty_project_id_rejected(self) -> None:
        """Empty string project_id should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(phase='P-100', payload={'project_id': ''})
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'value_error'
        assert 'non-empty' in error['msg']

    def test_whitespace_project_id_rejected(self) -> None:
        """Whitespace-only project_id should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(phase='P-100', payload={'project_id': '   '})
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'value_error'
        assert 'non-empty' in error['msg']

    def test_non_string_project_id_rejected(self) -> None:
        """Non-string project_id should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(phase='P-100', payload={'project_id': 123})
        
        error = exc_info.value.errors()[0]
        assert error['type'] == 'value_error'
        assert 'string' in error['msg']

    def test_p200_requires_project_id(self) -> None:
        """P-200 phase should also require project_id."""
        with pytest.raises(ValidationError):
            JobCreateRequest(phase='P-200', payload={})

    def test_p300_requires_project_id(self) -> None:
        """P-300 phase should also require project_id."""
        with pytest.raises(ValidationError):
            JobCreateRequest(phase='P-300', payload={})

    def test_p400_requires_project_id(self) -> None:
        """P-400 phase should also require project_id."""
        with pytest.raises(ValidationError):
            JobCreateRequest(phase='P-400', payload={})

    def test_valid_project_id_with_extra_fields(self) -> None:
        """Payload with project_id and other fields should be accepted."""
        req = JobCreateRequest(
            phase='P-100',
            payload={
                'project_id': 'test-project',
                'extra_field': 'value',
                'number': 42,
            }
        )
        assert req.payload['project_id'] == 'test-project'
        assert req.payload['extra_field'] == 'value'


class TestJobCreateEndpointValidation:
    """Test HTTP endpoint validation for /jobs/create."""

    def setup_method(self) -> None:
        """Create a test client for each test."""
        self.client = TestClient(build_app())

    def test_valid_payload_returns_202(self) -> None:
        """Valid payload should return 202 Accepted."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-100', 'payload': {'project_id': 'test-project'}}
        )
        assert response.status_code == 202

    def test_missing_project_id_returns_422(self) -> None:
        """Missing project_id should return 422 Unprocessable Entity."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-100', 'payload': {}}
        )
        assert response.status_code == 422
        detail = response.json()['detail'][0]
        assert detail['type'] == 'value_error'
        assert 'project_id' in detail['msg']

    def test_empty_project_id_returns_422(self) -> None:
        """Empty project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-100', 'payload': {'project_id': ''}}
        )
        assert response.status_code == 422

    def test_whitespace_project_id_returns_422(self) -> None:
        """Whitespace project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-100', 'payload': {'project_id': '   '}}
        )
        assert response.status_code == 422

    def test_non_string_project_id_returns_422(self) -> None:
        """Non-string project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-100', 'payload': {'project_id': 123}}
        )
        assert response.status_code == 422

    def test_p200_missing_project_id_returns_422(self) -> None:
        """P-200 with missing project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-200', 'payload': {}}
        )
        assert response.status_code == 422

    def test_p300_missing_project_id_returns_422(self) -> None:
        """P-300 with missing project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-300', 'payload': {}}
        )
        assert response.status_code == 422

    def test_p400_missing_project_id_returns_422(self) -> None:
        """P-400 with missing project_id should return 422."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-400', 'payload': {}}
        )
        assert response.status_code == 422

    def test_valid_p200_payload_returns_202(self) -> None:
        """Valid P-200 payload should return 202."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-200', 'payload': {'project_id': 'test-project'}}
        )
        assert response.status_code == 202

    def test_valid_p300_payload_returns_202(self) -> None:
        """Valid P-300 payload should return 202."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-300', 'payload': {'project_id': 'test-project'}}
        )
        assert response.status_code == 202

    def test_valid_p400_payload_returns_202(self) -> None:
        """Valid P-400 payload should return 202."""
        response = self.client.post(
            '/jobs/create',
            json={'phase': 'P-400', 'payload': {'project_id': 'test-project'}}
        )
        assert response.status_code == 202
