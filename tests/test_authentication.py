"""Tests for authentication service (SEC-02)."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone

from app.services.authentication import APIKeyStore, AuthenticationError


class TestAPIKeyStore:
    """Test API key store functionality."""
    
    @pytest.fixture
    def temp_db(self, tmp_path: Path) -> tuple[Path, APIKeyStore]:
        """Create temporary database and key store."""
        db_path = tmp_path / "api_keys.db"
        store = APIKeyStore(db_path)
        return db_path, store
    
    def test_create_key_returns_valid_key(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should create a valid API key."""
        _, store = temp_db
        
        api_key, full_key = store.create_key(name="Test Key")
        
        assert api_key.key_id is not None
        assert api_key.prefix is not None
        assert len(api_key.prefix) == 4
        assert api_key.name == "Test Key"
        assert api_key.permissions == ["read", "write"]
        assert full_key is not None
        assert "." in full_key
    
    def test_create_key_with_custom_permissions(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should create key with custom permissions."""
        _, store = temp_db
        
        api_key, _ = store.create_key(
            name="Admin Key",
            permissions=["read", "write", "admin"],
        )
        
        assert set(api_key.permissions) == {"read", "write", "admin"}
    
    def test_create_key_with_expiration(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should create key with expiration date."""
        _, store = temp_db
        
        api_key, _ = store.create_key(
            name="Temporary Key",
            expires_in_days=30,
        )
        
        assert api_key.expires_at is not None
        expected_expiry = api_key.created_at + timedelta(days=30)
        # Allow 1 second tolerance
        assert abs((api_key.expires_at - expected_expiry).total_seconds()) < 1
    
    def test_validate_key_with_valid_key(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should validate a valid key."""
        _, store = temp_db
        
        # Create key
        _, full_key = store.create_key(name="Test Key")
        
        # Validate it
        validated = store.validate_key(full_key)
        
        assert validated is not None
        assert validated.name == "Test Key"
    
    def test_validate_key_with_invalid_format(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should reject invalid key format."""
        _, store = temp_db
        
        with pytest.raises(AuthenticationError) as exc_info:
            store.validate_key("invalid-key-format")
        
        assert "Invalid API key format" in str(exc_info.value)
    
    def test_validate_key_with_wrong_secret(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should reject key with wrong secret."""
        _, store = temp_db
        
        # Create a valid key
        api_key, _ = store.create_key(name="Test Key")
        
        # Try to validate with wrong secret
        fake_key = f"{api_key.prefix}.wrongsecret1234567890abcdef"
        validated = store.validate_key(fake_key)
        
        assert validated is None
    
    def test_validate_expired_key_returns_none(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should return None for expired keys."""
        _, store = temp_db
        
        # Create key that expires immediately (0 days)
        api_key, full_key = store.create_key(
            name="Expired Key",
            expires_in_days=0,
        )
        
        validated = store.validate_key(full_key)
        assert validated is None
    
    def test_revoke_key(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should revoke a key."""
        _, store = temp_db
        
        # Create and validate key
        api_key, full_key = store.create_key(name="Test Key")
        
        assert store.validate_key(full_key) is not None
        
        # Revoke it
        result = store.revoke_key(api_key.prefix)
        
        assert result is True
        
        # Should no longer be valid
        validated = store.validate_key(full_key)
        assert validated is None
    
    def test_revoke_nonexistent_key_returns_false(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should return False for non-existent key."""
        _, store = temp_db
        
        result = store.revoke_key("nonexistent")
        
        assert result is False
    
    def test_list_keys(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should list all keys."""
        _, store = temp_db
        
        # Create multiple keys
        store.create_key(name="Key 1", owner_id="user1")
        store.create_key(name="Key 2", owner_id="user1")
        store.create_key(name="Key 3", owner_id="user2")
        
        all_keys = store.list_keys()
        
        assert len(all_keys) == 3
    
    def test_list_keys_filtered_by_owner(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should filter keys by owner."""
        _, store = temp_db
        
        # Create keys for different owners
        store.create_key(name="User1 Key", owner_id="user1")
        store.create_key(name="User2 Key", owner_id="user2")
        
        user1_keys = store.list_keys(owner_id="user1")
        
        assert len(user1_keys) == 1
        assert user1_keys[0]["name"] == "User1 Key"
    
    def test_prefix_uniqueness(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should ensure prefix uniqueness."""
        _, store = temp_db
        
        # Create multiple keys and verify all have unique prefixes
        keys = []
        for i in range(10):
            api_key, _ = store.create_key(name=f"Key {i}")
            keys.append(api_key)
        
        prefixes = [k.prefix for k in keys]
        assert len(prefixes) == len(set(prefixes))  # All unique
    
    def test_last_used_at_updated_on_validation(self, temp_db: tuple[Path, APIKeyStore]) -> None:
        """Should update last_used_at when key is validated."""
        _, store = temp_db
        
        api_key, full_key = store.create_key(name="Test Key")
        
        # Initially no last_used_at in the returned object
        assert api_key.last_used_at is None
        
        # Validate the key - this should update last_used_at in DB
        validated = store.validate_key(full_key)
        
        # The validated key from DB should have last_used_at set
        assert validated is not None
        assert validated.last_used_at is not None
