"""Authentication API endpoints (SEC-02)."""

from __future__ import annotations

import secrets

from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, status

from ..services.authentication import AuthenticationError, get_auth_service


router = APIRouter(prefix="/auth", tags=["authentication"])


@dataclass
class CreateAPIKeyRequest:
    """Request to create a new API key."""
    
    name: str
    owner_id: str | None = None
    permissions: list[str] = field(default_factory=lambda: ["read", "write"])
    expires_in_days: int | None = None


@dataclass
class CreateAPIKeyResponse:
    """Response containing newly created API key."""
    
    key_id: str
    prefix: str
    full_key: str  # Only returned once at creation!
    name: str
    permissions: list[str]
    created_at: str
    expires_at: str | None


@router.post("/keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(request: CreateAPIKeyRequest) -> CreateAPIKeyResponse:
    """Create a new API key.
    
    IMPORTANT: The full_key is only returned once during creation.
    Store it securely as it cannot be retrieved later.
    
    Args:
        request: Key creation parameters
        
    Returns:
        New API key with full secret (one-time return)
    """
    try:
        auth_service = get_auth_service()
        
        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Key name cannot be empty",
            )
        
        if len(request.name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Key name exceeds maximum length of 100 characters",
            )
        
        # Validate permissions
        valid_permissions = {"read", "write", "admin"}
        for perm in request.permissions:
            if perm not in valid_permissions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission '{perm}'. Must be one of: {valid_permissions}",
                )
        
        # Create key
        api_key, full_key = auth_service.create_key(
            name=request.name.strip(),
            owner_id=request.owner_id,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days,
        )
        
        return CreateAPIKeyResponse(
            key_id=api_key.key_id,
            prefix=api_key.prefix,
            full_key=full_key,  # Full key from service
            name=api_key.name,
            permissions=api_key.permissions,
            created_at=api_key.created_at.isoformat(),
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/keys")
async def list_api_keys(owner_id: str | None = None) -> dict:
    """List API keys (without secrets).
    
    Args:
        owner_id: Optional filter by owner ID
        
    Returns:
        List of key metadata
    """
    try:
        auth_service = get_auth_service()
        keys = auth_service.list_keys(owner_id=owner_id)
        
        return {
            "keys": keys,
            "count": len(keys),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {e}",
        ) from e


@router.delete("/keys/{prefix}")
async def revoke_api_key(prefix: str) -> dict:
    """Revoke an API key.
    
    Args:
        prefix: Key prefix to revoke
        
    Returns:
        Confirmation of revocation
    """
    try:
        auth_service = get_auth_service()
        
        if not auth_service.revoke_key(prefix):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with prefix '{prefix}' not found",
            )
        
        return {
            "message": f"API key '{prefix}' has been revoked",
            "prefix": prefix,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {e}",
        ) from e
