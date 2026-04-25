from __future__ import annotations

import json
import pytest
from app.services.entity_intake import NewEntity


def test_new_entity_dataclass():
    entity = NewEntity(
        name="Soraya",
        entity_type="character",
        inferred_archetype="mysterious ally",
        inferred_goal="Protect the caravan",
        raw_evidence="Soraya watched from the shadows, her hand never far from her dagger.",
    )
    assert entity.name == "Soraya"
    assert entity.entity_type == "character"


def test_extract_proper_noun_candidates():
    from app.services.entity_intake import extract_proper_noun_candidates

    text = "Khal marched ahead while Soraya watched from the shadows."
    candidates = extract_proper_noun_candidates(text)
    assert "Soraya" in candidates


class FakeInferencerIntake:
    descriptor = type("Descriptor", (), {"default_model": "test"})()

    def generate_text(self, request):
        from app.schemas.inference import InferenceResponse, InferenceUsage

        return InferenceResponse(
            model="test",
            content=json.dumps(
                {
                    "name": "Soraya",
                    "archetype": "mysterious ally",
                    "goal": "Protect the caravan",
                }
            ),
            backend="stub",
            finish_reason="completed",
            usage=InferenceUsage(),
        )


def test_intake_detects_new_character():
    from app.services.entity_intake import EntityIntakeService

    service = EntityIntakeService(inferencer=FakeInferencerIntake())
    entities = service.intake_new_entities(
        draft_text="Soraya watched from the shadows while Khal marched ahead.",
        known_character_ids={"Khal": "char-001"},
    )
    assert len(entities) >= 1
    assert any(e.name == "Soraya" for e in entities)


def test_intake_skips_known_characters():
    from app.services.entity_intake import EntityIntakeService

    service = EntityIntakeService(inferencer=FakeInferencerIntake())
    entities = service.intake_new_entities(
        draft_text="Khal said nothing.",
        known_character_ids={"Khal": "char-001"},
    )
    assert not any(e.name == "Khal" for e in entities)


def test_intake_returns_empty_for_no_unknowns():
    from app.services.entity_intake import EntityIntakeService

    service = EntityIntakeService(inferencer=FakeInferencerIntake())
    entities = service.intake_new_entities(
        draft_text="Khal said nothing.",
        known_character_ids={"Khal": "char-001"},
    )
    assert entities == []


def test_intake_limits_to_max_entities():
    from app.services.entity_intake import EntityIntakeService

    service = EntityIntakeService(inferencer=FakeInferencerIntake())
    entities = service.intake_new_entities(
        draft_text="Alice met Bob and Charlie and Dave at the inn.",
        known_character_ids={},
    )
    assert len(entities) <= service.MAX_ENTITIES_PER_DRAFT


def test_intake_handles_inference_error_gracefully():
    from app.services.entity_intake import EntityIntakeService

    class FailingInferencer:
        descriptor = type("Descriptor", (), {"default_model": "test"})()

        def generate_text(self, request):
            from app.inference.base import InferenceBackendError

            raise InferenceBackendError(
                "timeout", category="timeout", code="TIMEOUT", finish_reason="error", retryable=True
            )

    service = EntityIntakeService(inferencer=FailingInferencer())
    entities = service.intake_new_entities(
        draft_text="Unknown character appeared.",
        known_character_ids={},
    )
    assert entities == []


def test_intake_handles_invalid_json_gracefully():
    from app.services.entity_intake import EntityIntakeService

    class BadJsonInferencer:
        descriptor = type("Descriptor", (), {"default_model": "test"})()

        def generate_text(self, request):
            from app.schemas.inference import InferenceResponse, InferenceUsage

            return InferenceResponse(
                model="test",
                content="not valid json {",
                backend="stub",
                finish_reason="completed",
                usage=InferenceUsage(),
            )

    service = EntityIntakeService(inferencer=BadJsonInferencer())
    entities = service.intake_new_entities(
        draft_text="Unknown character appeared.",
        known_character_ids={},
    )
    assert entities == []
