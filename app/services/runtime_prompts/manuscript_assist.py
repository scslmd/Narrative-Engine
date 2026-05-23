from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ...schemas.inference import InferenceMessage, InferenceRequest
from ...settings import settings

if TYPE_CHECKING:
    from app.schemas.manuscript_assist import ManuscriptAssistPacket


_ASSIST_INSTRUCTIONS: dict[str, str] = {
    "developmental_review": (
        "Perform a developmental review focusing on pacing, character motivation, plot logic, "
        "thematic consistency, and emotional beats. Identify specific passages that could be "
        "improved and propose concrete rewrites as suggestions. For each suggestion, provide "
        "the exact source_text to replace, the proposed_text replacement, and a rationale explaining "
        "why the change improves the narrative."
    ),
    "canon_check": (
        "Check the manuscript for canon consistency. Verify that character traits, world rules, "
        "established facts, and prior events are consistent with the story's canon. Identify "
        "contradictions and propose corrections. For each suggestion, provide the exact source_text, "
        "proposed_text, and rationale."
    ),
    "character_voice_check": (
        "Review character voice consistency. Check that dialogue, internal monologue, and narrative "
        "perspective match each character's established voice, background, and personality. Identify "
        "passages where voice feels inconsistent or generic and propose rewrites. For each suggestion, "
        "provide source_text, proposed_text, and rationale."
    ),
    "pacing_review": (
        "Review pacing and rhythm. Check for scenes that rush important moments or linger too long on "
        "minor details. Identify transitions between scenes and suggest improvements to scene flow. "
        "For each suggestion, provide source_text, proposed_text, and rationale."
    ),
    "theme_review": (
        "Review thematic development. Check that themes are introduced, developed, and resonated through "
        "the narrative without being heavy-handed or inconsistent. Identify passages where theme could be "
        "strengthened or clarified. For each suggestion, provide source_text, proposed_text, and rationale."
    ),
    "line_edit_selection": (
        "Tighten and polish the selected passage. Remove redundancy, improve flow, fix awkward phrasing, "
        "and enhance clarity while preserving the original meaning and voice. Provide source_text, "
        "proposed_text, and rationale for each change."
    ),
    "expand_sensory_sight": (
        "Expand the selected passage with vivid visual detail. Focus on lighting, color, shapes, movement, "
        "spatial relationships, and visual atmosphere. Provide source_text, proposed_text, and rationale."
    ),
    "expand_sensory_sound": (
        "Expand the selected passage with auditory detail. Focus on ambient noise, tones, silence, rhythm, "
        "cadence of speech, and soundscape. Provide source_text, proposed_text, and rationale."
    ),
    "expand_sensory_smell": (
        "Expand the selected passage with olfactory detail. Focus on scents, odors, atmospheric qualities, "
        "and how smell shapes mood and memory. Provide source_text, proposed_text, and rationale."
    ),
    "expand_sensory_texture": (
        "Expand the selected passage with tactile detail. Focus on textures, temperature, weight, "
        "physical sensations, and how touch grounds the scene. Provide source_text, proposed_text, and rationale."
    ),
    "expand_sensory_taste": (
        "Expand the selected passage with gustatory detail. Focus on flavors, palate sensations, "
        "and taste memories. Provide source_text, proposed_text, and rationale."
    ),
    "expand_metaphor": (
        "Enrich the selected passage with figurative language. Add metaphors and similes that illuminate "
        "meaning without overwriting or distracting from the narrative. Provide source_text, proposed_text, "
        "and rationale."
    ),
    "expand_show_dont_tell": (
        "Rewrite the selected passage using show-don't-tell technique. Replace abstract statements with "
        "concrete actions, observations, behavior, and sensory detail. Provide source_text, proposed_text, "
        "and rationale."
    ),
    "compress_selection": (
        "Condense the selected passage to roughly half its length while preserving core meaning, tone, "
        "and character voice. Remove filler and tighten prose. Provide source_text, proposed_text, and rationale."
    ),
    "rewrite_selection_same_voice": (
        "Rewrite the selected passage with fresh phrasing while maintaining the same character voice and "
        "narrative tone. Provide source_text, proposed_text, and rationale."
    ),
    "alternate_selection": (
        "Produce an alternate version of the selected passage that conveys the same narrative beat but "
        "approaches it from a different angle. Provide source_text, proposed_text, and rationale."
    ),
    "continue_from_selection": (
        "Continue the narrative from the end of the selection. Maintain established character voice, tone, "
        "and pacing. Provide source_text (the last sentence of the selection), proposed_text (the continuation), "
        "and rationale."
    ),
    "fork_from_selection": (
        "Fork a new variant from the selected passage that explores an alternate direction while maintaining "
        "the same narrative foundation. Provide source_text, proposed_text, and rationale."
    ),
}

_DEFAULT_INSTRUCTION = (
    "Review the manuscript content and suggest specific improvements. For each suggestion, provide "
    "the exact source_text to replace, the proposed_text replacement, and a rationale explaining "
    "why the change improves the narrative."
)


def _resolve_instruction(assist_kind: str, explicit_instruction: str) -> str:
    """Resolve the final instruction by combining kind-specific guidance with user-provided instruction."""
    kind = assist_kind if isinstance(assist_kind, str) else str(assist_kind)
    base = _ASSIST_INSTRUCTIONS.get(kind, _DEFAULT_INSTRUCTION)
    if explicit_instruction and explicit_instruction.strip():
        return f"{base} Instruction: {explicit_instruction.strip()}"
    return base


def build_m500_manuscript_assist_request(
    packet: ManuscriptAssistPacket,
    default_model: str | None,
) -> InferenceRequest:
    payload = packet.model_dump(mode="json")
    instruction = _resolve_instruction(packet.assist_kind, payload.get("instruction", ""))

    return InferenceRequest(
        model=packet.model_id or default_model,
        temperature=packet.temperature if packet.temperature is not None else settings.inference_temperature("M-500"),
        max_tokens=packet.max_tokens if packet.max_tokens is not None else 4000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are a manuscript assistant for narrative editing."
                    "\n\nReturn strict JSON only with this exact structure:"
                    "\n{"
                    "  \"summary\": \"string — brief overview of the manuscript's current state\","
                    "  \"suggestions\": ["
                    "    {"
                    "      \"source_text\": \"exact text from the manuscript to replace\","
                    "      \"proposed_text\": \"the replacement text\","
                    "      \"rationale\": \"why this change improves the narrative\""
                    "    }"
                    "  ],"
                    "  \"warnings\": [\"string — high-level observations about pacing, continuity, etc.\"],"
                    "  \"created_branch_brief\": \"optional brief for a forked branch\""
                    "}"
                    "\nNo markdown code fences, no explanatory prose outside the JSON."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps({
                    **payload,
                    "instruction": instruction,
                }, ensure_ascii=True, indent=2, sort_keys=True),
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
        temperature=settings.inference_temperature("M-550"),
        max_tokens=3000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "Repair manuscript assist output to satisfy canon and continuity constraints. "
                    "Return strict JSON only with keys: summary, suggestions, created_branch_brief, warnings. "
                    "Do not include markdown or explanatory text."
                ),
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
        temperature=packet.temperature if packet.temperature is not None else settings.inference_temperature("M-500"),
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
