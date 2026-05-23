from __future__ import annotations

from ...schemas.inference import InferenceMessage, InferenceRequest


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

