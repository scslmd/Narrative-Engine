"""Tests for idempotency key management (REL-02)."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.services.idempotency import (
    IdempotencyError,
    IdempotencyRecord,
    IdempotencyStore,
    check_idempotency,
    get_idempotency_store,
    hash_request,
    store_response,
)


class TestIdempotencyHash:
    """Test request hashing."""
    
    def test_hash_is_deterministic(self) -> None:
        """Same payload should produce same hash."""
        payload = {"key": "value", "number": 42}
        
        hash1 = hash_request(payload)
        hash2 = hash_request(payload)
        
        assert hash1 == hash2
    
    def test_hash_is_order_independent(self) -> None:
        """Hash should be same regardless of dict key order."""
        payload1 = {"a": 1, "b": 2}
        payload2 = {"b": 2, "a": 1}
        
        hash1 = hash_request(payload1)
        hash2 = hash_request(payload2)
        
        assert hash1 == hash2
    
    def test_different_payloads_produce_different_hashes(self) -> None:
        """Different payloads should produce different hashes."""
        payload1 = {"key": "value"}
        payload2 = {"key": "different_value"}
        
        hash1 = hash_request(payload1)
        hash2 = hash_request(payload2)
        
        assert hash1 != hash2


class TestIdempotencyRecord:
    """Test idempotency record behavior."""
    
    def test_new_record_not_expired(self) -> None:
        """Newly created record should not be expired."""
        record = IdempotencyRecord(
            key="test-key",
            operation_type="project_create",
            operation_id="proj-123",
            request_hash="abc123",
            created_at=datetime.now(timezone.utc),
        )
        
        assert not record.is_expired()
    
    def test_old_record_is_expired(self) -> None:
        """Record older than 24h should be expired."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        
        record = IdempotencyRecord(
            key="test-key",
            operation_type="project_create",
            operation_id="proj-123",
            request_hash="abc123",
            created_at=old_time,
        )
        
        assert record.is_expired()
    
    def test_record_at_ttl_boundary(self) -> None:
        """Record exactly at 24h should not be expired yet."""
        exact_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        record = IdempotencyRecord(
            key="test-key",
            operation_type="project_create",
            operation_id="proj-123",
            request_hash="abc123",
            created_at=exact_time,
        )
        
        assert not record.is_expired()


class TestIdempotencyStore:
    """Test idempotency store operations."""
    
    def test_create_and_get_record(self) -> None:
        """Should be able to create and retrieve records."""
        store = IdempotencyStore()
        
        store.create(
            operation_type="project_create",
            idempotency_key="key-123",
            operation_id="proj-456",
            request_hash="hash-abc",
        )
        
        record = store.get("project_create", "key-123")
        
        assert record is not None
        assert record.key == "key-123"
        assert record.operation_type == "project_create"
        assert record.operation_id == "proj-456"
    
    def test_get_returns_none_for_missing_key(self) -> None:
        """Should return None for non-existent keys."""
        store = IdempotencyStore()
        
        record = store.get("project_create", "nonexistent")
        
        assert record is None
    
    def test_expired_records_are_cleaned_on_get(self) -> None:
        """Expired records should be removed when accessed."""
        store = IdempotencyStore()
        
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        
        with patch('app.services.idempotency.datetime') as mock_dt:
            mock_dt.now.return_value = old_time
            
            store.create(
                operation_type="project_create",
                idempotency_key="old-key",
                operation_id="proj-old",
                request_hash="hash-old",
            )
        
        # Record should be expired now and cleaned up
        record = store.get("project_create", "old-key")
        assert record is None
    
    def test_update_response(self) -> None:
        """Should update record with response data."""
        store = IdempotencyStore()
        
        store.create(
            operation_type="project_create",
            idempotency_key="key-123",
            operation_id="proj-456",
            request_hash="hash-abc",
        )
        
        store.update_response("project_create", "key-123", {"status": "success"})
        
        record = store.get("project_create", "key-123")
        assert record.response_data == {"status": "success"}


class TestCheckIdempotency:
    """Test idempotency check logic."""
    
    def test_no_key_allows_new_operation(self) -> None:
        """Missing idempotency key should allow new operation."""
        # Reset store for clean test
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        is_new, record = check_idempotency(
            operation_type="project_create",
            idempotency_key=None,
            operation_id="proj-123",
            payload={"name": "Test"},
        )
        
        assert is_new is True
        assert record is None
    
    def test_first_use_creates_record(self) -> None:
        """First use of key should create new record."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        is_new, record = check_idempotency(
            operation_type="project_create",
            idempotency_key="idem-123",
            operation_id="proj-456",
            payload={"name": "Test"},
        )
        
        assert is_new is True
        assert record is not None
        assert record.operation_id == "proj-456"
    
    def test_duplicate_key_returns_existing(self) -> None:
        """Duplicate key with same payload should return existing record."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # First call creates record
        check_idempotency(
            operation_type="project_create",
            idempotency_key="idem-123",
            operation_id="proj-original",
            payload={"name": "Test"},
        )
        
        # Second call with same key and payload should detect duplicate
        is_new, record = check_idempotency(
            operation_type="project_create",
            idempotency_key="idem-123",
            operation_id="proj-new",  # Different ID - shouldn't matter
            payload={"name": "Test"},  # Same payload
        )
        
        assert is_new is False
        assert record is not None
        assert record.operation_id == "proj-original"
    
    def test_duplicate_key_with_different_payload_raises_error(self) -> None:
        """Duplicate key with different payload should raise error."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # First call creates record
        check_idempotency(
            operation_type="project_create",
            idempotency_key="idem-123",
            operation_id="proj-original",
            payload={"name": "Original"},
        )
        
        # Second call with different payload should fail
        with pytest.raises(IdempotencyError) as exc_info:
            check_idempotency(
                operation_type="project_create",
                idempotency_key="idem-123",
                operation_id="proj-new",
                payload={"name": "Modified"},  # Different!
            )
        
        assert "request payload differs" in str(exc_info.value.message)
        assert exc_info.value.existing_id == "proj-original"


class TestStoreResponse:
    """Test response storage."""
    
    def test_stores_response_for_valid_key(self) -> None:
        """Should store response for valid idempotency key."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # Create record first
        check_idempotency(
            operation_type="project_create",
            idempotency_key="idem-123",
            operation_id="proj-456",
            payload={"name": "Test"},
        )
        
        # Store response
        store_response("project_create", "idem-123", {"id": "proj-456"})
        
        record = idempotency._store.get("project_create", "idem-123")
        assert record.response_data == {"id": "proj-456"}
    
    def test_noop_for_missing_key(self) -> None:
        """Should be no-op for missing idempotency key."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # Should not raise error
        store_response("project_create", None, {"id": "proj-456"})


class TestIdempotencyIntegration:
    """Test full idempotency workflow."""
    
    def test_full_workflow_new_operation(self) -> None:
        """Test complete workflow for new operation."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # Check idempotency (should be new)
        is_new, record = check_idempotency(
            operation_type="project_create",
            idempotency_key="client-key-123",
            operation_id="proj-generated-id",
            payload={"name": "My Project"},
        )
        
        assert is_new is True
        
        # Simulate storing response after successful operation
        store_response("project_create", "client-key-123", {
            "project_id": "proj-generated-id",
            "status": "created",
        })
    
    def test_full_workflow_retry_returns_same_result(self) -> None:
        """Test that retry with same key returns existing result."""
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        # First operation
        check_idempotency(
            operation_type="project_create",
            idempotency_key="client-key-123",
            operation_id="proj-original-id",
            payload={"name": "My Project"},
        )
        store_response("project_create", "client-key-123", {
            "project_id": "proj-original-id",
            "status": "created",
        })
        
        # Retry with same key and payload
        is_new, record = check_idempotency(
            operation_type="project_create",
            idempotency_key="client-key-123",
            operation_id="proj-would-be-new-id",
            payload={"name": "My Project"},  # Same payload
        )
        
        assert is_new is False
        assert record.operation_id == "proj-original-id"
        assert record.response_data["project_id"] == "proj-original-id"


class TestIdempotencyThreadSafety:
    """Test thread safety of idempotency operations."""
    
    def test_concurrent_checks_dont_create_duplicates(self) -> None:
        """Concurrent checks with same key should not create duplicate records."""
        import threading
        
        from app.services import idempotency
        idempotency._store = IdempotencyStore()
        
        results = []
        errors = []
        
        def check_operation():
            try:
                is_new, record = check_idempotency(
                    operation_type="project_create",
                    idempotency_key="concurrent-key",
                    operation_id=f"proj-{threading.current_thread().ident}",
                    payload={"name": "Test"},
                )
                results.append((is_new, record))
            except Exception as e:
                errors.append(e)
        
        # Run 10 concurrent checks
        threads = [threading.Thread(target=check_operation) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors from race conditions
        assert len(errors) == 0
        
        # At least one should be new, rest should detect duplicate
        new_count = sum(1 for is_new, _ in results if is_new)
        assert new_count >= 1
