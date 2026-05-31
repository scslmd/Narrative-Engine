import inspect
from pathlib import Path

from app.api import health


def test_backup_handlers_are_sync_functions():
    """Backup handlers should be sync (no await calls, no need for async)."""
    source = Path("app/api/backup.py").read_text(encoding="utf-8")
    # After conversion, no handler should be 'async def'
    for name in ("create_backup", "restore_backup", "list_backups", "get_latest_backup", "delete_backup"):
        # Find the def line for this handler
        for line in source.split("\n"):
            if f"def {name}(" in line:
                assert "async def" not in line, f"{name} should be sync"
                break


def test_health_handlers_are_sync_functions():
    handlers = [
        health.health_check,
        health.readiness_check,
        health.llm_health_check,
        health.get_metrics,
    ]

    assert all(not inspect.iscoroutinefunction(handler) for handler in handlers)
