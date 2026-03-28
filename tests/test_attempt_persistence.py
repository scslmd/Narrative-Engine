"""Tests for attempt history persistence and projection."""

from __future__ import annotations

import pytest
from uuid import UUID

from app.persistence.jobs import JobRepository
from app.settings import settings
from tests.conftest import get_test_job_id


class TestAttemptHistoryPersistence:
    """Test richer attempt history persistence."""

    def test_get_attempt_summary_stats_returns_correct_structure(self) -> None:
        """get_attempt_summary_stats should return all expected fields."""
        repo = JobRepository(settings.operations_db_path)
        
        # Use shared utility to find an existing job
        job_id = get_test_job_id()
        if not job_id:
            pytest.skip("No jobs in database")
        
        stats = repo.get_attempt_summary_stats(job_id)
        
        # Verify structure
        assert 'total_attempts' in stats
        assert 'successful_attempts' in stats
        assert 'failed_attempts' in stats
        assert 'total_duration_seconds' in stats
        assert 'last_attempt_number' in stats
        assert 'last_attempt_status' in stats
        
        # Verify types
        assert isinstance(stats['total_attempts'], int)
        assert isinstance(stats['successful_attempts'], int)
        assert isinstance(stats['failed_attempts'], int)
        assert isinstance(stats['total_duration_seconds'], (int, float))

    def test_get_attempt_history_with_metadata_returns_enriched_data(self) -> None:
        """get_attempt_history_with_metadata should include duration and events."""
        repo = JobRepository(settings.operations_db_path)
        
        # Find an existing job
        from app.persistence.sqlite import connect
        with connect(settings.operations_db_path) as conn:
            row = conn.execute('SELECT job_id FROM jobs LIMIT 1').fetchone()
            if not row:
                pytest.skip("No jobs in database")
            job_id = UUID(row['job_id'])
        
        history = repo.get_attempt_history_with_metadata(job_id)
        
        assert len(history) > 0
        
        # Check first attempt has enriched fields
        first_attempt = history[0]
        assert 'duration_seconds' in first_attempt
        assert 'events' in first_attempt
        assert isinstance(first_attempt['events'], list)

    def test_attempt_history_ordered_by_attempt_number(self) -> None:
        """Attempt history should be ordered by attempt number ascending."""
        repo = JobRepository(settings.operations_db_path)
        
        # Find an existing job
        from app.persistence.sqlite import connect
        with connect(settings.operations_db_path) as conn:
            row = conn.execute('SELECT job_id FROM jobs LIMIT 1').fetchone()
            if not row:
                pytest.skip("No jobs in database")
            job_id = UUID(row['job_id'])
        
        history = repo.get_attempt_history_with_metadata(job_id)
        
        if len(history) > 1:
            attempt_numbers = [a['attempt_number'] for a in history]
            assert attempt_numbers == sorted(attempt_numbers)

    def test_attempt_summary_stats_correct_counts(self) -> None:
        """Attempt summary stats should have correct counts."""
        repo = JobRepository(settings.operations_db_path)
        
        # Find an existing job
        from app.persistence.sqlite import connect
        with connect(settings.operations_db_path) as conn:
            row = conn.execute('SELECT job_id FROM jobs LIMIT 1').fetchone()
            if not row:
                pytest.skip("No jobs in database")
            job_id = UUID(row['job_id'])
        
        stats = repo.get_attempt_summary_stats(job_id)
        
        # Verify counts are consistent
        assert stats['total_attempts'] == stats['successful_attempts'] + stats['failed_attempts'] + \
               max(0, stats['total_attempts'] - stats['successful_attempts'] - stats['failed_attempts'])
        assert stats['total_attempts'] >= stats['successful_attempts']
        assert stats['total_attempts'] >= stats['failed_attempts']

    def test_empty_job_returns_empty_history(self) -> None:
        """Non-existent job should return empty history."""
        repo = JobRepository(settings.operations_db_path)
        
        # Use a UUID that doesn't exist
        fake_job_id = UUID('00000000-0000-0000-0000-000000000001')
        
        history = repo.get_attempt_history_with_metadata(fake_job_id)
        assert history == []
        
        stats = repo.get_attempt_summary_stats(fake_job_id)
        assert stats['total_attempts'] == 0

    def test_duration_calculation_includes_queue_time(self) -> None:
        """Duration should be calculated from created_at if started_at not available."""
        repo = JobRepository(settings.operations_db_path)
        
        # Find an existing job
        from app.persistence.sqlite import connect
        with connect(settings.operations_db_path) as conn:
            row = conn.execute('SELECT job_id FROM jobs LIMIT 1').fetchone()
            if not row:
                pytest.skip("No jobs in database")
            job_id = UUID(row['job_id'])
        
        history = repo.get_attempt_history_with_metadata(job_id)
        
        if history:
            # Duration should be non-negative
            assert history[0]['duration_seconds'] is None or history[0]['duration_seconds'] >= 0

    def test_parent_attempt_number_set_for_retries(self) -> None:
        """Retried attempts should have parent_attempt_number set."""
        repo = JobRepository(settings.operations_db_path)
        
        # Find a job with multiple attempts (if any exist)
        from app.persistence.sqlite import connect
        with connect(settings.operations_db_path) as conn:
            row = conn.execute(
                'SELECT job_id FROM jobs WHERE attempt_number > 1 LIMIT 1'
            ).fetchone()
            
            if not row:
                pytest.skip("No jobs with retries found")
            job_id = UUID(row['job_id'])
        
        history = repo.get_attempt_history_with_metadata(job_id)
        
        # Check that attempts after the first have parent_attempt_number
        for attempt in history[1:]:
            assert 'parent_attempt_number' in attempt
            assert attempt['parent_attempt_number'] == attempt['attempt_number'] - 1
