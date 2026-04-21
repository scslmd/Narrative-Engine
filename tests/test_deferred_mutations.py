"""Integration tests for deferred mutations: arc selection, relationships, planning reorder."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.story_development import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.settings import settings

_TEST_TIMESTAMP = datetime.now(timezone.utc).isoformat()


def _seed_project(db_path: Path, project_id: str) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    ensure_operations_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, "Test Deferred", str(db_path), str(db_path), _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()


def _build_client(tmp_path: Path, project_id: str = "deferred-mutations") -> tuple[TestClient, str, Path]:
    db_path = tmp_path / "data" / "state" / "deferred_ops.db"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), project_id, db_path


# ============================================================================
# Arc Selection Mutations
# ============================================================================


def test_create_arc_candidate_returns_201(tmp_path: Path) -> None:
    project_id = f"arc-candidate-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    payload = {
        "arc_id": "arc-protagonist",
        "project_id": project_id,
        "name": "The Hero's Journey",
        "summary": "A classic hero's journey arc.",
        "stage_map_notes": ["growth"],
        "fit_notes": ["fits theme"],
        "tags": ["protagonist", "growth"],
    }
    response = client.post("/story-development/arcs/candidates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["arc_id"] == "arc-protagonist"
    assert data["name"] == "The Hero's Journey"
    assert data["project_id"] == project_id


def test_create_arc_candidate_validates_required_fields(tmp_path: Path) -> None:
    project_id = f"arc-candidate-2-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    payload = {
        "arc_id": "arc-invalid",
        "project_id": project_id,
        "name": "Name",
        "summary": "",
    }
    response = client.post("/story-development/arcs/candidates", json=payload)
    assert response.status_code == 422


def test_create_arc_candidate_upsert(tmp_path: Path) -> None:
    project_id = f"arc-candidate-3-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    payload = {
        "arc_id": "arc-upsert-test",
        "project_id": project_id,
        "name": "Original Name",
        "summary": "Original summary.",
        "stage_map_notes": [],
        "fit_notes": [],
        "tags": [],
    }
    first = client.post("/story-development/arcs/candidates", json=payload)
    assert first.status_code == 201
    payload["name"] = "Updated Name"
    payload["summary"] = "Updated summary."
    second = client.post("/story-development/arcs/candidates", json=payload)
    assert second.status_code == 201
    assert second.json()["name"] == "Updated Name"


def test_compare_arc_candidates_scores_and_ranks(tmp_path: Path) -> None:
    project_id = f"arc-compare-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    candidates = [
        {
            "arc_id": "arc-a",
            "project_id": project_id,
            "name": "Arc A",
            "summary": "Summary A.",
            "stage_map_notes": ["note1", "note2", "note3"],
            "fit_notes": ["fit1", "fit2"],
            "tags": ["tag1", "tag2", "tag3", "tag4"],
        },
        {
            "arc_id": "arc-b",
            "project_id": project_id,
            "name": "Arc B",
            "summary": "B.",
            "stage_map_notes": ["note1"],
            "fit_notes": ["fit1"],
            "tags": ["tag1"],
        },
    ]
    payload = {"project_id": project_id, "candidates": candidates}
    response = client.post("/story-development/arcs/comparisons", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    ranked_ids = [item["arc_id"] for item in data["items"]]
    assert ranked_ids[0] == "arc-a"


def test_select_arc_candidate_creates_selection(tmp_path: Path) -> None:
    project_id = f"arc-select-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    candidate_payload = {
        "arc_id": "arc-selected",
        "project_id": project_id,
        "name": "Selected Arc",
        "summary": "Summary.",
        "stage_map_notes": [],
        "fit_notes": [],
        "tags": [],
    }
    client.post("/story-development/arcs/candidates", json=candidate_payload)
    selection_payload = {
        "project_id": project_id,
        "selected_arc": "arc-selected",
        "rejected_arc_ids": ["arc-other"],
        "comparison_notes": ["Reason for selection."],
    }
    response = client.post("/story-development/arcs/selections", json=selection_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_arc"]["arc_id"] == "arc-selected"
    assert data["rejected_arc_ids"] == ["arc-other"]
    assert data["comparison_notes"] == ["Reason for selection."]


def test_select_arc_candidate_with_full_object(tmp_path: Path) -> None:
    project_id = f"arc-select-2-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    selection_payload = {
        "project_id": project_id,
        "selected_arc": {
            "arc_id": "arc-full",
            "project_id": project_id,
            "name": "Full Arc",
            "summary": "Summary.",
            "stage_map_notes": [],
            "fit_notes": [],
            "tags": [],
        },
    }
    response = client.post("/story-development/arcs/selections", json=selection_payload)
    assert response.status_code == 201


def test_select_arc_candidate_cannot_select_rejected(tmp_path: Path) -> None:
    project_id = f"arc-select-3-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    selection_payload = {
        "project_id": project_id,
        "selected_arc": {
            "arc_id": "arc-self",
            "project_id": project_id,
            "name": "Self Arc",
            "summary": "Summary.",
            "stage_map_notes": [],
            "fit_notes": [],
            "tags": [],
        },
        "rejected_arc_ids": ["arc-self"],
    }
    response = client.post("/story-development/arcs/selections", json=selection_payload)
    assert response.status_code == 400


def test_update_arc_selection_patches_notes(tmp_path: Path) -> None:
    project_id = f"arc-update-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    selection_payload = {
        "project_id": project_id,
        "selected_arc": {
            "arc_id": "arc-update",
            "project_id": project_id,
            "name": "Update Arc",
            "summary": "Summary.",
            "stage_map_notes": [],
            "fit_notes": [],
            "tags": [],
        },
        "comparison_notes": ["Original note."],
    }
    create_response = client.post("/story-development/arcs/selections", json=selection_payload)
    assert create_response.status_code == 201
    selection_id = create_response.json()["selection_id"]
    patch_payload = {"comparison_notes": ["Updated note."]}
    response = client.patch(
        f"/story-development/arcs/selections/{selection_id}",
        json=patch_payload,
        params={"project_id": project_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["comparison_notes"] == ["Updated note."]


def test_update_arc_selection_returns_404_when_missing(tmp_path: Path) -> None:
    project_id = f"arc-update-2-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    payload = {"comparison_notes": ["Updated."]}
    response = client.patch(
        "/story-development/arcs/selections/nonexistent",
        json=payload,
        params={"project_id": project_id},
    )
    assert response.status_code == 404


def test_delete_arc_selection_returns_200(tmp_path: Path) -> None:
    project_id = f"arc-delete-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    selection_payload = {
        "project_id": project_id,
        "selected_arc": {
            "arc_id": "arc-delete",
            "project_id": project_id,
            "name": "Delete Arc",
            "summary": "Summary.",
            "stage_map_notes": [],
            "fit_notes": [],
            "tags": [],
        },
    }
    create_response = client.post("/story-development/arcs/selections", json=selection_payload)
    assert create_response.status_code == 201
    selection_id = create_response.json()["selection_id"]
    response = client.delete(
        f"/story-development/arcs/selections/{selection_id}",
        params={"project_id": project_id},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_delete_arc_selection_returns_404_when_missing(tmp_path: Path) -> None:
    project_id = f"arc-delete-2-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    response = client.delete(
        "/story-development/arcs/selections/nonexistent",
        params={"project_id": project_id},
    )
    assert response.status_code == 404


def test_create_arc_stage_map_returns_201(tmp_path: Path) -> None:
    project_id = f"arc-stage-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    candidate_payload = {
        "arc_id": "arc-stage",
        "project_id": project_id,
        "name": "Stage Arc",
        "summary": "Summary.",
        "stage_map_notes": [],
        "fit_notes": [],
        "tags": [],
    }
    client.post("/story-development/arcs/candidates", json=candidate_payload)
    stage_map_payload = {
        "arc_id": "arc-stage",
        "stage_kinds": ["setup", "confrontation", "resolution"],
        "notes": "Main arc structure.",
    }
    response = client.post(
        f"/story-development/arcs/stage-maps?project_id={project_id}",
        json=stage_map_payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["arc_id"] == "arc-stage"
    assert data["stage_kinds"] == ["setup", "confrontation", "resolution"]


# ============================================================================
# Character Relationship Mutations
# ============================================================================


def test_list_all_relationships_returns_200(tmp_path: Path) -> None:
    project_id = f"rel-list-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    response = client.get("/story-development/relationships", params={"project_id": project_id})
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert isinstance(data["items"], list)


def test_create_relationship_via_post(tmp_path: Path) -> None:
    project_id = f"rel-create-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    # Create characters first (required by FK constraint)
    for char_id, name in [("rel-char-a", "Character A"), ("rel-char-b", "Character B")]:
        client.post(
            "/story-development/characters",
            json={
                "project_id": project_id,
                "character_id": char_id,
                "display_name": name,
                "role_in_story": "Supporting",
                "archetype": "Mentor",
                "external_goal": "Help protagonist",
                "internal_need": "Redemption",
                "misbelief_or_wound": "Past failures",
                "core_fear": "Failure",
                "primary_strength": "Wisdom",
                "fatal_flaw_or_limitation": "Pride",
                "contradictions": [],
                "backstory_summary": "Experienced warrior.",
                "voice_notes": "Gruff but kind.",
                "secrets": [],
                "values": ["Loyalty"],
                "taboos": [],
                "change_axis": "Isolation to connection",
                "arc_stage_notes": [],
                "continuity_facts": [],
            },
        )
    # Create relationship
    payload = {
        "edge_id": "rel-edge-1",
        "project_id": project_id,
        "source_character_id": "rel-char-a",
        "target_character_id": "rel-char-b",
        "relation_kind": "allies",
        "summary": "Close friends.",
        "tension": "none",
        "notes": "Met in chapter 1.",
    }
    response = client.post("/story-development/relationships", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["edge_id"] == "rel-edge-1"
    assert data["relation_kind"] == "allies"


def test_update_relationship_via_patch(tmp_path: Path) -> None:
    project_id = f"rel-patch-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    # Create characters first
    for char_id, name in [("rel-patch-a", "Character A"), ("rel-patch-b", "Character B")]:
        client.post(
            "/story-development/characters",
            json={
                "project_id": project_id,
                "character_id": char_id,
                "display_name": name,
                "role_in_story": "Supporting",
                "archetype": "Mentor",
                "external_goal": "Help protagonist",
                "internal_need": "Redemption",
                "misbelief_or_wound": "Past failures",
                "core_fear": "Failure",
                "primary_strength": "Wisdom",
                "fatal_flaw_or_limitation": "Pride",
                "contradictions": [],
                "backstory_summary": "Experienced warrior.",
                "voice_notes": "Gruff but kind.",
                "secrets": [],
                "values": ["Loyalty"],
                "taboos": [],
                "change_axis": "Isolation to connection",
                "arc_stage_notes": [],
                "continuity_facts": [],
            },
        )
    # Create relationship
    client.post(
        "/story-development/relationships",
        json={
            "edge_id": "rel-patch-test",
            "project_id": project_id,
            "source_character_id": "rel-patch-a",
            "target_character_id": "rel-patch-b",
            "relation_kind": "allies",
            "summary": "Original summary.",
        },
    )
    # Patch relationship
    patch_payload = {
        "source_character_id": "rel-patch-a",
        "target_character_id": "rel-patch-b",
        "relation_kind": "rivals",
        "summary": "Updated summary.",
        "tension": "high",
        "notes": None,
    }
    response = client.patch(
        "/story-development/relationships/rel-patch-test",
        json=patch_payload,
        params={"project_id": project_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["relation_kind"] == "rivals"
    assert data["summary"] == "Updated summary."


def test_delete_relationship_returns_200(tmp_path: Path) -> None:
    project_id = f"rel-delete-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    # Create characters first
    for char_id, name in [("rel-del-a", "Character A"), ("rel-del-b", "Character B")]:
        client.post(
            "/story-development/characters",
            json={
                "project_id": project_id,
                "character_id": char_id,
                "display_name": name,
                "role_in_story": "Supporting",
                "archetype": "Mentor",
                "external_goal": "Help protagonist",
                "internal_need": "Redemption",
                "misbelief_or_wound": "Past failures",
                "core_fear": "Failure",
                "primary_strength": "Wisdom",
                "fatal_flaw_or_limitation": "Pride",
                "contradictions": [],
                "backstory_summary": "Experienced warrior.",
                "voice_notes": "Gruff but kind.",
                "secrets": [],
                "values": ["Loyalty"],
                "taboos": [],
                "change_axis": "Isolation to connection",
                "arc_stage_notes": [],
                "continuity_facts": [],
            },
        )
    # Create relationship
    client.post(
        "/story-development/relationships",
        json={
            "edge_id": "rel-delete",
            "project_id": project_id,
            "source_character_id": "rel-del-a",
            "target_character_id": "rel-del-b",
            "relation_kind": "allies",
            "summary": "Summary.",
        },
    )
    response = client.delete(
        "/story-development/relationships/rel-delete",
        params={"project_id": project_id},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    list_response = client.get("/story-development/relationships", params={"project_id": project_id})
    items = list_response.json()["items"]
    assert not any(item["edge_id"] == "rel-delete" for item in items)


def test_delete_relationship_returns_404_when_missing(tmp_path: Path) -> None:
    project_id = f"rel-delete-2-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    response = client.delete(
        "/story-development/relationships/nonexistent",
        params={"project_id": project_id},
    )
    assert response.status_code == 404


# ============================================================================
# Planning Board Reorder
# ============================================================================


def test_reorder_plan_objects_sequences(tmp_path: Path) -> None:
    project_id = f"reorder-seq-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    sequence_a = f"seq-a-{uuid4().hex[:6]}"
    sequence_b = f"seq-b-{uuid4().hex[:6]}"
    client.post("/story-development/planning/sequence-plans", json={
        "sequence_id": sequence_a,
        "project_id": project_id,
        "title": "Sequence A",
        "summary": "Summary A.",
        "beat_ids": [],
        "chapter_ids": [],
        "position": 0,
    })
    client.post("/story-development/planning/sequence-plans", json={
        "sequence_id": sequence_b,
        "project_id": project_id,
        "title": "Sequence B",
        "summary": "Summary B.",
        "beat_ids": [],
        "chapter_ids": [],
        "position": 1,
    })
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "sequence",
        "ordered_plan_ids": [sequence_b, sequence_a],
    })
    assert response.status_code == 200
    list_response = client.get(f"/story-development/planning/sequence-plans?project_id={project_id}")
    items = list_response.json()["items"]
    assert items[0]["sequence_id"] == sequence_b
    assert items[1]["sequence_id"] == sequence_a


def test_reorder_plan_objects_chapters(tmp_path: Path) -> None:
    project_id = f"reorder-chap-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    sequence_id = f"seq-{uuid4().hex[:6]}"
    chapter_a = f"chap-a-{uuid4().hex[:6]}"
    chapter_b = f"chap-b-{uuid4().hex[:6]}"
    from app.persistence.sqlite import connect as _connect
    db_path = db_path
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sequence_plans (sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json, status, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sequence_id, project_id, "Seq", "Summary.", "[]", "[]", "draft", 0, _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        for chap_id in [chapter_a, chapter_b]:
            conn.execute(
                "INSERT INTO chapter_plans (chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes, active_character_ids_json, continuity_requirements_json, unresolved_questions_json, status, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (chap_id, project_id, sequence_id, f"Chapter {chap_id[-3:]}", f"Summary {chap_id[-3:]}.", f"Obj {chap_id[-3:]}.", f"Conflict {chap_id[-3:]}.", f"Stakes {chap_id[-3:]}.", "[]", "[]", "[]", "draft", 0, _TEST_TIMESTAMP, _TEST_TIMESTAMP),
            )
        conn.execute(
            "UPDATE chapter_plans SET position = ? WHERE chapter_id = ?",
            (1, chapter_b),
        )
        conn.commit()
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "chapter",
        "ordered_plan_ids": [chapter_b, chapter_a],
    })
    assert response.status_code == 200
    list_response = client.get(f"/story-development/planning/chapter-plans?project_id={project_id}")
    items = list_response.json()["items"]
    assert items[0]["chapter_id"] == chapter_b
    assert items[1]["chapter_id"] == chapter_a


def test_reorder_plan_objects_scenes(tmp_path: Path) -> None:
    project_id = f"reorder-scene-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    chapter_id = f"chap-scene-{uuid4().hex[:6]}"
    sequence_id = f"seq-scene-{uuid4().hex[:6]}"
    from app.persistence.sqlite import connect as _connect
    db_path = db_path
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sequence_plans (sequence_id, project_id, title, summary, beat_ids_json, chapter_ids_json, status, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sequence_id, project_id, "Seq", "Summary.", "[]", "[]", "draft", 0, _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.execute(
            "INSERT INTO chapter_plans (chapter_id, project_id, sequence_id, title, summary, objective, conflict, stakes, active_character_ids_json, continuity_requirements_json, unresolved_questions_json, status, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chapter_id, project_id, sequence_id, "Chapter", "Summary.", "Obj.", "Conflict.", "Stakes.", "[]", "[]", "[]", "draft", 0, _TEST_TIMESTAMP, _TEST_TIMESTAMP),
        )
        conn.commit()
    scene_a = f"scene-a-{uuid4().hex[:6]}"
    scene_b = f"scene-b-{uuid4().hex[:6]}"
    with _connect(db_path) as conn:
        for scene_id in [scene_a, scene_b]:
            conn.execute(
                "INSERT INTO scene_plans (scene_id, project_id, chapter_id, title, summary, objective, conflict, stakes, active_character_ids_json, continuity_requirements_json, unresolved_questions_json, status, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (scene_id, project_id, chapter_id, f"Scene {scene_id[-3:]}", f"Summary {scene_id[-3:]}.", f"Obj {scene_id[-3:]}.", f"Conflict {scene_id[-3:]}.", f"Stakes {scene_id[-3:]}.", "[]", "[]", "[]", "draft", 0, _TEST_TIMESTAMP, _TEST_TIMESTAMP),
            )
        conn.execute(
            "UPDATE scene_plans SET position = ? WHERE scene_id = ?",
            (1, scene_b),
        )
        conn.commit()
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "scene",
        "ordered_plan_ids": [scene_b, scene_a],
    })
    assert response.status_code == 200
    list_response = client.get(f"/story-development/planning/scene-plans?project_id={project_id}")
    items = list_response.json()["items"]
    assert items[0]["scene_id"] == scene_b
    assert items[1]["scene_id"] == scene_a


def test_reorder_plan_objects_validates_plan_kind(tmp_path: Path) -> None:
    project_id = f"reorder-kind-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "invalid_kind",
        "ordered_plan_ids": ["some-id"],
    })
    assert response.status_code == 400


def test_reorder_plan_objects_rejects_missing_ids(tmp_path: Path) -> None:
    project_id = f"reorder-miss-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "sequence",
        "ordered_plan_ids": ["nonexistent-sequence"],
    })
    assert response.status_code == 400


def test_reorder_plan_objects_rejects_duplicates(tmp_path: Path) -> None:
    project_id = f"reorder-dup-{uuid4().hex[:8]}"
    client, project_id, db_path = _build_client(tmp_path, project_id)
    sequence = f"seq-dup-{uuid4().hex[:6]}"
    client.post("/story-development/planning/sequence-plans", json={
        "sequence_id": sequence,
        "project_id": project_id,
        "title": "Seq",
        "summary": "Summary.",
        "beat_ids": [],
        "chapter_ids": [],
        "position": 0,
    })
    response = client.post("/story-development/planning/reorder", json={
        "project_id": project_id,
        "plan_kind": "sequence",
        "ordered_plan_ids": [sequence, sequence],
    })
    assert response.status_code == 400
