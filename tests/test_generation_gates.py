from __future__ import annotations

from app.schemas.generation import (
    CanonGenerationPacket,
    CanonPolicy,
    CanonicalCharacterSnapshot,
    ContinuityStrictness,
    GenerationMode,
    GenerationPlan,
)
from app.services.generation_gates import GenerationGateService


def _packet(
    forbidden: list[str] | None = None,
    characters: list[CanonicalCharacterSnapshot] | None = None,
    strictness: ContinuityStrictness | None = None,
) -> CanonGenerationPacket:
    return CanonGenerationPacket(
        packet_id="packet-1",
        source_project_id="source",
        target_project_id="target",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        generation_brief="brief",
        foundation_snapshot={"premise": "premise"},
        characters=characters if characters is not None else [CanonicalCharacterSnapshot(character_id="char-1", display_name="Aria")],
        canon_policy=CanonPolicy(
            forbidden_contradictions=forbidden if forbidden is not None else ["Aria dies"],
            continuity_strictness=strictness if strictness is not None else ContinuityStrictness.REPAIR_ONCE,
        ),
    )


def _plan(
    obligations: list[str] | None = None,
) -> GenerationPlan:
    return GenerationPlan(
        plan_id="plan-1",
        project_id="target",
        packet_id="packet-1",
        mode=GenerationMode.SAME_PROJECT_SIDE_STORY,
        premise="premise",
        logline="logline",
        canon_obligations=obligations or ["character:char-1"],
    )


# -- Existing tests --


def test_generation_gates_block_forbidden_contradiction() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies in this chapter.")
    assert result.passed is False
    assert gates.should_block(result, packet.canon_policy) is True


def test_generation_gates_validate_plan_known_character() -> None:
    gates = GenerationGateService()
    packet = _packet()
    plan = _plan()
    result = gates.check_generation_plan(packet, plan)
    assert result.passed is True


# -- New tests --


def test_chapter_draft_passes_when_no_contradictions_present() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria walks through the garden peacefully.")
    assert result.passed is True
    assert len(result.reasons) == 0


def test_chapter_draft_detects_multiple_forbidden_contradictions() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=["Aria dies", "The kingdom falls"])
    draft = "Aria dies in battle and the kingdom falls to ruin."
    result = gates.check_chapter_draft(packet, "chapter-1", draft)
    assert result.passed is False
    assert len(result.reasons) == 2
    assert any("Aria dies" in r for r in result.reasons)
    assert any("The kingdom falls" in r for r in result.reasons)


def test_chapter_draft_is_case_insensitive() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=["aria dies"])
    draft = "FORBIDDEN: ARIA DIES IN THIS CHAPTER."
    result = gates.check_chapter_draft(packet, "chapter-1", draft)
    assert result.passed is False
    assert len(result.reasons) == 1


def test_manuscript_gate_blocks_forbidden_contradiction() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=["the dragon returns"])
    manuscript = "In the final chapter, the dragon returns to destroy everything."
    result = gates.check_manuscript(packet, manuscript)
    assert result.passed is False
    assert result.gate_name == "manuscript_canon_congruence"
    assert any("the dragon returns" in r for r in result.reasons)


def test_manuscript_gate_passes_clean_manuscript() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=["the dragon returns"])
    manuscript = "The hero journeys to the mountains and finds peace."
    result = gates.check_manuscript(packet, manuscript)
    assert result.passed is True
    assert len(result.reasons) == 0


def test_generation_plan_fails_with_unknown_character_obligation() -> None:
    gates = GenerationGateService()
    packet = _packet(characters=[CanonicalCharacterSnapshot(character_id="char-1", display_name="Aria")])
    plan = _plan(obligations=["character:char-unknown"])
    result = gates.check_generation_plan(packet, plan)
    assert result.passed is False
    assert any("unknown character obligation" in r for r in result.reasons)


def test_generation_plan_passes_non_character_obligations() -> None:
    gates = GenerationGateService()
    packet = _packet(characters=[CanonicalCharacterSnapshot(character_id="char-1", display_name="Aria")])
    plan = _plan(obligations=["world:fire-magic-exists", "arc:hero-journey"])
    result = gates.check_generation_plan(packet, plan)
    assert result.passed is True
    assert len(result.reasons) == 0


def test_build_repair_prompt_returns_correct_structure() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    req = gates.build_repair_prompt(packet, "draft text", result)
    assert req.model is None
    assert req.temperature == 0.1
    assert req.max_tokens == 4000


def test_build_repair_prompt_includes_gate_name_reasons_policy_and_artifact() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=["Aria dies"])
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    req = gates.build_repair_prompt(packet, "this is the artifact text", result)
    user_msg = [m for m in req.messages if m.role == "user"][0]
    assert result.gate_name in user_msg.content
    assert str(result.reasons) in user_msg.content
    policy_dict = packet.canon_policy.model_dump(mode="json")
    assert "forbidden_contradictions" in user_msg.content
    assert "repair_once" in user_msg.content
    assert "this is the artifact text" in user_msg.content


def test_should_block_returns_false_when_gate_passed() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Clean text.")
    assert result.passed is True
    for strictness in ContinuityStrictness:
        policy = CanonPolicy(continuity_strictness=strictness)
        assert gates.should_block(result, policy) is False


def test_should_block_warn_returns_false_when_gate_failed() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    assert result.passed is False
    policy = CanonPolicy(continuity_strictness=ContinuityStrictness.WARN)
    assert gates.should_block(result, policy) is False


def test_should_block_block_returns_true_when_gate_failed() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    assert result.passed is False
    policy = CanonPolicy(continuity_strictness=ContinuityStrictness.BLOCK)
    assert gates.should_block(result, policy) is True


def test_should_block_repair_once_returns_true_when_gate_failed() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    assert result.passed is False
    policy = CanonPolicy(continuity_strictness=ContinuityStrictness.REPAIR_ONCE)
    assert gates.should_block(result, policy) is True


def test_should_block_repair_twice_returns_true_when_gate_failed() -> None:
    gates = GenerationGateService()
    packet = _packet()
    result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies.")
    assert result.passed is False
    policy = CanonPolicy(continuity_strictness=ContinuityStrictness.REPAIR_TWICE)
    assert gates.should_block(result, policy) is True


def test_gate_name_values_are_correct() -> None:
    gates = GenerationGateService()
    packet = _packet()

    plan = _plan()
    plan_result = gates.check_generation_plan(packet, plan)
    assert plan_result.gate_name == "plan_references_known_canon"

    chapter_result = gates.check_chapter_draft(packet, "chapter-1", "text")
    assert chapter_result.gate_name == "chapter_canon_congruence"

    manuscript_result = gates.check_manuscript(packet, "text")
    assert manuscript_result.gate_name == "manuscript_canon_congruence"


def test_empty_forbidden_contradictions_all_gates_pass() -> None:
    gates = GenerationGateService()
    packet = _packet(forbidden=[])

    chapter_result = gates.check_chapter_draft(packet, "chapter-1", "Aria dies in this chapter.")
    assert chapter_result.passed is True

    manuscript_result = gates.check_manuscript(packet, "Aria dies everywhere.")
    assert manuscript_result.passed is True
