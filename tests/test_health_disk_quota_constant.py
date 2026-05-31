from pathlib import Path


def test_health_check_uses_disk_quota_constant():
    health_source = Path("app/api/health.py").read_text(encoding="utf-8")
    constants_source = Path("app/constants.py").read_text(encoding="utf-8")

    assert "DISK_QUOTA_BYTES" in constants_source
    assert "DISK_QUOTA_BYTES" in health_source
    assert "1_073_741_824" not in health_source
