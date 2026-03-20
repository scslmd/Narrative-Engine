from __future__ import annotations

import json
from pathlib import Path

from app.schemas.manifest import Manifest


class ManifestValidationService:
    @staticmethod
    def validate_payload(payload: dict) -> Manifest:
        return Manifest.model_validate(payload)

    @staticmethod
    def validate_file(manifest_path: Path) -> Manifest:
        raw_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return Manifest.model_validate(raw_payload)


def validate_manifest_dict(payload: dict) -> Manifest:
    return ManifestValidationService.validate_payload(payload)