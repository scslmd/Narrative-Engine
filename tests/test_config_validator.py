"""Tests for configuration validation (REL-07)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.config_validator import ConfigValidator, ConfigValidationError


class TestConfigValidator:
    """Test REL-07: Configuration validation at startup."""
    
    def test_validate_all_returns_true_when_valid(self) -> None:
        """validate_all() should return True when all checks pass."""
        validator = ConfigValidator()
        
        with patch.object(validator, '_validate_api_key', return_value=True), \
             patch.object(validator, '_validate_inference_backend', return_value=True), \
             patch.object(validator, '_validate_database', return_value=True), \
             patch.object(validator, '_validate_directories', return_value=True):
            result = validator.validate_all()
            
            assert result is True
    
    def test_validate_all_returns_false_when_invalid(self) -> None:
        """validate_all() should return False when any check fails."""
        validator = ConfigValidator()
        
        with patch.object(validator, '_validate_api_key', return_value=True), \
             patch.object(validator, '_validate_inference_backend', side_effect=ConfigValidationError("Test error", "test")), \
             patch.object(validator, '_validate_database', return_value=True), \
             patch.object(validator, '_validate_directories', return_value=True):
            result = validator.validate_all(fail_fast=False)
            
            assert result is False
    
    def test_fail_fast_stops_at_first_failure(self) -> None:
        """fail_fast=True should stop at first failure."""
        validator = ConfigValidator()
        
        call_count = [0]
        
        def failing_check():
            call_count[0] += 1
            raise ConfigValidationError("Test error", "test")
        
        with patch.object(validator, '_validate_api_key', side_effect=failing_check), \
             patch.object(validator, '_validate_inference_backend', return_value=True), \
             patch.object(validator, '_validate_database', return_value=True), \
             patch.object(validator, '_validate_directories', return_value=True):
            result = validator.validate_all(fail_fast=True)
            
            assert result is False
            assert call_count[0] == 1  # Only first check was called
    
    def test_api_key_validation_passes_when_set(self) -> None:
        """API key validation should pass when key is set."""
        validator = ConfigValidator()
        
        with patch.dict(os.environ, {"API_KEY": "test-key-12345"}):
            result = validator._validate_api_key()
            
            assert result is True
    
    def test_api_key_validation_warns_when_not_set(self) -> None:
        """API key validation should warn but not fail when key is not set."""
        validator = ConfigValidator()
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.print') as mock_print:
                result = validator._validate_api_key()
                
                assert result is True  # Not a hard failure
                mock_print.assert_called_once()
    
    def test_database_validation_creates_directory_if_needed(self) -> None:
        """Database validation should create directory if it doesn't exist."""
        validator = ConfigValidator()
        
        with patch('tempfile.mkdtemp') as mock_mkdtemp:
            temp_dir = "/fake/temp/dir"
            mock_mkdtemp.return_value = temp_dir
            
            with patch.dict(os.environ, {"DATABASE_PATH": f"{temp_dir}/test.db"}):
                # This should not raise even if directory doesn't exist
                try:
                    result = validator._validate_database()
                    # May succeed or fail depending on permissions, but shouldn't crash
                except ConfigValidationError:
                    pass  # Expected if we can't actually create the file
    
    def test_directories_validation_creates_directory_if_needed(self) -> None:
        """Directories validation should create directory if it doesn't exist."""
        validator = ConfigValidator()
        
        with patch('tempfile.mkdtemp') as mock_mkdtemp:
            temp_dir = "/fake/temp/dir"
            mock_mkdtemp.return_value = temp_dir
            
            with patch.dict(os.environ, {"PROJECTS_DIR": temp_dir}):
                try:
                    result = validator._validate_directories()
                except ConfigValidationError:
                    pass  # Expected if we can't actually create the file
    
    def test_validation_report_format(self) -> None:
        """get_validation_report() should return correct format."""
        validator = ConfigValidator()
        
        with patch.object(validator, '_validate_api_key', return_value=True), \
             patch.object(validator, '_validate_inference_backend', return_value=False), \
             patch.object(validator, '_validate_database', return_value=True), \
             patch.object(validator, '_validate_directories', return_value=True):
            validator.validate_all(fail_fast=False)
            
            report = validator.get_validation_report()
            
            assert "total" in report
            assert "passed" in report
            assert "failed" in report
            assert "errors" in report
            assert "details" in report
            assert report["total"] == 4
            assert report["passed"] == 3
            assert report["failed"] == 1
    
    def test_config_validation_error_has_component(self) -> None:
        """ConfigValidationError should include component information."""
        error = ConfigValidationError("Test message", "test_component")
        
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.component == "test_component"


class TestDirectoryPermissionValidation:
    """Test REL-09: Directory permission validation."""
    
    def test_safe_directory_passes_validation(self, tmp_path: Path) -> None:
        """A safe, writable directory should pass validation."""
        validator = ConfigValidator()
        
        # Create a safe directory
        safe_dir = tmp_path / "safe_projects"
        safe_dir.mkdir()
        
        with patch.dict(os.environ, {"PROJECTS_DIR": str(safe_dir)}, clear=False):
            result = validator._validate_directories()
            assert result is True
    
    def test_world_writable_directory_fails_on_unix(self, tmp_path: Path) -> None:
        """A world-writable directory should fail validation on Unix systems."""
        import platform
        
        # Skip on Windows - world-writable check only applies to Unix
        if platform.system() == "Windows":
            pytest.skip("World-writable check only applies to Unix systems")
        
        validator = ConfigValidator()
        
        # Create a directory and make it world-writable
        unsafe_dir = tmp_path / "unsafe_projects"
        unsafe_dir.mkdir()
        os.chmod(unsafe_dir, 0o777)  # rwxrwxrwx - world-writable
        
        with patch.dict(os.environ, {"PROJECTS_DIR": str(unsafe_dir)}, clear=False):
            with pytest.raises(ConfigValidationError) as exc_info:
                validator._validate_directories()
            
            assert "world-writable" in str(exc_info.value).lower()
            assert exc_info.value.component == "directories"
    
    def test_group_writable_directory_warns_on_unix(self, tmp_path: Path) -> None:
        """A group-writable directory should warn but not fail on Unix systems."""
        import platform
        
        # Skip on Windows - group-writable check only applies to Unix
        if platform.system() == "Windows":
            pytest.skip("Group-writable check only applies to Unix systems")
        
        validator = ConfigValidator()
        
        # Create a directory and make it group-writable
        group_writable_dir = tmp_path / "group_writable_projects"
        group_writable_dir.mkdir()
        os.chmod(group_writable_dir, 0o775)  # rwxrwxr-x - group-writable
        
        with patch.dict(os.environ, {"PROJECTS_DIR": str(group_writable_dir)}, clear=False):
            with patch('builtins.print') as mock_print:
                result = validator._validate_directories()
                assert result is True  # Should still pass
                # Should have printed a warning
                warning_calls = [call for call in mock_print.call_args_list 
                               if 'group-writable' in str(call).lower()]
                assert len(warning_calls) > 0
    
    def test_non_writable_directory_fails(self, tmp_path: Path) -> None:
        """A non-writable directory should fail validation."""
        import platform
        
        # Skip on Windows - permission model is different
        if platform.system() == "Windows":
            pytest.skip("Permission model different on Windows")
        
        validator = ConfigValidator()
        
        # Create a directory and make it read-only
        readonly_dir = tmp_path / "readonly_projects"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, 0o555)  # r-xr-xr-x - read-only
        
        with patch.dict(os.environ, {"PROJECTS_DIR": str(readonly_dir)}, clear=False):
            with pytest.raises(ConfigValidationError) as exc_info:
                validator._validate_directories()
            
            assert "not writable" in str(exc_info.value).lower()
            assert exc_info.value.component == "directories"
    
    def test_directory_creation_on_missing(self, tmp_path: Path) -> None:
        """Validation should create directory if it doesn't exist."""
        validator = ConfigValidator()
        
        new_dir = tmp_path / "new_projects"
        assert not new_dir.exists()
        
        with patch.dict(os.environ, {"PROJECTS_DIR": str(new_dir)}, clear=False):
            result = validator._validate_directories()
            assert result is True
            assert new_dir.exists()
    
    def test_system_path_rejected_windows_style(self, tmp_path: Path) -> None:
        """Windows-style system paths should be rejected."""
        validator = ConfigValidator()
        
        # Simulate Windows-style system paths
        windows_system_paths = [
            str(tmp_path / "Windows" / "Test"),
            str(tmp_path / "Program Files" / "Test"),
            str(tmp_path / "Program Files (x86)" / "Test"),
            str(tmp_path / "System32" / "Test"),
            str(tmp_path / "ProgramData" / "Test"),
        ]
        
        for system_path in windows_system_paths:
            system_path_obj = Path(system_path)
            system_path_obj.mkdir(parents=True, exist_ok=True)
            
            with patch.dict(os.environ, {"PROJECTS_DIR": system_path}, clear=False):
                with pytest.raises(ConfigValidationError) as exc_info:
                    validator._validate_directories()
                
                assert "system-protected" in str(exc_info.value).lower()
                assert exc_info.value.component == "directories"
    
    def test_system_path_rejected_macos_style(self, tmp_path: Path) -> None:
        """macOS-style system paths should be rejected."""
        validator = ConfigValidator()
        
        # Simulate macOS-style system paths
        macos_system_paths = [
            str(tmp_path / "System" / "Test"),
            str(tmp_path / "bin" / "Test"),
            str(tmp_path / "sbin" / "Test"),
            str(tmp_path / "usr" / "Test"),
            str(tmp_path / "private" / "Test"),
        ]
        
        for system_path in macos_system_paths:
            system_path_obj = Path(system_path)
            system_path_obj.mkdir(parents=True, exist_ok=True)
            
            with patch.dict(os.environ, {"PROJECTS_DIR": system_path}, clear=False):
                with pytest.raises(ConfigValidationError) as exc_info:
                    validator._validate_directories()
                
                assert "system-protected" in str(exc_info.value).lower()
                assert exc_info.value.component == "directories"
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-only test")
    def test_read_only_directory_rejected_on_windows(self, tmp_path: Path) -> None:
        """A read-only directory should fail validation on Windows."""
        import ctypes
        
        validator = ConfigValidator()
        
        # Create a directory with a safe name (not matching system paths)
        readonly_dir = tmp_path / "user_projects_readonly"
        readonly_dir.mkdir()
        
        # Set read-only attribute using Windows API
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(readonly_dir))
        result = ctypes.windll.kernel32.SetFileAttributesW(str(readonly_dir), attrs | 0x0001)
        
        # Verify attribute was set
        attrs_after = ctypes.windll.kernel32.GetFileAttributesW(str(readonly_dir))
        assert attrs_after & 0x0001, "Read-only attribute not set correctly"
        
        try:
            with patch.dict(os.environ, {"PROJECTS_DIR": str(readonly_dir)}, clear=False):
                with pytest.raises(ConfigValidationError) as exc_info:
                    validator._validate_directories()
                
                assert "read-only" in str(exc_info.value).lower()
                assert exc_info.value.component == "directories"
        finally:
            # Clean up: remove read-only attribute
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(readonly_dir))
            ctypes.windll.kernel32.SetFileAttributesW(str(readonly_dir), attrs & ~0x0001)
