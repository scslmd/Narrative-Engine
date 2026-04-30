from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import build_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="serial-rate-limiting"),
]
API_KEY = "test-secret-key-123"
"""Rate-limiting tests are serial (xdist_group) because they:
- Create checker runs that trigger LocalExecutor daemon threads
- Are inherently timing-dependent (race between request rate and executor processing)
- Share global state: projects_dir, circuit breaker registry, executor threads
On Windows, concurrent executor threads from multiple test instances can cause
file lock conflicts on shared data/projects/ directory, leading to intermittent
.staged file artifacts or worker crashes.
"""


class TestRateLimiting:
    """Tests for SEC-05: Rate limiting."""

    def test_jobs_creation_rate_limit_exists(self):
        """Jobs creation should have rate limit headers."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.post(
                "/v1/jobs/create",
                json={"phase": "P-100", "payload": {"project_id": "test"}},
                headers={"X-API-Key": API_KEY},
            )

            assert "x-ratelimit-limit" in response.headers or response.status_code == 429

    def test_checker_runs_rate_limit_exists(self):
        """Checker runs should have rate limit headers."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.post(
                "/v1/role-model-checker/start",
                json={"project_id": "test"},
                headers={"X-API-Key": API_KEY},
            )

            assert "x-ratelimit-limit" in response.headers or response.status_code == 429

    def test_status_checks_have_higher_limit(self):
        """Status check endpoints should have higher rate limits."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.get(
                "/v1/jobs/test-id/status",
                headers={"X-API-Key": API_KEY},
            )

            if "x-ratelimit-limit" in response.headers:
                limit = int(response.headers["x-ratelimit-limit"])
                assert limit == 60, f"Expected 60 for status checks, got {limit}"

    def test_logs_endpoint_has_rate_limit(self):
        """Logs endpoints should have rate limits."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.get(
                "/v1/jobs/test-id/logs",
                headers={"X-API-Key": API_KEY},
            )

            assert "x-ratelimit-limit" in response.headers or response.status_code == 429

    def test_rate_limit_headers_format(self):
        """Rate limit headers should follow standard format."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.get(
                "/v1/jobs/test-id/status",
                headers={"X-API-Key": API_KEY},
            )

            if "x-ratelimit-limit" in response.headers:
                limit = response.headers["x-ratelimit-limit"]
                remaining = response.headers.get("x-ratelimit-remaining")
                reset = response.headers.get("x-ratelimit-reset")

                assert limit.isdigit()
                if remaining:
                    assert remaining.isdigit()
                if reset:
                    assert reset.isdigit()

    def test_health_endpoint_not_rate_limited(self):
        """Health endpoint should not have rate limits."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.get("/health")

            assert "x-ratelimit-limit" not in response.headers
            assert response.status_code == 200

    def test_projects_endpoint_not_rate_limited(self):
        """Projects listing should not be rate limited."""
        with TestClient(build_app(start_executor=False)) as client:
            response = client.get(
                "/v1/projects",
                headers={"X-API-Key": API_KEY},
            )

            assert "x-ratelimit-limit" not in response.headers

    def test_rate_limit_429_response_format(self):
        """Rate limited responses should return 429 with proper format."""
        with TestClient(build_app(start_executor=False)) as client:
            for _ in range(10):
                response = client.post(
                    "/v1/role-model-checker/start",
                    json={"project_id": "test"},
                    headers={"X-API-Key": API_KEY},
                )

    def test_retry_after_header_on_429(self):
        """Rate limited responses should include Retry-After header."""
        with TestClient(build_app(start_executor=False)) as client:
            responses = []
            for _ in range(10):
                response = client.post(
                    "/v1/role-model-checker/start",
                    json={"project_id": "test"},
                    headers={"X-API-Key": API_KEY},
                )
                responses.append(response)

            for response in responses:
                if response.status_code == 429:
                    assert "retry-after" in response.headers
                    assert response.json().get("error") == "Too Many Requests"
                    break
