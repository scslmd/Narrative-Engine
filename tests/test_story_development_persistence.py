from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.schemas import StoryFlowStageConfigurationState, StoryFlowStageProgressState
from app.persistence.sqlite import OPERATIONS_DB_VERSION, connect, ensure_operations_db
from app.persistence.story_development import StoryDevelopmentRepository


STAMP = datetime(2026, 3, 20, 12, 0, tzinfo=UTC)


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
                "Story Development Test Project",
                str(db_path.with_name("manifest.json")),
                str(db_path),
                STAMP.isoformat(),
                STAMP.isoformat(),
            ),
        )
        connection.commit()


def test_story_development_schema_creation_includes_canonical_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    ensure_operations_db(db_path)
    with connect(db_path) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        }

    assert version == OPERATIONS_DB_VERSION
    assert {"jobs", "checker_runs", "step_records", "artifact_lineage"}.issubset(tables)
    assert {
        "story_flow_definitions",
        "story_flow_stages",
        "brainstorm_items",
        "foundation_profiles",
        "foundation_revisions",
        "character_profiles",
        "world_bible_entries",
        "arc_candidates",
        "arc_selections",
    }.issubset(tables)


def test_story_development_repository_round_trips_representative_objects(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "state" / "narrative_ops.db"
    project_id = "story-dev-roundtrip"
    _seed_project(db_path, project_id)
    repo = StoryDevelopmentRepository(db_path)

    flow = repo.ensure_flow_definition(
        project_id=project_id,
        flow_name="Story Development Flow",
        flow_notes="Editable flow scaffold.",
        created_at=STAMP,
        updated_at=STAMP,
    )
    assert flow.flow_name == "Story Development Flow"

    primary_stage = repo.add_flow_stage(
        project_id=project_id,
        stage_key="brainstorm",
        stage_kind="brainstorm",
        is_custom=False,
        display_name="Brainstorm",
        position=0,
        stage_configuration_state=StoryFlowStageConfigurationState.ENABLED,
        stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
        created_at=STAMP,
        updated_at=STAMP,
    )
    custom_stage = repo.add_flow_stage(
        project_id=project_id,
        stage_key="custom_reflection",
        stage_kind="reflection_pass",
        is_custom=True,
        display_name="Reflection",
        position=1,
        description="Optional return point.",
        depends_on=[primary_stage.stage_key],
        stage_configuration_state=StoryFlowStageConfigurationState.OPTIONAL,
        stage_progress_state=StoryFlowStageProgressState.NOT_STARTED,
        custom_prompt_guidance="Revisit if needed.",
        created_at=STAMP,
        updated_at=STAMP,
    )

    renamed = repo.rename_flow_stage(
        project_id,
        stage_id=primary_stage.stage_id,
        display_name="Idea Storm",
        updated_at=STAMP,
    )
    redefined = repo.redefine_flow_stage(
        project_id,
        stage_id=primary_stage.stage_id,
        stage_kind="brainstorm",
        description="Generate and shape starting ideas.",
        writer_notes="Keep this stage lightweight.",
        custom_prompt_guidance="Offer a few alternate directions.",
        updated_at=STAMP,
    )
    reordered = repo.reorder_flow_stages(
        project_id,
        ordered_stage_ids=[custom_stage.stage_id, primary_stage.stage_id],
        updated_at=STAMP,
    )
    staged = repo.set_flow_stage_state(
        project_id,
        stage_id=primary_stage.stage_id,
        stage_configuration_state=StoryFlowStageConfigurationState.DISABLED,
        stage_progress_state=StoryFlowStageProgressState.IN_PROGRESS,
        updated_at=STAMP,
    )

    assert renamed.display_name == "Idea Storm"
    assert redefined.description == "Generate and shape starting ideas."
    assert [stage.stage_id for stage in reordered] == [custom_stage.stage_id, primary_stage.stage_id]
    assert staged.stage_progress_state == StoryFlowStageProgressState.IN_PROGRESS
    assert staged.stage_configuration_state == StoryFlowStageConfigurationState.DISABLED
    assert repo.delete_custom_flow_stage(project_id, stage_id=custom_stage.stage_id) is True
    assert [stage.stage_key for stage in repo.list_flow_stages(project_id)] == ["brainstorm"]
    assert custom_stage.is_custom is True
    assert primary_stage.is_custom is False

    brainstorm_item = repo.create_brainstorm_item(
        project_id=project_id,
        content="A city that rearranges itself each dusk.",
        item_state="open",
        cluster_key="setting",
        tags=["setting", "high-concept"],
        source_artifact_refs=["manifest"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    updated_brainstorm = repo.update_brainstorm_item_state(
        brainstorm_item.item_id,
        item_state="parked",
        cluster_key="world",
        updated_at=STAMP,
    )
    assert updated_brainstorm.item_state == "parked"
    assert updated_brainstorm.cluster_key == "world"
    assert repo.list_brainstorm_items(project_id)[0].content == brainstorm_item.content

    first_revision = repo.upsert_foundation_profile(
        project_id=project_id,
        premise="A cartographer maps a city that changes every dusk.",
        logline="A cartographer must chart a shifting city before it erases the people inside it.",
        thematic_spine="Memory versus control",
        narrative_constraints=["No time travel"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    second_revision = repo.upsert_foundation_profile(
        project_id=project_id,
        premise="A cartographer maps a city that changes every dusk.",
        logline="The cartographer discovers the city changes to protect a buried truth.",
        thematic_spine="Memory versus control",
        narrative_constraints=["No time travel", "Third-person limited"],
        complexity_level="medium",
        created_at=STAMP,
        updated_at=STAMP,
    )
    foundation_profile = repo.get_foundation_profile(project_id)
    foundation_revisions = repo.list_foundation_revisions(project_id)

    assert first_revision.revision_number == 1
    assert second_revision.revision_number == 2
    assert foundation_profile.current_revision_id == second_revision.revision_id
    assert [revision.revision_number for revision in foundation_revisions] == [1, 2]
    assert foundation_revisions[-1].logline.endswith("buried truth.")

    character = repo.upsert_character_profile(
        project_id=project_id,
        character_id="cartographer",
        display_name="Mara Vale",
        role_in_story="protagonist",
        external_goal="Map the city before dawn.",
        internal_need="Trust the people she maps.",
        contradictions=["Careful planner", "Impulsive explorer"],
        continuity_facts=["Can read hidden street patterns"],
        created_at=STAMP,
        updated_at=STAMP,
    )
    world_entry = repo.upsert_world_bible_entry(
        project_id=project_id,
        entry_type="location",
        title="Shifting City",
        summary="A city that rearranges itself every dusk.",
        canonical_facts=["The gates move at sunset."],
        source_artifacts=["manifest", "foundation"],
        continuity_warnings=["Do not treat street layout as stable."],
        created_at=STAMP,
        updated_at=STAMP,
    )

    assert repo.get_character_profile("cartographer").display_name == "Mara Vale"
    assert repo.list_character_profiles(project_id)[0].character_id == "cartographer"
    assert repo.get_world_bible_entry(project_id, entry_type="location", title="Shifting City").entry_id == world_entry.entry_id
    assert repo.list_world_bible_entries(project_id)[0].title == "Shifting City"
