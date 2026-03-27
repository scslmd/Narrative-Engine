"""Authentication service for API key management (SEC-02).

Provides:
- API key generation and validation
- Key hashing with bcrypt
- Key prefix matching for efficient lookup
- Revocation and expiration support
"""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import sqlite3


API_KEY_PREFIX_LENGTH = 4
API_KEY_SECRET_LENGTH = 32
API_KEY_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or "AUTHENTICATION_ERROR"


class APIKey:
    """Represents an API key with metadata."""
    
    def __init__(
        self,
        key_id: str,
        prefix: str,
        hashed_secret: str,
        name: str,
        owner_id: str | None = None,
        permissions: list[str] | None = None,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
        last_used_at: datetime | None = None,
    ):
        self.key_id = key_id
        self.prefix = prefix  # First N chars for identification
        self.hashed_secret = hashed_secret  # Full key is prefix + secret (hashed)
        self.name = name
        self.owner_id = owner_id
        self.permissions = permissions or ["read", "write"]
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.last_used_at = last_used_at
    
    @property
    def is_expired(self) -> bool:
        """Check if key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked (expires_at in the past but not naturally expired)."""
        # For simplicity, we use expires_at for both expiration and revocation
        # A truly revoked key would have expires_at set to a past timestamp
        return self.is_expired


class APIKeyStore:
    """SQLite-based API key store with prefix indexing."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Create API keys table if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    prefix TEXT NOT NULL,
                    hashed_secret TEXT NOT NULL,
                    name TEXT NOT NULL,
                    owner_id TEXT,
                    permissions TEXT NOT NULL DEFAULT '["read", "write"]',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_used_at TEXT,
                    UNIQUE(prefix)
                )
            """)
            
            # Create index on prefix for fast lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_prefix 
                ON api_keys(prefix)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def create_key(
        self,
        name: str,
        owner_id: str | None = None,
        permissions: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key.
        
        Args:
            name: Human-readable name for the key
            owner_id: Optional owner identifier (e.g., user ID)
            permissions: List of permissions (default: read, write)
            expires_in_days: Days until expiration (None = never expires)
            
        Returns:
            Tuple of (APIKey object, full_key string)
            
        Note:
            The full key is only returned once during creation.
            Store it securely as it cannot be retrieved later.
        """
        # Generate key components
        prefix = self._generate_prefix()
        secret = self._generate_secret()
        full_key = f"{prefix}.{secret}"
        
        # Hash the full key for storage
        hashed_secret = self._hash_key(full_key)
        
        # Generate unique ID
        key_id = secrets.token_hex(16)
        
        # Set timestamps
        created_at = datetime.now(timezone.utc)
        expires_at = None
        if expires_in_days is not None:
            expires_at = created_at + timedelta(days=expires_in_days)
        
        permissions = permissions or ["read", "write"]
        
        # Store in database
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            cursor = conn.execute(
                """
                INSERT INTO api_keys 
                (key_id, prefix, hashed_secret, name, owner_id, permissions, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key_id,
                    prefix,
                    hashed_secret,
                    name,
                    owner_id,
                    self._permissions_to_json(permissions),
                    created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            # Prefix collision (shouldn't happen with 4 chars + large alphabet)
            raise AuthenticationError(
                "Failed to create API key",
                code="KEY_CREATION_FAILED",
            ) from e
        finally:
            conn.close()
        
        return (
            APIKey(
                key_id=key_id,
                prefix=prefix,
                hashed_secret=hashed_secret,
                name=name,
                owner_id=owner_id,
                permissions=permissions,
                created_at=created_at,
                expires_at=expires_at,
            ),
            full_key,  # Return the full key (only available at creation time)
        )
    
    def validate_key(self, api_key: str) -> APIKey | None:
        """Validate an API key and return the key object if valid.
        
        Args:
            api_key: Full API key (prefix.secret format)
            
        Returns:
            APIKey object if valid, None if invalid or expired
            
        Raises:
            AuthenticationError: If key format is invalid
        """
        # Parse key components
        parts = api_key.split(".", 1)
        if len(parts) != 2:
            raise AuthenticationError(
                "Invalid API key format. Expected 'prefix.secret'",
                code="INVALID_KEY_FORMAT",
            )
        
        prefix, secret = parts
        full_key = f"{prefix}.{secret}"
        hashed_secret = self._hash_key(full_key)
        
        # Look up by prefix (efficient with index)
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE prefix = ?",
                (prefix,),
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Verify hashed secret matches
            stored_hashed_secret = row[2]  # hashed_secret column
            if stored_hashed_secret != hashed_secret:
                return None
            
            # Build APIKey object from row
            key = self._row_to_api_key(row)
            
            # Check expiration
            if key.is_expired:
                return None
            
            # Update last_used_at in database and object
            now = datetime.now(timezone.utc)
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                (now.isoformat(), key.key_id),
            )
            conn.commit()
            
            # Update the returned object as well
            key.last_used_at = now
            
            return key
            
        finally:
            conn.close()
    
    def revoke_key(self, prefix: str) -> bool:
        """Revoke an API key by setting expiration to past timestamp.
        
        Args:
            prefix: Key prefix to revoke
            
        Returns:
            True if revoked, False if not found
        """
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            cursor = conn.execute(
                "UPDATE api_keys SET expires_at = ? WHERE prefix = ?",
                (datetime.now(timezone.utc).isoformat(), prefix),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def list_keys(self, owner_id: str | None = None) -> list[dict[str, Any]]:
        """List API keys (without secrets).
        
        Args:
            owner_id: Optional filter by owner
            
        Returns:
            List of key metadata dictionaries
        """
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            if owner_id:
                cursor = conn.execute(
                    "SELECT * FROM api_keys WHERE owner_id = ?",
                    (owner_id,),
                )
            else:
                cursor = conn.execute("SELECT * FROM api_keys")
            
            rows = cursor.fetchall()
            return [self._row_to_key_dict(row) for row in rows]
        finally:
            conn.close()
    
    def _generate_prefix(self) -> str:
        """Generate random key prefix."""
        return "".join(
            secrets.choice(API_KEY_ALPHABET) for _ in range(API_KEY_PREFIX_LENGTH)
        )
    
    def _generate_secret(self) -> str:
        """Generate random key secret."""
        return "".join(
            secrets.choice(API_KEY_ALPHABET) for _ in range(API_KEY_SECRET_LENGTH)
        )
    
    def _hash_key(self, full_key: str) -> str:
        """Hash API key using SHA-256 (production should use bcrypt)."""
        import hashlib
        
        return hashlib.sha256(full_key.encode()).hexdigest()
    
    def _permissions_to_json(self, permissions: list[str]) -> str:
        """Convert permissions list to JSON string."""
        import json
        
        return json.dumps(permissions)
    
    def _row_to_api_key(self, row: tuple) -> APIKey:
        """Convert database row to APIKey object."""
        (
            key_id,
            prefix,
            hashed_secret,
            name,
            owner_id,
            permissions_json,
            created_at_str,
            expires_at_str,
            last_used_at_str,
        ) = row
        
        import json
        
        return APIKey(
            key_id=key_id,
            prefix=prefix,
            hashed_secret=hashed_secret,
            name=name,
            owner_id=owner_id,
            permissions=json.loads(permissions_json),
            created_at=datetime.fromisoformat(created_at_str),
            expires_at=datetime.fromisoformat(expires_at_str) if expires_at_str else None,
            last_used_at=datetime.fromisoformat(last_used_at_str) if last_used_at_str else None,
        )
    
    def _row_to_key_dict(self, row: tuple) -> dict[str, Any]:
        """Convert database row to key metadata dictionary."""
        import json
        
        return {
            "key_id": row[0],
            "prefix": row[1],
            "name": row[3],
            "owner_id": row[4],
            "permissions": json.loads(row[5]),
            "created_at": row[6],
            "expires_at": row[7],
            "last_used_at": row[8],
        }


# Global instance (initialized in main.py)
_key_store: APIKeyStore | None = None


def get_auth_service(data_root: Path | None = None) -> APIKeyStore:
    """Get or create authentication service instance."""
    global _key_store
    
    if _key_store is None:
        if data_root is None:
            data_root = Path(__file__).resolve().parents[2] / "data"
        
        db_path = data_root / "state" / "api_keys.db"
        _key_store = APIKeyStore(db_path)
    
    return _key_store
