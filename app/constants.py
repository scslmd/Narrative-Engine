"""Shared operational constants for the Narrative Engine.

This module centralizes magic numbers, timeouts, size limits, and other
operational constants used throughout the application.
"""
from __future__ import annotations

from typing import Final

# Request/Response Size Limits
MAX_BODY_SIZE: Final[int] = 10 * 1024 * 1024  # 10 MB
MAX_PAYLOAD_SIZE: Final[int] = 5 * 1024 * 1024  # 5 MB

# Idempotency Configuration
IDEMPOTENCY_TTL_HOURS: Final[int] = 24

# UUID Validation
UUID_LENGTH: Final[int] = 36

# Circuit Breaker Defaults
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS: Final[int] = 60
CIRCUIT_BREAKER_FAILURE_THRESHOLD: Final[int] = 5

# Backup Configuration
BACKUP_RETENTION_DAYS: Final[int] = 7

# Rate Limiting
RATE_LIMIT_REQUESTS: Final[int] = 100
RATE_LIMIT_WINDOW_SECONDS: Final[int] = 60

# Disk Space Thresholds
DISK_QUOTA_BYTES: Final[int] = 1_073_741_824  # 1 GB
