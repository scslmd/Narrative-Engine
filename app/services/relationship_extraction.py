from __future__ import annotations

import json
import logging
from typing import Any, Sequence

from ..inference.base import InferenceBackend, InferenceBackendError
from ..schemas.story_development import RelationshipEdge
from ..utils.json_extract import extract_json
from .runtime_prompts import build_relationship_extraction_request
from .story_knowledge import StoryKnowledgeService

logger = logging.getLogger(__name__)


class RelationshipExtractionError(ValueError):
    """Error during relationship extraction."""
    pass


class RelationshipExtractionService:
    """Extract character relationships from manuscript text using LLM analysis.

    Analyzes manuscript content to identify interpersonal connections, tensions,
    and dynamics between characters. Creates relationship edges in the project DB.
    """

    def __init__(
        self,
        *,
        story_knowledge_service: StoryKnowledgeService,
        inferencer: InferenceBackend,
    ) -> None:
        self._story_knowledge = story_knowledge_service
        self._inferencer = inferencer

    def extract_relationships(
        self,
        project_id: str,
        manuscript_text: str,
        character_ids: Sequence[str] | None = None,
        model: str | None = None,
    ) -> list[RelationshipEdge]:
        """Extract and persist relationships from manuscript text.

        Args:
            project_id: Project to persist relationships under.
            manuscript_text: Manuscript content to analyze.
            character_ids: Optional list of character IDs to consider. If None,
                loads all characters from the project.
            model: Optional model override.

        Returns:
            List of relationship edges created/updated.
        """
        if not manuscript_text.strip():
            return []

        # Load character IDs if not provided
        if character_ids is None:
            characters = self._story_knowledge.list_character_profiles(project_id)
            character_ids = [c.character_id for c in characters]

        if not character_ids:
            logger.info("No characters found for project %s; skipping relationship extraction", project_id)
            return []

        # Call LLM to extract relationships
        raw_json = self._call_llm(
            manuscript_text=manuscript_text,
            character_ids=list(character_ids),
            model=model,
        )

        # Parse and persist relationships
        edges = self._parse_and_persist(
            project_id=project_id,
            raw_json=raw_json,
            character_ids=set(character_ids),
        )

        logger.info(
            "Extracted %d relationships for project %s", len(edges), project_id
        )
        return edges

    def _call_llm(
        self,
        manuscript_text: str,
        character_ids: list[str],
        model: str | None = None,
    ) -> str:
        """Call LLM to extract relationships from manuscript text."""
        request = build_relationship_extraction_request(
            manuscript_text=manuscript_text,
            character_ids=character_ids,
            default_model=model,
        )

        try:
            response = self._inferencer.generate_text(request)
            return response.content
        except InferenceBackendError as exc:
            raise RelationshipExtractionError(
                f"LLM inference failed during relationship extraction: {exc}"
            ) from exc

    def _parse_and_persist(
        self,
        project_id: str,
        raw_json: str,
        character_ids: set[str],
    ) -> list[RelationshipEdge]:
        """Parse LLM JSON output and persist relationships to DB."""
        try:
            data = extract_json(raw_json)
        except ValueError as exc:
            logger.warning("Failed to parse relationship extraction JSON: %s", exc)
            return []

        if not isinstance(data, list):
            logger.warning("Relationship extraction returned non-array JSON; skipping")
            return []

        edges: list[RelationshipEdge] = []
        seen_pairs: set[tuple[str, str]] = set()

        for item in data:
            if not isinstance(item, dict):
                continue

            source_id = self._get_str(item, "source_character_id")
            target_id = self._get_str(item, "target_character_id")
            kind = self._get_str(item, "relation_kind")
            summary = self._get_str(item, "summary")

            # Validate required fields
            if not all([source_id, target_id, kind, summary]):
                continue

            # Validate character IDs exist
            if source_id not in character_ids or target_id not in character_ids:
                continue

            # Skip duplicates (normalize pair order)
            pair: tuple[str, str] = tuple(sorted([source_id, target_id]))  # type: ignore[assignment]
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            tension = item.get("tension")
            if isinstance(tension, str):
                tension = tension.strip() or None

            try:
                edge = self._story_knowledge.upsert_relationship_edge(
                    project_id,
                    source_character_id=source_id,
                    target_character_id=target_id,
                    relation_kind=kind,
                    summary=summary,
                    tension=tension,
                )
                edges.append(edge)
            except (ValueError, TypeError) as exc:
                logger.warning("Failed to persist relationship %s->%s: %s", source_id, target_id, exc)

        return edges

    @staticmethod
    def _get_str(item: dict[str, Any], key: str) -> str:
        value = item.get(key)
        if isinstance(value, str):
            return value.strip()
        return ""
