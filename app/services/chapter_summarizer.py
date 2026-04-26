from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..inference.base import InferenceBackend

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
