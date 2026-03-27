"""Circuit breaker pattern for inference backend resilience (REL-01).

Prevents cascade failures when inference backend is unhealthy by:
- Tracking consecutive failures per backend
- Opening circuit after threshold exceeded
- Allowing recovery after cooldown period
- Failing fast with clear error messages
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Failing fast, requests rejected immediately
    HALF_OPEN = "half_open"  # Testing if backend recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5  # Failures before opening circuit
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    half_open_max_calls: int = 3  # Max test calls in half-open state


@dataclass
class CircuitStateSnapshot:
    """Immutable snapshot of current circuit state."""
    
    state: CircuitState
    failure_count: int
    last_failure_time: float | None
    last_success_time: float | None
    recovery_available_at: float | None


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request is rejected."""
    
    def __init__(self, message: str, recovery_seconds: float):
        super().__init__(message)
        self.message = message
        self.recovery_seconds = recovery_seconds


class CircuitBreaker:
    """Circuit breaker for protecting against inference backend failures (REL-01).
    
    Usage:
        circuit = CircuitBreaker("llama-cpp", failure_threshold=5, recovery_timeout=60)
        
        try:
            result = circuit.call(lambda: inferencer.generate(prompt))
        except CircuitBreakerError as e:
            print(f"Circuit open, retry in {e.recovery_seconds}s")
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
        )
        
        # State (protected by lock)
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None
        self._half_open_calls = 0
    
    def get_state(self) -> CircuitStateSnapshot:
        """Get current circuit state snapshot (thread-safe)."""
        with self._lock:
            recovery_available_at = None
            if self._last_failure_time and self._state == CircuitState.OPEN:
                recovery_available_at = self._last_failure_time + self.config.recovery_timeout
            
            return CircuitStateSnapshot(
                state=self._state,
                failure_count=self._failure_count,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                recovery_available_at=recovery_available_at,
            )
    
    def _check_state_transition(self) -> None:
        """Check and perform state transitions based on current conditions."""
        now = time.time()
        
        if self._state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if self._last_failure_time:
                recovery_available_at = self._last_failure_time + self.config.recovery_timeout
                if now >= recovery_available_at:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        
        elif self._state == CircuitState.HALF_OPEN:
            # Half-open transitions handled by success/failure methods
            pass

    def call(self, func: Callable[[], object]) -> object:
        """Execute function through circuit breaker.
        
        Args:
            func: Zero-argument callable to execute
            
        Returns:
            Result of func() if successful
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from func() (also recorded as failure)
        """
        with self._lock:
            self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                # Calculate recovery time
                recovery_available_at = (
                    self._last_failure_time + self.config.recovery_timeout
                    if self._last_failure_time
                    else 0
                )
                recovery_seconds = max(0, recovery_available_at - time.time())
                
                raise CircuitBreakerError(
                    f"Circuit open for {self.name}. Retry after {recovery_seconds:.1f}s",
                    recovery_seconds,
                )
            
            # In half-open state, limit test calls (check BEFORE incrementing)
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit half-open for {self.name}, max test calls reached",
                        0,
                    )
                self._half_open_calls += 1
        
        # Execute function (outside lock to avoid blocking)
        try:
            result = func()
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            now = time.time()
            self._last_success_time = now
            
            if self._state == CircuitState.HALF_OPEN:
                # Success in half-open state - close circuit
                self._success_count += 1
                if self._success_count >= 2:  # Require 2 successes to close
                    self._close_circuit()
            
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def _record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            now = time.time()
            self._last_failure_time = now
            self._failure_count += 1
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state - reopen circuit
                self._open_circuit()
            
            elif self._state == CircuitState.CLOSED:
                # Check if we should open circuit
                if self._failure_count >= self.config.failure_threshold:
                    self._open_circuit()
    
    def _open_circuit(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._half_open_calls = 0
    
    def _close_circuit(self) -> None:
        """Transition to CLOSED state (fully recovered)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._close_circuit()


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers by backend name."""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                )
            return self._breakers[name]
    
    def get_all_states(self) -> dict[str, CircuitStateSnapshot]:
        """Get state snapshots for all circuit breakers."""
        with self._lock:
            return {name: cb.get_state() for name, cb in self._breakers.items()}


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    backend_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """Get circuit breaker for specified inference backend."""
    return _registry.get_or_create(
        name=backend_name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )


def get_all_circuit_states() -> dict[str, CircuitStateSnapshot]:
    """Get current state of all circuit breakers (for monitoring)."""
    return _registry.get_all_states()
