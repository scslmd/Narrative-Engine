"""Tests for lineage-aware artifact reads in ProjectService."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.projects import ProjectService
from app.schemas.projects import ProjectCreateRequest, ManifestConfig


class TestLineageAwareArtifactReads:
    """Test that read_artifact prefers lineage-aware canonical artifacts."""

    def test_read_artifact_falls_back_to_file_when_no_lineage(self, tmp_path: Path) -> None:
        """When no canonical lineage exists, read_artifact should fall back to file-based read."""
        # Create a test project
        project_id = f"test-fallback-{uuid4().hex[:8]}"
        service = ProjectService(root_dir=tmp_path)
        
        request = ProjectCreateRequest(
            project_id=project_id,
            project_name="Test Fallback Project",
            config=ManifestConfig(
                genre="Test",
                tone_profile="Test",
                story_structure="THREE_ACT",
            ),
        )
        service.create_project(request)
        
        # Update the sequences.json file with test content
        artifact_path = tmp_path / "data" / "projects" / project_id / "sequences.json"
        artifact_path.write_text('{"sequence": ["fallback test"]}')
        
        # Read the artifact
        result = service.read_artifact(project_id, "sequence")
        
        # Verify file-based read works and lineage fields are None
        assert result.project_id == project_id
        assert result.artifact_name == "sequence"
        assert "fallback test" in result.content
        assert result.lineage_id is None
        assert result.run_id is None
        assert result.step_name is None

    def test_read_manifest_always_uses_file_read(self, tmp_path: Path) -> None:
        """Manifest reads should always use file-based read (not lineage-tracked)."""
        # Create a test project
        project_id = f"test-manifest-{uuid4().hex[:8]}"
        service = ProjectService(root_dir=tmp_path)
        
        request = ProjectCreateRequest(
            project_id=project_id,
            project_name="Test Manifest Project",
            config=ManifestConfig(
                genre="Test",
                tone_profile="Test",
                story_structure="THREE_ACT",
            ),
        )
        service.create_project(request)
        
        # Read the manifest
        result = service.read_artifact(project_id, "manifest")
        
        # Verify manifest read works
        assert result.project_id == project_id
        assert result.artifact_name == "manifest"
        assert "project_name" in result.content
        assert result.lineage_id is None  # Manifest never has lineage

    def test_read_artifact_returns_404_when_not_found_anywhere(self, tmp_path: Path) -> None:
        """When artifact doesn't exist in lineage or files, should raise FileNotFoundError."""
        # Create a test project
        project_id = f"test-404-{uuid4().hex[:8]}"
        service = ProjectService(root_dir=tmp_path)
        
        request = ProjectCreateRequest(
            project_id=project_id,
            project_name="Test 404 Project",
            config=ManifestConfig(
                genre="Test",
                tone_profile="Test",
                story_structure="THREE_ACT",
            ),
        )
        service.create_project(request)
        
        # Try to read non-existent artifact
        with pytest.raises(FileNotFoundError, match="Artifact not found"):
            service.read_artifact(project_id, "non-existent-artifact")

    def test_read_artifact_with_lineage_fields_backward_compatible(self, tmp_path: Path) -> None:
        """ProjectArtifactResponse should be backward compatible when lineage fields are None."""
        from app.schemas.projects import ProjectArtifactResponse
        from datetime import datetime
        
        # Create response without lineage fields (old style)
        response = ProjectArtifactResponse(
            project_id="test-project",
            artifact_name="sequence",
            content="test content",
            updated_at=datetime.now(),
        )
        
        # Verify all fields are present
        assert response.project_id == "test-project"
        assert response.artifact_name == "sequence"
        assert response.content == "test content"
        assert response.lineage_id is None
        assert response.run_id is None
        assert response.step_name is None
        
        # Create response with lineage fields (new style)
        response_with_lineage = ProjectArtifactResponse(
            project_id="test-project",
            artifact_name="sequence",
            content="test content",
            updated_at=datetime.now(),
            lineage_id=123,
            run_id="run-456",
            step_name="generate_sequence",
        )
        
        # Verify lineage fields are present
        assert response_with_lineage.lineage_id == 123
        assert response_with_lineage.run_id == "run-456"
        assert response_with_lineage.step_name == "generate_sequence"

    def test_read_chapter_artifact(self, tmp_path: Path) -> None:
        """Test reading chapter artifact (chapter_1)."""
        # Create a test project
        project_id = f"test-chapter-{uuid4().hex[:8]}"
        service = ProjectService(root_dir=tmp_path)
        
        request = ProjectCreateRequest(
            project_id=project_id,
            project_name="Test Chapter Project",
            config=ManifestConfig(
                genre="Test",
                tone_profile="Test",
                story_structure="THREE_ACT",
            ),
        )
        service.create_project(request)
        
        # Update the chapter.md file with test content
        chapter_path = tmp_path / "data" / "projects" / project_id / "chapter.md"
        chapter_path.write_text("# Chapter 1\n\nTest chapter content.")
        
        # Read the chapter artifact
        result = service.read_artifact(project_id, "chapter-1")
        
        # Verify chapter read works
        assert result.project_id == project_id
        assert result.artifact_name == "chapter-1"
        assert "Chapter 1" in result.content
        assert result.lineage_id is None