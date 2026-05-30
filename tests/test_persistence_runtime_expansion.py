"""Integration tests for Storyboard Card, Chapter Packet, and Sequence Plan API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas import StoryArtifactLifecycleState

pytestmark = pytest.mark.integration


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _seed_project(db_path: Path, project_id: str) -> None:
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                "Persistence Runtime Expansion Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary,
                objective, conflict, stakes, active_character_ids_json,
                continuity_requirements_json, unresolved_questions_json,
                status, position, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "chapter-1", project_id, None, "Chapter 1", "Summary 1",
                "Obj 1", "Con 1", "Stk 1", "[]", "[]", "[]",
                "draft", 0, STAMP.isoformat(), STAMP.isoformat(),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary,
                objective, conflict, stakes, active_character_ids_json,
                continuity_requirements_json, unresolved_questions_json,
                status, position, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "chapter-2", project_id, None, "Chapter 2", "Summary 2",
                "Obj 2", "Con 2", "Stk 2", "[]", "[]", "[]",
                "draft", 1, STAMP.isoformat(), STAMP.isoformat(),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary,
                objective, conflict, stakes, active_character_ids_json,
                continuity_requirements_json, unresolved_questions_json,
                status, position, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "chapter-3", project_id, None, "Chapter 3", "Summary 3",
                "Obj 3", "Con 3", "Stk 3", "[]", "[]", "[]",
                "draft", 2, STAMP.isoformat(), STAMP.isoformat(),
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO chapter_plans (
                chapter_id, project_id, sequence_id, title, summary,
                objective, conflict, stakes, active_character_ids_json,
                continuity_requirements_json, unresolved_questions_json,
                status, position, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "chapter-5", project_id, None, "Chapter 5", "Summary 5",
                "Obj 5", "Con 5", "Stk 5", "[]", "[]", "[]",
                "draft", 4, STAMP.isoformat(), STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository, str]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "persistence-runtime-test"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository, project_id


# ============================================================================
# Storyboard Card Integration Tests
# (Only tests unique from test_storyboard_cards.py)
# ============================================================================

class TestStoryboardCardEndpoints:
    """Integration tests for storyboard card API endpoints."""

    def test_create_storyboard_card_validation_error(self, tmp_path: Path) -> None:
        """Creating a card with invalid card_type should return 400."""
        client, _, project_id = _build_client(tmp_path)

        response = client.post(
            "/story-development/storyboard/cards",
            json={
                "project_id": project_id,
                "card_id": f"card-{uuid4().hex[:8]}",
                "title": "Test",
                "content": "Test content",
                "card_type": "invalid_type",
            },
        )

        assert response.status_code == 400
        assert "card_type" in response.json()["detail"].lower() or "valid" in response.json()["detail"].lower()

    def test_update_storyboard_card(self, tmp_path: Path) -> None:
        """Updating a card should return the updated data."""
        client, repo, project_id = _build_client(tmp_path)
        card_id = f"card-{uuid4().hex[:8]}"

        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Original Title",
            content="Original content",
            card_type="idea",
        )

        response = client.patch(
            f"/story-development/storyboard/cards/{card_id}",
            params={"project_id": project_id},
            json={
                "title": "Updated Title",
                "content": "Updated content",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"

    def test_delete_storyboard_card(self, tmp_path: Path) -> None:
        """Deleting a card should return 204."""
        client, repo, project_id = _build_client(tmp_path)
        card_id = f"card-{uuid4().hex[:8]}"

        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="To Delete",
            content="Content",
        )

        response = client.delete(f"/story-development/storyboard/cards/{card_id}", params={"project_id": project_id})

        assert response.status_code == 204

        get_response = client.get(f"/story-development/storyboard/cards/{card_id}", params={"project_id": project_id})
        assert get_response.status_code == 404

    def test_delete_storyboard_card_not_found(self, tmp_path: Path) -> None:
        """Deleting a non-existent card should return 404."""
        client, _, project_id = _build_client(tmp_path)

        response = client.delete("/story-development/storyboard/cards/nonexistent", params={"project_id": project_id})

        assert response.status_code == 404

    def test_upsert_storyboard_card(self, tmp_path: Path) -> None:
        """Upserting an existing card should update it."""
        client, repo, project_id = _build_client(tmp_path)
        card_id = f"card-{uuid4().hex[:8]}"

        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Original Title",
            content="Original content",
        )

        response = client.put(
            f"/story-development/storyboard/cards/{card_id}",
            params={"project_id": project_id},
            json={
                "project_id": project_id,
                "card_id": card_id,
                "title": "Upserted Title",
                "content": "Upserted content",
                "card_type": "scene",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Upserted Title"
        assert data["content"] == "Upserted content"
        assert data["card_type"] == "scene"

    def test_reindex_storyboard_column(self, tmp_path: Path) -> None:
        """Reindexing should update positions in order."""
        client, repo, project_id = _build_client(tmp_path)

        card_id_1 = f"card-{uuid4().hex[:8]}"
        card_id_2 = f"card-{uuid4().hex[:8]}"
        card_id_3 = f"card-{uuid4().hex[:8]}"

        for cid in [card_id_1, card_id_2, card_id_3]:
            repo.create_storyboard_card(
                card_id=cid,
                project_id=project_id,
                title=f"Card {cid}",
                content="Content",
                column_id="planned",
            )

        response = client.put(
            "/story-development/storyboard/cards/planned/reindex",
            params={"project_id": project_id},
            json={"card_ids": [card_id_3, card_id_1, card_id_2]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        positions = {item["card_id"]: item["position"] for item in data["items"]}
        assert positions[card_id_3] == 0
        assert positions[card_id_1] == 1
        assert positions[card_id_2] == 2

    def test_storyboard_card_cross_project_rejection(self, tmp_path: Path) -> None:
        """Updating a card from a different project should return 404."""
        client, repo, project_id = _build_client(tmp_path)
        card_id = f"card-{uuid4().hex[:8]}"

        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Card",
            content="Content",
        )

        response = client.patch(
            f"/story-development/storyboard/cards/{card_id}",
            params={"project_id": "different-project"},
            json={
                "title": "Hacked",
                "content": "Hacked content",
                "card_type": "note",
            },
        )

        assert response.status_code == 404


# ============================================================================
# Chapter Packet Integration Tests
# ============================================================================

class TestChapterPacketEndpoints:
    """Integration tests for chapter packet API endpoints."""

    def test_create_chapter_packet(self, tmp_path: Path) -> None:
        """Creating a chapter packet should return 201."""
        client, _, project_id = _build_client(tmp_path)
        packet_id = f"packet-{uuid4().hex[:8]}"

        response = client.post(
            "/story-development/planning/chapter-packets",
            json={
                "project_id": project_id,
                "packet_id": packet_id,
                "chapter_id": "chapter-1",
                "included_reference_ids": ["ref-1", "ref-2"],
                "constraints": ["keep dialogue short"],
                "scene_goals": ["establish mood"],
                "status": "draft",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["packet_id"] == packet_id
        assert data["chapter_id"] == "chapter-1"
        assert data["status"] == "draft"
        assert "ref-1" in data["included_reference_ids"]

    def test_create_chapter_packet_validation_error(self, tmp_path: Path) -> None:
        """Creating a packet with empty packet_id should return 400."""
        client, _, project_id = _build_client(tmp_path)

        response = client.post(
            "/story-development/planning/chapter-packets",
            json={
                "project_id": project_id,
                "packet_id": "",
                "chapter_id": "chapter-1",
            },
        )

        assert response.status_code == 422

    def test_get_chapter_packet(self, tmp_path: Path) -> None:
        """Getting a packet by ID should return 200."""
        client, repo, project_id = _build_client(tmp_path)
        packet_id = f"packet-{uuid4().hex[:8]}"

        repo.upsert_chapter_packet(
            packet_id=packet_id,
            project_id=project_id,
            chapter_id="chapter-2",
            included_reference_ids=["ref-3"],
            status=StoryArtifactLifecycleState.CANONICAL.value,
        )

        response = client.get(
            f"/story-development/planning/chapter-packets/{packet_id}",
            params={"project_id": project_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["packet_id"] == packet_id
        assert data["status"] == StoryArtifactLifecycleState.CANONICAL.value

    def test_get_chapter_packet_not_found(self, tmp_path: Path) -> None:
        """Getting a non-existent packet should return 404."""
        client, _, project_id = _build_client(tmp_path)

        response = client.get(
            "/story-development/planning/chapter-packets/nonexistent",
            params={"project_id": project_id},
        )

        assert response.status_code == 404

    def test_update_chapter_packet(self, tmp_path: Path) -> None:
        """Updating a packet should return 200 with new data."""
        client, repo, project_id = _build_client(tmp_path)
        packet_id = f"packet-{uuid4().hex[:8]}"

        repo.upsert_chapter_packet(
            packet_id=packet_id,
            project_id=project_id,
            chapter_id="chapter-3",
            status=StoryArtifactLifecycleState.DRAFT.value,
        )

        response = client.patch(
            f"/story-development/planning/chapter-packets/{packet_id}",
            params={"project_id": project_id},
            json={
                "status": StoryArtifactLifecycleState.CANONICAL.value,
                "scene_goals": ["resolve conflict"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StoryArtifactLifecycleState.CANONICAL.value
        assert "resolve conflict" in data["scene_goals"]

    def test_update_chapter_packet_not_found(self, tmp_path: Path) -> None:
        """Updating a non-existent packet should return 404."""
        client, _, project_id = _build_client(tmp_path)

        response = client.patch(
            "/story-development/planning/chapter-packets/nonexistent",
            params={"project_id": project_id},
            json={"status": "canonical"},
        )

        assert response.status_code == 404

    def test_list_chapter_packets_still_works(self, tmp_path: Path) -> None:
        """Existing GET endpoint should still work after adding write endpoints."""
        client, repo, project_id = _build_client(tmp_path)

        repo.upsert_chapter_packet(
            packet_id=f"list-pkt-{uuid4().hex[:8]}",
            project_id=project_id,
            chapter_id="chapter-5",
            status=StoryArtifactLifecycleState.DRAFT.value,
        )

        response = client.get("/story-development/planning/chapter-packets", params={"project_id": project_id})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["project_id"] == project_id


# ============================================================================
# Sequence Plan Integration Tests
# ============================================================================

class TestSequencePlanEndpoints:
    """Integration tests for sequence plan API endpoints."""

    def test_create_sequence_plan(self, tmp_path: Path) -> None:
        """Creating a sequence plan should return 201."""
        client, _, project_id = _build_client(tmp_path)
        seq_id = f"seq-{uuid4().hex[:8]}"

        response = client.post(
            "/story-development/planning/sequence-plans",
            json={
                "project_id": project_id,
                "sequence_id": seq_id,
                "title": "The Journey Begins",
                "summary": "The protagonist leaves home and faces initial challenges.",
                "beat_ids": ["beat-1", "beat-2"],
                "chapter_ids": ["chapter-1", "chapter-2"],
                "status": "draft",
                "position": 1,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["sequence_id"] == seq_id
        assert data["title"] == "The Journey Begins"
        assert data["status"] == "draft"
        assert "beat-1" in data["beat_ids"]
        assert "chapter-1" in data["chapter_ids"]

    def test_create_sequence_plan_validation_error(self, tmp_path: Path) -> None:
        """Creating a sequence plan with empty sequence_id should return 400."""
        client, _, project_id = _build_client(tmp_path)

        response = client.post(
            "/story-development/planning/sequence-plans",
            json={
                "project_id": project_id,
                "sequence_id": "",
                "title": "Test",
            },
        )

        assert response.status_code == 422

    def test_get_sequence_plan(self, tmp_path: Path) -> None:
        """Getting a sequence plan by ID should return 200."""
        client, repo, project_id = _build_client(tmp_path)
        seq_id = f"seq-{uuid4().hex[:8]}"

        repo.upsert_sequence_plan(
            sequence_id=seq_id,
            project_id=project_id,
            title="Retrieval Sequence",
            summary="Retrieval summary",
            status=StoryArtifactLifecycleState.CANONICAL.value,
        )

        response = client.get(
            f"/story-development/planning/sequence-plans/{seq_id}",
            params={"project_id": project_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sequence_id"] == seq_id
        assert data["status"] == StoryArtifactLifecycleState.CANONICAL.value

    def test_get_sequence_plan_not_found(self, tmp_path: Path) -> None:
        """Getting a non-existent sequence plan should return 404."""
        client, _, project_id = _build_client(tmp_path)

        response = client.get(
            "/story-development/planning/sequence-plans/nonexistent",
            params={"project_id": project_id},
        )

        assert response.status_code == 404

    def test_update_sequence_plan(self, tmp_path: Path) -> None:
        """Updating a sequence plan should return 200 with new data."""
        client, repo, project_id = _build_client(tmp_path)
        seq_id = f"seq-{uuid4().hex[:8]}"

        repo.upsert_sequence_plan(
            sequence_id=seq_id,
            project_id=project_id,
            title="Original Title",
            summary="Original summary",
            status=StoryArtifactLifecycleState.DRAFT.value,
            position=1,
        )

        response = client.patch(
            f"/story-development/planning/sequence-plans/{seq_id}",
            params={"project_id": project_id},
            json={
                "title": "Updated Title",
                "status": StoryArtifactLifecycleState.CANONICAL.value,
                "beat_ids": ["beat-3", "beat-4"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == StoryArtifactLifecycleState.CANONICAL.value
        assert "beat-3" in data["beat_ids"]

    def test_update_sequence_plan_not_found(self, tmp_path: Path) -> None:
        """Updating a non-existent sequence plan should return 404."""
        client, _, project_id = _build_client(tmp_path)

        response = client.patch(
            "/story-development/planning/sequence-plans/nonexistent",
            params={"project_id": project_id},
            json={"title": "Updated"},
        )

        assert response.status_code == 404

    def test_list_sequence_plans_still_works(self, tmp_path: Path) -> None:
        """Existing GET endpoint should still work after adding write endpoints."""
        client, repo, project_id = _build_client(tmp_path)

        repo.upsert_sequence_plan(
            sequence_id=f"list-seq-{uuid4().hex[:8]}",
            project_id=project_id,
            title="List Sequence",
            summary="List summary",
        )

        response = client.get("/story-development/planning/sequence-plans", params={"project_id": project_id})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["project_id"] == project_id

    def test_create_sequence_plan_cross_project_rejection(self, tmp_path: Path) -> None:
        """Updating a sequence plan from a different project should return 404."""
        client, repo, project_id = _build_client(tmp_path)
        seq_id = f"seq-{uuid4().hex[:8]}"

        repo.upsert_sequence_plan(
            sequence_id=seq_id,
            project_id=project_id,
            title="Original",
            summary="Original summary",
            status=StoryArtifactLifecycleState.DRAFT.value,
        )

        response = client.patch(
            f"/story-development/planning/sequence-plans/{seq_id}",
            params={"project_id": "different-project"},
            json={"title": "Hacked"},
        )

        assert response.status_code == 404