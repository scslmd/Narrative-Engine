from __future__ import annotations

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from ..schemas.extraction_progress import ExtractionProgressResponse

logger = logging.getLogger(__name__)


@dataclass
class ExtractionJob:
    extraction_id: str
    status: str = "pending"  # pending | running | completed | failed
    phase: str = ""
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class ExtractionJobManager:
    """Manages async extraction jobs with in-memory storage.

    Jobs are stored in a thread-safe dict. Completed jobs expire after TTL.
    """

    def __init__(self, max_workers: int = 2, ttl_seconds: int = 300) -> None:
        self._jobs: dict[str, ExtractionJob] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="extraction-worker")
        self._ttl_seconds = ttl_seconds

    def submit(self, worker_fn: Callable[..., Any] | None = None, **worker_kwargs: Any) -> str:
        """Create a job and submit work to thread pool. Returns extraction_id."""
        extraction_id = str(uuid.uuid4())
        with self._lock:
            job = ExtractionJob(extraction_id=extraction_id)
            self._jobs[extraction_id] = job
        if worker_fn is not None:
            worker_kwargs["extraction_id"] = extraction_id
            self._executor.submit(self._worker, extraction_id, worker_fn, worker_kwargs)
        return extraction_id

    def get_status(self, extraction_id: str) -> ExtractionProgressResponse:
        """Get current job status for polling."""
        with self._lock:
            job = self._jobs.get(extraction_id)
            if job is None:
                raise KeyError(f"Extraction job {extraction_id} not found or expired")
        return ExtractionProgressResponse(
            extraction_id=job.extraction_id,
            status=job.status,
            phase=job.phase,
            result=job.result,
            error=job.error,
        )

    def update_progress(self, extraction_id: str, **kwargs: Any) -> None:
        """Update job progress from worker thread."""
        with self._lock:
            job = self._jobs.get(extraction_id)
            if job is None:
                return
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

    def complete(self, extraction_id: str, result: Any) -> None:
        """Mark job as completed with result."""
        self.update_progress(extraction_id, status="completed", result=result)

    def fail(self, extraction_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        self.update_progress(extraction_id, status="failed", error=error)

    def _worker(self, extraction_id: str, worker_fn: Callable[..., Any], kwargs: dict[str, Any]) -> None:
        """Thread pool worker: run function and update job status."""
        self.update_progress(extraction_id, status="running")
        try:
            result = worker_fn(**kwargs)
            self.complete(extraction_id, result)
        except Exception as exc:
            logger.exception("Extraction job %s failed", extraction_id)
            self.fail(extraction_id, str(exc))

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
