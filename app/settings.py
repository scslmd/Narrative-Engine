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

    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data"

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def state_dir(self) -> Path:
        return self.data_dir / "state"

    @property
    def operations_db_path(self) -> Path:
        return self.state_dir / "narrative_ops.db"

    @property
    def role_model_reports_dir(self) -> Path:
        return self.data_dir / "role_model_checker_runs"


settings = Settings()
