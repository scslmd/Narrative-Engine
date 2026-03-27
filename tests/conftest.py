from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

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
        # Only add API key if headers not explicitly set to empty dict
        if 'headers' not in kwargs or kwargs['headers'] is None:
            kwargs['headers'] = {}
        # Don't override if headers is already an empty dict (explicit no-auth test)
        if kwargs['headers'] and 'X-API-Key' not in kwargs['headers']:
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
