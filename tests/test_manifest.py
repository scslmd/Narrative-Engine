from __future__ import annotations

import json
from pathlib import Path

from app.utils.manifest import update_manifest


class TestUpdateManifest:
    """Tests for the shared manifest update helper."""

    def _make_project_dir(self, tmp_path: Path) -> Path:
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        return project_dir

    def test_adds_config_keys(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps({"project_id": "test", "config": {}}),
            encoding="utf-8",
        )

        update_manifest(project_dir, "test", {"key_a": "val_a", "key_b": "val_b"})

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["config"]["key_a"] == "val_a"
        assert data["config"]["key_b"] == "val_b"

    def test_overwrites_existing_key(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps({"project_id": "test", "config": {"key_a": "old"}}),
            encoding="utf-8",
        )

        update_manifest(project_dir, "test", {"key_a": "new"})

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["config"]["key_a"] == "new"

    def test_creates_config_dict_if_missing(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps({"project_id": "test"}),
            encoding="utf-8",
        )

        update_manifest(project_dir, "test", {"key_a": "val_a"})

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "config" in data
        assert data["config"]["key_a"] == "val_a"

    def test_skips_if_manifest_not_exists(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)

        update_manifest(project_dir, "test", {"key_a": "val_a"})

        assert not (project_dir / "manifest.json").exists()

    def test_handles_corrupt_json_no_raise(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text("not valid json {{{", encoding="utf-8")

        update_manifest(project_dir, "test", {"key_a": "val_a"})

        content = manifest_path.read_text(encoding="utf-8")
        assert content == "not valid json {{{"

    def test_sorts_keys_in_output(self, tmp_path: Path) -> None:
        project_dir = self._make_project_dir(tmp_path)
        manifest_path = project_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps({"project_id": "test", "config": {}}),
            encoding="utf-8",
        )

        update_manifest(project_dir, "test", {"zebra": "z", "alpha": "a"})

        content = manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)
        config_keys = list(data["config"].keys())
        assert config_keys == sorted(config_keys)
