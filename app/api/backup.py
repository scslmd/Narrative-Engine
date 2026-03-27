"""Backup API endpoints (REL-04)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..services.backup import BackupError, get_backup_service


router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/create")
async def create_backup(description: str | None = None) -> dict:
    """Create a new database backup.
    
    Performs WAL checkpoint before backup to ensure data consistency.
    Automatically enforces 7-day retention policy.
    
    Args:
        description: Optional description for this backup
        
    Returns:
        Backup metadata including path, size, and timestamp
    """
    try:
        service = get_backup_service()
        result = service.create_backup(description=description)
        return result
    except BackupError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/restore/{backup_id}")
async def restore_backup(backup_id: str) -> dict:
    """Restore database from backup.
    
    Creates a pre-restore backup before restoring to enable rollback.
    
    Args:
        backup_id: Backup ID or filename to restore from
        
    Returns:
        Restore metadata including source, destination, and timestamp
    """
    try:
        service = get_backup_service()
        result = service.restore_backup(backup_id)
        return result
    except BackupError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e)) from e


@router.get("/list")
async def list_backups() -> dict:
    """List all available backups.
    
    Returns:
        List of backup metadata sorted by creation time (newest first)
    """
    try:
        service = get_backup_service()
        backups = service.list_backups()
        return {"backups": backups, "count": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/latest")
async def get_latest_backup() -> dict | None:
    """Get metadata for most recent backup.
    
    Returns:
        Backup metadata or null if no backups exist
    """
    try:
        service = get_backup_service()
        latest = service.get_latest_backup()
        return latest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{backup_id}")
async def delete_backup(backup_id: str) -> dict:
    """Delete a specific backup.
    
    Args:
        backup_id: Backup ID to delete
        
    Returns:
        Confirmation of deletion
    """
    try:
        service = get_backup_service()
        deleted = service.delete_backup(backup_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
        
        return {"deleted": backup_id, "status": "success"}
    except BackupError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e
