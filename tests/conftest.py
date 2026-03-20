from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import _pytest.pathlib
import _pytest.tmpdir
import pytest


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
