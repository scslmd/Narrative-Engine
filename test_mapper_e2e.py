from __future__ import annotations

import json
import requests
from pydantic import ValidationError

from app.services.story_import import _map_llm_fields
from app.schemas.story_import import StoryImportAnalysis

# Read the test story
story = open("data/test_story_man_who_would_be_king.txt", "r").read()
story = story[:24000]

# Use the NEW prompt (clean JSON template)
from app.services.runtime_prompts import build_import_analysis_request
req = build_import_analysis_request(
    story_text=story,
    default_model="Qwen3.6-35B-A3B-UD-Q5_K_M.gguf",
)

print("Sending request to LLM...")
from app.schemas.inference import InferenceMessage
payload = {
    "model": req.model,
    "temperature": req.temperature,
    "max_tokens": req.max_tokens,
    "messages": [
        {"role": m.role, "content": m.content} for m in req.messages
    ],
    "stream": False,
}

r = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=300)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    print(f"Output length: {len(content)} chars")

    # Parse JSON (extract from potential markdown/code fences)
    import re
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1:
        json_str = content[first_brace : last_brace + 1]
        parsed = json.loads(json_str)

        # Apply mapper
        mapped = _map_llm_fields(parsed)
        print("\n=== After mapping ===\n")

        # Try validation
        try:
            analysis = StoryImportAnalysis.model_validate(mapped)
            print("=== VALIDATION PASSED ===\n")

            print(f"project_name: {analysis.project_name}")
            print(f"genre: {analysis.genre}")
            print(f"tone: {analysis.tone}")
            print(f"pov: {analysis.pov}")
            print(f"story_structure: {analysis.story_structure}")
            print(f"premise: {analysis.premise[:100]}...")
            print(f"logline: {analysis.logline}")
            print(f"thematic_spine: {analysis.thematic_spine[:100]}...")
            print(f"emotional_promise: {analysis.emotional_promise}")
            print(f"target_audience: {analysis.target_audience}")
            print(f"complexity_level: {analysis.complexity_level}")

            print(f"\ncharacters: {len(analysis.characters)}")
            for c in analysis.characters:
                print(f"  - {c.name} | role={c.role}")
                print(f"    goal: {c.external_goal or '(empty)'}")
                print(f"    need: {c.internal_need or '(empty)'}")
                print(f"    fear: {c.core_fear or '(empty)'}")
                print(f"    strength: {c.primary_strength or '(empty)'}")
                print(f"    flaw: {c.fatal_flaw or '(empty)'}")
                print(f"    change: {c.change_axis or '(empty)'}")
                if c.contradictions:
                    print(f"    contradictions: {c.contradictions}")
                if c.secrets:
                    print(f"    secrets: {c.secrets}")
                if c.values:
                    print(f"    values: {c.values}")
                if c.taboos:
                    print(f"    taboos: {c.taboos}")
                if c.continuity_facts:
                    print(f"    continuity_facts: {c.continuity_facts}")

            print(f"\nworld_bible: {len(analysis.world_bible)} entries")
            for w in analysis.world_bible:
                print(f"  - {w.entry_type}: {w.title}")
                print(f"    summary: {w.summary[:120]}...")
                if w.canonical_facts:
                    print(f"    facts: {w.canonical_facts}")

            print(f"\nstory_arcs: {len(analysis.story_arcs)}")
            for a in analysis.story_arcs:
                print(f"  - {a.name}: {a.summary[:80]}")
                print(f"    stage_map: {a.stage_map}")
                print(f"    tags: {a.tags}")

            print(f"\nsequences: {len(analysis.sequences)}")
            for s in analysis.sequences:
                print(f"  - {s.title}: {s.summary[:80]}")
                if s.chapters:
                    print(f"    chapters: {s.chapters}")

            print(f"\nnarrative_constraints: {analysis.narrative_constraints}")
            print(f"success_definition: {analysis.success_definition or '(empty)'}")

            # Save validated result
            validated_result = analysis.model_dump()
            with open("data/test_mapper_result.json", "w", encoding="utf-8") as f:
                json.dump(validated_result, f, indent=2, ensure_ascii=False)
            print("\nSaved to data/test_mapper_result.json")

        except ValidationError as e:
            print("=== VALIDATION FAILED ===")
            for err in e.errors():
                loc = " -> ".join(str(x) for x in err["loc"])
                msg = err["msg"]
                print(f"  {loc}: {msg}")

            # Save the mapped data for inspection
            with open("data/test_mapped_result.json", "w", encoding="utf-8") as f:
                json.dump(mapped, f, indent=2, ensure_ascii=False)
            print("\nMapped data saved to data/test_mapped_result.json")

    else:
        print("No JSON object found")
else:
    print(r.text[:1000])
