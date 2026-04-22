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


def build_p300_drafter_request(
    *,
    manifest: Manifest,
    payload: dict[str, Any],
    sequence_output: str | None = None,
    architect_output: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if sequence_output is not None:
        prompt_context["sequence_output"] = sequence_output
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
                    "You are the Drafter role for Narrative-Engine. "
                    "Produce the P-300 chapter-1 draft as deterministic markdown. "
                    "Preserve chapter flow, continuity, and stable section ordering."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    "Build the P-300 drafter foundation from this project context.\n\n"
                    f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
                ),
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
        temperature=_coerce_float(payload.get("temperature"), default=0.1),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=1400),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the Compiler role for Narrative-Engine. "
                    "Produce the P-400 story bible snapshot as deterministic JSON. "
                    "Return one JSON object with these top-level keys in stable order: "
                    "project, premise, world_anchors, character_threads, continuity_notes, open_questions."
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


def build_import_analysis_request(
    *,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for story analysis/structure extraction.

    The LLM should return a JSON object matching StoryImportAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output.
    Truncates story_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = story_text[:24_000]
    context_parts = []
    if genre_hint:
        context_parts.append(f"Genre hint: {genre_hint}")
    if tone_hint:
        context_parts.append(f"Tone hint: {tone_hint}")
    context = "\n".join(context_parts)

    system_prompt = (
        "You are a story analysis AI for Narrative-Engine. You analyze completed stories "
        "and extract structured metadata that fills out all project elements.\n\n"
        "Your output MUST be valid JSON with these exact top-level keys:\n"
        "- project_name (string, required)\n"
        "- genre (string, required)\n"
        "- tone (string, required)\n"
        "- pov (string: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER)\n"
        "- story_structure (string: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER)\n"
        "- premise (string, required)\n"
        "- logline (string, required)\n"
        "- thematic_spine (string, required)\n"
        "- emotional_promise (string, required)\n"
        "- target_audience (string, required)\n"
        "- complexity_level (string, required: LOW, MEDIUM, HIGH)\n"
        "- characters (array of objects: each with name, role, archetype, external_goal, internal_need, core_fear, primary_strength, fatal_flaw, backstory, voice_notes, change_axis, contradictions, secrets, values, taboos, continuity_facts)\n"
        "- world_bible (array of objects: each with entry_type, title, summary, canonical_facts, related_character_ids)\n"
        "- story_arcs (array of objects: each with name, summary, stage_map, tags)\n"
        "- sequences (array of objects: each with title, summary, chapters)\n"
        "- narrative_constraints (array of strings)\n"
        "- success_definition (string)\n"
        "- raw_story_text (string)\n\n"
        "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
    )

    user_content = f"Analyze this completed story and extract all structured metadata:\n\n{truncated_text}"
    if context:
        user_content += f"\n\nAdditional context:\n{context}"

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "story_import",
            "role": "import_analyzer",
        },
    )


def build_brain_dump_organize_request(
    *,
    raw_text: str,
    default_model: str | None,
) -> InferenceRequest:
    truncated_text = raw_text[:50_000]

    system_prompt = (
        "You are a story development assistant for Narrative-Engine. "
        "Your job is to organize a writer's brain dump into structured categories.\n\n"
        "Read the raw text carefully and categorize each distinct idea/segment into one "
        "of these categories:\n"
        "- character: character names, personalities, backstories, motivations\n"
        "- location: settings, places, environments, worlds\n"
        "- plot_point: plot events, twists, story beats, turning points\n"
        "- theme: themes, motifs, symbolism, underlying messages\n"
        "- conflict: conflicts, tensions, antagonistic forces\n"
        "- world_building: lore, magic systems, technology, cultures, history\n"
        "- dialogue: memorable quotes, conversations, speech patterns\n"
        "- relationship: character relationships, dynamics, connections\n"
        "- object: important items, artifacts, symbols, props\n"
        "- rule: world rules, constraints, laws, limitations\n\n"
        "Return ONLY valid JSON with these exact keys (all arrays must be present even if empty):\n"
        "character, location, plot_point, theme, conflict, world_building, dialogue, "
        "relationship, object, rule\n\n"
        "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks. "
        "Each array should contain the distinct text segments that belong in that category. "
        "Preserve the original text as much as possible -- do not rewrite the ideas."
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=4096,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=truncated_text),
        ],
        metadata={
            "mode": "brain_dump_organize",
            "role": "brain_dump_organizer",
        },
    )


def architect_output_path(project_dir: Path) -> Path:
    return project_dir / "exports" / "p100_architect_output.md"


def sequence_output_path(project_dir: Path) -> Path:
    return project_dir / "sequences.json"


def chapter_output_path(project_dir: Path) -> Path:
    return project_dir / "chapter.md"


def story_bible_output_path(project_dir: Path) -> Path:
    return project_dir / "story_bible.json"


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
