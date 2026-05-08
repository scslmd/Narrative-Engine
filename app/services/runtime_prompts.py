from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..schemas.inference import InferenceMessage, InferenceRequest
from ..schemas.manifest import Manifest
from ..schemas.pattern_extraction import PatternExtractionAnalysis
from ..settings import settings

if TYPE_CHECKING:
    from .scene_context import SceneContext
    from app.schemas.generation import CanonGenerationPacket, GenerationPlan
    from app.schemas.manuscript_assist import ManuscriptAssistPacket


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
        user_parts.append(_build_pattern_context_block(pattern_context))
    user_parts.append(
        "Build the P-100 architect foundation from this project context.\n\n"
        f"{json.dumps(prompt_context, ensure_ascii=True, indent=2, sort_keys=True)}"
    )

    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=settings.inference_temperature("P-100")),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=1200),
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
    chapter_id: str | None = None,
    scene_context: Any = None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if sequence_output is not None:
        prompt_context["sequence_output"] = sequence_output
    if architect_output is not None:
        prompt_context["architect_output"] = architect_output
    chapter_label = f"chapter {chapter_id}" if chapter_id else "chapter-1"

    # Resolve target_word_count: payload override > manifest default
    target_words: int | None = payload.get("target_word_count")
    if target_words is None:
        target_words = getattr(getattr(manifest, "config", None), "target_word_count", None)

    system_content = (
        f"You are the Drafter role for Narrative-Engine. "
        f"Produce the P-300 {chapter_label} draft as deterministic markdown. "
        f"Preserve chapter flow, continuity, and stable section ordering."
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
        max_tokens=_coerce_int(payload.get("max_tokens"), default=8000),
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


def build_g200_story_generation_plan_request(
    packet: CanonGenerationPacket,
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-200"),
        max_tokens=4000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the generation planner. Produce deterministic JSON with premise, logline, "
                    "chapter plans, canon obligations, and intentional differences."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(packet.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-200",
            "role": "generation_planner",
            "packet_id": packet.packet_id,
        },
    )


def build_g300_chapter_generation_request(
    packet: CanonGenerationPacket,
    plan: GenerationPlan,
    chapter_id: str,
    prior_summaries: list[str],
    default_model: str | None,
) -> InferenceRequest:
    payload = {
        "packet_id": packet.packet_id,
        "chapter_id": chapter_id,
        "premise": plan.premise,
        "logline": plan.logline,
        "canon_obligations": plan.canon_obligations,
        "intentional_differences": plan.intentional_differences,
        "characters": [item.model_dump(mode="json") for item in packet.characters],
        "world_bible": [item.model_dump(mode="json") for item in packet.world_bible],
        "continuity_threads": [item.model_dump(mode="json") for item in packet.continuity_threads],
        "prior_summaries": prior_summaries[-4:],
    }
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-300"),
        max_tokens=8000,
        messages=[
            InferenceMessage(
                role="system",
                content="Draft the chapter as markdown while preserving locked canon constraints.",
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-300",
            "role": "generation_drafter",
            "packet_id": packet.packet_id,
            "chapter_id": chapter_id,
        },
    )


def build_g350_canon_repair_request(
    packet: CanonGenerationPacket,
    artifact_text: str,
    gate_reasons: list[str],
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=0.1,
        max_tokens=4000,
        messages=[
            InferenceMessage(
                role="system",
                content="Repair canon contradictions while preserving intended story intent.",
            ),
            InferenceMessage(
                role="user",
                content=(
                    f"Gate reasons: {gate_reasons}\n"
                    f"Canon policy: {packet.canon_policy.model_dump(mode='json')}\n"
                    f"Artifact:\n{artifact_text}"
                ),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-350",
            "role": "generation_gate",
            "packet_id": packet.packet_id,
        },
    )


def build_g400_manuscript_assembly_request(
    packet: CanonGenerationPacket,
    chapter_artifacts: list[dict[str, str]],
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=0.1,
        max_tokens=6000,
        messages=[
            InferenceMessage(
                role="system",
                content="Assemble the chapter artifacts into a cohesive manuscript.",
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(
                    {
                        "packet_id": packet.packet_id,
                        "chapter_artifacts": chapter_artifacts,
                    },
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                ),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-400",
            "role": "generation_compiler",
            "packet_id": packet.packet_id,
        },
    )


def build_m500_manuscript_assist_request(
    packet: ManuscriptAssistPacket,
    default_model: str | None,
) -> InferenceRequest:
    payload = packet.model_dump(mode="json")
    return InferenceRequest(
        model=packet.model_id or default_model,
        temperature=packet.temperature if packet.temperature is not None else settings.inference_temperature("G-300"),
        max_tokens=packet.max_tokens if packet.max_tokens is not None else 4000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are a manuscript assistant for narrative editing. "
                    "Return strict JSON only: summary, suggestions[], created_branch_brief, warnings."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "manuscript_assist_phase",
            "phase": "M-500",
            "role": "manuscript_assist",
            "assist_id": packet.assist_id,
            "document_id": packet.document_id,
        },
    )


def build_m550_manuscript_repair_request(
    packet: ManuscriptAssistPacket,
    gate_reasons: list[str],
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=packet.model_id or default_model,
        temperature=0.1,
        max_tokens=3000,
        messages=[
            InferenceMessage(
                role="system",
                content="Repair manuscript assist output to satisfy canon and continuity constraints.",
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(
                        {
                            "assist_id": packet.assist_id,
                            "project_id": packet.project_id,
                            "document_id": packet.document_id,
                            "assist_kind": packet.assist_kind.value
                            if hasattr(packet.assist_kind, "value")
                            else str(packet.assist_kind),
                            "gate_reasons": gate_reasons,
                        "instruction": packet.instruction,
                        "text_range": packet.text_range.model_dump(mode="json")
                        if packet.text_range is not None
                        else None,
                    },
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                ),
            ),
        ],
        metadata={
            "mode": "manuscript_assist_phase",
            "phase": "M-550",
            "role": "manuscript_assist_repair",
            "assist_id": packet.assist_id,
            "document_id": packet.document_id,
        },
    )


def build_m500_draft_generation_request(
    packet: ManuscriptAssistPacket,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for full-content draft generation.

    Produces a creative prompt that generates complete prose content
    matching the brief and canon context. Returns strict JSON with
    full_content, summary, and warnings keys.
    """
    payload = {
        "assist_id": packet.assist_id,
        "project_id": packet.project_id,
        "document_id": packet.document_id,
        "instruction": packet.instruction,
        "document_title": packet.document_title,
        "document_content": packet.document_content,
    }

    system_prompt = (
        "You are a draft generator for narrative fiction. "
        "Generate complete prose content matching the brief and context provided.\n\n"
        "Return strict JSON only with these keys:\n"
        "{\n"
        '  "full_content": "<complete chapter prose in markdown>",\n'
        '  "summary": "<1-2 sentence summary of what was written>",\n'
        '  "warnings": ["<any continuity or quality concerns>"]\n'
        "}\n\n"
        "Write engaging, complete prose. Do not outline or summarize — write the actual draft.\n"
        "Use markdown formatting for dialogue and scene breaks."
    )

    return InferenceRequest(
        model=packet.model_id or default_model,
        temperature=packet.temperature if packet.temperature is not None else 0.7,
        max_tokens=packet.max_tokens if packet.max_tokens is not None else 8000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "manuscript_assist_phase",
            "phase": "M-500",
            "role": "draft_generator",
            "assist_id": packet.assist_id,
            "document_id": packet.document_id,
        },
    )


def build_import_analysis_request(
    *,
    story_text: str,
    genre_hint: str | None = None,
    tone_hint: str | None = None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for high-level single-pass story analysis.

    Single-pass import is intentionally limited to high-level artifacts.
    It should not attempt chapter-level planning synthesis.
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
        "and extract high-level structured metadata.\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys. The keys below are the ONLY valid JSON keys.\n\n"
        '{\n'
        '  "project_name": "<string>",\n'
        '  "genre": "<string>",\n'
        '  "tone": "<string>",\n'
        '  "pov": "<enum>",\n'
        '  "story_structure": "<enum>",\n'
        '  "premise": "<string>",\n'
        '  "logline": "<string>",\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "target_audience": "<string>",\n'
        '  "complexity_level": "<enum>",\n'
        '  "characters": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "role": "<enum>",\n'
        '      "archetype": "<string>",\n'
        '      "external_goal": "<string>",\n'
        '      "internal_need": "<string>",\n'
        '      "core_fear": "<string>",\n'
        '      "primary_strength": "<string>",\n'
        '      "fatal_flaw": "<string>",\n'
        '      "backstory": "<string>",\n'
        '      "voice_notes": "<string>",\n'
        '      "change_axis": "<string>",\n'
        '      "contradictions": [],\n'
        '      "secrets": [],\n'
        '      "values": [],\n'
        '      "taboos": [],\n'
        '      "continuity_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "world_bible": [\n'
        '    {\n'
        '      "entry_type": "<enum>",\n'
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "canonical_facts": [],\n'
        '      "related_character_ids": []\n'
        '    }\n'
        '  ],\n'
        '  "story_arcs": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "stage_map": [],\n'
        '      "tags": []\n'
        '    }\n'
        '  ],\n'
        '  "sequences": [\n'
        '    {\n'
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "chapters": [],\n'
        '      "provenance_note": "<string>",\n'
        '      "confidence_score": "<0.0 to 1.0>"\n'
        '    }\n'
        '  ],\n'
        '  "narrative_constraints": [],\n'
        '  "success_definition": "<string>"\n'
        '}\n\n'
        "CRITICAL RULES FOR FIELDS:\n"
        "- You MUST use the EXACT key names shown above. Do not use synonyms like name->title, description->summary, etc.\n"
        "- Arrays (contradictions, secrets, values, taboos, continuity_facts, canonical_facts, related_character_ids, stage_map, tags, chapters) MUST be JSON arrays, even if empty [].\n"
        "- If you cannot infer a value, use empty string \"\" for strings or [] for arrays. Do NOT skip keys.\n"
        "- Do NOT fabricate chapter_summaries, scene plans, beat plans, or scene-by-scene breakdowns in single-pass mode.\n"
        "- sequences are optional high-level movements only. If you include them, keep them coarse and use estimated chapter labels only when the text makes them clear.\n\n"
        "POV IDENTIFICATION GUIDE:\n"
        "- FIRST: Narrator uses \"I/me/my\". Reader only knows what narrator knows.\n"
        "- SECOND: Narrator addresses as \"you\". Rare.\n"
        "- THIRD_LIMITED: Uses \"he/she/they\" but reveals one character's thoughts. Most common.\n"
        "- THIRD_OMNI: Uses \"he/she/they\" and knows multiple characters' thoughts, sometimes commenting.\n"
        "- THIRD_OBJECTIVE: Uses \"he/she/they\" and reports only observable actions/dialogue. No internal thoughts.\n"
        "- THIRD_MULTIPLE: Uses \"he/she/they\" and alternates internal access between characters.\n"
        "- OTHER: Does not fit above.\n\n"
        "STORY STRUCTURE GUIDE:\n"
        "- THREE_ACT: Three-part (setup/confrontation/resolution) with midpoint. Most common. DEFAULT when unsure.\n"
        "- HERO_JOURNEY: Distinct stages: ordinary world -> call -> refusal -> mentor -> crossing threshold -> tests -> approach -> ordeal -> reward -> road back -> resurrection -> return.\n"
        "- SAVE_THE_CAT: Clear external goal, escalating obstacles, victory. Often episodic.\n"
        "- FREYTAGS_PYRAMID: Exposition -> rising action -> climax -> falling action -> denouement.\n"
        "- KISHOTENKETSU: Four acts without conflict: intro -> development -> twist -> reconciliation.\n"
        "- FICHTEAN_CURVE: Series of escalating crises. Starts mid-action.\n"
        "- SEVEN_POINT_STRUCTURE: Hook -> plot turn 1 -> puzzle 1 -> midpoint -> puzzle 2 -> plot turn 2 -> resolution.\n"
        "- SEVEN_KEY_STEPS: Similar to seven-point, emphasis on turning points.\n"
        "- SNOWFLAKE_METHOD: Expands from sentence to chapters to scenes.\n"
        "- BRAINDUMP: Fragmented, non-linear, stream-of-consciousness.\n"
        "- OTHER: Does not fit above.\n\n"
        "FIELD VALUE RULES:\n"
        "- pov: EXACT match to FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER\n"
        "- story_structure: EXACT match to SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER\n"
        "- complexity_level: exactly LOW, MEDIUM, or HIGH\n"
        "- genre: title case (e.g., \"Fantasy\", \"Science Fiction\")\n"
        "- role: exactly one of protagonist, antagonist, mentor, deuteragonist, foil, supporting, minor\n\n"
        'JSON OUTPUT FORMAT:\n'
        '- Return ONLY the raw JSON object. No markdown code fences. No explanation text.\n'
        '- Use "null" for fields you cannot determine, not empty strings (except for strings that must have content — use "" only when a string is expected but empty).\n'
        '- Every array field must be [] when empty, never omitted.\n'
        '- Do not use "description" anywhere — use "summary" for world_bible entries and "description" is not a valid key.\n'
        '- Do not use "name" for sequences — use "title" instead.\n'
        '- sequence confidence_score must be between 0.0 and 1.0.\n'
        '- sequence provenance_note should briefly say why you are confident, e.g. "single-pass high-level inference from opening chapters".\n\n'
        "CHARACTER EXTRACTION RULES:\n"
        "- Include every character with meaningful presence, not just named ones.\n"
        "- For unnamed characters, use descriptive names like \"the old guard,\" \"the merchant.\"\n"
        "- role is critical: correctly identify protagonist (drives plot) and antagonist (opposes protagonist).\n\n"
        "VALIDATION CHECKLIST (check before returning):\n"
        "1. All required keys present, no extra top-level keys.\n"
        "2. characters array is non-empty, every character has name and role.\n"
        "3. pov and story_structure are exact enum matches.\n"
        "4. All array fields (contradictions, secrets, values, taboos, continuity_facts, canonical_facts, stage_map, tags, chapters) are actual JSON arrays [].\n"
        "5. world_bible entries use entry_type and title (not name/description).\n"
        "6. story_arcs use summary (not description), stage_map, tags (not type).\n"
        "7. sequences use title (not name), summary (not description).\n"
        "8. Do not return chapter_summaries in this mode.\n\n"
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


def build_planning_consolidation_request(
    *,
    structure_json: str,
    chapter_summaries_json: str,
    story_arcs_json: str,
    character_roster_json: str,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for multi-pass planning synthesis.

    This phase refines chapter planning and sequence grouping from chapter-level evidence.
    """
    system_prompt = (
        "You are a planning synthesizer for Narrative-Engine. "
        "Your job is to convert chapter-level analysis into reliable planning scaffolding.\n\n"
        "You will receive detected structure, chapter summaries, narrative arcs, and a character roster.\n"
        "You must synthesize:\n"
        "1. sequence groupings that cover the full analyzed story without gaps or duplicates\n"
        "2. chapter planning summaries with objective, conflict, stakes, continuity requirements, and unresolved questions\n"
        "3. trust metadata for every synthesized planning artifact\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        "{\n"
        '  "sequences": [\n'
        "    {\n"
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "chapters": [],\n'
        '      "provenance_note": "<string>",\n'
        '      "confidence_score": "<0.0 to 1.0>"\n'
        "    }\n"
        "  ],\n"
        '  "chapter_summaries": [\n'
        "    {\n"
        '      "chapter_id": "<string>",\n'
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "section_type": "<string>",\n'
        '      "analysis_status": "<complete | partial_import | analysis_failed>",\n'
        '      "objective": "<string>",\n'
        '      "conflict": "<string>",\n'
        '      "stakes": "<string>",\n'
        '      "active_character_names": [],\n'
        '      "continuity_requirements": [],\n'
        '      "unresolved_questions": [],\n'
        '      "plot_events": [],\n'
        '      "estimated_word_count": "<integer or null>",\n'
        '      "provenance_note": "<string>",\n'
        '      "confidence_score": "<0.0 to 1.0>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "- Every chapter_id in sequences must exist in chapter_summaries.\n"
        "- Every analyzed chapter must appear exactly once across all sequences.\n"
        "- Do not invent new chapter_ids.\n"
        "- Preserve analysis_status from the supplied chapter evidence. Do not upgrade failed evidence to complete.\n"
        "- When evidence is weak, lower confidence_score instead of pretending certainty.\n"
        "- provenance_note must briefly explain whether the item comes from direct chapter evidence, partial evidence, or structural synthesis.\n"
        "- Do not return markdown or prose outside the JSON object.\n"
    )

    user_content = (
        "Synthesize reliable planning scaffolding from the following evidence.\n\n"
        f"STRUCTURE:\n{structure_json}\n\n"
        f"CHAPTER SUMMARIES:\n{chapter_summaries_json}\n\n"
        f"STORY ARCS:\n{story_arcs_json}\n\n"
        f"CHARACTERS:\n{character_roster_json}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "planning_consolidation",
            "role": "planning_synthesizer",
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


def chapter_output_path(project_dir: Path, chapter_id: str | None = None) -> Path:
    """Return output path for a chapter draft.

    If chapter_id is provided, writes to chapters/{chapter_id}.md.
    Otherwise falls back to project_dir/chapter.md (backward compat).
    """
    if chapter_id:
        out_dir = project_dir / "chapters"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"{chapter_id}.md"
    return project_dir / "chapter.md"


def story_bible_output_path(project_dir: Path) -> Path:
    return project_dir / "story_bible.json"


def _build_pattern_context_block(pc: PatternExtractionAnalysis) -> str:
    """Build a pattern context block for injection into P-100 architect prompts."""
    mode = pc.generation_mode or "same_world"
    source_corpus = pc.source_corpus or "(unknown source)"

    patterns = pc.archetypal_patterns or []
    rules = pc.world_rules or []
    voice_profile = pc.voice_profile

    lines: list[str] = []

    if mode == "same_world":
        lines.append("PATTERN CONTEXT (Same World Mode):")
        lines.append(f"Source: {source_corpus}")
        lines.append("Setting: Use the established world and characters as-is.")
        lines.append("")
        lines.append("Archetypal Patterns to Follow:")
        for p in patterns:
            lines.append(f"  - {p.name}: {p.description}")
        lines.append("")
        lines.append("World Rules (must be obeyed):")
        for r in rules:
            if r.enforcement:
                lines.append(f"  - {r.rule} ({r.enforcement})")
            else:
                lines.append(f"  - {r.rule}")
        if voice_profile:
            lines.append("")
            lines.append("Voice & Style Guide:")
            vp_lines = []
            if voice_profile.narrative_voice:
                vp_lines.append(f"narrative voice: {voice_profile.narrative_voice}")
            if voice_profile.sentence_rhythm:
                vp_lines.append(f"sentence rhythm: {voice_profile.sentence_rhythm}")
            if voice_profile.descriptive_density:
                vp_lines.append(f"descriptive density: {voice_profile.descriptive_density}")
            if voice_profile.humor_level:
                vp_lines.append(f"humor level: {voice_profile.humor_level}")
            if voice_profile.emotional_temperature:
                vp_lines.append(f"emotional temperature: {voice_profile.emotional_temperature}")
            lines.extend(vp_lines)
        lines.append("")
        lines.append("INSTRUCTION: Follow these patterns when building the P-100 architect foundation. ")
        lines.append("Your output must respect these world rules, voice guidelines, and archetypal patterns.")

    elif mode == "new_characters":
        lines.append("PATTERN CONTEXT (New Characters Mode):")
        lines.append(f"Source: {source_corpus}")
        lines.append("Setting: Same world, but create original characters who fulfill these archetypal roles.")
        lines.append("")
        lines.append("Archetypal Roles to Fill:")
        for p in patterns:
            if p.character_type:
                lines.append(f"  - {p.name} ({p.character_type}): {p.description}")
            else:
                lines.append(f"  - {p.name}: {p.description}")
        lines.append("")
        lines.append("World Rules (must be obeyed):")
        for r in rules:
            if r.enforcement:
                lines.append(f"  - {r.rule} ({r.enforcement})")
            else:
                lines.append(f"  - {r.rule}")
        lines.append("")
        lines.append("INSTRUCTION: Create new characters who fill these archetypal roles in this world. ")
        lines.append("Your architect output must respect the world rules and populate the archetypal structure.")

    elif mode == "transposed":
        lines.append("PATTERN CONTEXT (Transposed Mode):")
        lines.append(f"Source: {source_corpus}")
        lines.append("Your task: Map these archetypal patterns and narrative structures to a new setting.")
        lines.append("")
        lines.append("Patterns to Transpose:")
        for p in patterns:
            lines.append(f"  - {p.name}: {p.description}")
        narrative_structures = pc.narrative_structures or []
        if narrative_structures:
            lines.append("")
            lines.append("Narrative Structures:")
            for ns in narrative_structures:
                if ns.phases:
                    lines.append(f"  - {ns.name}: {' -> '.join(ns.phases)}")
                else:
                    lines.append(f"  - {ns.name}")
        lines.append("")
        lines.append("Structural Rules (adapt to new world):")
        for r in rules:
            if r.enforcement:
                lines.append(f"  - {r.rule} ({r.enforcement})")
            else:
                lines.append(f"  - {r.rule}")
        lines.append("")
        lines.append("INSTRUCTION: Transpose these patterns and structures into a new setting. ")
        lines.append("Map each archetypal pattern and narrative structure to an equivalent in your new world.")

    return "\n".join(lines)


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


def build_critic_check_request(
    *,
    draft_text: str,
    character_bios: dict[str, str],
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for consistency critic check."""
    bio_lines = []
    for name, bio in character_bios.items():
        bio_lines.append(f"  {name}: {bio}")
    bios_block = "\n".join(bio_lines) if bio_lines else "  (no character profiles)"

    # Number draft lines for LLM reference (capped at 500)
    draft_lines = draft_text.split("\n")
    max_display_lines = 500
    numbered_lines = []
    for i, line in enumerate(draft_lines[:max_display_lines], 1):
        numbered_lines.append(f"{i}: {line}")
    numbered_draft = "\n".join(numbered_lines)
    if len(draft_lines) > max_display_lines:
        numbered_draft += f"\n... ({len(draft_lines) - max_display_lines} more lines truncated)"

    system_prompt = (
        "You are a consistency critic for Narrative-Engine. "
        "Check whether characters' dialogue and actions align with their defined profiles.\n\n"
        "CHECK FOR:\n"
        "  1. VOICE: Does word choice, sentence length, and vocabulary match the character?\n"
        "  2. BEHAVIOR: Do goals, fears, and traits drive the character's actions?\n"
        "  3. KNOWLEDGE: Does the character only know what they should know?\n"
        "  4. CONFLICT: Is the character's stance consistent with their values?\n\n"
        "NOT VIOLATIONS:\n"
        "  - Natural character growth or emotional shifts (these are arc progressions)\n"
        "  - Understatement or subtlety (not all feelings are expressed openly)\n"
        "  - Cultural or background-appropriate behavior differences\n\n"
        "Only flag CLEAR contradictions between profile and draft. Be conservative.\n\n"
        "For each violation, include approximate line numbers (line_start, line_end)\n"
        "and a short quoted excerpt (max 100 characters) of the problematic passage.\n"
        "Line numbers refer to the numbered draft below.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "passed": true or false,\n'
        '  "violations": [\n'
        '    {\n'
        '      "character": "<name>",\n'
        '      "issue": "<what is wrong>",\n'
        '      "suggestion": "<how to fix>",\n'
        '      "line_start": <int or null>,\n'
        '      "line_end": <int or null>,\n'
        '      "quote": "<short excerpt of the offending text>"\n'
        '    }\n'
        '  ]\n\n'
        "If the character behaves consistently with their profile, set passed=true and violations=[]."
    )

    user_content = f"CHARACTER PROFILES:\n{bios_block}\n\nDRAFT TO CHECK (line numbers for reference):\n{numbered_draft}"

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=2048,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={"mode": "consistency_critic", "role": "critic"},
    )


def build_entity_intake_request(
    *,
    candidate_name: str,
    draft_excerpt: str,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for entity intake extraction."""
    system_prompt = (
        "You are an entity extraction AI for Narrative-Engine. "
        "From the draft passage below, extract a character profile for the named character.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "name": "<string>",\n'
        '  "archetype": "<string>",\n'
        '  "goal": "<string>"\n'
        '}\n\n'
        "Infer archetype and goal from the character's dialogue, actions, and behavior in the passage."
    )

    user_content = f"Character: {candidate_name}\n\nPassage:\n{draft_excerpt}"

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.2,
        max_tokens=512,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={"mode": "entity_intake", "role": "intake_extractor"},
    )


def build_chapter_summarize_request(
    *,
    chapter_id: str,
    chapter_text: str,
    character_names: list[str],
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for chapter summarization.

    Extracts structured PriorChapterSummary from completed chapter markdown.
    Returns JSON with key_events, character_states, unresolved_threads.
    """
    truncated_text = chapter_text[:16000] if len(chapter_text) > 16000 else chapter_text

    names_block = ", ".join(character_names) if character_names else "(no known characters)"

    system_prompt = (
        "You are a chapter summarizer for Narrative-Engine. "
        "Extract structured context from the completed chapter below.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "title": "<chapter title or descriptive label>",\n'
        '  "key_events": ["<event 1>", "<event 2>"],\n'
        '  "character_states": {"<name>": "<current goal + emotional state + key change>"},\n'
        '  "unresolved_threads": ["<thread 1>"]\n'
        '}\n\n'
        "KEY EVENTS: Major plot turns, character revelations, or pivotal decisions. "
        "Each event should describe WHAT happened and WHY it matters.\n"
        "CHARACTER STATES: Current goal, emotional state, and key change since last chapter.\n"
        "UNRESOLVED THREADS: Plot threads left open that affect subsequent chapters.\n\n"
        "Extract up to 10 key events, 10 character states, and 5 unresolved threads.\n"
        "Focus on plot-critical information that would affect continuity in subsequent chapters."
    )

    user_content = (
        f"Chapter: {chapter_id}\n"
        f"Known characters: {names_block}\n\n"
        f"CHAPTER TEXT:\n{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=2000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "chapter_summarizer",
            "role": "summarizer",
            "chapter_id": chapter_id,
        },
    )


def build_narrative_analysis_request(
    *,
    story_text: str,
    source_corpus: str | None = None,
    generation_mode: str = "same_world",
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for narrative pattern extraction.

    The LLM should return a JSON object matching PatternExtractionAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output with patterns and entities.
    Truncates story_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = story_text[:24_000]
    corpus_hint = (
        f"Source tradition hint: {source_corpus}"
        if source_corpus
        else "AI should identify the source tradition from the text."
    )

    system_prompt = (
        "You are a narrative analysis AI for Narrative-Engine. You analyze narrative texts "
        "and extract storytelling DNA — archetypal patterns, narrative structure, voice profile, "
        "thematic constraints, world rules, and symbolic motifs.\n\n"
        f"{corpus_hint}\n\n"
        f"Generation mode: {generation_mode}\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "source_type": "narrative",\n'
        '  "source_corpus": "<string - identified tradition or author>",\n'
        '  "generation_mode": "<same_world | new_characters | transposed>",\n'
        '  "archetypal_patterns": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "description": "<string>",\n'
        '      "character_type": "<string>",\n'
        '      "narrative_beats": [],\n'
        '      "examples_from_text": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_structures": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "phases": [],\n'
        '      "tension_curve": "<string>",\n'
        '      "resolution_type": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "world_rules": [\n'
        '    {\n'
        '      "rule": "<string>",\n'
        '      "enforcement": "<string>",\n'
        '      "exceptions": []\n'
        '    }\n'
        '  ],\n'
        '  "symbolic_motifs": [\n'
        '    {\n'
        '      "symbol": "<string>",\n'
        '      "meaning": "<string>",\n'
        '      "narrative_function": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "tone_and_voice_direction": "<string>",\n'
        '  "narrative_pattern": {\n'
        '    "pacing": "<string>",\n'
        '    "chapter_structure": "<string>",\n'
        '    "conflict_type": "<string>",\n'
        '    "dialogue_style": "<string>",\n'
        '    "scene_transition": "<string>"\n'
        '  },\n'
        '  "voice_profile": {\n'
        '    "narrative_voice": "<string>",\n'
        '    "sentence_rhythm": "<string>",\n'
        '    "descriptive_density": "<string>",\n'
        '    "humor_level": "<string>",\n'
        '    "emotional_temperature": "<string>"\n'
        '  },\n'
        '  "thematic_constraints": [\n'
        '    {\n'
        '      "theme": "<string>",\n'
        '      "moral_stance": "<string>",\n'
        '      "recurring_questions": [],\n'
        '      "forbidden_elements": []\n'
        '    }\n'
        '  ],\n'
        '  "key_entities": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "entity_type": "<character | location | concept | force>",\n'
        '      "archetype": "<string>",\n'
        '      "domain_or_power": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "entity_relationships": [\n'
        '    {\n'
        '      "source": "<string>",\n'
        '      "target": "<string>",\n'
        '      "relationship_type": "<string>",\n'
        '      "description": "<string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Focus on PATTERNS and STRUCTURES, not just cataloging entities. "
        "Extract the storytelling DNA — how stories are told in this tradition, "
        "what narrative rules govern them, what archetypal journeys characters undertake.\n\n"
        'JSON STRUCTURE RULES:\n'
        '- All arrays must be JSON arrays [], not strings.\n'
        '- Use null (not empty string) for missing optional fields where shown.\n'
        '- Do not include trailing commas in JSON objects or arrays.\n'
        '- The "generation_mode" field must exactly match: "same_world", "new_characters", or "transposed".\n\n'
        "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
    )

    user_content = (
        f"Analyze the following narrative text and extract its storytelling DNA, "
        f"archetypal patterns, narrative structures, world rules, voice profile, "
        f"and symbolic motifs:\n\n"
        f"{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "narrative_extraction",
            "role": "narrative_analyzer",
            "source": "narrative-analysis",
        },
    )


def build_mythos_analysis_request(
    *,
    mythos_text: str,
    source_corpus: str | None = None,
    generation_mode: str = "same_world",
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for mythos pattern extraction.

    The LLM should return a JSON object matching MythosExtractionAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output with patterns and entities.
    Truncates mythos_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = mythos_text[:24_000]
    corpus_hint = (
        f"Source tradition hint: {source_corpus}"
        if source_corpus
        else "AI should identify the source tradition from the text."
    )

    system_prompt = (
        "You are a mythology analysis AI for Narrative-Engine. You analyze mythological texts "
        "and extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs.\n\n"
        f"{corpus_hint}\n\n"
        f"Generation mode: {generation_mode}\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "source_corpus": "<string - identified tradition, e.g., Greek Mythology>",\n'
        '  "generation_mode": "<same_world | transposed | pure_pattern>",\n'
        '  "archetypal_patterns": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "description": "<string>",\n'
        '      "character_type": "<string>",\n'
        '      "narrative_beats": [],\n'
        '      "examples_from_text": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_structures": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "phases": [],\n'
        '      "tension_curve": "<string>",\n'
        '      "resolution_type": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "cosmic_rules": [\n'
        '    {\n'
        '      "rule": "<string>",\n'
        '      "enforcement": "<string>",\n'
        '      "exceptions": []\n'
        '    }\n'
        '  ],\n'
        '  "symbolic_motifs": [\n'
        '    {\n'
        '      "symbol": "<string>",\n'
        '      "meaning": "<string>",\n'
        '      "narrative_function": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "tone_and_voice_direction": "<string>",\n'
        '  "key_entities": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "entity_type": "<deity | location | concept | force>",\n'
        '      "archetype": "<string>",\n'
        '      "domain_or_power": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "entity_relationships": [\n'
        '    {\n'
        '      "source": "<string>",\n'
        '      "target": "<string>",\n'
        '      "relationship_type": "<string>",\n'
        '      "description": "<string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Focus on PATTERNS and STRUCTURES, not just cataloging entities. "
        "Extract the storytelling DNA — how stories are told in this tradition, "
        "what narrative rules govern them, what archetypal journeys characters undertake.\n\n"
        'JSON STRUCTURE RULES:\n'
        '- All arrays must be JSON arrays [], not strings.\n'
        '- Use null (not empty string) for missing optional fields where shown.\n'
        '- Do not include trailing commas in JSON objects or arrays.\n'
        '- The "generation_mode" field must exactly match: "same_world", "transposed", or "pure_pattern".\n'
        '- The "entity_type" field must be one of: "deity", "location", "concept", "force".\n\n'
    )

    user_content = (
        f"Analyze the following mythological text and extract its archetypal patterns, "
        f"narrative structures, cosmic rules, and symbolic motifs:\n\n"
        f"{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "mythos_extraction",
            "role": "mythos_analyzer",
        },
    )


def build_draft_brief_request(
    *,
    model: str,
    chapter_id: str,
    chapter_title: str,
    chapter_summary: str,
    continuity_threads: str | None = None,
    continuity_state: str | None = None,
    character_roster: str | None = None,
    world_constraints: str | None = None,
    voice_guidance: str | None = None,
    max_tokens: int = 12000,
) -> InferenceRequest:
    """Build inference request for drafting brief generation.

    Generates a writer-facing draft brief for a single chapter, including
    objective, emotional turn, continuity obligations, callbacks, forbidden
    contradictions, and voice guidance.
    """
    system_prompt = (
        "You are a drafting brief generator for Narrative-Engine. "
        "Your job is to create a writer-facing draft brief for a single chapter.\n\n"
        "The brief should include:\n"
        "1. **Objective**: What this chapter must accomplish narratively\n"
        "2. **Emotional turn**: The emotional arc from beginning to end of the chapter\n"
        "3. **Continuity obligations**: What MUST be consistent with prior chapters (threads, character states, world facts)\n"
        "4. **Required callbacks**: Specific threads or events that should be referenced or advanced\n"
        "5. **Forbidden contradictions**: Things that must NOT happen (based on established continuity)\n"
        "6. **Voice guidance**: Tone, POV, and stylistic direction\n\n"
        "This is a WRITER-FACING BRIEF, not an analysis summary. It should be actionable and specific.\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        "{\n"
        '  "objective": "<string>",\n'
        '  "emotional_turn": "<string>",\n'
        '  "continuity_obligations": ["<obligation>"],\n'
        '  "required_callbacks": ["<callback>"],\n'
        '  "forbidden_contradictions": ["<contradiction to avoid>"],\n'
        '  "voice_guidance": "<string>"\n'
        "}\n\n"
        "RULES:\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas in JSON objects or arrays.\n"
        "- objective should be a single actionable sentence describing what the chapter achieves.\n"
        "- emotional_turn should describe the emotional journey from start to end of the chapter.\n"
        "- continuity_obligations must list specific facts, states, or threads that MUST carry forward.\n"
        "- required_callbacks should reference specific events, threads, or character moments to advance.\n"
        "- forbidden_contradictions should list things that would break established continuity.\n"
        "- voice_guidance should cover tone, POV, and stylistic direction for this chapter.\n\n"
    )

    user_parts: list[str] = []
    user_parts.append(f"Chapter: {chapter_id} — {chapter_title}")
    if chapter_summary.strip():
        user_parts.append(f"Summary: {chapter_summary}")
    user_parts.append("")

    if continuity_threads and continuity_threads.strip():
        user_parts.append(f"ACTIVE CONTINUITY THREADS:\n{continuity_threads}\n")
    if continuity_state and continuity_state.strip():
        user_parts.append(f"CONTINUITY STATE AT THIS BOUNDARY:\n{continuity_state}\n")
    if character_roster and character_roster.strip():
        user_parts.append(f"CHARACTERS ACTIVE IN THIS CHAPTER:\n{character_roster}\n")
    if world_constraints and world_constraints.strip():
        user_parts.append(f"WORLD CONSTRAINTS:\n{world_constraints}\n")
    if voice_guidance and voice_guidance.strip():
        user_parts.append(f"NARRATIVE VOICE DIRECTION:\n{voice_guidance}\n")

    user_content = "\n".join(user_parts)

    return InferenceRequest(
        model=str(model or "").strip() or None,
        temperature=0.2,
        max_tokens=max_tokens,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "drafting_consolidation",
            "role": "draft_brief_generator",
            "chapter_id": chapter_id,
        },
    )


def build_continuity_analysis_request(
    *,
    model: str,
    chapter_summaries: list[str],
    planning_json: str | None = None,
    arcs_json: str | None = None,
    characters_json: str | None = None,
    max_tokens: int = 16000,
) -> InferenceRequest:
    """Build inference request for continuity analysis.

    Analyzes ordered chapter summaries + planning/arcs/characters to identify
    narrative threads, state snapshots at each chapter boundary, and contradictions.
    """
    system_prompt = (
        "You are a continuity analyzer for Narrative-Engine. "
        "Your job is to examine the ordered chapters and identify:\n"
        "1. Narrative threads that span multiple chapters (active, resolved, or dropped)\n"
        "2. State snapshots at each chapter boundary (what's true about characters/world/questions after each chapter)\n"
        "3. Overall contradictions or unresolved questions across the story\n\n"
        "You must NOT invent new chapter IDs or rewrite chapter order. Work only with what is provided.\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        "{\n"
        '  "threads": [\n'
        "    {\n"
        '      "thread_id": "<string>",\n'
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "status": "<active | resolved | dropped>",\n'
        '      "chapter_ids": ["<chapter_id>"],\n'
        '      "character_ids": [],\n'
        '      "evidence": ["<quote or reference>"],\n'
        '      "confidence_score": <0.0 to 1.0>\n'
        "    }\n"
        "  ],\n"
        '  "states": [\n'
        "    {\n"
        '      "state_id": "<string>",\n'
        '      "chapter_id": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "active_threads": ["<thread_id>"],\n'
        '      "resolved_threads": [],\n'
        '      "character_states": {"<name>": "<state description>"},\n'
        '      "world_facts": ["<fact established>"],\n'
        '      "unresolved_questions": ["<question>"],\n'
        '      "contradictions": [],\n'
        '      "status": "<complete | partial>",\n'
        '      "confidence_score": <0.0 to 1.0>\n'
        "    }\n"
        "  ],\n"
        '  "contradictions": ["<cross-chapter contradiction>"],\n'
        '  "unresolved_questions": ["<overarching question>"],\n'
        '  "overall_confidence": <0.0 to 1.0>,\n'
        '  "status": "<complete | partial | analysis_failed>"\n'
        "}\n\n"
        "RULES:\n"
        "- chapter_ids in threads and states MUST reference only the chapter IDs provided below.\n"
        "- Do NOT invent new chapter IDs.\n"
        "- Each state must correspond to exactly one chapter boundary.\n"
        "- Thread status must be one of: active, resolved, dropped.\n"
        "- State status must be one of: complete, partial.\n"
        "- Overall status must be one of: complete, partial, analysis_failed.\n"
        "- evidence arrays should contain brief quotes or references supporting the finding.\n"
        "- confidence_score must be between 0.0 and 1.0.\n"
        "- contradictions should describe cross-chapter inconsistencies (e.g., character state changes without explanation).\n"
        "- unresolved_questions should list overarching questions left open by the story.\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas in JSON objects or arrays.\n\n"
    )

    user_parts: list[str] = []
    user_parts.append("ORDERED CHAPTER SUMMARIES:\n")
    for i, summary in enumerate(chapter_summaries):
        user_parts.append(f"{i + 1}. {summary}")
    user_parts.append("")

    if planning_json:
        user_parts.append(f"PLANNING SYNTHESIS:\n{planning_json}\n")
    if arcs_json:
        user_parts.append(f"ARC ANALYSIS:\n{arcs_json}\n")
    if characters_json:
        user_parts.append(f"CHARACTER ROSTER:\n{characters_json}\n")

    user_content = "\n".join(user_parts)

    return InferenceRequest(
        model=str(model or "").strip() or None,
        temperature=0.1,
        max_tokens=max_tokens,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "continuity_analysis",
            "role": "continuity_analyzer",
        },
    )


def build_structure_detection_request(
    *,
    story_text: str,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for story structure detection (Phase 1).

    Scans text for TOC, chapter boundaries, section types.
    Extracts character/location/POV hints from chapter titles and headers.
    Uses first 40,000 chars of text (structure typically in opening portion).
    """
    truncated_text = story_text[:40_000]

    system_prompt = (
        "You are a story structure analyzer for Narrative-Engine. "
        "Your job is to detect the structural organization of a story.\n\n"
        "Scan the provided text and identify:\n"
        "1. Table of contents, title page, or structural markers\n"
        "2. Chapter boundaries (by line number and character offset)\n"
        "3. Section types: prologue, chapter, part, epilogue, appendix\n"
        "4. Character names, locations, POV hints from chapter titles/headers\n"
        "5. Estimated word count per section\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "project_name": "<string>",\n'
        '  "total_estimated_words": <int>,\n'
        '  "structure_type": "<traditional_novel | short_story | anthology | non_fiction>",\n'
        '  "chapters": [\n'
        '    {\n'
        '      "id": "<string, e.g. prologue, chapter-1, epilogue>",\n'
        '      "title": "<string>",\n'
        '      "section_type": "<prologue | chapter | part | epilogue | appendix>",\n'
        '      "start_line": <int>,\n'
        '      "end_line": <int>,\n'
        '      "start_pos": <int, character offset>,\n'
        '      "end_pos": <int, character offset>,\n'
        '      "estimated_word_count": <int>\n'
        '    }\n'
        '  ],\n'
        '  "hints": {\n'
        '    "character_names": [],\n'
        '    "location_names": [],\n'
        '    "pov_hints": [],\n'
        '    "thematic_keywords": []\n'
        '  },\n'
        '  "narrative_voice": "<string or null>"\n'
        '}\n\n'
        "RULES:\n"
        "- Line numbers are 1-indexed.\n"
        "- Character offsets (start_pos, end_pos) are 0-indexed positions in the source text.\n"
        "- If no clear TOC exists, detect chapter headings by common patterns:\n"
        "  'Chapter X', 'Part X', Roman numerals, centered titles, section breaks.\n"
        "- If the text has no discernible structure, return structure_type='short_story'\n"
        "  with a single chapter covering the full text range.\n"
        "- Extract character names from chapter titles like 'Chapter 3: Kvothe\'s Journey'.\n"
        "- Extract POV hints like 'POV: Kvothe' or 'From Elodin\'s Perspective'.\n"
        "- Do not include trailing commas in JSON.\n"
    )

    user_content = (
        f"Detect the structure of this story. Identify chapter boundaries, section types,\n"
        f"and extract hints from chapter titles and headers.\n\n"
        f"STORY TEXT:\n{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=8000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "structure_detection",
            "role": "structure_analyzer",
        },
    )


def build_chunk_analysis_request(
    *,
    chapter_text: str,
    chapter_id: str,
    chapter_title: str,
    known_characters_json: str | None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for per-chapter analysis (Phase 2).

    Analyzes a single chapter/chunk. Prior character map passed as context
    so the LLM can update existing characters and add new ones.
    """
    system_prompt = (
        "You are a deep story analyzer for Narrative-Engine. "
        "Your job is to analyze a single chapter of a story and extract detailed information.\n\n"
        "For each character in this chapter:\n"
        "- Note if this is their first introduction or a return appearance\n"
        "- Track physical descriptions, personality traits shown through behavior\n"
        "- Record actions they take (for arc building)\n"
        "- Capture distinctive dialogue samples (max 3 short quotes)\n"
        "- Note relationships and conflicts mentioned\n"
        "- Identify emotional state, motives for their actions\n"
        "- Track character development: how they changed in this chapter\n\n"
        "For world-building:\n"
        "- Extract locations, organizations, magic systems, technology, customs\n"
        "- Record canonical facts (things stated as true in-world)\n\n"
        "For plot:\n"
        "- Summarize key events\n"
        "- Note significance: inciting_incident, turning_point, climax, resolution, development\n"
        "- Track unresolved threads opened but not resolved\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "chapter_id": "<string>",\n'
        '  "chapter_title": "<string>",\n'
        '  "section_type": "<prologue | chapter | part | epilogue | appendix>",\n'
        '  "summary": "<2-3 sentence chapter summary>",\n'
        '  "key_events": [],\n'
        '  "characters": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "aliases": [],\n'
        '      "role": "<protagonist | antagonist | mentor | deuteragonist | foil | supporting | minor>",\n'
        '      "is_first_introduction": <boolean>,\n'
        '      "physical_description": "<string>",\n'
        '      "personality_traits": [],\n'
        '      "actions_in_chunk": [],\n'
        '      "dialogue_samples": [],\n'
        '      "relationships_mentioned": [],\n'
        '      "emotional_state": "<string>",\n'
        '      "motives_observed": "<string or null>",\n'
        '      "development_notes": "<string or null>"\n'
        '    }\n'
        '  ],\n'
        '  "world_details": [\n'
        '    {\n'
        '      "entry_type": "<location | organization | magic_system | technology | custom | creature | concept>",\n'
        '      "title": "<string>",\n'
        '      "description": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "plot_events": [\n'
        '    {\n'
        '      "summary": "<string>",\n'
        '      "characters_involved": [],\n'
        '      "significance": "<inciting_incident | turning_point | climax | resolution | development>",\n'
        '      "unresolved_threads": []\n'
        '    }\n'
        '  ],\n'
        '  "thematic_elements": [],\n'
        '  "tone_shifts": [],\n'
        '  "narrative_perspective": "<string or null>"\n'
        '}\n\n'
        "RULES:\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas.\n"
        '- Role must be one of: protagonist, antagonist, mentor, deuteragonist, foil, supporting, minor.\n'
        "- If a character was already known (from prior chapters), update their info — don't mark as first introduction.\n"
        "- Dialogue samples should be short (1-2 sentences max each), showing distinctive speech patterns.\n"
    )

    user_parts: list[str] = []

    if known_characters_json:
        user_parts.append(
            "KNOWN CHARACTERS FROM PRIOR CHAPTERS (use this to identify return appearances):\n"
            f"{known_characters_json}\n\n"
        )

    user_parts.append(
        f"ANALYZE THIS CHAPTER:\n"
        f"Chapter: {chapter_title} ({chapter_id})\n\n"
        f"{chapter_text}"
    )

    user_content = "\n".join(user_parts)

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "chapter_analysis",
            "role": "chapter_analyzer",
            "chapter_id": chapter_id,
        },
    )


def build_character_consolidation_request(
    *,
    character_data_json: str,
    story_premise: str | None,
    thematic_spine: str | None,
    genre_hint: str | None,
    tone_hint: str | None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for character bible consolidation (Phase 3a).

    Merges all per-chapter character data into comprehensive profiles with:
    - Character arcs from introduction through development
    - Relationship maps between characters
    - Symbolic/thematic roles
    - Psychological depth, narrative purpose, thematic significance
    """
    context_parts: list[str] = []
    if genre_hint:
        context_parts.append(f"Genre: {genre_hint}")
    if tone_hint:
        context_parts.append(f"Tone: {tone_hint}")
    if story_premise:
        context_parts.append(f"Premise: {story_premise}")
    if thematic_spine:
        context_parts.append(f"Thematic spine: {thematic_spine}")

    system_prompt = (
        "You are a character analysis expert for Narrative-Engine. "
        "Your job is to consolidate per-chapter character data into comprehensive character profiles.\n\n"
        "For each character, produce a deep analysis covering:\n\n"
        "1. CHARACTER ARC: How they developed from introduction through the story.\n"
        "   Track their growth, regression, or stasis. What changed and what didn't?\n\n"
        "2. RELATIONSHIPS: Map their key relationships — alliances, conflicts, mentorships, romances.\n"
        "   Note how relationships evolved over the course of the story.\n\n"
        "3. PSYCHOLOGICAL DEPTH: Their inner life — motivations, fears, desires, contradictions.\n"
        "   What drives them beneath the surface? What are their blind spots?\n\n"
        "4. SYMBOLIC/THEMATIC ROLE: What they represent in the story's larger themes.\n"
        "   Are they a symbol of something? Do they embody a theme or idea?\n\n"
        "5. NARRATIVE PURPOSE: What function they serve in the story structure.\n"
        "   Catalyst, foil, mirror, harbinger, etc.\n\n"
        "6. DIALOGUE PATTERNS: Their distinctive speech style — vocabulary, rhythm, catchphrases.\n\n"
        "7. IMPACT ON OTHERS: How other characters react to them. What effect do they have?\n\n"
        "8. MOTIVES: The reasons behind their actions — stated and unstated.\n\n"
        "MERGE RULES:\n"
        "- Characters with aliases (e.g., 'Kvothe', 'Kote', 'The Crimson Fair') are the SAME person.\n"
        "  Merge all data under the primary name, list aliases in the aliases array.\n"
        "- Physical descriptions should be merged into one coherent description.\n"
        "- Personality traits should be deduplicated and consolidated.\n"
        "- Character arc should trace development across ALL chapters they appear in.\n\n"
        "OUTPUT — Return a JSON array of character profiles. Each profile has EXACTLY these keys:\n\n"
        '{\n'
        '  "name": "<string, primary name>",\n'
        '  "aliases": [],\n'
        '  "role": "<protagonist | antagonist | mentor | deuteragonist | foil | supporting | minor>",\n'
        '  "archetype": "<string>",\n'
        '  "external_goal": "<string>",\n'
        '  "internal_need": "<string>",\n'
        '  "core_fear": "<string>",\n'
        '  "primary_strength": "<string>",\n'
        '  "fatal_flaw": "<string>",\n'
        '  "backstory": "<string>",\n'
        '  "voice_notes": "<string>",\n'
        '  "change_axis": "<string>",\n'
        '  "contradictions": [],\n'
        '  "secrets": [],\n'
        '  "values": [],\n'
        '  "taboos": [],\n'
        '  "continuity_facts": [],\n'
        '  "physical_description": "<string>",\n'
        '  "personality_traits": [],\n'
        '  "motives": "<string>",\n'
        '  "relationships": [],\n'
        '  "character_arc": "<string>",\n'
        '  "symbolic_role": "<string>",\n'
        '  "dialogue_patterns": "<string>",\n'
        '  "psychological_depth": "<string>",\n'
        '  "narrative_purpose": "<string>",\n'
        '  "thematic_significance": "<string>",\n'
        '  "impact_on_others": "<string>",\n'
        '  "first_appearance_chapter": "<string>",\n'
        '  "chapter_appearances": []\n'
        '}\n\n'
        "RULES:\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas.\n"
        "- Merge all data for the same character across chapters.\n"
        "- Character arc should be a narrative paragraph tracing their journey.\n"
    )

    user_content = (
        f"Consolidate the following accumulated character data into comprehensive profiles.\n\n"
        f"{chr(10).join(context_parts)}\n\n"
        f"ACCUMULATED CHARACTER DATA:\n{character_data_json}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "character_consolidation",
            "role": "character_consolidator",
        },
    )


def build_world_bible_consolidation_request(
    *,
    world_details_json: str,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for world bible consolidation (Phase 3b).

    Merges per-chapter world details into comprehensive entries.
    Deduplicates locations, organizations, magic systems, etc.
    """
    system_prompt = (
        "You are a world-building analyst for Narrative-Engine. "
        "Your job is to consolidate per-chapter world-building details into comprehensive entries.\n\n"
        "MERGE RULES:\n"
        "- Same-named entries from different chapters should be merged.\n"
        "- Descriptions should be combined into one coherent entry.\n"
        "- Canonical facts should be deduplicated.\n"
        "- Entry types: location, organization, magic_system, technology, custom, creature, concept, other\n\n"
        "OUTPUT — Return a JSON array of world bible entries. Each has EXACTLY these keys:\n\n"
        '{\n'
        '  "entry_type": "<string>",\n'
        '  "title": "<string>",\n'
        '  "summary": "<comprehensive description>",\n'
        '  "canonical_facts": [],\n'
        '  "related_character_ids": []\n'
        '}\n\n'
        "RULES:\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas.\n"
    )

    user_content = (
        f"Consolidate the following accumulated world-building details into comprehensive entries.\n\n"
        f"ACCUMULATED WORLD DETAILS:\n{world_details_json}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "world_bible_consolidation",
            "role": "world_consolidator",
        },
    )


def build_arc_detection_request(
    *,
    plot_events_json: str,
    character_arcs_json: str | None,
    story_premise: str | None,
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for overall arc detection and classification (Phase 3c).

    Analyzes accumulated plot events and character arcs to detect
    overarching narrative arcs and classify them.
    """
    context_parts: list[str] = []
    if story_premise:
        context_parts.append(f"Story premise: {story_premise}")

    system_prompt = (
        "You are a narrative structure analyst for Narrative-Engine. "
        "Your job is to detect and classify the overarching narrative arcs of a story\n"
        "from its accumulated plot events and character development data.\n\n"
        "Analyze the plot progression and identify:\n"
        "1. Major narrative arcs (the overall shape of the story)\n"
        "2. Character-driven arcs (individual character journeys)\n"
        "3. Thematic arcs (how themes develop and resolve)\n\n"
        "For each arc, map its stages:\n"
        "- status_quo: The world before change\n"
        "- inciting_incident: What disrupts the status quo\n"
        "- rising_action: Escalation of conflict\n"
        "- crisis: The lowest point, greatest uncertainty\n"
        "- climax: The decisive confrontation\n"
        "- resolution: How things settle after the climax\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "premise": "<string>",\n'
        '  "logline": "<string>",\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "target_audience": "<string>",\n'
        '  "complexity_level": "<LOW | MEDIUM | HIGH>",\n'
        '  "story_structure": "<SAVE_THE_CAT | THREE_ACT | HERO_JOURNEY | FREYTAGS_PYRAMID | KISHOTENKETSU | FICHTEAN_CURVE | SEVEN_POINT_STRUCTURE | SNOWFLAKE_METHOD | OTHER>",\n'
        '  "genre": "<string>",\n'
        '  "tone": "<string>",\n'
        '  "pov": "<FIRST | SECOND | THIRD_LIMITED | THIRD_OMNI | THIRD_OBJECTIVE | THIRD_MULTIPLE | OTHER>",\n'
        '  "story_arcs": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "stage_map": ["status_quo", "inciting_incident", "rising_action", "crisis", "climax", "resolution"],\n'
        '      "tags": []\n'
        '    }\n'
        '  ],\n'
        '  "sequences": [\n'
        '    {\n'
        '      "title": "<string>",\n'
        '      "summary": "<string>",\n'
        '      "chapters": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_constraints": [],\n'
        '  "success_definition": "<string>"\n'
        '}\n\n'
        "RULES:\n"
        "- All arrays must be JSON arrays [], not strings.\n"
        "- Do not include trailing commas.\n"
        '- story_structure must be one of the listed enum values.\n'
        '- pov must be one of the listed enum values.\n'
        "- Detect arcs from the progression of plot events and character development.\n"
    )

    user_parts: list[str] = []
    if context_parts:
        user_parts.append("\n".join(context_parts) + "\n\n")

    user_parts.append(f"PLOT EVENTS:\n{plot_events_json}")

    if character_arcs_json:
        user_parts.append(f"\nCHARACTER DEVELOPMENT DATA:\n{character_arcs_json}")

    user_content = "\n".join(user_parts)

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "multi_pass_import",
            "phase": "arc_detection",
            "role": "arc_detector",
        },
    )


def build_generate_description_request(
    *,
    project_name: str,
    genre: str,
    tone_profile: str,
    story_structure: str,
    premise_text: str | None,
    default_model: str | None,
) -> InferenceRequest:
    user_parts: list[str] = []
    user_parts.append(f"Project name: {project_name}")
    user_parts.append(f"Genre: {genre}")
    user_parts.append(f"Tone: {tone_profile}")
    user_parts.append(f"Structure: {story_structure}")
    if premise_text:
        user_parts.append(f"Premise: {premise_text}")

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.3,
        max_tokens=256,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are a story description generator. "
                    "Given project metadata, write a compelling 1-2 sentence description of the story. "
                    "Focus on the core conflict, setting, and what makes it unique. "
                    "Return ONLY the description text. No quotes, no preamble, no markdown."
                ),
            ),
            InferenceMessage(
                role="user",
                content="\n".join(user_parts),
            ),
        ],
        metadata={
            "mode": "project_description",
            "role": "description_generator",
        },
    )


def build_guided_setup_request(
    *,
    conversation_history: list[dict[str, str]],
    current_answer: str,
    accumulated_fields: dict[str, Any],
    default_model: str | None,
) -> InferenceRequest:
    history_text = "\n".join(
        f"[{msg.get('role', 'user')}]: {msg.get('content', '')}"
        for msg in conversation_history
    )

    fields_summary = _summarize_accumulated_fields(accumulated_fields)

    user_content = (
        f"CURRENT ANSWER:\n{current_answer}\n\n"
        f"CONVERSATION HISTORY:\n{history_text}\n\n"
        f"ALREADY COLLECTED FIELDS:\n{fields_summary}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.3,
        max_tokens=settings.inference_max_tokens("GUIDED_SETUP"),
        messages=[
            InferenceMessage(
                role="system",
                content=_GUIDED_SETUP_SYSTEM_PROMPT,
            ),
            InferenceMessage(
                role="user",
                content=user_content,
            ),
        ],
        metadata={
            "mode": "guided_setup",
            "role": "story_architect",
        },
    )


def _summarize_accumulated_fields(fields: dict[str, Any]) -> str:
    parts: list[str] = []

    config = fields.get("config", {})
    if config:
        config_parts = [f"{k}: {v}" for k, v in config.items() if v and v not in ("", [])]
        if config_parts:
            parts.append("Config:\n  " + "\n  ".join(config_parts))

    foundation = fields.get("foundation", {})
    if foundation:
        found_parts = [f"{k}: {v}" for k, v in foundation.items() if v and v not in ("", [])]
        if found_parts:
            parts.append("Foundation:\n  " + "\n  ".join(found_parts))

    characters = fields.get("characters", [])
    if characters:
        char_summaries = []
        for c in characters:
            name = c.get("name", "Unknown")
            role = c.get("role", "supporting")
            char_summaries.append(f"- {name} ({role})")
        parts.append("Characters:\n" + "\n".join(char_summaries))

    world_bible = fields.get("world_bible", [])
    if world_bible:
        world_summaries = []
        for w in world_bible:
            title = w.get("title", "Untitled")
            wtype = w.get("entry_type", "unknown")
            world_summaries.append(f"- [{wtype}] {title}")
        parts.append("World Bible:\n" + "\n".join(world_summaries))

    arcs = fields.get("arcs", [])
    if arcs:
        arc_summaries = []
        for a in arcs:
            char_name = a.get("character_name", "Unknown")
            atype = a.get("arc_type", "transformation")
            arc_summaries.append(f"- {char_name}: {atype}")
        parts.append("Arcs:\n" + "\n".join(arc_summaries))

    return "\n\n".join(parts) if parts else "(no fields collected yet)"


_GUIDED_SETUP_SYSTEM_PROMPT = """\
You are an experienced story architect helping an author set up a new writing project. \
Your job is to ask adaptive, conversational questions to gather all the information needed \
to create a complete project scaffold.

## IMPORTANT - NO REASONING
Do NOT include any thinking, reasoning, or internal monologue in your response. \
Output ONLY the raw JSON object. Do not wrap it in markdown code fences or explain your work.

## HOW TO ASK QUESTIONS
- Ask ONE focused question at a time. Never ask multiple things in one message.
- Adapt your next question based on everything the user has told you so far.
- If the user's answer is vague or unclear, ask a follow-up for clarification rather than guessing.
- Keep questions natural and conversational. Don't sound like a form.
- Reference details from earlier in the conversation to show you're tracking.

## WHAT TO COLLECT (in this order, but adapt based on flow)
1. **Project basics**: What kind of story? Genre, tone, overall idea.
2. **Narrative voice**: POV preference, writing style, target audience.
3. **Story structure**: Preferred narrative framework (three-act, hero's journey, etc.).
4. **Protagonist**: Who is the main character? Their goal, flaw, what makes them interesting.
5. **Secondary characters**: 1-3 other key characters and their roles.
6. **World/setting**: Where and when does the story take place? Key world rules or details.
7. **Core conflict**: What's the central tension or mystery driving the plot?
8. **Arcs**: How do the main characters change over the course of the story?
9. **Constraints & preferences**: Any specific requirements, themes to include/avoid, word count goals.
10. **Story structure**: Once core elements are collected, organize the story into
    sequences and chapters. Ask about pacing, chapter count, and major turning points.
    Propose a sequence/chapter outline for the user to confirm or adjust.

## OUTPUT FORMAT
Return ONLY a JSON object with these exact keys:
{
  "extracted_fields": {
    "config": {"project_name": "", "genre": "", "tone_profile": "", "pov": "", "story_structure": "", "primary_language": "", "constraints": []},
    "foundation": {"premise_text": "", "logline": "", "thematic_spine": "", "emotional_promise": "", "target_audience": "", "complexity_level": ""},
    "characters": [{"name": "", "role": "", "archetype": "", "age_range": "", "external_goal": "", "internal_need": "", "core_fear": "", "primary_strength": "", "fatal_flaw": "", "backstory_summary": "", "contradictions": [], "change_axis": ""}],
    "world_bible": [{"entry_type": "", "title": "", "summary": "", "canonical_facts": []}],
    "arcs": [{"character_name": "", "arc_type": "", "summary": "", "stages": ["status_quo", "inciting_incident", "rising_action", "crisis", "climax", "resolution"], "tags": []}],
    "sequences": [{"sequence_id": "", "title": "", "summary": "", "chapter_ids": [], "status": "guided"}],
    "chapters": [{"chapter_id": "", "sequence_id": "", "title": "", "summary": "",
        "objective": "", "conflict": "", "stakes": "", "active_character_ids": [],
        "continuity_requirements": [], "unresolved_questions": [], "position": 0, "status": "guided"}]
  },
  "next_question": "Your next adaptive question to ask the user.",
  "confidence": 0.5,
  "progress": 35.0,
  "ready_to_create": false,
  "category_progress": [
    {"category": "config", "completeness": 0.7, "confidence": 0.8, "fields_collected": ["genre", "tone_profile"], "fields_missing": ["pov", "story_structure"]},
    {"category": "foundation", "completeness": 0.3, "confidence": 0.6, "fields_collected": ["premise_text"], "fields_missing": ["logline", "thematic_spine"]},
    {"category": "characters", "completeness": 0.5, "confidence": 0.7, "fields_collected": ["protagonist"], "fields_missing": ["secondary characters"]},
    {"category": "world_bible", "completeness": 0.0, "confidence": 0.0, "fields_collected": [], "fields_missing": ["setting", "world rules"]},
    {"category": "arcs", "completeness": 0.0, "confidence": 0.0, "fields_collected": [], "fields_missing": ["protagonist arc"]}
  ]
}

## RULES
- Only populate fields you can extract with reasonable confidence from the conversation.
- Leave fields empty ("" or []) if you don't have enough information yet.
When config, foundation, characters, world_bible, and arcs all reach 0.7+ completeness,
shift focus to structuring the story into sequences and chapters. Present a proposed
outline and ask if it works or needs adjustment. Do not set ready_to_create until the
user has confirmed the story structure.
- Set ready_to_create to true only when all 5 categories reach at least 0.7 completeness.
- Progress should be the average of all category completeness values, multiplied by 100.
- Confidence reflects how sure you are about the extracted values (0.0 to 1.0).
- No markdown code fences. Return raw JSON only.
- Do NOT use thinking tags, reasoning blocks, or chain-of-thought. Output JSON directly.\
"""
