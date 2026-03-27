"""Authentication middleware for FastAPI (SEC-02)."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..services.authentication import APIKey, AuthenticationError, get_auth_service


security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> APIKey | None:
    """Verify API key from Authorization header.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials (optional)
        
    Returns:
        Validated APIKey if present and valid, None otherwise
        
    Raises:
        HTTPException: If key format is invalid or authentication fails
    """
    # Allow requests without API key for now (can be made mandatory per-route)
    if credentials is None:
        return None
    
    try:
        auth_service = get_auth_service()
        api_key = auth_service.validate_key(credentials.credentials)
        
        if api_key is None:
            # Key not found or expired - but don't reveal which
            request.state.authenticated = False
            return None
        
        request.state.authenticated = True
        request.state.api_key = api_key
        return api_key
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a route.
    
    Usage:
        @router.get("/protected")
        async def protected(require=Depends(require_auth)):
            return {"message": "authenticated"}
    """
    async def wrapper(api_key: APIKey | None = Depends(verify_api_key)) -> APIKey:
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return api_key
    
    return wrapper


def require_permission(permission: str) -> Callable:
    """Dependency to check for specific permission.
    
    Usage:
        @router.post("/admin")
        async def admin_action(
            key=Depends(require_auth),
            _=Depends(require_permission("admin")),
        ):
            return {"message": "admin action"}
    """
    async def check_permission(api_key: APIKey = Depends(require_auth)) -> None:
        if permission not in api_key.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
    
    return check_permission
