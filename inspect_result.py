import json

result = json.load(open("data/test_new_prompt_result.json", "r"))

print("=== world_bible entries ===")
for i, w in enumerate(result.get("world_bible", [])):
    print(f"{i}: {json.dumps(w, indent=2)}")

print()
print("=== story_arcs ===")
for i, a in enumerate(result.get("story_arcs", [])):
    print(f"{i}: {json.dumps(a, indent=2)}")

print()
print("=== sequences ===")
for i, s in enumerate(result.get("sequences", [])):
    print(f"{i}: {json.dumps(s, indent=2)}")

print()
print("=== Top-level keys ===")
for k, v in result.items():
    if isinstance(v, str):
        display = v[:80] if v else "(empty)"
        print(f"  {k}: {display}...")
    elif isinstance(v, list):
        print(f"  {k}: [{len(v)} items]")
    else:
        print(f"  {k}: {v}")
