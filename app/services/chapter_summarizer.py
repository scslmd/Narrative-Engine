from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..inference.base import InferenceBackend

from ..schemas.story_development import PriorChapterSummary
from .runtime_prompts import build_chapter_summarize_request

logger = logging.getLogger(__name__)


class ChapterSummarizerService:
    """LLM-based chapter summarization service.

    Reads completed chapter markdown and extracts structured PriorChapterSummary:
    - key_events: significant plot points from the chapter
    - character_states: character conditions/goals at chapter end
    - unresolved_threads: open questions, cliffhangers, pending conflicts

    Follows ConsistencyCriticService pattern: graceful error handling, never blocks pipeline.
    """

    def __init__(self, *, inferencer: InferenceBackend) -> None:
        self._inferencer = inferencer

    def summarize(
        self,
        chapter_id: str,
        chapter_text: str,
        character_names: list[str],
    ) -> PriorChapterSummary | None:
        """Extract structured summary from completed chapter markdown.

        Returns PriorChapterSummary on success, None on any failure.
        Never raises exceptions - errors are logged and swallowed.
        """
        if not chapter_text or not chapter_text.strip():
            logger.info("Skipping summarization for empty chapter: %s", chapter_id)
            return None

        try:
            request = build_chapter_summarize_request(
                chapter_id=chapter_id,
                chapter_text=chapter_text,
                character_names=character_names,
                default_model=self._inferencer.descriptor.default_model,
            )
            response = self._inferencer.generate_text(request)
            result = json.loads(response.content)

            return PriorChapterSummary(
                chapter_id=result.get("chapter_id", chapter_id),
                title=result.get("title", f"Chapter {chapter_id}"),
                key_events=result.get("key_events", [])[:10],
                character_states=dict(list(result.get("character_states", {}).items())[:10]),
                unresolved_threads=result.get("unresolved_threads", [])[:5],
            )

        except (json.JSONDecodeError, KeyError, AttributeError) as exc:
            logger.warning("Summarizer parse failed for %s: %s", chapter_id, exc)
            return None
        except Exception as exc:
            from ..inference.base import InferenceBackendError
            if isinstance(exc, InferenceBackendError):
                logger.warning("Summarizer LLM failed for %s: %s", chapter_id, exc)
            else:
                logger.warning("Summarizer unexpected error for %s: %s", chapter_id, exc)
            return None
