from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "Narrative-Engine"
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
        if self._is_pytest_runtime:
            return self._pytest_runtime_root / "state"
        return self.data_dir / "state"

    @property
    def operations_db_path(self) -> Path:
        return self.state_dir / "narrative_ops.db"

    @property
    def role_model_reports_dir(self) -> Path:
        if self._is_pytest_runtime:
            return self._pytest_runtime_root / "role_model_checker_runs"
        return self.data_dir / "role_model_checker_runs"

    @property
    def _is_pytest_runtime(self) -> bool:
        return bool(os.getenv("PYTEST_CURRENT_TEST", "").strip())

    @property
    def _pytest_runtime_root(self) -> Path:
        current_test = os.getenv("PYTEST_CURRENT_TEST", "").strip()
        if not current_test:
            return self.data_dir

        worker = os.getenv("PYTEST_XDIST_WORKER", "main").strip() or "main"
        test_key = f"{worker}:{current_test}".encode("utf-8")
        test_hash = hashlib.sha256(test_key).hexdigest()[:16]
        return self.root_dir / ".tmp_test_projects" / "pytest_runtime" / test_hash

    @property
    def inference_backend(self) -> str:
        return os.getenv("NARRATIVE_INFERENCE_BACKEND", "stub").strip() or "stub"

    @property
    def inference_base_url(self) -> str:
        configured = os.getenv("NARRATIVE_INFERENCE_BASE_URL", "").strip()
        if configured:
            return configured
        default_urls = {
            "llama.cpp": "http://127.0.0.1:8080",
            "lmstudio": "http://127.0.0.1:1234",
            "vllm": "http://127.0.0.1:8000",
            "openai_compatible": "http://127.0.0.1:8000",
        }
        return default_urls.get(self.inference_backend, "")

    @property
    def inference_api_key(self) -> str | None:
        value = os.getenv("NARRATIVE_INFERENCE_API_KEY", "").strip()
        return value or None

    @property
    def api_key(self) -> str | None:
        """API key for authentication middleware.
        
        Required when authentication is enabled. Set in .env file.
        For local development, can be any string (e.g., "dev-key-123").
        """
        value = os.getenv("API_KEY", "").strip()
        return value or None

    @property
    def inference_default_model(self) -> str | None:
        value = os.getenv("NARRATIVE_INFERENCE_MODEL", "").strip()
        return value or None

    @property
    def inference_timeout_seconds(self) -> float:
        raw_value = os.getenv("NARRATIVE_INFERENCE_TIMEOUT_SECONDS", "120").strip()
        try:
            return float(raw_value)
        except ValueError:
            return 120.0

    @property
    def inference_aliases(self) -> list[str]:
        aliases = {
            "llama.cpp": ["llama-server", "openai-compatible"],
            "lmstudio": ["lm-studio", "openai-compatible"],
            "vllm": ["openai-compatible"],
            "openai_compatible": ["openai-compatible"],
        }
        return aliases.get(self.inference_backend, [])


settings = Settings()
