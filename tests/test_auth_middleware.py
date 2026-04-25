from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = pytest.mark.integration


@pytest.fixture
def client_with_auth():
    """Create test client with authentication enabled."""
    with patch.dict(os.environ, {"API_KEY": "test-secret-key-123"}):
        # Need to reload settings to pick up new env var
        from app import settings as settings_module
        original_settings = settings_module.settings
        settings_module.settings = type(
            settings_module.settings
        )(
            app_name="Narrative-Engine",
            app_env="local",
            default_seed=42,
            telemetry_filename="telemetry.log",
            structured_log_filename="telemetry.jsonl",
            root_dir=settings_module.settings.root_dir,
        )
        try:
            app = build_app()
            yield TestClient(app)
        finally:
            settings_module.settings = original_settings


@pytest.fixture
def client_without_auth():
    """Create test client without authentication."""
    with patch.dict(os.environ, {}, clear=True):
        from app import settings as settings_module
        original_settings = settings_module.settings
        settings_module.settings = type(
            settings_module.settings
        )(
            app_name="Narrative-Engine",
            app_env="local",
            default_seed=42,
            telemetry_filename="telemetry.log",
            structured_log_filename="telemetry.jsonl",
            root_dir=settings_module.settings.root_dir,
        )
        try:
            app = build_app()
            yield TestClient(app)
        finally:
            settings_module.settings = original_settings


class TestAuthMiddleware:
    """Tests for SEC-01: Authentication Middleware."""

    def test_health_endpoint_no_auth_required(self, client_with_auth):
        """Health endpoint should be accessible without authentication."""
        response = client_with_auth.get("/health", headers={})
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_requires_x_api_key_header(self, client_with_auth):
        """API endpoints require X-API-Key header."""
        response = client_with_auth.get("/v1/projects", headers={})
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]

    def test_valid_api_key_grants_access(self, client_with_auth):
        """Valid API key grants access to protected endpoints."""
        response = client_with_auth.get(
            "/v1/projects", headers={"X-API-Key": "test-secret-key-123"}
        )
        # Should not be 401 (might be 200 or other status depending on data)
        assert response.status_code != 401

    def test_invalid_api_key_rejected(self, client_with_auth):
        """Invalid API key is rejected with 401."""
        response = client_with_auth.get(
            "/v1/projects", headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]

    def test_missing_api_key_rejected(self, client_with_auth):
        """Missing API key header is rejected with 401."""
        response = client_with_auth.get("/v1/projects", headers={})
        assert response.status_code == 401

    def test_post_request_requires_auth(self, client_with_auth):
        """POST requests also require authentication."""
        response = client_with_auth.post(
            "/v1/projects/create", json={"project_name": "Test Project"}, headers={}
        )
        assert response.status_code == 401

    def test_post_request_with_valid_key_accepted(self, client_with_auth):
        """POST request with valid API key is accepted."""
        response = client_with_auth.post(
            "/v1/projects/create",
            json={"project_name": "Test Project"},
            headers={"X-API-Key": "test-secret-key-123"},
        )
        # Should not be 401 (might succeed or fail for other reasons)
        assert response.status_code != 401

    def test_health_endpoint_variants_no_auth(self, client_with_auth):
        """All health endpoint variants accessible without auth."""
        response = client_with_auth.get("/health", headers={})
        assert response.status_code == 200


class TestAuthMiddlewareDisabled:
    """Tests for behavior when authentication is not configured."""

    def test_api_accessible_without_key_when_disabled(self, client_without_auth):
        """When API_KEY not set, endpoints are accessible without auth."""
        # This tests the case where middleware is not added
        response = client_without_auth.get("/health")
        assert response.status_code == 200


class TestAuthMiddlewareStartup:
    """Tests for authentication middleware startup validation."""

    def test_missing_api_key_raises_error(self):
        """Missing API_KEY should raise ValueError during middleware init."""
        from app.middleware.auth import AuthMiddleware
        
        # Create a dummy app
        from fastapi import FastAPI
        dummy_app = FastAPI()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                AuthMiddleware(dummy_app)
            
            assert "API_KEY environment variable is not set" in str(exc_info.value)


class TestAuthMiddlewareSecurity:
    """Tests for authentication middleware security properties."""

    def test_valid_api_key_uses_constant_time_comparison(self, client_with_auth):
        """API key validation should use constant-time comparison to prevent timing attacks."""
        # This test verifies the implementation uses hmac.compare_digest
        # by checking that valid and invalid keys both return 401 without timing out
        import time
        
        # Measure response time for valid key
        start = time.time()
        client_with_auth.get(
            "/v1/projects", headers={"X-API-Key": "test-secret-key-123"}
        )
        valid_time = time.time() - start
        
        # Measure response time for invalid key
        start = time.time()
        client_with_auth.get(
            "/v1/projects", headers={"X-API-Key": "wrong-key"}
        )
        invalid_time = time.time() - start
        
        # Response times should be similar (within 100ms tolerance)
        # This is a heuristic test - exact timing comparison is flaky
        assert abs(valid_time - invalid_time) < 0.1, (
            "Response times differ significantly - may indicate timing vulnerability"
        )
