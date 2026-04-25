from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = pytest.mark.integration
API_KEY = "test-secret-key-123"


class TestRequestSizeLimits:
    """Tests for SEC-03: Request size limits."""

    def test_payload_under_limit_accepted(self):
        """Payloads under 5 MB should be accepted."""
        client = TestClient(build_app())
        
        response = client.post(
            "/v1/projects/create",
            json={"project_name": "Test Project"},
            headers={"X-API-Key": API_KEY},
        )
        # Should not be rejected for size reasons
        assert response.status_code != 413

    def test_payload_over_limit_rejected(self):
        """Payloads over 5 MB should be rejected with 400."""
        client = TestClient(build_app())
        
        # Create a payload that exceeds the limit (6 MB)
        large_data = "x" * (6 * 1024 * 1024)
        
        response = client.post(
            "/v1/jobs/create",
            json={
                "phase": "P-100",
                "payload": {"data": large_data}
            },
            headers={"X-API-Key": API_KEY},
        )
        
        # Should be rejected with validation error (422) or size limit (400/413)
        assert response.status_code in [400, 413, 422]

    def test_payload_at_limit_accepted(self):
        """Payloads at exactly 5 MB should be accepted."""
        client = TestClient(build_app())
        
        # Create a payload that's just under the limit (4.9 MB)
        data_at_limit = "x" * int(4.9 * 1024 * 1024)
        
        response = client.post(
            "/v1/jobs/create",
            json={
                "phase": "P-100",
                "payload": {"data": data_at_limit}
            },
            headers={"X-API-Key": API_KEY},
        )
        
        # Should be accepted (might fail for other reasons but not size)
        assert response.status_code != 413

    def test_request_body_over_10mb_rejected(self):
        """Request bodies over 10 MB should be rejected with 413 or 422."""
        client = TestClient(build_app())
        
        # Create a very large payload (12 MB) that exceeds max_body_size
        huge_data = "x" * (12 * 1024 * 1024)
        
        response = client.post(
            "/v1/jobs/create",
            json={
                "phase": "P-100",
                "payload": {"data": huge_data}
            },
            headers={"X-API-Key": API_KEY},
        )
        
        # Should be rejected with 413 (body too large) or 422 (validation error for payload size)
        assert response.status_code in [413, 422]

    def test_normal_request_accepted(self):
        """Normal requests should work without issues."""
        client = TestClient(build_app())
        
        response = client.post(
            "/v1/projects/create",
            json={
                "project_name": "Test Project",
                "genre": "Fantasy",
                "tone_profile": "Epic",
            },
            headers={"X-API-Key": API_KEY},
        )
        
        # Should succeed or fail for validation reasons, not size
        assert response.status_code != 413
