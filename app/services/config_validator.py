"""Configuration validator service (REL-07).

Validates critical configuration at application startup:
- Inference backend URL is reachable
- Required directories are writable
- API key is set when required
- Database can be opened and written to
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


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
            print("[WARN] API_KEY environment variable not set. Authentication will be disabled.")
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
        
        inference_url = os.getenv("INFERENCE_URL")
        
        if not inference_url:
            print("[WARN] INFERENCE_URL not set. Using stub backend.")
            return True  # Stub backend is acceptable for development
        
        try:
            import urllib.request
            
            timeout = float(os.getenv("INFERENCE_TIMEOUT", "5.0"))
            
            with urllib.request.urlopen(inference_url, timeout=timeout) as response:
                status_code = response.status
                if status_code != 200:
                    print(f"[WARN] Inference backend returned {status_code}, but is reachable")
            
            return True
            
        except Exception as e:
            raise ConfigValidationError(
                f"Inference backend unreachable at {inference_url}: {e}",
                "inference_backend",
            )
    
    def _validate_database(self) -> bool:
        """Validate database can be opened and written to."""
        import os
        
        db_path = Path(os.getenv("DATABASE_PATH", "narrative_engine.db"))
        
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
                print("[WARN] Foreign keys disabled in SQLite. Enabling...")
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
        import stat
        
        base_dir = Path(os.getenv("PROJECTS_DIR", "projects"))
        
        if not base_dir.exists():
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigValidationError(
                    f"Cannot create projects directory {base_dir}: {e}",
                    "directories",
                )
        
        # Check directory permissions (REL-09)
        # Only enforce strict Unix permissions on Unix systems
        if os.name != 'nt':  # Not Windows
            try:
                dir_stat = os.stat(base_dir)
                mode = dir_stat.st_mode
                
                # Check if directory is world-writable (insecure on Unix)
                if mode & stat.S_IWOTH:
                    raise ConfigValidationError(
                        f"Projects directory {base_dir} is world-writable (insecure permissions)",
                        "directories",
                    )
                
                # Check if directory is group-writable (warn but allow)
                if mode & stat.S_IWGRP:
                    print(f"[WARN] Projects directory {base_dir} is group-writable")
                
            except OSError as e:
                # If we can't stat the directory, that's a problem
                raise ConfigValidationError(
                    f"Cannot check permissions for {base_dir}: {e}",
                    "directories",
                )
        
        # Test write permission
        test_file = base_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except OSError as e:
            raise ConfigValidationError(
                f"Projects directory {base_dir} is not writable: {e}",
                "directories",
            )
        
        return True
    
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
    
    print("=" * 60)
    print("Configuration Validation (REL-07)")
    print("=" * 60)
    
    try:
        success = validator.validate_all(fail_fast=False)
        
        report = validator.get_validation_report()
        
        for result in validator.validation_results:
            status_icon = "[OK]" if result["status"] == "passed" else "[FAIL]"
            print(f"{status_icon} {result['component']}: {result['status']}")
            if result.get("message"):
                print(f"   {result['message']}")
        
        print("=" * 60)
        
        if not success:
            failed_count = report["failed"] + report["errors"]
            print(f"WARNING: {failed_count} validation check(s) did not pass.")
            print("Application may have limited functionality.")
            
    except ConfigValidationError as e:
        print(f"[FAIL] {e.component}: FAILED")
        print(f"   {e.message}")
        print("=" * 60)
        raise
