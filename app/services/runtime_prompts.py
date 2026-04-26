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
    chapter_id: str | None = None,
) -> InferenceRequest:
    prompt_context = _runtime_prompt_context(manifest=manifest, payload=payload)
    if sequence_output is not None:
        prompt_context["sequence_output"] = sequence_output
    if architect_output is not None:
        prompt_context["architect_output"] = architect_output
    chapter_label = f"chapter {chapter_id}" if chapter_id else "chapter-1"
    return InferenceRequest(
        model=str(payload.get("model_id") or payload.get("model") or default_model or "").strip() or None,
        temperature=_coerce_float(payload.get("temperature"), default=0.2),
        max_tokens=_coerce_int(payload.get("max_tokens"), default=8000),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    f"You are the Drafter role for Narrative-Engine. "
                    f"Produce the P-300 {chapter_label} draft as deterministic markdown. "
                    f"Preserve chapter flow, continuity, and stable section ordering."
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
        "and extract structured metadata.\n\n"
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
        '      "chapters": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_constraints": [],\n'
        '  "success_definition": "<string>",\n'
        '  "raw_story_text": ""\n'
        '}\n\n'
        "CRITICAL RULES FOR FIELDS:\n"
        "- You MUST use the EXACT key names shown above. Do not use synonyms like name->title, description->summary, etc.\n"
        "- Arrays (contradictions, secrets, values, taboos, continuity_facts, canonical_facts, related_character_ids, stage_map, tags, chapters) MUST be JSON arrays, even if empty [].\n"
        "- If you cannot infer a value, use empty string \"\" for strings or [] for arrays. Do NOT skip keys.\n\n"
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
        "CHARACTER EXTRACTION RULES:\n"
        "- Include every character with meaningful presence, not just named ones.\n"
        "- For unnamed characters, use descriptive names like \"the old guard,\" \"the merchant.\"\n"
        "- role is critical: correctly identify protagonist (drives plot) and antagonist (opposes protagonist).\n\n"
        "VALIDATION CHECKLIST (check before returning):\n"
        "1. All required keys present, no extra top-level keys beyond raw_story_text.\n"
        "2. characters array is non-empty, every character has name and role.\n"
        "3. pov and story_structure are exact enum matches.\n"
        "4. All array fields (contradictions, secrets, values, taboos, continuity_facts, canonical_facts, stage_map, tags, chapters) are actual JSON arrays [].\n"
        "5. world_bible entries use entry_type and title (not name/description).\n"
        "6. story_arcs use summary (not description), stage_map, tags (not type).\n"
        "7. sequences use title (not name), summary (not description).\n\n"
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

    system_prompt = (
        "You are a consistency critic for Narrative-Engine. "
        "Check whether each character's dialogue and actions match their profile.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{\n'
        '  "passed": true or false,\n'
        '  "violations": [\n'
        '    {"character": "<name>", "issue": "<what is wrong>", "suggestion": "<how to fix>"}\n'
        '  ]\n\n'
        "If the character behaves consistently with their profile, set passed=true and violations=[].\n"
        "Check: voice (word choice, sentence style), behavior (goals, fears, traits), knowledge (what they should know)."
    )

    user_content = f"CHARACTER PROFILES:\n{bios_block}\n\nDRAFT TO CHECK:\n{draft_text}"

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
        '  "chapter_id": "<the chapter identifier>",\n'
        '  "title": "<chapter title or descriptive label>",\n'
        '  "key_events": ["<event 1>", "<event 2>"],\n'
        '  "character_states": {"<name>": "<condition/goal at chapter end>"},\n'
        '  "unresolved_threads": ["<thread 1>"]\n'
        '}\n\n'
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
