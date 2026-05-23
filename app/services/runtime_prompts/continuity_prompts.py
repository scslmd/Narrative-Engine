from __future__ import annotations

from ...schemas.inference import InferenceMessage, InferenceRequest


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
