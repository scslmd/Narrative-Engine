from __future__ import annotations

from app.schemas.manuscript_assist import ManuscriptAssistPacket, TextRange
from app.services.runtime_prompts import (
    build_m500_manuscript_assist_request,
    build_m550_manuscript_repair_request,
)


def _packet() -> ManuscriptAssistPacket:
    return ManuscriptAssistPacket(
        assist_id="assist-1",
        project_id="proj-1",
        document_id="doc-1",
        assist_kind="line_edit_selection",
        instruction="Tighten prose",
        document_title="Chapter 1",
        document_content="Hello world",
        text_range=TextRange(
            start_offset=0,
            end_offset=5,
            selected_text="Hello",
            anchor_before="",
            anchor_after=" world",
        ),
    )


def test_build_m500_prompt_has_metadata() -> None:
    request = build_m500_manuscript_assist_request(_packet(), default_model="model-x")
    assert request.metadata["phase"] == "M-500"
    assert request.metadata["assist_id"] == "assist-1"


def test_build_m550_prompt_has_gate_reasons() -> None:
    request = build_m550_manuscript_repair_request(_packet(), ["canon mismatch"], default_model="model-x")
    assert request.metadata["phase"] == "M-550"
    assert "canon mismatch" in request.messages[1].content
