from __future__ import annotations

from datetime import datetime, timezone

from app.persistence.sqlite import connect
from app.persistence.story_development import StoryDevelopmentRepository
from app.services.brainstorm import BrainstormService, BrainstormValidationError


def _make_service(tmp_path):
    repository = StoryDevelopmentRepository(tmp_path / "story-development.sqlite")
    return BrainstormService(repository), repository


def _register_project(repository: StoryDevelopmentRepository, project_id: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with connect(repository.db_path) as connection:
        connection.execute(
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                f"Project {project_id}",
                f"{project_id}/manifest.json",
                f"{project_id}/bible.db",
                timestamp,
                timestamp,
            ),
        )
        connection.commit()


def test_capture_brainstorm_item_supports_keep_discard_and_park_states(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-1")

    keep_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Keep this opening idea",
        status="keep",
        tags=["opening", "hook"],
        source_artifact_refs=["artifact-1"],
    )
    discard_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Discard this tangent",
        status="discard",
    )
    park_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Park this for later",
        status="park",
    )

    assert keep_item.status == "keep"
    assert discard_item.status == "discard"
    assert park_item.status == "park"
    assert keep_item.tags == ["opening", "hook"]

    stored_keep = repository.get_brainstorm_item(int(keep_item.item_id))
    stored_discard = repository.get_brainstorm_item(int(discard_item.item_id))
    stored_park = repository.get_brainstorm_item(int(park_item.item_id))

    assert stored_keep.item_state == "keep"
    assert stored_keep.source_artifact_refs == ["artifact-1"]
    assert stored_discard.item_state == "discard"
    assert stored_park.item_state == "park"


def test_cluster_brainstorm_items_assigns_shared_cluster_key(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-1")

    first_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Idea one",
        status="keep",
    )
    second_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Idea two",
        status="park",
    )

    clustered_items = service.cluster_brainstorm_items(
        project_id="project-1",
        item_ids=[first_item.item_id, second_item.item_id],
        cluster_key="cluster-001",
    )

    assert [item.item_id for item in clustered_items] == [first_item.item_id, second_item.item_id]
    assert [item.status for item in clustered_items] == ["keep", "park"]
    assert repository.get_brainstorm_item(int(first_item.item_id)).cluster_key == "cluster-001"
    assert repository.get_brainstorm_item(int(second_item.item_id)).cluster_key == "cluster-001"


def test_promote_brainstorm_item_records_cluster_sources_and_journal(tmp_path) -> None:
    service, repository = _make_service(tmp_path)
    _register_project(repository, "project-1")

    first_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Cluster source one",
        status="keep",
        source_artifact_refs=["artifact-a"],
    )
    second_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Cluster source two",
        status="keep",
        source_artifact_refs=["artifact-b"],
    )

    service.cluster_brainstorm_items(
        project_id="project-1",
        item_ids=[first_item.item_id, second_item.item_id],
        cluster_key="cluster-007",
    )

    promotion = service.promote_brainstorm_item(
        project_id="project-1",
        item_id=first_item.item_id,
        target_object_kind="foundation_profile",
        target_object_id="foundation-1",
        notes="Promote the strongest cluster idea.",
    )

    assert promotion.project_id == "project-1"
    assert promotion.source_item_ids == [first_item.item_id, second_item.item_id]
    assert promotion.target_object_kind == "foundation_profile"
    assert promotion.target_object_id == "foundation-1"
    assert promotion.notes == "Promote the strongest cluster idea."
    assert service.list_promotions("project-1") == (promotion,)
    assert repository.get_brainstorm_item(int(first_item.item_id)).cluster_key == "cluster-007"


def test_promote_brainstorm_item_rejects_discarded_items(tmp_path) -> None:
    service, _ = _make_service(tmp_path)
    repository = service.repository
    _register_project(repository, "project-1")

    discarded_item = service.capture_brainstorm_item(
        project_id="project-1",
        content="Discarded idea",
        status="discard",
    )

    try:
        service.promote_brainstorm_item(
            project_id="project-1",
            item_id=discarded_item.item_id,
            target_object_kind="foundation_profile",
            target_object_id="foundation-1",
        )
    except BrainstormValidationError as exc:
        assert "Discarded brainstorm items cannot be promoted." in str(exc)
    else:
        raise AssertionError("Expected discarded brainstorm item promotion to fail")
