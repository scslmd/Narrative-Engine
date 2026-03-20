from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Narrative-Core Recovered"
    app_env: str = "local"
    default_seed: int = 42
    telemetry_filename: str = "telemetry.log"
    structured_log_filename: str = "telemetry.jsonl"
    root_dir: Path = Path(__file__).resolve().parents[1]

    @property
    def frontend_dir(self) -> Path:
        return self.root_dir / "frontend"


settings = Settings()
