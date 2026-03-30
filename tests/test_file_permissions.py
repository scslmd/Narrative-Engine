"""Tests for file permission validation service (REL-09)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from app.services.file_permissions import FilePermissionValidator, PermissionValidationError


class TestFilePermissionValidator:
    """Test FilePermissionValidator class."""
    
    def test_world_writable_directory_fails(self, tmp_path: Path) -> None:
        """Test that world-writable directories are rejected."""
        dir_path = tmp_path / "world_writable"
        dir_path.mkdir()
        
        if os.name != 'nt':
            os.chmod(dir_path, 0o777)
        
        validator = FilePermissionValidator(strict=True)
        
        if os.name == 'nt':
            # Windows doesn't have world-writable in same way
            validator.validate_directory(dir_path)  # Should not raise
        else:
            with pytest.raises(PermissionValidationError) as exc_info:
                validator.validate_directory(dir_path)
            
            assert "world-writable" in str(exc_info.value)
    
    def test_world_writable_file_fails(self, tmp_path: Path) -> None:
        """Test that world-writable files are rejected."""
        file_path = tmp_path / "world_writable.txt"
        file_path.write_text("test")
        
        if os.name != 'nt':
            os.chmod(file_path, 0o666)
        
        validator = FilePermissionValidator(strict=True)
        
        if os.name == 'nt':
            validator.validate_file(file_path)  # Should not raise
        else:
            with pytest.raises(PermissionValidationError) as exc_info:
                validator.validate_file(file_path)
            
            assert "world-writable" in str(exc_info.value)
    
    def test_safe_directory_passes(self, tmp_path: Path) -> None:
        """Test that safe directories pass validation."""
        dir_path = tmp_path / "safe_dir"
        dir_path.mkdir()
        
        validator = FilePermissionValidator(strict=True)
        validator.validate_directory(dir_path)  # Should not raise
    
    def test_safe_file_passes(self, tmp_path: Path) -> None:
        """Test that safe files pass validation."""
        file_path = tmp_path / "safe_file.txt"
        file_path.write_text("test")
        
        validator = FilePermissionValidator(strict=True)
        validator.validate_file(file_path)  # Should not raise
    
    def test_nonexistent_directory_fails(self, tmp_path: Path) -> None:
        """Test that nonexistent directories fail validation."""
        dir_path = tmp_path / "nonexistent"
        
        validator = FilePermissionValidator(strict=True)
        with pytest.raises(PermissionValidationError) as exc_info:
            validator.validate_directory(dir_path)
        
        assert "Directory does not exist" in str(exc_info.value)
    
    def test_nonexistent_file_fails(self, tmp_path: Path) -> None:
        """Test that nonexistent files fail validation."""
        file_path = tmp_path / "nonexistent.txt"
        
        validator = FilePermissionValidator(strict=True)
        with pytest.raises(PermissionValidationError) as exc_info:
            validator.validate_file(file_path)
        
        assert "File does not exist" in str(exc_info.value)
    
    def test_path_is_directory_not_file(self, tmp_path: Path) -> None:
        """Test that validating a directory as a file fails."""
        dir_path = tmp_path / "dir"
        dir_path.mkdir()
        
        validator = FilePermissionValidator(strict=True)
        with pytest.raises(PermissionValidationError) as exc_info:
            validator.validate_file(dir_path)
        
        assert "Path is not a file" in str(exc_info.value)
    
    def test_path_is_file_not_directory(self, tmp_path: Path) -> None:
        """Test that validating a file as a directory fails."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        
        validator = FilePermissionValidator(strict=True)
        with pytest.raises(PermissionValidationError) as exc_info:
            validator.validate_directory(file_path)
        
        assert "Path is not a directory" in str(exc_info.value)
    
    def test_non_strict_mode_warns(self, tmp_path: Path) -> None:
        """Test that non-strict mode warns instead of raising."""
        dir_path = tmp_path / "world_writable"
        dir_path.mkdir()
        
        validator = FilePermissionValidator(strict=False)
        
        if os.name != 'nt':
            os.chmod(dir_path, 0o777)
            validator.validate_directory(dir_path)
            assert len(validator.warnings) > 0
            assert any("world-writable" in w for w in validator.warnings)
        else:
            validator.validate_directory(dir_path)
    
    def test_is_world_writable_method(self, tmp_path: Path) -> None:
        """Test is_world_writable method."""
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()
        
        validator = FilePermissionValidator()
        
        if os.name == 'nt':
            assert not validator.is_world_writable(dir_path)
        else:
            assert not validator.is_world_writable(dir_path)
            
            os.chmod(dir_path, 0o777)
            assert validator.is_world_writable(dir_path)
    
    def test_get_permissions_method(self, tmp_path: Path) -> None:
        """Test get_permissions method."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        
        validator = FilePermissionValidator()
        perms = validator.get_permissions(file_path)
        
        assert perms is not None
        if os.name == 'nt':
            assert "readonly" in perms or "unknown" in perms
        else:
            assert len(perms) == 3
