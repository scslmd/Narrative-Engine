"""Tests for extraction endpoint error handling."""
import pytest
from fastapi import HTTPException


class TestServiceErrorHandler:
    """Verify the service handler helper works correctly."""

    def test_handler_catches_specific_error(self) -> None:
        from app.api.projects import handle_service_error

        class ServiceError(ValueError):
            pass

        def failing_func():
            raise ServiceError("test error")

        with pytest.raises(HTTPException) as exc_info:
            handle_service_error(failing_func, ServiceError)
        assert exc_info.value.status_code == 400
        assert "test error" in exc_info.value.detail

    def test_handler_catches_generic_exception(self) -> None:
        from app.api.projects import handle_service_error

        class ServiceError(ValueError):
            pass

        def failing_func():
            raise RuntimeError("unexpected failure")

        with pytest.raises(HTTPException) as exc_info:
            handle_service_error(failing_func, ServiceError)
        assert exc_info.value.status_code == 500
        assert "unexpected failure" in exc_info.value.detail

    def test_handler_returns_result_on_success(self) -> None:
        from app.api.projects import handle_service_error

        class ServiceError(ValueError):
            pass

        def success_func():
            return {"status": "ok"}

        result = handle_service_error(success_func, ServiceError)
        assert result == {"status": "ok"}
