from __future__ import annotations

import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

JobStatusType = Literal["pending", "chunking", "extracting", "deduplicating", "staging", "completed", "failed"]


@dataclass
class CascadeJob:
    job_id: str
    project_id: str
    status: JobStatusType = "pending"
    chunk_index: int | None = None
    total_chunks: int | None = None
    stage_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CascadeJobManager:
    def __init__(self):
        self._jobs: dict[str, CascadeJob] = {}
        self._lock = threading.Lock()

    def create_job(self, project_id: str) -> CascadeJob:
        job = CascadeJob(job_id=str(uuid.uuid4()), project_id=project_id)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> CascadeJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_progress(
        self,
        job_id: str,
        status: JobStatusType,
        chunk_index: int | None = None,
        total_chunks: int | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                if chunk_index is not None:
                    job.chunk_index = chunk_index
                if total_chunks is not None:
                    job.total_chunks = total_chunks

    def complete(self, job_id: str, stage_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "completed"
                job.stage_id = stage_id

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "failed"
                job.error = error
