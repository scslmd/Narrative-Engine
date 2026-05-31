import logging
from io import StringIO
from pathlib import Path
from unittest.mock import patch


def test_cleanup_exceptions_are_logged():
    """Cleanup exceptions in _restore_published_output should be logged at debug level."""
    from app.services.local_executor.artifact_io import _ArtifactIOMixin

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("app.services.local_executor.artifact_io")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    output_path = Path("output.md")
    staged_path = Path("staged.md")
    backup_path = Path("backup.md")

    def fake_exists(self: Path) -> bool:
        return True

    def fake_unlink(self: Path) -> None:
        raise OSError(f"cannot unlink {self}")

    def fake_replace(self: Path, target: Path) -> None:
        raise OSError(f"cannot replace {self} -> {target}")

    try:
        mixin = _ArtifactIOMixin()
        with (
            patch.object(Path, "exists", fake_exists),
            patch.object(Path, "unlink", fake_unlink),
            patch.object(Path, "replace", fake_replace),
        ):
            mixin._restore_published_output(
                output_path=output_path,
                staged_output_path=staged_path,
                backup_output_path=backup_path,
            )
    finally:
        logger.removeHandler(handler)

    logs = log_capture.getvalue()
    assert "Failed to remove output" in logs
    assert "Failed to restore backup" in logs
    assert "Failed to remove staged" in logs
