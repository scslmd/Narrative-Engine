"""Tests for thread safety in LocalExecutor (REL-03)."""

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest


class TestThreadSafety:
    """Test REL-03: Thread safety race condition fix."""
    
    def test_start_is_thread_safe(self) -> None:
        """Multiple concurrent calls to start() should only create threads once."""
        from app.services.local_executor import LocalExecutor
        
        # Create executor with mocked dependencies
        job_manager = MagicMock()
        role_check_manager = MagicMock()
        role_check_service = MagicMock()
        
        executor = LocalExecutor(
            job_manager=job_manager,
            role_check_manager=role_check_manager,
            role_check_service=role_check_service,
        )
        
        # Track how many times threads are created by the executor itself
        worker_thread_count = [0]
        original_thread_init = threading.Thread.__init__
        
        def tracked_thread_init(self, *args, **kwargs):
            # Only count threads with our specific names
            if 'narrative-' in kwargs.get('name', ''):
                worker_thread_count[0] += 1
            return original_thread_init(self, *args, **kwargs)
        
        with patch.object(threading.Thread, '__init__', tracked_thread_init):
            # Call start() from multiple threads concurrently
            with ThreadPoolExecutor(max_workers=10) as pool:
                futures = [pool.submit(executor.start) for _ in range(10)]
                for future in futures:
                    future.result()
            
            # Should only create 2 worker threads (job and checker), not more
            assert worker_thread_count[0] == 2, f"Expected 2 worker thread creations, got {worker_thread_count[0]}"
    
    def test_start_with_existing_threads_returns_early(self) -> None:
        """Calling start() when threads already exist should return immediately."""
        from app.services.local_executor import LocalExecutor
        
        job_manager = MagicMock()
        role_check_manager = MagicMock()
        role_check_service = MagicMock()
        
        executor = LocalExecutor(
            job_manager=job_manager,
            role_check_manager=role_check_manager,
            role_check_service=role_check_service,
        )
        
        # Manually set threads to simulate already started
        mock_thread1 = MagicMock(spec=threading.Thread)
        mock_thread2 = MagicMock(spec=threading.Thread)
        executor._threads = [mock_thread1, mock_thread2]
        
        # Call start() - should return early without creating new threads
        thread_count_before = len(executor._threads)
        executor.start()
        thread_count_after = len(executor._threads)
        
        assert thread_count_before == thread_count_after == 2
    
    def test_stop_clears_threads(self) -> None:
        """stop() should clear the threads list."""
        from app.services.local_executor import LocalExecutor
        
        job_manager = MagicMock()
        role_check_manager = MagicMock()
        role_check_service = MagicMock()
        
        executor = LocalExecutor(
            job_manager=job_manager,
            role_check_manager=role_check_manager,
            role_check_service=role_check_service,
        )
        
        # Set up mock threads
        mock_thread1 = MagicMock(spec=threading.Thread)
        mock_thread2 = MagicMock(spec=threading.Thread)
        executor._threads = [mock_thread1, mock_thread2]
        
        # Stop should clear threads
        executor.stop()
        
        assert len(executor._threads) == 0
    
    def test_start_after_stop_creates_new_threads(self) -> None:
        """After stop(), start() should be able to create new threads."""
        from app.services.local_executor import LocalExecutor
        
        job_manager = MagicMock()
        role_check_manager = MagicMock()
        role_check_service = MagicMock()
        
        executor = LocalExecutor(
            job_manager=job_manager,
            role_check_manager=role_check_manager,
            role_check_service=role_check_service,
        )
        
        # Track thread creation
        creation_count = [0]
        original_thread_init = threading.Thread.__init__
        
        def tracked_thread_init(self, *args, **kwargs):
            if 'narrative-' in kwargs.get('name', ''):
                creation_count[0] += 1
            return original_thread_init(self, *args, **kwargs)
        
        with patch.object(threading.Thread, '__init__', tracked_thread_init):
            # First start
            executor.start()
            assert creation_count[0] == 2
            
            # Stop
            executor.stop()
            
            # Start again - should create new threads
            executor.start()
            assert creation_count[0] == 4, "Should create 2 more threads after restart"
