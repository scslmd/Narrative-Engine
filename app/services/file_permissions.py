"""File permission validation service (REL-09).

Validates file and directory permissions for:
- Ownership verification
- World-writable rejection
- Cross-platform compatibility
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any


class PermissionValidationError(Exception):
    """Raised when file permission validation fails."""
    
    def __init__(self, message: str, path: Path, permission_type: str):
        super().__init__(message)
        self.path = path
        self.permission_type = permission_type


class FilePermissionValidator:
    """Validates file and directory permissions."""
    
    def __init__(self, strict: bool = True) -> None:
        """
        Args:
            strict: If True, raise on permission issues. If False, warn only.
        """
        self.strict = strict
        self.warnings: list[str] = []
    
    def validate_directory(
        self,
        path: Path,
        check_ownership: bool = True,
        check_world_writable: bool = True,
        check_group_writable: bool = False,
    ) -> None:
        """Validate directory permissions."""
        if not path.exists():
            raise PermissionValidationError(
                f"Directory does not exist: {path}",
                path,
                "not_found",
            )
        
        if not path.is_dir():
            raise PermissionValidationError(
                f"Path is not a directory: {path}",
                path,
                "not_directory",
            )
        
        if check_ownership:
            self._validate_ownership(path)
        
        if check_world_writable:
            self._validate_not_world_writable(path)
        
        if check_group_writable:
            self._validate_not_group_writable(path)
    
    def validate_file(
        self,
        path: Path,
        check_ownership: bool = True,
        check_world_writable: bool = True,
    ) -> None:
        """Validate file permissions."""
        if not path.exists():
            raise PermissionValidationError(
                f"File does not exist: {path}",
                path,
                "not_found",
            )
        
        if not path.is_file():
            raise PermissionValidationError(
                f"Path is not a file: {path}",
                path,
                "not_file",
            )
        
        if check_ownership:
            self._validate_ownership(path)
        
        if check_world_writable:
            self._validate_not_world_writable(path)
    
    def _validate_ownership(self, path: Path) -> None:
        """Validate file/directory is owned by application user."""
        if os.name == 'nt':
            return
        
        file_stat = os.stat(path)
        file_uid = file_stat.st_uid
        
        current_uid = os.getuid()
        
        if file_uid != current_uid:
            self._handle_issue(
                f"File {path} is not owned by current user (UID {file_uid} != {current_uid})",
                path,
                "ownership",
            )
    
    def _validate_not_world_writable(self, path: Path) -> None:
        """Validate path is not world-writable."""
        if os.name == 'nt':
            return
        
        file_stat = os.stat(path)
        mode = file_stat.st_mode
        
        if mode & stat.S_IWOTH:
            self._handle_issue(
                f"Path {path} is world-writable (insecure permissions: {oct(mode)})",
                path,
                "world_writable",
            )
    
    def _validate_not_group_writable(self, path: Path) -> None:
        """Validate path is not group-writable (optional check)."""
        if os.name == 'nt':
            return
        
        file_stat = os.stat(path)
        mode = file_stat.st_mode
        
        if mode & stat.S_IWGRP:
            self._handle_issue(
                f"Path {path} is group-writable (permissions: {oct(mode)})",
                path,
                "group_writable",
            )
    
    def _handle_issue(
        self,
        message: str,
        path: Path,
        permission_type: str,
    ) -> None:
        """Handle permission issue based on strict mode."""
        warning = f"[PERMISSION WARNING] {message}"
        self.warnings.append(warning)
        
        if self.strict:
            raise PermissionValidationError(message, path, permission_type)
        else:
            print(warning)
    
    def is_world_writable(self, path: Path) -> bool:
        """Check if path is world-writable without raising."""
        if os.name == 'nt':
            return False
        
        try:
            mode = os.stat(path).st_mode
            return bool(mode & stat.S_IWOTH)
        except OSError:
            return False
    
    def get_permissions(self, path: Path) -> str:
        """Get human-readable permissions string."""
        if os.name == 'nt':
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attrs != -1 and (attrs & 0x0001):
                    return "readonly"
            except Exception:
                pass
            return "unknown (Windows)"
        
        try:
            mode = os.stat(path).st_mode
            return oct(mode)[-3:]
        except OSError:
            return "unknown"
