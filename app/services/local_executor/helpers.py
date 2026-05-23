from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ...schemas.inference import InferenceMessage, InferenceRequest


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def provider_backend_version(raw_response: dict[str, Any]) -> str | None:
    for key in ("backend_version", "provider_version", "version"):
        value = raw_response.get(key)
        if value is not None:
            return str(value)
    return None


def checker_runtime_response(role_result: Any) -> dict[str, Any] | None:
    runtime_response = role_result.metadata.get("runtime_response")
    return runtime_response if isinstance(runtime_response, dict) else None


def phase_step_name(phase: str) -> str:
    if phase == "P-100":
        return "architect"
    if phase == "P-200":
        return "sequencer"
    if phase == "P-300":
        return "drafter"
    if phase == "P-400":
        return "compiler"
    if phase == "G-200":
        return "generation_planner"
    if phase == "G-300":
        return "generation_drafter"
    if phase == "G-350":
        return "generation_gate"
    if phase == "G-400":
        return "generation_compiler"
    if phase == "M-500":
        return "manuscript_assist"
    if phase == "M-550":
        return "manuscript_assist_repair"
    return phase


def find_user_message_index(messages: list[InferenceMessage]) -> int | None:
    for idx, msg in enumerate(messages):
        if msg.role == "user":
            return idx
    return None


def inject_scene_context(
    request: InferenceRequest,
    context_prompt: str,
) -> InferenceRequest:
    if not context_prompt:
        return request

    user_idx = find_user_message_index(request.messages)
    if user_idx is None:
        return request

    existing_content = request.messages[user_idx].content
    new_messages = list(request.messages)
    new_messages[user_idx] = InferenceMessage(
        role=request.messages[user_idx].role,
        content=f"{existing_content}\n\n{context_prompt}",
    )
    return request.model_copy(update={"messages": new_messages})


def require_supported_job_phase(phase: str) -> str:
    if phase in {"P-100", "P-200", "P-300", "P-400", "G-200", "G-300", "G-350", "G-400", "M-500", "M-550"}:
        return phase
    raise ValueError(f"Unsupported job phase: {phase}")


def upstream_artifact_sources(step_name: str) -> list[tuple[str, str]]:
    if step_name == "sequencer":
        return [("architect_output", "architect_p100")]
    if step_name == "drafter":
        return [("sequence", "sequence"), ("architect_output", "architect_p100")]
    if step_name == "compiler":
        return [("architect_output", "architect_p100"), ("sequence", "sequence"), ("chapter_1", "chapter_1")]
    return []


def normalized_p100_job_request(request_payload: dict[str, object]) -> dict[str, object]:
    payload = dict(request_payload.get("payload", {}))
    return {
        "phase": request_payload.get("phase"),
        "payload": payload,
    }
