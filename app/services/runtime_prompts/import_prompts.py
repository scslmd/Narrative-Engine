from __future__ import annotations

from ...schemas.inference import InferenceMessage, InferenceRequest


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
