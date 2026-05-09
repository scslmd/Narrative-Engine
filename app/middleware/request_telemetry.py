"""Structured telemetry for legacy route usage during API migration."""
from __future__ import annotations

import json
import logging
import time
from typing import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger(__name__)

EXEMPT_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/assets",
    "/static",
)
EXEMPT_PATHS = {"/", "/role-model-checker-ui", "/vite.svg"}


async def legacy_route_telemetry_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Emit `legacy_route_hit` events for non-/v1 routes."""
    path = request.url.path

    if path in EXEMPT_PATHS or any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
        return await call_next(request)

    if not path.startswith("/v1/"):
        event = {
            "event": "legacy_route_hit",
            "timestamp": time.time(),
            "method": request.method,
            "path": path,
            "client_host": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
        }
        logger.info(json.dumps(event))

    return await call_next(request)
