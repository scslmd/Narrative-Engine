from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import _pytest.pathlib
import _pytest.tmpdir
import pytest


# Set API_KEY for all tests (SEC-01)
os.environ["API_KEY"] = "test-secret-key-123"


@pytest.fixture(autouse=True)
def set_api_key_header():
    """Automatically add X-API-Key header to all test requests (unless explicitly empty)."""
    from starlette.testclient import TestClient as OriginalTestClient
    
    # Patch TestClient to automatically include API key header
    original_request = OriginalTestClient.request
    
    def patched_request(self, *args, **kwargs):
        # Check if headers was originally absent or None
        headers_was_none = 'headers' not in kwargs or kwargs.get('headers') is None
        # Check if headers was explicitly set to empty dict (no-auth test)
        headers_explicitly_empty = 'headers' in kwargs and kwargs.get('headers') == {}
        
        if headers_was_none:
            kwargs['headers'] = {}
        
        # Don't inject if explicitly no-auth (empty dict passed by caller)
        if headers_explicitly_empty:
            return original_request(self, *args, **kwargs)
        
        # Inject API key if not already present
        if 'X-API-Key' not in kwargs.get('headers', {}):
            kwargs['headers']['X-API-Key'] = os.environ.get('API_KEY', 'test-secret-key-123')
        
        return original_request(self, *args, **kwargs)
    
    OriginalTestClient.request = patched_request
    try:
        yield
    finally:
        OriginalTestClient.request = original_request


_original_cleanup_dead_symlinks = _pytest.pathlib.cleanup_dead_symlinks


def _safe_cleanup_dead_symlinks(root) -> None:
    try:
        _original_cleanup_dead_symlinks(root)
    except PermissionError:
        # Some Windows environments deny directory iteration on pytest's own
        # base temp root during teardown. Ignore that cleanup-only failure so
        # the suite still reports the real test outcome.
        return


_pytest.pathlib.cleanup_dead_symlinks = _safe_cleanup_dead_symlinks
_pytest.tmpdir.cleanup_dead_symlinks = _safe_cleanup_dead_symlinks


def pytest_sessionfinish(session):
    """Clean up per-test pytest runtime directories after the session completes."""
    runtime_dir = Path(__file__).resolve().parents[1] / ".tmp_test_projects" / "pytest_runtime"
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir, ignore_errors=True)


@pytest.fixture
def tmp_path() -> Path:
    base_dir = Path(__file__).resolve().parents[1] / ".tmp_test_projects"
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


# ============================================================================
# Test Utilities
# ============================================================================


def read_last_audit_record() -> dict[str, Any] | None:
    """Read the last audit record from the log file."""
    import json
    from app.settings import settings
    
    log_path = Path(settings.structured_log_filename)
    if not log_path.exists():
        return None
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return None
    
    return json.loads(lines[-1])


def count_audit_records() -> int:
    """Count the number of audit records in the log file."""
    from app.settings import settings
    
    log_path = Path(settings.structured_log_filename)
    if not log_path.exists():
        return 0
    
    with open(log_path, 'r') as f:
        return sum(1 for _ in f)


def get_test_job_id() -> UUID | None:
    """Get an existing job ID from the database for testing."""
    from uuid import UUID
    from app.persistence.sqlite import connect
    from app.settings import settings
    
    with connect(settings.operations_db_path) as conn:
        row = conn.execute('SELECT job_id FROM jobs LIMIT 1').fetchone()
        if row:
            return UUID(row['job_id'])
    return None


def get_test_job_with_retries() -> UUID | None:
    """Get a job ID with multiple attempts for testing."""
    from uuid import UUID
    from app.persistence.sqlite import connect
    from app.settings import settings
    
    with connect(settings.operations_db_path) as conn:
        row = conn.execute(
            'SELECT job_id FROM jobs WHERE attempt_number > 1 LIMIT 1'
        ).fetchone()
        if row:
            return UUID(row['job_id'])
    return None
