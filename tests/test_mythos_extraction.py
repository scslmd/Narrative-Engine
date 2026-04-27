from __future__ import annotations


def test_archetypal_pattern_fields():
    from app.schemas.mythos_extraction import ArchetypalPattern
    pattern = ArchetypalPattern(
        name="hubris-fall-redemption",
        description="Hero rises through arrogance, falls through divine retribution",
        character_type="hubristic hero",
        narrative_beats=["rise", "transgression", "punishment", "suffering", "apotheosis"],
        examples_from_text=["Oedipus defies prophecy"],
    )
    assert pattern.name == "hubris-fall-redemption"
    assert len(pattern.narrative_beats) == 5


def test_narrative_structure_fields():
    from app.schemas.mythos_extraction import NarrativeStructure
    structure = NarrativeStructure(
        name="cyclical tragedy",
        phases=["call", "transgression", "punishment", "redemption"],
        tension_curve="escalating divine retribution",
        resolution_type="bittersweet apotheosis",
    )
    assert len(structure.phases) == 4


def test_cosmic_rule_fields():
    from app.schemas.mythos_extraction import CosmicRule
    rule = CosmicRule(
        rule="Fate cannot be escaped, only fulfilled",
        enforcement="Gods act as agents of moira (fate)",
        exceptions=["prophecies can be misinterpreted"],
    )
    assert len(rule.exceptions) == 1


def test_symbolic_motif_fields():
    from app.schemas.mythos_extraction import SymbolicMotif
    motif = SymbolicMotif(
        symbol="serpent",
        meaning="transformation, hidden knowledge",
        narrative_function="marks threshold between worlds",
    )
    assert motif.narrative_function


def test_mythos_entity_fields():
    from app.schemas.mythos_extraction import MythosEntity
    entity = MythosEntity(
        name="Zeus",
        entity_type="deity",
        archetype="sky father",
        domain_or_power="oaths, hospitality, strangers",
        canonical_facts=["King of the gods"],
    )
    assert entity.entity_type == "deity"


def test_relationship_fields():
    from app.schemas.mythos_extraction import Relationship
    rel = Relationship(
        source="Zeus",
        target="Hades",
        relationship_type="rivalry",
        description="Brothers who divided dominion",
    )
    assert rel.relationship_type == "rivalry"


def test_mythos_extraction_analysis_defaults():
    from app.schemas.mythos_extraction import MythosExtractionAnalysis
    analysis = MythosExtractionAnalysis(
        source_corpus="Greek Mythology",
        generation_mode="same_world",
    )
    assert analysis.archetypal_patterns == []
    assert analysis.key_entities == []
    assert analysis.thematic_spine == ""
