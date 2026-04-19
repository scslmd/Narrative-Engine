"""Tests for storyboard card persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.persistence.story_development import StoryDevelopmentRepository, StoryboardCardRecord


class TestStoryboardCardPersistence:
    """Test storyboard card CRUD operations."""

    def test_create_storyboard_card(self, tmp_path: Path) -> None:
        """Creating a storyboard card should persist it to the database."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        result = repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Test Card",
            content="Test card content",
            card_type="idea",
            column_id="planned",
            position=0,
            tags=["test", "new"],
            character_ids=["char-1"],
            dependencies=[],
            metadata={"source": "manual"},
        )
        
        assert result.card_id == card_id
        assert result.project_id == project_id
        assert result.title == "Test Card"
        assert result.content == "Test card content"
        assert result.card_type == "idea"
        assert result.column_id == "planned"
        assert result.position == 0
        assert "test" in result.tags
        assert "new" in result.tags
        assert "char-1" in result.character_ids
        assert result.dependencies == []
        assert result.metadata == {"source": "manual"}
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    def test_upsert_storyboard_card_creates_new(self, tmp_path: Path) -> None:
        """Upserting a non-existent card should create it."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        result = repo.upsert_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="New Card",
            content="New card content",
            card_type="scene",
        )
        
        assert result.card_id == card_id
        assert result.title == "New Card"
        assert result.card_type == "scene"

    def test_upsert_storyboard_card_updates_existing(self, tmp_path: Path) -> None:
        """Upserting an existing card should update it."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        # Create initial card
        repo.upsert_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Original Title",
            content="Original content",
            card_type="idea",
        )
        
        # Update the card
        result = repo.upsert_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Updated Title",
            content="Updated content",
            card_type="scene",
        )
        
        assert result.card_id == card_id
        assert result.title == "Updated Title"
        assert result.content == "Updated content"
        assert result.card_type == "scene"

    def test_get_storyboard_card(self, tmp_path: Path) -> None:
        """Getting a card by ID should return the correct record."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Get Test Card",
            content="Content for get test",
        )
        
        result = repo.get_storyboard_card(card_id)
        
        assert result.card_id == card_id
        assert result.title == "Get Test Card"
        assert result.content == "Content for get test"

    def test_get_storyboard_card_not_found(self, tmp_path: Path) -> None:
        """Getting a non-existent card should raise KeyError."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        
        with pytest.raises(KeyError, match="Storyboard card not found"):
            repo.get_storyboard_card("non-existent-card")

    def test_list_storyboard_cards(self, tmp_path: Path) -> None:
        """Listing cards should return all cards for a project."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        
        # Create multiple cards
        for i in range(3):
            repo.create_storyboard_card(
                card_id=f"card-{i}",
                project_id=project_id,
                title=f"Card {i}",
                content=f"Content {i}",
                position=i,
            )
        
        results = repo.list_storyboard_cards(project_id)
        
        assert len(results) == 3
        card_ids = {r.card_id for r in results}
        assert card_ids == {"card-0", "card-1", "card-2"}

    def test_list_storyboard_cards_filtered_by_column(self, tmp_path: Path) -> None:
        """Listing cards with column filter should return only cards in that column."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        
        # Create cards in different columns
        repo.create_storyboard_card(
            card_id="card-1",
            project_id=project_id,
            title="Card 1",
            content="Content",
            column_id="planned",
        )
        repo.create_storyboard_card(
            card_id="card-2",
            project_id=project_id,
            title="Card 2",
            content="Content",
            column_id="drafting",
        )
        repo.create_storyboard_card(
            card_id="card-3",
            project_id=project_id,
            title="Card 3",
            content="Content",
            column_id="planned",
        )
        
        results = repo.list_storyboard_cards(project_id, column_id="planned")
        
        assert len(results) == 2
        assert all(r.column_id == "planned" for r in results)

    def test_list_storyboard_cards_filtered_by_type(self, tmp_path: Path) -> None:
        """Listing cards with type filter should return only cards of that type."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        
        # Create cards of different types
        repo.create_storyboard_card(
            card_id="card-1",
            project_id=project_id,
            title="Scene Card",
            content="Content",
            card_type="scene",
        )
        repo.create_storyboard_card(
            card_id="card-2",
            project_id=project_id,
            title="Idea Card",
            content="Content",
            card_type="idea",
        )
        repo.create_storyboard_card(
            card_id="card-3",
            project_id=project_id,
            title="Beat Card",
            content="Content",
            card_type="beat",
        )
        
        results = repo.list_storyboard_cards(project_id, card_type="scene")
        
        assert len(results) == 1
        assert results[0].card_type == "scene"

    def test_list_storyboard_cards_filtered_by_tag(self, tmp_path: Path) -> None:
        """Listing cards with tag filter should return cards containing that tag."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        
        # Create cards with different tags
        repo.create_storyboard_card(
            card_id="card-1",
            project_id=project_id,
            title="Card 1",
            content="Content",
            tags=["urgent", "main"],
        )
        repo.create_storyboard_card(
            card_id="card-2",
            project_id=project_id,
            title="Card 2",
            content="Content",
            tags=["secondary"],
        )
        repo.create_storyboard_card(
            card_id="card-3",
            project_id=project_id,
            title="Card 3",
            content="Content",
            tags=["urgent", "side"],
        )
        
        results = repo.list_storyboard_cards(project_id, tag="urgent")
        
        assert len(results) == 2
        assert all("urgent" in r.tags for r in results)

    def test_delete_storyboard_card(self, tmp_path: Path) -> None:
        """Deleting a card should remove it from the database."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="To Delete",
            content="Content",
        )
        
        # Verify it exists
        assert repo.get_storyboard_card(card_id).card_id == card_id
        
        # Delete it
        repo.delete_storyboard_card(card_id)
        
        # Verify it's gone
        with pytest.raises(KeyError):
            repo.get_storyboard_card(card_id)

    def test_update_storyboard_card_position(self, tmp_path: Path) -> None:
        """Updating card position should change column and position."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Move Card",
            content="Content",
            column_id="planned",
            position=0,
        )
        
        # Update position
        result = repo.update_storyboard_card_position(
            card_id=card_id,
            column_id="drafting",
            position=5,
        )
        
        assert result.column_id == "drafting"
        assert result.position == 5

    def test_update_storyboard_card_content(self, tmp_path: Path) -> None:
        """Updating card content should modify specified fields."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Original Title",
            content="Original content",
            card_type="idea",
            tags=["old"],
        )
        
        # Update some fields
        result = repo.update_storyboard_card_content(
            card_id=card_id,
            title="New Title",
            tags=["new", "updated"],
        )
        
        assert result.title == "New Title"
        assert result.content == "Original content"  # Unchanged
        assert result.card_type == "idea"  # Unchanged
        assert result.tags == ["new", "updated"]

    def test_storyboard_card_default_values(self, tmp_path: Path) -> None:
        """Creating a card with minimal fields should use defaults."""
        repo = StoryDevelopmentRepository(tmp_path / "test.db")
        project_id = f"test-project-{uuid4().hex[:8]}"
        card_id = f"card-{uuid4().hex[:8]}"
        
        result = repo.create_storyboard_card(
            card_id=card_id,
            project_id=project_id,
            title="Minimal Card",
            content="Minimal content",
        )
        
        assert result.card_id == card_id
        assert result.card_type == "idea"  # Default
        assert result.column_id is None  # Default
        assert result.position == 0  # Default
        assert result.tags == []  # Default
        assert result.character_ids == []  # Default
        assert result.dependencies == []  # Default
        assert result.metadata == {}  # Default