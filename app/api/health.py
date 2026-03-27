"""Health and metrics endpoints (REL-05, REL-06)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from ..services.circuit_breaker import get_all_circuit_states, CircuitState
from ..settings import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    """Basic liveness probe.
    
    Returns 200 if the application is running.
    Used for Kubernetes liveness probes.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Deep readiness probe (REL-06).
    
    Checks all critical components:
    - Database connectivity
    - Inference backend health (via circuit breaker state)
    - Disk space availability
    - Project directory writability
    
    Returns 503 if any critical component is unhealthy.
    Used for Kubernetes readiness probes and load balancer health checks.
    """
    issues = []
    
    # Check database connectivity
    try:
        from ..database import get_db_connection
        
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        issues.append({"component": "database", "error": str(e)})
    
    # Check circuit breaker states (inference backend health)
    circuit_states = get_all_circuit_states()
    for backend_name, state in circuit_states.items():
        if state.state == CircuitState.OPEN:
            recovery_seconds = 0
            if state.recovery_available_at:
                import time
                recovery_seconds = max(0, state.recovery_available_at - time.time())
            
            issues.append({
                "component": f"inference_{backend_name}",
                "error": f"Circuit breaker open",
                "recovery_in_seconds": recovery_seconds,
            })
    
    # Check disk space (warn if < 1GB free)
    try:
        project_dir = settings.projects_dir
        if project_dir.exists():
            stat = os.statvfs(project_dir)
            free_bytes = stat.f_bavail * stat.f_frsize
            min_free_bytes = 1_073_741_824  # 1 GB
            
            if free_bytes < min_free_bytes:
                issues.append({
                    "component": "disk_space",
                    "error": f"Low disk space: {free_bytes / (1024*1024):.1f}MB free",
                })
    except Exception as e:
        issues.append({"component": "disk_space", "error": str(e)})
    
    # Check project directory writability
    try:
        projects_dir = settings.projects_dir
        if not projects_dir.exists():
            projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permission with temp file
        test_file = projects_dir / ".health_check_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append({"component": "projects_directory", "error": str(e)})
    
    if issues:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "issues": issues,
            },
        )
    
    return {
        "status": "ready",
        "components": {
            "database": "ok",
            "inference_backends": {name: str(state.state) for name, state in circuit_states.items()},
            "disk_space": "ok",
            "projects_directory": "ok",
        },
    }


@router.get("/metrics")
async def get_metrics() -> dict:
    """Prometheus-style metrics endpoint (REL-05).
    
    Returns current system metrics:
    - Circuit breaker states for all inference backends
    - Failure counts and recovery times
    
    Can be scraped by Prometheus or similar monitoring systems.
    """
    circuit_states = get_all_circuit_states()
    
    metrics = {
        "circuit_breakers": {},
        "timestamp": None,  # Will be set below
    }
    
    import time
    metrics["timestamp"] = time.time()
    
    for backend_name, state in circuit_states.items():
        metrics["circuit_breakers"][backend_name] = {
            "state": state.state.value,
            "failure_count": state.failure_count,
            "last_failure_time": state.last_failure_time,
            "last_success_time": state.last_success_time,
            "recovery_available_at": state.recovery_available_at,
        }
    
    return metrics
