from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query

from app.schemas import CharacterProfile, RelationshipEdge
from app.schemas.base import StrictModel
from app.services.relationship_extraction import RelationshipExtractionError, RelationshipExtractionService
from app.services.story_knowledge import (
    StoryKnowledgeNotFoundError,
    StoryKnowledgeService,
    StoryKnowledgeValidationError,
)
from pydantic import Field


class CharacterProfileCreateRequest(StrictModel):
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    character_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    display_name: str = Field(..., min_length=1, max_length=255)
    role_in_story: str = Field(..., min_length=1, max_length=255)
    archetype: str = Field(default="", max_length=100)
    external_goal: str = Field(default="", max_length=2000)
    internal_need: str = Field(default="", max_length=2000)
    misbelief_or_wound: str = Field(default="", max_length=2000)
    core_fear: str = Field(default="", max_length=1000)
    primary_strength: str = Field(default="", max_length=1000)
    fatal_flaw_or_limitation: str = Field(default="", max_length=1000)
    contradictions: list[str] = Field(default_factory=list)
    backstory_summary: str = Field(default="", max_length=5000)
    voice_notes: str = Field(default="", max_length=2000)
    secrets: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    change_axis: str = Field(default="", max_length=1000)
    arc_stage_notes: list[str] = Field(default_factory=list)
    continuity_facts: list[str] = Field(default_factory=list)
    writer_notes: str | None = Field(None, max_length=5000)


class CharacterProfileUpdateRequest(StrictModel):
    display_name: str | None = Field(None, max_length=255)
    role_in_story: str | None = Field(None, max_length=255)
    archetype: str | None = Field(None, max_length=100)
    external_goal: str | None = Field(None, max_length=2000)
    internal_need: str | None = Field(None, max_length=2000)
    misbelief_or_wound: str | None = Field(None, max_length=2000)
    core_fear: str | None = Field(None, max_length=1000)
    primary_strength: str | None = Field(None, max_length=1000)
    fatal_flaw_or_limitation: str | None = Field(None, max_length=1000)
    contradictions: list[str] | None = None
    backstory_summary: str | None = Field(None, max_length=5000)
    voice_notes: str | None = Field(None, max_length=2000)
    secrets: list[str] | None = None
    values: list[str] | None = None
    taboos: list[str] | None = None
    change_axis: str | None = Field(None, max_length=1000)
    arc_stage_notes: list[str] | None = None
    continuity_facts: list[str] | None = None
    writer_notes: str | None = Field(None, max_length=5000)


class CharacterProfileListResponse(StrictModel):
    project_id: str
    items: list[CharacterProfile] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class RelationshipEdgeCreateRequest(StrictModel):
    edge_id: str | None = Field(None, min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    project_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_-]+$')
    source_character_id: str = Field(..., min_length=1, max_length=255)
    target_character_id: str = Field(..., min_length=1, max_length=255)
    relation_kind: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1, max_length=2000)
    tension: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class RelationshipEdgeUpdateRequest(StrictModel):
    source_character_id: str | None = None
    target_character_id: str | None = None
    relation_kind: str | None = None
    summary: str | None = Field(None, min_length=1, max_length=2000)
    tension: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class RelationshipEdgeListResponse(StrictModel):
    project_id: str
    items: list[RelationshipEdge] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)


class RelationshipExtractRequest(StrictModel):
    manuscript_text: str = Field(..., min_length=1, description="Manuscript text to analyze for relationships")
    character_ids: list[str] | None = Field(None, description="Optional list of character IDs to consider")
    model: str | None = Field(None, description="Optional model override")


__all__ = [
    "CharacterProfileCreateRequest",
    "CharacterProfileListResponse",
    "CharacterProfileUpdateRequest",
    "RelationshipEdgeCreateRequest",
    "RelationshipEdgeListResponse",
    "RelationshipEdgeUpdateRequest",
    "RelationshipExtractRequest",
    "register_character_routes",
]


def register_character_routes(
    router: APIRouter,
    story_knowledge_service: StoryKnowledgeService,
    relationship_extraction_service: RelationshipExtractionService,
) -> None:
    @router.get("/characters", response_model=CharacterProfileListResponse)
    def list_characters(project_id: str) -> CharacterProfileListResponse:
        """List all character profiles for a project."""
        characters = list(story_knowledge_service.list_character_profiles(project_id))
        return CharacterProfileListResponse(
            project_id=project_id,
            items=characters,
            meta={"ordered_by": "character_id_asc"},
        )

    @router.get("/characters/{character_id}", response_model=CharacterProfile)
    def get_character(character_id: str, project_id: str) -> CharacterProfile:
        """Get a specific character profile."""
        try:
            return story_knowledge_service.get_character_profile(project_id, character_id=character_id)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Character not found.") from exc

    @router.post("/characters", response_model=CharacterProfile, status_code=201)
    def create_character(payload: CharacterProfileCreateRequest) -> CharacterProfile:
        """Create a new character profile."""
        try:
            return story_knowledge_service.upsert_character_profile(
                payload.project_id,
                character_id=payload.character_id,
                display_name=payload.display_name,
                role_in_story=payload.role_in_story,
                archetype=payload.archetype,
                external_goal=payload.external_goal,
                internal_need=payload.internal_need,
                misbelief_or_wound=payload.misbelief_or_wound,
                core_fear=payload.core_fear,
                primary_strength=payload.primary_strength,
                fatal_flaw_or_limitation=payload.fatal_flaw_or_limitation,
                contradictions=payload.contradictions,
                backstory_summary=payload.backstory_summary,
                voice_notes=payload.voice_notes,
                secrets=payload.secrets,
                values=payload.values,
                taboos=payload.taboos,
                change_axis=payload.change_axis,
                arc_stage_notes=payload.arc_stage_notes,
                continuity_facts=payload.continuity_facts,
                writer_notes=payload.writer_notes,
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/characters/{character_id}", response_model=CharacterProfile)
    def update_character(character_id: str, project_id: str, payload: CharacterProfileUpdateRequest) -> CharacterProfile:
        """Update a character profile."""
        try:
            updates = {
                key: value for key, value in (
                    ("display_name", payload.display_name),
                    ("role_in_story", payload.role_in_story),
                    ("archetype", payload.archetype),
                    ("external_goal", payload.external_goal),
                    ("internal_need", payload.internal_need),
                    ("misbelief_or_wound", payload.misbelief_or_wound),
                    ("core_fear", payload.core_fear),
                    ("primary_strength", payload.primary_strength),
                    ("fatal_flaw_or_limitation", payload.fatal_flaw_or_limitation),
                    ("contradictions", payload.contradictions),
                    ("backstory_summary", payload.backstory_summary),
                    ("voice_notes", payload.voice_notes),
                    ("secrets", payload.secrets),
                    ("values", payload.values),
                    ("taboos", payload.taboos),
                    ("change_axis", payload.change_axis),
                    ("arc_stage_notes", payload.arc_stage_notes),
                    ("continuity_facts", payload.continuity_facts),
                    ("writer_notes", payload.writer_notes),
                ) if value is not None and not (isinstance(value, str) and not value.strip())
            }
            if not updates:
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            # Get existing character and merge with updates
            existing = story_knowledge_service.get_character_profile(project_id, character_id=character_id)
            all_fields = {
                "character_id": character_id,
                **dict(existing),
                **updates,
            }
            # Filter out relationship_edges (auto-populated by service) and project_id
            # Note: relationship_edges is intentionally excluded - it's auto-populated from relationship edges
            upsert_fields = {
                k: v for k, v in all_fields.items()
                if v is not None and k not in ("project_id", "relationship_edges")
            }
            # Call upsert with merged data
            return story_knowledge_service.upsert_character_profile(project_id, **upsert_fields)
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Character not found.") from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/characters/{character_id}/relationships", response_model=RelationshipEdgeListResponse)
    def list_character_relationships(character_id: str, project_id: str) -> RelationshipEdgeListResponse:
        """List all relationships for a character."""
        try:
            relationships = list(story_knowledge_service.list_relationship_edges_for_character(project_id, character_id))
            return RelationshipEdgeListResponse(
                project_id=project_id,
                items=relationships,
                meta={"ordered_by": "edge_id_asc"},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/relationships", response_model=RelationshipEdge, status_code=201)
    def create_relationship(payload: RelationshipEdgeCreateRequest) -> RelationshipEdge:
        """Create a new relationship between characters."""
        try:
            return story_knowledge_service.upsert_relationship_edge(
                payload.project_id,
                edge_id=payload.edge_id,
                source_character_id=payload.source_character_id,
                target_character_id=payload.target_character_id,
                relation_kind=payload.relation_kind,
                summary=payload.summary,
                tension=payload.tension,
                notes=payload.notes,
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/relationships", response_model=RelationshipEdgeListResponse)
    def list_all_relationships(project_id: str) -> RelationshipEdgeListResponse:
        """List all relationship edges for a project."""
        try:
            relationships = list(story_knowledge_service.list_all_relationship_edges(project_id))
            return RelationshipEdgeListResponse(
                project_id=project_id,
                items=relationships,
                meta={"ordered_by": "edge_id_asc"},
            )
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/relationships/extract", response_model=RelationshipEdgeListResponse)
    def extract_relationships(
        project_id: str = Query(...),
        payload: RelationshipExtractRequest = Body(...),
    ) -> RelationshipEdgeListResponse:
        """Extract character relationships from manuscript text using AI analysis."""
        try:
            edges = relationship_extraction_service.extract_relationships(
                project_id=project_id,
                manuscript_text=payload.manuscript_text,
                character_ids=payload.character_ids or None,
                model=payload.model or None,
            )
            return RelationshipEdgeListResponse(
                project_id=project_id,
                items=edges,
                meta={"ordered_by": "edge_id_asc"},
            )
        except RelationshipExtractionError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.patch("/relationships/{edge_id}", response_model=RelationshipEdge)
    def update_relationship(edge_id: str, project_id: str, payload: RelationshipEdgeUpdateRequest) -> RelationshipEdge:
        """Update an existing relationship."""
        try:
            source = payload.source_character_id if payload.source_character_id is not None else None
            target = payload.target_character_id if payload.target_character_id is not None else None
            kind = payload.relation_kind if payload.relation_kind is not None else None
            summary = payload.summary if payload.summary is not None else None
            tension = payload.tension
            notes = payload.notes
            if not any(v is not None for v in [source, target, kind, summary, tension, notes]):
                raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
            return story_knowledge_service.upsert_relationship_edge(
                project_id,
                edge_id=edge_id,
                source_character_id=source if source else "",
                target_character_id=target if target else "",
                relation_kind=kind if kind else "",
                summary=summary if summary else "",
                tension=tension,
                notes=notes,
            )
        except HTTPException:
            raise
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/relationships/{edge_id}", status_code=200)
    def delete_relationship(edge_id: str, project_id: str) -> dict[str, str]:
        """Delete a relationship edge."""
        try:
            story_knowledge_service.delete_relationship_edge(project_id, edge_id)
            return {"status": "deleted", "edge_id": edge_id}
        except StoryKnowledgeNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Relationship not found.") from exc
        except (StoryKnowledgeValidationError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
