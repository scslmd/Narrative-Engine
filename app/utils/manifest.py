from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def update_manifest(
    project_dir: Path,
    project_id: str,
    config_updates: dict[str, str],
) -> None:
    """Update manifest.json with config key-value pairs.

    Log-warnings on failure; never raise. The caller handles
    transaction boundaries — this function only touches the file.
    """
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        logger.warning("Manifest not found for project %s, skipping update", project_id)
        return

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read manifest for project %s: %s", project_id, exc)
        return

    if "config" not in manifest_data:
        manifest_data["config"] = {}

    manifest_data["config"].update(config_updates)

    try:
        manifest_path.write_text(
            json.dumps(manifest_data, ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Failed to write manifest for project %s: %s", project_id, exc)
