from __future__ import annotations

from ...schemas.inference import InferenceMessage, InferenceRequest


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
        "- Extract character names from chapter titles like 'Chapter 3: Kvothe\\'s Journey'.\n"
        "- Extract POV hints like 'POV: Kvothe' or 'From Elodin\\'s Perspective'.\n"
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
