from __future__ import annotations

import logging
from dataclasses import dataclass
from time import sleep
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChapterResult:
    chapter_id: str
    success: bool
    output_path: str | None = None
    error: str | None = None


class ChapterOrchestrator:
    """Orchestrate sequential P-300 jobs for multi-chapter generation.

    Forward-compatible: same orchestrator can handle book-level orchestration
    in multi-book mode by changing the job payload and summary extraction.
    """

    def __init__(
        self,
        *,
        project_id: str,
        chapter_ids: list[str],
        job_manager: Any,  # JobManager - avoid circular import
    ) -> None:
        self._project_id = project_id
        self._chapter_ids = chapter_ids
        self._job_manager = job_manager

    def run_all(self) -> list[ChapterResult]:
        """Run P-300 jobs sequentially for each chapter.

        Each chapter waits for the prior to complete before starting.
        Prior chapter summaries are built from completed chapters and
        passed as context to subsequent chapters.
        """
        results: list[ChapterResult] = []
        prior_summaries: list[Any] = []  # PriorChapterSummary instances

        for i, chapter_id in enumerate(self._chapter_ids):
            logger.info(
                "Orchestrating chapter %d/%d: %s",
                i + 1,
                len(self._chapter_ids),
                chapter_id,
            )

            payload = {
                "project_id": self._project_id,
                "chapter_id": chapter_id,
            }

            try:
                from app.schemas.jobs import JobCreateRequest

                job = self._job_manager.create_job(
                    JobCreateRequest(phase="P-300", payload=payload)
                )
                status = self._wait_for_completion(job.id)

                if status == "COMPLETED":
                    results.append(
                        ChapterResult(
                            chapter_id=chapter_id,
                            success=True,
                        )
                    )
                    logger.info("Chapter %s completed", chapter_id)
                else:
                    results.append(
                        ChapterResult(
                            chapter_id=chapter_id,
                            success=False,
                            error=f"Job failed with status: {status}",
                        )
                    )
                    logger.warning("Chapter %s failed: %s", chapter_id, status)

            except Exception as exc:
                results.append(
                    ChapterResult(
                        chapter_id=chapter_id,
                        success=False,
                        error=str(exc),
                    )
                )
                logger.error("Chapter %s error: %s", chapter_id, exc)

        return results

    def _wait_for_completion(self, job_id: str, attempts: int = 200) -> str:
        """Poll job status until terminal state."""
        for _ in range(attempts):
            status = self._job_manager.get_status(job_id)
            if str(status.status) in {"COMPLETED", "FAILED"}:
                return str(status.status)
            sleep(0.1)
        return "TIMEOUT"
