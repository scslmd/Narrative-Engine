from __future__ import annotations

import json

from ...schemas.inference import InferenceMessage, InferenceRequest


def build_narrative_analysis_request(
    *,
    story_text: str,
    source_corpus: str | None = None,
    generation_mode: str = "same_world",
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for narrative pattern extraction.

    The LLM should return a JSON object matching PatternExtractionAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output with patterns and entities.
    Truncates story_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = story_text[:24_000]
    corpus_hint = (
        f"Source tradition hint: {source_corpus}"
        if source_corpus
        else "AI should identify the source tradition from the text."
    )

    system_prompt = (
        "You are a narrative analysis AI for Narrative-Engine. You analyze narrative texts "
        "and extract storytelling DNA — archetypal patterns, narrative structure, voice profile, "
        "thematic constraints, world rules, and symbolic motifs.\n\n"
        f"{corpus_hint}\n\n"
        f"Generation mode: {generation_mode}\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "source_type": "narrative",\n'
        '  "source_corpus": "<string - identified tradition or author>",\n'
        '  "generation_mode": "<same_world | new_characters | transposed>",\n'
        '  "archetypal_patterns": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "description": "<string>",\n'
        '      "character_type": "<string>",\n'
        '      "narrative_beats": [],\n'
        '      "examples_from_text": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_structures": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "phases": [],\n'
        '      "tension_curve": "<string>",\n'
        '      "resolution_type": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "world_rules": [\n'
        '    {\n'
        '      "rule": "<string>",\n'
        '      "enforcement": "<string>",\n'
        '      "exceptions": []\n'
        '    }\n'
        '  ],\n'
        '  "symbolic_motifs": [\n'
        '    {\n'
        '      "symbol": "<string>",\n'
        '      "meaning": "<string>",\n'
        '      "narrative_function": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "tone_and_voice_direction": "<string>",\n'
        '  "narrative_pattern": {\n'
        '    "pacing": "<string>",\n'
        '    "chapter_structure": "<string>",\n'
        '    "conflict_type": "<string>",\n'
        '    "dialogue_style": "<string>",\n'
        '    "scene_transition": "<string>"\n'
        '  },\n'
        '  "voice_profile": {\n'
        '    "narrative_voice": "<string>",\n'
        '    "sentence_rhythm": "<string>",\n'
        '    "descriptive_density": "<string>",\n'
        '    "humor_level": "<string>",\n'
        '    "emotional_temperature": "<string>"\n'
        '  },\n'
        '  "thematic_constraints": [\n'
        '    {\n'
        '      "theme": "<string>",\n'
        '      "moral_stance": "<string>",\n'
        '      "recurring_questions": [],\n'
        '      "forbidden_elements": []\n'
        '    }\n'
        '  ],\n'
        '  "key_entities": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "entity_type": "<character | location | concept | force>",\n'
        '      "archetype": "<string>",\n'
        '      "domain_or_power": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "entity_relationships": [\n'
        '    {\n'
        '      "source": "<string>",\n'
        '      "target": "<string>",\n'
        '      "relationship_type": "<string>",\n'
        '      "description": "<string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Focus on PATTERNS and STRUCTURES, not just cataloging entities. "
        "Extract the storytelling DNA — how stories are told in this tradition, "
        "what narrative rules govern them, what archetypal journeys characters undertake.\n\n"
        'JSON STRUCTURE RULES:\n'
        '- All arrays must be JSON arrays [], not strings.\n'
        '- Use null (not empty string) for missing optional fields where shown.\n'
        '- Do not include trailing commas in JSON objects or arrays.\n'
        '- The "generation_mode" field must exactly match: "same_world", "new_characters", or "transposed".\n\n'
        "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
    )

    user_content = (
        f"Analyze the following narrative text and extract its storytelling DNA, "
        f"archetypal patterns, narrative structures, world rules, voice profile, "
        f"and symbolic motifs:\n\n"
        f"{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "narrative_extraction",
            "role": "narrative_analyzer",
            "source": "narrative-analysis",
        },
    )


def build_mythos_analysis_request(
    *,
    mythos_text: str,
    source_corpus: str | None = None,
    generation_mode: str = "same_world",
    default_model: str | None,
) -> InferenceRequest:
    """Build inference request for mythos pattern extraction.

    The LLM should return a JSON object matching MythosExtractionAnalysis structure.
    Uses temperature=0.1 for deterministic output.
    max_tokens=16000 to fit full JSON output with patterns and entities.
    Truncates mythos_text to 24,000 chars for single-pass analysis.
    """
    truncated_text = mythos_text[:24_000]
    corpus_hint = (
        f"Source tradition hint: {source_corpus}"
        if source_corpus
        else "AI should identify the source tradition from the text."
    )

    system_prompt = (
        "You are a mythology analysis AI for Narrative-Engine. You analyze mythological texts "
        "and extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs.\n\n"
        f"{corpus_hint}\n\n"
        f"Generation mode: {generation_mode}\n\n"
        "OUTPUT — Return a JSON object with EXACTLY these keys:\n\n"
        '{\n'
        '  "source_corpus": "<string - identified tradition, e.g., Greek Mythology>",\n'
        '  "generation_mode": "<same_world | transposed | pure_pattern>",\n'
        '  "archetypal_patterns": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "description": "<string>",\n'
        '      "character_type": "<string>",\n'
        '      "narrative_beats": [],\n'
        '      "examples_from_text": []\n'
        '    }\n'
        '  ],\n'
        '  "narrative_structures": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "phases": [],\n'
        '      "tension_curve": "<string>",\n'
        '      "resolution_type": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "cosmic_rules": [\n'
        '    {\n'
        '      "rule": "<string>",\n'
        '      "enforcement": "<string>",\n'
        '      "exceptions": []\n'
        '    }\n'
        '  ],\n'
        '  "symbolic_motifs": [\n'
        '    {\n'
        '      "symbol": "<string>",\n'
        '      "meaning": "<string>",\n'
        '      "narrative_function": "<string>"\n'
        '    }\n'
        '  ],\n'
        '  "thematic_spine": "<string>",\n'
        '  "emotional_promise": "<string>",\n'
        '  "tone_and_voice_direction": "<string>",\n'
        '  "key_entities": [\n'
        '    {\n'
        '      "name": "<string>",\n'
        '      "entity_type": "<deity | location | concept | force>",\n'
        '      "archetype": "<string>",\n'
        '      "domain_or_power": "<string>",\n'
        '      "canonical_facts": []\n'
        '    }\n'
        '  ],\n'
        '  "entity_relationships": [\n'
        '    {\n'
        '      "source": "<string>",\n'
        '      "target": "<string>",\n'
        '      "relationship_type": "<string>",\n'
        '      "description": "<string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Focus on PATTERNS and STRUCTURES, not just cataloging entities. "
        "Extract the storytelling DNA — how stories are told in this tradition, "
        "what narrative rules govern them, what archetypal journeys characters undertake.\n\n"
        'JSON STRUCTURE RULES:\n'
        '- All arrays must be JSON arrays [], not strings.\n'
        '- Use null (not empty string) for missing optional fields where shown.\n'
        '- Do not include trailing commas in JSON objects or arrays.\n'
        '- The "generation_mode" field must exactly match: "same_world", "transposed", or "pure_pattern".\n'
        '- The "entity_type" field must be one of: "deity", "location", "concept", "force".\n\n'
    )

    user_content = (
        f"Analyze the following mythological text and extract its archetypal patterns, "
        f"narrative structures, cosmic rules, and symbolic motifs:\n\n"
        f"{truncated_text}"
    )

    return InferenceRequest(
        model=str(default_model or "").strip() or None,
        temperature=0.1,
        max_tokens=16000,
        messages=[
            InferenceMessage(role="system", content=system_prompt),
            InferenceMessage(role="user", content=user_content),
        ],
        metadata={
            "mode": "mythos_extraction",
            "role": "mythos_analyzer",
        },
    )
