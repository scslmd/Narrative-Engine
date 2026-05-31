import logging
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch


def test_config_validator_uses_logging_not_print():
    """Config validator should use logging, not print()."""
    from app.services.config_validator import ConfigValidator

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)

    with patch.dict(os.environ, {'API_KEY': '', 'NARRATIVE_INFERENCE_BACKEND': 'stub'}), \
         patch('sys.stdout', new=StringIO()) as fake_stdout:
        validator = ConfigValidator()

        logger = logging.getLogger('app.services.config_validator')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        validator._validate_api_key()

        stdout_output = fake_stdout.getvalue()
        log_output = log_capture.getvalue()

    assert '[WARN]' not in stdout_output, f"print() still used: {stdout_output}"
    assert 'API_KEY' in log_output, "Warning not logged"


def test_config_validator_has_no_print_calls():
    content = Path("app/services/config_validator.py").read_text(encoding="utf-8")
    assert "print(" not in content
