from pathlib import Path


def test_auth_service_accepts_injected_instance():
    """Auth service should accept injected instance for test isolation."""
    from app.services.authentication import get_auth_service, APIKeyStore
    import app.services.authentication as auth_mod

    mock_service = APIKeyStore(db_path=Path("/tmp/test-auth-di.db"))
    try:
        get_auth_service(service=mock_service)
        result = get_auth_service()
        assert result is mock_service, "Should return injected service"
    finally:
        auth_mod._key_store = None  # Reset singleton
