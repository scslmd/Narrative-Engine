from __future__ import annotations

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from ..schemas.story_import import ImportProgressResponse, StoryImportResponse

logger = logging.getLogger(__name__)


@dataclass
class ImportJob:
    import_id: str
    status: str = "pending"  # pending | running | completed | failed
    phase: str = ""
    chapters_processed: int = 0
    total_estimated_chapters: int = 0
    chunks_processed: int = 0
    total_estimated_chunks: int = 0
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class ImportJobManager:
    """Manages async story import jobs with in-memory storage.

    Jobs are stored in a thread-safe dict. Completed jobs expire after TTL.
    """

    def __init__(self, max_workers: int = 2, ttl_seconds: int = 300) -> None:
        self._jobs: dict[str, ImportJob] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="import-worker")
        self._ttl_seconds = ttl_seconds

    def submit(
        self, story_text: str, worker_fn: Callable[..., Any] | None = None, **worker_kwargs: Any
    ) -> str:
        """Create a job and submit work to thread pool. Returns import_id."""
        import_id = str(uuid.uuid4())
        with self._lock:
            job = ImportJob(import_id=import_id)
            self._jobs[import_id] = job
        if worker_fn is not None:
            worker_kwargs["import_id"] = import_id
            self._executor.submit(self._worker, import_id, worker_fn, worker_kwargs)
        return import_id

    def get_status(self, import_id: str) -> ImportProgressResponse:
        """Get current job status for polling."""
        with self._lock:
            job = self._jobs.get(import_id)
            if job is None:
                raise KeyError(f"Import job {import_id} not found or expired")
        return ImportProgressResponse(
            import_id=job.import_id,
            status=job.status,
            phase=job.phase,
            chapters_processed=job.chapters_processed,
            total_estimated_chapters=job.total_estimated_chapters,
            chunks_processed=job.chunks_processed,
            total_estimated_chunks=job.total_estimated_chunks,
            result=job.result,
            error=job.error,
        )

    def update_progress(self, import_id: str, **kwargs: Any) -> None:
        """Update job progress from worker thread."""
        with self._lock:
            job = self._jobs.get(import_id)
            if job is None:
                return
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

    def complete(self, import_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        self.update_progress(import_id, status="completed", result=result)

    def fail(self, import_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        self.update_progress(import_id, status="failed", error=error)

    def _worker(self, import_id: str, worker_fn: Callable[..., Any], kwargs: dict[str, Any]) -> None:
        """Thread pool worker: run function and update job status."""
        self.update_progress(import_id, status="running")
        try:
            result = worker_fn(**kwargs)
            if isinstance(result, StoryImportResponse) and result.status == "failed":
                self.update_progress(
                    import_id,
                    status="failed",
                    result=result,
                    error=result.message,
                )
                return
            self.complete(import_id, result)
        except Exception as exc:
            logger.exception("Import job %s failed", import_id)
            self.fail(import_id, str(exc))

    def cleanup_expired(self) -> int:
        """Remove completed jobs older than TTL. Returns count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_ids = [
                jid for jid, job in self._jobs.items()
                if job.status in ("completed", "failed") and (now - job.created_at) > self._ttl_seconds
            ]
            for jid in expired_ids:
                del self._jobs[jid]
                removed += 1
        return removed

    def shutdown(self, wait: bool = True) -> None:
        """Shut down thread pool."""
        self._executor.shutdown(wait=wait)
