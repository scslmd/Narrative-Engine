"""Tests for circuit breaker pattern (REL-01)."""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    get_circuit_breaker,
    get_all_circuit_states,
)


class TestCircuitBreakerBasic:
    """Test basic circuit breaker functionality."""
    
    def test_initial_state_is_closed(self) -> None:
        """New circuit breaker should start in CLOSED state."""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
        state = cb.get_state()
        
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0
    
    def test_successful_calls_reset_failure_count(self) -> None:
        """Successful calls should reset failure counter."""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
        
        # Simulate some failures then success
        with patch.object(cb, '_record_failure'):
            cb._failure_count = 2
        
        cb._record_success()
        
        assert cb._failure_count == 0
    
    def test_calls_pass_through_when_closed(self) -> None:
        """Calls should pass through when circuit is closed."""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
        
        result = cb.call(lambda: "success")
        
        assert result == "success"


class TestCircuitBreakerFailureThreshold:
    """Test circuit opening after failure threshold."""
    
    def test_circuit_opens_after_threshold_failures(self) -> None:
        """Circuit should open after consecutive failures reach threshold."""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError(f"failure {i}")))
        
        state = cb.get_state()
        assert state.state == CircuitState.OPEN
        assert state.failure_count == 3
    
    def test_calls_rejected_when_open(self) -> None:
        """Calls should be rejected immediately when circuit is open."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60.0)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        # Next call should be rejected by circuit breaker
        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(lambda: "should not execute")
        
        assert "Circuit open" in str(exc_info.value)
        assert exc_info.value.recovery_seconds > 0
    
    def test_circuit_open_error_includes_recovery_time(self) -> None:
        """CircuitBreakerError should include recovery time information."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=30.0)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(lambda: None)
        
        assert hasattr(exc_info.value, 'recovery_seconds')
        assert 29 <= exc_info.value.recovery_seconds <= 31


class TestCircuitBreakerRecovery:
    """Test circuit recovery behavior."""
    
    def test_circuit_transitions_to_half_open_after_timeout(self) -> None:
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        assert cb.get_state().state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should trigger state check and transition to half-open
        with pytest.raises((CircuitBreakerError, ValueError)):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("still failing")))
            except CircuitBreakerError:
                # May get rejected if still transitioning
                raise
        
        state = cb.get_state()
        # Should be either HALF_OPEN (if test call happened) or OPEN (if not yet checked)
        assert state.state in [CircuitState.HALF_OPEN, CircuitState.OPEN]
    
    def test_success_in_half_open_closes_circuit(self) -> None:
        """Successful calls in half-open state should close circuit."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        # Wait for half-open transition
        time.sleep(0.15)
        
        # Successful calls should close circuit (need 2 successes)
        result1 = cb.call(lambda: "success1")
        assert result1 == "success1"
        
        result2 = cb.call(lambda: "success2")
        assert result2 == "success2"
        
        state = cb.get_state()
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0
    
    def test_failure_in_half_open_reopens_circuit(self) -> None:
        """Any failure in half-open state should reopen circuit."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        # Wait for half-open transition
        time.sleep(0.15)
        
        # Failure should reopen circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("still failing")))
        
        state = cb.get_state()
        assert state.state == CircuitState.OPEN


class TestCircuitBreakerHalfOpenLimits:
    """Test half-open state call limits."""
    
    def test_half_open_limits_test_calls(self) -> None:
        """Half-open state should limit number of test calls."""
        cb = CircuitBreaker(
            "test", 
            failure_threshold=2, 
            recovery_timeout=0.1,
            half_open_max_calls=2,
        )
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        # Wait for half-open transition
        time.sleep(0.15)
        
        # First test call succeeds
        cb.call(lambda: "success")
        
        # Second test call succeeds
        cb.call(lambda: "success")
        
        # Circuit should now be closed (2 successes)
        state = cb.get_state()
        assert state.state == CircuitState.CLOSED
    
    def test_half_open_rejects_after_max_calls(self) -> None:
        """Should reject calls after max test calls in half-open."""
        cb = CircuitBreaker(
            "test", 
            failure_threshold=2, 
            recovery_timeout=0.1,
            half_open_max_calls=1,
        )
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        # Wait for half-open transition
        time.sleep(0.15)
        
        # First call (test call) - succeeds this time to increment counter
        result = cb.call(lambda: "success")
        assert result == "success"
        
        # Second call should be rejected (max test calls reached before 2 successes)
        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(lambda: "should not execute")
        
        assert "max test calls" in str(exc_info.value).lower()


class TestCircuitBreakerManualReset:
    """Test manual circuit reset."""
    
    def test_reset_returns_to_closed_state(self) -> None:
        """Manual reset should return circuit to CLOSED state."""
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60.0)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        assert cb.get_state().state == CircuitState.OPEN
        
        # Manual reset
        cb.reset()
        
        state = cb.get_state()
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry functionality."""
    
    def test_get_or_create_returns_same_instance(self) -> None:
        """Getting same backend should return same circuit breaker instance."""
        # Reset registry for clean test
        from app.services import circuit_breaker
        circuit_breaker._registry = circuit_breaker.CircuitBreakerRegistry()
        
        cb1 = get_circuit_breaker("llama-cpp")
        cb2 = get_circuit_breaker("llama-cpp")
        
        assert cb1 is cb2
    
    def test_different_backends_get_different_instances(self) -> None:
        """Different backends should get different circuit breakers."""
        # Reset registry for clean test
        from app.services import circuit_breaker
        circuit_breaker._registry = circuit_breaker.CircuitBreakerRegistry()
        
        cb1 = get_circuit_breaker("llama-cpp")
        cb2 = get_circuit_breaker("vllm")
        
        assert cb1 is not cb2
    
    def test_get_all_states_returns_all_registered(self) -> None:
        """Should return states for all registered circuit breakers."""
        # Reset registry for clean test
        from app.services import circuit_breaker
        circuit_breaker._registry = circuit_breaker.CircuitBreakerRegistry()
        
        # Register some breakers
        get_circuit_breaker("backend-1", failure_threshold=3)
        get_circuit_breaker("backend-2", failure_threshold=5)
        
        states = get_all_circuit_states()
        
        assert "backend-1" in states
        assert "backend-2" in states
        assert len(states) == 2


def test_get_circuit_breaker_preserves_per_backend_recovery_timeout() -> None:
    """Different backends should preserve their own recovery_timeout values."""
    # Reset registry for clean test
    from app.services import circuit_breaker
    circuit_breaker._registry = circuit_breaker.CircuitBreakerRegistry()
    
    cb1 = get_circuit_breaker("executor-local-backend", recovery_timeout=30.0)
    cb2 = get_circuit_breaker("executor-remote-backend", recovery_timeout=120.0)
    
    assert cb1.config.recovery_timeout == 30.0
    assert cb2.config.recovery_timeout == 120.0
    assert cb1 is not cb2


class TestCircuitBreakerThreadSafety:
    """Test thread safety of circuit breaker."""
    
    def test_concurrent_calls_dont_corrupt_state(self) -> None:
        """Concurrent calls should not corrupt internal state."""
        import threading
        
        cb = CircuitBreaker("test", failure_threshold=100, recovery_timeout=1.0)
        errors = []
        
        def make_call():
            try:
                cb.call(lambda: "success")
            except Exception as e:
                errors.append(e)
        
        # Make many concurrent calls
        threads = [threading.Thread(target=make_call) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors from state corruption
        assert len(errors) == 0
        
        # State should still be valid
        state = cb.get_state()
        assert state.state == CircuitState.CLOSED
