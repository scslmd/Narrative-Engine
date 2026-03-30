"""Tests for exception hierarchy consistency (CQ-001)."""
from __future__ import annotations

import pytest

from app.services.story_branching import (
    StoryBranchingNotFoundError,
    StoryBranchingValidationError,
    StoryBranchingServiceError,
)
from app.services.foundation import (
    FoundationNotFoundError,
    FoundationValidationError,
    FoundationServiceError,
)
from app.services.idempotency import IdempotencyError
from app.services.backup import BackupError
from app.services.authentication import AuthenticationError
from app.services.authorization import AuthorizationError
from app.services.protocol import IdempotencyConflictError, RetryNotAllowedError


class TestExceptionHierarchy:
    """Tests for service exception hierarchy consistency."""

    def test_story_branching_error_hierarchy(self):
        """StoryBranching errors should form proper hierarchy."""
        # Base error should be ValueError
        assert issubclass(StoryBranchingServiceError, ValueError)
        
        # Sub-classes should inherit from base
        assert issubclass(StoryBranchingNotFoundError, StoryBranchingServiceError)
        assert issubclass(StoryBranchingValidationError, StoryBranchingServiceError)

    def test_foundation_error_hierarchy(self):
        """Foundation errors should form proper hierarchy."""
        assert issubclass(FoundationServiceError, ValueError)
        assert issubclass(FoundationNotFoundError, FoundationServiceError)
        assert issubclass(FoundationValidationError, FoundationServiceError)

    def test_idempotency_error_has_attributes(self):
        """IdempotencyError should have message and existing_id attributes."""
        error = IdempotencyError("Test message", existing_id="123")
        assert error.message == "Test message"
        assert error.existing_id == "123"

    def test_backup_error_is_distinct(self):
        """BackupError should be a distinct exception type."""
        assert issubclass(BackupError, Exception)
        assert not issubclass(BackupError, ValueError)

    def test_authentication_error_is_distinct(self):
        """AuthenticationError should be a distinct exception type."""
        assert issubclass(AuthenticationError, Exception)
        assert not issubclass(AuthenticationError, ValueError)

    def test_authorization_error_is_distinct(self):
        """AuthorizationError should be a distinct exception type."""
        assert issubclass(AuthorizationError, Exception)
        assert not issubclass(AuthorizationError, ValueError)

    def test_protocol_errors_are_distinct(self):
        """Protocol errors should be distinct ValueError sub-classes."""
        assert issubclass(IdempotencyConflictError, ValueError)
        assert issubclass(RetryNotAllowedError, ValueError)
        assert IdempotencyConflictError is not RetryNotAllowedError


class TestExceptionUsage:
    """Tests for proper exception usage in service layer."""

    def test_idempotency_error_with_existing_id(self):
        """IdempotencyError should properly set existing_id."""
        error = IdempotencyError("Duplicate key", existing_id="proj-123")
        assert error.existing_id == "proj-123"
        assert "Duplicate key" in str(error)

    def test_idempotency_error_without_existing_id(self):
        """IdempotencyError should work without existing_id."""
        error = IdempotencyError("Some error")
        assert error.existing_id is None
