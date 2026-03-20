from __future__ import annotations

from typing import Literal

RoleName = Literal["architect", "sequencer", "drafter", "critic"]
CriticExperimentProfile = Literal["baseline", "minimal_context", "low_max_tokens_256", "low_max_tokens_128", "deterministic_only"]

WORKFLOW_ORDER: list[RoleName] = ["architect", "sequencer", "drafter", "critic"]

WORKFLOW_GUIDANCE: list[str] = [
    "Step 1: Architect first. Validate structured story-bible output before testing downstream roles.",
    "Step 2: Sequencer second. Validate beat planning and structural discipline after the architect passes.",
    "Step 3: Drafter third. Validate clean prose generation after the planning layers are stable.",
    "Step 4: Critic last, usually one role at a time, because critic runs are verification-heavy.",
]

DEFAULT_CRITIC_PROFILE: CriticExperimentProfile = "minimal_context"

CRITIC_PROFILE_DEFINITIONS = {
    "baseline": {"id": "baseline", "label": "Baseline", "description": "Recovered default comparison profile using fuller critic context.", "context_mode": "compact", "max_tokens": 384, "deterministic_only": False, "experimental": False},
    "minimal_context": {"id": "minimal_context", "label": "Minimal Context", "description": "Recovered recommended critic profile. Uses the smallest safe context that still passed earlier checks.", "context_mode": "minimal", "max_tokens": 384, "deterministic_only": False, "experimental": False},
    "low_max_tokens_256": {"id": "low_max_tokens_256", "label": "Low Max Tokens 256", "description": "Recovered experiment profile to reduce critic latency with a smaller output budget.", "context_mode": "minimal", "max_tokens": 256, "deterministic_only": False, "experimental": True},
    "low_max_tokens_128": {"id": "low_max_tokens_128", "label": "Low Max Tokens 128", "description": "Aggressive critic speed profile. Earlier notes suggest this may be too restrictive.", "context_mode": "minimal", "max_tokens": 128, "deterministic_only": False, "experimental": True},
    "deterministic_only": {"id": "deterministic_only", "label": "Deterministic Only", "description": "Skip LLM critique and only run deterministic checks. Very fast, but incomplete.", "context_mode": "minimal", "max_tokens": 0, "deterministic_only": True, "experimental": True},
}

MODEL_ROLE_PATTERNS = {
    "architect": ["qwen2.5-32b-instruct-q4_k_m", "qwen2.5-32b-instruct"],
    "sequencer": ["qwen2.5-32b-instruct-q5_k_m", "qwen2.5-32b-instruct"],
    "drafter": ["qwen2.5-32b-instruct-q4_k_m", "qwen2.5-14b-instruct", "gemma-2-27b"],
    "critic": ["qwen2.5-32b-instruct-q5_k_m", "qwen2.5-32b-instruct"],
}

OVERRIDE_WARNING = "Using a non-recommended model or critic profile may produce unpredictable results because that exact path was not explicitly validated."


def build_override_warning(role: str, selected: str, recommended: str) -> str:
    return f"Role '{role}' is using '{selected}' instead of the recommended '{recommended}'. {OVERRIDE_WARNING}"
