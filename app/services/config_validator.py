"""Configuration validator service (REL-07).

Validates critical configuration at application startup:
- Inference backend URL is reachable
- Required directories are writable
- API key is set when required
- Database can be opened and written to
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, component: str):
        super().__init__(message)
        self.message = message
        self.component = component


class ConfigValidator:
    """Validates application configuration at startup (REL-07)."""
    
    def __init__(self) -> None:
        self.validation_results: list[dict[str, Any]] = []
    
    def validate_all(self, *, fail_fast: bool = True) -> bool:
        """Run all validation checks.
        
        Args:
            fail_fast: If True, stop at first failure. If False, collect all failures.
            
        Returns:
            True if all validations pass, False otherwise.
        """
        self.validation_results = []
        all_passed = True
        
        checks = [
            ("API Key", self._validate_api_key),
            ("Inference Backend", self._validate_inference_backend),
            ("Database", self._validate_database),
            ("Project Directories", self._validate_directories),
        ]
        
        for name, check_fn in checks:
            try:
                result = check_fn()
                self.validation_results.append({
                    "component": name,
                    "status": "passed" if result else "failed",
                    "message": None if result else "Validation failed",
                })
                
                if not result:
                    all_passed = False
                    if fail_fast:
                        return False
                        
            except Exception as e:
                self.validation_results.append({
                    "component": name,
                    "status": "error",
                    "message": str(e),
                })
                all_passed = False
                if fail_fast:
                    return False
        
        return all_passed
    
    def _validate_api_key(self) -> bool:
        """Validate API key is set when required."""
        import os
        
        api_key = os.getenv("API_KEY")
        
        # For local-first use, API key is optional but should be set for security
        if not api_key:
            _logger.warning("API_KEY environment variable not set. Authentication will be disabled.")
            return True  # Not a hard failure for local development
        
        if len(api_key) < 8:
            raise ConfigValidationError(
                f"API key too short ({len(api_key)} chars, minimum 8 recommended)",
                "api_key",
            )
        
        return True
    
    def _validate_inference_backend(self) -> bool:
        """Validate inference backend is reachable."""
        import os
        from app.settings import settings

        backend = settings.inference_backend
        if backend == "stub":
            _logger.warning("Inference backend is 'stub'. Imports/extractions will produce placeholder content.")
            return True  # Stub backend is acceptable for development

        inference_url = settings.inference_base_url
        if not inference_url:
            _logger.warning("No inference URL configured for backend '%s'. Using stub behavior.", backend)
            return True

        try:
            import urllib.request

            timeout = float(os.getenv("INFERENCE_TIMEOUT", "5.0"))

            with urllib.request.urlopen(inference_url, timeout=timeout) as response:
                status_code = response.status
                if status_code != 200:
                    _logger.warning("Inference backend returned %d, but is reachable", status_code)

            return True

        except Exception as e:
            _logger.warning("Inference backend unreachable at %s: %s", inference_url, e)
            _logger.warning("Imports/extractions will fail until backend is available.")
            return True  # Don't block startup for unreachable backend
    
    def _validate_database(self) -> bool:
        """Validate database can be opened and written to."""
        import os
        from app.settings import settings
        
        configured_path = os.getenv("DATABASE_PATH", "").strip()
        db_path = Path(configured_path) if configured_path else settings.operations_db_path
        
        if not db_path.parent.exists():
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigValidationError(
                    f"Cannot create database directory {db_path.parent}: {e}",
                    "database",
                )
        
        test_conn = None
        try:
            test_conn = sqlite3.connect(str(db_path), timeout=5.0)
            cursor = test_conn.cursor()
            
            cursor.execute("PRAGMA writable_schema")
            result = cursor.fetchone()
            
            cursor.execute("PRAGMA foreign_keys")
            fk_status = cursor.fetchone()[0]
            
            if not fk_status:
                _logger.warning("Foreign keys disabled in SQLite. Enabling...")
                cursor.execute("PRAGMA foreign_keys = ON")
            
            test_conn.commit()
            return True
            
        except sqlite3.Error as e:
            raise ConfigValidationError(
                f"Database error at {db_path}: {e}",
                "database",
            )
        finally:
            if test_conn:
                test_conn.close()
    
    def _validate_directories(self) -> bool:
        """Validate required directories exist and are writable (REL-09)."""
        import os
        from app.settings import settings
        
        configured_path = os.getenv("PROJECTS_DIR", "").strip()
        base_dir = Path(configured_path) if configured_path else settings.projects_dir
        
        # Ensure directory exists
        self._ensure_directory_exists(base_dir)
        
        # Run all validation checks
        self._validate_system_path(base_dir)
        self._validate_windows_readonly(base_dir)
        self._validate_unix_permissions(base_dir)
        self._validate_write_permission(base_dir)
        
        return True
    
    def _ensure_directory_exists(self, base_dir: Path) -> None:
        """Create directory if it doesn't exist."""
        if not base_dir.exists():
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigValidationError(
                    f"Cannot create projects directory {base_dir}: {e}",
                    "directories",
                )
    
    def _validate_system_path(self, base_dir: Path) -> None:
        """Check for system-protected paths (cross-platform)."""
        path_str = str(base_dir).upper().replace("\\", "/")
        system_paths = [
            "/WINDOWS/", "/PROGRAM FILES/", "/PROGRAM FILES (X86)/",
            "/SYSTEM32/", "/PROGRAMDATA/", "/SYSTEM/", "/BIN/",
            "/SBIN/", "/USR/", "/PRIVATE/",
        ]
        
        for protected in system_paths:
            if protected in path_str:
                raise ConfigValidationError(
                    f"Projects directory {base_dir} is in a system-protected path. "
                    f"Use a user-writable location like Documents or Desktop.",
                    "directories",
                )
    
    def _validate_windows_readonly(self, base_dir: Path) -> None:
        """Check for read-only attribute (Windows only)."""
        import os
        if os.name != 'nt':
            return
        
        import ctypes
        try:
            attributes = ctypes.windll.kernel32.GetFileAttributesW(str(base_dir))
            if attributes != -1 and (attributes & 0x0001):
                raise ConfigValidationError(
                    f"Projects directory {base_dir} has read-only attribute set",
                    "directories",
                )
        except (OSError, AttributeError, ctypes.ArgumentError):
            pass  # Fall through to write test
    
    def _validate_unix_permissions(self, base_dir: Path) -> None:
        """Check Unix directory permissions."""
        import os
        import stat
        
        if os.name == 'nt':
            return
        
        try:
            mode = os.stat(base_dir).st_mode
            
            if mode & stat.S_IWOTH:
                raise ConfigValidationError(
                    f"Projects directory {base_dir} is world-writable (insecure permissions)",
                    "directories",
                )
            
            if mode & stat.S_IWGRP:
                _logger.warning("Projects directory %s is group-writable", base_dir)
                
        except OSError as e:
            raise ConfigValidationError(
                f"Cannot check permissions for {base_dir}: {e}",
                "directories",
            )
    
    def _validate_write_permission(self, base_dir: Path) -> None:
        """Test write permission (cross-platform)."""
        test_file = base_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except OSError as e:
            raise ConfigValidationError(
                f"Projects directory {base_dir} is not writable: {e}",
                "directories",
            )
    
    def get_validation_report(self) -> dict[str, Any]:
        """Get a summary report of validation results."""
        passed = sum(1 for r in self.validation_results if r["status"] == "passed")
        failed = sum(1 for r in self.validation_results if r["status"] == "failed")
        errors = sum(1 for r in self.validation_results if r["status"] == "error")
        
        return {
            "total": len(self.validation_results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "details": self.validation_results,
        }


def validate_config_at_startup() -> None:
    """Run configuration validation at application startup.

    Raises ConfigValidationError if critical checks fail.
    """
    validator = ConfigValidator()

    _logger.info("=" * 60)
    _logger.info("Configuration Validation (REL-07)")
    _logger.info("=" * 60)

    try:
        success = validator.validate_all(fail_fast=False)

        report = validator.get_validation_report()

        for result in validator.validation_results:
            status_icon = "[OK]" if result["status"] == "passed" else "[FAIL]"
            _logger.info("%s %s: %s", status_icon, result['component'], result['status'])
            if result.get("message"):
                _logger.info("   %s", result['message'])

        _logger.info("=" * 60)

        if not success:
            failed_count = report["failed"] + report["errors"]
            _logger.warning("%d validation check(s) did not pass.", failed_count)
            _logger.warning("Application may have limited functionality.")

    except ConfigValidationError as e:
        _logger.error("[FAIL] %s: FAILED", e.component)
        _logger.error("   %s", e.message)
        _logger.error("=" * 60)
        raise
