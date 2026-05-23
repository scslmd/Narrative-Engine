from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ...schemas.inference import InferenceMessage, InferenceRequest
from ...settings import settings

if TYPE_CHECKING:
    from app.schemas.generation import CanonGenerationPacket, GenerationPlan


def build_g200_story_generation_plan_request(
    packet: CanonGenerationPacket,
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-200"),
        max_tokens=4000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "You are the generation planner. Produce deterministic JSON with premise, logline, "
                    "chapter plans, canon obligations, and intentional differences. "
                    "Return ONLY one valid JSON object."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(packet.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-200",
            "role": "generation_planner",
            "packet_id": packet.packet_id,
        },
    )


def build_g300_chapter_generation_request(
    packet: CanonGenerationPacket,
    plan: GenerationPlan,
    chapter_id: str,
    prior_summaries: list[str],
    default_model: str | None,
) -> InferenceRequest:
    payload = {
        "packet_id": packet.packet_id,
        "chapter_id": chapter_id,
        "premise": plan.premise,
        "logline": plan.logline,
        "canon_obligations": plan.canon_obligations,
        "intentional_differences": plan.intentional_differences,
        "characters": [item.model_dump(mode="json") for item in packet.characters],
        "world_bible": [item.model_dump(mode="json") for item in packet.world_bible],
        "continuity_threads": [item.model_dump(mode="json") for item in packet.continuity_threads],
        "prior_summaries": prior_summaries[-4:],
    }
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-300"),
        max_tokens=settings.inference_max_tokens("G-300"),
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "Draft the chapter as markdown while preserving locked canon constraints. "
                    "Return ONLY chapter prose markdown with no analysis/preamble/code fences."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-300",
            "role": "generation_drafter",
            "packet_id": packet.packet_id,
            "chapter_id": chapter_id,
        },
    )


def build_g350_canon_repair_request(
    packet: CanonGenerationPacket,
    artifact_text: str,
    gate_reasons: list[str],
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-350"),
        max_tokens=4000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "Repair canon contradictions while preserving intended story intent. "
                    "Return ONLY the repaired artifact markdown text (no JSON, no explanations, no code fences)."
                ),
            ),
            InferenceMessage(
                role="user",
                content=(
                    f"Gate reasons: {gate_reasons}\n"
                    f"Canon policy: {packet.canon_policy.model_dump(mode='json')}\n"
                    f"Artifact:\n{artifact_text}"
                ),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-350",
            "role": "generation_gate",
            "packet_id": packet.packet_id,
        },
    )


def build_g400_manuscript_assembly_request(
    packet: CanonGenerationPacket,
    chapter_artifacts: list[dict[str, str]],
    default_model: str | None,
) -> InferenceRequest:
    return InferenceRequest(
        model=default_model,
        temperature=settings.inference_temperature("G-400"),
        max_tokens=6000,
        messages=[
            InferenceMessage(
                role="system",
                content=(
                    "Assemble the chapter artifacts into a cohesive manuscript. "
                    "Return ONLY manuscript markdown text with consistent chapter ordering and transitions."
                ),
            ),
            InferenceMessage(
                role="user",
                content=json.dumps(
                    {
                        "packet_id": packet.packet_id,
                        "chapter_artifacts": chapter_artifacts,
                    },
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                ),
            ),
        ],
        metadata={
            "mode": "generation_phase",
            "phase": "G-400",
            "role": "generation_compiler",
            "packet_id": packet.packet_id,
        },
    )
