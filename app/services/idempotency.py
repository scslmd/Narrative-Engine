"""Idempotency key management for retry-safe operations (REL-02).

Prevents duplicate operations by tracking idempotency keys with 24h TTL.
Used for project creation and story-development writes.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


IDEMPOTENCY_TTL_HOURS = 24


@dataclass
class IdempotencyRecord:
    """Record of an idempotent operation."""
    
    key: str
    operation_type: str  # "project_create", "job_create", etc.
    operation_id: str  # project_id, job_id, etc.
    request_hash: str  # SHA256 hash of request payload
    created_at: datetime
    response_data: dict[str, Any] | None = None
    
    def is_expired(self) -> bool:
        """Check if record has expired (TTL exceeded)."""
        expiry = self.created_at + timedelta(hours=IDEMPOTENCY_TTL_HOURS)
        return datetime.now(timezone.utc) > expiry


class IdempotencyError(Exception):
    """Raised when idempotency check fails."""
    
    def __init__(self, message: str, existing_id: str | None = None):
        super().__init__(message)
        self.message = message
        self.existing_id = existing_id


class IdempotencyStore:
    """Thread-safe store for idempotency records.
    
    Uses in-memory storage with periodic cleanup of expired records.
    For production, consider SQLite or Redis backend.
    """
    
    def __init__(self):
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()
    
    def get(self, operation_type: str, idempotency_key: str) -> IdempotencyRecord | None:
        """Get existing record for idempotency key."""
        composite_key = f"{operation_type}:{idempotency_key}"
        
        with self._lock:
            record = self._records.get(composite_key)
            
            if record and record.is_expired():
                # Clean up expired record
                del self._records[composite_key]
                return None
            
            return record
    
    def create(
        self,
        operation_type: str,
        idempotency_key: str,
        operation_id: str,
        request_hash: str,
    ) -> IdempotencyRecord:
        """Create new idempotency record."""
        composite_key = f"{operation_type}:{idempotency_key}"
        
        with self._lock:
            # Double-check no existing record
            if composite_key in self._records:
                raise IdempotencyError(
                    f"Idempotency key already exists",
                    existing_id=self._records[composite_key].operation_id,
                )
            
            record = IdempotencyRecord(
                key=idempotency_key,
                operation_type=operation_type,
                operation_id=operation_id,
                request_hash=request_hash,
                created_at=datetime.now(timezone.utc),
            )
            
            self._records[composite_key] = record
            return record
    
    def update_response(
        self,
        operation_type: str,
        idempotency_key: str,
        response_data: dict[str, Any],
    ) -> None:
        """Update record with response data after successful operation."""
        composite_key = f"{operation_type}:{idempotency_key}"
        
        with self._lock:
            if composite_key in self._records:
                self._records[composite_key].response_data = response_data
    
    def cleanup_expired(self) -> int:
        """Remove expired records. Returns count of removed records."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, record in self._records.items()
            if now > record.created_at + timedelta(hours=IDEMPOTENCY_TTL_HOURS)
        ]
        
        with self._lock:
            for key in expired_keys:
                del self._records[key]
        
        return len(expired_keys)


# Global idempotency store instance
_store = IdempotencyStore()


def hash_request(payload: dict[str, Any]) -> str:
    """Create deterministic hash of request payload."""
    import json
    
    # Sort keys for consistent hashing
    normalized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def check_idempotency(
    operation_type: str,
    idempotency_key: str | None,
    operation_id: str,
    payload: dict[str, Any],
) -> tuple[bool, IdempotencyRecord | None]:
    """Check and create idempotency record.
    
    Args:
        operation_type: Type of operation ("project_create", "job_create")
        idempotency_key: Client-provided idempotency key (optional)
        operation_id: Generated ID for this operation
        payload: Request payload to hash
        
    Returns:
        Tuple of (is_new_operation, existing_record)
        
        - If is_new_operation=True: This is a new operation, record created
        - If is_new_operation=False: Duplicate detected, return existing record
        
    Raises:
        IdempotencyError: If idempotency key exists but for different operation
    """
    if not idempotency_key:
        # No idempotency key provided - always allow new operation
        return True, None
    
    request_hash = hash_request(payload)
    
    # Check for existing record
    existing = _store.get(operation_type, idempotency_key)
    
    if existing:
        # Idempotency key already used
        if existing.request_hash != request_hash:
            raise IdempotencyError(
                f"Idempotency key exists but request payload differs",
                existing_id=existing.operation_id,
            )
        
        # Same operation - return existing result (idempotent)
        return False, existing
    
    # New operation - create record
    try:
        record = _store.create(
            operation_type=operation_type,
            idempotency_key=idempotency_key,
            operation_id=operation_id,
            request_hash=request_hash,
        )
        return True, record
    except IdempotencyError:
        # Race condition - another thread created the record
        raise


def store_response(
    operation_type: str,
    idempotency_key: str | None,
    response_data: dict[str, Any],
) -> None:
    """Store response data for idempotent operation."""
    if not idempotency_key:
        return
    
    _store.update_response(operation_type, idempotency_key, response_data)


def get_idempotency_store() -> IdempotencyStore:
    """Get the global idempotency store (for testing/monitoring)."""
    return _store
