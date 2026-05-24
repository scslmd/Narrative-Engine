from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api import build_story_development_router
from app.persistence.sqlite import connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository

pytestmark = pytest.mark.integration

STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)


def _seed_project(db_path: Path, project_id: str) -> None:
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                "Research API Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def _build_client(tmp_path: Path) -> tuple[TestClient, StoryDevelopmentRepository]:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "research-api"
    _seed_project(db_path, project_id)
    repository = StoryDevelopmentRepository(db_path)
    app = FastAPI()
    app.include_router(build_story_development_router(repository))
    return TestClient(app), repository


# --- List Tests ---


def test_list_research_items_returns_empty(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get("/story-development/research/items", params={"project_id": "research-api"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_list_research_items_filters_by_status(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Item 1",
            "content": "Content 1",
            "status": "active",
        },
    )
    client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Item 2",
            "content": "Content 2",
            "status": "archived",
        },
    )
    response = client.get(
        "/story-development/research/items",
        params={"project_id": "research-api", "status": "active"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_list_research_items_filters_by_genre_tag(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Tagged Item",
            "content": "Content",
            "genre_tags": ["fantasy", "magic"],
        },
    )
    client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Untagged Item",
            "content": "Content",
            "genre_tags": ["sci-fi"],
        },
    )
    response = client.get(
        "/story-development/research/items",
        params={"project_id": "research-api", "genre_tag": "fantasy"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


# --- Create Tests ---


def test_create_research_item_returns_201(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "New Research",
            "content": "Some content",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Research"
    assert data["content"] == "Some content"
    assert data["project_id"] == "research-api"
    assert "item_id" in data


def test_create_research_item_with_all_fields(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Full Item",
            "content": "Full content",
            "source_url": "https://example.com",
            "source_type": "article",
            "genre_tags": ["drama"],
            "citations": ["citation-1"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source_url"] == "https://example.com"
    assert data["source_type"] == "article"
    assert data["genre_tags"] == ["drama"]
    assert data["citations"] == ["citation-1"]


def test_create_research_item_invalid_source_type_returns_422(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Item",
            "content": "Content",
            "source_type": "invalid_type",
        },
    )
    assert response.status_code == 422


def test_create_research_item_missing_title_returns_422(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "content": "Content",
        },
    )
    assert response.status_code == 422


# --- Get Tests ---


def test_get_research_item_returns_200(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Get Item",
            "content": "Get content",
        },
    )
    item_id = create_resp.json()["item_id"]
    response = client.get(
        f"/story-development/research/items/{item_id}",
        params={"project_id": "research-api"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Get Item"


def test_get_research_item_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.get(
        "/story-development/research/items/nonexistent",
        params={"project_id": "research-api"},
    )
    assert response.status_code == 404


# --- Update Tests ---


def test_update_research_item_returns_200(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Original",
            "content": "Original content",
        },
    )
    item_id = create_resp.json()["item_id"]
    response = client.patch(
        f"/story-development/research/items/{item_id}",
        params={"project_id": "research-api"},
        json={"title": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_update_research_item_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.patch(
        "/story-development/research/items/nonexistent",
        params={"project_id": "research-api"},
        json={"title": "Updated"},
    )
    assert response.status_code == 404


# --- Delete Tests ---


def test_delete_research_item_returns_204(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Delete Me",
            "content": "Content",
        },
    )
    item_id = create_resp.json()["item_id"]
    response = client.delete(
        f"/story-development/research/items/{item_id}",
        params={"project_id": "research-api"},
    )
    assert response.status_code == 204


def test_delete_research_item_not_found_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    response = client.delete(
        "/story-development/research/items/nonexistent",
        params={"project_id": "research-api"},
    )
    assert response.status_code == 404


def test_delete_research_item_soft_deletes(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    create_resp = client.post(
        "/story-development/research/items",
        json={
            "project_id": "research-api",
            "title": "Soft Delete",
            "content": "Content",
        },
    )
    item_id = create_resp.json()["item_id"]
    client.delete(
        f"/story-development/research/items/{item_id}",
        params={"project_id": "research-api"},
    )
    response = client.get(
        f"/story-development/research/items/{item_id}",
        params={"project_id": "research-api"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "archived"
