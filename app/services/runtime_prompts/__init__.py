from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...schemas.inference import InferenceMessage, InferenceRequest
from ...schemas.manifest import Manifest
from ...settings import settings
from .output_paths import (
    architect_output_path,
    chapter_output_path,
    sequence_output_path,
    story_bible_output_path,
)
from .shared_fragments import (
    coerce_float as _coerce_float,
    coerce_int as _coerce_int,
    effective_premise_text as _effective_premise_text,
    runtime_prompt_context as _runtime_prompt_context,
)

if TYPE_CHECKING:
    from ..scene_context import SceneContext

# Pipeline phase prompts (core 4 kept inline)


def build_p100_architect_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    default_model: str | None,
    pattern_context: Any = None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)

    user_parts: list[str] = []
    if pattern_context is not None:
        from .guided_setup import _build_pattern_context_block
        user_parts.append(_build_pattern_context_block(pattern_context))
    user_parts.append(
        "Build the P-100 architect foundation from this project context.\n\n"
        f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
    )

    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=settings.inference_temperature("P-100")),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=settings.inference_max_tokens("P-100")),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Architect role for Narrative-Engine. "
                    "Produce the P-100 story architecture foundation as deterministic markdown.\n\n"
                    "Use these EXACT headings in this EXACT order (no extra headings, no preamble):\n"
                    "## Logline — One sentence, 20-40 words\n"
                    "## Core Premise — 2-4 sentences describing the story's engine\n"
                    "## Story Engine — What drives the plot forward (conflict mechanism)\n"
                    "## World Anchors — 3-5 immutable world facts the story cannot contradict\n"
                    "## Character Arcs — Per character: starting state to ending state\n"
                    "## Constraints — Rules the story must obey (tone, POV, themes)\n"
                    "## Open Questions — Unresolved questions to guide subsequent chapters\n\n"
                    "Return ONLY markdown with these headings. No code fences. No introduction text."
                ),
            ),
            InferenceMessage(
                role="user",
                content="\n\n".join(user_parts),
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
        temperature=_coerce_float(payload.get("temperature"), default=settings.inference_temperature("P-200")),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=settings.inference_max_tokens("P-200")),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Sequencer role for Narrative-Engine. "
                    "Produce the P-200 sequence foundation as deterministic JSON. "
                    "Return an ordered sequence plan with stable item ordering and explicit dependencies. "
                    "Return ONLY one valid JSON object. No markdown, no code fences, no commentary."
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


def build_p300_drafter_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    sequence_output: str | None = None,
    architect_output: str | None = None,
    default_model: str | None,
    chapter_id: str | None = None,
    scene_context: Any = None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if sequence_output is not None:
        prompt_context["sequence_output"] = sequence_output
    if architect_output is not None:
        prompt_context["architect_output"] = architect_output
    chapter_label = f"chapter {chapter_id}" if chapter_id else "chapter-1"

    target_words: int | None = payload.get("target_word_count")
    if target_words is None:
        target_words = getattr(getattr(manifest, "config", None), "target_word_count", None)

    system_content = (
        f"You are the Drafter role for Narrative-Engine. "
        f"Produce the P-300 {chapter_label} draft as deterministic markdown. "
        f"Preserve chapter flow, continuity, and stable section ordering. "
        "Return ONLY the chapter markdown text with no preamble and no code fences."
    )
    if target_words is not None:
        system_content += (
            f"\n\nTarget length: approximately {target_words} words.\n"
            f"Adjust detail and pacing to meet this target while maintaining story quality."
        )

    user_parts: list[str] = []
    if scene_context is not None:
        scene_str = scene_context.to_prompt_string()
        if scene_str:
            user_parts.append(scene_str)
    user_parts.append(
        "Build the P-300 drafter foundation from this project context.\n\n"
        f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
    )

    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=settings.inference_temperature("P-300")),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=settings.inference_max_tokens("P-300")),
        messages=[
            InferenceMessage(
                role="system",
                content=system_content,
                cache_control={"type": "ephemeral"},
            ),
            InferenceMessage(
                role="user",
                content="\n\n".join(user_parts),
            ),
        ],
        metadata={
            "mode": "pipeline_phase",
            "phase": "P-300",
            "role": "drafter",
            "project_id": manifest.project_id,
            "project_name": manifest.project_name,
        },
    )


def build_p400_compiler_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    architect_output: str | None = None,
    sequence_output: str | None = None,
    chapter_output: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if architect_output is not None:
        prompt_context["architect_output"] = architect_output
    if sequence_output is not None:
        prompt_context["sequence_output"] = sequence_output
    if chapter_output is not None:
        prompt_context["chapter_output"] = chapter_output
    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=settings.inference_temperature("P-400")),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=settings.inference_max_tokens("P-400")),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Compiler role for Narrative-Engine. "
                    "Produce the P-400 story bible snapshot as deterministic JSON. "
                    "Return one JSON object with these top-level keys in stable order: "
                    "project, premise, world_anchors, character_threads, continuity_notes, open_questions. "
                    "Return ONLY valid JSON (no markdown/code fences/comments)."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    "Build the P-400 compiler story bible snapshot from this project context.\n\n"
                    f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
                ),
            ),
        ],
        metadata={
            "mode": "pipeline_phase",
            "phase": "P-400",
            "role": "compiler",
            "project_id": manifest.project_id,
            "project_name": manifest.project_name,
        },
    )


# Re-exports from domain submodules


from .checker import build_critic_check_request  # noqa: F401
from .continuity_prompts import build_continuity_analysis_request  # noqa: F401
from .entity_analysis import (  # noqa: F401
    build_chapter_summarize_request,
    build_entity_intake_request,
)
from .generation import (  # noqa: F401
    build_g200_story_generation_plan_request,
    build_g300_chapter_generation_request,
    build_g350_canon_repair_request,
    build_g400_manuscript_assembly_request,
)
from .guided_setup import (  # noqa: F401
    _build_pattern_context_block,
    build_cascade_extraction_request,
    build_generate_description_request,
    build_guided_setup_request,
    build_relationship_extraction_request,
)
from .import_prompts import build_import_analysis_request  # noqa: F401
from .manuscript_assist import (  # noqa: F401
    build_m500_draft_generation_request,
    build_m500_manuscript_assist_request,
    build_m550_manuscript_repair_request,
)
from .multi_pass import (  # noqa: F401
    build_arc_detection_request,
    build_character_consolidation_request,
    build_chunk_analysis_request,
    build_structure_detection_request,
    build_world_bible_consolidation_request,
)
from .narrative_analysis import (  # noqa: F401
    build_mythos_analysis_request,
    build_narrative_analysis_request,
)
from .planning import (  # noqa: F401
    build_brain_dump_organize_request,
    build_draft_brief_request,
    build_planning_consolidation_request,
)
