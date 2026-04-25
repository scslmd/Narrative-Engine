from __future__ import annotations

import json

result = json.load(open("data/test_final_result.json", "r"))

print("=== TOP-LEVEL FIELDS ===")
for k, v in result.items():
    if isinstance(v, str):
        display = v[:100] if v else "(empty)"
        print(f"  {k}: {display}...")
    elif isinstance(v, list):
        print(f"  {k}: [{len(v)} items]")
    else:
        print(f"  {k}: {v}")

print()
print("=== CHARACTERS ===")
for i, c in enumerate(result.get("characters", [])):
    print(f"{i}: {c.get('name')} | role={c.get('role')}")
    for f in ["external_goal", "internal_need", "core_fear", "primary_strength", "fatal_flaw", "change_axis"]:
        val = c.get(f, "")
        if val:
            print(f"    {f}: {val}")
    for f in ["contradictions", "secrets", "values", "taboos", "continuity_facts"]:
        val = c.get(f, [])
        if val:
            print(f"    {f}: {val}")

print()
print("=== WORLD BIBLE ===")
for i, w in enumerate(result.get("world_bible", [])):
    print(f"{i}: {w.get('entry_type')}: {w.get('title')}")
    print(f"    summary: {w.get('summary', '')[:120]}")
    facts = w.get("canonical_facts", [])
    if facts:
        print(f"    facts: {facts}")

print()
print("=== STORY ARCS ===")
for i, a in enumerate(result.get("story_arcs", [])):
    print(f"{i}: {a.get('name')}")
    print(f"    summary: {a.get('summary', '')[:100]}")
    sm = a.get("stage_map", [])
    if sm:
        print(f"    stages: {sm}")
    tags = a.get("tags", [])
    if tags:
        print(f"    tags: {tags}")

print()
print("=== SEQUENCES ===")
for i, s in enumerate(result.get("sequences", [])):
    print(f"{i}: {s.get('title')}")
    print(f"    summary: {s.get('summary', '')[:100]}")
    ch = s.get("chapters", [])
    if ch:
        print(f"    chapters: {ch}")

print()
print("=== TYPE VALIDATION ===")
valid_roles = {"protagonist", "antagonist", "mentor", "deuteragonist", "foil", "supporting", "minor"}
valid_pov = {"FIRST", "SECOND", "THIRD_LIMITED", "THIRD_OMNI", "THIRD_OBJECTIVE", "THIRD_MULTIPLE", "OTHER"}
valid_structures = {
    "SAVE_THE_CAT", "THREE_ACT", "HERO_JOURNEY", "FREYTAGS_PYRAMID",
    "KISHOTENKETSU", "FICHTEAN_CURVE", "SEVEN_POINT_STRUCTURE",
    "SEVEN_KEY_STEPS", "SNOWFLAKE_METHOD", "BRAINDUMP", "OTHER",
}
valid_complexity = {"LOW", "MEDIUM", "HIGH"}
valid_wb_types = {"location", "culture", "magic_system", "technology", "organization", "history", "creature", "concept", "other"}

issues = []

# Enums
if result.get("pov") not in valid_pov:
    issues.append(f"Invalid pov: {result.get('pov')}")
else:
    print(f"  pov: {result.get('pov')} OK")

if result.get("story_structure") not in valid_structures:
    issues.append(f"Invalid story_structure: {result.get('story_structure')}")
else:
    print(f"  story_structure: {result.get('story_structure')} OK")

if result.get("complexity_level") not in valid_complexity:
    issues.append(f"Invalid complexity_level: {result.get('complexity_level')}")
else:
    print(f"  complexity_level: {result.get('complexity_level')} OK")

# Characters
for c in result.get("characters", []):
    if c.get("role") not in valid_roles:
        issues.append(f"Invalid role: {c.get('name')} = {c.get('role')}")
    for f in ["external_goal", "internal_need", "core_fear", "primary_strength", "fatal_flaw", "change_axis", "backstory", "voice_notes"]:
        val = c.get(f)
        if val and not isinstance(val, str):
            issues.append(f"Char '{c.get('name')}.'{f} is not string: {type(val)}")
    for f in ["contradictions", "secrets", "values", "taboos", "continuity_facts"]:
        val = c.get(f)
        if val and not isinstance(val, list):
            issues.append(f"Char '{c.get('name')}.'{f} is not list: {type(val)}")
        if val and isinstance(val, list):
            for item in val:
                if not isinstance(item, str):
                    issues.append(f"Char '{c.get('name')}.'{f} has non-string: {item}")

# World bible
for i, w in enumerate(result.get("world_bible", [])):
    if w.get("entry_type") not in valid_wb_types:
        issues.append(f"WB[{i}] entry_type invalid: {w.get('entry_type')}")

# Arcs
for i, a in enumerate(result.get("story_arcs", [])):
    if not isinstance(a.get("stage_map"), list):
        issues.append(f"Arc[{i}] stage_map not list")
    if not isinstance(a.get("tags"), list):
        issues.append(f"Arc[{i}] tags not list")

# Sequences
for i, s in enumerate(result.get("sequences", [])):
    if not isinstance(s.get("chapters"), list):
        issues.append(f"Seq[{i}] chapters not list")

# narrative_constraints
nc = result.get("narrative_constraints", [])
if not isinstance(nc, list):
    issues.append("narrative_constraints not a list")

if issues:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nALL TYPE CHECKS PASSED - No issues")

print()
print("=== CONTENT QUALITY ===")
genre = result.get("genre", "")
if genre == genre.title() or " " in genre:
    print(f"  genre \"{genre}\": OK")
else:
    print(f"  genre \"{genre}\": WARNING - should be title case")

characters = result.get("characters", [])
print(f"  characters: {len(characters)} (need >= 1)")

roles = [c.get("role") for c in characters]
if "protagonist" in roles:
    print(f"  protagonist: FOUND")
else:
    print(f"  protagonist: MISSING")

print(f"  pov: {result.get('pov')}")
print(f"  structure: {result.get('story_structure')}")
print(f"  world_bible: {len(result.get('world_bible', []))} entries")
print(f"  story_arcs: {len(result.get('story_arcs', []))}")
print(f"  sequences: {len(result.get('sequences', []))}")
print(f"  narrative_constraints: {len(nc)} items")
