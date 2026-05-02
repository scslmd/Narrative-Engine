from __future__ import annotations

from dataclasses import dataclass

from app.schemas.generation import CanonGenerationPacket, CanonPolicy, GenerationPlan
from app.schemas.inference import InferenceMessage, InferenceRequest


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    severity: str
    reasons: list[str]


class GenerationGateService:
    def check_generation_plan(self, packet: CanonGenerationPacket, plan: GenerationPlan) -> GateResult:
        reasons: list[str] = []
        known_character_ids = {character.character_id for character in packet.characters}
        for obligation in plan.canon_obligations:
            if obligation.startswith("character:"):
                _, character_id = obligation.split(":", 1)
                if character_id not in known_character_ids:
                    reasons.append(f"unknown character obligation: {obligation}")
        passed = not reasons
        return GateResult(
            gate_name="plan_references_known_canon",
            passed=passed,
            severity="blocking" if not passed else "info",
            reasons=reasons,
        )

    def check_chapter_draft(self, packet: CanonGenerationPacket, chapter_id: str, draft_text: str) -> GateResult:
        reasons: list[str] = []
        lowered = draft_text.lower()
        for character in packet.characters:
            if character.display_name and character.display_name.lower() not in lowered:
                continue
        for forbidden in packet.canon_policy.forbidden_contradictions:
            if forbidden.lower() in lowered:
                reasons.append(f"forbidden contradiction detected: {forbidden}")
        passed = not reasons
        return GateResult(
            gate_name="chapter_canon_congruence",
            passed=passed,
            severity="blocking" if not passed else "info",
            reasons=reasons,
        )

    def check_manuscript(self, packet: CanonGenerationPacket, manuscript_text: str) -> GateResult:
        reasons: list[str] = []
        lowered = manuscript_text.lower()
        for forbidden in packet.canon_policy.forbidden_contradictions:
            if forbidden.lower() in lowered:
                reasons.append(f"forbidden contradiction detected: {forbidden}")
        passed = not reasons
        return GateResult(
            gate_name="manuscript_canon_congruence",
            passed=passed,
            severity="blocking" if not passed else "info",
            reasons=reasons,
        )

    def build_repair_prompt(
        self,
        packet: CanonGenerationPacket,
        artifact_text: str,
        result: GateResult,
    ) -> InferenceRequest:
        return InferenceRequest(
            model=None,
            temperature=0.1,
            max_tokens=4000,
            messages=[
                InferenceMessage(
                    role="system",
                    content=(
                        "Repair the artifact so it remains faithful to canonical constraints. "
                        "Preserve intent while removing contradictions."
                    ),
                ),
                InferenceMessage(
                    role="user",
                    content=(
                        f"Gate: {result.gate_name}\n"
                        f"Reasons: {result.reasons}\n"
                        f"Canon policy: {packet.canon_policy.model_dump(mode='json')}\n"
                        f"Artifact text:\n{artifact_text}"
                    ),
                ),
            ],
            metadata={
                "mode": "generation_gate_repair",
                "phase": "G-350",
                "role": "generation_gate",
                "packet_id": packet.packet_id,
            },
        )

    def should_block(self, result: GateResult, policy: CanonPolicy) -> bool:
        if result.passed:
            return False
        strictness = policy.continuity_strictness.value if hasattr(policy.continuity_strictness, "value") else policy.continuity_strictness
        return strictness in {"block", "repair_once", "repair_twice"}
