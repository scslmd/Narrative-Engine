from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArchetypalPattern:
    name: str
    description: str
    character_type: str
    narrative_beats: list[str] = field(default_factory=list)
    examples_from_text: list[str] = field(default_factory=list)


@dataclass
class NarrativeStructure:
    name: str
    phases: list[str] = field(default_factory=list)
    tension_curve: str = ""
    resolution_type: str = ""


@dataclass
class CosmicRule:
    rule: str
    enforcement: str
    exceptions: list[str] = field(default_factory=list)


@dataclass
class SymbolicMotif:
    symbol: str
    meaning: str
    narrative_function: str = ""


@dataclass
class MythosEntity:
    name: str
    entity_type: str  # deity | location | concept | force
    archetype: str
    domain_or_power: str
    canonical_facts: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source: str
    target: str
    relationship_type: str
    description: str = ""


@dataclass
class MythosExtractionAnalysis:
    source_corpus: str
    generation_mode: str  # same_world | transposed | pure_pattern

    # Pattern layer (core)
    archetypal_patterns: list[ArchetypalPattern] = field(default_factory=list)
    narrative_structures: list[NarrativeStructure] = field(default_factory=list)
    cosmic_rules: list[CosmicRule] = field(default_factory=list)
    symbolic_motifs: list[SymbolicMotif] = field(default_factory=list)

    # Thematic layer (foundation)
    thematic_spine: str = ""
    emotional_promise: str = ""
    tone_and_voice_direction: str = ""

    # Entity layer (light — for same_world mode)
    key_entities: list[MythosEntity] = field(default_factory=list)
    entity_relationships: list[Relationship] = field(default_factory=list)
