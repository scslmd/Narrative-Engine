from __future__ import annotations

import re
from typing import Any


class PathTraversalMiddleware:
    """Security middleware to prevent path traversal attacks (SEC-04).
    
    Validates that URL paths and query parameters don't contain path traversal
    sequences like '..', encoded variants, or null bytes.
    
    Blocks requests containing:
    - '..' sequences
    - Encoded variants (%2e%2e, %252e%252e)
    - Null bytes (%00)
    - Backslash-based traversal on Windows
    """
    
    # Patterns that indicate path traversal attempts
    TRAVERSAL_PATTERNS = [
        r'\.\.',  # Basic parent directory reference
        r'%2e%2e',  # URL-encoded dots (case insensitive)
        r'%252e',  # Double-encoded percent
        r'%00',  # Null byte injection
        r'\\',  # Backslash (Windows path separator)
    ]
    
    def __init__(self, app: Any):
        self.app = app
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.TRAVERSAL_PATTERNS]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check the path for traversal patterns
        raw_path = scope.get("path", "")
        query_string = scope.get("query_string", b"")
        
        # Decode query string to check it too
        try:
            query_str = query_string.decode('utf-8', errors='replace')
        except Exception:
            query_str = ""
        
        # Check both path and query string for traversal patterns
        combined_check = f"{raw_path}?{query_str}"
        
        for pattern in self.compiled_patterns:
            if pattern.search(combined_check):
                async def blocked_send(message):
                    if message["type"] == "http.response.start":
                        new_message = {
                            "type": "http.response.start",
                            "status": 400,
                            "headers": [
                                [b"content-type", b"application/json"],
                            ],
                        }
                        return await send(new_message)
                    elif message["type"] == "http.response.body":
                        import json
                        body = json.dumps({
                            "detail": "Invalid path: potential path traversal detected"
                        }).encode()
                        new_message = {
                            "type": "http.response.body",
                            "body": body,
                            "more_body": False,
                        }
                        return await send(new_message)
                    return await send(message)
                
                return await self.app(scope, receive, blocked_send)
        
        # No traversal patterns found, proceed normally
        await self.app(scope, receive, send)


def build_path_traversal_middleware(app: Any) -> PathTraversalMiddleware:
    """Factory function to create path traversal middleware."""
    return PathTraversalMiddleware(app)
