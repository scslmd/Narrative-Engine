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
        if self._is_pytest_runtime:
            return self._pytest_runtime_root / "projects"
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
    def audit_log_path(self) -> Path:
        if self._is_pytest_runtime:
            return self._pytest_runtime_root / "telemetry.jsonl"
        return Path(self.structured_log_filename)

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

    def inference_temperature(self, phase: str) -> float:
        """Get temperature for a pipeline phase.

        Overridable per-phase via env vars:
          NARRATIVE_TEMPERATURE_ARCHITECT   (P-100, default 1.0)
          NARRATIVE_TEMPERATURE_SEQUENCER   (P-200, default 0.6)
          NARRATIVE_TEMPERATURE_DRAFTER     (P-300, default 1.0)
          NARRATIVE_TEMPERATURE_PLANNER     (G-200, default 0.6)
          NARRATIVE_TEMPERATURE_CHAPTER     (G-300, default 1.0)

        Fallback env var for all phases: NARRATIVE_TEMPERATURE_DEFAULT (0.7).
        """
        phase_key = {
            "P-100": "ARCHITECT",
            "P-200": "SEQUENCER",
            "P-300": "DRAFTER",
            "G-200": "PLANNER",
            "G-300": "CHAPTER",
        }.get(phase.upper(), phase.upper())

        env_value = os.getenv(f"NARRATIVE_TEMPERATURE_{phase_key}", "").strip()
        if env_value:
            try:
                return float(env_value)
            except ValueError:
                pass

        fallback_default = os.getenv("NARRATIVE_TEMPERATURE_DEFAULT", "").strip()
        if fallback_default:
            try:
                return float(fallback_default)
            except ValueError:
                pass

        defaults = {
            "ARCHITECT": 1.0,
            "SEQUENCER": 0.6,
            "DRAFTER": 1.0,
            "PLANNER": 0.6,
            "CHAPTER": 1.0,
        }
        return defaults.get(phase_key, 0.7)

    def inference_max_tokens(self, phase: str) -> int:
        """Get max_tokens for a pipeline phase.

        Overridable per-phase via env vars:
          NARRATIVE_MAX_TOKENS_ARCHITECT    (P-100, default 4096)
          NARRATIVE_MAX_TOKENS_SEQUENCER    (P-200, default 4096)
          NARRATIVE_MAX_TOKENS_DRAFTER      (P-300, default 8000)
          NARRATIVE_MAX_TOKENS_COMPILER     (P-400, default 4096)
          NARRATIVE_MAX_TOKENS_PLANNER      (G-200, default 4096)
          NARRATIVE_MAX_TOKENS_CHAPTER      (G-300, default 8000)
          NARRATIVE_MAX_TOKENS_GUIDED_SETUP (default 8192)

        Fallback env var for all phases: NARRATIVE_MAX_TOKENS_DEFAULT (4096).
        """
        phase_key = {
            "P-100": "ARCHITECT",
            "P-200": "SEQUENCER",
            "P-300": "DRAFTER",
            "P-400": "COMPILER",
            "G-200": "PLANNER",
            "G-300": "CHAPTER",
            "GUIDED_SETUP": "GUIDED_SETUP",
        }.get(phase.upper(), phase.upper())

        env_value = os.getenv(f"NARRATIVE_MAX_TOKENS_{phase_key}", "").strip()
        if env_value:
            try:
                return max(64, int(env_value))
            except ValueError:
                pass

        fallback_default = os.getenv("NARRATIVE_MAX_TOKENS_DEFAULT", "").strip()
        if fallback_default:
            try:
                return max(64, int(fallback_default))
            except ValueError:
                pass

        defaults = {
            "ARCHITECT": 4096,
            "SEQUENCER": 4096,
            "DRAFTER": 8000,
            "COMPILER": 4096,
            "PLANNER": 4096,
            "CHAPTER": 8000,
            "GUIDED_SETUP": 8192,
        }
        return defaults.get(phase_key, 4096)

    @property
    def cors_origins(self) -> list[str]:
        raw_value = os.getenv("CORS_ORIGINS", "").strip()
        if raw_value:
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    @property
    def cors_allow_credentials(self) -> bool:
        raw_value = os.getenv("CORS_ALLOW_CREDENTIALS", "").strip()
        return raw_value.lower() == "true"

    @property
    def audit_log_retain_lines(self) -> int:
        raw = os.getenv("AUDIT_LOG_RETAIN_LINES", "").strip()
        if raw:
            try:
                return max(1, int(raw))
            except ValueError:
                pass
        return 10000


settings = Settings()
