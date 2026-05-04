from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from app.services.project_import import ProjectImportService, ProjectImportError


def _create_valid_export_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "valid_export.zip"
    metadata = {
        "export_version": 1,
        "engine_version": "1.5.1",
        "created_at": "2026-05-04T12:00:00Z",
        "original_project_id": "proj-import-test",
        "original_project_name": "Imported Story",
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(metadata))
        zf.writestr("manifest.json", json.dumps({
            "project_id": "proj-import-test",
            "project_name": "Imported Story",
            "config": {"genre": "sci-fi", "tone_profile": "optimistic"},
        }))

    return zip_path


def _create_corrupt_zip(tmp_path: Path) -> Path:
    bad_path = tmp_path / "not_a_zip.zip"
    bad_path.write_text("this is not a zip file")
    return bad_path


def _create_missing_metadata_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "no_meta.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({"project_id": "x"}))
    return zip_path


def _create_old_version_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "old.zip"
    metadata = {
        "export_version": 0,
        "engine_version": "1.0.0",
        "created_at": "2025-01-01T00:00:00Z",
        "original_project_id": "proj-old",
        "original_project_name": "Old Export",
    }
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("metadata.json", json.dumps(metadata))
    return zip_path


class TestProjectImportService:
    def test_validate_zip_accepts_valid_export(self, tmp_path: Path):
        zip_path = _create_valid_export_zip(tmp_path)
        result = ProjectImportService().validate_zip(zip_path)
        assert result.export_version == 1
        assert result.original_project_name == "Imported Story"

    def test_validate_zip_rejects_corrupt_file(self, tmp_path: Path):
        zip_path = _create_corrupt_zip(tmp_path)
        with pytest.raises(ProjectImportError, match="not a valid ZIP"):
            ProjectImportService().validate_zip(zip_path)

    def test_validate_zip_rejects_missing_metadata(self, tmp_path: Path):
        zip_path = _create_missing_metadata_zip(tmp_path)
        with pytest.raises(ProjectImportError, match="missing metadata.json"):
            ProjectImportService().validate_zip(zip_path)

    def test_validate_zip_rejects_old_version(self, tmp_path: Path):
        zip_path = _create_old_version_zip(tmp_path)
        with pytest.raises(ProjectImportError, match="not supported"):
            ProjectImportService().validate_zip(zip_path)

    def test_migrate_v1_to_current_is_identity(self):
        ops_data = {
            "jobs": [{"job_id": "j-1", "project_id": "proj-x"}],
            "foundation_profiles": [{"project_id": "proj-x", "premise": "Test"}],
        }
        result = ProjectImportService.migrate_v1_to_current(ops_data)
        assert result["jobs"] == ops_data["jobs"]
        assert result["foundation_profiles"] == ops_data["foundation_profiles"]

    def test_extract_zip_valid(self, tmp_path: Path):
        zip_path = _create_valid_export_zip(tmp_path)
        extract_dir = tmp_path / "extracted"

        result = ProjectImportService().extract_zip(zip_path, extract_dir)

        assert (extract_dir / "metadata.json").exists()
        assert (extract_dir / "manifest.json").exists()

    def test_extract_zip_rejects_path_traversal(self, tmp_path: Path):
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../escape.txt", "malicious content")

        with pytest.raises(ProjectImportError, match="Path traversal"):
            ProjectImportService().extract_zip(zip_path, tmp_path / "bad_dir")
