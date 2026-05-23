from __future__ import annotations

import json

from ...schemas.inference import InferenceMessage, InferenceRequest


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
