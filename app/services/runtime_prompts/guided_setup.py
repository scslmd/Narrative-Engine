from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ...schemas.inference import InferenceMessage, InferenceRequest
from ...settings import settings

if TYPE_CHECKING:
    from ...schemas.pattern_extraction import PatternExtractionAnalysis


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
        temperature=settings.inference_temperature("GUIDED_SETUP"),
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
10. **Planning structure**: Once core elements are collected, organize the story into
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
- When config, foundation, characters, world_bible, and arcs all reach 0.7+ completeness,
  shift focus to structuring the story into sequences and chapters. Present a proposed
  outline and ask if it works or needs adjustment.
- Do not set ready_to_create until the user has confirmed the story structure.
- Set ready_to_create to true only when:
  - the 5 core categories (config/foundation/characters/world_bible/arcs) are each >= 0.7
"""


def build_relationship_extraction_request(
    *,
    manuscript_text: str,
    character_ids: list[str],
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for extracting character relationships from manuscript text."""
    char_list = json.dumps(character_ids, ensure_ascii=True)

    system_prompt = (
        "You are a character relationship analyst for Narrative-Engine. "
        "Your job is to extract character relationships from manuscript text.\n\n"
        "Analyze the text to identify:\n"
        "1. Direct interactions between characters (dialogue, shared scenes)\n"
        "2. Implied relationships (references, memories, emotional connections)\n"
        "3. Relationship dynamics (power, affection, conflict, rivalry)\n\n"
        "For each relationship found, determine:\n"
        "- relation_kind: The type of relationship\n"
        "- summary: Brief description of the relationship (1-2 sentences)\n"
        "- tension: Any conflict or strain in the relationship (optional)\n\n"
        "OUTPUT - Return a JSON array with EXACTLY these keys per relationship:\n\n"
        '[\n'
        '  {\n'
        '    "source_character_id": "<character_id>",\n'
        '    "target_character_id": "<character_id>",\n'
        '    "relation_kind": "<string>",\n'
        '    "summary": "<string>",\n'
        '    "tension": "<string or null>"\n'
        "  }\n"
        "]\n\n"
        "RULES:\n"
        "- Only include relationships between the provided character IDs.\n"
        "- Use the exact character_id values provided - do not invent new IDs.\n"
        "- relation_kind must be one of: family, friendship, rivalry, romance, mentorship, alliance, enmity, sibling, parent_child, spouse, colleague, enemy\n"
        "- summary must be 1-2 sentences describing the relationship.\n"
        "- tension is optional; include only if there is clear conflict or strain.\n"
        "- Do not include duplicate pairs (A->B and B->A are the same relationship).\n"
        "- No markdown code fences. Return raw JSON array only.\n"
        "- Do NOT use thinking tags, reasoning blocks, or chain-of-thought. Output JSON directly.\n"
    )

    user_content = (
        f"Available character IDs:\n{char_list}\n\n"
        f"Manuscript text:\n{manuscript_text}"
    )

    return InferenceRequest(
        model=default_model,
        temperature=0.1,
        max_tokens=8000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={"phase": "relationship_extraction"},
    )


def build_cascade_extraction_request(
    manuscript_text: str,
    existing_characters: list[str] | None = None,
    max_tokens: int | None = None,
) -> InferenceRequest:
    effective_max = max_tokens or settings.discovery_max_tokens

    system_prompt = """You are an expert literary analyst. Extract characters, relationships, and world bible entries from the provided manuscript text.

Output a JSON object with three arrays: "characters", "relationships", "world_entries".

For each character, include: display_name, aliases (array of strings), role_in_story, archetype, external_goal, internal_need, misbelief_or_wound, core_fear, primary_strength, fatal_flaw_or_limitation, backstory_summary, voice_notes, secrets (array), values (array), taboos (array), description. Leave fields as empty string or empty array if not mentioned in text.

For each relationship, include: source_character_name, target_character_name, relation_kind (one of: family, friendship, rivalry, romance, mentorship, alliance, enmity, sibling, parent_child, spouse, colleague, enemy), summary, tension, directionality ("directed" or "bidirectional"), confidence (0-1 float). Only extract direct interactions with significant confidence.

For each world entry, include: entry_type (one of: location, organization, magic_system, technology, creature, concept, object, custom), title, summary, canonical_facts (array), related_character_names (array), confidence (0-1 float).

Self-rate confidence for each entity on a 0-1 scale based on how clearly it appears in the text."""

    context_parts: list[str] = []
    if existing_characters:
        context_parts.append("## Existing Characters\n" + "\n".join("- " + c for c in existing_characters))
    context_parts.append(f"## Manuscript Text\n\n{manuscript_text}")
    user_prompt = "\n".join(context_parts)

    return InferenceRequest(
        model="default",
        temperature=0.1,
        max_tokens=effective_max,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_prompt),
        ],
        metadata={"phase": "cascade_extraction"},
    )


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

