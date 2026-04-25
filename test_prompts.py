from __future__ import annotations

import json
import re
import requests

# Read the test story
story = open("data/test_story_man_who_would_be_king.txt", "r").read()
story = story[:24000]

# NEW system prompt (from our improved prompts.py)
new_system = (
    "You are a story analysis AI for Narrative-Engine. You analyze completed stories "
    "and extract structured metadata that fills out all project elements.\n\n"
    "ANALYSIS APPROACH:\n"
    "Read the story carefully. Work through these steps in order:\n"
    "1. Identify POV from narrative voice (see POV guide below).\n"
    "2. Identify the core conflict and protagonist's journey to classify story structure.\n"
    "3. List every named character and infer their role from their function in the plot.\n"
    "4. Extract world details: locations, cultures, systems, rules that shape the narrative.\n"
    "5. Identify major arcs: character growth, relationship evolution, thematic development.\n"
    "6. Write the premise, logline, and thematic spine as concise summaries.\n\n"
    "POV IDENTIFICATION GUIDE:\n"
    "- FIRST: Narrator uses I/me/my. Reader only knows what narrator knows.\n"
    "- SECOND: Narrator addresses reader/character as you. Rare in prose fiction.\n"
    "- THIRD_LIMITED: Narrator uses he/she/they but reveals one character's thoughts/feelings. Most common narrative mode.\n"
    "- THIRD_OMNI: Narrator uses he/she/they and knows thoughts/feelings of multiple characters, sometimes commenting directly.\n"
    "- THIRD_OBJECTIVE: Narrator uses he/she/they and reports only observable actions/dialogue. No internal thoughts.\n"
    "- THIRD_MULTIPLE: Narrator uses he/she/they and alternates internal access between two or more characters.\n"
    "- OTHER: Does not fit the above.\n\n"
    "STORY STRUCTURE CLASSIFICATION GUIDE:\n"
    "- THREE_ACT: Clear three-part division (setup/confrontation/resolution) with midpoint reversal.\n"
    "- HERO_JOURNEY: Distinct stages: ordinary world -> call to adventure -> refusal -> mentor -> crossing threshold -> tests/allies/enemies -> approach -> ordeal -> reward -> road back -> resurrection -> return with elixir.\n"
    "- SAVE_THE_CAT: Hero pursues a clearly defined goal, faces escalating obstacles, achieves victory.\n"
    "- FREYTAGS_PYRAMID: Exposition -> rising action -> climax -> falling action -> denouement.\n"
    "- KISHOTENKETSU: Four-act structure without conflict: introduction, development, twist, reconciliation.\n"
    "- FICHTEAN_CURVE: Series of escalating crises with each resolving into a worse one.\n"
    "- SEVEN_POINT_STRUCTURE: Hook -> plot turn 1 -> puzzle 1 -> midpoint -> puzzle 2 -> plot turn 2 -> resolution.\n"
    "- SEVEN_KEY_STEPS: Similar to seven-point but with emphasis on key plot turning points.\n"
    "- SNOWFLAKE_METHOD: Expands from one sentence to chapters to scenes.\n"
    "- BRAINDUMP: Fragmented, non-linear, stream-of-consciousness.\n"
    "- OTHER: Does not fit the above.\n"
    "When in doubt, use THREE_ACT.\n\n"
    "CHARACTER FIELD DEFINITIONS:\n"
    "- name: Full display name as it appears in the story.\n"
    "- role: One of: protagonist, antagonist, mentor, deuteragonist, foil, supporting, minor.\n"
    "- archetype: Common archetype pattern (hero, villain, trickster, sage, rebel, guardian, orphan, creator, caregiver, ruler, magician, everyman). Use unknown if unclear.\n"
    "- external_goal: What the character actively tries to achieve or obtain (concrete, observable).\n"
    "- internal_need: What the character fundamentally needs to grow or find fulfillment.\n"
    "- core_fear: What the character is most terrified of, driving their actions.\n"
    "- primary_strength: The character's defining positive trait or ability.\n"
    "- fatal_flaw: The character's defining weakness or vice that creates conflict.\n"
    "- backstory: Key past events that shaped the character. Keep it concise.\n"
    "- voice_notes: How the character speaks or their distinctive verbal mannerisms.\n"
    "- change_axis: How the character transforms from beginning to end.\n"
    "- contradictions: Paradoxical traits that coexist.\n"
    "- secrets: Information the character hides from others.\n"
    "- values: Core principles the character lives by.\n"
    "- taboos: Lines the character will not cross.\n"
    "- continuity_facts: Observable facts about the character used for consistency.\n\n"
    "REQUIRED OUTPUT KEYS:\n"
    "- project_name, genre (title case), tone, pov, story_structure\n"
    "- premise (1-2 sentences), logline (1 sentence, under 500 chars), thematic_spine, emotional_promise\n"
    "- target_audience, complexity_level (LOW/MEDIUM/HIGH)\n"
    "- characters (non-empty array, see definitions above)\n"
    "- world_bible (array, can be empty), story_arcs (array, can be empty)\n"
    "- sequences (array, can be empty), narrative_constraints, success_definition (optional)\n\n"
    "FIELD VALUE RULES:\n"
    "- pov must be EXACT match: FIRST, SECOND, THIRD_LIMITED, THIRD_OMNI, THIRD_OBJECTIVE, THIRD_MULTIPLE, OTHER\n"
    "- story_structure must be EXACT match: SAVE_THE_CAT, THREE_ACT, HERO_JOURNEY, FREYTAGS_PYRAMID, KISHOTENKETSU, FICHTEAN_CURVE, SEVEN_POINT_STRUCTURE, SEVEN_KEY_STEPS, SNOWFLAKE_METHOD, BRAINDUMP, OTHER\n"
    "- complexity_level must be exactly one of: LOW, MEDIUM, HIGH\n"
    "- If a field cannot be inferred, use empty string. Do not guess.\n\n"
    "VALIDATION CHECKLIST:\n"
    "1. All required top-level keys present.\n"
    "2. characters array non-empty.\n"
    "3. pov and story_structure are exact enum matches.\n"
    "4. Every character has name and role.\n"
    "5. No field uses values outside specified constraints.\n\n"
    "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
)

payload = {
    "model": "Qwen3.6-35B-A3B-UD-Q5_K_M.gguf",
    "temperature": 0.1,
    "max_tokens": 16000,
    "messages": [
        {"role": "system", "content": new_system},
        {"role": "user", "content": f"Analyze this completed story and extract all structured metadata:\n\n{story}"}
    ],
    "stream": False,
}

print("Sending request with NEW prompt...")
r = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=300)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    print(f"Output length: {len(content)} chars")

    # Count braces
    open_b = content.count(chr(123))
    close_b = content.count(chr(125))
    print(f"Brace balance: {open_b} opening, {close_b} closing (diff: {open_b - close_b})")

    # Extract JSON
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1:
        json_str = content[first_brace : last_brace + 1]
        try:
            result = json.loads(json_str)
            print("\n=== PARSED SUCCESSFULLY ===\n")

            project_name = result.get("project_name", "(missing)")
            genre = result.get("genre", "(missing)")
            tone = result.get("tone", "(missing)")
            pov = result.get("pov", "(missing)")
            structure = result.get("story_structure", "(missing)")
            premise = result.get("premise", "")
            logline = result.get("logline", "")
            thematic_spine = result.get("thematic_spine", "")
            emotional_promise = result.get("emotional_promise", "")
            target_audience = result.get("target_audience", "")
            complexity = result.get("complexity_level", "")
            chars = result.get("characters", [])
            wb = result.get("world_bible", [])
            arcs = result.get("story_arcs", [])
            seqs = result.get("sequences", [])
            constraints = result.get("narrative_constraints", [])

            print(f"project_name: {project_name}")
            print(f"genre: {genre}")
            print(f"tone: {tone}")
            print(f"pov: {pov}")
            print(f"story_structure: {structure}")
            print(f"premise: {premise[:120]}...")
            print(f"logline: {logline}")
            print(f"thematic_spine: {thematic_spine[:100]}...")
            print(f"emotional_promise: {emotional_promise}")
            print(f"target_audience: {target_audience}")
            print(f"complexity_level: {complexity}")
            print(f"\ncharacters: {len(chars)}")
            for c in chars:
                name = c.get("name", "?")
                role = c.get("role", "?")
                goal = c.get("external_goal", "")
                need = c.get("internal_need", "")
                fear = c.get("core_fear", "")
                strength = c.get("primary_strength", "")
                flaw = c.get("fatal_flaw", "")
                change = c.get("change_axis", "")
                print(f"  - {name} | role={role}")
                print(f"    goal: {goal or '(empty)'}")
                print(f"    need: {need or '(empty)'}")
                print(f"    fear: {fear or '(empty)'}")
                print(f"    strength: {strength or '(empty)'}")
                print(f"    flaw: {flaw or '(empty)'}")
                print(f"    change: {change or '(empty)'}")

            print(f"\nworld_bible: {len(wb)} entries")
            for w in wb:
                print(f"  - {w.get('entry_type')}: {w.get('title')} | {w.get('summary', '')[:80]}")

            print(f"\nstory_arcs: {len(arcs)}")
            for a in arcs:
                print(f"  - {a.get('name')}: {a.get('summary', '')[:80]}")

            print(f"\nsequences: {len(seqs)}")
            for s in seqs:
                print(f"  - {s.get('title')}: {s.get('summary', '')[:80]}")

            print(f"\nnarrative_constraints: {constraints}")
            print(f"success_definition: {result.get('success_definition', '(empty)')}")

            # Save result
            with open("data/test_new_prompt_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("\nSaved to data/test_new_prompt_result.json")

        except json.JSONDecodeError as e:
            print(f"\nJSON parse error: {e}")
            # Save raw for inspection
            with open("data/test_new_prompt_raw.txt", "w", encoding="utf-8") as f:
                f.write(content)
            # Show error context
            pos = e.pos
            start = max(0, pos - 100)
            end = min(len(json_str), pos + 100)
            print(f"Context:\n{json_str[start:end]}")
            print(f"\nRaw output saved to data/test_new_prompt_raw.txt")
    else:
        print("No JSON object found")

else:
    print(r.text[:1000])
