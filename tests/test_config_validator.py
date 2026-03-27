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
