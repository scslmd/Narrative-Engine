"""Tests for backup service (REL-04)."""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.backup import BackupError, BackupService


class TestBackupService:
    """Test backup service functionality."""
    
    @pytest.fixture
    def temp_data_root(self, tmp_path: Path) -> Path:
        """Create temporary data root with sample database."""
        # Create directory structure
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        # Create sample database
        db_path = state_dir / "narrative_ops.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test_data')")
        conn.commit()
        
        # Enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL")
        conn.close()
        
        return tmp_path
    
    @pytest.fixture
    def backup_service(self, temp_data_root: Path) -> BackupService:
        """Create backup service with test data root."""
        return BackupService(temp_data_root)
    
    def test_create_backup_succeeds(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should create backup successfully."""
        result = backup_service.create_backup()
        
        assert "backup_id" in result
        assert "path" in result
        assert "size_bytes" in result
        assert "created_at" in result
        
        # Verify backup file exists
        backup_path = Path(result["path"])
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0
    
    def test_create_backup_with_description(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should store description in metadata."""
        result = backup_service.create_backup(description="Manual backup for testing")
        
        assert result["description"] == "Manual backup for testing"
    
    def test_create_backup_nonexistent_database_raises_error(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should raise error if database doesn't exist."""
        nonexistent_db = temp_data_root / "nonexistent.db"
        
        with pytest.raises(BackupError) as exc_info:
            backup_service.create_backup(db_path=nonexistent_db)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_list_backups_returns_empty_when_no_backups(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should return empty list when no backups exist."""
        backups = backup_service.list_backups()
        
        assert backups == []
    
    def test_list_backups_returns_created_backups(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should list created backups sorted by date."""
        # Create two backups with delay (need >1 second for different timestamps)
        backup1 = backup_service.create_backup(description="First")
        
        import time
        time.sleep(1.1)  # Ensure different timestamp
        
        backup2 = backup_service.create_backup(description="Second")
        
        backups = backup_service.list_backups()
        
        assert len(backups) == 2
        # Should be sorted newest first
        assert backups[0]["backup_id"] == backup2["backup_id"]
        assert backups[1]["backup_id"] == backup1["backup_id"]
    
    def test_get_latest_backup_returns_most_recent(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should return most recent backup."""
        backup1 = backup_service.create_backup()
        
        import time
        time.sleep(1.1)  # Ensure different timestamp
        
        backup2 = backup_service.create_backup()
        
        latest = backup_service.get_latest_backup()
        
        assert latest is not None
        assert latest["backup_id"] == backup2["backup_id"]
    
    def test_delete_backup_removes_file(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should delete backup file."""
        result = backup_service.create_backup()
        backup_id = result["backup_id"]
        
        deleted = backup_service.delete_backup(backup_id)
        
        assert deleted is True
        
        # Verify file is gone
        backups = backup_service.list_backups()
        assert len(backups) == 0
    
    def test_delete_nonexistent_backup_returns_false(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should return False for non-existent backup."""
        deleted = backup_service.delete_backup("nonexistent-backup")
        
        assert deleted is False
    
    def test_restore_backup_creates_pre_restore_backup(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should create pre-restore backup before restoring."""
        # Create initial backup
        original_backup = backup_service.create_backup(description="Original")
        
        # Modify database
        db_path = temp_data_root / "state" / "narrative_ops.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("INSERT INTO test VALUES (2, 'modified')")
        conn.commit()
        conn.close()
        
        # Restore from backup
        result = backup_service.restore_backup(original_backup["backup_id"])
        
        assert "pre_restore_backup" in result
        assert result["pre_restore_backup"] is not None
        
        # Verify data was restored
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1  # Should be back to original state
    
    def test_restore_nonexistent_backup_raises_error(
        self,
        temp_data_root: Path,
        backup_service: BackupService,
    ) -> None:
        """Should raise error for non-existent backup."""
        with pytest.raises(BackupError) as exc_info:
            backup_service.restore_backup("nonexistent-backup")
        
        assert "not found" in str(exc_info.value).lower()

    def test_restore_backup_raises_error_when_disk_space_is_insufficient(
        self,
        backup_service: BackupService,
    ) -> None:
        """Should refuse restore when free space is lower than the backup size."""
        original_backup = backup_service.create_backup(description="Original")

        with patch("app.services.backup.shutil.disk_usage") as mock_disk_usage:
            mock_disk_usage.return_value = (10_000, 9_990, 1)

            with pytest.raises(BackupError) as exc_info:
                backup_service.restore_backup(original_backup["backup_id"])

        assert str(exc_info.value) == "Insufficient disk space to restore backup"

    def test_restore_backup_raises_error_when_disk_space_check_fails(
        self,
        backup_service: BackupService,
    ) -> None:
        """Should fail closed when free-space verification cannot be completed."""
        original_backup = backup_service.create_backup(description="Original")

        with patch("app.services.backup.shutil.disk_usage", side_effect=OSError("disk unavailable")):
            with pytest.raises(BackupError) as exc_info:
                backup_service.restore_backup(original_backup["backup_id"])

        assert str(exc_info.value) == "Failed to verify disk space before restore"


class TestBackupRetentionPolicy:
    """Test backup retention policy enforcement."""
    
    def test_old_backups_are_cleaned_after_create(
        self,
        tmp_path: Path,
    ) -> None:
        """Should automatically clean up backups older than 7 days."""
        service = BackupService(tmp_path)
        
        # Create directory structure and database
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        db_path = state_dir / "narrative_ops.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()
        
        # Create old backup manually (8 days ago)
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=8)
        old_backup_path = service._get_backup_path(old_timestamp)
        shutil_copy_file(db_path, old_backup_path)
        
        # Verify old backup exists
        assert old_backup_path.exists()
        
        # Create new backup (should trigger cleanup)
        service.create_backup()
        
        # Old backup should be deleted
        assert not old_backup_path.exists()


def shutil_copy_file(src: Path, dst: Path) -> None:
    """Helper to copy file using shutil."""
    import shutil
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
