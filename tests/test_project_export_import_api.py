from __future__ import annotations

import hashlib
import json
import os
import time
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import build_app
from app.settings import settings


def _get_pytest_runtime_root() -> Path | None:
    """Get the pytest runtime root dir if running under pytest."""
    current_test = os.getenv("PYTEST_CURRENT_TEST", "").strip()
    if not current_test:
        return None
    worker = os.getenv("PYTEST_XDIST_WORKER", "main").strip() or "main"
    test_key = f"{worker}:{current_test}".encode("utf-8")
    test_hash = hashlib.sha256(test_key).hexdigest()[:16]
    return settings.root_dir / ".tmp_test_projects" / "pytest_runtime" / test_hash


def _remove_all_projects_from_runtime() -> None:
    """Remove all project directories from the pytest runtime root."""
    rt = _get_pytest_runtime_root()
    if not rt:
        return
    projects_dir = rt / "projects"
    if not projects_dir.is_dir():
        return
    import shutil
    for entry in sorted(projects_dir.iterdir()):
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)


def _create_test_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "test_export.zip"
    metadata = {
        "export_version": 1,
        "engine_version": "1.5.1",
        "created_at": "2026-05-04T12:00:00Z",
        "original_project_id": "proj-api-test",
        "original_project_name": "API Test Project",
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(metadata))
        zf.writestr("manifest.json", json.dumps({
            "project_id": "proj-api-test",
            "project_name": "API Test Project",
            "config": {
                "genre": "mystery",
                "tone_profile": "noir",
                "story_structure": "THREE_ACT",
            },
        }))
    return zip_path


class TestExportAPI:
    def test_export_project_returns_zip_stream(self, tmp_path: Path):
        """POST /projects/{id}/export returns application/zip."""
        client = TestClient(build_app())

        resp = client.post("/projects/create", json={
            "project_name": "Export Test Project",
        })
        assert resp.status_code == 201
        project_id = resp.json()["project_id"]

        resp = client.post(f"/projects/{project_id}/export")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/zip"
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert len(resp.content) > 0

        with zipfile.ZipFile(BytesIO(resp.content)) as zf:
            names = zf.namelist()
            assert "metadata.json" in names

    def test_export_nonexistent_project_returns_404(self):
        client = TestClient(build_app())
        resp = client.post("/projects/nonexistent-id/export")
        assert resp.status_code == 404


class TestImportAPI:
    def test_import_export_submits_async_job(self, tmp_path: Path):
        """POST /projects/import-export returns 202 with import_id."""
        _remove_all_projects_from_runtime()
        zip_path = _create_test_zip(tmp_path)

        client = TestClient(build_app())
        with open(zip_path, "rb") as f:
            resp = client.post(
                "/projects/import-export",
                files={"file": ("test_export.zip", f, "application/zip")},
                data={"project_name": "Imported via API"},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert "import_id" in data
        assert data["status"] == "pending"

    def test_import_export_rejects_non_zip(self):
        _remove_all_projects_from_runtime()
        client = TestClient(build_app())
        resp = client.post(
            "/projects/import-export",
            files={"file": ("notazip.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 422

    def test_get_export_status_returns_job_state(self, tmp_path: Path):
        """GET /projects/export/{id} returns job status."""
        _remove_all_projects_from_runtime()
        zip_path = _create_test_zip(tmp_path)

        client = TestClient(build_app())
        with open(zip_path, "rb") as f:
            resp = client.post(
                "/projects/import-export",
                files={"file": ("test_export.zip", f, "application/zip")},
            )
        import_id = resp.json()["import_id"]

        resp = client.get(f"/projects/export/{import_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("pending", "running", "completed", "failed")

    def test_get_export_status_returns_404_for_unknown(self):
        client = TestClient(build_app())
        resp = client.get("/projects/export/nonexistent-id")
        assert resp.status_code == 404
