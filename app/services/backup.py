"""Backup service for SQLite database (REL-04).

Provides point-in-time recovery with:
- Daily automated backups
- 7-day retention policy
- WAL checkpoint before backup
- Create/restore endpoints
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BACKUP_RETENTION_DAYS = 7
BACKUPS_DIR_NAME = "backups"


class BackupError(Exception):
    """Raised when backup/restore operation fails."""
    
    pass


class BackupService:
    """Backup service for SQLite database with WAL support (REL-04)."""
    
    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.backups_dir = data_root / BACKUPS_DIR_NAME
        self.backups_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_backup_path(self, timestamp: datetime) -> Path:
        """Get backup file path for given timestamp."""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        base_path = self.backups_dir / f"narrative_ops_{timestamp_str}.db"
        
        # Handle collisions by adding counter suffix
        if not base_path.exists():
            return base_path
        
        counter = 1
        while True:
            candidate = self.backups_dir / f"narrative_ops_{timestamp_str}_{counter}.db"
            if not candidate.exists():
                return candidate
            counter += 1
    
    def _get_wal_path(self, db_path: Path) -> Path:
        """Get WAL file path for database."""
        return db_path.with_suffix(db_path.suffix + "-wal")
    
    def _get_shm_path(self, db_path: Path) -> Path:
        """Get SHM file path for database."""
        return db_path.with_suffix(db_path.suffix + "-shm")
    
    def create_backup(
        self,
        db_path: Path | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create backup of SQLite database.
        
        Process:
        1. Checkpoint WAL to ensure all data is in main DB file
        2. Copy DB file (and WAL/SHM if they exist)
        3. Return backup metadata
        
        Args:
            db_path: Path to database (defaults to narrative_ops.db)
            description: Optional description for backup
            
        Returns:
            Backup metadata including path, size, timestamp
        """
        if db_path is None:
            db_path = self.data_root / "state" / "narrative_ops.db"
        
        if not db_path.exists():
            raise BackupError(f"Database not found: {db_path}")
        
        # Checkpoint WAL to ensure all data is flushed to main DB
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
        except Exception as e:
            raise BackupError(f"Failed to checkpoint WAL: {e}") from e
        
        # Create backup with timestamp
        timestamp = datetime.now(timezone.utc)
        backup_path = self._get_backup_path(timestamp)
        
        try:
            # Copy main database file
            shutil.copy2(str(db_path), str(backup_path))
            
            # Also copy WAL and SHM if they exist (shouldn't after checkpoint, but be safe)
            wal_path = self._get_wal_path(db_path)
            shm_path = self._get_shm_path(db_path)
            
            if wal_path.exists():
                shutil.copy2(str(wal_path), str(backup_path.with_suffix(backup_path.suffix + "-wal")))
            
            if shm_path.exists():
                shutil.copy2(str(shm_path), str(backup_path.with_suffix(backup_path.suffix + "-shm")))
            
            # Clean up old backups (enforce retention policy)
            self._cleanup_old_backups()
            
            # Return metadata
            return {
                "backup_id": backup_path.stem,
                "path": str(backup_path),
                "size_bytes": backup_path.stat().st_size,
                "created_at": timestamp.isoformat(),
                "description": description or f"Backup created at {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            }
            
        except Exception as e:
            # Clean up partial backup on failure
            if backup_path.exists():
                backup_path.unlink()
            
            raise BackupError(f"Failed to create backup: {e}") from e
    
    def restore_backup(
        self,
        backup_id: str,
        db_path: Path | None = None,
    ) -> dict[str, Any]:
        """Restore database from backup.
        
        Args:
            backup_id: Backup ID (filename without extension) or full path
            db_path: Path to restore to (defaults to narrative_ops.db)
            
        Returns:
            Restore metadata including source and destination
            
        Raises:
            BackupError: If backup not found or restore fails
        """
        if db_path is None:
            db_path = self.data_root / "state" / "narrative_ops.db"
        
        # Find backup file
        backup_file = self._find_backup(backup_id)
        
        if not backup_file.exists():
            raise BackupError(f"Backup not found: {backup_id}")
        
        # Check disk space before restore
        try:
            import shutil
            backup_size = backup_file.stat().st_size
            dest_dir = db_path.parent
            if os.name == 'nt':  # Windows
                drive = str(dest_dir).split(':')[0] + ':'
                total, used, free = shutil.disk_usage(drive)
                free_bytes = free
            else:  # Unix/Linux/macOS
                stat = os.statvfs(dest_dir)
                free_bytes = stat.f_bavail * stat.f_frsize
            
            if free_bytes < backup_size:
                raise BackupError("Insufficient disk space to restore backup")
        except OSError:
            pass
        
        try:
            # Create backup of current database before restore
            pre_restore_backup = None
            if db_path.exists():
                pre_restore_backup = self.create_backup(
                    db_path=db_path,
                    description=f"Pre-restore backup before restoring {backup_id}",
                )
            
            # Ensure destination directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore from backup - copy all related files
            shutil.copy2(str(backup_file), str(db_path))
            
            # Copy WAL/SHM if they exist in backup
            wal_src = backup_file.with_suffix(backup_file.suffix + "-wal")
            shm_src = backup_file.with_suffix(backup_file.suffix + "-shm")
            
            wal_dst = self._get_wal_path(db_path)
            shm_dst = self._get_shm_path(db_path)
            
            if wal_src.exists():
                shutil.copy2(str(wal_src), str(wal_dst))
            else:
                # Remove any existing WAL/SHM to ensure clean state
                if wal_dst.exists():
                    wal_dst.unlink()
            
            if shm_src.exists():
                shutil.copy2(str(shm_src), str(shm_dst))
            else:
                if shm_dst.exists():
                    shm_dst.unlink()
            
            # Force checkpoint on restored DB to ensure consistency
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            
            return {
                "restored_from": str(backup_file),
                "restored_to": str(db_path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pre_restore_backup": pre_restore_backup,
            }
            
        except Exception as e:
            raise BackupError(f"Failed to restore backup: {e}") from e
    
    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups.
        
        Returns:
            List of backup metadata sorted by creation time (newest first)
        """
        backups = []
        
        if not self.backups_dir.exists():
            return backups
        
        for file_path in self.backups_dir.glob("narrative_ops_*.db"):
            try:
                stat = file_path.stat()
                
                # Extract timestamp from filename
                stem = file_path.stem  # e.g., "narrative_ops_20240315_143022"
                parts = stem.split("_")
                if len(parts) >= 4:
                    # Format: narrative_ops_YYYYMMDD_HHMMSS
                    timestamp_str = f"{parts[2]}{parts[3]}"
                    created_at = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                else:
                    continue  # Skip malformed filenames
                
                backups.append({
                    "backup_id": stem,
                    "path": str(file_path),
                    "size_bytes": stat.st_size,
                    "created_at": created_at.isoformat(),
                })
            except Exception:
                # Skip invalid backup files
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a specific backup.
        
        Args:
            backup_id: Backup ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        backup_file = self._find_backup(backup_id)
        
        if not backup_file.exists():
            return False
        
        try:
            # Delete main backup file
            backup_file.unlink()
            
            # Also delete associated WAL/SHM files
            wal_file = backup_file.with_suffix(backup_file.suffix + "-wal")
            shm_file = backup_file.with_suffix(backup_file.suffix + "-shm")
            
            if wal_file.exists():
                wal_file.unlink()
            
            if shm_file.exists():
                shm_file.unlink()
            
            return True
            
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {e}") from e
    
    def _find_backup(self, backup_id: str) -> Path:
        """Find backup file by ID or path."""
        # If it's an absolute path, use it directly
        if Path(backup_id).is_absolute():
            return Path(backup_id)
        
        # Try as full filename in backups directory (with .db extension)
        candidate = self.backups_dir / f"{backup_id}.db"
        if candidate.exists():
            return candidate
        
        # If backup_id doesn't start with "narrative_ops_", add prefix
        if not backup_id.startswith("narrative_ops_"):
            candidate2 = self.backups_dir / f"narrative_ops_{backup_id}.db"
            if candidate2.exists():
                return candidate2
        
        # Try matching prefix (in case only partial ID provided)
        matches = list(self.backups_dir.glob(f"{backup_id}*"))
        if len(matches) == 1:
            return matches[0]
        
        # Return the candidate even if it doesn't exist (caller will check)
        return candidate
    
    def _cleanup_old_backups(self) -> int:
        """Remove backups older than retention period.
        
        Returns:
            Number of backups deleted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=BACKUP_RETENTION_DAYS)
        deleted_count = 0
        
        for backup in self.list_backups():
            created_at = datetime.fromisoformat(backup["created_at"])
            
            if created_at < cutoff:
                try:
                    self.delete_backup(backup["backup_id"])
                    deleted_count += 1
                except Exception:
                    # Log but don't fail the entire cleanup
                    continue
        
        return deleted_count
    
    def get_latest_backup(self) -> dict[str, Any] | None:
        """Get metadata for most recent backup.
        
        Returns:
            Backup metadata or None if no backups exist
        """
        backups = self.list_backups()
        return backups[0] if backups else None


# Global instance (will be initialized in main.py)
_backup_service: BackupService | None = None


def get_backup_service(data_root: Path | None = None) -> BackupService:
    """Get or create backup service instance."""
    global _backup_service
    
    if _backup_service is None:
        if data_root is None:
            data_root = Path(__file__).resolve().parents[2] / "data"
        
        _backup_service = BackupService(data_root)
    
    return _backup_service
