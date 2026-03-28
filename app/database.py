"""Database connection utilities.

Provides centralized access to database connections for health checks
and other cross-cutting concerns.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .persistence.sqlite import connect as _connect
from .settings import settings


def get_db_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection.
    
    Args:
        db_path: Optional path to database. Defaults to operations database.
        
    Returns:
        A configured sqlite3.Connection ready for use.
        
    Example:
        ```python
        from app.database import get_db_connection
        
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        ```
    """
    target_path = db_path or settings.operations_db_path
    return _connect(target_path)


def check_database_health(db_path: Path | None = None) -> tuple[bool, str | None]:
    """Check if database is accessible.
    
    Args:
        db_path: Optional path to database. Defaults to operations database.
        
    Returns:
        Tuple of (is_healthy, error_message).
        is_healthy is True if database can be queried, False otherwise.
        error_message contains the error if unhealthy, None if healthy.
    """
    try:
        conn = get_db_connection(db_path)
        conn.execute("SELECT 1")
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)
