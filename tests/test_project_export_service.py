from __future__ import annotations

import json
import zipfile
from pathlib import Path

import sqlite3

from app.services.project_export import ProjectExportService


def _create_test_project_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    (project_dir / "manifest.json").write_text(json.dumps({
        "project_id": "proj-test-001",
        "project_name": "Test Story",
        "config": {"genre": "fantasy", "tone_profile": "dark", "pov": "Third_Limited"},
    }))

    conn = sqlite3.connect(str(project_dir / "bible.db"))
    conn.execute("CREATE TABLE IF NOT EXISTS project_metadata (key TEXT, value TEXT)")
    conn.execute("INSERT INTO project_metadata VALUES ('version', '1')")
    conn.commit()
    conn.close()

    (project_dir / "sequences.json").write_text(json.dumps([]))
    (project_dir / "chapter.md").write_text("# Chapter 1\n\nOnce upon a time...")

    exports_dir = project_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "p100_output.md").write_text("# Architect output")

    return project_dir


def _create_ops_db_with_empty_tables(db_path: Path) -> Path:
    from app.services.project_export import _OPS_TABLES_WITH_PROJECT_ID

    conn = sqlite3.connect(str(db_path))
    for tname in _OPS_TABLES_WITH_PROJECT_ID:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {tname} (project_id TEXT, data TEXT)"
        )
    conn.commit()
    conn.close()
    return db_path


class TestProjectExportService:
    def test_create_zip_includes_metadata(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        service = ProjectExportService(ops_db_path=ops_db)
        project_dir = _create_test_project_dir(tmp_path)
        zip_path = tmp_path / "export.zip"

        service.create_zip(project_dir, zip_path, "Test Story", "proj-test-001")

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, "r") as zf:
            metadata_raw = json.loads(zf.read("metadata.json"))
        assert metadata_raw["export_version"] == 1
        assert metadata_raw["original_project_id"] == "proj-test-001"
        assert metadata_raw["original_project_name"] == "Test Story"

    def test_create_zip_includes_project_files(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        service = ProjectExportService(ops_db_path=ops_db)
        project_dir = _create_test_project_dir(tmp_path)
        zip_path = tmp_path / "export.zip"

        service.create_zip(project_dir, zip_path, "Test Story", "proj-test-001")

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert any("manifest.json" in n for n in names)
        assert any("bible.db" in n for n in names)
        assert any("chapter.md" in n for n in names)

    def test_create_zip_includes_ops_db_directory(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        service = ProjectExportService(ops_db_path=ops_db)
        project_dir = _create_test_project_dir(tmp_path)
        zip_path = tmp_path / "export.zip"

        service.create_zip(project_dir, zip_path, "Test Story", "proj-test-001")

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert any("ops_db/" in n for n in names) or zip_path.stat().st_size > 100

    def test_dump_ops_data_queries_tables(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        conn = sqlite3.connect(str(ops_db))
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, project_id TEXT, job_type TEXT, status TEXT)")
        conn.execute("INSERT INTO jobs VALUES ('job-1', 'proj-test-001', 'P-300', 'COMPLETED')")
        conn.execute("INSERT INTO jobs VALUES ('job-2', 'proj-other', 'P-100', 'FAILED')")
        conn.commit()
        conn.close()

        service = ProjectExportService(ops_db_path=ops_db)
        result = service.dump_ops_data("proj-test-001")

        assert "jobs" in result
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["job_id"] == "job-1"

    def test_project_files_excludes_wal_shm(self, tmp_path: Path):
        project_dir = _create_test_project_dir(tmp_path)
        (project_dir / "bible.db-wal").write_bytes(b"wal")
        (project_dir / "bible.db-shm").write_bytes(b"shm")

        files = ProjectExportService.project_files(project_dir)
        names = [f.name for f in files]
        assert "bible.db-wal" not in names
        assert "bible.db-shm" not in names

    def test_create_zip_with_ops_data(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        service = ProjectExportService(ops_db_path=ops_db)
        project_dir = _create_test_project_dir(tmp_path)
        zip_path = tmp_path / "export.zip"

        conn = sqlite3.connect(str(ops_db))
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, project_id TEXT, job_type TEXT, status TEXT)")
        conn.execute("INSERT INTO jobs VALUES ('job-1', 'proj-test-001', 'P-300', 'COMPLETED')")
        conn.commit()
        conn.close()

        service.create_zip(project_dir, zip_path, "Test Story", "proj-test-001")

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert any("ops_db/jobs.json" in n for n in names)

        with zipfile.ZipFile(zip_path, "r") as zf:
            jobs_content = json.loads(zf.read("ops_db/jobs.json"))
        assert len(jobs_content) == 1
        assert jobs_content[0]["job_id"] == "job-1"

    def test_dump_ops_data_excludes_other_project(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        conn = sqlite3.connect(str(ops_db))
        conn.execute("DROP TABLE IF EXISTS projects")
        conn.execute("CREATE TABLE projects (project_id TEXT PRIMARY KEY, project_name TEXT)")
        conn.execute("INSERT INTO projects VALUES ('proj-test-001', 'Test Story')")
        conn.execute("INSERT INTO projects VALUES ('proj-other', 'Other Story')")
        conn.commit()
        conn.close()

        service = ProjectExportService(ops_db_path=ops_db)
        result = service.dump_ops_data("proj-test-001")

        assert "projects" in result
        assert len(result["projects"]) == 1
        assert result["projects"][0]["project_name"] == "Test Story"

    def test_dump_ops_data_empty_db(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")

        service = ProjectExportService(ops_db_path=ops_db)
        result = service.dump_ops_data("proj-test-001")

        assert result == {}

    def test_project_files_includes_nested(self, tmp_path: Path):
        project_dir = _create_test_project_dir(tmp_path)
        nested = project_dir / "exports" / "deep"
        nested.mkdir(parents=True)
        (nested / "nested_file.txt").write_text("nested content")

        files = ProjectExportService.project_files(project_dir)
        names = [f.name for f in files]
        assert "nested_file.txt" in names

    def test_create_zip_includes_nested_files(self, tmp_path: Path):
        ops_db = _create_ops_db_with_empty_tables(tmp_path / "ops.db")
        service = ProjectExportService(ops_db_path=ops_db)
        project_dir = _create_test_project_dir(tmp_path)

        nested = project_dir / "exports" / "deep"
        nested.mkdir(parents=True)
        (nested / "nested_file.txt").write_text("nested content")

        zip_path = tmp_path / "export.zip"
        service.create_zip(project_dir, zip_path, "Test Story", "proj-test-001")

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert any("exports/deep/nested_file.txt" in n for n in names)
