from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.enums import PovMode, StoryStructure
from app.schemas.manifest import Manifest, ManifestConfig
from app.services.scene_context import SceneContext


def test_chapter_plan_persists_target_word_count(tmp_path: Path):
    from app.persistence.sqlite import connect, ensure_operations_db
    from app.persistence.story_development import StoryDevelopmentRepository

    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("proj-1", "Test Project", str(db_path.with_name("manifest.json")), str(db_path), "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        connection.commit()

    repo = StoryDevelopmentRepository(db_path)
    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test Chapter",
        summary="A test",
        objective="Test objective",
        conflict="Test conflict",
        stakes="Test stakes",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
        target_word_count=2500,
    )

    record = repo.get_chapter_plan("ch-1")
    assert record.target_word_count == 2500


def test_chapter_plan_target_word_count_defaults_to_none(tmp_path: Path):
    from app.persistence.sqlite import connect, ensure_operations_db
    from app.persistence.story_development import StoryDevelopmentRepository

    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("proj-1", "Test Project", str(db_path.with_name("manifest.json")), str(db_path), "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        connection.commit()

    repo = StoryDevelopmentRepository(db_path)
    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test Chapter",
        summary="A test",
        objective="Test objective",
        conflict="Test conflict",
        stakes="Test stakes",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
    )

    record = repo.get_chapter_plan("ch-1")
    assert record.target_word_count is None


def test_manifest_config_accepts_target_word_count():
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="dark",
        story_structure="THREE_ACT",
        target_word_count=2000,
    )
    assert config.target_word_count == 2000


def test_manifest_config_target_word_count_defaults_to_none():
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="dark",
        story_structure="THREE_ACT",
    )
    assert config.target_word_count is None


def test_manifest_config_rejects_target_word_count_below_100():
    with pytest.raises(ValidationError):
        ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            story_structure="THREE_ACT",
            target_word_count=50,
        )


def test_manifest_config_accepts_target_word_count_at_boundary():
    config = ManifestConfig(
        genre="Fantasy",
        tone_profile="dark",
        story_structure="THREE_ACT",
        target_word_count=100,
    )
    assert config.target_word_count == 100


def test_scene_context_renders_target_word_count():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        target_word_count=1500,
    )
    result = ctx.to_prompt_string()
    assert "CHAPTER LENGTH:" in result
    assert "1500 words" in result


def test_scene_context_omits_length_when_none():
    ctx = SceneContext(
        characters=[],
        world_facts=[],
        target_word_count=None,
    )
    result = ctx.to_prompt_string()
    assert "CHAPTER LENGTH" not in result


def test_assemble_context_resolves_target_word_count_from_manifest(tmp_path: Path):
    from app.persistence.sqlite import connect, ensure_operations_db
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.services.scene_context import SceneContextService

    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("proj-1", "Test Project", str(db_path.with_name("manifest.json")), str(db_path), "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        connection.commit()

    repo = StoryDevelopmentRepository(db_path)
    service = SceneContextService(repo)

    # Add a character so assemble_context doesn't return empty
    repo.upsert_character_profile(
        project_id="proj-1",
        character_id="char-1",
        display_name="Hero",
        role_in_story="protagonist",
        archetype="hero",
    )

    ctx = service.assemble_context(
        project_id="proj-1",
        manifest_target_word_count=2000,
    )
    assert ctx.target_word_count == 2000


def test_assemble_context_chapter_plan_overrides_manifest(tmp_path: Path):
    from app.persistence.sqlite import connect, ensure_operations_db
    from app.persistence.story_development import StoryDevelopmentRepository
    from app.services.scene_context import SceneContextService

    db_path = tmp_path / "test.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO projects (project_id, project_name, manifest_path, db_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("proj-1", "Test Project", str(db_path.with_name("manifest.json")), str(db_path), "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        connection.commit()

    repo = StoryDevelopmentRepository(db_path)
    repo.upsert_chapter_plan(
        project_id="proj-1",
        chapter_id="ch-1",
        title="Test",
        summary="Test",
        objective="Test",
        conflict="Test",
        stakes="Test",
        active_character_ids=[],
        continuity_requirements=[],
        unresolved_questions=[],
        status="planned",
        position=1,
        target_word_count=3000,
    )
    repo.upsert_character_profile(
        project_id="proj-1",
        character_id="char-1",
        display_name="Hero",
        role_in_story="protagonist",
        archetype="hero",
    )

    service = SceneContextService(repo)
    ctx = service.assemble_context(
        project_id="proj-1",
        active_character_ids=["char-1"],
        chapter_plan_id="ch-1",
        manifest_target_word_count=2000,
    )
    assert ctx.target_word_count == 3000


def test_p300_includes_length_instruction_from_manifest():
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
            target_word_count=2000,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately 2000 words" in system_content


def test_p300_payload_override_beats_manifest_target():
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
            target_word_count=2000,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={"target_word_count": 3000},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately 3000 words" in system_content
    assert "2000" not in system_content


def test_p300_omits_length_when_no_target():
    from app.services.runtime_prompts import build_p300_drafter_request

    manifest = Manifest(
        project_id="proj-1",
        project_name="Test",
        config=ManifestConfig(
            genre="Fantasy",
            tone_profile="dark",
            pov=PovMode.THIRD_LIMITED,
            story_structure=StoryStructure.THREE_ACT,
        ),
    )
    req = build_p300_drafter_request(
        manifest=manifest,
        payload={},
        default_model="test-model",
    )
    system_content = req.messages[0].content
    assert "approximately" not in system_content or "words" not in system_content
