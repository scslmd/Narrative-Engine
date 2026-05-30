"""Tests for thread-local SQLite connection caching."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from app.persistence.sqlite import (
    _connection_cache,
    connect,
    ensure_operations_db,
)

pytestmark = pytest.mark.integration


def test_same_thread_returns_cached_connection(tmp_path: Path) -> None:
    """Multiple connect() calls from the same thread should return the same connection."""
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)

    conn1 = connect(db_path)
    conn2 = connect(db_path)

    assert conn1 is conn2, "Same thread should get cached connection"

    conn1.close()
    conn2.close()


def test_different_threads_get_separate_connections(tmp_path: Path) -> None:
    """Different threads should get separate connections."""
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)

    results: list[bool] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        conn = connect(db_path)
        barrier.wait(timeout=5)
        # Verify connection works in this thread
        conn.execute("SELECT 1")
        results.append(True)
        conn.close()

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert len(results) == 2, "Both threads should have completed"


def test_connection_cache_clear_removes_entry(tmp_path: Path) -> None:
    """Clearing the cache should cause a new connection to be created."""
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)

    conn1 = connect(db_path)
    _connection_cache.clear()
    conn2 = connect(db_path)

    assert conn1 is not conn2, "Cache clear should produce a new connection"
    # conn1 was closed by clear(), so only verify conn2 works
    conn2.execute("SELECT 1")

    conn2.close()


def test_connection_cache_handles_closed_connection(tmp_path: Path) -> None:
    """If a cached connection is closed, subsequent calls should create a new one."""
    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)

    conn1 = connect(db_path)
    conn1.close()

    conn2 = connect(db_path)

    assert conn2 is not conn1, "Closed connection should be replaced"
    conn2.execute("SELECT 1")

    conn2.close()


def test_different_db_paths_get_separate_connections(tmp_path: Path) -> None:
    """Different database paths should get separate cached connections."""
    db_path1 = tmp_path / "test1.db"
    db_path2 = tmp_path / "test2.db"
    ensure_operations_db(db_path1)
    ensure_operations_db(db_path2)

    conn1 = connect(db_path1)
    conn2 = connect(db_path2)

    assert conn1 is not conn2, "Different paths should get different connections"

    conn1.close()
    conn2.close()
