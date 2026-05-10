from __future__ import annotations

from difflib import SequenceMatcher


class DeduplicationEngine:
    FUZZY_THRESHOLD = 0.85

    def match_character(self, name: str, existing: list[dict]) -> dict | None:
        name_lower = name.lower()
        for char in existing:
            if char["display_name"].lower() == name_lower:
                return {"match_type": "exact", "character_id": char["character_id"], "display_name": char["display_name"]}
            aliases = char.get("aliases", [])
            if any(a.lower() == name_lower for a in aliases):
                return {"match_type": "exact", "character_id": char["character_id"], "display_name": char["display_name"]}

        best_match: dict | None = None
        best_ratio = 0.0
        for char in existing:
            ratio = SequenceMatcher(None, name_lower, char["display_name"].lower()).ratio()
            if ratio > best_ratio and ratio >= self.FUZZY_THRESHOLD:
                best_ratio = ratio
                best_match = {"match_type": "fuzzy", "character_id": char["character_id"], "display_name": char["display_name"], "confidence": ratio}
            for alias in char.get("aliases", []):
                alias_ratio = SequenceMatcher(None, name_lower, alias.lower()).ratio()
                if alias_ratio > best_ratio and alias_ratio >= self.FUZZY_THRESHOLD:
                    best_ratio = alias_ratio
                    best_match = {"match_type": "fuzzy", "character_id": char["character_id"], "display_name": char["display_name"], "confidence": alias_ratio}

        return best_match

    def match_world_entry(self, entry_type: str, title: str, existing: list[dict]) -> dict | None:
        for entry in existing:
            if entry["entry_type"].lower() == entry_type.lower() and entry["title"].lower() == title.lower():
                return {"match_type": "exact", "entry_type": entry["entry_type"], "title": entry["title"]}
        return None

    def deduplicate_relationship_pairs(self, pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen: set[tuple[str, str]] = set()
        unique: list[tuple[str, str]] = []
        for source, target in pairs:
            key = tuple(sorted([source.lower(), target.lower()]))
            if key not in seen:
                seen.add(key)
                unique.append((source, target))
        return unique

    def enrich_character(self, existing: dict, new_data: dict) -> dict:
        enriched = dict(existing)
        for key, value in new_data.items():
            if key in ("character_id", "project_id"):
                continue
            current = enriched.get(key, "")
            if not current and value:
                enriched[key] = value
            elif isinstance(current, list) and isinstance(value, list):
                for item in value:
                    if item not in current:
                        current.append(item)
        return enriched
