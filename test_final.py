from __future__ import annotations

import json
import requests

from app.services.story_import import _extract_json, _map_llm_fields
from app.schemas.story_import import StoryImportAnalysis
from app.services.runtime_prompts import build_import_analysis_request

story = open("data/test_story_man_who_would_be_king.txt", "r").read()[:24000]
req = build_import_analysis_request(story_text=story, default_model="Qwen3.6-35B-A3B-UD-Q5_K_M.gguf")

payload = {
    "model": req.model,
    "temperature": req.temperature,
    "max_tokens": req.max_tokens,
    "messages": [{"role": m.role, "content": m.content} for m in req.messages],
    "stream": False,
}

r = requests.post("http://127.0.0.1:8080/v1/chat/completions", json=payload, timeout=300)
content = r.json()["choices"][0]["message"]["content"]
print(f"Total chars: {len(content)}")

try:
    parsed = _extract_json(content)
    print("JSON EXTRACTED SUCCESSFULLY")
    print(f"Keys: {list(parsed.keys())}")

    mapped = _map_llm_fields(parsed)
    analysis = StoryImportAnalysis.model_validate(mapped)
    print("VALIDATION: PASSED")
    print(f"  project_name: {analysis.project_name}")
    print(f"  genre: {analysis.genre}")
    print(f"  pov: {analysis.pov}")
    print(f"  story_structure: {analysis.story_structure}")
    print(f"  characters: {len(analysis.characters)}")
    print(f"  world_bible: {len(analysis.world_bible)} entries")
    for w in analysis.world_bible:
        print(f"    - {w.entry_type}: {w.title}")
    print(f"  arcs: {len(analysis.story_arcs)}")
    print(f"  sequences: {len(analysis.sequences)}")

    validated = analysis.model_dump()
    with open("data/test_final_result.json", "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)
    print("\nSaved to data/test_final_result.json")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
