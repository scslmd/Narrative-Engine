from pathlib import Path


def test_backup_service_accepts_injected_instance():
    """Backup service should accept injected instance for test isolation."""
    from app.services.backup import get_backup_service, BackupService, _reset_backup_service

    mock_service = BackupService(data_root=Path("/tmp/test-backup-di"))
    try:
        get_backup_service(service=mock_service)
        result = get_backup_service()
        assert result is mock_service, "Should return injected service"
    finally:
        _reset_backup_service()


def test_backup_service_data_root_still_works():
    """Existing callers using data_root=... should still work."""
    from app.services.backup import get_backup_service
    import app.services.backup as backup_mod
    backup_mod._backup_service = None  # Clear singleton

    # This should not raise
    service = get_backup_service(data_root=Path("/tmp/test-backup-dataroot"))
    assert service is not None
