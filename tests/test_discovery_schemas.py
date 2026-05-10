from __future__ import annotations

import pytest

from app.schemas.discovery import (
    CascadeApplyResponse,
    CascadeJobResponse,
    CascadeScanRequest,
    CascadeUndoResponse,
    EntityApprovalUpdate,
    StagedEntitiesResponse,
    StagedEntity,
)


# -- CascadeScanRequest --

def test_cascade_scan_request_minimal():
    req = CascadeScanRequest(
        project_id="proj-1",
        manuscript_text="A short piece of text that is long enough to pass validation checks.",
    )
    assert req.project_id == "proj-1"
    assert req.chunk_size == 8000
    assert req.include_types == ["character", "relationship", "world_bible"]


def test_cascade_scan_request_custom_chunk_and_types():
    req = CascadeScanRequest(
        project_id="proj-2",
        manuscript_text="Another sufficiently long manuscript text for testing purposes here.",
        chunk_size=15000,
        include_types=["character"],
    )
    assert req.chunk_size == 15000
    assert req.include_types == ["character"]


def test_cascade_scan_request_empty_project_id():
    with pytest.raises(Exception):
        CascadeScanRequest(
            project_id="",
            manuscript_text="A short piece of text that is long enough to pass validation checks.",
        )


def test_cascade_scan_request_short_text():
    with pytest.raises(Exception):
        CascadeScanRequest(
            project_id="proj-1",
            manuscript_text="Short",
        )


def test_cascade_scan_request_chunk_size_too_small():
    with pytest.raises(Exception):
        CascadeScanRequest(
            project_id="proj-1",
            manuscript_text="A short piece of text that is long enough to pass validation checks.",
            chunk_size=500,
        )


def test_cascade_scan_request_chunk_size_too_large():
    with pytest.raises(Exception):
        CascadeScanRequest(
            project_id="proj-1",
            manuscript_text="A short piece of text that is long enough to pass validation checks.",
            chunk_size=100000,
        )


# -- CascadeJobResponse --

def test_cascade_job_response_extracting():
    resp = CascadeJobResponse(
        job_id="job-1",
        status="extracting",
        phase="extracting",
        chunk_index=2,
        total_chunks=5,
    )
    assert resp.job_id == "job-1"
    assert resp.status == "extracting"
    assert resp.chunk_index == 2
    assert resp.total_chunks == 5


def test_cascade_job_response_completed():
    resp = CascadeJobResponse(
        job_id="job-2",
        status="completed",
        phase="completed",
        stage_id="stage-1",
    )
    assert resp.stage_id == "stage-1"


def test_cascade_job_response_failed():
    resp = CascadeJobResponse(
        job_id="job-3",
        status="failed",
        phase="extracting",
        error="LLM timeout",
    )
    assert resp.error == "LLM timeout"


# -- StagedEntity --

def test_staged_entity_all_fields():
    entity = StagedEntity(
        entity_id="ent-1",
        entity_type="character",
        entity_json={"name": "Alice"},
        confidence=0.92,
        source_excerpt="Alice walked in.",
        approved=True,
        dedup_action="new",
    )
    assert entity.entity_id == "ent-1"
    assert entity.entity_type == "character"
    assert entity.confidence == 0.92
    assert entity.approved is True
    assert entity.dedup_action == "new"


def test_staged_entity_defaults():
    entity = StagedEntity(
        entity_id="ent-2",
        entity_type="world_bible",
        entity_json={"title": "Magic"},
        dedup_action="enrich",
    )
    assert entity.confidence == 0.0
    assert entity.source_excerpt is None
    assert entity.approved is False


def test_staged_entity_confidence_too_high():
    with pytest.raises(Exception):
        StagedEntity(
            entity_id="ent-3",
            entity_type="character",
            entity_json={},
            confidence=1.5,
            dedup_action="new",
        )


# -- EntityApprovalUpdate --

def test_entity_approval_update():
    update = EntityApprovalUpdate(entity_id="ent-1", approved=True)
    assert update.entity_id == "ent-1"
    assert update.approved is True


# -- CascadeApplyResponse --

def test_cascade_apply_response_defaults():
    resp = CascadeApplyResponse()
    assert resp.characters_added == 0
    assert resp.relationships_added == 0
    assert resp.world_bible_added == 0
    assert resp.characters_enriched == 0


def test_cascade_apply_response_custom():
    resp = CascadeApplyResponse(
        characters_added=3,
        relationships_added=1,
        world_bible_added=2,
        characters_enriched=1,
    )
    assert resp.characters_added == 3
    assert resp.relationships_added == 1


# -- StagedEntitiesResponse --

def test_staged_entities_response():
    entity = StagedEntity(
        entity_id="ent-1",
        entity_type="character",
        entity_json={"name": "Bob"},
        dedup_action="new",
    )
    resp = StagedEntitiesResponse(
        stage_id="stage-1",
        project_id="proj-1",
        characters=[entity],
    )
    assert resp.stage_id == "stage-1"
    assert len(resp.characters) == 1


def test_staged_entities_response_empty():
    resp = StagedEntitiesResponse(stage_id="stage-2", project_id="proj-2")
    assert resp.characters == []
    assert resp.relationships == []
    assert resp.world_bible == []


# -- CascadeUndoResponse --

def test_cascade_undo_response():
    resp = CascadeUndoResponse(stage_id="stage-1", entities_reverted=5)
    assert resp.stage_id == "stage-1"
    assert resp.entities_reverted == 5
