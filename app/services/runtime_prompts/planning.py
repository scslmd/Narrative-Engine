from __future__ import annotations

import json

from ...schemas.inference import InferenceMessage, InferenceRequest


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
