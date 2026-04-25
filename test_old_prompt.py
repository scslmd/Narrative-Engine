from __future__ import annotations

import json
import re
import requests

# Read the test story
story = open("data/test_story_man_who_would_be_king.txt", "r").read()
story = story[:24000]

# OLD system prompt
old_system = (
    "You are a story analysis AI for Narrative-Engine. You analyze completed stories "
    "and extract structured metadata that fills out all project elements.\n\n"
    "Your output MUST be valid JSON with these exact top-level keys:\n"
    "- project_name (string, required)\n"
    "- genre (string, required)\n"
    "- tone (string, required)\n"
    "- pov (string: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER)\n"
    "- story_structure (string: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER)\n"
    "- premise (string, required)\n"
    "- logline (string, required)\n"
    "- thematic_spine (string, required)\n"
    "- emotional_promise (string, required)\n"
    "- target_audience (string, required)\n"
    "- complexity_level (string, required: LOW, MEDIUM, HIGH)\n"
    "- characters (array of objects: each with name, role, archetype, external_goal, internal_need, core_fear, primary_strength, fatal_flaw, backstory, voice_notes, change_axis, contradictions, secrets, values, taboos, continuity_facts)\n"
    "- world_bible (array of objects: each with entry_type, title, summary, canonical_facts, related_character_ids)\n"
    "- story_arcs (array of objects: each with name, summary, stage_map, tags)\n"
    "- sequences (array of objects: each with title, summary, chapters)\n"
    "- narrative_constraints (array of strings)\n"
    "- success_definition (string)\n"
    "- raw_story_text (string)\n\n"
    "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
)

payload = {
    "model": "Qwen3.6-35B-A3B-UD-Q5_K_M.gguf",
    "temperature": 0.1,
    "max_tokens": 16000,
    "messages": [
        {"role": "system", "content": old_system},
        {"role": "user", "content": f"Analyze this completed story and extract all structured metadata:\n\n{story}"}
    ],
    "stream": False,
}

print("Sending request to llama.cpp...")
r = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=300)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    content = data["choices"][0]["message"]["content"]

    # Save raw output
    with open("data/test_old_prompt_raw.txt", "w", encoding="utf-8") as f:
        f.write(content)

    # Extract JSON using brace-finding approach
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1:
        json_str = content[first_brace : last_brace + 1]
        print(f"\nExtracted JSON: {len(json_str)} chars (chars {first_brace}-{last_brace})")

        # Show context around the error
        try:
            json.loads(json_str)
        except json.JSONDecodeError as e:
            pos = e.pos
            # Show 200 chars before and after the error
            start = max(0, pos - 200)
            end = min(len(json_str), pos + 200)
            context = json_str[start:end]
            marker = " " * (pos - start) + "^"
            print(f"\n--- Error at position {e.pos} (line {e.lineno}, col {e.colno}) ---")
            print(f"Error: {e.msg}")
            print(f"\nContext:\n{context}\n{marker}")

            # Try to find the issue - likely an unescaped quote or missing comma
            lines = json_str.split("\n")
            line_num = e.lineno - 1
            if line_num >= 0 and line_num < len(lines):
                print(f"\nLine {e.lineno}: {lines[line_num]}")
                if e.lineno - 2 >= 0:
                    print(f"Line {e.lineno - 1}: {lines[e.lineno - 2]}")
                if e.lineno < len(lines):
                    print(f"Line {e.lineno + 1}: {lines[e.lineno]}")

    else:
        print(f"No JSON object found in content (len={len(content)})")

else:
    print(r.text[:1000])
