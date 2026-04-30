from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Configuration for a specific rate limit."""
    max_requests: int
    window_seconds: int


# Rate limit configurations (SEC-05)
RATE_LIMITS = {
    # Jobs creation: 10 requests per minute
    "jobs_create": RateLimitConfig(max_requests=10, window_seconds=60),
    # Checker runs: 5 requests per minute  
    "checker_runs": RateLimitConfig(max_requests=5, window_seconds=60),
    # Status checks: 60 requests per minute (more lenient for polling)
    "status_checks": RateLimitConfig(max_requests=60, window_seconds=60),
}


@dataclass
class ClientRequestHistory:
    """Tracks request timestamps for a client."""
    timestamps: list[float] = field(default_factory=list)
    
    def add_request(self) -> bool:
        """Add a request timestamp. Returns True if allowed, False if rate limited."""
        self.timestamps.append(time.time())
        return True
    
    def prune_old_requests(self, window_seconds: int) -> None:
        """Remove timestamps older than the window."""
        cutoff = time.time() - window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
    
    def count_in_window(self, window_seconds: int) -> int:
        """Count requests within the time window."""
        cutoff = time.time() - window_seconds
        return sum(1 for ts in self.timestamps if ts > cutoff)


class RateLimitMiddleware:
    """Rate limiting middleware (SEC-05).
    
    Enforces different rate limits based on endpoint type:
    - Jobs creation (/v1/jobs/create): 10 requests per minute
    - Checker runs (/v1/role-model-checker/start): 5 requests per minute
    - Status checks (*status, *logs): 60 requests per minute
    
    Rate limits are tracked per client IP address.
    """
    
    def __init__(self, app: Any):
        self.app = app
        # Track request history per client IP
        self.client_history: dict[str, ClientRequestHistory] = defaultdict(ClientRequestHistory)
    
    def _get_client_ip(self, scope: dict) -> str:
        """Extract client IP from ASGI scope (IP only, not port)."""
        client = scope.get("client")
        if client:
            return client[0]  # Just the IP address, not the port
        return "unknown"
    
    def _get_rate_limit_key(self, path: str) -> str | None:
        """Determine which rate limit applies to a given path."""
        # Jobs creation endpoint
        if "/v1/jobs/create" in path:
            return "jobs_create"
        
        # Checker runs endpoint
        if "/v1/role-model-checker/start" in path:
            return "checker_runs"
        
        # Status check endpoints (more lenient for polling)
        if "/status" in path or "/logs" in path:
            return "status_checks"
        
        return None
    
    def _check_rate_limit(self, client_ip: str, limit_key: str) -> tuple[bool, int]:
        """Check if request is within rate limits.
        
        Returns (is_allowed, remaining_requests).
        """
        config = RATE_LIMITS.get(limit_key)
        if not config:
            return True, -1  # No limit configured
        
        history = self.client_history[client_ip]
        
        # Prune old requests
        history.prune_old_requests(config.window_seconds)
        
        # Count current requests in window
        current_count = history.count_in_window(config.window_seconds)
        
        if current_count >= config.max_requests:
            return False, 0
        
        # Add this request
        history.add_request()
        remaining = config.max_requests - current_count - 1
        
        return True, max(0, remaining)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        # Determine which rate limit applies
        limit_key = self._get_rate_limit_key(path)
        
        if not limit_key:
            # No rate limit for this endpoint
            await self.app(scope, receive, send)
            return
        
        # Get client IP and check rate limit
        client_ip = self._get_client_ip(scope)
        is_allowed, remaining = self._check_rate_limit(client_ip, limit_key)
        
        if not is_allowed:
            config = RATE_LIMITS[limit_key]
            retry_after = str(config.window_seconds)
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Please retry after {config.window_seconds} seconds.",
                    "error": "Too Many Requests",
                },
                headers={
                    "retry-after": retry_after,
                    "x-ratelimit-limit": str(config.max_requests),
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-reset": str(int(time.time()) + config.window_seconds),
                },
            )
            await response(scope, receive, send)
            return
        
        # Request allowed - add rate limit headers to response
        original_send = send
        
        async def enhanced_send(message):
            if message["type"] == "http.response.start":
                # Add rate limit headers
                headers = list(message.get("headers", []))
                config = RATE_LIMITS[limit_key]
                
                # Find existing headers to avoid duplicates
                header_keys = {h[0].lower() for h in headers}
                
                if b"x-ratelimit-limit" not in header_keys:
                    headers.append([b"x-ratelimit-limit", str(config.max_requests).encode()])
                if b"x-ratelimit-remaining" not in header_keys:
                    headers.append([b"x-ratelimit-remaining", str(remaining).encode()])
                if b"x-ratelimit-reset" not in header_keys:
                    reset_time = int(time.time()) + config.window_seconds
                    headers.append([b"x-ratelimit-reset", str(reset_time).encode()])
                
                message["headers"] = headers
            
            return await original_send(message)
        
        await self.app(scope, receive, enhanced_send)


def build_rate_limit_middleware(app: Any) -> RateLimitMiddleware:
    """Factory function to create rate limit middleware."""
    return RateLimitMiddleware(app)
