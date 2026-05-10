from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, HTTPException

from app.schemas.discovery import (
    CascadeJobResponse,
    CascadeScanRequest,
    CascadeUndoResponse,
    EntityApprovalUpdate,
    StagedEntitiesResponse,
    StagedEntity,
)
from app.services.cascade_discovery import CascadeDiscoveryService
from app.services.discovery_jobs import CascadeJobManager
from app.persistence.sqlite import connect as connect_sqlite
from app.settings import settings

router = APIRouter(prefix="/v1/discovery", tags=["discovery"])

_service: CascadeDiscoveryService | None = None
_job_manager: CascadeJobManager | None = None


def init_discovery_router(
    service: CascadeDiscoveryService, job_manager: CascadeJobManager
) -> APIRouter:
    global _service, _job_manager
    _service = service
    _job_manager = job_manager
    return router


@router.post("/scan", status_code=202)
async def submit_scan(request: CascadeScanRequest) -> dict[str, str]:
    if _service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")

    job_id = _service.run_scan(
        request.project_id,
        request.manuscript_text,
        request.chunk_size,
        request.include_types,
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> CascadeJobResponse:
    if _job_manager is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")

    job = _job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return CascadeJobResponse(
        job_id=job.job_id,
        status=job.status,
        phase=job.status,
        chunk_index=job.chunk_index,
        total_chunks=job.total_chunks,
        stage_id=job.stage_id,
        error=job.error,
    )


@router.get("/staging/{stage_id}")
async def get_staged_entities(stage_id: str) -> StagedEntitiesResponse:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)

    proj_row = conn.execute(
        "SELECT project_id FROM discovery_staging WHERE stage_id=?",
        (stage_id,),
    ).fetchone()

    if not proj_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Staging session {stage_id} not found")

    rows = conn.execute(
        "SELECT entity_type, entity_id, entity_json, confidence, approved, dedup_action "
        "FROM discovery_staging WHERE stage_id=?",
        (stage_id,),
    ).fetchall()
    conn.close()

    characters: list[StagedEntity] = []
    relationships: list[StagedEntity] = []
    world_bible: list[StagedEntity] = []

    for entity_type, entity_id, entity_json_str, confidence, approved, dedup_action in rows:
        entity = StagedEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            entity_json=json.loads(entity_json_str),
            confidence=confidence or 0.0,
            source_excerpt=None,
            approved=bool(approved) if approved else False,
            dedup_action=dedup_action or "new",
        )
        if entity_type == "character":
            characters.append(entity)
        elif entity_type == "relationship":
            relationships.append(entity)
        else:
            world_bible.append(entity)

    return StagedEntitiesResponse(
        stage_id=stage_id,
        project_id=proj_row[0],
        characters=characters,
        relationships=relationships,
        world_bible=world_bible,
    )


@router.patch("/staging/{stage_id}/entities")
async def update_entity_approval(
    stage_id: str, updates: list[EntityApprovalUpdate]
) -> dict[str, int]:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    for update in updates:
        conn.execute(
            "UPDATE discovery_staging SET approved=? WHERE stage_id=? AND entity_id=?",
            (1 if update.approved else 0, stage_id, update.entity_id),
        )
    conn.commit()
    conn.close()
    return {"updated": len(updates)}


@router.post("/staging/{stage_id}/apply")
async def apply_staged_entities(stage_id: str) -> dict[str, int]:
    from app.schemas.discovery import CascadeApplyResponse as _CascadeApplyResponse

    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    conn.execute("BEGIN IMMEDIATE")

    proj_row = conn.execute(
        "SELECT project_id FROM discovery_staging WHERE stage_id=? AND approved=1",
        (stage_id,),
    ).fetchone()
    if not proj_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Staging session {stage_id} not found")

    project_id = proj_row[0]

    rows = conn.execute(
        "SELECT entity_type, entity_json FROM discovery_staging "
        "WHERE stage_id=? AND approved=1",
        (stage_id,),
    ).fetchall()

    chars_added = 0
    chars_enriched = 0
    rels_added = 0
    wb_added = 0

    for entity_type, entity_json_str in rows:
        data = json.loads(entity_json_str)

        if entity_type == "character":
            name = data.get("display_name", "")
            existing = conn.execute(
                "SELECT character_id FROM character_profiles "
                "WHERE display_name=? COLLATE NOCASE AND project_id=?",
                (name, project_id),
            ).fetchone()

            if existing:
                updates: list[str] = []
                values: list[object] = []
                for key in (
                    "backstory_summary",
                    "voice_notes",
                    "archetype",
                    "external_goal",
                    "internal_need",
                ):
                    if data.get(key):
                        updates.append(f"{key}=?")
                        values.append(data[key])
                if updates:
                    values.extend([existing[0], project_id])
                    conn.execute(
                        f"UPDATE character_profiles SET {', '.join(updates)} "
                        "WHERE character_id=? AND project_id=?",
                        values,
                    )
                chars_enriched += 1
            else:
                char_id = data.get(
                    "character_id", f"discovery-{name.lower().replace(' ', '-')}"
                )
                conn.execute(
                    "INSERT OR IGNORE INTO character_profiles "
                    "(character_id, project_id, display_name, role_in_story) "
                    "VALUES (?, ?, ?, ?)",
                    (char_id, project_id, name, data.get("role_in_story", "")),
                )
                chars_added += 1

        elif entity_type == "relationship":
            rels_added += 1
        else:
            wb_added += 1

    conn.commit()
    conn.close()

    return _CascadeApplyResponse(
        characters_added=chars_added,
        relationships_added=rels_added,
        world_bible_added=wb_added,
        characters_enriched=chars_enriched,
    ).model_dump()


@router.post("/staging/{stage_id}/undo")
async def undo_apply(stage_id: str) -> dict[str, object]:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)

    rows = conn.execute(
        "SELECT entity_type, entity_json FROM discovery_staging "
        "WHERE stage_id=? AND approved=1",
        (stage_id,),
    ).fetchall()

    reverted = 0
    for entity_type, entity_json_str in rows:
        data = json.loads(entity_json_str)
        if entity_type == "character":
            name = data.get("display_name", "")
            conn.execute(
                "DELETE FROM character_profiles WHERE display_name=? COLLATE NOCASE",
                (name,),
            )
            reverted += max(conn.rowcount, 1)
        else:
            reverted += 1

    conn.execute("DELETE FROM discovery_staging WHERE stage_id=?", (stage_id,))
    conn.commit()
    conn.close()

    return {"stage_id": stage_id, "entities_reverted": reverted}


@router.delete("/staging/{stage_id}")
async def discard_staging(stage_id: str) -> dict[str, bool]:
    db_path = settings.operations_db_path
    conn = connect_sqlite(db_path)
    conn.execute("DELETE FROM discovery_staging WHERE stage_id=?", (stage_id,))
    conn.commit()
    conn.close()
    return {"deleted": True}