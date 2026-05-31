def test_circuit_breaker_can_reset_registry():
    """Circuit breaker registry should support reset for test isolation."""
    from app.services.circuit_breaker import CircuitBreakerRegistry, CircuitState, get_circuit_breaker

    cb = get_circuit_breaker("test-reset-service")
    for _ in range(5):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("test")))
        except Exception:
            pass

    assert cb.get_state().state == CircuitState.OPEN, "Circuit should be OPEN after failures"

    CircuitBreakerRegistry.reset_all()

    cb2 = get_circuit_breaker("test-reset-service")
    assert cb2.get_state().state == CircuitState.CLOSED, "Circuit should be CLOSED after reset"
