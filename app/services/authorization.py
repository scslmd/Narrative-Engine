"""Authorization service for permission-based access control (SEC-03).

Provides:
- Permission checking based on API key permissions
- Owner-based resource access control
- Role-based authorization patterns
"""

from __future__ import annotations

from typing import Any


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or "AUTHORIZATION_ERROR"


# Permission levels (from least to most privileged)
PERMISSION_READ = "read"
PERMISSION_WRITE = "write"
PERMISSION_ADMIN = "admin"

ALL_PERMISSIONS = {PERMISSION_READ, PERMISSION_WRITE, PERMISSION_ADMIN}


class AuthorizationService:
    """Permission-based authorization service."""
    
    def __init__(self):
        pass
    
    def check_permission(
        self,
        user_permissions: list[str],
        required_permission: str,
    ) -> bool:
        """Check if user has the required permission.
        
        Args:
            user_permissions: List of permissions granted to user
            required_permission: Permission required for operation
            
        Returns:
            True if authorized, False otherwise
            
        Note:
            Admin permission grants all access.
            Write permission includes read access.
        """
        # Admin has all permissions
        if PERMISSION_ADMIN in user_permissions:
            return True
        
        # Write includes read
        if required_permission == PERMISSION_READ and PERMISSION_WRITE in user_permissions:
            return True
        
        # Direct match
        return required_permission in user_permissions
    
    def require_permission(
        self,
        user_permissions: list[str],
        required_permission: str,
    ) -> None:
        """Require a permission or raise AuthorizationError.
        
        Args:
            user_permissions: List of permissions granted to user
            required_permission: Permission required for operation
            
        Raises:
            AuthorizationError: If permission not granted
        """
        if not self.check_permission(user_permissions, required_permission):
            raise AuthorizationError(
                f"Permission '{required_permission}' is required for this operation",
                code="INSUFFICIENT_PERMISSIONS",
            )


class ResourceAuthorizationService(AuthorizationService):
    """Extended authorization with resource ownership checks."""
    
    def check_resource_access(
        self,
        user_permissions: list[str],
        user_owner_id: str | None,
        resource_owner_id: str | None,
        required_permission: str = PERMISSION_READ,
    ) -> bool:
        """Check if user can access a specific resource.
        
        Args:
            user_permissions: User's API key permissions
            user_owner_id: User's owner ID (from API key)
            resource_owner_id: Resource's owner ID
            required_permission: Permission level needed
            
        Returns:
            True if authorized to access the resource
            
        Logic:
            - Admin permission grants all access
            - Users can always access their own resources with appropriate permissions
            - Cross-owner access requires explicit admin permission
        """
        # Admin has full access to everything
        if PERMISSION_ADMIN in user_permissions:
            return True
        
        # Check basic permission level first
        if not self.check_permission(user_permissions, required_permission):
            return False
        
        # If resource has an owner, check ownership
        if resource_owner_id is not None:
            # User must either own the resource or have admin permission
            if user_owner_id is None:
                # Unauthenticated users can't access owned resources
                return False
            
            # Users can only access their own resources (unless admin)
            if user_owner_id != resource_owner_id:
                return False
        
        return True
    
    def require_resource_access(
        self,
        user_permissions: list[str],
        user_owner_id: str | None,
        resource_owner_id: str | None,
        required_permission: str = PERMISSION_READ,
    ) -> None:
        """Require access to a specific resource or raise AuthorizationError.
        
        Args:
            user_permissions: User's API key permissions
            user_owner_id: User's owner ID (from API key)
            resource_owner_id: Resource's owner ID
            required_permission: Permission level needed
            
        Raises:
            AuthorizationError: If not authorized to access the resource
        """
        if not self.check_resource_access(
            user_permissions,
            user_owner_id,
            resource_owner_id,
            required_permission,
        ):
            error_msg = f"Access denied to resource"
            
            if resource_owner_id is not None and user_owner_id != resource_owner_id:
                error_msg += " (resource belongs to another owner)"
            elif not self.check_permission(user_permissions, required_permission):
                error_msg += f" (requires '{required_permission}' permission)"
            
            raise AuthorizationError(error_msg, code="RESOURCE_ACCESS_DENIED")


# Global authorization service instance
_auth_service: ResourceAuthorizationService | None = None


def get_authorization_service() -> ResourceAuthorizationService:
    """Get or create authorization service instance."""
    global _auth_service
    
    if _auth_service is None:
        _auth_service = ResourceAuthorizationService()
    
    return _auth_service
