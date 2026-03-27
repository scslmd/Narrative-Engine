"""Tests for authorization service (SEC-03)."""

import pytest

from app.services.authorization import (
    AuthorizationError,
    PERMISSION_ADMIN,
    PERMISSION_READ,
    PERMISSION_WRITE,
    ResourceAuthorizationService,
)


class TestAuthorizationService:
    """Test basic permission checking."""
    
    @pytest.fixture
    def auth_service(self) -> ResourceAuthorizationService:
        return ResourceAuthorizationService()
    
    def test_admin_has_all_permissions(self, auth_service: ResourceAuthorizationService) -> None:
        """Admin should have all permissions."""
        assert auth_service.check_permission([PERMISSION_ADMIN], PERMISSION_READ) is True
        assert auth_service.check_permission([PERMISSION_ADMIN], PERMISSION_WRITE) is True
        assert auth_service.check_permission([PERMISSION_ADMIN], PERMISSION_ADMIN) is True
    
    def test_write_includes_read(self, auth_service: ResourceAuthorizationService) -> None:
        """Write permission should include read access."""
        assert auth_service.check_permission([PERMISSION_WRITE], PERMISSION_READ) is True
        assert auth_service.check_permission([PERMISSION_WRITE], PERMISSION_WRITE) is True
        assert auth_service.check_permission([PERMISSION_WRITE], PERMISSION_ADMIN) is False
    
    def test_read_only_cannot_write(self, auth_service: ResourceAuthorizationService) -> None:
        """Read-only users should not be able to write."""
        assert auth_service.check_permission([PERMISSION_READ], PERMISSION_READ) is True
        assert auth_service.check_permission([PERMISSION_READ], PERMISSION_WRITE) is False
    
    def test_require_permission_raises_on_failure(self, auth_service: ResourceAuthorizationService) -> None:
        """Should raise AuthorizationError when permission not granted."""
        with pytest.raises(AuthorizationError) as exc_info:
            auth_service.require_permission([PERMISSION_READ], PERMISSION_WRITE)
        
        assert "write" in str(exc_info.value).lower()


class TestResourceAuthorizationService:
    """Test resource-based authorization."""
    
    @pytest.fixture
    def auth_service(self) -> ResourceAuthorizationService:
        return ResourceAuthorizationService()
    
    def test_admin_can_access_all_resources(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Admin should access any resource regardless of ownership."""
        assert auth_service.check_resource_access(
            user_permissions=[PERMISSION_ADMIN],
            user_owner_id="user1",
            resource_owner_id="user2",  # Different owner
            required_permission=PERMISSION_READ,
        ) is True
    
    def test_user_can_access_own_resources(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Users should access their own resources with appropriate permissions."""
        assert auth_service.check_resource_access(
            user_permissions=[PERMISSION_READ],
            user_owner_id="user1",
            resource_owner_id="user1",  # Same owner
            required_permission=PERMISSION_READ,
        ) is True
    
    def test_user_cannot_access_others_resources(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Users should not access resources owned by others."""
        assert auth_service.check_resource_access(
            user_permissions=[PERMISSION_READ],
            user_owner_id="user1",
            resource_owner_id="user2",  # Different owner
            required_permission=PERMISSION_READ,
        ) is False
    
    def test_unauthenticated_cannot_access_owned_resources(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Unauthenticated users (no owner_id) cannot access owned resources."""
        assert auth_service.check_resource_access(
            user_permissions=[PERMISSION_READ],
            user_owner_id=None,  # No authentication
            resource_owner_id="user1",
            required_permission=PERMISSION_READ,
        ) is False
    
    def test_insufficient_permission_denies_access(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Insufficient permission level should deny access even for own resources."""
        assert auth_service.check_resource_access(
            user_permissions=[PERMISSION_READ],
            user_owner_id="user1",
            resource_owner_id="user1",  # Own resource
            required_permission=PERMISSION_WRITE,  # But need write
        ) is False
    
    def test_require_resource_access_raises_for_wrong_owner(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Should raise when trying to access another user's resource."""
        with pytest.raises(AuthorizationError) as exc_info:
            auth_service.require_resource_access(
                user_permissions=[PERMISSION_READ],
                user_owner_id="user1",
                resource_owner_id="user2",
                required_permission=PERMISSION_READ,
            )
        
        assert "belongs to another owner" in str(exc_info.value)
    
    def test_require_resource_access_raises_for_insufficient_permission(
        self,
        auth_service: ResourceAuthorizationService,
    ) -> None:
        """Should raise when permission level is insufficient."""
        with pytest.raises(AuthorizationError) as exc_info:
            auth_service.require_resource_access(
                user_permissions=[PERMISSION_READ],
                user_owner_id="user1",
                resource_owner_id="user1",  # Own resource
                required_permission=PERMISSION_WRITE,  # But need write
            )
        
        assert "requires" in str(exc_info.value).lower()


class TestIntegration:
    """Test authorization integration scenarios."""
    
    def test_api_key_with_read_permission(self) -> None:
        """Simulate API key with read-only access to own projects."""
        auth = ResourceAuthorizationService()
        
        # Read-only user accessing their own project - should work
        assert auth.check_resource_access(
            user_permissions=["read"],
            user_owner_id="user123",
            resource_owner_id="user123",
            required_permission=PERMISSION_READ,
        ) is True
        
        # Same user trying to write - should fail
        with pytest.raises(AuthorizationError):
            auth.require_resource_access(
                user_permissions=["read"],
                user_owner_id="user123",
                resource_owner_id="user123",
                required_permission=PERMISSION_WRITE,
            )
    
    def test_api_key_with_admin_permission(self) -> None:
        """Simulate admin API key with full access."""
        auth = ResourceAuthorizationService()
        
        # Admin can do anything to any resource
        assert auth.check_resource_access(
            user_permissions=["admin"],
            user_owner_id="admin_user",
            resource_owner_id="anyone_else",
            required_permission=PERMISSION_ADMIN,
        ) is True
