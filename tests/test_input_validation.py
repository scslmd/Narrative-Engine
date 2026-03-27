"""Tests for input validation and sanitization (SEC-01)."""

import pytest

from app.utils.input_validation import (
    MAX_DICT_KEYS,
    MAX_JSON_DEPTH,
    MAX_LIST_LENGTH,
    MAX_STRING_LENGTH,
    ValidationError,
    is_safe_url,
    sanitize_filename,
    sanitize_project_id,
    sanitize_sql_identifier,
    sanitize_string,
    validate_json_depth,
)


class TestSanitizeString:
    """Test string sanitization."""
    
    def test_basic_sanitization(self) -> None:
        """Should strip whitespace by default."""
        result = sanitize_string("  hello world  ")
        assert result == "hello world"
    
    def test_html_escaping(self) -> None:
        """Should escape HTML entities by default (XSS prevention)."""
        result = sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_allows_html_when_requested(self) -> None:
        """Should allow HTML when explicitly permitted."""
        html_input = "<p>Hello <strong>world</strong></p>"
        result = sanitize_string(html_input, allow_html=True)
        assert result == html_input
    
    def test_rejects_null_bytes(self) -> None:
        """Should reject strings with null bytes."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string("hello\x00world")
        
        assert "null bytes" in str(exc_info.value).lower()
    
    def test_rejects_non_string_input(self) -> None:
        """Should reject non-string input."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string(12345)  # type: ignore
        
        assert "expected string" in str(exc_info.value).lower()
    
    def test_rejects_too_long_strings(self) -> None:
        """Should reject strings exceeding max length."""
        long_string = "a" * (MAX_STRING_LENGTH + 1)
        
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string(long_string, max_length=100)
        
        assert "exceeds maximum length" in str(exc_info.value).lower()


class TestSanitizeFilename:
    """Test filename sanitization."""
    
    def test_basic_filename(self) -> None:
        """Should accept valid filenames."""
        result = sanitize_filename("my_file.txt")
        assert result == "my_file.txt"
    
    def test_removes_path_components_unix(self) -> None:
        """Should remove Unix path separators (path traversal prevention)."""
        result = sanitize_filename("/etc/passwd")
        assert "/" not in result
    
    def test_removes_path_components_windows(self) -> None:
        """Should remove Windows path separators."""
        result = sanitize_filename(r"folder\subfolder\file.txt")
        assert "\\" not in result
        assert "foldersubfolderfile.txt" == result
    
    def test_rejects_parent_directory_traversal(self) -> None:
        """Should reject parent directory traversal sequences."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_filename("../secret.txt")
        
        assert "path traversal" in str(exc_info.value).lower()
    
    def test_removes_null_bytes(self) -> None:
        """Should remove null bytes from filename."""
        result = sanitize_filename("file\x00.txt")
        assert "\x00" not in result
    
    def test_rejects_empty_filename(self) -> None:
        """Should reject empty filenames."""
        with pytest.raises(ValidationError):
            sanitize_filename("")
    
    def test_rejects_too_long_filename(self) -> None:
        """Should reject filenames exceeding max length."""
        long_name = "a" * 300
        
        with pytest.raises(ValidationError):
            sanitize_filename(long_name, max_length=255)
    
    def test_rejects_windows_reserved_names(self) -> None:
        """Should reject Windows reserved names."""
        with pytest.raises(ValidationError) as exc_info:
            sanitize_filename("CON.txt")
        
        assert "reserved name" in str(exc_info.value).lower()
    
    def test_rejects_invalid_characters(self) -> None:
        """Should reject filenames with invalid characters."""
        with pytest.raises(ValidationError):
            sanitize_filename("file|name.txt")  # Pipe is invalid
    
    def test_allows_valid_special_chars(self) -> None:
        """Should allow dots, dashes, underscores, and spaces."""
        result = sanitize_filename("my-file_name v2.0.txt")
        assert result == "my-file_name v2.0.txt"


class TestSanitizeProjectId:
    """Test project ID sanitization."""
    
    def test_valid_uuid(self) -> None:
        """Should accept valid UUID format."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = sanitize_project_id(uuid)
        assert result == uuid
    
    def test_valid_alphanumeric(self) -> None:
        """Should accept alphanumeric IDs."""
        result = sanitize_project_id("project123")
        assert result == "project123"
    
    def test_allows_dash_and_underscore(self) -> None:
        """Should allow dashes and underscores."""
        result = sanitize_project_id("my-project_123")
        assert result == "my-project_123"
    
    def test_rejects_empty_id(self) -> None:
        """Should reject empty project IDs."""
        with pytest.raises(ValidationError):
            sanitize_project_id("")
    
    def test_rejects_invalid_characters(self) -> None:
        """Should reject invalid characters like dots and spaces."""
        with pytest.raises(ValidationError):
            sanitize_project_id("project.id")  # Dot not allowed
    
    def test_rejects_path_traversal(self) -> None:
        """Should reject path traversal attempts."""
        with pytest.raises(ValidationError):
            sanitize_project_id("../etc/passwd")


class TestSanitizeSqlIdentifier:
    """Test SQL identifier sanitization."""
    
    def test_valid_identifier(self) -> None:
        """Should accept valid SQL identifiers."""
        result = sanitize_sql_identifier("user_name")
        assert result == "user_name"
    
    def test_starts_with_underscore(self) -> None:
        """Should allow identifiers starting with underscore."""
        result = sanitize_sql_identifier("_private")
        assert result == "_private"
    
    def test_rejects_starting_with_number(self) -> None:
        """Should reject identifiers starting with number."""
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("123table")
    
    def test_rejects_special_characters(self) -> None:
        """Should reject special characters."""
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("user-name")  # Dash not allowed
    
    def test_empty_identifier(self) -> None:
        """Should reject empty identifiers."""
        with pytest.raises(ValidationError):
            sanitize_sql_identifier("")


class TestValidateJsonDepth:
    """Test JSON depth validation."""
    
    def test_valid_shallow_structure(self) -> None:
        """Should accept shallow structures."""
        obj = {"key": "value", "nested": {"a": 1}}
        
        # Should not raise
        validate_json_depth(obj)
    
    def test_rejects_too_deep_structure(self) -> None:
        """Should reject deeply nested structures (DoS prevention)."""
        # Create deeply nested structure
        deep_obj: dict[str, int | dict] = {"level": 0}
        current = deep_obj
        for i in range(1, MAX_JSON_DEPTH + 5):
            new_level: dict[str, int | dict] = {"level": i}
            current["child"] = new_level
            current = new_level
        
        with pytest.raises(ValidationError) as exc_info:
            validate_json_depth(deep_obj)
        
        assert "exceeds maximum depth" in str(exc_info.value).lower()
    
    def test_rejects_too_many_keys(self) -> None:
        """Should reject objects with too many keys."""
        large_obj = {f"key_{i}": i for i in range(MAX_DICT_KEYS + 10)}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_json_depth(large_obj)
        
        assert "exceeds maximum key count" in str(exc_info.value).lower()
    
    def test_rejects_too_long_list(self) -> None:
        """Should reject lists that are too long."""
        large_list = list(range(MAX_LIST_LENGTH + 10))
        
        with pytest.raises(ValidationError) as exc_info:
            validate_json_depth(large_list)
        
        assert "exceeds maximum length" in str(exc_info.value).lower()


class TestIsSafeUrl:
    """Test URL safety checking."""
    
    def test_safe_http_url(self) -> None:
        """Should accept safe HTTP URLs."""
        assert is_safe_url("https://example.com") is True
    
    def test_safe_ftp_url(self) -> None:
        """Should accept FTP URLs."""
        assert is_safe_url("ftp://files.example.com/file.txt") is True
    
    def test_rejects_javascript_protocol(self) -> None:
        """Should reject javascript: protocol (XSS)."""
        assert is_safe_url("javascript:alert('xss')") is False
    
    def test_rejects_data_protocol(self) -> None:
        """Should reject data: protocol."""
        assert is_safe_url("data:text/html,<script>alert(1)</script>") is False
    
    def test_rejects_vbscript_protocol(self) -> None:
        """Should reject vbscript: protocol."""
        assert is_safe_url("vbscript:msgbox('hello')") is False
    
    def test_case_insensitive(self) -> None:
        """Should be case-insensitive for protocol checking."""
        assert is_safe_url("JAVASCRIPT:alert(1)") is False
        assert is_safe_url("JaVaScRiPt:alert(1)") is False


class TestIntegration:
    """Test integration of multiple sanitization functions."""
    
    def test_full_sanitization_pipeline(self) -> None:
        """Test complete sanitization pipeline for user input."""
        # Simulate malicious input
        malicious_input = "<script>alert('xss')</script>"
        
        # Sanitize as string (XSS prevention)
        sanitized = sanitize_string(malicious_input, allow_html=False)
        assert "&lt;script&gt;" in sanitized
        
        # Validate JSON structure
        payload = {"name": "test", "description": sanitized}
        validate_json_depth(payload)  # Should not raise
    
    def test_filename_from_user_input(self) -> None:
        """Test filename sanitization from potentially malicious input."""
        # Path traversal attempt
        user_input = "../../../etc/passwd"
        
        with pytest.raises(ValidationError):
            sanitize_filename(user_input)
