from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = pytest.mark.integration
API_KEY = "test-secret-key-123"


class TestPathTraversalValidation:
    """Tests for SEC-04: Path traversal validation."""

    def test_normal_path_accepted(self):
        """Normal paths without traversal should be accepted."""
        client = TestClient(build_app())
        
        response = client.get(
            "/v1/projects",
            headers={"X-API-Key": API_KEY},
        )
        # Should not be blocked (might return 200 or other status)
        assert response.status_code != 400

    def test_double_dot_in_query_blocked(self):
        """Paths containing '..' in query params should be blocked with 400."""
        client = TestClient(build_app())
        
        # Try to access parent directory via path traversal in query param
        response = client.get(
            "/v1/projects?filter=../projects",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400
        assert "path traversal" in response.json()["detail"].lower()

    def test_encoded_double_dot_blocked(self):
        """URL-encoded '..' (%2e%2e) should be blocked."""
        client = TestClient(build_app())
        
        # Try encoded path traversal
        response = client.get(
            "/v1/projects/%2e%2e/projects",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_double_encoded_dot_blocked(self):
        """Double-encoded dots should be blocked."""
        client = TestClient(build_app())
        
        # Try double-encoded traversal
        response = client.get(
            "/v1/projects/%252e%252e",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_null_byte_in_query_blocked(self):
        """Null bytes (%00) in query parameters should be blocked."""
        client = TestClient(build_app())
        
        # Try null byte injection in query string
        response = client.get(
            "/v1/projects?name=test%00.txt",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_backslash_in_path_blocked(self):
        """Backslashes in path should be blocked (Windows traversal)."""
        client = TestClient(build_app())
        
        # Try backslash-based traversal
        response = client.get(
            "/v1/projects\\..\\projects",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_traversal_in_query_param_blocked(self):
        """Path traversal in query parameters should be blocked."""
        client = TestClient(build_app())
        
        # Try traversal in query string
        response = client.get(
            "/v1/projects?path=../../../etc/passwd",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_health_endpoint_not_affected(self):
        """Health endpoint should still work normally."""
        client = TestClient(build_app())
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_case_insensitive_encoded_blocked(self):
        """Case variations of encoded dots should be blocked."""
        client = TestClient(build_app())
        
        # Try uppercase encoding
        response = client.get(
            "/v1/projects/%2E%2E",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400

    def test_mixed_case_encoded_blocked(self):
        """Mixed case encoded dots should be blocked."""
        client = TestClient(build_app())
        
        # Try mixed case encoding
        response = client.get(
            "/v1/projects/%2e%2E",
            headers={"X-API-Key": API_KEY},
        )
        
        assert response.status_code == 400
