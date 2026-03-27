from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request, status


class AuthMiddleware:
    """API Key authentication middleware.
    
    Requires X-API-Key header on all requests except /health endpoint.
    API key is read from the API_KEY environment variable.
    """
    
    def __init__(self, app: Any, api_key: str | None = None):
        self.app = app
        self.api_key = api_key or os.getenv("API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "API_KEY environment variable is not set. "
                "Set it in your .env file to enable authentication."
            )
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope)
        
        # Skip authentication for health check endpoint
        if request.url.path.startswith("/health"):
            await self.app(scope, receive, send)
            return
        
        # Get API key from header
        api_key_header = request.headers.get("X-API-Key")
        
        # Validate API key (simple string comparison for local-first use)
        if not api_key_header or api_key_header != self.api_key:
            async def unauthorized_send(message):
                if message["type"] == "http.response.start":
                    new_message = {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [
                            [b"content-type", b"application/json"],
                            [b"www-authenticate", b"Bearer"],
                        ],
                    }
                    return await send(new_message)
                elif message["type"] == "http.response.body":
                    import json
                    body = json.dumps({"detail": "Invalid or missing API key"}).encode()
                    new_message = {
                        "type": "http.response.body",
                        "body": body,
                        "more_body": False,
                    }
                    return await send(new_message)
                return await send(message)
            
            return await self.app(scope, receive, unauthorized_send)
        
        # Add validated API key to request state for downstream use
        scope["auth"] = {"api_key_hash": hash(api_key_header)}
        
        await self.app(scope, receive, send)


def build_auth_middleware(app: Any) -> AuthMiddleware:
    """Factory function to create auth middleware with configured API key."""
    return AuthMiddleware(app)
