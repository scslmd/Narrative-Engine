from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.story_import import (
    ImportProgressResponse,
    StoryImportRequest,
    StoryImportResponse,
)
from app.services.import_jobs import ImportJob, ImportJobManager


# ---------------------------------------------------------------------------
# ImportJob dataclass tests
# ---------------------------------------------------------------------------


class TestImportJob:
    def test_import_job_defaults(self):
        job = ImportJob(import_id="test-123")
        assert job.status == "pending"
        assert job.phase == ""
        assert job.chapters_processed == 0
        assert job.total_estimated_chapters == 0
        assert job.chunks_processed == 0
        assert job.total_estimated_chunks == 0
        assert job.result is None
        assert job.error is None

    def test_import_job_created_at_set(self):
        before = time.time()
        job = ImportJob(import_id="test-123")
        after = time.time()
        assert before <= job.created_at <= after


# ---------------------------------------------------------------------------
# ImportJobManager - submit / get_status (no threads)
# ---------------------------------------------------------------------------


class TestImportJobManagerSubmit:
    def test_submit_returns_import_id(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        assert isinstance(import_id, str)
        assert len(import_id) > 0
        mgr.shutdown(wait=False)

    def test_submit_creates_pending_job(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        status = mgr.get_status(import_id)
        assert status.status == "pending"
        assert status.import_id == import_id
        mgr.shutdown(wait=False)

    def test_submit_without_worker_does_not_spawn_threads(self):
        mgr = ImportJobManager()
        import_id = mgr.submit(worker_fn=None)
        status = mgr.get_status(import_id)
        assert status.status == "pending"
        mgr.shutdown(wait=False)

    def test_submit_with_worker_sets_running(self):
        completed_event = threading.Event()

        def slow_worker(**kwargs):
            completed_event.wait(timeout=2)
            return "done"

        mgr = ImportJobManager()
        import_id = mgr.submit(worker_fn=slow_worker)
        time.sleep(0.1)
        status = mgr.get_status(import_id)
        assert status.status == "running"
        completed_event.set()
        time.sleep(0.2)
        mgr.shutdown(wait=True)

    def test_submit_multiple_jobs_returns_unique_ids(self):
        mgr = ImportJobManager()
        ids = {mgr.submit() for i in range(5)}
        assert len(ids) == 5
        mgr.shutdown(wait=False)


class TestImportJobManagerGetStatus:
    def test_get_status_returns_import_progress_response(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        status = mgr.get_status(import_id)
        assert isinstance(status, ImportProgressResponse)
        mgr.shutdown(wait=False)

    def test_get_status_unknown_id_raises_key_error(self):
        mgr = ImportJobManager()
        with pytest.raises(KeyError, match="not found or expired"):
            mgr.get_status(str(uuid.uuid4()))
        mgr.shutdown(wait=False)

    def test_get_status_reflects_updated_fields(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        mgr.update_progress(
            import_id,
            status="running",
            phase="analysis",
            chapters_processed=3,
            total_estimated_chapters=10,
            chunks_processed=5,
            total_estimated_chunks=20,
        )
        status = mgr.get_status(import_id)
        assert status.status == "running"
        assert status.phase == "analysis"
        assert status.chapters_processed == 3
        assert status.total_estimated_chapters == 10
        assert status.chunks_processed == 5
        assert status.total_estimated_chunks == 20
        mgr.shutdown(wait=False)


# ---------------------------------------------------------------------------
# ImportJobManager - update_progress / complete / fail
# ---------------------------------------------------------------------------


class TestImportJobManagerUpdateProgress:
    def test_update_progress_sets_known_fields(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        mgr.update_progress(import_id, phase="structure_detection", chapters_processed=1)
        status = mgr.get_status(import_id)
        assert status.phase == "structure_detection"
        assert status.chapters_processed == 1
        mgr.shutdown(wait=False)

    def test_update_progress_ignores_unknown_keys(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        mgr.update_progress(import_id, unknown_field="value", phase="test")
        status = mgr.get_status(import_id)
        assert status.phase == "test"
        assert not hasattr(status, "unknown_field")
        mgr.shutdown(wait=False)

    def test_update_progress_missing_job_is_noop(self):
        mgr = ImportJobManager()
        mgr.update_progress(str(uuid.uuid4()), phase="test")
        mgr.shutdown(wait=False)


class TestImportJobManagerComplete:
    def test_complete_sets_status_and_result(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        result = StoryImportResponse(
            project_id="proj-1",
            status="completed",
            message="OK",
        )
        mgr.complete(import_id, result)
        status = mgr.get_status(import_id)
        assert status.status == "completed"
        assert status.result == result
        mgr.shutdown(wait=False)


class TestImportJobManagerFail:
    def test_fail_sets_status_and_error(self):
        mgr = ImportJobManager()
        import_id = mgr.submit()
        mgr.fail(import_id, "something went wrong")
        status = mgr.get_status(import_id)
        assert status.status == "failed"
        assert status.error == "something went wrong"
        mgr.shutdown(wait=False)


# ---------------------------------------------------------------------------
# ImportJobManager - _worker behaviour
# ---------------------------------------------------------------------------


class TestImportJobManagerWorker:
    def test_worker_completes_on_success(self):
        expected_result = StoryImportResponse(
            project_id="proj-1",
            status="completed",
            message="OK",
        )

        def worker_fn(**kwargs):
            return expected_result

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(worker_fn=worker_fn)
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "completed"
        assert status.result == expected_result
        mgr.shutdown(wait=True)

    def test_worker_catches_exception_and_fails(self):
        def failing_fn(**kwargs):
            raise ValueError("boom")

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(worker_fn=failing_fn)
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "failed"
        assert "boom" in status.error
        mgr.shutdown(wait=True)

    def test_worker_detects_story_import_response_failed(self):
        def failed_import_fn(**kwargs):
            return StoryImportResponse(
                project_id="proj-1",
                status="failed",
                message="LLM unavailable",
            )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(worker_fn=failed_import_fn)
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "failed"
        assert status.error == "LLM unavailable"
        assert isinstance(status.result, StoryImportResponse)
        mgr.shutdown(wait=True)

    def test_worker_passes_import_id_to_worker_fn(self):
        received_kwargs = {}

        def capture_fn(**kwargs):
            received_kwargs.update(kwargs)
            return "ok"

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(worker_fn=capture_fn, extra="value")
        time.sleep(0.3)
        assert received_kwargs.get("import_id") == import_id
        assert received_kwargs.get("extra") == "value"
        mgr.shutdown(wait=True)

    def test_worker_sets_running_before_execution(self):
        started_event = threading.Event()
        release_event = threading.Event()
        captured_status = None

        def blocking_fn(**kwargs):
            nonlocal captured_status
            started_event.set()
            release_event.wait(timeout=3)
            return "ok"

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(worker_fn=blocking_fn)
        started_event.wait(timeout=2)
        captured_status = mgr.get_status(import_id).status
        release_event.set()
        assert captured_status == "running"
        mgr.shutdown(wait=True)


# ---------------------------------------------------------------------------
# ImportJobManager - cleanup_expired
# ---------------------------------------------------------------------------


class TestImportJobManagerCleanup:
    def test_cleanup_removes_expired_completed_jobs(self):
        mgr = ImportJobManager(ttl_seconds=0)
        import_id = mgr.submit()
        mgr.complete(import_id, "result")
        time.sleep(0.05)
        removed = mgr.cleanup_expired()
        assert removed >= 1
        with pytest.raises(KeyError):
            mgr.get_status(import_id)
        mgr.shutdown(wait=False)

    def test_cleanup_removes_expired_failed_jobs(self):
        mgr = ImportJobManager(ttl_seconds=0)
        import_id = mgr.submit()
        mgr.fail(import_id, "error")
        time.sleep(0.05)
        removed = mgr.cleanup_expired()
        assert removed >= 1
        with pytest.raises(KeyError):
            mgr.get_status(import_id)
        mgr.shutdown(wait=False)

    def test_cleanup_keeps_running_jobs(self):
        mgr = ImportJobManager(ttl_seconds=0)
        import_id = mgr.submit()
        mgr.update_progress(import_id, status="running")
        removed = mgr.cleanup_expired()
        assert removed == 0
        status = mgr.get_status(import_id)
        assert status.status == "running"
        mgr.shutdown(wait=False)

    def test_cleanup_keeps_pending_jobs(self):
        mgr = ImportJobManager(ttl_seconds=0)
        import_id = mgr.submit()
        removed = mgr.cleanup_expired()
        assert removed == 0
        status = mgr.get_status(import_id)
        assert status.status == "pending"
        mgr.shutdown(wait=False)

    def test_cleanup_keeps_non_expired_jobs(self):
        mgr = ImportJobManager(ttl_seconds=300)
        import_id = mgr.submit()
        result = StoryImportResponse(
            project_id="proj-1",
            status="completed",
            message="OK",
        )
        mgr.complete(import_id, result)
        removed = mgr.cleanup_expired()
        assert removed == 0
        status = mgr.get_status(import_id)
        assert status.status == "completed"
        mgr.shutdown(wait=False)

    def test_cleanup_returns_count_of_removed(self):
        mgr = ImportJobManager(ttl_seconds=0)
        ids = [mgr.submit() for i in range(3)]
        for iid in ids:
            mgr.complete(iid, "result")
        time.sleep(0.05)
        removed = mgr.cleanup_expired()
        assert removed == 3
        mgr.shutdown(wait=False)


# ---------------------------------------------------------------------------
# ImportJobManager - thread safety
# ---------------------------------------------------------------------------


class TestImportJobManagerThreadSafety:
    def test_concurrent_updates_do_not_corrupt_state(self):
        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit()
        errors = []

        def updater(i: int):
            try:
                for _ in range(50):
                    mgr.update_progress(
                        import_id,
                        phase=f"phase-{i}",
                        chapters_processed=i,
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=updater, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0
        status = mgr.get_status(import_id)
        assert status.chapters_processed >= 0
        mgr.shutdown(wait=True)

    def test_concurrent_get_status_is_safe(self):
        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit()
        results = []
        errors = []

        def reader():
            try:
                for _ in range(50):
                    s = mgr.get_status(import_id)
                    results.append(s.status)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0
        assert len(results) == 500
        mgr.shutdown(wait=True)


# ---------------------------------------------------------------------------
# ImportJobManager - shutdown & TTL config
# ---------------------------------------------------------------------------


class TestImportJobManagerLifecycle:
    def test_shutdown_stops_executor(self):
        mgr = ImportJobManager()
        mgr.shutdown(wait=True)
        with pytest.raises(RuntimeError, match="shutdown"):
            mgr._executor.submit(lambda: None)

    def test_ttl_configuration_is_respected(self):
        mgr = ImportJobManager(ttl_seconds=1)
        assert mgr._ttl_seconds == 1

    def test_max_workers_configuration(self):
        mgr = ImportJobManager(max_workers=4)
        assert mgr._executor._max_workers == 4  # type: ignore[union-attr]
        mgr.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Progress callback integration tests
# ---------------------------------------------------------------------------


class TestProgressCallbackIntegration:
    """Test that progress callbacks correctly update job state via the worker."""

    def test_progress_callback_updates_job_phase(self):
        phases_received = []
        barrier = threading.Barrier(2)

        def worker_with_callbacks(import_id, job_manager, **kwargs):
            job_manager.update_progress(import_id, phase="structure_detection")
            phases_received.append("structure_detection")
            job_manager.update_progress(import_id, phase="chapter_analysis", chapters_processed=1)
            phases_received.append("chapter_analysis")
            barrier.wait(timeout=2)
            return StoryImportResponse(
                project_id="proj-1",
                status="completed",
                message="OK",
            )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=worker_with_callbacks,
            job_manager=mgr,
        )
        barrier.wait(timeout=2)
        status = mgr.get_status(import_id)
        assert status.phase == "chapter_analysis"
        assert status.chapters_processed == 1
        assert "structure_detection" in phases_received
        assert "chapter_analysis" in phases_received
        mgr.shutdown(wait=True)

    def test_progress_callback_updates_chapter_counts(self):
        def counting_worker(import_id, job_manager, **kwargs):
            for i in range(5):
                job_manager.update_progress(
                    import_id,
                    phase="chapter_analysis",
                    chapters_processed=i + 1,
                    total_estimated_chapters=5,
                )
            return StoryImportResponse(
                project_id="proj-1",
                status="completed",
                message="OK",
                chapters_processed=5,
                total_estimated_chapters=5,
            )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=counting_worker,
            job_manager=mgr,
        )
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "completed"
        assert status.chapters_processed == 5
        assert status.total_estimated_chapters == 5
        mgr.shutdown(wait=True)

    def test_progress_callback_updates_chunk_counts(self):
        def chunk_worker(import_id, job_manager, **kwargs):
            job_manager.update_progress(
                import_id,
                phase="consolidation_characters",
                chunks_processed=3,
                total_estimated_chunks=10,
            )
            return StoryImportResponse(
                project_id="proj-1",
                status="completed",
                message="OK",
            )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=chunk_worker,
            job_manager=mgr,
        )
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.phase == "consolidation_characters"
        assert status.chunks_processed == 3
        assert status.total_estimated_chunks == 10
        mgr.shutdown(wait=True)

    def test_progress_callback_failure_does_not_block_service(self):
        error_raised = False

        def failing_callback_worker(import_id, job_manager, **kwargs):
            nonlocal error_raised
            job_manager.update_progress(import_id, phase="analysis")
            try:
                raise RuntimeError("service failure")
            except RuntimeError:
                error_raised = True
                return StoryImportResponse(
                    project_id="proj-1",
                    status="failed",
                    message="service failure",
                )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=failing_callback_worker,
            job_manager=mgr,
        )
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert error_raised
        assert status.status == "failed"
        assert status.phase == "analysis"
        mgr.shutdown(wait=True)

    def test_all_phase_names_are_supported(self):
        expected_phases = [
            "initializing",
            "structure_detection",
            "chapter_analysis",
            "consolidation_characters",
            "consolidation_world_bible",
            "consolidation_arcs",
            "planning_synthesis",
            "persisting",
        ]

        def multi_phase_worker(import_id, job_manager, **kwargs):
            for phase in expected_phases:
                job_manager.update_progress(import_id, phase=phase)
            return StoryImportResponse(
                project_id="proj-1",
                status="completed",
                message="OK",
            )

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=multi_phase_worker,
            job_manager=mgr,
        )
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "completed"
        assert status.phase == "persisting"
        mgr.shutdown(wait=True)

    def test_worker_fn_exception_still_records_last_phase(self):
        def crashing_worker(import_id, job_manager, **kwargs):
            job_manager.update_progress(import_id, phase="chapter_analysis", chapters_processed=2)
            raise ValueError("mid-import crash")

        mgr = ImportJobManager(ttl_seconds=1)
        import_id = mgr.submit(
            worker_fn=crashing_worker,
            job_manager=mgr,
        )
        time.sleep(0.3)
        status = mgr.get_status(import_id)
        assert status.status == "failed"
        assert status.phase == "chapter_analysis"
        assert status.chapters_processed == 2
        assert "mid-import crash" in status.error
        mgr.shutdown(wait=True)

    def test_concurrent_workers_respect_max_workers(self):
        active_count = 0
        max_active = 0
        lock = threading.Lock()
        gate = threading.Event()
        finished = threading.Event()

        def tracked_worker(**kwargs):
            nonlocal active_count, max_active
            with lock:
                active_count += 1
                max_active = max(max_active, active_count)
            gate.wait(timeout=3)
            with lock:
                active_count -= 1
            if active_count == 0:
                finished.set()
            return "ok"

        mgr = ImportJobManager(max_workers=2, ttl_seconds=1)
        for _ in range(4):
            mgr.submit(worker_fn=tracked_worker)

        time.sleep(0.2)
        gate.set()
        finished.wait(timeout=10)
        with lock:
            assert max_active <= 2
        mgr.shutdown(wait=True)
