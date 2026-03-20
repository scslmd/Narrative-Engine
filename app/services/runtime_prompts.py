from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..schemas.inference import InferenceMessage, InferenceRequest
from ..schemas.manifest import Manifest


def build_p100_architect_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    default_model: str | None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=0.2),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=1200),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Architect role for Narrative-Engine. "
                    "Produce the P-100 story architecture foundation as deterministic markdown. "
                    "Use these exact headings in order: "
                    "## Logline, ## Core Premise, ## Story Engine, ## World Anchors, "
                    "## Character Arcs, ## Constraints, ## Open Questions."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    "Build the P-100 architect foundation from this project context.\n\n"
                    f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
                ),
            ),
        ],
        metadata={
            "mode": "pipeline_phase",
            "phase": "P-100",
            "role": "architect",
            "project_id": manifest.project_id,
            "project_name": manifest.project_name,
        },
    )


def build_p200_sequencer_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    architect_output: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if architect_output is not None:
        prompt_context["architect_output"] = architect_output
    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=0.2),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=1200),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Sequencer role for Narrative-Engine. "
                    "Produce the P-200 sequence foundation as deterministic JSON. "
                    "Return an ordered sequence plan with stable item ordering and explicit dependencies."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    "Build the P-200 sequencer foundation from this project context.\n\n"
                    f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
                ),
            ),
        ],
        metadata={
            "mode": "pipeline_phase",
            "phase": "P-200",
            "role": "sequencer",
            "project_id": manifest.project_id,
            "project_name": manifest.project_name,
        },
    )


def architect_output_path(project_dir: Path) -> Path:
    return project_dir / "exports" / "p100_architect_output.md"


def sequence_output_path(project_dir: Path) -> Path:
    return project_dir / "sequences.json"


def _runtime_prompt_context(*, manifest: Manifest, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": manifest.project_id,
        "project_name": manifest.project_name,
        "genre": manifest.config.genre,
        "tone_profile": manifest.config.tone_profile,
        "pov": manifest.config.pov,
        "primary_language": manifest.config.primary_language,
        "secondary_language": manifest.config.secondary_language,
        "story_structure": manifest.config.story_structure,
        "constraints": list(manifest.constraints),
        "premise_text": _effective_premise_text(manifest, payload),
        "job_payload": dict(payload),
    }


def _effective_premise_text(manifest: Manifest, payload: dict[str, Any]) -> str | None:
    premise_override = str(payload.get("premise_text") or "").strip()
    if premise_override:
        return premise_override
    return manifest.premise_text


def _coerce_float(value: Any, *, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
